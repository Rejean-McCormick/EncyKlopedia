# Kristal and Da’at

Baseline: Da’at is the IK participant in front of Kristal. Kristal does not parse IK Envelopes.

Pinned release:

- version `5.0.0-rc.1`
- tag `v5.0.0-rc.1`
- commit `af703bf02ee04a69a5f2ad6694fa8b8e56ae2b19`
- canonicalization `kristal.v5:jcs-rfc8785`
- schema-set digest `sha256:7a94a1e8a91d5c5267b73b7f1e98977faa548324bc937bb491cd08d49fdc8c92`

Da’at applies explicit versioned mappings from Konnaxion/Orgo ExportManifests to Kristal-native inputs, invokes Kristal-native contracts, validates outputs, then emits IK Receipts/Events with Kristal-owned ArtifactRefs.

## Authority boundary

Konnaxion and Orgo do not write their mutable operational databases into Kristal and do not grant Da’at ownership of that state. They provide source-owned snapshots/revisions suitable for mapping.

Da’at is an anti-corruption and compilation boundary:

```text
source operational DB
       |
       | source-owned snapshot / ExportManifest
       v
      Da'at
       |
       | versioned mapping
       v
Kristal-native artifact
       |
       | ArtifactRef
       v
source/local consumer projection
```

Kristal owns its native epistemic artifacts. A Runtime Pack or database-like query materialization derived from a Kristal artifact remains an artifact/materialization; it does not become the source application's operational system of record.

IK does not require a distributed transaction between the source database, Da’at and Kristal. Cross-boundary completion is expressed through durable delivery, Receipts, Events, ArtifactRefs and reconciliation.

See [ADR-IK-05](adrs/ADR-IK-05-operational-state-artifact-boundary.md).
