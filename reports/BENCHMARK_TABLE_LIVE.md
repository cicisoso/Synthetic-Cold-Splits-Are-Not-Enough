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
| `BindingDB_Ki / unseen_target` | 1/1 | `0.6574 / 0.7103` | `n/a` | `0.6295 / 0.6855` | `FTM -0.0279 / -0.0248` | assay shift is negative for target-memory |
| `DAVIS / unseen_target` | 1/1 | `0.4258 / 0.8849` | `n/a` | `0.3705 / 0.8757` | `FTM -0.0554 / -0.0092` | external dataset shift is negative for target-memory |

