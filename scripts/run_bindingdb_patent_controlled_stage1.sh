#!/usr/bin/env bash
set -euo pipefail

source /root/miniconda3/etc/profile.d/conda.sh
conda activate research
export PYTHONPATH=src

mkdir -p \
  logs \
  results/patent_controlled_base \
  results/patent_controlled_rf \
  results/patent_controlled_dtilm

LOG=logs/bindingdb_patent_controlled_stage1.log
: > "$LOG"

for SPLIT in patent_temporal_pair_novel patent_temporal_drug_novel; do
  python scripts/train_raicd.py \
    --dataset BindingDB_patent \
    --split "$SPLIT" \
    --model base \
    --seed 0 \
    --epochs 6 \
    --batch-size 256 \
    --output-dir results/patent_controlled_base | tee -a "$LOG"

  python scripts/train_classical_baseline.py \
    --dataset BindingDB_patent \
    --split "$SPLIT" \
    --model rf \
    --seed 0 \
    --output-dir results/patent_controlled_rf | tee -a "$LOG"

  python scripts/train_recent_baseline.py \
    --dataset BindingDB_patent \
    --split "$SPLIT" \
    --model dtilm \
    --seed 0 \
    --epochs 4 \
    --batch-size 64 \
    --encoder-batch-size 4 \
    --output-dir results/patent_controlled_dtilm | tee -a "$LOG"
done

echo "bindingdb patent controlled stage1 complete" | tee -a "$LOG"
