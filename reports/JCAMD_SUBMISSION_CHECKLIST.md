# JCAMD Submission Checklist

Manuscript title:

- `Benchmarking synthetic cold-start and temporal/provenance distribution shifts in drug--target interaction prediction`

Current manuscript file:

- `paper/main.tex`
- `paper/main.pdf`

## Scientific status

- [x] Main synthetic panel completed with matched 3-seed evaluation
- [x] Primary temporal/provenance panel completed with matched 3-seed evaluation
- [x] Controlled patent overlap variants completed
- [x] Year-band and overlap-bucket diagnosis completed
- [x] Full five-model support panel completed on `BindingDB_Ki / unseen_target`
- [x] Full five-model support panel completed on `DAVIS / unseen_target`
- [x] Paired bootstrap support completed for principal ranking comparisons

## Reviewer-risk items already addressed

- [x] Title reframed in journal methodology style
- [x] Rebuttal/revision language removed from the main text
- [x] `GraphDTA-style` missing main-table entry explicitly explained
- [x] Process-history appendices removed
- [x] Data/code availability upgraded from "reasonable request" wording to a fixed review snapshot with commit hash
- [x] Release manifest added at `benchmark_resources/RELEASE_MANIFEST.md`

## Required before submission

- [ ] Replace placeholder author names in `paper/main.tex`
- [ ] Replace placeholder affiliation and corresponding-author email in `paper/main.tex`
- [ ] Finalize `Author contributions` in `paper/main.tex`
- [ ] Finalize `Funding` statement in `paper/main.tex`
- [ ] Finalize `Competing interests` wording if needed
- [ ] Decide whether to keep `Not applicable` or add an ethics/data-use statement in Declarations
- [ ] Create the actual frozen submission archive from commit `a5d6b8b`
- [ ] If possible, mint or reserve a DOI-backed archive for the review snapshot
- [ ] Verify that the public repository branch/tag matches the frozen archive

## Recommended before submission

- [ ] Refresh all paper-facing summary docs from the final result JSONs
- [ ] Do one last language-tightening pass on the appendix tables and captions
- [ ] Remove local cache noise such as `src/raicd/__pycache__/`
- [ ] Generate a clean submission zip containing:
  - `paper/`
  - `benchmark_resources/RELEASE_MANIFEST.md`
  - evaluator scripts
  - final benchmark summary reports
- [ ] Prepare a point-by-point internal response memo for likely reviewer questions

## Current manuscript strengths to emphasize

- The paper is framed as validation methodology rather than as a new-model claim
- The main conclusion is benchmark-qualified and supported by both synthetic and temporal/provenance evidence
- The patent panel is diagnosed rather than treated as a black-box leaderboard
- The support OOD panel is now a full five-model matched comparison, not a partial follow-up

## Current weak points to keep in mind

- The patent benchmark remains temporal/provenance OOD rather than a pure time-shift benchmark
- The paper is still strongest as a benchmark/validation study, not as a benchmark-plus-resource-with-final-DOI paper until the archive is finalized
- Some appendix tables still produce minor box warnings, although compilation is clean

## Suggested immediate order

1. Freeze the submission snapshot and archive metadata
2. Fill real title-page and declaration fields
3. Do one final manuscript polish pass
4. Draft the cover letter and submission metadata in the JCAMD portal
