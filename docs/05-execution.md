# Exécution, projections et Renderer Registry

## 1. Pipeline d'exécution

```text
QuerySpec + Reader Policy
  -> ResultSet visible
  -> NavigationPlan
  -> Projection request(recipeId, focus, query)
  -> versioned projection DTO
  -> Renderer Registry
  -> approved renderer
```

## 2. Séparation des responsabilités

### Planner

Décide **quoi proposer**.

### Projection Service

Décide **quelles données bornées fournir à la recette**.

### Renderer

Décide **comment représenter ces données**.

Un renderer ne doit pas recalculer des règles de policy ni exécuter des requêtes cachées hors contrat.

## 3. Renderer Registry 1.0 implémenté

| Renderer | Recettes principales | État 1.0 RC |
|---|---|---|
| `list` | catalogue | implémenté |
| `table` | table | implémenté |
| `constellation` | constellation/arguments | implémenté, générique et sans branche domaine |
| `timeline-lineage` | timeline/evolution | implémenté |
| `tree` | hierarchy | implémenté |
| `dag-proof` | dependencies/proofs | implémenté |
| `flow-path` | path | implémenté |
| `causal-feedback` | feedback | implémenté |
| `matrix-profile` | dimensions | implémenté |
| `state-flow` | states/action-context | implémenté ; `actionability` reste informatif |
| `multiscale-layer` | multiscale/multiplex | implémenté |
| `spatial` | spatial | implémenté |
| `traceability` | traceability/divergences | implémenté |

Chaque renderer spécialisé consomme un DTO de projection versionné et borné. La qualification navigateur complète reste un gate de release distinct de l’état d’implémentation source ; voir [VALIDATION-v1.0-RC.md](VALIDATION-v1.0-RC.md).

## 4. Contrat RendererDefinition cible

```json
{
  "id": "dag-proof",
  "supportedRecipes": ["dependencies", "proofs"],
  "requiresAffordances": ["dependency"],
  "benefitsFrom": ["proof", "hierarchy"],
  "maxRecommendedItems": 500,
  "projectionKind": "dag",
  "accessibilityFallback": "table",
  "supportsKeyboard": true,
  "supportsExport": true
}
```

## 5. Règles de registry

Le registry DOIT :

- être défini dans le code ou une configuration opérateur de confiance ;
- refuser un `rendererId` inconnu ;
- déclarer son fallback ;
- déclarer ses budgets ;
- déclarer les recettes supportées ;
- disposer d'un chemin accessible clavier/lecteur d'écran.

## 6. Bornage

Tout renderer réseau doit appliquer au moins une stratégie :

- pagination ;
- voisinage N-hops borné ;
- top-K déterministe ;
- agrégation ;
- LOD selon zoom ;
- virtualisation.

Le frontend ne doit jamais demander « tout le graphe » sans limite.
