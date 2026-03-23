# Patent Shift Diagnosis (External Panel)

Generated from `BindingDB_patent / patent_temporal` result JSON files and the local patent test split.

## Global 3-Seed Summary

| System | Seeds | Test AUPRC / AUROC | Delta vs Base AUPRC / AUROC |
|--------|-------|--------------------|------------------------------|
| `base` | 3 | `0.7772 ± 0.0086 / 0.7223 ± 0.0109` | `0.0000 / 0.0000` |
| `DTI-LM` | 3 | `0.7825 ± 0.0078 / 0.7362 ± 0.0083` | `+0.0054 / +0.0139` |
| `HyperPCM` | 3 | `0.7753 ± 0.0050 / 0.7368 ± 0.0090` | `-0.0019 / +0.0145` |

## Year-Band Summary

| Year | Count | base AUPRC / AUROC | DTI-LM AUPRC / AUROC | HyperPCM AUPRC / AUROC |
|------|-------|--------------------|--------------------|--------------------|
| `2019` | 42009 | `0.7626 ± 0.0098 / 0.7086 ± 0.0114` | `0.7734 ± 0.0071 / 0.7303 ± 0.0065` | `0.7637 ± 0.0049 / 0.7301 ± 0.0079` |
| `2020` | 6947 | `0.8715 ± 0.0122 / 0.8135 ± 0.0132` | `0.8545 ± 0.0100 / 0.7951 ± 0.0167` | `0.8526 ± 0.0139 / 0.7938 ± 0.0208` |
| `2021` | 72 | `0.9529 ± 0.0340 / 0.9108 ± 0.0586` | `0.7511 ± 0.0485 / 0.6971 ± 0.0781` | `0.6953 ± 0.0151 / 0.6041 ± 0.0181` |

## Overlap-Bucket Summary

| Bucket | Overlap Range | Count | base AUPRC / AUROC | DTI-LM AUPRC / AUROC | HyperPCM AUPRC / AUROC |
|--------|---------------|-------|--------------------|--------------------|--------------------|
| `0` | `0.000 - 0.531` | 16341 | `0.5551 ± 0.0190 / 0.5575 ± 0.0228` | `0.6353 ± 0.0175 / 0.6388 ± 0.0169` | `0.6147 ± 0.0208 / 0.6304 ± 0.0223` |
| `1` | `0.531 - 0.710` | 16342 | `0.7218 ± 0.0167 / 0.6580 ± 0.0194` | `0.7489 ± 0.0094 / 0.6905 ± 0.0117` | `0.7513 ± 0.0060 / 0.7072 ± 0.0076` |
| `2` | `0.710 - 0.989` | 16345 | `0.9237 ± 0.0030 / 0.8927 ± 0.0053` | `0.8866 ± 0.0097 / 0.8452 ± 0.0099` | `0.8767 ± 0.0042 / 0.8387 ± 0.0046` |

## Key Findings

1. `DTI-LM` is the overall winner on patent temporal shift by 3-seed mean AUPRC (`0.7825`).
2. `base` reaches `0.7772` mean AUPRC and is ranked `DTI-LM` (0.7825), `HyperPCM` (0.7753).
3. The year-band and overlap-bucket views remain non-uniform, so aggregate temporal OOD cannot be reduced to a single scalar difficulty even within the patent shift diagnosis (external panel).

