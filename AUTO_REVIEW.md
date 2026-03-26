# Auto Review Log

Target venue: Journal of Computer-Aided Molecular Design (JCAMD)
Reviewer model: gpt-5.4 (xhigh reasoning)
Started: 2026-03-25 (fresh loop after major paper restructuring)

---

## Round 1 (2026-03-25)

### Assessment (Summary)
- Score: 6/10
- Verdict: Major Revision
- Key criticisms:
  - Claims stronger than evidence can isolate (temporal/provenance mixes multiple confounders)
  - Model comparison fairness not documented (tuning effort parity)
  - Over-reliance on AUPRC alone — need screening-oriented metric
  - 3 seeds too few given high variance; need global rank stability measure
  - Ki/DAVIS role overinterpreted
  - Split taxonomy hard to parse quickly

### Reviewer Raw Response

<details>
<summary>Click to expand full reviewer response</summary>

**Overall Score (1-10):** 6
**Verdict:** major revision

**Summary of the paper**
This manuscript studies whether synthetic cold-start evaluation in DTI prediction is a reliable proxy for deployment-relevant temporal and provenance shift. Using six models across synthetic BindingDB_Kd splits, two temporal/provenance BindingDB benchmarks, and two supporting target-cold datasets, the authors argue that model rankings do not transfer cleanly across these evaluation settings and that benchmark-qualified reporting is therefore necessary.

**Strengths**
1. The paper addresses an important and under-examined question for DTI benchmarking that is highly relevant to JCAMD readers.
2. The benchmark design is broader than many prior DTI papers, especially in separating patent and non-patent temporal settings rather than relying on a single split.
3. The model panel spans several commonly used families, which makes the conclusions more useful than a single-architecture case study.
4. The overlap-restricted and overlap-bucket analyses add diagnostic value and move beyond a simple leaderboard comparison.
5. The use of paired bootstrap confidence intervals is appropriate and strengthens the empirical claims relative to point estimates alone.
6. The manuscript appears clearly written, with a strong title, motivated introduction, and a practically useful take-home message.
7. The planned release of split manifests and a standalone evaluator is a meaningful resource contribution.

**Weaknesses**
1. The central claim is somewhat stronger than the evidence currently isolates. The temporal/provenance benchmarks appear to mix several factors at once: time, provenance, overlap support, assay/task composition, and possibly label-noise differences. As written, it is difficult to determine how much of the ranking change is specifically due to temporal/provenance shift versus other benchmark construction effects.
2. For a benchmarking paper, the fairness of the model comparison needs to be documented more rigorously. It is not yet clear whether all models received comparable tuning effort, validation protocol, and optimization treatment, which matters especially when simpler models outperform more expressive ones.
3. The evaluation relies very heavily on AUPRC. Because DTI data are highly imbalanced and JCAMD readers will care about screening utility, the main conclusions should be shown to hold under at least one additional threshold-free metric and one early-recognition metric.
4. Three seeds are on the low side given the substantial variance reported for some models/splits. The selected paired bootstrap analyses are useful, but the manuscript would benefit from a more global quantification of ranking instability or rank transferability across benchmark families.
5. The role of the supporting Ki and DAVIS target-cold benchmarks is not fully clear. They are useful context, but they are sufficiently different from the main BindingDB_Kd setting that they should not be over-interpreted as direct support for the main temporal/provenance argument.
6. The related work is broadly competent, but the DTI-specific benchmarking/leakage/prospective-validation positioning could be sharpened further.
7. The split taxonomy and overlap terminology may be difficult to parse quickly; the paper would benefit from a clearer schematic and tighter definitions.

**Questions for the authors**
1. How are positives and negatives defined across all benchmarks, and are class prevalences comparable across the main splits?
2. What leakage controls were applied for duplicate compounds, near-duplicate compounds, salt/tautomer variants, homologous targets, repeated assays, and document-family overlap?
3. How were hyperparameters selected for each model, and were tuning budgets comparable across model families?
4. Were pretrained encoders frozen or fine-tuned in the LM-based models, and how was this choice validated?
5. Do the main qualitative conclusions persist under AUROC and a screening-oriented metric such as EF or BEDROC?
6. Can the authors quantify ranking transferability more directly, for example with rank correlations, probability-of-being-best estimates, or a benchmark-family interaction analysis?
7. How exactly are overlap buckets defined, and what are the sample sizes in each bucket?
8. Will the public release include exact data snapshots, preprocessing code, trained model configs, and per-sample predictions in addition to split manifests and the evaluator?

**Minor issues**
1. "Blind-start" should be defined carefully and mapped explicitly to prior cold-start nomenclature.
2. The manuscript should consistently distinguish "temporal," "provenance," and "temporal/provenance" shift rather than blending them rhetorically.
3. The main results table would be easier to interpret if test-set size and class prevalence were shown in the caption or headers.
4. Some headline wording in the abstract and introduction should be slightly tempered unless supported by broader rank-based statistics.
5. A single figure summarizing benchmark construction and overlap-restricted variants would improve readability.

**Recommendation**
This is a relevant and potentially publishable benchmarking study for JCAMD. However, the core claim depends on benchmark rigor more than on model novelty, which raises the bar. Required changes: clarify causal scope of claims; document leakage controls and model-selection fairness; add screening-oriented metric; strengthen statistical treatment of ranking instability; make reproducibility package fully explicit.

</details>

### Actions Taken
- Implementing fixes for Round 2 (see below)

### Status
- Continuing to Round 2

---

## Round 2 (2026-03-25)

### Assessment (Summary)
- Score: 7/10
- Verdict: Minor Revision
- Remaining: tighten framing consistency, enumerate reproducibility artifacts, add computation details to rank concordance

### Actions Taken
- Added "Training fairness" paragraph documenting uniform optimization protocol
- Added Kendall's W rank concordance analysis (W=0.378 AUPRC, W=0.374 AUROC)
- Added metric robustness paragraph confirming conclusions hold under AUROC
- Tempered causal claims in Discussion
- Clarified Ki/DAVIS role as supporting (not primary) evidence
- Mapped blind_start to Pahikkala S4

### Status
- Continuing to Round 3

---

## Round 3 (2026-03-25)

### Assessment (Summary)
- Score: 8/10
- Verdict: Accept
- No substantive scientific issues remain

### Actions Taken
- Ensured consistent causal framing across abstract, discussion, conclusion
- Enumerated reproducibility artifacts precisely
- Added explicit "two threshold-free metrics" statement
- Added rank concordance computation details (midrank ties, mean over seeds)
- Added fixed-tuning-budget caveat

### Status
- COMPLETED — accepted

---

## Final Summary

| Round | Score | Verdict |
|-------|-------|---------|
| 1 | 6/10 | Major Revision |
| 2 | 7/10 | Minor Revision |
| 3 | 8/10 | Accept |

Key improvements across rounds:
1. Model comparison fairness documented (uniform tuning protocol)
2. Kendall's W rank concordance analysis added (W≈0.38, confirming low rank agreement)
3. AUROC metric robustness verified
4. Causal claims tempered to "aggregate non-interchangeability"
5. Ki/DAVIS role clarified as supporting evidence
6. Reproducibility package enumerated explicitly
7. Rank concordance computation details added

## Method Description

This paper presents a validation-oriented benchmark study for drug-target interaction (DTI) prediction. Six models spanning descriptor-based (MLP, Random Forest), language-model (DTI-LM, HyperPCM), graph-based (GraphDTA-style), and cross-attention (DrugBAN) architectures are evaluated across seven benchmarks organized into three families: synthetic cold-start (BindingDB_Kd unseen_drug/blind_start/unseen_target), temporal/provenance (patent and non-patent BindingDB time splits), and supporting target-cold OOD (BindingDB_Ki, DAVIS). The study demonstrates that model rankings are not preserved across these evaluation axes (Kendall's W ≈ 0.38), with overlap-bucket diagnosis revealing structured rather than monolithic temporal shift. The contribution is methodological — demonstrating and quantifying benchmark non-interchangeability — rather than architectural.
