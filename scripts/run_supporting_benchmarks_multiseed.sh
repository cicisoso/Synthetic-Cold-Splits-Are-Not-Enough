#!/usr/bin/env bash
set -euo pipefail

mkdir -p logs \
  results/full_bindingdb_ki_unseen_target_base_multiseed \
  results/full_bindingdb_ki_unseen_target_raicd_multiseed \
  results/full_bindingdb_ki_unseen_target_ftm_multiseed \
  results/full_davis_unseen_target_base_multiseed \
  results/full_davis_unseen_target_raicd_multiseed \
  results/full_davis_unseen_target_ftm_multiseed

run_if_missing() {
  local output_json="$1"
  shift
  if [ -f "$output_json" ]; then
    echo "{\"skip\":\"$output_json\"}" | tee -a logs/supporting_benchmarks_multiseed.log
    return 0
  fi
  PYTHONPATH=src python scripts/train_raicd.py "$@" | tee -a logs/supporting_benchmarks_multiseed.log
}

for seed in 0 1 2; do
  run_if_missing \
    "results/full_bindingdb_ki_unseen_target_base_multiseed/BindingDB_Ki_unseen_target_base_seed${seed}.json" \
    --dataset BindingDB_Ki --split unseen_target --model base --seed "$seed" --epochs 6 --batch-size 256 \
    --output-dir results/full_bindingdb_ki_unseen_target_base_multiseed
  run_if_missing \
    "results/full_bindingdb_ki_unseen_target_raicd_multiseed/BindingDB_Ki_unseen_target_raicd_seed${seed}_both.json" \
    --dataset BindingDB_Ki --split unseen_target --model raicd --seed "$seed" --epochs 6 --batch-size 256 \
    --output-dir results/full_bindingdb_ki_unseen_target_raicd_multiseed
  run_if_missing \
    "results/full_bindingdb_ki_unseen_target_ftm_multiseed/BindingDB_Ki_unseen_target_ftm_seed${seed}_chem32_top4_shr8p0.json" \
    --dataset BindingDB_Ki --split unseen_target --model ftm --seed "$seed" --epochs 6 --batch-size 256 \
    --output-dir results/full_bindingdb_ki_unseen_target_ftm_multiseed

  run_if_missing \
    "results/full_davis_unseen_target_base_multiseed/DAVIS_unseen_target_base_seed${seed}.json" \
    --dataset DAVIS --split unseen_target --model base --seed "$seed" --epochs 6 --batch-size 256 \
    --output-dir results/full_davis_unseen_target_base_multiseed
  run_if_missing \
    "results/full_davis_unseen_target_raicd_multiseed/DAVIS_unseen_target_raicd_seed${seed}_both.json" \
    --dataset DAVIS --split unseen_target --model raicd --seed "$seed" --epochs 6 --batch-size 256 \
    --output-dir results/full_davis_unseen_target_raicd_multiseed
  run_if_missing \
    "results/full_davis_unseen_target_ftm_multiseed/DAVIS_unseen_target_ftm_seed${seed}_chem32_top4_shr8p0.json" \
    --dataset DAVIS --split unseen_target --model ftm --seed "$seed" --epochs 6 --batch-size 256 \
    --output-dir results/full_davis_unseen_target_ftm_multiseed
done
