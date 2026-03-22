#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

from raicd.metrics import binary_metrics, stratified_overlap_metrics


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train a sample-adaptive router on frozen expert predictions.")
    parser.add_argument("--expert", action="append", required=True, help="Format: name=/path/to/result.json")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--epochs", type=int, default=200)
    parser.add_argument("--lr", type=float, default=1e-2)
    parser.add_argument("--weight-decay", type=float, default=1e-4)
    parser.add_argument("--hidden-dim", type=int, default=64)
    parser.add_argument("--dropout", type=float, default=0.1)
    parser.add_argument("--val-frac", type=float, default=0.2)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def to_logit(p: np.ndarray) -> np.ndarray:
    p = np.clip(p, 1e-6, 1.0 - 1e-6)
    return np.log(p / (1.0 - p))


def load_experts(specs: list[str]) -> tuple[list[str], dict]:
    names = []
    records = {}
    for spec in specs:
        name, path = spec.split("=", 1)
        data = json.loads(Path(path).read_text())
        names.append(name)
        records[name] = data
    return names, records


def stack_split(records: dict, names: list[str], split_key: str) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    labels = None
    overlap = None
    probs = []
    for name in names:
        pred = records[name][split_key]
        current_labels = np.asarray(pred["labels"], dtype=np.int64)
        current_overlap = np.asarray(pred["overlap_score"], dtype=np.float32)
        current_prob = np.asarray(pred["probabilities"], dtype=np.float32)
        if labels is None:
            labels = current_labels
            overlap = current_overlap
        else:
            if not np.array_equal(labels, current_labels):
                raise ValueError(f"Label mismatch for expert {name} on {split_key}")
            if not np.allclose(overlap, current_overlap):
                raise ValueError(f"Overlap mismatch for expert {name} on {split_key}")
        probs.append(current_prob)
    return labels, overlap, np.stack(probs, axis=1)


def build_features(prob: np.ndarray, overlap: np.ndarray) -> np.ndarray:
    logit = to_logit(prob)
    top1 = np.max(prob, axis=1, keepdims=True)
    sorted_prob = np.sort(prob, axis=1)
    margin = sorted_prob[:, -1:] - sorted_prob[:, -2:-1] if prob.shape[1] > 1 else top1
    mean_prob = np.mean(prob, axis=1, keepdims=True)
    std_prob = np.std(prob, axis=1, keepdims=True)
    overlap = overlap.reshape(-1, 1)
    return np.concatenate([prob, logit, top1, margin, mean_prob, std_prob, overlap], axis=1).astype(np.float32)


class MetaRouter(nn.Module):
    def __init__(self, input_dim: int, num_experts: int, hidden_dim: int, dropout: float):
        super().__init__()
        self.router = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, num_experts),
        )

    def forward(self, features: torch.Tensor, expert_logits: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        route_logits = self.router(features)
        route_weights = F.softmax(route_logits, dim=-1)
        fused_logit = torch.sum(route_weights * expert_logits, dim=-1)
        return fused_logit, route_weights


def fit_router(
    x_train: np.ndarray,
    y_train: np.ndarray,
    expert_logits_train: np.ndarray,
    x_val: np.ndarray,
    y_val: np.ndarray,
    expert_logits_val: np.ndarray,
    args: argparse.Namespace,
) -> MetaRouter:
    torch.manual_seed(args.seed)
    model = MetaRouter(x_train.shape[1], expert_logits_train.shape[1], args.hidden_dim, args.dropout)
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=args.weight_decay)
    criterion = nn.BCEWithLogitsLoss()

    x_train_t = torch.from_numpy(x_train)
    y_train_t = torch.from_numpy(y_train.astype(np.float32))
    expert_train_t = torch.from_numpy(expert_logits_train.astype(np.float32))
    x_val_t = torch.from_numpy(x_val)
    y_val_t = torch.from_numpy(y_val.astype(np.float32))
    expert_val_t = torch.from_numpy(expert_logits_val.astype(np.float32))

    best_state = None
    best_val = -1.0
    for _ in range(args.epochs):
        model.train()
        fused, _ = model(x_train_t, expert_train_t)
        loss = criterion(fused, y_train_t)
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        model.eval()
        with torch.no_grad():
            val_logits, _ = model(x_val_t, expert_val_t)
            val_prob = torch.sigmoid(val_logits).cpu().numpy()
            val_metrics = binary_metrics(y_val, val_prob)
        if val_metrics["auprc"] > best_val:
            best_val = val_metrics["auprc"]
            best_state = {k: v.detach().cpu() for k, v in model.state_dict().items()}

    if best_state is not None:
        model.load_state_dict(best_state)
    return model


def evaluate_router(model: MetaRouter, features: np.ndarray, labels: np.ndarray, expert_logits: np.ndarray, overlap: np.ndarray, expert_names: list[str]) -> tuple[dict, dict]:
    model.eval()
    with torch.no_grad():
        fused_logits, route_weights = model(torch.from_numpy(features), torch.from_numpy(expert_logits.astype(np.float32)))
        prob = torch.sigmoid(fused_logits).cpu().numpy()
        route = route_weights.cpu().numpy()
    metrics = binary_metrics(labels, prob)
    metrics["overlap_buckets"] = stratified_overlap_metrics(labels, prob, overlap)
    metrics["route_weight_mean"] = route.mean(axis=0).tolist()
    metrics["route_hard_assignment"] = (np.bincount(route.argmax(axis=1), minlength=len(expert_names)) / len(route)).tolist()
    metrics["route_expert_names"] = expert_names
    extras = {
        "labels": labels.tolist(),
        "probabilities": prob.tolist(),
        "overlap_score": overlap.tolist(),
        "route_weights": route.tolist(),
        "expert_logits": expert_logits.tolist(),
    }
    return metrics, extras


def main() -> None:
    args = parse_args()
    np.random.seed(args.seed)

    expert_names, records = load_experts(args.expert)
    valid_labels, valid_overlap, valid_prob = stack_split(records, expert_names, "valid_predictions")
    test_labels, test_overlap, test_prob = stack_split(records, expert_names, "test_predictions")

    valid_features = build_features(valid_prob, valid_overlap)
    test_features = build_features(test_prob, test_overlap)
    valid_logits = to_logit(valid_prob).astype(np.float32)
    test_logits = to_logit(test_prob).astype(np.float32)

    indices = np.arange(len(valid_labels))
    np.random.shuffle(indices)
    split_at = int(len(indices) * (1.0 - args.val_frac))
    train_idx = indices[:split_at]
    inner_val_idx = indices[split_at:]

    router = fit_router(
        valid_features[train_idx],
        valid_labels[train_idx],
        valid_logits[train_idx],
        valid_features[inner_val_idx],
        valid_labels[inner_val_idx],
        valid_logits[inner_val_idx],
        args,
    )

    valid_metrics, valid_extras = evaluate_router(router, valid_features, valid_labels, valid_logits, valid_overlap, expert_names)
    test_metrics, test_extras = evaluate_router(router, test_features, test_labels, test_logits, test_overlap, expert_names)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(
            {
                "experts": expert_names,
                "args": vars(args),
                "valid_metrics": valid_metrics,
                "test_metrics": test_metrics,
                "valid_predictions": valid_extras,
                "test_predictions": test_extras,
            },
            indent=2,
            default=str,
        )
    )
    print(json.dumps({"saved_to": str(args.output), "test_auprc": test_metrics["auprc"], "test_auroc": test_metrics["auroc"], "route_weight_mean": test_metrics["route_weight_mean"]}), flush=True)


if __name__ == "__main__":
    main()
