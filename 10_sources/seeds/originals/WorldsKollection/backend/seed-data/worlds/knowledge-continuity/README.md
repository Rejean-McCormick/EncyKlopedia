# World 6 — Knowledge Continuity

Drop-in Konnaxion World pack. Copy the `backend/` tree into the Konnaxion repository.

## Core promise

If a critical expert becomes unavailable tomorrow, can the organization still perform the capability safely and explain why?

The canonical object is a **capability**, not a course, document, or score. Capability continuity moves through explicit states:

`at_risk → capturing → successor_identified → supervised_practice → validating → covered`

A capability becomes **covered** only after independent practice, evidence, and peer validation.

## Runtime boundary

The current Worlds builder automatically validates/imports the declared `ethikos-demo-scenario/v3` scenario. That scenario provides the shared personas, EkoH demo profiles, and Korum Case Clinics.

The `canon/` and `modules/` files use `konnaxion-world-module-bridge-seed/v1`. They are **declarative bridge seeds**, aligned to current native Konnaxion models, but the supplied Worlds builder does not yet auto-import them. This distinction is intentional and explicit in `world.yaml`.

## Cross-module invariant

Stable actor, capability, case, evidence, project, and certification keys are reused across the pack. Canonical cases now carry direct cross-links to Stockage evidence, Knowledge resources, Korum clinics, Konstruct transfer projects, CertifiKation paths, and Konservation archive items.

## Deliberate exclusions

- No Smart Vote readings.
- No Konsultations ballot.
- No expert leaderboard.
- No quiz-only certification.
- No duplicated Knowledge/Stockage/Konservation content semantics.
- No claim that an AI clone replaces a departing expert.

## Content size

- 3 critical capabilities
- 20 fictional personas
- 15 cases
- 25 evidence assets
- 12 Knowledge resources
- 3 transfer projects
- 3 certification paths
- 6 preservation/archive stories
- 3 Korum Case Clinics

## v1.1 optimizations

- all 20 personas have a concrete role in the World flow;
- Ana Pereira owns historical data extraction, Victor Chen operational practice scheduling, and Zoé Martel validated playbook publication;
- capability lifecycle and next gates are explicit;
- Konstruct tasks are structured and use native project/task/team enums;
- native model fields are separated from World linkage metadata;
- each canonical Case exposes cross-module references instead of relying on implicit matching.
