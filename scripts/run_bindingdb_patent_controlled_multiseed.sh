#!/usr/bin/env bash
set -euo pipefail

cd /root/exp/dti_codex

mkdir -p \
  logs \
  results/patent_controlled_base \
  results/patent_controlled_rf \
  results/patent_controlled_dtilm

LOG=logs/bindingdb_patent_controlled_multiseed.log

eval "$(/root/miniconda3/bin/conda shell.bash hook)"
conda activate research
export PYTHONPATH=src

run_if_missing() {
  local output_json="$1"
  shift
  if [ -f "$output_json" ]; then
    echo "{\"skip\":\"$output_json\"}" | tee -a "$LOG"
    return 0
  fi
  python "$@" | tee -a "$LOG"
}

for split in patent_temporal_pair_novel patent_temporal_drug_novel; do
  for seed in 1 2; do
    run_if_missing \
      "results/patent_controlled_base/BindingDB_patent_${split}_base_seed${seed}.json" \
      scripts/train_raicd.py \
      --dataset BindingDB_patent \
      --split "$split" \
      --model base \
      --seed "$seed" \
      --epochs 6 \
      --batch-size 256 \
      --output-dir results/patent_controlled_base

    run_if_missing \
      "results/patent_controlled_rf/BindingDB_patent_${split}_rf_seed${seed}.json" \
      scripts/train_classical_baseline.py \
      --dataset BindingDB_patent \
      --split "$split" \
      --model rf \
      --seed "$seed" \
      --n-estimators 400 \
      --output-dir results/patent_controlled_rf

    run_if_missing \
      "results/patent_controlled_dtilm/BindingDB_patent_${split}_dtilm_seed${seed}.json" \
      scripts/train_recent_baseline.py \
      --dataset BindingDB_patent \
      --split "$split" \
      --model dtilm \
      --seed "$seed" \
      --epochs 4 \
      --batch-size 64 \
      --encoder-batch-size 4 \
      --output-dir results/patent_controlled_dtilm
  done
done

echo "bindingdb patent controlled multiseed complete" | tee -a "$LOG"
