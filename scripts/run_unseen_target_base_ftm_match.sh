#!/usr/bin/env bash
set -euo pipefail
cd /root/exp/dti_codex
mkdir -p logs results/full_unseen_target_base_multiseed results/meta_router_unseen_target_base_ftm_sparse_multiseed

eval "$('/root/miniconda3/bin/conda' shell.bash hook)"
conda activate research
export PYTHONPATH=src

for seed in 0 1 2; do
  python scripts/train_raicd.py \
    --dataset BindingDB_Kd \
    --split unseen_target \
    --model base \
    --seed "$seed" \
    --epochs 8 \
    --batch-size 256 \
    --output-dir results/full_unseen_target_base_multiseed | tee -a logs/unseen_target_base_ftm_match.log

  python scripts/train_meta_router.py \
    --seed "$seed" \
    --expert base=/root/exp/dti_codex/results/full_unseen_target_base_multiseed/BindingDB_Kd_unseen_target_base_seed${seed}.json \
    --expert ftm_sparse=/root/exp/dti_codex/results/full_ftm_unseen_target_sparse_multiseed/BindingDB_Kd_unseen_target_ftm_seed${seed}_chem32_top4_shr8p0.json \
    --output /root/exp/dti_codex/results/meta_router_unseen_target_base_ftm_sparse_multiseed/BindingDB_Kd_unseen_target_meta_router_seed${seed}.json | tee -a logs/unseen_target_base_ftm_match.log
 done
