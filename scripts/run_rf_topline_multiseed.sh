#!/usr/bin/env bash
set -euo pipefail

mkdir -p logs \
  results/rf_unseen_drug_multiseed \
  results/rf_unseen_target_multiseed \
  results/rf_blind_multiseed \
  results/rf_patent_multiseed \
  results/rf_nonpatent_multiseed

run_if_missing() {
  local output_json="$1"
  shift
  if [ -f "$output_json" ]; then
    echo "{\"skip\":\"$output_json\"}" | tee -a logs/rf_topline_multiseed.log
    return 0
  fi
  PYTHONPATH=src python scripts/train_classical_baseline.py "$@" | tee -a logs/rf_topline_multiseed.log
}

for seed in 1 2; do
  run_if_missing \
    "results/rf_unseen_drug_multiseed/BindingDB_Kd_unseen_drug_rf_seed${seed}.json" \
    --dataset BindingDB_Kd --split unseen_drug --model rf --seed "$seed" \
    --n-estimators 400 \
    --output-dir results/rf_unseen_drug_multiseed

  run_if_missing \
    "results/rf_unseen_target_multiseed/BindingDB_Kd_unseen_target_rf_seed${seed}.json" \
    --dataset BindingDB_Kd --split unseen_target --model rf --seed "$seed" \
    --n-estimators 400 \
    --output-dir results/rf_unseen_target_multiseed

  run_if_missing \
    "results/rf_blind_multiseed/BindingDB_Kd_blind_start_rf_seed${seed}.json" \
    --dataset BindingDB_Kd --split blind_start --model rf --seed "$seed" \
    --n-estimators 400 \
    --output-dir results/rf_blind_multiseed

  run_if_missing \
    "results/rf_patent_multiseed/BindingDB_patent_patent_temporal_rf_seed${seed}.json" \
    --dataset BindingDB_patent --split patent_temporal --model rf --seed "$seed" \
    --n-estimators 400 \
    --output-dir results/rf_patent_multiseed

  run_if_missing \
    "results/rf_nonpatent_multiseed/BindingDB_nonpatent_Kd_nonpatent_temporal_rf_seed${seed}.json" \
    --dataset BindingDB_nonpatent_Kd --split nonpatent_temporal --model rf --seed "$seed" \
    --n-estimators 400 \
    --output-dir results/rf_nonpatent_multiseed
done

echo "rf topline multiseed complete" | tee -a logs/rf_topline_multiseed.log
