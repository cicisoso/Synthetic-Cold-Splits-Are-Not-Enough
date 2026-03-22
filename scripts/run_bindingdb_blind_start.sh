#!/usr/bin/env bash
set -euo pipefail

eval "$(/root/miniconda3/bin/conda shell.bash hook)"
conda activate research

PYTHONPATH=src python scripts/train_raicd.py \
  --dataset BindingDB_Kd \
  --split blind_start \
  --model raicd \
  --epochs 8 \
  --batch-size 256 \
  --output-dir results/bindingdb_blind_start
