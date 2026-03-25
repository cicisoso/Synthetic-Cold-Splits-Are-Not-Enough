# HANDOFF

## 1. Project Status In One Paragraph

This repository started as a method-development workspace for cold-start DTI, but it has already pivoted into a benchmark-first paper. The current manuscript is **not** arguing that `RAICD` or `FTM` is the best general DTI model. The final scientific claim is that **model ranking in DTI is benchmark-sensitive**: synthetic cold-start splits, temporal/provenance benchmarks, and overlap-restricted variants can produce different winners. The current paper target is **Journal of Computer-Aided Molecular Design (JCAMD)**, and the paper has already been reworked into a chemoinformatics validation/methodology style.

## 2. Final Scientific Framing

Current title:

- `Benchmarking synthetic cold-start and temporal/provenance distribution shifts in drug-target interaction prediction`

Current paper focus:

- benchmark design changes model ranking in DTI
- synthetic cold-start and temporal/provenance evaluation are not interchangeable
- overlap policy inside the temporal family can also change conclusions
- the repository contributes reusable split manifests and standalone evaluators

What **not** to do unless explicitly redirected:

- do not revert the paper back into a method paper about `RAICD`
- do not overclaim that `RAICD`, `FTM`, or any single model is the universal winner
- do not treat the synthetic results alone as the main story

## 3. Current Manuscript State

Primary manuscript files:

- `paper/main.tex`
- `paper/main.pdf`

Current submission target:

- `JCAMD`

Formatting/status:

- already migrated to Springer `sn-jnl`
- journal-style title, abstract, discussion, declarations, figures, and tables are in place
- paper compiles cleanly
- the main missing submission metadata are still human-facing items such as real author names, affiliations, corresponding email, and finalized declarations

Submission checklist:

- see `reports/JCAMD_SUBMISSION_CHECKLIST.md`

## 4. Final Paper Narrative

The paper currently has a stable benchmark narrative:

1. On the synthetic `BindingDB_Kd` panel, there is already **no universal winner**.
2. On temporal/provenance benchmarks, the ranking changes again.
3. Within the patent temporal/provenance family, controlled overlap variants and slice diagnoses show that the shift is structured, not monolithic.
4. Supporting OOD target-cold benchmarks (`BindingDB_Ki`, `DAVIS`) also remain heterogeneous and do not recover a single universal winner.

This is the core result that should be preserved.

## 5. Implemented Model Families

### Current five-model comparison panel

These are the models that matter for the paper:

- `base`: descriptor-based MLP reference model
- `rf`: Random Forest on the exact same Morgan + hashed-k-mer descriptor set as `base`
- `dtilm`: pooled LM baseline
- `hyperpcm`: task-conditioned pooled LM baseline
- `graphdta`: GraphDTA-style graph/CNN baseline

### Legacy exploratory models still implemented

These remain in the codebase, but are now secondary:

- `raicd`: retrieval-augmented inductive cold-start model
- `ftm`: functional target memory model
- `rftm`: more conservative fused target-memory variant
- `router`: split-adaptive expert router
- `train_meta_router.py`: two-stage meta-router

These methods are important mainly because their failures/successes informed the pivot:

- `RAICD` helped on synthetic `blind_start`, but failed on real OOD
- `FTM` helped on synthetic `unseen_target`, but did not generalize across `patent`, `Ki`, and `DAVIS`

## 6. Implementation Details By Model

### `base`

Code:

- `src/raicd/model.py`
- `scripts/train_raicd.py --model base`

Implementation:

- drug input: RDKit Morgan fingerprint
- target input: hashed protein k-mer vector
- separate MLP encoders for drug and target
- pair feature = `[drug, target, drug * target, |drug - target|]`
- prediction head = 2-layer MLP

### `rf`

Code:

- `src/raicd/classical_baselines.py`
- `scripts/train_classical_baseline.py`

Implementation:

- exact same drug and target descriptors as `base`
- pair feature matrix is concatenation-based
- `RandomForestClassifier` with `class_weight="balanced_subsample"`
- this isolates learner effects from representation effects

### `dtilm`

Code:

- `src/raicd/lm_baselines.py`
- `src/raicd/lm_features.py`
- `scripts/train_recent_baseline.py --model dtilm`

Implementation:

- drug encoder: pooled ChemBERTa features
- target encoder: pooled ESM2 features
- downstream adapter: concatenation + MLP

### `hyperpcm`

Code:

- `src/raicd/lm_baselines.py`
- `scripts/train_recent_baseline.py --model hyperpcm`

Implementation:

- same pooled LM inputs as `dtilm`
- target branch generates conditioning terms (`gamma`, `beta`, `weight`, `bias`) for the drug representation

### `graphdta`

Code:

- `src/raicd/graph_baselines.py`
- `scripts/train_graph_baseline.py`

Implementation:

- drug encoder: small GCN over RDKit molecular graph
- target encoder: amino-acid token CNN
- pair head: MLP over graph and protein embeddings

### `raicd`

Code:

- `src/raicd/model.py`
- `scripts/train_raicd.py --model raicd`

Implementation:

- same descriptor inputs as `base`
- train-only top-k drug/target neighbor banks
- pair-conditioned retrieval scoring
- similarity-biased attention over retrieved neighbors
- retrieval modes: `both`, `drug_only`, `target_only`
- optional retrieval gate

Current role:

- secondary/exploratory
- used to support the argument that synthetic gains do not necessarily survive real OOD

### `ftm` / `rftm`

Code:

- `src/raicd/model.py`
- `scripts/train_raicd.py --model ftm`
- `scripts/train_raicd.py --model rftm`

Implementation:

- drug chemotype weights are learned via sparse top-k clustering assignments
- targets store chemotype preference profiles relative to a global prior
- count-based shrinkage regularizes sparse target statistics
- `rftm` is a more conservative fusion variant

Current role:

- secondary/exploratory
- useful in synthetic `unseen_target`, but not the final paper anchor

## 7. Data And Benchmark Definitions

Core benchmark code:

- `src/raicd/data.py`
- `src/raicd/benchmark_resource.py`
- `scripts/export_benchmark_resource.py`
- `scripts/export_benchmark_suite.sh`

### Primary synthetic panel

- `BindingDB_Kd / unseen_drug`
- `BindingDB_Kd / blind_start`
- `BindingDB_Kd / unseen_target`

### Primary temporal/provenance panel

- `BindingDB_patent / patent_temporal`
- `BindingDB_nonpatent_Kd / nonpatent_temporal`

### Supporting OOD panel

- `BindingDB_Ki / unseen_target`
- `DAVIS / unseen_target`

### Robustness / controlled variants

- `BindingDB_Kd / scaffold_drug`
- `BindingDB_patent / patent_temporal_v2017`
- `BindingDB_patent / patent_temporal_pair_novel`
- `BindingDB_patent / patent_temporal_drug_novel`

Important semantics:

- `BindingDB_patent` is **temporal/provenance OOD**, not pure time shift
- `BindingDB_nonpatent_Kd` partially reduces provenance confounding, but is much smaller
- overlap-restricted patent variants are important for showing that conclusions change even inside the temporal family

## 8. Canonical Resource / Evaluator Layer

This part is important for both the paper and the open-source release.

Key files:

- `scripts/evaluate_prediction_csv.py`
- `scripts/evaluate_decision_csv.py`
- `benchmark_resources/RELEASE_MANIFEST.md`
- `docs/BENCHMARKS.md`
- `docs/DATA_ACCESS.md`
- `docs/REPRODUCE_BENCHMARKS.md`

Evaluator contract:

- all exported rows receive stable `example_id`
- external predictions are joined on `example_id`
- `evaluate_prediction_csv.py` reports global metrics plus overlap buckets
- `evaluate_decision_csv.py` is the decision-facing evaluator

Public-release policy:

- the repository is currently set up to keep large generated `benchmark_resources/<dataset>/<split>/seed<k>/` directories out of Git
- code, manifests, smoke example, docs, and manuscript stay in Git
- large generated bundles are intended for GitHub Release/Zenodo-style archival instead

## 9. Key Experimental Conclusions

The most important topline summaries are already aggregated in:

- `reports/BENCHMARK_TABLE_LIVE.md`
- `reports/EXTERNAL_PANEL_LIVE.md`
- `reports/PATENT_SHIFT_DIAGNOSIS.md`
- `reports/UNCERTAINTY_SUPPORT.md`

### Synthetic reference panel

- `BindingDB_Kd / unseen_drug`
  - `base`: `0.5509 ± 0.0900 / 0.7794 ± 0.0534`
  - `RAICD`: `0.5228 ± 0.0828 / 0.7803 ± 0.0506`
  - `RF`: `0.7339 ± 0.0051 / 0.8854 ± 0.0088`
  - read: retrieval loses on mean AUPRC; `RF` is strongest

- `BindingDB_Kd / blind_start`
  - `base`: `0.3737 ± 0.0229 / 0.6778 ± 0.0151`
  - `RAICD`: `0.4024 ± 0.0508 / 0.6844 ± 0.0145`
  - `RF`: `0.4512 ± 0.0373 / 0.7451 ± 0.0260`
  - read: `RAICD` beats `base`, but `RF` is still strongest

- `BindingDB_Kd / unseen_target`
  - `base`: `0.5224 ± 0.0602 / 0.7741 ± 0.0161`
  - `FTM`: `0.5439 ± 0.0791 / 0.7848 ± 0.0204`
  - `RF`: `0.5183 ± 0.0612 / 0.7838 ± 0.0218`
  - read: `FTM` wins over `base`, but this did not generalize broadly

### Primary temporal/provenance panel

- `BindingDB_patent / patent_temporal`
  - `base`: `0.7772 ± 0.0086 / 0.7223 ± 0.0109`
  - `RAICD`: `0.7692 ± 0.0018 / 0.7032 ± 0.0010`
  - `FTM`: `0.7721 ± 0.0025 / 0.7059 ± 0.0037`
  - `DTI-LM`: `0.7825 ± 0.0078 / 0.7362 ± 0.0083`
  - `RF`: `0.8234 ± 0.0012 / 0.7773 ± 0.0017`
  - read: temporal/provenance ranking is different again; `RF` is strongest in the five-model panel

- `BindingDB_nonpatent_Kd / nonpatent_temporal`
  - `base`: `0.6369 ± 0.0173 / 0.7333 ± 0.0081`
  - `DTI-LM`: `0.6531 ± 0.0066 / 0.7644 ± 0.0041`
  - `RF`: `0.7201 ± 0.0012 / 0.7627 ± 0.0020`
  - `GraphDTA-style`: `0.6635 ± 0.0142 / 0.7334 ± 0.0096`
  - read: temporal/provenance family remains heterogeneous, but `RF` still wins here

### Supporting OOD panel

- `BindingDB_Ki / unseen_target`
  - winner: `base`
  - read: support benchmark does not preserve the same winner as patent temporal

- `DAVIS / unseen_target`
  - winner: `RF`
  - read: support benchmark changes the winner yet again

This is exactly why the paper is now benchmark-first.

## 10. Uncertainty Support

Paired bootstrap support is already done for the headline comparisons:

- `blind_start`: `RAICD - base = +0.0288`, CI `[+0.0145, +0.0431]`
- `unseen_target`: `FTM - base = +0.0214`, CI `[+0.0143, +0.0286]`
- `patent`: `RAICD - base = -0.0080`, CI `[-0.0101, -0.0059]`
- `patent`: `FTM - base = -0.0050`, CI `[-0.0072, -0.0029]`
- `patent`: `DTI-LM - base = +0.0054`, CI `[+0.0028, +0.0079]`

Source:

- `reports/UNCERTAINTY_SUPPORT.md`
- `reports/bootstrap_pairwise_ci.json`
- `scripts/bootstrap_pairwise_ci.py`

## 11. Key Slice Diagnosis

The patent benchmark has already been diagnosed by:

- year band
- overlap bucket

Main interpretation:

- temporal/provenance shift is structured, not monolithic
- `RF` dominates aggregate patent performance largely because it wins in the medium/high-overlap regions
- the lowest-overlap region can favor a different family

See:

- `reports/PATENT_SHIFT_DIAGNOSIS.md`
- `scripts/analyze_patent_shift.py`
- `scripts/bootstrap_patent_slices.py`

## 12. Important Scripts

### Core benchmark/export/eval

- `scripts/export_benchmark_resource.py`
- `scripts/export_benchmark_suite.sh`
- `scripts/evaluate_prediction_csv.py`
- `scripts/evaluate_decision_csv.py`

### Training entrypoints

- `scripts/train_raicd.py`
- `scripts/train_recent_baseline.py`
- `scripts/train_classical_baseline.py`
- `scripts/train_graph_baseline.py`

### Summaries and diagnoses

- `scripts/summarize_benchmarks.py`
- `scripts/summarize_external_panel.py`
- `scripts/summarize_benchmark_taxonomy.py`
- `scripts/analyze_patent_shift.py`
- `scripts/analyze_patent_decision_panel.py`
- `scripts/bootstrap_pairwise_ci.py`
- `scripts/bootstrap_patent_slices.py`

### Launcher scripts used during the paper push

- `scripts/run_complete_regime_multiseed.sh`
- `scripts/run_rf_topline_multiseed.sh`
- `scripts/run_dtilm_topline_multiseed.sh`
- `scripts/run_hyperpcm_topline_multiseed.sh`
- `scripts/run_graphdta_topline_multiseed.sh`
- `scripts/run_bindingdb_patent_multiseed.sh`
- `scripts/run_bindingdb_nonpatent_temporal_multiseed.sh`
- `scripts/run_bindingdb_patent_controlled_multiseed.sh`
- `scripts/run_bindingdb_patent_v2017_multiseed.sh`
- `scripts/run_supporting_benchmarks_multiseed.sh`

## 13. Open-Source Repo Preparation Already Done

The repo has already been reorganized for a public benchmark release:

- `README.md` rewritten as a public benchmark repo entrypoint
- `docs/` added for benchmark catalog, data staging, reproduction, and GitHub release checklist
- `.gitignore` updated to keep large local outputs out of Git
- `pyproject.toml`, `requirements-core.txt`, and `requirements-models.txt` added
- `benchmark_resources/README.md` and `benchmark_resources_smoke/README.md` added

Important note:

- the repository is ready for a code-first public release, but a real `LICENSE` still needs to be chosen by the human owner before treating it as a formal open-source release

## 14. What Is Still Human-Blocking

For the paper:

- replace placeholder author names, affiliation, and corresponding email in `paper/main.tex`
- finalize declarations in `paper/main.tex`
- freeze the final submission archive and DOI-backed snapshot if desired

For the public GitHub release:

- choose a license
- decide whether to publish generated benchmark bundles as release assets
- optionally add `CITATION.cff`

## 15. Recommended Next Actions For The Next AI

If the next AI continues the **paper** track:

1. do a final manuscript polish pass without changing the main claim
2. fill title-page and declaration placeholders once human metadata is provided
3. prepare cover letter / submission package for JCAMD

If the next AI continues the **open-source release** track:

1. generate a clean public release checklist from `docs/GITHUB_RELEASE_CHECKLIST.md`
2. add `LICENSE` and optional citation metadata once approved
3. export benchmark bundles and package them as release assets

If the next AI continues **scientific extension** work:

1. keep the benchmark-first framing
2. do not sink more time into making `RAICD` the paper centerpiece
3. only add new experiments if they directly strengthen the benchmark-sensitivity claim

## 16. Minimal Orientation Map

If you only read six files, read these first:

1. `README.md`
2. `paper/main.tex`
3. `reports/BENCHMARK_TABLE_LIVE.md`
4. `reports/EXTERNAL_PANEL_LIVE.md`
5. `reports/PATENT_SHIFT_DIAGNOSIS.md`
6. `reports/UNCERTAINTY_SUPPORT.md`
