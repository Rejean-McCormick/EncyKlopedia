# Stockage V32 proposé : registre unique, jobs et reprise

**CORRECTION V32.1 :** cette SQLite est un **registre de travail EncyK**, pas un nouveau canon. Les anciennes tables `kristal`, `fact_claim` et `fact_evidence` sont remplacées dans le schéma ci-dessous par `island_ref`, `proposal`, `proposal_evidence` et `admission_receipt` : voir [modèle V32.1](../09_FEDERATION_KRISTAL/06_CONTRATS_LOGIQUES_ET_EXEMPLES.md). Toute admission dans un îlot a un auteur et une transaction de reprise séparés.


**Principe : monolithe modulaire SQLite avec bases de travail modestes.** Utiliser de nouvelles tables dans un espace `D:\EncyKlopedia\V32` configurable, sans toucher aux index géants et sans imposer la migration du pilote v25/v27/v28/v30.

## Découpage conseillé

Un ou plusieurs SQLite métier restent acceptables; pour démarrer, **une base V32 unique** simplifie les transactions de sélection/enrichissement. Les gros textes ne sont pas des BLOB à copier dans le SQLite : des chemins de caches sur D: suffisent. Aucune architecture event-sourcing complète n'est nécessaire.

### Tables proposées (schéma conceptuel)

| Table | Identité / rôle | Index utiles |
|---|---|---|
| `branch` | `branch_id` | unique branch |
| `concept` | `concept_id`, URI, labels | PK, index labels si recherche locale |
| `branch_concept` | `(branch_id, concept_id)` | index concept inverse |
| `concept_relation` | `(from_id, predicate, to_id)` | index source / target |
| `alignment` | `(concept_id, qid, method)` + état | index qid, status |
| `qid_page` | `(qid, wiki, page_id)` + source/redirect | index QID et page |
| `candidate` | `(concept_id, subject_key, page_key)` | état, branche/score |
| `candidate_route` | `(candidate_id, route_key)` | index propriété, provenance |
| `selection_decision` | `(candidate_id, decision_revision)` | dernière décision |
| `subject_ref` | `(namespace,subject_id)` et QID éventuel | sujet→routes, jamais îlot forcé |
| `island_ref` | `(namespace,island_id)` + propriétaire et capacité | lecteur/fédération |
| `island_scope` | `(island_ref, concept_id, relation)` + provenance | concept→îlots N:N |
| `source_article` | `(wiki,page_id,revision_id)` | révisions, source cache |
| `proposal` | proposition sourcée, contextualisée, cible potentielle | sujet, statut, version |
| `proposal_evidence` | `(proposal_id,source_key,locator)` | citation, QID statement |
| `admission_decision` | proposition exacte, politique/version, état attendu | audit ciblé |
| `admission_receipt` | auteur, opération, nouvel état constaté | reprise sans écriture dupliquée |
| `job` | `job_id`, `kind`, `status`, `lane`, données | état et création |
| `job_item` | `(job_id,candidate_id)` ou `(job_id,kristal_id)` | imports partiels |
| `import_receipt` | résultat de retour déjà pris en compte | idempotence |
| `run_cursor` | `(branch_id, strategy, anchor, path)` + position | reprise |
| `job_event` | événements opérationnels compacts | historique limité |

Le texte énorme des pages et les fichiers Wikidata originaux restent stockés **une fois** dans les référentiels/caches, pas dans une table de claims ni dans chaque paquet de branche.

## Transactions et reprises

- Créer job et items en **une transaction**; une tâche prête ne peut pas correspondre à une sélection de candidats non persistée.
- Importer un retour avec une clé d'idempotence et un état temporaire, puis commit de l’ensemble des propositions valides et statut job. En cas d'échec, rester `failed_retryable` sans compter le résultat comme terminé.
- La fermeture d'une fenêtre `.pyw` n'annule ni la file ni les données validées. La prochaine ouverture réaffiche la vraie prochaine action.
- Pour le préchargement ou la lecture externe longue, enregistrer `running`, horodatage, dernier item traité; un ancien `running` au redémarrage devient `interrupted/recoverable`, pas « fait ».
- Une branche complète au sens opérationnel est « plus de travail profitable choisi maintenant », pas « tous les sujets Wikipédia sont classés à 100 % ».

## Etats de travail simples

`draft → ready → sent → received → imported` ; erreurs `failed_retryable` et abandons volontaires `skipped`. La passe 1 et la passe 2 ont des jobs **de types distincts** mais partagent l'infrastructure d'envoi/retour. L'UI évite de confondre « pack prêt sur disque », « donné à ChatGPT », « réponse reçue » et « import réussi ».

## File de plusieurs conversations

Dix *slots* visibles, mais nombre de tâches réel piloté par les sources. Le manager peut proposer dix jobs, pas forcer dix jobs fictifs. Une fois un retour importé, il peut attribuer automatiquement la tâche suivante du même type ou de l'autre passe selon la priorité choisie. Les travaux les plus lourds sont séparés afin de ne pas saturer l'UI.
