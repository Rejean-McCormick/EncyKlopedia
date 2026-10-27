# Renderer Registry

Le Renderer Registry est la frontière entre la **navigation sémantique** et la **présentation exécutable**.

## 1. Principe

Un Kristal peut influencer **quelle recette est pertinente**, mais il ne fournit jamais le code qui l'affiche. Le registry appartient à Konstellation ou à un opérateur explicitement approuvé.

## 2. RendererDefinition 1.0

```json
{
  "id": "flow-path",
  "supportedRecipes": ["path"],
  "requiresAffordances": ["sequence"],
  "benefitsFrom": ["stateMachine", "conditionalTransition"],
  "projectionKind": "flow",
  "maxRecommendedItems": 400,
  "accessibilityFallback": "table",
  "supportsKeyboard": true,
  "supportsExport": true
}
```

## 3. Registry 1.0 implémenté

| Renderer | Projection | Recettes | Priorité 1.0 |
|---|---|---|---|
| `list` | rows | catalogue | implémenté |
| `table` | rows/columns | table, dimensions fallback | implémenté |
| `constellation` | bounded neighborhood | constellation, arguments | implémenté |
| `timeline-lineage` | temporal events/links | timeline, evolution | implémenté |
| `tree` | nodes + parent edges | hierarchy | implémenté |
| `dag-proof` | DAG + proof metadata | dependencies, proofs | implémenté |
| `flow-path` | states/steps/transitions | path | implémenté |
| `causal-feedback` | signed directed graph | feedback | implémenté |
| `matrix-profile` | dimensions x entities | dimensions | implémenté |
| `state-flow` | state records/transitions | states, action-context | implémenté |
| `traceability` | evidence/provenance graph | traceability | implémenté |
| `multiscale-layer` | layers/scales + cross-links | multiscale | implémenté |
| `spatial` | points/regions | spatial | implémenté |

## 4. Sélection du renderer

Le planner choisit une recette. La recette référence un `rendererId`. Le frontend résout ce renderer dans le registry.

Un renderer inconnu n’est jamais chargé dynamiquement depuis le Kristal. Le frontend consulte `accessibilityFallback` dans le registry, puis seulement les fallbacks génériques Table/Liste si nécessaire. Si aucun fallback valide n’existe, une erreur diagnostique structurée est produite.

## 5. Contrat de projection

Chaque renderer consomme un DTO versionné. Exemple DAG :

```json
{
  "schemaVersion": "1.0",
  "projectionKind": "dag",
  "recipeId": "proofs",
  "nodes": [],
  "edges": [],
  "roots": [],
  "truncated": false,
  "explanation": {}
}
```

Les DTOs ne doivent pas contenir d'objets canonique bruts inutiles. Ils doivent exposer seulement les données visibles nécessaires à la vue.

## 6. Accessibilité

Chaque renderer DOIT fournir :

- navigation clavier ;
- focus visible ;
- texte/labels accessibles ;
- fallback structuré non graphique ;
- comportement sous zoom ;
- absence de dépendance exclusive à la couleur.

## 7. Budgets

Chaque définition doit préciser :

- max recommandé ;
- stratégie de troncation ;
- stratégie LOD/pagination ;
- coût estimé ;
- fallback.

Le planner peut préférer une recette moins coûteuse si le budget de la vue spécialisée est dépassé.
