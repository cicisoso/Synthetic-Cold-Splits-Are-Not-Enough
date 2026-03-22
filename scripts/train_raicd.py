#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

import numpy as np
import torch
from torch.utils.data import DataLoader

from raicd.data import InteractionDataset, collate_batch, prepare_split_artifacts
from raicd.metrics import binary_metrics, stratified_overlap_metrics
from raicd.model import BaseDTI, Batch, FunctionalTargetMemoryDTI, RAICD, RobustFunctionalTargetMemoryDTI, SplitAdaptiveRouter


ROUTER_EXPERT_NAMES = ["base", "drug_only", "target_only", "both"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train retrieval-augmented cold-start DTI models.")
    parser.add_argument("--dataset", type=str, default="BindingDB_Kd")
    parser.add_argument("--split", type=str, default="unseen_drug")
    parser.add_argument("--model", type=str, default="raicd", choices=["base", "raicd", "router", "ftm", "rftm"])
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--epochs", type=int, default=8)
    parser.add_argument("--batch-size", type=int, default=256)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--weight-decay", type=float, default=1e-4)
    parser.add_argument("--dropout", type=float, default=0.1)
    parser.add_argument("--hidden-dim", type=int, default=512)
    parser.add_argument("--embed-dim", type=int, default=256)
    parser.add_argument("--drug-bits", type=int, default=2048)
    parser.add_argument("--drug-radius", type=int, default=2)
    parser.add_argument("--target-dim", type=int, default=2048)
    parser.add_argument("--pkd-threshold", type=float, default=7.0)
    parser.add_argument("--topk", type=int, default=8)
    parser.add_argument("--num-chemotypes", type=int, default=32)
    parser.add_argument("--chemotype-topk", type=int, default=4)
    parser.add_argument("--profile-shrinkage", type=float, default=8.0)
    parser.add_argument("--retrieval-mode", type=str, default="both", choices=["both", "drug_only", "target_only"])
    parser.add_argument("--use-retrieval-gate", action="store_true")
    parser.add_argument("--expert-loss-weight", type=float, default=0.5)
    parser.add_argument("--profile-loss-weight", type=float, default=0.2)
    parser.add_argument("--profile-magnitude-weight", type=float, default=0.0)
    parser.add_argument("--num-workers", type=int, default=0)
    parser.add_argument("--device", type=str, default="cuda" if torch.cuda.is_available() else "cpu")
    parser.add_argument("--output-dir", type=Path, default=Path("results"))
    parser.add_argument("--cache-dir", type=Path, default=Path("data/cache"))
    parser.add_argument("--max-train-samples", type=int, default=None)
    parser.add_argument("--max-valid-samples", type=int, default=None)
    parser.add_argument("--max-test-samples", type=int, default=None)
    parser.add_argument("--frac", type=float, nargs=3, default=[0.7, 0.1, 0.2])
    return parser.parse_args()


def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)


def make_model(args: argparse.Namespace, artifacts) -> torch.nn.Module:
    if args.model == "base":
        return BaseDTI(
            drug_dim=args.drug_bits,
            target_dim=args.target_dim,
            hidden_dim=args.hidden_dim,
            embed_dim=args.embed_dim,
            dropout=args.dropout,
        )
    if args.model == "raicd":
        return RAICD(
            drug_dim=args.drug_bits,
            target_dim=args.target_dim,
            hidden_dim=args.hidden_dim,
            embed_dim=args.embed_dim,
            stat_dim=3,
            retrieval_mode=args.retrieval_mode,
            use_retrieval_gate=args.use_retrieval_gate,
            dropout=args.dropout,
        )
    if args.model == "router":
        return SplitAdaptiveRouter(
            drug_dim=args.drug_bits,
            target_dim=args.target_dim,
            hidden_dim=args.hidden_dim,
            embed_dim=args.embed_dim,
            stat_dim=3,
            use_retrieval_gate=args.use_retrieval_gate,
            dropout=args.dropout,
        )
    if args.model == "ftm":
        return FunctionalTargetMemoryDTI(
            drug_dim=args.drug_bits,
            target_dim=args.target_dim,
            num_chemotypes=int(artifacts.chemotype_prior.shape[0]),
            chemotype_prior=artifacts.chemotype_prior,
            hidden_dim=args.hidden_dim,
            embed_dim=args.embed_dim,
            stat_dim=3,
            dropout=args.dropout,
        )
    return RobustFunctionalTargetMemoryDTI(
        drug_dim=args.drug_bits,
        target_dim=args.target_dim,
        num_chemotypes=int(artifacts.chemotype_prior.shape[0]),
        chemotype_prior=artifacts.chemotype_prior,
        hidden_dim=args.hidden_dim,
        embed_dim=args.embed_dim,
        stat_dim=3,
        dropout=args.dropout,
    )


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


def compute_loss(
    criterion: torch.nn.Module,
    logits: torch.Tensor,
    labels: torch.Tensor,
    aux: dict,
    batch: Batch,
    expert_loss_weight: float,
    profile_loss_weight: float,
    profile_magnitude_weight: float,
) -> tuple[torch.Tensor, dict]:
    main_loss = criterion(logits, labels)
    total_loss = main_loss
    stats = {
        "main_loss": float(main_loss.detach().cpu()),
        "expert_loss": 0.0,
        "profile_loss": 0.0,
        "profile_magnitude_loss": 0.0,
    }

    if "expert_logits" in aux and expert_loss_weight > 0:
        expert_logits = aux["expert_logits"]
        expert_loss = 0.0
        for i in range(expert_logits.shape[1]):
            expert_loss = expert_loss + criterion(expert_logits[:, i], labels)
        expert_loss = expert_loss / expert_logits.shape[1]
        total_loss = total_loss + expert_loss_weight * expert_loss
        stats["expert_loss"] = float(expert_loss.detach().cpu())

    if (
        "target_profile_pred" in aux
        and batch.target_cluster_profile is not None
        and batch.target_cluster_mask is not None
        and profile_loss_weight > 0
    ):
        profile_pred = aux["target_profile_pred"]
        profile_target = batch.target_cluster_profile
        mask = batch.target_cluster_mask.view(-1)
        if torch.sum(mask) > 0:
            profile_error = torch.nn.functional.smooth_l1_loss(profile_pred, profile_target, reduction="none").mean(dim=-1)
            profile_loss = torch.sum(profile_error * mask) / torch.clamp(torch.sum(mask), min=1.0)
            total_loss = total_loss + profile_loss_weight * profile_loss
            stats["profile_loss"] = float(profile_loss.detach().cpu())

    if "profile_magnitude" in aux and profile_magnitude_weight > 0:
        profile_mag_loss = torch.mean(aux["profile_magnitude"])
        total_loss = total_loss + profile_magnitude_weight * profile_mag_loss
        stats["profile_magnitude_loss"] = float(profile_mag_loss.detach().cpu())

    return total_loss, stats


@torch.no_grad()
def evaluate(model: torch.nn.Module, loader: DataLoader, device: torch.device) -> tuple[dict, dict]:
    model.eval()
    probs = []
    labels = []
    overlap = []
    route_weights = []
    expert_logits = []
    cluster_match = []
    profile_entropy = []
    profile_magnitude = []
    fusion_weight = []
    for batch in loader:
        move = move_batch(batch, device)
        logits, aux = model(move)
        probs.append(torch.sigmoid(logits).cpu().numpy())
        labels.append(batch["label"].numpy())
        overlap.append(batch["overlap_score"].numpy())
        if "route_weights" in aux:
            route_weights.append(aux["route_weights"].detach().cpu().numpy())
        if "expert_logits" in aux:
            expert_logits.append(aux["expert_logits"].detach().cpu().numpy())
        if "cluster_match" in aux:
            cluster_match.append(aux["cluster_match"].detach().cpu().numpy())
        if "profile_entropy" in aux:
            profile_entropy.append(aux["profile_entropy"].detach().cpu().numpy())
        if "profile_magnitude" in aux:
            profile_magnitude.append(aux["profile_magnitude"].detach().cpu().numpy())
        if "fusion_weight" in aux:
            fusion_weight.append(aux["fusion_weight"].detach().cpu().numpy())
    probs_arr = np.concatenate(probs)
    labels_arr = np.concatenate(labels).astype(int)
    overlap_arr = np.concatenate(overlap)
    metrics = binary_metrics(labels_arr, probs_arr)
    metrics["overlap_buckets"] = stratified_overlap_metrics(labels_arr, probs_arr, overlap_arr)
    extras = {
        "labels": labels_arr.tolist(),
        "probabilities": probs_arr.tolist(),
        "overlap_score": overlap_arr.tolist(),
    }
    if route_weights:
        route_arr = np.concatenate(route_weights, axis=0)
        metrics["route_weight_mean"] = route_arr.mean(axis=0).tolist()
        metrics["route_hard_assignment"] = (np.bincount(route_arr.argmax(axis=1), minlength=len(ROUTER_EXPERT_NAMES)) / len(route_arr)).tolist()
        metrics["route_expert_names"] = ROUTER_EXPERT_NAMES
        extras["route_weights"] = route_arr.tolist()
    if expert_logits:
        expert_arr = np.concatenate(expert_logits, axis=0)
        extras["expert_logits"] = expert_arr.tolist()
    if cluster_match:
        metrics["cluster_match_mean"] = float(np.mean(np.concatenate(cluster_match)))
    if profile_entropy:
        metrics["profile_entropy_mean"] = float(np.mean(np.concatenate(profile_entropy)))
    if profile_magnitude:
        metrics["profile_magnitude_mean"] = float(np.mean(np.concatenate(profile_magnitude)))
    if fusion_weight:
        metrics["fusion_weight_mean"] = float(np.mean(np.concatenate(fusion_weight)))
    return metrics, extras


def main() -> None:
    args = parse_args()
    set_seed(args.seed)
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
        max_train=args.max_train_samples,
        max_valid=args.max_valid_samples,
        max_test=args.max_test_samples,
    )

    train_ds = InteractionDataset(artifacts.train_df, artifacts)
    valid_ds = InteractionDataset(artifacts.valid_df, artifacts)
    test_ds = InteractionDataset(artifacts.test_df, artifacts)

    train_loader = DataLoader(train_ds, batch_size=args.batch_size, shuffle=True, num_workers=args.num_workers, collate_fn=collate_batch)
    valid_loader = DataLoader(valid_ds, batch_size=args.batch_size, shuffle=False, num_workers=args.num_workers, collate_fn=collate_batch)
    test_loader = DataLoader(test_ds, batch_size=args.batch_size, shuffle=False, num_workers=args.num_workers, collate_fn=collate_batch)

    model = make_model(args, artifacts).to(device)
    pos_rate = float(artifacts.train_df["label"].mean())
    pos_weight = (1.0 - pos_rate) / max(pos_rate, 1e-6)
    criterion = torch.nn.BCEWithLogitsLoss(pos_weight=torch.tensor(pos_weight, device=device))
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=args.weight_decay)

    best_valid_auprc = -1.0
    best_state = None
    history = []

    for epoch in range(1, args.epochs + 1):
        model.train()
        total_loss = 0.0
        total_main_loss = 0.0
        total_expert_loss = 0.0
        total_profile_loss = 0.0
        total_profile_magnitude_loss = 0.0
        total_rows = 0
        for batch in train_loader:
            move = move_batch(batch, device)
            logits, aux = model(move)
            loss, loss_stats = compute_loss(
                criterion=criterion,
                logits=logits,
                labels=move.labels,
                aux=aux,
                batch=move,
                expert_loss_weight=args.expert_loss_weight,
                profile_loss_weight=args.profile_loss_weight,
                profile_magnitude_weight=args.profile_magnitude_weight,
            )
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

            batch_size = move.labels.shape[0]
            total_loss += loss.item() * batch_size
            total_main_loss += loss_stats["main_loss"] * batch_size
            total_expert_loss += loss_stats["expert_loss"] * batch_size
            total_profile_loss += loss_stats["profile_loss"] * batch_size
            total_profile_magnitude_loss += loss_stats["profile_magnitude_loss"] * batch_size
            total_rows += batch_size

        valid_metrics, _ = evaluate(model, valid_loader, device)
        epoch_record = {
            "epoch": epoch,
            "train_loss": total_loss / max(total_rows, 1),
            "train_main_loss": total_main_loss / max(total_rows, 1),
            "train_expert_loss": total_expert_loss / max(total_rows, 1),
            "train_profile_loss": total_profile_loss / max(total_rows, 1),
            "train_profile_magnitude_loss": total_profile_magnitude_loss / max(total_rows, 1),
            "valid_auprc": valid_metrics["auprc"],
            "valid_auroc": valid_metrics["auroc"],
        }
        if "route_weight_mean" in valid_metrics:
            epoch_record["route_weight_mean"] = valid_metrics["route_weight_mean"]
        history.append(epoch_record)
        print(json.dumps(epoch_record), flush=True)

        if valid_metrics["auprc"] > best_valid_auprc:
            best_valid_auprc = valid_metrics["auprc"]
            best_state = {k: v.detach().cpu() for k, v in model.state_dict().items()}

    if best_state is not None:
        model.load_state_dict(best_state)

    valid_metrics, valid_extras = evaluate(model, valid_loader, device)
    test_metrics, test_extras = evaluate(model, test_loader, device)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    run_name = f"{args.dataset}_{args.split}_{args.model}_seed{args.seed}"
    if args.model == "raicd":
        run_name += f"_{args.retrieval_mode}"
        if args.use_retrieval_gate:
            run_name += "_gate"
    elif args.model == "router":
        run_name += "_adaptive"
        if args.use_retrieval_gate:
            run_name += "_gate"
    elif args.model in {"ftm", "rftm"}:
        shrink_tag = str(args.profile_shrinkage).replace(".", "p")
        suffix = "_fused" if args.model == "rftm" else ""
        run_name += f"_chem{args.num_chemotypes}_top{args.chemotype_topk}_shr{shrink_tag}{suffix}"
    result_path = args.output_dir / f"{run_name}.json"
    torch.save(model.state_dict(), args.output_dir / f"{run_name}.pt")
    result_path.write_text(
        json.dumps(
            {
                "args": vars(args),
                "train_rows": len(artifacts.train_df),
                "valid_rows": len(artifacts.valid_df),
                "test_rows": len(artifacts.test_df),
                "train_positive_rate": float(artifacts.train_df["label"].mean()),
                "history": history,
                "valid_metrics": valid_metrics,
                "test_metrics": test_metrics,
                "valid_predictions": valid_extras,
                "test_predictions": test_extras,
            },
            indent=2,
            default=str,
        )
    )
    print(json.dumps({"saved_to": str(result_path), "test_auprc": test_metrics["auprc"], "test_auroc": test_metrics["auroc"]}), flush=True)


if __name__ == "__main__":
    main()
