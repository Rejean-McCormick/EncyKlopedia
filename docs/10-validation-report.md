# Stratégie de validation du système final

Ce document décrit **comment valider Konstellation 1.0**. Les rapports `VALIDATION-v0.x.md` restent historiques.

## 1. Niveaux de validation

### Contrats

- JSON Schema valide ;
- examples valides ;
- refus des propriétés non prévues lorsque `additionalProperties: false` ;
- migration versionnée.

### Moteur

- sélection déterministe ;
- policy appliquée partout ;
- facettes exactes ;
- witnesses corrects ;
- cursors/fingerprints cohérents.

### Profiler

- détection positive ;
- détection négative ;
- hints cohérents ;
- pas de confusion domaine/structure ;
- complexité bornée.

### Planner

- applicabilité ;
- classement déterministe ;
- raisons explicables ;
- fallback ;
- mode pinned/adaptive.

### Projections

- aucune fuite de données policy ;
- DTO borné ;
- provenance/witnesses ;
- troncature explicite ;
- reconstruction possible.

### Renderers

- clavier ;
- responsive ;
- empty/error/loading states ;
- fallback accessible ;
- aucune mutation cachée de query.

### E2E

- changement Lens ;
- changement policy ;
- navigation entre recettes ;
- restauration d'exploration ;
- import Kristal v6 ;
- corpus multi-Kristal.

## 2. Golden corpus

Le corpus de validation doit contenir des cas structuraux volontairement distincts. Voir [21-testing-golden-corpus.md](21-testing-golden-corpus.md).

## 3. Tests négatifs obligatoires

Exemples :

- Math ne doit pas recevoir une timeline sans signal temporel ;
- un simple graphe avec cycles non causaux ne doit pas être présenté comme feedback causal ;
- `actionability=automatic` ne doit jamais créer un bouton d'exécution ;
- une source masquée par Reader Policy ne doit pas réapparaître dans traceability ;
- un hint `temporal: 1` sans structure temporelle cohérente doit être rejeté, plafonné ou signalé.

## 4. Validation production

Une architecture correcte n'est pas équivalente à une release production. La qualification 1.0 exige aussi :

- build reproductible ;
- Playwright ;
- benchmarks ;
- observabilité ;
- sécurité ;
- runbooks ;
- packaging/signature/checksum.
