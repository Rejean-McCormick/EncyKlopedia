# Validation report

Validated on 2026-09-14 against the provided Konnaxion_Worlds, Orgo_Worlds and Kristal Framework v5.0.0-rc.1 snapshots.

## Passing gates

- repository JSON Schemas/Profile schemas: PASS;
- Kristal consumer lock and schema-set digest: PASS;
- Kristal RFC 8785 JCS vectors: 9/9 PASS in Python and TypeScript;
- IK semantic fingerprint vectors: 3/3 PASS in Python and TypeScript;
- Python admission/idempotency tests: PASS;
- TypeScript admission/idempotency tests: PASS;
- Konnaxion existing `validate_publish_request()` compatibility for `accountability.impact.publish`: PASS;
- TypeScript Orgo reference adapter static typecheck: PASS;
- Markdown relative links: PASS.

## Pinned upstream

Kristal Framework `5.0.0-rc.1` / tag `v5.0.0-rc.1` / commit `af703bf02ee04a69a5f2ad6694fa8b8e56ae2b19`.

## Not yet claimed

This repository does not claim that the reference adapters have already been merged into the authoritative Konnaxion, Orgo, Da’at/kOA-Linux repositories. They are integration-ready boundaries validated against the supplied snapshots. Full product-level integration still requires applying those adapters in the authoritative repositories and running each product's native CI/database migration suites.
