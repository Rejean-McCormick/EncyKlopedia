# Atlas SQL statique — tables et index déclarés dans les sources

**59 fichiers source** possèdent du DDL repéré dans le code des snapshots. Cette liste décrit les chaînes `CREATE TABLE`/`CREATE INDEX` détectées, sans lire les bases SQLite réelles du poste. Les schémas historiques et de tests sont mêlés.

| Source du DDL | Tables (aperçu) | Index (aperçu) |
|---|---|---|
| `EncyKlopedia/OVERLAY_CONTEXTE_UNESCO_V28/tests/test_contexte_revue_unesco_v28.py` | `evidence`, `pages`, `seed_queue`, `v21_meta` |  |
| `EncyKlopedia/OVERLAY_CONTEXTE_UNESCO_V28/tools/unesco_pilot/poste_chatgpt_v30.py` | `events`, `jobs`, `lanes`, `meta`, `receipts`, `review_index`, `updates` | `idx_job_kind`, `idx_job_queue`, `idx_review_priority` |
| `EncyKlopedia/_SAUVEGARDES_CODE_CONTEXTE_V28/20261112_163151/tools/unesco_pilot/poste_chatgpt_v30.py` | `events`, `jobs`, `lanes`, `meta`, `receipts`, `review_index`, `updates` | `idx_job_kind`, `idx_job_queue`, `idx_review_priority` |
| `EncyKlopedia/_SAUVEGARDES_PROFONDEUR_KRISTAL/20261114T171028552327Z/tools/unesco_pilot/poste_chatgpt_v30.py` | `events`, `jobs`, `lanes`, `meta`, `receipts`, `review_index`, `updates`, `v311_job_routes` | `idx_job_kind`, `idx_job_queue`, `idx_review_priority` |
| `EncyKlopedia/_SAUVEGARDES_PROFONDEUR_KRISTAL/20261114T171028552327Z/tools/unesco_pilot/production_kristals_v27.py` | `article_visits`, `citations`, `claim_branches`, `claim_concepts`, `claims`, `delta_imports`, `meta`, `packs` … (+4) | `idx_claim_pred`, `idx_queue_pending` |
| `EncyKlopedia/tests/test_automated_local_pilot.py` | `ingest_state`, `wiki_pages`, `wiki_qid` |  |
| `EncyKlopedia/tests/test_catalogue_global_v25.py` | `important`, `ingest_state`, `wiki_categorylink_ids`, `wiki_linktargets`, `wiki_pages`, `wiki_qid` | `idx_wiki_catid_from`, `idx_wiki_catid_target`, `idx_wiki_lt_title`, `idx_wiki_pages_title`, `idx_wiki_qid_qid` |
| `EncyKlopedia/tests/test_decouverte_articles_relies_v28.py` | `assignments`, `candidates`, `evidence`, `ingest_state`, `jobs`, `pages`, `v21_meta`, `wiki_categorylink_ids` … (+3) | `idx_wiki_catid_from`, `idx_wiki_catid_target`, `idx_wiki_lt_title`, `idx_wiki_pages_title`, `idx_wiki_qid_qid` |
| `EncyKlopedia/tests/test_integration_ponts_revus_v26.py` | `ingest_state`, `wiki_categorylink_ids`, `wiki_linktargets`, `wiki_pages`, `wiki_qid` | `idx_wiki_catid_from`, `idx_wiki_catid_target`, `idx_wiki_lt_title`, `idx_wiki_pages_title`, `idx_wiki_qid_qid` |
| `EncyKlopedia/tests/test_integration_v31.py` | `articles`, `assignments`, `candidates`, `evidence`, `meta`, `reviewed_article_links_v28`, `wiki_categorylinks`, `wiki_linktargets` … (+3) | `idx_wiki_cat_from`, `idx_wiki_pagelinks_from` |
| `EncyKlopedia/tests/test_inventaire_categories_v26.py` | `foreign_table`, `ingest_state`, `wiki_categorylink_ids`, `wiki_linktargets`, `wiki_pages` | `idx_wiki_catid_target`, `idx_wiki_lt_title`, `idx_wiki_pages_title` |
| `EncyKlopedia/tests/test_megamaj_v311.py` | `articles`, `assignments`, `branches`, `candidates`, `evidence`, `meta`, `reviewed_article_links_v28`, `wiki_categorylink_ids` … (+3) | `idx_p_ns_title`, `idx_page_title`, `idx_wiki_catid_from`, `idx_wiki_catid_target` |
| `EncyKlopedia/tests/test_poste_chatgpt_v30.py` | `articles`, `assignments`, `reviewed_article_links_v28` |  |
| `EncyKlopedia/tests/test_preuves_xml_v31.py` | `candidates`, `wiki_pages` |  |
| `EncyKlopedia/tests/test_production_kristals_v27.py` | `articles`, `assignments`, `meta`, `pages`, `v21_meta` | `idx_assgn_article` |
| `EncyKlopedia/tests/test_sqlite_windows_v3111.py` | `candidates`, `jobs`, `unrelated` |  |
| `EncyKlopedia/tests/test_stats_globales_v31.py` | `article_profiles`, `branch_suggestions`, `ingest_state`, `meta`, `wiki_pages` |  |
| `EncyKlopedia/tests/test_unesco_4000_v317.py` | `articles`, `assignments`, `candidates`, `evidence`, `meta`, `reviewed_article_links_v28` |  |
| `EncyKlopedia/tests/test_unesco_pilot_bridge.py` | `wiki_pages`, `wiki_qid` | `idx_wiki_qid_qid` |
| `EncyKlopedia/tests/test_volume_backpressure_v3121.py` | `candidates`, `meta` |  |
| `EncyKlopedia/tests/test_volume_transition_v315.py` | `candidates` |  |
| `EncyKlopedia/tools/dictionary-harvester/dik_qualification.py` | `candidates`, `completed_languages`, `license_events`, `meta`, `review_events` | `ix_license_events_source`, `ix_qualification_language`, `ix_qualification_tier`, `ix_review_events_candidate` |
| `EncyKlopedia/tools/dictionary-harvester/dik_reconciliation.py` | `candidates`, `completed_languages`, `meta` | `idx_candidates_language` |
| `EncyKlopedia/tools/dictionary-harvester/lexical_indexer.py` | `entries`, `language_stats`, `metadata`, `source_files`, `source_members` | `idx_entries_form`, `idx_entries_language_lemma`, `idx_entries_source_line` |
| `EncyKlopedia/tools/dictionary-harvester/quality_audit.py` | `language_audit`, `metadata`, `overlap_examples` |  |
| `EncyKlopedia/tools/dictionary-harvester/semantic_enrichment.py` | `anchors`, `evidence`, `exports`, `meta`, `review_tiers`, `source_progress`, `staged_languages` | `ix_anchors_candidate`, `ix_evidence_candidate`, `ix_evidence_language_candidate` |
| `EncyKlopedia/tools/unesco_pilot/catalogue_global_v25.py` | `articles`, `assignments`, `audit_events`, `branch_concepts`, `branches`, `category_suggestions`, `category_tasks`, `concepts` … (+1) | `idx_assgn_article`, `idx_assgn_branch_article`, `idx_assgn_concept`, `idx_suggestion_review`, `idx_tasks_branch`, `idx_tasks_work` |
| `EncyKlopedia/tools/unesco_pilot/decouvrir_articles_relies_v28.py` | `candidates`, `evidence`, `meta`, `reviewed_article_links_v28`, `seed_queue`, `seed_revision_mismatches`, `v3110_category_roots`, `v3110_probe_cursor` … (+1) | `idx_v28_candidate_article`, `idx_v28_evidence`, `idx_v28_seeds` |
| `EncyKlopedia/tools/unesco_pilot/integrer_ponts_revus_v26.py` | `reviewed_bridge_imports_v26`, `reviewed_bridges_v26` |  |
| `EncyKlopedia/tools/unesco_pilot/inventaire_categories_v26.py` | `categories`, `meta` |  |
| `EncyKlopedia/tools/unesco_pilot/poste_chatgpt_v30.py` | `events`, `hold_reexaminations`, `jobs`, `lanes`, `meta`, `receipts`, `review_index`, `updates` … (+1) | `idx_job_kind`, `idx_job_queue`, `idx_review_priority` |
| `EncyKlopedia/tools/unesco_pilot/preuves_xml_v31.py` | `meta`, `prepared_pages` | `idx_prepared_revision` |
| `EncyKlopedia/tools/unesco_pilot/production_kristals_v27.py` | `article_visits`, `citations`, `claim_branches`, `claim_concepts`, `claims`, `delta_imports`, `meta`, `packs` … (+4) | `idx_claim_pred`, `idx_queue_pending` |
| `EncyKlopedia/tools/unesco_pilot/qualification_globale_v31.py` | `article_profiles`, `branch_suggestions`, `meta` | `idx_v31_branch_score` |
| `EncyKlopedia/tools/unesco_pilot/stabiliser_catalogue_import_v28.py` | `reviewed_article_links_v28` |  |
| `Skope (external)/encyk/00_system/tools/performance/scripts/build_fast_access.py` | `meta`, `reverse_edge` | `idx_reverse_target_property` |
| `Skope (external)/encyk/00_system/tools/scope-builder/scripts/05_build_scope_index.py` | `edge`, `entity`, `literal_value`, `meta`, `name`, `scope_role`, `statement` | `idx_literal_property`, `idx_name_norm`, `idx_scope_role_role`, `idx_statement_property`, `idx_statement_subject`, `idx_statement_target` |
| `Skope (external)/encyk/00_system/tools/scope-builder/scripts/scope_common.py` | `entity_raw`, `meta` |  |
| `Skope (external)/encyk/00_system/tools/wikidata-manager/scripts/build_compact_index.py` | `chronology`, `claim_presence`, `entity`, `entity_edge`, `meta`, `name` | `idx_edge_target_property`, `idx_name_norm`, `idx_presence_property`, `sorts` |
| `Skope (external)/skope/author_campaign.py` | `people`, `selected`, `status`, `works` |  |
| `Skope (external)/skope/massive.py` | `queue`, `selected`, `status` | `queue_unprocessed` |
| `Skope (external)/skope/portfolio.py` | `approved`, `lexeme`, `project`, `query_cache`, `setting`, `tentative` |  |
| `Skope (external)/skope/reconciliation.py` | `audit`, `decisions` |  |
| `Skope (external)/skope/reconciliation_batch.py` | `batch_audit`, `batch_proposals` |  |
| `Skope (external)/tests/test_author_campaign_1322.py` | `entity`, `entity_edge`, `meta`, `name` | `idx_edge_target`, `idx_name_norm` |
| `Skope (external)/tests/test_full_extraction.py` | `status` |  |
| `Skope (external)/tests/test_integration.py` | `entity`, `entity_edge`, `meta`, `name` | `edge_from`, `edge_to`, `idx_name_norm` |
| `Skope (external)/tests/test_results_export.py` | `status` |  |
| `mediatheque-references/tests/test_categorylinks_145_fix.py` | `categorylinks`, `wiki_categorylinks`, `wiki_linktargets` |  |
| `mediatheque-references/tests/test_multiline_fix.py` | `ingest_state`, `page` |  |
| `mediatheque-references/tests/test_unesco_atlas_v19.py` | `ingest_state`, `wiki_categorylink_ids`, `wiki_externallinks`, `wiki_linktargets`, `wiki_pagelinks`, `wiki_pages`, `wiki_qid` | `idx_wiki_catid_from`, `idx_wiki_external_from`, `idx_wiki_lt_title`, `idx_wiki_pagelinks_from`, `idx_wiki_pages_title`, `idx_wiki_qid_qid` |
| `mediatheque-references/tests/test_unesco_multistream_v20.py` | `unrelated` |  |
| `mediatheque-references/tools/wiki/atlas/extraction_multistream_v20.py` | `page_offsets`, `streams`, `v20_meta` |  |
| `mediatheque-references/tools/wiki/atlas/index_xml_v21.py` | `pages`, `v21_meta` |  |
| `mediatheque-references/tools/wiki/dump_import/import_dumps.py` | `ingest_state`, `wiki_categorylink_ids`, `wiki_categorylinks`, `wiki_externallinks`, `wiki_linktargets`, `wiki_pagelinks`, `wiki_pages`, `wiki_qid` | `idx_wiki_cat_from`, `idx_wiki_catid_from`, `idx_wiki_catid_target`, `idx_wiki_external_from`, `idx_wiki_external_url`, `idx_wiki_lt_title`, `idx_wiki_pagelinks_from`, `idx_wiki_pages_latest` … (+2) |
| `mediatheque/06_GUI/koa_mediatheque_gui/koa_mediatheque/services/encyk_handoff_service.py` | `encyk_handoff_receipts` |  |
| `mediatheque/tests/python/test_backup_service.py` | `schema_meta` |  |
| `mediatheque/tests/python/test_xlsx_export_service.py` | `audit_log`, `library_rows` |  |
| `mediatheque/tests/python/test_xlsx_import_service.py` | `audit_log`, `library_rows`, `xlsx_import_log` |  |

**Règle de migration :** ne pas réutiliser une table simplement parce que son nom apparaît ici. Vérifier la version du schéma dans la base source et son propriétaire, puis définir l’adaptateur nécessaire. Les gros index externes restent en lecture seule.

Pour la machine : [`schémas_sql_statiques.json`](schémas_sql_statiques.json).
