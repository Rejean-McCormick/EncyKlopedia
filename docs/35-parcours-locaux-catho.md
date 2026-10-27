# Parcours de lecture locale — Catho / Konstellation

**Statut :** correctif expérimental, non qualifié en release.

## Diagnostic

L’ancien lecteur local construisait en premier `v9_state`, puis `v9_artifact`
(et un seul type générique `v9_node`). L’Explorer choisissait le premier type,
d’où la page « V9 state » avec un seul élément. Il déclarait également
`synthetic: true`, donnant un avertissement de corpus de démonstration
inexact pour le véritable Kristal Catho.

## Nouveau comportement

- Les `kind` du graphe dérivé deviennent des **types de présentation** sans
  altérer ni qualifier les classes canoniques du Kristal.
- La projection dérivée `node-edge-json/1` conserve les identités d'origine,
  les prédicats sources et le champ `originalEvidence`, particulièrement
  `identity_independently_verified: false` pour les correspondances candidates.
- Les relations sont séparées par prédicat et type cible pour satisfaire
  les domaines et portées de Konstellation sans modifier le graphe.
- `preferredKind`, `featuredKinds`, `kindLabels`, `predicateLabels` sont
  des choix UI **strictement locaux** dans `config/active-reader.json`.
  Les libellés ne créent pas de vérités ni de droits d’accès.
- La page d’accueil présente six raccourcis cliquables, avec les décomptes
  calculés depuis les entités visibles dans l’Explorer.
- Les vues techniques `v9_state` et `v9_artifact` restent accessibles.
- Une bannière « Lecture locale dérivée » rappelle le caractère non canonique.

## Mise en place Windows

1. Arrêter Konstellation et sauvegarder `C:\mycode\Konstellation\Konstellation`.
2. Décompresser le correctif **dans** ce dossier en préservant les chemins.
3. Ne déplacer ni modifier `C:\mycode\Kristal\locals\A-Kristal-Catho`.
4. Lancer `Ouvrir_Kristal_Catho_v10.cmd`, qui reconstruit Astro puis démarre
   Konstellation sur `http://127.0.0.1:4321`.
5. Vérifier la première perspective « Personnes », les six parcours et la
   bannière « Lecture locale dérivée ».
6. Si le navigateur reprend une exploration enregistrée via une URL contenant
   `#exploration=`, revenir à `/` pour retrouver la vue par défaut.

## Validation disponible

- 9 tests `tests/kristal-local-v10.test.mjs` : réussis.
- Test direct sur le Catho mis à jour : 4 527 entités, 13 217 assertions,
  668 personnes; toutes les relations de la projection typée correspondent
  aux domaines et plages déclarés.
- `scripts/check-svelte-structure.mjs` : aucun problème.
- `scripts/check-frontend-security.mjs` : aucun problème.
- La construction Astro, le comportement navigateur et les tests e2e Windows
  doivent être validés sur l’environnement Node.js >= 24.15 avec dépendances.

## Frontières

La présentation ne vérifie pas la véracité des propositions, ne valide pas
le canon, ne publie rien, et ne constitue pas une qualification v10 complète.
Manager, Interaction Kernel, Daat et le Kristal sont inchangés.
