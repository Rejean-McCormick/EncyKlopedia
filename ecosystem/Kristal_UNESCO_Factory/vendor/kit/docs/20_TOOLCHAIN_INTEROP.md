# 20 — Local toolchain interoperability

Local Kit produces two machine-readable read-only contracts:

```bash
python tools/kristal.py inspect <workspace> --compact
python tools/kristal.py read-surface <workspace> --compact --require-ready
```

- `inspect` remains `kristal.local-inspection/1.0`, a local status and file-location discovery aid.
- `read-surface` remains `kristal.github-read-surface/1.0`, the **exact, verified** list of reader files, file roles, media types, byte counts and SHA-256 values. `surface_digest` is an operational fingerprint, never a semantic commitment.

## State discovery precedence

1. `state/state-snapshot.json` (explicit export).
2. `build/v9/state-snapshot.json` (latest local build).
3. `.kristal/v9/` and legacy root State Snapshot (compatibility).
4. `release/v9/states/**/state-snapshot.json` (immutable local releases).

This precedence is operational. Selecting a path does not rewrite the state's Logical Commitment.

## Projection rules

`read-surface` includes approved reader files such as `AI_START_HERE.md`, `AI_MANIFEST.json`, indexed `canon/`, `sources/`, `docs/`, projection descriptions, materialization manifests and the exact `state/state-snapshot.json`. It does **not** mirror `tools/`, `build/`, `release/`, `hosting/`, `validation/` or `runtime/`. It refuses path traversal and checks actual byte length and digest against indexed metadata. Physical blob candidates are listed separately in `materialization_objects` so the host can select Git, Release, LFS, GHCR or a resolver without automatically copying huge objects.

The Manager must consume this producer contract rather than reconstructing an index from directory traversal; a public upload must also pass C1/C2 authorization before the first network write.
