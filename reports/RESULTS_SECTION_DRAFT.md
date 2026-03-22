# Results Section Draft

## 4. Results

### 4.1 Synthetic cold splits are already regime-dependent

We first establish a synthetic reference panel on `BindingDB_Kd` using three standard cold-start regimes: `unseen_drug`, `blind_start`, and `unseen_target`. The key result is that even within a single dataset, model rankings are not stable across split definitions. On `unseen_drug`, the plain `base` model achieves `0.5509 ± 0.0900` AUPRC, while `RAICD` drops to `0.5228 ± 0.0828`, indicating that retrieval does not provide a reliable mean AUPRC gain in the drug-cold regime. In contrast, on `blind_start`, retrieval becomes beneficial: `RAICD` improves AUPRC from `0.3737 ± 0.0229` to `0.4024 ± 0.0508`. The target-memory probe behaves differently again. On `unseen_target`, `FTM sparse` improves over `base` from `0.5224 ± 0.0602` to `0.5439 ± 0.0791` AUPRC.

This synthetic panel already argues against treating “cold-start DTI” as a single benchmark condition. Different synthetic splits favor different inductive biases, so any claim of general cold-start superiority based on one split is structurally weak.

### 4.2 Real temporal shift reverses the retrieval conclusion

We next evaluate the same compact model panel on `BindingDB_patent / patent_temporal`, which is our primary real-OOD benchmark. Unlike the synthetic cold splits, the temporal split consistently favors the plain `base` model over both retrieval and target-memory variants. Over three seeds, `base` reaches `0.7772 ± 0.0086` AUPRC and `0.7223 ± 0.0109` AUROC. `RAICD` falls to `0.7692 ± 0.0018` AUPRC and `0.7032 ± 0.0010` AUROC, while `FTM sparse` reaches `0.7721 ± 0.0025` AUPRC and `0.7059 ± 0.0037` AUROC. Paired bootstrap confidence intervals over the mean AUPRC deltas support both losses relative to `base`: `RAICD - base = -0.0080` with 95% CI `[-0.0101, -0.0059]`, and `FTM - base = -0.0050` with 95% CI `[-0.0072, -0.0029]`.

This result is the central ranking reversal in the paper. Retrieval is the winning bias on synthetic `blind_start`, but it loses clearly on real temporal OOD. The synthetic `blind_start` gain is itself stable under paired bootstrap (`RAICD - base = +0.0288`, 95% CI `[+0.0145, +0.0431]`), which makes the reversal more consequential rather than easier to dismiss. Target-memory also fails to transfer cleanly: although it remains closer to `base` than `RAICD`, it still underperforms the plain model on both AUPRC and AUROC. The main implication is that synthetic cold splits and real temporal shifts are not interchangeable evaluation settings.

### 4.3 Temporal shift is structured across year bands and overlap levels

To understand why temporal OOD differs from synthetic cold splits, we analyze the patent benchmark by year and by overlap bucket. The year-band analysis shows that the temporal gap is not uniform. In the large 2019 slice, `base` and `FTM` are nearly tied in AUPRC (`0.7626` vs. `0.7624`), but `base` preserves a stronger AUROC (`0.7086` vs. `0.6992`). In 2020, the gap widens substantially: `base` reaches `0.8715 / 0.8135`, whereas `RAICD` drops to `0.8395 / 0.7596` and `FTM` drops to `0.8358 / 0.7534`. The tiny 2021 slice follows the same ordering but is too small to dominate the overall result.

The overlap-bucket analysis reveals a similarly non-uniform pattern. In the lowest-overlap bucket, `base` remains strongest (`0.5551 / 0.5575`), with both `RAICD` and `FTM` slightly below it. In the middle-overlap bucket, `RAICD` and `FTM` gain a small AUPRC edge over `base`, but they still remain weaker on AUROC. In the highest-overlap bucket, `base` regains a clear lead on both metrics. Together, these findings indicate that temporal shift is not simply “more cold-start.” It changes which regions of the evaluation space dominate the aggregate metric and therefore changes the model ranking.

### 4.4 Preliminary support screens are consistent with the benchmark-centric interpretation

We treat `BindingDB_Ki / unseen_target` and `DAVIS / unseen_target` as preliminary support screens rather than primary headline benchmarks. Both are informative because they test whether the synthetic `unseen_target` advantage of `FTM sparse` transfers beyond `BindingDB_Kd`. In these seed0 screens, it does not. On `BindingDB_Ki`, `FTM sparse` falls from the `base` score of `0.6574 / 0.7103` to `0.6295 / 0.6855`. On `DAVIS`, it falls from `0.4258 / 0.8849` to `0.3705 / 0.8757`.

These auxiliary negatives are consistent with the main claim of the paper, but they should not carry the same argumentative weight as the patent benchmark because they are currently seed0-only support. Their role is narrower: they show that the synthetic `unseen_target` gain of `FTM sparse` is not obviously portable across additional OOD settings. The main real-OOD evidence therefore remains the 3-seed patent benchmark.

## Placement Notes

- Main text:
  - synthetic 3-seed reference panel
  - `BindingDB_patent / patent_temporal` 3-seed panel
  - patent year-band and overlap-bucket diagnosis
- Appendix:
  - `BindingDB_Ki / unseen_target` support table
  - `DAVIS / unseen_target` support table
  - older method-centric ablations (`router`, `rftm`, selective fallback)
