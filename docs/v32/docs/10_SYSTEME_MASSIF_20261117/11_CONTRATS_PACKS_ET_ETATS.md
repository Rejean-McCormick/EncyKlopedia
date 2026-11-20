# 11 — Contrats des tâches, ZIP, retours, source et canon

## A. Pack de sélection `SEL_######.zip`

**Contenu V32.2** : `selection_pack.json`, `candidates.jsonl`, `INSTRUCTIONS_CHATGPT.md`. Pour chaque ligne : `candidate_id`, branche, concept, sujet, `page_id`, titre, `revision_id`, routes de découverte, `context_completeness`, extrait source quand disponible. Le `manifest` compte les candidats et rappelle `canonical_admissions=0`.

**Contrat de réponse** : CSV `selection_decisions.csv` encodé UTF-8, au moins les colonnes `candidate_id`, `decision`, `justification` telles que définies dans les instructions de la version du pack; chaque décision dans `{SELECT, REJECT, HOLD}`. Les identifiants doivent venir **exactement** du pack. La justification française doit expliquer la pertinence conceptuelle, pas seulement « Wikidata P31 ».

**Cas sans extrait** : ne pas présenter l'absence d'extrait comme une preuve positive. HOLD doit rester autorisé lorsque le titre/gaphe est ambigu.

## B. Pack d'enrichissement `ENR_######.zip`

**Contenu V32.2** (voir `pipeline.make_enrichment`) : `enrichment_pack.json`, `articles.jsonl`, `articles/enwiki-<page_id>.wikitext.txt`, `INSTRUCTIONS_CHATGPT.md` et, en V6, `DOSSIER_LECTURE_V316.jsonl`. Les textes restent complets et hachés; la source est l'original révisé, pas le guide.

**Réponse attendue** : `kristal_delta.json` avec `format` reconnu `encyk.enrichment-delta.v32/1` ou `/2`, `job_id`, `facts`, `source_coverage` et interdiction canonique explicite. Le moteur exige pour chaque fait l'`page_id`, le `revision_id`, le `subject_key` autorisés, un énoncé, un `predicate`, un `object` typé, `source_quote` exacte et `source_locator`, plus `concept_ids` valides. Voir `encyk_v32/pipeline.py::_validate_fact` pour le schéma exact de la version installée.

**Statuts par article** : `processed`, `incomplete`, `blocked`, `no_relevant_claim`; V32 peut également accepter `legacy` pour les anciens retours. `incomplete` ne doit pas être choisi pour cacher des citations invalides; il signifie couverture encore partielle. `source_coverage` doit documenter ce qui reste.

## C. Retours partiels, corrections, erreurs

- Une ligne invalide est enregistrée dans `import_errors` avec ordinal et payload; les valides sont sauvegardées, source article marquée PARTIAL si nécessaire.
- `--correction` existe pour **remplacer une proposition déjà acceptée** via `supersedes`, dans le contexte du job d'origine; ce n'est **pas** le protocole de réparation de toutes les lignes invalides jamais acceptées.
- `receipts` et `return_archives` détectent les soumissions répétées au même job; ne pas recréer `ENR_000021` parce que son import est `PARTIAL`.
- L'inventaire des sections V31.6 est un guide de lecture non probant. Toute assertion doit se rattacher à l'article d'origine, sa révision et une citation précise.

## D. États de stockage EncyK

La base de travail **private** V32 inclut `DRAFT`, `UNASSIGNED`, `SUPERSEDED` pour propositions, et `READY`/`SENT`/`DONE`/`PARTIAL`/`REVIEW_REQUIRED`/`DONE_EMPTY` pour jobs, selon les fonctions de V32. Une proposition `DRAFT` **n'est pas** un fait Kristal. Les statuts de retour ne doivent pas modifier arbitrairement les autorisations canoniques.

## E. Contrat d'extraction future Wikidata originale

Pour une entité QID sélectionnée : demander à un export Skope qualifié le **record source original** avec identité vérifiée, `claims`, qualifiers, references et sitelinks, plutôt que recréer des références depuis `entity_edge`. Conserver digest du dump, date, identifiant de statement, qualifiers, attribution/URL/licence, et espace des sources. Extraire séparément dans EncyK en propositions *WIKIDATA_ORIGINAL*, jamais comme si une citation Wikitext les prouvait. **Non implémenté dans V32.2**.

## F. Contrat différé vers les Kristals

Une proposition doit pouvoir être reliée à une île par un choix du vrai registre d'autorité, avec KQ/KP/KA/KS qualifiés et admission signée/traçable. Aucun passage `wd:Q... → nouvelle île` ne doit être généré automatiquement. Le Kit est l'outil d'admission, pas le moteur ChatGPT. Ces contrats sont **à qualifier**, pas des APIs disponibles dans l'archive V6.
