# Manuscript Skeleton

## Title

Synthetic Cold Splits Are Not Enough: Distribution-Shift Benchmarking for Drug-Target Interaction Prediction

## Abstract

- Problem:
- Approach:
- Main result:
- Implication:

## 1 Introduction

### Paragraph 1: Motivation

- Cold-start DTI evaluation is widely used to claim generalization.
- Existing practice often treats split choice as a technical detail rather than a source of scientific uncertainty.

### Paragraph 2: Gap

- Synthetic cold splits and real distribution shifts are conceptually different.
- It is unclear whether model rankings are preserved across them.

### Paragraph 3: Questions

- Are synthetic cold-start conclusions stable across regimes?
- Do they survive under real temporal and assay shifts?
- Which shift axes explain disagreement?

### Paragraph 4: Contributions

1. We show regime-dependent rankings across `BindingDB_Kd / unseen_drug`, `blind_start`, and `unseen_target`.
2. We show a 3-seed ranking reversal on `BindingDB_patent / patent_temporal`.
3. We diagnose the temporal benchmark by year and overlap.
4. We provide support evidence from `BindingDB_Ki` and `DAVIS` that synthetic `unseen_target` gains do not transfer reliably.

## 2 Related Work

### 2.1 Cold-start evaluation in DTI

- [VERIFY citation block]

### 2.2 Inductive, retrieval, and memory-based DTI methods

- [VERIFY citation block]

### 2.3 Distribution shift and benchmark design in molecular ML

- [VERIFY citation block]

### Positioning paragraph

- This paper is benchmark-first and diagnostic.
- The contribution is not a new architecture, but evidence that benchmark choice changes conclusions.

## 3 Benchmark Setup

### 3.1 Problem Statement

- Define the benchmark question as rank stability across shift definitions.

### 3.2 Benchmarks

- Synthetic:
  - `BindingDB_Kd / unseen_drug`
  - `BindingDB_Kd / blind_start`
  - `BindingDB_Kd / unseen_target`
- Real-OOD:
  - `BindingDB_patent / patent_temporal`
  - `BindingDB_Ki / unseen_target`
  - `DAVIS / unseen_target`

### 3.3 Model Panel

- `base`
- `RAICD`
- `FTM sparse`

### 3.4 Metrics and Protocol

- Primary metric: AUPRC
- Secondary metric: AUROC
- Matched 3-seed reporting where available
- Seed0 support on auxiliary benchmarks

### 3.5 Benchmark Construction Notes

- Patent year split
- Patent affinity conversion
- Overlap-score computation
- Overlap-bucket definition

## 4 Results

### 4.1 Synthetic cold splits are already regime-dependent

- Insert Table 1.
- Key claim: no single method wins all synthetic regimes.

### 4.2 Real temporal shift reverses the retrieval conclusion

- Insert patent 3-seed comparison.
- Key claim: `base` beats `RAICD` and `FTM` on real temporal OOD.

### 4.3 Temporal shift is structured across year bands and overlap levels

- Insert Figure 2.
- Key claim: the ranking change aligns with year and overlap structure.

### 4.4 Additional real-OOD screens support the benchmark-centric interpretation

- Insert appendix forward-reference.
- Key claim: synthetic `unseen_target` gains are not portable.

## 5 Discussion

### 5.1 Why synthetic cold splits can mislead

- Benchmark choice changes dominant failure modes.

### 5.2 Why a compact model panel is enough

- The main story is ranking instability, not leaderboard breadth.

### 5.3 Limitations

- Compact baseline set
- Incomplete seed coverage on support benchmarks
- No significance testing yet

## 6 Conclusion

- Restate ranking reversal
- Restate recommendation for future DTI evaluation

## Appendix

### A. Additional Real-OOD Support

- `BindingDB_Ki`
- `DAVIS`

### B. Method-Centric Ablations

- router
- selective fallback
- robustness regularization
