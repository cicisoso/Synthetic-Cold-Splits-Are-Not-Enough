#!/usr/bin/env bash
set -euo pipefail
cd /root/exp/dti_codex
mkdir -p logs results/selective_ftm_unseen_target_multiseed

eval "$('/root/miniconda3/bin/conda' shell.bash hook)"
conda activate research
export PYTHONPATH=src

for seed in 0 1 2; do
  python scripts/eval_selective_ftm.py \
    --dataset BindingDB_Kd \
    --split unseen_target \
    --seed "$seed" \
    --base-ckpt "/root/exp/dti_codex/results/full_unseen_target_base_multiseed/BindingDB_Kd_unseen_target_base_seed${seed}.pt" \
    --ftm-ckpt "/root/exp/dti_codex/results/full_ftm_unseen_target_sparse_multiseed/BindingDB_Kd_unseen_target_ftm_seed${seed}_chem32_top4_shr8p0.pt" \
    --output "/root/exp/dti_codex/results/selective_ftm_unseen_target_multiseed/BindingDB_Kd_unseen_target_selective_seed${seed}.json" | tee -a logs/selective_ftm_unseen_target_multiseed.log
 done
