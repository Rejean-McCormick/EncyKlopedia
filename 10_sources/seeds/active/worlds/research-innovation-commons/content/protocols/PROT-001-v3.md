# PROT-001 v3 — Harmonized blinded case definition

**Status:** current. **Synthetic demo protocol.**

## Objective
Apply one explicit NEX-27 classification rule across all sites while retaining clinically meaningful site metadata.

## Inputs
- PROT-001 v2 mapping.
- Frozen glossary DEF-001 through DEF-006.
- DATA-001 v1 synthetic harmonized cohort.

## Inclusion rule
A synthetic participant is a `case` only when all prespecified inclusion conditions are met. `Response` and `recovery` remain separate outcomes.

## Exclusion rule
Exclusions are applied before outcome classification and are recorded as reason codes; no silent deletion is allowed.

## Blinded procedure
1. Freeze the reference dataset and glossary.
2. Remove site labels from the classification worksheet.
3. Two independent classifiers assign case/recovery/response labels.
4. A third reviewer resolves only disagreements documented in the audit log.
5. Site metadata is restored after classification.

## Analysis
- Agreement is reported before adjudication.
- Residual site differences are analyzed after harmonization.
- Differences that survive harmonization are preserved as possible signal, not automatically labeled noise.

## Outputs
- Harmonized labels in DATA-001 v1.
- Adjudication log.
- Mapping from v1/v2 labels to v3.

## Limitations
Harmonization can remove semantic artifacts but can also hide meaningful local variation if used carelessly. Site metadata must therefore remain available.

## Reproducibility requirement
Any result using `case`, `response`, or `recovery` must cite `PROT-001:v3` explicitly.
