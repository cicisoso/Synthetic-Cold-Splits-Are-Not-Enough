# Uncertainty Support

This note reports paired bootstrap confidence intervals for the key ranking claims highlighted in the paper:

1. `BindingDB_Kd / blind_start`: `RAICD` vs `base`
2. `BindingDB_Kd / unseen_target`: `FTM` vs `base`
3. `BindingDB_patent / patent_temporal`: `RAICD` vs `base`
4. `BindingDB_patent / patent_temporal`: `FTM` vs `base`
5. `BindingDB_patent / patent_temporal`: `DTI-LM` vs `base`
6. `BindingDB_Ki / unseen_target`: `RAICD` vs `base`
7. `BindingDB_Ki / unseen_target`: `FTM` vs `base`
8. `DAVIS / unseen_target`: `RAICD` vs `base`
9. `DAVIS / unseen_target`: `FTM` vs `base`

The intended use is limited and reviewer-facing:

- support the wording of the main comparative claims
- show whether the direction of the mean AUPRC delta is stable under paired resampling
- avoid stronger wording than the evidence allows

## Reporting Template

| Comparison | Mean AUPRC delta | 95% paired bootstrap CI | Interpretation |
|-----------|-------------------|-------------------------|----------------|
| `blind_start`: `RAICD - base` | `+0.0288` | `[+0.0145, +0.0431]` | positive delta is stable under paired resampling |
| `unseen_target`: `FTM - base` | `+0.0214` | `[+0.0143, +0.0286]` | synthetic target-cold gain is supported |
| `patent`: `RAICD - base` | `-0.0080` | `[-0.0101, -0.0059]` | temporal real-OOD loss for retrieval is supported |
| `patent`: `FTM - base` | `-0.0050` | `[-0.0072, -0.0029]` | temporal real-OOD loss for target-memory is supported |
| `patent`: `DTI-LM - base` | `+0.0054` | `[+0.0028, +0.0079]` | temporal real-OOD gain for the strongest recent baseline is supported |
| `Ki`: `RAICD - base` | `-0.0249` | `[-0.0271, -0.0226]` | assay-shift loss for retrieval is supported |
| `Ki`: `FTM - base` | `-0.0174` | `[-0.0197, -0.0150]` | assay-shift loss for target-memory is supported |
| `DAVIS`: `RAICD - base` | `-0.0259` | `[-0.0375, -0.0127]` | external-dataset loss for retrieval is supported |
| `DAVIS`: `FTM - base` | `-0.0310` | `[-0.0434, -0.0177]` | external-dataset loss for target-memory is supported |

## Source

- JSON output: [bootstrap_pairwise_ci.json](/root/exp/dti_codex/reports/bootstrap_pairwise_ci.json)
- Script: [bootstrap_pairwise_ci.py](/root/exp/dti_codex/scripts/bootstrap_pairwise_ci.py)

## Interpretation Summary

- The synthetic `blind_start` gain of `RAICD` over `base` is not just a seed-mean artifact; the paired bootstrap CI remains strictly positive.
- The synthetic `unseen_target` gain of `FTM` over `base` is also supported, so the synthetic panel has uncertainty support for all three headline winner claims.
- On the promoted `BindingDB_patent / patent_temporal` benchmark, both `RAICD` and `FTM` remain below `base`, and both paired bootstrap CIs remain strictly negative.
- On the same patent benchmark, `DTI-LM` remains above `base`, and the paired bootstrap CI remains strictly positive.
- On the supporting `BindingDB_Ki` and `DAVIS` target-cold OOD panels, both `RAICD` and `FTM` remain below `base`, and all paired bootstrap CIs remain strictly negative.
- This uncertainty support strengthens the paper's main ranking-reversal claim and makes the supporting OOD negatives harder to dismiss as descriptive noise.

## Wording Policy

- If the 95% CI excludes `0`, the paper can use stronger wording such as “the gain/loss is supported by paired bootstrap confidence intervals.”
- If the 95% CI overlaps `0`, the paper should use disciplined language such as “consistent in mean ranking” or “suggestive but not statistically decisive.”
- The uncertainty result should be used for every comparison that supports a headline sentence in the paper; purely descriptive table cells can remain untested.
