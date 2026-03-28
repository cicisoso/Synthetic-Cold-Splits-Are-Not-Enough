#!/usr/bin/env bash
# Run ColdstartCPI-style model across all primary benchmarks, 5 seeds
set -euo pipefail

mkdir -p logs

LOGFILE="logs/coldstartcpi_multiseed.log"
echo "=== coldstartcpi multiseed started $(date) ===" | tee -a "$LOGFILE"

run_if_missing() {
  local output_json="$1"; shift
  if [ -f "$output_json" ]; then
    echo "{\"skip\":\"$output_json\"}" | tee -a "$LOGFILE"
    return 0
  fi
  PYTHONPATH=src python scripts/train_graph_baseline.py "$@" | tee -a "$LOGFILE"
}

for seed in 0 1 2 3 4; do
  for split in unseen_drug blind_start unseen_target; do
    mkdir -p "results/5seed_coldstartcpi_${split}"
    run_if_missing \
      "results/5seed_coldstartcpi_${split}/BindingDB_Kd_${split}_coldstartcpi_seed${seed}.json" \
      --dataset BindingDB_Kd --split "$split" --model coldstartcpi --seed "$seed" \
      --epochs 8 --batch-size 64 \
      --output-dir "results/5seed_coldstartcpi_${split}"
  done

  mkdir -p "results/5seed_coldstartcpi_patent"
  run_if_missing \
    "results/5seed_coldstartcpi_patent/BindingDB_patent_patent_temporal_coldstartcpi_seed${seed}.json" \
    --dataset BindingDB_patent --split patent_temporal --model coldstartcpi --seed "$seed" \
    --epochs 6 --batch-size 64 \
    --output-dir "results/5seed_coldstartcpi_patent"

  mkdir -p "results/5seed_coldstartcpi_nonpatent"
  run_if_missing \
    "results/5seed_coldstartcpi_nonpatent/BindingDB_nonpatent_Kd_nonpatent_temporal_coldstartcpi_seed${seed}.json" \
    --dataset BindingDB_nonpatent_Kd --split nonpatent_temporal --model coldstartcpi --seed "$seed" \
    --epochs 6 --batch-size 64 \
    --output-dir "results/5seed_coldstartcpi_nonpatent"
done

echo "=== coldstartcpi multiseed complete $(date) ===" | tee -a "$LOGFILE"
