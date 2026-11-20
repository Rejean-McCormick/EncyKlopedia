# 05 — Documentation technique, ports, tables, algorithmes, frontières

## A. Dépôt V32 et séparation des dépendances

Le code actif V32.2 est installé sur `C:\mycode\EncyKlopedia\EncyKlopedia`. La station V6 est un **adaptateur externe**; son runtime `station_v32_adaptateur.py` utilise le **même** `encyk_v32.sqlite` sur D:. La configuration charge les chemins depuis `Settings.load()` puis surcharge explicitement le répertoire UNESCO des 88 définitions et `work_root` de l'environnement neuf.

V6 patchait seulement `encyk_v32/sources.py` et `encyk_v32/pipeline.py`, en sauvegardant leurs originaux, et ajoutait à chaud des fonctions de V27/V28. **Vérifier la signature du code installé avant de prendre une archive V32.2 comme état live.**

## B. Ports de données existants

| Port concret | Entrée | Sortie | I/O | Observations |
|---|---|---|---|---|
| `import_unesco(db,root)` | 88 dossiers UNESCO | Branches/concepts/mappings | écrit registre **V32 uniquement** | Aucune décision V31 importée |
| `WikipediaIndex.by_qid()` | `wiki_qid`, `wiki_pages` | pages ns=0 hors redirects | source RO | QID peut avoir zéro ou plusieurs pages; routage, pas admission |
| `WikidataGraph.page(qid,pid,direction,cursor,limit)` | `entity_edge` agrégée | voisins + compte/rank | source RO | Correction de propriété P31 en `31`, pas +1e9 |
| `discover()` | mappings, graphe, Wikipedia | candidats + routes + curseurs | work write, sources RO | Résultats **provisoires**, priorité numérique |
| `discover_fallback()` | alias concept/indices titre | candidats par préfixe | sources RO | V6 rétablit recherche même si concept possède QID |
| V6 `discover_v28_wikilinks()` | articles déjà SELECT, XML/index | liens internes candidates | sources RO | au plus 6 graines×100 liens/itération; table curseur V6 |
| V6 `discover_v3111_ontology()` | broader/related + SELECT | nouvelles paires concept/articles | lecture UNESCO locale | 400 routes max/appel, pas d'auto SELECT |
| `make_selection()` | PENDING | `SEL_*.zip`, jobs | work write | extraits Wikitext disponibles selon index |
| `make_enrichment()` | SELECTED + XML révision | `ENR_*.zip`, job + texte complet | work write | réemploi seulement quand source/profil/association couverts |
| `import_for_job()` | ZIP de retour + pack source | propositions, erreurs, reçus | work write | sait gérer PARTIAL, supersedes sous correction explicite |
| `scan_islands()` | états Kristal | vue de lecture fédérée | lecture états | pas d'admission |

## C. Modèle d'identité : éviter les faux raccourcis

- `branch_id = unesco.mt2.45` : **axe éditorial de travail**, pas Kristal.
- `concept_id = concept...` : **concept UNESCO**, peut être partagé par branches selon les données.
- `qid = Q...` : identifiant sujet externe Wikidata, pas une preuve ni un îlot Kristal.
- `page_id` : page Wikipédia anglaise; `revision_id`, `text_sha256` : identité du texte exact de référence.
- `candidate_id = SHA256(branch,concept,page_id)` tronqué (V32) : **association de travail**; des couples différents peuvent viser la même page.
- `subject_key = wd:Q...` ou `enwiki:<page_id>` : référent externe de la proposition; pas KQ/KP/KA/KS.
- `proposal_id` : clé de déduplication exacte; ne dit pas que les paraphrases sont sémantiquement différentes.
- `island_key` : identité indépendante de l'îlot canonique, choisie/qualifiée par ses autorités.

**Invariants** : un seul article/révision peut être cité par plusieurs propositions et concepts; les concepts ne transforment pas le QID en Kristal. Les mêmes faits peuvent avoir plusieurs occurrences documentaires indépendantes.

## D. Transactions et garanties existantes

- `open_work()` sur V32/2, SQLite WAL, `PRAGMA synchronous=FULL`, verrous sérialisés, migrations V32.1→V32.2 explicitement sauvegardées dans le moteur.
- `read_source()` ouvre les sources SQLite via `mode=ro` + `PRAGMA query_only=ON`.
- Un pack ZIP reçoit un SHA-256 et une réservation `jobs/job_items/active_items/lanes` enregistrée. Ne jamais recréer automatiquement un job `READY`.
- Les retours sont archivés par SHA-256 sous `returns/` ; reçus idempotents par `(file_sha256,job_id)`; `import_errors` conservent chaque ordinal refusé.
- L'intégrité du ZIP et la présence de citation sont vérifiées, mais **non** la vérité sémantique ou l'autorité du fait. Voir document 06.
- **Aucun atomic commit global** entre système de fichiers, cache et SQLite en cas de coupure électrique; `recover()` sert à diagnostiquer. Un autoscheduler futur devra réutiliser ces garanties plutôt que les contredire.

## E. DDL et sémantique de provenance

`proposals` a : `proposal_id`, `subject_key`, `page_id`, `revision_id`, `statement`, `predicate`, `object_json`, `source_quote`, `source_locator`, `status`, `source_job`, `created_utc`, `context_json`, `payload_json`, `supersedes`.  
`proposal_citations` rattache `(proposal_id,page_id,revision_id,quote,locator)`; `proposal_occurrences` conserve la présence de propositions à chaque retour.  
`source_results` suit chaque `(job_id,page_id)` avec hash de texte, profil, statut, couverture, concepts, sujets.  
`import_errors` contient `(job_id,return_sha256,ordinal,error,payload_json)` : **le retour rejeté n'est pas perdu**, mais la réparation automatique n'existe pas encore.

## F. Quelles lectures sont coûteuses ?

1. **Graphes Wikidata** : requêtes indexées `WHERE subject_id=? AND property_id=?` ou `target_id=?` et keyset; jamais ORDER BY mondial des 121M entités ni dump scan.
2. **Noms Wikidata** : `idx_name_norm` pour égalité/préfixe borné, validé dans Skope; ne pas énumérer tout le graphe pour un terme.
3. **Wikipédia** : `wiki_pages.title` indexé et `page_from_index` pour XML par offset; ne pas scanner 110 Go par article.
4. **Source originale Wikidata** : extraction `full_source_entity_json` seulement **après prévol** dump+index fast+identité de source; ne pas croire que le compact suffit.
5. **Enrichissements** : coût essentiel = quantité de texte fourni à ChatGPT et contrôle des citations, non nombre brut d'articles.

## G. Manques matériels de V6

- Pas d'ordonnanceur persistant de **fenêtre de campagne** avec politiques de saturation et quotas interconcepts adaptatifs.
- Pas de **mémoire de sections par révision interbranches** distincte des `source_results` (qui sont une base réutilisable mais partielle).
- Les textes sources longs restent dans un ZIP monolithique; pas de découpage intra-article physique, même si le dossier de lecture fournit inventaire des sections.
- Pas de queue de **réparation** `import_errors` ni validation sémantique nuancée; aucun rejet ne doit être « corrigé » sans source.
- Pas de port qualifié Wikidata-full→propositions EncyK pour les 88 branches.
- Catégories/sous-catégories historiques V28/V31 non complètement rebranchées.
- Nul accès canonique via Kit : `admit_proposals()` échoue intentionnellement.

## H. Compatibilité et trajectoire de migration

**Préférer une mise à jour additive**, après test sur copie légère du V32, plutôt qu'une refonte du schéma ou un nouveau serveur concurrent. Si une table `campaign_windows` devient nécessaire, la documenter, sauvegarder la base via SQLite Backup API, tester son injection; ne jamais copier les gros index D:.

**Exemple d'extension cible NON LIVRÉE** : `campaign_windows(window_id,branch,source_epoch,policy_json,opened_utc,closed_utc,status,receipt_sha256)` ; `window_candidates(window_id,candidate_id,source_revision,snapshot_sha256)`; `work_capabilities` ou table d'actions. Les tables existantes de candidates/jobs/proposals restent canoniques pour le **registre privé**.
