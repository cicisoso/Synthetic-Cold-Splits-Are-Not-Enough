#!/usr/bin/env bash
set -euo pipefail
cd /root/exp/dti_codex
mkdir -p logs results/smoke_bindingdb_ki_unseen_target_base results/smoke_bindingdb_ki_unseen_target_ftm

eval "$('/root/miniconda3/bin/conda' shell.bash hook)"
conda activate research
export PYTHONPATH=src

python scripts/train_raicd.py \
  --dataset BindingDB_Ki \
  --split unseen_target \
  --model base \
  --seed 0 \
  --epochs 2 \
  --batch-size 128 \
  --max-train-samples 8192 \
  --max-valid-samples 2048 \
  --max-test-samples 2048 \
  --output-dir results/smoke_bindingdb_ki_unseen_target_base | tee -a logs/bindingdb_ki_unseen_target_smoke.log

python scripts/train_raicd.py \
  --dataset BindingDB_Ki \
  --split unseen_target \
  --model ftm \
  --seed 0 \
  --epochs 2 \
  --batch-size 128 \
  --max-train-samples 8192 \
  --max-valid-samples 2048 \
  --max-test-samples 2048 \
  --output-dir results/smoke_bindingdb_ki_unseen_target_ftm | tee -a logs/bindingdb_ki_unseen_target_smoke.log
