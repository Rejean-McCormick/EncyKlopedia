# EncyKlopedia

**Global multilingual encyclopedia — powered by the Kristal knowledge ecosystem.**

> **Status:** `0.1.0-alpha.1` — functional, local-only, synthetic **read-only demonstration**. Real-content publication, bulk indexing, public deployment and 100-language qualification are **not implemented**.

EncyKlopedia is the *public reading and discovery application*, formerly planned as `kristal-encyclopedia` and discussed under the possible name `KristALL`. It is **not** the legacy EncyK source-acquisition engine and does not replace Skope, Konstellation, the Kristal Framework or Médiathèque kOA.

## GitHub description (English, <=350 characters)

Global, multilingual encyclopedia powered by the Kristal knowledge ecosystem. Provides scalable public access to articles, search, source references, provenance, and read-only APIs, while preserving semantic identities and supporting transparent language coverage across a worldwide knowledge network.

## Responsibilities

| Component | Owns |
|---|---|
| Skope (EncyK integrated) | Source discovery, scopes, acquisition and evidence handoffs |
| Médiathèque kOA | Durable source/snapshot/representation authority |
| Kristal Framework + Authoring Kit | Semantic identity, approved knowledge and canonical contract governance |
| Kristal Integration Pack | Validated, **non-canonical**, derived v11 read-view handoff |
| Konstellation | Interactive exploration/navigation |
| **EncyKlopedia** | Public-oriented read-only articles, discovery, multilingual presentation and publication delivery (once qualified) |

**No data moves from Skope or EncyK to this demo.** No GitHub repo should contain the real knowledge corpus, dumps, credentials, local collection stores, or billions of generated article files.

## Quick start (Node.js 22+; no npm dependencies)

```sh
npm run verify
npm start
```

On Windows you can instead double-click `Start_EncyKlopedia.cmd`. Open **http://127.0.0.1:8787**. Sample content is explicitly fictional/synthetic and stored in `examples/synthetic-publication.json`. Select Français to see a direct translation for one entry and a disclosed English fallback for another; Japanese is a fallback preview, **not a certified translation**.

### Demo API

```text
GET /healthz
GET /readyz
GET /api/v1/status
GET /api/v1/locales
GET /api/v1/search?lang=fr&q=observatoire
GET /api/v1/articles/northwind-observatory?lang=fr
```

No write APIs, public-network listener, external fetching or real publication mechanism exist in this alpha. `ENCYKLOPEDIA_MODE=public` deliberately refuses to start. Demo mode binds to loopback only. See [release gates](docs/RELEASE_GATES.md).

## Language/identity semantics

Article `display_status` of `direct` or `fallback` is **UI display availability**, *not* the upstream Framework's lexical `direct/fallback/missing` coverage. The complete Kristal IDs (KQ/KP/KA/KS), original assertions, provenance and source hashes must remain traceable in the future **approved publication adapter**. Synthetic `demo:` identifiers in this repository must never be interpreted as Kristal identities.

The architecture targets Framework `11.0.0-draft.4` and Integration Pack read view `kristal.integration.read-view/v11.0-draft.1`. Their presence in metadata **does not prove interoperability or publication approval**. Source data must only be promoted to a public serving artifact after explicit C2/C4 checks, authorized source rights, privacy/redaction and independent cross-repo qualification.

## Repository structure

```text
src/          Node HTTP demo reader and narrow display adapter
public/       Accessible, dependency-free demo interface
examples/     Synthetic demo fixture only
contracts/    Local draft reader/bundle schema, NOT normative Kristal contracts
tests/        Node test runner unit and HTTP regression tests
docs/         Architecture, publication gates and GitHub handoff instructions
.github/      Dependency-free CI for this repository
```

## Roadmap (not implemented)

1. Qualify read-only adapter of approved Framework v11 / Integration Pack reading views.
2. Define immutable, explicitly authorized *publications* with privacy and licensing gates.
3. Integrate distributed public article reads and search indexes on object storage/serving infrastructure, not on GitHub.
4. Add progressive multilingual release qualification with transparent `direct/fallback/missing` presentation and accessible user experiences.
5. Add observability, abuse protection, CDN/cache, redundancy and load tests for the actual target scale.

See [architecture](docs/ARCHITECTURE.md). Every production gate is **open work**.

## License

**Not selected.** Do not infer a default open-source license or rights for future corpus data. The repository owner must decide a code license and separate content policy before public redistribution.
