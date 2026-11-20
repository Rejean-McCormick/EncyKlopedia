# 13 — Registre des sources et contradictions documentaires

## Périmètre vérifié pour cet overlay

**Source primaire locale analysée :** `znapshot_EncyKlopedia_11172030.zip` (5 335 entrées d'archive), `AGENTS.md`, `README.md`, `docs/v32/*`, `encyk_v32/{config,sources,pipeline,sql}.py`, documentation V7. Les rapports de V8 proviennent de la production antérieure dans cette conversation, **sans archive V8 autonome montée dans cette session**.

| Affirmation | Source / preuve | Degré |
|---|---|---|
| 88 branches UNESCO attendues | Dossiers `ecosystem/UNESCO_Kristals/branches/` et documentation V32/V7 | [SNAPSHOT] |
| Noyau SQLite schéma `encyk.local-manager.v32/2` | `encyk_v32/sql.py:SCHEMA` | [CODE VÉRIFIÉ] |
| Candidat unique par `(branch_id,concept_id,page_id)` | DDL `candidates` dans `sql.py` | [CODE VÉRIFIÉ] |
| Sélection ZIP → `selection_decisions.csv` | `pipeline.py:selection_prompt`, `_selection_reply` | [CODE VÉRIFIÉ] |
| Enrichissement ZIP → `kristal_delta.json` | `pipeline.py:enrichment_prompt`, `_enrichment_reply` | [CODE VÉRIFIÉ] |
| Couverture par page requise et citations exactes | `pipeline.py` et `_validate_fact` | [CODE VÉRIFIÉ] |
| Les sources indexées Skope sont lues comme arêtes et non statements originaux | `sources.py`, docs Skope/V7 | [CODE VÉRIFIÉ + DOCUMENTÉ] |
| V8 possède une station autonome à 10 postes et mode campagne | Livraison antérieure dans la conversation | [V8 À REQUALIFIER SUR ZIP] |
| Base V8 réellement installée et index D: prêts | Non accessibles depuis ce snapshot | [INCONNU] |
| 10 606 propositions Météorologie historiques | Journaux utilisateur antérieurs, puis abandon autorisé | [JOURNAL HISTORIQUE] |
| Extraction Wikidata originale intégrée à V8 | Pas démontrée | [CIBLE / NON VÉRIFIÉ] |
| Admission canonique automatique via `ENR` | Prohibée par contrats | [INTERDITE] |

## Contradictions réparées ou contextualisées

| Document hérité | Ancien message | Remédiation de cet overlay |
|---|---|---|
| `AGENTS.md` | Entrée V32.2 uniquement | Bandeau priorisant la nouvelle référence documentaire, sans supprimer les consignes de V32.2 |
| `README.md` | Présente le noyau V32.2 comme point d'entrée unique | Bandeau expliquant la coexistence dépôt V32 et distribution V8 séparée |
| `docs/v32/AGENTS.md` | Référence V32.1 / « 87 branches restantes » | Lien prioritaire vers le guide 88 branches/V8, document V32 conservé comme historique |
| `docs/v32/README.md` | « futur manager » V32 documentaire | Note sur code V32 existant, V7 et livraison autonome V8 distincte |
| `docs/v32/docs/00_INDEX.md` | Ne référence pas le dossier V7/V8 en tête | Table de navigation vers la référence IA et inventaire V7 |
| `00_DEMARRAGE_IA/01_BREVE_LECTURE.md` | « 87 branches restantes » | Note d'orientation 88 branches et historique de l'ancien pilote |
| `10_SYSTEME_MASSIF_20261117/11_CONTRATS_PACKS_ET_ETATS.md` | Appelle le retour `enrichment_delta.json` | **Corrigé vers `kristal_delta.json`**, nom effectivement attendu par le moteur |

## Risque de confusion majeur

Le snapshot permet une **correction fiable des documents**, mais ne permet pas de vérifier le comportement réel de la V8 installée, son code autonome, ses endpoints ou les caractéristiques du Windows vivant. Le bon comportement consiste à laisser une preuve **V8 À REQUALIFIER**, pas à écrire un document trompeur.

## Règle d'évolution documentaire

Chaque nouvelle version doit conserver : chemin du ZIP/source, date du snapshot, fonction vérifiée, commandes testées, résultats de test, limites observées et références croisées. Lorsqu'un fait documentaire devient caduc, conserver un pointeur historique et actualiser le point d'entrée ; ne pas effacer l'information de provenance.
