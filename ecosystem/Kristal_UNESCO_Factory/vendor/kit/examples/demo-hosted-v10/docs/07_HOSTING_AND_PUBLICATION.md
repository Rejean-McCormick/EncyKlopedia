# Hosting et publication v10

Le canon et les commitments restent v9. L'hébergement est une couche v10 séparée.

## Node / repository

TODO — choisir le nœud de collection GitHub qui publiera cet état. Un dépôt peut héberger plusieurs Kristals si les permissions et le lifecycle sont communs.

## State path

TODO — utiliser un chemin stable et relatif au repo, par exemple `kristals/<slug>/state/state-snapshot.json`.

## Qualification

La qualification doit viser le commit exact contenant l'état exporté.

## Publication

La publication v10 produit un bundle vérifiable et une Release immuable. Elle ne modifie pas le Logical Commitment v9.

## Activation

L'activation reste séparée et optionnelle. Une Release publiée n'est pas automatiquement l'état actif d'un channel.
