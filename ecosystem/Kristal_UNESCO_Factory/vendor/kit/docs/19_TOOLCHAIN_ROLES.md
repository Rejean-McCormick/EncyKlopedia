# 19 — Toolchain responsibility boundaries

| Component | Role and authority |
| --- | --- |
| Framework v10 | Normative candidate schema, semantic commitments, host-profile contracts and TCK |
| Local Authoring Kit | Initialize, check and build local v9 state, optional portable AI read surface |
| KristalDiag / C1 | Independent qualification of the exact scoped state/revision |
| GitHub Bootstrap / C2 | Network configuration, owner authorization and trust gates |
| Kristal Manager | Operator inventory, exact read-surface verification and authorized GitHub synchronization |
| C3 collection controller | Integrity of collection entries, sync manifests and publication candidate |
| Arketype | Non-normative archetype templates and design guidance |
| Konstellation | Read-only navigation across accessible Kristals and within a selected state |
| Kompiler | Read-only retrieval and provenance-preserving context packs |

The authoritative file source is never moved to a convenient reader or controller merely because the reader can parse it. An index is not a canon; a GitHub URL is not a State Commitment; a passing test is not permission to publish.
