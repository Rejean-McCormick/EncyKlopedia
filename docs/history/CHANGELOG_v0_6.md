# v0.6 — People-first Wikidata harvest + Kristal handoff

- Added `00_system/tools/encyklopedia-kristal-ingest/`.
- Added people-first extraction from the local Wikidata SQLite index.
- Added authored-work discovery via reverse `P50` plus direct `P800` notable works.
- Added intellectual currents (`P135`), political ideologies (`P1142`), fields (`P101`) and influence (`P737`).
- Added candidate feed for UCKK Médiathèque without claiming catalogue authority.
- Added immutable content-addressed source snapshots under `20_ingest/snapshots/encyklopedia/`.
- Added DaaT handoff manifests under `20_ingest/handoffs/kristal/`.
- Added optional probe of the pinned Kristal v5 repository; no Kristal schema is reimplemented.
- Added `run_kristal_ingest.pyw`, `harvest_to_kristal.ps1`, and a `Harvest → Kristal` button in the Wikidata Local Manager.
- Tests cover people, works, currents, Mediatheque candidates, snapshot and handoff generation.
