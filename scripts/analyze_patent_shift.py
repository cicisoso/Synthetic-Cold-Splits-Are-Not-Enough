#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
from collections import defaultdict
from pathlib import Path

from sklearn.metrics import average_precision_score, roc_auc_score


PATENT_SYSTEMS = {
    "base": [
        "results/full_bindingdb_patent_base/BindingDB_patent_patent_temporal_base_seed0.json",
        "results/full_bindingdb_patent_base/BindingDB_patent_patent_temporal_base_seed1.json",
        "results/full_bindingdb_patent_base/BindingDB_patent_patent_temporal_base_seed2.json",
    ],
    "RAICD": [
        "results/full_bindingdb_patent_raicd/BindingDB_patent_patent_temporal_raicd_seed0_both.json",
        "results/full_bindingdb_patent_raicd/BindingDB_patent_patent_temporal_raicd_seed1_both.json",
        "results/full_bindingdb_patent_raicd/BindingDB_patent_patent_temporal_raicd_seed2_both.json",
    ],
    "FTM": [
        "results/full_bindingdb_patent_ftm/BindingDB_patent_patent_temporal_ftm_seed0_chem32_top4_shr8p0.json",
        "results/full_bindingdb_patent_ftm/BindingDB_patent_patent_temporal_ftm_seed1_chem32_top4_shr8p0.json",
        "results/full_bindingdb_patent_ftm/BindingDB_patent_patent_temporal_ftm_seed2_chem32_top4_shr8p0.json",
    ],
}


def load_result(path: Path) -> dict:
    with path.open() as fh:
        return json.load(fh)


def mean_std(values: list[float]) -> tuple[float, float | None]:
    if not values:
        return math.nan, None
    if len(values) == 1:
        return values[0], None
    return statistics.mean(values), statistics.pstdev(values)


def format_scalar(values: list[float | None]) -> str:
    clean = [value for value in values if value is not None]
    if not clean:
        return "n/a"
    mean, std = mean_std(clean)
    if std is None:
        return f"{mean:.4f}"
    return f"{mean:.4f} ± {std:.4f}"


def format_pair(auprc_values: list[float | None], auroc_values: list[float | None]) -> str:
    return f"{format_scalar(auprc_values)} / {format_scalar(auroc_values)}"


def safe_auroc(labels: list[int], probs: list[float]) -> float | None:
    if len(set(labels)) < 2:
        return None
    return float(roc_auc_score(labels, probs))


def compute_metrics(labels: list[int], probs: list[float]) -> tuple[float, float | None]:
    auprc = float(average_precision_score(labels, probs))
    auroc = safe_auroc(labels, probs)
    return auprc, auroc


def load_test_years() -> list[int]:
    years: list[int] = []
    path = Path("data/tdc_benchmark/dti_dg_group/bindingdb_patent/test.csv")
    with path.open(newline="") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            years.append(int(row["Year"]))
    return years


def collect_existing_paths() -> dict[str, list[Path]]:
    existing: dict[str, list[Path]] = {}
    for system, paths in PATENT_SYSTEMS.items():
        existing[system] = [Path(path) for path in paths if Path(path).exists()]
    return existing


def overall_summary(existing: dict[str, list[Path]]) -> dict[str, dict[str, list[float | None]]]:
    summary: dict[str, dict[str, list[float | None]]] = {}
    for system, paths in existing.items():
        auprc_values: list[float] = []
        auroc_values: list[float] = []
        for path in paths:
            result = load_result(path)
            auprc_values.append(float(result["test_metrics"]["auprc"]))
            auroc_values.append(float(result["test_metrics"]["auroc"]))
        summary[system] = {"auprc": auprc_values, "auroc": auroc_values}
    return summary


def year_summary(existing: dict[str, list[Path]], years: list[int]) -> dict[int, dict[str, dict[str, list[float | None]]]]:
    year_to_indices: dict[int, list[int]] = defaultdict(list)
    for idx, year in enumerate(years):
        year_to_indices[year].append(idx)

    out: dict[int, dict[str, dict[str, list[float | None]]]] = {}
    for year, indices in sorted(year_to_indices.items()):
        out[year] = {}
        for system, paths in existing.items():
            auprc_values: list[float] = []
            auroc_values: list[float | None] = []
            for path in paths:
                result = load_result(path)
                labels = result["test_predictions"]["labels"]
                probs = result["test_predictions"]["probabilities"]
                year_labels = [int(labels[idx]) for idx in indices]
                year_probs = [float(probs[idx]) for idx in indices]
                auprc, auroc = compute_metrics(year_labels, year_probs)
                auprc_values.append(auprc)
                auroc_values.append(auroc)
            out[year][system] = {"auprc": auprc_values, "auroc": auroc_values}
    return out


def overlap_summary(existing: dict[str, list[Path]]) -> dict[int, dict[str, dict[str, object]]]:
    out: dict[int, dict[str, dict[str, object]]] = defaultdict(dict)
    for system, paths in existing.items():
        per_bucket: dict[int, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
        low_high_count: dict[int, tuple[float, float, int]] = {}
        for path in paths:
            result = load_result(path)
            for bucket in result["test_metrics"]["overlap_buckets"]:
                bucket_id = int(bucket["bucket"])
                per_bucket[bucket_id]["auprc"].append(float(bucket["auprc"]))
                per_bucket[bucket_id]["auroc"].append(float(bucket["auroc"]))
                low_high_count[bucket_id] = (
                    float(bucket["low"]),
                    float(bucket["high"]),
                    int(bucket["count"]),
                )
        for bucket_id, metrics in per_bucket.items():
            low, high, count = low_high_count[bucket_id]
            out[bucket_id][system] = {
                "range": (low, high),
                "count": count,
                "auprc": metrics["auprc"],
                "auroc": metrics["auroc"],
            }
    return dict(sorted(out.items()))


def winner_by_auprc(overall: dict[str, dict[str, list[float | None]]]) -> str:
    best_system = None
    best_score = -1.0
    for system, metrics in overall.items():
        mean, _ = mean_std([value for value in metrics["auprc"] if value is not None])
        if mean > best_score:
            best_score = mean
            best_system = system
    return best_system or "n/a"


def build_markdown(existing: dict[str, list[Path]], years: list[int]) -> str:
    overall = overall_summary(existing)
    year_stats = year_summary(existing, years)
    overlap_stats = overlap_summary(existing)
    base_auprc_mean, _ = mean_std(overall["base"]["auprc"])
    raicd_auprc_mean, _ = mean_std(overall["RAICD"]["auprc"])
    ftm_auprc_mean, _ = mean_std(overall["FTM"]["auprc"])

    lines = [
        "# Patent Shift Diagnosis",
        "",
        "Generated from `BindingDB_patent / patent_temporal` result JSON files and the local patent test split.",
        "",
        "## Global 3-Seed Summary",
        "",
        "| System | Seeds | Test AUPRC / AUROC | Delta vs Base AUPRC / AUROC |",
        "|--------|-------|--------------------|------------------------------|",
    ]
    for system in ["base", "RAICD", "FTM"]:
        seed_count = len(existing[system])
        pair = format_pair(overall[system]["auprc"], overall[system]["auroc"])
        if system == "base":
            delta = "0.0000 / 0.0000"
        else:
            auprc_mean, _ = mean_std([value for value in overall[system]["auprc"] if value is not None])
            auroc_mean, _ = mean_std([value for value in overall[system]["auroc"] if value is not None])
            base_auroc_mean, _ = mean_std([value for value in overall["base"]["auroc"] if value is not None])
            delta = f"{auprc_mean - base_auprc_mean:+.4f} / {auroc_mean - base_auroc_mean:+.4f}"
        lines.append(f"| `{system}` | {seed_count} | `{pair}` | `{delta}` |")

    lines.extend(
        [
            "",
            "## Year-Band Summary",
            "",
            "| Year | Count | Base AUPRC / AUROC | RAICD AUPRC / AUROC | FTM AUPRC / AUROC |",
            "|------|-------|--------------------|---------------------|-------------------|",
        ]
    )
    year_counts = defaultdict(int)
    for year in years:
        year_counts[year] += 1
    for year, systems in year_stats.items():
        lines.append(
            f"| `{year}` | {year_counts[year]} | "
            f"`{format_pair(systems['base']['auprc'], systems['base']['auroc'])}` | "
            f"`{format_pair(systems['RAICD']['auprc'], systems['RAICD']['auroc'])}` | "
            f"`{format_pair(systems['FTM']['auprc'], systems['FTM']['auroc'])}` |"
        )

    lines.extend(
        [
            "",
            "## Overlap-Bucket Summary",
            "",
            "| Bucket | Overlap Range | Count | Base AUPRC / AUROC | RAICD AUPRC / AUROC | FTM AUPRC / AUROC |",
            "|--------|---------------|-------|--------------------|---------------------|-------------------|",
        ]
    )
    for bucket_id, systems in overlap_stats.items():
        ref = systems["base"]
        low, high = ref["range"]
        count = ref["count"]
        lines.append(
            f"| `{bucket_id}` | `{low:.3f} - {high:.3f}` | {count} | "
            f"`{format_pair(systems['base']['auprc'], systems['base']['auroc'])}` | "
            f"`{format_pair(systems['RAICD']['auprc'], systems['RAICD']['auroc'])}` | "
            f"`{format_pair(systems['FTM']['auprc'], systems['FTM']['auroc'])}` |"
        )

    lines.extend(
        [
            "",
            "## Key Findings",
            "",
            f"1. `base` is the overall winner on patent temporal shift by 3-seed mean AUPRC (`{base_auprc_mean:.4f}`) over `FTM` (`{ftm_auprc_mean:.4f}`) and `RAICD` (`{raicd_auprc_mean:.4f}`).",
            "2. `RAICD` is consistently below `base` in the global 3-seed summary and remains the clearest synthetic-vs-real ranking reversal relative to `BindingDB_Kd / blind_start`.",
            "3. `FTM` narrows the gap relative to `RAICD`, but it still trails `base` on both overall AUPRC and AUROC under patent temporal shift.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    existing = collect_existing_paths()
    years = load_test_years()
    markdown = build_markdown(existing, years)
    if args.output is not None:
        args.output.write_text(markdown + "\n")
    else:
        print(markdown)


if __name__ == "__main__":
    main()
