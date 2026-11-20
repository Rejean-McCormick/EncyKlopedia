# 03 — Données, index et possibilités d'extraction

## Sources et usages (les preuves ne sont pas interchangeables)

| Source | Représentation et chemin indicatif | Produit exploitable | Limite de preuve |
|---|---|---|---|
| Thésaurus UNESCO | `UNESCO_Kristals/branches/unesco-mt*/canon/domain/unesco-source.json` | Microthésaurus, concept, libellés, SKOS broader/related | Classification, non fait encyclopédique |
| P3916 candidats | `derived/wikidata-p3916-candidates.json` | QID candidats SINGLE/AMBIGUOUS/NO_MAPPING | Appariement en attente d'arbitrage documentaire |
| Skope compact | `D:\EncyKlopedia\30_working\wikidata\wikidata.compact.sqlite` | Table `entity_edge`, voisins P31/P279/P921/P361, labels | Arête agrégée, pas le statement original référencé |
| Wikidata lossless | Dump original + index aléatoire si disponibles, `skope/extraction.py` | Statement, qualifiers, références, sitelinks | **Capacité du code, disponibilité locale non vérifiée** |
| Pages Wikipédia | `D:\EncyKlopedia\80_search_indexes\mediatheque-references\wikipedia_en.sqlite` | Titre, page_id, revision_id, `wiki_qid` | Index de localisation, pas texte de preuve |
| Accès direct XML | `wikipedia_en_direct_pages_v21.sqlite` + XML non compressé | Wikitext exact par page/revision, texte haché | L'index peut être déphasé par rapport au Wikipédia vivant |
| Catalogue global V25 | `catalogue_global_unesco_wikipedia_v25.sqlite` | Routes/relations/catégories historiques | Schéma et couverture à préauditer avant réemploi |
| Workspaces V32/V8 | Sous `D:\EncyKlopedia\30_working\...\etat_v32\` | Missions, propositions, reçus et anomalies | Ne pas confondre avec les données canoniques |

Les tailles de « 134 Go Wikidata » et « 110 Go XML » sont des estimations historiques, **pas** des mesures de cet overlay. Les liens et chemins sont indicatifs : les **chemins actifs** viennent de la configuration V8 installée.

## Quelles opérations peuvent être déterministes ?

1. Extraire des QID, labels, mappings et relations via requêtes indexées.
2. Résoudre un `page_id` et une révision, ainsi que les sections et titres d'une page.
3. Extraire des citations verbatim et vérifier qu'elles appartiennent au Wikitext exact.
4. Préparer des dossiers de lecture et des *candidats de faits* à partir d'infobox (à vérifier, les valeurs de modèles peuvent être complexes).
5. Réutiliser le même document `page_id + revision_id + text_sha256` dans plusieurs associations conceptuelles, sans effacer les routes.
6. Mesurer les pages uniques, paires candidates, erreurs et couverture par branche.

L'analyse causale, l'interprétation de controverses, la sélection de relations conceptuelles douteuses et la formulation d'assertions propres restent des tâches utiles pour ChatGPT.

## Décision structurante : gel des sources, découverte ouverte

**Figer** le contenu de chaque pack et ses identifiants pour reproduire un retour. **Ne pas figer définitivement** tout l'univers des candidats : chaque source sélectionnée peut ouvrir de nouveaux liens ou catégories. Les campagnes délimitent des **fenêtres de découverte bornées et datées**.

Les retours doivent citer la révision fournie, **pas** une page web plus récente consultée au hasard. Ne jamais inventer une source absente d'un ZIP.

## Réemploi sans faux doublons

- Une page peut appartenir à **plusieurs concepts** et à plusieurs branches. Une seule lecture documentaire ne supprime pas ces rattachements.
- Un fait distinct peut être corroboré par plusieurs citations : conserver les occurrences, ne pas forcément multiplier des propositions équivalentes.
- Une source différente, un profil différent ou une révision différente peut légitimement nécessiter une réextraction.
- Les données **Wikidata originales** doivent être identifiées comme telles; le compact ne suffit pas.

Voir [base technique](08_MODELE_TECHNIQUE.md), [preuves](13_REGISTRE_DES_PREUVES.md), [inventaire V7](../10_SYSTEME_MASSIF_20261117/01_INVENTAIRE_DONNEES.md).
