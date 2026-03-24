# Reproduce The Benchmark Release

This document turns the current codebase into a GitHub-friendly reproduction flow.

## 1. Install Dependencies

Core export and evaluation flow:

```bash
pip install -r requirements-core.txt
pip install -e . --no-deps
```

Optional model-training and analysis stack:

```bash
pip install -r requirements-models.txt
```

## 2. Stage Raw Data

Follow [`DATA_ACCESS.md`](DATA_ACCESS.md) to stage:

- TDC-backed synthetic datasets through `pytdc`
- `bindingdb_patent` local temporal split files
- `bindingdb_nonpatent_kd` files built with `scripts/build_bindingdb_nonpatent_temporal.py`

## 3. Export Benchmark Bundles

Export the full paper benchmark suite:

```bash
bash scripts/export_benchmark_suite.sh
```

Export a single split:

```bash
PYTHONPATH=src python scripts/export_benchmark_resource.py \
  --dataset BindingDB_patent \
  --split patent_temporal \
  --seed 0
```

## 4. Score External Predictions

```bash
PYTHONPATH=src python scripts/evaluate_prediction_csv.py \
  --reference-csv benchmark_resources/BindingDB_patent/patent_temporal/seed0/test.csv \
  --prediction-csv path/to/predictions.csv \
  --output path/to/eval.json
```

Decision-facing evaluation:

```bash
PYTHONPATH=src python scripts/evaluate_decision_csv.py \
  --reference-csv benchmark_resources/BindingDB_patent/patent_temporal/seed0/test.csv \
  --prediction-csv path/to/predictions.csv \
  --output path/to/decision_eval.json
```

## 5. Reproduce Paper Tables

The manuscript summary tables are derived from result JSON files under `results/`. If you also want the paper summaries:

```bash
PYTHONPATH=src python scripts/summarize_benchmarks.py
PYTHONPATH=src python scripts/summarize_external_panel.py
PYTHONPATH=src python scripts/summarize_benchmark_taxonomy.py
```

More focused analyses:

```bash
PYTHONPATH=src python scripts/analyze_patent_shift.py
PYTHONPATH=src python scripts/bootstrap_pairwise_ci.py
PYTHONPATH=src python scripts/bootstrap_patent_slices.py
PYTHONPATH=src python scripts/analyze_patent_decision_panel.py
```

## 6. Public Release Packaging

Recommended packaging for GitHub plus archive release:

1. push the source repository without `data/`, `results/`, or generated `benchmark_resources/seed*/` bundles
2. export benchmark bundles locally
3. attach the exported bundles as a versioned GitHub Release asset or DOI-backed archive
4. include the manuscript PDF and [`benchmark_resources/RELEASE_MANIFEST.md`](../benchmark_resources/RELEASE_MANIFEST.md)

## 7. Smoke Test

```bash
PYTHONPATH=src python scripts/evaluate_prediction_csv.py \
  --reference-csv benchmark_resources_smoke/BindingDB_Kd/unseen_target/seed0/test.csv \
  --prediction-csv benchmark_resources_smoke/mock_predictions.csv \
  --output benchmark_resources_smoke/mock_eval.json
```

This confirms that the evaluator wiring works before the full benchmark export is run.
