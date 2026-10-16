# EncyK v0.14.0 clean rebuild — validation

Source baseline: uploaded full EncyK `znapshot_EncyKlopedia_10141405.zip`
(version 0.13.17); reconstructed from that snapshot, with integrated Skope
removed. Earlier 0.13.22 changes to Skope itself are now owned by the separate
Skope Standalone repository and deliberately not included.

- No `00_system/tools/skope/`, `Lancer_Skope.pyw` or embedded Skope package.
- No code imports `skope.*` within the active EncyK runtime.
- EncyK Wikidata Manager has a pull-only Skope External GUI tab.
- Local HTTP bridge only accepts loopback URLs, follows no redirects, validates
  completed job, validates QID sort/uniqueness/count, validates ZIP filenames,
  checksum and byte/entry limits; returns immutable noncanonical intake.
- `encyk.source-evidence-handoff/2.0.0` still accepted; permitted producer
  release list extended with 0.14.0 (not changed to a new contract).
- Wikidata SQLite, dump, random-access sidecars and Kristals remain on D:
  or in their own repositories; not copied, rebuilt, indexed or modified here.
- The cleaner protects source evidence and does not target the new import area.

Commands:

```powershell
python -B 00_system/tools/validate_repo.py
python -m pytest -q 00_system/tools/scope-builder/tests 00_system/tools/wikidata-manager/tests 00_system/tools/data_cleaner/tests 00_system/tools/migration/tests 00_system/integrations/tests
```

## Results (container, Python 3.13)

- 29 tests passed, 5 subtests passed, across Scope Builder, Wikidata Manager,
  Data Cleaner, migration and the external Skope bridge.
- Fast CI: PASS — architecture validator, 114 JSON files parsed,
  44 Python files syntactically checked, 16 critical tests passed.
- Previously supplied real Skope result archive `skope-b669d969-results.zip`
  passed integrity validation with **16,299** selected QIDs (read-only).
- Small mocked HTTP server tested completed import, re-import idempotence,
  incomplete-job refusal, invalid paths/duplicate QIDs, provenance and ZIP checks.
- Windows-specific GUI / live 125 GiB SQLite / Skope server interoperability
  has **not yet been run against the user's PC**.
