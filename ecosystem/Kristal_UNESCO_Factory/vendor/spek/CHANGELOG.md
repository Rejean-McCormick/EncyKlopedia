## 2026-11-03 — Contrats discursifs pour les 62 templates

- Modèles de mouvements rhétoriques, groupes de paragraphes et DAG des relations déclarées, non vérifiées sémantiquement.
- Slots de transition SemantiK explicites dans quatre modèles, sans connecteurs automatiques ni reformulations.
- `discourse-audit`, `compose-source-check`, dialogue étendu, audit graphique et refus stricts.
- Test de présence de références sur graphe réel Agriculture v11 ; aucune réalisation GF/PGF réelle ni autorisation de publication.
- Documentation `/docs/COMPOSITION_RECURSIVE_VNEXT/14_…` et `15_…`.

## 2026-11-02 — vNext : composition récursive et templates rhétoriques (aperçu privé)

- Ajout du moteur `spek.composition` : définitions/instances versionnées, DAG instancié, répétitions explicites et validation stricte.
- Nouvelle catégorie `template_library/rhetorical/` : 10 templates au même niveau que la bibliothèque Wiki ; exemple intercatégorie `wiki.article`.
- CLI : `compose-check`, `compose-dialogue`, `compose-import-semantik`, `compose-preview` et intégration graphique facultative.
- HTML/Markdown privés plus fluides, sans titres techniques répétés et sans données d'audit ; contrôle stricte des réalisations fournies.
- 27 layouts historiques, registre des 127 propositions et mécanisme de publication séparé inchangés.
- **Non implémentés :** exécution GF/PGF vNext directe, qualification C1/C2/C3, publication de la collection, formats PDF/TeX récursifs.
- Référence : `docs/COMPOSITION_RECURSIVE_VNEXT/11_ETAT_DU_CODE_LIVRE.md`.

## 2026-11-02 — Aperçu documentaire et réalisation SemantiK explicite

- L’aperçu du plan d’un Kristal n’expose plus les triplets canoniques en tant que prose. Il indique « Texte en attente de réalisation SemantiK ».
- Ajout de l’exécution locale du CLI officiel SemantiK Architect sur les requêtes déjà associées explicitement à un article Spek, suivie de la validation stricte des résultats.
- Un RuntimeSet absent ou invalide provoque un refus, sans génération artificielle de phrases.
- Conservation des 127 propositions IA, des 27 layouts, des contrôles de source, du thème #1E6864 et des règles C1/C2/C3.

## 2026-11-01 — Spek Atelier UX v2 (local, no release/publish)

- New unified primary workflow `open → check → preview`, implemented in existing `.pyw` launcher, accessible with `START_SPEK.bat` or `OUVRIR_SPEK.cmd`; former demo preserved as `DEMO_SPEK_LOCAL.bat`.
- Read-only Kristal metadata opener; no recursive content scan or automatic template selection.
- 19 AI-designed Wiki editorial compositions included under `template_library/wiki/compositions/`; assignment registry intentionally empty pending source evidence.
- Advanced/contextual editor retained with backups, concurrency protection and additional composition-layout reference safeguards.
- Real local HTML preview uses existing Spek compiler, never a simulated or published result.
- UX audit aligned with supplied AI interface guide v2, documented in `docs/ATELIER_OPTIMISE_IA_V2.md`.

## Gestionnaire de templates (2026-11-01)

Ajout d’un lanceur Tkinter `.pyw` local pour naviguer dans `template_library/`, éditer les profils Wiki et les contrats de layouts, dupliquer/créer des brouillons, valider avec sauvegardes et protections contre les modifications concurrentes. Pas de moteur de publication ajouté.

# Changelog

## Spek template library organization — 2026-11-01

- Consolidated template categories under `template_library/{wiki,educational,scientific,report,book}/`.
- Migrated the existing Wiki archetype profiles from `wiki-templates/` to `template_library/wiki/`.
- Updated Wiki CLI defaults, added category discovery (`list-template-categories`) and preserved the eight reusable layouts under `layouts/`.
- The Wiki category is implemented; other category descriptors remain **reserved**. No new data-processing or publication authority is implied.
- Packaged as a complete source tree for local restoration, without a `.git` directory.


## 0.5.0 — Educational publishing, independent Ekole/Kompose adapters

- Five additional typed layouts (eight total), localized in FR/EN/IT and rendered in HTML, PDF and LaTeX.
- `spek.educational-projection/1` curated input contract, `import-educational --adapter ekole|kompose` and independently verifiable local builds.
- Fail-closed rejection of teacher/session/PII fields, unknown metadata, unreferenced phrase payloads, private evidence locations and session-restricted Kompose content.
- No public release/teacher grade/clinical inference or educational authority conferred by the export. All educational imports remain local preview projections and cannot pass Spek's production gate.
- A fictitious Ekole school-garden example across five layouts and a separate Kompose public-excerpt example, neither an actual upstream deployment.
- Windows-friendly `.bat` demo script, fixed the PowerShell bridge demo's comma argument issue, tests and English wiki additions.


## 0.4.0 — Autonomous interoperability and language-channel separation

- Spek is a standalone compiler; external connectors are optional.
- `bridge-import --adapter konstellation|exchange` converts explicitly mapped, scoped export payloads to derived Spek article sources.
- `bridge-fetch-konstellation` adds opt-in read-only `/api/query` capture with environment-sourced bearer token and redirect blocking.
- `import-ai` ingests preconstructed AI text without calling SemantiK; provenance channel, model, generation and review status are distinct from GF runtime qualification.
- Structured Source Explorer offers source-system references and an operator-configured outbound deep link.
- Synthetic Konstellation `ResultSet 0.2` and generic exchange fixtures; regression tests for scope, integrity, non-escalation and linguistic provenance.
- Full English connector and language-channel docs and Wiki pages.
- External source projections are never canonically verified or auto-authorized for production.

## 0.3.0 — Source Explorer

- Added a native, accessible **Explore source** toggle to every HTML card, in French, English, and Italian.
- Displayed typed semantic references, qualifications, provenance, realization provider/status and evidence links as structured records, not inline raw metadata or JSON.
- Added surface-word tables, validated optional per-word annotations and an explicit distinction between user-supplied linguistic properties and unanalysed surface text.
- Extended the shared `SpekDocument` projection to `spek.document/0.3` with explicit word annotations and evidence details; PDF and TeX semantic trace rendering is unchanged.
- Added 9 source-explorer regression tests. Demonstration word annotations remain unqualified manual fixtures.
- No automatic GitHub publication, external state activation, SemantiK certification, or language translation.

# Changelog

## 0.2.0 — Rendering and semantic fidelity

- Added a versioned, derived `SpekDocument` projection used by HTML, PDF, LaTeX and `document.json`.
- Preserved all semantic IDs, status, evidence links and locators in the renderers.
- Prevented orphaned PDF trace blocks and corrected the French demo's third blank-like page.
- Added installed Unicode font discovery and fail-closed glyph checks on Windows/Linux.
- Localized provenance metadata and linked language pages to PDF, LaTeX and JSON exports.
- Grouped evidence, fixed repeated comparison criterion labels, and expanded regression testing.
- Kept v0.1 source/layout contracts and publishing protections unchanged.


## 0.1.0 — Initial Spek repository candidate

- Named the local publishing prototype **Spek** (spec / speak / speck).
- Kept the validated Kristal editorial input format identifiers at `0.1` for compatibility.
- Included three layouts and trilingual demonstration outputs.
- Added a versioned English wiki, integration notes, local Git instructions, and guarded publishing workflows.
- Explicitly documented missing upstream qualifications and authorization boundaries.

## 2026-11-02 — Refonte de l'atelier opérateur

- Nouveau lanceur principal Spek Studio en quatre espaces : Kristal, Composition, Aperçu Wiki, Publication.
- Recherche dans les 127 propositions IA existantes, sans inférence de template ni approbation implicite.
- Inspection privée conditionnée à une revue structurelle et à une correspondance exacte de la source locale.
- Import SemantiK, vérification et aperçu HTML locaux conservés.
- Ancien gestionnaire technique conservé en mode `--advanced`, accessible via « Outils avancés ».
- Interface opérateur sans affichage des empreintes et métadonnées techniques ; identité graphique `#1E6864` et logo existant conservés.
