#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -ne 1 ]; then
  echo "usage: $0 <dtilm|hyperpcm>" >&2
  exit 1
fi

MODEL="$1"
case "$MODEL" in
  dtilm)
    ENCODER_BATCH_SIZE=2
    ;;
  hyperpcm)
    ENCODER_BATCH_SIZE=2
    ;;
  *)
    echo "unsupported model: $MODEL" >&2
    exit 1
    ;;
esac

LOG_PATH="logs/external_replacement_${MODEL}.log"
UNSEEN_DRUG_DIR="results/recent_${MODEL}_unseen_drug_multiseed"
KI_DIR="results/recent_${MODEL}_ki_multiseed"
DAVIS_DIR="results/recent_${MODEL}_davis_multiseed"

mkdir -p logs "$UNSEEN_DRUG_DIR" "$KI_DIR" "$DAVIS_DIR"

run_if_missing() {
  local output_json="$1"
  shift
  if [ -f "$output_json" ]; then
    echo "{\"skip\":\"$output_json\"}" | tee -a "$LOG_PATH"
    return 0
  fi
  PYTHONPATH=src python scripts/train_recent_baseline.py "$@" | tee -a "$LOG_PATH"
}

copy_seed0_if_available() {
  local src_prefix="$1"
  local dst_prefix="$2"
  if [ -f "${dst_prefix}.json" ]; then
    echo "{\"skip_copy\":\"${dst_prefix}.json\"}" | tee -a "$LOG_PATH"
    return 0
  fi
  if [ -f "${src_prefix}.json" ]; then
    cp "${src_prefix}.json" "${dst_prefix}.json"
    cp "${src_prefix}.pt" "${dst_prefix}.pt"
    cp "${src_prefix}_test_predictions.csv" "${dst_prefix}_test_predictions.csv"
    echo "{\"copied_seed0\":\"${dst_prefix}.json\"}" | tee -a "$LOG_PATH"
  fi
}

for seed in 0 1 2; do
  run_if_missing \
    "${UNSEEN_DRUG_DIR}/BindingDB_Kd_unseen_drug_${MODEL}_seed${seed}.json" \
    --dataset BindingDB_Kd --split unseen_drug --model "$MODEL" --seed "$seed" \
    --epochs 6 --batch-size 64 --encoder-batch-size "$ENCODER_BATCH_SIZE" \
    --output-dir "$UNSEEN_DRUG_DIR"
done

if [ "$MODEL" = "dtilm" ]; then
  copy_seed0_if_available \
    "results/recent_dtilm_support_stage1/BindingDB_Ki_unseen_target_dtilm_seed0" \
    "${KI_DIR}/BindingDB_Ki_unseen_target_dtilm_seed0"
  copy_seed0_if_available \
    "results/recent_dtilm_support_stage1/DAVIS_unseen_target_dtilm_seed0" \
    "${DAVIS_DIR}/DAVIS_unseen_target_dtilm_seed0"
fi

for seed in 0 1 2; do
  run_if_missing \
    "${KI_DIR}/BindingDB_Ki_unseen_target_${MODEL}_seed${seed}.json" \
    --dataset BindingDB_Ki --split unseen_target --model "$MODEL" --seed "$seed" \
    --epochs 6 --batch-size 64 --encoder-batch-size "$ENCODER_BATCH_SIZE" \
    --output-dir "$KI_DIR"

  run_if_missing \
    "${DAVIS_DIR}/DAVIS_unseen_target_${MODEL}_seed${seed}.json" \
    --dataset DAVIS --split unseen_target --model "$MODEL" --seed "$seed" \
    --epochs 6 --batch-size 64 --encoder-batch-size "$ENCODER_BATCH_SIZE" \
    --output-dir "$DAVIS_DIR"
done

echo "{\"status\":\"external replacement ${MODEL} complete\"}" | tee -a "$LOG_PATH"
