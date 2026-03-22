#!/usr/bin/env bash
set -euo pipefail

mkdir -p logs results/recent_panel_stage1

run_if_missing() {
  local output_json="$1"
  shift
  if [ -f "$output_json" ]; then
    echo "{\"skip\":\"$output_json\"}" | tee -a logs/recent_panel_stage1.log
    return 0
  fi
  PYTHONPATH=src python scripts/train_recent_baseline.py "$@" | tee -a logs/recent_panel_stage1.log
}

for split in unseen_target blind_start; do
run_if_missing \
  "results/recent_panel_stage1/BindingDB_Kd_${split}_dtilm_seed0.json" \
    --dataset BindingDB_Kd --split "$split" --model dtilm --seed 0 --epochs 6 --batch-size 64 --encoder-batch-size 4 \
    --output-dir results/recent_panel_stage1
  run_if_missing \
    "results/recent_panel_stage1/BindingDB_Kd_${split}_hyperpcm_seed0.json" \
    --dataset BindingDB_Kd --split "$split" --model hyperpcm --seed 0 --epochs 6 --batch-size 64 --encoder-batch-size 4 \
    --output-dir results/recent_panel_stage1
done

run_if_missing \
  "results/recent_panel_stage1/BindingDB_patent_patent_temporal_dtilm_seed0.json" \
  --dataset BindingDB_patent --split patent_temporal --model dtilm --seed 0 --epochs 4 --batch-size 64 --encoder-batch-size 4 \
  --output-dir results/recent_panel_stage1

run_if_missing \
  "results/recent_panel_stage1/BindingDB_patent_patent_temporal_hyperpcm_seed0.json" \
  --dataset BindingDB_patent --split patent_temporal --model hyperpcm --seed 0 --epochs 4 --batch-size 64 --encoder-batch-size 4 \
  --output-dir results/recent_panel_stage1
