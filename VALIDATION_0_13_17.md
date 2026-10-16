# v0.13.17 — Fast-reader preflight hotfix

- `Check sources` re-probes `indexed_bzip2` *inside the Skope server process*, correcting a cached missing optional dependency after installation.
- Detailed backend, Skope Python interpreter, file presence and import failure are included in the preflight report when blocked.
- Never scans the dump, rebuilds the locator, changes SQLite, or modifies Kristal canon.
- Tests: `test_reader_reprobe.py` plus full Skope regression, Scope Builder and repository validator.
- Real Windows 96 GiB dump and 2 GiB locator not available in test environment; check on user's machine.
