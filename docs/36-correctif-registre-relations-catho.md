# Correctif du registre des relations — 16 octobre 2026

## Symptôme

Au démarrage du lecteur local Catho, validation de `relation-registry/0.2` :
`/relations/1/domain must NOT have more than 10 items`.

## Cause

Le graphe dérivé de Catho possède 13 catégories de nœuds. L'adaptateur
`kristal-local-v10` publiait une seule relation technique `v9:node_kind`
avec les 13 catégories dans `domain`. Le contrat Konstellation impose 10
catégories au maximum par relation.

## Correction

Le lecteur partitionne les domaines trop grands en définitions de relations
au maximum de dix types chacune. Il conserve toutes les assertions, leur
identifiant, le type et le statut épistémique. Le même mécanisme protège
les liens dérivés reliant plus de dix types de sources à une même catégorie
cible. Le contrat global n'est **pas** assoupli.

## Vérification

- 10/10 tests ciblés du lecteur, y compris une fixture de 13 types sources.
- Avec l'archive Catho v10 fournie : 4 527 entités, 13 217 assertions,
  50 définitions de relations, 15 types dont les deux types techniques.
- Registre conforme à `contracts/relation-registry.schema.json` (JSON Schema 2020-12).
- Toutes les assertions trouvent un domaine et une portée compatibles.

Ces contrôles sont effectués hors navigateur. Le lancement sur Windows
avec Node 24.21 et le rendu UI doivent être confirmés par l'utilisateur.
Aucune modification de Catho, du Framework, de Manager, du noyau
Interaction Kernel ni de Daat n'est nécessaire pour ce correctif.
