#!/usr/bin/env bash
set -euo pipefail

mkdir -p logs \
  results/drugban_unseen_drug_multiseed \
  results/drugban_blind_start_multiseed \
  results/drugban_unseen_target_multiseed \
  results/drugban_patent_multiseed \
  results/drugban_nonpatent_multiseed \
  results/drugban_ki_support_multiseed \
  results/drugban_davis_support_multiseed

run_if_missing() {
  local output_json="$1"
  shift
  if [ -f "$output_json" ]; then
    echo "{\"skip\":\"$output_json\"}" | tee -a logs/drugban_topline_multiseed.log
    return 0
  fi
  PYTHONPATH=src python scripts/train_graph_baseline.py "$@" | tee -a logs/drugban_topline_multiseed.log
}

for seed in 0 1 2; do
  # Synthetic reference panel
  run_if_missing \
    "results/drugban_unseen_drug_multiseed/BindingDB_Kd_unseen_drug_drugban_seed${seed}.json" \
    --dataset BindingDB_Kd --split unseen_drug --model drugban --seed "$seed" \
    --epochs 8 --batch-size 64 \
    --output-dir results/drugban_unseen_drug_multiseed

  run_if_missing \
    "results/drugban_blind_start_multiseed/BindingDB_Kd_blind_start_drugban_seed${seed}.json" \
    --dataset BindingDB_Kd --split blind_start --model drugban --seed "$seed" \
    --epochs 8 --batch-size 64 \
    --output-dir results/drugban_blind_start_multiseed

  run_if_missing \
    "results/drugban_unseen_target_multiseed/BindingDB_Kd_unseen_target_drugban_seed${seed}.json" \
    --dataset BindingDB_Kd --split unseen_target --model drugban --seed "$seed" \
    --epochs 8 --batch-size 64 \
    --output-dir results/drugban_unseen_target_multiseed

  # Primary temporal/provenance panel
  run_if_missing \
    "results/drugban_patent_multiseed/BindingDB_patent_patent_temporal_drugban_seed${seed}.json" \
    --dataset BindingDB_patent --split patent_temporal --model drugban --seed "$seed" \
    --epochs 6 --batch-size 64 \
    --output-dir results/drugban_patent_multiseed

  run_if_missing \
    "results/drugban_nonpatent_multiseed/BindingDB_nonpatent_Kd_nonpatent_temporal_drugban_seed${seed}.json" \
    --dataset BindingDB_nonpatent_Kd --split nonpatent_temporal --model drugban --seed "$seed" \
    --epochs 6 --batch-size 64 \
    --output-dir results/drugban_nonpatent_multiseed

  # Supporting OOD benchmarks
  run_if_missing \
    "results/drugban_ki_support_multiseed/BindingDB_Ki_unseen_target_drugban_seed${seed}.json" \
    --dataset BindingDB_Ki --split unseen_target --model drugban --seed "$seed" \
    --epochs 6 --batch-size 64 \
    --output-dir results/drugban_ki_support_multiseed

  run_if_missing \
    "results/drugban_davis_support_multiseed/DAVIS_unseen_target_drugban_seed${seed}.json" \
    --dataset DAVIS --split unseen_target --model drugban --seed "$seed" \
    --epochs 8 --batch-size 64 \
    --output-dir results/drugban_davis_support_multiseed
done

echo "drugban topline multiseed complete" | tee -a logs/drugban_topline_multiseed.log
