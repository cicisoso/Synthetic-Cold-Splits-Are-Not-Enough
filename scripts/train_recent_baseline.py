#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from torch.utils.data import DataLoader

from raicd.benchmark_resource import ensure_benchmark_resource
from raicd.lm_baselines import DTILMAdapter, HyperPCMAdapter, PairFeatureDataset, PairBatch, collate_pair_features
from raicd.lm_features import load_or_compute_pooled_embeddings
from raicd.metrics import binary_metrics, stratified_overlap_metrics


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train recent pooled-LM DTI baselines on exported benchmark resources.")
    parser.add_argument("--dataset", type=str, required=True)
    parser.add_argument("--split", type=str, required=True)
    parser.add_argument("--model", type=str, default="dtilm", choices=["dtilm", "hyperpcm"])
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--epochs", type=int, default=6)
    parser.add_argument("--batch-size", type=int, default=128)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--weight-decay", type=float, default=1e-4)
    parser.add_argument("--dropout", type=float, default=0.1)
    parser.add_argument("--hidden-dim", type=int, default=512)
    parser.add_argument("--drug-hidden-dim", type=int, default=256)
    parser.add_argument("--target-hidden-dim", type=int, default=256)
    parser.add_argument("--hyper-hidden-dim", type=int, default=256)
    parser.add_argument("--drug-model-name", type=str, default="seyonec/PubChem10M_SMILES_BPE_450k")
    parser.add_argument("--target-model-name", type=str, default="facebook/esm2_t12_35M_UR50D")
    parser.add_argument("--drug-max-length", type=int, default=128)
    parser.add_argument("--target-max-length", type=int, default=1024)
    parser.add_argument("--encoder-batch-size", type=int, default=16)
    parser.add_argument("--pkd-threshold", type=float, default=7.0)
    parser.add_argument("--num-workers", type=int, default=0)
    parser.add_argument("--device", type=str, default="cuda" if torch.cuda.is_available() else "cpu")
    parser.add_argument("--output-dir", type=Path, default=Path("results/recent_baselines"))
    parser.add_argument("--cache-dir", type=Path, default=Path("data/cache"))
    parser.add_argument("--resource-base-dir", type=Path, default=Path("benchmark_resources"))
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


def move_batch(batch: PairBatch, device: torch.device) -> PairBatch:
    return PairBatch(
        drug_x=batch.drug_x.to(device),
        target_x=batch.target_x.to(device),
        labels=batch.labels.to(device),
        overlap_score=batch.overlap_score.to(device),
        example_ids=batch.example_ids,
    )


def make_model(args: argparse.Namespace, drug_dim: int, target_dim: int) -> torch.nn.Module:
    if args.model == "dtilm":
        return DTILMAdapter(
            drug_dim=drug_dim,
            target_dim=target_dim,
            hidden_dim=args.hidden_dim,
            dropout=args.dropout,
        )
    return HyperPCMAdapter(
        drug_dim=drug_dim,
        target_dim=target_dim,
        drug_hidden_dim=args.drug_hidden_dim,
        target_hidden_dim=args.target_hidden_dim,
        hyper_hidden_dim=args.hyper_hidden_dim,
        dropout=args.dropout,
    )


@torch.no_grad()
def evaluate(model: torch.nn.Module, loader: DataLoader, device: torch.device) -> tuple[dict, dict]:
    model.eval()
    probs = []
    labels = []
    overlap = []
    example_ids = []
    aux_stats = {}
    for batch in loader:
        move = move_batch(batch, device)
        logits, aux = model(move.drug_x, move.target_x)
        probs.append(torch.sigmoid(logits).cpu().numpy())
        labels.append(move.labels.cpu().numpy())
        overlap.append(move.overlap_score.cpu().numpy())
        example_ids.extend(move.example_ids)
        for key, value in aux.items():
            aux_stats.setdefault(key, []).append(float(value))
    probs_arr = np.concatenate(probs)
    labels_arr = np.concatenate(labels).astype(int)
    overlap_arr = np.concatenate(overlap)
    metrics = binary_metrics(labels_arr, probs_arr)
    metrics["overlap_buckets"] = stratified_overlap_metrics(labels_arr, probs_arr, overlap_arr)
    for key, values in aux_stats.items():
        metrics[key] = float(np.mean(values))
    extras = {
        "example_id": example_ids,
        "labels": labels_arr.tolist(),
        "probabilities": probs_arr.tolist(),
        "overlap_score": overlap_arr.tolist(),
    }
    return metrics, extras


def main() -> None:
    args = parse_args()
    set_seed(args.seed)
    device = torch.device(args.device)

    resource = ensure_benchmark_resource(
        dataset=args.dataset,
        split=args.split,
        seed=args.seed,
        output_base_dir=args.resource_base_dir,
        frac=args.frac,
        cache_dir=args.cache_dir,
        pkd_threshold=args.pkd_threshold,
        max_train=args.max_train_samples,
        max_valid=args.max_valid_samples,
        max_test=args.max_test_samples,
    )

    train_frame = pd.read_csv(resource.train_csv)
    valid_frame = pd.read_csv(resource.valid_csv)
    test_frame = pd.read_csv(resource.test_csv)
    drugs = pd.read_csv(resource.drugs_csv)
    targets = pd.read_csv(resource.targets_csv)

    feature_cache_root = args.cache_dir / "recent_baseline_embeddings" / args.dataset / args.split
    drug_embeddings = load_or_compute_pooled_embeddings(
        frame=drugs,
        id_col="drug_id",
        text_col="drug_smile",
        model_name=args.drug_model_name,
        cache_dir=feature_cache_root / "drugs",
        device=device,
        batch_size=args.encoder_batch_size,
        max_length=args.drug_max_length,
    )
    target_embeddings = load_or_compute_pooled_embeddings(
        frame=targets,
        id_col="prot_id",
        text_col="prot_seq",
        model_name=args.target_model_name,
        cache_dir=feature_cache_root / "targets",
        device=device,
        batch_size=args.encoder_batch_size,
        max_length=args.target_max_length,
    )

    drug_lookup = {str(drug_id): idx for idx, drug_id in enumerate(drugs["drug_id"].astype(str).tolist())}
    target_lookup = {str(prot_id): idx for idx, prot_id in enumerate(targets["prot_id"].astype(str).tolist())}

    train_ds = PairFeatureDataset(train_frame, drug_lookup, target_lookup, drug_embeddings, target_embeddings)
    valid_ds = PairFeatureDataset(valid_frame, drug_lookup, target_lookup, drug_embeddings, target_embeddings)
    test_ds = PairFeatureDataset(test_frame, drug_lookup, target_lookup, drug_embeddings, target_embeddings)

    train_loader = DataLoader(train_ds, batch_size=args.batch_size, shuffle=True, num_workers=args.num_workers, collate_fn=collate_pair_features)
    valid_loader = DataLoader(valid_ds, batch_size=args.batch_size, shuffle=False, num_workers=args.num_workers, collate_fn=collate_pair_features)
    test_loader = DataLoader(test_ds, batch_size=args.batch_size, shuffle=False, num_workers=args.num_workers, collate_fn=collate_pair_features)

    model = make_model(args, drug_dim=drug_embeddings.shape[1], target_dim=target_embeddings.shape[1]).to(device)
    pos_rate = float(train_frame["label"].mean())
    pos_weight = (1.0 - pos_rate) / max(pos_rate, 1e-6)
    criterion = torch.nn.BCEWithLogitsLoss(pos_weight=torch.tensor(pos_weight, device=device))
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=args.weight_decay)

    best_valid_auprc = -1.0
    best_state = None
    history = []
    for epoch in range(1, args.epochs + 1):
        model.train()
        total_loss = 0.0
        total_rows = 0
        for batch in train_loader:
            move = move_batch(batch, device)
            logits, _ = model(move.drug_x, move.target_x)
            loss = criterion(logits, move.labels)
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            batch_rows = move.labels.shape[0]
            total_loss += float(loss.detach().cpu()) * batch_rows
            total_rows += batch_rows

        valid_metrics, _ = evaluate(model, valid_loader, device)
        epoch_record = {
            "epoch": epoch,
            "train_loss": total_loss / max(total_rows, 1),
            "valid_auprc": valid_metrics["auprc"],
            "valid_auroc": valid_metrics["auroc"],
        }
        history.append(epoch_record)
        print(json.dumps(epoch_record), flush=True)
        if valid_metrics["auprc"] > best_valid_auprc:
            best_valid_auprc = valid_metrics["auprc"]
            best_state = {key: value.detach().cpu() for key, value in model.state_dict().items()}

    if best_state is not None:
        model.load_state_dict(best_state)

    valid_metrics, valid_extras = evaluate(model, valid_loader, device)
    test_metrics, test_extras = evaluate(model, test_loader, device)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    run_name = f"{args.dataset}_{args.split}_{args.model}_seed{args.seed}"
    ckpt_path = args.output_dir / f"{run_name}.pt"
    result_path = args.output_dir / f"{run_name}.json"
    pred_csv_path = args.output_dir / f"{run_name}_test_predictions.csv"
    torch.save(model.state_dict(), ckpt_path)
    pd.DataFrame(
        {
            "example_id": test_extras["example_id"],
            "label": test_extras["labels"],
            "probability": test_extras["probabilities"],
            "overlap_score": test_extras["overlap_score"],
        }
    ).to_csv(pred_csv_path, index=False)
    result_path.write_text(
        json.dumps(
            {
                "args": vars(args),
                "resource_dir": str(resource.resource_dir),
                "train_rows": len(train_frame),
                "valid_rows": len(valid_frame),
                "test_rows": len(test_frame),
                "train_positive_rate": float(train_frame["label"].mean()),
                "history": history,
                "valid_metrics": valid_metrics,
                "test_metrics": test_metrics,
                "valid_predictions": valid_extras,
                "test_predictions": test_extras,
                "test_prediction_csv": str(pred_csv_path),
            },
            indent=2,
            default=str,
        )
    )
    print(json.dumps({"saved_to": str(result_path), "test_auprc": test_metrics["auprc"], "test_auroc": test_metrics["auroc"]}), flush=True)


if __name__ == "__main__":
    main()
