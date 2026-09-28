# ADR-IK-03 — DecisionRecord handoff

**Status:** Accepted

`DecisionRecord` is the immutable/read-model canonical handoff contract from Konnaxion to Orgo. Decision publication does not itself imply execution; the `governance.decision.execute` Profile plus governance authority claim makes execution intent explicit.
