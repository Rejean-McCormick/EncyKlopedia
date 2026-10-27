# Couche de présentation sémantique (FR) — 17 octobre 2026

## Objectif

Konstellation est un **lecteur**, et non une autorité canonique. Cette évolution vise l’intelligibilité de la projection locale Kristal v10/état v9, sans modifier les fichiers des Kristals, les assertions, les sources, le contrat Discovery ou les contrats du Framework.

## Modifications

- `src/lib/semantic-display.mjs` : dictionnaire français **déclaré et limité** des propriétés Wikidata connues (par exemple `P138 → Nommé d’après`). Une propriété inconnue s’affiche `Propriété Wikidata P… (libellé indisponible)`, sans déduction hasardeuse. Les noms propres et titres d’œuvres en langue source restent inchangés.
- Le lecteur `server/integrations/kristal-local-v10.mjs` utilise ces libellés pour les relations dérivées. Les identifiants d'origine restent dans `originalPredicate`, `upstreamRef`, etc. Une relation vers une source documentaire est décrite comme source et non comme vérité validée.
- Dans Astrolabe, `aquin` ne correspond plus au suffixe `Joaquín`, les correspondances par mots ont priorité, et l’ordre favorise des intitulés distincts sans fusionner les notices.
- Les facettes sans valeurs et la propriété technique constante du type du nœud sont masquées par défaut; un filtre déjà actif reste affiché.
- Dans l’inspecteur, `not_evaluated`, `unspecified`, `read_only_local_projection` sont traduits pour l’affichage; les références brutes restent consultables sous « Provenance et détails techniques ».
- La constellation ne fait plus remonter la relation métadonnée `v9:node_kind` comme premier groupe de liens conceptuels. L’assertion elle-même reste intacte.

## Frontières

- Les dictionnaires sont des **aides de présentation**, pas un glossaire canonique général ni une validation sémantique.
- Pas de traduction automatique de toutes les œuvres Wikidata. La langue source est conservée à défaut de traduction certifiée.
- Les statuts des assertions ne changent pas; la sélection et la lecture locales restent soumises aux règles actuelles.
- Pas d’écriture dans `C:/mycode/Kristal/locals`; aucun changement de Manager, Interaction Kernel ou Daat.

## Tests et limites

- `node --test tests/semantic-display.test.mjs tests/kristal-local-v10.test.mjs`
- `node scripts/check-svelte-structure.mjs`
- `node scripts/check-frontend-security.mjs`
- `node scripts/check-docs.mjs`
- Lecture réelle Catho : 4 527 entités, 13 217 assertions, 50 définitions de relations; `P138` apparaît « Nommé d’après » sur ses deux arêtes.
- L’exécution complète Astro/Svelte et la validation dans un navigateur Windows **restent à faire** sur l’installation de l’utilisateur.

## Installation

1. Sauvegarder le dossier Konstellation et arrêter le serveur.
2. Appliquer le correctif à la racine du dépôt `C:\mycode\Konstellation\Konstellation`, en conservant les sous-dossiers.
3. Conserver `config/local-catalog.json` et `config/active-reader.json` existants : **le correctif ne les remplace pas**.
4. Lancer `Konstellation.cmd`, sélectionner `A-Kristal-Catho` dans « Mes Kristals ».
5. Tester `aquin`, ouvrir Albert le Grand, consulter une facette, puis vérifier les libellés et la provenance d’une arête `P138`.
