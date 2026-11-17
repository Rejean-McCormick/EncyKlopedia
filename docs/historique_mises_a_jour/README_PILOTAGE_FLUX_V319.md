# EncyKlopedia v31.9 — Pilotage des vagues et réexamen HOLD

## Situation vérifiée

Lorsqu'un utilisateur réarmait 500 HOLD, `reopen_holds()` créait immédiatement
une revue UNESCO via `prepare()`. Une seule revue `READY` suffisait ensuite à
activer le gel des preuves, et le batch global reportait la découverte XML/SQL.
De plus, le journal nommait « éligibles » les candidats déjà parcourus par
l'index, qui peuvent être `DONE`, `HOLD`, `QUEUED`, etc. Ce nombre n'était pas
le stock `PENDING` réellement disponible.

## Correctif

1. Les réexamens HOLD sont refusés tant qu'une revue UNESCO est ouverte
   (`WAITING`, `READY`, `SENT`, `ERROR`, `IMPORTING`, `NEEDS_CONFIRMATION`).
   Aucune tâche et aucune preuve figée n'est alors modifiée.
2. Lorsqu'il n'y a plus de revue ouverte, le réexamen HOLD volontaire (max. 500)
   remet les candidats sélectionnés en `PENDING`, puis lance le batch global
   complet : *découverte d'abord*, indexation et préparation ensuite.
3. La petite table additive `hold_reexaminations` mémorise les tentatives de
   réexamen explicites et l'identifiant/l'empreinte de la revue précédente.
   La sélection privilégie les candidats moins souvent réexaminés : elle évite
   de recycler toujours les mêmes HOLD, sans exclusion définitive.
4. L'interface affiche séparément les **tâches** encore non attribuées et les
   **candidats** `PENDING + DEFERRED`. Les causes du gel sont visibles et le
   bouton HOLD est désactivé lorsqu'une revue UNESCO est ouverte.
5. Le journal indique « candidats parcourus dans la découverte » au lieu de
   « propositions éligibles », pour éviter d'assimiler ce nombre à une file.

## Contrats préservés

- Jamais de reconstruction des anciens ZIP ou tâches ; aucun changement des
  APPROVE/REJECT/HOLD déjà importés en l'absence d'un réexamen **explicite**.
- Les fichiers de preuve v28, les manifestes, les SHA et les deltas v27 restent
  sous le régime existant. L'ancienne preuve d'un HOLD volontairement réarmé
  reste dans le ZIP original de son travail et sa trace est sauvegardée dans
  `hold_reexaminations` avant toute remise en `PENDING`.
- La base cumulative Kristal et le catalogue UNESCO ne sont pas modifiés par
  l'installation de cet overlay ; une seule table est ajoutée à la base
  **de pilotage** par le logiciel lors du redémarrage.
- Aucune admission canonique ni publication.
- Le correctif n'invente pas de candidats et ne garantit pas 10 postes occupés
  si les moteurs n'ont pas suffisamment de nouveau travail.

## Installation prudente

**Attendre l'import complet des cinq packs actuellement ouverts.** Arrêter la
station, réaliser une sauvegarde locale du poste de travail et des bases SQLite,
prévalider l'overlay depuis « Mises à jour logicielles » et confirmer seulement
si toutes les préconditions SHA-256 correspondent. Redémarrer la station.

Au prochain cycle, cliquer « Préparer toute la prochaine vague » avant tout
réexamen de HOLD. Consulter le diagnostic. Si la découverte ne fournit plus de
nouveau travail, lancer un réexamen volontaire de 500 HOLD, qui fera lui-même
la découverte en premier. Ne pas lancer de réexamen en boucle.

## Limites

Les données de la station Windows ne sont pas présentes dans le snapshot
source. La prévalidation, l'application et le retour arrière ont donc été
validés **sur copie isolée**. L'installation sur le poste réel doit être
confirmée par les empreintes. La couverture exploratoire UNESCO n'est toujours
pas démontrée par l'absence de packs.
