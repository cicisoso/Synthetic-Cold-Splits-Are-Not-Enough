#!/usr/bin/env python
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from raicd.benchmark_resource import benchmark_resource_dir
from raicd.decision_metrics import merged_decision_metrics


SYSTEMS = {
    "base": [
        "results/full_bindingdb_patent_base/BindingDB_patent_patent_temporal_base_seed0.json",
        "results/full_bindingdb_patent_base/BindingDB_patent_patent_temporal_base_seed1.json",
        "results/full_bindingdb_patent_base/BindingDB_patent_patent_temporal_base_seed2.json",
    ],
    "RF": [
        "results/rf_panel_stage1/BindingDB_patent_patent_temporal_rf_seed0.json",
        "results/rf_patent_multiseed/BindingDB_patent_patent_temporal_rf_seed1.json",
        "results/rf_patent_multiseed/BindingDB_patent_patent_temporal_rf_seed2.json",
    ],
    "DTI-LM": [
        "results/recent_panel_stage1/BindingDB_patent_patent_temporal_dtilm_seed0.json",
        "results/recent_dtilm_patent_multiseed/BindingDB_patent_patent_temporal_dtilm_seed1.json",
        "results/recent_dtilm_patent_multiseed/BindingDB_patent_patent_temporal_dtilm_seed2.json",
    ],
}


def load_seed_frame(result_path: Path) -> pd.DataFrame:
    payload = json.loads(result_path.read_text())
    if "resource_dir" in payload:
        resource_dir = Path(payload["resource_dir"])
    else:
        args = payload["args"]
        resource_dir = benchmark_resource_dir(
            base_dir=Path("benchmark_resources"),
            dataset=args["dataset"],
            split=args["split"],
            seed=int(args["seed"]),
        )
    reference = pd.read_csv(resource_dir / "test.csv")

    if "test_prediction_csv" in payload:
        pred_csv = Path(payload["test_prediction_csv"])
        predictions = pd.read_csv(pred_csv)[["example_id", "probability"]]
    else:
        preds = payload["test_predictions"]
        if "example_id" in preds:
            predictions = pd.DataFrame(
                {
                    "example_id": preds["example_id"],
                    "probability": preds["probabilities"],
                }
            )
        else:
            predictions = pd.DataFrame(
                {
                    "example_id": reference["example_id"].astype(str).tolist(),
                    "probability": preds["probabilities"],
                }
            )
    merged = reference.merge(predictions, on="example_id", how="inner")
    if len(merged) != len(reference):
        raise ValueError(f"Missing predictions for {result_path}")
    return merged


def summarize_metrics(metrics_list: list[dict]) -> dict:
    ef1 = [m["global_enrichment"]["ef_at_1pct"] for m in metrics_list]
    ef5 = [m["global_enrichment"]["ef_at_5pct"] for m in metrics_list]
    hit10 = [m["per_target"]["hit_rate"]["10"] for m in metrics_list]
    recall10 = [m["per_target"]["recall"]["10"] for m in metrics_list]
    macro_ap = [m["per_target"]["macro_auprc"] for m in metrics_list]
    return {
        "ef_at_1pct_mean": sum(ef1) / len(ef1),
        "ef_at_5pct_mean": sum(ef5) / len(ef5),
        "per_target_hit_at_10_mean": sum(hit10) / len(hit10),
        "per_target_recall_at_10_mean": sum(recall10) / len(recall10),
        "per_target_macro_auprc_mean": sum(macro_ap) / len(macro_ap),
    }


def main() -> None:
    out_json = Path("reports/patent_decision_panel.json")
    out_md = Path("reports/PATENT_DECISION_PANEL.md")
    payload = {}
    for system, paths in SYSTEMS.items():
        metrics_list = []
        for path_str in paths:
            merged = load_seed_frame(Path(path_str))
            metrics = merged_decision_metrics(merged)
            metrics_list.append(metrics)
        payload[system] = {
            "paths": paths,
            "summary": summarize_metrics(metrics_list),
        }

    out_json.write_text(json.dumps(payload, indent=2))

    lines = [
        "# Patent Decision Panel",
        "",
        "Decision-facing metrics on `BindingDB_patent / patent_temporal`, averaged over the matched 3-seed runs.",
        "",
        "| System | EF@1% | EF@5% | Per-target Hit@10 | Per-target Recall@10 | Per-target Macro-AUPRC |",
        "|--------|-------|-------|-------------------|----------------------|------------------------|",
    ]
    for system, item in payload.items():
        s = item["summary"]
        lines.append(
            f"| `{system}` | `{s['ef_at_1pct_mean']:.4f}` | `{s['ef_at_5pct_mean']:.4f}` | "
            f"`{s['per_target_hit_at_10_mean']:.4f}` | `{s['per_target_recall_at_10_mean']:.4f}` | "
            f"`{s['per_target_macro_auprc_mean']:.4f}` |"
        )
    best_ef1 = max(payload.items(), key=lambda kv: kv[1]["summary"]["ef_at_1pct_mean"])[0]
    best_hit10 = max(payload.items(), key=lambda kv: kv[1]["summary"]["per_target_hit_at_10_mean"])[0]
    lines.extend(
        [
            "",
            f"- Best mean `EF@1%`: `{best_ef1}`",
            f"- Best mean `per-target Hit@10`: `{best_hit10}`",
        ]
    )
    out_md.write_text("\n".join(lines) + "\n")
    print(json.dumps({"saved_json": str(out_json), "saved_md": str(out_md)}))


if __name__ == "__main__":
    main()
