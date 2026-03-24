#!/usr/bin/env bash
set -euo pipefail

OUTPUT_BASE_DIR="${OUTPUT_BASE_DIR:-benchmark_resources}"
CACHE_DIR="${CACHE_DIR:-data/cache}"
SEEDS="${SEEDS:-0 1 2}"
INCLUDE_AUXILIARY="${INCLUDE_AUXILIARY:-1}"

COMMON_ARGS=(
  --output-base-dir "$OUTPUT_BASE_DIR"
  --cache-dir "$CACHE_DIR"
)

export_split() {
  local dataset="$1"
  local split="$2"
  local seed="$3"
  echo "[export] dataset=${dataset} split=${split} seed=${seed}"
  PYTHONPATH=src python scripts/export_benchmark_resource.py \
    --dataset "$dataset" \
    --split "$split" \
    --seed "$seed" \
    "${COMMON_ARGS[@]}"
}

for seed in ${SEEDS}; do
  export_split BindingDB_Kd unseen_drug "$seed"
  export_split BindingDB_Kd blind_start "$seed"
  export_split BindingDB_Kd unseen_target "$seed"
  export_split BindingDB_patent patent_temporal "$seed"
  export_split BindingDB_nonpatent_Kd nonpatent_temporal "$seed"
  export_split BindingDB_Ki unseen_target "$seed"
  export_split DAVIS unseen_target "$seed"

  if [[ "$INCLUDE_AUXILIARY" == "1" ]]; then
    export_split BindingDB_Kd scaffold_drug "$seed"
    export_split BindingDB_patent patent_temporal_v2017 "$seed"
    export_split BindingDB_patent patent_temporal_pair_novel "$seed"
    export_split BindingDB_patent patent_temporal_drug_novel "$seed"
  fi
done

echo "[done] benchmark suite export complete"
