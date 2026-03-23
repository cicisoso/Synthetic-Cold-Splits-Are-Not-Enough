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
| `BindingDB_Ki / unseen_target` | 3 | `0.6934 ± 0.0257 / 0.7192 ± 0.0068` | `0.6685 ± 0.0223 / 0.6919 ± 0.0052` | `0.6760 ± 0.0333 / 0.7007 ± 0.0110` | `RAICD: -0.0249 / -0.0273`, `FTM: -0.0174 / -0.0185` | assay shift still favors `base` over both probes |
| `DAVIS / unseen_target` | 3 | `0.4097 ± 0.0275 / 0.8613 ± 0.0153` | `0.3839 ± 0.0134 / 0.8565 ± 0.0154` | `0.3787 ± 0.0312 / 0.8577 ± 0.0101` | `RAICD: -0.0258 / -0.0048`, `FTM: -0.0310 / -0.0036` | external dataset shift still favors `base` |

### Expanded Recent-Baseline Panel

| Benchmark | Seeds | DTI-LM AUPRC / AUROC | HyperPCM AUPRC / AUROC | Primary Read |
|-----------|-------|----------------------|------------------------|--------------|
| `BindingDB_patent / patent_temporal` | `3 / 3` | `0.7825 ± 0.0078 / 0.7362 ± 0.0083` | `0.7753 ± 0.0050 / 0.7368 ± 0.0090` | `DTI-LM` remains the strongest recent baseline by mean AUPRC, while `HyperPCM` is close on AUROC |
| `BindingDB_Kd / blind_start` | `3 / 3` | `0.3636 ± 0.0693 / 0.6490 ± 0.0642` | `0.3828 ± 0.1024 / 0.6807 ± 0.0824` | `HyperPCM` has the highest mean AUPRC, but `HyperPCM - base` crosses zero under paired bootstrap, so the external panel has no reliable blind-start winner |
| `BindingDB_Kd / unseen_target` | `3 / 3` | `0.5136 ± 0.0730 / 0.7970 ± 0.0159` | `0.4955 ± 0.0793 / 0.7810 ± 0.0191` | neither recent pooled-LM baseline beats `FTM` on mean AUPRC |

### Reviewer-Proofing Additions

| Benchmark | Seeds | Base AUPRC / AUROC | DTI-LM AUPRC / AUROC | Primary Read |
|-----------|-------|--------------------|----------------------|--------------|
| `BindingDB_Ki / unseen_target` | `seed0` | `0.6574 / 0.7103` | `0.6410 / 0.6946` | strongest recent baseline still loses on assay-shift target-cold |
| `DAVIS / unseen_target` | `seed0` | `0.4009 / 0.8817` | `0.3478 / 0.8674` | strongest recent baseline still loses on external dataset shift |
| `BindingDB_patent / patent_temporal` | `3 / 3` | `0.7772 ± 0.0086 / 0.7223 ± 0.0109` | `0.7825 ± 0.0078 / 0.7362 ± 0.0083` | `DTI-LM - base` mean AUPRC delta is `+0.0054`, 95% CI `[+0.0028, +0.0079]` |
| `BindingDB_patent / patent_temporal_v2017` | `3 / 3` | `0.7044 ± 0.0058 / 0.6624 ± 0.0079` | `0.7134 ± 0.0027 / 0.6754 ± 0.0039` | earlier-cutoff matched 3-seed probe preserves `DTI-LM > base` |

## Key Findings

1. **Retrieval is split-sensitive, not uniformly robust.** `RAICD` wins on synthetic `blind_start`, loses on synthetic `unseen_drug`, and also loses on all three real-OOD panels now summarized over 3 seeds.
2. **Target-memory is not transportable as a headline method.** `FTM sparse` is positive on synthetic `BindingDB_Kd / unseen_target`, but loses on `BindingDB_Ki`, `DAVIS`, and patent temporal.
3. **`DTI-LM` remains the strongest added recent baseline on patent temporal.** Its promoted 3-seed score on `BindingDB_patent` is `0.7825 ± 0.0078 / 0.7362 ± 0.0083`, while `HyperPCM` reaches `0.7753 ± 0.0050 / 0.7368 ± 0.0090`.
4. **The strongest recent baseline still does not rescue the supporting target-cold OOD panels.** On both `BindingDB_Ki` and `DAVIS`, `DTI-LM` seed0 remains below `base`.
5. **The patent conclusion is now supported statistically and by an alternative cutoff.** `DTI-LM - base` on the main patent split has 95% paired bootstrap CI `[+0.0028, +0.0079]`, and the earlier-cutoff `patent_temporal_v2017` matched 3-seed panel also preserves the same ranking direction (`+0.0091 / +0.0131` mean delta).
6. **The synthetic and supporting panels now have uncertainty support for their headline claims as well.** `FTM - base` on synthetic `BindingDB_Kd / unseen_target` has CI `[+0.0143, +0.0286]`, while `RAICD/FTM` remain strictly below `base` on `BindingDB_Ki` and `DAVIS` under paired bootstrap.
7. **`BindingDB_patent / patent_temporal` remains the strongest main benchmark.** It carries the clearest synthetic-vs-real ranking reversal and now supports a broader recent-baseline comparison.
8. **The review-driven robustness probes strengthen both main pressure points.** `BindingDB_nonpatent_Kd / nonpatent_temporal` preserves `DTI-LM > base` over 3 seeds (`0.6531 ± 0.0066` vs. `0.6369 ± 0.0173`, paired CI `[+0.0064, +0.0265]`), while `BindingDB_Kd / scaffold_drug` eliminates support for the original synthetic `HyperPCM` edge (`HyperPCM - base` paired CI `[-0.0203, +0.0025]`).

## Suggested Next Experiments

1. Fold the completed uncertainty additions and manuscript restructuring into the next external re-review.
2. Decide whether reviewer-proofing still needs one more recent baseline family beyond `DTI-LM` and `HyperPCM`, or whether the panel is now wide enough for submission.
3. If no more baselines are added, switch effort from benchmark expansion to venue-specific manuscript tightening.

## Live Status

- Auto-generated live table: [BENCHMARK_TABLE_LIVE.md](/root/exp/dti_codex/reports/BENCHMARK_TABLE_LIVE.md)
- Patent multi-seed is complete.
- Final `BindingDB_patent / patent_temporal` 3-seed summary:
  - `base`: `0.7772 ± 0.0086 / 0.7223 ± 0.0109`
  - `RAICD`: `0.7692 ± 0.0018 / 0.7032 ± 0.0010`
  - `FTM`: `0.7721 ± 0.0025 / 0.7059 ± 0.0037`
- `DTI-LM` promoted 3-seed toplines are complete:
  - `patent_temporal`: `0.7825 ± 0.0078 / 0.7362 ± 0.0083`
  - `blind_start`: `0.3636 ± 0.0693 / 0.6490 ± 0.0642`
  - `unseen_target`: `0.5136 ± 0.0730 / 0.7970 ± 0.0159`
- `HyperPCM` promoted 3-seed toplines are complete:
  - `patent_temporal`: `0.7753 ± 0.0050 / 0.7368 ± 0.0090`
  - `blind_start`: `0.3828 ± 0.1024 / 0.6807 ± 0.0824`
  - `unseen_target`: `0.4955 ± 0.0793 / 0.7810 ± 0.0191`
- `BindingDB_Ki` and `DAVIS` support benchmarks are now matched 3-seed, not seed0-only.
- `DTI-LM` support screens are complete:
  - `BindingDB_Ki / unseen_target / seed0`: `0.6410 / 0.6946`
  - `DAVIS / unseen_target / seed0`: `0.3478 / 0.8674`
- `DTI-LM - base` paired bootstrap on patent temporal is complete:
  - mean AUPRC delta: `+0.0054`
  - 95% CI: `[+0.0028, +0.0079]`
- alternative cutoff probe is complete over matched 3-seed:
  - `BindingDB_patent / patent_temporal_v2017`
  - `base`: `0.7044 ± 0.0058 / 0.6624 ± 0.0079`
  - `DTI-LM`: `0.7134 ± 0.0027 / 0.6754 ± 0.0039`
- Patent-specific diagnosis: [PATENT_SHIFT_DIAGNOSIS.md](/root/exp/dti_codex/reports/PATENT_SHIFT_DIAGNOSIS.md)
