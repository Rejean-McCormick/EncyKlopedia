# Consumer interop: Authoring Kit 3.3.1 → Manager → Konstellation / Light

## Scope and ownership

The Local Kit **produces** optional, derived `kristal.discovery/1.0`,
`kristal.reader-inventory/1.0`, and `kristal.reader-profile/1.0` files.
The Kit does **not** inventory a host's fleet, authorize disclosure or
publication, choose a global reader, or perform remote discovery.

- **Kristal Manager** owns local operational inventory, identity collisions,
  availability and operator diagnostics. `reader-inventory.json` inventories
  *tracked artifacts inside one Kristal*, not the fleet.
- **Konstellation / My Kristals** consumes an authorization-filtered projection
  from Manager; its own `entries[]` view must not be treated as a substitute
  for Manager's `records[]` operational data. A consumer adapter is required.
- **Konstellation Explorer** may select a read strategy *after* independent
  permission, file-format, digest and size checks. A missing/unknown Arketype
  classification must never block generic access that is already authorized.
- **Konstellation-Light** may use a public, qualified projection, and must
  independently preserve its publication gate C4. Discovery is never approval
  for public distribution.
- **Arketype 1.4** classification describes design intent, not semantic proof,
  source credibility, execution authority or publication authorization.
- **EncyKlopedia/Skope** scope exploration is separate from the semantic
  `state_scope` and from derived Kristal reader discovery.

## Read-only audit protocol

```console
python tools/kristal.py audit-discovery ./My-Kristal --compact
python tools/kristal.py audit-discovery ./My-Kristal --require-fresh
```

The output `kristal.discovery-audit/1.0` (schema: `schemas/kristal-discovery-audit.schema.json`) is a **transient diagnostic** (not an
additional persisted manifest). It contains:

- `status`: `fresh`, `stale`, `invalid`, `incomplete` or `absent`;
- `usable_as_reader_hint`: true **only** for a verified fresh set;
- `issues`: stable, intentionally minimal diagnostic codes;
- `authorization`: always `not_evaluated_no_access_or_publication_grant`;
- on `fresh` only: `state_ref`, suggested `reader_profile`, tracked file count.

An absent set is valid for a legacy Kristal; readers fall back to a guarded
specialization-neutral approach. `--require-fresh` exits with code 2 unless
status is `fresh`. An audit never changes the workspace, walks remote targets,
or authorizes file access. Consumers MUST still apply their own ACL, size,
digest, symlink/path, decompression, and resource limits when opening payloads.
A successful audit is not an integrity signature or C2/C4 qualification.

The consumer can consume actual `kristal.discovery.json` and its `hints_ref`
/ `inventory_ref` only after resolving these *fixed relative paths* within the
permitted Kristal root, verifying the same state reference and matching source
fingerprints across all three, and enforcing the caller's access policy. Do
not blindly expose inventory file paths, digests, materialization locators or
local diagnostics in My Kristals or public Light.

## Compatibility checklist

- Unclassified legacy Kristal: `absent`; generic read allowed only by consumer policy.
- Complete, current derived set: `fresh`; hints only, never executable config.
- Missing single derived file: `incomplete`; regenerate locally.
- Edited profile/digest or changed canonical bytes: `invalid`/`stale`;
  refuse specialization until refreshed and checked.
- Manager maintains operational inventory identity and state separately;
  never join hosted/local Kristals only by slug/title.
- Kit v9 Logical/State Commitments and workspace v3.2 envelopes are unchanged.

For local snapshot upgrade cleanup see [Cleaning obsolete snapshot indexes](25_NETTOYAGE_LOCAL.md).
