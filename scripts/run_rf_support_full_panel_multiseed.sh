#!/usr/bin/env bash
set -euo pipefail

cd /root/exp/dti_codex

mkdir -p \
  logs \
  results/rf_ki_multiseed \
  results/rf_davis_multiseed

LOG=logs/rf_support_full_panel_multiseed.log

eval "$(/root/miniconda3/bin/conda shell.bash hook)"
conda activate research
export PYTHONPATH=src

run_if_missing() {
  local output_json="$1"
  shift
  if [ -f "$output_json" ]; then
    echo "{\"skip\":\"$output_json\"}" | tee -a "$LOG"
    return 0
  fi
  python scripts/train_classical_baseline.py "$@" | tee -a "$LOG"
}

for seed in 0 1 2; do
  run_if_missing \
    "results/rf_ki_multiseed/BindingDB_Ki_unseen_target_rf_seed${seed}.json" \
    --dataset BindingDB_Ki --split unseen_target --model rf --seed "$seed" \
    --n-estimators 400 \
    --output-dir results/rf_ki_multiseed

  run_if_missing \
    "results/rf_davis_multiseed/DAVIS_unseen_target_rf_seed${seed}.json" \
    --dataset DAVIS --split unseen_target --model rf --seed "$seed" \
    --n-estimators 400 \
    --output-dir results/rf_davis_multiseed
done

echo "rf support full-panel multiseed complete" | tee -a "$LOG"
