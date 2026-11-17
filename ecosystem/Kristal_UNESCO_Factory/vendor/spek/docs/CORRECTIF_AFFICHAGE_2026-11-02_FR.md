# Spek — affichage compact et aperçu : correctif du 2 novembre 2026

Ce correctif ne change ni les compositions prescrites par l'IA, ni les états canoniques, ni les permissions de publication.

## Pourquoi corriger l'interface ?

L'ancien lanceur ouvrait une fenêtre de **1270 × 820 px** même sur un petit écran. Les commandes et descriptions situées à droite pouvaient donc apparaître tronquées, comme sur les captures en 1024/1069 px. Le lanceur tient maintenant compte des dimensions de l'écran, préserve la possibilité de redimensionner la fenêtre et garde la zone de travail prioritaire.

## Catalogue, source, aperçu : trois états distincts

- **Kristal trouvé dans le registre** : les compositions proposées sont visibles, sans lecture du contenu canonique.
- **Dossier local identifié** : Spek a trouvé un dossier dont l'identité déclarée correspond au slug. Il ne l'a pas encore ouvert.
- **Sources ouvertes** : l'utilisateur a explicitement ouvert le dossier local ; l'outil peut vérifier la correspondance avec une étude structurelle existante.

Les cinq Kristals dont une revue structurelle existe disposent d'une exploration privée si l'état source correspond. Pour les 122 autres, l'onglet Aperçu renvoie explicitement vers **Voir le plan proposé** et **Ouvrir les sources trouvées** ; il ne suggère plus qu'un aperçu structurel détaillé est prêt.

La prévisualisation d'une **page Wiki rédigée** reste distincte : elle nécessite un article et ses réalisations linguistiques SemantiK vérifiées. Aucun triplet technique n'est automatiquement converti en phrase, aucune page n'est publiée et aucun contrôle C1/C2/C3 n'est contourné.

## Installation

Fermer Spek. Extraire le correctif dans le **dossier parent** qui contient `Spek/`, en conservant la structure de l'archive. Relancer `START_SPEK.bat`. Les tests de démarrage existants restent disponibles avec `VERIFIER_INSTALLATION_SPEK.cmd`.
