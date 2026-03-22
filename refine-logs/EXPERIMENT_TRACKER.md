# Experiment Tracker

| Run ID | Milestone | Purpose | System / Variant | Split | Metrics | Priority | Status | Notes |
|--------|-----------|---------|------------------|-------|---------|----------|--------|-------|
| B001 | M1 | synthetic reference panel | aggregate `base / RAICD / FTM` | `BindingDB_Kd synthetic splits` | AUPRC, AUROC | MUST | IN_PROGRESS | results exist; need one benchmark table |
| B002 | M2 | real OOD baseline | `base` | `BindingDB_patent / patent_temporal / seed0` | AUPRC, AUROC | MUST | DONE | `0.7743 / 0.7194` |
| B003 | M2 | real OOD retrieval probe | `RAICD both` | `BindingDB_patent / patent_temporal / seed0` | AUPRC, AUROC | MUST | DONE | `0.7688 / 0.7046`; completed in `patent_stage1_queue` |
| B004 | M2 | real OOD target-memory probe | `FTM sparse` | `BindingDB_patent / patent_temporal / seed0` | AUPRC, AUROC | MUST | DONE | `0.7757 / 0.7077` |
| B005 | M2 | assay-shift baseline | `base` | `BindingDB_Ki / unseen_target / seed0` | AUPRC, AUROC | MUST | DONE | `0.6574 / 0.7103` |
| B006 | M2 | assay-shift target-memory probe | `FTM sparse` | `BindingDB_Ki / unseen_target / seed0` | AUPRC, AUROC | MUST | DONE | `0.6295 / 0.6855` |
| B007 | M3 | real OOD multi-seed promotion | `base / RAICD / FTM sparse` | `BindingDB_patent / patent_temporal` | AUPRC, AUROC | MUST | DONE | `base 0.7772±0.0086/0.7223±0.0109`, `RAICD 0.7692±0.0018/0.7032±0.0010`, `FTM 0.7721±0.0025/0.7059±0.0037` |
| B008 | M4 | shift-axis diagnosis | overlap / year buckets | `all completed benchmarks` | bucket AUPRC, AUROC | MUST | IN_PROGRESS | patent diagnosis done in `reports/PATENT_SHIFT_DIAGNOSIS.md`; extend aggregation to remaining benchmarks |
| B009 | M4 | benchmark pivot narrative report | benchmark paper summary | all | ranking reversals, tables | MUST | IN_PROGRESS | pivot active |
