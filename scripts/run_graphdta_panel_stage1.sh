#!/usr/bin/env bash
set -euo pipefail

mkdir -p logs results/graphdta_panel_stage1

run_if_missing() {
  local output_json="$1"
  shift
  if [ -f "$output_json" ]; then
    echo "{\"skip\":\"$output_json\"}" | tee -a logs/graphdta_panel_stage1.log
    return 0
  fi
  PYTHONPATH=src python scripts/train_graph_baseline.py "$@" | tee -a logs/graphdta_panel_stage1.log
}

for split in unseen_drug unseen_target blind_start; do
  run_if_missing \
    "results/graphdta_panel_stage1/BindingDB_Kd_${split}_graphdta_seed0.json" \
    --dataset BindingDB_Kd --split "$split" --model graphdta --seed 0 \
    --epochs 6 --batch-size 64 --output-dir results/graphdta_panel_stage1
done

run_if_missing \
  "results/graphdta_panel_stage1/BindingDB_patent_patent_temporal_graphdta_seed0.json" \
  --dataset BindingDB_patent --split patent_temporal --model graphdta --seed 0 \
  --epochs 4 --batch-size 64 --output-dir results/graphdta_panel_stage1

run_if_missing \
  "results/graphdta_panel_stage1/BindingDB_nonpatent_Kd_nonpatent_temporal_graphdta_seed0.json" \
  --dataset BindingDB_nonpatent_Kd --split nonpatent_temporal --model graphdta --seed 0 \
  --epochs 4 --batch-size 64 --output-dir results/graphdta_panel_stage1
