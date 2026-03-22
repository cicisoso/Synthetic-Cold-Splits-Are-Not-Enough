#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import torch
from torch.utils.data import DataLoader

from raicd.data import InteractionDataset, collate_batch, prepare_split_artifacts
from raicd.metrics import binary_metrics, stratified_overlap_metrics
from raicd.model import BaseDTI, Batch, FunctionalTargetMemoryDTI


FEATURE_NAMES = ["profile_magnitude", "profile_entropy", "cluster_match", "overlap"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate a low-variance selective fallback between base and FTM.")
    parser.add_argument("--dataset", type=str, default="BindingDB_Kd")
    parser.add_argument("--split", type=str, default="unseen_target", choices=["warm", "unseen_drug", "unseen_target", "blind_start"])
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--base-ckpt", type=Path, required=True)
    parser.add_argument("--ftm-ckpt", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--batch-size", type=int, default=256)
    parser.add_argument("--drug-bits", type=int, default=2048)
    parser.add_argument("--drug-radius", type=int, default=2)
    parser.add_argument("--target-dim", type=int, default=2048)
    parser.add_argument("--pkd-threshold", type=float, default=7.0)
    parser.add_argument("--topk", type=int, default=8)
    parser.add_argument("--num-chemotypes", type=int, default=32)
    parser.add_argument("--chemotype-topk", type=int, default=4)
    parser.add_argument("--profile-shrinkage", type=float, default=8.0)
    parser.add_argument("--hidden-dim", type=int, default=512)
    parser.add_argument("--embed-dim", type=int, default=256)
    parser.add_argument("--dropout", type=float, default=0.1)
    parser.add_argument("--frac", type=float, nargs=3, default=[0.7, 0.1, 0.2])
    parser.add_argument("--cache-dir", type=Path, default=Path("data/cache"))
    parser.add_argument("--device", type=str, default="cuda" if torch.cuda.is_available() else "cpu")
    return parser.parse_args()


def move_batch(batch: dict, device: torch.device) -> Batch:
    return Batch(
        drug_x=batch["drug_x"].to(device),
        target_x=batch["target_x"].to(device),
        drug_neighbors=batch["drug_neighbors"].to(device),
        target_neighbors=batch["target_neighbors"].to(device),
        drug_neighbor_stats=batch["drug_neighbor_stats"].to(device),
        target_neighbor_stats=batch["target_neighbor_stats"].to(device),
        labels=batch["label"].to(device),
        drug_cluster_weights=batch.get("drug_cluster_weights", None).to(device) if "drug_cluster_weights" in batch else None,
        target_cluster_profile=batch.get("target_cluster_profile", None).to(device) if "target_cluster_profile" in batch else None,
        target_cluster_mask=batch.get("target_cluster_mask", None).to(device) if "target_cluster_mask" in batch else None,
        overlap_score=batch.get("overlap_score", None).to(device) if "overlap_score" in batch else None,
    )


@torch.no_grad()
def collect_split(
    loader: DataLoader,
    device: torch.device,
    base_model: BaseDTI,
    ftm_model: FunctionalTargetMemoryDTI,
) -> dict[str, np.ndarray]:
    labels = []
    overlap = []
    base_prob = []
    ftm_prob = []
    profile_magnitude = []
    profile_entropy = []
    cluster_match = []

    for batch in loader:
        move = move_batch(batch, device)
        base_logits, _ = base_model(move)
        ftm_logits, aux = ftm_model(move)
        labels.append(batch["label"].numpy().astype(int))
        overlap.append(batch["overlap_score"].numpy())
        base_prob.append(torch.sigmoid(base_logits).cpu().numpy())
        ftm_prob.append(torch.sigmoid(ftm_logits).cpu().numpy())
        profile_magnitude.append(aux["profile_magnitude"].detach().cpu().numpy())
        profile_entropy.append(aux["profile_entropy"].detach().cpu().numpy())
        cluster_match.append(aux["cluster_match"].detach().cpu().numpy())

    return {
        "labels": np.concatenate(labels),
        "overlap": np.concatenate(overlap),
        "base_prob": np.concatenate(base_prob),
        "ftm_prob": np.concatenate(ftm_prob),
        "profile_magnitude": np.concatenate(profile_magnitude),
        "profile_entropy": np.concatenate(profile_entropy),
        "cluster_match": np.concatenate(cluster_match),
    }


def blend_prob(base_prob: np.ndarray, ftm_prob: np.ndarray, alpha: float) -> np.ndarray:
    return (1.0 - alpha) * base_prob + alpha * ftm_prob


def evaluate_rule(data: dict[str, np.ndarray], feature_name: str, threshold: float, low_alpha: float, high_alpha: float) -> tuple[dict, np.ndarray, np.ndarray]:
    feature = data[feature_name]
    low_mask = feature <= threshold
    prob = np.empty_like(data["base_prob"])
    prob[low_mask] = blend_prob(data["base_prob"][low_mask], data["ftm_prob"][low_mask], low_alpha)
    prob[~low_mask] = blend_prob(data["base_prob"][~low_mask], data["ftm_prob"][~low_mask], high_alpha)
    metrics = binary_metrics(data["labels"], prob)
    metrics["overlap_buckets"] = stratified_overlap_metrics(data["labels"], prob, data["overlap"])
    metrics["ftm_weight_mean"] = float(np.mean(np.where(low_mask, low_alpha, high_alpha)))
    metrics["low_region_fraction"] = float(np.mean(low_mask))
    return metrics, prob, low_mask


def search_rule(valid: dict[str, np.ndarray]) -> dict:
    alpha_grid = [0.0, 0.25, 0.5, 0.75, 1.0]
    quantile_grid = [0.1, 0.25, 0.5, 0.75, 0.9]
    best = None
    for feature_name in FEATURE_NAMES:
        values = valid[feature_name]
        for q in quantile_grid:
            threshold = float(np.quantile(values, q))
            for low_alpha in alpha_grid:
                for high_alpha in alpha_grid:
                    metrics, _, low_mask = evaluate_rule(valid, feature_name, threshold, low_alpha, high_alpha)
                    candidate = {
                        "feature": feature_name,
                        "quantile": q,
                        "threshold": threshold,
                        "low_alpha": low_alpha,
                        "high_alpha": high_alpha,
                        "valid_auprc": metrics["auprc"],
                        "valid_auroc": metrics["auroc"],
                        "low_region_fraction": float(np.mean(low_mask)),
                    }
                    score = (metrics["auprc"], metrics["auroc"], -abs(low_alpha - high_alpha))
                    if best is None or score > best[0]:
                        best = (score, candidate)
    if best is None:
        raise RuntimeError("Failed to find a selective rule")
    return best[1]


def main() -> None:
    args = parse_args()
    device = torch.device(args.device)

    artifacts = prepare_split_artifacts(
        dataset=args.dataset,
        split=args.split,
        seed=args.seed,
        frac=args.frac,
        pkd_threshold=args.pkd_threshold,
        drug_bits=args.drug_bits,
        drug_radius=args.drug_radius,
        target_dim=args.target_dim,
        k=args.topk,
        cache_dir=args.cache_dir,
        num_chemotypes=args.num_chemotypes,
        chemotype_topk=args.chemotype_topk,
        profile_shrinkage=args.profile_shrinkage,
    )

    valid_loader = DataLoader(InteractionDataset(artifacts.valid_df, artifacts), batch_size=args.batch_size, shuffle=False, collate_fn=collate_batch)
    test_loader = DataLoader(InteractionDataset(artifacts.test_df, artifacts), batch_size=args.batch_size, shuffle=False, collate_fn=collate_batch)

    base_model = BaseDTI(
        drug_dim=args.drug_bits,
        target_dim=args.target_dim,
        hidden_dim=args.hidden_dim,
        embed_dim=args.embed_dim,
        dropout=args.dropout,
    ).to(device)
    base_model.load_state_dict(torch.load(args.base_ckpt, map_location=device))
    base_model.eval()

    ftm_model = FunctionalTargetMemoryDTI(
        drug_dim=args.drug_bits,
        target_dim=args.target_dim,
        num_chemotypes=int(artifacts.chemotype_prior.shape[0]),
        chemotype_prior=artifacts.chemotype_prior,
        hidden_dim=args.hidden_dim,
        embed_dim=args.embed_dim,
        stat_dim=3,
        dropout=args.dropout,
    ).to(device)
    ftm_model.load_state_dict(torch.load(args.ftm_ckpt, map_location=device))
    ftm_model.eval()

    valid = collect_split(valid_loader, device, base_model, ftm_model)
    test = collect_split(test_loader, device, base_model, ftm_model)

    rule = search_rule(valid)
    valid_metrics, valid_prob, valid_low_mask = evaluate_rule(valid, rule["feature"], rule["threshold"], rule["low_alpha"], rule["high_alpha"])
    test_metrics, test_prob, test_low_mask = evaluate_rule(test, rule["feature"], rule["threshold"], rule["low_alpha"], rule["high_alpha"])

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(
            {
                "args": vars(args),
                "rule": rule,
                "valid_metrics": valid_metrics,
                "test_metrics": test_metrics,
                "valid_predictions": {
                    "labels": valid["labels"].tolist(),
                    "probabilities": valid_prob.tolist(),
                    "overlap_score": valid["overlap"].tolist(),
                    "low_region": valid_low_mask.astype(int).tolist(),
                },
                "test_predictions": {
                    "labels": test["labels"].tolist(),
                    "probabilities": test_prob.tolist(),
                    "overlap_score": test["overlap"].tolist(),
                    "low_region": test_low_mask.astype(int).tolist(),
                },
            },
            indent=2,
            default=str,
        )
    )
    print(json.dumps({
        "saved_to": str(args.output),
        "rule": rule,
        "test_auprc": test_metrics["auprc"],
        "test_auroc": test_metrics["auroc"],
        "ftm_weight_mean": test_metrics["ftm_weight_mean"],
    }), flush=True)


if __name__ == "__main__":
    main()
