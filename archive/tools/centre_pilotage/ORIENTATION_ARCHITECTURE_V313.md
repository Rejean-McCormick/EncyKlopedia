# Note d'architecture — EncyKlopedia v31.3

## Constats fondés sur le diagnostic réel

1. Poste Windows opérationnel avec PowerShell 7.6.10, Python 3.12, Node 22, Tkinter installé.
2. Station : 281 jobs, dont 277 DONE et 4 READY ; conserver l'état actif existant.
3. UNESCO : 41 concepts configurés pour la première branche, 6 197 HOLD non tranchés ; l'achèvement global n'est pas démontré.
4. Kristal : base privée avec 25 812 enregistrements `claims`, distincts des articles canoniques.
5. Les schémas SQLite du diagnostic couvrent cinq sources majeures et sont suffisants pour une première supervision en lecture seule.

## Amélioration immédiatement livrée

Un tableau de bord autonome **reprend le diagnostic UNESCO v31.2 existant** et affiche le statut de la station, des réserves et de Kristal. Les sources ne sont jamais modifiées. Le code peut être déployé en parallèle de l'ancienne interface et retiré simplement en effaçant son dossier après fermeture.

## Travaux suivants à réaliser après vérifications locales

- **S0 : Sécurité des lectures** : tests de lecture concurrents sur copies de bases en WAL ; métriques de fraîcheur et cohérence de génération.
- **S1 : Inventaire exhaustif** : différencier paires absentes d'index, réserve de candidats et états historiques ; vérification manuelle sur un échantillon de 667 paires non rapprochées.
- **S2 : Qualité documentaire** : file de seconde revue des HOLD, sans décision automatisée et sans modification des preuves tant que le gel est actif.
- **S3 : Saturation** : campagnes successives explicitement autorisées, observation de vraies nouvelles graines et estimation indépendante des omissions.
- **S4 : Intégration station** : concevoir un contrat d'interface stable pour les métriques ; éviter le couplage aux tables internes. Toute écriture éventuelle exigera une phase distincte avec tests et sauvegardes.

**Règle fondamentale :** aucune prétention de « X % terminé » pour la branche tant que la saturation et le rappel ne sont pas démontrés. Les compteurs de production (tâches terminées) ne mesurent pas la complétude encyclopédique.
