# Spek.

**Structured knowledge. Reusable forms. Multilingual publications.**

**Version: 0.5.0 — Educational Layouts and Curated Interoperability** ([source inspection guide](docs/SOURCE_EXPLORER.md), [v0.2 rendering guide](docs/UPGRADE_0.2.md), [font configuration](docs/FONTS.md)).

Spek is an **autonomous, local-first semantic publishing engine** that assembles readable scientific-style documents from **typed semantic units**, **short language realizations**, and **standardized editorial layouts**. One content model can be expressed in multiple languages without asking a language engine to improvise long paragraphs.

> **Spek is an independent publishing product, not a Konstellation extension or a source of scientific truth.** The included article is fictional/illustrative, and its French, English, and Italian sentences are manually supplied fixtures—not certified SemantiK output. Spek does **not** compute or authenticate Kristal v9 canonical commitments, certify GF/PGF RuntimeSets, grant publication approval, or activate Kristal states.

## Why Spek?

- **Spec**: a layout is an explicit, versioned contract specifying the kinds of information it requires.
- **Speak**: SemantiK or another reviewed realization provider supplies short language-specific expressions.
- **Speck**: a small, independently traceable presentation unit can be reused in larger articles.

**Crystallize the form; vary the content.** Spek makes information easier to scan and compare, while preserving evidence, scope, limitations, and provenance. Layouts communicate relationships between units, not merely their typography.

## What's included

| Area | Contents |
| --- | --- |
| Engine | Python module `spek`; CLI `spek` / `python -m spek` |
| Layout library | `result-card`, `argument-map`, `comparison` plus five educational layouts: `concept-card`, `learning-path`, `evidence-comparison`, `observation-inference`, `chronology` (eight explicit HTML/TeX/PDF contracts) |
| Language support | FR, EN, IT strict parity; no automatic translation or silent fallback |
| Output | Static HTML with per-card source explorers, PDF, XeLaTeX source, per-language `document.json`, SHA-256 inventory (`manifest.json`) |
| Source Explorer | Each card reveals semantic unit identity, proof references, provenance, word segmentation, and **supplied** linguistic attributes — never inferred grammar |
| Integrity | Typed slots, bounded cardinality, cross-references, epistemic labels, shared rendering model and source-reference checks |
| Integration | Optional Konstellation `ResultSet 0.2` bridge, generic exchange, **curated Ekole/Kompose preview importer**, legacy SemantiK and frozen AI-sentence importers |
| Operations | CI preview, manual fail-closed GitHub Pages workflow, local site verifier |
| Documentation | Detailed `/docs` plus a complete English GitHub wiki source in `/wiki` |

## Atelier Spek optimisé (Windows)

Lancer **`OUVRIR_SPEK.cmd`** ou **`Spek_Template_Manager.pyw`** pour ouvrir une **interface de travail unique** : charger un `article.json` et ses `realizations.json`, vérifier avec le moteur Spek, puis prévisualiser le HTML **local et non publié**. On peut aussi ouvrir un Kristal en lecture seule pour voir ses métadonnées et les éventuelles compositions explicitement assignées.

La bibliothèque est regroupée sous `template_library/`. Le catalogue Wiki inclut **19 compositions IA candidates**, sans assignation automatique ni génération de faits. Le gestionnaire de catégories et layouts, son éditeur JSON et les sauvegardes avec contrôle d'empreintes restent disponibles de manière contextuelle. Le vieux `OUVRIR_TEMPLATES.cmd` ouvre le même atelier, et `START_SPEK.bat` ouvrent le même atelier ; la démonstration CLI préexistante est conservée sous `DEMO_SPEK_LOCAL.bat`.

[Documentation et scénarios de l'atelier](docs/ATELIER_OPTIMISE_IA_V2.md) · [Gestion des templates](docs/TEMPLATE_MANAGER_GUI.md).

## Rédaction des templates avec SemantiK Architect (atelier privé)

L'atelier distingue maintenant le **plan documentaire**, qui n'affiche aucun triplet brut,
du **Wiki rédigé**, qui exige les réalisations fournies par SemantiK Architect.
L'action **« Réaliser avec SemantiK… »** exécute uniquement les requêtes déjà
associées explicitement aux champs du template, puis vérifie leurs résultats
avant de les assembler. Sans RuntimeSet GF/PGF utilisable, le travail est bloqué
sans texte fictif ni publication.

[Guide : réalisations SemantiK et templates](docs/REALISATION_SEMANTIK_TEMPLATES_2026-11-02_FR.md).

## Try it locally

Requirements: **Python 3.10+**. No external service is called while compiling. PDFs use ReportLab and installed Unicode TrueType fonts (`requirements.txt`); HTML and TeX can be generated with Python's standard library. Regression tests additionally use `pypdf`.

```bash
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python -m spek check
python -m spek build --out dist --formats html,pdf,tex
python -m spek verify-site dist
python -m http.server 8000 --directory dist
# Open http://localhost:8000/
```

Or install the CLI locally: `python -m pip install -e .` and use `spek check`, `spek build`, etc. The CLI's default example paths target this source checkout; for work outside the checkout specify `--source`, `--realizations`, and `--layouts`.

For an actual article:

```bash
python -m spek check \
  --source my-article.json --realizations my-realizations.json --layouts layouts
python -m spek build \
  --source my-article.json --realizations my-realizations.json --layouts layouts \
  --languages en,fr,it --formats html,tex,pdf --out dist
```

**A successful demonstration build is not permission to publish.** Publication of real research requires reviewed, qualified source data and separate authorization.

## v0.5: Educational publishing without becoming an education platform

The educational layout pack adds five **editorial** structures, not a grading engine:

| Layout | Typed information it presents |
| --- | --- |
| `concept-card` | Definition, example(s), counterexample(s), context, limits |
| `learning-path` | Objective, prerequisites, ordered steps, reflection, limits |
| `evidence-comparison` | Question, two source records, two perspectives, synthesis, limits |
| `observation-inference` | Explicit observations, interpretation, proposed verification, limits |
| `chronology` | Context, ordered events, optional interpretation, limits (no implied causality) |

A new `import-educational` command reads **only deliberately filtered `spek.educational-projection/1` exports**. It does **not** crawl Ekole repositories, call Kompose APIs, access student records, infer curricular approvals, produce assessment marks, or authorize publication. Kompose retains access decisions; Ekole retains curriculum and pedagogical validation. A static Spek build cannot protect private student or session data, so these are refused at the input boundary.

**Offline Windows demo (no PowerShell execution-policy change required):**

```bat
scripts\demo-education.bat
```

**Or run the portable commands:**

```bash
python -m spek import-educational --adapter ekole --input examples/education/ekole-curated-preview.json --out-dir education-ekole
python -m spek build --source education-ekole/article.json --realizations education-ekole/realizations.json --out dist-education --formats html,pdf,tex
python -m spek verify-site dist-education
python -m http.server 8000 --directory dist-education
```

For the separate, public-demo **Kompose** projection:

```bash
python -m spek import-educational --adapter kompose --input examples/education/kompose-public-excerpt.json --out-dir education-kompose
python -m spek build --source education-kompose/article.json --realizations education-kompose/realizations.json --out dist-kompose --formats html,pdf,tex
```

See [Educational Connectors](docs/EDUCATIONAL_CONNECTORS.md), [Educational Layout Pack](docs/EDUCATIONAL_LAYOUTS.md), and [Security Boundaries](docs/EDUCATIONAL_PRIVACY.md). These input files are **fictional, manually translated demonstrations**, not actual Ekole curriculum releases or genuine Kompose access grants.

## v0.4: Optional connectors and two language channels

Spek **runs completely independently** from Konstellation, and can attach to multiple Kristals or non-Kristal systems. The core accepts native Spek article JSON; optional adapters can import **Konstellation `ResultSet 0.2`** or a generic **`spek.exchange/0.1`** selection. All mappings are operator-supplied and pin the source assertion content; reader scope is explicitly recorded. The imported text remains a *derived, non-authoritative preview*.

Language expression takes **one of two separate routes per phrase**:

1. `semantik_architect`: externally supplied short SemantiK realizations with request/RuntimeSet provenance when available; Spek does not run GF or certify RuntimeSets.
2. `ai_preconstructed`: sentences authored by an AI **outside Spek**, then frozen and imported with generation and human-review metadata; no SemantiK invocation, no GF qualification and no automatic LLM calls.

The existing v0.3 manual fixtures remain `legacy`. Every card's **Source Explorer** can show its external source context, language channel and an operator-configured link back to the upstream reader. Importing does not install any plugin in Konstellation or activate a Kristal state.

See [Standalone connectors](docs/STANDALONE_AND_CONNECTORS.md) and [Language channels](docs/LANGUAGE_CHANNELS.md), with complete English wiki pages [Source Connectors](wiki/Source-Connectors.md) and [Language Channels](wiki/Language-Channels.md).

**Local Konstellation export demonstration (no live server):**

```powershell
python -m spek bridge-import --adapter konstellation --input examples/bridge/konstellation-resultset.json --template examples/article.json --mapping examples/bridge/konstellation-mapping.json --out bridge-article.json
python -m spek build --source bridge-article.json --out dist-bridge
python -m spek verify-site dist-bridge
```

**Same Spek layouts with a different system and frozen AI examples:**

```powershell
python -m spek bridge-import --adapter exchange --input examples/bridge/external-system-exchange.json --template examples/article.json --mapping examples/bridge/external-system-mapping.json --out external-article.json
python -m spek import-ai --input examples/bridge/ai-preconstructed-example.json --base examples/bridge/realizations-without-example-claim.json --out ai-realizations.json
python -m spek build --source external-article.json --realizations ai-realizations.json --out dist-external
```

These are **illustrative exports and sentences**, not a claim of live Konstellation integration or a real AI model invocation. Published datasets require explicit disclosure authorization and independent review.

## Architecture

```text
           Knowledge sources: Kristal(s) / external systems / local authoring
                            |
            explicitly mapped, derived preview projection
                            v
                  Article source JSON
                            |        reviewed short phrases
                            |       /    (SemantiK or other)
                            v      v
                   +--------------------+
                   |    Spek compiler   |<---- versioned layout library
                   | validate & compose |
                   +--------------------+
                            |
             SpekDocument (derived; per language)
                            |
          HTML / PDF / XeLaTeX / document.json
                            |
                  SHA-256 build manifest
                            |
                   local scientific QA
                            |
              independent publication approval
                            |
              manually gated GitHub Pages publish
```

The HTML reader includes a **"Explore source" button-like toggle in every card**. It expands a structured inspector without exposing raw JSON. Unprovided word attributes display "Not supplied"; the sample word annotations are explicitly illustrative, not certified SemantiK output. See [Source Explorer](docs/SOURCE_EXPLORER.md).

The derived article source is **not a new canonical Kristal artifact**. Spek reads it and emits other derivatives; it does not write back to Kristal.

## The three layouts

| Layout ID | Required semantic roles | Main reading pattern |
| --- | --- | --- |
| `result-card` | claim, applicability, evidence, uncertainty | Main finding → proof/scope → limitation |
| `argument-map` | thesis, evidence-linked premises, inference, conclusion | Argument chain, with optional objection |
| `comparison` | topic, criterion, alternatives A/B, synthesis, limitation | Side-by-side methods or theories |

The `layouts/*.json` files hold **typed slot contracts**. The current prototype's renderers are explicit Python templates in `spek/render.py`; adding a wholly new layout requires updating the renderer as well as adding a JSON file. This is intentionally **not** a generic arbitrary-template interpreter yet. See [Layout design](docs/LAYOUT_DESIGN.md).

For v0.2 output parity, PDF font setup and existing output migration see [Upgrade guide](docs/UPGRADE_0.2.md) and [Fonts](docs/FONTS.md).

## Spek v0.4 test matrix

The demo fixtures are explicitly synthetic. The automated suite checks bridge mappings, source reader-policy agreement, assertion/source payload fingerprints, AI/SemantiK channel isolation, unsafe navigation schemes, local build and the existing v0.3 rendering regressions. A separate development check validated the sample Konstellation `ResultSet 0.2` against the JSON Schema extracted from the supplied Konstellation snapshot. **No live server, real AI generator or real GF RuntimeSet was invoked**.

## Template library — one root directory for all publication families

Reusable page **categories** live in [`template_library/`](template_library/README.md),
separate from the eight shared typed components in [`layouts/`](layouts/):

```text
template_library/
├── wiki/          # Implemented: 19 Arketype mappings and Spek Wiki Markdown drafts
├── educational/   # Reserved template category (educational layouts work separately)
├── scientific/    # Reserved template category
├── report/        # Reserved template category
└── book/          # Reserved template category
```

The former root-level `wiki-templates/` folder has been superseded by
`template_library/wiki/`. All Wiki CLI defaults and tests now resolve the new
location. Existing educational layout contracts remain in `layouts/`;
**reserved** folders do not imply working generators.

```bash
python -m spek list-template-categories
python -m spek list-wiki-templates
```

`build-wiki` generates a **private Markdown draft**, not a live GitHub Wiki.
SemantiK realizations, Arketype mappings, qualified linguistic runtime, source
provenance and external publication authorizations are separate prerequisites.
See [Kristal Wiki templates](docs/KRISTAL_WIKI_TEMPLATES.md).

## GitHub wiki

The English wiki is checked into [`wiki/`](wiki/Home.md) for versioned review. GitHub stores its live wiki in a **separate repository** (`OWNER/Spek.wiki.git`), so it is **not** automatically created by pushing this main repository. See [Wiki publishing](docs/WIKI_PUBLISHING.md) and `scripts/sync-wiki.sh` for the controlled sync procedure.

## CI and public deployment

- `.github/workflows/quality.yml`: tests, checks, demonstration preview archive. **Never publishes.**
- `.github/workflows/publish.yml`: manual publish of an already locally compiled `published-site/` directory. Rejects demonstration artifacts and requires the protected environment `public-pages` and an environment-scoped `KRISTAL_PUBLICATION_GATE=authorized`. **Never recompiles, modifies canon, or activates a state.**
- `published-site/` is ignored locally by default; explicitly force-add only a reviewed public release payload after independent approval: `git add -f published-site/`.
- GitHub repository creation, Pages activation, external Kristal approvals, and initial wiki creation are **operator actions**; no remote account changes happen during a local build.

See [Release and deployment](docs/PUBLISHING.md), [Security](docs/SECURITY_MODEL.md), and [GitHub setup](docs/GITHUB_SETUP.md).

## Project map

```text
spek/                  validator, compiler and renderers
layouts/               typed, reusable layout definitions
template_library/      Wiki category + reserved educational/scientific/report/book categories
examples/              illustrative semantic content + realization bundles
tests/                 automated test suite
docs/                  source-controlled engineering documentation
wiki/                  complete English GitHub wiki source (including Home and _Sidebar)
scripts/               safe wiki sync and repository setup assistance
.github/workflows/     offline CI previews and gated Pages workflow
```

## Project status

**Prototype 0.5 / experimental.** FR/EN/IT outputs and local tests are available. Live Konstellation integration in a deployed environment, native AI generation, real SemantiK RuntimeSet execution, JCS commitment verification, JATS/Crossref/DOI support, externally authenticated approval records, generalized layout rendering, and independent translation equivalence tests are **not implemented**. Do not infer those capabilities from the example.

See [Roadmap](docs/ROADMAP.md). Contributions are welcome via the proposed [contribution guide](CONTRIBUTING.md); **no copyright license is granted by this repository unless the rights holder explicitly adds a license** (see [License decision](LICENSE-DECISION.md)).


### Composition Wiki — inspection structurelle privée

L’atelier peut explorer les sections AI prescrites des cinq Kristals étudiés, à partir des assertions et des positions de source vérifiées par empreinte brute ; aucune sélection pour publication ni réalisation SemantiK ne sont déduites. Voir [Atelier de composition structurelle](docs/ATELIER_COMPOSITION_STRUCTURELLE_PRIVEE_FR.md).

Commande locale : `python -m spek preview-structure --kristal <dossier>` — produit uniquement une inspection HTML privée, non un brouillon publiable.


Pour distinguer le **Wiki public des Kristals** du Wiki documentaire Spek, voir [Pipeline GitHub Wiki Kristal](docs/PIPELINE_KRISTAL_PUBLIC_GITHUB_WIKI_FR.md).


Installation locale de cette version : [Guide de mise à jour de l’atelier](docs/INSTALLATION_ATELIER_SPECIALISE_V4_FR.md).

**SemantiK Architect (import contrôlé, non publiable) :** [guide de transfert local explicite](docs/INTEGRATION_SEMANTIK_2026-11-02_FR.md).

### Identité visuelle et confidentialité des aperçus (2026-11-02)

La version actuelle de l'atelier utilise le logo SVG fourni et la couleur principale
`#1E6864`. L'aperçu structurel privé et les documents de lecture n'affichent plus
les empreintes de fichiers sources ; les contrôles d'intégrité restent effectués
avant la création des aperçus. Les relations structurelles demeurent privées et
ne sont pas destinées à la publication. Voir
`docs/IDENTITE_VISUELLE_CONFIDENTIALITE_2026-11-02_FR.md`.

## Composition récursive vNext (aperçus privés)

Spek prend en charge la catégorie `rhetorical`, les templates imbriqués versionnés et les répétitions avec bindings explicites. Le rendu HTML/Markdown privé utilise des phrases fournies par SemantiK ; il ne sélectionne pas de faits et ne publie rien. Voir [documentation vNext](docs/COMPOSITION_RECURSIVE_VNEXT/11_ETAT_DU_CODE_LIVRE.md) et `python -m spek compose-check --help`. Le compilateur classique reste supporté.

## Composition discursive vNext — mise à jour du 3 novembre 2026

Spek dispose de **62 templates rhétoriques** décrivant chacun leurs mouvements de discours, leurs relations déclarées, leurs groupes de paragraphes et leurs limites. Les transitions linguistiques ne sont pas produites par Spek : quatre modèles proposent un champ de liaison facultatif dont la phrase doit provenir d'une réalisation explicitement fournie à SemantiK.

Depuis la racine du dépôt :

```powershell
py -3 -m spek discourse-audit --instance docs\COMPOSITION_RECURSIVE_VNEXT\exemples\toulmin-avec-liaison-FICTIVE.instance.json
```

L'atelier graphique propose aussi un audit privé des mouvements rhétoriques dans les options SemantiK. Tous les modèles restent non publiables sans qualification des faits, relations et réalisations et autorisations externes. Consulter [la grammaire du discours](docs/COMPOSITION_RECURSIVE_VNEXT/14_GRAMMAIRE_DU_DISCOURS.md) et [le test d'ancrage réel](docs/COMPOSITION_RECURSIVE_VNEXT/15_SOURCES_REELLES_ET_LIMITES_SEMANTIK.md). Les phrases des exemples sont **fictives et manuelles**.
