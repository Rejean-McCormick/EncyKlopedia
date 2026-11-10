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

## Language/identity semantics

Article `display_status` of `direct` or `fallback` is **UI display availability**, *not* the upstream Framework's lexical `direct/fallback/missing` coverage. The complete Kristal IDs (KQ/KP/KA/KS), original assertions, provenance and source hashes must remain traceable in the future **approved publication adapter**. Synthetic `demo:` identifiers in this repository must never be interpreted as Kristal identities.

The architecture targets Framework `11.0.0-draft.4` and Integration Pack read view `kristal.integration.read-view/v11.0-draft.1`. Their presence in metadata **does not prove interoperability or publication approval**. Source data must only be promoted to a public serving artifact after explicit C2/C4 checks, authorized source rights, privacy/redaction and independent cross-repo qualification.

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

## License

**Not selected.** Do not infer a default open-source license or rights for future corpus data. The repository owner must decide a code license and separate content policy before public redistribution.

### Index local des dictionnaires (candidat v0.2)

L'outil privé `Start_Indexation_Dictionnaires.cmd` dans le dépôt **C:** découvre les archives Kaikki, UniMorph et Wikidata Lexemes déjà présentes dans **D:\EncyKlopedia**, les lit en flux et crée **uniquement sur D:** un index SQLite de lemmes, des formes UniMorph, des compteurs de sens/formes/traductions et des rapports par langue. Il ne télécharge ni ne copie les archives. Statuts **unreviewed**, sans promotion diK/Framework. Python 3.10+ est requis en complément de Node.js. Voir [indexation lexicale mondiale](docs/INDEXATION_LEXICALE_MONDE.md).


### Réparation des données UniMorph (v0.3)

Double-cliquer sur `Reparer_Dictionnaires_UI.pyw` (code sur C:, archives et index dérivé sur D:). Le bouton de réparation ne reprend que les sources UniMorph non complètes, jamais les archives déjà indexées. Détails : `docs/REPARATION_UNIMORPH_V03.md`.


### Audit qualité lexical avec interface graphique (v0.4)

Double-cliquer sur `Audit_Qualite_Lexicale_UI.pyw` **sur C:**. Le diagnostic `pib` / `sdh`, les comptes exacts de clés lexicales normalisées par langue et les chevauchements orthographiques entre familles de sources sont produits **seulement sur D:**, sous `30_working/lexical/harvester/quality-v1`. Le calcul exhaustif reprend par langue ; les `exactMatch`, les licences et la publication ne sont jamais approuvés automatiquement. Voir [audit qualité v0.4](docs/AUDIT_QUALITE_LEXICALE_V04.md).


### Conciliation candidate vers diK (v0.5, interface graphique)

Après l'audit v0.4, double-cliquer sur `Concilier_Dictionnaires_diK_UI.pyw` (ou `Start_Conciliation_diK.cmd`) **dans le moteur sur C:**. L'application lit l'index existant sur **D:** en lecture seule, repère massivement les graphies communes aux familles Kaikki, UniMorph et Wikidata L, conserve les preuves et crée des shards JSONL + une file de revue diK **strictement candidate** sous `30_working/lexical/harvester/dik-reconciliation-v1`. Un mode pilote `fr,en`, un parcours mondial reprenable, un explorateur et une vérification SHA-256 sont fournis. **Aucune conciliation de sens, licence validée, identité Kristal ou publication** n'est effectuée automatiquement. Voir [le contrat et le mode d'emploi](docs/CONCILIATION_DIK_LEX1_V05.md).


## Enrichissement lexical candidat DIK-LEX-1 v0.6 (facultatif)

**Code sur C:, toutes les données sur D:.** Après un traitement v0.5 terminé et
ses exports SHA-256 vérifiés, double-cliquer sur `Enrichir_Dictionnaires_diK_UI.pyw`
(ou `Start_Enrichissement_diK.cmd`). Vue plan, pilote français/anglais, reprise
mondiale et vérification SHA-256. La lecture est **ciblée sur les ancrages de
provenance échantillonnés en v0.5** : elle ne prétend ni lire tous les sens,
ni arbitrer les homographes. Les originaux restent intacts; résultats sous
`D:\EncyKlopedia\30_working\lexical\harvester\dik-enrichment-v1`.

CLI : `npm run lexical:dik:enrich:plan`, `npm run lexical:dik:enrich`,
`npm run lexical:dik:enrich:verify`. Détails : `docs/ENRICHISSEMENT_DIK_LEX1_V06.md`.
Aucune écriture dans le dépôt diK, aucun KQ/KP, `exactMatch` ou publication.

## Qualification candidate diK v0.7 — interface graphique (facultatif)

Après la v0.6, double-cliquer sur `Qualifier_Dictionnaires_diK_UI.pyw` ou
`Start_Qualification_diK.cmd` **dans le dépôt C:**. Le programme relit les
JSONL probatoires v0.6 déjà présents sur **D:**, compare leurs SHA-256,
classe les candidats, conserve des checkpoints par langue et produit une
file de revue locale sous `D:\EncyKlopedia\30_working\lexical\harvester\dik-qualification-v1`.
L'explorateur affiche les preuves échantillonnées et permet d'ajouter des
**annotations humaines non normatives** en journal append-only. La file de
licences reste bloquée par défaut. **Aucun sens fusionné, aucune décision
« accepted », aucun KS inventé, aucun KQ/KP et aucune publication.**

CLI : `npm run lexical:dik:qualify:plan`, `npm run lexical:dik:qualify`
(et `-- --languages fr,en` pour le pilote),
`npm run lexical:dik:qualify:verify`.
Voir `docs/QUALIFICATION_DIK_LEX1_V07.md`.

## Branch 04 functional-chain alignment

See [final-system reader/language boundaries](docs/PRIVATE_V11_PACK_PREFLIGHT.md). This is a pinned-snapshot coordination note and does not override owner normative contracts or qualify public publication.
