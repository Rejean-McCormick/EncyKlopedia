# Architecture — EncyKlopedia 0.1.0-alpha.1

## Boundary map

```text
External sources
   |
Skope + EncyK  [research/acquisition, noncanonical evidence]
   |
Médiathèque kOA  [durable source and snapshot authority]
   |
Kristal Framework / Authoring Kit [semantic identity, validation, approved state]
   |
Kristal Integration Pack [read-only derived v11 reading view; not publication]
   |
  [FUTURE: independent, authorized C2/C4 PUBLICATION BOUNDARY]
   |
  [FUTURE: immutable public artifact + search indexes + CDN/object storage]
   |
EncyKlopedia [read-only public website, search and API]
```

Konstellation is a parallel *interactive exploration* consumer of qualified data; EncyKlopedia is the general public encyclopedia delivery surface. They may share approved read projections, but neither grants semantic authority, and one must not reimport the other's display pages as canonical evidence.

## Current implementation

The alpha provides a runnable local Node.js reader of **synthetic fixtures only**. The demonstration validates a local `encyklopedia.publication-bundle/0.1.0` envelope. It neither reads real Integrated Pack output nor consumes real Wikidata, GitHub source repositories, production article storage or a real content-management database.

The local reader bundle is an **application draft contract**. Kristal Framework v11 remains the only normative owner of KQ/KP/KA/KS identifiers, source binding and lexical validation. The demo's `semantic_id` has a fake `demo:` prefix by design.

Security baseline:
- local loopback binding only, no public-network mode;
- synthetic-demo-only validation and no content ingestion route;
- HTTP GET/HEAD only; no mutation endpoints, wildcard CORS, or filesystem traversal;
- bounded search and narrow slug routing;
- content rendered as text via DOM APIs; no user-supplied HTML;
- `no-store` responses, browser security headers, no analytics.

## Future non-negotiable properties

1. **C1:** pin implementation/code and normative contract revisions by digest.
2. **C2:** verify source owner, licensing, privacy/redaction and unambiguous public scope; no private or experimental workspace leakage.
3. **C3:** verify publication materialization, references, integrity, reproducibility and rollback.
4. **C4:** separately approve public publication and profile-specific disclosure, never infer release authorization from a derived reading view.
5. **Identity:** never mint or silently rewrite KQ, KP, KA or KS identifiers for convenience.
6. **Multilingual:** preserve provenance and actual locale coverage; fallback is visible, never claimed as a direct translation.
7. **Scale:** use partitioned read services, indexes, object storage, cache/CDN and operations appropriate to traffic. GitHub stores code/governance, not bulk content.
8. **Trust:** reject unknown profiles, versions, digests and incomplete source artifacts; do not turn an API response into an authority declaration.

## Source alignment used for this starter

- `Kristal Framework` snapshot: `11.0.0-draft.4` (normative semantics).
- `Kristal Integration Pack` snapshot: `0.3.0-alpha.1`, derived view `kristal.integration.read-view/v11.0-draft.1`.
- `Konstellation` snapshot: `1.0.0-rc.2`, separate navigation responsibility.
- `Skope` + `EncyK` integrated code snapshots, separate upstream source processing.

These are **reference baselines**, not a tested live end-to-end production deployment. No adapter or contract is presumed ratified beyond what the individual sources establish.
