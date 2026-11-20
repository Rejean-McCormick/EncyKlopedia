# 08 — Modèle technique V32/2 : identités, tables, source, transactions

**Source de vérification :** `encyk_v32/sql.py`, `sources.py`, `pipeline.py` du snapshot `znapshot_EncyKlopedia_11172030.zip`. Ce schéma est celui du moteur V32.2 visible, **pas une migration V8 postulée**.

## Modèle d'objets

```text
branches (UNESCO) ─── branch_concepts ─── concepts ─── mappings (P3916 QID)
     │                                         │
     └─ candidates (branch,concept,page_id) ──┘
             │         │
      candidate_routes │
             │         ▼
          decisions   article_sources(page_id,revision_id,sha)
             │         │
             └─ job_items / jobs / lanes (SEL,ENR) ── receipts, import_errors
                           │
                           ▼
                        proposals ─ proposal_concepts
                           │
                           ├─ proposal_citations
                           └─ proposal_occurrences

kristal_islands / island_branch_links / island_locations : VUE FÉDÉRÉE, pas la base privée des propositions
```

## Identités qui ne se superposent pas

| Clé | Dépendance | Ce qu'elle garantit |
|---|---|---|
| `branch_id` | UNESCO, ex. `unesco.mt2.45` | Périmètre éditorial |
| `concept_id` | Thésaurus | Sens thématique; peut se retrouver dans plusieurs branches |
| `qid` | Wikidata externe | Référent externe, non identité canonique |
| `page_id` | Wikipédia anglais | Une page indépendamment de ses multiples rattachements |
| `revision_id` | Page et index de source | Version du texte dans le pack |
| `text_sha256` | Octets du Wikitext | Égalité de source au moment d'un traitement |
| `candidate_id` | Branche + concept + page | Décision sur une correspondance, pas sur un document unique |
| `subject_key` | QID ou identifiant wiki | Sujet d'une proposition privée, non îlot Kristal |
| `proposal_id` | Clé de dédup du moteur | Un fait distinct selon les règles **exactes** d'identité V32 |
| `island_key` | Framework canonique | Îlot de connaissance admise, géré par autorités propres |

## Tables principales

| Famille | Tables dans V32/2 | Contrôle |
|---|---|---|
| Référence | `branches`, `concepts`, `branch_concepts`, `concept_aliases`, `mappings`, `subjects` | Distinction mapping candidat et relation validée |
| Découverte | `candidates`, `candidate_routes`, `graph_cursors`, `fallback_cursors` | Cursor reprenable, route conservée |
| Missions | `jobs`, `job_items`, `active_items`, `lanes`, `decisions`, `decision_history` | Réservation exclusive et retour idempotent |
| Sources et couverture | `article_sources`, `source_results`, `candidate_extractions`, `candidate_failures` | Réutilisation dépendante révision/profil/hash |
| Assertions privées | `proposals`, `proposal_concepts`, `proposal_citations`, `proposal_occurrences`, `proposal_replacements` | Provenance, reprises, corrections explicites |
| Import | `receipts`, `return_archives`, `import_errors`, `events` | Retour archivé, refus par ordinal |
| Fédération | `kristal_islands`, `island_branch_links`, `island_locations` | Lecture des sources canoniques, sans pouvoir d'écriture |

**V8 peut ajouter un répertoire de reçus de campagnes** ; ne pas inventer la table `campaign_windows` comme si elle existait dans le schéma V32/2 du snapshot.

## Invariants de robustesse

- Les connexions Skope/index Wikipédia sont strictement **read-only** ; la base de travail est le seul registre que le manager modifie.
- Ne pas copier/modifier les index ou dumps pour faciliter un seul retour ChatGPT.
- Une mission `READY` ou `SENT` conserve son ZIP de source et son hash; l'import le compare et empêche les substitutions.
- `return_archives` et `receipts` portent la preuve d'un retour importé; `import_errors` enregistre les faits non acceptés par ordinal.
- Une proposition avec citation et concept n'est **pas** un enregistrement canonique; `admit_proposals()` refuse l'admission tant que le Kit n'est pas qualifié.
- Les sauvegardes d'une base SQLite active doivent utiliser une procédure cohérente (Backup API, WAL correctement géré), **jamais supprimer un `-wal` à la main**.
- La nature d'une correction `supersedes` doit être documentée; les lignes jamais acceptées ne sont pas des propositions admises à superséder.

## Points sensibles à vérifier pour une V8 installée

1. Provenance exacte du `code_v8/encyk_v32` et présence du correctif `entity_edge.property_id` Skope.
2. Accord entre schéma `/2`, tables complémentaires de la station et les wrappers V8 de campagnes.
3. Identité des sources `text_sha256` et version du XML de référence.
4. Concurrence: dix lanes globales, un seul worker d'écriture, arrêt/pause et reprise après crash.
5. Absence de migration implicite depuis la branche Météorologie abandonnée.
6. `canonical_admissions=0` pendant les deux passes et l'import.
