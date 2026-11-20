# 01 — Inventaire des données, par autorité et par usage

## 1. Données de référence existantes

| Source/ensemble | Emplacement Windows ou origine | Représentation | Autorité et usage | Statut de vérification |
|---|---|---|---|---|
| UNESCO — thésaurus et microthésaurus | `C:\mycode\EncyKlopedia\UNESCO_Kristals` et copie de 88 définitions `...\encyk_v32_NEUF_87_...\unesco_88_sources\branches` | `canon/domain/unesco-source.json`; `derived/wikidata-p3916-candidates.json` | 88 branches et concepts; la copie V32 détermine l'espace de travail, sans réimport V31 | **88/88 dans journal V6 d'activation** ; définitions 41 concepts MT1.10 vierges |
| Crosswalk UNESCO→Wikidata | Chaque branche `derived/wikidata-p3916-candidates.json` | Correspondances **candidates** P3916, état SINGLE/AMBIGUOUS/NO_MAPPING | Amorçage des QID; **pas** affectation canonique par QID | `import_unesco()` réel, statuts documentés |
| Wikidata compact global / Skope | `D:\EncyKlopedia\30_working\wikidata\wikidata.compact.sqlite` | Tables `entity`, `name`, `entity_edge`, `meta`; arêtes agrégées | Recherche et voisinage; **aucun `statement_id`, qualifiers et références individuelles dans ce compact** | Schéma confirmé par `skope/db.py`; volume ~134 Go historique **non rescanné** |
| Données Wikidata originales lossless | Dump et index de localisation rapide **si présents** dans volume de données | JSON entité complet ciblé, références, qualificatifs, sitelinks | Source possible d'extraction structurée avec provenance; Skope `extraction.py` a un mode opt-in | Code présent; chemins/matérialisation effective **non vérifiés** |
| Wikipédia index de pages / QID | `D:\EncyKlopedia\80_search_indexes\mediatheque-references\wikipedia_en.sqlite` | `wiki_qid`, `wiki_pages`, index des titres | Chercher `page_id`, `latest_revision`, titre et QID, candidats | Utilisé avec succès sur Météorologie ; taille actuelle non vérifiée |
| Wikipédia index direct de texte | `D:\EncyKlopedia\80_search_indexes\mediatheque-references\wikipedia_en_direct_pages_v21.sqlite` | Offsets/registre direct | Accès par ID à la révision du texte XML, sans parcours complet | Extraction des packs réels confirme fonctionnement |
| XML Wikipédia original | `D:\EncyKlopedia\30_working\wikipedia_en_uncompressed\enwiki-latest-pages-articles-multistream.xml` | Texte encyclopédique ~110 Go (historique) | Source textuelle exacte de la citation; pages extraites par index direct | Fichiers d'ENR attestent d'un contenu lu, pas d'un scan intégral |
| Catalogue global UNESCO–Wikipédia V25 | `D:\EncyKlopedia\80_search_indexes\EncyKlopedia\catalogue_global_unesco_wikipedia_v25.sqlite` | Index partagé historique de routes/candidats | Préservation et possibilités de réemploi V27/V28; **ne pas déplacer** | Code `catalogue_global_v25.py`, rapports d'audit |
| Médiathèque C: et D: | `C:\mycode\EncyKlopedia\mediatheque[-references]` et index D: | Sources et index secondaires | Hors zone de modification; source éventuelle via contrat | Protégée par décision d'architecture |
| Kristals UNESCO vivants | `C:\mycode\EncyKlopedia\UNESCO_Kristals` | `canon/state.index.json`, artefacts `build/v9` | Véritable état d'îlots canoniques indépendants | Audit du 16/11 : 88 branches avec état `build/v9`; lecture seule dans EncyK |

### Remarques de sûreté

- Les chiffres 134 Go, 110 Go et les 88 îlots sont des **informations issues d'audits/situations rapportées**. Le présent pack ne s'est pas connecté au poste Windows pour les revérifier.
- Skope **n'est pas synonyme de dump Wikidata lossless**. Le compact est optimisé pour explorer. L'extraction complète exige dump original vérifié et index rapide existant ; jamais de scan complet accidentel.
- Les sources UNESCO copiées dans le *nouveau registre* sont des définitions, pas des décisions V31. `unesco.mt1.10` est vierge dans V32 même si son histoire est archivée.

## 2. Données produites par le moteur V32

| Zone | Tables/fichiers exacts | Contenu et réutilisation |
|---|---|---|
| Concepts et correspondances | `branches`, `concepts`, `branch_concepts`, `concept_aliases`, `mappings` | Taxonomie locale, alias, candidats QID; plusieurs concepts/branches possibles |
| Découverte | `candidates`, `candidate_routes`, `graph_cursors`, `fallback_cursors`, `v6_link_seed_cursor` | Couple article/concept/branche, origine, priorité et curseurs reprenables |
| Distribution et postes | `jobs`, `job_items`, `active_items`, `lanes` | ZIPs actifs/réservations; **dix postes globaux** et non dix par branche |
| Sélection | `decisions`, `decision_history` | SELECT, REJECT, HOLD contextualisés, audit historique |
| Texte de source / couverture | `article_sources`, `source_results`, `candidate_extractions` | Page + révision + hash texte + profil, couverture `PROCESSED`/`PARTIAL`; réemploi strict |
| Connaissances privées | `proposals`, `proposal_concepts`, `proposal_citations`, `proposal_occurrences`, `proposal_replacements` | Faits, objets typés, concepts, provenance et corrections; **non canoniques** |
| Retours et anomalies | `receipts`, `return_archives`, `import_errors`, `events`, `candidate_failures` | ZIP reçus hachés, erreurs par ligne, files réessayables |
| Fédération lecture seule | `kristal_islands`, `island_branch_links`, `island_locations` | Références vers les îlots existants sans canon créé automatiquement |
| ZIP prêts | `etat_v32/packs/SEL_*.zip`, `ENR_*.zip` | Sources d'une tâche figées avec identifiant job + empreinte |
| Retours reçus | `etat_v32/returns/<sha256>.zip` | Contenu entrant conservé pour audit; aucun ZIP de réponse ne constitue du code exécutable |

## 3. Archives historiques : source d'acquis techniques, pas nouveau registre

- Archive historique du pilote : `D:\EncyKlopedia_ARCHIVES\V31_UNESCO_MT1_10_20261116T202122Z_5614645f`.
- Contient les trois dossiers déplacés `decouverte_articles_relies_v28`, `poste_chatgpt_v30`, `production_kristals_v27` (avec anciens packs, WAL et états).
- Les cinq SQLite sauvegardées séparément par l'archiveur V5; WAL de `station_v30` **conservé**, aucune suppression arbitraire.
- V32/88 réutilise le **code** de ces outils, pas leurs décisions MT1.10; aucune suppression de l'archive.
- Données historiques du pilote : **201 006 décisions décidées**, **22 509 HOLD** (bilan daté), zéro tâche UNESCO ouverte à l'époque; **clôture scientifique non démontrée**.

## 4. Cas Météorologie, observations réelles

Extrait des journaux du 17/11/2026, branch `unesco.mt2.45` :

- Après correction Skope, le compact a permis de passer de **27** à **631** candidats (10 768 voisins inspectés, 615 routes de graphe); après complément V6, **2 460 candidats**.
- **575 SELECT**, **56 REJECT**, **0 HOLD** sur les 631 premiers candidats.
- **10 606 propositions privées** cumulées, **320 articles traités** et **253–254 PARTIAL** selon le moment du journal; ces compteurs ne doivent pas être confondus avec l'exhaustivité des textes.
- Après découverte additionnelle, **sept missions `SEL_000008` à `SEL_000014`**, six de 300 candidats et une de 30 : total 1 830 paires candidat/concept.
- Les journaux ont aussi révélé des erreurs d'import : 379 sur `ENR_000007`, 47 sur `ENR_000018`, 80 sur `ENR_000022` ; total **506 faits invalides**, sans suppression des faits valides.

**Attention :** la station compte des **paires candidat/concept** et des **propositions soumises/acceptées**, pas nécessairement autant d'articles uniques, ni autant de faits scientifiquement confirmés.

## 5. Principes de fraîcheur et d'autorité

1. Enregistrement de la source originale : chemin ou locator, format, version de dump/revision, hash/epoch documenté.
2. Travail IA : version du prompt, identifiant job, ensemble exact des pages/révisions, profil d'extraction.
3. Import : accusé, hash du ZIP, erreurs, relation entre occurrences et propositions distinctes.
4. Vie de la proposition : DRAFT / UNASSIGNED / SUPERSEDED et statut canonique **toujours indépendant**.
5. Nouvelles révisions sources : la preuve précédente ne disparaît pas; réextraction sur source changée seulement quand justifié.
