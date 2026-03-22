from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

import numpy as np
import pandas as pd
import torch
from torch import nn
from torch.utils.data import Dataset


@dataclass
class PairBatch:
    drug_x: torch.Tensor
    target_x: torch.Tensor
    labels: torch.Tensor
    overlap_score: torch.Tensor
    example_ids: List[str]


class PairFeatureDataset(Dataset):
    def __init__(
        self,
        frame: pd.DataFrame,
        drug_lookup: Dict[str, int],
        target_lookup: Dict[str, int],
        drug_embeddings: np.ndarray,
        target_embeddings: np.ndarray,
    ):
        self.frame = frame.reset_index(drop=True)
        self.drug_lookup = drug_lookup
        self.target_lookup = target_lookup
        self.drug_embeddings = drug_embeddings
        self.target_embeddings = target_embeddings

    def __len__(self) -> int:
        return len(self.frame)

    def __getitem__(self, idx: int) -> Dict[str, np.ndarray | str]:
        row = self.frame.iloc[idx]
        drug_idx = self.drug_lookup[str(row["Drug_ID"])]
        target_idx = self.target_lookup[str(row["Target_ID"])]
        return {
            "drug_x": self.drug_embeddings[drug_idx],
            "target_x": self.target_embeddings[target_idx],
            "label": np.float32(row["label"]),
            "overlap_score": np.float32(row["overlap_score"]),
            "example_id": str(row["example_id"]),
        }


def collate_pair_features(items: List[Dict[str, np.ndarray | str]]) -> PairBatch:
    drug_x = torch.from_numpy(np.stack([item["drug_x"] for item in items]).astype(np.float32))
    target_x = torch.from_numpy(np.stack([item["target_x"] for item in items]).astype(np.float32))
    labels = torch.from_numpy(np.asarray([item["label"] for item in items], dtype=np.float32))
    overlap_score = torch.from_numpy(np.asarray([item["overlap_score"] for item in items], dtype=np.float32))
    example_ids = [str(item["example_id"]) for item in items]
    return PairBatch(
        drug_x=drug_x,
        target_x=target_x,
        labels=labels,
        overlap_score=overlap_score,
        example_ids=example_ids,
    )


class DTILMAdapter(nn.Module):
    def __init__(self, drug_dim: int, target_dim: int, hidden_dim: int = 512, dropout: float = 0.1):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(drug_dim + target_dim, hidden_dim),
            nn.BatchNorm1d(hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.BatchNorm1d(hidden_dim // 2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim // 2, 1),
        )

    def forward(self, drug_x: torch.Tensor, target_x: torch.Tensor) -> tuple[torch.Tensor, dict]:
        logits = self.net(torch.cat([drug_x, target_x], dim=-1)).squeeze(-1)
        return logits, {}


class HyperPCMAdapter(nn.Module):
    def __init__(
        self,
        drug_dim: int,
        target_dim: int,
        drug_hidden_dim: int = 256,
        target_hidden_dim: int = 256,
        hyper_hidden_dim: int = 256,
        dropout: float = 0.1,
    ):
        super().__init__()
        self.drug_encoder = nn.Sequential(
            nn.Linear(drug_dim, drug_hidden_dim),
            nn.LayerNorm(drug_hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
        )
        self.target_encoder = nn.Sequential(
            nn.Linear(target_dim, target_hidden_dim),
            nn.LayerNorm(target_hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
        )
        self.hyper = nn.Sequential(
            nn.Linear(target_hidden_dim, hyper_hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
        )
        self.gamma_head = nn.Linear(hyper_hidden_dim, drug_hidden_dim)
        self.beta_head = nn.Linear(hyper_hidden_dim, drug_hidden_dim)
        self.weight_head = nn.Linear(hyper_hidden_dim, drug_hidden_dim)
        self.bias_head = nn.Linear(hyper_hidden_dim, 1)

    def forward(self, drug_x: torch.Tensor, target_x: torch.Tensor) -> tuple[torch.Tensor, dict]:
        drug_hidden = self.drug_encoder(drug_x)
        target_hidden = self.target_encoder(target_x)
        hyper_hidden = self.hyper(target_hidden)
        gamma = self.gamma_head(hyper_hidden)
        beta = self.beta_head(hyper_hidden)
        weight = self.weight_head(hyper_hidden)
        conditioned = torch.relu(drug_hidden * (1.0 + gamma) + beta)
        logits = torch.sum(conditioned * weight, dim=-1) + self.bias_head(hyper_hidden).squeeze(-1)
        aux = {
            "gamma_mean": float(gamma.mean().detach().cpu()),
            "beta_mean": float(beta.mean().detach().cpu()),
            "weight_norm_mean": float(weight.norm(dim=-1).mean().detach().cpu()),
        }
        return logits, aux
