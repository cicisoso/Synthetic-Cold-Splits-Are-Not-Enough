# Distribution-Shift Benchmark Pivot

## New Thesis

The project is no longer a method paper centered on `FTM sparse`. It is now a benchmark-first paper about how DTI conclusions change under different shift definitions.

The core claim is:

> synthetic cold splits and real distribution shifts are not interchangeable in DTI, and model rankings can reverse when the benchmark changes.

## Why The Pivot Happened

The previous method line produced one real positive result on `BindingDB_Kd / unseen_target`, but it did not transfer reliably:

- `FTM sparse` was positive on `BindingDB_Kd / unseen_target`
- `RAICD` remained useful on `BindingDB_Kd / blind_start`
- `RAICD` lost its mean AUPRC advantage on `BindingDB_Kd / unseen_drug`
- `FTM sparse` failed on `DAVIS / unseen_target`
- `BindingDB_Ki` required data-loader fixes before even becoming evaluable

This pattern is better interpreted as benchmark sensitivity than as evidence for one clean universal method.

## What Counts As Success Now

A successful paper no longer needs one method to win everywhere. It needs to show that:

1. synthetic split conclusions are unstable across shift definitions
2. at least one real OOD benchmark disagrees with the synthetic split ranking
3. the disagreement can be linked to measurable shift axes such as drug overlap, target overlap, assay family, or time

## Current Evidence Base

### Synthetic reference panel

From `BindingDB_Kd`:

- `unseen_target`: `FTM sparse` improves over `base` on the 3-seed mean
- `unseen_drug`: `RAICD` does not improve mean AUPRC over `base`
- `blind_start`: `RAICD` improves mean AUPRC over `base`

This already shows that even synthetic split conclusions are regime-dependent.

### Real-shift screening

- `DAVIS / unseen_target / seed0`: `FTM sparse` is negative versus `base`
- `BindingDB_Ki / unseen_target / seed0`: `base = 0.6574 / 0.7103`, `FTM sparse = 0.6295 / 0.6855`; target-memory remains negative under assay shift
- `BindingDB_patent / patent_temporal / 3 seeds`: `base = 0.7772 ± 0.0086 / 0.7223 ± 0.0109`, `RAICD = 0.7692 ± 0.0018 / 0.7032 ± 0.0010`, `FTM sparse = 0.7721 ± 0.0025 / 0.7059 ± 0.0037`; temporal real-OOD rejects retrieval and still favors `base` over target-memory

### Early reversal signal

A ranking reversal is already visible between the synthetic and real-OOD views for retrieval:

- on `BindingDB_Kd / blind_start`, `RAICD` beats `base` on the 3-seed mean AUPRC
- on `BindingDB_patent / patent_temporal / 3 seeds`, `base` beats `RAICD` on both AUPRC and AUROC

This is the kind of disagreement the benchmark paper is supposed to surface.

### Promotion decision

`BindingDB_patent / patent_temporal` is now the primary real-OOD benchmark for multi-seed promotion. The reason is straightforward:

- it already has the full `base / RAICD / FTM sparse` seed0 panel
- it exposes a cleaner synthetic-vs-real ranking disagreement than `BindingDB_Ki`
- `BindingDB_Ki` remains useful as assay-shift support, but it is currently a two-model negative result rather than the paper's main reversal axis

## Immediate Run Order

1. aggregate synthetic versus real-shift ranking changes into one benchmark table
2. fold the completed patent year-band and overlap-bucket diagnosis into the benchmark paper narrative
3. keep `BindingDB_Ki` as a supporting assay-shift counterexample in the main narrative or appendix
4. decide whether any additional bucket analysis beyond patent is needed for reviewer-proofing

## Interpretation Policy

- If a method loses on real OOD benchmarks, that is benchmark evidence, not a failed paper.
- If rankings reverse between synthetic and real OOD settings, that is the main result.
- If no benchmark reversal appears, the benchmark claim weakens and the paper should be re-scoped.
