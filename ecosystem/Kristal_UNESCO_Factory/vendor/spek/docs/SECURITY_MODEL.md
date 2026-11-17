# Security and trust model

## Trust boundaries

- **Kristal authoritative data**: governed upstream; Spek receives only a derived editorial projection.
- **SemantiK realizations**: externally qualified; Spek records strings and declared provenance but is not the runtime certifier.
- **Spek presentation**: validates IDs, slot kind/cardinality, evidence links, language completeness, escape handling, and inventory digests.
- **Deployment authority**: external scientific/disclosure approval plus a protected GitHub environment; never inferred from a successful build.

## Implemented defensive checks

- Strict supported data format IDs and bounded identifiers.
- No silent missing language fallback; all used keys must exist in all requested languages.
- Result evidence must be explicitly linked to the claim; an argument must reference evidence.
- HTML and LaTeX text is escaped.
- Build occurs in staging and produces a SHA-256 manifest; `verify-site` refuses tampering, unlisted files, symlinks, and unsafe manifest paths.
- `--production` rejects illustrative source and unqualified realization declarations.
- Public workflow is manual and configured to fail closed without environment-gated authorization.

## Explicit non-guarantees

Spek is not a sandbox for untrusted executable code, a scientific fact checker, a translator quality evaluator, a signature verifier, an access control system, a consent registry, a replacement for Kristal C1/C2/C3/C4, or an activation controller. Build checks do **not** guarantee no confidential text appears in a derived output. Operators must inspect and authorize the exact output set.

Do not embed credentials, private paths, raw canonical states, sensitive provenance, or personally identifiable research data in published HTML, PDF, TeX, or manifests.
