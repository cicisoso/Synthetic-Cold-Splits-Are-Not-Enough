# Target-Side Memory Redo

## Motivation

The first functional target memory attempt was still too dense. Drug chemotype weights were soft over all clusters, so every target accumulated support across all chemotypes. On `BindingDB_Kd / unseen_target`, that produced target profiles with all 32 chemotypes active and high entropy, which matched the negative result from the first FTM prototype.

## Redesign

This round changed the target-side memory in three ways:

1. Drug chemotype assignments are now sparse top-k instead of dense softmax over all clusters.
2. Target chemotype profiles are no longer raw bind-rate vectors. They are signed chemotype preferences relative to the global chemotype prior.
3. Low-support target-cluster estimates are shrunk toward zero with count-based shrinkage, so weak targets do not broadcast noise across the whole memory.

The target-memory model then predicts these signed chemotype preferences from the target embedding and uses them as target-side functional memory, while keeping drug-side retrieval.

## Data Diagnosis

Using the original dense target memory on `BindingDB_Kd / unseen_target`:

- every train target had all 32 chemotypes active
- train profile entropy mean was about `0.63`
- `230 / 764` train targets had effective soft count below `5`
- `312 / 764` train targets had effective soft count below `10`

Using the redesigned sparse signed target memory with `num_chemotypes=32`, `chemotype_topk=4`, `profile_shrinkage=8.0`:

- prior range: `0.086` to `0.954`
- target profile range: `-0.416` to `0.131`
- mean absolute profile value: `0.0063`
- mean nonzero chemotypes per target: `6.49`
- median nonzero chemotypes per target: `7`
- `687 / 764` targets have at most `8` active chemotypes

This confirms the new memory is much sharper and much less noisy.

## Results

### Previous unseen-target baselines

- `base`: `AUPRC 0.5444`, `AUROC 0.7856`
- `RAICD both`: `AUPRC 0.4652`, `AUROC 0.7440`
- `RAICD drug_only`: `AUPRC 0.5159`, `AUROC 0.7655`
- first dense FTM smoke: `AUPRC 0.4707`, `AUROC 0.7586`

### Redesigned sparse FTM

Full seed-0 run:

- `FTM sparse`: `AUPRC 0.5862`, `AUROC 0.7992`

Bucket breakdown against `base`:

- bucket 0: `base 0.4135 / 0.7626`, `FTM sparse 0.3889 / 0.7560`
- bucket 1: `base 0.4988 / 0.7557`, `FTM sparse 0.5631 / 0.7831`
- bucket 2: `base 0.6315 / 0.7783`, `FTM sparse 0.6803 / 0.8007`

Diagnostics for `FTM sparse`:

- `cluster_match_mean`: `0.0076`
- `profile_entropy_mean`: `0.4972`
- `profile_magnitude_mean`: `0.0163`

Interpretation: the redesigned target-side memory is not uniformly better across all overlap regimes, but it is decisively better in medium and high-overlap unseen-target cases and finally beats the base model overall.

### Base + FTM sparse meta-router

Two-stage routing between `base` and `FTM sparse` further improves the seed-0 result:

- `meta-router(base, ftm_sparse)`: `AUPRC 0.5882`, `AUROC 0.8028`
- route weight mean: `[0.3154, 0.6846]`

Bucket breakdown:

- bucket 0: `0.3997 / 0.7645`
- bucket 1: `0.5648 / 0.7837`
- bucket 2: `0.6753 / 0.8016`

## Matching 3-Seed Comparison

To make the unseen-target claim fair, I ran matching 3-seed baselines and routers using the same split seeds as the sparse FTM runs.

Per-seed test metrics:

- seed 0: `base 0.5444 / 0.7856`, `FTM sparse 0.5862 / 0.7992`, `router(base, ftm) 0.5882 / 0.8028`
- seed 1: `base 0.5826 / 0.7853`, `FTM sparse 0.6124 / 0.7993`, `router(base, ftm) 0.5911 / 0.8013`
- seed 2: `base 0.4402 / 0.7514`, `FTM sparse 0.4330 / 0.7559`, `router(base, ftm) 0.4414 / 0.7524`

Mean and population std:

- `base`: `AUPRC 0.5224 ± 0.0602`, `AUROC 0.7741 ± 0.0161`
- `FTM sparse`: `AUPRC 0.5439 ± 0.0791`, `AUROC 0.7848 ± 0.0204`
- `router(base, ftm)`: `AUPRC 0.5402 ± 0.0699`, `AUROC 0.7855 ± 0.0234`

Interpretation:

- `FTM sparse` beats `base` on 2 of 3 seeds and improves the 3-seed mean on both AUPRC and AUROC.
- The two-stage router is the best seed-0 model and slightly improves the mean AUROC, but its mean AUPRC is slightly below standalone `FTM sparse` because it leans too much toward `base` on seeds 1 and 2.
- The main remaining issue is robustness. Seed 2 stays hard for all methods, so the target-memory gain is real but not yet fully stable.

Bucket-level pattern for the router:

- seed 0: improves bucket 1 and 2 over `base`
- seed 1: mostly tracks `base`, with small gains in all buckets
- seed 2: nearly collapses back to `base`

This supports the current reading that sparse target memory is the stronger expert, while the router still needs better regime features or a stronger validation split to choose experts reliably.

## Robustness Follow-Up

I tested two follow-up robustness ideas specifically to address the hard `seed 2` split.

### Reliability-gated fusion (`rftm`)

This variant fused an internal `base` head and an `FTM` head using overlap and target-memory confidence features.

- `seed 2 rftm`: `AUPRC 0.4231`, `AUROC 0.7795`

Interpretation: the gate improved AUROC but hurt AUPRC. It over-smoothed ranking and is not a better replacement for the main model.

### Conservative target memory via profile-magnitude regularization

I added a `profile_magnitude` penalty to discourage overly strong target-memory activations.

- `seed 2`, `profile-magnitude-weight=1.0`: `AUPRC 0.4404`, `AUROC 0.7563`
- versus original `seed 2 FTM sparse`: `0.4330 / 0.7559`

Matching 3-seed results for this conservative variant:

- `seed 0`: `0.5617 / 0.7951`
- `seed 1`: `0.6030 / 0.7905`
- `seed 2`: `0.4404 / 0.7563`
- mean: `AUPRC 0.5350 ± 0.0690`, `AUROC 0.7806 ± 0.0173`

Interpretation: this improves the hardest split and reduces variance, but it also weakens the stronger seeds. It is a useful robustness knob, not the new main model.

### Selective fallback between `base` and `FTM sparse`

I also tested a post-hoc selective fallback that uses validation diagnostics to decide whether to trust `base`, `FTM sparse`, or a simple blend. The searched rule family used only four interpretable diagnostics: `profile_magnitude`, `profile_entropy`, `cluster_match`, and `overlap`.

Per-seed best selective rules:

- `seed 0`: `profile_magnitude` low-tail fallback, `AUPRC 0.5900`, `AUROC 0.8069`
- `seed 1`: `profile_entropy` high-tail fallback, `AUPRC 0.6083`, `AUROC 0.7948`
- `seed 2`: mostly-FTM rule with a small low-magnitude fallback, `AUPRC 0.4371`, `AUROC 0.7562`

Matching 3-seed summary:

- validation-tuned selective fallback: `AUPRC 0.5451 ± 0.0768`, `AUROC 0.7860 ± 0.0216`
- best fixed cross-seed rule (`q25_half_else_base`): `AUPRC 0.5366`, `AUROC 0.7825`

Interpretation: a post-hoc selective fallback can squeeze out a small average gain over standalone `FTM sparse`, but only when the rule is tuned separately for each split seed. Once I constrain the mechanism to a single fixed cross-seed rule, the gain disappears. So this is a promising reliability analysis, not yet a stable replacement for the main model.

## Model Selection

The final choice is to keep **original `FTM sparse`** as the primary method.

Why:

- it has the best mean AUPRC across the matching 3-seed comparison
- it still improves mean AUROC over `base`
- the `rftm` fusion variant is not competitive on AUPRC
- the conservative `profile-magnitude` penalty is more robust on `seed 2`, but lowers the overall mean compared with original `FTM sparse`
- the selective fallback slightly improves the 3-seed mean, but its chosen rule is not stable across seeds and the best fixed rule still trails `FTM sparse`

So the clean current framing is:

- **primary method**: original `FTM sparse`
- **secondary robustness analysis**: conservative target-memory regularization
- **exploratory secondary result**: per-split selective fallback between `base` and `FTM sparse`
- **negative/secondary ablation**: free reliability-gated fusion (`rftm`)

## Conclusion

This fixes the main failure mode identified in the previous round. The problem was not target-side memory as a direction; it was the definition of the memory. Dense chemotype-rate profiles were too smooth and too noisy. Sparse top-k chemotype assignment plus signed, shrunk target preferences is the first target-side memory variant that beats the unseen-target base model.

The most defensible current claim is:

> cold-start target generalization improves when target memory is defined as sparse functional chemotype preference rather than sequence-neighbor retrieval or dense chemotype-rate averaging.

The strongest version of that claim uses the original `FTM sparse` model as the main line, with the later conservative variants reported as robustness analysis rather than as the new primary method. A validation-tuned selective fallback is worth mentioning as an exploratory appendix result, but it is not yet stable enough to replace the main model.
