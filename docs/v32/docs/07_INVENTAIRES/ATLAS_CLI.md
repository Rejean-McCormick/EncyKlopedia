# Atlas des entrées CLI détectées statiquement

Cet index regroupe **117 modules Python** contenant des options CLI repérées dans les snapshots. Il ne remplace pas les README ni ne prouve que toutes les options peuvent être appelées en production. Les nombreux lanceurs `.cmd/.ps1` et interfaces HTML/JS sont décrits dans la carte source; un dossier ne devient pas une commande officielle parce qu’il a `argparse`.

## EncyKlopedia

| Module | Options observées (aperçu) |
|---|---|
| `OVERLAY_CONTEXTE_UNESCO_V28/tools/unesco_pilot/poste_chatgpt_v30.py` | `--repo`, `--work`, `--v27-work`, `--v28-work`, `--catalogue`, `--port`, `--no-browser` |
| `REARMER_HOLD_V30.py` | `--work`, `--preview` |
| `_SAUVEGARDES_CODE_CONTEXTE_V28/20261112_163151/tools/unesco_pilot/poste_chatgpt_v30.py` | `--repo`, `--work`, `--v27-work`, `--v28-work`, `--catalogue`, `--port`, `--no-browser` |
| `_SAUVEGARDES_PROFONDEUR_KRISTAL/20261114T171028552327Z/tools/unesco_pilot/poste_chatgpt_v30.py` | `--repo`, `--work`, `--v27-work`, `--v28-work`, `--catalogue`, `--port`, `--no-browser` |
| `_SAUVEGARDES_PROFONDEUR_KRISTAL/20261114T171028552327Z/tools/unesco_pilot/production_kristals_v27.py` | `--work`, `--catalogue`, `--xml`, `--index`, `--max-packs`, `--max-articles`, `--target-words`, `--target-bytes`, `--pack`, `--delta` |
| `outils_v30/planifier_packs_unesco_v28.py` | `--csv`, `--packs`, `--contextes`, `--sortie`, `--configuration` |
| `outils_v30/priorisation_unesco_v28.py` | `--packs`, `--csv`, `--sortie`, `--top` |
| `outils_v30/reperer_integration_v30.py` | `--repo`, `--sortie` |
| `outils_v30/stats_globales_v30.py` | `--sortie`, `--station`, `--decouverte`, `--catalogue`, `--kristal`, `--repertoires-retours`, `--secondes-par-requete` |
| `tools/dictionary-harvester/dik_qualification.py` | `--data-root`, `--languages`, `--min-free-gb`, `--batch-size`, `--max-languages`, `--candidate-id`, `--source-id`, `--reviewer`, `--disposition`, `--reason`, `--reference-url` |
| `tools/dictionary-harvester/dik_reconciliation.py` | `--data-root`, `--languages`, `--min-free-gb` |
| `tools/dictionary-harvester/lexical_indexer.py` | `--data-root`, `--only`, `--refresh-changed`, `--max-lines-per-source`, `--min-free-gb`, `--query`, `--language`, `--match`, `--limit` |
| `tools/dictionary-harvester/quality_audit.py` | `--data-root`, `--languages`, `--min-free-gb` |
| `tools/dictionary-harvester/semantic_enrichment.py` | `--data-root`, `--languages`, `--batch-lines`, `--min-free-gb`, `--max-scan-lines` |
| `tools/unesco_pilot/audit_integrite_encyklopedia.py` | `--data`, `--repo`, `--output` |
| `tools/unesco_pilot/automated_local_pilot.py` | `--root`, `--scope-zip`, `--db`, `--xml`, `--work`, `--runtime-root`, `--metadata-only`, `--non-interactive` |
| `tools/unesco_pilot/canonical_bridge_v13.py` | `--work`, `--repo-root`, `--workspace`, `--output`, `--check-only` |
| `tools/unesco_pilot/catalogue_global_v25.py` | `--source-db`, `--catalogue-db`, `--output-dir`, `--branch`, `--max-batches`, `--extend-branch-id`, `--new-max-members`, `--new-max-tasks`, `--batch-size`, `--sample-limit`, `--export-branch-id`, `--after-page-id` … (+1) |
| `tools/unesco_pilot/cumulative_preflight.py` | `--root`, `--manifest` |
| `tools/unesco_pilot/decouverte_relationnelle_v311.py` | `--source-db`, `--catalogue-db`, `--branch`, `--work`, `--max-seeds`, `--max-links-per-seed` |
| `tools/unesco_pilot/decouvrir_articles_relies_v28.py` | `--source-db`, `--catalogue-db`, `--index`, `--xml`, `--branch`, `--work`, `--catalogue-output`, `--max-seeds`, `--max-links-per-seed`, `--max-seed-categories`, `--max-categories-per-concept`, `--max-category-size` … (+6) |
| `tools/unesco_pilot/diagnostiquer_import_v28_sur_copie.py` | `--task-id` |
| `tools/unesco_pilot/editorial_advance_v14.py` | `--work`, `--repo-root`, `--check-only` |
| `tools/unesco_pilot/final_product_pipeline_v17.py` | `--work`, `--repo-root`, `--workbench-workspace`, `--output-name`, `--check-only`, `--require-final` |
| `tools/unesco_pilot/generer_branches_unesco_v25.py` | `--source`, `--dest`, `--revision`, `--prefix` |
| `tools/unesco_pilot/integrer_ponts_revus_v26.py` | `--source-db`, `--catalogue-db`, `--output-dir`, `--branch`, `--reviewed-bridges`, `--max-batches`, `--batch-size`, `--sample-limit` |
| `tools/unesco_pilot/inventaire_categories_v26.py` | `--source-db`, `--inventory-db`, `--output-dir`, `--concepts`, `--decisions`, `--queries-file`, `--max-rows`, `--batch-size`, `--max-candidates`, `--max-per-name`, `--broad-per-term` |
| `tools/unesco_pilot/local_wikipedia_bridge.py` | `--scope-zip`, `--db`, `--out` |
| `tools/unesco_pilot/lot2_preflight.py` | `--root`, `--runtime-root` |
| `tools/unesco_pilot/lot4_preflight.py` | `--root` |
| `tools/unesco_pilot/offline_xml_evidence.py` | `--inventory`, `--xml`, `--out`, `--progress-every` |
| `tools/unesco_pilot/ouvrir_exploration_v311.py` | `--station`, `--count`, `--branch` |
| `tools/unesco_pilot/overlay_ia_v22.py` | `--work`, `--batch` |
| `tools/unesco_pilot/overlay_probatoire_v23.py` | `--work-root` |
| `tools/unesco_pilot/piloter_branches_v311.py` | `--source`, `--catalogue`, `--branches`, `--stage`, `--station`, `--max-batches`, `--batch-size`, `--max-seeds` |
| `tools/unesco_pilot/poste_chatgpt_v30.py` | `--repo`, `--work`, `--v27-work`, `--v28-work`, `--catalogue`, `--port`, `--no-browser` |
| `tools/unesco_pilot/preuves_xml_v31.py` | `--xml`, `--stage`, `--cache`, `--text-chars` |
| `tools/unesco_pilot/production_kristals_v27.py` | `--work`, `--catalogue`, `--xml`, `--index`, `--max-packs`, `--max-articles`, `--target-words`, `--target-bytes`, `--pack`, `--delta` |
| `tools/unesco_pilot/qualification_globale_v31.py` | `--source`, `--output`, `--branches`, `--batch-size`, `--max-articles`, `--categories-per-article` |
| `tools/unesco_pilot/recevoir_lots_atlas_v19.py` | `--batch`, `--proposals`, `--ledger` |
| `tools/unesco_pilot/registry_provenance_v16.py` | `--work`, `--repo-root`, `--registry-root`, `--registry-workspace`, `--check-only`, `--output-name` |
| `tools/unesco_pilot/reparer_ecriture_catalogue_v25.py` | `--catalogue`, `--backup-root`, `--no-confirm` |
| `tools/unesco_pilot/repo_preflight.py` | `--root`, `--snapshot-layout` |
| `tools/unesco_pilot/reprendre_import_unesco_v28.py` | `--task-id` |
| `tools/unesco_pilot/review_global_overlay_v12.py` | `--work`, `--check-only` |
| `tools/unesco_pilot/semantic_candidate_stage_v4.py` | `--work`, `--out` |
| `tools/unesco_pilot/semantic_candidate_stage_v6.py` | `--work`, `--check-only` |
| `tools/unesco_pilot/stabiliser_catalogue_import_v28.py` | `--catalogue`, `--backup-root` |
| `tools/unesco_pilot/statistiques_globales_v31.py` | `--sortie`, `--avec-historique-v30` |
| `tools/unesco_pilot/workspace_readiness_v15.py` | `--work`, `--repo-root`, `--existing-workspace`, `--output-name`, `--check-only` |

## Kristal_UNESCO_Factory

| Module | Options observées (aperçu) |
|---|---|
| `tools/unesco_gf_pilot/audit_archive.py` | `--json` |
| `tools/unesco_gf_pilot/pilot.py` | `--kristal`, `--semantik`, `--run`, `--concept`, `--languages`, `--gf`, `--wordbench`, `--orchestrator`, `--pgf-python`, `--existing-pgf`, `--output` |
| `unesco_inventory_corrige.py` | `--ttl`, `--out` |
| `unesco_wikidata_bridge.py` | `--inventory`, `--claims`, `--index`, `--out` |
| `vendor/kit/examples/demo-hosted-v10/tools/kristal.py` | `--slug`, `--title`, `--profile`, `--with-ai`, `--force`, `--id`, `--kind`, `--locator`, `--version-or-date`, `--sha256`, `--authority-scope`, `--trust-class` … (+30) |
| `vendor/kit/examples/demo-open/tools/kristal.py` | `--slug`, `--title`, `--profile`, `--with-ai`, `--force`, `--id`, `--kind`, `--locator`, `--version-or-date`, `--sha256`, `--authority-scope`, `--trust-class` … (+30) |
| `vendor/kit/examples/demo-semantic-v11/tools/kristal.py` | `--slug`, `--title`, `--profile`, `--with-ai`, `--force`, `--compact`, `--require-fresh`, `--arketype-dir`, `--usage`, `--archetype`, `--arketype-version`, `--family` … (+50) |
| `vendor/kit/examples/demo-v9-small/tools/kristal.py` | `--slug`, `--title`, `--profile`, `--with-ai`, `--force`, `--id`, `--kind`, `--locator`, `--version-or-date`, `--sha256`, `--authority-scope`, `--trust-class` … (+30) |
| `vendor/kit/scripts/audit_workspace_migration.py` | `--before`, `--after` |
| `vendor/kit/scripts/qualify_framework_v11.py` | `--project`, `--framework`, `--integration-pack`, `--locales` |
| `vendor/kit/tools/kristal.py` | `--slug`, `--title`, `--profile`, `--with-ai`, `--force`, `--compact`, `--require-fresh`, `--arketype-dir`, `--usage`, `--archetype`, `--arketype-version`, `--family` … (+52) |
| `vendor/spek/scripts/exporter_sources_pour_analyse_ia.py` | `--root`, `--out`, `--include-content` |
| `vendor/spek/scripts/launch_spek.py` | `--mode`, `--ekole-file`, `--port`, `--lang`, `--no-browser`, `--no-server` |
| `vendor/spek/scripts/serve_education_demo.py` | `--site`, `--port`, `--lang`, `--no-browser` |
| `vendor/spek/spek/cli.py` | `--source`, `--realizations`, `--layouts`, `--languages`, `--state-snapshot`, `--out`, `--formats`, `--production`, `--require-production`, `--input`, `--mapping`, `--adapter` … (+20) |
| `vendor/spek/spek/semantik_execution.py` | `--article`, `--mapping`, `--architect`, `--runtime-root`, `--layouts`, `--snapshot` |
| `vendor/spek/spek/semantik_transfer.py` | `--article`, `--mapping`, `--out`, `--layouts`, `--state-snapshot` |
| `vendor/spek/spek/slot_dialogue.py` | `--article`, `--layouts`, `--language`, `--output` |
| `wikidata_reader_worker.py` | `--dump`, `--index`, `--request`, `--out` |

## LevelUpDiag_EncyK

| Module | Options observées (aperçu) |
|---|---|
| `levelupdiag_core/cli.py` | `--target`, `--jobs`, `--fail-fast`, `--level`, `--run-id`, `--output` |

## Skope (external)

| Module | Options observées (aperçu) |
|---|---|
| `encyk/00_system/integrations/skope_bridge.py` | `--job`, `--api`, `--data-root` |
| `encyk/00_system/tools/performance/scripts/benchmark_dump.py` | `--root`, `--dump`, `--entities`, `--parse-every`, `--threads` |
| `encyk/00_system/tools/performance/scripts/build_fast_access.py` | `--root`, `--dump`, `--threads`, `--reverse-properties`, `--initial-qid-capacity`, `--force`, `--allow-sequential-locator`, `--force-reverse-sidecar` |
| `encyk/00_system/tools/performance/scripts/fast_status.py` | `--root` |
| `encyk/00_system/tools/performance/scripts/install_fast_deps.py` | `--root`, `--try-bzip2`, `--dry-run` |
| `encyk/00_system/tools/scope-builder/scripts/01_resolve_roots.py` | `--root`, `--scope`, `--backend`, `--db`, `--dump` |
| `encyk/00_system/tools/scope-builder/scripts/02_discover_scope.py` | `--root`, `--scope`, `--backend`, `--db`, `--dump` |
| `encyk/00_system/tools/scope-builder/scripts/03_estimate.py` | `--root`, `--scope`, `--dump` |
| `encyk/00_system/tools/scope-builder/scripts/03_freeze_scope.py` | `--root`, `--scope` |
| `encyk/00_system/tools/scope-builder/scripts/04_extract_evidence.py` | `--root`, `--scope`, `--dump`, `--compression`, `--cache-vault`, `--threads`, `--no-fast-access`, `--allow-full-scan`, `--max-auto-scan-gib` |
| `encyk/00_system/tools/scope-builder/scripts/05_build_scope_index.py` | `--root`, `--scope`, `--snapshot-id`, `--fresh`, `--batch-entities`, `--threads` |
| `encyk/00_system/tools/scope-builder/scripts/06_prepare_identity_candidates.py` | `--root`, `--scope` |
| `encyk/00_system/tools/scope-builder/scripts/07_prepare_source_handoff.py` | `--root`, `--scope` |
| `encyk/00_system/tools/scope-builder/scripts/08_status.py` | `--root` |
| `encyk/00_system/tools/scope-builder/scripts/09_maintenance.py` | `--root`, `--min-free-gib` |
| `encyk/00_system/tools/scope-builder/scripts/estimate_selected.py` | `--root`, `--scope` |
| `encyk/00_system/tools/scope-builder/scripts/run_scope_pipeline.py` | `--root`, `--scope`, `--through`, `--from-stage`, `--discovery-backend`, `--wait-for-index`, `--poll-seconds`, `--build-query-index`, `--cache-vault`, `--min-free-gib`, `--threads`, `--prepare-fast-access` … (+1) |
| `encyk/00_system/tools/scope-builder/scripts/verify_mediatheque_receipt.py` | `--handoff`, `--receipt` |
| `encyk/00_system/tools/scope-builder/scripts/watch_then_run.py` | `--root`, `--scope`, `--through`, `--discovery-backend`, `--prefer-index`, `--poll-seconds`, `--force`, `--build-query-index`, `--cache-vault`, `--allow-full-scan`, `--threads` |
| `encyk/00_system/tools/wikidata-manager/scripts/auto_pipeline.py` | `--root`, `--languages`, `--python`, `--force-space`, `--dump-format`, `--threads`, `--temp-dir` |
| `encyk/00_system/tools/wikidata-manager/scripts/build_compact_index.py` | `--dump`, `--db`, `--languages`, `--commit-every`, `--state`, `--fresh`, `--skip-sha1`, `--threads`, `--root`, `--temp-dir`, `--finalize-only`, `--skip-optimize` … (+2) |
| `encyk/00_system/tools/wikidata-manager/scripts/discover_dump.py` | `--base-url`, `--out`, `--format` |
| `encyk/00_system/tools/wikidata-manager/scripts/download_dump.py` | `--snapshot`, `--dest-dir`, `--curl` |
| `encyk/00_system/tools/wikidata-manager/scripts/local_graph.py` | `--db`, `--registry`, `--out`, `--qid-map`, `--properties-file`, `--levels` |
| `encyk/00_system/tools/wikidata-manager/scripts/verify_dump.py` | `--snapshot`, `--file`, `--write-marker` |
| `skope/cli.py` | `--db`, `--recipe`, `--out`, `--scope-key`, `--guidance`, `--kristal`, `--host`, `--port`, `--input`, `--work`, `--include-metadata`, `--review-out` … (+10) |
| `tools/unesco_local_source_dossier.py` | `--inventory`, `--xml-manifest`, `--out` |

## UNESCO_Workbench

| Module | Options observées (aperçu) |
|---|---|
| `candidates/educational-policy-en-v11/unesco-mt1-10/tools/kristal.py` | `--slug`, `--title`, `--profile`, `--with-ai`, `--force`, `--compact`, `--require-fresh`, `--arketype-dir`, `--usage`, `--archetype`, `--arketype-version`, `--family` … (+52) |
| `candidates/educational-policy/en/SCOPE-20261104-100028-fb5dd7/01_CANDIDATE_WORKSPACE/unesco-mt1-10/tools/kristal.py` | `--slug`, `--title`, `--profile`, `--with-ai`, `--force`, `--compact`, `--require-fresh`, `--arketype-dir`, `--usage`, `--archetype`, `--arketype-version`, `--family` … (+52) |
| `legacy/archived-prototypes/Kristal_UNESCO_Correctifs_v3/Kristal_UNESCO_Pilote_v3/pilot.py` | `--kristal`, `--semantik`, `--run`, `--concept`, `--languages`, `--gf`, `--pgf-python`, `--existing-pgf`, `--output` |
| `legacy/archived-prototypes/Kristal_UNESCO_Pilote_v1/pilot.py` | `--kristal`, `--semantik`, `--run`, `--concept`, `--languages`, `--gf`, `--output` |
| `pipelines/unesco_total.py` | `--workbench`, `--rdf` |
| `tools/educational_policy_en/prepare.py` | `--source`, `--output`, `--kristalizer`, `--index`, `--zip-dir`, `--check-only`, `--no-scan` |

## mediatheque

| Module | Options observées (aperçu) |
|---|---|
| `05_TOOLS/Build-UckkBootstrapManifest.py` | `--kristal-root`, `--korpus-inventory`, `--korpus-root`, `--repository-catalog`, `--output` |
| `05_TOOLS/ImportEncyKHandoff.py` | `--handoff`, `--evidence-root`, `--db`, `--storage`, `--instance-root`, `--accept`, `--receipt-out` |
| `05_TOOLS/KoaKristalMedia.py` | `--db`, `--version-uuid`, `--kind`, `--id`, `--actor`, `--output-dir`, `--reason`, `--producer-instance`, `--producer-organization` |
| `05_TOOLS/KoaKristalSources.py` | `--root`, `--include-candidates`, `--store`, `--show-files`, `--db`, `--storage-root`, `--kristal`, `--source-status`, `--search`, `--limit`, `--output-dir` |
| `05_TOOLS/KoaLocalWorkspace.py` | `--config`, `--show-files`, `--db`, `--init-db` |

## mediatheque-references

| Module | Options observées (aperçu) |
|---|---|
| `tools/guard_git.py` | `--root` |
| `tools/instance_guard.py` | `--instance-root`, `--require-db` |
| `tools/wiki/WikipediaReferenceInventory.py` | `--titles`, `--output`, `--contact`, `--delay`, `--max-pages`, `--manifest`, `--accept` |
| `tools/wiki/atlas/atlas_wikipedia.py` | `--db`, `--inventory`, `--out`, `--max-pages`, `--depth`, `--max-links`, `--max-candidates`, `--max-side-links`, `--shortlist`, `--identity-map`, `--atlas`, `--output` … (+7) |
| `tools/wiki/atlas/extraire_lots_v20.py` | `--atlas`, `--selection`, `--output`, `--xml`, `--official-index`, `--force-reconstruct`, `--future-lot`, `--sidecar`, `--cache`, `--max-streams`, `--progress-every` |
| `tools/wiki/atlas/extraire_lots_xml_v21.py` | `--xml`, `--db`, `--atlas`, `--selection`, `--output`, `--future-lot` |
| `tools/wiki/atlas/index_xml_v21.py` | `--xml`, `--db`, `--batch-pages`, `--progress-pages`, `--max-pages`, `--require-complete`, `--page-id`, `--output` |
| `tools/wiki/dump_import/import_dumps.py` | `--instance`, `--dumps`, `--index`, `--stage`, `--title`, `--qid`, `--test-allow-custom`, `--test-stop-after` |

## scan_engine (Kristalizer external)

| Module | Options observées (aperçu) |
|---|---|
| `kristalizer/cli.py` | `--source`, `--output`, `--index`, `--max-results`, `--staging`, `--kit`, `--publish`, `--activate`, `--file` |


**Usage V32 :** réemployer les opérations utiles en adaptateur/commande interne; unifier `enc...py` et `EncyKlopedia.pyw` plus tard au lieu de lancer arbitrairement ces scripts depuis l’interface. Pour les méthodes/classes, consulter [`inventaire_modules.csv`](inventaire_modules.csv).
