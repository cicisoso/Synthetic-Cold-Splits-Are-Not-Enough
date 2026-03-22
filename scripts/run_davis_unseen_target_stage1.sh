#!/usr/bin/env bash
set -euo pipefail
cd /root/exp/dti_codex
mkdir -p logs results/smoke_davis_unseen_target_base results/smoke_davis_unseen_target_ftm results/full_davis_unseen_target_base results/full_davis_unseen_target_ftm

eval "$('/root/miniconda3/bin/conda' shell.bash hook)"
conda activate research
export PYTHONPATH=src

python scripts/train_raicd.py \
  --dataset DAVIS \
  --split unseen_target \
  --model base \
  --seed 0 \
  --epochs 2 \
  --batch-size 128 \
  --max-train-samples 4096 \
  --max-valid-samples 1024 \
  --max-test-samples 1024 \
  --output-dir results/smoke_davis_unseen_target_base | tee -a logs/davis_unseen_target_stage1.log

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
  --output-dir results/smoke_davis_unseen_target_ftm | tee -a logs/davis_unseen_target_stage1.log

python scripts/train_raicd.py \
  --dataset DAVIS \
  --split unseen_target \
  --model base \
  --seed 0 \
  --epochs 8 \
  --batch-size 256 \
  --output-dir results/full_davis_unseen_target_base | tee -a logs/davis_unseen_target_stage1.log

python scripts/train_raicd.py \
  --dataset DAVIS \
  --split unseen_target \
  --model ftm \
  --seed 0 \
  --epochs 8 \
  --batch-size 256 \
  --output-dir results/full_davis_unseen_target_ftm | tee -a logs/davis_unseen_target_stage1.log
