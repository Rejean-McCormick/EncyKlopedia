# Jobs persistants, reprise, quotas et concurrence

## Modèle d'état [CIBLE]

Un job désigne une *mission immuable envoyée à une conversation*, liée à un ensemble exact de candidats (passe 1) ou de pages/révisions/sujets (passe 2). Les décisions et claims peuvent être importés progressivement, mais on ne régénère pas en silence le contenu d'un job ouvert.

```text
queued -> preparing -> ready -> sent -> importing -> done
                   |                 |          |
                   v                 v          v
                 failed            retry      partial -> repair -> done
```

`paused` et `cancelled` sont des choix explicites. Le champ `next_action` est calculé à partir de l'état et des fichiers réellement présents. Les lanes 1..10 sont une **vue d'attribution**, non le registre primaire des jobs.

## Tables logiques proposées

| Table | Champs importants | Pourquoi |
|---|---|---|
| `jobs` | `job_id, kind, branch_ids, state, source_cutoff, pack_path, created_at` | Autorité du cycle de vie |
| `job_items` | `job_id, item_id, logical_key, state, result_id, error` | Reprise fine d'une réponse incomplète |
| `lanes` | `lane_id, job_id, assigned_at` | 10 conversations affichées |
| `imports` | `import_id, job_id, digest_optional, imported_at, summary` | Empêcher les doublons de dépôt |
| `work_cursors` | `route_key, scan_kind, resume_key, exhausted, updated_at` | Budget et reprise sans perte |
| `events` | `run_id, job_id, event_type, at, small_payload` | Affichage d'un journal utile, pas event sourcing géant |

Les tables ci-dessus sont une **spécification de domaine**, pas le schéma en production. Préférer une SQLite de contrôle locale plutôt qu'un ensemble de fichiers JSON servant implicitement de bases de jobs.

## Transactions et reprise en cas de panne

1. Préparer le pack dans un emplacement temporaire puis publier le ZIP final; enregistrer l'état `ready` *après* écriture réussie.
2. Lors d'un import, lire le ZIP, associer un job existant, parser et valider les champs essentiels avant d'écrire les faits.
3. Upsert des éléments dans une transaction courte; un item déjà importé devient `unchanged`, non un doublon.
4. Un crash après 43/80 items ne doit pas effacer les 43; reprendre seulement les 37 manquants. Si la base choisit une transaction globale, ne pas annoncer de succès partiel avant commit.
5. Ne jamais modifier une preuve ou une révision attachée à un job déjà envoyé; de nouvelles preuves partent dans un **nouveau job**.

## Pas de dépendance totale entre les deux passes

Des branches peuvent rester en sélection pendant que d'autres ont des pages prêtes à enrichir. Le scheduler pèse les stocks **par travail utile et par coûts**, pas par simple tour de rôle de branches. Un article accepté dans trois concepts alimente un seul job d'enrichissement par révision, avec liens multiples aux concepts.

## Gestion de la concurrence locale

- Un seul propriétaire effectif des écritures sur la SQLite de contrôle; travailleurs avec connexions séparées et transactions courtes.
- Budgets de lecture indépendants : index Wikipédia SQL, index Wikidata compact, résolution XML, préchargement ZIP.
- Interdire **deux lancements simultanés du même run** par clé logique, mais autoriser préparation d'une autre branche si les ressources suivent.
- Les analyses et exports read-only n'arrêtent pas la production; ils peuvent porter une mention « lecture multi-sources non atomique ».
- Les paquets d'un même `job_id` ne doivent pas être remaniés quand une autre conversation rend un retour.

## Quotas et priorités

Le système choisit un mélange de passe 1, passe 2, réparations, cas différés et diversités de branches. Il affiche la demande réelle. Conserver les **4 000 propositions UNESCO** et **120 articles/400k mots/60MiB Kristal** comme *précédents historiques*, à mesurer selon la densité réelle du contenu. Un plafond atteint déclenche un curseur de reprise, jamais une exclusion permanente. L'approche « 10/10 ou bug » est fausse : l'inoccupation peut être une absence de stock; la réserve PENDING+DEFERRED et les jobs prêts doivent cependant être comptés avant d'affirmer cela.

## En cas de source indisponible

| Incident | Réaction souhaitée |
|---|---|
| Skope absent | Suspendre nouvelles traversées Wikidata, pas imports et lecture |
| SQLite Wikipédia verrouillée | Retry limité, informer, libérer lane non préparée |
| XML article absent | Signaler `source_missing` sur l'item, le différer, continuer les autres |
| ZIP corrompu | Rejeter l'import de ce fichier, ne pas nettoyer les anciens jobs |
| Retour incomplet | Recevoir les items valides et proposer réparation ciblée |
| Une branche en erreur | Ne pas bloquer les 86 autres |
