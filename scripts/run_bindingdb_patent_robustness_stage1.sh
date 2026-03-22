#!/usr/bin/env bash
set -euo pipefail
cd /root/exp/dti_codex

mkdir -p logs \
  results/full_bindingdb_patent_v2017_base \
  results/recent_dtilm_patent_v2017_stage1

eval "$(/root/miniconda3/bin/conda shell.bash hook)"
conda activate research
export PYTHONPATH=src

SPLIT="patent_temporal_v2017"
LOG="logs/bindingdb_patent_robustness_stage1.log"

run_if_missing() {
  local outfile="$1"
  shift
  if [[ -f "$outfile" ]]; then
    echo "SKIP $outfile exists" | tee -a "$LOG"
    return 0
  fi
  "$@" | tee -a "$LOG"
}

run_if_missing \
  "results/full_bindingdb_patent_v2017_base/BindingDB_patent_${SPLIT}_base_seed0.json" \
  python scripts/train_raicd.py \
    --dataset BindingDB_patent \
    --split "$SPLIT" \
    --model base \
    --seed 0 \
    --epochs 6 \
    --batch-size 256 \
    --output-dir results/full_bindingdb_patent_v2017_base

run_if_missing \
  "results/recent_dtilm_patent_v2017_stage1/BindingDB_patent_${SPLIT}_dtilm_seed0.json" \
  python scripts/train_recent_baseline.py \
    --dataset BindingDB_patent \
    --split "$SPLIT" \
    --model dtilm \
    --seed 0 \
    --epochs 4 \
    --batch-size 64 \
    --encoder-batch-size 2 \
    --output-dir results/recent_dtilm_patent_v2017_stage1
