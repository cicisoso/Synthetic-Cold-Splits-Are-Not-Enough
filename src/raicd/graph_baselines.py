from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

import numpy as np
import pandas as pd
import torch
from rdkit import Chem
from torch import nn
from torch.utils.data import Dataset
from torch_geometric.data import Batch as GeometricBatch
from torch_geometric.data import Data
from torch_geometric.nn import GCNConv, global_max_pool, global_mean_pool


AMINO_ACIDS = "ACDEFGHIKLMNPQRSTVWY"
AMINO_TO_INDEX = {aa: idx + 1 for idx, aa in enumerate(AMINO_ACIDS)}
ATOM_SYMBOLS = ["C", "N", "O", "S", "F", "P", "Cl", "Br", "I", "B", "Si", "Se"]
HYBRIDIZATIONS = [
    Chem.rdchem.HybridizationType.SP,
    Chem.rdchem.HybridizationType.SP2,
    Chem.rdchem.HybridizationType.SP3,
    Chem.rdchem.HybridizationType.SP3D,
    Chem.rdchem.HybridizationType.SP3D2,
]


@dataclass
class GraphPairBatch:
    graph_batch: GeometricBatch
    target_tokens: torch.Tensor
    labels: torch.Tensor
    overlap_score: torch.Tensor
    example_ids: List[str]


def _one_hot(value, choices: list) -> list[float]:
    return [1.0 if value == choice else 0.0 for choice in choices]


def atom_feature_vector(atom: Chem.Atom) -> np.ndarray:
    symbol = atom.GetSymbol()
    degree = min(int(atom.GetDegree()), 5)
    num_h = min(int(atom.GetTotalNumHs()), 4)
    formal_charge = int(atom.GetFormalCharge())
    valence = min(int(atom.GetTotalValence()), 5)
    aromatic = 1.0 if atom.GetIsAromatic() else 0.0
    hybridization = atom.GetHybridization()

    features = (
        _one_hot(symbol, ATOM_SYMBOLS) + [1.0 if symbol not in ATOM_SYMBOLS else 0.0]
        + _one_hot(degree, list(range(6)))
        + _one_hot(num_h, list(range(5)))
        + _one_hot(valence, list(range(6)))
        + [float(formal_charge), aromatic]
        + _one_hot(hybridization, HYBRIDIZATIONS)
        + [1.0 if hybridization not in HYBRIDIZATIONS else 0.0]
    )
    return np.asarray(features, dtype=np.float32)


def smiles_to_graph(smiles: str) -> Data:
    mol = Chem.MolFromSmiles(smiles)
    if mol is None or mol.GetNumAtoms() == 0:
        x = torch.zeros((1, atom_feature_dim()), dtype=torch.float32)
        edge_index = torch.zeros((2, 0), dtype=torch.long)
        return Data(x=x, edge_index=edge_index)

    node_features = [atom_feature_vector(atom) for atom in mol.GetAtoms()]
    edge_pairs: list[list[int]] = []
    for bond in mol.GetBonds():
        start = bond.GetBeginAtomIdx()
        end = bond.GetEndAtomIdx()
        edge_pairs.append([start, end])
        edge_pairs.append([end, start])
    if edge_pairs:
        edge_index = torch.tensor(edge_pairs, dtype=torch.long).t().contiguous()
    else:
        edge_index = torch.zeros((2, 0), dtype=torch.long)
    x = torch.tensor(np.stack(node_features), dtype=torch.float32)
    return Data(x=x, edge_index=edge_index)


def atom_feature_dim() -> int:
    return len(ATOM_SYMBOLS) + 1 + 6 + 5 + 6 + 2 + len(HYBRIDIZATIONS) + 1


def sequence_to_token_ids(sequence: str, max_length: int = 1000) -> np.ndarray:
    seq = "".join(ch for ch in str(sequence).upper() if ch in AMINO_TO_INDEX)[:max_length]
    tokens = np.zeros((max_length,), dtype=np.int64)
    if not seq:
        return tokens
    ids = [AMINO_TO_INDEX[ch] for ch in seq]
    tokens[: len(ids)] = np.asarray(ids, dtype=np.int64)
    return tokens


def build_drug_graphs(drugs: pd.DataFrame) -> dict[str, Data]:
    return {str(row["drug_id"]): smiles_to_graph(str(row["drug_smile"])) for _, row in drugs.iterrows()}


def build_target_tokens(targets: pd.DataFrame, max_length: int = 1000) -> dict[str, np.ndarray]:
    return {
        str(row["prot_id"]): sequence_to_token_ids(str(row["prot_seq"]), max_length=max_length)
        for _, row in targets.iterrows()
    }


class GraphPairDataset(Dataset):
    def __init__(
        self,
        frame: pd.DataFrame,
        drug_graphs: Dict[str, Data],
        target_tokens: Dict[str, np.ndarray],
    ):
        self.frame = frame.reset_index(drop=True)
        self.drug_graphs = drug_graphs
        self.target_tokens = target_tokens

    def __len__(self) -> int:
        return len(self.frame)

    def __getitem__(self, idx: int) -> dict:
        row = self.frame.iloc[idx]
        drug_id = str(row["Drug_ID"])
        target_id = str(row["Target_ID"])
        return {
            "graph": self.drug_graphs[drug_id].clone(),
            "target_tokens": self.target_tokens[target_id].copy(),
            "label": np.float32(row["label"]),
            "overlap_score": np.float32(row["overlap_score"]),
            "example_id": str(row["example_id"]),
        }


def collate_graph_pairs(items: List[dict]) -> GraphPairBatch:
    graph_batch = GeometricBatch.from_data_list([item["graph"] for item in items])
    target_tokens = torch.from_numpy(np.stack([item["target_tokens"] for item in items]).astype(np.int64))
    labels = torch.from_numpy(np.asarray([item["label"] for item in items], dtype=np.float32))
    overlap_score = torch.from_numpy(np.asarray([item["overlap_score"] for item in items], dtype=np.float32))
    example_ids = [str(item["example_id"]) for item in items]
    return GraphPairBatch(
        graph_batch=graph_batch,
        target_tokens=target_tokens,
        labels=labels,
        overlap_score=overlap_score,
        example_ids=example_ids,
    )


class ProteinCNN(nn.Module):
    def __init__(self, vocab_size: int, embed_dim: int = 64, hidden_dim: int = 128, dropout: float = 0.1):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, embed_dim, padding_idx=0)
        self.conv1 = nn.Conv1d(embed_dim, hidden_dim, kernel_size=8, padding=4)
        self.conv2 = nn.Conv1d(hidden_dim, hidden_dim, kernel_size=8, padding=4)
        self.conv3 = nn.Conv1d(hidden_dim, hidden_dim, kernel_size=8, padding=4)
        self.dropout = nn.Dropout(dropout)
        self.act = nn.ReLU()

    def forward(self, tokens: torch.Tensor, return_sequence: bool = False) -> torch.Tensor:
        x = self.embedding(tokens).transpose(1, 2)
        x = self.dropout(self.act(self.conv1(x)))
        x = self.dropout(self.act(self.conv2(x)))
        x = self.dropout(self.act(self.conv3(x)))
        if return_sequence:
            return x.transpose(1, 2)  # (B, L, hidden_dim)
        x = torch.max(x, dim=-1).values
        return x


class DrugGCN(nn.Module):
    def __init__(self, in_dim: int, hidden_dim: int = 128, out_dim: int = 128, dropout: float = 0.1):
        super().__init__()
        self.conv1 = GCNConv(in_dim, hidden_dim)
        self.conv2 = GCNConv(hidden_dim, hidden_dim)
        self.conv3 = GCNConv(hidden_dim, out_dim)
        self.dropout = nn.Dropout(dropout)
        self.act = nn.ReLU()

    def forward(self, batch: GeometricBatch, return_node_features: bool = False) -> torch.Tensor:
        x, edge_index, graph_index = batch.x, batch.edge_index, batch.batch
        x = self.dropout(self.act(self.conv1(x, edge_index)))
        x = self.dropout(self.act(self.conv2(x, edge_index)))
        x = self.dropout(self.act(self.conv3(x, edge_index)))
        if return_node_features:
            return x, graph_index
        pooled_mean = global_mean_pool(x, graph_index)
        pooled_max = global_max_pool(x, graph_index)
        return torch.cat([pooled_mean, pooled_max], dim=-1)


class GraphDTALite(nn.Module):
    def __init__(
        self,
        atom_dim: int,
        protein_vocab_size: int,
        graph_hidden_dim: int = 128,
        graph_out_dim: int = 128,
        protein_embed_dim: int = 64,
        protein_hidden_dim: int = 128,
        pair_hidden_dim: int = 256,
        dropout: float = 0.1,
    ):
        super().__init__()
        self.drug_encoder = DrugGCN(
            in_dim=atom_dim,
            hidden_dim=graph_hidden_dim,
            out_dim=graph_out_dim,
            dropout=dropout,
        )
        self.target_encoder = ProteinCNN(
            vocab_size=protein_vocab_size,
            embed_dim=protein_embed_dim,
            hidden_dim=protein_hidden_dim,
            dropout=dropout,
        )
        pair_dim = graph_out_dim * 2 + protein_hidden_dim
        self.head = nn.Sequential(
            nn.Linear(pair_dim, pair_hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(pair_hidden_dim, pair_hidden_dim // 2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(pair_hidden_dim // 2, 1),
        )

    def forward(self, graph_batch: GeometricBatch, target_tokens: torch.Tensor) -> tuple[torch.Tensor, dict]:
        drug_embed = self.drug_encoder(graph_batch)
        target_embed = self.target_encoder(target_tokens)
        logits = self.head(torch.cat([drug_embed, target_embed], dim=-1)).squeeze(-1)
        aux = {
            "drug_embed_norm_mean": float(drug_embed.norm(dim=-1).mean().detach().cpu()),
            "target_embed_norm_mean": float(target_embed.norm(dim=-1).mean().detach().cpu()),
        }
        return logits, aux


class BilinearAttention(nn.Module):
    """Bilinear attention module inspired by DrugBAN (Bai et al., Nature MI 2023).

    Computes pairwise attention between drug atom features and protein residue
    features via a learned bilinear mapping, then pools the attended interaction
    into a fixed-size vector.
    """

    def __init__(self, drug_dim: int, target_dim: int, hidden_dim: int = 128, n_heads: int = 2, dropout: float = 0.1):
        super().__init__()
        self.n_heads = n_heads
        self.head_dim = hidden_dim // n_heads
        self.drug_proj = nn.Linear(drug_dim, hidden_dim)
        self.target_proj = nn.Linear(target_dim, hidden_dim)
        self.bilinear_weights = nn.Parameter(torch.randn(n_heads, self.head_dim, self.head_dim) * 0.02)
        self.out_proj = nn.Linear(n_heads, n_heads)
        self.pool_drug = nn.Linear(hidden_dim, hidden_dim)
        self.pool_target = nn.Linear(hidden_dim, hidden_dim)
        self.dropout = nn.Dropout(dropout)

    def forward(
        self,
        drug_nodes: torch.Tensor,
        drug_mask: torch.Tensor,
        target_seq: torch.Tensor,
        target_mask: torch.Tensor,
    ) -> torch.Tensor:
        """
        Args:
            drug_nodes: (B, N_atoms, drug_dim) padded atom features
            drug_mask: (B, N_atoms) bool mask (True = valid)
            target_seq: (B, L, target_dim) per-residue features
            target_mask: (B, L) bool mask (True = valid)
        Returns:
            interaction: (B, n_heads * 2) pooled interaction vector
        """
        B = drug_nodes.size(0)
        # project to hidden
        d = self.drug_proj(drug_nodes)   # (B, N, H)
        t = self.target_proj(target_seq) # (B, L, H)

        # reshape for multi-head: (B, N, n_heads, head_dim)
        d_heads = d.view(B, -1, self.n_heads, self.head_dim)
        t_heads = t.view(B, -1, self.n_heads, self.head_dim)

        # bilinear attention: for each head h, A_h[i,j] = d_i^T W_h t_j
        # d_heads: (B, N, n_heads, hd) -> (n_heads, B, N, hd)
        dh = d_heads.permute(2, 0, 1, 3)  # (n_heads, B, N, hd)
        th = t_heads.permute(2, 0, 1, 3)  # (n_heads, B, L, hd)
        # dh @ W @ th^T => (n_heads, B, N, L)
        dW = torch.einsum("hbnd,hde->hbne", dh, self.bilinear_weights)
        attn = torch.einsum("hbne,hble->hbnl", dW, th)  # (n_heads, B, N, L)

        # mask invalid positions: need (1, B, N, L)
        dm = drug_mask.unsqueeze(-1)   # (B, N, 1)
        tm = target_mask.unsqueeze(1)  # (B, 1, L)
        mask = (dm & tm).unsqueeze(0)  # (1, B, N, L)
        attn = attn.masked_fill(~mask, float("-inf"))

        # softmax over target dim for drug-attended-by-target
        attn_d = torch.softmax(attn, dim=-1)  # (n_heads, B, N, L)
        attn_d = attn_d.masked_fill(~mask, 0.0)
        attn_d = self.dropout(attn_d)

        # pool: attention-weighted sum over targets for each drug node, then mean over drug nodes
        # (n_heads, B, N, L) x (n_heads, B, L, hd) -> (n_heads, B, N, hd)
        ctx_d = torch.einsum("hbnl,hble->hbne", attn_d, th)
        # mask and mean-pool over drug nodes
        dm_flat = drug_mask.unsqueeze(0).unsqueeze(-1)  # (1, B, N, 1)
        ctx_d = (ctx_d * dm_flat).sum(dim=2) / dm_flat.sum(dim=2).clamp(min=1)  # (n_heads, B, hd)
        ctx_d = ctx_d.permute(1, 0, 2).reshape(B, -1)  # (B, n_heads * hd)

        # softmax over drug dim for target-attended-by-drug
        attn_t = torch.softmax(attn, dim=-2)  # (n_heads, B, N, L)
        attn_t = attn_t.masked_fill(~mask, 0.0)
        attn_t = self.dropout(attn_t)

        # (n_heads, B, N, L)^T x (n_heads, B, N, hd) -> (n_heads, B, L, hd)
        ctx_t = torch.einsum("hbnl,hbne->hble", attn_t, dh)
        tm_flat = target_mask.unsqueeze(0).unsqueeze(-1)  # (1, B, L, 1)
        ctx_t = (ctx_t * tm_flat).sum(dim=2) / tm_flat.sum(dim=2).clamp(min=1)  # (n_heads, B, hd)
        ctx_t = ctx_t.permute(1, 0, 2).reshape(B, -1)  # (B, n_heads * hd)

        return torch.cat([ctx_d, ctx_t], dim=-1)  # (B, 2 * n_heads * hd)


class DrugBANLite(nn.Module):
    """Simplified DrugBAN with bilinear attention (Bai et al., Nature MI 2023).

    Uses the same GCN drug encoder and CNN protein encoder as GraphDTALite,
    but replaces global-pool + concatenation with bilinear cross-attention
    between atom-level and residue-level features.
    """

    def __init__(
        self,
        atom_dim: int,
        protein_vocab_size: int,
        graph_hidden_dim: int = 128,
        graph_out_dim: int = 128,
        protein_embed_dim: int = 64,
        protein_hidden_dim: int = 128,
        ban_hidden_dim: int = 128,
        ban_n_heads: int = 2,
        pair_hidden_dim: int = 256,
        dropout: float = 0.1,
    ):
        super().__init__()
        self.drug_encoder = DrugGCN(
            in_dim=atom_dim,
            hidden_dim=graph_hidden_dim,
            out_dim=graph_out_dim,
            dropout=dropout,
        )
        self.target_encoder = ProteinCNN(
            vocab_size=protein_vocab_size,
            embed_dim=protein_embed_dim,
            hidden_dim=protein_hidden_dim,
            dropout=dropout,
        )
        self.ban = BilinearAttention(
            drug_dim=graph_out_dim,
            target_dim=protein_hidden_dim,
            hidden_dim=ban_hidden_dim,
            n_heads=ban_n_heads,
            dropout=dropout,
        )
        # BAN outputs 2 * n_heads * (ban_hidden_dim // n_heads) = 2 * ban_hidden_dim
        ban_out_dim = 2 * ban_hidden_dim
        self.head = nn.Sequential(
            nn.Linear(ban_out_dim, pair_hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(pair_hidden_dim, pair_hidden_dim // 2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(pair_hidden_dim // 2, 1),
        )

    def forward(self, graph_batch: GeometricBatch, target_tokens: torch.Tensor) -> tuple[torch.Tensor, dict]:
        B = target_tokens.size(0)

        # Get per-atom features from GCN
        node_feats, graph_index = self.drug_encoder(graph_batch, return_node_features=True)
        # node_feats: (total_atoms, out_dim), graph_index: (total_atoms,)

        # Pad atom features to (B, max_atoms, out_dim)
        max_atoms = 0
        atom_counts = []
        for i in range(B):
            count = int((graph_index == i).sum())
            atom_counts.append(count)
            if count > max_atoms:
                max_atoms = count
        max_atoms = max(max_atoms, 1)

        drug_nodes = torch.zeros(B, max_atoms, node_feats.size(-1), device=node_feats.device)
        drug_mask = torch.zeros(B, max_atoms, dtype=torch.bool, device=node_feats.device)
        for i in range(B):
            idx = (graph_index == i)
            n = atom_counts[i]
            if n > 0:
                drug_nodes[i, :n] = node_feats[idx]
                drug_mask[i, :n] = True

        # Get per-residue features from CNN
        target_seq = self.target_encoder(target_tokens, return_sequence=True)  # (B, L', hidden)
        # CNN with padding may change sequence length; align mask to CNN output
        L_out = target_seq.size(1)
        L_in = target_tokens.size(1)
        if L_out != L_in:
            target_mask = torch.nn.functional.pad(target_tokens > 0, (0, L_out - L_in), value=False)
        else:
            target_mask = target_tokens > 0  # (B, L)

        # Bilinear cross-attention
        interaction = self.ban(drug_nodes, drug_mask, target_seq, target_mask)

        logits = self.head(interaction).squeeze(-1)
        aux = {
            "drug_atoms_mean": float(np.mean(atom_counts)),
            "target_len_mean": float(target_mask.sum(dim=-1).float().mean().detach().cpu()),
        }
        return logits, aux


class ColdstartCPILite(nn.Module):
    """Simplified ColdstartCPI (Zhao et al., Nature Communications 2025).

    Faithful reimplementation of the core architecture: per-atom drug features
    and per-residue protein features are concatenated with learnable global
    tokens and processed by a Transformer self-attention layer.
    Architecturally distinct from DrugBAN (bilinear attention) and GraphDTA
    (global-pool + MLP): self-attention enables implicit cross-entity
    interactions without explicit pairwise scoring.
    """

    def __init__(
        self,
        atom_dim: int,
        protein_vocab_size: int,
        graph_hidden_dim: int = 128,
        graph_out_dim: int = 128,
        protein_embed_dim: int = 64,
        protein_hidden_dim: int = 128,
        unify_dim: int = 128,
        n_heads: int = 2,
        pair_hidden_dim: int = 256,
        dropout: float = 0.1,
        max_drug_atoms: int = 100,
        max_protein_len: int = 200,
    ):
        super().__init__()
        self.max_drug_atoms = max_drug_atoms
        self.max_protein_len = max_protein_len
        self.unify_dim = unify_dim

        # Encoders (same as GraphDTA/DrugBAN)
        self.drug_encoder = DrugGCN(
            in_dim=atom_dim,
            hidden_dim=graph_hidden_dim,
            out_dim=graph_out_dim,
            dropout=dropout,
        )
        self.target_encoder = ProteinCNN(
            vocab_size=protein_vocab_size,
            embed_dim=protein_embed_dim,
            hidden_dim=protein_hidden_dim,
            dropout=dropout,
        )

        # Projection to unified dimension (like ColdstartCPI's c_m_unit / p_m_unit)
        self.drug_proj = nn.Sequential(
            nn.Linear(graph_out_dim, unify_dim), nn.PReLU(),
            nn.Linear(unify_dim, unify_dim), nn.PReLU(),
        )
        self.target_proj = nn.Sequential(
            nn.Linear(protein_hidden_dim, unify_dim), nn.PReLU(),
            nn.Linear(unify_dim, unify_dim), nn.PReLU(),
        )

        # Learnable global tokens (CLS-style for drug and protein)
        self.drug_global_token = nn.Parameter(torch.randn(1, 1, unify_dim) * 0.02)
        self.prot_global_token = nn.Parameter(torch.randn(1, 1, unify_dim) * 0.02)

        # Transformer self-attention (single layer, like ColdstartCPI)
        self.transformer = nn.TransformerEncoderLayer(
            d_model=unify_dim,
            nhead=n_heads,
            dim_feedforward=unify_dim * 4,
            dropout=dropout,
            batch_first=True,
        )

        # Classification head
        self.head = nn.Sequential(
            nn.Linear(unify_dim * 2, pair_hidden_dim),
            nn.PReLU(),
            nn.Dropout(dropout),
            nn.Linear(pair_hidden_dim, pair_hidden_dim // 2),
            nn.PReLU(),
            nn.Dropout(dropout),
            nn.Linear(pair_hidden_dim // 2, 1),
        )

    def forward(self, graph_batch: GeometricBatch, target_tokens: torch.Tensor) -> tuple[torch.Tensor, dict]:
        B = target_tokens.size(0)
        device = target_tokens.device

        # --- Per-atom drug features ---
        node_feats, graph_index = self.drug_encoder(graph_batch, return_node_features=True)

        # Pad to (B, max_drug_atoms, out_dim)
        drug_tokens_list = []
        drug_lens = []
        for i in range(B):
            idx = (graph_index == i)
            feats = node_feats[idx][:self.max_drug_atoms]
            n = feats.size(0)
            drug_lens.append(n)
            if n < self.max_drug_atoms:
                pad = torch.zeros(self.max_drug_atoms - n, feats.size(-1), device=device)
                feats = torch.cat([feats, pad], dim=0)
            drug_tokens_list.append(feats)
        drug_atoms = torch.stack(drug_tokens_list)  # (B, max_drug, out_dim)
        drug_atoms = self.drug_proj(drug_atoms)  # (B, max_drug, unify)

        # --- Per-residue protein features ---
        target_seq = self.target_encoder(target_tokens, return_sequence=True)  # (B, L', hidden)
        target_seq = target_seq[:, :self.max_protein_len, :]  # truncate
        L = target_seq.size(1)
        target_seq = self.target_proj(target_seq)  # (B, L, unify)

        # --- Construct sequence: [drug_global, drug_atoms..., prot_global, prot_residues...] ---
        drug_g = self.drug_global_token.expand(B, -1, -1)  # (B, 1, unify)
        prot_g = self.prot_global_token.expand(B, -1, -1)  # (B, 1, unify)

        sequence = torch.cat([drug_g, drug_atoms, prot_g, target_seq], dim=1)
        # shape: (B, 1 + max_drug + 1 + L, unify)

        # --- Padding mask ---
        # drug_global is always valid (1), drug atoms have variable length, prot_global always valid (1)
        drug_mask = torch.zeros(B, self.max_drug_atoms, dtype=torch.bool, device=device)
        for i in range(B):
            drug_mask[i, :drug_lens[i]] = True
        prot_mask = (target_tokens[:, :self.max_protein_len] > 0) if self.max_protein_len <= target_tokens.size(1) else torch.ones(B, L, dtype=torch.bool, device=device)

        # CNN may change length; ensure prot_mask matches
        if prot_mask.size(1) != L:
            prot_mask = prot_mask[:, :L]

        global_true = torch.ones(B, 1, dtype=torch.bool, device=device)
        pad_mask = torch.cat([global_true, drug_mask, global_true, prot_mask], dim=1)
        # TransformerEncoderLayer expects src_key_padding_mask: True = IGNORE
        src_key_padding_mask = ~pad_mask

        # --- Transformer ---
        out = self.transformer(sequence, src_key_padding_mask=src_key_padding_mask)

        # Extract global tokens
        drug_global_out = out[:, 0, :]  # (B, unify)
        prot_global_idx = 1 + self.max_drug_atoms
        prot_global_out = out[:, prot_global_idx, :]  # (B, unify)

        # --- Classification ---
        combined = torch.cat([drug_global_out, prot_global_out], dim=-1)  # (B, 2*unify)
        logits = self.head(combined).squeeze(-1)

        aux = {
            "drug_atoms_mean": float(np.mean(drug_lens)),
            "target_len_mean": float(L),
        }
        return logits, aux
