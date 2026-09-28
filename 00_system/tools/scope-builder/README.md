# EncyKlopedia Scope Builder v0.11

## Purpose

Build project-specific, **scope-rooted** evidence directly from the raw Wikidata dump without requiring a universal DB transformation first.

A scope chooses its own root semantics. Existing intellectual scopes remain people-first, but the engine is not universally people-first.

```text
configured roots
   ↓
resolve source identities
   ↓
scope discovery (auto/index/fast/raw)
   ↓
freeze QIDs + domain roles
   ↓
04_extract_evidence.py
   ↓
complete selected Wikidata JSON
   ├── 07_publish_referents.py
   ├── 07_publish_mediatheque.py
   └── optional query index
   ↓
08_prepare_daat_handoff.py
   ↓
Da'at → Kristal lifecycle
```

## Invariants

**Entity selection may be selective; entity evidence is not field-pruned.**

Once a QID is admitted, its whole Wikidata entity object is preserved. Qualifiers, references, literal values, sitelinks and external IDs are not dropped.

**Root semantics belong to the scope.** A scope can declare, for example:

```json
"root_semantics": {
  "role": "person_root",
  "kind": "person"
}
```

or:

```json
"root_semantics": {
  "role": "installation_root",
  "kind": "installation"
}
```

The supported shallow referent kinds follow the frozen Kristal Referent Registry profile. Domain ontologies remain extensions; the Scope Builder does not invent a universal taxonomy.

## Discovery configuration v3

Preferred keys:

- `discovery.include_all_entity_relations_from_roots`
- `discovery.reverse_root_relations`
- `discovery.root_relation_roles`
- `discovery.follow_rules`

Example reverse relation:

```json
"reverse_root_relations": {
  "P50": {
    "source_role": "work",
    "relation_role": "authored_work"
  }
}
```

Legacy v2 keys (`include_all_entity_relations_from_root_people`, `include_reverse_authored_works`, `reverse_work_properties`) remain accepted for compatibility.

## Scripts

1. `01_resolve_roots.py` — explicit/cached QIDs first; then global index or raw dump.
2. `02_discover_scope.py` — domain-configured root discovery.
3. `03_freeze_scope.py` — immutable QID + role set.
4. `04_extract_evidence.py` — direct lossless source extraction; no project DB required.
5. `06_build_scope_index.py` — optional query-oriented project SQLite.
6. `07_publish_referents.py` — source-qualified candidate Referent Registry.
7. `07_publish_mediatheque.py` — work/document candidates; work/edition/manifestation are not collapsed.
8. `08_prepare_daat_handoff.py` — frozen content-addressed handoff to Da'at.
9. `09_status.py` — raw dump, accelerators and scope state.

Compatibility/cache scripts `04_fill_entity_vault.py` + `05_materialize_evidence.py` remain optional.

## Backends

`--backend auto` / `--discovery-backend auto` selects the completed global index if available, then fast random access when available, otherwise raw dump scanning.

- `index` — require the completed compact SQLite.
- `fast` — require random-access locator/compression support.
- `raw` — scan the raw dump.

All indexes remain derived accelerators, never epistemic sources.

## Candidate referents

`07_publish_referents.py` emits a Kristal-shaped **candidate registry** under:

```text
20_ingest/referent-registries/<scope>/
```

Refs such as `wikidata:Q8018` are source-qualified candidate identities. Da'at/Kristal owns canonical mapping/acceptance.

## Médiathèque boundary

`07_publish_mediatheque.py` emits documentary candidates only. It explicitly preserves:

```text
work ≠ edition ≠ manifestation/file
```

UCKK Médiathèque remains authoritative for final edition, provider, access and rights resolution.

## Frozen handoff

`08_prepare_daat_handoff.py` emits:

`encyklopedia.corpus-harvest-handoff/1.0.0`

The compatibility pin is stored in `00_system/contracts/knowledge-baseline.json`.

Interaction Kernel is a transport boundary only. The bundled IK snapshot is inspected for compatible profiles; EncyKlopedia does not fabricate conformance or write directly into `40_kristal`.
