# Skope v0.13.16 — Full extraction validation

- Unit fixtures: preflight, verified-vs-unverified source, absent fast sidecar, explicit confirmation, lossless JSON and SHA-256 snapshots, missing QID and resume.
- HTTP endpoint and browser UI tests on small fixture index; **not** executed on the user's 96 GiB dump or Windows installation.
- Failure modes are reported as blockers. Full-dump scans and new-index creation are not supported by this route.
- The v0.13.15 density map and large QID results controls remain present.

### Executed in this container
- Skope: **51 unit/integration tests passed** (including fake-source end-to-end, resume, identity fail-closed, HTTP security).
- Scope Builder: **5 tests passed**.
- EncyK `validate_repo.py`: **PASS**.
- Chromium (mock API): preflight -> Start -> modal -> completed progress and original UI controls.
- Windows clipboard / Explorer and actual 96 GiB dump: **not tested here**.
- Expected first run on D: may show a blocker if the installed `indexed_bzip2` backend, pre-existing sidecars, verified manifest or free disk cannot be confirmed. Do not bypass it.
