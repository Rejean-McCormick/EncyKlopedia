# Kristal v5 integration

**External normative authority:** Kristal v5 specification
**Pinned release:** `5.0.0-rc.1`

kOA does not duplicate Kristal schemas. It pins and references the Kristal release, then defines only ecosystem/deployment policy around those contracts. Kristal is the epistemic/knowledge artifact authority, not the transactional database authority for Orgo, Konnaxion or other products.

## Core semantic changes from the old kOA model

- Structured Epistemic State is the primary structured input.
- Claim-IR and Resolved Claim-IR are optional profiles/intermediate artifacts, not a universal pipeline.
- Compilation may produce a Working Exchange before final validation/recognition.
- Validation, certainty and authority recognition are independent axes.
- Reference Exchange means recognized reference under declared authority/scope, not universal truth.
- Runtime Packs preserve `source_artifact_status` and Reader Policy metadata.
- Validation must not be treated as a universal compile blocker.
- Product-owned mutable state enters Kristal only through immutable exports/snapshots or other explicit source artifacts with provenance.
- Runtime/query materializations may optimize consumption but remain derived and non-authoritative.

See `pinned-dependency.md`, `contract-pointers.md`, `koa-profile.md`, `conformance.md` and `legacy-compat.md`.
