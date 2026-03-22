from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, Tuple

import torch
import torch.nn as nn
import torch.nn.functional as F


@dataclass
class Batch:
    drug_x: torch.Tensor
    target_x: torch.Tensor
    drug_neighbors: torch.Tensor
    target_neighbors: torch.Tensor
    drug_neighbor_stats: torch.Tensor
    target_neighbor_stats: torch.Tensor
    labels: torch.Tensor
    drug_cluster_weights: torch.Tensor | None = None
    target_cluster_profile: torch.Tensor | None = None
    target_cluster_mask: torch.Tensor | None = None
    overlap_score: torch.Tensor | None = None


def make_head(input_dim: int, hidden_dim: int, dropout: float = 0.1) -> nn.Sequential:
    return nn.Sequential(
        nn.Linear(input_dim, hidden_dim),
        nn.GELU(),
        nn.Dropout(dropout),
        nn.Linear(hidden_dim, 1),
    )


class MLPEncoder(nn.Module):
    def __init__(self, input_dim: int, hidden_dim: int, embed_dim: int, dropout: float = 0.1):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, embed_dim),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return F.normalize(self.net(x), dim=-1)


class PairConditionedRetriever(nn.Module):
    def __init__(self, embed_dim: int, stat_dim: int, dropout: float = 0.1):
        super().__init__()
        self.stat_dim = stat_dim
        self.scorer = nn.Sequential(
            nn.Linear(embed_dim * 3 + stat_dim, embed_dim),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(embed_dim, 1),
        )
        self.sim_alpha = nn.Parameter(torch.tensor(1.0))
        self.proj = nn.Sequential(
            nn.Linear(embed_dim + stat_dim, embed_dim),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(embed_dim, embed_dim),
        )

    def forward(
        self,
        query: torch.Tensor,
        condition: torch.Tensor,
        neighbors: torch.Tensor,
        neighbor_stats: torch.Tensor,
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        batch_size, k, embed_dim = neighbors.shape
        query_rep = query.unsqueeze(1).expand(batch_size, k, embed_dim)
        cond_rep = condition.unsqueeze(1).expand(batch_size, k, embed_dim)
        scorer_in = torch.cat([query_rep, cond_rep, neighbors, neighbor_stats], dim=-1)
        logits = self.scorer(scorer_in).squeeze(-1)
        if self.stat_dim > 0:
            sim_scores = neighbor_stats[..., -1]
            logits = logits + self.sim_alpha * sim_scores
        attn = F.softmax(logits, dim=-1)
        mixed = torch.sum(attn.unsqueeze(-1) * torch.cat([neighbors, neighbor_stats], dim=-1), dim=1)
        return self.proj(mixed), attn


class BaseDTI(nn.Module):
    def __init__(
        self,
        drug_dim: int,
        target_dim: int,
        hidden_dim: int = 512,
        embed_dim: int = 256,
        dropout: float = 0.1,
    ):
        super().__init__()
        self.embed_dim = embed_dim
        self.hidden_dim = hidden_dim
        self.drug_encoder = MLPEncoder(drug_dim, hidden_dim, embed_dim, dropout)
        self.target_encoder = MLPEncoder(target_dim, hidden_dim, embed_dim, dropout)
        self.head = make_head(embed_dim * 4, hidden_dim, dropout)

    def encode_pair(self, drug_x: torch.Tensor, target_x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        drug = self.drug_encoder(drug_x)
        target = self.target_encoder(target_x)
        return drug, target

    @staticmethod
    def pair_features(drug: torch.Tensor, target: torch.Tensor) -> torch.Tensor:
        return torch.cat([drug, target, drug * target, (drug - target).abs()], dim=-1)

    def forward(self, batch: Batch) -> Tuple[torch.Tensor, Dict[str, torch.Tensor]]:
        drug, target = self.encode_pair(batch.drug_x, batch.target_x)
        features = self.pair_features(drug, target)
        logits = self.head(features).squeeze(-1)
        return logits, {}


class RAICD(BaseDTI):
    def __init__(
        self,
        drug_dim: int,
        target_dim: int,
        hidden_dim: int = 512,
        embed_dim: int = 256,
        stat_dim: int = 3,
        retrieval_mode: str = "both",
        use_retrieval_gate: bool = False,
        dropout: float = 0.1,
    ):
        super().__init__(drug_dim, target_dim, hidden_dim, embed_dim, dropout)
        if retrieval_mode not in {"both", "drug_only", "target_only"}:
            raise ValueError(f"Unknown retrieval_mode: {retrieval_mode}")
        self.retrieval_mode = retrieval_mode
        self.use_retrieval_gate = use_retrieval_gate
        self.drug_retriever = PairConditionedRetriever(embed_dim, stat_dim, dropout)
        self.target_retriever = PairConditionedRetriever(embed_dim, stat_dim, dropout)
        if use_retrieval_gate:
            self.retrieval_gate = nn.Sequential(
                nn.Linear(embed_dim * 2 + 2, embed_dim),
                nn.GELU(),
                nn.Dropout(dropout),
                nn.Linear(embed_dim, 2),
            )
        else:
            self.retrieval_gate = None
        self.head = make_head(embed_dim * 6 + 4, hidden_dim, dropout)

    @staticmethod
    def _norm_entropy(attn: torch.Tensor) -> torch.Tensor:
        eps = 1e-8
        denom = math.log(attn.shape[-1])
        return -(attn * (attn + eps).log()).sum(dim=-1, keepdim=True) / max(denom, eps)

    def _encode_drug_neighbors(self, batch: Batch) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
        drug, target = self.encode_pair(batch.drug_x, batch.target_x)
        batch_size, k_drug, drug_dim = batch.drug_neighbors.shape
        drug_neighbors = self.drug_encoder(batch.drug_neighbors.reshape(batch_size * k_drug, drug_dim)).reshape(batch_size, k_drug, -1)
        drug_ctx, drug_attn = self.drug_retriever(drug, target, drug_neighbors, batch.drug_neighbor_stats)
        drug_entropy = self._norm_entropy(drug_attn)
        top_drug_sim = batch.drug_neighbor_stats[:, 0, -1:].clamp(min=-1.0, max=1.0)
        return drug, target, drug_ctx, drug_attn, drug_entropy, top_drug_sim

    def _encode_target_neighbors(self, drug: torch.Tensor, target: torch.Tensor, batch: Batch) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        batch_size, k_target, target_dim = batch.target_neighbors.shape
        target_neighbors = self.target_encoder(batch.target_neighbors.reshape(batch_size * k_target, target_dim)).reshape(batch_size, k_target, -1)
        target_ctx, target_attn = self.target_retriever(target, drug, target_neighbors, batch.target_neighbor_stats)
        target_entropy = self._norm_entropy(target_attn)
        return target_ctx, target_attn, target_entropy

    def _masked_full_features(
        self,
        drug: torch.Tensor,
        target: torch.Tensor,
        drug_ctx: torch.Tensor,
        target_ctx: torch.Tensor,
        drug_entropy: torch.Tensor,
        target_entropy: torch.Tensor,
        top_drug_sim: torch.Tensor,
        top_target_sim: torch.Tensor,
        mode: str,
    ) -> Tuple[torch.Tensor, Dict[str, torch.Tensor]]:
        if mode not in {"both", "drug_only", "target_only"}:
            raise ValueError(f"Unknown mode: {mode}")

        if mode == "drug_only":
            target_ctx = torch.zeros_like(target_ctx)
            target_entropy = torch.zeros_like(target_entropy)
            top_target_sim = torch.zeros_like(top_target_sim)
        elif mode == "target_only":
            drug_ctx = torch.zeros_like(drug_ctx)
            drug_entropy = torch.zeros_like(drug_entropy)
            top_drug_sim = torch.zeros_like(top_drug_sim)

        if self.retrieval_gate is not None:
            gate_in = torch.cat([drug, target, top_drug_sim, top_target_sim], dim=-1)
            retrieval_gate = torch.sigmoid(self.retrieval_gate(gate_in))
            drug_ctx = drug_ctx * retrieval_gate[:, 0:1]
            target_ctx = target_ctx * retrieval_gate[:, 1:2]
        else:
            retrieval_gate = torch.ones((drug.shape[0], 2), device=drug.device, dtype=drug.dtype)

        if mode == "drug_only":
            retrieval_gate[:, 1] = 0.0
        elif mode == "target_only":
            retrieval_gate[:, 0] = 0.0

        features = torch.cat(
            [
                drug,
                target,
                drug * target,
                (drug - target).abs(),
                drug_ctx,
                target_ctx,
                drug_entropy,
                target_entropy,
                top_drug_sim,
                top_target_sim,
            ],
            dim=-1,
        )
        extras = {
            "drug_entropy": drug_entropy,
            "target_entropy": target_entropy,
            "top_drug_sim": top_drug_sim,
            "top_target_sim": top_target_sim,
            "retrieval_gate": retrieval_gate,
        }
        return features, extras

    def forward(self, batch: Batch) -> Tuple[torch.Tensor, Dict[str, torch.Tensor]]:
        drug, target, drug_ctx, drug_attn, drug_entropy, top_drug_sim = self._encode_drug_neighbors(batch)
        target_ctx, target_attn, target_entropy = self._encode_target_neighbors(drug, target, batch)
        top_target_sim = batch.target_neighbor_stats[:, 0, -1:].clamp(min=-1.0, max=1.0)
        features, extras = self._masked_full_features(
            drug=drug,
            target=target,
            drug_ctx=drug_ctx,
            target_ctx=target_ctx,
            drug_entropy=drug_entropy,
            target_entropy=target_entropy,
            top_drug_sim=top_drug_sim,
            top_target_sim=top_target_sim,
            mode=self.retrieval_mode,
        )
        logits = self.head(features).squeeze(-1)
        aux = {
            "drug_attention": drug_attn,
            "target_attention": target_attn,
            "drug_entropy": extras["drug_entropy"].squeeze(-1),
            "target_entropy": extras["target_entropy"].squeeze(-1),
            "retrieval_gate": extras["retrieval_gate"],
        }
        return logits, aux


class SplitAdaptiveRouter(RAICD):
    expert_names = ("base", "drug_only", "target_only", "both")

    def __init__(
        self,
        drug_dim: int,
        target_dim: int,
        hidden_dim: int = 512,
        embed_dim: int = 256,
        stat_dim: int = 3,
        use_retrieval_gate: bool = False,
        dropout: float = 0.1,
    ):
        super().__init__(
            drug_dim=drug_dim,
            target_dim=target_dim,
            hidden_dim=hidden_dim,
            embed_dim=embed_dim,
            stat_dim=stat_dim,
            retrieval_mode="both",
            use_retrieval_gate=use_retrieval_gate,
            dropout=dropout,
        )
        pair_dim = embed_dim * 4
        full_dim = embed_dim * 6 + 4
        self.base_expert = make_head(pair_dim, hidden_dim, dropout)
        self.drug_expert = make_head(full_dim, hidden_dim, dropout)
        self.target_expert = make_head(full_dim, hidden_dim, dropout)
        self.both_expert = make_head(full_dim, hidden_dim, dropout)
        self.router = nn.Sequential(
            nn.Linear(full_dim + 8, hidden_dim),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, len(self.expert_names)),
        )

    def forward(self, batch: Batch) -> Tuple[torch.Tensor, Dict[str, torch.Tensor]]:
        drug, target, drug_ctx, drug_attn, drug_entropy, top_drug_sim = self._encode_drug_neighbors(batch)
        target_ctx, target_attn, target_entropy = self._encode_target_neighbors(drug, target, batch)
        top_target_sim = batch.target_neighbor_stats[:, 0, -1:].clamp(min=-1.0, max=1.0)

        base_features = self.pair_features(drug, target)
        drug_features, _ = self._masked_full_features(
            drug, target, drug_ctx, target_ctx, drug_entropy, target_entropy, top_drug_sim, top_target_sim, mode="drug_only"
        )
        target_features, _ = self._masked_full_features(
            drug, target, drug_ctx, target_ctx, drug_entropy, target_entropy, top_drug_sim, top_target_sim, mode="target_only"
        )
        both_features, both_extras = self._masked_full_features(
            drug, target, drug_ctx, target_ctx, drug_entropy, target_entropy, top_drug_sim, top_target_sim, mode="both"
        )

        base_logits = self.base_expert(base_features).squeeze(-1)
        drug_logits = self.drug_expert(drug_features).squeeze(-1)
        target_logits = self.target_expert(target_features).squeeze(-1)
        both_logits = self.both_expert(both_features).squeeze(-1)
        expert_logits = torch.stack([base_logits, drug_logits, target_logits, both_logits], dim=-1)

        router_input = torch.cat(
            [
                both_features,
                both_extras["retrieval_gate"],
                both_extras["top_drug_sim"],
                both_extras["top_target_sim"],
                expert_logits,
            ],
            dim=-1,
        )
        route_logits = self.router(router_input)
        route_weights = F.softmax(route_logits, dim=-1)
        logits = torch.sum(route_weights * expert_logits, dim=-1)

        aux = {
            "drug_attention": drug_attn,
            "target_attention": target_attn,
            "drug_entropy": both_extras["drug_entropy"].squeeze(-1),
            "target_entropy": both_extras["target_entropy"].squeeze(-1),
            "retrieval_gate": both_extras["retrieval_gate"],
            "route_weights": route_weights,
            "expert_logits": expert_logits,
        }
        return logits, aux


class FunctionalTargetMemoryDTI(RAICD):
    """
    Replace target-target retrieval with a chemotype-conditioned functional memory.

    The target head predicts signed chemotype preferences relative to the global
    chemotype prior, while drug chemotype assignments stay sparse and query
    specific. This makes target-side memory sharper and less sensitive to noisy,
    low-support targets.
    """

    def __init__(
        self,
        drug_dim: int,
        target_dim: int,
        num_chemotypes: int,
        chemotype_prior: torch.Tensor,
        hidden_dim: int = 512,
        embed_dim: int = 256,
        stat_dim: int = 3,
        dropout: float = 0.1,
    ):
        super().__init__(
            drug_dim=drug_dim,
            target_dim=target_dim,
            hidden_dim=hidden_dim,
            embed_dim=embed_dim,
            stat_dim=stat_dim,
            retrieval_mode="drug_only",
            use_retrieval_gate=False,
            dropout=dropout,
        )
        prior = torch.as_tensor(chemotype_prior, dtype=torch.float32)
        if prior.ndim != 1 or prior.numel() != num_chemotypes:
            raise ValueError("chemotype_prior must be a 1D vector with num_chemotypes entries")
        self.num_chemotypes = num_chemotypes
        self.register_buffer("chemotype_prior", prior)
        self.cluster_memory = nn.Parameter(torch.randn(num_chemotypes, embed_dim) * 0.02)
        self.target_profile_head = nn.Sequential(
            nn.Linear(embed_dim, hidden_dim),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, num_chemotypes),
        )
        feature_dim = embed_dim * 8 + 5
        self.head = make_head(feature_dim, hidden_dim, dropout)

    @staticmethod
    def _binary_entropy(prob: torch.Tensor) -> torch.Tensor:
        eps = 1e-8
        return -(prob * (prob + eps).log() + (1.0 - prob) * (1.0 - prob + eps).log()).mean(dim=-1, keepdim=True)

    def _functional_memory_forward(self, batch: Batch) -> Tuple[torch.Tensor, torch.Tensor, Dict[str, torch.Tensor]]:
        if batch.drug_cluster_weights is None:
            raise ValueError("FunctionalTargetMemoryDTI requires drug_cluster_weights in the batch")

        drug, target, drug_ctx, drug_attn, drug_entropy, top_drug_sim = self._encode_drug_neighbors(batch)
        pair_features = self.pair_features(drug, target)

        drug_cluster_weights = batch.drug_cluster_weights
        centered_drug_weights = drug_cluster_weights - self.chemotype_prior.unsqueeze(0)
        target_profile_pred = torch.tanh(self.target_profile_head(target))
        target_profile_prob = torch.clamp(self.chemotype_prior.unsqueeze(0) + target_profile_pred, min=1e-4, max=1.0 - 1e-4)

        drug_cluster_ctx = drug_cluster_weights @ self.cluster_memory
        query_preference_ctx = centered_drug_weights @ self.cluster_memory
        target_cluster_ctx = target_profile_pred @ self.cluster_memory
        functional_gap = (query_preference_ctx - target_cluster_ctx).abs()
        cluster_match = torch.sum(centered_drug_weights * target_profile_pred, dim=-1, keepdim=True)
        profile_magnitude = torch.mean(target_profile_pred.abs(), dim=-1, keepdim=True)
        profile_entropy = self._binary_entropy(target_profile_prob)

        features = torch.cat(
            [
                pair_features,
                drug_ctx,
                drug_cluster_ctx,
                target_cluster_ctx,
                functional_gap,
                drug_entropy,
                top_drug_sim,
                cluster_match,
                profile_magnitude,
                profile_entropy,
            ],
            dim=-1,
        )
        diagnostics = {
            "drug_attention": drug_attn,
            "drug_entropy": drug_entropy,
            "top_drug_sim": top_drug_sim,
            "target_profile_pred": target_profile_pred,
            "target_profile_prob": target_profile_prob,
            "cluster_match": cluster_match,
            "profile_magnitude": profile_magnitude,
            "profile_entropy": profile_entropy,
        }
        return pair_features, features, diagnostics

    def forward(self, batch: Batch) -> Tuple[torch.Tensor, Dict[str, torch.Tensor]]:
        _, features, diagnostics = self._functional_memory_forward(batch)
        logits = self.head(features).squeeze(-1)
        aux = {
            "drug_attention": diagnostics["drug_attention"],
            "drug_entropy": diagnostics["drug_entropy"].squeeze(-1),
            "top_drug_sim": diagnostics["top_drug_sim"].squeeze(-1),
            "target_profile_pred": diagnostics["target_profile_pred"],
            "target_profile_prob": diagnostics["target_profile_prob"],
            "cluster_match": diagnostics["cluster_match"].squeeze(-1),
            "profile_magnitude": diagnostics["profile_magnitude"].squeeze(-1),
            "profile_entropy": diagnostics["profile_entropy"].squeeze(-1),
        }
        return logits, aux


class RobustFunctionalTargetMemoryDTI(FunctionalTargetMemoryDTI):
    """
    Fuse a base expert and an FTM expert with reliability-aware gating.

    The gate sees overlap and target-memory confidence statistics so that the
    model can revert toward the base interaction head on hard splits where the
    functional memory becomes overconfident.
    """

    def __init__(
        self,
        drug_dim: int,
        target_dim: int,
        num_chemotypes: int,
        chemotype_prior: torch.Tensor,
        hidden_dim: int = 512,
        embed_dim: int = 256,
        stat_dim: int = 3,
        dropout: float = 0.1,
    ):
        super().__init__(
            drug_dim=drug_dim,
            target_dim=target_dim,
            num_chemotypes=num_chemotypes,
            chemotype_prior=chemotype_prior,
            hidden_dim=hidden_dim,
            embed_dim=embed_dim,
            stat_dim=stat_dim,
            dropout=dropout,
        )
        self.base_head = make_head(embed_dim * 4, hidden_dim, dropout)
        gate_hidden = max(32, hidden_dim // 4)
        self.fusion_gate = nn.Sequential(
            nn.Linear(8, gate_hidden),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(gate_hidden, 1),
        )

    def forward(self, batch: Batch) -> Tuple[torch.Tensor, Dict[str, torch.Tensor]]:
        pair_features, ftm_features, diagnostics = self._functional_memory_forward(batch)
        base_logit = self.base_head(pair_features).squeeze(-1)
        ftm_logit = self.head(ftm_features).squeeze(-1)
        overlap_score = batch.overlap_score.unsqueeze(-1) if batch.overlap_score is not None else diagnostics["top_drug_sim"]
        gate_input = torch.cat(
            [
                overlap_score,
                diagnostics["drug_entropy"],
                diagnostics["top_drug_sim"],
                diagnostics["cluster_match"],
                diagnostics["profile_magnitude"],
                diagnostics["profile_entropy"],
                base_logit.unsqueeze(-1),
                ftm_logit.unsqueeze(-1),
            ],
            dim=-1,
        )
        fusion_weight = torch.sigmoid(self.fusion_gate(gate_input))
        logits = fusion_weight.squeeze(-1) * ftm_logit + (1.0 - fusion_weight.squeeze(-1)) * base_logit
        aux = {
            "drug_attention": diagnostics["drug_attention"],
            "drug_entropy": diagnostics["drug_entropy"].squeeze(-1),
            "top_drug_sim": diagnostics["top_drug_sim"].squeeze(-1),
            "target_profile_pred": diagnostics["target_profile_pred"],
            "target_profile_prob": diagnostics["target_profile_prob"],
            "cluster_match": diagnostics["cluster_match"].squeeze(-1),
            "profile_magnitude": diagnostics["profile_magnitude"].squeeze(-1),
            "profile_entropy": diagnostics["profile_entropy"].squeeze(-1),
            "expert_logits": torch.stack([base_logit, ftm_logit], dim=1),
            "fusion_weight": fusion_weight.squeeze(-1),
        }
        return logits, aux
