# Patent Decision Panel

Decision-facing metrics on `BindingDB_patent / patent_temporal`, averaged over the matched 3-seed runs.

| System | EF@1% | EF@5% | Per-target Hit@10 | Per-target Recall@10 | Per-target Macro-AUPRC |
|--------|-------|-------|-------------------|----------------------|------------------------|
| `base` | `1.7062` | `1.6428` | `0.8941` | `0.3258` | `0.6191` |
| `RF` | `1.7287` | `1.7206` | `0.9167` | `0.3480` | `0.6567` |
| `DTI-LM` | `1.7169` | `1.5931` | `0.9097` | `0.3190` | `0.6011` |

- Best mean `EF@1%`: `RF`
- Best mean `per-target Hit@10`: `RF`
