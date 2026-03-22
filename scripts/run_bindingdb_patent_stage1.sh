#!/usr/bin/env bash
set -euo pipefail
cd /root/exp/dti_codex
mkdir -p logs results/full_bindingdb_patent_base results/full_bindingdb_patent_raicd results/full_bindingdb_patent_ftm

eval "$('/root/miniconda3/bin/conda' shell.bash hook)"
conda activate research
export PYTHONPATH=src

python scripts/train_raicd.py \
  --dataset BindingDB_patent \
  --split patent_temporal \
  --model base \
  --seed 0 \
  --epochs 6 \
  --batch-size 256 \
  --output-dir results/full_bindingdb_patent_base | tee -a logs/bindingdb_patent_stage1.log

python scripts/train_raicd.py \
  --dataset BindingDB_patent \
  --split patent_temporal \
  --model raicd \
  --seed 0 \
  --epochs 6 \
  --batch-size 256 \
  --output-dir results/full_bindingdb_patent_raicd | tee -a logs/bindingdb_patent_stage1.log

python scripts/train_raicd.py \
  --dataset BindingDB_patent \
  --split patent_temporal \
  --model ftm \
  --seed 0 \
  --epochs 6 \
  --batch-size 256 \
  --output-dir results/full_bindingdb_patent_ftm | tee -a logs/bindingdb_patent_stage1.log
