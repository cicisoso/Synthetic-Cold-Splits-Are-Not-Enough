#!/usr/bin/env bash
set -euo pipefail

mkdir -p logs results/recent_dtilm_support_stage1

run_if_missing() {
  local output_json="$1"
  shift
  if [ -f "$output_json" ]; then
    echo "{\"skip\":\"$output_json\"}" | tee -a logs/dtilm_support_stage1.log
    return 0
  fi
  PYTHONPATH=src python scripts/train_recent_baseline.py "$@" | tee -a logs/dtilm_support_stage1.log
}

run_if_missing \
  "results/recent_dtilm_support_stage1/BindingDB_Ki_unseen_target_dtilm_seed0.json" \
  --dataset BindingDB_Ki --split unseen_target --model dtilm --seed 0 \
  --epochs 6 --batch-size 64 --encoder-batch-size 2 \
  --output-dir results/recent_dtilm_support_stage1

run_if_missing \
  "results/recent_dtilm_support_stage1/DAVIS_unseen_target_dtilm_seed0.json" \
  --dataset DAVIS --split unseen_target --model dtilm --seed 0 \
  --epochs 6 --batch-size 64 --encoder-batch-size 2 \
  --output-dir results/recent_dtilm_support_stage1
