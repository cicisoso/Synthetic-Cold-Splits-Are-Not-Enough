#!/usr/bin/env bash
set -euo pipefail

eval "$(/root/miniconda3/bin/conda shell.bash hook)"
conda activate research

cd /root/exp/dti_codex
mkdir -p logs
export PYTHONPATH="/root/exp/dti_codex/src:${PYTHONPATH:-}"

python scripts/train_recent_baseline.py \
  --dataset BindingDB_nonpatent_Kd \
  --split nonpatent_temporal \
  --model hyperpcm \
  --seed 0 \
  --epochs 4 \
  --batch-size 64 \
  --encoder-batch-size 2 \
  --output-dir results/recent_hyperpcm_nonpatent_multiseed \
  > logs/hyperpcm_nonpatent_seed0.log 2>&1

python scripts/train_recent_baseline.py \
  --dataset BindingDB_nonpatent_Kd \
  --split nonpatent_temporal \
  --model hyperpcm \
  --seed 1 \
  --epochs 4 \
  --batch-size 64 \
  --encoder-batch-size 2 \
  --output-dir results/recent_hyperpcm_nonpatent_multiseed \
  > logs/hyperpcm_nonpatent_seed1.log 2>&1

python scripts/train_recent_baseline.py \
  --dataset BindingDB_nonpatent_Kd \
  --split nonpatent_temporal \
  --model hyperpcm \
  --seed 2 \
  --epochs 4 \
  --batch-size 64 \
  --encoder-batch-size 2 \
  --output-dir results/recent_hyperpcm_nonpatent_multiseed \
  > logs/hyperpcm_nonpatent_seed2.log 2>&1

python scripts/train_graph_baseline.py \
  --dataset BindingDB_Kd \
  --split blind_start \
  --seed 1 \
  --epochs 6 \
  --batch-size 64 \
  --output-dir results/graphdta_blind_multiseed \
  > logs/graphdta_blind_seed1.log 2>&1

python scripts/train_graph_baseline.py \
  --dataset BindingDB_Kd \
  --split blind_start \
  --seed 2 \
  --epochs 6 \
  --batch-size 64 \
  --output-dir results/graphdta_blind_multiseed \
  > logs/graphdta_blind_seed2.log 2>&1
