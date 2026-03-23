#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import random
import statistics
from pathlib import Path

import numpy as np
from sklearn.metrics import average_precision_score


SYSTEM_PATHS = {
    "base": [
        "results/full_bindingdb_patent_base/BindingDB_patent_patent_temporal_base_seed0.json",
        "results/full_bindingdb_patent_base/BindingDB_patent_patent_temporal_base_seed1.json",
        "results/full_bindingdb_patent_base/BindingDB_patent_patent_temporal_base_seed2.json",
    ],
    "DTI-LM": [
        "results/recent_panel_stage1/BindingDB_patent_patent_temporal_dtilm_seed0.json",
        "results/recent_dtilm_patent_multiseed/BindingDB_patent_patent_temporal_dtilm_seed1.json",
        "results/recent_dtilm_patent_multiseed/BindingDB_patent_patent_temporal_dtilm_seed2.json",
    ],
    "HyperPCM": [
        "results/recent_panel_stage1/BindingDB_patent_patent_temporal_hyperpcm_seed0.json",
        "results/recent_hyperpcm_patent_multiseed/BindingDB_patent_patent_temporal_hyperpcm_seed1.json",
        "results/recent_hyperpcm_patent_multiseed/BindingDB_patent_patent_temporal_hyperpcm_seed2.json",
    ],
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Bootstrap patent diagnostic slice confidence intervals.")
    parser.add_argument("--num-bootstrap", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--output-json", type=Path, default=Path("reports/patent_slice_bootstrap.json"))
    parser.add_argument("--output-md", type=Path, default=Path("reports/PATENT_SLICE_BOOTSTRAP.md"))
    return parser.parse_args()


def load_years() -> list[int]:
    years = []
    with open("data/tdc_benchmark/dti_dg_group/bindingdb_patent/test.csv", newline="") as fh:
        for row in csv.DictReader(fh):
            years.append(int(row["Year"]))
    return years


def load_preds(path: str) -> dict:
    with open(path) as fh:
        data = json.load(fh)
    return {
        "labels": np.asarray(data["test_predictions"]["labels"], dtype=np.int32),
        "probs": np.asarray(data["test_predictions"]["probabilities"], dtype=np.float32),
        "overlap": np.asarray(data["test_predictions"]["overlap_score"], dtype=np.float32),
    }


def percentile(sorted_values: list[float], q: float) -> float:
    pos = q * (len(sorted_values) - 1)
    lo = int(pos)
    hi = min(lo + 1, len(sorted_values) - 1)
    frac = pos - lo
    return sorted_values[lo] * (1.0 - frac) + sorted_values[hi] * frac


def bootstrap_mean_auprc(seed_data: list[tuple[np.ndarray, np.ndarray]], num_bootstrap: int, seed: int) -> dict:
    rng = random.Random(seed)
    observed = [float(average_precision_score(labels, probs)) for labels, probs in seed_data]
    observed_mean = float(statistics.mean(observed))

    boot = []
    for _ in range(num_bootstrap):
        per_seed = []
        for labels, probs in seed_data:
            n = len(labels)
            idx = [rng.randrange(n) for _ in range(n)]
            y = labels[idx]
            p = probs[idx]
            per_seed.append(float(average_precision_score(y, p)))
        boot.append(float(statistics.mean(per_seed)))
    boot.sort()
    return {
        "observed_seed_values": observed,
        "observed_mean": observed_mean,
        "ci95": [percentile(boot, 0.025), percentile(boot, 0.975)],
    }


def build_markdown(results: dict) -> str:
    lines = [
        "# Patent Slice Bootstrap",
        "",
        "Bootstrap 95% confidence intervals for the external-panel patent diagnosis slices.",
        "",
        "## Year Bands",
        "",
        "| Slice | Count | base | DTI-LM | HyperPCM |",
        "|-------|-------|------|--------|----------|",
    ]
    for slice_name, payload in results["year_groups"].items():
        values = []
        for system in ["base", "DTI-LM", "HyperPCM"]:
            cell = payload["systems"][system]
            values.append(f"`{cell['observed_mean']:.4f} [{cell['ci95'][0]:.4f}, {cell['ci95'][1]:.4f}]`")
        lines.append(f"| `{slice_name}` | {payload['count']} | " + " | ".join(values) + " |")
    lines.extend(
        [
            "",
            "## Overlap Buckets",
            "",
            "| Slice | Count | base | DTI-LM | HyperPCM |",
            "|-------|-------|------|--------|----------|",
        ]
    )
    for slice_name, payload in results["overlap_buckets"].items():
        values = []
        for system in ["base", "DTI-LM", "HyperPCM"]:
            cell = payload["systems"][system]
            values.append(f"`{cell['observed_mean']:.4f} [{cell['ci95'][0]:.4f}, {cell['ci95'][1]:.4f}]`")
        lines.append(f"| `{slice_name}` | {payload['count']} | " + " | ".join(values) + " |")
    return "\n".join(lines)


def main() -> None:
    args = parse_args()
    years = load_years()
    year_groups = {
        "2019": np.asarray([i for i, y in enumerate(years) if y == 2019], dtype=np.int32),
        "2020-2021": np.asarray([i for i, y in enumerate(years) if y >= 2020], dtype=np.int32),
    }

    loaded = {system: [load_preds(path) for path in paths] for system, paths in SYSTEM_PATHS.items()}
    base_overlap = loaded["base"][0]["overlap"]
    q1, q2 = np.quantile(base_overlap, [1 / 3, 2 / 3])
    overlap_groups = {
        f"0 (0.000-{q1:.3f})": np.asarray(np.where(base_overlap <= q1)[0], dtype=np.int32),
        f"1 ({q1:.3f}-{q2:.3f})": np.asarray(np.where((base_overlap > q1) & (base_overlap <= q2))[0], dtype=np.int32),
        f"2 ({q2:.3f}-{float(np.max(base_overlap)):.3f})": np.asarray(np.where(base_overlap > q2)[0], dtype=np.int32),
    }

    results = {"year_groups": {}, "overlap_buckets": {}}
    for name, indices in year_groups.items():
        results["year_groups"][name] = {"count": int(len(indices)), "systems": {}}
        for system, seeds in loaded.items():
            seed_data = [(seed["labels"][indices], seed["probs"][indices]) for seed in seeds]
            results["year_groups"][name]["systems"][system] = bootstrap_mean_auprc(seed_data, args.num_bootstrap, args.seed)

    for name, indices in overlap_groups.items():
        results["overlap_buckets"][name] = {"count": int(len(indices)), "systems": {}}
        for system, seeds in loaded.items():
            seed_data = [(seed["labels"][indices], seed["probs"][indices]) for seed in seeds]
            results["overlap_buckets"][name]["systems"][system] = bootstrap_mean_auprc(seed_data, args.num_bootstrap, args.seed)

    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(results, indent=2))
    args.output_md.write_text(build_markdown(results))
    print(json.dumps({"saved_json": str(args.output_json), "saved_md": str(args.output_md)}))


if __name__ == "__main__":
    main()
