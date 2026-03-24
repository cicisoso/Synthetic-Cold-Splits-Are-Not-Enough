# Paper Plan

**Title**: Synthetic Cold Splits Are Not Enough: Distribution-Shift Benchmarking for Drug-Target Interaction Prediction
**Venue**: Q2 SCI journal target in bioinformatics / AI for drug discovery
**Type**: empirical / diagnostic benchmark paper
**Date**: 2026-03-21
**Target manuscript length**: about 10-12 main-body pages before references and appendix
**Section count**: 6 main sections

## Claims-Evidence Matrix

| Claim | Evidence | Status | Section |
|-------|----------|--------|---------|
| Synthetic cold-start DTI is regime-dependent even within one dataset. | `BindingDB_Kd` 3-seed panel: `unseen_drug` (`base > RAICD`), `blind_start` (`RAICD > base`), `unseen_target` (`FTM > base`). | Supported | §4.1 |
| Synthetic cold splits and real temporal shifts are not interchangeable because model rankings reverse. | `BindingDB_patent / patent_temporal` 3-seed panel: `base > FTM > RAICD`, contrasted with synthetic `blind_start` where `RAICD` wins. | Supported | §4.2 |
| Real temporal OOD is structured across shift axes rather than being a single scalar difficulty. | Patent diagnosis by year band and overlap bucket. | Supported | §4.3 |
| Synthetic `unseen_target` gains do not consistently transfer to additional OOD settings. | Preliminary support screens on `BindingDB_Ki / unseen_target` seed0 and `DAVIS / unseen_target` seed0 are both negative for `FTM sparse`. | Suggestive / secondary | §4.4 + Appendix |

## Paper Type And Structure

This is a benchmark-first empirical paper, not a method paper. The structure should emphasize:

1. one compact synthetic reference panel
2. one promoted real-OOD benchmark with full 3-seed evidence
3. one diagnosis section that explains why the ranking changes
4. one short secondary support section showing that the synthetic `unseen_target` gain may not be portable

The paper should avoid turning into a method-ablation catalog. Older method-centric threads such as routers, conservative FTM, and selective fallback should stay in the appendix or be omitted.

## Structure

### §0 Abstract

- **One-sentence problem**: cold-start DTI papers commonly use synthetic split definitions as proxies for real OOD generalization, but the stability of that assumption is unclear.
- **Approach**: compare a compact model panel across synthetic cold splits and real-OOD benchmarks, then diagnose the promoted temporal benchmark by year and overlap.
- **Key result**: `RAICD` wins on synthetic `BindingDB_Kd / blind_start`, but loses to `base` on `BindingDB_patent / patent_temporal` over 3 seeds; `FTM sparse` also fails to exceed `base` on the temporal benchmark.
- **Implication**: synthetic cold splits and real-OOD shifts are not interchangeable, so DTI evaluation should report both.
- **Estimated length**: 180-220 words.

### §1 Introduction

- **Opening hook**: many DTI papers claim cold-start robustness from one split definition, but “cold-start” bundles together distinct failure modes.
- **Gap**: prior evaluation practice often assumes synthetic cold splits are adequate proxies for real distribution shift.
- **Key questions**:
  - do model rankings remain stable across synthetic cold-start regimes?
  - do those rankings survive under real temporal and assay shifts?
  - which shift axes explain the disagreement?
- **Contributions**:
  1. a 3-seed synthetic reference panel on `BindingDB_Kd` showing regime-dependent rankings across `unseen_drug`, `blind_start`, and `unseen_target`
  2. a 3-seed real temporal benchmark on `BindingDB_patent` showing a ranking reversal relative to synthetic `blind_start`
  3. a year-band and overlap-bucket diagnosis demonstrating that temporal OOD is structured, not monolithic
  4. preliminary support screens from `BindingDB_Ki` and `DAVIS` suggesting that synthetic `unseen_target` gains do not transfer reliably
- **Hero figure**: synthetic-vs-real ranking reversal. Left panel: synthetic `blind_start` where `RAICD` wins. Right panel: patent temporal where `base` wins. Caption should explicitly state that the same model family changes rank when the benchmark changes.
- **Estimated length**: 1.5 pages.
- **Key citations**: synthetic cold-start DTI studies such as `DTI-LM`, `DrugLAMP`, `PMMR`, `SP-DTI`, `GS-DTI`, and `ColdstartCPI`; dataset anchors such as `BindingDB` and `DAVIS`; and benchmark-sensitivity precedents such as the inductive drug-repurposing critique, the generalizability analysis of therapeutic ML, and `DDI-Ben`.

### §2 Related Work

- **Subtopics**:
  - synthetic cold-start evaluation in DTI
  - retrieval, inductive, and memory-based DTI generalization methods
  - distribution-shift and benchmark design in molecular ML / biomedical interaction prediction
- **Positioning**:
  - this paper is not introducing another universal DTI architecture
  - the novelty is diagnostic: it demonstrates that conclusions depend on shift definition
  - the compact baseline panel is a deliberate design choice to expose benchmark sensitivity rather than to win a leaderboard
- **Minimum length**: about 1 page with synthesis rather than a method list.

### §3 Benchmark Setup

- **Problem formulation**: evaluate whether a compact model panel preserves its ranking across synthetic and real-OOD shift definitions.
- **Benchmarks**:
  - synthetic panel: `BindingDB_Kd / unseen_drug`, `blind_start`, `unseen_target`
  - primary real-OOD benchmark: `BindingDB_patent / patent_temporal`
  - support real-OOD screens: `BindingDB_Ki / unseen_target`, `DAVIS / unseen_target`
- **Benchmark taxonomy table**:
  - synthetic entity holdout axes: unseen drug, unseen target, blind start
  - real-OOD axes: temporal/provenance shift, assay shift, dataset shift
  - split statistics: sample count and prevalence for each benchmark
- **Models**:
  - `base`
  - `RF`
  - `DTI-LM`
  - `HyperPCM`
  - `GraphDTA-style`
- **Metrics**:
  - AUPRC as primary
  - AUROC as secondary
- **Reproducibility**:
  - matched 3-seed reporting for the synthetic reference panel, the promoted patent benchmark, and the non-patent temporal robustness probe
  - matched 3-seed support on `BindingDB_Ki` and `DAVIS`
  - paired bootstrap uncertainty support for the headline expanded-panel comparisons, especially `RF` against `base` and `DTI-LM` on synthetic drug-cold, blind-start, and temporal benchmarks
- **Setup details to document**:
  - dataset-specific affinity conversion for patent
  - year-based patent split construction
  - overlap score and overlap-bucket definition
- **Estimated length**: 1.5-2 pages.

### §4 Results

- **§4.1 Synthetic cold splits are already regime-dependent**
  - use `BindingDB_Kd` 3-seed table
  - main point: no single method wins all synthetic regimes
  - expected evidence source: [BENCHMARK_TABLE_LIVE.md](/root/exp/dti_codex/reports/BENCHMARK_TABLE_LIVE.md)

- **§4.2 Real temporal/provenance shift favors a different learner family**
  - use patent 3-seed panel and the non-patent temporal probe
  - main point: the promoted temporal benchmarks favor the learner-control `RF` baseline rather than preserving the smaller-panel or pooled-LM-centered ordering
  - connect directly back to the heterogeneous synthetic reference panel

- **§4.3 Temporal shift is structured across year bands and overlap levels**
  - use year-band and overlap-bucket patent diagnosis
  - main point: the ranking change is linked to measurable shift axes
  - expected evidence source: [PATENT_SHIFT_DIAGNOSIS.md](/root/exp/dti_codex/reports/PATENT_SHIFT_DIAGNOSIS.md)

- **§4.4 Preliminary support screens**
  - short subsection or appendix forward-reference
  - use `BindingDB_Ki` and `DAVIS` as secondary support benchmarks, not co-equal headline results

- **Estimated length**: about 3 pages.

### §5 Discussion

- **Main discussion points**:
  - why synthetic cold splits can mislead when treated as universal proxies
  - why a compact benchmark panel is sufficient to reveal ranking instability
  - what future DTI papers should report to avoid overclaiming
- **Limitations**:
- compact model family rather than a large external baseline zoo
- incomplete multi-seed coverage on support benchmarks
- no statistical significance testing yet
- no downstream biological validation beyond benchmark performance
- the promoted patent benchmark mixes temporal shift with provenance / assay changes, so it should be described as temporal/provenance OOD rather than pure time alone
- **Estimated length**: about 1 page.

### §6 Conclusion

- **Restatement**: synthetic cold splits and real-OOD shifts are not interchangeable in DTI evaluation.
- **Takeaway**: ranking reversals are not edge cases; they are central evidence that benchmark design changes conclusions.
- **Future work**:
  - expand real-OOD axes beyond patent temporal and assay shift
  - standardize benchmark reporting protocols for DTI generalization
- **Estimated length**: 0.5 pages.

## Figure Plan

| ID | Type | Description | Data Source | Priority |
|----|------|-------------|-------------|----------|
| Fig 1 | Hero comparison | Benchmark-sensitivity summary contrasting the synthetic reference panel with the promoted temporal benchmarks under the expanded five-model panel. | [BENCHMARK_TABLE_LIVE.md](/root/exp/dti_codex/reports/BENCHMARK_TABLE_LIVE.md) | HIGH |
| Table 1 | Main comparison table | Synthetic reference panel plus promoted patent temporal benchmark. | [PAPER_TABLE_DRAFTS.md](/root/exp/dti_codex/reports/PAPER_TABLE_DRAFTS.md) | HIGH |
| Fig 2 | Diagnosis figure | Patent temporal year-band and overlap-bucket analysis. | [PATENT_SHIFT_DIAGNOSIS.md](/root/exp/dti_codex/reports/PATENT_SHIFT_DIAGNOSIS.md) | HIGH |
| Table A1 | Appendix table | `BindingDB_Ki` and `DAVIS` support benchmarks showing non-transfer of synthetic `unseen_target` gains. | [PAPER_TABLE_DRAFTS.md](/root/exp/dti_codex/reports/PAPER_TABLE_DRAFTS.md) | MEDIUM |

### Hero Figure Detail

The hero figure should not be an architecture diagram. It should be a benchmark-comparison figure with:

- left panel: synthetic `BindingDB_Kd` rows highlighting that different synthetic regimes already favor different systems
- right panel: promoted temporal benchmarks highlighting that `RF` becomes the strongest learner-control baseline on both patent and non-patent temporal axes
- visual emphasis on benchmark-dependent winner changes and on the fact that the expanded panel is not LM-dominated
- a caption that explicitly says benchmark choice and overlap policy change the apparent best system

Draft caption:

> Different benchmark families can favor different learner families. Within the expanded panel, synthetic `BindingDB_Kd` already shows regime-dependent winners, while the promoted patent and non-patent temporal benchmarks favor the learner-control `RF` baseline rather than preserving a single pooled-LM-centered ordering.

## Citation Plan

- §1 Intro:
  - cold-start DTI / DTA motivation papers already cited in the manuscript
  - benchmark or generalization papers motivating evaluation caution, including generalizability and benchmark-design precedent
- §2 Related:
  - retrieval / inductive DTI methods already represented by the cited synthetic cold-start literature
  - distribution-shift / domain generalization papers represented by the cited molecular benchmark literature
  - benchmark-design precedent represented by `DDI-Ben` and the inductive-world critique
- §3 Setup:
  - data-source anchors for BindingDB and DAVIS, with the local patent split documented in the appendix tables

## Reviewer Feedback

- Claude review summary:
  - strongest story: `BindingDB_Kd` synthetic regime instability + `BindingDB_patent` ranking reversal + patent diagnosis
  - main fixes required: add uncertainty support for key reversals, downgrade claim 4 to secondary evidence, add benchmark taxonomy and split-count context
  - keep `BindingDB_Ki` and `DAVIS` in appendix-strength support rather than letting them carry the paper
  - paired bootstrap uncertainty support has now been added for the three key AUPRC comparisons

## Next Steps

- [x] Turn [PAPER_TABLE_DRAFTS.md](/root/exp/dti_codex/reports/PAPER_TABLE_DRAFTS.md) into final paper tables / figure captions
- [x] Add paired uncertainty support for the main ranking reversals
- [x] Add benchmark taxonomy and split-statistics table
- [x] Write Introduction / Setup / Results into journal-style manuscript text
- [x] Verify and complete citation list
- [x] Compile a first manuscript draft
- [ ] Tighten wording and reduce redundancy across Abstract / Introduction / Discussion
- [ ] Finalize journal-facing figure/table placement and appendix references
