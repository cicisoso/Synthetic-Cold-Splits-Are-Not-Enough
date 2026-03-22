# Manuscript First Draft

## Title

Synthetic Cold Splits Are Not Enough: Distribution-Shift Benchmarking for Drug-Target Interaction Prediction

## Abstract

Drug-target interaction (DTI) papers often use synthetic cold-start splits as proxies for generalization, but it is unclear whether conclusions drawn from these splits transfer to real distribution shifts. We present a benchmark-first study showing that model rankings in DTI are highly sensitive to how the shift is defined. Using a compact model panel consisting of a plain base encoder, a retrieval-augmented model (`RAICD`), and a functional target-memory variant (`FTM sparse`), we first build a 3-seed synthetic reference panel on `BindingDB_Kd`. Even within this single dataset, rankings are unstable: `RAICD` improves over `base` on `blind_start`, loses on `unseen_drug`, and `FTM sparse` is strongest on synthetic `unseen_target`. We then evaluate the same panel on a real temporal benchmark, `BindingDB_patent / patent_temporal`, where the ranking reverses. Over 3 seeds, the plain `base` model achieves `0.7772 ± 0.0086` AUPRC, outperforming both `RAICD` (`0.7692 ± 0.0018`) and `FTM sparse` (`0.7721 ± 0.0025`). A year-band and overlap-bucket diagnosis further shows that temporal OOD is structured rather than monolithic. Additional support from `BindingDB_Ki` and `DAVIS` indicates that synthetic `unseen_target` gains are not reliably portable. These results suggest that synthetic cold splits and real OOD shifts are not interchangeable evaluation settings for DTI, and that future work should report both.

## 1 Introduction

Predicting drug-target interactions for unseen molecules or proteins is a central goal in computational drug discovery. Because truly prospective evaluation is difficult and expensive, many studies rely on synthetic cold-start splits, such as holding out drugs, targets, or both, to estimate generalization performance. These protocols are useful, but they also encourage a strong implicit assumption: if a method performs well on one cold-start split, then it is broadly robust to the kinds of distribution shift encountered in realistic deployment.

That assumption is weaker than it appears. Different split definitions remove different forms of overlap, and they may favor different inductive biases. A retrieval mechanism may be useful when support examples remain structurally informative, but much less useful when the benchmark shift is temporal, assay-dependent, or otherwise changes the data distribution in ways that are not captured by synthetic exclusion rules. Likewise, a target-memory mechanism may appear beneficial on one synthetic regime while failing to transfer across datasets or assay families. If these ranking changes occur in practice, then benchmark design is not a technical footnote. It becomes part of the scientific claim.

This paper studies that question directly. Rather than proposing a new universal architecture, we ask whether the ranking of a compact DTI model panel is preserved across synthetic cold-start regimes and real distribution shifts. Our starting point is a synthetic reference panel on `BindingDB_Kd`, where we compare three representative systems: a plain base encoder, a retrieval-augmented model (`RAICD`), and a functional target-memory model (`FTM sparse`). Even here, rankings are already heterogeneous: `RAICD` improves on `blind_start`, loses on `unseen_drug`, and `FTM sparse` is strongest on synthetic `unseen_target`.

We then contrast this synthetic picture with a real temporal benchmark, `BindingDB_patent / patent_temporal`, using matched 3-seed evaluation. The result is a clear ranking reversal. On synthetic `blind_start`, retrieval is beneficial; on patent temporal shift, the plain `base` model is best, outperforming both `RAICD` and `FTM sparse`. Paired bootstrap confidence intervals support both parts of this contrast: the synthetic `blind_start` AUPRC delta for `RAICD - base` remains positive, while the patent-temporal deltas for both `RAICD - base` and `FTM - base` remain negative. This reversal is the central result of the paper, because it shows that synthetic cold-start conclusions do not automatically transfer to real OOD settings.

To move beyond leaderboard-style reporting, we also diagnose the promoted temporal benchmark by year and overlap bucket. This analysis shows that temporal OOD is not simply “harder cold-start.” Instead, the gap is concentrated in specific year bands and overlap regimes, which helps explain why a method that looks strong under one split can lose under another. We further include `BindingDB_Ki` and `DAVIS` as supporting real-OOD screens, showing that the synthetic `unseen_target` advantage of `FTM sparse` does not transfer reliably outside the original benchmark.

Our contributions are fourfold. First, we construct a 3-seed synthetic reference panel showing that even standard cold-start evaluation is regime-dependent. Second, we establish a 3-seed temporal benchmark on `BindingDB_patent` and show a ranking reversal relative to the synthetic `blind_start` regime. Third, we provide year-band and overlap-bucket analyses that connect the ranking change to measurable shift axes. Fourth, we show through supporting benchmarks that method gains observed on synthetic `unseen_target` are not robust enough to serve as a universal claim. The main conclusion is straightforward: synthetic cold splits and real OOD shifts are not interchangeable, and DTI evaluation should report both.

## 2 Related Work

The first line of related work concerns cold-start evaluation in DTI and drug-target affinity prediction. Many methods report results on random or cold splits in BindingDB, DAVIS, and related datasets, using held-out drugs, held-out targets, or both as proxies for inductive generalization. This literature has established cold-start evaluation as standard practice, but it often treats different split definitions as variations of the same problem. Our results suggest that this assumption is too coarse, because different synthetic regimes already lead to different model rankings.

The second line of work develops inductive, retrieval-based, or memory-based architectures for DTI. These approaches are motivated by the need to transfer information from seen entities to unseen drugs or targets, and they often report gains on one or two benchmark settings. Our work does not dispute that these mechanisms can help under some conditions. In fact, we reproduce such behavior on synthetic `blind_start` and synthetic `unseen_target`. Instead, we show that these gains are benchmark-sensitive and therefore should be interpreted as regime-specific rather than universal.

The third line of work studies distribution shift and benchmark design in molecular machine learning more broadly. Recent benchmark papers in related domains have shown that model rankings can change when evaluation moves from random splits to scaffold splits, temporal splits, or domain-shifted benchmarks. Our paper brings that diagnostic perspective into DTI. The key distinction is that we keep the model panel intentionally compact. This is not a leaderboard paper with many baselines; it is a benchmark paper whose main result is that the benchmark itself changes the conclusion.

## 3 Benchmark Setup

Our goal is to test whether a compact DTI model panel preserves its ranking across synthetic cold-start regimes and real distribution shifts. The panel contains three models: `base`, a plain encoder that serves as the reference system; `RAICD`, a retrieval-augmented model that aggregates support from similar seen entities; and `FTM sparse`, a functional target-memory model designed to improve target-cold generalization. We intentionally keep the panel small so that benchmark effects are not obscured by a large architecture zoo.

We evaluate this panel on two groups of benchmarks. The first group is a synthetic reference panel based on `BindingDB_Kd`, with three split definitions: `unseen_drug`, `blind_start`, and `unseen_target`. These represent the synthetic cold-start protocols that are commonly used in the literature. The second group is a real-OOD screening panel. Our primary real-OOD benchmark is `BindingDB_patent / patent_temporal`, which uses a year-based temporal split and is evaluated over three seeds. We also include `BindingDB_Ki / unseen_target` and `DAVIS / unseen_target` as supporting screens that test whether the synthetic `unseen_target` gain of `FTM sparse` transfers across assay and dataset shifts.

We report area under the precision-recall curve (AUPRC) as the primary metric and area under the ROC curve (AUROC) as a secondary metric. AUPRC is emphasized because the class balance and ranking behavior are central to the benchmark claims in this paper. For the synthetic reference panel and the promoted patent benchmark, we report matched three-seed results. For `BindingDB_Ki` and `DAVIS`, we report seed0 support only and treat these as supporting, not headline, evidence.

The patent benchmark requires several setup choices that are documented explicitly. We use a local year-based split of `BindingDB_patent`, with train years before the validation year, a held-out validation year, and a later temporal test set. We also use a patent-specific affinity conversion rather than reusing the standard `pKd` transform, because the patent benchmark stores affinities in a different log-scale convention. Finally, for diagnostic analysis, we use the saved overlap score from each test prediction to compute overlap buckets that summarize how strongly each test example resembles the training support.

## 4 Results

### 4.1 Synthetic cold splits are already regime-dependent

We begin with the `BindingDB_Kd` synthetic reference panel. The main result is that even within a single dataset, model rankings are not stable across split definitions. On `unseen_drug`, the plain `base` model achieves `0.5509 ± 0.0900` AUPRC, while `RAICD` drops to `0.5228 ± 0.0828`, showing that retrieval does not provide a reliable mean AUPRC gain in the drug-cold regime. On `blind_start`, however, the pattern reverses: `RAICD` improves over `base` from `0.3737 ± 0.0229` to `0.4024 ± 0.0508` AUPRC. On `unseen_target`, `FTM sparse` becomes the strongest model, improving AUPRC from `0.5224 ± 0.0602` to `0.5439 ± 0.0791`.

These results matter because they show that “synthetic cold-start DTI” is already not a single evaluation condition. Different synthetic regimes reward different modeling choices, so it is unsafe to generalize from one split to another without explicit evidence.

### 4.2 Real temporal shift reverses the retrieval conclusion

We next evaluate the same panel on `BindingDB_patent / patent_temporal`, our primary real-OOD benchmark. Over three seeds, the plain `base` model reaches `0.7772 ± 0.0086` AUPRC and `0.7223 ± 0.0109` AUROC. `RAICD` falls to `0.7692 ± 0.0018` AUPRC and `0.7032 ± 0.0010` AUROC, while `FTM sparse` reaches `0.7721 ± 0.0025` AUPRC and `0.7059 ± 0.0037` AUROC. Paired bootstrap intervals over the mean AUPRC deltas support both losses relative to `base`: `RAICD - base = -0.0080` with 95% CI `[-0.0101, -0.0059]`, and `FTM - base = -0.0050` with 95% CI `[-0.0072, -0.0029]`.

This is the central ranking reversal in the paper. Retrieval is the winning inductive bias on synthetic `blind_start`, but it loses clearly on real temporal OOD. `FTM sparse` narrows the gap relative to `RAICD`, but it also remains below the plain `base` model. The implication is direct: synthetic cold splits and real temporal shifts are not interchangeable settings for model comparison.

### 4.3 Temporal shift is structured across year bands and overlap levels

To explain why the temporal benchmark changes the ranking, we analyze the patent results by year and by overlap bucket. The year-band analysis shows that the temporal gap is uneven. In the large 2019 slice, `base` and `FTM` are nearly tied in AUPRC (`0.7626` vs. `0.7624`), but `base` maintains a clearer AUROC advantage (`0.7086` vs. `0.6992`). In 2020, the gap becomes much larger: `base` reaches `0.8715 / 0.8135`, while `RAICD` and `FTM` drop to `0.8395 / 0.7596` and `0.8358 / 0.7534`, respectively. The 2021 slice is small, but follows the same ordering.

The overlap-bucket analysis reveals another useful pattern. In the lowest-overlap bucket, `base` is the strongest model and both `RAICD` and `FTM` remain slightly weaker. In the middle-overlap bucket, `RAICD` and `FTM` gain a modest AUPRC advantage over `base`, but still lose on AUROC. In the highest-overlap bucket, `base` again dominates on both metrics. Together, these results suggest that temporal OOD is not just a colder version of synthetic cold-start. Instead, it changes which subpopulations dominate the aggregate result, and therefore changes the model ranking.

### 4.4 Additional real-OOD screens support the benchmark-centric interpretation

We treat `BindingDB_Ki / unseen_target` and `DAVIS / unseen_target` as supporting real-OOD screens rather than co-equal main benchmarks. Both are informative because they test whether the synthetic `unseen_target` advantage of `FTM sparse` transfers beyond `BindingDB_Kd`. It does not. On `BindingDB_Ki`, `FTM sparse` falls from the `base` score of `0.6574 / 0.7103` to `0.6295 / 0.6855`. On `DAVIS`, it falls from `0.4258 / 0.8849` to `0.3705 / 0.8757`.

These support benchmarks reinforce the same interpretation as the patent results. The issue is not merely that one auxiliary method failed on one extra dataset. Rather, the benchmark itself determines which inductive bias appears to work. This is why we position the paper as a benchmark study, not as a method paper with negative ablations.

## 5 Discussion

The main message of this study is that DTI evaluation is benchmark-sensitive in a way that current reporting practice often obscures. A synthetic split can still be useful, but it should not be treated as a universal proxy for real OOD generalization. Our results show that even the sign of a method’s apparent gain can change when the benchmark changes.

An important design choice in this paper is the use of a compact model panel. A larger benchmark zoo could be added later, but it is not necessary to establish the central claim. The ranking reversal already appears with three representative systems, and the shift-axis diagnosis explains why that reversal occurs. In this sense, benchmark design itself is the main object of study.

The paper also has clear limitations. The support benchmarks `BindingDB_Ki` and `DAVIS` are currently seed0 only. The model family is intentionally narrow rather than exhaustive. We have not yet added statistical significance tests, and we do not evaluate downstream biological decision quality. These limitations should be stated plainly, but they do not weaken the central finding that synthetic and real-OOD rankings can disagree.

## 6 Conclusion

We presented a benchmark-first study of distribution shift in DTI prediction. A 3-seed synthetic reference panel on `BindingDB_Kd` showed that cold-start regimes are already heterogeneous, with different model biases winning on different splits. A promoted 3-seed temporal benchmark on `BindingDB_patent` then showed a ranking reversal: the plain `base` model outperformed both retrieval and target-memory variants, even though retrieval was strongest on synthetic `blind_start`. Patent year-band and overlap-bucket analyses further showed that temporal OOD is structured rather than monolithic. Overall, these results indicate that synthetic cold splits and real distribution shifts are not interchangeable evaluation settings. Future DTI papers should therefore report both synthetic and real-OOD evidence when making generalization claims.
