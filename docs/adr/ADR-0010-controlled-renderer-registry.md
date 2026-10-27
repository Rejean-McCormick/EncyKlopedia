# ADR-0010 — Registry contrôlé de renderers

- Statut : accepté

## Décision

Les renderers exécutables appartiennent à Konstellation ou à une extension opérateur explicitement approuvée. Un Kristal ne peut pas fournir du JavaScript, du HTML ou un composant Svelte à exécuter.

## Conséquences

- surface d'attaque réduite ;
- UX cohérente ;
- tests centralisés ;
- accessibilité contrôlable ;
- les extensions passent par des contrats déclaratifs.
