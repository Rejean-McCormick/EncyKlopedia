# Matrice de réemploi : fonction cible → code source existant

Cette matrice indique **où regarder en premier**. Les chemins sont relatifs au dépôt indiqué et les noms de fonctions ont été observés statiquement dans les snapshots. La cible décrit des **adaptations**, non une promesse que le module fonctionne sans changement.

| Fonction cible | Dépôt / code réutilisable | Fonctions / remarques concrètes | Décision |
|---|---|---|---|
| Générer la liste des branches | `EncyKlopedia/tools/unesco_pilot/generer_branches_unesco_v25.py` | `run(source,dest,revision,prefix)`, `BRANCHES_INDEX_V25.json`; source `microthesaurus_ids` | Réutiliser le partitionnement; **ajouter crosswalk** au lieu de refondre |
| Charger les concepts UNESCO | `catalogue_global_v25.py` | `load_branch`; `concepts`, `branch_concepts`, `branches`, `assignments` | Garder compatibilité des identités; ne pas porter toute l'ancienne base |
| Correspondance P3916 | `UNESCO_Kristals/branches/*/derived/wikidata-p3916-candidates.json` et `Kristal_UNESCO_Factory/unesco_wikidata_bridge.py` | `read_claims`, `read_inventory`, `local_entity`; 4 289 candidats uniques | Convertir en assertions de mapping avec statut |
| Comparer source SKOS 2025 | `UNESCO_Workbench/pipelines/unesco_total.py` | `verify_historical_rdf`, `comparison`, `make_view` | Réutiliser comme outil de lecture/audit, pas dépendance runtime |
| SQL Wikipédia QID→page | `mediatheque-references/tools/wiki/dump_import/import_dumps.py` et `catalogue_global_v25.py` | `wiki_qid`, `wiki_pages`, `source_by_qid` | Requête en lecture seule, pas nouvel import |
| Liens, catégories | `mediatheque-references/tools/wiki/atlas/atlas_wikipedia.py` et `decouvrir_articles_relies_v28.py` | `wiki_categorylink_ids`, `wiki_pagelinks`, `collect_seed` | Fallback et rappel, après jointures directes |
| Structure Wikidata QID/graphes | `Skope/skope/db.py` (EXTERNE) | `connect`, `node`, `neighbors`, `induced_edges` | Utiliser interfaces exposées, ne pas copier le code |
| Wikidata lossless | `Skope/skope/extraction.py` (EXTERNE) | `preflight`, `start`, `status`, `open_results` | Adapter les appels existants, données originales ciblées |
| Préparation revue UNESCO | `poste_chatgpt_v30.py` et `contexte_revue_unesco_v28.py` | `Station._prepare_v28`, `prompt`, `merge_review`; extraits XML locaux | Récupérer méthode de lot/retour, changer modèle des décisions V32 |
| Classification locale v31 | `qualification_globale_v31.py` | `definitions`, `classify`, `article_profiles` | **Ne pas** reprendre la boucle N pages × 4 500 concepts comme chemin principal |
| Recherche large v31.10 | `decouvrir_articles_relies_v28.py` | `bootstrap`, `_scan_prefix`, `_scan_category` et curseurs | Fallback notionnel, pas colonne vertébrale |
| Rappel via SKOS v31.11 | `decouvrir_articles_relies_v28.py` | `bootstrap_ontology`, `_relation_paths` et `_scan_relation` | Idées de budget et provenance réutilisables |
| Récupération DEFERRED v31.12 | `poste_chatgpt_v30.py` | `_prepare_v28`, sélection `PENDING` **et** `DEFERRED` | Réutiliser le principe pour éviter réserve oubliée |
| Liste de tâches / stations | `poste_chatgpt_v30.py` | `Station`, `jobs`, `lanes`, `bundle`, `receive`, `_import_one` | Récupérer file durable, métier deux passes distinct |
| Export JSON/ZIP retour | `production_kristals_v27.py` | `make_pack`, `verify_pack`, `validate_delta`, `import_delta` | Reprendre le protocole avec nouveau `subject_kristal_id` |
| Lire texte XML entier | `production_kristals_v27.py` | `VerifiedXmlResolver`, `page_from_index`, `validated_sources` | Adapter sur pages sélectionnées, ne pas tronquer l'article source |
| Vérifier provenance claim | `production_kristals_v27.py` | `source_quote`, `source_revision_id`, citations, `article_visits` | Conserver une citation réelle pour chaque fait, éviter survalidation |
| Ecrire cumul privé | `production_kristals_v27.py` | `claims`, `citations`, `claim_concepts`, `claim_branches` | Réutiliser logique de déduplication; schéma V32 orienté sujet |
| Lire/servir encyclopédie | `EncyKlopedia/src/server.mjs`, `src/catalog.mjs` | `/api/v1/search`, `/api/v1/articles/:slug`, lecture privée | Utile pour lecteur futur, pas pour manager principal |
| Statistiques & audits | `statistiques_globales_v31.py`, `CENTRE_PILOTAGE_ENCYK_V314.pyw` | Comptes, écarts, exports | Un seul onglet avancé « Diagnostics » dans manager |
| Préserver sources | `mediatheque/05_TOOLS/KoaKristalSources.py`, `ImportEncyKHandoff.py` | `source_uuid`, imports Skope handoff | Dépendance partagée facultative; ne pas copier le moteur |
| Diagnostic externe | `LevelUpDiag_EncyK/levelupdiag.py` | campagnes `quick`, `reader`, `bridge`, `standard` | Réutiliser les tests et afficher leurs résultats |
| Découverte des repos | `ENCYKLOPEDIA_EXPORT_CHATGPT/exporter.py` | exporter des contextes/SmartDump ciblés | Intégrer outil support, pas un écran permanent |

## Anti-réécriture

Avant une nouvelle fonction : chercher dans [`inventaire_modules.csv`](../07_INVENTAIRES/inventaire_modules.csv) par nom, option CLI, classe ou fichier. Lire ensuite la fonction réelle. L'index des fonctions est une **carte de navigation**, pas un contrat d'API stable. L'interface V32 doit encapsuler un module réutilisé et posséder ses propres tests d'adaptation.

## Modules à ne PAS déplacer automatiquement

- Code Skope ou Kristalizer ; même si une copie figure dans SmartDump, **hors périmètre**.
- Index/dumps D: (SQLite Wikidata compact, SQL Wikipédia, XML Wikipédia, offsets) : rester en place.
- Médiathèque partagé si d'autres bibliothèques l'utilisent : liaison externe.
- Artefacts de pilote `mt1.10`/ZIPs déjà importés : archives et références, pas dépendances de V32.
