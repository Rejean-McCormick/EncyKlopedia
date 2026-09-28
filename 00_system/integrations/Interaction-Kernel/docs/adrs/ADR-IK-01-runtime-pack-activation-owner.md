# ADR-IK-01 — Runtime Pack activation owner

**Status:** Accepted

Konnaxion owns desired/application selection. When kOA-Linux is present, kOA-Linux owns physical verify/stage/activate/rollback state through `RuntimePackActivationPort`. Standalone Konnaxion may supply its own implementation. There must be exactly one authoritative activation state per deployment.
