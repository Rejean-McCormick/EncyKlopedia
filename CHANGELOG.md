# Changelog

## 0.12.0 — 2026-10-03

- Reduces EncyK to `discover → acquire → extract → handoff`.
- Makes Médiathèque kOA `0.2.0` / `koa.source-catalog/2.0.0` the canonical persistent source authority.
- Replaces the old DaaT/Kristal corpus handoff with `encyk.source-evidence-handoff/2.0.0` targeting Médiathèque.
- Removes active `40_kristal` and `50_mediatheque` zones.
- Removes Kristal-shaped candidate Referent Registry publication and replaces it with consumer-neutral external identity candidates.
- Removes the built-in documentary/media candidate catalog; complete source evidence remains available to the source authority.
- Removes the vendored Interaction Kernel snapshot and stale Kristal v5 reference documentation.
- Aligns ecosystem metadata to Interaction Kernel `2.0.0-dev.2`, DaaT/`daat`, portable `kristal_state/6.0`, Kristal/Kristall `7.0.0-draft.3.2`, Médiathèque `0.2.0`, and Kompiler `0.5.0`.
- Moves `20_ingest` to `20_evidence` and optional entity-vault cache authority to `30_working`.
- Renames Kristal-specific launchers to generic harvest commands.

Historical pre-0.12 plans/changelogs are under `docs/history/`.
