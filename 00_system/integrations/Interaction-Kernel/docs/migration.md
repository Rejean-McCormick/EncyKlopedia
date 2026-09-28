# Migration

1. D0 — lock Core/Profile contracts and TCK.
2. D1 — wrap existing Orgo→Konnaxion bridge under `accountability.impact.publish` without behavior change.
3. D2 — implement immutable Konnaxion DecisionRecord handoff → Orgo Signal/workflow.
4. D3 — add ArtifactRef/ExportManifest and source-owned exports.
5. D4 — migrate Da’at from Kristal v4 assumptions to pinned Kristal v5 RC.
6. D5 — reuse/upgrade Orgo BuildRecord/ReleaseRecord semantics.
7. D6 — route Runtime Pack activation through the single deployment activation owner.
8. D7 — deprecate bespoke paths only after conformance, observability and redrive validation.
