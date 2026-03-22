# RAICD: Retrieval-Augmented Inductive Cold-start DTI

Minimal research framework for the topic:

`cold start in drug target interaction prediction`

This repository was bootstrapped from scratch to execute a focused research pipeline around one chosen idea:

- `RAICD`: Retrieval-Augmented Inductive Cold-start DTI

The core claim is that cold-start DTI, especially unseen-drug and blind-start settings, is not only an encoding problem. It is a conditional evidence aggregation problem: given an unseen drug or target, the model should retrieve the most relevant seen entities from the training bank and aggregate their evidence in a pair-conditioned way.

## What is included

- Stage 1 report in [reports/IDEA_REPORT.md](/root/exp/dti_codex/reports/IDEA_REPORT.md)
- Implementation plan in [reports/IMPLEMENTATION_PLAN.md](/root/exp/dti_codex/reports/IMPLEMENTATION_PLAN.md)
- PyTorch implementation of:
  - hashed protein featurization
  - RDKit Morgan drug featurization
  - train-only retrieval banks
  - base encoder and retrieval-augmented model
  - warm / unseen-drug / unseen-target / blind-start splits via TDC
- runnable training entrypoint: [scripts/train_raicd.py](/root/exp/dti_codex/scripts/train_raicd.py)
- smoke and experiment launch scripts under [scripts](/root/exp/dti_codex/scripts)

## Round 1 results

On `BindingDB_Kd` with binary labels from `pKd >= 7.0`:

- `unseen_drug`
  - `base`: AUPRC `0.608`, AUROC `0.823`
  - `raicd` with similarity-biased attention: AUPRC `0.614`, AUROC `0.840`
- `blind_start`
  - `base`: AUPRC `0.352`, AUROC `0.658`
  - `raicd` with similarity-biased attention: AUPRC `0.407`, AUROC `0.686`

These results suggest the retrieval idea is worth keeping, especially for stricter cold-start settings.

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

## Notes

- `BindingDB_Kd` is used as the primary dataset because it gives a healthier positive rate than `DAVIS` under `pKd >= 7.0`.
- Retrieval is strictly train-only to avoid leakage.
- Similarity-overlap statistics are saved with the metrics so the model can later be stress-tested under decreasing train-test overlap.
- `--use-retrieval-gate` is available for ablation, but the current best results use similarity-biased attention without the extra global gate.
