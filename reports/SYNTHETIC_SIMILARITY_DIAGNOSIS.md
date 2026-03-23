# Synthetic Similarity Diagnosis

Nearest-neighbor similarity diagnostics for the synthetic `BindingDB_Kd` reference panel.
Drug-cold splits use exact Morgan-fingerprint Tanimoto and Bemis-Murcko scaffold overlap.
Target-cold splits use nearest global sequence identity after a hashed-kmer shortlist.

## `unseen_drug`

- Drug nearest Tanimoto: `0.7732 ± 0.0023` median, `1.0000 ± 0.0000` p90
- Drug high-similarity rates: `>=0.8` = `0.4360 ± 0.0064`, `>=0.9` = `0.1998 ± 0.0019`
- Murcko scaffold match rate: `0.6204 ± 0.0080`

## `unseen_target`

- Target nearest identity: `0.3835 ± 0.0456` median, `0.9446 ± 0.0454` p90
- Target identity rates: `>=0.4` = `0.4935 ± 0.0180`, `>=0.6` = `0.3876 ± 0.0243`, `>=0.8` = `0.2293 ± 0.0393`

## `blind_start`

- Drug nearest Tanimoto: `0.5333 ± 0.0538` median, `0.8558 ± 0.0442` p90
- Drug high-similarity rates: `>=0.8` = `0.1995 ± 0.0859`, `>=0.9` = `0.0690 ± 0.0439`
- Murcko scaffold match rate: `0.3512 ± 0.0435`
- Target nearest identity: `0.4029 ± 0.0642` median, `0.9096 ± 0.0273` p90
- Target identity rates: `>=0.4` = `0.4998 ± 0.0307`, `>=0.6` = `0.3581 ± 0.0214`, `>=0.8` = `0.1733 ± 0.0216`
