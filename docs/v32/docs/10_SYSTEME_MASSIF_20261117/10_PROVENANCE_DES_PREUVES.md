# 10 — Provenance, méthode, limites et vérifiabilité

Cette documentation n'est pas un diagnostic exécuté sur les disques Windows. Les **sources primaires inspectées** sont les archives suivantes présentes dans la conversation et le conteneur :

1. `EncyKlopedia_V32_2_REPO_CORRIGE_20261116 (1).zip` — code complet V32.2, 5 305 fichiers; en particulier `encyk_v32/{sources,pipeline,sql,config,federation,cli}.py`, `tools/unesco_pilot/production_kristals_v27.py`, `decouvrir_articles_relies_v28.py`, la documentation `docs/v32`.
2. `ENCYK_UPDATE_V32_V6_CONSOLIDATION_PROTOTYPE_88_BRANCHES_20261117.zip` — station à 88 branches, adaptateur, patch moteur, dossier de lecture et correctifs Skope; 34 fichiers.
3. `znapshot_Skope_11162132.zip` — `skope/db.py`, `skope/extraction.py`, `skope/massive.py`, contrats `source-evidence-handoff`; 505 fichiers.
4. `znapshot_Kristalizer_11162133.zip` — `kristalizer/core.py`, `kit_reference.py`, staging et intégrations pilote MT1.10; 57 fichiers.
5. Rapports d'audit `RAPPORT_DEPOTS_ENCYK_20261116T161850Z.json`, `AUDIT_COMPLEMENTAIRE_ENCYK_20261116T162401Z.json` — données de chemin et de protection du 16 novembre.
6. Journaux transmis par l'opérateur le 17 novembre 2026 — compteurs V6 Météorologie (631 puis 2 460 candidats, 10 606 propositions, 506 erreurs d'import observées sur trois missions).
7. Analyses antérieures `AUDIT_CHAINE_ENCYK_V32_MASSIFICATION_20261117.md` et `AUDIT_COMPARATIF_PROTOTYPE_MT110_V31_VERS_V32_20261117.md` — document d'orientation, **moins probant que les codes inspectés**.

## Hiérarchie de preuve dans nos documents

| Niveau | Exemple | Interprétation |
|---|---|---|
| CODE OBSERVÉ | La fonction `WikidataGraph.page()` en V32.2 brut cherche l'offset P incorrect; `skope/db.py` stocke P en entier brut | Capacité/défaut **dans ce snapshot précis** |
| JOURNAL UTILISATEUR | `graph_neighbors_scanned=10768`, 759 propositions importées | Comportement rapporté sur **son Windows et cette campagne** |
| TEST SYNTHÉTIQUE | Suite V6 a annoncé 50 tests | Qualification d'un scénario; ne prouve pas tous les cas réels |
| HYPOTHÈSE | Les nouveaux parcours catégories augmenteront l'exactitude | À mesurer, pas une fonction livrée |
| CIBLE | Ordonnanceur progressif par fenêtre | Architecture choisie, **non exécutée** dans ce pack |

## Inventaire reproductible

`inventaires/FICHIERS_SNAPSHOTS.csv` contient source ZIP, chemin interne, octets, SHA-256 SHA de fichier et catégorie indicative pour **5 901 occurrences**. `PROGRAMMES_DETECTES.csv` liste **889 occurrences** de scripts `.py`, `.pyw`, `.ps1`, `.cmd`, `.sql` et leurs fonctions/classes si l'AST Python était lisible. Les mêmes fonctions peuvent apparaître à plusieurs endroits (snapshot fusionné / legacy / réplique), et certains scripts sont historiques; ces nombres ne sont **pas un nombre de fonctions actives**.

Les chemins D: proviennent de `config.py`, d'outils historiques et des journaux utilisateur, **pas d'une connexion live du conteneur**. Les tailles de 134 Go et 110 Go sont des estimations historiques. L'accès réel à un dump Wikidata lossless indexé et ses SHA de provenance n'a pas été contrôlé. La qualité scientifique des propositions ChatGPT n'a pas été réévaluée indépendamment lors de cet inventaire.

## Erreur importante à ne pas répéter

Une réponse ChatGPT `ENR` munie d'une citation qui est exactement présente dans le Wikitext peut être techniquement acceptable tout en contenant une inférence trop forte. Ce pack documente **l'exactitude des liens**, **la conformité du format**, puis **la plausibilité sémantique** comme niveaux différents; il ne transforme aucun des trois en validation canonique.

## Auditer le contenu de cette livraison

Le ZIP final fournit un `MANIFEST_SHA256.json` des documents et scripts livrés. L'installateur vérifie que le dépôt cible contient bien `encyk_v32/pipeline.py` avant de copier seulement la documentation. La suite `tests/` teste une base SQLite synthétique sans contact avec les volumes Windows.
