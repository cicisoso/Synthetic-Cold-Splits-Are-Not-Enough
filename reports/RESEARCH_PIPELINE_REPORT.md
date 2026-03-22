# Research Pipeline Report

**Direction**: cold start in drug target interaction prediction  
**Chosen Idea**: `RAICD`  
**Date**: 2026-03-21  
**Pipeline**: idea-discovery → implement → run-experiment → auto-review-loop

## Journey Summary

- Ideas generated: 3
- Chosen method: retrieval-augmented inductive cold-start DTI
- Implementation: bootstrapped a full minimal project from an empty workspace
- Primary dataset: `BindingDB_Kd`
- Completed strict splits:
  - `unseen_drug`
  - `blind_start`

## Current Status

- [x] Idea discovery
- [x] Implementation scaffold
- [x] Initial baseline vs method experiments
- [x] First auto-review loop round
- [x] `unseen_target` redesign with sparse functional target memory
- [x] Matching 3-seed comparison for `base`, `ftm_sparse`, and `router(base, ftm)` on `unseen_target`
- [x] Exploratory selective fallback analysis on `unseen_target`
- [ ] Multi-seed verification on the remaining splits
- [ ] Cross-seed hard-split robustness improvement that preserves the current mean win

## Remaining TODOs

- run matching multi-seed verification on `unseen_drug` and `blind_start`
- improve hard-split robustness for `unseen_target` without sacrificing the `ftm_sparse` mean advantage
- stabilize the selective fallback / abstention story with a cross-seed transferable rule, or keep it as appendix-only analysis
- decide whether to push the target-memory line into the main paper or keep it as a focused `unseen_target` contribution

## Round 1 Results

- `BindingDB_Kd / unseen_drug`
  - `base`: AUPRC `0.608`, AUROC `0.823`
  - `raicd` with similarity-biased attention: AUPRC `0.614`, AUROC `0.840`
- `BindingDB_Kd / blind_start`
  - `base`: AUPRC `0.352`, AUROC `0.658`
  - `raicd` with similarity-biased attention: AUPRC `0.407`, AUROC `0.686`
- `BindingDB_Kd / unseen_target`
  - `base`: AUPRC `0.544`, AUROC `0.786`
  - `raicd` with similarity-biased attention: AUPRC `0.465`, AUROC `0.744`

## Ablation Results

- `unseen_drug`
  - `raicd drug_only`: AUPRC `0.522`, AUROC `0.793`
  - `raicd target_only`: AUPRC `0.538`, AUROC `0.793`
  - conclusion: both-side retrieval is necessary
- `unseen_target`
  - `raicd drug_only`: AUPRC `0.516`, AUROC `0.765`
  - `raicd target_only`: AUPRC `0.475`, AUROC `0.752`
  - conclusion: drug-only is the least bad retrieval variant, but base still wins

## Target-Memory Results

- `unseen_target / seed0`
  - `ftm_sparse`: AUPRC `0.5862`, AUROC `0.7992`
  - `router(base, ftm_sparse)`: AUPRC `0.5882`, AUROC `0.8028`
- matching 3-seed summary on `unseen_target`
  - `base`: `0.5224 ± 0.0602` AUPRC, `0.7741 ± 0.0161` AUROC
  - `ftm_sparse`: `0.5439 ± 0.0791` AUPRC, `0.7848 ± 0.0204` AUROC
  - `router(base, ftm_sparse)`: `0.5402 ± 0.0699` AUPRC, `0.7855 ± 0.0234` AUROC
- robustness follow-up
  - free fusion `rftm` improved AUROC on hard splits but hurt AUPRC and is not retained as the main variant
  - `profile-magnitude` regularization improved the hardest split, but reduced the overall 3-seed mean versus original `ftm_sparse`
  - validation-tuned selective fallback reached `0.5451 ± 0.0768` AUPRC and `0.7860 ± 0.0216` AUROC, slightly above standalone `ftm_sparse` on the 3-seed mean
  - the best fixed cross-seed fallback rule only reached `0.5366 / 0.7825`, so the fallback signal is still exploratory rather than stable
- conclusion
  - keep original `ftm_sparse` as the primary target-side memory model
  - treat selective fallback as a promising secondary analysis, not as the main method

## Files Added or Updated

- [README.md](/root/exp/dti_codex/README.md)
- [reports/IDEA_REPORT.md](/root/exp/dti_codex/reports/IDEA_REPORT.md)
- [reports/IMPLEMENTATION_PLAN.md](/root/exp/dti_codex/reports/IMPLEMENTATION_PLAN.md)
- [reports/AUTO_REVIEW.md](/root/exp/dti_codex/reports/AUTO_REVIEW.md)
- [scripts/train_raicd.py](/root/exp/dti_codex/scripts/train_raicd.py)
- [src/raicd/data.py](/root/exp/dti_codex/src/raicd/data.py)
- [src/raicd/model.py](/root/exp/dti_codex/src/raicd/model.py)
- [reports/TARGET_MEMORY_REDO.md](/root/exp/dti_codex/reports/TARGET_MEMORY_REDO.md)
- [scripts/run_bindingdb_unseen_target_ftm_sparse.sh](/root/exp/dti_codex/scripts/run_bindingdb_unseen_target_ftm_sparse.sh)
- [scripts/run_unseen_target_base_ftm_match.sh](/root/exp/dti_codex/scripts/run_unseen_target_base_ftm_match.sh)
- [scripts/eval_selective_ftm.py](/root/exp/dti_codex/scripts/eval_selective_ftm.py)
- [scripts/run_unseen_target_selective_ftm_match.sh](/root/exp/dti_codex/scripts/run_unseen_target_selective_ftm_match.sh)
