# Baseline Panel Expansion

Date: 2026-03-23

## Goal

Expand the benchmark panel beyond the current `base / DTI-LM / HyperPCM` trio with two architecturally distinct baselines:

- `rf`: same representation as `base`, different learner
- `graphdta`: different representation and different inductive bias

This addresses the main reviewer concern that a three-model panel is too narrow to support claims about rank sensitivity under distribution shift.

## RandomForest Methodology

### Role

`rf` is a learner-control baseline. It uses the exact same raw pair input information as `base`:

- drug: RDKit Morgan fingerprint, radius `2`, `2048` bits
- target: hashed protein k-mer vector, `k={1,2,3}`, dimension `2048`

### Pair Representation

The default pair feature is direct concatenation:

`x_pair = [x_drug ; x_target]`

This keeps the representation aligned with `base` while changing only the decision function.

### Learner

- model: `sklearn.ensemble.RandomForestClassifier`
- class weighting: `balanced_subsample`
- default panel config: `n_estimators=400`

### Interpretation

If `rf` changes rankings relative to `base`, the shift sensitivity cannot be attributed only to neural optimization or representation learning. It indicates that even with fixed handcrafted inputs, the learner choice matters.

## GraphDTA-style Methodology

### Role

`graphdta` adds a qualitatively different inductive bias:

- drug: molecular graph instead of fixed fingerprint
- target: tokenized amino-acid sequence with a CNN encoder instead of hashed k-mers or pooled LM embeddings

### Drug Encoder

- graph construction from RDKit atoms and bonds
- node features: atom symbol, degree, hydrogen count, valence, formal charge, aromaticity, hybridization
- encoder: 3-layer GCN with mean/max global pooling

### Target Encoder

- vocabulary: 20 standard amino acids + padding
- representation: fixed-length token sequence
- encoder: embedding + 3-layer 1D CNN + global max pooling

### Pair Head

- concatenated drug/target embeddings
- 2-layer MLP prediction head

### Interpretation

`graphdta` is not meant as a line-by-line reproduction of a single published implementation. It is a `GraphDTA-style` baseline that supplies the missing graph-based architectural family in the benchmark panel.

## Output Contract

Both baselines reuse the benchmark resource and evaluator contract:

- input: `benchmark_resources/<dataset>/<split>/seed<k>/`
- output JSON: metrics + predictions
- output CSV: `example_id`, `probability`, `overlap_score`
- evaluation: [scripts/evaluate_prediction_csv.py](/root/exp/dti_codex/scripts/evaluate_prediction_csv.py)

## Stage-1 Screening Order

1. `BindingDB_Kd / unseen_drug`
2. `BindingDB_Kd / unseen_target`
3. `BindingDB_Kd / blind_start`
4. `BindingDB_patent / patent_temporal`
5. `BindingDB_nonpatent_Kd / nonpatent_temporal`

Current launchers:

- [run_rf_panel_stage1.sh](/root/exp/dti_codex/scripts/run_rf_panel_stage1.sh)
- [run_graphdta_panel_stage1.sh](/root/exp/dti_codex/scripts/run_graphdta_panel_stage1.sh)

## Seed0 Screening Snapshot

The first screening round already shows that the panel story changes once these baselines are added.

### RandomForest seed0

- `BindingDB_Kd / unseen_drug`: `0.7279 / 0.8912`
- `BindingDB_Kd / unseen_target`: `0.5618 / 0.7981`
- `BindingDB_Kd / blind_start`: `0.4488 / 0.7589`
- `BindingDB_patent / patent_temporal`: `0.8249 / 0.7793`
- `BindingDB_nonpatent_Kd / nonpatent_temporal`: `0.7216 / 0.7648`

### GraphDTA-style seed0

- `BindingDB_Kd / unseen_drug`: `0.5386 / 0.8159`
- `BindingDB_Kd / unseen_target`: `0.5289 / 0.7776`
- `BindingDB_Kd / blind_start`: `0.4245 / 0.7426`
- `BindingDB_patent / patent_temporal`: `0.7741 / 0.7242`
- `BindingDB_nonpatent_Kd / nonpatent_temporal`: `0.6673 / 0.7444`

## Promotion Decision

Based on seed0 screening:

- `RandomForest` is promoted on all main and key robustness panels because it is unexpectedly strong across the board.
- `GraphDTA-style` is promoted only on the most decision-relevant synthetic and temporal splits:
  - `BindingDB_Kd / unseen_drug`
  - `BindingDB_Kd / unseen_target`
  - `BindingDB_patent / patent_temporal`
  - `BindingDB_nonpatent_Kd / nonpatent_temporal`

Current promotion launchers:

- [run_rf_topline_multiseed.sh](/root/exp/dti_codex/scripts/run_rf_topline_multiseed.sh)
- [run_graphdta_topline_multiseed.sh](/root/exp/dti_codex/scripts/run_graphdta_topline_multiseed.sh)

## Final 3-seed Summary

### RandomForest

- `BindingDB_Kd / unseen_drug`: `0.7339 ± 0.0051 / 0.8854 ± 0.0088`
- `BindingDB_Kd / unseen_target`: `0.5183 ± 0.0612 / 0.7838 ± 0.0218`
- `BindingDB_Kd / blind_start`: `0.4512 ± 0.0373 / 0.7451 ± 0.0260`
- `BindingDB_patent / patent_temporal`: `0.8234 ± 0.0012 / 0.7773 ± 0.0017`
- `BindingDB_nonpatent_Kd / nonpatent_temporal`: `0.7201 ± 0.0012 / 0.7627 ± 0.0020`

### GraphDTA-style

- `BindingDB_Kd / unseen_drug`: `0.5626 ± 0.0172 / 0.7988 ± 0.0129`
- `BindingDB_Kd / unseen_target`: `0.4722 ± 0.0925 / 0.7637 ± 0.0314`
- `BindingDB_patent / patent_temporal`: `0.7726 ± 0.0016 / 0.7232 ± 0.0007`
- `BindingDB_nonpatent_Kd / nonpatent_temporal`: `0.6635 ± 0.0142 / 0.7334 ± 0.0096`

## Current Read

- `RandomForest` is the main result-changing addition. It becomes strongest on every promoted axis except synthetic `unseen_target`, where `base` remains slightly ahead on mean \AUPRC{}.
- `GraphDTA-style` is valuable as an architecture-diverse control, but it does not become the dominant model on any promoted axis.
- The benchmark story is now stronger than the earlier three-model version: ranking sensitivity is no longer only about pooled-LM models, because a classical learner on the same handcrafted features can become the strongest system on both synthetic and temporal panels.
