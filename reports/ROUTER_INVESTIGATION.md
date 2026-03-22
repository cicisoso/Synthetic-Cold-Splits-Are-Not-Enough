# Router Investigation

**Date**: 2026-03-21  
**Goal**: upgrade RAICD into split-adaptive expert routing and test whether sample-level routing resolves the asymmetry across cold-start regimes.

## Setup

Available experts from existing full runs:

- `base`
- `raicd both`
- `raicd drug_only`
- `raicd target_only`

Target splits investigated:

- `unseen_drug`
- `unseen_target`
- `blind_start`

## Phase A: Joint Router Inside The Main Model

Implemented a new `SplitAdaptiveRouter` in [src/raicd/model.py](/root/exp/dti_codex/src/raicd/model.py) and exposed it in [scripts/train_raicd.py](/root/exp/dti_codex/scripts/train_raicd.py).

Design:

- shared encoders and retrieval blocks
- four experts per sample:
  - `base`
  - `drug_only`
  - `target_only`
  - `both`
- router sees pair features, retrieval features, and expert raw logits
- final prediction is a weighted sum of expert logits

Result:

- joint router smoke on `unseen_drug` underperformed existing single experts
- adding auxiliary expert supervision still did not recover competitive performance

Conclusion:

- end-to-end joint routing from scratch is a negative result in the current lightweight setup
- likely cause: the experts are not specialized enough when trained jointly with the router

## Phase B: Two-Stage Meta-Router On Frozen Experts

Added [scripts/train_meta_router.py](/root/exp/dti_codex/scripts/train_meta_router.py).

This trains a lightweight router on frozen expert predictions from the validation split, then evaluates on test.

### Results

#### Unseen drug

- best single expert before routing:
  - `raicd both`: AUPRC `0.614`, AUROC `0.840`
- two-stage meta-router:
  - AUPRC `0.643`, AUROC `0.835`

Routing behavior:

- mean route weights: `[0.135, 0.156, 0.110, 0.598]`
- expert order: `base`, `both`, `drug_only`, `target_only`
- the router mostly leans on `target_only`, but still uses all four experts

Interpretation:

- sample-adaptive routing is real signal here, not just a rhetorical idea
- the gain is mainly from better precision-recall tradeoff rather than higher AUROC

#### Unseen target

- best single expert before routing:
  - `base`: AUPRC `0.544`, AUROC `0.786`
- 4-expert meta-router:
  - AUPRC `0.524`, AUROC `0.770`
- 2-expert meta-router (`base + drug_only`):
  - AUPRC `0.528`, AUROC `0.775`

Routing behavior of 4-expert router:

- mean route weights: `[0.073, 0.113, 0.622, 0.191]`
- the router mostly chooses `drug_only`

Interpretation:

- routing cannot fully rescue `unseen_target`
- the issue is upstream: target-side generalization is weak enough that switching between current experts is insufficient

#### Blind start

- best single expert before routing:
  - `raicd both`: AUPRC `0.407`, AUROC `0.686`
- 2-expert meta-router (`base + both`):
  - AUPRC `0.402`, AUROC `0.683`

Interpretation:

- for blind-start, routing mostly collapses to the `both` expert and does not add much

## Main Takeaways

1. `Split-adaptive expert routing` is worth keeping, but only in the two-stage form.
2. It is clearly useful on `unseen_drug`.
3. It does not solve `unseen_target`, which remains the main unresolved research problem.
4. This strengthens the larger claim that cold-start DTI is heterogeneous across regimes and should not be treated with one uniform inductive bias.

## Most Honest Current Claim

A frozen-expert, sample-adaptive router improves unseen-drug DTI prediction beyond any single expert, but target-cold generalization remains bottlenecked by the quality of target-side representation and memory.

## Best Next Research Step

Do not spend the next cycle squeezing more out of the router itself.

The highest-value next method idea is:

- keep the two-stage router for the drug-cold and mixed regimes
- redesign target-side memory or target representation for `unseen_target`
- the current target-side retrieval appears to be the limiting factor rather than the absence of routing
