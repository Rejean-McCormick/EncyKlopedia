# QuerySpec, Lens, Reader Policy et état d'exploration

## 1. QuerySpec

QuerySpec représente **ce que l'utilisateur sélectionne**. Il ne contient pas de préférence de rendu.

Principes :

- un type racine ;
- des critères explicites ;
- des contraintes existentielles bornées ;
- un contexte identifiant corpus/policy ;
- un ordre déterministe ;
- un curseur opaque pour pagination.

Une recette de navigation ne doit pas être encodée comme un filtre QuerySpec.

## 2. Lens

Une Lens décrit **l'angle de lecture** :

- type racine ;
- facettes pertinentes ;
- pivots ;
- labels ;
- priorités ;
- éventuellement préférences de navigation non autoritatives.

Une Lens ne contient jamais de permission d'accès et ne remplace jamais Reader Policy.

## 3. Reader Policy

Reader Policy détermine **ce qui est visible**. Elle doit être appliquée avant :

- query ;
- facettes ;
- compteurs ;
- autocomplete ;
- entity inspector ;
- evidence/provenance ;
- navigation plan ;
- projections spécialisées.

Changer de Lens ne change pas la policy. Changer de policy invalide cursors, caches et projections dépendants du contexte précédent.

## 4. Focus

Le focus est l'entité ou le sous-ensemble actuellement inspecté. Il peut modifier les affordances locales sans modifier QuerySpec.

Exemple : un Kristal HumanBody peut être globalement `multiScale`, mais une entité de type `pathway` peut faire émerger `sequence + causal + cycle`.

## 5. ExplorationState cible

L'état d'exploration doit séparer sélection et navigation :

```json
{
  "schemaVersion": "1.0",
  "query": {},
  "lensRef": "systems",
  "readerPolicyRef": "public",
  "focus": {"kind": "entity", "id": "..."},
  "navigation": {
    "mode": "adaptive",
    "recipeId": "feedback"
  },
  "history": {}
}
```

L’implémentation 1.0 utilise `exploration-state` 1.0. Les états 0.2 restent acceptés uniquement par une migration explicite et testée ; ils ne sont jamais réinterprétés silencieusement.

## 6. Mode adaptive et mode pinned

### adaptive

Konstellation peut remplacer la recette courante si elle n'est plus applicable au nouveau contexte.

### pinned

Le choix utilisateur est conservé tant que la recette reste valide. Si elle devient impossible, l'UI doit expliquer la raison et proposer un fallback.

## 7. Pivots

Un pivot transforme explicitement la sélection. Il doit :

- partir de la population complète sélectionnée, pas de la page visible ;
- produire un nouveau QuerySpec ;
- être visible dans l'historique ;
- rester indépendant de la vue active.
