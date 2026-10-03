# Migration 0.11 → 0.12

0.12 is an architecture cleanup aligned with Médiathèque `0.2.0`, Interaction Kernel `2.0.0-dev.2`, DaaT, Kristal/Kristall `7.0.0-draft.3.2` and Kompiler `0.5.0`.

## Removed active responsibilities

- `40_kristal/` — EncyK no longer stores Kristal lifecycle outputs.
- `50_mediatheque/` — EncyK no longer maintains a mini-Médiathèque candidate catalog.
- candidate Kristal Referent Registry publication.
- direct EncyK → DaaT/Kristal handoff.
- vendored Interaction Kernel snapshot and frozen v5 reference documentation.

## New pipeline

```text
resolve → discover → freeze → evidence → [optional index] → identities → handoff
```

`handoff` now means **Médiathèque source-evidence handoff**.

## Data paths

- `20_ingest/` → `20_evidence/`.
- optional entity-vault cache moves to `30_working/entity-vaults/`.
- source handoffs are written to `20_evidence/handoffs/mediatheque/`.

Existing accepted source bytes should be migrated into Médiathèque, not copied into a new EncyK-owned catalog.

## Existing data on D:

Before running `configure_data_on_D.ps1` against an existing installation:

1. rename or move `D:\EncyKlopedia\20_ingest` to `D:\EncyKlopedia\20_evidence`;
2. keep any historical `40_kristal` artifacts with the Kristal repository/archive rather than relinking them into EncyK;
3. import any still-useful `50_mediatheque` candidate/source bytes into Médiathèque kOA before deleting the old workspace;
4. rerun `configure_data_on_D.ps1 -Apply` to create the new junction set.

Do not delete historical source bytes merely because the EncyK zone was removed; first establish their durable Médiathèque representation and integrity record.
