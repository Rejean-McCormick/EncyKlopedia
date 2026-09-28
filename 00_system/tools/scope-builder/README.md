# EncyKlopedia Scope Builder v0.8

## Purpose

Build project-specific, people-first evidence directly from the raw Wikidata dump without requiring a universal DB transformation first.

```text
people roots
   ↓
resolve
   ↓
scope discovery (auto/index/raw)
   ↓
freeze QIDs + roles
   ↓
04_extract_evidence.py
   ↓
complete selected Wikidata JSON
   ↓
UCKK candidates + Da'at handoff
   ↓
Kristal lifecycle
```

## Invariant

**Entity selection may be selective; entity evidence is not field-pruned.**

Once a QID is admitted, its whole Wikidata entity object is preserved. Qualifiers, references, literal values, sitelinks and external IDs are not dropped.

## Scripts

1. `01_resolve_roots.py` — explicit/cached QIDs first; then global index or raw dump.
2. `02_discover_scope.py` — people-centred scope discovery via optional global index or raw dump.
3. `03_freeze_scope.py` — immutable QID + role set.
4. `04_extract_evidence.py` — **default evidence path**: direct raw-dump scan for one or many scopes; no DB required.
5. `06_build_scope_index.py` — optional query-oriented project SQLite.
6. `07_publish_mediatheque.py` — candidates directly from lossless evidence.
7. `08_prepare_daat_handoff.py` — handoff directly from scope + evidence; project SQLite optional.
8. `09_status.py` — shows raw dump, optional global index and scope state.

Compatibility/cache scripts `04_fill_entity_vault.py` + `05_materialize_evidence.py` remain available, but the vault is no longer mandatory.

## Backends

`--backend auto` / `--discovery-backend auto` selects the completed global index if available, otherwise raw dump scanning. `raw` guarantees no dependency on the global compact SQLite. `index` explicitly requires it.

## Efficient multi-scope extraction

The expensive evidence pass can handle several frozen scopes at once:

```powershell
python -u .\00_system\tools\scope-builder\scripts\run_scope_pipeline.py `
  --root . `
  --scope catholic-pilot `
  --scope intellectuals `
  --discovery-backend auto
```

All requested scopes share one direct dump scan for evidence extraction.

## Optional DBs

`--build-query-index` builds `30_working/scopes/<scope>/index/<scope>.sqlite`. It preserves raw statements/qualifiers/references for querying, but it is **not** required by Da'at and is never a canon.

`--cache-vault` caches selected raw entities in `20_ingest/entity-vaults/`; this can save future rescans but is also optional.

## Interaction Kernel boundary

The handoff records `kristal.build.request/1.0.0` as the relevant IK profile candidate from the supplied kOA reference, but emits no IK protocol message. The exact IK runtime/contracts are not bundled here and the kOA docs require explicit Profile/version adoption and conformance evidence.
