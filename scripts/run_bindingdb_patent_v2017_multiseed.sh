#!/usr/bin/env bash
set -euo pipefail
cd /root/exp/dti_codex

mkdir -p logs \
  results/full_bindingdb_patent_v2017_base \
  results/recent_dtilm_patent_v2017_multiseed

LOG=logs/bindingdb_patent_v2017_multiseed.log

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
  "$@" | tee -a "$LOG"
}

for seed in 1 2; do
  run_if_missing \
    "results/full_bindingdb_patent_v2017_base/BindingDB_patent_patent_temporal_v2017_base_seed${seed}.json" \
    python scripts/train_raicd.py \
      --dataset BindingDB_patent \
      --split patent_temporal_v2017 \
      --model base \
      --seed "$seed" \
      --epochs 6 \
      --batch-size 256 \
      --output-dir results/full_bindingdb_patent_v2017_base

  run_if_missing \
    "results/recent_dtilm_patent_v2017_multiseed/BindingDB_patent_patent_temporal_v2017_dtilm_seed${seed}.json" \
    python scripts/train_recent_baseline.py \
      --dataset BindingDB_patent \
      --split patent_temporal_v2017 \
      --model dtilm \
      --seed "$seed" \
      --epochs 4 \
      --batch-size 64 \
      --encoder-batch-size 2 \
      --output-dir results/recent_dtilm_patent_v2017_multiseed
done
