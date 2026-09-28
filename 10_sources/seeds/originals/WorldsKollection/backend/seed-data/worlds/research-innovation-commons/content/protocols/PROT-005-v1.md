# PROT-005 v1 — Subtype stratification analysis

**Status:** current. **Synthetic demo protocol.**

## Objective
Test whether pooled heterogeneity becomes more coherent when prespecified synthetic subgroups are analyzed separately.

## Inputs
- DATA-004 v1.
- PROT-001 v3 harmonized phenotype labels.
- Prespecified subgroup variables.

## Procedure
1. Freeze subgroup definitions before outcome comparison.
2. Estimate the shared signal in the pooled cohort.
3. Repeat within each subgroup.
4. Compare effect direction and uncertainty.
5. Flag subgroups with insufficient synthetic sample support.

## Guardrail
Do not create new subgroups after inspecting the desired outcome and then report them as confirmatory.

## Outputs
- Subtype-stratified summary.
- Heterogeneity note.
- Candidate follow-up questions.

## Limitation
Improved fit after stratification does not by itself establish distinct biological diseases.
