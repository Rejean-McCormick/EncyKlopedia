<?php
// This file is part of Moodle - https://moodle.org/
//
// Moodle is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// any later version.

/**
 * Return media versions for one media object.
 *
 * @package    mod_uckkarchive
 * @copyright  2026 Univers-Cité King Klown
 * @license    https://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later
 */

declare(strict_types=1);

namespace mod_uckkarchive\external;

defined('MOODLE_INTERNAL') || die();

global $CFG;
require_once($CFG->libdir . '/externallib.php');
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
 * Return media versions for one media object.
 *
 * Target service:
 *
 * ```text
 * mod_uckkarchive_get_media_versions
 * ```
 *
 * This service is read-only. It resolves the Moodle module context, verifies
 * media visibility, checks version access, and returns permission-filtered
 * version metadata. It does not serve files directly; download authority still
 * belongs to the pluginfile handler and media policy.
 */
final class get_media_versions extends external_api {
    /** Main media table. */
    private const TABLE_MEDIA = 'uckkarchive_media';

    /** Media version table. */
    private const TABLE_VERSION = 'uckkarchive_media_version';

    /** Moodle File API component. */
    private const COMPONENT = 'mod_uckkarchive';

    /** Media file areas normally associated with versions. */
    private const VERSION_FILEAREAS = [
        'media_original',
        'media_preview',
        'media_derivative',
        'media_caption',
        'media_transcript',
        'media_attachment',
    ];

    /**
     * Load page objects.
     *
     * @param int $cmid Course module id.
     * @return array{0:stdClass,1:stdClass,2:stdClass,3:context_module}
     */
    protected static function load_page(int $cmid): array {
        [$course, $cm, $archive, $context] = \uckkarchive_require_page($cmid, 0);
        return [$course, $cm, $archive, $context];
    }

    /**
     * Define parameters.
     *
     * @return external_function_parameters
     */
    public static function execute_parameters(): external_function_parameters {
        return new external_function_parameters([
            'cmid' => new external_value(PARAM_INT, 'Course module id'),
            'mediaid' => new external_value(PARAM_INT, 'Media id'),
            'include' => new external_single_structure([
                'deleted' => new external_value(PARAM_BOOL, 'Include soft-deleted versions', VALUE_DEFAULT, false),
                'files' => new external_value(PARAM_BOOL, 'Include file metadata and URLs where allowed', VALUE_DEFAULT, true),
                'metadata' => new external_value(PARAM_BOOL, 'Include decoded/version metadata JSON', VALUE_DEFAULT, true),
                'hashes' => new external_value(PARAM_BOOL, 'Include file hashes', VALUE_DEFAULT, true),
            ], 'Include options', VALUE_DEFAULT, []),
        ]);
    }

    /**
     * Execute service.
     *
     * @param int $cmid Course module id.
     * @param int $mediaid Media id.
     * @param array<string, mixed> $include Include options.
     * @return array<string, mixed>
     */
    public static function execute(int $cmid, int $mediaid, array $include = []): array {
        global $DB;

        $params = self::validate_parameters(self::execute_parameters(), [
            'cmid' => $cmid,
            'mediaid' => $mediaid,
            'include' => $include,
        ]);

        [$course, $cm, $archive, $context] = self::load_page((int)$params['cmid']);
        self::validate_context($context);

        require_capability('mod/uckkarchive:viewmedia', $context);

        $mediaid = self::require_positive_id((int)$params['mediaid'], 'mediaid');
        $include = self::normalise_include((array)$params['include']);

        self::require_table(self::TABLE_MEDIA);
        self::require_table(self::TABLE_VERSION);

        $media = self::get_media_record($mediaid, (int)$archive->id);

        if (!$media) {
            throw new moodle_exception('invalidrecord', 'error', '', 'mediaid');
        }

        if (!self::can_view_media($context, $media)) {
            throw new moodle_exception('nopermissions', 'error', '', 'viewmedia');
        }

        $versions = self::load_versions($mediaid, !empty($include['deleted']));
        $exported = [];

        foreach ($versions as $version) {
            if (!self::can_view_version($context, $media, $version)) {
                continue;
            }

            $exported[] = self::export_version($context, $media, $version, $include);
        }

        return [
            'mediaid' => $mediaid,
            'mediauuid' => (string)self::field($media, ['uuid'], ''),
            'currentversionid' => (int)self::field($media, ['currentversionid'], 0),
            'versions' => $exported,
            'permissions' => self::permissions($context, $media),
            'warnings' => [],
        ];
    }

    /**
     * Define returns.
     *
     * @return external_single_structure
     */
    public static function execute_returns(): external_single_structure {
        return new external_single_structure([
            'mediaid' => new external_value(PARAM_INT, 'Media id'),
            'mediauuid' => new external_value(PARAM_TEXT, 'Media UUID'),
            'currentversionid' => new external_value(PARAM_INT, 'Current version id'),
            'versions' => new external_multiple_structure(self::version_structure(), 'Media versions'),
            'permissions' => new external_single_structure([
                'viewmedia' => new external_value(PARAM_BOOL, 'Can view media'),
                'downloadmedia' => new external_value(PARAM_BOOL, 'Can download media'),
                'versionmedia' => new external_value(PARAM_BOOL, 'Can add versions'),
                'viewrestrictedmedia' => new external_value(PARAM_BOOL, 'Can view restricted media'),
                'viewculturallyrestricted' => new external_value(PARAM_BOOL, 'Can view culturally restricted media'),
            ]),
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
     * Return version structure.
     *
     * @return external_single_structure
     */
    protected static function version_structure(): external_single_structure {
        return new external_single_structure([
            'id' => new external_value(PARAM_INT, 'Version id'),
            'uuid' => new external_value(PARAM_TEXT, 'Version UUID'),
            'mediaid' => new external_value(PARAM_INT, 'Media id'),
            'versionnumber' => new external_value(PARAM_INT, 'Version number'),
            'label' => new external_value(PARAM_TEXT, 'Version label'),
            'status' => new external_value(PARAM_ALPHANUMEXT, 'Version status'),
            'filearea' => new external_value(PARAM_ALPHANUMEXT, 'Primary file area'),
            'filename' => new external_value(PARAM_FILE, 'Primary filename'),
            'filesize' => new external_value(PARAM_INT, 'Primary file size'),
            'mimetype' => new external_value(PARAM_TEXT, 'Primary MIME type'),
            'contenthash' => new external_value(PARAM_TEXT, 'Primary content hash'),
            'iscurrent' => new external_value(PARAM_BOOL, 'Whether this is the current version'),
            'createdby' => new external_value(PARAM_INT, 'Creator user id'),
            'modifiedby' => new external_value(PARAM_INT, 'Modifier user id'),
            'timecreated' => new external_value(PARAM_INT, 'Creation timestamp'),
            'timemodified' => new external_value(PARAM_INT, 'Modified timestamp'),
            'metadata' => new external_value(PARAM_RAW, 'Metadata JSON'),
            'files' => new external_multiple_structure(
                new external_single_structure([
                    'filearea' => new external_value(PARAM_ALPHANUMEXT, 'File area'),
                    'filename' => new external_value(PARAM_FILE, 'File name'),
                    'filepath' => new external_value(PARAM_PATH, 'File path'),
                    'filesize' => new external_value(PARAM_INT, 'File size'),
                    'mimetype' => new external_value(PARAM_TEXT, 'MIME type'),
                    'contenthash' => new external_value(PARAM_TEXT, 'Content hash'),
                    'url' => new external_value(PARAM_RAW, 'Pluginfile URL'),
                    'downloadurl' => new external_value(PARAM_RAW, 'Forced download URL'),
                ]),
                'Files linked to this version'
            ),
        ]);
    }

    /**
     * Get media record for current archive.
     *
     * @param int $mediaid Media id.
     * @param int $archiveid Archive id.
     * @return stdClass|null
     */
    protected static function get_media_record(int $mediaid, int $archiveid): ?stdClass {
        global $DB;

        $media = $DB->get_record(self::TABLE_MEDIA, ['id' => $mediaid], '*', IGNORE_MISSING);
        if (!$media) {
            return null;
        }

        $recordarchiveid = (int)self::field($media, ['archiveid', 'uckkarchiveid'], 0);
        if ($recordarchiveid > 0 && $recordarchiveid !== $archiveid) {
            return null;
        }

        return $media;
    }

    /**
     * Load versions.
     *
     * @param int $mediaid Media id.
     * @param bool $includedeleted Include deleted_soft.
     * @return stdClass[]
     */
    protected static function load_versions(int $mediaid, bool $includedeleted): array {
        global $DB;

        if (class_exists('\\mod_uckkarchive\\local\\media_version') &&
                method_exists('\\mod_uckkarchive\\local\\media_version', 'get_versions')) {
            return array_values(\mod_uckkarchive\local\media_version::get_versions($mediaid, $includedeleted));
        }

        $columns = self::columns(self::TABLE_VERSION);
        $conditions = ['mediaid' => $mediaid];

        if (!$includedeleted && array_key_exists('status', $columns)) {
            return array_values($DB->get_records_select(
                self::TABLE_VERSION,
                'mediaid = :mediaid AND status <> :deleted',
                ['mediaid' => $mediaid, 'deleted' => 'deleted_soft'],
                self::version_sort_sql($columns)
            ));
        }

        return array_values($DB->get_records(self::TABLE_VERSION, $conditions, self::version_sort_sql($columns)));
    }

    /**
     * Export one version.
     *
     * @param context_module $context Module context.
     * @param stdClass $media Media record.
     * @param stdClass $version Version record.
     * @param array<string, mixed> $include Include options.
     * @return array<string, mixed>
     */
    protected static function export_version(
        context_module $context,
        stdClass $media,
        stdClass $version,
        array $include
    ): array {
        $metadata = !empty($include['metadata']) ? self::safe_metadata((string)self::field($version, ['metadata'], '{}')) : '{}';

        $files = [];
        if (!empty($include['files']) && self::can_download_version($context, $media, $version)) {
            $files = self::version_files($context, $version, !empty($include['hashes']));
        }

        return [
            'id' => (int)$version->id,
            'uuid' => (string)self::field($version, ['uuid'], ''),
            'mediaid' => (int)self::field($version, ['mediaid'], 0),
            'versionnumber' => (int)self::field($version, ['versionnumber', 'versionno', 'number'], 0),
            'label' => (string)self::field($version, ['label', 'title', 'name'], ''),
            'status' => (string)self::field($version, ['status'], ''),
            'filearea' => (string)self::field($version, ['filearea'], ''),
            'filename' => (string)self::field($version, ['filename'], ''),
            'filesize' => (int)self::field($version, ['filesize'], 0),
            'mimetype' => (string)self::field($version, ['mimetype', 'mime'], ''),
            'contenthash' => !empty($include['hashes']) ? (string)self::field($version, ['contenthash', 'filehash'], '') : '',
            'iscurrent' => (bool)self::field($version, ['iscurrent'], 0),
            'createdby' => (int)self::field($version, ['createdby', 'userid'], 0),
            'modifiedby' => (int)self::field($version, ['modifiedby'], 0),
            'timecreated' => (int)self::field($version, ['timecreated'], 0),
            'timemodified' => (int)self::field($version, ['timemodified'], 0),
            'metadata' => $metadata,
            'files' => $files,
        ];
    }

    /**
     * Return files for one version.
     *
     * @param context_module $context Context.
     * @param stdClass $version Version.
     * @param bool $includehashes Include hashes.
     * @return array<int, array<string, mixed>>
     */
    protected static function version_files(context_module $context, stdClass $version, bool $includehashes): array {
        $fs = get_file_storage();
        $versionid = (int)$version->id;
        $files = [];

        $candidateareas = self::VERSION_FILEAREAS;
        $primaryarea = (string)self::field($version, ['filearea'], '');
        if ($primaryarea !== '') {
            array_unshift($candidateareas, $primaryarea);
            $candidateareas = array_values(array_unique($candidateareas));
        }

        foreach ($candidateareas as $filearea) {
            $storedfiles = $fs->get_area_files(
                (int)$context->id,
                self::COMPONENT,
                $filearea,
                $versionid,
                'filename',
                false
            );

            foreach ($storedfiles as $file) {
                if ($file->is_directory()) {
                    continue;
                }

                $url = moodle_url::make_pluginfile_url(
                    $file->get_contextid(),
                    $file->get_component(),
                    $file->get_filearea(),
                    $file->get_itemid(),
                    $file->get_filepath(),
                    $file->get_filename(),
                    false
                );

                $downloadurl = moodle_url::make_pluginfile_url(
                    $file->get_contextid(),
                    $file->get_component(),
                    $file->get_filearea(),
                    $file->get_itemid(),
                    $file->get_filepath(),
                    $file->get_filename(),
                    true
                );

                $files[] = [
                    'filearea' => $filearea,
                    'filename' => $file->get_filename(),
                    'filepath' => $file->get_filepath(),
                    'filesize' => $file->get_filesize(),
                    'mimetype' => $file->get_mimetype(),
                    'contenthash' => $includehashes ? $file->get_contenthash() : '',
                    'url' => $url->out(false),
                    'downloadurl' => $downloadurl->out(false),
                ];
            }
        }

        return $files;
    }

    /**
     * Return whether current user may view this media record.
     *
     * @param context_module $context Context.
     * @param stdClass $media Media record.
     * @return bool
     */
    protected static function can_view_media(context_module $context, stdClass $media): bool {
        if (class_exists('\\mod_uckkarchive\\local\\media_policy') &&
                method_exists('\\mod_uckkarchive\\local\\media_policy', 'can_view_media')) {
            return \mod_uckkarchive\local\media_policy::can_view_media($context, $media);
        }

        if (self::is_restricted_media($media)) {
            return has_capability('mod/uckkarchive:viewrestrictedmedia', $context) ||
                has_capability('mod/uckkarchive:viewrestricted', $context) ||
                (self::is_culturally_restricted_media($media) &&
                    has_capability('mod/uckkarchive:viewculturallyrestricted', $context));
        }

        return has_capability('mod/uckkarchive:viewmedia', $context);
    }

    /**
     * Return whether current user may view this version.
     *
     * @param context_module $context Context.
     * @param stdClass $media Media.
     * @param stdClass $version Version.
     * @return bool
     */
    protected static function can_view_version(context_module $context, stdClass $media, stdClass $version): bool {
        $status = (string)self::field($version, ['status'], '');

        if ($status === 'deleted_soft') {
            return has_capability('mod/uckkarchive:deletemedia', $context);
        }

        if (self::is_restricted_media($media) || $status === 'restricted') {
            return has_capability('mod/uckkarchive:viewrestrictedmedia', $context) ||
                has_capability('mod/uckkarchive:viewrestricted', $context) ||
                (self::is_culturally_restricted_media($media) &&
                    has_capability('mod/uckkarchive:viewculturallyrestricted', $context));
        }

        return has_capability('mod/uckkarchive:viewmedia', $context);
    }

    /**
     * Return whether current user may see file URLs for this version.
     *
     * @param context_module $context Context.
     * @param stdClass $media Media.
     * @param stdClass $version Version.
     * @return bool
     */
    protected static function can_download_version(context_module $context, stdClass $media, stdClass $version): bool {
        if (!has_capability('mod/uckkarchive:downloadmedia', $context)) {
            return false;
        }

        if (class_exists('\\mod_uckkarchive\\local\\media_policy') &&
                method_exists('\\mod_uckkarchive\\local\\media_policy', 'can_download_media')) {
            return \mod_uckkarchive\local\media_policy::can_download_media($context, $media);
        }

        return self::can_view_version($context, $media, $version);
    }

    /**
     * Return restricted media flag.
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
     * Return culturally restricted media flag.
     *
     * @param stdClass $media Media.
     * @return bool
     */
    protected static function is_culturally_restricted_media(stdClass $media): bool {
        if (class_exists('\\mod_uckkarchive\\local\\media_policy') &&
                method_exists('\\mod_uckkarchive\\local\\media_policy', 'is_culturally_restricted')) {
            return \mod_uckkarchive\local\media_policy::is_culturally_restricted($media);
        }

        return (string)self::field($media, ['visibility'], '') === 'restricted_cultural' ||
            !empty($media->culturalprotocol);
    }

    /**
     * Return permissions.
     *
     * @param context_module $context Context.
     * @param stdClass $media Media.
     * @return array<string, bool>
     */
    protected static function permissions(context_module $context, stdClass $media): array {
        return [
            'viewmedia' => has_capability('mod/uckkarchive:viewmedia', $context),
            'downloadmedia' => has_capability('mod/uckkarchive:downloadmedia', $context),
            'versionmedia' => has_capability('mod/uckkarchive:versionmedia', $context),
            'viewrestrictedmedia' => has_capability('mod/uckkarchive:viewrestrictedmedia', $context),
            'viewculturallyrestricted' => has_capability('mod/uckkarchive:viewculturallyrestricted', $context),
        ];
    }

    /**
     * Normalize include options.
     *
     * @param array<string, mixed> $include Include options.
     * @return array<string, bool>
     */
    protected static function normalise_include(array $include): array {
        $defaults = [
            'deleted' => false,
            'files' => true,
            'metadata' => true,
            'hashes' => true,
        ];

        $include = array_merge($defaults, $include);

        foreach ($defaults as $key => $default) {
            $include[$key] = !empty($include[$key]);
        }

        return $include;
    }

    /**
     * Return safe metadata JSON.
     *
     * @param string $metadata Metadata JSON.
     * @return string
     */
    protected static function safe_metadata(string $metadata): string {
        $metadata = trim($metadata);
        if ($metadata === '') {
            return '{}';
        }

        $decoded = json_decode($metadata, true);
        if (!is_array($decoded)) {
            return '{}';
        }

        $json = json_encode($decoded, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);

        return $json === false ? '{}' : $json;
    }

    /**
     * Return version sort SQL.
     *
     * @param array<string, object> $columns Columns.
     * @return string
     */
    protected static function version_sort_sql(array $columns): string {
        if (array_key_exists('versionnumber', $columns)) {
            return 'versionnumber DESC, id DESC';
        }

        if (array_key_exists('versionno', $columns)) {
            return 'versionno DESC, id DESC';
        }

        return 'id DESC';
    }

    /**
     * Return field value from record.
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
     * Return whether table exists.
     *
     * @param string $table Table.
     * @return bool
     */
    protected static function table_exists(string $table): bool {
        global $DB;

        return $DB->get_manager()->table_exists(new \xmldb_table($table));
    }

    /**
     * Require table.
     *
     * @param string $table Table.
     * @return void
     * @throws moodle_exception
     */
    protected static function require_table(string $table): void {
        if (!self::table_exists($table)) {
            throw new moodle_exception('missingtable', 'error', '', $table);
        }
    }

    /**
     * Require positive id.
     *
     * @param int $id Id.
     * @param string $name Parameter name.
     * @return int
     */
    protected static function require_positive_id(int $id, string $name): int {
        if ($id <= 0) {
            throw new invalid_parameter_exception($name . ' must be a positive integer.');
        }

        return $id;
    }
}
