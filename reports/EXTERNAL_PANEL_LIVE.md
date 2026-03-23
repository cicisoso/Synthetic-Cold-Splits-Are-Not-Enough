# External Replacement Panel

Generated from local result JSON files for `base`, `DTI-LM`, and `HyperPCM`.

## Synthetic Reference Panel

| Benchmark | Seeds | Base AUPRC / AUROC | DTI-LM AUPRC / AUROC | HyperPCM AUPRC / AUROC | Delta vs Base | Winner |
|-----------|-------|--------------------|----------------------|-------------------------|---------------|--------|
| `BindingDB_Kd / unseen_drug` | 3/3 | `0.5509 ± 0.0900 / 0.7794 ± 0.0534` | `0.5004 ± 0.0341 / 0.7364 ± 0.0122` | `0.5694 ± 0.0473 / 0.7778 ± 0.0448` | `DTI-LM -0.0505 / -0.0431, HyperPCM +0.0185 / -0.0017` | `HyperPCM` |
| `BindingDB_Kd / blind_start` | 3/3 | `0.3737 ± 0.0229 / 0.6778 ± 0.0151` | `0.3636 ± 0.0693 / 0.6490 ± 0.0642` | `0.3828 ± 0.1024 / 0.6807 ± 0.0824` | `DTI-LM -0.0100 / -0.0288, HyperPCM +0.0092 / +0.0029; CI crosses 0` | `none` |
| `BindingDB_Kd / unseen_target` | 3/3 | `0.5224 ± 0.0602 / 0.7741 ± 0.0161` | `0.5136 ± 0.0730 / 0.7970 ± 0.0159` | `0.4955 ± 0.0793 / 0.7810 ± 0.0191` | `DTI-LM -0.0088 / +0.0229, HyperPCM -0.0269 / +0.0069` | `base` |

## Primary Real-OOD Benchmark

| Benchmark | Seeds | Base AUPRC / AUROC | DTI-LM AUPRC / AUROC | HyperPCM AUPRC / AUROC | Delta vs Base | Winner |
|-----------|-------|--------------------|----------------------|-------------------------|---------------|--------|
| `BindingDB_patent / patent_temporal` | 3/3 | `0.7772 ± 0.0086 / 0.7223 ± 0.0109` | `0.7825 ± 0.0078 / 0.7362 ± 0.0083` | `0.7753 ± 0.0050 / 0.7368 ± 0.0090` | `DTI-LM +0.0054 / +0.0139, HyperPCM -0.0019 / +0.0145` | `DTI-LM` |

## Supporting Real-OOD Benchmarks

| Benchmark | Seeds | Base AUPRC / AUROC | DTI-LM AUPRC / AUROC | HyperPCM AUPRC / AUROC | Delta vs Base | Winner |
|-----------|-------|--------------------|----------------------|-------------------------|---------------|--------|
| `BindingDB_Ki / unseen_target` | 3/3 | `0.6934 ± 0.0257 / 0.7192 ± 0.0068` | `0.6648 ± 0.0177 / 0.6936 ± 0.0044` | `0.6515 ± 0.0301 / 0.6757 ± 0.0211` | `DTI-LM -0.0286 / -0.0256, HyperPCM -0.0419 / -0.0435` | `base` |
| `DAVIS / unseen_target` | 3/3 | `0.4097 ± 0.0275 / 0.8613 ± 0.0153` | `0.4090 ± 0.0570 / 0.8718 ± 0.0152` | `0.3840 ± 0.0269 / 0.8610 ± 0.0245` | `DTI-LM -0.0007 / +0.0105, HyperPCM -0.0258 / -0.0003` | `base` |
