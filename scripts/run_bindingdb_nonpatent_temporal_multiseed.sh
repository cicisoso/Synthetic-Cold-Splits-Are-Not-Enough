#!/usr/bin/env bash
set -euo pipefail

cd /root/exp/dti_codex
eval "$(/root/miniconda3/bin/conda shell.bash hook)"
conda activate research

LOG=logs/bindingdb_nonpatent_temporal_multiseed.log
mkdir -p logs

for seed in 1 2; do
  PYTHONPATH=src python scripts/train_raicd.py \
    --dataset BindingDB_nonpatent_Kd \
    --split nonpatent_temporal \
    --model base \
    --seed "$seed" \
    --epochs 8 \
    --output-dir results/full_bindingdb_nonpatent_temporal_base | tee -a "$LOG"

  PYTHONPATH=src python scripts/train_recent_baseline.py \
    --dataset BindingDB_nonpatent_Kd \
    --split nonpatent_temporal \
    --model dtilm \
    --seed "$seed" \
    --batch-size 64 \
    --encoder-batch-size 4 \
    --output-dir results/recent_bindingdb_nonpatent_temporal_dtilm | tee -a "$LOG"
done

echo "bindingdb nonpatent temporal multiseed complete" | tee -a "$LOG"
