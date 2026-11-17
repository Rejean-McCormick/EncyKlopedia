# Contrats de fichiers : héritage réel et cible V32

## Contrat actuel UNESCO v28 [OBSERVÉ CODE]

Entrée ZIP : `REVUE_<id>.csv` avec candidate_id, branch_id, concept_id, page_id, title, scores et exemples; l'export peut inclure `CONTEXTES_DOCUMENTAIRES_V28.jsonl` sans modifier le CSV de preuve. Retour ChatGPT : **un CSV de 3 colonnes** `candidate_id,decision,justification` (APPROVE/REJECT/HOLD). La station recopie ses propres colonnes source pour appliquer, ne fait pas confiance à des colonnes modifiées par l'IA.

### Contrat actuel Kristal v27 [OBSERVÉ CODE]

Format source `encyklopedia.wikipedia-fulltext-pack.v27/1`, delta `encyklopedia.kristal-ai-delta.v27/1`. Le JSON de retour contient `format`, `pack_id`, `pack_sha256`, `producer`, `coverage_note`, `claims`, `canonical_admissions=0`, `publication_authorized=false`. Chaque claim peut contenir `source_page_id`, `source_revision_id`, `subject_ref`, `predicate`, `object: {type,value}`, `statement_en`, `unesco_concepts`, `source_locator`, `source_quote`, `confidence`.

Le validateur v31.8 impose que `source_quote` soit effectivement présente dans le wikitext original et qu'un bilan de couverture existe pour **chaque** article. Le delta v27 déduplique par claim, conserve plusieurs citations et garde les anciennes versions de texte.

## V32 : séparer formellement deux types de missions

### `encyk.selection-pack.v32/1` [CIBLE]

Fichiers : `selection_pack.json`, `candidates.jsonl`, `instructions.md`, `context/*.jsonl` facultatifs. Chaque candidat contient `candidate_id`, `branch_id`, `concept_id`, `concept_labels`, `scope_notes`, `subject_qid?`, `wiki_page_id?`, `page_title?`, `route_ids`, `signals`, `context_excerpt?`, `source_version`.

Retour `selection_decisions.jsonl` ou CSV compact : `candidate_id`, `decision` (`SELECT|REJECT|HOLD`), `justification`, `notes` optionnelles. Le manager ne permet pas qu'un modèle remplace la source, le QID ou le chemin de découverte.

### `encyk.enrichment-pack.v32/1` [CIBLE]

Fichiers : `enrichment_pack.json`, `subjects.jsonl`, `wikitext/<page_id>.*` (texte complet pour les sélectionnés), `wikidata/<qid>.json` si disponible, `reading_guides.jsonl`. Un **sujet** peut avoir plusieurs textes/révisions et plusieurs scopes, mais la même source est présente une seule fois par pack.

Retour `kristal_delta.json` ou JSONL : `job_id`, `subjects`, `facts`, `source_coverage`. Chaque fait renseigne `kristal_id/subject_key`, `predicate`, valeur, phrase, `source_kind`, `source_id`, révision/déclaration, citation littérale ou référence explicite, scope si lié à un concept particulier, confiance. Les contradictions gardent une relation entre claims plutôt qu'un « verdict vrai/faux » arbitraire.

**Important :** ces schémas sont des propositions à implémenter, pas des formats acceptés aujourd'hui par v27/v30. Adapter les anciens validateurs au nouveau format; éviter d'obliger chaque package dérivé à embarquer un manifeste SHA global.

## Exemple de décision V32 (illustratif)

```json
{"candidate_id":"cand-demo","decision":"SELECT",
 "justification":"Le passage sur l'organisation et les fonctions de l'établissement traite directement du concept examiné."}
```

## Exemple de claim V32 (illustratif)

```json
{"kristal_id":"wd:Q123","predicate":"founded_in_year","value":1910,
 "statement_en":"The institution was founded in 1910.",
 "source":{"wiki":"enwiki","page_id":123,"revision_id":"456",
           "section":"History","quote":"The institution was founded in 1910."},
 "private_status":"DRAFT"}
```

**Aucune des valeurs de démonstration n'est une connaissance attestée.**

## Robustesse sans lourdeur

Le retour inconnu, ZIP non fiable ou tâche non correspondante doit être refusé, car ce sont des pertes de travail concrètes. En revanche, le manager n'exige pas d'empreinte SHA de chacun des 30 fichiers de contexte ni un triple audit textuel de chaque claim. Il préserve l'identité de la source et le lien direct citation→révision, qui sont les vérifications utiles.
