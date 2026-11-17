# Skope/EncyK 0.14.0 → Médiathèque engine 0.5.1

## Engine versus libraries

`mediatheque/` is the single common engine. An instance such as
`mediatheque-privee/`, `mediatheque-uckk/` or `mediatheque-math/` owns its own
configuration and files. **No existing instance is auto-selected.**

This adapter handles **private local SQLite/filesystem** instances only. Moodle
or other remote instance backends need their own approved adapter; pointing
`--instance-root` at a Moodle instance does not import into Moodle.

## Contract verification

The schema embedded under
`koa_mediatheque/contracts/encyk_source_handoff_2/schema.json` is byte-identical
to `encyk/00_system/contracts/source-evidence-handoff/2.0.0/schema.json` from
Skope snapshot `znapshot_Skope_10270842.zip`, 2026-10-27:

`SHA-256: 90086656ea04e2bc012dda5bd95d8ff7b075bb08d1a7bd580fd339d50a0a2428`

The contract name and version remain `encyk.source-evidence-handoff/2.0.0`.
Producer versions including `0.12.0` and `0.14.0` are accepted only as permitted
by this exact schema. Unknown future versions fail closed.

## Procedure — local private instance only

First create or select an **existing** instance with an initialized
`01_DB/koa_mediatheque.sqlite` and `02_STORAGE/` directory. Do not extract
this Engine ZIP into an instance, and do not point it at raw data on `D:`
without deliberate review.

Example from the Engine checkout, adjusting paths to your machine:

```powershell
# Read-only plan, before import. Use the EncyK checkout/root holding evidence.
py -3 05_TOOLS/ImportEncyKHandoff.py `
  --handoff "D:\EncyKlopedia\20_evidence\handoffs\mediatheque\pilot\handoff-XXXXXXXXXXXXXXXXXXXX.json" `
  --evidence-root "D:\EncyKlopedia"

# Explicit acceptance into ONE selected private local library (not UCKK or Math).
py -3 05_TOOLS/ImportEncyKHandoff.py --accept `
  --handoff "D:\EncyKlopedia\20_evidence\handoffs\mediatheque\pilot\handoff-XXXXXXXXXXXXXXXXXXXX.json" `
  --evidence-root "D:\EncyKlopedia" `
  --instance-root "C:\mycode\mediatheque-privee" `
  --receipt-out "C:\mycode\mediatheque-privee\03_IMPORTS\encyk-receipt.json"
```

The paths above are **examples**, not claims that your instance has these
locations. The producer must have prepared a real handoff first. Plan does not
write; accept checks a pre-existing database and storage directory. Explicit
`--db` and `--storage` are still supported, but cannot be combined with
`--instance-root`.

Each imported source, snapshot and stored representation receives durable local
identifiers. Rights default to private, public export to no; no KQ/KP/KA/KS
are issued. Re-import is idempotent and rechecks the stored bytes. In the
current snapshot, tests use synthetic evidence; actual Windows/D: and producer
handoffs remain to be qualified separately. No signature authenticates the
handoff ID; human approval of the evidence root remains mandatory.

The UCKK external-instance bootstrap tests require a separate, real sibling
`mediatheque-uckk/` with inventory; they cannot pass from the engine snapshot
alone. Do not fabricate that data to make those tests green.
