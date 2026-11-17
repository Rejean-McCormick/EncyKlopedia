# 16 — V10 publication and activation boundaries

A qualified network release contains, at minimum, an exact `state-snapshot.json`, a `bundle-manifest.json` and a `publication.json`. The independently verified bundle must refer to the exact authorized Git commit and source state. C1 qualification, C2 authorization, C3 collection integrity, GitHub synchronization, immutable release, and activation have **different responsible owners and checks**.

The Authoring Kit's ordinary offline pipeline neither synchronizes a GitHub collection nor activates a hosted channel. The `publish-v9` and `activate-v9` commands belong to a **local v9 lifecycle** and must not be presented as hosted network publication.

**A public sync is already a disclosure operation.** A GitHub release is not the first point of exposure. Never bypass authorization or attempt to repair a blocked C3 collection by fabricating a sync index or qualification receipt.
