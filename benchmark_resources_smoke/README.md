# Smoke Example

This directory contains a tiny example for testing the evaluator wiring without exporting a full benchmark bundle.

Files:

- `BindingDB_Kd/unseen_target/seed0/test.csv`: tiny reference split with benchmark columns
- `mock_predictions.csv`: toy prediction file with `example_id` and `probability`
- `mock_eval.json`: example evaluator output

The smoke assets are intended only for tooling checks. They are not part of the scientific benchmark release.

Example:

```bash
PYTHONPATH=src python scripts/evaluate_prediction_csv.py \
  --reference-csv benchmark_resources_smoke/BindingDB_Kd/unseen_target/seed0/test.csv \
  --prediction-csv benchmark_resources_smoke/mock_predictions.csv \
  --output benchmark_resources_smoke/mock_eval.json
```
