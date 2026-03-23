#!/usr/bin/env bash
set -euo pipefail

cd /root/exp/dti_codex
eval "$(/root/miniconda3/bin/conda shell.bash hook)"
conda activate research

LOG=logs/bindingdb_scaffold_stage1.log
mkdir -p logs

PYTHONPATH=src python scripts/train_raicd.py \
  --dataset BindingDB_Kd \
  --split scaffold_drug \
  --model base \
  --seed 0 \
  --epochs 8 \
  --output-dir results/full_bindingdb_kd_scaffold_base | tee -a "$LOG"

PYTHONPATH=src python scripts/train_recent_baseline.py \
  --dataset BindingDB_Kd \
  --split scaffold_drug \
  --model dtilm \
  --seed 0 \
  --batch-size 64 \
  --encoder-batch-size 4 \
  --output-dir results/recent_bindingdb_kd_scaffold_dtilm | tee -a "$LOG"

PYTHONPATH=src python scripts/train_recent_baseline.py \
  --dataset BindingDB_Kd \
  --split scaffold_drug \
  --model hyperpcm \
  --seed 0 \
  --batch-size 64 \
  --encoder-batch-size 4 \
  --output-dir results/recent_bindingdb_kd_scaffold_hyperpcm | tee -a "$LOG"
