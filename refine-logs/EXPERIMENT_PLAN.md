# Experiment Plan

**Problem**: distribution-shift robustness in drug-target interaction prediction is currently overstated by synthetic random/cold splits.
**Method Thesis**: the paper is now benchmark-first, not method-first. The main thesis is that DTI model rankings change materially across synthetic cold splits, assay-shifted BindingDB variants, and temporal/patent OOD splits, so benchmark design is itself the contribution.
**Date**: 2026-03-21

## Claim Map
| Claim | Why It Matters | Minimum Convincing Evidence | Linked Blocks |
|-------|-----------------|-----------------------------|---------------|
| C1: Synthetic cold splits do not faithfully predict performance under real distribution shifts. | This is the main paper claim and the benchmark contribution. | Same model family shows different rankings across `BindingDB_Kd` synthetic splits versus at least one real shift benchmark such as `BindingDB_patent / patent_temporal` and one assay-shifted BindingDB variant. | B1, B2, B3 |
| C2: Distribution shift in DTI is multi-axis rather than one-dimensional. | Reviewers need to see that "cold-start" is too coarse a label. | Performance varies systematically with drug overlap, target overlap, and temporal gap / benchmark source. | B1, B3, B4 |
| C3: Previously positive method gains are split-sensitive and often fail to transfer. | This justifies why the paper is benchmark-oriented rather than proposing yet another method. | `RAICD` and `FTM` behave inconsistently across `unseen_target`, `unseen_drug`, `blind_start`, `DAVIS`, and at least one additional shift benchmark. | B2, B3 |
| Anti-claim to rule out: the story is only about one unstable seed or one bad dataset. | Without this, the benchmark paper looks anecdotal. | Use matching multi-seed results where available and at least seed-0 screening on new benchmark families before drawing claims. | B1, B2, B3 |

## Paper Storyline
- Main paper must prove:
  - existing DTI conclusions change under benchmark choice
  - synthetic cold splits and real OOD shifts are not interchangeable
  - a compact baseline panel is enough to expose the mismatch
- Appendix can support:
  - detailed ablations of `FTM sparse`, routers, and selective fallback
  - extra dataset-specific hyperparameter sweeps
  - case studies and overlap-bucket plots
- Experiments intentionally cut:
  - new heavyweight method proposals as the paper centerpiece
  - broad architecture zoo comparisons before the benchmark thesis is established

## Experiment Blocks

### Block 1: Synthetic Split Reference Panel
- Claim tested: synthetic split rankings are already heterogeneous even within one dataset.
- Why this block exists: this is the reference point that the benchmark paper will challenge.
- Dataset / split / task: `BindingDB_Kd / unseen_target`, `unseen_drug`, `blind_start`.
- Compared systems: `base`, `RAICD both`, `FTM sparse` where applicable.
- Metrics: AUPRC first, AUROC second.
- Setup details: use matching multi-seed runs already available.
- Success criterion: produce a compact table showing ranking reversals across synthetic splits.
- Failure interpretation: if rankings are identical across splits, the benchmark thesis weakens.
- Table / figure target: Main Table 1.
- Priority: MUST-RUN

### Block 2: Real OOD Benchmark Panel
- Claim tested: real OOD benchmark splits produce materially different conclusions from synthetic splits.
- Why this block exists: this is the paper's main benchmark evidence.
- Dataset / split / task: `BindingDB_patent / patent_temporal` as the primary real-shift benchmark; `BindingDB_Ki / unseen_target` as assay-shift support if it yields a clean signal.
- Compared systems: `base`, `RAICD both`, `FTM sparse`.
- Metrics: AUPRC, AUROC.
- Setup details: seed-0 screening first, then escalate to 3 seeds only for benchmarks that produce a meaningful ranking difference.
- Success criterion: at least one real-shift benchmark yields a different ranking than the synthetic `BindingDB_Kd` story.
- Failure interpretation: if rankings remain the same everywhere, the benchmark contribution reduces to replication.
- Table / figure target: Main Table 2.
- Priority: MUST-RUN

### Block 3: Shift-Axis Diagnosis
- Claim tested: benchmark difficulty is driven by measurable shift axes, not just dataset name.
- Why this block exists: the paper needs diagnosis, not only leaderboard tables.
- Dataset / split / task: all benchmark panels.
- Compared systems: same compact model panel as Blocks 1 and 2.
- Metrics: bucketed AUPRC / AUROC versus drug overlap, target overlap, and temporal split year bands where available.
- Setup details: reuse saved predictions, compute post-hoc diagnostics offline.
- Success criterion: show that different benchmarks stress different axes.
- Failure interpretation: if no axis explains variance, the benchmark narrative is weaker.
- Table / figure target: Figure 2 or 3.
- Priority: MUST-RUN

### Block 4: Method-Stability Appendix
- Claim tested: the previously proposed methods are interesting probes but not stable enough to headline the paper.
- Why this block exists: preserve prior work without letting it control the paper.
- Dataset / split / task: `BindingDB_Kd / unseen_target`, `DAVIS / unseen_target`, optional `BindingDB_patent / patent_temporal`.
- Compared systems: `FTM sparse`, conservative FTM, selective fallback, `RAICD`.
- Metrics: AUPRC, AUROC.
- Setup details: reuse existing runs; only add new runs if needed for fairness on the patent benchmark.
- Success criterion: appendix clearly documents what transfers and what does not.
- Failure interpretation: if one method suddenly dominates all shifts, it should be reconsidered as the main line.
- Table / figure target: Appendix method-stability section.
- Priority: NICE-TO-HAVE

## Run Order and Milestones
| Milestone | Goal | Runs | Decision Gate | Cost | Risk |
|-----------|------|------|---------------|------|------|
| M0 | Freeze benchmark-paper thesis | rewrite plan + tracker + pivot report | story is benchmark-first and compact | low | lingering method-centric framing |
| M1 | Lock the synthetic reference panel | aggregate existing `BindingDB_Kd` multi-seed results | enough evidence for Table 1 | low | unresolved metric inconsistencies |
| M2 | Run real OOD benchmark screening | `BindingDB_patent / patent_temporal` seed0 panel, continue `BindingDB_Ki / unseen_target` seed0 | at least one benchmark yields a different ranking | medium | patent benchmark may require more epochs / caching time |
| M3 | Promote the strongest real OOD benchmark | escalate the most informative benchmark to multi-seed | real-shift claim is seed-stable | medium | compute grows if multiple benchmarks look promising |
| M4 | Finish diagnosis and paper-ready reporting | aggregate tables, shift-axis figures, and benchmark conclusions | main-paper tables covered | low | too many side results dilute the benchmark message |

## Compute and Data Budget
- Total estimated GPU-hours: about 20 to 35 GPU-hours for a benchmark-first paper if only one real OOD benchmark is escalated to multi-seed.
- Data preparation needs: existing TDC caches plus local `bindingdb_patent` benchmark files.
- Human evaluation needs: none.
- Biggest bottleneck: getting one real OOD benchmark with a clear ranking reversal and enough seeds to defend it.

## Risks and Mitigations
- Risk: the patent benchmark may still roughly agree with synthetic splits.
- Mitigation: keep `BindingDB_Ki` as the second screening route and emphasize the negative result if synthetic and real shifts unexpectedly align.
- Risk: assay and temporal shifts may interact with label conventions.
- Mitigation: use dataset-specific affinity conversion explicitly and document it in the benchmark section.
- Risk: benchmark paper looks like a collection of failures.
- Mitigation: frame the contribution as a benchmark diagnostic study where split-sensitive ranking reversals are the main result.

## Final Checklist
- [ ] Main paper tables are covered
- [ ] Real OOD benchmark evidence is present
- [ ] Shift-axis diagnosis is computed
- [ ] Method appendix is separated from benchmark contribution
- [ ] Nice-to-have runs are separated from must-run runs
