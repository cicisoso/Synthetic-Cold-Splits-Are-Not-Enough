#!/usr/bin/env bash
set -euo pipefail

eval "$(/root/miniconda3/bin/conda shell.bash hook)"
conda activate research
export PYTHONPATH=src

python scripts/train_raicd.py   --dataset BindingDB_Kd   --split unseen_target   --model ftm   --epochs 8   --batch-size 256   --num-chemotypes 32   --chemotype-topk 4   --profile-shrinkage 8.0   --output-dir results/full_ftm_unseen_target_sparse
