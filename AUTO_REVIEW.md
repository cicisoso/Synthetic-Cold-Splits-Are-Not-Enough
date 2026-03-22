# Auto Review Log

Project: `Synthetic Cold Splits Are Not Enough: Distribution-Shift Benchmarking for Drug-Target Interaction Prediction`

Start time: 2026-03-22

This document records the autonomous external-review loop, including raw reviewer responses, actions taken, and resulting manuscript changes.

## Round 1 (2026-03-22)

### Assessment (Summary)
- Score: `6/10`
- Verdict: `ALMOST`
- Submission recommendation: `No, not yet`
- Key criticisms:
  - the promoted patent benchmark was still under-specified
  - the claim scope was slightly broader than the evidence
  - the recent-baseline promotion logic looked vulnerable to cherry-picking criticism
  - uncertainty support was missing for several headline comparisons
  - the resource contribution was visible in code but under-sold in the manuscript
  - the diagnosis section needed more explicit quantitative support

### Reviewer Raw Response

<details>
<summary>Click to expand full reviewer response</summary>

1. **Score: 6/10.**

2. **Verdict: ALMOST.**

3. **Remaining critical weaknesses, ranked by severity.**

   **1. The central patent benchmark still looks too custom and under-specified.**  
   This is the biggest risk. Your main claim depends on `BindingDB_patent / patent_temporal`, yet the current wording leaves too much room for a reviewer to say: “this ranking reversal may be an artifact of your local split, preprocessing, or affinity conversion.”

   **2. The claim scope is slightly broader than the evidence.**  
   The evidence supports: *model rankings can flip across synthetic vs real OOD in this studied panel*. It does **not** yet fully support a broad field-level conclusion unless you stay very disciplined in wording. The title is strong; the paper must be equally cautious.

   **3. The recent-baseline story is vulnerable to cherry-picking criticism.**  
   “We screened multiple candidates on seed0, then promoted DTI-LM, while HyperPCM is summarized outside the main topline table because it does not change the main ranking” is exactly the kind of thing a skeptical reviewer will attack.

   **4. Statistical support is still thinner than it should be for a benchmark paper.**  
   You have the key bootstrap deltas, which is good. But several headline “winner” statements are still descriptive only. For a benchmark/resource paper, reviewers will ask for uncertainty whenever you make ranking claims.

   **5. The resource contribution is not yet sold hard enough.**  
   Right now it reads like a useful side product, not a clearly packaged contribution. For a non-method paper, that weakens the submission.

   **6. The diagnostic analysis sounds plausible but is not yet carrying enough weight in the narrative.**  
   “Year-band and overlap-bucket analyses show…” is not enough on its own. If that diagnosis is part of why the paper matters, it needs more visible quantitative support.

4. **Minimum concrete fix for each weakness.**

   **1. Patent benchmark under-specified → Minimum fix:**  
   Add one brutally explicit methods/appendix table for `patent_temporal` covering:
   - exact train/val/test year boundaries,
   - sample counts per split,
   - duplicate/overlap handling,
   - label construction and thresholding,
   - the patent-specific affinity conversion,
   - what “temporal/provenance OOD” concretely means,
   - what is seed-dependent vs fixed.  
   If a reviewer cannot reproduce the benchmark from the manuscript + release, this paper is in trouble.

   **2. Claim scope too broad → Minimum fix:**  
   Tighten title/abstract/discussion language to the evidence actually shown:
   - “synthetic cold splits and real OOD are not interchangeable” is okay,
   - but avoid sounding like you proved this universally across DTI.  
   Rephrase to “in the tested panel and benchmarks” wherever needed.

   **3. Cherry-picking risk in recent baselines → Minimum fix:**  
   Add a transparent screening table listing:
   - all recent baselines screened,
   - the seed0 criterion,
   - which models advanced to 3-seed runs,
   - why DTI-LM is promoted in the main text,
   - where HyperPCM fits.  
   Do not make readers infer selection logic.

   **4. Incomplete statistical support → Minimum fix:**  
   Add paired bootstrap or equivalent paired significance support for **every comparison used in a headline conclusion**, at minimum:
   - FTM vs base on `BindingDB_Kd / unseen_target`,
   - base vs RAICD and FTM on `BindingDB_Ki / unseen_target`,
   - base vs RAICD and FTM on `DAVIS / unseen_target`.  
   Then explicitly state that other cells are descriptive if you are not testing them.

   **5. Resource contribution under-described → Minimum fix:**  
   Add a short dedicated subsection plus one table:  
   - what exactly is released,
   - what files/artifacts a user gets,
   - how an external prediction CSV is evaluated,
   - why this is reusable beyond this paper.  
   For a benchmark-first paper, the reusable asset must be visible.

   **6. Diagnosis not visible enough → Minimum fix:**  
   Put one compact main-text figure/table with the actual year-band and overlap-bucket numbers, and tie it directly to the ranking reversal.  
   Right now the diagnosis reads more like a claim than evidence.

5. **Would I recommend submission now?**  
   **No. Not yet.**  

   The core empirical story is genuinely interesting and probably publishable in a solid Q2 venue. But in its current form, I think reviewers can still hit it on **benchmark construction clarity, selection/fairness of the model panel, and incomplete uncertainty coverage**. Fix those first. After that, this becomes a credible submission.

</details>

### Actions Taken
- Added an explicit patent benchmark specification table with year boundaries, counts, label transform, overlap policy, duplicate policy, and seed semantics:
  - [table_patent_spec.tex](/root/exp/dti_codex/paper/tables/table_patent_spec.tex)
- Added a transparent recent-baseline screening/promote table:
  - [table_recent_screening.tex](/root/exp/dti_codex/paper/tables/table_recent_screening.tex)
- Added a dedicated reusable-resource table and appendix subsection:
  - [table_resource_release.tex](/root/exp/dti_codex/paper/tables/table_resource_release.tex)
- Added a compact main-text patent diagnosis table with explicit year-band and overlap-bucket AUPRC values:
  - [table_patent_diagnosis_compact.tex](/root/exp/dti_codex/paper/tables/table_patent_diagnosis_compact.tex)
- Tightened claim-scope wording in the abstract, introduction, setup, results, and discussion:
  - [0_abstract.tex](/root/exp/dti_codex/paper/sections/0_abstract.tex)
  - [1_introduction.tex](/root/exp/dti_codex/paper/sections/1_introduction.tex)
  - [3_setup.tex](/root/exp/dti_codex/paper/sections/3_setup.tex)
  - [4_results.tex](/root/exp/dti_codex/paper/sections/4_results.tex)
  - [5_discussion.tex](/root/exp/dti_codex/paper/sections/5_discussion.tex)
- Rewrote the appendix structure so it now covers patent specification, support benchmarks, paired uncertainty support, baseline screening, and released resources:
  - [A_appendix.tex](/root/exp/dti_codex/paper/sections/A_appendix.tex)
- Extended the paired-bootstrap script to cover every comparison used in headline ranking claims:
  - [bootstrap_pairwise_ci.py](/root/exp/dti_codex/scripts/bootstrap_pairwise_ci.py)
- Added a paper appendix bootstrap summary table:
  - [table_bootstrap_summary.tex](/root/exp/dti_codex/paper/tables/table_bootstrap_summary.tex)
- Updated the repository README from the old RAICD method-centric storyline to the current benchmark/resource storyline:
  - [README.md](/root/exp/dti_codex/README.md)

### Results
- Patent main split remained supported:
  - `DTI-LM - base = +0.0054`, 95% CI `[+0.0028, +0.0079]`
- Patent alternative cutoff remained positive over matched 3-seed:
  - `patent_temporal_v2017`: `base 0.7044 ± 0.0058 / 0.6624 ± 0.0079`
  - `DTI-LM 0.7134 ± 0.0027 / 0.6754 ± 0.0039`
- Newly added paired bootstrap support for the remaining headline comparisons:
  - `BindingDB_Kd / unseen_target`: `FTM - base = +0.0214`, 95% CI `[+0.0143, +0.0286]`
  - `BindingDB_Ki / unseen_target`: `RAICD - base = -0.0249`, 95% CI `[-0.0271, -0.0226]`
  - `BindingDB_Ki / unseen_target`: `FTM - base = -0.0174`, 95% CI `[-0.0197, -0.0150]`
  - `DAVIS / unseen_target`: `RAICD - base = -0.0259`, 95% CI `[-0.0375, -0.0127]`
  - `DAVIS / unseen_target`: `FTM - base = -0.0310`, 95% CI `[-0.0434, -0.0177]`
- The paper still compiles successfully after all revisions:
  - [main.pdf](/root/exp/dti_codex/paper/main.pdf)

### Status
- Continuing to Round 2 re-review.

## Round 2 (2026-03-22)

### Assessment (Summary)
- Score: `8/10`
- Verdict: `READY`
- Submission recommendation: `Yes`
- Remaining concerns:
  - external-validity breadth is still limited to one promoted patent benchmark plus supporting Ki/DAVIS
  - model-panel breadth is still compact
  - diagnosis remains descriptive rather than fully mechanistic
  - venue fit should stay benchmark/resource-oriented rather than method-oriented
  - metric wording should remain anchored to AUPRC as the primary metric

### Reviewer Raw Response

<details>
<summary>Click to expand full reviewer response</summary>

1. **Score: 8/10**

2. **Verdict: READY**

3. **Remaining critical weaknesses, ranked by severity**

   **1. External-validity ceiling is still real.**  
   The paper is now much better defended, but the main real-OOD claim still leans heavily on one promoted patent benchmark plus supporting Ki/DAVIS checks. That is enough for a solid Q2 benchmark paper, but some reviewers will still say the real-OOD side is not broad.

   **2. Model-panel breadth is still limited.**  
   You fixed the cherry-picking problem, but the paper still tests a compact internal panel plus two recent LM-style baselines. That is acceptable if framed as a benchmark-diagnostic case study, not as a definitive field-wide ranking paper.

   **3. The diagnosis is quantitative now, but still mostly descriptive.**  
   Year-band and overlap-bucket slices strengthen the paper, but they do not fully establish mechanism. A reviewer can still say: “interesting stratification, but not a full explanation.”

   **4. The paper remains more benchmark/resource than biological-insight or method paper.**  
   That is not a flaw for the right venue, but it affects venue fit. A method-hungry reviewer may still ask, “what is the algorithmic novelty?” even though that is no longer the right standard for evaluating this manuscript.

   **5. Metric interpretation still needs to stay disciplined.**  
   You are clearly using AUPRC as the primary metric, which is correct here, but because some AUROC patterns are weaker or mixed, the prose must remain careful not to overstate “best model” beyond the declared primary metric.

4. **Minimum concrete fix for each remaining weakness**

   **1. External-validity ceiling → Minimum fix:**  
   Add one explicit sentence in the discussion/conclusion saying this is a **well-supported benchmark case study**, not an exhaustive census of all real-OOD DTI settings. That preempts the obvious reviewer objection.

   **2. Limited model panel → Minimum fix:**  
   Keep the current transparent screening table and add one sentence making clear that the goal is to test **ranking stability under benchmark shift**, not to declare a universal SOTA leaderboard.

   **3. Diagnosis remains descriptive → Minimum fix:**  
   Tone the language down slightly: say the diagnosis **helps explain** or is **consistent with** the reversal, rather than implying it fully explains causality.

   **4. Benchmark/resource positioning → Minimum fix:**  
   In the introduction and discussion, explicitly position the contribution as a **benchmarking/resource paper for reliable DTI evaluation**, not a new-model paper. Also make sure the release is easy to access at submission.

   **5. Metric interpretation discipline → Minimum fix:**  
   Wherever you say “strongest” or “winner,” anchor it explicitly to **AUPRC as the primary metric under class imbalance**, with AUROC secondary.

5. **Would I recommend submission now?**  
   **Yes.** I would recommend submission now **to a benchmark/resource-friendly Q2 journal** in bioinformatics or AI for drug discovery.

   Bluntly: this is now past the “not ready” line. The major blockers from the first round were the right ones, and you fixed them. I would still avoid overselling it as a field-definitive conclusion or a method paper, but as a careful benchmark/diagnostic/resource manuscript, it now looks submission-worthy.

</details>

### Actions Taken
- Added the final wording safeguards requested in Round 2:
  - explicit benchmark-case-study framing in the introduction, discussion, and conclusion
  - explicit AUPRC-primary wording around winner/strongest claims
  - softer causal wording for the diagnosis (`helps explain`, `consistent with`)
- Recompiled the paper after these final wording edits:
  - [main.pdf](/root/exp/dti_codex/paper/main.pdf)

### Results
- External reviewer assessment improved from `6/10, ALMOST` to `8/10, READY`.
- The reviewer explicitly recommended submission to a benchmark/resource-friendly Q2 journal.

### Status
- Loop completed after positive external assessment.
