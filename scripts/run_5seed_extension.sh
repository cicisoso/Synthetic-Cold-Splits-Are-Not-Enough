#!/usr/bin/env bash
# Extend all primary benchmarks from 3 seeds to 5 seeds (add seeds 3,4)
# Also fills any gaps in seeds 0-2
set -euo pipefail

mkdir -p logs

LOGFILE="logs/5seed_extension.log"
echo "=== 5-seed extension started $(date) ===" | tee -a "$LOGFILE"

# --- Helper ---
run_if_missing() {
  local output_json="$1"; shift
  if [ -f "$output_json" ]; then
    echo "{\"skip\":\"$output_json\"}" | tee -a "$LOGFILE"
    return 0
  fi
  PYTHONPATH=src python "$@" | tee -a "$LOGFILE"
}

# ===== BASE (train_raicd.py, model=base) =====
for seed in 0 1 2 3 4; do
  for split in unseen_drug blind_start unseen_target; do
    mkdir -p "results/5seed_base_${split}"
    run_if_missing \
      "results/5seed_base_${split}/BindingDB_Kd_${split}_base_seed${seed}.json" \
      scripts/train_raicd.py --dataset BindingDB_Kd --split "$split" --model base --seed "$seed" \
      --epochs 8 --batch-size 256 --output-dir "results/5seed_base_${split}"
  done
  # Patent temporal
  mkdir -p "results/5seed_base_patent"
  run_if_missing \
    "results/5seed_base_patent/BindingDB_patent_patent_temporal_base_seed${seed}.json" \
    scripts/train_raicd.py --dataset BindingDB_patent --split patent_temporal --model base --seed "$seed" \
    --epochs 8 --batch-size 256 --output-dir "results/5seed_base_patent"
  # Nonpatent temporal
  mkdir -p "results/5seed_base_nonpatent"
  run_if_missing \
    "results/5seed_base_nonpatent/BindingDB_nonpatent_Kd_nonpatent_temporal_base_seed${seed}.json" \
    scripts/train_raicd.py --dataset BindingDB_nonpatent_Kd --split nonpatent_temporal --model base --seed "$seed" \
    --epochs 8 --batch-size 256 --output-dir "results/5seed_base_nonpatent"
done

# ===== RF (train_classical_baseline.py) =====
for seed in 0 1 2 3 4; do
  for split in unseen_drug blind_start unseen_target; do
    mkdir -p "results/5seed_rf_${split}"
    run_if_missing \
      "results/5seed_rf_${split}/BindingDB_Kd_${split}_rf_seed${seed}.json" \
      scripts/train_classical_baseline.py --dataset BindingDB_Kd --split "$split" --model rf --seed "$seed" \
      --output-dir "results/5seed_rf_${split}"
  done
  mkdir -p "results/5seed_rf_patent"
  run_if_missing \
    "results/5seed_rf_patent/BindingDB_patent_patent_temporal_rf_seed${seed}.json" \
    scripts/train_classical_baseline.py --dataset BindingDB_patent --split patent_temporal --model rf --seed "$seed" \
    --output-dir "results/5seed_rf_patent"
  mkdir -p "results/5seed_rf_nonpatent"
  run_if_missing \
    "results/5seed_rf_nonpatent/BindingDB_nonpatent_Kd_nonpatent_temporal_rf_seed${seed}.json" \
    scripts/train_classical_baseline.py --dataset BindingDB_nonpatent_Kd --split nonpatent_temporal --model rf --seed "$seed" \
    --output-dir "results/5seed_rf_nonpatent"
done

# ===== DTI-LM (train_recent_baseline.py --model dtilm) =====
for seed in 0 1 2 3 4; do
  for split in unseen_drug blind_start unseen_target; do
    mkdir -p "results/5seed_dtilm_${split}"
    run_if_missing \
      "results/5seed_dtilm_${split}/BindingDB_Kd_${split}_dtilm_seed${seed}.json" \
      scripts/train_recent_baseline.py --dataset BindingDB_Kd --split "$split" --model dtilm --seed "$seed" \
      --epochs 6 --batch-size 128 --output-dir "results/5seed_dtilm_${split}"
  done
  mkdir -p "results/5seed_dtilm_patent"
  run_if_missing \
    "results/5seed_dtilm_patent/BindingDB_patent_patent_temporal_dtilm_seed${seed}.json" \
    scripts/train_recent_baseline.py --dataset BindingDB_patent --split patent_temporal --model dtilm --seed "$seed" \
    --epochs 4 --batch-size 128 --output-dir "results/5seed_dtilm_patent"
  mkdir -p "results/5seed_dtilm_nonpatent"
  run_if_missing \
    "results/5seed_dtilm_nonpatent/BindingDB_nonpatent_Kd_nonpatent_temporal_dtilm_seed${seed}.json" \
    scripts/train_recent_baseline.py --dataset BindingDB_nonpatent_Kd --split nonpatent_temporal --model dtilm --seed "$seed" \
    --epochs 4 --batch-size 128 --output-dir "results/5seed_dtilm_nonpatent"
done

# ===== HyperPCM (train_recent_baseline.py --model hyperpcm) =====
for seed in 0 1 2 3 4; do
  for split in unseen_drug blind_start unseen_target; do
    mkdir -p "results/5seed_hyperpcm_${split}"
    run_if_missing \
      "results/5seed_hyperpcm_${split}/BindingDB_Kd_${split}_hyperpcm_seed${seed}.json" \
      scripts/train_recent_baseline.py --dataset BindingDB_Kd --split "$split" --model hyperpcm --seed "$seed" \
      --epochs 6 --batch-size 128 --output-dir "results/5seed_hyperpcm_${split}"
  done
  mkdir -p "results/5seed_hyperpcm_patent"
  run_if_missing \
    "results/5seed_hyperpcm_patent/BindingDB_patent_patent_temporal_hyperpcm_seed${seed}.json" \
    scripts/train_recent_baseline.py --dataset BindingDB_patent --split patent_temporal --model hyperpcm --seed "$seed" \
    --epochs 4 --batch-size 128 --output-dir "results/5seed_hyperpcm_patent"
  mkdir -p "results/5seed_hyperpcm_nonpatent"
  run_if_missing \
    "results/5seed_hyperpcm_nonpatent/BindingDB_nonpatent_Kd_nonpatent_temporal_hyperpcm_seed${seed}.json" \
    scripts/train_recent_baseline.py --dataset BindingDB_nonpatent_Kd --split nonpatent_temporal --model hyperpcm --seed "$seed" \
    --epochs 4 --batch-size 128 --output-dir "results/5seed_hyperpcm_nonpatent"
done

# ===== GraphDTA (train_graph_baseline.py --model graphdta) =====
for seed in 0 1 2 3 4; do
  for split in unseen_drug blind_start unseen_target; do
    mkdir -p "results/5seed_graphdta_${split}"
    run_if_missing \
      "results/5seed_graphdta_${split}/BindingDB_Kd_${split}_graphdta_seed${seed}.json" \
      scripts/train_graph_baseline.py --dataset BindingDB_Kd --split "$split" --model graphdta --seed "$seed" \
      --epochs 8 --batch-size 64 --output-dir "results/5seed_graphdta_${split}"
  done
  mkdir -p "results/5seed_graphdta_patent"
  run_if_missing \
    "results/5seed_graphdta_patent/BindingDB_patent_patent_temporal_graphdta_seed${seed}.json" \
    scripts/train_graph_baseline.py --dataset BindingDB_patent --split patent_temporal --model graphdta --seed "$seed" \
    --epochs 4 --batch-size 64 --output-dir "results/5seed_graphdta_patent"
  mkdir -p "results/5seed_graphdta_nonpatent"
  run_if_missing \
    "results/5seed_graphdta_nonpatent/BindingDB_nonpatent_Kd_nonpatent_temporal_graphdta_seed${seed}.json" \
    scripts/train_graph_baseline.py --dataset BindingDB_nonpatent_Kd --split nonpatent_temporal --model graphdta --seed "$seed" \
    --epochs 4 --batch-size 64 --output-dir "results/5seed_graphdta_nonpatent"
done

# ===== DrugBAN (train_graph_baseline.py --model drugban) =====
for seed in 0 1 2 3 4; do
  for split in unseen_drug blind_start unseen_target; do
    mkdir -p "results/5seed_drugban_${split}"
    run_if_missing \
      "results/5seed_drugban_${split}/BindingDB_Kd_${split}_drugban_seed${seed}.json" \
      scripts/train_graph_baseline.py --dataset BindingDB_Kd --split "$split" --model drugban --seed "$seed" \
      --epochs 8 --batch-size 64 --output-dir "results/5seed_drugban_${split}"
  done
  mkdir -p "results/5seed_drugban_patent"
  run_if_missing \
    "results/5seed_drugban_patent/BindingDB_patent_patent_temporal_drugban_seed${seed}.json" \
    scripts/train_graph_baseline.py --dataset BindingDB_patent --split patent_temporal --model drugban --seed "$seed" \
    --epochs 6 --batch-size 64 --output-dir "results/5seed_drugban_patent"
  mkdir -p "results/5seed_drugban_nonpatent"
  run_if_missing \
    "results/5seed_drugban_nonpatent/BindingDB_nonpatent_Kd_nonpatent_temporal_drugban_seed${seed}.json" \
    scripts/train_graph_baseline.py --dataset BindingDB_nonpatent_Kd --split nonpatent_temporal --model drugban --seed "$seed" \
    --epochs 6 --batch-size 64 --output-dir "results/5seed_drugban_nonpatent"
done

echo "=== 5-seed extension complete $(date) ===" | tee -a "$LOGFILE"
