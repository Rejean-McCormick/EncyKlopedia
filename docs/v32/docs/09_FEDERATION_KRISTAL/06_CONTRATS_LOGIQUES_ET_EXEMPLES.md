# Contrats logiques minimums (non normatifs)

Tous les champs ci-dessous sont des **exemples de contrats EncyK**, pas des schémas officiels du Framework ni du Kit. Avant d'implémenter, rechercher leurs équivalents existants dans les sources.

## Inventaire d'îlot

```json
{"island_ref":"namespace:education", "owner":"kristal-workspace", "kind":"domain", "known_state_ref":"state:...", "capabilities":["read"], "concept_links":["unesco:concept..."], "local_path_hint":"D:/...", "source":"manager-inventory"}
```

Ne pas faire d'un chemin un ID. `capabilities` est la liste observée dans un adaptateur, non une permission universelle d'écrire.

## Proposition EncyK provenant de l'IA

```json
{"proposal_id":"prop:...", "proposal_version":1, "subject_refs":["wd:Q..."], "target_islands_candidates":["namespace:education"], "statement":{"kind":"observation","value":"...","conditions":{"place":"...","time":"..."}}, "source":{"kind":"enwiki","page_id":123,"revision_id":"...","locator":"section/offset","excerpt":"..."}, "extraction_profile":"education-v1", "status":"PROVISIONAL"}
```

Un vrai retour conserve le texte source et ses qualifiers; ce JSON ne fixe **pas** un modèle universel pour toutes les assertions de tous les domaines.

## Décision et reçu

```json
{"decision_id":"decision:...", "proposal_id":"prop:...", "proposal_version":1, "policy":"education-admission-v1", "result":"ELIGIBLE", "expected_state_ref":"state:old", "reason":"conditions satisfaites"}
```

```json
{"receipt_id":"receipt:...", "decision_id":"decision:...", "island_ref":"namespace:education", "expected_state_ref":"state:old", "observed_state_ref":"state:new", "authoring_operation_ref":"kit-operation:...", "status":"RECONCILED"}
```

Une décision favorable n'est **pas** une preuve d'écriture. Le reçu doit correspondre à un état réellement observé. Les valeurs `state:...` et `kit-operation:...` sont illustratives, non des conventions confirmées.

## Job de production

```json
{"job_id":"job:...", "phase":"SELECT|ENRICH|ADMIT|READ", "scope_refs":["unesco:branch..."], "input_snapshot_ref":"...", "idempotency_key":"...", "budget_reserved":0, "cost_observed":null, "status":"READY|SENT|DONE|UNKNOWN", "artifact_path":"..."}
```

La réservation de budget et le coût constaté doivent être séparés. Un appel IA au résultat inconnu peut avoir consommé des ressources; ne pas comptabiliser silencieusement zéro.

## Flux des états

`candidate -> SELECT/REJECT/HOLD -> proposal(PROVISIONAL) -> policy decision -> authoring operation -> reconciled receipt -> island state -> projected view`.

`REJECT` en passe 1 concerne la **pertinence du couple**, pas un jugement universel sur le sujet. Une proposition non admise reste consultable dans le mode exploratoire. Les publications externes constituent une autre action.
