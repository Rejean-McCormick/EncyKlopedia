# Chemins Windows et schémas SQLite existants

## Répertoires observés dans le code et les audits

| Source | Chemin Windows | Tables/usage connus |
|---|---|---|
| Dépôt principal historique | `C:\mycode\EncyKlopedia\EncyKlopedia` | scripts source et ancien launcher `LANCER_ENCYKLOPEDIA.cmd` |
| Données de production | `D:\EncyKlopedia` | plusieurs espaces de travail V25/V27/V28/V30 |
| Catalogue v25 | `D:\EncyKlopedia\80_search_indexes\EncyKlopedia\catalogue_global_unesco_wikipedia_v25.sqlite` | `branches`, `concepts`, `branch_concepts`, `articles`, `assignments`, revues importées |
| Index SQL Wikipédia anglais | `D:\EncyKlopedia\80_search_indexes\mediatheque-references\wikipedia_en.sqlite` | `wiki_pages`, `wiki_qid`, `wiki_pagelinks`, catégories |
| Offsets XML Wikipédia v21 | `D:\EncyKlopedia\80_search_indexes\mediatheque-references\wikipedia_en_direct_pages_v21.sqlite` | récupération d'une page XML à l'offset |
| XML articles décompressé | `D:\EncyKlopedia\30_working\wikipedia_en_uncompressed\enwiki-latest-pages-articles-multistream.xml` | texte complet, peut dépasser 100 Go |
| Index Wikidata compact | `D:\EncyKlopedia\30_working\wikidata\wikidata.compact.sqlite` | `entity`, `name`, `entity_edge`, `meta` |
| Découverte v28 | `D:\EncyKlopedia\30_working\decouverte_articles_relies_v28\DECOUVERTE_ARTICLES_RELIES_V28.sqlite` | `seed_queue`, `candidates`, `evidence`, curseurs |
| Station v30 | `D:\EncyKlopedia\30_working\poste_chatgpt_v30\station_v30.sqlite` | `jobs`, `lanes`, `review_index`, `receipts` |
| Queue Kristal v27 | `D:\EncyKlopedia\30_working\production_kristals_v27\FILE_PACKS_V27.sqlite` | queue pages et packs |
| Cumul privé Kristal v27 | `D:\EncyKlopedia\30_working\production_kristals_v27\KRISTAL_CUMULATIF_PRIVE_V27.sqlite` | claims, citations, visites, affectations |
| Sauvegardes v3 | `D:\EncyKlopedia_SAUVEGARDES` | snapshots des cinq bases de résultats, pas dump XML |

**Important :** les chemins sont des **valeurs observées**, pas des dossiers à recréer pendant l'étape documentation. Les 5 bases résultat v3 ne comprennent ni le dump ni les index massifs de Wikipédia ou Wikidata. V32 devrait utiliser un **config** de chemins modifiables et rendre explicite « absent » au lieu de recréer les corpus.

## Schémas natifs à connaître

### Index Wikipedia

`wiki_pages(page_id PK, ns, title, redirect, latest_revision, content_bytes)`, `wiki_qid(page_id PK, qid)`, `wiki_linktargets(target_id PK,ns,title)`, `wiki_pagelinks(source_page_id,target_id)`, `wiki_categorylinks(...)`, `wiki_categorylink_ids(source_page_id,target_id,type)`, vue `wiki_categorylinks_resolved`. Importeur : `mediatheque-references/tools/wiki/dump_import/import_dumps.py`.

Les index `idx_wiki_qid_qid`, `idx_wiki_pages_title`, `idx_wiki_lt_title`, `idx_wiki_catid_from`, `idx_wiki_catid_target` sont requis/observés par `catalogue_global_v25.checked_source`. Une requête sur D: doit vérifier son plan si elle risque de balayer 125 Go; **pas** de `quick_check` mondial obligatoire à chaque lancement.

### Catalogue v25

`branches`, `concepts`, `branch_concepts`, `articles`, `assignments`, `category_suggestions`, `category_tasks`, `audit_events`, `meta`, registre `reviewed_article_links_v28` créé par revue. `assignments` représente une relation paire concept/article; un même article peut avoir plusieurs affectations. L'auditeur ancien a déjà confondu `assignments` et registre de décisions : **garder ces deux catégories distinctes**.

### Découverte v28/v31

`candidates`, `evidence`, `seed_queue`, `seed_revision_mismatches`, plus curseurs `v3110_probe_cursor`, `v3110_category_roots`, `v3111_relation_cursor`. Les états de découverte ne sont pas les états des décisions station. La découverte peut être figée pendant des revues ouvertes pour conserver les preuves.

### Station v30

`jobs`, `lanes`, `review_index`, `receipts`, `events`, `updates`, `hold_reexaminations`, `v311_job_routes`, `meta`. `jobs.kind` sépare UNESCO `v28` et Kristal `v27`; `jobs.status` inclut `WAITING,READY,SENT,ERROR,IMPORTING,NEEDS_CONFIRMATION,DONE,SKIPPED`. `review_index.state` inclut `PENDING,DEFERRED,QUEUED,DECIDED,HOLD,STALE`.

### Kristal v27

`FILE_PACKS`: `queue`, `packs`, `source_epoch_history`, `meta`.

`KRISTAL_CUMULATIF`: `claims`, `citations`, `claim_concepts`, `claim_branches`, `article_visits`, `delta_imports`, `text_variants`, `meta`. Le `claim_key` distingue les faits; plusieurs citations pour un même fait sont possibles. Les entités de V32 seront **sujets**, pas nécessairement pages.

Une cartographie exhaustive des `CREATE TABLE/INDEX` repérés statiquement dans les modules est disponible sous [`../07_INVENTAIRES/schémas_sql_statiques.json`](../07_INVENTAIRES/schémas_sql_statiques.json). Le JSON de cartographie **n'est pas** un dump du schéma de tes bases Windows; les migrations historiques peuvent l'avoir enrichi.

## Politique de V32

- Sources massives : connexions `mode=ro`; aucun ALTER/CREATE dans les index externes.
- Stockage de travail : nouvelle base propre dans un répertoire `D:\EncyKlopedia\V32` (chemin **proposé**, configurable), avec journal de jobs et curseurs.
- Sauvegarde : pouvoir sauvegarder rapidement seulement l'état de travail/les résultats, sans recopier les dizaines/centaines de Go de sources reconstructibles.
- Anciens registres : rester archivés, consultables, sans les imposer comme schéma du nouveau moteur.
