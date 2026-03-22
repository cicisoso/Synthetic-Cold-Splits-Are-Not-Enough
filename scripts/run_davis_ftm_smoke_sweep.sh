#!/usr/bin/env bash
set -euo pipefail
cd /root/exp/dti_codex
mkdir -p logs results/smoke_davis_ftm_sweep

eval "$('/root/miniconda3/bin/conda' shell.bash hook)"
conda activate research
export PYTHONPATH=src

run_variant() {
  local chemotypes="$1"
  local topk="$2"
  python scripts/train_raicd.py \
    --dataset DAVIS \
    --split unseen_target \
    --model ftm \
    --seed 0 \
    --epochs 2 \
    --batch-size 128 \
    --max-train-samples 4096 \
    --max-valid-samples 1024 \
    --max-test-samples 1024 \
    --num-chemotypes "$chemotypes" \
    --chemotype-topk "$topk" \
    --output-dir results/smoke_davis_ftm_sweep | tee -a logs/davis_ftm_smoke_sweep.log
}

run_variant 4 2
run_variant 8 2
run_variant 16 4
run_variant 32 4
