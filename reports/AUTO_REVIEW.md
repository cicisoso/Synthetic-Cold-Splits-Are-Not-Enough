# AUTO_REVIEW

**Round**: 1  
**Date**: 2026-03-21  
**Reviewer**: Claude Code review MCP  
**Scope**: diagnose first-round RAICD failures and propose the minimum fix

## Round 1 Review Finding

Initial `RAICD` with flat retrieval attention behaved inconsistently:

- on `BindingDB_Kd / unseen_drug`, it improved AUROC but underperformed the matched base model on overall AUPRC
- overlap analysis showed the failure concentrated in the lowest-overlap bucket

Reviewer diagnosis:

> the attention aggregator had no retrieval-quality bias, so low-similarity neighbors could inject misleading evidence as confidently as high-similarity ones.

## Implemented Fixes

### Tried and kept

- added neighbor similarity as an additive bias to retrieval attention logits
- preserved train-only retrieval
- kept overlap-aware reporting

### Tried and rejected

- global retrieval gate
- result: did not improve the main metrics consistently

## Key Results

### Unseen drug

- `base`: AUPRC `0.608`, AUROC `0.823`
- `raicd` flat retrieval: AUPRC `0.569`, AUROC `0.828`
- `raicd` similarity-biased attention: AUPRC `0.614`, AUROC `0.840`

### Blind start

- `base`: AUPRC `0.352`, AUROC `0.658`
- `raicd` similarity-biased attention: AUPRC `0.407`, AUROC `0.686`

## Interpretation

- Retrieval is worth keeping.
- The original flat attention was too confidence-blind.
- Similarity-biased attention recovers the main idea into a net win on both strict splits that were fully tested.
- The lowest-overlap bucket is still weak and remains the main unresolved failure mode.

## Next Recommended Steps

1. add an abstention or fallback mechanism for the lowest-overlap regime
2. run multi-seed comparisons for `base` versus `raicd`
3. extend to `unseen_target`
4. test whether drug-side retrieval alone is stronger than symmetric retrieval on `unseen_drug`

## Follow-up Investigation

Additional full experiments were run after Round 1.

### Full unseen_target

- `base`: AUPRC `0.544`, AUROC `0.786`
- `raicd` both-side retrieval: AUPRC `0.465`, AUROC `0.744`
- `raicd` drug-only retrieval: AUPRC `0.516`, AUROC `0.765`
- `raicd` target-only retrieval: AUPRC `0.475`, AUROC `0.752`

### Interpretation of asymmetry

- `RAICD` is a clear positive on `unseen_drug` and `blind_start`.
- `RAICD` is currently a negative on `unseen_target`.
- On `unseen_drug`, both-side retrieval is necessary. Drug-only and target-only retrieval both underperform the symmetric model.
- On `unseen_target`, drug-only retrieval is the least bad retrieval variant, but the plain base encoder still wins.

### Current best honest claim

Retrieval-augmented inductive DTI helps in stricter cold-start regimes involving unseen drugs and blind-start combinations, but it is not yet robust for unseen-target generalization under the current lightweight protein representation.

### Ongoing jobs

A multi-seed validation job was launched in tmux session `raicd_round1` using [scripts/run_round1_multiseed.sh](/root/exp/dti_codex/scripts/run_round1_multiseed.sh). Logs are written to [logs/round1_multiseed.log](/root/exp/dti_codex/logs/round1_multiseed.log).
