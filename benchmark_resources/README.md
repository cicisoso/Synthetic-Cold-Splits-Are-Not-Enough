# Generated Benchmark Bundles

This directory is reserved for exported benchmark-resource bundles such as:

```text
benchmark_resources/<dataset>/<split>/seed<k>/
```

The public GitHub repository does not commit these large generated directories by default. Instead, it commits:

- this README
- [`RELEASE_MANIFEST.md`](RELEASE_MANIFEST.md)
- the code required to regenerate the bundles

## How To Generate Bundles Locally

Export one split:

```bash
PYTHONPATH=src python scripts/export_benchmark_resource.py \
  --dataset BindingDB_Kd \
  --split unseen_target \
  --seed 0
```

Export the paper benchmark suite:

```bash
bash scripts/export_benchmark_suite.sh
```

## Expected Bundle Contents

Each generated `seed<k>/` directory should contain:

- `manifest.json`
- `train.csv`, `valid.csv`, `test.csv`
- `all.csv`
- `drugs.csv`, `targets.csv`
- `train_pairs.csv`, `valid_pairs.csv`, `test_pairs.csv`, `all_pairs.csv`

See [`docs/BENCHMARKS.md`](../docs/BENCHMARKS.md) for the benchmark catalog and [`docs/DATA_ACCESS.md`](../docs/DATA_ACCESS.md) for raw-data staging requirements.
