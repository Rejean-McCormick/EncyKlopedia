<?php
// This file is part of Moodle - https://moodle.org/
//
// Moodle is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// any later version.

/**
 * Return one permission-filtered media item.
 *
 * @package     mod_uckkarchive
 * @copyright   2026 Univers-Cité King Klown
 * @license     https://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later
 */

declare(strict_types=1);

namespace mod_uckkarchive\external;

defined('MOODLE_INTERNAL') || die();

global $CFG;
require_once($CFG->libdir . '/externallib.php');
require_once(dirname(__DIR__, 2) . '/locallib.php');
require_once(dirname(__DIR__) . '/local/metadata_validator.php');
require_once(dirname(__DIR__) . '/local/content_policy.php');

use core_external\external_api;
use core_external\external_function_parameters;
use core_external\external_multiple_structure;
use core_external\external_single_structure;
use core_external\external_value;
use mod_uckkarchive\local\content_policy;
use mod_uckkarchive\local\metadata_validator;

/**
 * Return one permission-filtered media item.
 *
 * This read endpoint is deliberately policy-first. It resolves Moodle context,
 * checks module capabilities, loads only media owned by the current archive
 * instance, filters restricted records, and redacts advisory markers before
 * returning a stable response structure.
 */
final class get_media_item extends external_api {

    /** Media table name. */
    private const TABLE_MEDIA = 'uckkarchive_media';

    /** Media version table name. */
    private const TABLE_VERSION = 'uckkarchive_media_version';

    /** Media relation table name. */
    private const TABLE_RELATION = 'uckkarchive_media_relation';

    /** Media tag table name. */
    private const TABLE_TAG = 'uckkarchive_media_tag';

    /** Media source table name. */
    private const TABLE_SOURCE = 'uckkarchive_media_source';

    /** Content marker table name. */
    private const TABLE_MARKER = 'uckkarchive_content_marker';

    /** Content review table name. */
    private const TABLE_REVIEW = 'uckkarchive_content_review';

    /** Capability required for ordinary media read. */
    private const CAP_VIEW_MEDIA = 'mod/uckkarchive:viewmedia';

    /** Capability required for restricted media read. */
    private const CAP_VIEW_RESTRICTED_MEDIA = 'mod/uckkarchive:viewrestrictedmedia';

    /** Capability fallback for restricted archive read. */
    private const CAP_VIEW_RESTRICTED_ARCHIVE = 'mod/uckkarchive:viewrestricted';

    /**
     * Return external function parameters.
     *
     * Either mediaid or mediauuid must be provided.
     *
     * @return external_function_parameters
     */
    public static function execute_parameters(): external_function_parameters {
        return new external_function_parameters([
            'cmid' => new external_value(PARAM_INT, 'Course module id'),
            'mediaid' => new external_value(PARAM_INT, 'Media id. Optional when mediauuid is provided.', VALUE_DEFAULT, 0),
            'mediauuid' => new external_value(PARAM_ALPHANUMEXT, 'Media UUID. Optional when mediaid is provided.', VALUE_DEFAULT, ''),
            'includeversions' => new external_value(PARAM_BOOL, 'Include media versions.', VALUE_DEFAULT, true),
            'includerelations' => new external_value(PARAM_BOOL, 'Include media relations.', VALUE_DEFAULT, true),
            'includetags' => new external_value(PARAM_BOOL, 'Include media tags.', VALUE_DEFAULT, true),
            'includeadvisories' => new external_value(PARAM_BOOL, 'Include content advisory markers.', VALUE_DEFAULT, true),
            'includesource' => new external_value(PARAM_BOOL, 'Include media source metadata.', VALUE_DEFAULT, true),
        ]);
    }

    /**
     * Execute the service.
     *
     * @param int $cmid Course module id.
     * @param int $mediaid Media id.
     * @param string $mediauuid Media UUID.
     * @param bool $includeversions Include versions.
     * @param bool $includerelations Include relations.
     * @param bool $includetags Include tags.
     * @param bool $includeadvisories Include advisories.
     * @param bool $includesource Include source.
     * @return array
     */
    public static function execute(
        int $cmid,
        int $mediaid = 0,
        string $mediauuid = '',
        bool $includeversions = true,
        bool $includerelations = true,
        bool $includetags = true,
        bool $includeadvisories = true,
        bool $includesource = true
    ): array {
        global $DB;

        $params = self::validate_parameters(self::execute_parameters(), [
            'cmid' => $cmid,
            'mediaid' => $mediaid,
            'mediauuid' => $mediauuid,
            'includeversions' => $includeversions,
            'includerelations' => $includerelations,
            'includetags' => $includetags,
            'includeadvisories' => $includeadvisories,
            'includesource' => $includesource,
        ]);

        [$course, $cm, $archive, $context] = self::load_page((int)$params['cmid']);
        self::validate_context($context);
        require_capability(self::CAP_VIEW_MEDIA, $context);

        if ((int)$params['mediaid'] <= 0 && trim((string)$params['mediauuid']) === '') {
            throw new \invalid_parameter_exception('Either mediaid or mediauuid is required.');
        }

        if (!self::table_exists(self::TABLE_MEDIA)) {
            throw new \moodle_exception('mediatablenotavailable', 'uckkarchive');
        }

        $media = self::load_media(
            $archive,
            (int)$params['mediaid'],
            trim((string)$params['mediauuid'])
        );

        self::require_media_access($context, $media);

        $currentversion = self::load_current_version($context, $media);
        $versions = $params['includeversions'] ? self::load_versions($context, $media) : [];
        $relations = $params['includerelations'] ? self::load_relations($media) : [];
        $tags = $params['includetags'] ? self::load_tags($media) : [];
        $markers = $params['includeadvisories'] ? self::load_content_markers($context, $media) : [];
        $source = $params['includesource'] ? self::load_source($media) : self::empty_source();

        return [
            'media' => self::export_media($context, $media, $currentversion),
            'currentversion' => $currentversion,
            'versions' => $versions,
            'relations' => $relations,
            'tags' => $tags,
            'contentmarkers' => $markers,
            'source' => $source,
            'warnings' => [],
        ];
    }

    /**
     * Return external function result structure.
     *
     * @return external_single_structure
     */
    public static function execute_returns(): external_single_structure {
        return new external_single_structure([
            'media' => self::media_structure(),
            'currentversion' => self::version_structure(),
            'versions' => new external_multiple_structure(self::version_structure()),
            'relations' => new external_multiple_structure(self::relation_structure()),
            'tags' => new external_multiple_structure(self::tag_structure()),
            'contentmarkers' => new external_multiple_structure(self::marker_structure()),
            'source' => self::source_structure(),
            'warnings' => new external_multiple_structure(self::warning_structure()),
        ]);
    }

    /**
     * Load Moodle page objects.
     *
     * @param int $cmid Course module id.
     * @return array{0:\stdClass,1:\stdClass,2:\stdClass,3:\context_module}
     */
    private static function load_page(int $cmid): array {
        [$course, $cm, $archive, $context] = \uckkarchive_require_page($cmid, 0);
        return [$course, $cm, $archive, $context];
    }

    /**
     * Load media record by id or UUID.
     *
     * @param \stdClass $archive Archive instance.
     * @param int $mediaid Media id.
     * @param string $mediauuid Media UUID.
     * @return \stdClass Media record.
     */
    private static function load_media(\stdClass $archive, int $mediaid, string $mediauuid): \stdClass {
        global $DB;

        $fields = self::table_fields(self::TABLE_MEDIA);
        $archivefield = self::archive_field($fields);

        $conditions = [$archivefield => (int)$archive->id];

        if ($mediaid > 0) {
            $conditions['id'] = $mediaid;
        } else {
            if (!isset($fields['uuid'])) {
                throw new \invalid_parameter_exception('mediauuid lookup is not available because uuid field is missing.');
            }
            $conditions['uuid'] = metadata_validator::uuid($mediauuid, 'mediauuid', true);
        }

        return $DB->get_record(self::TABLE_MEDIA, $conditions, '*', MUST_EXIST);
    }

    /**
     * Require access to the media record.
     *
     * @param \context_module $context Module context.
     * @param \stdClass $media Media record.
     */
    private static function require_media_access(\context_module $context, \stdClass $media): void {
        if (!self::can_view_media($context, $media)) {
            throw new \required_capability_exception($context, self::CAP_VIEW_MEDIA, 'nopermissions', '');
        }

        if (self::is_restricted_media($media) && !self::can_view_restricted_media($context)) {
            throw new \required_capability_exception($context, self::CAP_VIEW_RESTRICTED_MEDIA, 'nopermissions', '');
        }
    }

    /**
     * Return whether the user can view ordinary media.
     *
     * @param \context_module $context Module context.
     * @param \stdClass $media Media record.
     * @return bool
     */
    private static function can_view_media(\context_module $context, \stdClass $media): bool {
        $mediapolicy = '\\mod_uckkarchive\\local\\media_policy';

        if (class_exists($mediapolicy) && method_exists($mediapolicy, 'can_view_media')) {
            return (bool)$mediapolicy::can_view_media($context, $media);
        }

        return has_capability(self::CAP_VIEW_MEDIA, $context);
    }

    /**
     * Return whether the user can view restricted media.
     *
     * @param \context_module $context Module context.
     * @return bool
     */
    private static function can_view_restricted_media(\context_module $context): bool {
        return has_capability(self::CAP_VIEW_RESTRICTED_MEDIA, $context)
            || has_capability(self::CAP_VIEW_RESTRICTED_ARCHIVE, $context)
            || content_policy::can_view_culturally_restricted($context);
    }

    /**
     * Return whether a media record is restricted.
     *
     * @param \stdClass $media Media record.
     * @return bool
     */
    private static function is_restricted_media(\stdClass $media): bool {
        $status = self::field_string($media, 'status');
        $visibility = self::field_string($media, 'visibility');
        $suitability = self::field_string($media, 'audiencesuitability');

        return in_array($status, ['restricted', 'deleted_soft'], true)
            || in_array($visibility, ['restricted', 'restricted_integrity', 'restricted_cultural'], true)
            || in_array($suitability, ['restricted', 'restricted_integrity', 'restricted_cultural', 'staff_only'], true);
    }

    /**
     * Export media record.
     *
     * @param \context_module $context Module context.
     * @param \stdClass $media Media record.
     * @param array $currentversion Current version export.
     * @return array
     */
    private static function export_media(\context_module $context, \stdClass $media, array $currentversion): array {
        $metadata = self::decode_record_metadata($media);

        return [
            'id' => (int)$media->id,
            'uuid' => self::field_string_raw($media, 'uuid'),
            'archiveid' => self::record_archive_id($media),
            'title' => self::field_string_raw($media, 'title'),
            'description' => self::field_string_raw($media, 'description'),
            'mediatype' => self::field_string($media, 'mediatype', 'other'),
            'mimetype' => self::field_string_raw($media, 'mimetype'),
            'status' => self::field_string($media, 'status', 'draft'),
            'visibility' => self::field_string($media, 'visibility', 'course'),
            'audiencesuitability' => self::field_string($media, 'audiencesuitability', 'guided'),
            'sourceid' => self::field_int($media, 'sourceid'),
            'currentversionid' => self::field_int($media, 'currentversionid'),
            'createdby' => self::field_int($media, 'createdby'),
            'modifiedby' => self::field_int($media, 'modifiedby'),
            'timecreated' => self::field_int($media, 'timecreated'),
            'timemodified' => self::field_int($media, 'timemodified'),
            'isrestricted' => self::is_restricted_media($media),
            'canviewrestricted' => self::can_view_restricted_media($context),
            'hascurrentversion' => !empty($currentversion['id']),
            'downloadurl' => (string)($currentversion['downloadurl'] ?? ''),
            'metadatajson' => self::json_for_return($metadata),
        ];
    }

    /**
     * Load current media version.
     *
     * @param \context_module $context Module context.
     * @param \stdClass $media Media record.
     * @return array
     */
    private static function load_current_version(\context_module $context, \stdClass $media): array {
        global $DB;

        if (!self::table_exists(self::TABLE_VERSION)) {
            return self::empty_version();
        }

        $fields = self::table_fields(self::TABLE_VERSION);

        $record = null;
        $currentversionid = self::field_int($media, 'currentversionid');

        if ($currentversionid > 0) {
            $record = $DB->get_record(self::TABLE_VERSION, ['id' => $currentversionid, 'mediaid' => (int)$media->id]);
        }

        if (!$record) {
            $sort = isset($fields['versionno']) ? 'versionno DESC, id DESC' : 'id DESC';
            $records = $DB->get_records(self::TABLE_VERSION, ['mediaid' => (int)$media->id], $sort, '*', 0, 1);
            $record = $records ? reset($records) : null;
        }

        if (!$record) {
            return self::empty_version();
        }

        return self::export_version($context, $record);
    }

    /**
     * Load all media versions.
     *
     * @param \context_module $context Module context.
     * @param \stdClass $media Media record.
     * @return array
     */
    private static function load_versions(\context_module $context, \stdClass $media): array {
        global $DB;

        if (!self::table_exists(self::TABLE_VERSION)) {
            return [];
        }

        $fields = self::table_fields(self::TABLE_VERSION);
        $sort = isset($fields['versionno']) ? 'versionno DESC, id DESC' : 'id DESC';

        $records = $DB->get_records(self::TABLE_VERSION, ['mediaid' => (int)$media->id], $sort);
        $out = [];

        foreach ($records as $record) {
            $out[] = self::export_version($context, $record);
        }

        return $out;
    }

    /**
     * Export media version.
     *
     * @param \context_module $context Module context.
     * @param \stdClass $version Version record.
     * @return array
     */
    private static function export_version(\context_module $context, \stdClass $version): array {
        $file = self::find_version_file($context, $version);
        $metadata = self::decode_record_metadata($version);

        return [
            'id' => (int)$version->id,
            'uuid' => self::field_string_raw($version, 'uuid'),
            'mediaid' => self::field_int($version, 'mediaid'),
            'versionno' => self::field_int($version, 'versionno', 1),
            'status' => self::field_string($version, 'status', 'active'),
            'filename' => self::field_string_raw($version, 'filename', (string)($file['filename'] ?? '')),
            'filepath' => self::field_string_raw($version, 'filepath', '/'),
            'filearea' => self::field_string_raw($version, 'filearea', 'media_original'),
            'filesize' => self::field_int($version, 'filesize', (int)($file['filesize'] ?? 0)),
            'mimetype' => self::field_string_raw($version, 'mimetype', (string)($file['mimetype'] ?? '')),
            'contenthash' => self::field_string_raw($version, 'contenthash', self::field_string_raw($version, 'filehash')),
            'downloadurl' => (string)($file['downloadurl'] ?? ''),
            'timecreated' => self::field_int($version, 'timecreated'),
            'timemodified' => self::field_int($version, 'timemodified'),
            'metadatajson' => self::json_for_return($metadata),
        ];
    }

    /**
     * Load media relations.
     *
     * @param \stdClass $media Media record.
     * @return array
     */
    private static function load_relations(\stdClass $media): array {
        global $DB;

        if (!self::table_exists(self::TABLE_RELATION)) {
            return [];
        }

        $fields = self::table_fields(self::TABLE_RELATION);
        $params = [];
        $whereparts = [];

        foreach (['mediaid', 'frommediaid', 'sourcemediaid'] as $field) {
            if (isset($fields[$field])) {
                $whereparts[] = $field . ' = ?';
                $params[] = (int)$media->id;
            }
        }

        foreach (['relatedmediaid', 'tomediaid', 'targetmediaid'] as $field) {
            if (isset($fields[$field])) {
                $whereparts[] = $field . ' = ?';
                $params[] = (int)$media->id;
            }
        }

        if (!$whereparts) {
            return [];
        }

        $records = $DB->get_records_select(self::TABLE_RELATION, implode(' OR ', $whereparts), $params, 'id ASC');
        $out = [];

        foreach ($records as $record) {
            $out[] = [
                'id' => (int)$record->id,
                'uuid' => self::field_string_raw($record, 'uuid'),
                'relationtype' => self::field_string($record, 'relationtype', self::field_string($record, 'type')),
                'mediaid' => self::first_int_field($record, ['mediaid', 'frommediaid', 'sourcemediaid']),
                'relatedmediaid' => self::first_int_field($record, ['relatedmediaid', 'tomediaid', 'targetmediaid']),
                'externalworkid' => self::field_int($record, 'externalworkid'),
                'itemid' => self::field_int($record, 'itemid'),
                'sortorder' => self::field_int($record, 'sortorder'),
                'metadatajson' => self::json_for_return(self::decode_record_metadata($record)),
            ];
        }

        return $out;
    }

    /**
     * Load media tags.
     *
     * @param \stdClass $media Media record.
     * @return array
     */
    private static function load_tags(\stdClass $media): array {
        global $DB;

        if (!self::table_exists(self::TABLE_TAG)) {
            return [];
        }

        $fields = self::table_fields(self::TABLE_TAG);
        if (!isset($fields['mediaid'])) {
            return [];
        }

        $records = $DB->get_records(self::TABLE_TAG, ['mediaid' => (int)$media->id], 'tagkey ASC, id ASC');
        $out = [];

        foreach ($records as $record) {
            $out[] = [
                'id' => (int)$record->id,
                'tagkey' => self::field_string($record, 'tagkey', self::field_string($record, 'name')),
                'tagsetkey' => self::field_string($record, 'tagsetkey'),
                'label' => self::field_string_raw($record, 'label'),
                'sortorder' => self::field_int($record, 'sortorder'),
            ];
        }

        return $out;
    }

    /**
     * Load media source.
     *
     * @param \stdClass $media Media record.
     * @return array
     */
    private static function load_source(\stdClass $media): array {
        global $DB;

        if (!self::table_exists(self::TABLE_SOURCE)) {
            return self::empty_source();
        }

        $sourceid = self::field_int($media, 'sourceid');
        if ($sourceid <= 0) {
            return self::empty_source();
        }

        $record = $DB->get_record(self::TABLE_SOURCE, ['id' => $sourceid]);
        if (!$record) {
            return self::empty_source();
        }

        return [
            'id' => (int)$record->id,
            'uuid' => self::field_string_raw($record, 'uuid'),
            'sourcetype' => self::field_string($record, 'sourcetype', 'unknown_source'),
            'sourceownership' => self::field_string($record, 'sourceownership', 'unknown_source'),
            'title' => self::field_string_raw($record, 'title'),
            'creator' => self::field_string_raw($record, 'creator'),
            'owner' => self::field_string_raw($record, 'owner'),
            'license' => self::field_string_raw($record, 'license'),
            'rightsnote' => self::field_string_raw($record, 'rightsnote'),
            'citation' => self::field_string_raw($record, 'citation'),
            'url' => self::field_string_raw($record, 'url'),
            'identifier' => self::field_string_raw($record, 'identifier'),
            'metadatajson' => self::json_for_return(self::decode_record_metadata($record)),
        ];
    }

    /**
     * Load content markers for media.
     *
     * @param \context_module $context Context.
     * @param \stdClass $media Media record.
     * @return array
     */
    private static function load_content_markers(\context_module $context, \stdClass $media): array {
        global $DB;

        if (!self::table_exists(self::TABLE_MARKER)) {
            return [];
        }

        $fields = self::table_fields(self::TABLE_MARKER);
        $params = [];
        $whereparts = [];

        if (isset($fields['mediaid'])) {
            $whereparts[] = 'mediaid = ?';
            $params[] = (int)$media->id;
        }

        if (isset($fields['targettype']) && isset($fields['targetid'])) {
            $whereparts[] = '(targettype = ? AND targetid = ?)';
            $params[] = 'media';
            $params[] = (int)$media->id;
        }

        if (!$whereparts) {
            return [];
        }

        $records = $DB->get_records_select(self::TABLE_MARKER, implode(' OR ', $whereparts), $params, 'id ASC');
        $out = [];

        foreach ($records as $record) {
            $mode = content_policy::redaction_mode($context, $record);
            if ($mode === content_policy::REDACT_HIDE) {
                continue;
            }

            $record = content_policy::redact_marker($record, $mode);
            $out[] = self::export_marker($context, $record);
        }

        return $out;
    }

    /**
     * Export marker.
     *
     * @param \context_module $context Context.
     * @param \stdClass $marker Marker.
     * @return array
     */
    private static function export_marker(\context_module $context, \stdClass $marker): array {
        $locatorjson = self::field_string_raw($marker, 'locatorjson');
        $locator = [];

        if ($locatorjson !== '') {
            try {
                $locator = metadata_validator::decode_json($locatorjson, 'locatorjson');
            } catch (\invalid_parameter_exception $e) {
                $locator = [];
            }
        } else if (isset($marker->locator) && is_array($marker->locator)) {
            $locator = $marker->locator;
        }

        return [
            'id' => (int)$marker->id,
            'uuid' => self::field_string_raw($marker, 'uuid'),
            'tagkey' => self::field_string($marker, 'tagkey'),
            'tagsetkey' => self::field_string($marker, 'tagsetkey'),
            'label' => self::field_string_raw($marker, 'label', self::field_string($marker, 'tagkey')),
            'severity' => self::field_string($marker, 'severity', 'notice'),
            'visibility' => self::field_string($marker, 'visibility', 'course'),
            'audiencesuitability' => self::field_string($marker, 'audiencesuitability', 'guided'),
            'reviewstate' => self::field_string($marker, 'reviewstate', 'draft'),
            'redacted' => !empty($marker->redacted),
            'redactionmode' => self::field_string($marker, 'redactionmode', content_policy::REDACT_NONE),
            'showlocator' => content_policy::can_view_locator($context, $marker),
            'locatorjson' => self::json_for_return($locator),
            'note' => self::field_string_raw($marker, 'note'),
            'metadatajson' => self::json_for_return(self::decode_record_metadata($marker)),
        ];
    }

    /**
     * Find first file associated with a media version.
     *
     * @param \context_module $context Context.
     * @param \stdClass $version Version.
     * @return array
     */
    private static function find_version_file(\context_module $context, \stdClass $version): array {
        $fs = get_file_storage();

        $filearea = self::field_string_raw($version, 'filearea', 'media_original');
        $itemid = self::field_int($version, 'fileitemid', (int)$version->id);

        $files = $fs->get_area_files(
            $context->id,
            'mod_uckkarchive',
            $filearea,
            $itemid,
            'timemodified DESC, id DESC',
            false
        );

        if (!$files) {
            return [];
        }

        $file = reset($files);
        if (!$file) {
            return [];
        }

        $url = \moodle_url::make_pluginfile_url(
            $context->id,
            'mod_uckkarchive',
            $filearea,
            $itemid,
            $file->get_filepath(),
            $file->get_filename()
        );

        return [
            'filename' => $file->get_filename(),
            'filesize' => $file->get_filesize(),
            'mimetype' => (string)$file->get_mimetype(),
            'downloadurl' => $url->out(false),
        ];
    }

    /**
     * Return table field map.
     *
     * @param string $table Table name without prefix.
     * @return array
     */
    private static function table_fields(string $table): array {
        global $DB;

        static $cache = [];

        if (!array_key_exists($table, $cache)) {
            try {
                $cache[$table] = $DB->get_columns($table);
            } catch (\Throwable $e) {
                $cache[$table] = [];
            }
        }

        return $cache[$table];
    }

    /**
     * Return whether table exists.
     *
     * @param string $table Table name without prefix.
     * @return bool
     */
    private static function table_exists(string $table): bool {
        return !empty(self::table_fields($table));
    }

    /**
     * Return archive id field name for a table.
     *
     * @param array $fields Field map.
     * @return string
     */
    private static function archive_field(array $fields): string {
        if (isset($fields['uckkarchiveid'])) {
            return 'uckkarchiveid';
        }

        return 'archiveid';
    }

    /**
     * Return archive id from a record.
     *
     * @param \stdClass $record Record.
     * @return int
     */
    private static function record_archive_id(\stdClass $record): int {
        if (isset($record->uckkarchiveid)) {
            return (int)$record->uckkarchiveid;
        }

        return self::field_int($record, 'archiveid');
    }

    /**
     * Decode metadata from a record.
     *
     * @param \stdClass $record Record.
     * @return array
     */
    private static function decode_record_metadata(\stdClass $record): array {
        if (!isset($record->metadata) || trim((string)$record->metadata) === '') {
            return [];
        }

        try {
            return metadata_validator::decode_json((string)$record->metadata);
        } catch (\invalid_parameter_exception $e) {
            return ['_invalid' => true];
        }
    }

    /**
     * Return JSON string safe for external return.
     *
     * @param array $data Data.
     * @return string
     */
    private static function json_for_return(array $data): string {
        if ($data === []) {
            return '{}';
        }

        $json = json_encode($data, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
        return $json === false ? '{}' : $json;
    }

    /**
     * Read lower-case string field.
     *
     * @param \stdClass $record Record.
     * @param string $field Field name.
     * @param string $default Default value.
     * @return string
     */
    private static function field_string(\stdClass $record, string $field, string $default = ''): string {
        return strtolower(trim(self::field_string_raw($record, $field, $default)));
    }

    /**
     * Read raw string field.
     *
     * @param \stdClass $record Record.
     * @param string $field Field name.
     * @param string $default Default value.
     * @return string
     */
    private static function field_string_raw(\stdClass $record, string $field, string $default = ''): string {
        if (!isset($record->{$field}) || $record->{$field} === null || !is_scalar($record->{$field})) {
            return $default;
        }

        return trim((string)$record->{$field});
    }

    /**
     * Read integer field.
     *
     * @param \stdClass $record Record.
     * @param string $field Field name.
     * @param int $default Default value.
     * @return int
     */
    private static function field_int(\stdClass $record, string $field, int $default = 0): int {
        if (!isset($record->{$field}) || $record->{$field} === null || !is_numeric($record->{$field})) {
            return $default;
        }

        return (int)$record->{$field};
    }

    /**
     * Return first available integer field.
     *
     * @param \stdClass $record Record.
     * @param array $fields Candidate fields.
     * @return int
     */
    private static function first_int_field(\stdClass $record, array $fields): int {
        foreach ($fields as $field) {
            $value = self::field_int($record, $field);
            if ($value > 0) {
                return $value;
            }
        }

        return 0;
    }

    /**
     * Empty version response.
     *
     * @return array
     */
    private static function empty_version(): array {
        return [
            'id' => 0,
            'uuid' => '',
            'mediaid' => 0,
            'versionno' => 0,
            'status' => '',
            'filename' => '',
            'filepath' => '',
            'filearea' => '',
            'filesize' => 0,
            'mimetype' => '',
            'contenthash' => '',
            'downloadurl' => '',
            'timecreated' => 0,
            'timemodified' => 0,
            'metadatajson' => '{}',
        ];
    }

    /**
     * Empty source response.
     *
     * @return array
     */
    private static function empty_source(): array {
        return [
            'id' => 0,
            'uuid' => '',
            'sourcetype' => '',
            'sourceownership' => '',
            'title' => '',
            'creator' => '',
            'owner' => '',
            'license' => '',
            'rightsnote' => '',
            'citation' => '',
            'url' => '',
            'identifier' => '',
            'metadatajson' => '{}',
        ];
    }

    /**
     * Media external structure.
     *
     * @return external_single_structure
     */
    private static function media_structure(): external_single_structure {
        return new external_single_structure([
            'id' => new external_value(PARAM_INT, 'Media id'),
            'uuid' => new external_value(PARAM_TEXT, 'Media UUID'),
            'archiveid' => new external_value(PARAM_INT, 'Archive instance id'),
            'title' => new external_value(PARAM_TEXT, 'Title'),
            'description' => new external_value(PARAM_RAW, 'Description'),
            'mediatype' => new external_value(PARAM_ALPHANUMEXT, 'Media type'),
            'mimetype' => new external_value(PARAM_TEXT, 'MIME type'),
            'status' => new external_value(PARAM_ALPHANUMEXT, 'Status'),
            'visibility' => new external_value(PARAM_ALPHANUMEXT, 'Visibility'),
            'audiencesuitability' => new external_value(PARAM_ALPHANUMEXT, 'Audience suitability'),
            'sourceid' => new external_value(PARAM_INT, 'Source id'),
            'currentversionid' => new external_value(PARAM_INT, 'Current version id'),
            'createdby' => new external_value(PARAM_INT, 'Created by user id'),
            'modifiedby' => new external_value(PARAM_INT, 'Modified by user id'),
            'timecreated' => new external_value(PARAM_INT, 'Time created'),
            'timemodified' => new external_value(PARAM_INT, 'Time modified'),
            'isrestricted' => new external_value(PARAM_BOOL, 'Whether media is restricted'),
            'canviewrestricted' => new external_value(PARAM_BOOL, 'Whether current user can view restricted media'),
            'hascurrentversion' => new external_value(PARAM_BOOL, 'Whether current version exists'),
            'downloadurl' => new external_value(PARAM_RAW, 'Download URL for current version'),
            'metadatajson' => new external_value(PARAM_RAW, 'Metadata JSON'),
        ]);
    }

    /**
     * Version external structure.
     *
     * @return external_single_structure
     */
    private static function version_structure(): external_single_structure {
        return new external_single_structure([
            'id' => new external_value(PARAM_INT, 'Version id'),
            'uuid' => new external_value(PARAM_TEXT, 'Version UUID'),
            'mediaid' => new external_value(PARAM_INT, 'Media id'),
            'versionno' => new external_value(PARAM_INT, 'Version number'),
            'status' => new external_value(PARAM_ALPHANUMEXT, 'Status'),
            'filename' => new external_value(PARAM_FILE, 'File name'),
            'filepath' => new external_value(PARAM_PATH, 'File path'),
            'filearea' => new external_value(PARAM_AREA, 'File area'),
            'filesize' => new external_value(PARAM_INT, 'File size'),
            'mimetype' => new external_value(PARAM_TEXT, 'MIME type'),
            'contenthash' => new external_value(PARAM_TEXT, 'Content hash'),
            'downloadurl' => new external_value(PARAM_RAW, 'Download URL'),
            'timecreated' => new external_value(PARAM_INT, 'Time created'),
            'timemodified' => new external_value(PARAM_INT, 'Time modified'),
            'metadatajson' => new external_value(PARAM_RAW, 'Metadata JSON'),
        ]);
    }

    /**
     * Relation external structure.
     *
     * @return external_single_structure
     */
    private static function relation_structure(): external_single_structure {
        return new external_single_structure([
            'id' => new external_value(PARAM_INT, 'Relation id'),
            'uuid' => new external_value(PARAM_TEXT, 'Relation UUID'),
            'relationtype' => new external_value(PARAM_ALPHANUMEXT, 'Relation type'),
            'mediaid' => new external_value(PARAM_INT, 'Media id'),
            'relatedmediaid' => new external_value(PARAM_INT, 'Related media id'),
            'externalworkid' => new external_value(PARAM_INT, 'External work id'),
            'itemid' => new external_value(PARAM_INT, 'Archive item id'),
            'sortorder' => new external_value(PARAM_INT, 'Sort order'),
            'metadatajson' => new external_value(PARAM_RAW, 'Metadata JSON'),
        ]);
    }

    /**
     * Tag external structure.
     *
     * @return external_single_structure
     */
    private static function tag_structure(): external_single_structure {
        return new external_single_structure([
            'id' => new external_value(PARAM_INT, 'Tag record id'),
            'tagkey' => new external_value(PARAM_ALPHANUMEXT, 'Tag key'),
            'tagsetkey' => new external_value(PARAM_ALPHANUMEXT, 'Tag set key'),
            'label' => new external_value(PARAM_TEXT, 'Label'),
            'sortorder' => new external_value(PARAM_INT, 'Sort order'),
        ]);
    }

    /**
     * Marker external structure.
     *
     * @return external_single_structure
     */
    private static function marker_structure(): external_single_structure {
        return new external_single_structure([
            'id' => new external_value(PARAM_INT, 'Marker id'),
            'uuid' => new external_value(PARAM_TEXT, 'Marker UUID'),
            'tagkey' => new external_value(PARAM_ALPHANUMEXT, 'Tag key'),
            'tagsetkey' => new external_value(PARAM_ALPHANUMEXT, 'Tag set key'),
            'label' => new external_value(PARAM_TEXT, 'Label'),
            'severity' => new external_value(PARAM_ALPHANUMEXT, 'Severity'),
            'visibility' => new external_value(PARAM_ALPHANUMEXT, 'Visibility'),
            'audiencesuitability' => new external_value(PARAM_ALPHANUMEXT, 'Audience suitability'),
            'reviewstate' => new external_value(PARAM_ALPHANUMEXT, 'Review state'),
            'redacted' => new external_value(PARAM_BOOL, 'Whether marker is redacted'),
            'redactionmode' => new external_value(PARAM_ALPHANUMEXT, 'Redaction mode'),
            'showlocator' => new external_value(PARAM_BOOL, 'Whether locator can be shown'),
            'locatorjson' => new external_value(PARAM_RAW, 'Locator JSON'),
            'note' => new external_value(PARAM_RAW, 'Safe note'),
            'metadatajson' => new external_value(PARAM_RAW, 'Metadata JSON'),
        ]);
    }

    /**
     * Source external structure.
     *
     * @return external_single_structure
     */
    private static function source_structure(): external_single_structure {
        return new external_single_structure([
            'id' => new external_value(PARAM_INT, 'Source id'),
            'uuid' => new external_value(PARAM_TEXT, 'Source UUID'),
            'sourcetype' => new external_value(PARAM_ALPHANUMEXT, 'Source type'),
            'sourceownership' => new external_value(PARAM_ALPHANUMEXT, 'Source ownership'),
            'title' => new external_value(PARAM_TEXT, 'Title'),
            'creator' => new external_value(PARAM_TEXT, 'Creator'),
            'owner' => new external_value(PARAM_TEXT, 'Owner'),
            'license' => new external_value(PARAM_TEXT, 'License'),
            'rightsnote' => new external_value(PARAM_RAW, 'Rights note'),
            'citation' => new external_value(PARAM_RAW, 'Citation'),
            'url' => new external_value(PARAM_RAW, 'URL'),
            'identifier' => new external_value(PARAM_TEXT, 'Identifier'),
            'metadatajson' => new external_value(PARAM_RAW, 'Metadata JSON'),
        ]);
    }

    /**
     * Warning external structure.
     *
     * @return external_single_structure
     */
    private static function warning_structure(): external_single_structure {
        return new external_single_structure([
            'item' => new external_value(PARAM_TEXT, 'Warning item'),
            'itemid' => new external_value(PARAM_INT, 'Warning item id'),
            'warningcode' => new external_value(PARAM_ALPHANUMEXT, 'Warning code'),
            'message' => new external_value(PARAM_TEXT, 'Warning message'),
        ]);
    }
}
