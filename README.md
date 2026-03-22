# Distribution-Shift Benchmarking for DTI

Research workspace for:

`cold start in drug target interaction prediction`

The repository started from an internal method exploration around retrieval-augmented cold-start DTI, but the current primary output is a benchmark/resource paper:

`Synthetic Cold Splits Are Not Enough: Distribution-Shift Benchmarking for Drug-Target Interaction Prediction`

The current thesis is benchmark-first rather than method-first:

- synthetic cold-start DTI splits are regime-dependent even within one dataset
- synthetic cold splits and real OOD shifts are not interchangeable evaluation settings
- model rankings can reverse when the benchmark axis changes
- reusable split manifests and a standalone evaluator are part of the contribution

## What is included

- benchmark-first paper materials under [paper](/root/exp/dti_codex/paper) and [reports](/root/exp/dti_codex/reports)
- Stage 1 report in [reports/IDEA_REPORT.md](/root/exp/dti_codex/reports/IDEA_REPORT.md)
- implementation history in [reports/IMPLEMENTATION_PLAN.md](/root/exp/dti_codex/reports/IMPLEMENTATION_PLAN.md)
- PyTorch implementations of:
  - compact internal DTI panel: `base`, `RAICD`, `FTM sparse`
  - hashed protein featurization
  - RDKit Morgan drug featurization
  - train-only retrieval banks
  - synthetic `warm / unseen-drug / unseen-target / blind-start` splits via TDC
  - local patent temporal splits for real-OOD evaluation
- reusable benchmark resources under `benchmark_resources/<dataset>/<split>/seed<k>/`
- unified offline evaluator: [scripts/evaluate_prediction_csv.py](/root/exp/dti_codex/scripts/evaluate_prediction_csv.py)
- pooled-LM recent baseline trainer: [scripts/train_recent_baseline.py](/root/exp/dti_codex/scripts/train_recent_baseline.py)
- benchmark exporter: [scripts/export_benchmark_resource.py](/root/exp/dti_codex/scripts/export_benchmark_resource.py)
- runnable training entrypoint: [scripts/train_raicd.py](/root/exp/dti_codex/scripts/train_raicd.py)
- smoke and experiment launch scripts under [scripts](/root/exp/dti_codex/scripts)

## Current benchmark snapshot

The current paper-ready topline results are summarized in [reports/BENCHMARK_TABLE_LIVE.md](/root/exp/dti_codex/reports/BENCHMARK_TABLE_LIVE.md). The high-level read is:

- `BindingDB_Kd / blind_start`: retrieval (`RAICD`) wins over `base`
- `BindingDB_Kd / unseen_drug`: retrieval loses to `base`
- `BindingDB_Kd / unseen_target`: `FTM sparse` wins over `base`
- `BindingDB_patent / patent_temporal`: `DTI-LM` is the strongest recent baseline, while the internal-panel ordering reverses relative to synthetic `blind_start`
- `BindingDB_Ki` and `DAVIS` support the claim that synthetic target-cold gains do not reliably transfer

## Environment

Use the local machine described in `AGENTS.md`:

```bash
eval "$(/root/miniconda3/bin/conda shell.bash hook)" && conda activate research
```

## Install

Already installed in the `research` environment during this run:

- `pytdc`
- `scikit-learn`
- `pandas`
- `tqdm`

## Quick smoke test

```bash
bash scripts/run_smoke.sh
```

## Export A Reusable Benchmark Split

```bash
PYTHONPATH=src python scripts/export_benchmark_resource.py \
  --dataset BindingDB_Kd \
  --split unseen_target \
  --seed 0
```

This writes canonical train/valid/test CSVs, entity tables, pair tables, and a manifest under `benchmark_resources/`.

## Initial experiment

```bash
bash scripts/run_bindingdb_cold_drug.sh
```

This launches a first `BindingDB_Kd` unseen-drug experiment with binary labels from `pKd >= 7.0`.

```bash
bash scripts/run_bindingdb_blind_start.sh
```

This launches the corresponding `blind_start` experiment.

## Main entrypoint

```bash
PYTHONPATH=src python scripts/train_raicd.py \
  --dataset BindingDB_Kd \
  --split unseen_drug \
  --model raicd \
  --epochs 10 \
  --batch-size 256 \
  --pkd-threshold 7.0
```

## Recent Baseline Adapters

```bash
PYTHONPATH=src python scripts/train_recent_baseline.py \
  --dataset BindingDB_Kd \
  --split unseen_target \
  --model dtilm \
  --seed 0 \
  --epochs 4
```

The current recent-baseline panel exposes:

- `dtilm`: pooled ChemBERTa + ESM2 MLP adapter aligned to the DTI-LM setup
- `hyperpcm`: task-conditioned pooled-LM adapter aligned to recent HyperPCM-style target-conditioned modeling

These adapters are intentionally run on the same exported split resources and evaluator as the in-repo models.

## Notes

- `BindingDB_Kd` is used as the primary dataset because it gives a healthier positive rate than `DAVIS` under `pKd >= 7.0`.
- Retrieval is strictly train-only to avoid leakage.
- Similarity-overlap statistics are saved with the metrics so the model can later be stress-tested under decreasing train-test overlap.
- `--use-retrieval-gate` is available for ablation, but the current best results use similarity-biased attention without the extra global gate.
