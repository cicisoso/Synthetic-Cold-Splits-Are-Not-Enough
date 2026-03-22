#!/usr/bin/env bash
set -euo pipefail
cd /root/exp/dti_codex
mkdir -p logs results/full_bindingdb_patent_base results/full_bindingdb_patent_raicd results/full_bindingdb_patent_ftm

LOG=logs/bindingdb_patent_multiseed.log

eval "$(/root/miniconda3/bin/conda shell.bash hook)"
conda activate research
export PYTHONPATH=src

run_if_missing() {
  local outfile="$1"
  shift
  if [[ -f "$outfile" ]]; then
    echo "SKIP $outfile exists" | tee -a "$LOG"
    return 0
  fi
  python scripts/train_raicd.py "$@" | tee -a "$LOG"
}

for seed in 1 2; do
  run_if_missing \
    "results/full_bindingdb_patent_base/BindingDB_patent_patent_temporal_base_seed${seed}.json" \
    --dataset BindingDB_patent --split patent_temporal --model base --seed "$seed" --epochs 6 --batch-size 256 --output-dir results/full_bindingdb_patent_base

  run_if_missing \
    "results/full_bindingdb_patent_raicd/BindingDB_patent_patent_temporal_raicd_seed${seed}_both.json" \
    --dataset BindingDB_patent --split patent_temporal --model raicd --seed "$seed" --epochs 6 --batch-size 256 --output-dir results/full_bindingdb_patent_raicd

  run_if_missing \
    "results/full_bindingdb_patent_ftm/BindingDB_patent_patent_temporal_ftm_seed${seed}_chem32_top4_shr8p0.json" \
    --dataset BindingDB_patent --split patent_temporal --model ftm --seed "$seed" --epochs 6 --batch-size 256 --output-dir results/full_bindingdb_patent_ftm
 done
