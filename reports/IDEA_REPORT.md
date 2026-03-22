# IDEA_REPORT

**Direction**: cold start in drug target interaction prediction  
**Date**: 2026-03-21  
**Pipeline Mode**: `research-pipeline` with `AUTO_PROCEED=true`

## Top Ideas

1. `RAICD` — Retrieval-Augmented Inductive Cold-start DTI
2. Confidence-aware cold-start DTI
3. Overlap-aware cold-start benchmarking

## External Review Summary

An external critical review ranked the ideas in the same order:

- `RAICD` is strongest because it directly targets the documented cold-drug weakness of recent DTI models while staying compute-feasible on a single RTX 4090.
- Confidence-aware DTI is useful, but stronger as a secondary contribution than as the main paper.
- Overlap-aware benchmarking is important, but too close to recent generalization-analysis work if used as the sole headline contribution.

## Chosen Idea

`AUTO_PROCEED: selected Idea 1 — RAICD`

## Working Hypothesis

Cold-start DTI failure is largely a conditional evidence aggregation problem. For an unseen drug or target, a model should explicitly retrieve the nearest seen entities from the training bank and combine their support using the opposite-side query as context.

## Minimal Publishable Claim

Compared with a matched non-retrieval baseline, query-conditioned retrieval should improve:

- unseen-drug AUROC and AUPRC
- blind-start robustness
- performance in low train-test similarity regimes

## Source Anchors

- DTI-LM: https://academic.oup.com/bioinformatics/article/40/9/btae533/7747660
- DrugLAMP: https://pubmed.ncbi.nlm.nih.gov/39570605
- SP-DTI: https://academic.oup.com/bioinformatics/article/41/3/btaf011/7951882
- GS-DTI: https://pubmed.ncbi.nlm.nih.gov/40795814/
- ColdstartCPI: https://www.nature.com/articles/s41467-025-61745-7
- SPECTRA: https://www.nature.com/articles/s42256-024-00931-6
- Towards a more inductive world for drug repurposing approaches: https://www.nature.com/articles/s42256-025-00987-y
