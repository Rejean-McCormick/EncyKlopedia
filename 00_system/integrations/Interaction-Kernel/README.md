# Interaction Kernel

Interaction Kernel (IK) is a distributed interoperability protocol and reference implementation for autonomous systems. It is not an operational database, artifact store or distributed transaction coordinator.

**Status:** `v1.1-draft-r2` reference implementation.

The repository contains:

- normative JSON Schemas for IK records and artifact interchange;
- versioned Profile descriptors and payload schemas;
- Python and TypeScript runtimes;
- RFC 8785 JCS + SHA-256 semantic request fingerprinting;
- a reusable admission pipeline;
- TCK/golden vectors shared across runtimes;
- Konnaxion, Orgo, Da’at/Kristal and kOA-Linux reference adapters;
- a pinned Kristal `v5.0.0-rc.1` dependency lock;
- GitHub-native technical documentation.

## Architecture

```text
Konnaxion  <----------- IK ----------->  Orgo
    \                                   /
     \                                 /
      +---------- IK ---------->  Da'at
                                      |
                              Kristal-native contracts
                                      |
                                   Kristal
```

Konnaxion↔Orgo remains direct. Kristal is not a mandatory relay. Da’at is the baseline IK participant in front of Kristal.

## Quick checks

### Python

```bash
cd runtime/python
python -m unittest discover -s tests -v
```

### TypeScript

```bash
cd runtime/typescript
npm run build
npm test
```

The TypeScript runtime intentionally has no runtime dependencies.

## Repository map

```text
contracts/      IK schemas, Profiles and payload schemas
locks/          immutable downstream dependency locks
runtime/        Python + TypeScript reference runtimes
adapters/       Konnaxion / Orgo / Da’at / kOA-Linux reference adapters
tck/            cross-language golden vectors
scripts/        validation utilities
docs/           technical documentation + ADRs
```

## Accepted architecture decisions

- Runtime Pack: Konnaxion selects/requests; local platform activation is executed by the configured `RuntimePackActivationPort` owner (kOA-Linux when present).
- Kristal pin: `v5.0.0-rc.1` at commit `af703bf02ee04a69a5f2ad6694fa8b8e56ae2b19`.
- Konnaxion handoff: `DecisionRecord` is the canonical immutable handoff contract.
- Request fingerprint: semantic projection → RFC 8785 JCS → SHA-256.
- State/artifact boundary: each participant owns its mutable operational state; IK transports interactions and references; Da’at maps source-owned snapshots into Kristal-native artifacts; no distributed cross-owner database transaction is required.

See [`docs/`](docs/README.md).
