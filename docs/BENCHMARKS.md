# Benchmark Catalog

This repository exposes a benchmark suite for studying how model ranking changes across synthetic cold-start and temporal/provenance DTI evaluation.

## Primary Paper Benchmarks

| Dataset | Split ID | Shift family | Role in paper |
| --- | --- | --- | --- |
| `BindingDB_Kd` | `unseen_drug` | synthetic drug-cold | primary synthetic |
| `BindingDB_Kd` | `blind_start` | synthetic drug+target-cold | primary synthetic |
| `BindingDB_Kd` | `unseen_target` | synthetic target-cold | primary synthetic |
| `BindingDB_patent` | `patent_temporal` | temporal/provenance | primary temporal/provenance |
| `BindingDB_nonpatent_Kd` | `nonpatent_temporal` | temporal/provenance | primary temporal/provenance support |

## Supporting And Robustness Benchmarks

| Dataset | Split ID | Shift family | Role in paper |
| --- | --- | --- | --- |
| `BindingDB_Ki` | `unseen_target` | assay + target-cold | supporting OOD |
| `DAVIS` | `unseen_target` | dataset + target-cold | supporting OOD |
| `BindingDB_Kd` | `scaffold_drug` | scaffold-restricted synthetic | robustness |
| `BindingDB_patent` | `patent_temporal_v2017` | earlier-cutoff temporal/provenance | robustness |
| `BindingDB_patent` | `patent_temporal_pair_novel` | overlap-restricted temporal/provenance | robustness |
| `BindingDB_patent` | `patent_temporal_drug_novel` | overlap-restricted temporal/provenance | robustness |

## Exported Bundle Schema

Each exported bundle lives under:

```text
benchmark_resources/<dataset>/<split>/seed<k>/
```

Required files:

- `manifest.json`
- `train.csv`
- `valid.csv`
- `test.csv`
- `all.csv`
- `drugs.csv`
- `targets.csv`
- `train_pairs.csv`
- `valid_pairs.csv`
- `test_pairs.csv`
- `all_pairs.csv`

## Core Columns

Partition tables contain:

- `example_id`: stable identifier used by the evaluator
- `dataset`
- `split`
- `seed`
- `partition`
- `Drug_ID`
- `Target_ID`
- `Drug`
- `Target`
- `Y`
- `pKd`
- `label`
- `Year`
- `drug_overlap`
- `target_overlap`
- `overlap_score`

Pair-level tables keep the audit-critical subset:

- `example_id`
- `partition`
- `drug_id`
- `prot_id`
- `label`
- `Y`
- `pKd`
- `Year`
- `overlap_score`

## Evaluator Contract

External predictions are matched by `example_id`. The default evaluator expects:

- a reference CSV such as `test.csv`
- a prediction CSV containing `example_id` and a score column

Example:

```bash
PYTHONPATH=src python scripts/evaluate_prediction_csv.py \
  --reference-csv benchmark_resources/BindingDB_Kd/unseen_target/seed0/test.csv \
  --prediction-csv path/to/predictions.csv \
  --output path/to/eval.json
```

The decision-facing evaluator uses the same join contract:

```bash
PYTHONPATH=src python scripts/evaluate_decision_csv.py \
  --reference-csv benchmark_resources/BindingDB_patent/patent_temporal/seed0/test.csv \
  --prediction-csv path/to/predictions.csv \
  --output path/to/decision_eval.json
```

## Notes On Semantics

- Synthetic `unseen_drug`, `unseen_target`, and `blind_start` come from TDC cold-split generation.
- `BindingDB_patent` and `BindingDB_nonpatent_Kd` are local temporal/provenance benchmarks staged under `data/tdc_benchmark/dti_dg_group/`.
- Overlap-restricted patent variants are derived from the same temporal family and tighten pair-level or drug-level recurrence.

For local raw-data staging, see [`DATA_ACCESS.md`](DATA_ACCESS.md). For end-to-end reproduction, see [`REPRODUCE_BENCHMARKS.md`](REPRODUCE_BENCHMARKS.md).
