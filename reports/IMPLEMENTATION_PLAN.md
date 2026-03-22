# IMPLEMENTATION_PLAN

**Chosen Idea**: `RAICD`  
**Primary dataset**: `BindingDB_Kd`  
**Task framing**: binary DTI classification from transformed affinity labels

## Labeling

- Convert affinity `Y` in nM to `pKd = -log10(Y / 1e9)`
- Label as positive if `pKd >= 7.0`

## Splits

- `warm`: TDC random split
- `unseen_drug`: TDC cold split on `Drug_ID`
- `unseen_target`: TDC cold split on `Target_ID`
- `blind_start`: TDC cold split on both `Drug_ID` and `Target_ID`

## Features

- Drugs:
  - RDKit Morgan fingerprints
- Targets:
  - hashed k-mer bag-of-subsequences

## Models

- `base`: no retrieval, only pair encoding
- `raicd`: base model + train-only drug and target retrieval + pair-conditioned aggregation

## Retrieval Design

- bank built strictly from the training split
- exact cosine top-k retrieval
- per-neighbor stats:
  - train positive rate
  - support count
- retrieval outputs:
  - drug-side context
  - target-side context
  - retrieval entropy as a confidence proxy

## Metrics

- AUROC
- AUPRC
- Accuracy
- F1
- Brier score
- ECE
- overlap-aware bucket metrics on test set

## Initial Run Order

1. smoke test on `BindingDB_Kd` unseen-drug split with subsampled training
2. compare `base` vs `raicd` on unseen-drug
3. run best setting on blind-start
4. add unseen-target

## Budget

- initial smoke: under 15 minutes
- first real run: 1 split, 1 seed
- full first round: `base` + `raicd`, unseen-drug + blind-start, 1 seed each
