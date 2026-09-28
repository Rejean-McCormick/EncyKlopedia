# Layer 05 — Validation / Reference

**Layer status:** Conceptual layer  
**Normative for Kristal contracts:** NO — Kristal v5 is normative.

> Historical name: “Validation / Canon”. The active model uses validation, authority recognition and reference status as separate concepts.

## Function

This layer explains how kOA evaluates structured epistemic material, records review/validation outcomes, applies authority recognition and determines eligibility for reference publication or downstream use.

It does **not** create truth by assertion and does not use a universal validation-before-compile gate.

## Active lifecycle

```text
Structured Epistemic State
  -> Working Exchange
  -> validation / review
  -> authority recognition
  -> Reference Exchange (when recognized for declared scope)
  -> policy-governed publication / Runtime Pack / consumption
```

Claim-IR / Resolved Claim-IR may appear in extractor/resolver Profiles but are optional.

## Core distinctions

Keep separate:

- compilation status;
- assertion status;
- certainty;
- validation status;
- `validated_as`;
- authority channel/scope;
- recognition status;
- publication status;
- activation status.

## Gating

Kristal v5 validation is **not** a universal compile blocker. kOA production Profiles may require validated and/or recognized material before:

- Reference Exchange publication;
- distribution;
- reference-only consumption;
- Runtime Pack activation.

Those requirements are explicit policy gates.

## Failure behavior

A failed/rejected/unfinished validation can make an artifact ineligible for reference publication while leaving a Working Exchange available for diagnosis, research or review under an eligible Reader Policy.

Feedback creates new governed work or new versions; it does not mutate published reference artifacts in place.
