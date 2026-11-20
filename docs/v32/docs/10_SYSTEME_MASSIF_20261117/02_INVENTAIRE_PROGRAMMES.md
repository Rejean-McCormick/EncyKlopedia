# 02 — Inventaire des programmes, possibilités et réemploi

## Comment l'inventaire a été constitué

Les scripts/fichiers sont extraits et hachés **depuis quatre ZIP concrets fournis par le projet**. Les tableaux `inventaires/FICHIERS_SNAPSHOTS.csv` et `inventaires/PROGRAMMES_DETECTES.csv` recensent les occurrences, y compris doublons et code historique : une occurrence **ne prouve pas** que le module est installé ou exécuté sur le Windows réel. Le parseur AST relève les fonctions/classes de premier niveau; la classification par répertoire reste **indicative**.

| Snapshot source | Fichiers observés | Scripts détectés (py, pyw, ps1, cmd, sql) | Rôle |
|---|---:|---:|---|
| V32.2 dépôt complet | 5 305 | Voir inventaire CSV | Moteur, outils historiques, docs, tests, sources |
| Station de production V6 | 34 | Voir inventaire CSV | Interface 88 branches / 10 postes, adaptateurs |
| Snapshot Skope | 505 | Voir inventaire CSV | Index/Wikidata, profils, extraction ciblée |
| Snapshot Kristalizer | 57 | Voir inventaire CSV | Analyse d'îlots, staging et Kit externe |
| **Total occurrences** | **5 901** | **889** | Comptes d'archives, non programmes indépendants |

L'inventaire historique `docs/v32/docs/07_INVENTAIRES/ATLAS_MODULES.md` compte **488 modules Python** des snapshots étudiés lors de V32. Ce n'est pas contradictoire avec les 889 scripts ci-dessus (périmètres/versions/types différents). Conserver les deux atlas, **ne pas convertir des occurrences en « modules actifs »**.

## A. Moteur central V32.2 (ACTUEL)

| Fichier | Fonctions vérifiées | Ce qu'il sait faire | Ce qu'il ne fait pas |
|---|---|---|---|
| `encyk_v32/config.py` | `Settings.load`, variables `ENCYK_*` | Chemins séparés C/D et paramètres budgets; valeurs explicites | Localiser automatiquement tous les dumps ni créer un Kit |
| `encyk_v32/sql.py` | `open_work`, `read_source`, DDL V32/2 | Registre privé, migration qualifiée, verrou sérialisé, SQLite RO | Stocker tous les JSON originaux de Wikidata compact |
| `encyk_v32/sources.py` | `import_unesco`, `discover`, `discover_fallback`, `WikidataGraph`, `WikipediaIndex` | Mappings QID, voisins agrégés, candidats et curseurs; titre préfixe | Exploration complète de toutes les catégories; preuve Wikidata statement dans le compact |
| `encyk_v32/pipeline.py` | `make_selection`, `make_enrichment`, `make_wave`, `import_for_job`, `retry_candidates`, `cancel_job`, `export_proposals` | ZIP, deux passes, réservations, validation partielle, dédup exacte et corrections | Garantir vérité sémantique de chaque proposition; automatiser ChatGPT |
| `encyk_v32/federation.py` | `scan_islands`, `export_federated_read_view`, `admit_proposals` | Inventaire lecture fédérée; **admission échoue volontairement** | Muter le canon via Kit non qualifié |
| `encyk_v32/locking.py`, `doctor.py`, `cli.py`, `ui.py` | Verrou, diagnostic, CLI, interface | Exploitation, reprise, introspection | Ordonnanceur de campagne infini et gestion de preuve exhaustive |

**Alerte technique vérifiée :** le code V32.2 ZIP d'origine utilisait un offset incorrect pour `entity_edge.property_id`; la station V4/V6 a corrigé la lecture. Ne pas déployer le **code V32.2 brut** sur une installation patchée V6 sans vérifier cette adaptation.

## B. Station V30 adaptée V6 (ACTUEL, journal d'installation)

| Module | Rôle | Préservation |
|---|---|---|
| `station_v32_adaptateur.py` | Interface HTTP locale, 88 noms, 10 postes, import ZIP, opérations `discover`/`batch`/`prepare`/`resume_partials` | Ne pas réécrire les jobs ouverts; une branche active à la fois |
| `optimisation_prototype_v6.py` | Liens V28, relations UNESCO V31.11, guide de lecture V27, prompts six passes, reprise manuelle des PARTIAL | **Code réemployé**, pas ancienne base restaurée |
| `missions_intensives.py` | Sélection 300, prompts longs, budget affiché 20 000 | Ne pas supposer que 300 est toujours optimal |
| `transport_groupe_v6.py` | Regrouper des ZIP de sélection intacts dans une seule enveloppe | Chaque `SEL_...` conserve son identité de retour |
| `patch_prototype_v6.py`, `correctif_graphe_skope.py`, `correctif_zip_windows.py` | Petits correctifs traçables avec sauvegardes | Ne pas déclencher silencieusement sur nouveau code incompatible |
| `presse_papiers_windows_v3161.py`, `poste_v30_adapte_v32.html`, JS | Gestes V30 familiers, « Copier + ZIP » | Transport dans ChatGPT reste manuel |

L'adaptateur V6 appelle dans son worker les quatre voies de découverte : `discover()` pour Skope, `discover_fallback()` pour titres, `discover_v28_wikilinks()` pour liens, `discover_v3111_ontology()` pour relations UNESCO. Le bouton `batch` ne découvre que si aucun candidat PENDING/SELECTED n'attend : **c'est une automatisation partielle, pas un ordonnanceur de campagne complet**.

## C. Prototype historique V27–V31 (CODE PRESENT, production V31 ARCHIVÉE)

| Source du dépôt V32 (copie historique) | Acquis à réutiliser | Statut réel V6 |
|---|---|---|
| `tools/unesco_pilot/production_kristals_v27.py` | `page_from_index`, `_reading_guide`, inventaire des sections, accès offset XML sans full-scan | **Réutilisé** pour ENR V32 et dossier de lecture V6 |
| `tools/unesco_pilot/decouvrir_articles_relies_v28.py` | `parse_wikilinks`, candidats par liens, parcours catégories/sous-catégories, priorités | **Liens repris**, catégories complètes **pas encore reprises** |
| `tools/unesco_pilot/catalogue_global_v25.py` | Registre historique des routes de découverte, recherche catégories/titres | **Index préservé**, adaptation complète au nouveau registre à étudier |
| `tools/unesco_pilot/poste_chatgpt_v30.py` | Tableau dix postes, clipboard, transfert multi-packs, traitements des retours | **Interface/clipboard réutilisés**, base V30 non réactivée |
| `outils_v30/priorisation_unesco_v28.py`, `planifier_packs_unesco_v28.py` | Planification, scoring/partition de lots | Logique à mesurer contre la rotation V6 |
| Documents historiques `docs/historique_mises_a_jour/*` | Analyses six passes, contrôle de couverture, synthèses, HOLD/DEFERRED, reprise | Plusieurs principes repris; stratification DEFERRED V31.12 pas entièrement réintégrée |

**Non-régression à exiger :** toute nouvelle V32 doit comparer sa couverture de sources, son traitement de PARTIAL, son coût en texte et ses retours avec les meilleurs acquis V27–V31. Reprendre les tests historiques pertinents, sans importer leurs données de production.

## D. Skope (code indépendant, NON MODIFIÉ)

- `skope/db.py` : `connect`, `node`, `find`, `neighbors`, `induced_edges`, index compact EncyK RO. Contrôle `complete`; recherche noms via `idx_name_norm`. **`property_id` est un entier brut dans `entity_edge`**.
- `skope/scope.py` : préparation de listes QID/relations; `skope/massive.py` : campagnes QID volumineuses et exports réutilisables, jobs persistants.
- `skope/extraction.py` : **extraction full original Wikidata opt-in** (`full_source_entity_json`, gzip-jsonl), exige dump avec identité vérifiée et index random-access **déjà disponible**. Ne lance pas de scan de dump mondial ni de réindexation dans cette voie.
- `skope/export.py`, `api.py`, `cli.py`, `reconciliation.py`, `portfolio.py` : sorties/recettes/API, correspondances, portfolios et opérations.
- `encyk/00_system/contracts/source-evidence-handoff/2.0.0/README.md` : contrat d'acheminement de preuves vers **Médiathèque kOA**; ne contient pas d'identités Kristal ni d'admission canonique. **Autre sous-projet/version** : pas une API V32.2 déjà branchée.

**Décision :** réutiliser des capacités Skope en lecture seule ou via contrats existants; **aucune modification du code Skope**. La disponibilité de la voie lossless sur les vrais dumps/index est **à confirmer** avant tout couplage.

## E. Kristalizer et frontière canonique (NON MODIFIÉ)

- `kristalizer/core.py` : inventaire des projets, rapprochement identités, vérifications, staging et appel Kit externe.
- `kristalizer/kit_reference.py` : recherche/qualification d'un Authoring Kit.
- `tools/unesco_ai_proposal_intake.py` et intégrations `unesco-mt1-10` : **spécifiques au pilote**, pas pont général certifié pour les 88 branches.
- **Ce qui manque :** un contrat universel validé EncyK-propositions → staging/island source → Kit officiel, résolvant les ambiguïtés de KQ/KP/KA/KS et autorisations. Ne pas bricoler de faux canon.

## F. Catalogue des possibilités à qualifier (ne pas coder avant mesure)

1. Lecture de catégories/sous-catégories via catalogue V25: inspecter schéma et indices **sur le poste** avant activation (pas de full-scan); mesurer bruit par concept.
2. Rechercher des candidats par noms Wikidata indexés `idx_name_norm` pour concepts peu couverts; limiter les retours et conserver la route.
3. Extraction lossless de QID sélectionnés via Skope: vérifier les prérequis, provenance des statements, coût et licence; enrichissement structuré séparé des textes Wikipédia.
4. Extraction des infoboxes et sections en programme local: matériel préparatoire non factuel; les valeurs non sourcées de modèles restent des indices.
5. Groupes de mêmes articles/révisions interconcepts/branches: construire mémoire documentaire partagée sans fusionner concept/QID/Kristal.
6. Génération de *missions de réparation* depuis `import_errors` avec un retour par job compatible; **ne pas corriger les citations par substitution automatique**.
7. Mettre les candidats `PARTIAL` dans une file dédiée avec budget de reprises, seuil de gain et cooldown.

Ces pistes ne doivent pas être présentées comme capacités V6 déjà livrées.
