# Navigation adaptative — spécification détaillée 1.0

## 1. Objectif

Permettre à Konstellation de naviguer des milliers de Kristals sans créer une UI spécifique par domaine.

## 2. Introspection

Le profiler exploite :

- relation registry ;
- value kinds ;
- types d'entités ;
- topologie ;
- fréquences ;
- cycles ;
- profondeur hiérarchique ;
- metadata Kristal v6 ;
- hints déclaratifs ;
- structure locale du focus.

Les heuristiques lexicales ne sont qu'un fallback.

## 3. Calcul de profil

Chaque affordance contient :

```json
{
  "score": 0.82,
  "evidence": [
    "relation:proof_dependency",
    "record_role:proof"
  ]
}
```

Un score est borné entre 0 et 1 et accompagne toujours une evidence explicable.

## 4. Ordre d'autorité des signaux

```text
structure canonique explicite
  > hints déclaratifs de confiance
  > schéma et topologie observés
  > heuristiques lexicales
```

Un hint ne doit pas écraser une incompatibilité manifeste.

## 5. Localité

Le profiler global est calculé une fois puis caché. Les profils locaux se calculent sur le sous-ensemble nécessaire : type, result set ou focus.

Le planner peut donc proposer des vues différentes dans le même Kristal.

## 6. Exemple HumanBody

```text
Lens anatomique
  -> hierarchy + spatial + multiScale

Lens physiologique
  -> sequence + causal + cycle + multiplex

Focus pathway
  -> path + feedback
```

## 7. Exemple Math

```text
Focus proposition
  -> dependency + proof
  -> Preuves, Dépendances, Conséquences

Focus proof
  -> dependency + sequence
  -> Étapes, hypothèses, propositions utilisées
```

## 8. Exemple HistoryTech

Une technologie peut être reliée à une occurrence qui porte la date. La projection timeline peut suivre un saut sémantique borné :

```text
technology -> occurrence -> date
```

Cette règle est structurelle et réutilisable, pas spécifique à HistoryTech.

## 9. Exemple ScolQc

Les transitions conditionnelles font émerger `path` et un planner de prérequis. Le système doit distinguer une transition autorisée d'une relation simple.

## 10. Coûts

Le planner doit intégrer un coût estimé :

- volume du result set ;
- nombre de nœuds/edges ;
- profondeur ;
- besoin d'agrégation ;
- coût de calcul ;
- taille d'écran éventuellement.

Une vue très pertinente mais trop coûteuse peut être remplacée par une version agrégée ou un fallback.

## 11. Explication

Pour chaque recette, l'UI doit pouvoir afficher une justification de type :

> « Chronologie proposée car 87 % des occurrences visibles portent une date ou période et deux relations structurantes relient les entités aux occurrences datées. »

L'explication ne doit pas exposer de données masquées par policy.
