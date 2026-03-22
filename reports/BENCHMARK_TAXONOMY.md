# Benchmark Taxonomy

This table documents the shift axes and split statistics used in the paper. Counts and test prevalence are reported from seed0 result files for consistency.

| Benchmark | Synthetic? | Shift Axes | Time Shift | Assay/Source Shift | Overlap Regime | Test Rows | Test Positive Rate |
|-----------|------------|------------|------------|--------------------|----------------|-----------|--------------------|
| `BindingDB_Kd / unseen_drug` | yes | unseen drug IDs | no | no | drug-cold, target overlap remains | 12744 | `0.1966` |
| `BindingDB_Kd / blind_start` | yes | unseen drug IDs + unseen target IDs | no | no | drug-cold and target-cold | 2821 | `0.2031` |
| `BindingDB_Kd / unseen_target` | yes | unseen target IDs | no | no | target-cold, drug overlap remains | 12052 | `0.2239` |
| `BindingDB_patent / patent_temporal` | no | time + provenance/source change | yes | yes | partial drug and target overlap | 49028 | `0.5745` |
| `BindingDB_Ki / unseen_target` | mixed | target holdout + assay-family change | no | yes | target-cold under assay shift | 70380 | `0.4652` |
| `DAVIS / unseen_target` | mixed | target holdout + dataset shift | no | yes | target-cold under dataset shift | 5168 | `0.0615` |

## Main-Text Use

- Use this taxonomy table in the Setup section or appendix to justify why `BindingDB_patent` should be described as temporal/provenance OOD rather than pure time shift.
- Use the test positive rate column to remind readers that AUPRC should be interpreted within benchmark, not across benchmark families.
