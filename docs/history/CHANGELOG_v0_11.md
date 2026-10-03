# EncyKlopedia v0.11 — domain-neutral acquisition contract

## Architecture

- Scope Builder is now scope-rooted rather than universally people-first.
- `root_semantics.role` and `root_semantics.kind` are explicit scope policy.
- Generic `reverse_root_relations` replaces hard-coded reverse authorship in v3 scope configs; v2 keys remain backward-compatible.
- Existing intellectual scopes remain intentionally people-first.

## Referent candidates

- Added `07_publish_referents.py`.
- Emits a Kristal-shaped `referent_registry` candidate from immutable scope evidence.
- Source-qualified refs remain candidates until DaaT/Kristal mapping/acceptance.
- Added referent stage to the orchestrated pipeline.

## Documentary acquisition

- Médiathèque feed upgraded to `encyklopedia-mediatheque-candidate/v3`.
- Explicitly preserves `work != edition != manifestation/file`.
- Edition/provider/access/rights remain unresolved candidate metadata owned downstream by UCKK Médiathèque.

## Handoff contract

- Added frozen `encyklopedia.corpus-harvest-handoff/1.0.0`.
- Handoff upgraded to `encyklopedia-daat-handoff/v4`.
- Current pin: Kristal `5.0.0-rc.3`, Referent Registry `1.0.0`.
- Bundled Interaction Kernel is inspected, not silently modified or claimed as authoritative.

## Compatibility

- Existing v2 people-first scope keys remain accepted.
- No existing source evidence or Kristal artifact is rewritten.
- Global/project SQLite, vault and Fast Access remain optional derived accelerators.
