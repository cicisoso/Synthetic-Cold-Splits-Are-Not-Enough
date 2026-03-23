#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier

from raicd.benchmark_resource import ensure_benchmark_resource
from raicd.classical_baselines import (
    build_pair_matrix,
    drug_feature_table,
    evaluate_probabilities,
    save_prediction_csv,
    target_feature_table,
    write_result_json,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train classical DTI baselines on exported benchmark resources.")
    parser.add_argument("--dataset", type=str, required=True)
    parser.add_argument("--split", type=str, required=True)
    parser.add_argument("--model", type=str, default="rf", choices=["rf"])
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--pkd-threshold", type=float, default=7.0)
    parser.add_argument("--drug-bits", type=int, default=2048)
    parser.add_argument("--drug-radius", type=int, default=2)
    parser.add_argument("--target-dim", type=int, default=2048)
    parser.add_argument("--pair-feature-mode", type=str, default="concat", choices=["concat", "concat_absdiff"])
    parser.add_argument("--n-estimators", type=int, default=400)
    parser.add_argument("--max-depth", type=int, default=None)
    parser.add_argument("--min-samples-leaf", type=int, default=1)
    parser.add_argument("--max-features", type=str, default="sqrt")
    parser.add_argument("--n-jobs", type=int, default=-1)
    parser.add_argument("--num-workers", type=int, default=0)
    parser.add_argument("--output-dir", type=Path, default=Path("results/classical_baselines"))
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


def main() -> None:
    args = parse_args()
    set_seed(args.seed)

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

    feature_cache_root = args.cache_dir / "classical_baseline_features" / args.dataset / args.split / f"seed{args.seed}"
    drug_table = drug_feature_table(
        drugs=drugs,
        cache_path=feature_cache_root / f"drugs_morgan_bits{args.drug_bits}_r{args.drug_radius}.npz",
        n_bits=args.drug_bits,
        radius=args.drug_radius,
    )
    target_table = target_feature_table(
        targets=targets,
        cache_path=feature_cache_root / f"targets_kmer_dim{args.target_dim}.npz",
        dim=args.target_dim,
    )

    train_x = build_pair_matrix(
        frame=train_frame,
        drug_lookup=drug_table.lookup,
        target_lookup=target_table.lookup,
        drug_features=drug_table.features,
        target_features=target_table.features,
        pair_feature_mode=args.pair_feature_mode,
    )
    valid_x = build_pair_matrix(
        frame=valid_frame,
        drug_lookup=drug_table.lookup,
        target_lookup=target_table.lookup,
        drug_features=drug_table.features,
        target_features=target_table.features,
        pair_feature_mode=args.pair_feature_mode,
    )
    test_x = build_pair_matrix(
        frame=test_frame,
        drug_lookup=drug_table.lookup,
        target_lookup=target_table.lookup,
        drug_features=drug_table.features,
        target_features=target_table.features,
        pair_feature_mode=args.pair_feature_mode,
    )
    train_y = train_frame["label"].to_numpy(dtype=np.int64)

    model = RandomForestClassifier(
        n_estimators=args.n_estimators,
        max_depth=args.max_depth,
        min_samples_leaf=args.min_samples_leaf,
        max_features=args.max_features,
        class_weight="balanced_subsample",
        n_jobs=args.n_jobs,
        random_state=args.seed,
    )
    model.fit(train_x, train_y)

    valid_prob = model.predict_proba(valid_x)[:, 1].astype(np.float32)
    test_prob = model.predict_proba(test_x)[:, 1].astype(np.float32)
    valid_metrics, valid_extras = evaluate_probabilities(valid_frame, valid_prob)
    test_metrics, test_extras = evaluate_probabilities(test_frame, test_prob)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    run_name = f"{args.dataset}_{args.split}_{args.model}_seed{args.seed}"
    model_path = args.output_dir / f"{run_name}.joblib"
    result_path = args.output_dir / f"{run_name}.json"
    pred_csv_path = args.output_dir / f"{run_name}_test_predictions.csv"
    joblib.dump(model, model_path)
    save_prediction_csv(pred_csv_path, test_extras)
    payload = {
        "args": vars(args),
        "resource_dir": str(resource.resource_dir),
        "train_rows": len(train_frame),
        "valid_rows": len(valid_frame),
        "test_rows": len(test_frame),
        "train_positive_rate": float(train_frame["label"].mean()),
        "feature_dim": int(train_x.shape[1]),
        "feature_cache_root": str(feature_cache_root),
        "model_path": str(model_path),
        "valid_metrics": valid_metrics,
        "test_metrics": test_metrics,
        "valid_predictions": valid_extras,
        "test_predictions": test_extras,
        "test_prediction_csv": str(pred_csv_path),
        "feature_importance_top16": np.argsort(model.feature_importances_)[-16:][::-1].astype(int).tolist(),
    }
    write_result_json(result_path, payload)
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
