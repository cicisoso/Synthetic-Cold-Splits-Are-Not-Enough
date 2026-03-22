#!/usr/bin/env bash
set -euo pipefail
cd /root/exp/dti_codex
mkdir -p logs results/full_bindingdb_ki_unseen_target_base results/full_bindingdb_ki_unseen_target_ftm

eval "$('/root/miniconda3/bin/conda' shell.bash hook)"
conda activate research
export PYTHONPATH=src

python scripts/train_raicd.py \
  --dataset BindingDB_Ki \
  --split unseen_target \
  --model base \
  --seed 0 \
  --epochs 8 \
  --batch-size 256 \
  --output-dir results/full_bindingdb_ki_unseen_target_base | tee -a logs/bindingdb_ki_unseen_target_stage1.log

python scripts/train_raicd.py \
  --dataset BindingDB_Ki \
  --split unseen_target \
  --model ftm \
  --seed 0 \
  --epochs 8 \
  --batch-size 256 \
  --output-dir results/full_bindingdb_ki_unseen_target_ftm | tee -a logs/bindingdb_ki_unseen_target_stage1.log
