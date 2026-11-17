<?php
// This file is part of Moodle - https://moodle.org/
//
// Moodle is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// any later version.

/**
 * Restore task for the UCKK Archive activity module.
 *
 * @package    mod_uckkarchive
 * @copyright  2026 Univers-Cité King Klown
 * @license    https://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later
 */

defined('MOODLE_INTERNAL') || die();

require_once($CFG->dirroot . '/mod/uckkarchive/backup/moodle2/restore_uckkarchive_stepslib.php');

/**
 * Restore task for mod_uckkarchive.
 *
 * The task wires the restore structure step, content decoding, activity-link
 * decoding, and legacy log restoration rules. Record creation, id mapping,
 * file-area restoration, provenance reconstruction, revision mapping, media
 * mapping, content advisory mapping, external work mapping, and export metadata
 * handling belong in restore_uckkarchive_activity_structure_step.
 */
class restore_uckkarchive_activity_task extends restore_activity_task {
    /**
     * Define activity-specific restore settings.
     *
     * No custom task-level settings are required. User-data inclusion is
     * governed by Moodle's standard activity restore settings and interpreted
     * by the structure step.
     *
     * @return void
     */
    protected function define_my_settings(): void {
    }

    /**
     * Define restore steps.
     *
     * @return void
     */
    protected function define_my_steps(): void {
        $this->add_step(new restore_uckkarchive_activity_structure_step(
            'uckkarchive_structure',
            'uckkarchive.xml'
        ));
    }

    /**
     * Define content fields requiring link decoding after restore.
     *
     * @return restore_decode_content[]
     */
    public static function define_decode_contents(): array {
        $contents = [];

        // Main archive instance.
        $contents[] = new restore_decode_content('uckkarchive', [
            'intro',
            'summary',
            'policytext',
            'retentionpolicy',
            'metadata',
        ], 'uckkarchive');

        // Archive items.
        $contents[] = new restore_decode_content('uckkarchive_item', [
            'title',
            'summary',
            'content',
            'publicsummary',
            'description',
            'notes',
            'sourceref',
            'sourceurl',
            'metadata',
        ], 'uckkarchive_item');

        // Kristals.
        $contents[] = new restore_decode_content('uckkarchive_kristal', [
            'title',
            'summary',
            'content',
            'description',
            'notes',
            'sourceref',
            'sourceurl',
            'metadata',
        ], 'uckkarchive_kristal');

        // Proof records.
        $contents[] = new restore_decode_content('uckkarchive_proof', [
            'title',
            'summary',
            'content',
            'description',
            'notes',
            'sourceref',
            'sourceurl',
            'metadata',
        ], 'uckkarchive_proof');

        // Provenance records.
        $contents[] = new restore_decode_content('uckkarchive_prov', [
            'summary',
            'statement',
            'sourcecomponent',
            'sourceref',
            'sourceurl',
            'metadata',
        ], 'uckkarchive_prov');

        // Revision records.
        $contents[] = new restore_decode_content('uckkarchive_rev', [
            'summary',
            'reason',
            'beforejson',
            'afterjson',
            'metadata',
        ], 'uckkarchive_rev');

        // Export records.
        $contents[] = new restore_decode_content('uckkarchive_export', [
            'title',
            'summary',
            'description',
            'reason',
            'exportmanifest',
            'metadata',
        ], 'uckkarchive_export');

        // Media records.
        $contents[] = new restore_decode_content('uckkarchive_media', [
            'title',
            'description',
            'alttext',
            'caption',
            'rightsnote',
            'transcript',
            'metadata',
        ], 'uckkarchive_media');

        // Media version records.
        $contents[] = new restore_decode_content('uckkarchive_media_version', [
            'title',
            'label',
            'summary',
            'description',
            'changenote',
            'rightsnote',
            'metadata',
        ], 'uckkarchive_media_version');

        // Media relation records.
        $contents[] = new restore_decode_content('uckkarchive_media_relation', [
            'title',
            'description',
            'note',
            'metadata',
        ], 'uckkarchive_media_relation');

        // Media tag records.
        $contents[] = new restore_decode_content('uckkarchive_media_tag', [
            'tag',
            'tagkey',
            'label',
            'description',
            'metadata',
        ], 'uckkarchive_media_tag');

        // Media collection records.
        $contents[] = new restore_decode_content('uckkarchive_media_collection', [
            'title',
            'summary',
            'description',
            'metadata',
        ], 'uckkarchive_media_collection');

        // Media collection membership records.
        $contents[] = new restore_decode_content('uckkarchive_media_collection_item', [
            'title',
            'summary',
            'description',
            'note',
            'metadata',
        ], 'uckkarchive_media_collection_item');

        // Media source records.
        $contents[] = new restore_decode_content('uckkarchive_media_source', [
            'title',
            'description',
            'sourceurl',
            'sourcenote',
            'rightsstatement',
            'licensekey',
            'metadata',
        ], 'uckkarchive_media_source');

        // Content advisory tag records.
        $contents[] = new restore_decode_content('uckkarchive_content_tag', [
            'tagkey',
            'label',
            'category',
            'description',
            'guidance',
            'metadata',
        ], 'uckkarchive_content_tag');

        // Content advisory tag-set records.
        $contents[] = new restore_decode_content('uckkarchive_content_tag_set', [
            'tagsetkey',
            'label',
            'description',
            'version',
            'metadata',
        ], 'uckkarchive_content_tag_set');

        // Content marker records.
        $contents[] = new restore_decode_content('uckkarchive_content_marker', [
            'title',
            'summary',
            'description',
            'note',
            'locator',
            'locatorstart',
            'locatorend',
            'locatorlabel',
            'culturalprotocolnote',
            'metadata',
        ], 'uckkarchive_content_marker');

        // Content review records.
        $contents[] = new restore_decode_content('uckkarchive_content_review', [
            'rationale',
            'reviewnote',
            'decisionnote',
            'culturalprotocolnote',
            'metadata',
        ], 'uckkarchive_content_review');

        // External work records.
        $contents[] = new restore_decode_content('uckkarchive_external_work', [
            'title',
            'subtitle',
            'creator',
            'publisher',
            'sourceurl',
            'identifier',
            'citation',
            'rightsstatement',
            'licensekey',
            'sourcenote',
            'teachingnote',
            'culturalprotocolnote',
            'description',
            'metadata',
        ], 'uckkarchive_external_work');

        return $contents;
    }

    /**
     * Define rules for decoding encoded activity links after restore.
     *
     * These tokens should match backup_uckkarchive_activity_task::encode_content_links().
     *
     * @return restore_decode_rule[]
     */
    public static function define_decode_rules(): array {
        $rules = [];

        $rules[] = new restore_decode_rule(
            'UCKKARCHIVEINDEX',
            '/mod/uckkarchive/index.php?id=$1',
            'course'
        );

        $rules[] = new restore_decode_rule(
            'UCKKARCHIVEVIEWBYCMID',
            '/mod/uckkarchive/view.php?id=$1',
            'course_module'
        );

        $rules[] = new restore_decode_rule(
            'UCKKARCHIVEVIEWBYID',
            '/mod/uckkarchive/view.php?a=$1',
            'uckkarchive'
        );

        $rules[] = new restore_decode_rule(
            'UCKKARCHIVEITEMBYCMID',
            '/mod/uckkarchive/item.php?id=$1',
            'course_module'
        );

        $rules[] = new restore_decode_rule(
            'UCKKARCHIVEITEMBYID',
            '/mod/uckkarchive/item.php?itemid=$1',
            'uckkarchive_item'
        );

        $rules[] = new restore_decode_rule(
            'UCKKARCHIVEADDBYCMID',
            '/mod/uckkarchive/add.php?id=$1',
            'course_module'
        );

        $rules[] = new restore_decode_rule(
            'UCKKARCHIVEVALIDATEBYCMID',
            '/mod/uckkarchive/validate.php?id=$1',
            'course_module'
        );

        $rules[] = new restore_decode_rule(
            'UCKKARCHIVEEXPORTBYCMID',
            '/mod/uckkarchive/export.php?id=$1',
            'course_module'
        );

        $rules[] = new restore_decode_rule(
            'UCKKARCHIVEEXPORTBYID',
            '/mod/uckkarchive/export.php?exportid=$1',
            'uckkarchive_export'
        );

        $rules[] = new restore_decode_rule(
            'UCKKARCHIVEMEDIABYCMID',
            '/mod/uckkarchive/media.php?id=$1',
            'course_module'
        );

        $rules[] = new restore_decode_rule(
            'UCKKARCHIVEMEDIABYID',
            '/mod/uckkarchive/media.php?mediaid=$1',
            'uckkarchive_media'
        );

        $rules[] = new restore_decode_rule(
            'UCKKARCHIVEMEDIAVERSIONBYID',
            '/mod/uckkarchive/media.php?versionid=$1',
            'uckkarchive_media_version'
        );

        $rules[] = new restore_decode_rule(
            'UCKKARCHIVEMEDIACOLLECTIONBYID',
            '/mod/uckkarchive/media.php?collectionid=$1',
            'uckkarchive_media_collection'
        );

        $rules[] = new restore_decode_rule(
            'UCKKARCHIVEEXTERNALWORKBYID',
            '/mod/uckkarchive/media.php?externalworkid=$1',
            'uckkarchive_external_work'
        );

        $rules[] = new restore_decode_rule(
            'UCKKARCHIVECONTENTMARKERBYID',
            '/mod/uckkarchive/media.php?contentmarkerid=$1',
            'uckkarchive_content_marker'
        );

        return $rules;
    }

    /**
     * Define legacy activity log restore rules.
     *
     * @return restore_log_rule[]
     */
    public static function define_restore_log_rules(): array {
        $rules = [];

        $rules[] = new restore_log_rule(
            'uckkarchive',
            'add',
            'view.php?id={course_module}',
            '{uckkarchive}'
        );

        $rules[] = new restore_log_rule(
            'uckkarchive',
            'update',
            'view.php?id={course_module}',
            '{uckkarchive}'
        );

        $rules[] = new restore_log_rule(
            'uckkarchive',
            'view',
            'view.php?id={course_module}',
            '{uckkarchive}'
        );

        $rules[] = new restore_log_rule(
            'uckkarchive',
            'add item',
            'add.php?id={course_module}',
            '{uckkarchive_item}'
        );

        $rules[] = new restore_log_rule(
            'uckkarchive',
            'view item',
            'item.php?id={course_module}&itemid={uckkarchive_item}',
            '{uckkarchive_item}'
        );

        $rules[] = new restore_log_rule(
            'uckkarchive',
            'validate item',
            'validate.php?id={course_module}&itemid={uckkarchive_item}',
            '{uckkarchive_item}'
        );

        $rules[] = new restore_log_rule(
            'uckkarchive',
            'revise item',
            'item.php?id={course_module}&itemid={uckkarchive_item}',
            '{uckkarchive_rev}'
        );

        $rules[] = new restore_log_rule(
            'uckkarchive',
            'export',
            'export.php?id={course_module}',
            '{uckkarchive_export}'
        );

        $rules[] = new restore_log_rule(
            'uckkarchive',
            'view media',
            'media.php?id={course_module}&mediaid={uckkarchive_media}',
            '{uckkarchive_media}'
        );

        $rules[] = new restore_log_rule(
            'uckkarchive',
            'add media',
            'media.php?id={course_module}',
            '{uckkarchive_media}'
        );

        $rules[] = new restore_log_rule(
            'uckkarchive',
            'update media',
            'media.php?id={course_module}&mediaid={uckkarchive_media}',
            '{uckkarchive_media}'
        );

        $rules[] = new restore_log_rule(
            'uckkarchive',
            'delete media',
            'media.php?id={course_module}',
            '{uckkarchive_media}'
        );

        $rules[] = new restore_log_rule(
            'uckkarchive',
            'version media',
            'media.php?id={course_module}&mediaid={uckkarchive_media}',
            '{uckkarchive_media_version}'
        );

        $rules[] = new restore_log_rule(
            'uckkarchive',
            'export media',
            'export.php?id={course_module}',
            '{uckkarchive_export}'
        );

        $rules[] = new restore_log_rule(
            'uckkarchive',
            'create media collection',
            'media.php?id={course_module}&collectionid={uckkarchive_media_collection}',
            '{uckkarchive_media_collection}'
        );

        $rules[] = new restore_log_rule(
            'uckkarchive',
            'create content marker',
            'media.php?id={course_module}&contentmarkerid={uckkarchive_content_marker}',
            '{uckkarchive_content_marker}'
        );

        $rules[] = new restore_log_rule(
            'uckkarchive',
            'review content marker',
            'media.php?id={course_module}&contentmarkerid={uckkarchive_content_marker}',
            '{uckkarchive_content_review}'
        );

        $rules[] = new restore_log_rule(
            'uckkarchive',
            'create external work',
            'media.php?id={course_module}&externalworkid={uckkarchive_external_work}',
            '{uckkarchive_external_work}'
        );

        return $rules;
    }

    /**
     * Define legacy course-level log restore rules.
     *
     * @return restore_log_rule[]
     */
    public static function define_restore_log_rules_for_course(): array {
        $rules = [];

        $rules[] = new restore_log_rule(
            'uckkarchive',
            'view all',
            'index.php?id={course}',
            null
        );

        return $rules;
    }

    /**
     * Return file areas used by the activity.
     *
     * Actual file restoration is performed by the restore structure step. These
     * names must stay aligned with mod_uckkarchive_pluginfile(), backup steps,
     * restore steps, privacy provider, file_area_registry, and tests.
     *
     * @return string[]
     */
    public function get_fileareas(): array {
        return [
            'intro',

            // Archive file areas.
            'item_content',
            'item_publicsummary',
            'item_files',
            'proof_files',
            'decision_attachments',
            'minutes_files',
            'kristal_files',
            'portfolio_files',
            'integrity_exports',
            'provenance_files',
            'validation_files',
            'revision_files',

            // Media file areas.
            'media_original',
            'media_preview',
            'media_thumbnail',
            'media_derivative',
            'media_caption',
            'media_transcript',
            'media_attachment',

            // Content advisory and external-work file areas.
            'content_review_files',
            'external_work_reference_files',
            'cultural_protocol_files',

            // Export file areas.
            'export_package',
            'export_manifest',
        ];
    }

    /**
     * Return encoded config-data attributes.
     *
     * @return string[]
     */
    public function get_configdata_encoded_attributes(): array {
        return [];
    }
}