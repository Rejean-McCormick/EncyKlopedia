# Référentiel UNESCO, LinkedDataHub et 88 espaces existants

## Deux générations de sources

**[OBSERVÉ DONNÉES]** `UNESCO_Kristals/branches/unesco-mtX-YY/canon/domain/unesco-source.json` contient un import du thésaurus (date de schéma **2026-08-31**) et les notions du microthésaurus. On y trouve `concepts[]`, `unesco_id`, `source_uri`, `preferred_labels`, `alternate_labels`, `scope_notes`, `definitions`, `broader`, `narrower`, `related`, `microthesaurus_ids`, `domain_ids`. Le statut indique **source importée, non sémantiquement revue**.

**[OBSERVÉ DONNÉES]** `LinkedDataHub-UNESCO/demo/unesco-thesaurus` fournit un démonstrateur RDF/SKOS plus ancien, comparé dans `UNESCO_Workbench/reference/ldh_2025_educational_policy.json`. Le snapshot 2025 contient **4 490 concepts**, tandis que le jeu 2026 distribué parmi les 88 branches contient **4 500 concepts distincts**. Ce sont des sources différentes; ne pas fusionner leurs données sans version/provenance.

## 88 branches : chiffres réellement parcourus dans les JSON

| Mesure | Valeur |
|---|---:|
| Dossiers de branche `unesco-mt*` | 88 |
| Concepts distincts (ensemble des `unesco_id`) | 4 500 |
| Enregistrements de statut P3916 | 4 500 |
| `SINGLE_P3916_CANDIDATE` | 4 289 |
| `REVIEW_AMBIGUOUS_P3916` | 134 |
| `NO_P3916_MAPPING` | 77 |
| Structure de branche au format | `kristal.local-workspace/3.2.0` |
| Structure du snapshot conceptuel | `kristal.unesco-import-snapshot/1.0` |

Ces chiffres sont issus de **fichiers de référence** du snapshot, pas de la vérification des QID dans le corpus Wikidata vivant. La distribution par branche, y compris toutes les étiquettes, est dans [`../07_INVENTAIRES/unesco_88_branches.csv`](../07_INVENTAIRES/unesco_88_branches.csv).

## Fichiers par branche et responsabilité

```
UNESCO_Kristals/branches/unesco-mt1-10/
  kristal.workspace.json                 # espace de branche, profil, frontière sémantique
  kristal.discovery.json                 # découvrabilité des sources, non autorité d'édition
  canon/domain/unesco-source.json        # données UNESCO importées, pas canon approuvé
  derived/wikidata-p3916-candidates.json # 1 entrée par concept, statut P3916
  derived/wikidata-full-facts-index.json # prévisualisation des faits, non preuves originales
  derived/reader-profile.json            # métadonnées d'accès/lecture
  docs/...                               # notices génériques d'espace
```

Le nom historique `canon/domain/` **ne signifie pas** que les affirmations sont approuvées; les champs de données incluent `not_canon=true` et des statuts de source. Le futur manager doit conserver cette distinction plutôt que canoniser par inférence de chemin.

## Politique V32 [CIBLE]

1. Importer les 88 fiches de branche en un **registre UNESCO transversal**, un seul `concept_id` logique même si des concepts sont présents dans plusieurs microthésaurus.
2. Importer leurs relations `broader`, `narrower`, `related` en conservant leur sens et la version de source.
3. Reprendre les 4 500 statuts P3916 à l'identique; ne jamais créer 77 QID imaginaires ni arbitrer arbitrairement les 134 ambigus.
4. Constituer les candidatures Wikidata/Wikipédia depuis ces ancrages; une petite liste d'alignements ambigus peut être revue en parallèle, sans bloquer les 4 289 uniques.
5. La préparation d'une branche ne réexécute plus la Fabrique mondiale ni le traitement RDF complet : elle lit l'import global préexistant.

## Réemploi de la Factory

Le dépôt `Kristal_UNESCO_Factory` comprend `unesco_inventory_corrige.py` (lecture/structuration UNESCO), `unesco_wikidata_bridge.py` (rapprochement P3916, index local) et `wikidata_full.py` (fiches de faits de source Wikidata). Conserver ces fonctions comme références pour l'adaptateur; ne pas demander de reconstruire 88 dossiers complets si le registre d'import contient déjà tout ce qui est requis.

## Licences et versions

La source UNESCO annonce **CC BY-SA 3.0 IGO**; les captures RDF et imports doivent conserver une indication de provenance. Pour V32 privé, éviter de transformer cette information en procédure lourde; elle reste nécessaire si l'agent de finition de 2027 envisage la publication.
