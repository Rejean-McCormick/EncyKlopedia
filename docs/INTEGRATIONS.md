# Intégrations — guide complet

Ce document complète [06-integrations.md](06-integrations.md) avec les règles d'exploitation.

## 1. Adapter boundary

Chaque intégration produit un objet que le moteur peut lire tout en conservant :

- identité source ;
- version ;
- pertes ;
- policy ;
- provenance de transformation.

## 2. Runtime Pack

Le lecteur de Runtime Pack doit vérifier :

- manifest ;
- checksums/signatures configurées ;
- catalog ;
- tables ;
- Reader Policy ;
- capacités annoncées.

Une capacité externe non disponible doit être signalée, pas simulée.

## 3. HTTP projection

Pour une source distante :

- pagination obligatoire ;
- timeouts ;
- taille maximale ;
- validation de schéma ;
- identité/fingerprint ;
- retry limité ;
- aucune confiance implicite dans le client.

## 4. SemantiK / SA

SA est une intégration distincte de la navigation.

Règles :

- action explicitement demandée ;
- recompute côté serveur ;
- CommunicationRequest validée ;
- CommunicationResult validé ;
- aucune mutation du Kristal par défaut ;
- erreurs d'indisponibilité explicites.

## 5. navigationHints

Les hints sont acceptés seulement après validation contre `contracts/navigation-hints.schema.json` ou une version ultérieure compatible.

Ils sont advisory. En cas de conflit manifeste avec la structure, le moteur peut les plafonner ou les ignorer avec diagnostic.

## 6. Nouvelles intégrations

Avant d'ajouter un adaptateur :

- démontrer qu'un adaptateur existant ne suffit pas ;
- documenter la frontière de confiance ;
- définir le loss model ;
- ajouter des fixtures ;
- ajouter un test de non-fuite policy ;
- documenter la maintenance/version upstream.
