# Kristal Local Kit 3.2.5-rc.1 — V10 harmonization verification

**Scope:** Maintenance candidate prepared from the 2026-10-12 `Kristal-Authoring-Kit` snapshot (3.2.4) and the inter-repository harmonization plan A-01 through A-05.

## Checked changes

- Reader paths and file roles are confined to the allowed local reader roots; symlink traversal outside the workspace is rejected.
- Readiness requires actual file size **and** SHA-256 to match AI index metadata; duplicate/unsafe paths are rejected.
- Portable AI entrypoint/manifest fields cannot redirect the validator to arbitrary paths.
- Disabled optional AI does not make a stale, explicitly inspected reader projection valid.
- Missing/external materialization locators remain explicitly reported and are never downloaded by the Kit.
- A migration audit CLI compares two separate workspaces without changing files; missing comparable State Snapshots result in `NOT_FULLY_QUALIFIED` (nonzero CLI status).
- The v9 Logical Artifact and State Commitment functions and serialized contract identifiers remain unchanged.
- The snapshot's original demo workspaces and their historical derived content remain untouched.

## Validation methods

1. Python syntax checks of `tools/kristal.py`, the migration audit and new tests.
2. Legacy unit tests + new regression tests (`python -m unittest discover -s tests -v`).
3. Independent check against `profiles/github/schemas/kristal-github-read-surface.schema.json` from the supplied Kristal Framework `10.0.0-draft.3.1` snapshot using `jsonschema` Draft 2020-12: **zero schema errors** for a newly generated candidate read surface.
4. Existing shipped demo workspace checks and deterministic ZIP builds, where executed.
5. SHA-256 inventory of the final release package.

The 3.2.5-rc.1 candidate **is not an official stable v10 release**, a committed GitHub revision or proof that the `kristal-public` C3 collection, Manager runtime, C1/C2 grants, or readers are integrated end-to-end. The current snapshot of Manager remains incomplete and the public collection is not established as qualified.

## Deployment restrictions

Do not overwrite the 126 original workspaces or their bundled Kit versions automatically. Use copies, compare State Commitments and canonical bytes, obtain independent qualification for the exact revision, and enforce disclosure/owner consent before writing anything to public GitHub collections.

## Human review still required

- Agree on a single exact Framework contract set/commit SHA and Kit consumer compatibility pin.
- Review changed read-surface behavior with the Manager and C3 owners.
- Perform an authorized private staging pilot through the full chain. No hosting, remote write, publication or activation is performed by this package.
