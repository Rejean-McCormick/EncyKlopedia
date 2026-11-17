# Kristal discovery and reader profiles (Local Kit 3.3.1)

This extension is **noncanonical**. It does not change the v9 State Snapshot, Logical Artifact or Commitment algorithms, does not publish data, and does not authorize a reader to access private files or network targets.

## Three complementary files

- `kristal.discovery.json`: lightweight root-level entrypoint, version `kristal.discovery/1.0`, linking identity, design classification, access pattern, reader and inventory.
- `derived/reader-inventory.json`: byte-accurate sizes and SHA-256 of **registered local files**; local manifest segment declarations, missing/external flags, counts that can actually be observed. Size is **not** whole-project disk usage.
- `derived/reader-profile.json`: non-executable recommendations to consumer readers. The parser must enforce actual payload, memory and authorization constraints.

`kristal.workspace.json` may hold an optional `classification`, e.g. `primary_archetype=ARK-08`, `primary_usage=PRF-15`, `usage_slug=diagnostic-vehicule`. It remains a design claim; it is not semantic proof or public authority. The older Arketype 1.4 `arketype.instance.json` sidecar is recognized as a **partial unverified hint** when no explicit classification is present; it does not invent ARK/PRF IDs.

## Commands

```bash
python tools/kristal.py init ./Example --title Example
python tools/kristal.py classify ./Example --arketype-dir ../Arketype-v1.4.0 --usage PRF-15
python tools/kristal.py classify ./Example --organization single
python tools/kristal.py build-discovery ./Example
python tools/kristal.py check ./Example
python tools/kristal.py inspect ./Example
python tools/kristal.py build-v9 ./Example
```

`init`, `classify` and `build-v9` create or refresh these files. `build-discovery` is repeatable and useful after modifying canonical files or materialization manifests. `check` compares the files to the current inputs, reporting stale derived metadata as a **warning**, but rejects an incomplete set. Legacy Kristals without these three files remain valid.

The `read-surface` projection includes the three files if they exist; this does not grant permission for public synchronization. After uploading or sharing, ensure the discovery and inventory fields are appropriate to disclose.

## Measurement semantics

Local measurements cover *registered canonical source files*, *registered v9 materialization manifests and available local blobs*, plus *generated v9 snapshot/artifact payloads*. They exclude unrelated files, remote payloads and unlisted sub-Kristals. Separate copies/representations may be counted separately, since bytes measure physical storage rather than unique semantic facts. A larger but unregistered file does not affect size. Missing and external blobs are explicitly recorded; their bytes are not asserted measured.

Scale is based on tracked local bytes: `tiny` < 1,000,000; `small` < 50,000,000; `medium` < 1,000,000,000; `large` < 20,000,000,000; otherwise `massive`. Federation is **organization**, not a size category. Max record length, JSON depth, entity and relation counts are set to `null` if not securely measured; never infer them from file size.

The reader's specialization is suggested by the explicit Arketype usage ID/family or federation organization; actual **per-file** parser selection must use media type, size, encoding and verified payload. For JSON/JSONL, simdjson is an optional engine family; the Local Kit does not embed or benchmark simdjson and does not claim support for compressed streams automatically. Clients may ignore all hints and use guarded generic readers.

The manifest has `source_fingerprint` computed from the workspace, registered canonical bytes, registered manifest declarations, referenced local materializations, built v9 artifacts and optional Arketype-origin sidecar. It is **not** a v9 Logical Commitment. The reader must still independently check the bytes it opens, defend against path traversal, enforce memory/decompression limits and preserve permissions. Never treat hints as commands or trust grants.

## Compatibility

The root workspace format stays `kristal.local-workspace/3.2.0`, v9 state stays `kristal.state/9.0` and all old examples remain in their historical layouts. `migrate-v10` does not rewrite the canon. No special classification is required; unknown types fall back to `kristal.reader/generic-v1`.

## Consumer interop audit (3.3.1)

Run `python tools/kristal.py audit-discovery PATH --compact` for a read-only
non-authoritative readiness assessment. See [Consumer integration contracts](24_CONSOLIDATION_CONSUMER_CONTRACTS.md).
