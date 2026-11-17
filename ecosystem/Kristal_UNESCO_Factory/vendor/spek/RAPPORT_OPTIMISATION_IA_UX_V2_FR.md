# Livraison — Spek Atelier optimisé, 1 novembre 2026

## Source de la refonte

`guide-architecture-interfaces-ia-v2(8).zip`, lu en tant que guide de **navigation par intentions**, de parcours principal, de regroupement des actions contextuelles, de conservation des statuts réels et de préservation des mécanismes fiables. Voir `docs/ATELIER_OPTIMISE_IA_V2.md` pour la correspondance ancien/nouveau.

## Livré

- **Atelier GUI unique**, via `START_SPEK.bat` / `OUVRIR_SPEK.cmd` / `Spek_Template_Manager.pyw`, avec ouverture explicite article+realizations, vérification, aperçu local HTML, navigation des templates et gestion contextuelle.
- **Ouverture de Kristal en lecture seule** (métadonnées déclarées). Ne sélectionne pas ses connaissances, ne l’analyse pas pour deviner des templates, ne lance pas SemantiK.
- **Registre IA de 19 compositions éditoriales** avec 19 recettes, 19 profils Arketype préexistants, 8 layouts Spek, et assignations Kristal volontairement **vides** avant réception du rapport des 127 Kristals.
- **Contrôle de non-régression** des contrats des layouts référencés par les compositions (suppression/modification incompatible refusée).
- **Commandes** `list-wiki-compositions` et `check-wiki-compositions`.
- Documentation et catalogue HTML rangés sous **Spek/**, pas à côté du dépôt.
- Source Spek 0.5 et ses exporteurs HTML/PDF/TeX, tests et démonstrations maintenus.

## Limites transparentes

La démonstration historique de `START_SPEK.bat` est conservée sous `DEMO_SPEK_LOCAL.bat` : pas de perte de fonctionnalité.

Aucun Wiki de Kristal réel n’est encore généré par la seule ouverture d’un dossier Kristal. Il faut les assertions choisies et les formulations qualifiées fournies à Spek, plus les assignations éditoriales IA et autorisations de publication séparées. Un aperçu local HTML est une démonstration **non publiable** tant que ces frontières ne sont pas satisfaites.

## Vérifications effectuées

- Suite de tests en ligne de commande : **95 tests réussis** (tests initiaux de Spek + nouvelles vérifications de registre et de workflow).
- Démarrage graphique en session X virtuelle ; navigation des compositions, ouverture d’un article et d’un Kristal en lecture seule.
- Génération d'un vrai aperçu HTML français avec les fixtures Spek : le compilateur réel a produit le fichier et son inventaire.
- `python -m spek check-wiki-compositions` : **19 compositions valides, zéro assignation**.
- Vérifications ZIP : CRC et chemins internes, sans `.git` ni fichiers temporaires générés.
- Le comportement exact sur Windows de l'utilisateur n'a pas pu être testé ici.

## Installation propre

Sauvegarder les changements locaux non poussés. Cloner `https://github.com/Rejean-McCormick/Spek.git` dans `C:\\mycode\\Kristal\\Spek` puis extraire l’archive, dont le dossier racine est **`Spek/`**, dans `C:\\mycode\\Kristal` en acceptant les remplacements.

Le ZIP **ne contient pas** `.git`. La connexion Git est donc récupérée par le clone ; aucun push automatique n’est effectué. Puis lancer `C:\\mycode\\Kristal\\Spek\\OUVRIR_SPEK.cmd`.

Sur un clone neuf, retirer l’ancien `Spek/wiki-templates/` **après sauvegarde de tout contenu personnalisé**, car la nouvelle bibliothèque est sous `Spek/template_library/wiki/`.
