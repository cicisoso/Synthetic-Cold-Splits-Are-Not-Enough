#!/usr/bin/env bash
set -euo pipefail

eval "$(/root/miniconda3/bin/conda shell.bash hook)"
conda activate research

PYTHONPATH=src python scripts/train_raicd.py \
  --dataset BindingDB_Kd \
  --split unseen_drug \
  --model raicd \
  --epochs 2 \
  --batch-size 128 \
  --max-train-samples 4096 \
  --max-valid-samples 1024 \
  --max-test-samples 1024 \
  --output-dir results/smoke
