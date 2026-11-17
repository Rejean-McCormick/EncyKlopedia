# Guide développeur du nouveau noyau

## Données détenues par V32

`work_root/encyk_v32.sqlite` gère les tables `branches`, `concepts`, `branch_concepts`, `mappings`, `subjects`, `candidates`, `candidate_routes`, `graph_cursors`, `jobs`, `job_items`, `lanes`, `decisions`, `proposals`, `proposal_concepts`, `proposal_citations`, `kristal_islands`, `island_branch_links` et `receipts`.

Les bases v25/v27/v28/v30 restent **séparées**; aucune migration ni transformation de leurs IDs n'est lancée automatiquement.

### Phases

- **0 → découverte** : `DIRECT_P3916`, `WIKIDATA_GRAPH` avec propriété et direction typées. Le parcours source est read-only et les curseurs reprennent là où une vague s'arrête. L'identité d'un candidat est `(branche, concept, page_id)`, plusieurs routes par candidat.
- **0 bis → rappel sans QID** : préfixes de titres indexés pour les concepts sans mapping P3916 unique, avec curseurs et budget par vague; aucun scan global ni exclusion définitive.
- **1 → sélection** : `PENDING → QUEUED_SELECTION → SELECTED|REJECTED|HOLD`. `PARTIAL` renvoie uniquement les candidats sans réponse vers PENDING. Pas de décisions fictives.
- **2 → enrichissement** : regroupement par page; `SELECTED → QUEUED_ENRICHMENT → ENRICHED`. Extraction de wikitext intégral à révision vérifiée par l'ancien lecteur v27. Les propositions sont dédupliquées par sujet, article, révision, prédicat et objet. Source quote vérifiée dans le texte du ZIP.
- **Admettre** : non activé. `federation.admit_proposals()` échoue explicitement; `export_proposals()` produit un JSONL de transit privé et non un état Kristal.

### Critères d'architecture

- Un même sujet Wikidata peut être lié à plusieurs concepts UNESCO; un îlot Kristal n'est pas créé pour chaque QID.
- Les relations graphes ne sont jamais des preuves d'APPROVE. Pas de publication canonique ni de décision automatique d'admission.
- Sources lourdes : requêtes SQLite ciblées, jamais scan global du XML lors d'une nouvelle branche. Le lecteur direct v21 lit les pages choisies.
- Les fichiers de retour ZIP sont explicitement liés à leur tâche et les citations à la révision d'article. Pas de triple validation indépendante, pas de manifest global obligatoire.
- Le nombre de postes est une **capacité maximale**, pas un objectif d'occupation artificiel.

## Schéma de retour (exemples et non sources factuelles)

Sélection : ZIP avec `selection_decisions.csv` (3 colonnes `candidate_id,decision,justification`) et ID du poste `SEL_...` précisé à l'interface.

Enrichissement : ZIP avec `kristal_delta.json`, `format=encyk.enrichment-delta.v32/1`, `job_id`, `facts`, `source_coverage` (article par article), `canonical_admissions=0`, `publication_authorized=false`. Chaque `facts[]` relie page_id, revision_id, subject_key, predicate, object, statement, source_quote, source_locator et concept_ids. La ligne citée doit être présente littéralement dans le wikitext fourni.

## Restauration et suivi

Les sources externes n'étant pas modifiées, sauvegarder le répertoire `work_root` suffit pour l'état V32 (SQLite + packs). Le système utilise les transactions SQLite, mais les retours ZIP sont des fichiers sur disque : un audit des orphelins pourra faciliter la récupération si la machine s'arrête entre création de pack et affectation de poste.
