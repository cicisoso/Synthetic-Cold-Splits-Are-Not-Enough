# GitHub Release Checklist

This checklist is meant for the final public benchmark release, not for day-to-day research iteration.

## Repository Readiness

- [ ] README reflects the benchmark-first scope rather than the earlier method-exploration history
- [ ] `docs/` explains benchmark semantics, data staging, and evaluator usage
- [ ] `.gitignore` excludes local data, results, logs, and generated bundles
- [ ] `benchmark_resources/RELEASE_MANIFEST.md` matches the release commit

## Legal And Metadata

- [ ] choose and add an explicit repository license
- [ ] confirm that redistribution of any derived benchmark tables is allowed by upstream data terms
- [ ] replace placeholder repository URL, if changed
- [ ] add author-level metadata such as `CITATION.cff` if desired

## Release Assets

- [ ] export the benchmark bundles required by the manuscript
- [ ] attach bundles as a GitHub Release asset or DOI-backed archive
- [ ] attach the compiled manuscript PDF
- [ ] include the exact commit hash in the release notes

## Sanity Checks

- [ ] run the smoke evaluator example in `benchmark_resources_smoke/`
- [ ] export at least one benchmark bundle from scratch on a clean machine
- [ ] score an external prediction CSV against one exported test split
- [ ] verify that the public repository does not contain `data/`, `results/`, or `logs/`

## Nice-To-Have

- [ ] add GitHub topics such as `drug-target-interaction`, `benchmark`, `chemoinformatics`, `bindingdb`
- [ ] add a DOI badge after archiving
- [ ] add continuous integration for evaluator smoke tests
