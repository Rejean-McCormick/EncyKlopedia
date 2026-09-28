# PROT-004 v1 — KX-17 batch-effect challenge

**Status:** current. **Synthetic demo protocol.**

## Objective
Quantify how much KX-17 measurement changes when batch conditions vary while the synthetic reference material remains fixed.

## Inputs
- DATA-003 v1.
- Frozen reference samples.
- Declared batch-condition matrix.

## Procedure
1. Randomize reference samples across batches.
2. Change one declared batch condition at a time where possible.
3. Measure the same synthetic reference repeatedly.
4. Record calibration and instrument metadata.
5. Fit the prespecified batch-effect model.

## Primary outcome
Fraction of apparent KX-17 variation attributable to batch rather than reference-sample identity.

## Outputs
- Batch-effect estimate.
- Recalibration requirements.
- Measurement limitation note attached to historical KX-17 results.

## Limitation
This protocol identifies measurement instability; it does not identify the biological meaning of KX-17.
