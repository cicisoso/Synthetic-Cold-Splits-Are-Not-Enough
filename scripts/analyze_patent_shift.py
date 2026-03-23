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

YEAR_GROUPS = [
    ("2019", [2019]),
    ("2020-2021", [2020, 2021]),
]


PANELS = {
    "internal": {
        "title": "Patent Shift Diagnosis",
        "systems": {
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
        },
    },
    "external": {
        "title": "Patent Shift Diagnosis (External Panel)",
        "systems": {
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
        },
    },
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


def collect_existing_paths(panel: dict[str, object]) -> dict[str, list[Path]]:
    existing: dict[str, list[Path]] = {}
    for system, paths in panel["systems"].items():
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


def year_summary(existing: dict[str, list[Path]], years: list[int]) -> dict[str, dict[str, dict[str, list[float | None]]]]:
    year_to_indices: dict[int, list[int]] = defaultdict(list)
    for idx, year in enumerate(years):
        year_to_indices[year].append(idx)

    out: dict[str, dict[str, dict[str, list[float | None]]]] = {}
    for label, grouped_years in YEAR_GROUPS:
        indices: list[int] = []
        for year in grouped_years:
            indices.extend(year_to_indices.get(year, []))
        if not indices:
            continue
        out[label] = {}
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
            out[label][system] = {"auprc": auprc_values, "auroc": auroc_values}
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


def build_markdown(existing: dict[str, list[Path]], years: list[int], title: str, ordered_systems: list[str]) -> str:
    overall = overall_summary(existing)
    year_stats = year_summary(existing, years)
    overlap_stats = overlap_summary(existing)
    base_auprc_mean, _ = mean_std(overall["base"]["auprc"])

    lines = [
        f"# {title}",
        "",
        "Generated from `BindingDB_patent / patent_temporal` result JSON files and the local patent test split.",
        "",
        "## Global 3-Seed Summary",
        "",
        "| System | Seeds | Test AUPRC / AUROC | Delta vs Base AUPRC / AUROC |",
        "|--------|-------|--------------------|------------------------------|",
    ]
    for system in ordered_systems:
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
            "| Year | Count | " + " | ".join(f"{system} AUPRC / AUROC" for system in ordered_systems) + " |",
            "|" + "|".join(["------", "-------"] + ["--------------------"] * len(ordered_systems)) + "|",
        ]
    )
    year_counts = defaultdict(int)
    for year in years:
        year_counts[str(year)] += 1
    grouped_counts = {
        "2019": year_counts["2019"],
        "2020-2021": year_counts["2020"] + year_counts["2021"],
    }
    for label, systems in year_stats.items():
        values = [f"`{format_pair(systems[system]['auprc'], systems[system]['auroc'])}`" for system in ordered_systems]
        lines.append(f"| `{label}` | {grouped_counts.get(label, 0)} | " + " | ".join(values) + " |")

    lines.extend(
        [
            "",
            "## Overlap-Bucket Summary",
            "",
            "| Bucket | Overlap Range | Count | " + " | ".join(f"{system} AUPRC / AUROC" for system in ordered_systems) + " |",
            "|" + "|".join(["--------", "---------------", "-------"] + ["--------------------"] * len(ordered_systems)) + "|",
        ]
    )
    for bucket_id, systems in overlap_stats.items():
        ref = systems["base"]
        low, high = ref["range"]
        count = ref["count"]
        values = [f"`{format_pair(systems[system]['auprc'], systems[system]['auroc'])}`" for system in ordered_systems]
        lines.append(f"| `{bucket_id}` | `{low:.3f} - {high:.3f}` | {count} | " + " | ".join(values) + " |")

    ordered_non_base = [system for system in ordered_systems if system != "base"]
    ranked = []
    for system in ordered_systems:
        mean_auprc, _ = mean_std([value for value in overall[system]["auprc"] if value is not None])
        ranked.append((system, mean_auprc))
    ranked.sort(key=lambda item: item[1], reverse=True)

    lines.extend(
        [
            "",
            "## Key Findings",
            "",
            f"1. `{ranked[0][0]}` is the overall winner on patent temporal shift by 3-seed mean AUPRC (`{ranked[0][1]:.4f}`).",
            f"2. `base` reaches `{base_auprc_mean:.4f}` mean AUPRC and is ranked "
            + ", ".join(f"`{system}` ({score:.4f})" for system, score in ranked if system != "base")
            + ".",
            f"3. The year-band and overlap-bucket views remain non-uniform, so aggregate temporal OOD cannot be reduced to a single scalar difficulty even within the {title.lower()}.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--panel", choices=sorted(PANELS.keys()), default="internal")
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    panel = PANELS[args.panel]
    existing = collect_existing_paths(panel)
    years = load_test_years()
    markdown = build_markdown(existing, years, title=panel["title"], ordered_systems=list(panel["systems"].keys()))
    if args.output is not None:
        args.output.write_text(markdown + "\n")
    else:
        print(markdown)


if __name__ == "__main__":
    main()
