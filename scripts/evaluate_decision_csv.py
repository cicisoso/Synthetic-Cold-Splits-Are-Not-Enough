#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from raicd.decision_metrics import merged_decision_metrics


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate decision-facing ranking metrics from a prediction CSV.")
    parser.add_argument("--reference-csv", type=Path, required=True)
    parser.add_argument("--prediction-csv", type=Path, required=True)
    parser.add_argument("--id-col", type=str, default="example_id")
    parser.add_argument("--pred-col", type=str, default="probability")
    parser.add_argument("--score-type", type=str, default="probability", choices=["probability", "logit"])
    parser.add_argument("--group-col", type=str, default="Target_ID")
    parser.add_argument("--ks", type=int, nargs="+", default=[1, 3, 5, 10, 20])
    parser.add_argument("--top-fracs", type=float, nargs="+", default=[0.01, 0.05, 0.10])
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
        merged["probability"] = 1.0 / (1.0 + np.exp(-scores))
    else:
        merged["probability"] = np.clip(scores, 0.0, 1.0)

    payload = {
        "reference_csv": str(args.reference_csv),
        "prediction_csv": str(args.prediction_csv),
        "merged_rows": int(len(merged)),
        "metrics": merged_decision_metrics(
            merged=merged,
            group_col=args.group_col,
            label_col="label",
            prob_col="probability",
            ks=args.ks,
            top_fracs=args.top_fracs,
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2))
    ef1 = payload["metrics"]["global_enrichment"].get("ef_at_1pct", None)
    macro_hit10 = payload["metrics"]["per_target"]["hit_rate"].get("10", None)
    print(json.dumps({"saved_to": str(args.output), "ef_at_1pct": ef1, "per_target_hit_at_10": macro_hit10}))


if __name__ == "__main__":
    main()
