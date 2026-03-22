# Benchmark Screening Summary

## Raw Data Table

### Synthetic Reference Panel

| Benchmark | Seeds | Base AUPRC / AUROC | RAICD AUPRC / AUROC | FTM AUPRC / AUROC | Primary Read |
|-----------|-------|--------------------|---------------------|-------------------|--------------|
| `BindingDB_Kd / unseen_drug` | 3 | `0.5509 ± 0.0900 / 0.7794 ± 0.0534` | `0.5228 ± 0.0828 / 0.7803 ± 0.0506` | `n/a` | retrieval loses on mean AUPRC |
| `BindingDB_Kd / blind_start` | 3 | `0.3737 ± 0.0229 / 0.6778 ± 0.0151` | `0.4024 ± 0.0508 / 0.6844 ± 0.0145` | `n/a` | retrieval wins on mean AUPRC |
| `BindingDB_Kd / unseen_target` | 3 | `0.5224 ± 0.0602 / 0.7741 ± 0.0161` | `n/a` | `0.5439 ± 0.0791 / 0.7848 ± 0.0204` | target-memory wins on mean AUPRC |

### Real-OOD Screening Panel

| Benchmark | Seeds | Base AUPRC / AUROC | RAICD AUPRC / AUROC | FTM AUPRC / AUROC | Delta vs Base | Primary Read |
|-----------|-------|--------------------|---------------------|-------------------|---------------|--------------|
| `BindingDB_patent / patent_temporal` | 3 | `0.7772 ± 0.0086 / 0.7223 ± 0.0109` | `0.7692 ± 0.0018 / 0.7032 ± 0.0010` | `0.7721 ± 0.0025 / 0.7059 ± 0.0037` | `RAICD: -0.0080 / -0.0191`, `FTM: -0.0050 / -0.0164` | real temporal shift rejects retrieval and still favors `base` |
| `BindingDB_Ki / unseen_target` | 1 | `0.6574 / 0.7103` | `n/a` | `0.6295 / 0.6855` | `FTM: -0.0279 / -0.0248` | assay shift is negative for target-memory |
| `DAVIS / unseen_target` | 1 | `0.4258 / 0.8849` | `n/a` | `0.3705 / 0.8757` | `FTM: -0.0553 / -0.0092` | external dataset shift is negative for target-memory |

## Key Findings

1. **Retrieval is split-sensitive, not uniformly robust.** `RAICD` wins on synthetic `blind_start`, loses on synthetic `unseen_drug`, and also loses on real temporal OOD `BindingDB_patent`.
2. **Target-memory is not transportable as a paper headline method.** `FTM sparse` is positive on synthetic `BindingDB_Kd / unseen_target`, but negative on `BindingDB_Ki` and `DAVIS`, and only mixed on patent temporal.
3. **`BindingDB_patent / patent_temporal` is the strongest real-OOD benchmark to promote.** It already contains the full `base / RAICD / FTM` panel and shows the cleanest synthetic-vs-real ranking disagreement.

## Suggested Next Experiments

1. Turn [BENCHMARK_TABLE_LIVE.md](/root/exp/dti_codex/reports/BENCHMARK_TABLE_LIVE.md) and [PATENT_SHIFT_DIAGNOSIS.md](/root/exp/dti_codex/reports/PATENT_SHIFT_DIAGNOSIS.md) into the main paper's benchmark table and diagnosis figure captions.
2. Decide whether `BindingDB_Ki` stays in the main text as assay-shift support or moves to the appendix.
3. Extend bucket-level aggregation to one more completed benchmark only if reviewer-proofing needs an additional counterexample beyond patent.

## Live Status

- Auto-generated live table: [BENCHMARK_TABLE_LIVE.md](/root/exp/dti_codex/reports/BENCHMARK_TABLE_LIVE.md)
- Patent multi-seed is complete.
- Final `BindingDB_patent / patent_temporal` 3-seed summary:
  - `base`: `0.7772 ± 0.0086 / 0.7223 ± 0.0109`
  - `RAICD`: `0.7692 ± 0.0018 / 0.7032 ± 0.0010`
  - `FTM`: `0.7721 ± 0.0025 / 0.7059 ± 0.0037`
- Patent-specific diagnosis: [PATENT_SHIFT_DIAGNOSIS.md](/root/exp/dti_codex/reports/PATENT_SHIFT_DIAGNOSIS.md)
