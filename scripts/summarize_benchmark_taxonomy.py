#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path


BENCHMARKS = [
    {
        "name": "BindingDB_Kd / unseen_drug",
        "path": "results/full_base/BindingDB_Kd_unseen_drug_base_seed0.json",
        "synthetic": "yes",
        "shift_axes": "unseen drug IDs",
        "time_shift": "no",
        "assay_or_source_shift": "no",
        "overlap_regime": "drug-cold, target overlap remains",
    },
    {
        "name": "BindingDB_Kd / blind_start",
        "path": "results/full_blind_base/BindingDB_Kd_blind_start_base_seed0.json",
        "synthetic": "yes",
        "shift_axes": "unseen drug IDs + unseen target IDs",
        "time_shift": "no",
        "assay_or_source_shift": "no",
        "overlap_regime": "drug-cold and target-cold",
    },
    {
        "name": "BindingDB_Kd / unseen_target",
        "path": "results/full_unseen_target_base/BindingDB_Kd_unseen_target_base_seed0.json",
        "synthetic": "yes",
        "shift_axes": "unseen target IDs",
        "time_shift": "no",
        "assay_or_source_shift": "no",
        "overlap_regime": "target-cold, drug overlap remains",
    },
    {
        "name": "BindingDB_patent / patent_temporal",
        "path": "results/full_bindingdb_patent_base/BindingDB_patent_patent_temporal_base_seed0.json",
        "synthetic": "no",
        "shift_axes": "time + provenance/source change",
        "time_shift": "yes",
        "assay_or_source_shift": "yes",
        "overlap_regime": "partial drug and target overlap",
    },
    {
        "name": "BindingDB_Ki / unseen_target",
        "path": "results/full_bindingdb_ki_unseen_target_base/BindingDB_Ki_unseen_target_base_seed0.json",
        "synthetic": "mixed",
        "shift_axes": "target holdout + assay-family change",
        "time_shift": "no",
        "assay_or_source_shift": "yes",
        "overlap_regime": "target-cold under assay shift",
    },
    {
        "name": "DAVIS / unseen_target",
        "path": "results/full_davis_unseen_target_base/DAVIS_unseen_target_base_seed0.json",
        "synthetic": "mixed",
        "shift_axes": "target holdout + dataset shift",
        "time_shift": "no",
        "assay_or_source_shift": "yes",
        "overlap_regime": "target-cold under dataset shift",
    },
]


def load_result(path: Path) -> dict:
    with path.open() as fh:
        return json.load(fh)


def positive_rate(labels: list[int]) -> float:
    return sum(labels) / len(labels)


def build_markdown() -> str:
    lines = [
        "# Benchmark Taxonomy",
        "",
        "This table documents the shift axes and split statistics used in the paper. Counts and test prevalence are reported from seed0 result files for consistency.",
        "",
        "| Benchmark | Synthetic? | Shift Axes | Time Shift | Assay/Source Shift | Overlap Regime | Test Rows | Test Positive Rate |",
        "|-----------|------------|------------|------------|--------------------|----------------|-----------|--------------------|",
    ]
    for bench in BENCHMARKS:
        result = load_result(Path(bench["path"]))
        test_rows = int(result["test_rows"])
        test_pos = positive_rate([int(x) for x in result["test_predictions"]["labels"]])
        lines.append(
            f"| `{bench['name']}` | {bench['synthetic']} | {bench['shift_axes']} | {bench['time_shift']} | "
            f"{bench['assay_or_source_shift']} | {bench['overlap_regime']} | {test_rows} | `{test_pos:.4f}` |"
        )
    lines.extend(
        [
            "",
            "## Main-Text Use",
            "",
            "- Use this taxonomy table in the Setup section or appendix to justify why `BindingDB_patent` should be described as temporal/provenance OOD rather than pure time shift.",
            "- Use the test positive rate column to remind readers that AUPRC should be interpreted within benchmark, not across benchmark families.",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    output = Path("reports/BENCHMARK_TAXONOMY.md")
    output.write_text(build_markdown() + "\n")
    print(output)


if __name__ == "__main__":
    main()
