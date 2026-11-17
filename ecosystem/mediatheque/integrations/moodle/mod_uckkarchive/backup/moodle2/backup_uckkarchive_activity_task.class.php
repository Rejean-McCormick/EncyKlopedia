<?php
// This file is part of Moodle - https://moodle.org/
//
// Moodle is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// any later version.

/**
 * Backup task for the UCKK Archive activity.
 *
 * @package    mod_uckkarchive
 * @copyright  2026 Univers-Cité King Klown
 * @license    https://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later
 */

defined('MOODLE_INTERNAL') || die();

require_once($CFG->dirroot . '/backup/moodle2/backup_activity_task.class.php');
require_once($CFG->dirroot . '/mod/uckkarchive/backup/moodle2/backup_uckkarchive_stepslib.php');

/**
 * Backup task for mod_uckkarchive.
 *
 * This class wires the Archive activity into Moodle backup. Detailed table
 * structure belongs in backup_uckkarchive_activity_structure_step.
 *
 * UCKK Archive owns archive items, proof packages, Kristals, provenance,
 * revisions, exports, validation state, media/didactic material, external
 * work references, content advisories, cultural protocol notes, and restricted
 * archive metadata.
 */
class backup_uckkarchive_activity_task extends backup_activity_task {
    /**
     * Define activity-specific backup settings.
     *
     * The Archive activity currently relies on Moodle's standard activity
     * backup settings: activity inclusion, user data, files, groups,
     * completion, and gradebook where applicable.
     *
     * @return void
     */
    protected function define_my_settings(): void {
        // No custom backup settings.
    }

    /**
     * Define backup steps.
     *
     * @return void
     */
    protected function define_my_steps(): void {
        $this->add_step(new backup_uckkarchive_activity_structure_step(
            'uckkarchive_structure',
            'uckkarchive.xml'
        ));
    }

    /**
     * Return file areas used by this activity.
     *
     * These names must match the component/filearea values used by lib.php,
     * controllers, forms, output classes, services, revision services, export
     * services, privacy provider, restore steps, and pluginfile handling.
     *
     * @return array<int, string>
     */
    public function get_fileareas(): array {
        return [
            // Moodle activity intro.
            'intro',

            // Archive item text/file areas.
            'item_content',
            'item_publicsummary',
            'item_files',
            'item_attachment',

            // Canonical archive domain file areas.
            'proof_files',
            'decision_attachments',
            'minutes_files',
            'kristal_files',
            'portfolio_files',
            'integrity_exports',

            // Provenance, validation, and revision support.
            'provenance_files',
            'validation_files',
            'revision_files',

            // Media library file areas.
            'media_original',
            'media_preview',
            'media_thumbnail',
            'media_derivative',
            'media_caption',
            'media_transcript',
            'media_attachment',

            // Content advisory / cultural protocol support.
            'content_review_files',
            'content_marker_files',
            'content_tag_files',
            'cultural_protocol_files',

            // External work reference support.
            'external_work_reference_files',

            // Export package storage.
            'export_package',
            'export_manifest',
        ];
    }

    /**
     * Return config-data attributes requiring link encoding.
     *
     * Activity modules normally store rich content in owned tables rather than
     * instance config attributes. Table content link encoding is handled by
     * encode_content_links().
     *
     * @return array<int, string>
     */
    public function get_configdata_encoded_attributes(): array {
        return [];
    }

    /**
     * Encode links to this activity inside backed-up content.
     *
     * These tokens are decoded by the matching restore task. They keep internal
     * Archive links portable across backup and restore.
     *
     * @param string $content Content to encode.
     * @return string Encoded content.
     */
    public static function encode_content_links($content): string {
        global $CFG;

        $base = preg_quote($CFG->wwwroot, '/');

        // Course-level archive index links.
        $search = '/(' . $base . '\/mod\/uckkarchive\/index\.php\?id=)([0-9]+)/';
        $content = preg_replace($search, '$@UCKKARCHIVEINDEX*$2@$', $content);

        // Main activity view links by course module id.
        $search = '/(' . $base . '\/mod\/uckkarchive\/view\.php\?id=)([0-9]+)/';
        $content = preg_replace($search, '$@UCKKARCHIVEVIEWBYCMID*$2@$', $content);

        // Main activity view links by archive instance id.
        $search = '/(' . $base . '\/mod\/uckkarchive\/view\.php\?a=)([0-9]+)/';
        $content = preg_replace($search, '$@UCKKARCHIVEVIEWBYID*$2@$', $content);

        // Archive item links by course module id and item id.
        $search = '/(' . $base . '\/mod\/uckkarchive\/item\.php\?id=)([0-9]+)(&amp;|&)itemid=([0-9]+)/';
        $content = preg_replace($search, '$@UCKKARCHIVEITEMBYCMID*$2*$4@$', $content);

        // Archive item links by archive instance id and item id.
        $search = '/(' . $base . '\/mod\/uckkarchive\/item\.php\?a=)([0-9]+)(&amp;|&)itemid=([0-9]+)/';
        $content = preg_replace($search, '$@UCKKARCHIVEITEMBYID*$2*$4@$', $content);

        // Validation panel/controller links.
        $search = '/(' . $base . '\/mod\/uckkarchive\/validate\.php\?id=)([0-9]+)(&amp;|&)itemid=([0-9]+)/';
        $content = preg_replace($search, '$@UCKKARCHIVEVALIDATEBYCMID*$2*$4@$', $content);

        // Revision controller links.
        $search = '/(' . $base . '\/mod\/uckkarchive\/revise\.php\?id=)([0-9]+)(&amp;|&)itemid=([0-9]+)/';
        $content = preg_replace($search, '$@UCKKARCHIVEREVISEBYCMID*$2*$4@$', $content);

        // Export controller links by course module id.
        $search = '/(' . $base . '\/mod\/uckkarchive\/export\.php\?id=)([0-9]+)/';
        $content = preg_replace($search, '$@UCKKARCHIVEEXPORTBYCMID*$2@$', $content);

        // Export package links by course module id and export id.
        $search = '/(' . $base . '\/mod\/uckkarchive\/export\.php\?id=)([0-9]+)(&amp;|&)exportid=([0-9]+)/';
        $content = preg_replace($search, '$@UCKKARCHIVEEXPORTPACKAGEBYCMID*$2*$4@$', $content);

        // Media library controller links by course module id.
        $search = '/(' . $base . '\/mod\/uckkarchive\/media\.php\?id=)([0-9]+)/';
        $content = preg_replace($search, '$@UCKKARCHIVEMEDIABYCMID*$2@$', $content);

        // Media item links by course module id and media id.
        $search = '/(' . $base . '\/mod\/uckkarchive\/media\.php\?id=)([0-9]+)(&amp;|&)mediaid=([0-9]+)/';
        $content = preg_replace($search, '$@UCKKARCHIVEMEDIAITEMBYCMID*$2*$4@$', $content);

        // Media collection links by course module id and collection id.
        $search = '/(' . $base . '\/mod\/uckkarchive\/media\.php\?id=)([0-9]+)(&amp;|&)collectionid=([0-9]+)/';
        $content = preg_replace($search, '$@UCKKARCHIVEMEDIACOLLECTIONBYCMID*$2*$4@$', $content);

        // Media version links by course module id, media id, and version id.
        $search = '/(' . $base . '\/mod\/uckkarchive\/media\.php\?id=)([0-9]+)(&amp;|&)mediaid=([0-9]+)(&amp;|&)versionid=([0-9]+)/';
        $content = preg_replace($search, '$@UCKKARCHIVEMEDIAVERSIONBYCMID*$2*$4*$6@$', $content);

        // External work links by course module id and external work id.
        $search = '/(' . $base . '\/mod\/uckkarchive\/media\.php\?id=)([0-9]+)(&amp;|&)externalworkid=([0-9]+)/';
        $content = preg_replace($search, '$@UCKKARCHIVEEXTERNALWORKBYCMID*$2*$4@$', $content);

        // Content marker links by course module id and marker id.
        $search = '/(' . $base . '\/mod\/uckkarchive\/media\.php\?id=)([0-9]+)(&amp;|&)contentmarkerid=([0-9]+)/';
        $content = preg_replace($search, '$@UCKKARCHIVECONTENTMARKERBYCMID*$2*$4@$', $content);

        // Content advisory panel links by course module id and media id.
        $search = '/(' . $base . '\/mod\/uckkarchive\/media\.php\?id=)([0-9]+)(&amp;|&)mediaid=([0-9]+)(&amp;|&)panel=contentadvisory/';
        $content = preg_replace($search, '$@UCKKARCHIVECONTENTADVISORYBYCMID*$2*$4@$', $content);

        return $content;
    }
}