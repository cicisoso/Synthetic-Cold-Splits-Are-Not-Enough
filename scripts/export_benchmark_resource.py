#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
from pathlib import Path

from raicd.benchmark_resource import export_benchmark_resource


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export a reusable benchmark resource for a given DTI dataset split.")
    parser.add_argument("--dataset", type=str, required=True)
    parser.add_argument("--split", type=str, required=True)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--pkd-threshold", type=float, default=7.0)
    parser.add_argument("--drug-bits", type=int, default=2048)
    parser.add_argument("--drug-radius", type=int, default=2)
    parser.add_argument("--target-dim", type=int, default=2048)
    parser.add_argument("--topk", type=int, default=8)
    parser.add_argument("--num-chemotypes", type=int, default=32)
    parser.add_argument("--chemotype-topk", type=int, default=4)
    parser.add_argument("--profile-shrinkage", type=float, default=8.0)
    parser.add_argument("--output-base-dir", type=Path, default=Path("benchmark_resources"))
    parser.add_argument("--cache-dir", type=Path, default=Path("data/cache"))
    parser.add_argument("--max-train-samples", type=int, default=None)
    parser.add_argument("--max-valid-samples", type=int, default=None)
    parser.add_argument("--max-test-samples", type=int, default=None)
    parser.add_argument("--frac", type=float, nargs=3, default=[0.7, 0.1, 0.2])
    parser.add_argument("--force", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    resource = export_benchmark_resource(
        dataset=args.dataset,
        split=args.split,
        seed=args.seed,
        output_base_dir=args.output_base_dir,
        frac=args.frac,
        cache_dir=args.cache_dir,
        pkd_threshold=args.pkd_threshold,
        drug_bits=args.drug_bits,
        drug_radius=args.drug_radius,
        target_dim=args.target_dim,
        topk=args.topk,
        num_chemotypes=args.num_chemotypes,
        chemotype_topk=args.chemotype_topk,
        profile_shrinkage=args.profile_shrinkage,
        max_train=args.max_train_samples,
        max_valid=args.max_valid_samples,
        max_test=args.max_test_samples,
        force=args.force,
    )
    manifest = json.loads(resource.manifest_json.read_text())
    print(json.dumps({"resource_dir": str(resource.resource_dir), "manifest": manifest}, indent=2))


if __name__ == "__main__":
    main()
