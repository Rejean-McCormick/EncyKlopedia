# PROT-002 v1 — Cross-site preprocessing equivalence test

**Status:** current. **Synthetic demo protocol.**

## Objective
Determine whether five preprocessing pipelines produce analytically equivalent outputs from the same frozen synthetic input.

## Inputs
- DATA-001 v1.
- Five declared preprocessing pipelines.
- Frozen transformation dictionaries.

## Procedure
1. Run every pipeline against the same immutable input.
2. Log every transformation in order.
3. Compare missing-value handling, scaling, categorical recoding, and outlier treatment.
4. Re-run the primary summary model on each processed output.

## Primary comparison
Measure whether direction, magnitude, uncertainty interval, and sample retention remain materially consistent.

## Failure criterion
Pipelines are non-equivalent when one or more prespecified transformations materially change a headline conclusion or eligible sample composition.

## Outputs
- Transformation log.
- Equivalence table.
- Harmonized pipeline specification.

## Limitations
Equivalence under DATA-001 does not prove equivalence for every future dataset.

## Provenance
All outputs must retain links to the input dataset version and exact transformation sequence.
