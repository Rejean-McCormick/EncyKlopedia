# Décisions et invariants de Konstellation 1.0

Ce document fixe les décisions non négociables de la cible 1.0.

## 1. Séparer connaissance, sélection, navigation et présentation

Konstellation distingue quatre plans :

1. **connaissance canonique** : Kristal v6 ;
2. **sélection explicite** : QuerySpec ;
3. **navigation dérivée** : profil d'affordances + NavigationPlan ;
4. **présentation** : projection + renderer.

Aucun de ces plans ne doit être confondu avec un autre.

## 2. Invariants

| Invariant | Exigence |
|---|---|
| Autorité | `kristal_state` v6 est canonique. Les packs normalisés, profils, plans et projections Konstellation sont dérivés. |
| Sélection | QuerySpec reste la vérité de la sélection utilisateur. Une vue ne modifie jamais silencieusement la requête. |
| Lecture | Reader Policy est appliquée avant résultats, facettes, recherche, voisinages, projections, provenance et explications. |
| Pas de nouveaux faits | Une recommandation, un score, une vue ou un layout ne crée aucune assertion. |
| Explicabilité | Toute recette recommandée doit pouvoir expliquer les signaux observés ou déclarés qui l'ont rendue pertinente. |
| Fallback | Liste, Tableau et Constellation restent disponibles lorsque les vues spécialisées ne s'appliquent pas. |
| Déclaratif | Les `navigationHints` peuvent orienter la navigation mais n'injectent ni JavaScript, ni HTML, ni permission. |
| Déterminisme | À corpus, contexte, policy, Lens et focus identiques, le plan doit être déterministe. |
| Bornage | Toute projection de graphe ou de voisinage est bornée, paginée ou soumise à LOD. |
| Actionabilité | `actionability` décrit une condition d'action, jamais une autorité d'exécution. |
| Compatibilité | Une rupture de contrat public exige une nouvelle version de schéma et une migration explicite. |

## 3. Décision sur les catégories de Kristals

Les catégories comme `math`, `history`, `biology` ou `education` peuvent être utilisées comme **priors faibles** ou métadonnées d'organisation, mais elles ne doivent pas piloter des branches métier dans le planner.

Le moteur doit choisir la navigation en fonction de la structure effective : temporalité, dépendance, hiérarchie, preuve, causalité, multi-échelle, états, etc.

## 4. Décision sur les renderers

Les Kristals ne fournissent pas leur propre UI exécutable. Le code des renderers appartient à Konstellation et est enregistré dans un **Renderer Registry contrôlé**.

Un Kristal peut seulement fournir des hints déclaratifs validés.

## 5. Décision sur l'adaptation

L'adaptation se fait à plusieurs niveaux :

```text
KristalProfile
  + LensProfile
  + ResultSetProfile
  + FocusProfile
  + préférences explicites utilisateur
  -> NavigationPlan
```

Le Kristal global ne suffit pas : une région d'un même corpus peut présenter une topologie différente d'une autre.

## 6. Décision sur les modes

- `adaptive` : Konstellation peut changer la recette recommandée lorsque le contexte change ;
- `pinned` : l'utilisateur a explicitement choisi une recette, qui reste active tant qu'elle reste applicable.

Aucun mode ne peut contourner la Reader Policy.

## 7. Règle d'arbitrage

En cas de conflit entre une optimisation UX et un invariant épistémique, de sécurité ou d'autorisation, **l'invariant gagne**.
