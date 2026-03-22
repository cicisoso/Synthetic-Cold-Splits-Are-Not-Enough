#!/usr/bin/env bash
set -euo pipefail
cd /root/exp/dti_codex
mkdir -p logs results/multiseed_unseen_drug_base results/multiseed_unseen_drug_raicd results/multiseed_blind_base results/multiseed_blind_raicd

eval "$('/root/miniconda3/bin/conda' shell.bash hook)"
conda activate research
export PYTHONPATH=src

run_if_missing() {
  local outfile="$1"
  shift
  if [[ -f "$outfile" ]]; then
    echo "SKIP $outfile exists" | tee -a logs/paper_push_regime_multiseed.log
    return 0
  fi
  python scripts/train_raicd.py "$@" | tee -a logs/paper_push_regime_multiseed.log
}

run_if_missing \
  results/multiseed_unseen_drug_base/BindingDB_Kd_unseen_drug_base_seed2.json \
  --dataset BindingDB_Kd --split unseen_drug --model base --seed 2 --epochs 6 --batch-size 256 --output-dir results/multiseed_unseen_drug_base

run_if_missing \
  results/multiseed_unseen_drug_raicd/BindingDB_Kd_unseen_drug_raicd_seed2_both.json \
  --dataset BindingDB_Kd --split unseen_drug --model raicd --seed 2 --epochs 6 --batch-size 256 --output-dir results/multiseed_unseen_drug_raicd

run_if_missing \
  results/multiseed_blind_base/BindingDB_Kd_blind_start_base_seed1.json \
  --dataset BindingDB_Kd --split blind_start --model base --seed 1 --epochs 6 --batch-size 256 --output-dir results/multiseed_blind_base

run_if_missing \
  results/multiseed_blind_raicd/BindingDB_Kd_blind_start_raicd_seed1_both.json \
  --dataset BindingDB_Kd --split blind_start --model raicd --seed 1 --epochs 6 --batch-size 256 --output-dir results/multiseed_blind_raicd

run_if_missing \
  results/multiseed_blind_base/BindingDB_Kd_blind_start_base_seed2.json \
  --dataset BindingDB_Kd --split blind_start --model base --seed 2 --epochs 6 --batch-size 256 --output-dir results/multiseed_blind_base

run_if_missing \
  results/multiseed_blind_raicd/BindingDB_Kd_blind_start_raicd_seed2_both.json \
  --dataset BindingDB_Kd --split blind_start --model raicd --seed 2 --epochs 6 --batch-size 256 --output-dir results/multiseed_blind_raicd
