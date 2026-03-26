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
from raicd.graph_baselines import (
    AMINO_TO_INDEX,
    DrugBANLite,
    GraphDTALite,
    GraphPairBatch,
    GraphPairDataset,
    atom_feature_dim,
    build_drug_graphs,
    build_target_tokens,
    collate_graph_pairs,
)
from raicd.metrics import binary_metrics, stratified_overlap_metrics


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train GraphDTA-style baselines on exported benchmark resources.")
    parser.add_argument("--dataset", type=str, required=True)
    parser.add_argument("--split", type=str, required=True)
    parser.add_argument("--model", type=str, default="graphdta", choices=["graphdta", "drugban"])
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--epochs", type=int, default=8)
    parser.add_argument("--batch-size", type=int, default=128)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--weight-decay", type=float, default=1e-4)
    parser.add_argument("--dropout", type=float, default=0.1)
    parser.add_argument("--graph-hidden-dim", type=int, default=128)
    parser.add_argument("--graph-out-dim", type=int, default=128)
    parser.add_argument("--protein-embed-dim", type=int, default=64)
    parser.add_argument("--protein-hidden-dim", type=int, default=128)
    parser.add_argument("--pair-hidden-dim", type=int, default=256)
    parser.add_argument("--protein-max-length", type=int, default=1000)
    parser.add_argument("--pkd-threshold", type=float, default=7.0)
    parser.add_argument("--num-workers", type=int, default=0)
    parser.add_argument("--device", type=str, default="cuda" if torch.cuda.is_available() else "cpu")
    parser.add_argument("--output-dir", type=Path, default=Path("results/graph_baselines"))
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


def move_batch(batch: GraphPairBatch, device: torch.device) -> GraphPairBatch:
    return GraphPairBatch(
        graph_batch=batch.graph_batch.to(device),
        target_tokens=batch.target_tokens.to(device),
        labels=batch.labels.to(device),
        overlap_score=batch.overlap_score.to(device),
        example_ids=batch.example_ids,
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
        logits, aux = model(move.graph_batch, move.target_tokens)
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

    drug_graphs = build_drug_graphs(drugs)
    target_tokens = build_target_tokens(targets, max_length=args.protein_max_length)

    train_ds = GraphPairDataset(train_frame, drug_graphs=drug_graphs, target_tokens=target_tokens)
    valid_ds = GraphPairDataset(valid_frame, drug_graphs=drug_graphs, target_tokens=target_tokens)
    test_ds = GraphPairDataset(test_frame, drug_graphs=drug_graphs, target_tokens=target_tokens)

    train_loader = DataLoader(train_ds, batch_size=args.batch_size, shuffle=True, num_workers=args.num_workers, collate_fn=collate_graph_pairs)
    valid_loader = DataLoader(valid_ds, batch_size=args.batch_size, shuffle=False, num_workers=args.num_workers, collate_fn=collate_graph_pairs)
    test_loader = DataLoader(test_ds, batch_size=args.batch_size, shuffle=False, num_workers=args.num_workers, collate_fn=collate_graph_pairs)

    if args.model == "drugban":
        model = DrugBANLite(
            atom_dim=atom_feature_dim(),
            protein_vocab_size=len(AMINO_TO_INDEX) + 1,
            graph_hidden_dim=args.graph_hidden_dim,
            graph_out_dim=args.graph_out_dim,
            protein_embed_dim=args.protein_embed_dim,
            protein_hidden_dim=args.protein_hidden_dim,
            pair_hidden_dim=args.pair_hidden_dim,
            dropout=args.dropout,
        ).to(device)
    else:
        model = GraphDTALite(
            atom_dim=atom_feature_dim(),
            protein_vocab_size=len(AMINO_TO_INDEX) + 1,
            graph_hidden_dim=args.graph_hidden_dim,
            graph_out_dim=args.graph_out_dim,
            protein_embed_dim=args.protein_embed_dim,
            protein_hidden_dim=args.protein_hidden_dim,
            pair_hidden_dim=args.pair_hidden_dim,
            dropout=args.dropout,
        ).to(device)

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
            logits, _ = model(move.graph_batch, move.target_tokens)
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
                "drug_graphs": len(drug_graphs),
                "target_token_sequences": len(target_tokens),
            },
            indent=2,
            default=str,
        )
    )
    print(
        json.dumps(
            {
                "saved_to": str(result_path),
                "test_auprc": test_metrics["auprc"],
                "test_auroc": test_metrics["auroc"],
            }
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
