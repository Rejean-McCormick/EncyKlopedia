# Migration v0.10 → v0.11

No rebuild of the Wikidata dump or global index is required.

Existing v2 scope files continue to work. The preferred v3 form adds:

```json
"root_semantics": {
  "role": "person_root",
  "kind": "person"
}
```

and renames the people-specific discovery keys:

```text
include_all_entity_relations_from_root_people
    → include_all_entity_relations_from_roots

include_reverse_authored_works + reverse_work_properties
    → reverse_root_relations
```

The bundled `catholic-pilot` and `intellectuals` configs have already been migrated.

For an existing frozen/evidence scope, rerun from the new `referents` stage if you only need the new candidate registry and handoff:

```powershell
python -u .\00_system\tools\scope-builder\scripts\run_scope_pipeline.py `
  --root . `
  --scope catholic-pilot `
  --from-stage referents `
  --through handoff
```

This does not modify `40_kristal`.
