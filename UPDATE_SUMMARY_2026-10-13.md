# Mise à jour Konstellation — 13 octobre 2026

Cible : snapshot `znapshot_Konstellation_10131042.zip`.

## Inclus

- Intégration **locale et facultative** de l'export candidat `kristal.manager-local-inventory/0.1-candidate`.
- Fichier privé de politique `konstellation.manager-access-policy/0.1` **obligatoire** pour un inventaire Manager brut : aucune autorisation implicite.
- Métadonnées **non canoniques** de l'Authoring Kit 3.3 projetées dans un catalogue local explicite (archétype, usage, organisation, recommandations de lecture, taille mesurée déclarée).
- Vue **My Kristals** enrichie ; aucune modification des Kristals ni ouverture implicite d'un inventaire local.
- Prévisualisation historique déplacée dans `examples/fleet/legacy` ; le `.pyw` racine permet un nettoyage volontaire et contrôlé de l'ancien emplacement après copie de la mise à jour.
- Documentation et tests `tests/manager-discovery.test.mjs`.

## Mode d'installation

1. Effectuer une sauvegarde ou commit du dépôt Konstellation local.
2. Extraire le ZIP **à la racine du dépôt Konstellation**, en remplaçant les fichiers mis à jour.
3. Lire `docs/32-manager-discovery-3.3.md` pour configurer les fichiers privés d'inventaire, politique et Discovery.
4. Si l'ancien fichier `examples/fleet/manager-preview.example.json` subsiste, lancer **`Nettoyage_Konstellation.pyw`** après vérification des éléments listés. Aucun nettoyage automatique n'a lieu.
5. Exécuter les tests et construire dans l'environnement Node pris en charge (>=24.15, avec les dépendances du projet).

## Validation effectuée ici

- Tests ciblés `fleet`, `manager-discovery`, `kristal-v10` : **19/19 passés** avec Node 22.
- Vérifications de documentation, frontend structure et script `.pyw` : passées.
- Suite complète non qualifiée dans cet environnement (dépendances `ajv` et `hyparquet` absentes et Node 22 inférieur au minimum supporté 24.15).
- Aucune validation visuelle navigateur ou Windows n'a été réalisée.

## Frontières préservées

Ce patch n'inclut ni changement dans Kristal Manager ou Authoring Kit, ni changement canonique de Kristal, ni synchronisation GitHub, ni autorisation de publication C2/C4. Arketype reste descriptif.
