# Consolidation EncyK 0.13.1 — Skope à dépôt unique

**Statut** : EncyK est le seul dépôt actif. Skope devient l’outil
`00_system/tools/skope/` et n’est plus livré comme projet autonome.

## Sources fusionnées

- Source principale : EncyK `0.13.0_Skope_Arketype` (contrats EncyK,
  Arketype 1.4, API locale, CLI, interface, `Lancer_Skope.pyw`, staged export).
- Source complémentaire : première intégration `0.12_Skope_Integre` ;
  sa licence MIT est conservée et ses tests/invariants sont examinés, sans réintroduire le second importeur
  `ingest.py`, les bases `entities/edges`, le CLI démo autonome, les
  nettoyeurs spécifiques au dépôt Skope ni un second contrat d’export.
- EncyK garde `encyk.source-evidence-handoff/2.0.0` inchangé : la liste
  des versions de producteurs admises inclut maintenant `0.13.1`.

## Flux retenu

1. Finaliser un index global EncyK, comprenant `meta.complete=1`.
2. Lancer `Lancer_Skope.pyw` ; Skope lit cet index sans écriture.
3. Explorer racines, branches, profondeur, convergence ; consulter la
   proposition `skope-encyk-proposal/1.0`, éventuellement guidée par
   `arketype.scope-guidance/1.0` à valeur uniquement descriptive.
4. Après contrôle humain de la provenance du dump et de la liste des QID,
   copier les deux fichiers de `staged/` vers leurs chemins EncyK.
5. EncyK extrait le **JSON Wikidata complet** et prépare le handoff
   Médiathèque. La vue Skope n’est jamais utilisée comme preuve.

## Nettoyage d’une double installation dans EncyK

Le manifeste `00_system/tools/migration/obsolete-files.json` répertorie les
chemins présents uniquement dans la première archive EncyK intégrée,
avec leur SHA-256 d'origine. L’utilitaire **facultatif**
`Nettoyer_Fichiers_Obsoletes.pyw` vérifie les fichiers sur la machine
locale, prévisualise et demande confirmation avant suppression.
Un fichier modifié ou inconnu est conservé. Aucun dossier, dépôt externe,
`.git`, dump ou base de données n’est supprimé.

Le dépôt Skope autonome ne sera **pas** nettoyé par EncyK :
son effacement/retrait relève d’une décision manuelle de l’utilisateur.

## Limites et validation

L'index compact est lossy (arêtes agrégées, pas de statement IDs ni JSON
source complet). Aucune conversion Arketype → `state_scope` et aucune
publication/activation automatiques. Tests locaux documentés dans `VALIDATION.md`.
L'interface Windows sur la machine cible et un vrai dump Wikidata massif
restent non vérifiés.
