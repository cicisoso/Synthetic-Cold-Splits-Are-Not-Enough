# Patent Shift Diagnosis

Generated from `BindingDB_patent / patent_temporal` result JSON files and the local patent test split.

## Global 3-Seed Summary

| System | Seeds | Test AUPRC / AUROC | Delta vs Base AUPRC / AUROC |
|--------|-------|--------------------|------------------------------|
| `base` | 3 | `0.7772 ± 0.0086 / 0.7223 ± 0.0109` | `0.0000 / 0.0000` |
| `RAICD` | 3 | `0.7692 ± 0.0018 / 0.7032 ± 0.0010` | `-0.0080 / -0.0191` |
| `FTM` | 3 | `0.7721 ± 0.0025 / 0.7059 ± 0.0037` | `-0.0050 / -0.0164` |

## Year-Band Summary

| Year | Count | Base AUPRC / AUROC | RAICD AUPRC / AUROC | FTM AUPRC / AUROC |
|------|-------|--------------------|---------------------|-------------------|
| `2019` | 42009 | `0.7626 ± 0.0098 / 0.7086 ± 0.0114` | `0.7583 ± 0.0026 / 0.6950 ± 0.0008` | `0.7624 ± 0.0024 / 0.6992 ± 0.0029` |
| `2020` | 6947 | `0.8715 ± 0.0122 / 0.8135 ± 0.0132` | `0.8395 ± 0.0021 / 0.7596 ± 0.0026` | `0.8358 ± 0.0034 / 0.7534 ± 0.0071` |
| `2021` | 72 | `0.9529 ± 0.0340 / 0.9108 ± 0.0586` | `0.9211 ± 0.0104 / 0.8444 ± 0.0245` | `0.9469 ± 0.0360 / 0.8947 ± 0.0693` |

## Overlap-Bucket Summary

| Bucket | Overlap Range | Count | Base AUPRC / AUROC | RAICD AUPRC / AUROC | FTM AUPRC / AUROC |
|--------|---------------|-------|--------------------|---------------------|-------------------|
| `0` | `0.000 - 0.531` | 16341 | `0.5551 ± 0.0190 / 0.5575 ± 0.0228` | `0.5505 ± 0.0071 / 0.5426 ± 0.0061` | `0.5537 ± 0.0063 / 0.5465 ± 0.0138` |
| `1` | `0.531 - 0.710` | 16342 | `0.7218 ± 0.0167 / 0.6580 ± 0.0194` | `0.7274 ± 0.0076 / 0.6432 ± 0.0059` | `0.7297 ± 0.0033 / 0.6471 ± 0.0074` |
| `2` | `0.710 - 0.989` | 16345 | `0.9237 ± 0.0030 / 0.8927 ± 0.0053` | `0.9085 ± 0.0090 / 0.8744 ± 0.0090` | `0.9113 ± 0.0137 / 0.8764 ± 0.0171` |

## Key Findings

1. `base` is the overall winner on patent temporal shift by 3-seed mean AUPRC (`0.7772`) over `FTM` (`0.7721`) and `RAICD` (`0.7692`).
2. `RAICD` is consistently below `base` in the global 3-seed summary and remains the clearest synthetic-vs-real ranking reversal relative to `BindingDB_Kd / blind_start`.
3. `FTM` narrows the gap relative to `RAICD`, but it still trails `base` on both overall AUPRC and AUROC under patent temporal shift.

