# 20_ingest

Immutable acquisition/evidence boundary.

## v0.8

- `scope-snapshots/<scope>/<snapshot>/entities.wikidata.jsonl.gz` contains complete selected Wikidata entity objects extracted directly from the raw dump.
- `entity-vaults/` is an optional reusable cache, not a required stage.
- `daat-handoff/` points Da'at at frozen scope + immutable evidence; optional indexes are convenience artifacts only.

These are source/evidence artifacts. They do not imply Kristal validation or recognition.
