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
        "systems": {
            "base": [
                "results/full_base/BindingDB_Kd_unseen_drug_base_seed0.json",
                "results/multiseed_unseen_drug_base/BindingDB_Kd_unseen_drug_base_seed1.json",
                "results/multiseed_unseen_drug_base/BindingDB_Kd_unseen_drug_base_seed2.json",
            ],
            "DTI-LM": [
                "results/recent_dtilm_unseen_drug_multiseed/BindingDB_Kd_unseen_drug_dtilm_seed0.json",
                "results/recent_dtilm_unseen_drug_multiseed/BindingDB_Kd_unseen_drug_dtilm_seed1.json",
                "results/recent_dtilm_unseen_drug_multiseed/BindingDB_Kd_unseen_drug_dtilm_seed2.json",
            ],
            "HyperPCM": [
                "results/recent_hyperpcm_unseen_drug_multiseed/BindingDB_Kd_unseen_drug_hyperpcm_seed0.json",
                "results/recent_hyperpcm_unseen_drug_multiseed/BindingDB_Kd_unseen_drug_hyperpcm_seed1.json",
                "results/recent_hyperpcm_unseen_drug_multiseed/BindingDB_Kd_unseen_drug_hyperpcm_seed2.json",
            ],
        },
    },
    {
        "section": "Synthetic Reference Panel",
        "benchmark": "BindingDB_Kd / blind_start",
        "systems": {
            "base": [
                "results/full_blind_base/BindingDB_Kd_blind_start_base_seed0.json",
                "results/multiseed_blind_base/BindingDB_Kd_blind_start_base_seed1.json",
                "results/multiseed_blind_base/BindingDB_Kd_blind_start_base_seed2.json",
            ],
            "DTI-LM": [
                "results/recent_panel_stage1/BindingDB_Kd_blind_start_dtilm_seed0.json",
                "results/recent_dtilm_blind_multiseed/BindingDB_Kd_blind_start_dtilm_seed1.json",
                "results/recent_dtilm_blind_multiseed/BindingDB_Kd_blind_start_dtilm_seed2.json",
            ],
            "HyperPCM": [
                "results/recent_panel_stage1/BindingDB_Kd_blind_start_hyperpcm_seed0.json",
                "results/recent_hyperpcm_blind_multiseed/BindingDB_Kd_blind_start_hyperpcm_seed1.json",
                "results/recent_hyperpcm_blind_multiseed/BindingDB_Kd_blind_start_hyperpcm_seed2.json",
            ],
        },
    },
    {
        "section": "Synthetic Reference Panel",
        "benchmark": "BindingDB_Kd / unseen_target",
        "systems": {
            "base": [
                "results/full_unseen_target_base_multiseed/BindingDB_Kd_unseen_target_base_seed0.json",
                "results/full_unseen_target_base_multiseed/BindingDB_Kd_unseen_target_base_seed1.json",
                "results/full_unseen_target_base_multiseed/BindingDB_Kd_unseen_target_base_seed2.json",
            ],
            "DTI-LM": [
                "results/recent_panel_stage1/BindingDB_Kd_unseen_target_dtilm_seed0.json",
                "results/recent_dtilm_unseen_target_multiseed/BindingDB_Kd_unseen_target_dtilm_seed1.json",
                "results/recent_dtilm_unseen_target_multiseed/BindingDB_Kd_unseen_target_dtilm_seed2.json",
            ],
            "HyperPCM": [
                "results/recent_panel_stage1/BindingDB_Kd_unseen_target_hyperpcm_seed0.json",
                "results/recent_hyperpcm_unseen_target_multiseed/BindingDB_Kd_unseen_target_hyperpcm_seed1.json",
                "results/recent_hyperpcm_unseen_target_multiseed/BindingDB_Kd_unseen_target_hyperpcm_seed2.json",
            ],
        },
    },
    {
        "section": "Primary Real-OOD Benchmark",
        "benchmark": "BindingDB_patent / patent_temporal",
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
    {
        "section": "Supporting Real-OOD Benchmarks",
        "benchmark": "BindingDB_Ki / unseen_target",
        "systems": {
            "base": [
                "results/full_bindingdb_ki_unseen_target_base_multiseed/BindingDB_Ki_unseen_target_base_seed0.json",
                "results/full_bindingdb_ki_unseen_target_base_multiseed/BindingDB_Ki_unseen_target_base_seed1.json",
                "results/full_bindingdb_ki_unseen_target_base_multiseed/BindingDB_Ki_unseen_target_base_seed2.json",
            ],
            "DTI-LM": [
                "results/recent_dtilm_ki_multiseed/BindingDB_Ki_unseen_target_dtilm_seed0.json",
                "results/recent_dtilm_ki_multiseed/BindingDB_Ki_unseen_target_dtilm_seed1.json",
                "results/recent_dtilm_ki_multiseed/BindingDB_Ki_unseen_target_dtilm_seed2.json",
            ],
            "HyperPCM": [
                "results/recent_hyperpcm_ki_multiseed/BindingDB_Ki_unseen_target_hyperpcm_seed0.json",
                "results/recent_hyperpcm_ki_multiseed/BindingDB_Ki_unseen_target_hyperpcm_seed1.json",
                "results/recent_hyperpcm_ki_multiseed/BindingDB_Ki_unseen_target_hyperpcm_seed2.json",
            ],
        },
    },
    {
        "section": "Supporting Real-OOD Benchmarks",
        "benchmark": "DAVIS / unseen_target",
        "systems": {
            "base": [
                "results/full_davis_unseen_target_base_multiseed/DAVIS_unseen_target_base_seed0.json",
                "results/full_davis_unseen_target_base_multiseed/DAVIS_unseen_target_base_seed1.json",
                "results/full_davis_unseen_target_base_multiseed/DAVIS_unseen_target_base_seed2.json",
            ],
            "DTI-LM": [
                "results/recent_dtilm_davis_multiseed/DAVIS_unseen_target_dtilm_seed0.json",
                "results/recent_dtilm_davis_multiseed/DAVIS_unseen_target_dtilm_seed1.json",
                "results/recent_dtilm_davis_multiseed/DAVIS_unseen_target_dtilm_seed2.json",
            ],
            "HyperPCM": [
                "results/recent_hyperpcm_davis_multiseed/DAVIS_unseen_target_hyperpcm_seed0.json",
                "results/recent_hyperpcm_davis_multiseed/DAVIS_unseen_target_hyperpcm_seed1.json",
                "results/recent_hyperpcm_davis_multiseed/DAVIS_unseen_target_hyperpcm_seed2.json",
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
    existing = [Path(path) for path in paths if Path(path).exists()]
    if not existing:
        return None
    values = [load_metrics(path) for path in existing]
    auprc = [value[0] for value in values]
    auroc = [value[1] for value in values]
    return {
        "count": len(existing),
        "expected": len(paths),
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


def winner_label(systems: dict[str, dict | None]) -> str:
    scored = [(name, summary["auprc_mean"]) for name, summary in systems.items() if summary is not None]
    if not scored:
        return "n/a"
    return max(scored, key=lambda item: item[1])[0]


def build_markdown() -> str:
    lines = [
        "# External Replacement Panel",
        "",
        "Generated from local result JSON files for `base`, `DTI-LM`, and `HyperPCM`.",
        "",
    ]
    for section in dict.fromkeys(item["section"] for item in BENCHMARKS):
        lines.append(f"## {section}")
        lines.append("")
        lines.append("| Benchmark | Seeds | Base AUPRC / AUROC | DTI-LM AUPRC / AUROC | HyperPCM AUPRC / AUROC | Delta vs Base | Winner |")
        lines.append("|-----------|-------|--------------------|----------------------|-------------------------|---------------|--------|")
        for bench in [item for item in BENCHMARKS if item["section"] == section]:
            systems = {name: summarize(paths) for name, paths in bench["systems"].items()}
            base = systems["base"]
            seeds = min(summary["count"] for summary in systems.values() if summary is not None)
            expected = max(summary["expected"] for summary in systems.values() if summary is not None)
            delta = ", ".join(
                [
                    f"DTI-LM {format_delta(systems['DTI-LM'], base)}",
                    f"HyperPCM {format_delta(systems['HyperPCM'], base)}",
                ]
            )
            lines.append(
                f"| `{bench['benchmark']}` | {seeds}/{expected} | "
                f"`{format_metrics(systems['base'])}` | "
                f"`{format_metrics(systems['DTI-LM'])}` | "
                f"`{format_metrics(systems['HyperPCM'])}` | "
                f"`{delta}` | `{winner_label(systems)}` |"
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
