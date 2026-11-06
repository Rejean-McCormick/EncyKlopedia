# EncyKlopedia

**Global multilingual encyclopedia — powered by the Kristal knowledge ecosystem.**

> **Status:** `0.2.0-alpha.1` — local-only read-only synthetic demo **plus private unapproved UNESCO research preview**. Public release, bulk indexing and 100-language qualification are **not implemented**.

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
| diK (curated dictionaries; future qualified handoff) | Curated lexical identities, language-specific lexicalizations and governed sense mappings; candidate harvester output is **not** curated diK content |
| GF / GF Wordbench | Abstract/concrete grammar and language realization tooling; production handoff is **not yet qualified** |
| Konstellation | Interactive exploration/navigation |
| **EncyKlopedia** | Public-oriented read-only articles, discovery, multilingual presentation and publication delivery (once qualified) |

**No source data enters the synthetic demo.** The separate `research` mode reads explicitly selected UNESCO Workbench outputs, checks their SHA-256 integrity, and does not approve any semantic identity or source. No GitHub repo should contain the real knowledge corpus, dumps, credentials, local collection stores, or billions of generated article files.

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

The private UNESCO research preview is launched by `UNESCO_Workbench\LANCER_VERSION_TOTALE.cmd`, followed by `Start_UNESCO_Research.cmd`. It contains 41 English vocabulary anchors and an unapproved draft on *Right to education*. See [private UNESCO research](docs/UNESCO_PRIVATE_RESEARCH.md).

No write APIs, public-network listener, external fetching or authorized real publication mechanism exist in this alpha. `ENCYKLOPEDIA_MODE=public` deliberately refuses to start. Demo mode binds to loopback only. See [release gates](docs/RELEASE_GATES.md).

## Knowledge, dictionaries and grammatical realization

**Kristals are language-independent knowledge objects.** Their semantic identifiers, predicates, argument roles, assertions, epistemic states and provenance do **not** depend on English, French or any other natural language. Source quotations or language-tagged labels may be attached as evidence or annotations, but they are **not** the identity or truth of the knowledge claim.

The intended publication pipeline separates semantic and linguistic authority:

```text
Approved Kristal knowledge + provenance
    -> qualified, non-canonical read projection / semantic realization input
    -> reviewed semantic-to-lexical bindings + curated diK dictionaries
    -> GF abstract trees + language-specific GF grammar/lexicon
    -> generated language-specific text
    -> qualified EncyKlopedia article composition and read-only delivery
```

The GF Wordbench supports lexical and grammar development; the GF Resource Grammar Library supplies reusable language grammar infrastructure. Lexical resources must be shared and versioned **outside individual Kristals**. Neither string matching, UNESCO SKOS labels nor Wikidata sitelinks/Lexemes automatically certify a semantic equivalence, a dictionary entry or a publishable phrase.

The existing local Kaikki/UniMorph/Wikidata Lexemes pipeline **only discovers and stages candidates**; its v0.5 and v0.6 handoffs do not populate curated diK dictionaries, assign Kristal identities, or generate approved GF sentences. The alpha reader currently uses manually authored synthetic demonstration text, **not** this production realization pipeline.

For the full contract, including semantic-role requirements, dictionary layers, GF interfaces, fallback rules, traceability and test gates, see **[Language architecture and Kristal realization contract](docs/LANGUAGE_ARCHITECTURE.md)** and the [overall architecture](docs/ARCHITECTURE.md).

### Language/identity semantics in the current alpha

Article `display_status` of `direct` or `fallback` is **UI display availability**, *not* the upstream Framework's lexical `direct/fallback/missing` coverage. A future production adapter must report lexical coverage, grammar coverage and actually delivered locale independently. The complete Kristal IDs (KQ/KP/KA/KS), original assertions, provenance, lexical/grammar versions and source hashes must remain traceable. Synthetic `demo:` identifiers in this repository must never be interpreted as Kristal identities.

The architecture targets Framework `11.0.0-draft.4` and Integration Pack read view `kristal.integration.read-view/v11.0-draft.1`. Their presence in metadata **does not prove interoperability or publication approval**. Source data must only be promoted to a public serving artifact after explicit C2/C4 checks, authorized source rights, privacy/redaction, independently qualified linguistic realization and cross-repo qualification.

## Optional private dictionary harvester (candidate tool) — C: code / D: data

This snapshot can be extended by a separate local, opt-in dictionary-acquisition tool under `tools/dictionary-harvester/`, storing raw captures on **D:** under `D:\EncyKlopedia\10_sources\lexical\harvester` and unreviewed observations under `D:\EncyKlopedia\30_working\lexical\harvester` (code stays in the C: repository). It **does not** make the EncyKlopedia reader a source-acquisition authority and does not bypass Skope/EncyK, Médiathèque kOA, diK or C2/C4 publication checks. No public HTTP ingestion endpoint is added. Run `npm run harvest:sources` for a list of candidate sources; see [local dictionary harvester](docs/DICTIONARY_HARVESTER.md).

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

## Roadmap (not implemented as production features)

1. Qualify read-only adapter of approved Framework v11 / Integration Pack reading views.
2. Define immutable, explicitly authorized *publications* with privacy and licensing gates.
3. Integrate distributed public article reads and search indexes on object storage/serving infrastructure, not on GitHub.
4. Add progressive multilingual release qualification with transparent `direct/fallback/missing` presentation and accessible user experiences.
5. Add observability, abuse protection, CDN/cache, redundancy and load tests for the actual target scale.

See [architecture](docs/ARCHITECTURE.md). Every production gate is **open work**.

## Local lexical source pipeline (candidate, not language authority)

All source archives, work databases and candidate exports stay on `D:\EncyKlopedia`; tools and UI launchers remain in the C: repository. These are **private, opt-in preparation utilities**, not public reading endpoints or automatic diK/Framework/GF publishers. Their legacy tool-specific runbooks remain available under `docs/`.

| Stage | Entry point / guide | What it produces (and does not authorize) |
|---|---|---|
| v0.2 inventory and indexing | `Start_Indexation_Dictionnaires.cmd` — [global lexical indexing](docs/INDEXATION_LEXICALE_MONDE.md) | Streams existing Kaikki, UniMorph and Wikidata Lexemes archives into a private D: SQLite index; observations remain unreviewed |
| v0.3 UniMorph repair | `Reparer_Dictionnaires_UI.pyw` — [targeted repair](docs/REPARATION_UNIMORPH_V03.md) | Repairs eligible incomplete UniMorph source records; never modifies original archives |
| v0.4 quality audit | `Audit_Qualite_Lexicale_UI.pyw` — [quality audit](docs/AUDIT_QUALITE_LEXICALE_V04.md) | Measures candidate quality and normalized-key overlap; does not establish shared meaning |
| v0.5 candidate diK reconciliation | `Concilier_Dictionnaires_diK_UI.pyw` / `Start_Conciliation_diK.cmd` — [candidate reconciliation](docs/CONCILIATION_DIK_LEX1_V05.md) | Produces evidence shards and a diK review queue; **no automatic sense alignment or `exactMatch`** |
| v0.6 evidence enrichment | `Enrichir_Dictionnaires_diK_UI.pyw` / `Start_Enrichissement_diK.cmd` — [evidence enrichment](docs/ENRICHISSEMENT_DIK_LEX1_V06.md) | Re-reads selected provenance-anchored examples; not an exhaustive sense dictionary or a normative diK import |

The candidate output lives under `D:\EncyKlopedia\30_working\lexical\harvester`. It requires separate license/provenance review, word-sense disambiguation, curated diK acceptance and an independently validated semantic-to-GF interface before it can support real text generation. See [dictionary acquisition](docs/DICTIONARY_HARVESTER.md) and [language architecture](docs/LANGUAGE_ARCHITECTURE.md).

## Roadmap clarification

In addition to the release roadmap above, language realization needs a separate cross-repository qualification: stable semantic role signatures, governed lexical bindings, versioned GF abstract/concrete grammar, EN/FR pilot tests, explicit direct/fallback/missing behavior and reproducibility of generated text. This is **future work**, not a feature of `0.2.0-alpha.1`.

## License

**Not selected.** Do not infer a default open-source license or rights for future corpus data. The repository owner must decide a code license and separate content policy before public redistribution.
