# Da’at — Interaction Kernel to Kristal v5 boundary

Da’at is the baseline anti-corruption/adapter layer between IK-facing ecosystem interactions and Kristal-native contracts.

Kristal does not parse Interaction Kernel Envelopes directly.

## Pinned dependency

```text
version                  5.0.0-rc.1
tag                      v5.0.0-rc.1
commit                   af703bf02ee04a69a5f2ad6694fa8b8e56ae2b19
canonicalization_profile kristal.v5:jcs-rfc8785
canonicalization_version 1
```

## Responsibilities

- verify the exact Kristal pin expected by the active Profile;
- validate the IK-side request/profile/admission requirements;
- map immutable source-owned exports/snapshots into Kristal-native Structured Epistemic State or other explicitly supported inputs;
- invoke Kristal-native contracts/tools;
- validate produced artifacts against the pinned schemas/contracts;
- return receipts/events with Kristal-owned ArtifactRefs;
- preserve lineage, source status, validation/recognition metadata and Reader Policy references.

## Non-responsibilities

Da’at does not:

- add IK-only fields to Kristal core schemas;
- collapse compilation, validation and recognition into one gate;
- interpret a signature as epistemic recognition;
- turn Working Exchange into Reference Exchange;
- own physical Runtime Pack activation;
- read/write another product's live operational database as part of Kristal compilation;
- maintain bidirectional authority synchronization between a product database and Kristal;
- treat an optional Runtime Pack query database/index as authoritative state.
