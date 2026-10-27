# Upstream contract snapshots

Konstellation keeps immutable copies of the upstream contracts it validates at its integration boundary.

- `structured-epistemic-state.schema.json` — Kristal v5 compatibility surface used by the legacy SES importer.
- `runtime-pack-manifest.schema.json` and `reader-policy.schema.json` — Kristal v5 compatibility surfaces used by Runtime Pack adapters.
- `kristal-state-v6.schema.json` — copied unchanged from the supplied `kristal-framework` snapshot, `docs/Technical-Reference/kristal-docs-v6/02-schemas/kristal-state.schema.json`. This is the canonical v6 state shape used by the direct v6 reader.

Schema validation is not epistemic validation, authority recognition, signature verification, or permission to act. In v6, Konstellation treats `kristal_state` as canonical and its own query packs, timelines, pathways and navigation projections as rebuildable derived views.
