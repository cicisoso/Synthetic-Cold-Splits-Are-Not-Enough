Dear Editors,

Please consider our manuscript, `Benchmarking synthetic cold-start and temporal/provenance distribution shifts in drug--target interaction prediction`, for publication in the *Journal of Computer-Aided Molecular Design*.

This study addresses a validation problem in drug--target interaction prediction rather than proposing a new predictive architecture. Current DTI studies often rely on a single synthetic cold-start split as a proxy for model generalization. We examine this assumption using a matched five-model comparison panel spanning descriptor-based neural and classical baselines, pooled language-model baselines, and a graph-based baseline. Across synthetic `BindingDB_Kd` splits, temporal/provenance BindingDB benchmarks, and supporting target-cold OOD panels on `BindingDB_Ki` and `DAVIS`, we find that model ranking is benchmark-sensitive: the apparent best-performing model changes with split semantics, and even conclusions within the temporal family depend on overlap policy.

We believe the manuscript is well aligned with JCAMD because it is centered on chemoinformatics validation practice. The paper emphasizes benchmark semantics, reproducible evaluation, and practical guidance for model reporting and selection in DTI workflows. In addition to the main analyses, we provide year-band and overlap-bucket diagnosis for the primary temporal/provenance benchmark, paired-bootstrap support for principal comparisons, and reusable split manifests together with standalone evaluation scripts.

The main practical message is straightforward: single-split reporting is not sufficient for generalization claims in DTI, and benchmark-qualified reporting should be part of routine chemoinformatics model evaluation. We expect this to be relevant to readers working on affinity prediction, bioactivity modeling, and validation design for molecular machine learning.

This manuscript is original, is not under consideration elsewhere, and has been approved by all authors. A fixed review snapshot corresponding to commit `a5d6b8b` has been prepared for reproducibility, and a DOI-backed public archive will be deposited at acceptance.

Thank you for your consideration.

Sincerely,

- `[Corresponding Author Name]`
- `[Institution]`
- `[Email]`
