<?php
// This file is part of Moodle - https://moodle.org/
//
// Moodle is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// any later version.

/**
 * Create an export request for selected media objects.
 *
 * @package    mod_uckkarchive
 * @copyright  2026 Univers-Cité King Klown
 * @license    https://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later
 */

namespace mod_uckkarchive\external;

defined('MOODLE_INTERNAL') || die();

global $CFG;
require_once($CFG->libdir . '/externallib.php');
require_once($CFG->libdir . '/filelib.php');
require_once(dirname(__DIR__, 2) . '/locallib.php');

use context_module;
use core_external\external_api;
use core_external\external_function_parameters;
use core_external\external_multiple_structure;
use core_external\external_single_structure;
use core_external\external_value;
use invalid_parameter_exception;
use moodle_exception;
use moodle_url;
use stdClass;

/**
 * Create an export request for selected media objects.
 *
 * Target service:
 *
 * ```text
 * mod_uckkarchive_export_media
 * ```
 *
 * The service creates an export record and a safe `manifest.json` file.
 * Heavy export package generation remains the responsibility of the export
 * task / package generator.
 */
class export_media extends external_api {
    /** Media table. */
    private const MEDIA_TABLE = 'uckkarchive_media';

    /** Media version table. */
    private const MEDIA_VERSION_TABLE = 'uckkarchive_media_version';

    /** Media relation table. */
    private const MEDIA_RELATION_TABLE = 'uckkarchive_media_relation';

    /** Media tag table. */
    private const MEDIA_TAG_TABLE = 'uckkarchive_media_tag';

    /** Content marker table. */
    private const CONTENT_MARKER_TABLE = 'uckkarchive_content_marker';

    /** External work table. */
    private const EXTERNAL_WORK_TABLE = 'uckkarchive_external_work';

    /** Export table. */
    private const EXPORT_TABLE = 'uckkarchive_export';

    /** File component. */
    private const COMPONENT = 'mod_uckkarchive';

    /** Manifest file area. */
    private const MANIFEST_FILEAREA = 'export_manifest';

    /** Package file area. */
    private const PACKAGE_FILEAREA = 'export_package';

    /**
     * Load the page context.
     *
     * @param int $cmid Course module id.
     * @return array{0:stdClass,1:stdClass,2:stdClass,3:context_module}
     */
    protected static function load_page(int $cmid): array {
        [$course, $cm, $archive, $context] = \uckkarchive_require_page($cmid, 0);
        return [$course, $cm, $archive, $context];
    }

    /**
     * Define service parameters.
     *
     * @return external_function_parameters
     */
    public static function execute_parameters(): external_function_parameters {
        return new external_function_parameters([
            'cmid' => new external_value(PARAM_INT, 'Course module id'),
            'mediaids' => new external_multiple_structure(
                new external_value(PARAM_INT, 'Media id'),
                'Selected media ids'
            ),
            'format' => new external_value(PARAM_ALPHANUMEXT, 'Export format', VALUE_DEFAULT, 'zip'),
            'options' => new external_single_structure([
                'includeoriginals' => new external_value(PARAM_BOOL, 'Include original files', VALUE_DEFAULT, true),
                'includederivatives' => new external_value(PARAM_BOOL, 'Include derivative files', VALUE_DEFAULT, true),
                'includethumbnails' => new external_value(PARAM_BOOL, 'Include thumbnails', VALUE_DEFAULT, true),
                'includepreviews' => new external_value(PARAM_BOOL, 'Include previews', VALUE_DEFAULT, true),
                'includecaptions' => new external_value(PARAM_BOOL, 'Include captions', VALUE_DEFAULT, true),
                'includetranscripts' => new external_value(PARAM_BOOL, 'Include transcripts', VALUE_DEFAULT, true),
                'includeattachments' => new external_value(PARAM_BOOL, 'Include media attachments', VALUE_DEFAULT, true),
                'includeversions' => new external_value(PARAM_BOOL, 'Include media versions', VALUE_DEFAULT, true),
                'includerelations' => new external_value(PARAM_BOOL, 'Include media relations', VALUE_DEFAULT, true),
                'includetags' => new external_value(PARAM_BOOL, 'Include media tags', VALUE_DEFAULT, true),
                'includeadvisories' => new external_value(PARAM_BOOL, 'Include content advisories', VALUE_DEFAULT, true),
                'includeexternalrefs' => new external_value(PARAM_BOOL, 'Include external work references', VALUE_DEFAULT, true),
                'redactionlevel' => new external_value(PARAM_ALPHANUMEXT, 'Redaction level', VALUE_DEFAULT, 'standard'),
                'visibility' => new external_value(PARAM_ALPHANUMEXT, 'Export visibility', VALUE_DEFAULT, 'private'),
            ], 'Export options', VALUE_DEFAULT, []),
            'reason' => new external_value(PARAM_RAW, 'Export reason', VALUE_DEFAULT, ''),
        ]);
    }

    /**
     * Execute the service.
     *
     * @param int $cmid Course module id.
     * @param int[] $mediaids Selected media ids.
     * @param string $format Export format.
     * @param array<string, mixed> $options Export options.
     * @param string $reason Export reason.
     * @return array<string, mixed>
     */
    public static function execute(
        int $cmid,
        array $mediaids,
        string $format = 'zip',
        array $options = [],
        string $reason = ''
    ): array {
        global $DB, $USER;

        $params = self::validate_parameters(self::execute_parameters(), [
            'cmid' => $cmid,
            'mediaids' => $mediaids,
            'format' => $format,
            'options' => $options,
            'reason' => $reason,
        ]);

        [$course, $cm, $archive, $context] = self::load_page((int)$params['cmid']);
        self::validate_context($context);

        require_capability('mod/uckkarchive:export', $context);
        require_capability('mod/uckkarchive:exportmedia', $context);

        self::require_table(self::EXPORT_TABLE);

        $warnings = [];
        $format = self::normalise_format((string)$params['format']);
        $options = self::normalise_options((array)$params['options']);
        $reason = self::normalise_text((string)$params['reason']);

        $mediaids = self::normalise_ids((array)$params['mediaids']);
        if (empty($mediaids)) {
            throw new invalid_parameter_exception('At least one media id is required.');
        }

        if (!self::table_exists(self::MEDIA_TABLE)) {
            throw new moodle_exception('missingtable', 'error', '', self::MEDIA_TABLE);
        }

        $allowed = [];
        $excluded = [];
        $redacted = [];

        foreach ($mediaids as $mediaid) {
            $media = self::get_media_record($mediaid, (int)$archive->id);

            if (!$media) {
                $excluded[] = self::excluded($mediaid, 'notfound', 'Media record not found.');
                continue;
            }

            if (!self::can_export_media_record($context, $media)) {
                $excluded[] = self::excluded($mediaid, 'noexportpermission', 'Current user cannot export this media.');
                continue;
            }

            if (self::is_restricted_media($media) && !has_capability('mod/uckkarchive:viewrestrictedmedia', $context)) {
                $excluded[] = self::excluded($mediaid, 'restrictedmedia', 'Restricted media requires restricted media authority.');
                continue;
            }

            if (self::is_culturally_restricted_media($media) &&
                    !has_capability('mod/uckkarchive:viewculturallyrestricted', $context)) {
                $excluded[] = self::excluded($mediaid, 'culturalrestriction', 'Culturally restricted media requires cultural access authority.');
                continue;
            }

            $allowed[] = $media;

            if (self::is_restricted_media($media) || self::is_culturally_restricted_media($media)) {
                $redacted[] = (int)$media->id;
            }
        }

        if (empty($allowed)) {
            throw new moodle_exception('nopermissions', 'error', '', null, 'No selected media can be exported.');
        }

        $now = time();
        $exportuuid = self::generate_uuid();
        $manifest = self::build_manifest(
            $archive,
            $course,
            $cm,
            $context,
            $allowed,
            $excluded,
            $redacted,
            $format,
            $options,
            $reason,
            $exportuuid,
            $now
        );

        $record = self::build_export_record(
            $archive,
            $course,
            $cm,
            $context,
            $USER,
            $allowed,
            $excluded,
            $redacted,
            $format,
            $options,
            $reason,
            $exportuuid,
            $manifest,
            $now
        );

        $exportid = (int)$DB->insert_record(self::EXPORT_TABLE, self::filter_record_for_table(self::EXPORT_TABLE, $record));

        $manifesturl = self::write_manifest_file($context, $exportid, $manifest, (int)$USER->id);

        self::trigger_media_export_events($allowed, $context, $archive, $course, $cm, $exportid, $format);

        if (!empty($excluded)) {
            $warnings[] = self::warning('media', 0, 'partialexport', count($excluded) . ' selected media records were excluded.');
        }

        return [
            'exportid' => $exportid,
            'exportuuid' => $exportuuid,
            'state' => $record->status,
            'mediaexported' => count($allowed),
            'mediaexcluded' => count($excluded),
            'redactedcount' => count($redacted),
            'manifest' => self::encode_json($manifest),
            'downloadurl' => '',
            'manifesturl' => $manifesturl,
            'warnings' => $warnings,
        ];
    }

    /**
     * Define service returns.
     *
     * @return external_single_structure
     */
    public static function execute_returns(): external_single_structure {
        return new external_single_structure([
            'exportid' => new external_value(PARAM_INT, 'Export id'),
            'exportuuid' => new external_value(PARAM_TEXT, 'Export UUID'),
            'state' => new external_value(PARAM_ALPHANUMEXT, 'Export state'),
            'mediaexported' => new external_value(PARAM_INT, 'Number of media records included'),
            'mediaexcluded' => new external_value(PARAM_INT, 'Number of selected media records excluded'),
            'redactedcount' => new external_value(PARAM_INT, 'Number of media records requiring redaction/restricted handling'),
            'manifest' => new external_value(PARAM_RAW, 'Manifest JSON'),
            'downloadurl' => new external_value(PARAM_RAW, 'Package download URL when ready'),
            'manifesturl' => new external_value(PARAM_RAW, 'Manifest file URL'),
            'warnings' => new external_multiple_structure(
                new external_single_structure([
                    'item' => new external_value(PARAM_TEXT, 'Warning item'),
                    'itemid' => new external_value(PARAM_INT, 'Warning item id'),
                    'warningcode' => new external_value(PARAM_ALPHANUMEXT, 'Warning code'),
                    'message' => new external_value(PARAM_TEXT, 'Warning message'),
                ])
            ),
        ]);
    }

    /**
     * Build export record for uckkarchive_export.
     *
     * @param stdClass $archive Archive instance.
     * @param stdClass $course Course.
     * @param stdClass $cm Course module.
     * @param context_module $context Context.
     * @param stdClass $user User.
     * @param stdClass[] $allowed Allowed media.
     * @param array<int, array<string, mixed>> $excluded Excluded items.
     * @param int[] $redacted Redacted media ids.
     * @param string $format Format.
     * @param array<string, mixed> $options Options.
     * @param string $reason Reason.
     * @param string $exportuuid Export UUID.
     * @param array<string, mixed> $manifest Manifest.
     * @param int $now Timestamp.
     * @return stdClass
     */
    protected static function build_export_record(
        stdClass $archive,
        stdClass $course,
        stdClass $cm,
        context_module $context,
        stdClass $user,
        array $allowed,
        array $excluded,
        array $redacted,
        string $format,
        array $options,
        string $reason,
        string $exportuuid,
        array $manifest,
        int $now
    ): stdClass {
        $record = new stdClass();
        $record->archiveid = (int)$archive->id;
        $record->courseid = (int)$course->id;
        $record->cmid = (int)$cm->id;
        $record->contextid = (int)$context->id;
        $record->userid = (int)$user->id;
        $record->exportscope = 'media_items';
        $record->exportformat = $format;
        $record->packagename = 'uckkarchive-media-' . $archive->id . '-' . $now;
        $record->description = 'Media export request';
        $record->itemids = self::encode_json(array_values(array_map(static fn(stdClass $media): int => (int)$media->id, $allowed)));
        $record->reason = $reason;
        $record->auditnote = 'Created by external export_media service';
        $record->redactionlevel = $options['redactionlevel'];
        $record->redacted = !empty($redacted) || $options['redactionlevel'] !== 'none' ? 1 : 0;
        $record->includefiles = self::includes_any_file_area($options) ? 1 : 0;
        $record->includeproofs = 0;
        $record->includeprovenance = 1;
        $record->includeversions = !empty($options['includeversions']) ? 1 : 0;
        $record->fileitemid = null;
        $record->downloadcount = 0;
        $record->lastdownloaded = null;
        $record->timequeued = $now;
        $record->timestarted = null;
        $record->timecompleted = null;
        $record->error = null;
        $record->status = 'pending';
        $record->visibility = $options['visibility'];
        $record->versionno = 1;
        $record->provenancehash = hash('sha256', self::encode_json($manifest));
        $record->integritycaseid = null;
        $record->createdby = (int)$user->id;
        $record->modifiedby = (int)$user->id;
        $record->timecreated = $now;
        $record->timemodified = $now;
        $record->metadata = self::encode_json([
            'service' => 'mod_uckkarchive_export_media',
            'exportuuid' => $exportuuid,
            'mediaids' => array_values(array_map(static fn(stdClass $media): int => (int)$media->id, $allowed)),
            'excluded' => $excluded,
            'redactedmediaids' => array_values($redacted),
            'options' => $options,
            'manifest' => $manifest,
        ]);

        return $record;
    }

    /**
     * Build export manifest.
     *
     * @param stdClass $archive Archive instance.
     * @param stdClass $course Course.
     * @param stdClass $cm Course module.
     * @param context_module $context Context.
     * @param stdClass[] $mediarecords Allowed media records.
     * @param array<int, array<string, mixed>> $excluded Excluded media.
     * @param int[] $redacted Redacted media ids.
     * @param string $format Format.
     * @param array<string, mixed> $options Options.
     * @param string $reason Reason.
     * @param string $exportuuid Export UUID.
     * @param int $now Timestamp.
     * @return array<string, mixed>
     */
    protected static function build_manifest(
        stdClass $archive,
        stdClass $course,
        stdClass $cm,
        context_module $context,
        array $mediarecords,
        array $excluded,
        array $redacted,
        string $format,
        array $options,
        string $reason,
        string $exportuuid,
        int $now
    ): array {
        $media = [];

        foreach ($mediarecords as $record) {
            $media[] = self::manifest_media_entry($record, $context, $options);
        }

        return [
            'manifest_version' => 1,
            'plugin' => 'mod_uckkarchive',
            'export_type' => 'media_items',
            'export_uuid' => $exportuuid,
            'export_format' => $format,
            'export_timestamp' => $now,
            'export_actor' => [
                'userid' => (int)$GLOBALS['USER']->id,
            ],
            'reason' => $reason,
            'archive' => [
                'id' => (int)$archive->id,
                'courseid' => (int)$course->id,
                'cmid' => (int)$cm->id,
                'contextid' => (int)$context->id,
            ],
            'options' => $options,
            'counts' => [
                'media_included' => count($mediarecords),
                'media_excluded' => count($excluded),
                'redacted' => count($redacted),
            ],
            'media' => $media,
            'excluded' => $excluded,
        ];
    }

    /**
     * Build one manifest media entry.
     *
     * @param stdClass $media Media record.
     * @param context_module $context Context.
     * @param array<string, mixed> $options Options.
     * @return array<string, mixed>
     */
    protected static function manifest_media_entry(stdClass $media, context_module $context, array $options): array {
        $restricted = self::is_restricted_media($media);
        $cultural = self::is_culturally_restricted_media($media);

        $entry = [
            'id' => (int)$media->id,
            'uuid' => (string)self::field($media, ['uuid'], ''),
            'title' => (string)self::field($media, ['title', 'name'], ''),
            'mediatype' => (string)self::field($media, ['mediatype', 'type'], ''),
            'mimetype' => (string)self::field($media, ['mimetype', 'mime'], ''),
            'status' => (string)self::field($media, ['status'], ''),
            'visibility' => (string)self::field($media, ['visibility'], ''),
            'audiencesuitability' => (string)self::field($media, ['audiencesuitability'], ''),
            'source' => (string)self::field($media, ['source', 'sourcetype'], ''),
            'timecreated' => (int)self::field($media, ['timecreated'], 0),
            'timemodified' => (int)self::field($media, ['timemodified'], 0),
            'restricted' => $restricted,
            'culturalprotocol' => $cultural,
            'redacted' => $restricted || $cultural || $options['redactionlevel'] !== 'none',
            'files' => self::manifest_file_entries($media, $context, $options),
        ];

        if (!empty($options['includeversions'])) {
            $entry['versions'] = self::manifest_versions((int)$media->id);
        }

        if (!empty($options['includerelations'])) {
            $entry['relations'] = self::manifest_relations((int)$media->id);
        }

        if (!empty($options['includetags'])) {
            $entry['tags'] = self::manifest_tags((int)$media->id);
        }

        if (!empty($options['includeadvisories'])) {
            $entry['content_markers'] = self::manifest_content_markers((int)$media->id, $options);
        }

        return $entry;
    }

    /**
     * Return manifest file entries.
     *
     * @param stdClass $media Media record.
     * @param context_module $context Context.
     * @param array<string, mixed> $options Options.
     * @return array<int, array<string, mixed>>
     */
    protected static function manifest_file_entries(stdClass $media, context_module $context, array $options): array {
        $areas = [
            'media_original' => 'includeoriginals',
            'media_preview' => 'includepreviews',
            'media_thumbnail' => 'includethumbnails',
            'media_derivative' => 'includederivatives',
            'media_caption' => 'includecaptions',
            'media_transcript' => 'includetranscripts',
            'media_attachment' => 'includeattachments',
        ];

        $files = [];

        foreach ($areas as $area => $option) {
            if (empty($options[$option])) {
                continue;
            }

            if (!self::can_download_area($context, $media, $area)) {
                $files[] = [
                    'filearea' => $area,
                    'included' => false,
                    'redacted' => true,
                    'reason' => 'download_not_allowed',
                ];
                continue;
            }

            foreach (self::get_area_files($context, $area, (int)$media->id) as $file) {
                $files[] = [
                    'filearea' => $area,
                    'filename' => $file->get_filename(),
                    'filepath' => $file->get_filepath(),
                    'filesize' => $file->get_filesize(),
                    'mimetype' => $file->get_mimetype(),
                    'contenthash' => $file->get_contenthash(),
                    'included' => true,
                    'redacted' => false,
                ];
            }
        }

        return $files;
    }

    /**
     * Return media version manifest entries.
     *
     * @param int $mediaid Media id.
     * @return array<int, array<string, mixed>>
     */
    protected static function manifest_versions(int $mediaid): array {
        global $DB;

        if (!self::table_exists(self::MEDIA_VERSION_TABLE)) {
            return [];
        }

        $columns = self::columns(self::MEDIA_VERSION_TABLE);
        $mediafield = self::first_column($columns, ['mediaid']);
        if ($mediafield === null) {
            return [];
        }

        $records = $DB->get_records(self::MEDIA_VERSION_TABLE, [$mediafield => $mediaid], 'versionno ASC, id ASC');
        $versions = [];

        foreach ($records as $record) {
            $versions[] = [
                'id' => (int)$record->id,
                'uuid' => (string)self::field($record, ['uuid'], ''),
                'versionno' => (int)self::field($record, ['versionno'], 0),
                'status' => (string)self::field($record, ['status'], ''),
                'filearea' => (string)self::field($record, ['filearea'], ''),
                'filename' => (string)self::field($record, ['filename'], ''),
                'contenthash' => (string)self::field($record, ['contenthash', 'filehash'], ''),
                'timecreated' => (int)self::field($record, ['timecreated'], 0),
            ];
        }

        return $versions;
    }

    /**
     * Return media relation manifest entries.
     *
     * @param int $mediaid Media id.
     * @return array<int, array<string, mixed>>
     */
    protected static function manifest_relations(int $mediaid): array {
        global $DB;

        if (!self::table_exists(self::MEDIA_RELATION_TABLE)) {
            return [];
        }

        $columns = self::columns(self::MEDIA_RELATION_TABLE);
        $sourcefield = self::first_column($columns, ['mediaid', 'sourcemediaid', 'sourceid']);
        if ($sourcefield === null) {
            return [];
        }

        $records = $DB->get_records(self::MEDIA_RELATION_TABLE, [$sourcefield => $mediaid], 'id ASC');
        $relations = [];

        foreach ($records as $record) {
            $relations[] = [
                'id' => (int)$record->id,
                'uuid' => (string)self::field($record, ['uuid'], ''),
                'type' => (string)self::field($record, ['relationtype', 'type'], ''),
                'targetid' => (int)self::field($record, ['targetid', 'targetmediaid'], 0),
                'targettype' => (string)self::field($record, ['targettype'], ''),
            ];
        }

        return $relations;
    }

    /**
     * Return media tag manifest entries.
     *
     * @param int $mediaid Media id.
     * @return array<int, array<string, mixed>>
     */
    protected static function manifest_tags(int $mediaid): array {
        global $DB;

        if (!self::table_exists(self::MEDIA_TAG_TABLE)) {
            return [];
        }

        $columns = self::columns(self::MEDIA_TAG_TABLE);
        $mediafield = self::first_column($columns, ['mediaid', 'itemid']);
        if ($mediafield === null) {
            return [];
        }

        $records = $DB->get_records(self::MEDIA_TAG_TABLE, [$mediafield => $mediaid], 'id ASC');
        $tags = [];

        foreach ($records as $record) {
            $tags[] = [
                'id' => (int)$record->id,
                'tag' => (string)self::field($record, ['tag', 'tagkey', 'name', 'rawname'], ''),
                'type' => (string)self::field($record, ['tagtype', 'type'], ''),
            ];
        }

        return $tags;
    }

    /**
     * Return content marker manifest entries.
     *
     * @param int $mediaid Media id.
     * @param array<string, mixed> $options Options.
     * @return array<int, array<string, mixed>>
     */
    protected static function manifest_content_markers(int $mediaid, array $options): array {
        global $DB;

        if (!self::table_exists(self::CONTENT_MARKER_TABLE)) {
            return [];
        }

        $columns = self::columns(self::CONTENT_MARKER_TABLE);
        $mediafield = self::first_column($columns, ['mediaid']);
        if ($mediafield === null) {
            return [];
        }

        $records = $DB->get_records(self::CONTENT_MARKER_TABLE, [$mediafield => $mediaid], 'id ASC');
        $markers = [];

        foreach ($records as $record) {
            $restricted = !empty($record->restricted) || (string)self::field($record, ['visibility'], '') === 'restricted_cultural';
            $redact = $restricted && $options['redactionlevel'] !== 'none';

            $markers[] = [
                'id' => (int)$record->id,
                'uuid' => (string)self::field($record, ['uuid'], ''),
                'tag' => (string)self::field($record, ['tag', 'tagkey', 'contenttag', 'advisorytag'], ''),
                'locator_type' => (string)self::field($record, ['locatortype'], ''),
                'locator' => $redact ? '' : (string)self::field($record, ['locator', 'locatorvalue'], ''),
                'severity' => (string)self::field($record, ['severity'], ''),
                'audiencesuitability' => (string)self::field($record, ['audiencesuitability'], ''),
                'redacted' => $redact,
            ];
        }

        return $markers;
    }

    /**
     * Get one media record belonging to archive.
     *
     * @param int $mediaid Media id.
     * @param int $archiveid Archive id.
     * @return stdClass|null
     */
    protected static function get_media_record(int $mediaid, int $archiveid): ?stdClass {
        global $DB;

        $mediaid = max(0, $mediaid);
        if ($mediaid <= 0 || !self::table_exists(self::MEDIA_TABLE)) {
            return null;
        }

        $record = $DB->get_record(self::MEDIA_TABLE, ['id' => $mediaid], '*', IGNORE_MISSING);
        if (!$record) {
            return null;
        }

        $recordarchiveid = (int)self::field($record, ['archiveid', 'uckkarchiveid'], 0);
        if ($recordarchiveid > 0 && $recordarchiveid !== $archiveid) {
            return null;
        }

        return $record;
    }

    /**
     * Return whether the current user can export media.
     *
     * @param context_module $context Context.
     * @param stdClass $media Media record.
     * @return bool
     */
    protected static function can_export_media_record(context_module $context, stdClass $media): bool {
        if (class_exists('\\mod_uckkarchive\\local\\media_policy') &&
                method_exists('\\mod_uckkarchive\\local\\media_policy', 'can_export_media')) {
            return \mod_uckkarchive\local\media_policy::can_export_media($context, $media);
        }

        return has_capability('mod/uckkarchive:exportmedia', $context);
    }

    /**
     * Return whether current user can download a media area.
     *
     * @param context_module $context Context.
     * @param stdClass $media Media.
     * @param string $filearea File area.
     * @return bool
     */
    protected static function can_download_area(context_module $context, stdClass $media, string $filearea): bool {
        if (class_exists('\\mod_uckkarchive\\local\\media_policy') &&
                method_exists('\\mod_uckkarchive\\local\\media_policy', 'can_download_filearea')) {
            return \mod_uckkarchive\local\media_policy::can_download_filearea($context, $media, $filearea);
        }

        return has_capability('mod/uckkarchive:downloadmedia', $context);
    }

    /**
     * Return files from one area.
     *
     * @param context_module $context Context.
     * @param string $filearea File area.
     * @param int $itemid Item id.
     * @return stored_file[]
     */
    protected static function get_area_files(context_module $context, string $filearea, int $itemid): array {
        $fs = get_file_storage();
        $files = $fs->get_area_files(
            (int)$context->id,
            self::COMPONENT,
            $filearea,
            $itemid,
            'filename',
            false
        );

        return array_values(array_filter($files, static fn($file): bool => !$file->is_directory()));
    }

    /**
     * Write manifest JSON into Moodle File API.
     *
     * @param context_module $context Context.
     * @param int $exportid Export id.
     * @param array<string, mixed> $manifest Manifest.
     * @param int $userid User id.
     * @return string Manifest URL.
     */
    protected static function write_manifest_file(context_module $context, int $exportid, array $manifest, int $userid): string {
        $fs = get_file_storage();
        $fs->delete_area_files((int)$context->id, self::COMPONENT, self::MANIFEST_FILEAREA, $exportid);

        $record = [
            'contextid' => (int)$context->id,
            'component' => self::COMPONENT,
            'filearea' => self::MANIFEST_FILEAREA,
            'itemid' => $exportid,
            'filepath' => '/',
            'filename' => 'manifest.json',
            'userid' => $userid,
        ];

        $file = $fs->create_file_from_string($record, self::encode_json($manifest));

        return moodle_url::make_pluginfile_url(
            $file->get_contextid(),
            $file->get_component(),
            $file->get_filearea(),
            $file->get_itemid(),
            $file->get_filepath(),
            $file->get_filename(),
            true
        )->out(false);
    }

    /**
     * Trigger media exported events when available.
     *
     * @param stdClass[] $mediarecords Media records.
     * @param context_module $context Context.
     * @param stdClass $archive Archive.
     * @param stdClass $course Course.
     * @param stdClass $cm Course module.
     * @param int $exportid Export id.
     * @param string $format Format.
     * @return void
     */
    protected static function trigger_media_export_events(
        array $mediarecords,
        context_module $context,
        stdClass $archive,
        stdClass $course,
        stdClass $cm,
        int $exportid,
        string $format
    ): void {
        $eventclass = '\\mod_uckkarchive\\event\\media_exported';
        if (!class_exists($eventclass)) {
            return;
        }

        foreach ($mediarecords as $media) {
            try {
                $event = $eventclass::create([
                    'objectid' => (int)$media->id,
                    'context' => $context,
                    'other' => [
                        'archiveid' => (int)$archive->id,
                        'courseid' => (int)$course->id,
                        'cmid' => (int)$cm->id,
                        'exportid' => $exportid,
                        'exportformat' => $format,
                    ],
                ]);
                $event->trigger();
            } catch (\Throwable $ignored) {
                // Export persistence must not fail because an optional event class is not ready.
            }
        }
    }

    /**
     * Return whether record is restricted.
     *
     * @param stdClass $media Media.
     * @return bool
     */
    protected static function is_restricted_media(stdClass $media): bool {
        if (class_exists('\\mod_uckkarchive\\local\\media_policy') &&
                method_exists('\\mod_uckkarchive\\local\\media_policy', 'is_restricted_media')) {
            return \mod_uckkarchive\local\media_policy::is_restricted_media($media);
        }

        $status = (string)self::field($media, ['status'], '');
        $visibility = (string)self::field($media, ['visibility'], '');

        return $status === 'restricted' ||
            in_array($visibility, ['restricted', 'restricted_integrity', 'restricted_cultural'], true) ||
            !empty($media->restricted);
    }

    /**
     * Return whether record is culturally restricted.
     *
     * @param stdClass $media Media.
     * @return bool
     */
    protected static function is_culturally_restricted_media(stdClass $media): bool {
        if (class_exists('\\mod_uckkarchive\\local\\media_policy') &&
                method_exists('\\mod_uckkarchive\\local\\media_policy', 'is_culturally_restricted')) {
            return \mod_uckkarchive\local\media_policy::is_culturally_restricted($media);
        }

        $visibility = (string)self::field($media, ['visibility'], '');

        return $visibility === 'restricted_cultural' || !empty($media->culturalprotocol);
    }

    /**
     * Return normalized id list.
     *
     * @param array<int, mixed> $ids Raw ids.
     * @return int[]
     */
    protected static function normalise_ids(array $ids): array {
        $clean = [];

        foreach ($ids as $id) {
            $id = (int)$id;
            if ($id > 0) {
                $clean[] = $id;
            }
        }

        return array_values(array_unique($clean));
    }

    /**
     * Normalize export format.
     *
     * @param string $format Format.
     * @return string
     */
    protected static function normalise_format(string $format): string {
        $format = clean_param($format, PARAM_ALPHANUMEXT);
        $allowed = ['json', 'csv', 'html', 'zip', 'pdf', 'moodle'];

        return in_array($format, $allowed, true) ? $format : 'zip';
    }

    /**
     * Normalize export options.
     *
     * @param array<string, mixed> $options Options.
     * @return array<string, mixed>
     */
    protected static function normalise_options(array $options): array {
        $defaults = [
            'includeoriginals' => true,
            'includederivatives' => true,
            'includethumbnails' => true,
            'includepreviews' => true,
            'includecaptions' => true,
            'includetranscripts' => true,
            'includeattachments' => true,
            'includeversions' => true,
            'includerelations' => true,
            'includetags' => true,
            'includeadvisories' => true,
            'includeexternalrefs' => true,
            'redactionlevel' => 'standard',
            'visibility' => 'private',
        ];

        $options = array_merge($defaults, $options);

        foreach ([
            'includeoriginals',
            'includederivatives',
            'includethumbnails',
            'includepreviews',
            'includecaptions',
            'includetranscripts',
            'includeattachments',
            'includeversions',
            'includerelations',
            'includetags',
            'includeadvisories',
            'includeexternalrefs',
        ] as $key) {
            $options[$key] = !empty($options[$key]);
        }

        $options['redactionlevel'] = clean_param((string)$options['redactionlevel'], PARAM_ALPHANUMEXT);
        if (!in_array($options['redactionlevel'], ['none', 'standard', 'strict'], true)) {
            $options['redactionlevel'] = 'standard';
        }

        $options['visibility'] = clean_param((string)$options['visibility'], PARAM_ALPHANUMEXT);
        if (!in_array($options['visibility'], ['private', 'user', 'course', 'restricted'], true)) {
            $options['visibility'] = 'private';
        }

        return $options;
    }

    /**
     * Return whether options include any file area.
     *
     * @param array<string, mixed> $options Options.
     * @return bool
     */
    protected static function includes_any_file_area(array $options): bool {
        foreach ([
            'includeoriginals',
            'includederivatives',
            'includethumbnails',
            'includepreviews',
            'includecaptions',
            'includetranscripts',
            'includeattachments',
        ] as $key) {
            if (!empty($options[$key])) {
                return true;
            }
        }

        return false;
    }

    /**
     * Return exclusion payload.
     *
     * @param int $mediaid Media id.
     * @param string $code Code.
     * @param string $message Message.
     * @return array<string, mixed>
     */
    protected static function excluded(int $mediaid, string $code, string $message): array {
        return [
            'mediaid' => $mediaid,
            'code' => clean_param($code, PARAM_ALPHANUMEXT),
            'message' => $message,
        ];
    }

    /**
     * Return warning payload.
     *
     * @param string $item Warning item.
     * @param int $itemid Item id.
     * @param string $code Warning code.
     * @param string $message Message.
     * @return array<string, mixed>
     */
    protected static function warning(string $item, int $itemid, string $code, string $message): array {
        return [
            'item' => $item,
            'itemid' => $itemid,
            'warningcode' => clean_param($code, PARAM_ALPHANUMEXT),
            'message' => $message,
        ];
    }

    /**
     * Return table columns.
     *
     * @param string $table Table.
     * @return array<string, object>
     */
    protected static function columns(string $table): array {
        global $DB;

        return $DB->get_columns($table);
    }

    /**
     * Return whether a table exists.
     *
     * @param string $table Table name.
     * @return bool
     */
    protected static function table_exists(string $table): bool {
        global $DB;

        return $DB->get_manager()->table_exists(new \xmldb_table($table));
    }

    /**
     * Require a table to exist.
     *
     * @param string $table Table name.
     * @return void
     * @throws moodle_exception
     */
    protected static function require_table(string $table): void {
        if (!self::table_exists($table)) {
            throw new moodle_exception('missingtable', 'error', '', $table);
        }
    }

    /**
     * Filter record to actual table columns.
     *
     * @param string $table Table.
     * @param stdClass $record Record.
     * @return stdClass
     */
    protected static function filter_record_for_table(string $table, stdClass $record): stdClass {
        $columns = self::columns($table);
        $filtered = new stdClass();

        foreach ($columns as $field => $definition) {
            if (property_exists($record, $field)) {
                $filtered->{$field} = $record->{$field};
            }
        }

        return $filtered;
    }

    /**
     * Return first existing column.
     *
     * @param array<string, object> $columns Columns.
     * @param string[] $fields Candidate fields.
     * @return string|null
     */
    protected static function first_column(array $columns, array $fields): ?string {
        foreach ($fields as $field) {
            if (array_key_exists($field, $columns)) {
                return $field;
            }
        }

        return null;
    }

    /**
     * Return field from record.
     *
     * @param stdClass $record Record.
     * @param string[] $fields Candidate fields.
     * @param mixed $default Default.
     * @return mixed
     */
    protected static function field(stdClass $record, array $fields, mixed $default = null): mixed {
        foreach ($fields as $field) {
            if (property_exists($record, $field) && $record->{$field} !== null && $record->{$field} !== '') {
                return $record->{$field};
            }
        }

        return $default;
    }

    /**
     * Clean text.
     *
     * @param string $text Text.
     * @return string
     */
    protected static function normalise_text(string $text): string {
        return clean_param(trim($text), PARAM_TEXT);
    }

    /**
     * Encode JSON.
     *
     * @param mixed $data Data.
     * @return string
     */
    protected static function encode_json(mixed $data): string {
        $json = json_encode($data, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);

        if ($json === false) {
            throw new invalid_parameter_exception('Unable to encode export manifest JSON.');
        }

        return $json;
    }

    /**
     * Generate UUID.
     *
     * @return string
     */
    protected static function generate_uuid(): string {
        if (class_exists('\\mod_uckkarchive\\local\\uuid') &&
                method_exists('\\mod_uckkarchive\\local\\uuid', 'generate')) {
            return \mod_uckkarchive\local\uuid::generate();
        }

        return \core\uuid::generate();
    }
}
