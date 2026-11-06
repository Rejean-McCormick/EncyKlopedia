# Release and public exposure gates

**Current status:** ALL PRODUCTION GATES BLOCKED. The project serves a synthetic demo or explicit unapproved UNESCO research on loopback only.

| Gate | Minimum condition before a real public deployment | Alpha status |
|---|---|---|
| C1 Implementation/contract | Exact Framework v11 integration pins, compatible published reader, reproducible build | BLOCKED |
| C2 Content/security | Explicit artifact origin, source rights, authorizations, private/public separation, redaction approval | BLOCKED |
| C3 Materialization | Verified immutable publication, digest verification, storage/index consistency, rollback and observability | BLOCKED |
| C4 Public release | Explicit independent approval of named collection + projection + locale coverage + public exposure | BLOCKED |
| Production | Qualified load tests, network security, rate limits, CDN, backup and incident/rollback procedures | BLOCKED |

An Integration Pack reading view is **derived only**; `presentation` is not a publication grant. Likewise a Skope scope, EncyK source handoff, Konstellation view or GitHub Pages demonstration is not evidence of permission to publish a real Kristal collection.

The application refuses `ENCYKLOPEDIA_MODE=public` for this release. Do not remove this gate as a deployment shortcut. The future gate must verify *external, independently authorized* publication attestation, never a `true` flag provided by the same untrusted bundle.

## UNESCO private research adapter (0.2-alpha)

The private mode does **not** lift C1–C4. Its validation checks structural status, SHA-256 digest, localhost binding and candidate provenance. It neither proves source rights nor publishes real content.

## Future language-realization qualification (non-normative proposal)

**Not implemented in the alpha; all C1–C4 gates remain blocked.** These are additional checks to consider within existing gates, **not** new authorization flags and **not** a change to the normative Framework contracts:

1. **Stable semantic input:** every realizable proposition carries immutable Kristal identifiers, typed predicate/argument roles, qualification/context and approved state; no canonical meaning depends on English strings.
2. **Reviewed lexical bindings:** every locale's chosen lexeme/sense and predicate construction maps to an explicit semantic identity, with a curated diK review decision and source/license evidence. Kaikki, UniMorph and Wikidata Lexemes harvester candidates are **not** themselves publishable lexicons.
3. **Typed GF realization:** pin GF abstract grammar, each concrete language grammar, lexicon, RGL/toolchain versions and build digests; compile and validate supported language paths.
4. **No silent invention:** unsupported semantic roles, missing dictionary senses, missing morphology or failed GF linearization must block direct generation or yield an explicitly disclosed unavailable/fallback status. No unverified paraphrase becomes an assertion.
5. **Measured locale coverage:** report distinct semantic, lexical, grammar and displayed-locale coverage; do not confuse the reader's `display_status` with Framework lexical `direct/fallback/missing` statuses.
6. **Reproducible trace:** each served sentence must be traceable to exact approved assertion IDs, source provenance, lexical choices, GF artefact versions, post-processing/composition configuration and publication manifest.
7. **Independent checks:** evaluate semantic preservation and grammatical quality (initial EN/FR pilot), rights and privacy, accessibility, attribution and public-release approval before any C2/C3/C4 qualification.

These requirements must be agreed with the owners of **Kristal Framework, diK and GF Wordbench** before a production serialization or automated adapter is introduced. See [language architecture](LANGUAGE_ARCHITECTURE.md).
