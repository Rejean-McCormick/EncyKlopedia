# Cartographie vérifiée de l'existant et écarts avec la cible

**Source primaire :** `DIAGNOSTIC_EXISTANT_ET_GRANULARITES_ENCYK_V30.zip`, généré le **13 novembre 2026, vers 10:00**.  
**Sources secondaires :** packs UNESCO v28 et contrat d'import, tests et noms de fonctions observés dans le diagnostic, audit de réutilisation livré dans la conversation.  
**Niveau de preuve :** schémas SQLite, nombres de lignes de petites tables, noms de fonctions et présence de fichiers. **Pas d'accès direct au contenu des scripts natifs ou aux index massifs depuis cette conversation.**

## 1. Index et corpus massifs — ne pas dupliquer

| Ressource | Réalité vérifiée | Point à confirmer |
|---|---|---|
| `D:\EncyKlopedia\80_search_indexes\mediatheque-references\wikipedia_en.sqlite` | ~125,6 Go ; `wiki_pages`, `wiki_pagelinks`, `wiki_linktargets`, `wiki_categorylinks`, `wiki_categorylink_ids`, `wiki_externallinks`, `wiki_qid`, `ingest_state` | `COUNT` complet, source/snapshot, couverture `ns=0`, performances des jointures, résolution des redirections |
| `...\wikipedia_en_direct_pages_v21.sqlite` | 25 932 219 lignes `pages`, champs `page_id,byte_offset,byte_length,namespace,title,revision_id,is_redirect` ; ~1,55 Go | Index compatible avec **quel** XML ; ne pas réutiliser les offsets avec le dump courant sans vérification |
| `...\wikipedia_en_multistream_offsets_v20.sqlite` | Tables `page_offsets`, `streams` ; ~48,6 Mo | Format/source de création et compatibilité du dump |
| `D:\EncyKlopedia\30_working\wikipedia_en_uncompressed\enwiki-latest-pages-articles-multistream.xml` | XML présent, ~117,84 Go | Empreinte/version compatible avec les index, validité des offsets |
| `...\inventaire_categories_wikipedia_v26.sqlite` | ~1,32 Go, tables `categories` et FTS5 sur **titres de catégories** | Complétude de l'inventaire de catégories et fonction de recherche effective |
| `D:\EncyKlopedia\30_working\wikidata\wikidata.compact.sqlite` | Base ~134,2 Go identifiée ; `wiki_qid` dans l'index pages | Schéma et correspondances QID effectives ; ne pas scanner intégralement |
| Bases lexicales locales | Index de lemmes, formes, lexèmes et rapprochements linguistiques | Usage concret dans le score sémantique ; **ne pas** les assimiler à des passages d'articles |

**Attention :** 25 932 219 est le nombre d'entrées de l'index direct, **pas** le nombre d'articles encyclopédiques, de titres uniques ni de contenus utilisables. Le premier compteur mondial à produire devra spécifier `namespace`, redirection et instantané.

## 2. Catalogue UNESCO v25 — déjà multibranche au niveau du modèle

Fichier : `D:\EncyKlopedia\80_search_indexes\EncyKlopedia\catalogue_global_unesco_wikipedia_v25.sqlite` (~5,55 Mo).

| Table | Colonnes clés observées | Lignes du diagnostic |
|---|---|---:|
| `branches` | `branch_id,vocabulary,branch_version,title_fr,config_sha,...` | 1 |
| `concepts` | `vocabulary,concept_id,label_fr,label_en,broader_json,related_json` | 41 |
| `branch_concepts` | `branch_id,vocabulary,concept_id` | 41 |
| `articles` | `wiki,page_id,title,qid,revision_id,content_bytes` | 2 115 |
| `assignments` | `branch_id,wiki,page_id,vocabulary,concept_id,score,evidence_kind,...` | 2 358 |
| `reviewed_article_links_v28` | `branch_id,concept_id,page_id,candidate_id,evidence_sha256,decision,...` | 9 531 |
| `category_tasks` | `branch_id,concept_id,root_category,target_id,depth,state,...` | 31 |
| `category_suggestions` | `branch_id,concept_id,category_title,lexical_score,review_state` | 23 |
| `reviewed_bridges_v26` | `branch_id,concept_id,category_title,target_id,depth_limit,justification` | 28 |
| `reviewed_bridge_imports_v26` | Schéma, empreinte, nombre de décisions importées | 1 |
| `audit_events` | `event_id,branch_id,kind,description,created_utc` | 84 |

**Interprétation :** la structure `branches` + `branch_concepts` + `assignments` représente déjà des affectations multibranches ; aucun nouveau catalogue central n'est prescrit. Le diagnostic ne prouve pas que toutes les branches UNESCO sont déjà configurées. Les tests natifs détectés comportent `test_multi_branches_shared_articles_no_double_global_records` : ceci constitue un **indice fort de prise en compte** des articles communs, à valider par lecture du code et exécution des tests dans l'environnement installé.

## 3. Découverte et station — état réel, protections existantes

**Découverte v28** : `D:\EncyKlopedia\30_working\decouverte_articles_relies_v28\DECOUVERTE_ARTICLES_RELIES_V28.sqlite` (~31,2 Mo).

- `candidates` : **39 301** lignes, colonnes `branch_id, concept_id, page_id, title, revision, first_seen`.
- `evidence` : **100 096** lignes, colonnes `branch_id, concept_id, page_id, seed_page_id, kind, detail`.
- `seed_queue` : **1 225** lignes ; `seed_revision_mismatches` : **13** lignes ; les divergences sont journalisées, pas à effacer.
- Les catégories partagées génèrent beaucoup de bruit : les filtres visés doivent **déprioriser**, pas effacer de l'inventaire.

**Station v30** : `D:\EncyKlopedia\30_working\poste_chatgpt_v30\station_v30.sqlite` (~9,25 Mo).

- `review_index` : **36 786** entrées, avec `candidate_id`, `branch_id`, `concept_id`, `page_id`, preuve et statut.
- `jobs` : **108** enregistrements, avec `id,kind,key,count,status,source_sha256,bundle_sha256,...`.
- `lanes` : files de répartition, `receipts` : réceptions, `events` : journal, `updates` : mises à jour suivies.
- Le gel des preuves lorsque des revues sont en cours est **une protection volontaire** à conserver.
- Ces comptes décrivent le stock du diagnostic ; ils ne donnent ni le nombre de propositions nouvelles futures ni un pourcentage exhaustif de branche achevée.

**Contrat revues v28 confirmé par les ZIP :** `REVUE_v28_<id>.csv`, éventuellement `CONTEXTES_DOCUMENTAIRES_V28.jsonl` et manifeste ; retour strict `DECISIONS_v28_<id>.csv` (`candidate_id,decision,justification`).

## 4. Kristal — réutilisable mais circuit isolé

`D:\EncyKlopedia\30_working\production_kristals_v27\KRISTAL_CUMULATIF_PRIVE_V27.sqlite` (~9,74 Mo) :

- `claims` : **4 119** ; `citations` : **4 119**, avec `page_id`, `revision_id`, `section_hint`, `source_quote`, `wikitext_sha256`.
- `claim_branches` : **4 119**, `claim_concepts` : **3 882**, `article_visits` : **1 225**, `delta_imports` : **96**.
- Ce schéma prouve que le produit **sait déjà localiser certaines citations** dans les articles visités. Il ne prouve pas la disponibilité d'un index universel de paragraphes ou de sections Wikipédia.
- Une qualification globale peut aider à orienter les articles vers Kristal, mais elle ne transforme pas ses assertions privées en connaissances canoniques.

## 5. Modules natifs détectés — audit du code nécessaire

Chemins relatifs au dépôt `C:\mycode\EncyKlopedia\EncyKlopedia` :

| Module | Rôle probable d'après le nom, les fonctions et les tests | Niveau de certitude |
|---|---|---|
| `tools\unesco_pilot\catalogue_global_v25.py` | Catalogue, branches, concepts, sécurité de source | Existence confirmée ; implémentation non lue |
| `tools\unesco_pilot\generer_branches_unesco_v25.py` | Génération initiale des branches | Existence confirmée ; règles à lire |
| `tools\unesco_pilot\inventaire_categories_v26.py` | Indexation et recherche de catégories | Fonctions `inventory`, `ingest`, `search_category`, `score` signalées |
| `tools\unesco_pilot\semantic_candidate_stage_v4.py` | Étape préparatoire de candidats sémantiques | Fonctions `build`, `write_stage`, vérifications identifiées |
| `tools\unesco_pilot\semantic_candidate_stage_v6.py` | Construction/installation d'un stade sémantique | Fonctions `build`, `install` et tests d'immutabilité identifiés |
| `tools\unesco_pilot\local_wikipedia_bridge.py` | Adaptateur de requêtes aux index Wikipédia locaux | Fonction `query_wikipedia`, noms et contrats réels à vérifier |
| `tools\unesco_pilot\decouvrir_articles_relies_v28.py` | Découverte, liens, catégories, seeds et revue | Fonctions `collect_seed`, `parse_wikilinks`, `candidate_id` signalées |
| `tools\unesco_pilot\contexte_revue_unesco_v28.py` | Enrichissement documentaire et accès aux extraits | Fonctions `_open_optional_xml_context`, `_targeted_passages` signalées |
| `tools\unesco_pilot\poste_chatgpt_v30.py` | Propriétaire des tâches, protections, ZIP et imports | Classe `Station` et fonctions de contrôle identifiées |
| `tools\unesco_pilot\production_kristals_v27.py` | Packs et suivi de la production privée | Fonctions `make_pack`, `verify_pack`, `recover_orphans` signalées |

Les tests de dépôt détectés couvrent des préoccupations intéressantes : verrou de preuves, idempotence, non-duplication des articles entre branches, intégrité des ZIP, cohérence des révisions. **Seuls leurs noms ont été relevés : leur exécution et leurs assertions effectives restent à vérifier.**

## 6. Écarts à combler par ordre de priorité

| Priorité | Besoin réel | Etat | Décision |
|---|---|---|---|
| P0 | Vérifier couverture du corpus et `ingest_state` | Inconnu | Lire le code et quelques métadonnées ciblées |
| P0 | Confirmer résolution `target_id → page_id` et redirections | Inconnu | Tester sur échantillons connus |
| P0 | Sécuriser l'accès XML / v21 | Incompatibilité signalée | Diagnostic de signatures, révisions et offsets sans désactivation du garde-fou |
| P0 | Audit effectif des stades v4/v6 et des branches v25 | Contrats non lus | Réutiliser l'existant plutôt qu'ajouter un moteur parallèle |
| P1 | Statistiques mondiales/branches cohérentes | Modules autonomes développés, raccordement partiel | Adapter aux tables natives après revue |
| P1 | Profil documentaire global versionné | Non démontré | Réemployer un module existant si possible, sinon petit cache |
| P1 | Qualification multibranche / article–concept | Modèle de branche existant ; préqualification complète non démontrée | Ajouter uniquement le maillon absent |
| P1 | Audit du rappel et des différés | Non démontré | Nouveau journal non destructif et échantillonnage |
| P2 | Nouvelle taille de packs native | Planificateur autonome ; raccordement natif non vérifié | 110 puis essais 150–200/300 |
| P3 | Index global de paragraphes ou vecteurs | Aucun besoin démontré à ce stade | Ne pas créer avant preuve de nécessité |

## 7. Interdictions dérivées du diagnostic

Ne pas prendre les tables FTS5 `categories_fts_data`, `categories_fts_idx` pour des paragraphes ou des tokens des articles Wikipédia. Ne pas utiliser les lexèmes comme positions de mots dans le XML. Ne pas déduire le pourcentage d'achèvement de l'encyclopédie à partir des 39 301 candidats, des 36 786 lignes de station ou des 9 531 revues. Ne pas supposer qu'un module détecté est activement branché dans la station. Ne pas faire un `COUNT(*)` intégral sur la base de 125 Go au démarrage du tableau de bord : privilégier des compteurs d'ingestion fiables et des contrôles bornés.

**Bilan :** la majeure partie des briques de bas niveau est **présente**. Le travail porte d'abord sur la validation de leurs contrats, leur orchestration, les statistiques et une qualification multibranche non destructrice, pas sur la création d'un autre graphe mondial.
