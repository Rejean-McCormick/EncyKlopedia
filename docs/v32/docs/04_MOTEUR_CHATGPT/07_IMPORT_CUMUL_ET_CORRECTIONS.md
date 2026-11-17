# Import V32 : cumul de connaissances, doublons, corrections et erreurs partielles

**V32.1 :** dans ce chapitre, « importer des claims » signifie **enregistrer des propositions provisoires EncyK**, pas écrire le canon des îlots. `SELECT` associe un **sujet référencé**, sans créer obligatoirement un workspace; un reçu de ZIP ne remplace jamais un [reçu d’admission](../09_FEDERATION_KRISTAL/04_ADMISSION_KIT_REPRISE.md).


## Trois niveaux à distinguer

1. **Transport** : ZIP/chat/message. Le retour n'est pas encore une décision ni une connaissance.
2. **Validation de contrat** : le fichier correspond à un job existant et les IDs/versions/citations sont compatibles avec les sources conservées.
3. **Intégration** : la base de travail consomme les nouvelles décisions/faits et confirme la transaction dans un `import_receipt`.

Les services de sélection et d'enrichissement partagent la plomberie de transport, mais **n'écrivent pas les mêmes tables**. Le dépôt de ZIP n'est jamais un déploiement de code.

## Import SELECT/REJECT/HOLD

Affecter une décision à une paire connue; garder sa justification et sa révision documentaire. Les multiples routes de graphe restent dans le registre de candidature. `SELECT` crée/récupère un sujet référencé et un lien de navigation (`concept_id`, `branch_id`). `REJECT` exclut cette **paire dans cette version de revue**, pas la page entière du monde. `HOLD` la conserve disponible pour une autre campagne de contexte.

Une même page peut recevoir `SELECT` pour un concept et `REJECT` pour un autre. Elle ne doit pas être exclue globalement à cause du deuxième cas.

## Import des propositions sourcées (staging EncyK)

Pour chaque claim : identifier le sujet, normaliser le prédicat/objet si une règle existe, rechercher la clé sémantique proche, fusionner si identique sans écraser les citations, conserver une variante si les valeurs sont concurrentes. Les citations et les sources sont N:N. Pour une assertion Wikidata, l'ID de déclaration peut servir de référence directe; l'index compact seul ne suffit pas.

Ne pas forcer une taxonomie de prédicats trop fermée au premier jour : utiliser des prédicats courants et stocker les valeurs originales. L'agent de finition pourra harmoniser, reformuler et arbitrer en 2027.

## Gestion des erreurs partielle

Une erreur de citation ne doit pas effacer 200 claims corrects si le format du retour permet l'import transactionnel de la partie valide **avec une liste explicite d'items refusés**. Plusieurs stratégies sont acceptables (transaction complète et retour de réparation, ou import partiel avec accusé par item); en choisir une et la documenter. Le programme ne doit ni faire disparaître un item invalide silencieusement ni marquer tout le job « terminé » s'il reste des items demandés non traités.

## Reprise

`import_receipt` unique par `(job_id, return_digest)` ou ID logique; `job_item` suit le statut de chaque sujet/pair. Les requêtes d'intégration sont réentrantes : une panne après l'écriture d'un claim ne réinitialise pas sa source ni ne compte deux fois le fait. Le tableau de bord doit clairement offrir « Reprendre un import » ou « Corriger le retour », plutôt que demander un nouveau batch mondial.

## Principe de non canonisation

Même si ChatGPT est très généreux en contenu, `SELECT`, les propositions et la base de travail ne sont jamais des actes de publication ou d’admission dans un état Kristal. Une politique future pourra admettre certaines propositions dans des états Kristal via un auteur qualifié. La publication externe reste distincte; aucune promotion implicite.
