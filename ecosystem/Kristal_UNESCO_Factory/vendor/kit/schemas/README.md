# Local Kit schemas

These schemas describe **authoring envelopes and derived readers**. They are not replacements for the normative Kristal Framework's v9/v10 schemas or domain Logical Contracts.

| Schema | Responsibility |
| --- | --- |
| `workspace.schema.json` | Local 3.2 envelope with v9 semantics, optional derived AI and v10 hosting target |
| `kristal-classification.schema.json` | Optional noncanonical Arketype design identity and usage |
| `kristal-discovery.schema.json` | Lightweight root discovery manifest for readers |
| `kristal-reader-inventory.schema.json` | Tracked local file size/digest and materialization segments |
| `kristal-reader-profile.schema.json` | Advisory reader specialization and parser candidates |
| `state-index.schema.json` | Canonical v9 Logical Artifact and pinned reference index |
| `source-catalog.schema.json` | Source provenance and local source catalog |
| `projection-recipe.schema.json` | Noncanonical portable view recipes |
| `portable-ai-manifest.schema.json` | `kristal.portable-ai/1.0` derived AI capsule |
| `ai-index.schema.json` | Reader files with roles, sizes and SHA-256 digests |
| `ai-coverage.schema.json` | Owned/external coverage and explicit limitations |
| `github-read-surface.schema.json` | `kristal.github-read-surface/1.0` exact derived projection for Manager |
| `github-hosting.schema.json` | Optional operational GitHub host binding |
| `kristal-materialization-manifest.schema.json` | Local copy of the v9 Materialization Manifest schema |
| `kristal-v9-capabilities.schema.json` | Local copy of v9 physical representation capabilities |

**Important:** a read-surface file-list digest, a Git SHA and a transport Blob Digest are not a v9 Logical/State Commitment. `ai/` and collection indexes are derived. A valid schema or SHA-256 does not independently qualify domain truth or authorize public upload.

- `kristal-discovery-audit.schema.json`: transient read-only compatibility diagnostic
  for Manager and Konstellation adapters; **not** a persisted or authoritative Kristal file.
