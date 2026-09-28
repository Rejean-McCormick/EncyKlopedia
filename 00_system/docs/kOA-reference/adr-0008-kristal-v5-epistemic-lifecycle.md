# ADR-0008: Kristal v5 epistemic lifecycle and stage-specific gates

- **Status:** Accepted
- **Date:** 2026-09-16
- **Supersedes:** ADR-0001 Truth Boundary
- **Scope:** kOA interpretation of Kristal v5 lifecycle; does not redefine Kristal schemas

## Context

The former kOA model treated Kristal as a single truth boundary and required validation success before compilation. Kristal v5 explicitly separates compilation, validation, certainty, authority recognition, reference status, publication and activation.

## Decision

1. Structured Epistemic State is the primary structured Kristal input.
2. Claim-IR/Resolved Claim-IR are optional profile/intermediate artifacts.
3. A Working Exchange may be compiled before final validation or recognition when policy permits.
4. Validation failure/rejection does not universally erase or prohibit Working artifacts.
5. Reference Exchange status requires the applicable recognition path.
6. Runtime Packs preserve source artifact status and Reader Policy references.
7. kOA Build Records keep compile, validation, recognition, publication and activation statuses separate.
8. kOA may define stricter **stage-specific** gates for reference publication/distribution/activation, but must label them as kOA/deployment policy rather than Kristal core semantics.

## Consequences

The terms “canonical truth”, “truth plane”, “truth boundary” and universal “no compile on fail” are removed from active normative kOA documentation when they refer to Kristal v5 status.
