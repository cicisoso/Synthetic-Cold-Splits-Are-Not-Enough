#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -lt 2 ]; then
  echo "usage: $0 <dtilm|hyperpcm> <seed> [seed...]" >&2
  exit 1
fi

MODEL="$1"
shift
SEEDS=("$@")

case "$MODEL" in
  dtilm)
    ENCODER_BATCH_SIZE=2
    OUT_DIR="results/recent_dtilm_davis_multiseed"
    LOG_PATH="logs/dtilm_davis_fast.log"
    ;;
  hyperpcm)
    ENCODER_BATCH_SIZE=2
    OUT_DIR="results/recent_hyperpcm_davis_multiseed"
    LOG_PATH="logs/hyper_davis_fast.log"
    ;;
  *)
    echo "unsupported model: $MODEL" >&2
    exit 1
    ;;
esac

mkdir -p logs "$OUT_DIR"

run_if_missing() {
  local output_json="$1"
  shift
  if [ -f "$output_json" ]; then
    echo "{\"skip\":\"$output_json\"}" | tee -a "$LOG_PATH"
    return 0
  fi
  PYTHONPATH=src python scripts/train_recent_baseline.py "$@" | tee -a "$LOG_PATH"
}

for seed in "${SEEDS[@]}"; do
  run_if_missing \
    "${OUT_DIR}/DAVIS_unseen_target_${MODEL}_seed${seed}.json" \
    --dataset DAVIS --split unseen_target --model "$MODEL" --seed "$seed" \
    --epochs 6 --batch-size 64 --encoder-batch-size "$ENCODER_BATCH_SIZE" \
    --output-dir "$OUT_DIR"
done

echo "{\"status\":\"davis ${MODEL} complete\"}" | tee -a "$LOG_PATH"
