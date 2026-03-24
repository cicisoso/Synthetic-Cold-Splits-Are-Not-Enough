# Expanded External Panel

Generated from local result JSON files for `base`, `RF`, `DTI-LM`, `HyperPCM`, and the promoted `GraphDTA-style` graph-family probe.

## Synthetic Reference Panel

| Benchmark | Seeds | Base AUPRC / AUROC | RF AUPRC / AUROC | DTI-LM AUPRC / AUROC | HyperPCM AUPRC / AUROC | Winner |
|-----------|-------|--------------------|------------------|----------------------|-------------------------|--------|
| `BindingDB_Kd / unseen_drug` | 3/3 | `0.5509 ± 0.0900 / 0.7794 ± 0.0534` | `0.7339 ± 0.0051 / 0.8854 ± 0.0088` | `0.5004 ± 0.0341 / 0.7364 ± 0.0122` | `0.5694 ± 0.0473 / 0.7778 ± 0.0448` | `RF` |
| `BindingDB_Kd / blind_start` | 3/3 | `0.3737 ± 0.0229 / 0.6778 ± 0.0151` | `0.4512 ± 0.0373 / 0.7451 ± 0.0260` | `0.3636 ± 0.0693 / 0.6490 ± 0.0642` | `0.3828 ± 0.1024 / 0.6807 ± 0.0824` | `RF` |
| `BindingDB_Kd / unseen_target` | 3/3 | `0.5224 ± 0.0602 / 0.7741 ± 0.0161` | `0.5183 ± 0.0612 / 0.7838 ± 0.0218` | `0.5136 ± 0.0730 / 0.7970 ± 0.0159` | `0.4955 ± 0.0793 / 0.7810 ± 0.0191` | `base` |

## Primary Real-OOD Benchmarks

| Benchmark | Seeds | Base AUPRC / AUROC | RF AUPRC / AUROC | DTI-LM AUPRC / AUROC | HyperPCM AUPRC / AUROC | Winner |
|-----------|-------|--------------------|------------------|----------------------|-------------------------|--------|
| `BindingDB_patent / patent_temporal` | 3/3 | `0.7772 ± 0.0086 / 0.7223 ± 0.0109` | `0.8234 ± 0.0012 / 0.7773 ± 0.0017` | `0.7825 ± 0.0078 / 0.7362 ± 0.0083` | `0.7753 ± 0.0050 / 0.7368 ± 0.0090` | `RF` |
| `BindingDB_nonpatent_Kd / nonpatent_temporal` | 3/3 | `0.6369 ± 0.0173 / 0.7333 ± 0.0081` | `0.7201 ± 0.0012 / 0.7627 ± 0.0020` | `0.6531 ± 0.0066 / 0.7644 ± 0.0041` | `-` | `RF` |

## Supporting Real-OOD Benchmarks

| Benchmark | Seeds | Base AUPRC / AUROC | RF AUPRC / AUROC | DTI-LM AUPRC / AUROC | HyperPCM AUPRC / AUROC | GraphDTA-style AUPRC / AUROC | Winner |
|-----------|-------|--------------------|------------------|----------------------|-------------------------|-------------------------------|--------|
| `BindingDB_Ki / unseen_target` | 3/3 | `0.6934 ± 0.0257 / 0.7192 ± 0.0068` | `0.6328 ± 0.0465 / 0.6581 ± 0.0319` | `0.6648 ± 0.0177 / 0.6936 ± 0.0044` | `0.6515 ± 0.0301 / 0.6757 ± 0.0211` | `0.6280 ± 0.0237 / 0.6550 ± 0.0193` | `base` |
| `DAVIS / unseen_target` | 3/3 | `0.4097 ± 0.0275 / 0.8613 ± 0.0153` | `0.4408 ± 0.0325 / 0.8806 ± 0.0128` | `0.4090 ± 0.0570 / 0.8718 ± 0.0152` | `0.3840 ± 0.0269 / 0.8610 ± 0.0245` | `0.3601 ± 0.0502 / 0.8359 ± 0.0292` | `RF` |

## Graph-Family Probe

The graph-family probe does not overturn the primary synthetic or temporal panels, but it is now also completed on the two support benchmarks. This closes the main reviewer concern that the support OOD benchmarks lacked a matched five-model comparison panel.

| Benchmark | Seeds | GraphDTA-style AUPRC / AUROC | Read |
|-----------|-------|-------------------------------|------|
| `BindingDB_Kd / unseen_drug` | 3/3 | `0.5626 ± 0.0172 / 0.7988 ± 0.0129` | competitive, but below `RF` |
| `BindingDB_Kd / unseen_target` | 3/3 | `0.4722 ± 0.0925 / 0.7637 ± 0.0314` | unstable target-cold behavior |
| `BindingDB_patent / patent_temporal` | 3/3 | `0.7726 ± 0.0016 / 0.7232 ± 0.0007` | below `RF` and `DTI-LM` |
| `BindingDB_nonpatent_Kd / nonpatent_temporal` | 3/3 | `0.6635 ± 0.0142 / 0.7334 ± 0.0096` | above `base`, below `RF` |
| `BindingDB_Ki / unseen_target` | 3/3 | `0.6280 ± 0.0237 / 0.6550 ± 0.0193` | below `base` and `DTI-LM` |
| `DAVIS / unseen_target` | 3/3 | `0.3601 ± 0.0502 / 0.8359 ± 0.0292` | below `RF`, `base`, and `DTI-LM` |
