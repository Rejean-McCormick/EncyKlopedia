# Validation — EncyK 0.12.0

Validated on 2026-10-03 after the source-authority cleanup.

## Passing checks

- repository architecture validator: **PASS**;
- JSON parsing: **116 files PASS**;
- Python compileall over active tools/launchers: **PASS**;
- Scope Builder + Wikidata Manager pytest suite: **8 tests PASS**;
- end-to-end raw scope pipeline: **PASS**;
- non-person root scope: **PASS**;
- lossless qualifiers/references/external IDs: **PASS**;
- fast-access evidence path: **PASS**;
- optional project query index: **PASS**;
- external identity candidate generation: **PASS**;
- `encyk.source-evidence-handoff/2.0.0` schema validation: **PASS** when `jsonschema` is available;
- repeated source handoff generation is content-address stable: **PASS**.

## Architecture gates

The active repository contains no:

- `40_kristal/`;
- `50_mediatheque/`;
- `20_ingest/`;
- vendored `00_system/integrations/Interaction-Kernel/`;
- active legacy Kristal v5 contract pin;
- active legacy DaaT spelling.

The canonical source handoff targets Médiathèque kOA `>=0.2.0` / `koa.source-catalog/2.0.0` and deliberately does not encode downstream IK, DaaT, Kristal/Kristall or Kompiler versions.

Those downstream compatibility baselines remain documented separately in `00_system/contracts/knowledge-baseline.json`.
