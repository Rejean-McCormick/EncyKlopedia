# Carte technique : où chercher le code avant de l'écrire

Chemins **relatifs à l'ensemble indiqué**; voir le CSV de 488 modules pour fonctions et méthodes détaillées. Les signatures/DDL ici ont été inspectés dans des snapshots statiques. Certains modules ont évolué après les snapshots : confronter la version de code à migrer avec la version actuelle avant d'en copier un fragment.

## Pilotage et production — dépôt EncyKlopedia

| Domaine | Entrée réelle | Recherche à faire |
|---|---|---|
| Préparer branches v25 | `tools/unesco_pilot/generer_branches_unesco_v25.py` | `run`, lecture `microthesaurus_ids` |
| Catalogue/alignements | `tools/unesco_pilot/catalogue_global_v25.py` | `load_branch`, `source_by_qid`, schémas `assignments/reviewed_article_links_v28` |
| Découverte relationnelle | `tools/unesco_pilot/decouvrir_articles_relies_v28.py` | `collect_seed`, `bootstrap`, préfixes et catégories, `bootstrap_ontology` |
| Rappel ontologique | `tools/unesco_pilot/decouverte_relationnelle_v311.py` et moteur v28 | Chemins SKOS et budgets/cursors |
| Priorité UNESCO | `tools/unesco_pilot/priorisation_native_v31.py` | Score et sélection de candidats |
| Station v30 | `tools/unesco_pilot/poste_chatgpt_v30.py` | `Station`, création des packs, réception et import |
| Front web station | `tools/unesco_pilot/poste_chatgpt_v30.html`, `.js` | 10 lanes, flux principal, formulaires ZIP |
| Routage multibranche | `tools/unesco_pilot/routage_branches_v311.py` | `all_branches`, `refresh`, `prepare` et états DEFERRED |
| Pilotage multibranche | `tools/unesco_pilot/piloter_branches_v311.py` | command-line et orchestration |
| Cumul Kristal | `tools/unesco_pilot/production_kristals_v27.py` | `make_pack`, `validate_delta`, `import_delta`, `VerifiedXmlResolver` |
| Contextes UNESCO | `tools/unesco_pilot/contexte_revue_unesco_v28.py` | Extraits documentaires, provenance revue |
| Lecteur alpha | `src/server.mjs`, `src/catalog.mjs` | API lecture, démo et recherche privées |

## Thésaurus, P3916 et Wikidata

| Source | Emplacement | Nature |
|---|---|---|
| `UNESCO_Kristals` | `branches/*/canon/domain/unesco-source.json` | Source UNESCO organisée par branche, statut d'import non revu |
| `UNESCO_Kristals` | `branches/*/derived/wikidata-p3916-candidates.json` | Rapprochements QID candidats, statuts univoque/ambigu/absent |
| `UNESCO_Kristals` | `branches/*/derived/wikidata-full-facts-index.json` | Préparation locale de faits, **pas** un dump de statements lossless |
| `Kristal_UNESCO_Factory` | `unesco_wikidata_bridge.py` | Candidats P3916 et utilitaires de rapprochement |
| `UNESCO_Workbench` | `pipelines/unesco_total.py` | Préparation/vérification historique SKOS/RDF |
| `LinkedDataHub-UNESCO` | `demo.zip` | RDF SKOS daté 2025, à usage comparatif |
| `Skope` | `skope/db.py` | `node`, `neighbors` et index `entity_edge` en lecture |
| `Skope` | `skope/extraction.py` | Extractions Wikidata originales ciblées; **externe intouchable** |

## Wikipédia et représentation

| Source | Emplacement | Nature |
|---|---|---|
| `mediatheque-references` | `tools/wiki/dump_import/import_dumps.py` | Import SQL `wiki_pages`, `wiki_qid`, liens et catégories |
| `mediatheque-references` | `tools/wiki/atlas/atlas_wikipedia.py` | Accès index/atlas et graphes Wikipédia |
| `mediatheque` | `05_TOOLS/KoaKristalSources.py` | Médiathèque partagée, sources/références |
| `mediatheque` | `05_TOOLS/ImportEncyKHandoff.py` | Handoff source historique |

## UIs, audits et outils isolés

- `ENCYK_CENTRE_PILOTAGE_V313/V314` : `CENTRE_PILOTAGE_ENCYK_V314.pyw`, `encyk_triage_v314.py`, `encyk_global_v313.py`.
- `EncykAudit` : `AUDIT_AUTOMATIQUE_BRANCHE_V312.pyw`, exports CSV/JSON, `ACTIVER_AUDIT_QUOTIDIEN_V312.ps1`.
- `LevelUpDiag_EncyK` : `levelupdiag.py` avec campagnes.
- `ENCYKLOPEDIA_EXPORT_CHATGPT` : `exporter.py`, SmartDump d'inventaire.
- Sauvegardes V2/V3 : code de snapshot SQLite, vérification de récupération; les ZIP de base de résultats ne sont pas un dépôt de code.

## Si un nom manque dans cette carte

Rechercher dans [`inventaire_modules.csv`](../07_INVENTAIRES/inventaire_modules.csv) via `depot`, `fichier`, `fonctions`, `methodes_classes`, `options_cli`; ce catalogue est une indexation **des signatures statiques**, et non une garantie de fonctionnement. Les scripts shell, JS et JSON de données sont explorés dans leurs répertoires de source cités ici.
