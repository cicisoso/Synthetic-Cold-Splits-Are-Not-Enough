#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from raicd.metrics import binary_metrics, stratified_overlap_metrics


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate a prediction CSV against a benchmark resource partition.")
    parser.add_argument("--reference-csv", type=Path, required=True)
    parser.add_argument("--prediction-csv", type=Path, required=True)
    parser.add_argument("--id-col", type=str, default="example_id")
    parser.add_argument("--pred-col", type=str, default="probability")
    parser.add_argument("--score-type", type=str, default="probability", choices=["probability", "logit"])
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    reference = pd.read_csv(args.reference_csv)
    predictions = pd.read_csv(args.prediction_csv)
    merged = reference.merge(predictions[[args.id_col, args.pred_col]], on=args.id_col, how="inner")
    if len(merged) != len(reference):
        missing = int(len(reference) - len(merged))
        raise ValueError(f"Prediction CSV did not cover the full reference set; missing {missing} rows.")

    scores = merged[args.pred_col].to_numpy(dtype=np.float32)
    if args.score_type == "logit":
        probabilities = 1.0 / (1.0 + np.exp(-scores))
    else:
        probabilities = np.clip(scores, 0.0, 1.0)

    labels = merged["label"].to_numpy(dtype=np.int64)
    overlap = merged["overlap_score"].to_numpy(dtype=np.float32)
    metrics = binary_metrics(labels, probabilities)
    metrics["overlap_buckets"] = stratified_overlap_metrics(labels, probabilities, overlap)

    payload = {
        "reference_csv": str(args.reference_csv),
        "prediction_csv": str(args.prediction_csv),
        "merged_rows": int(len(merged)),
        "metrics": metrics,
        "predictions": {
            "example_id": merged[args.id_col].astype(str).tolist(),
            "labels": labels.tolist(),
            "probabilities": probabilities.tolist(),
            "overlap_score": overlap.tolist(),
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2))
    print(json.dumps({"saved_to": str(args.output), "auprc": metrics["auprc"], "auroc": metrics["auroc"]}))


if __name__ == "__main__":
    main()
