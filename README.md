# DTI Benchmark Suite

Code, benchmark builders, and evaluation resources for the benchmark paper:

`Benchmarking synthetic cold-start and temporal/provenance distribution shifts in drug-target interaction prediction`

This repository is benchmark-first rather than method-first. Its purpose is to make the validation setup behind the paper easy to inspect, regenerate, and reuse.

## Scope

The repository is organized around one methodological claim:

- synthetic cold-start splits in DTI are not interchangeable with temporal/provenance-shifted evaluation
- model ranking can change across `unseen_drug`, `blind_start`, `unseen_target`, and temporal/provenance benchmarks
- overlap policy inside the same benchmark family can further change the apparent winner

This repository therefore exposes:

- split builders and benchmark exporters
- canonical benchmark-resource bundles with stable `example_id`s
- standalone evaluators for external prediction files
- reference baselines and analysis scripts used in the manuscript

## What Is Included

- benchmark export and evaluation code in [`scripts/`](scripts)
- reusable Python package code in [`src/raicd/`](src/raicd)
- benchmark release notes in [`benchmark_resources/RELEASE_MANIFEST.md`](benchmark_resources/RELEASE_MANIFEST.md)
- a smoke-example evaluator bundle in [`benchmark_resources_smoke/`](benchmark_resources_smoke)
- manuscript source and PDF in [`paper/`](paper)
- benchmark summaries and analysis reports in [`reports/`](reports)

## What Is Not Committed By Default

To keep the GitHub repository lightweight and legally clean, the following are intentionally not versioned by default:

- raw source datasets under `data/`
- generated benchmark bundles under `benchmark_resources/<dataset>/<split>/seed<k>/`
- training outputs under `results/`
- logs and local caches under `logs/`

The committed repository should contain the code, schema, manifests, smoke example, and release instructions. Large benchmark bundles can be attached separately as GitHub release assets or a DOI-backed archive.

## Repository Layout

```text
.
├── benchmark_resources/        # release manifest and bundle documentation
├── benchmark_resources_smoke/  # tiny example bundle for evaluator smoke tests
├── docs/                       # GitHub-facing benchmark and release documentation
├── paper/                      # manuscript source and compiled PDF
├── reports/                    # paper tables, diagnostics, and benchmark summaries
├── scripts/                    # exporters, evaluators, training, and analysis entrypoints
└── src/raicd/                  # reusable package code
```

## Supported Benchmark Families

Primary paper benchmarks:

- `BindingDB_Kd / unseen_drug`
- `BindingDB_Kd / blind_start`
- `BindingDB_Kd / unseen_target`
- `BindingDB_patent / patent_temporal`
- `BindingDB_nonpatent_Kd / nonpatent_temporal`

Supporting and robustness benchmarks:

- `BindingDB_Ki / unseen_target`
- `DAVIS / unseen_target`
- `BindingDB_Kd / scaffold_drug`
- `BindingDB_patent / patent_temporal_v2017`
- `BindingDB_patent / patent_temporal_pair_novel`
- `BindingDB_patent / patent_temporal_drug_novel`

Benchmark definitions and resource schema are documented in [`docs/BENCHMARKS.md`](docs/BENCHMARKS.md).

## Installation

The repository can be used in two tiers.

Core benchmark export and evaluator usage:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-core.txt
pip install -e . --no-deps
```

Optional training and analysis dependencies:

```bash
pip install -r requirements-models.txt
```

The local development environment used in the paper is documented in [`AGENTS.md`](AGENTS.md).

## Quick Start

Export one benchmark bundle:

```bash
PYTHONPATH=src python scripts/export_benchmark_resource.py \
  --dataset BindingDB_Kd \
  --split unseen_target \
  --seed 0
```

Evaluate an external prediction CSV:

```bash
PYTHONPATH=src python scripts/evaluate_prediction_csv.py \
  --reference-csv benchmark_resources/BindingDB_Kd/unseen_target/seed0/test.csv \
  --prediction-csv path/to/predictions.csv \
  --output path/to/eval.json
```

Run the smoke example:

```bash
PYTHONPATH=src python scripts/evaluate_prediction_csv.py \
  --reference-csv benchmark_resources_smoke/BindingDB_Kd/unseen_target/seed0/test.csv \
  --prediction-csv benchmark_resources_smoke/mock_predictions.csv \
  --output benchmark_resources_smoke/mock_eval.json
```

Export the paper benchmark suite in one shot:

```bash
bash scripts/export_benchmark_suite.sh
```

## Reproducibility Guides

- benchmark catalog: [`docs/BENCHMARKS.md`](docs/BENCHMARKS.md)
- data provenance and local staging: [`docs/DATA_ACCESS.md`](docs/DATA_ACCESS.md)
- manuscript reproduction and release flow: [`docs/REPRODUCE_BENCHMARKS.md`](docs/REPRODUCE_BENCHMARKS.md)
- GitHub release checklist: [`docs/GITHUB_RELEASE_CHECKLIST.md`](docs/GITHUB_RELEASE_CHECKLIST.md)

## Manuscript Assets

- compiled paper PDF: [`paper/main.pdf`](paper/main.pdf)
- live benchmark summary table: [`reports/BENCHMARK_TABLE_LIVE.md`](reports/BENCHMARK_TABLE_LIVE.md)
- external-panel summary: [`reports/EXTERNAL_PANEL_LIVE.md`](reports/EXTERNAL_PANEL_LIVE.md)
- patent diagnosis: [`reports/PATENT_SHIFT_DIAGNOSIS.md`](reports/PATENT_SHIFT_DIAGNOSIS.md)

## Data Redistribution Note

This repository is structured so that the public GitHub snapshot can remain lightweight. Before publishing generated benchmark bundles, verify that the redistribution terms for the underlying datasets are compatible with the intended release channel. The expected local data layout and recommended release practice are documented in [`docs/DATA_ACCESS.md`](docs/DATA_ACCESS.md).

## Release Snapshot

The current manuscript-linked snapshot is described in [`benchmark_resources/RELEASE_MANIFEST.md`](benchmark_resources/RELEASE_MANIFEST.md).
