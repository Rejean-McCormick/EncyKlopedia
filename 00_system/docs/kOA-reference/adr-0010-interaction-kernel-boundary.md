# ADR-0010: Interaction Kernel as target cross-system protocol

- **Status:** Accepted as target ecosystem architecture; adoption is system-specific
- **Date:** 2026-09-16

## Decision

Interaction Kernel (IK) is the target distributed protocol/Profile layer for selected cross-system boundaries, especially Konnaxion↔Orgo and ecosystem↔Da’at.

However:

- kOA-Linux already owns canonical internal/component communication contracts;
- IK does not automatically replace those contracts;
- product/platform conformance requires explicit Profile/version adoption and evidence;
- Digital Ecosystem must not infer IK adoption from generic product build/runtime qualification.

## Architecture

- Konnaxion↔Orgo remains direct by default.
- No forced Kristal hop.
- Da’at maps IK/ecosystem interactions to Kristal-native contracts.
- Source-owned artifacts remain source-owned.
- Durable interactions preserve idempotency and reconciliation.
