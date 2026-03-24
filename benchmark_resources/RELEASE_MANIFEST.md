# Benchmark Release Manifest

This document describes the frozen benchmark snapshot associated with the current manuscript revision and the intended public release layout.

## Snapshot Identity

- manuscript revision date: `2026-03-24`
- repository URL: `https://github.com/cicisoso/Synthetic-Cold-Splits-Are-Not-Enough`
- commit short hash: `a5d6b8b`
- commit full hash: `a5d6b8bd96c98fed73c5a9771c2a1079c9f12255`

## Public Repository Policy

The GitHub repository is intended to publish:

- source code under `src/` and `scripts/`
- benchmark documentation under `docs/`
- smoke examples under `benchmark_resources_smoke/`
- benchmark schema and release notes under `benchmark_resources/`
- manuscript materials under `paper/` and `reports/`

Large generated benchmark bundles under `benchmark_resources/<dataset>/<split>/seed<k>/` are not committed by default. They should be exported locally and attached as release assets or archived separately with a fixed DOI.

## Benchmark Bundles Covered By The Paper

Primary benchmark families:

- `BindingDB_Kd / unseen_drug`
- `BindingDB_Kd / blind_start`
- `BindingDB_Kd / unseen_target`
- `BindingDB_patent / patent_temporal`
- `BindingDB_nonpatent_Kd / nonpatent_temporal`

Supporting and robustness bundles:

- `BindingDB_Ki / unseen_target`
- `DAVIS / unseen_target`
- `BindingDB_Kd / scaffold_drug`
- `BindingDB_patent / patent_temporal_v2017`
- `BindingDB_patent / patent_temporal_pair_novel`
- `BindingDB_patent / patent_temporal_drug_novel`

## Bundle Contents

Each exported bundle is expected to contain:

- `manifest.json`: fixed metadata, row counts, prevalence, and canonical file paths
- `train.csv`, `valid.csv`, `test.csv`: labeled partitions with stable `example_id`
- `all.csv`: concatenated audit table
- `drugs.csv`, `targets.csv`: entity vocabularies aligned to exported IDs
- `train_pairs.csv`, `valid_pairs.csv`, `test_pairs.csv`, `all_pairs.csv`: pair-level views

## Evaluators

- probability-based benchmark evaluator: `scripts/evaluate_prediction_csv.py`
- decision-facing ranking evaluator: `scripts/evaluate_decision_csv.py`

## Manuscript Summaries Anchored To This Snapshot

- main benchmark table: `reports/BENCHMARK_TABLE_LIVE.md`
- external-panel summary: `reports/EXTERNAL_PANEL_LIVE.md`
- patent diagnosis: `reports/PATENT_SHIFT_DIAGNOSIS.md`
- paired bootstrap summaries: `reports/bootstrap_pairwise_ci_expanded_panel.json`
- controlled-patent bootstrap summaries: `reports/bootstrap_pairwise_ci_controlled_patent.json`

## Recommended Public Release Shape

For a GitHub release or Zenodo archive, include:

1. the source snapshot at the commit above
2. exported benchmark bundles for the paper benchmark families
3. the compiled manuscript PDF
4. a short changelog or release note pointing to this manifest

Before publishing raw or derived benchmark tables, verify the redistribution terms of the upstream datasets. See `docs/DATA_ACCESS.md` for the expected local data staging policy.
