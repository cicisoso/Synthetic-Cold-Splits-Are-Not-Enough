#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path


BENCHMARKS = [
    {
        "section": "Synthetic Reference Panel",
        "benchmark": "BindingDB_Kd / unseen_drug",
        "note": "retrieval loses on mean AUPRC",
        "systems": {
            "base": [
                "results/full_base/BindingDB_Kd_unseen_drug_base_seed0.json",
                "results/multiseed_unseen_drug_base/BindingDB_Kd_unseen_drug_base_seed1.json",
                "results/multiseed_unseen_drug_base/BindingDB_Kd_unseen_drug_base_seed2.json",
            ],
            "RAICD": [
                "results/full_raicd_simattn/BindingDB_Kd_unseen_drug_raicd_seed0.json",
                "results/multiseed_unseen_drug_raicd/BindingDB_Kd_unseen_drug_raicd_seed1_both.json",
                "results/multiseed_unseen_drug_raicd/BindingDB_Kd_unseen_drug_raicd_seed2_both.json",
            ],
            "FTM": [],
        },
    },
    {
        "section": "Synthetic Reference Panel",
        "benchmark": "BindingDB_Kd / blind_start",
        "note": "retrieval wins on mean AUPRC",
        "systems": {
            "base": [
                "results/full_blind_base/BindingDB_Kd_blind_start_base_seed0.json",
                "results/multiseed_blind_base/BindingDB_Kd_blind_start_base_seed1.json",
                "results/multiseed_blind_base/BindingDB_Kd_blind_start_base_seed2.json",
            ],
            "RAICD": [
                "results/full_blind_raicd_simattn/BindingDB_Kd_blind_start_raicd_seed0.json",
                "results/multiseed_blind_raicd/BindingDB_Kd_blind_start_raicd_seed1_both.json",
                "results/multiseed_blind_raicd/BindingDB_Kd_blind_start_raicd_seed2_both.json",
            ],
            "FTM": [],
        },
    },
    {
        "section": "Synthetic Reference Panel",
        "benchmark": "BindingDB_Kd / unseen_target",
        "note": "target-memory wins on mean AUPRC",
        "systems": {
            "base": [
                "results/full_unseen_target_base_multiseed/BindingDB_Kd_unseen_target_base_seed0.json",
                "results/full_unseen_target_base_multiseed/BindingDB_Kd_unseen_target_base_seed1.json",
                "results/full_unseen_target_base_multiseed/BindingDB_Kd_unseen_target_base_seed2.json",
            ],
            "RAICD": [],
            "FTM": [
                "results/full_ftm_unseen_target_sparse_multiseed/BindingDB_Kd_unseen_target_ftm_seed0_chem32_top4_shr8p0.json",
                "results/full_ftm_unseen_target_sparse_multiseed/BindingDB_Kd_unseen_target_ftm_seed1_chem32_top4_shr8p0.json",
                "results/full_ftm_unseen_target_sparse_multiseed/BindingDB_Kd_unseen_target_ftm_seed2_chem32_top4_shr8p0.json",
            ],
        },
    },
    {
        "section": "Real-OOD Screening Panel",
        "benchmark": "BindingDB_patent / patent_temporal",
        "note": "temporal shift is the promoted real-OOD axis",
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
    {
        "section": "Real-OOD Screening Panel",
        "benchmark": "BindingDB_Ki / unseen_target",
        "note": "assay shift is negative for target-memory",
        "systems": {
            "base": [
                "results/full_bindingdb_ki_unseen_target_base/BindingDB_Ki_unseen_target_base_seed0.json",
            ],
            "RAICD": [],
            "FTM": [
                "results/full_bindingdb_ki_unseen_target_ftm/BindingDB_Ki_unseen_target_ftm_seed0_chem32_top4_shr8p0.json",
            ],
        },
    },
    {
        "section": "Real-OOD Screening Panel",
        "benchmark": "DAVIS / unseen_target",
        "note": "external dataset shift is negative for target-memory",
        "systems": {
            "base": [
                "results/full_davis_unseen_target_base/DAVIS_unseen_target_base_seed0.json",
            ],
            "RAICD": [],
            "FTM": [
                "results/full_davis_unseen_target_ftm/DAVIS_unseen_target_ftm_seed0_chem32_top4_shr8p0.json",
            ],
        },
    },
]


def load_metrics(path: Path) -> tuple[float, float]:
    with path.open() as fh:
        data = json.load(fh)
    metrics = data["test_metrics"]
    return float(metrics["auprc"]), float(metrics["auroc"])


def summarize(paths: list[str]) -> dict | None:
    if not paths:
        return None
    existing = [Path(path) for path in paths if Path(path).exists()]
    if not existing:
        return None
    values = [load_metrics(path) for path in existing]
    auprc = [value[0] for value in values]
    auroc = [value[1] for value in values]
    return {
        "count": len(existing),
        "expected": len(paths),
        "paths": existing,
        "auprc_mean": statistics.mean(auprc),
        "auroc_mean": statistics.mean(auroc),
        "auprc_std": statistics.pstdev(auprc) if len(auprc) > 1 else None,
        "auroc_std": statistics.pstdev(auroc) if len(auroc) > 1 else None,
    }


def format_metrics(summary: dict | None) -> str:
    if summary is None:
        return "n/a"
    if summary["count"] == 1:
        return f"{summary['auprc_mean']:.4f} / {summary['auroc_mean']:.4f}"
    return (
        f"{summary['auprc_mean']:.4f} ± {summary['auprc_std']:.4f} / "
        f"{summary['auroc_mean']:.4f} ± {summary['auroc_std']:.4f}"
    )


def format_delta(summary: dict | None, base: dict | None) -> str:
    if summary is None or base is None:
        return "n/a"
    return (
        f"{summary['auprc_mean'] - base['auprc_mean']:+.4f} / "
        f"{summary['auroc_mean'] - base['auroc_mean']:+.4f}"
    )


def format_seeds(systems: dict[str, dict | None]) -> str:
    counts = [summary["count"] for summary in systems.values() if summary is not None]
    totals = [summary["expected"] for summary in systems.values() if summary is not None]
    if not counts or not totals:
        return "0/0"
    return f"{min(counts)}/{max(totals)}"


def build_markdown() -> str:
    lines = [
        "# Live Benchmark Table",
        "",
        "Generated from local result JSON files.",
        "",
    ]
    sections = []
    for bench in BENCHMARKS:
        sections.append(bench["section"])
    for section in dict.fromkeys(sections):
        lines.append(f"## {section}")
        lines.append("")
        lines.append(
            "| Benchmark | Seeds | Base AUPRC / AUROC | RAICD AUPRC / AUROC | "
            "FTM AUPRC / AUROC | Delta vs Base | Note |"
        )
        lines.append(
            "|-----------|-------|--------------------|---------------------|-------------------|---------------|------|"
        )
        for bench in [item for item in BENCHMARKS if item["section"] == section]:
            systems = {name: summarize(paths) for name, paths in bench["systems"].items()}
            base = systems["base"]
            delta_parts = []
            if systems["RAICD"] is not None:
                delta_parts.append(f"RAICD {format_delta(systems['RAICD'], base)}")
            if systems["FTM"] is not None:
                delta_parts.append(f"FTM {format_delta(systems['FTM'], base)}")
            delta = ", ".join(delta_parts) if delta_parts else "n/a"
            lines.append(
                f"| `{bench['benchmark']}` | {format_seeds(systems)} | "
                f"`{format_metrics(systems['base'])}` | "
                f"`{format_metrics(systems['RAICD'])}` | "
                f"`{format_metrics(systems['FTM'])}` | "
                f"`{delta}` | {bench['note']} |"
            )
        lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()
    markdown = build_markdown()
    if args.output is not None:
        args.output.write_text(markdown + "\n")
    else:
        print(markdown)


if __name__ == "__main__":
    main()
