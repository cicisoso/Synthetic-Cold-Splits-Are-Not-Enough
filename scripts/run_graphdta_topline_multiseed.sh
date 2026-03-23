#!/usr/bin/env bash
set -euo pipefail

mkdir -p logs \
  results/graphdta_unseen_drug_multiseed \
  results/graphdta_unseen_target_multiseed \
  results/graphdta_patent_multiseed \
  results/graphdta_nonpatent_multiseed

run_if_missing() {
  local output_json="$1"
  shift
  if [ -f "$output_json" ]; then
    echo "{\"skip\":\"$output_json\"}" | tee -a logs/graphdta_topline_multiseed.log
    return 0
  fi
  PYTHONPATH=src python scripts/train_graph_baseline.py "$@" | tee -a logs/graphdta_topline_multiseed.log
}

for seed in 1 2; do
  run_if_missing \
    "results/graphdta_unseen_drug_multiseed/BindingDB_Kd_unseen_drug_graphdta_seed${seed}.json" \
    --dataset BindingDB_Kd --split unseen_drug --model graphdta --seed "$seed" \
    --epochs 6 --batch-size 64 \
    --output-dir results/graphdta_unseen_drug_multiseed

  run_if_missing \
    "results/graphdta_unseen_target_multiseed/BindingDB_Kd_unseen_target_graphdta_seed${seed}.json" \
    --dataset BindingDB_Kd --split unseen_target --model graphdta --seed "$seed" \
    --epochs 6 --batch-size 64 \
    --output-dir results/graphdta_unseen_target_multiseed

  run_if_missing \
    "results/graphdta_patent_multiseed/BindingDB_patent_patent_temporal_graphdta_seed${seed}.json" \
    --dataset BindingDB_patent --split patent_temporal --model graphdta --seed "$seed" \
    --epochs 4 --batch-size 64 \
    --output-dir results/graphdta_patent_multiseed

  run_if_missing \
    "results/graphdta_nonpatent_multiseed/BindingDB_nonpatent_Kd_nonpatent_temporal_graphdta_seed${seed}.json" \
    --dataset BindingDB_nonpatent_Kd --split nonpatent_temporal --model graphdta --seed "$seed" \
    --epochs 4 --batch-size 64 \
    --output-dir results/graphdta_nonpatent_multiseed
done

echo "graphdta topline multiseed complete" | tee -a logs/graphdta_topline_multiseed.log
