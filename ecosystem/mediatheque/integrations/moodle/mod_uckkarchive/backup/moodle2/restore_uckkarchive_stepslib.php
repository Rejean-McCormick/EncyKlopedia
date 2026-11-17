<?php
// This file is part of Moodle - https://moodle.org/
//
// Moodle is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// any later version.

/**
 * Restore steps for the UCKK Archive activity.
 *
 * @package    mod_uckkarchive
 * @category   backup
 * @copyright  2026 Univers-Cité King Klown
 * @license    https://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later
 */

defined('MOODLE_INTERNAL') || die();

/**
 * Restore structure step for Archives UCKK.
 *
 * This restores archive-owned records only:
 * - archive activity configuration;
 * - archive items;
 * - Kristals;
 * - proof records;
 * - provenance records;
 * - revision records;
 * - export package records;
 * - media records;
 * - media versions, sources, tags, relations, and collections;
 * - content advisory tags, tag sets, markers, and reviews;
 * - external work references.
 *
 * It does not restore external challenge, assembly, integrity, report, badge,
 * competency, seed, registry, or analytics records. Those are owned by their
 * respective plugins.
 */
class restore_uckkarchive_activity_structure_step extends restore_activity_structure_step {
    /**
     * Media records whose current version must be remapped after versions are restored.
     *
     * @var array<int, int>
     */
    private array $pendingcurrentversions = [];

    /**
     * Define restore structure.
     *
     * @return restore_path_element[]
     */
    protected function define_structure(): array {
        $paths = [];
        $userinfo = $this->get_setting_value('userinfo');

        $paths[] = new restore_path_element('uckkarchive', '/activity/uckkarchive');

        if ($userinfo) {
            $paths[] = new restore_path_element(
                'uckkarchive_item',
                '/activity/uckkarchive/items/item'
            );

            $paths[] = new restore_path_element(
                'uckkarchive_kristal',
                '/activity/uckkarchive/items/item/kristals/kristal'
            );

            $paths[] = new restore_path_element(
                'uckkarchive_proof',
                '/activity/uckkarchive/items/item/proofs/proof'
            );

            $paths[] = new restore_path_element(
                'uckkarchive_prov',
                '/activity/uckkarchive/items/item/provenance/prov'
            );

            $paths[] = new restore_path_element(
                'uckkarchive_rev',
                '/activity/uckkarchive/items/item/revisions/revision'
            );

            $paths[] = new restore_path_element(
                'uckkarchive_export',
                '/activity/uckkarchive/exports/export'
            );

            $paths[] = new restore_path_element(
                'uckkarchive_external_work',
                '/activity/uckkarchive/externalworks/externalwork'
            );

            $paths[] = new restore_path_element(
                'uckkarchive_content_tag_set',
                '/activity/uckkarchive/contenttagsets/tagset'
            );

            $paths[] = new restore_path_element(
                'uckkarchive_content_tag',
                '/activity/uckkarchive/contenttags/tag'
            );

            $paths[] = new restore_path_element(
                'uckkarchive_media',
                '/activity/uckkarchive/media/media'
            );

            $paths[] = new restore_path_element(
                'uckkarchive_media_version',
                '/activity/uckkarchive/media/media/versions/version'
            );

            $paths[] = new restore_path_element(
                'uckkarchive_media_source',
                '/activity/uckkarchive/media/media/sources/source'
            );

            $paths[] = new restore_path_element(
                'uckkarchive_media_tag',
                '/activity/uckkarchive/media/media/tags/tag'
            );

            $paths[] = new restore_path_element(
                'uckkarchive_media_collection',
                '/activity/uckkarchive/mediacollections/collection'
            );

            $paths[] = new restore_path_element(
                'uckkarchive_media_collection_item',
                '/activity/uckkarchive/mediacollections/collection/items/item'
            );

            $paths[] = new restore_path_element(
                'uckkarchive_media_relation',
                '/activity/uckkarchive/mediarelations/relation'
            );

            $paths[] = new restore_path_element(
                'uckkarchive_content_marker',
                '/activity/uckkarchive/contentmarkers/marker'
            );

            $paths[] = new restore_path_element(
                'uckkarchive_content_review',
                '/activity/uckkarchive/contentmarkers/marker/reviews/review'
            );
        }

        return $this->prepare_activity_structure($paths);
    }

    /**
     * Restore the main archive activity record.
     *
     * @param array $data Backup data.
     */
    protected function process_uckkarchive($data): void {
        global $DB;

        $data = (object)$data;
        $oldid = (int)$data->id;

        unset($data->id);

        $data->course = $this->get_courseid();

        $this->map_common_restore_fields($data, false);
        $this->offset_common_dates($data);

        $newitemid = $DB->insert_record('uckkarchive', $this->filter_record_for_table('uckkarchive', $data));

        $this->apply_activity_instance($newitemid);
        $this->set_mapping('uckkarchive', $oldid, $newitemid);
    }

    /**
     * Restore an archive item.
     *
     * @param array $data Backup data.
     */
    protected function process_uckkarchive_item($data): void {
        global $DB;

        $data = (object)$data;
        $oldid = (int)$data->id;

        unset($data->id);

        $data->archiveid = $this->get_new_parentid('uckkarchive');
        $data->courseid = $this->get_courseid();

        $this->regenerate_uuid($data);
        $this->map_common_restore_fields($data);
        $this->map_subject_reference($data);
        $this->offset_common_dates($data);

        $newitemid = $DB->insert_record('uckkarchive_item', $this->filter_record_for_table('uckkarchive_item', $data));

        $this->set_mapping('uckkarchive_item', $oldid, $newitemid, true);
    }

    /**
     * Restore a Kristal record.
     *
     * @param array $data Backup data.
     */
    protected function process_uckkarchive_kristal($data): void {
        global $DB;

        $data = (object)$data;
        $oldid = (int)$data->id;

        unset($data->id);

        $data->archiveid = $this->get_new_parentid('uckkarchive');
        $data->itemid = $this->get_new_parentid('uckkarchive_item');
        $data->courseid = $this->get_courseid();

        $this->regenerate_uuid($data);
        $this->map_common_restore_fields($data);
        $this->map_source_reference($data);
        $this->offset_common_dates($data);

        $newitemid = $DB->insert_record('uckkarchive_kristal', $this->filter_record_for_table('uckkarchive_kristal', $data));

        $this->set_mapping('uckkarchive_kristal', $oldid, $newitemid, true);
    }

    /**
     * Restore a proof record.
     *
     * @param array $data Backup data.
     */
    protected function process_uckkarchive_proof($data): void {
        global $DB;

        $data = (object)$data;
        $oldid = (int)$data->id;

        unset($data->id);

        $data->archiveid = $this->get_new_parentid('uckkarchive');
        $data->itemid = $this->get_new_parentid('uckkarchive_item');
        $data->courseid = $this->get_courseid();

        $this->regenerate_uuid($data);
        $this->map_common_restore_fields($data);
        $this->map_source_reference($data);
        $this->offset_common_dates($data);

        $newitemid = $DB->insert_record('uckkarchive_proof', $this->filter_record_for_table('uckkarchive_proof', $data));

        $this->set_mapping('uckkarchive_proof', $oldid, $newitemid, true);
    }

    /**
     * Restore a provenance record.
     *
     * @param array $data Backup data.
     */
    protected function process_uckkarchive_prov($data): void {
        global $DB;

        $data = (object)$data;
        $oldid = (int)$data->id;

        unset($data->id);

        $data->archiveid = $this->get_new_parentid('uckkarchive');
        $data->itemid = $this->get_new_parentid('uckkarchive_item');
        $data->courseid = $this->get_courseid();

        if (!empty($data->proofid)) {
            $data->proofid = $this->get_mappingid('uckkarchive_proof', $data->proofid, 0);
        }

        if (!empty($data->kristalid)) {
            $data->kristalid = $this->get_mappingid('uckkarchive_kristal', $data->kristalid, 0);
        }

        $this->regenerate_uuid($data);
        $this->map_common_restore_fields($data);
        $this->map_source_reference($data);
        $this->offset_common_dates($data);

        $newitemid = $DB->insert_record('uckkarchive_prov', $this->filter_record_for_table('uckkarchive_prov', $data));

        $this->set_mapping('uckkarchive_prov', $oldid, $newitemid, true);
    }

    /**
     * Restore a revision record.
     *
     * @param array $data Backup data.
     */
    protected function process_uckkarchive_rev($data): void {
        global $DB;

        $data = (object)$data;
        $oldid = (int)$data->id;

        unset($data->id);

        $data->archiveid = $this->get_new_parentid('uckkarchive');
        $data->itemid = $this->get_new_parentid('uckkarchive_item');
        $data->courseid = $this->get_courseid();

        if (!empty($data->kristalid)) {
            $data->kristalid = $this->get_mappingid('uckkarchive_kristal', $data->kristalid, 0);
        }

        if (!empty($data->proofid)) {
            $data->proofid = $this->get_mappingid('uckkarchive_proof', $data->proofid, 0);
        }

        if (!empty($data->previd)) {
            $data->previd = $this->get_mappingid('uckkarchive_rev', $data->previd, 0);
        }

        $this->regenerate_uuid($data);
        $this->map_common_restore_fields($data);
        $this->offset_common_dates($data);

        $newitemid = $DB->insert_record('uckkarchive_rev', $this->filter_record_for_table('uckkarchive_rev', $data));

        $this->set_mapping('uckkarchive_rev', $oldid, $newitemid, true);
    }

    /**
     * Restore an archive export record.
     *
     * @param array $data Backup data.
     */
    protected function process_uckkarchive_export($data): void {
        global $DB;

        $data = (object)$data;
        $oldid = (int)$data->id;

        unset($data->id);

        $data->archiveid = $this->get_new_parentid('uckkarchive');
        $data->courseid = $this->get_courseid();

        if (!empty($data->itemid)) {
            $data->itemid = $this->get_mappingid('uckkarchive_item', $data->itemid, 0);
        }

        if (!empty($data->kristalid)) {
            $data->kristalid = $this->get_mappingid('uckkarchive_kristal', $data->kristalid, 0);
        }

        if (!empty($data->mediaid)) {
            $data->mediaid = $this->get_mappingid('uckkarchive_media', $data->mediaid, 0);
        }

        if (!empty($data->collectionid)) {
            $data->collectionid = $this->get_mappingid('uckkarchive_media_collection', $data->collectionid, 0);
        }

        $this->regenerate_uuid($data);
        $this->map_common_restore_fields($data);
        $this->map_source_reference($data);
        $this->offset_common_dates($data);

        $newitemid = $DB->insert_record('uckkarchive_export', $this->filter_record_for_table('uckkarchive_export', $data));

        $this->set_mapping('uckkarchive_export', $oldid, $newitemid, true);
    }

    /**
     * Restore an external work reference.
     *
     * @param array $data Backup data.
     */
    protected function process_uckkarchive_external_work($data): void {
        global $DB;

        $data = (object)$data;
        $oldid = (int)$data->id;

        unset($data->id);

        $data->archiveid = $this->get_new_parentid('uckkarchive');
        $data->courseid = $this->get_courseid();

        $this->regenerate_uuid($data);
        $this->map_common_restore_fields($data);
        $this->offset_common_dates($data);

        $newitemid = $DB->insert_record(
            'uckkarchive_external_work',
            $this->filter_record_for_table('uckkarchive_external_work', $data)
        );

        $this->set_mapping('uckkarchive_external_work', $oldid, $newitemid, true);
    }

    /**
     * Restore a content tag set.
     *
     * @param array $data Backup data.
     */
    protected function process_uckkarchive_content_tag_set($data): void {
        global $DB;

        $data = (object)$data;
        $oldid = (int)$data->id;

        unset($data->id);

        if (property_exists($data, 'archiveid')) {
            $data->archiveid = $this->get_new_parentid('uckkarchive');
        }

        if (property_exists($data, 'courseid')) {
            $data->courseid = $this->get_courseid();
        }

        $this->regenerate_uuid($data);
        $this->map_common_restore_fields($data);
        $this->offset_common_dates($data);

        $newitemid = $DB->insert_record(
            'uckkarchive_content_tag_set',
            $this->filter_record_for_table('uckkarchive_content_tag_set', $data)
        );

        $this->set_mapping('uckkarchive_content_tag_set', $oldid, $newitemid);
    }

    /**
     * Restore a content tag.
     *
     * @param array $data Backup data.
     */
    protected function process_uckkarchive_content_tag($data): void {
        global $DB;

        $data = (object)$data;
        $oldid = (int)$data->id;

        unset($data->id);

        if (property_exists($data, 'archiveid')) {
            $data->archiveid = $this->get_new_parentid('uckkarchive');
        }

        if (property_exists($data, 'courseid')) {
            $data->courseid = $this->get_courseid();
        }

        if (!empty($data->tagsetid)) {
            $data->tagsetid = $this->get_mappingid('uckkarchive_content_tag_set', $data->tagsetid, 0);
        }

        $this->regenerate_uuid($data);
        $this->map_common_restore_fields($data);
        $this->offset_common_dates($data);

        $newitemid = $DB->insert_record(
            'uckkarchive_content_tag',
            $this->filter_record_for_table('uckkarchive_content_tag', $data)
        );

        $this->set_mapping('uckkarchive_content_tag', $oldid, $newitemid);
    }

    /**
     * Restore a media record.
     *
     * @param array $data Backup data.
     */
    protected function process_uckkarchive_media($data): void {
        global $DB;

        $data = (object)$data;
        $oldid = (int)$data->id;
        $oldcurrentversionid = !empty($data->currentversionid) ? (int)$data->currentversionid : 0;

        unset($data->id);

        $data->archiveid = $this->get_new_parentid('uckkarchive');
        $data->courseid = $this->get_courseid();

        if (property_exists($data, 'currentversionid')) {
            $data->currentversionid = 0;
        }

        $this->regenerate_uuid($data);
        $this->map_common_restore_fields($data);
        $this->map_archive_object_fields($data);
        $this->map_source_reference($data);
        $this->offset_common_dates($data);
        $this->assign_restored_object_to_root_library($data);

        $newitemid = $DB->insert_record('uckkarchive_media', $this->filter_record_for_table('uckkarchive_media', $data));

        $this->set_mapping('uckkarchive_media', $oldid, $newitemid, true);

        if ($oldcurrentversionid > 0) {
            $this->pendingcurrentversions[$newitemid] = $oldcurrentversionid;
        }
    }

    /**
     * Restore a media version record.
     *
     * @param array $data Backup data.
     */
    protected function process_uckkarchive_media_version($data): void {
        global $DB;

        $data = (object)$data;
        $oldid = (int)$data->id;

        unset($data->id);

        $data->archiveid = $this->get_new_parentid('uckkarchive');
        $data->mediaid = $this->get_new_parentid('uckkarchive_media');
        $data->courseid = $this->get_courseid();

        $this->regenerate_uuid($data);
        $this->map_common_restore_fields($data);
        $this->map_archive_object_fields($data);
        $this->offset_common_dates($data);

        $newitemid = $DB->insert_record(
            'uckkarchive_media_version',
            $this->filter_record_for_table('uckkarchive_media_version', $data)
        );

        $this->set_mapping('uckkarchive_media_version', $oldid, $newitemid, true);
    }

    /**
     * Restore a media source record.
     *
     * @param array $data Backup data.
     */
    protected function process_uckkarchive_media_source($data): void {
        global $DB;

        $data = (object)$data;
        $oldid = (int)$data->id;

        unset($data->id);

        $data->archiveid = $this->get_new_parentid('uckkarchive');
        $data->mediaid = $this->get_new_parentid('uckkarchive_media');
        $data->courseid = $this->get_courseid();

        if (!empty($data->externalworkid)) {
            $data->externalworkid = $this->get_mappingid('uckkarchive_external_work', $data->externalworkid, 0);
        }

        $this->regenerate_uuid($data);
        $this->map_common_restore_fields($data);
        $this->map_source_reference($data);
        $this->offset_common_dates($data);

        $newitemid = $DB->insert_record(
            'uckkarchive_media_source',
            $this->filter_record_for_table('uckkarchive_media_source', $data)
        );

        $this->set_mapping('uckkarchive_media_source', $oldid, $newitemid, true);
    }

    /**
     * Restore a media tag record.
     *
     * @param array $data Backup data.
     */
    protected function process_uckkarchive_media_tag($data): void {
        global $DB;

        $data = (object)$data;
        $oldid = (int)$data->id;

        unset($data->id);

        $data->archiveid = $this->get_new_parentid('uckkarchive');
        $data->mediaid = $this->get_new_parentid('uckkarchive_media');
        $data->courseid = $this->get_courseid();

        if (!empty($data->contenttagid)) {
            $data->contenttagid = $this->get_mappingid('uckkarchive_content_tag', $data->contenttagid, 0);
        }

        if (!empty($data->tagid)) {
            $data->tagid = $this->get_mappingid('uckkarchive_content_tag', $data->tagid, $data->tagid);
        }

        $this->regenerate_uuid($data);
        $this->map_common_restore_fields($data);
        $this->offset_common_dates($data);

        $newitemid = $DB->insert_record(
            'uckkarchive_media_tag',
            $this->filter_record_for_table('uckkarchive_media_tag', $data)
        );

        $this->set_mapping('uckkarchive_media_tag', $oldid, $newitemid);
    }

    /**
     * Restore a media collection.
     *
     * @param array $data Backup data.
     */
    protected function process_uckkarchive_media_collection($data): void {
        global $DB;

        $data = (object)$data;
        $oldid = (int)$data->id;

        unset($data->id);

        $data->archiveid = $this->get_new_parentid('uckkarchive');
        $data->courseid = $this->get_courseid();

        $this->regenerate_uuid($data);
        $this->map_common_restore_fields($data);
        $this->offset_common_dates($data);
        $this->assign_restored_object_to_root_library($data);

        $newitemid = $DB->insert_record(
            'uckkarchive_media_collection',
            $this->filter_record_for_table('uckkarchive_media_collection', $data)
        );

        $this->set_mapping('uckkarchive_media_collection', $oldid, $newitemid, true);
    }

    /**
     * Restore a media collection membership row.
     *
     * @param array $data Backup data.
     */
    protected function process_uckkarchive_media_collection_item($data): void {
        global $DB;

        $data = (object)$data;
        $oldid = (int)$data->id;

        unset($data->id);

        $data->collectionid = $this->get_new_parentid('uckkarchive_media_collection');

        if (!empty($data->mediaid)) {
            $data->mediaid = $this->get_mappingid('uckkarchive_media', $data->mediaid, 0);
        }

        $this->regenerate_uuid($data);
        $this->map_common_restore_fields($data);
        $this->offset_common_dates($data);

        $newitemid = $DB->insert_record(
            'uckkarchive_media_collection_item',
            $this->filter_record_for_table('uckkarchive_media_collection_item', $data)
        );

        $this->set_mapping('uckkarchive_media_collection_item', $oldid, $newitemid);
    }

    /**
     * Restore a media relation.
     *
     * @param array $data Backup data.
     */
    protected function process_uckkarchive_media_relation($data): void {
        global $DB;

        $data = (object)$data;
        $oldid = (int)$data->id;

        unset($data->id);

        $data->archiveid = $this->get_new_parentid('uckkarchive');

        if (property_exists($data, 'courseid')) {
            $data->courseid = $this->get_courseid();
        }

        $this->regenerate_uuid($data);
        $this->map_common_restore_fields($data);
        $this->map_media_relation_endpoints($data);
        $this->offset_common_dates($data);

        $newitemid = $DB->insert_record(
            'uckkarchive_media_relation',
            $this->filter_record_for_table('uckkarchive_media_relation', $data)
        );

        $this->set_mapping('uckkarchive_media_relation', $oldid, $newitemid);
    }

    /**
     * Restore a content marker.
     *
     * @param array $data Backup data.
     */
    protected function process_uckkarchive_content_marker($data): void {
        global $DB;

        $data = (object)$data;
        $oldid = (int)$data->id;

        unset($data->id);

        $data->archiveid = $this->get_new_parentid('uckkarchive');
        $data->courseid = $this->get_courseid();

        if (!empty($data->mediaid)) {
            $data->mediaid = $this->get_mappingid('uckkarchive_media', $data->mediaid, 0);
        }

        if (!empty($data->externalworkid)) {
            $data->externalworkid = $this->get_mappingid('uckkarchive_external_work', $data->externalworkid, 0);
        }

        if (!empty($data->contenttagid)) {
            $data->contenttagid = $this->get_mappingid('uckkarchive_content_tag', $data->contenttagid, 0);
        }

        if (!empty($data->tagid)) {
            $data->tagid = $this->get_mappingid('uckkarchive_content_tag', $data->tagid, $data->tagid);
        }

        $this->map_marker_target($data);
        $this->regenerate_uuid($data);
        $this->map_common_restore_fields($data);
        $this->offset_common_dates($data);

        $newitemid = $DB->insert_record(
            'uckkarchive_content_marker',
            $this->filter_record_for_table('uckkarchive_content_marker', $data)
        );

        $this->set_mapping('uckkarchive_content_marker', $oldid, $newitemid, true);
    }

    /**
     * Restore a content review.
     *
     * @param array $data Backup data.
     */
    protected function process_uckkarchive_content_review($data): void {
        global $DB;

        $data = (object)$data;
        $oldid = (int)$data->id;

        unset($data->id);

        $data->markerid = $this->get_new_parentid('uckkarchive_content_marker');

        if (property_exists($data, 'archiveid')) {
            $data->archiveid = $this->get_new_parentid('uckkarchive');
        }

        if (property_exists($data, 'courseid')) {
            $data->courseid = $this->get_courseid();
        }

        $this->regenerate_uuid($data);
        $this->map_common_restore_fields($data);
        $this->offset_common_dates($data);

        $newitemid = $DB->insert_record(
            'uckkarchive_content_review',
            $this->filter_record_for_table('uckkarchive_content_review', $data)
        );

        $this->set_mapping('uckkarchive_content_review', $oldid, $newitemid, true);
    }

    /**
     * Restore related file areas after all records have been restored.
     */
    protected function after_execute(): void {
        $this->restore_current_media_versions();

        $this->add_related_files('mod_uckkarchive', 'intro', null);

        // Archive-level file areas.
        $this->add_related_files('mod_uckkarchive', 'archive_attachments', null);

        // Archive item file areas.
        $this->add_related_files('mod_uckkarchive', 'item_content', 'uckkarchive_item');
        $this->add_related_files('mod_uckkarchive', 'public_summary', 'uckkarchive_item');
        $this->add_related_files('mod_uckkarchive', 'item_files', 'uckkarchive_item');
        $this->add_related_files('mod_uckkarchive', 'item_attachments', 'uckkarchive_item');

        // Kristal file areas.
        $this->add_related_files('mod_uckkarchive', 'kristal_content', 'uckkarchive_kristal');
        $this->add_related_files('mod_uckkarchive', 'kristal_summary', 'uckkarchive_kristal');
        $this->add_related_files('mod_uckkarchive', 'kristal_files', 'uckkarchive_kristal');
        $this->add_related_files('mod_uckkarchive', 'kristal_attachments', 'uckkarchive_kristal');

        // Proof file areas.
        $this->add_related_files('mod_uckkarchive', 'proof_description', 'uckkarchive_proof');
        $this->add_related_files('mod_uckkarchive', 'proof_content', 'uckkarchive_proof');
        $this->add_related_files('mod_uckkarchive', 'proof_files', 'uckkarchive_proof');
        $this->add_related_files('mod_uckkarchive', 'proof_attachments', 'uckkarchive_proof');

        // Provenance, revision, and export file areas.
        $this->add_related_files('mod_uckkarchive', 'provenance_statement', 'uckkarchive_prov');
        $this->add_related_files('mod_uckkarchive', 'provenance_attachments', 'uckkarchive_prov');
        $this->add_related_files('mod_uckkarchive', 'revision_attachments', 'uckkarchive_rev');
        $this->add_related_files('mod_uckkarchive', 'export_files', 'uckkarchive_export');
        $this->add_related_files('mod_uckkarchive', 'export_manifest', 'uckkarchive_export');
        $this->add_related_files('mod_uckkarchive', 'export_package', 'uckkarchive_export');

        // Media file areas.
        $this->add_related_files('mod_uckkarchive', 'media_original', 'uckkarchive_media');
        $this->add_related_files('mod_uckkarchive', 'media_preview', 'uckkarchive_media');
        $this->add_related_files('mod_uckkarchive', 'media_thumbnail', 'uckkarchive_media');
        $this->add_related_files('mod_uckkarchive', 'media_derivative', 'uckkarchive_media');
        $this->add_related_files('mod_uckkarchive', 'media_caption', 'uckkarchive_media');
        $this->add_related_files('mod_uckkarchive', 'media_transcript', 'uckkarchive_media');
        $this->add_related_files('mod_uckkarchive', 'media_attachment', 'uckkarchive_media');
        $this->add_related_files('mod_uckkarchive', 'media_metadata', 'uckkarchive_media');

        // Media version and source file areas.
        $this->add_related_files('mod_uckkarchive', 'media_version_file', 'uckkarchive_media_version');
        $this->add_related_files('mod_uckkarchive', 'media_version_attachment', 'uckkarchive_media_version');
        $this->add_related_files('mod_uckkarchive', 'media_source_files', 'uckkarchive_media_source');

        // Media collection file areas.
        $this->add_related_files('mod_uckkarchive', 'media_collection_attachment', 'uckkarchive_media_collection');

        // External work file areas.
        $this->add_related_files('mod_uckkarchive', 'external_work_reference_files', 'uckkarchive_external_work');

        // Content advisory file areas.
        $this->add_related_files('mod_uckkarchive', 'content_marker_files', 'uckkarchive_content_marker');
        $this->add_related_files('mod_uckkarchive', 'content_review_files', 'uckkarchive_content_review');
        $this->add_related_files('mod_uckkarchive', 'cultural_protocol_files', 'uckkarchive_content_marker');
    }

    /**
     * Put restored media/collections in the destination site's root UCKK fund.
     *
     * Media-library ownership and bridges are site-level configuration and are
     * deliberately not transported by an activity backup. This avoids treating
     * a numeric library id from another Moodle installation as authoritative.
     * Administrators may reassign the restored objects afterwards.
     *
     * @param stdClass $data Restored record before insertion.
     * @return void
     */
    private function assign_restored_object_to_root_library(stdClass $data): void {
        if (!\mod_uckkarchive\local\media_library_scope::schema_ready()) {
            return;
        }

        $scope = new \mod_uckkarchive\local\media_library_scope();
        $library = $scope->resolve_by_slug(\mod_uckkarchive\local\media_library_scope::LIBRARY_UCKK);
        if ($library) {
            $data->libraryid = (int)$library->id;
        }
    }

    /**
     * Map common user/context/course references.
     *
     * @param stdClass $data Restore record.
     * @param bool $hascontext Whether the table owns a contextid field.
     */
    private function map_common_restore_fields(stdClass $data, bool $hascontext = true): void {
        if (property_exists($data, 'courseid')) {
            $data->courseid = $this->get_courseid();
        }

        if ($hascontext && property_exists($data, 'contextid')) {
            $data->contextid = $this->map_contextid((int)$data->contextid);
        }

        foreach ($this->get_user_fields() as $field) {
            if (property_exists($data, $field) && !empty($data->{$field})) {
                $data->{$field} = $this->get_mappingid('user', $data->{$field}, $data->{$field});
            }
        }

        if (property_exists($data, 'cmid')) {
            $data->cmid = $this->task->get_moduleid();
        }
    }

    /**
     * Map archive-owned direct foreign keys when present.
     *
     * @param stdClass $data Restore record.
     */
    private function map_archive_object_fields(stdClass $data): void {
        $map = [
            'itemid' => 'uckkarchive_item',
            'proofid' => 'uckkarchive_proof',
            'kristalid' => 'uckkarchive_kristal',
            'provenanceid' => 'uckkarchive_prov',
            'provid' => 'uckkarchive_prov',
            'revisionid' => 'uckkarchive_rev',
            'revid' => 'uckkarchive_rev',
            'mediaid' => 'uckkarchive_media',
            'versionid' => 'uckkarchive_media_version',
            'mediaversionid' => 'uckkarchive_media_version',
            'sourceid' => 'uckkarchive_media_source',
            'collectionid' => 'uckkarchive_media_collection',
            'collectionitemid' => 'uckkarchive_media_collection_item',
            'relationid' => 'uckkarchive_media_relation',
            'markerid' => 'uckkarchive_content_marker',
            'reviewid' => 'uckkarchive_content_review',
            'contenttagid' => 'uckkarchive_content_tag',
            'tagid' => 'uckkarchive_content_tag',
            'tagsetid' => 'uckkarchive_content_tag_set',
            'externalworkid' => 'uckkarchive_external_work',
        ];

        foreach ($map as $field => $mapping) {
            if (property_exists($data, $field) && !empty($data->{$field})) {
                $data->{$field} = $this->get_mappingid($mapping, $data->{$field}, 0);
            }
        }
    }

    /**
     * Map source component/id references when the source belongs to this restore.
     *
     * External sources are preserved as references and not duplicated.
     *
     * @param stdClass $data Restore record.
     */
    private function map_source_reference(stdClass $data): void {
        if (empty($data->sourcecomponent) || empty($data->sourceid)) {
            return;
        }

        $mapping = $this->mapping_for_component((string)$data->sourcecomponent);

        if ($mapping !== '') {
            $data->sourceid = $this->get_mappingid($mapping, $data->sourceid, $data->sourceid);
        }
    }

    /**
     * Map subject component/id references when they point to restored archive data.
     *
     * @param stdClass $data Restore record.
     */
    private function map_subject_reference(stdClass $data): void {
        if (empty($data->subjectcomponent) || empty($data->subjectid)) {
            return;
        }

        $mapping = $this->mapping_for_component((string)$data->subjectcomponent);

        if ($mapping !== '') {
            $data->subjectid = $this->get_mappingid($mapping, $data->subjectid, $data->subjectid);
        }
    }

    /**
     * Map content marker target ids.
     *
     * @param stdClass $data Restore record.
     */
    private function map_marker_target(stdClass $data): void {
        if (empty($data->targettype) || empty($data->targetid)) {
            return;
        }

        $mapping = $this->mapping_for_object_type((string)$data->targettype);

        if ($mapping !== '') {
            $data->targetid = $this->get_mappingid($mapping, $data->targetid, 0);
        }
    }

    /**
     * Map media relation endpoint ids.
     *
     * @param stdClass $data Restore record.
     */
    private function map_media_relation_endpoints(stdClass $data): void {
        if (!empty($data->fromtype) && !empty($data->fromid)) {
            $mapping = $this->mapping_for_object_type((string)$data->fromtype);

            if ($mapping !== '') {
                $data->fromid = $this->get_mappingid($mapping, $data->fromid, 0);
            }
        }

        if (!empty($data->totype) && !empty($data->toid)) {
            $mapping = $this->mapping_for_object_type((string)$data->totype);

            if ($mapping !== '') {
                $data->toid = $this->get_mappingid($mapping, $data->toid, 0);
            }
        }
    }

    /**
     * Return restore mapping name for a component reference.
     *
     * @param string $component Component reference.
     * @return string Mapping name or empty string.
     */
    private function mapping_for_component(string $component): string {
        $component = trim($component);

        return match ($component) {
            'mod_uckkarchive:item',
            'mod_uckkarchive:archive_item',
            'uckkarchive_item',
            'archive_item' => 'uckkarchive_item',

            'mod_uckkarchive:kristal',
            'uckkarchive_kristal',
            'kristal' => 'uckkarchive_kristal',

            'mod_uckkarchive:proof',
            'uckkarchive_proof',
            'proof' => 'uckkarchive_proof',

            'mod_uckkarchive:provenance',
            'uckkarchive_prov',
            'provenance',
            'prov' => 'uckkarchive_prov',

            'mod_uckkarchive:revision',
            'uckkarchive_rev',
            'revision',
            'rev' => 'uckkarchive_rev',

            'mod_uckkarchive:media',
            'uckkarchive_media',
            'media' => 'uckkarchive_media',

            'mod_uckkarchive:media_version',
            'uckkarchive_media_version',
            'media_version' => 'uckkarchive_media_version',

            'mod_uckkarchive:media_source',
            'uckkarchive_media_source',
            'media_source' => 'uckkarchive_media_source',

            'mod_uckkarchive:media_collection',
            'uckkarchive_media_collection',
            'media_collection' => 'uckkarchive_media_collection',

            'mod_uckkarchive:media_collection_item',
            'uckkarchive_media_collection_item',
            'media_collection_item' => 'uckkarchive_media_collection_item',

            'mod_uckkarchive:content_marker',
            'uckkarchive_content_marker',
            'content_marker' => 'uckkarchive_content_marker',

            'mod_uckkarchive:content_review',
            'uckkarchive_content_review',
            'content_review' => 'uckkarchive_content_review',

            'mod_uckkarchive:content_tag',
            'uckkarchive_content_tag',
            'content_tag' => 'uckkarchive_content_tag',

            'mod_uckkarchive:external_work',
            'uckkarchive_external_work',
            'external_work' => 'uckkarchive_external_work',

            default => '',
        };
    }

    /**
     * Return restore mapping name for an object type.
     *
     * @param string $type Object type.
     * @return string Mapping name or empty string.
     */
    private function mapping_for_object_type(string $type): string {
        $type = trim($type);

        return match ($type) {
            'archive_item',
            'item',
            'uckkarchive_item' => 'uckkarchive_item',

            'proof',
            'uckkarchive_proof' => 'uckkarchive_proof',

            'kristal',
            'uckkarchive_kristal' => 'uckkarchive_kristal',

            'provenance',
            'prov',
            'uckkarchive_prov' => 'uckkarchive_prov',

            'revision',
            'rev',
            'uckkarchive_rev' => 'uckkarchive_rev',

            'media',
            'uckkarchive_media' => 'uckkarchive_media',

            'media_version',
            'version',
            'uckkarchive_media_version' => 'uckkarchive_media_version',

            'media_source',
            'source',
            'uckkarchive_media_source' => 'uckkarchive_media_source',

            'media_collection',
            'collection',
            'uckkarchive_media_collection' => 'uckkarchive_media_collection',

            'media_collection_item',
            'collection_item',
            'uckkarchive_media_collection_item' => 'uckkarchive_media_collection_item',

            'content_marker',
            'marker',
            'uckkarchive_content_marker' => 'uckkarchive_content_marker',

            'content_review',
            'review',
            'uckkarchive_content_review' => 'uckkarchive_content_review',

            'content_tag',
            'tag',
            'uckkarchive_content_tag' => 'uckkarchive_content_tag',

            'external_work',
            'work',
            'uckkarchive_external_work' => 'uckkarchive_external_work',

            default => '',
        };
    }

    /**
     * Offset common date fields.
     *
     * @param stdClass $data Restore record.
     */
    private function offset_common_dates(stdClass $data): void {
        foreach ($this->get_date_fields() as $field) {
            if (property_exists($data, $field) && !empty($data->{$field})) {
                $data->{$field} = $this->apply_date_offset($data->{$field});
            }
        }
    }

    /**
     * Restore current media-version pointers after child versions have mappings.
     */
    private function restore_current_media_versions(): void {
        global $DB;

        if (empty($this->pendingcurrentversions)) {
            return;
        }

        foreach ($this->pendingcurrentversions as $newmediaid => $oldversionid) {
            $newversionid = $this->get_mappingid('uckkarchive_media_version', $oldversionid, 0);

            if ($newversionid <= 0) {
                continue;
            }

            if (!$DB->record_exists('uckkarchive_media', ['id' => $newmediaid])) {
                continue;
            }

            if (!$this->table_has_field('uckkarchive_media', 'currentversionid')) {
                continue;
            }

            $record = new stdClass();
            $record->id = $newmediaid;
            $record->currentversionid = $newversionid;

            if ($this->table_has_field('uckkarchive_media', 'timemodified')) {
                $record->timemodified = time();
            }

            $DB->update_record('uckkarchive_media', $record);
        }
    }

    /**
     * Map an old context id to the restored context id when possible.
     *
     * @param int $contextid Original context id.
     * @return int Restored context id.
     */
    private function map_contextid(int $contextid): int {
        $modulecontextid = \context_module::instance($this->task->get_moduleid())->id;

        if ($contextid <= 0) {
            return $modulecontextid;
        }

        return $this->get_mappingid('context', $contextid, $modulecontextid);
    }

    /**
     * Replace restored UUID to avoid duplicate portable identifiers on same-site restore.
     *
     * @param stdClass $data Restore record.
     */
    private function regenerate_uuid(stdClass $data): void {
        if (!property_exists($data, 'uuid')) {
            return;
        }

        $data->uuid = $this->generate_uuid();
    }

    /**
     * Generate a UUID using Moodle core/local helper when available.
     *
     * @return string
     */
    private function generate_uuid(): string {
        if (class_exists('\\mod_uckkarchive\\local\\uuid') &&
                method_exists('\\mod_uckkarchive\\local\\uuid', 'generate')) {
            return \mod_uckkarchive\local\uuid::generate();
        }

        if (class_exists('\\core\\uuid') && method_exists('\\core\\uuid', 'generate')) {
            return \core\uuid::generate();
        }

        $data = random_bytes(16);
        $data[6] = chr((ord($data[6]) & 0x0f) | 0x40);
        $data[8] = chr((ord($data[8]) & 0x3f) | 0x80);

        return vsprintf('%s%s-%s-%s-%s-%s%s%s', str_split(bin2hex($data), 4));
    }

    /**
     * Filter a restored record to the fields that exist in the current table.
     *
     * This makes the restore step safer across plugin upgrades where backups
     * may contain fields introduced before or after the current installed
     * schema.
     *
     * @param string $table Table name without braces.
     * @param stdClass $data Restore record.
     * @return stdClass Filtered record.
     */
    private function filter_record_for_table(string $table, stdClass $data): stdClass {
        global $DB;

        $columns = $DB->get_columns($table);
        $record = new stdClass();

        foreach ((array)$data as $field => $value) {
            if ($field === 'id') {
                continue;
            }

            if (array_key_exists($field, $columns)) {
                $record->{$field} = $value;
            }
        }

        return $record;
    }

    /**
     * Return whether a table has a field.
     *
     * @param string $table Table name.
     * @param string $field Field name.
     * @return bool
     */
    private function table_has_field(string $table, string $field): bool {
        global $DB;

        if (!$DB->get_manager()->table_exists(new xmldb_table($table))) {
            return false;
        }

        $columns = $DB->get_columns($table);

        return array_key_exists($field, $columns);
    }

    /**
     * User reference fields used across archive tables.
     *
     * @return string[]
     */
    private function get_user_fields(): array {
        return [
            'userid',
            'authorid',
            'ownerid',
            'submittedby',
            'validatedby',
            'reviewedby',
            'reviewerid',
            'revisedby',
            'exportedby',
            'publishedby',
            'createdby',
            'modifiedby',
            'deletedby',
            'archivedby',
            'approvedby',
            'rejectedby',
        ];
    }

    /**
     * Date fields used across archive tables.
     *
     * @return string[]
     */
    private function get_date_fields(): array {
        return [
            'timeopen',
            'timeclose',
            'sourcedate',
            'validatedtime',
            'reviewedtime',
            'revisedtime',
            'exportedtime',
            'publishedtime',
            'deletedtime',
            'archivedtime',
            'approvedtime',
            'rejectedtime',
            'expirytime',
            'expiresat',
            'timecreated',
            'timemodified',
        ];
    }
}

