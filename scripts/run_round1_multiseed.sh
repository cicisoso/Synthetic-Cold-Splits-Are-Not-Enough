#!/usr/bin/env bash
set -euo pipefail

eval "$(/root/miniconda3/bin/conda shell.bash hook)"
conda activate research

run() {
  local split="$1"
  local model="$2"
  local seed="$3"
  local outdir="$4"
  shift 4
  PYTHONPATH=src python scripts/train_raicd.py \
    --dataset BindingDB_Kd \
    --split "$split" \
    --model "$model" \
    --seed "$seed" \
    --epochs 6 \
    --batch-size 256 \
    --output-dir "$outdir" \
    "$@"
}

for seed in 0 1 2; do
  run unseen_drug base "$seed" results/multiseed_unseen_drug_base
  run unseen_drug raicd "$seed" results/multiseed_unseen_drug_raicd
  run blind_start base "$seed" results/multiseed_blind_base
  run blind_start raicd "$seed" results/multiseed_blind_raicd
done
