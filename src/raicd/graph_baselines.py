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

    def forward(self, tokens: torch.Tensor) -> torch.Tensor:
        x = self.embedding(tokens).transpose(1, 2)
        x = self.dropout(self.act(self.conv1(x)))
        x = self.dropout(self.act(self.conv2(x)))
        x = self.dropout(self.act(self.conv3(x)))
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

    def forward(self, batch: GeometricBatch) -> torch.Tensor:
        x, edge_index, graph_index = batch.x, batch.edge_index, batch.batch
        x = self.dropout(self.act(self.conv1(x, edge_index)))
        x = self.dropout(self.act(self.conv2(x, edge_index)))
        x = self.dropout(self.act(self.conv3(x, edge_index)))
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
