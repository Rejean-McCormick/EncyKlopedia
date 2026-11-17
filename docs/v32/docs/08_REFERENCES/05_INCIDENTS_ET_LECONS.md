# Incidents observés dans V31 — leçons pour V32

Cette liste n'est **pas** un inventaire de bogues ouverts dans la future base V32. Ce sont des scénarios historiques utiles pour éviter de répéter des cycles improductifs.

## 1. « Les 10 postes ne se remplissent pas » n'est pas un diagnostic

Une première phase `mt1.10` a produit parfois 3 à 6 packs malgré 10 postes. Certaines fois le stock réellement disponible ne suffisait pas; d'autres fois un bogue de distribution masquait les candidats `DEFERRED`. La station v31.12 a corrigé le chemin **historique** de récupération `PENDING+DEFERRED`. En revanche, la fonction `routage_branches_v311.prepare()` du snapshot conserve un `if not ranked: continue` avant de lire les DEFERRED, avec un risque multibranche similaire. Pour V32 : mesurer séparément PENDING/DEFERRED, tester `PENDING=0` et stock reporté positif, ne pas viser 10/10 comme fin en soi.

## 2. Le problème originel des 19 concepts vides

Le vieux moteur partait essentiellement des affectations de catalogue. Si un concept n'avait aucun article initial, il avait peu de chances de recevoir un premier candidat. V31.10 a ajouté scans de titres/catégories et V31.11 un rappel ontologique par relations UNESCO. Ces stratégies ont découvert de nouvelles paires, mais les chiffres ne prouvent pas la saturation du corpus. Pour V32 : **démarrer à partir des ancrages P3916 et du graphe**, puis combiner les rappels faibles, pas l'inverse.

## 3. Un audit de couverture n'est pas une preuve de complétude

Le rapport v31.2 a mesuré 214 554 paires découvertes, 21 226 HOLD et 791 paires absentes des deux index interrogés dans un état antérieur. Ces chiffres sont des observations de **cette génération**, pas le résultat final de V32. L'audit charge plusieurs grands ensembles en mémoire et ne démontre ni exhaustivité ni rappel réel. Son calcul d'« absent catalogue » ne considère pas toutes les affectations historiques; il faut rapprocher la station, le registre de décisions **et** `assignments` avant d'expliquer un écart. Pour V32 : inventaire d'états simple, échantillon d'omissions utile et libellé « inconnu » quand l'exploration ne permet pas de conclure.

## 4. Une requête de diagnostic peut être trompeuse en production

Les bases SQLite source et résultats peuvent être consultées séparément pendant les imports. Les totaux observés ne sont alors pas une photographie atomique. Faire une sauvegarde cohérente pour les investigations exigeant une preuve ferme; pour la production normale, signaler seulement la temporalité du comptage.

## 5. Les prompts « prudents » peuvent produire peu de savoir

Le pilote Kristal 289 a couvert 64 articles et produit 305 claims vérifiés dans les sources du pack. Ce volume est un exemple, pas un plafond ni une cible automatique. Le V32 doit demander **plus de connaissance réellement présente** lorsqu'un article est dense : chronologie, caractéristiques, mécanismes, institutions, conséquences, acteurs, controverses attribuées, comparaisons, sans gonfler les petits articles ni inventer des citations.

## 6. Le guide de démarrage historique est dispersé

Le README ancien décrit surtout un lecteur alpha, alors que le centre v30 était un producteur privé; les guides v27 parlaient encore de petits packs. La documentation V32 doit devenir le **point d'entrée unique pour coder** : architecture actuelle et cible distinctes, propriétaire des données, module à réutiliser, tests visibles, catalogue des fonctions.

## 7. Trop de contrôles cérémoniels ralentissent les déplacements

Les overlays v31 avaient des contrôles de précondition SHA utiles en production, mais la grande migration V32 peut se faire dans un **nouveau repo/une nouvelle SQLite** avec des tests concrets, sans générer un manifeste SHA pour chaque déplacement de fichier. Les identités logiques et la citation exacte de la source demeurent indispensables à la qualité de la connaissance; ce n'est pas la même chose que l'ancienne mécanique de mise à jour de logiciels.
