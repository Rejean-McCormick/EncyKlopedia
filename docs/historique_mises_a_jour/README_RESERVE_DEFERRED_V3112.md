# EncyKlopedia v31.12 — Réserve UNESCO DEFERRED et postes inoccupés

Date : 15 novembre 2026. Correctif **limité à l'empaquetage** de la station v30.

## Pourquoi

Lors d'une vague avec **5 tâches ouvertes sur 10** (3 revues UNESCO de 4 000
propositions et 2 packs Kristal) la station affichait encore **7 023 candidats
PENDING + DEFERRED**. La découverte v31.11 avait trouvé 19 023 nouveaux
candidats, mais la file n'avait créé que 12 000 propositions à examiner.

Dans `Station._prepare_v28`, le code s'arrêtait si la liste `PENDING` était vide,
**avant** d'examiner `DEFERRED`. Un ensemble entièrement `DEFERRED` ne pouvait
jamais former un nouveau pack, bien que ces propositions n'aient été ni rejetées
ni revues. Un test isolé reproduit la situation avec 7 023 lignes.

La répartition entre `PENDING` et `DEFERRED` n'a pas encore été mesurée sur la
station Windows de production ; le correctif traite les deux états sans
réarmer les dossiers décidés ou HOLD.

## Modification

- Examiner les deux réserves (`PENDING` et `DEFERRED`) avant de conclure qu'il
  n'existe plus rien à empaqueter.
- Continuer à privilégier les `PENDING`, mais si leur stock est trop faible,
  compléter les lots à partir des `DEFERRED` ; une réserve exclusivement
  `DEFERRED` peut produire ses propres lots.
- Plafond inchangé à **4 000** propositions par revue, sans exclure ni rejeter
  automatiquement les articles non sélectionnés.
- En présence de revues ouvertes, **la nouvelle découverte demeure gelée**.
  Les propositions **déjà découvertes et conservées en station** peuvent être
  empaquetées sans modifier les preuves de ces revues.
- Journal explicite de la réserve restante : `PENDING=... ; DEFERRED=...`.
- Message de diagnostic/interface clarifié pour ne plus confondre gel de la
  découverte et interdiction de préparer la réserve.

## Contrats inchangés

- Identifiants, révisions, SHA-256, preuves des tâches en cours et décisions
  importées inchangés.
- `APPROVE`, `REJECT`, `HOLD` déterminés uniquement lors de la revue ChatGPT ;
  aucune admission canonique ni publication.
- Ne pas modifier ni reconstruire les ZIP déjà envoyés ; aucune réinitialisation
  de file ou exclusion permanente de candidat.
- Les candidatures de faible priorité peuvent être nombreuses et nécessitent
  une vraie revue documentaire ; `DEFERRED` **n'est pas un verdict de pertinence**.

## Tests de régression

`python -m unittest discover -s tests -p test_station_reserve_deferred_v3112.py -v`

Scénarios : 7 023 DEFERRED produisant des lots 4 000 et 3 023, mélange
PENDING/DEFERRED sans doublon, revue UNESCO ouverte interdisant la découverte
mais pas l'empaquetage. Compatibilité ciblée avec les tests v30, v31.9 et v31.7.

## Déploiement

1. Effectuer une nouvelle sauvegarde des bases *résultats* avec l'outil v3.
2. Installer **uniquement** par « Mises à jour logicielles » (préconditions
   SHA-256 vérifiées, sauvegardes de code par le mécanisme natif).
3. Fermer puis relancer `LANCER_ENCYKLOPEDIA.cmd` ; ne pas reconstituer les
   tâches déjà émises.
4. Avec une réserve existante, utiliser « Préparer toute la prochaine vague ».
   S'il existe des revues ouvertes, seul le passage Discover est sauté ; le
   programme tente d'empaqueter les candidats déjà présents.
5. Vérifier le nombre de nouvelles revues et le nouveau message
   `Réserve UNESCO après préparation : PENDING=... ; DEFERRED=...`.

Le cas de production *7 023* est susceptible de donner **deux** nouvelles
revues (4 000 + 3 023), **sous réserve** de l'état exact des candidats, de la
cohérence de leurs preuves et de l'absence d'une autre limite de préparation.
Cela ne garantira pas automatiquement dix postes occupés.
