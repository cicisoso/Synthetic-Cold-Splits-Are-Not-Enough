#!/usr/bin/env bash
set -euo pipefail

echo "Waiting for 5-seed extension to finish..."
# Wait for the 5-seed extension process to complete
while pgrep -f "run_5seed_extension" > /dev/null 2>&1; do
  sleep 60
done

echo "5-seed extension complete. Starting ColdstartCPI runs..."
cd /root/exp/dti_codex
conda run -n research bash scripts/run_coldstartcpi_multiseed.sh

echo "All experiments complete: $(date)"
