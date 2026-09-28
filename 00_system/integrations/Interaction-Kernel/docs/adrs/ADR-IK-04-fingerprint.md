# ADR-IK-04 — Canonical reliable fingerprint

**Status:** Accepted

Fingerprint = SHA-256 over RFC 8785 JCS of the semantic request projection. The projection excludes volatile transport/trace/correlation/time fields. Python and TypeScript must match TCK golden vectors exactly.
