# Registre des observations, hypothèses et décisions

**Ajout V32.1 :** les affirmations relatives aux contrats du Framework/Kit/Arketype/Kompiler viennent du [rapport d’architecture du 16 novembre](07_RAPPORT_DECISION_20261116.md) et ne sont **pas des tests réalisés dans ce paquet**. L’architecture fédérée est une décision cible; l’existence des API exactes reste à corroborer.


## Échelle de certitude

- **[OBSERVÉ CODE]** : fonction, DDL, chemin ou comportement identifié dans un snapshot local; ce n'est **pas** une preuve que la version du poste Windows est identique.
- **[OBSERVÉ DONNÉES]** : chiffre et statut calculés depuis des JSON/ZIP du snapshot utilisateur (les grosses SQLite ne sont pas ici).
- **[CIBLE]** : modèle V32 proposé; n'existe pas encore sous cette forme.
- **[À MESURER]** : ne peut être conclu sans requête/essai sur D: ou échantillon documentaire.
- **[HISTORIQUE]** : modèle antérieur ou artefact passé, réutilisable mais pas normatif en V32.

## Observations source par source

| Fait | Statut | Source exacte déjà inspectée | Réserve |
|---|---|---|---|
| 88 espaces UNESCO | OBSERVÉ DONNÉES | `UNESCO_Kristals/branches/*/canon/domain/unesco-source.json` | Ne sont pas des sujets encyclopédiques |
| 4 500 concepts au total | OBSERVÉ DONNÉES | Agrégation des 88 snapshots | Périmètre des fichiers fournis, pas version live plus récente |
| 4 289 QID candidats uniques P3916 | OBSERVÉ DONNÉES | `*/derived/wikidata-p3916-candidates.json` | Mapping **candidat**, non preuve d'équivalence validée |
| 134 ambiguïtés, 77 sans mapping | OBSERVÉ DONNÉES | Mêmes fichiers de mapping | Ne doivent pas disparaître du registre |
| 4 288 extraits/fiches Wikidata préservés | OBSERVÉ DONNÉES | `*/derived/wikidata-full-facts-index.json` | Index de faits dérivés, pas dump source lossless |
| L'extrait RDF 2025 contient 4 490 concepts | OBSERVÉ DONNÉES | `LinkedDataHub-UNESCO/demo.zip` | Ancienne source comparative, pas le référentiel le plus récent fourni |
| Générateur v25 charge des branches | OBSERVÉ CODE | `EncyKlopedia/tools/unesco_pilot/generer_branches_unesco_v25.py` | Ne transporte pas automatiquement les P3916 |
| `load_branch` accepte crosswalk | OBSERVÉ CODE | `EncyKlopedia/tools/unesco_pilot/catalogue_global_v25.py` | La transformation des 88 crosswalks reste à intégrer |
| Wikidata→Wikipédia par QID | OBSERVÉ CODE | `mediatheque-references/tools/wiki/dump_import/import_dumps.py` et `catalogue_global_v25.py` | Taux de jointure effectif **non mesuré** |
| Graphes entrants/sortants Skope | OBSERVÉ CODE | `Skope/skope/db.py` | Index compact sans provenance détaillée de statements |
| Extraction ciblée originale Skope | OBSERVÉ CODE | `Skope/skope/extraction.py` | Disponibilité live des résultats à vérifier; code intouché |
| Packs Kristal complets, cumulés | OBSERVÉ CODE | `EncyKlopedia/tools/unesco_pilot/production_kristals_v27.py` | Nouveau domaine doit être sujet/claim, non article isolé |
| Station de 10 lanes et deux types historiques | OBSERVÉ CODE | `EncyKlopedia/tools/unesco_pilot/poste_chatgpt_v30.py` | Refactorer métier, ne pas recopier toute la station |
| Problème potentiel DEFERRED multibranche | OBSERVÉ CODE | `EncyKlopedia/tools/unesco_pilot/routage_branches_v311.py` | `if not ranked:continue` avant requête `DEFERRED` |
| Audit v31.2 n'atteste pas la saturation | OBSERVÉ CODE | `EncykAudit/AUDIT_AUTOMATIQUE_BRANCHE_V312.pyw` | L'absence d'entrées dans un index n'est pas l'absence de sources pertinentes |
| Un manager `.pyw` commun | CIBLE | `docs/05_MANAGER_ET_UX/` | **Pas encore construit** |
| Plusieurs Kristals sujets par concept | CIBLE | `docs/03_ARCHITECTURE_V32/02_MODELE_DOMAINES_ET_KRISTALS.md` | Cardinalités à mesurer sur les données |
| Qualité et densité par branche | À MESURER | Campagne de deux passes V32 | Pas de promesse de 100 % ni d'un quota de facts arbitraire |

## Références et extraction

Les snapshots de code ont été lus depuis les dossiers de travail `/mnt/data/architecture_deep/*` et `/mnt/data/architecture_review/smart/*`, extraits des ZIP fournis par l'utilisateur. Ces chemins sont **temporaires au contexte d'audit** et ne doivent pas devenir des chemins de runtime sur Windows. Utiliser leur correspondance `depot/fichier` dans [`inventaire_modules.csv`](../07_INVENTAIRES/inventaire_modules.csv) pour retrouver le code après consolidation.

Les bases de données Windows `D:` de taille importante n'ont pas été ouvertes dans cette livraison. Il serait incorrect de déclarer leurs millions de lignes vérifiées sur la seule base de l'existence d'un schéma ou d'un ancien journal.
