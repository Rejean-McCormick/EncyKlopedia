# Guide d'extension à de nouveaux Kristals

## 1. Chemin normal : zéro code spécifique

Un nouveau Kristal doit idéalement fonctionner sans modification de Konstellation :

1. fournir un `kristal_state` v6 valide ou un adaptateur existant ;
2. exposer ses types/relations ;
3. fournir Reader Policy ;
4. optionnellement une Lens ;
5. optionnellement `navigationHints` ;
6. laisser le profiler/planner choisir les recettes.

## 2. Quand ajouter des navigationHints

Utiliser des hints lorsque :

- une relation a une sémantique structurelle difficile à reconnaître lexicalement ;
- un dérivé canonique du domaine fournit un signal fiable ;
- un label utilisateur doit être contextualisé ;
- une recette doit être préférée parmi plusieurs équivalentes.

Ne pas utiliser les hints pour :

- forcer une UI malgré l'absence de structure ;
- encoder des permissions ;
- introduire des faits ;
- injecter du code.

## 3. Quand ajouter une nouvelle affordance

Seulement si la structure :

- apparaît dans plusieurs domaines potentiels ;
- ne se compose pas proprement avec les affordances existantes ;
- a des règles d'applicabilité distinctes ;
- ouvre une navigation réellement différente.

Éviter les affordances nommées d'après un domaine.

## 4. Quand ajouter une nouvelle recette

Une recette représente une **intention cognitive** distincte, pas seulement un style visuel.

Avant ajout :

- vérifier si un renderer existant peut servir ;
- définir requirements et benefits ;
- définir projection DTO ;
- définir fallback ;
- ajouter golden tests.

## 5. Quand ajouter un renderer

Ajouter un renderer si plusieurs recettes ou structures ont besoin d'une représentation qui ne peut pas être rendue correctement avec les primitives existantes.

Le renderer doit être générique. `MathProofRenderer` est mauvais ; `DagProofRenderer` est bon.

## 6. Checklist intégrateur

- [ ] état source validé ;
- [ ] identité vérifiée ;
- [ ] losses explicites ;
- [ ] policy testée ;
- [ ] Lens optionnelle validée ;
- [ ] hints optionnels validés ;
- [ ] recettes attendues testées ;
- [ ] recettes interdites testées ;
- [ ] labels traduits ;
- [ ] provenance visible selon policy.
