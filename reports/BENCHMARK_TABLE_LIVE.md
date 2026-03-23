# Live Benchmark Table

Generated from local result JSON files.

## Synthetic Reference Panel

| Benchmark | Seeds | Base AUPRC / AUROC | RAICD AUPRC / AUROC | FTM AUPRC / AUROC | Delta vs Base | Note |
|-----------|-------|--------------------|---------------------|-------------------|---------------|------|
| `BindingDB_Kd / unseen_drug` | 3/3 | `0.5509 ± 0.0900 / 0.7794 ± 0.0534` | `0.5228 ± 0.0828 / 0.7803 ± 0.0506` | `n/a` | `RAICD -0.0281 / +0.0008` | retrieval loses on mean AUPRC |
| `BindingDB_Kd / blind_start` | 3/3 | `0.3737 ± 0.0229 / 0.6778 ± 0.0151` | `0.4024 ± 0.0508 / 0.6844 ± 0.0145` | `n/a` | `RAICD +0.0288 / +0.0066` | retrieval wins on mean AUPRC |
| `BindingDB_Kd / unseen_target` | 3/3 | `0.5224 ± 0.0602 / 0.7741 ± 0.0161` | `n/a` | `0.5439 ± 0.0791 / 0.7848 ± 0.0204` | `FTM +0.0214 / +0.0107` | target-memory wins on mean AUPRC |

## Real-OOD Screening Panel

| Benchmark | Seeds | Base AUPRC / AUROC | RAICD AUPRC / AUROC | FTM AUPRC / AUROC | Delta vs Base | Note |
|-----------|-------|--------------------|---------------------|-------------------|---------------|------|
| `BindingDB_patent / patent_temporal` | 3/3 | `0.7772 ± 0.0086 / 0.7223 ± 0.0109` | `0.7692 ± 0.0018 / 0.7032 ± 0.0010` | `0.7721 ± 0.0025 / 0.7059 ± 0.0037` | `RAICD -0.0080 / -0.0191, FTM -0.0050 / -0.0164` | temporal shift is the promoted real-OOD axis |
| `BindingDB_Ki / unseen_target` | 3/3 | `0.6934 ± 0.0257 / 0.7192 ± 0.0068` | `0.6685 ± 0.0223 / 0.6919 ± 0.0052` | `0.6760 ± 0.0333 / 0.7007 ± 0.0110` | `RAICD -0.0249 / -0.0273, FTM -0.0174 / -0.0185` | assay shift still favors `base` |
| `DAVIS / unseen_target` | 3/3 | `0.4097 ± 0.0275 / 0.8613 ± 0.0153` | `0.3839 ± 0.0134 / 0.8565 ± 0.0154` | `0.3787 ± 0.0312 / 0.8577 ± 0.0101` | `RAICD -0.0258 / -0.0048, FTM -0.0310 / -0.0036` | external dataset shift still favors `base` |

## Expanded Recent-Baseline Panel

| Benchmark | Seeds | DTI-LM AUPRC / AUROC | HyperPCM AUPRC / AUROC | Note |
|-----------|-------|----------------------|------------------------|------|
| `BindingDB_patent / patent_temporal` | `3 / 3` | `0.7825 ± 0.0078 / 0.7362 ± 0.0083` | `0.7753 ± 0.0050 / 0.7368 ± 0.0090` | `DTI-LM` remains the strongest recent baseline by mean AUPRC; `HyperPCM` is close on AUROC |
| `BindingDB_Kd / blind_start` | `3 / 3` | `0.3636 ± 0.0693 / 0.6490 ± 0.0642` | `0.3828 ± 0.1024 / 0.6807 ± 0.0824` | `HyperPCM` is highly unstable and still does not beat `RAICD` on mean AUPRC |
| `BindingDB_Kd / unseen_target` | `3 / 3` | `0.5136 ± 0.0730 / 0.7970 ± 0.0159` | `0.4955 ± 0.0793 / 0.7810 ± 0.0191` | neither recent pooled-LM baseline beats `FTM` on mean AUPRC |

## Recent-Baseline Support Screens

| Benchmark | Seeds | Base AUPRC / AUROC | DTI-LM AUPRC / AUROC | Delta vs Base | Note |
|-----------|-------|--------------------|----------------------|---------------|------|
| `BindingDB_Ki / unseen_target` | `seed0` | `0.6574 / 0.7103` | `0.6410 / 0.6946` | `-0.0165 / -0.0157` | strongest recent baseline still remains below `base` on assay-shift target-cold |
| `DAVIS / unseen_target` | `seed0` | `0.4009 / 0.8817` | `0.3478 / 0.8674` | `-0.0530 / -0.0143` | strongest recent baseline still remains below `base` on external dataset shift |

## Patent Robustness Probe

| Benchmark | Seeds | Base AUPRC / AUROC | DTI-LM AUPRC / AUROC | Delta vs Base | Note |
|-----------|-------|--------------------|----------------------|---------------|------|
| `BindingDB_patent / patent_temporal` | `3 / 3` | `0.7772 ± 0.0086 / 0.7223 ± 0.0109` | `0.7825 ± 0.0078 / 0.7362 ± 0.0083` | `+0.0054 / +0.0139` | paired bootstrap CI for AUPRC delta is `[+0.0028, +0.0079]` |
| `BindingDB_patent / patent_temporal_v2017` | `3 / 3` | `0.7044 ± 0.0058 / 0.6624 ± 0.0079` | `0.7134 ± 0.0027 / 0.6754 ± 0.0039` | `+0.0091 / +0.0131` | earlier-cutoff matched 3-seed probe preserves the same winner direction |

## Review-Driven Robustness Probes

| Benchmark | Seeds | Base AUPRC / AUROC | DTI-LM AUPRC / AUROC | HyperPCM AUPRC / AUROC | Note |
|-----------|-------|--------------------|----------------------|------------------------|------|
| `BindingDB_nonpatent_Kd / nonpatent_temporal` | `3 / 3` | `0.6369 ± 0.0173 / 0.7333 ± 0.0081` | `0.6531 ± 0.0066 / 0.7644 ± 0.0041` | `n/a` | non-patent temporal probe preserves `DTI-LM > base`, reducing the concern that patent ranking is driven only by patent provenance |
| `BindingDB_Kd / scaffold_drug` | `3 / 3` | `0.6069 ± 0.0161 / 0.8351 ± 0.0037` | `seed0: 0.5554 / 0.7784` | `0.5983 ± 0.0368 / 0.8155 ± 0.0204` | stricter scaffold holdout removes the original `HyperPCM > base` ordering seen on synthetic `unseen_drug` |
