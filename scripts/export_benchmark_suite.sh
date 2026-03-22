#!/usr/bin/env bash
set -euo pipefail

export_one() {
  local dataset="$1"
  local split="$2"
  local seed="$3"
  PYTHONPATH=src python scripts/export_benchmark_resource.py \
    --dataset "$dataset" \
    --split "$split" \
    --seed "$seed" \
    "$@"
}

COMMON_ARGS=(
  --output-base-dir benchmark_resources
  --cache-dir data/cache
)

for seed in 0 1 2; do
  PYTHONPATH=src python scripts/export_benchmark_resource.py \
    --dataset BindingDB_Kd \
    --split unseen_target \
    --seed "$seed" \
    "${COMMON_ARGS[@]}"
  PYTHONPATH=src python scripts/export_benchmark_resource.py \
    --dataset BindingDB_Kd \
    --split unseen_drug \
    --seed "$seed" \
    "${COMMON_ARGS[@]}"
  PYTHONPATH=src python scripts/export_benchmark_resource.py \
    --dataset BindingDB_Kd \
    --split blind_start \
    --seed "$seed" \
    "${COMMON_ARGS[@]}"
  PYTHONPATH=src python scripts/export_benchmark_resource.py \
    --dataset BindingDB_Ki \
    --split unseen_target \
    --seed "$seed" \
    "${COMMON_ARGS[@]}"
  PYTHONPATH=src python scripts/export_benchmark_resource.py \
    --dataset DAVIS \
    --split unseen_target \
    --seed "$seed" \
    "${COMMON_ARGS[@]}"
  PYTHONPATH=src python scripts/export_benchmark_resource.py \
    --dataset BindingDB_patent \
    --split patent_temporal \
    --seed "$seed" \
    "${COMMON_ARGS[@]}"
done
