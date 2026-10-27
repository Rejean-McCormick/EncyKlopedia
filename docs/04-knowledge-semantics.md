# Autorité, sémantique, provenance et projections

## 1. Trois niveaux

| Niveau | Exemple | Autorité |
|---|---|---|
| Canonique | `kristal_state` v6, assertions, coordinates, valuations | Kristal |
| Dérivé | profil d'affordances, score, NavigationPlan, projection timeline | Konstellation, reconstructible |
| Présentation | layout, icônes, ordre visuel local | UI uniquement |

## 2. Une projection n'est jamais un fait

Une timeline peut ordonner des éléments, un DAG peut sélectionner des dépendances et un graphe causal peut dessiner une boucle. Ces structures d'affichage ne deviennent pas de nouvelles assertions.

Toute projection doit être reconstruisible à partir des éléments visibles et de la configuration de la recette.

## 3. Evidence et provenance

Konstellation maintient la distinction :

- **evidence** : éléments qui soutiennent une assertion/record ;
- **provenance** : origine, transformation et chaîne de production.

L'UI ne doit pas fusionner ces deux notions sous un label générique « source » lorsqu'elles sont distinctes dans Kristal v6.

## 4. Conflits

`conflicts_with` signale une divergence explicite. Konstellation peut :

- montrer les assertions concernées ;
- expliquer la nature de la relation ;
- comparer leurs evidence/provenance visibles.

Il ne doit pas décider laquelle est vraie sans règle externe explicite.

## 5. Succession et lineage

- `supersedes` indique un remplacement/révision ;
- `lineage` indique une dérivation/lignée.

Ni l'un ni l'autre n'implique automatiquement causalité.

## 6. Witnesses

Lorsqu'un élément apparaît parce qu'il satisfait une contrainte relationnelle, Konstellation devrait pouvoir montrer le ou les witnesses qui expliquent la correspondance.

Un witness est une explication de sélection, pas une nouvelle assertion.

## 7. Labels et terminologie

Les labels contextuels peuvent varier par Lens ou navigationHints, mais les identifiants de contrats doivent rester stables.

Exemple : `dependencies` peut être affiché comme « Prérequis », « Dépendances de preuve » ou « Dépendances techniques » selon le contexte, sans changer de sémantique de base.
