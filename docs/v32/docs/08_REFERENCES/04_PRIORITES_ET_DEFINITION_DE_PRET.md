# Décisions de priorité et conditions de départ du refactor

**V32.1 :** la priorité n’est plus une « nouvelle base de Kristals sujets » mais **lecture des îlots existants + proposition EncyK + admission différée et qualifiée**. Voir [plan A–E](../09_FEDERATION_KRISTAL/07_LOTS_A_E.md).


## Ce qui est raisonnablement connu

Nous avons **assez de code et de données de référence pour documenter l'architecture**. Le thésaurus, les 88 branches, le crosswalk candidat, l'index Wikipédia QID, l'index Wikidata compact, les contrats ZIP et la station existent chacun dans un composant observé. Il n'est **pas** nécessaire de coder un clone de LinkedDataHub, de Skope ou de Kristalizer.

## Ce qui reste réellement manquant dans la future application

1. Une **autorité unique de jobs et propositions EncyK** multibranches, avec références de sujets et liens N:N vers les îlots existants; pas d’ID de Kristal attribué à chaque QID.
2. Un **raccordement automatique P3916** entre les 88 snapshots et la jointure locale `wiki_qid`, en gardant les ambiguïtés, la provenance et les alias.
3. Un **moteur de découverte par jointures et traversées indexées**, dont la stratégie varie avec la branche et non des boucles N pages × N concepts.
4. Un **protocole deux passes** permettant de réutiliser l'article sélectionné une seule fois et de l'enrichir intensément, avec des retours idempotents.
5. Une **interface manager unique** qui récupère la robustesse du centre de production, retire les doubles écrans de pilotage et garde diagnostics/backup avancés.

Ce sont les fonctionnalités que le refactor doit créer; ce document ne les présente pas comme implémentées.

## Critères pour commencer le code (sans bloquer des semaines)

- Posséder un accès en lecture à un exemplaire local de chaque **catégorie de source** : UNESCO snapshot, P3916, Wikidata compact, `wiki_qid` et résolution XML.
- Pouvoir exécuter une jointure QID→page et afficher son taux réel sur D:; sinon la prototype peut commencer avec fixtures, mais ne pas annoncer de rendement.
- Sélectionner une branche de test autre que `mt1.10` et 20–50 pages à enrichir; conserver le moteur historique arrêté, sans migration obligatoire.
- Référencer le module existant à réutiliser pour chaque étape, et préciser les trois fonctions à remplacer plutôt que « on réécrit tout ».
- Conserver Skope et Kristalizer à l'extérieur et vérifier que les scripts de migration ne ciblent pas leurs dossiers.

## Ce qui n'est PAS une condition d'entrée

- Taux de rappel Wikipédia à 100 %; audit indépendant exhaustif de chaque omission.
- Résolution des 134 mappings P3916 ambigus et 77 sans mapping avant de commencer.
- Clôture des 21k HOLD historiques de `unesco.mt1.10`.
- Audit `quick_check` de 125 Go, manifeste SHA de tous les scripts, triple revue humaine des sources.
- Fusion préalable de tous les dépôts, ni création de la totalité de l'interface.

## Responsabilité de mise à jour de la doc

Lorsqu'un module V32 existe réellement, changer ses mentions de `[CIBLE]` à `[OBSERVÉ CODE V32]`, indiquer sa localisation et faire évoluer la matrice `fonction ancienne → propriétaire nouveau`. Ne pas effacer l'historique des choix ou faire passer un prototype pour une fonction déployée. Ce petit entretien documentaire **évite à l'IA de redécouvrir le système** et ne doit pas devenir un protocole bureaucratique.
