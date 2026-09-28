# PROT-001 v1 — Site-local case definition baseline

**Status:** superseded. **Synthetic demo protocol.**

## Objective
Capture the five sites' original NEX-27 case rules before harmonization so later changes are reconstructible.

## Inputs
- Site-local symptom inventory.
- Site-local time window.
- Site-local exclusion rules.
- Local labels for `case`, `response`, and `recovery`.

## Procedure
1. Each site applies its existing rule without translation.
2. A data steward records each rule verbatim.
3. Sixty synthetic reference cases are classified independently.
4. Disagreements are retained rather than reconciled.

## Analysis
Report pairwise agreement and list cases whose classification changes between sites. Do not pool labels as if they were equivalent.

## Outputs
- Frozen site-local definitions.
- Classification matrix for the 60 synthetic cases.
- Disagreement inventory feeding PROT-001 v2.

## Limitations
This version intentionally preserves incompatibility. Its classifications must not be treated as a harmonized phenotype.

## Version note
Baseline only; replaced by v2 mapping after semantic differences were identified.
