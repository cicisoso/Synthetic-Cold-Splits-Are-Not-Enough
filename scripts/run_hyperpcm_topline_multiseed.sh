#!/usr/bin/env bash
set -euo pipefail

mkdir -p logs \
  results/recent_hyperpcm_patent_multiseed \
  results/recent_hyperpcm_blind_multiseed \
  results/recent_hyperpcm_unseen_target_multiseed

run_if_missing() {
  local output_json="$1"
  shift
  if [ -f "$output_json" ]; then
    echo "{\"skip\":\"$output_json\"}" | tee -a logs/hyperpcm_topline_multiseed.log
    return 0
  fi
  PYTHONPATH=src python scripts/train_recent_baseline.py "$@" | tee -a logs/hyperpcm_topline_multiseed.log
}

for seed in 1 2; do
  run_if_missing \
    "results/recent_hyperpcm_patent_multiseed/BindingDB_patent_patent_temporal_hyperpcm_seed${seed}.json" \
    --dataset BindingDB_patent --split patent_temporal --model hyperpcm --seed "$seed" \
    --epochs 4 --batch-size 64 --encoder-batch-size 2 \
    --output-dir results/recent_hyperpcm_patent_multiseed

  run_if_missing \
    "results/recent_hyperpcm_blind_multiseed/BindingDB_Kd_blind_start_hyperpcm_seed${seed}.json" \
    --dataset BindingDB_Kd --split blind_start --model hyperpcm --seed "$seed" \
    --epochs 6 --batch-size 64 --encoder-batch-size 2 \
    --output-dir results/recent_hyperpcm_blind_multiseed

  run_if_missing \
    "results/recent_hyperpcm_unseen_target_multiseed/BindingDB_Kd_unseen_target_hyperpcm_seed${seed}.json" \
    --dataset BindingDB_Kd --split unseen_target --model hyperpcm --seed "$seed" \
    --epochs 6 --batch-size 64 --encoder-batch-size 2 \
    --output-dir results/recent_hyperpcm_unseen_target_multiseed
done
