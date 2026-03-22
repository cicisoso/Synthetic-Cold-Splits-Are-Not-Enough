# Paper Table Drafts

## Main Table 1: Synthetic vs Real-OOD Benchmark Summary

### Caption Draft

Synthetic cold splits and real distribution shifts yield different model rankings. `RAICD` helps on `BindingDB_Kd / blind_start` but loses on `BindingDB_patent / patent_temporal`, while `FTM sparse` helps on synthetic `unseen_target` but fails to transfer consistently to real-OOD settings.

### LaTeX-Friendly Table Content

| Benchmark | Seeds | Base AUPRC / AUROC | RAICD AUPRC / AUROC | FTM AUPRC / AUROC | Winner by AUPRC |
|-----------|-------|--------------------|---------------------|-------------------|-----------------|
| `BindingDB_Kd / unseen_drug` | 3 | `0.5509 ± 0.0900 / 0.7794 ± 0.0534` | `0.5228 ± 0.0828 / 0.7803 ± 0.0506` | `n/a` | `base` |
| `BindingDB_Kd / blind_start` | 3 | `0.3737 ± 0.0229 / 0.6778 ± 0.0151` | `0.4024 ± 0.0508 / 0.6844 ± 0.0145` | `n/a` | `RAICD` |
| `BindingDB_Kd / unseen_target` | 3 | `0.5224 ± 0.0602 / 0.7741 ± 0.0161` | `n/a` | `0.5439 ± 0.0791 / 0.7848 ± 0.0204` | `FTM` |
| `BindingDB_patent / patent_temporal` | 3 | `0.7772 ± 0.0086 / 0.7223 ± 0.0109` | `0.7692 ± 0.0018 / 0.7032 ± 0.0010` | `0.7721 ± 0.0025 / 0.7059 ± 0.0037` | `base` |

### Text Draft

The synthetic reference panel already shows that cold-start DTI is regime-dependent: retrieval helps on `blind_start` but not on `unseen_drug`, while target-memory helps on synthetic `unseen_target`. However, this ranking does not transfer to real-OOD settings. On the promoted temporal benchmark `BindingDB_patent / patent_temporal`, `base` is the best model over 3 seeds, outperforming `RAICD` by `0.0080` AUPRC and `0.0191` AUROC and outperforming `FTM` by `0.0050` AUPRC and `0.0164` AUROC.

Paired bootstrap confidence intervals strengthen this comparison. On synthetic `blind_start`, the `RAICD - base` AUPRC delta is `+0.0288` with 95% CI `[+0.0145, +0.0431]`. On patent temporal, the `RAICD - base` delta is `-0.0080` with 95% CI `[-0.0101, -0.0059]`, and the `FTM - base` delta is `-0.0050` with 95% CI `[-0.0072, -0.0029]`.

### Main-Text Placement Decision

Keep `BindingDB_patent / patent_temporal` in the main table and move `BindingDB_Ki` and `DAVIS` to appendix support. The reason is evidential strength rather than convenience:

- `BindingDB_patent` has a matched 3-seed panel for `base / RAICD / FTM`
- it is the cleanest synthetic-vs-real ranking reversal
- `BindingDB_Ki` and `DAVIS` are useful negative-transfer support, but they are currently seed-0 only and do not carry the full three-model evidence chain

## Appendix Table A1: Additional Real-OOD Support Benchmarks

### Caption Draft

Preliminary real-OOD support screens are consistent with the main temporal benchmark conclusion. Both assay-shifted BindingDB and the external DAVIS benchmark suggest that the target-memory gain observed on synthetic `BindingDB_Kd / unseen_target` does not transfer reliably.

### Table Content

| Benchmark | Seeds | Base AUPRC / AUROC | FTM AUPRC / AUROC | Delta vs Base |
|-----------|-------|--------------------|-------------------|---------------|
| `BindingDB_Ki / unseen_target` | 1 | `0.6574 / 0.7103` | `0.6295 / 0.6855` | `-0.0279 / -0.0248` |
| `DAVIS / unseen_target` | 1 | `0.4258 / 0.8849` | `0.3705 / 0.8757` | `-0.0553 / -0.0092` |

### Text Draft

These auxiliary benchmarks are consistent with the benchmark-centric interpretation, but they should remain secondary because they are currently seed0-only support. Even though `FTM sparse` improves synthetic `BindingDB_Kd / unseen_target`, it loses on both `BindingDB_Ki` and `DAVIS`, suggesting that the apparent gain is not robust to assay or dataset shift. This keeps `BindingDB_patent` as the main real-OOD benchmark and positions `BindingDB_Ki` and `DAVIS` as supporting counterexamples rather than co-equal headline benchmarks.

## Figure 2 Draft: Patent Shift Diagnosis

### Caption Draft

Patent temporal shift stresses models differently across year bands and overlap buckets. The strongest degradation appears in the 2020 slice and in the highest-overlap bucket, where `base` remains the most reliable model. `RAICD` is consistently below `base`, while `FTM` partially narrows the gap but does not recover the synthetic `unseen_target` advantage.

### Table Proxy for Figure Data

#### Year Bands

| Year | Count | Base AUPRC / AUROC | RAICD AUPRC / AUROC | FTM AUPRC / AUROC |
|------|-------|--------------------|---------------------|-------------------|
| `2019` | 42009 | `0.7626 ± 0.0098 / 0.7086 ± 0.0114` | `0.7583 ± 0.0026 / 0.6950 ± 0.0008` | `0.7624 ± 0.0024 / 0.6992 ± 0.0029` |
| `2020` | 6947 | `0.8715 ± 0.0122 / 0.8135 ± 0.0132` | `0.8395 ± 0.0021 / 0.7596 ± 0.0026` | `0.8358 ± 0.0034 / 0.7534 ± 0.0071` |
| `2021` | 72 | `0.9529 ± 0.0340 / 0.9108 ± 0.0586` | `0.9211 ± 0.0104 / 0.8444 ± 0.0245` | `0.9469 ± 0.0360 / 0.8947 ± 0.0693` |

#### Overlap Buckets

| Bucket | Overlap Range | Count | Base AUPRC / AUROC | RAICD AUPRC / AUROC | FTM AUPRC / AUROC |
|--------|---------------|-------|--------------------|---------------------|-------------------|
| `0` | `0.000 - 0.531` | 16341 | `0.5551 ± 0.0190 / 0.5575 ± 0.0228` | `0.5505 ± 0.0071 / 0.5426 ± 0.0061` | `0.5537 ± 0.0063 / 0.5465 ± 0.0138` |
| `1` | `0.531 - 0.710` | 16342 | `0.7218 ± 0.0167 / 0.6580 ± 0.0194` | `0.7274 ± 0.0076 / 0.6432 ± 0.0059` | `0.7297 ± 0.0033 / 0.6471 ± 0.0074` |
| `2` | `0.710 - 0.989` | 16345 | `0.9237 ± 0.0030 / 0.8927 ± 0.0053` | `0.9085 ± 0.0090 / 0.8744 ± 0.0090` | `0.9113 ± 0.0137 / 0.8764 ± 0.0171` |

### Text Draft

The patent diagnosis shows that the real-OOD gap is not uniform. In the largest 2019 slice, `base` and `FTM` are close in AUPRC, but `base` retains a clearer AUROC advantage. In 2020, which contains a smaller but still substantial test subset, both `RAICD` and `FTM` degrade sharply relative to `base`. By overlap bucket, `base` dominates the lowest- and highest-overlap regimes, while `RAICD` and `FTM` slightly improve mid-overlap AUPRC but still remain weaker on AUROC. This pattern supports a benchmark paper narrative centered on shift-axis sensitivity rather than on one universally superior method.
