# Data Access And Local Staging

This repository separates code release from raw-data staging. The public GitHub snapshot is meant to remain small and code-centric, while the large source datasets and generated benchmark bundles are staged locally or attached to a release archive.

## Upstream Sources

Synthetic TDC-backed benchmarks:

- `BindingDB_Kd`
- `BindingDB_Ki`
- `DAVIS`

These are loaded through `pytdc` inside [`src/raicd/data.py`](../src/raicd/data.py).

Local temporal/provenance benchmarks:

- `BindingDB_patent`
- `BindingDB_nonpatent_Kd`

These are expected under:

```text
data/tdc_benchmark/dti_dg_group/bindingdb_patent/
data/tdc_benchmark/dti_dg_group/bindingdb_nonpatent_kd/
```

## Expected Local Files

### TDC-backed datasets

No manual CSV placement is required if `pytdc` can download the source data.

### Patent temporal/provenance benchmark

Expected files:

```text
data/tdc_benchmark/dti_dg_group/bindingdb_patent/train_val.csv
data/tdc_benchmark/dti_dg_group/bindingdb_patent/test.csv
```

This benchmark is treated as a local staged resource in the current codebase.

### Non-patent temporal/provenance benchmark

Expected files after local build:

```text
data/tdc_benchmark/dti_dg_group/bindingdb_nonpatent_kd/train_val.csv
data/tdc_benchmark/dti_dg_group/bindingdb_nonpatent_kd/test.csv
data/tdc_benchmark/dti_dg_group/bindingdb_nonpatent_kd/summary.json
```

Build command:

```bash
PYTHONPATH=src python scripts/build_bindingdb_nonpatent_temporal.py \
  --input-zip data/external/BindingDB_All_202603_tsv.zip \
  --output-dir data/tdc_benchmark/dti_dg_group/bindingdb_nonpatent_kd
```

## Cache Layout

Feature caches are written to:

```text
data/cache/
```

These are local accelerators only and should not be committed to Git.

## Redistribution Guidance

Before publishing derived benchmark bundles under `benchmark_resources/`, verify that the redistribution terms of the upstream data sources are compatible with your release channel.

Recommended release practice:

1. Keep the GitHub repository source-only.
2. Attach generated benchmark bundles as a GitHub release asset or DOI-backed archive.
3. Include the commit hash and [`benchmark_resources/RELEASE_MANIFEST.md`](../benchmark_resources/RELEASE_MANIFEST.md) in the archive.

## Minimal Public Repo vs Full Release Archive

### GitHub repository

Should contain:

- code in `src/` and `scripts/`
- benchmark docs in `docs/`
- smoke example in `benchmark_resources_smoke/`
- release manifest and bundle schema notes

### Release archive

Can additionally contain:

- exported `benchmark_resources/<dataset>/<split>/seed<k>/` bundles
- manuscript PDF
- benchmark summary tables used in the paper

For the exact benchmark list, see [`BENCHMARKS.md`](BENCHMARKS.md).
