# Uncertainty Support

This note reports paired bootstrap confidence intervals for the key ranking reversals highlighted in the paper:

1. `BindingDB_Kd / blind_start`: `RAICD` vs `base`
2. `BindingDB_patent / patent_temporal`: `RAICD` vs `base`
3. `BindingDB_patent / patent_temporal`: `FTM` vs `base`

The intended use is limited and reviewer-facing:

- support the wording of the main comparative claims
- show whether the direction of the mean AUPRC delta is stable under paired resampling
- avoid stronger wording than the evidence allows

## Reporting Template

| Comparison | Mean AUPRC delta | 95% paired bootstrap CI | Interpretation |
|-----------|-------------------|-------------------------|----------------|
| `blind_start`: `RAICD - base` | `+0.0288` | `[+0.0145, +0.0431]` | positive delta is stable under paired resampling |
| `patent`: `RAICD - base` | `-0.0080` | `[-0.0101, -0.0059]` | temporal real-OOD loss for retrieval is supported |
| `patent`: `FTM - base` | `-0.0050` | `[-0.0072, -0.0029]` | temporal real-OOD loss for target-memory is supported |

## Source

- JSON output: [bootstrap_pairwise_ci.json](/root/exp/dti_codex/reports/bootstrap_pairwise_ci.json)
- Script: [bootstrap_pairwise_ci.py](/root/exp/dti_codex/scripts/bootstrap_pairwise_ci.py)

## Interpretation Summary

- The synthetic `blind_start` gain of `RAICD` over `base` is not just a seed-mean artifact; the paired bootstrap CI remains strictly positive.
- On the promoted `BindingDB_patent / patent_temporal` benchmark, both `RAICD` and `FTM` remain below `base`, and both paired bootstrap CIs remain strictly negative.
- This uncertainty support strengthens the paper's core ranking-reversal claim and allows stronger wording than “suggestive” for the patent comparisons.

## Wording Policy

- If the 95% CI excludes `0`, the paper can use stronger wording such as “the gain/loss is supported by paired bootstrap confidence intervals.”
- If the 95% CI overlaps `0`, the paper should use disciplined language such as “consistent in mean ranking” or “suggestive but not statistically decisive.”
- The uncertainty result should be used only for the main ranking-reversal comparisons, not every table entry.
