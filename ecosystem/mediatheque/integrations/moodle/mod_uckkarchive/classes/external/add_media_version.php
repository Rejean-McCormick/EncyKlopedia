<?php
// This file is part of Moodle - https://moodle.org/.
//
// Moodle is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// any later version.
//
// Moodle is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with Moodle. If not, see <https://www.gnu.org/licenses/>.

/**
 * External service for adding a media version.
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
require_once($CFG->dirroot . '/repository/lib.php');

use context_module;
use external_api;
use external_function_parameters;
use external_multiple_structure;
use external_single_structure;
use external_value;
use invalid_parameter_exception;
use mod_uckkarchive\local\media_file;
use mod_uckkarchive\local\media_policy;
use mod_uckkarchive\local\media_version;
use moodle_exception;
use stdClass;
use stored_file;

/**
 * Add a first-class version to an existing media object.
 *
 * Media files are never silently overwritten. File replacement, corrected
 * metadata, captions, transcripts, previews, thumbnails, and generated
 * derivatives are represented by media version records or version-linked files.
 *
 * Target service name:
 *
 * ```text
 * mod_uckkarchive_add_media_version
 * ```
 */
final class add_media_version extends external_api {
    /** Media table. */
    private const TABLE_MEDIA = 'uckkarchive_media';

    /** Media version table. */
    private const TABLE_VERSION = 'uckkarchive_media_version';

    /** Default media file area. */
    private const DEFAULT_FILEAREA = 'media_original';

    /** Default version status. */
    private const DEFAULT_STATUS = 'submitted';

    /**
     * Define service parameters.
     *
     * Either mediaid or mediauuid must be supplied.
     *
     * @return external_function_parameters
     */
    public static function execute_parameters(): external_function_parameters {
        return new external_function_parameters([
            'cmid' => new external_value(PARAM_INT, 'Course module id for the UCKK Archive instance.'),
            'mediaid' => new external_value(PARAM_INT, 'Media id. Optional when mediauuid is supplied.', VALUE_DEFAULT, 0),
            'mediauuid' => new external_value(PARAM_ALPHANUMEXT, 'Media UUID. Optional when mediaid is supplied.', VALUE_DEFAULT, ''),
            'draftitemid' => new external_value(PARAM_INT, 'Draft item id containing uploaded files.', VALUE_DEFAULT, 0),
            'filearea' => new external_value(PARAM_ALPHANUMEXT, 'Canonical media file area.', VALUE_DEFAULT, self::DEFAULT_FILEAREA),
            'label' => new external_value(PARAM_TEXT, 'Version label.', VALUE_DEFAULT, ''),
            'summary' => new external_value(PARAM_RAW, 'Version summary.', VALUE_DEFAULT, ''),
            'status' => new external_value(PARAM_ALPHANUMEXT, 'Version lifecycle status.', VALUE_DEFAULT, self::DEFAULT_STATUS),
            'visibility' => new external_value(PARAM_ALPHANUMEXT, 'Version visibility. Empty inherits media visibility.', VALUE_DEFAULT, ''),
            'audiencesuitability' => new external_value(PARAM_ALPHANUMEXT, 'Audience suitability. Empty inherits media suitability.', VALUE_DEFAULT, ''),
            'sourceversionid' => new external_value(PARAM_INT, 'Source media version id for derivative/replacement links.', VALUE_DEFAULT, 0),
            'makecurrent' => new external_value(PARAM_BOOL, 'Whether this version becomes the current media version.', VALUE_DEFAULT, true),
            'metadatajson' => new external_value(PARAM_RAW, 'Additional JSON metadata.', VALUE_DEFAULT, '{}'),
            'metadata' => new external_single_structure([
                'reason' => new external_value(PARAM_TEXT, 'Reason for creating this version.', VALUE_DEFAULT, ''),
                'technicalnotes' => new external_value(PARAM_RAW, 'Technical notes.', VALUE_DEFAULT, ''),
                'language' => new external_value(PARAM_ALPHANUMEXT, 'Language code.', VALUE_DEFAULT, ''),
                'durationseconds' => new external_value(PARAM_INT, 'Duration in seconds, when known.', VALUE_DEFAULT, 0),
                'pagecount' => new external_value(PARAM_INT, 'Page count, when known.', VALUE_DEFAULT, 0),
                'captionlanguage' => new external_value(PARAM_ALPHANUMEXT, 'Caption language, when relevant.', VALUE_DEFAULT, ''),
                'transcriptlanguage' => new external_value(PARAM_ALPHANUMEXT, 'Transcript language, when relevant.', VALUE_DEFAULT, ''),
                'generated' => new external_value(PARAM_BOOL, 'Whether this version is generated.', VALUE_DEFAULT, false),
            ], 'Structured version metadata.', VALUE_DEFAULT, []),
        ]);
    }

    /**
     * Execute service.
     *
     * @param int $cmid Course module id.
     * @param int $mediaid Media id.
     * @param string $mediauuid Media UUID.
     * @param int $draftitemid Draft item id.
     * @param string $filearea Canonical media file area.
     * @param string $label Version label.
     * @param string $summary Version summary.
     * @param string $status Version status.
     * @param string $visibility Version visibility.
     * @param string $audiencesuitability Audience suitability.
     * @param int $sourceversionid Source version id.
     * @param bool $makecurrent Make current version.
     * @param string $metadatajson Extra metadata JSON.
     * @param array<string,mixed> $metadata Structured metadata.
     * @return array<string,mixed>
     */
    public static function execute(
        int $cmid,
        int $mediaid = 0,
        string $mediauuid = '',
        int $draftitemid = 0,
        string $filearea = self::DEFAULT_FILEAREA,
        string $label = '',
        string $summary = '',
        string $status = self::DEFAULT_STATUS,
        string $visibility = '',
        string $audiencesuitability = '',
        int $sourceversionid = 0,
        bool $makecurrent = true,
        string $metadatajson = '{}',
        array $metadata = []
    ): array {
        global $DB, $USER;

        $params = self::validate_parameters(self::execute_parameters(), [
            'cmid' => $cmid,
            'mediaid' => $mediaid,
            'mediauuid' => $mediauuid,
            'draftitemid' => $draftitemid,
            'filearea' => $filearea,
            'label' => $label,
            'summary' => $summary,
            'status' => $status,
            'visibility' => $visibility,
            'audiencesuitability' => $audiencesuitability,
            'sourceversionid' => $sourceversionid,
            'makecurrent' => $makecurrent,
            'metadatajson' => $metadatajson,
            'metadata' => $metadata,
        ]);

        [$course, $cm, $archive, $context] = self::load_page((int)$params['cmid']);
        self::validate_context($context);
        require_login($course, false, $cm);

        if (!self::table_exists(self::TABLE_MEDIA)) {
            throw new moodle_exception('missingtable', 'error', '', self::TABLE_MEDIA);
        }

        if (!self::table_exists(self::TABLE_VERSION)) {
            throw new moodle_exception('missingtable', 'error', '', self::TABLE_VERSION);
        }

        $media = self::load_media($archive, (int)$params['mediaid'], (string)$params['mediauuid']);

        require_capability('mod/uckkarchive:versionmedia', $context);
        if (class_exists(media_policy::class) && method_exists(media_policy::class, 'require_version_media')) {
            media_policy::require_version_media($context, $media);
        }

        if (!class_exists(media_version::class) || !method_exists(media_version::class, 'create')) {
            throw new \coding_exception('The media version domain service must implement media_version::create().');
        }

        $filearea = self::normalise_filearea((string)$params['filearea']);
        $status = self::normalise_status((string)$params['status']);

        $draftitemid = max(0, (int)$params['draftitemid']);
        $sourceversionid = max(0, (int)$params['sourceversionid']);

        $mergedmetadata = self::merge_metadata((string)$params['metadatajson'], (array)$params['metadata']);
        $now = time();

        $versiondata = [
            'archiveid' => (int)$archive->id,
            'courseid' => (int)$course->id,
            'cmid' => (int)$cm->id,
            'contextid' => (int)$context->id,
            'label' => clean_param((string)$params['label'], PARAM_TEXT),
            'summary' => clean_param((string)$params['summary'], PARAM_RAW),
            'filearea' => $filearea,
            'filepath' => '/',
            'status' => $status,
            'sourceversionid' => $sourceversionid,
            'iscurrent' => !empty($params['makecurrent']) ? 1 : 0,
            'createdby' => (int)$USER->id,
            'modifiedby' => (int)$USER->id,
            'timecreated' => $now,
            'timemodified' => $now,
            'metadata' => $mergedmetadata,
        ];

        if ((string)$params['visibility'] !== '') {
            $versiondata['visibility'] = self::normalise_visibility((string)$params['visibility']);
        }

        if ((string)$params['audiencesuitability'] !== '') {
            $versiondata['audiencesuitability'] = self::normalise_suitability((string)$params['audiencesuitability']);
        }

        $transaction = $DB->start_delegated_transaction();

        $version = media_version::create($media, $versiondata, null);

        $filemetadata = [];
        if ($draftitemid > 0) {
            $filemetadata = self::save_draft_files_and_get_metadata($draftitemid, $context, $filearea, (int)$version->id);
            if (!empty($filemetadata)) {
                $version = self::update_version_file_metadata((int)$version->id, $filemetadata);
            }
        }

        if (!empty($params['makecurrent']) && method_exists(media_version::class, 'make_current')) {
            $version = media_version::make_current((int)$version->id);
        }

        $transaction->allow_commit();

        self::trigger_version_event($context, $media, $version);

        return [
            'version' => self::format_version_response($version, $context),
            'mediaid' => (int)$media->id,
            'mediauuid' => (string)($media->uuid ?? ''),
            'warnings' => [],
        ];
    }

    /**
     * Describe service return structure.
     *
     * @return external_single_structure
     */
    public static function execute_returns(): external_single_structure {
        return new external_single_structure([
            'version' => new external_single_structure([
                'id' => new external_value(PARAM_INT, 'Version id.'),
                'uuid' => new external_value(PARAM_RAW, 'Stable version UUID.'),
                'mediaid' => new external_value(PARAM_INT, 'Media id.'),
                'versionnumber' => new external_value(PARAM_INT, 'Version number.'),
                'label' => new external_value(PARAM_TEXT, 'Version label.'),
                'summary' => new external_value(PARAM_RAW, 'Version summary.'),
                'filearea' => new external_value(PARAM_ALPHANUMEXT, 'File area.'),
                'fileitemid' => new external_value(PARAM_INT, 'File API item id.'),
                'filepath' => new external_value(PARAM_RAW, 'File path.'),
                'filename' => new external_value(PARAM_FILE, 'File name.'),
                'contenthash' => new external_value(PARAM_RAW, 'Content hash.'),
                'filesize' => new external_value(PARAM_INT, 'File size.'),
                'mimetype' => new external_value(PARAM_RAW, 'MIME type.'),
                'mediatype' => new external_value(PARAM_ALPHANUMEXT, 'Media type.'),
                'status' => new external_value(PARAM_ALPHANUMEXT, 'Status.'),
                'visibility' => new external_value(PARAM_ALPHANUMEXT, 'Visibility.'),
                'audiencesuitability' => new external_value(PARAM_ALPHANUMEXT, 'Audience suitability.'),
                'iscurrent' => new external_value(PARAM_BOOL, 'Whether this is the current version.'),
                'downloadurl' => new external_value(PARAM_RAW, 'Download URL, if a file exists.'),
                'timecreated' => new external_value(PARAM_INT, 'Created timestamp.'),
                'timemodified' => new external_value(PARAM_INT, 'Modified timestamp.'),
                'metadatajson' => new external_value(PARAM_RAW, 'Version metadata JSON.'),
            ]),
            'mediaid' => new external_value(PARAM_INT, 'Media id.'),
            'mediauuid' => new external_value(PARAM_RAW, 'Media UUID.'),
            'warnings' => new external_multiple_structure(
                new external_single_structure([
                    'item' => new external_value(PARAM_TEXT, 'Warning item.'),
                    'itemid' => new external_value(PARAM_INT, 'Warning item id.'),
                    'warningcode' => new external_value(PARAM_ALPHANUMEXT, 'Warning code.'),
                    'message' => new external_value(PARAM_TEXT, 'Warning message.'),
                ])
            ),
        ]);
    }

    /**
     * Load page objects.
     *
     * @param int $cmid Course module id.
     * @return array{0:stdClass,1:stdClass,2:stdClass,3:context_module}
     */
    private static function load_page(int $cmid): array {
        global $DB;

        $cmid = self::require_positive_int($cmid, 'cmid');
        if (function_exists('\\uckkarchive_require_page')) {
            return \uckkarchive_require_page($cmid, 0);
        }

        $cm = get_coursemodule_from_id('uckkarchive', $cmid, 0, false, MUST_EXIST);
        $course = $DB->get_record('course', ['id' => $cm->course], '*', MUST_EXIST);
        $archive = $DB->get_record('uckkarchive', ['id' => $cm->instance], '*', MUST_EXIST);
        $context = context_module::instance($cm->id);

        return [$course, $cm, $archive, $context];
    }

    /**
     * Load a media record owned by the archive instance.
     *
     * @param stdClass $archive Archive instance.
     * @param int $mediaid Media id.
     * @param string $mediauuid Media UUID.
     * @return stdClass
     */
    private static function load_media(stdClass $archive, int $mediaid, string $mediauuid): stdClass {
        global $DB;

        $fields = $DB->get_columns(self::TABLE_MEDIA);
        $archivefield = self::first_existing_field($fields, ['archiveid', 'uckkarchiveid']);
        if ($archivefield === null) {
            throw new moodle_exception('missingfield', 'error', '', self::TABLE_MEDIA . '.archiveid');
        }

        $conditions = [$archivefield => (int)$archive->id];

        if ($mediaid > 0) {
            $conditions['id'] = $mediaid;
        } else {
            $mediauuid = trim($mediauuid);
            if ($mediauuid === '') {
                throw new invalid_parameter_exception('Either mediaid or mediauuid is required.');
            }

            if (!isset($fields['uuid'])) {
                throw new invalid_parameter_exception('Media UUID lookup is not available because uuid field is missing.');
            }

            $conditions['uuid'] = clean_param($mediauuid, PARAM_ALPHANUMEXT);
        }

        return $DB->get_record(self::TABLE_MEDIA, $conditions, '*', MUST_EXIST);
    }

    /**
     * Save draft files and return first stored file metadata.
     *
     * @param int $draftitemid Draft item id.
     * @param context_module $context Context.
     * @param string $filearea File area.
     * @param int $versionid Version id used as File API item id.
     * @return array<string,mixed>
     */
    private static function save_draft_files_and_get_metadata(
        int $draftitemid,
        context_module $context,
        string $filearea,
        int $versionid
    ): array {
        if (class_exists(media_file::class) && method_exists(media_file::class, 'save_draft_area_files')) {
            media_file::save_draft_area_files($draftitemid, $context, $filearea, $versionid);
            $file = media_file::get_first_file($context, $filearea, $versionid);
        } else {
            global $CFG;
            require_once($CFG->libdir . '/filelib.php');

            file_save_draft_area_files(
                $draftitemid,
                $context->id,
                'mod_uckkarchive',
                $filearea,
                $versionid,
                [
                    'subdirs' => false,
                    'maxbytes' => 0,
                    'maxfiles' => 1,
                    'return_types' => \FILE_INTERNAL,
                ]
            );

            $fs = get_file_storage();
            $files = $fs->get_area_files($context->id, 'mod_uckkarchive', $filearea, $versionid, 'filename', false);
            $file = null;
            foreach ($files as $candidate) {
                if (!$candidate->is_directory()) {
                    $file = $candidate;
                    break;
                }
            }
        }

        if (!$file instanceof stored_file) {
            return [];
        }

        return [
            'filearea' => $file->get_filearea(),
            'fileitemid' => (int)$file->get_itemid(),
            'filepath' => $file->get_filepath(),
            'filename' => $file->get_filename(),
            'contenthash' => $file->get_contenthash(),
            'filesize' => (int)$file->get_filesize(),
            'mimetype' => (string)$file->get_mimetype(),
        ];
    }

    /**
     * Update a version with File API metadata after draft files are saved.
     *
     * @param int $versionid Version id.
     * @param array<string,mixed> $filemetadata File metadata.
     * @return stdClass
     */
    private static function update_version_file_metadata(int $versionid, array $filemetadata): stdClass {
        global $DB, $USER;

        $version = $DB->get_record(self::TABLE_VERSION, ['id' => $versionid], '*', MUST_EXIST);
        $columns = $DB->get_columns(self::TABLE_VERSION);

        foreach ($filemetadata as $field => $value) {
            if (array_key_exists($field, $columns)) {
                $version->{$field} = $value;
            }
        }

        if (array_key_exists('modifiedby', $columns)) {
            $version->modifiedby = (int)$USER->id;
        }
        if (array_key_exists('timemodified', $columns)) {
            $version->timemodified = time();
        }

        $DB->update_record(self::TABLE_VERSION, $version);

        if (class_exists(media_version::class) && method_exists(media_version::class, 'get')) {
            return media_version::get($versionid);
        }

        return $DB->get_record(self::TABLE_VERSION, ['id' => $versionid], '*', MUST_EXIST);
    }

    /**
     * Format version response.
     *
     * @param stdClass $version Version record.
     * @param context_module $context Context.
     * @return array<string,mixed>
     */
    private static function format_version_response(stdClass $version, context_module $context): array {
        $downloadurl = '';
        $filearea = (string)self::field($version, ['filearea'], self::DEFAULT_FILEAREA);
        $fileitemid = (int)self::field($version, ['fileitemid', 'id'], (int)$version->id);
        $filename = (string)self::field($version, ['filename'], '');

        if ($filename !== '' && class_exists(media_file::class) && method_exists(media_file::class, 'get_file')) {
            $file = media_file::get_file(
                $context,
                $filearea,
                $fileitemid,
                $filename,
                (string)self::field($version, ['filepath'], '/')
            );
            if ($file) {
                $downloadurl = media_file::get_file_url($file, true)->out(false);
            }
        }

        return [
            'id' => (int)$version->id,
            'uuid' => (string)self::field($version, ['uuid'], ''),
            'mediaid' => (int)self::field($version, ['mediaid'], 0),
            'versionnumber' => (int)self::field($version, ['versionnumber', 'versionno'], 0),
            'label' => (string)self::field($version, ['label'], ''),
            'summary' => (string)self::field($version, ['summary'], ''),
            'filearea' => $filearea,
            'fileitemid' => $fileitemid,
            'filepath' => (string)self::field($version, ['filepath'], '/'),
            'filename' => $filename,
            'contenthash' => (string)self::field($version, ['contenthash', 'filehash'], ''),
            'filesize' => (int)self::field($version, ['filesize'], 0),
            'mimetype' => (string)self::field($version, ['mimetype'], ''),
            'mediatype' => (string)self::field($version, ['mediatype'], ''),
            'status' => (string)self::field($version, ['status'], ''),
            'visibility' => (string)self::field($version, ['visibility'], ''),
            'audiencesuitability' => (string)self::field($version, ['audiencesuitability'], ''),
            'iscurrent' => !empty($version->iscurrent),
            'downloadurl' => $downloadurl,
            'timecreated' => (int)self::field($version, ['timecreated'], 0),
            'timemodified' => (int)self::field($version, ['timemodified'], 0),
            'metadatajson' => self::metadata_json_for_return($version),
        ];
    }

    /**
     * Trigger media_version_created when the event class exists.
     *
     * @param context_module $context Context.
     * @param stdClass $media Media record.
     * @param stdClass $version Version record.
     * @return void
     */
    private static function trigger_version_event(context_module $context, stdClass $media, stdClass $version): void {
        $eventclass = '\\mod_uckkarchive\\event\\media_version_created';

        if (!class_exists($eventclass)) {
            return;
        }

        try {
            $event = $eventclass::create([
                'context' => $context,
                'objectid' => (int)$version->id,
                'other' => [
                    'mediaid' => (int)$media->id,
                    'mediauuid' => (string)($media->uuid ?? ''),
                    'versionuuid' => (string)($version->uuid ?? ''),
                    'filearea' => (string)($version->filearea ?? ''),
                ],
            ]);
            $event->trigger();
        } catch (\Throwable $ignored) {
            // Version creation must not fail because the event class is not ready.
        }
    }

    /**
     * Merge JSON metadata and structured metadata.
     *
     * @param string $metadatajson JSON metadata.
     * @param array<string,mixed> $metadata Structured metadata.
     * @return array<string,mixed>
     */
    private static function merge_metadata(string $metadatajson, array $metadata): array {
        $decoded = json_decode(trim($metadatajson) === '' ? '{}' : $metadatajson, true);
        if (!is_array($decoded)) {
            throw new invalid_parameter_exception('Invalid metadatajson.');
        }

        $clean = [];
        foreach (array_merge($decoded, $metadata) as $key => $value) {
            $cleankey = clean_param((string)$key, PARAM_ALPHANUMEXT);
            if ($cleankey === '') {
                continue;
            }

            if (is_bool($value) || is_int($value) || is_float($value) || $value === null) {
                $clean[$cleankey] = $value;
                continue;
            }

            if (is_array($value)) {
                $clean[$cleankey] = self::clean_array($value);
                continue;
            }

            $clean[$cleankey] = clean_param((string)$value, PARAM_TEXT);
        }

        return $clean;
    }

    /**
     * Clean nested array metadata.
     *
     * @param array<mixed> $data Input data.
     * @return array<mixed>
     */
    private static function clean_array(array $data): array {
        $clean = [];

        foreach ($data as $key => $value) {
            $cleankey = is_int($key) ? $key : clean_param((string)$key, PARAM_ALPHANUMEXT);
            if ($cleankey === '') {
                continue;
            }

            if (is_array($value)) {
                $clean[$cleankey] = self::clean_array($value);
            } else if (is_bool($value) || is_int($value) || is_float($value) || $value === null) {
                $clean[$cleankey] = $value;
            } else {
                $clean[$cleankey] = clean_param((string)$value, PARAM_TEXT);
            }
        }

        return $clean;
    }

    /**
     * Return metadata JSON for external response.
     *
     * @param stdClass $version Version record.
     * @return string
     */
    private static function metadata_json_for_return(stdClass $version): string {
        $metadata = (string)self::field($version, ['metadata'], '{}');
        if ($metadata === '') {
            return '{}';
        }

        json_decode($metadata);
        if (json_last_error() !== JSON_ERROR_NONE) {
            return '{}';
        }

        return $metadata;
    }

    /**
     * Normalise a media file area.
     *
     * @param string $filearea File area.
     * @return string
     */
    private static function normalise_filearea(string $filearea): string {
        $filearea = clean_param(trim($filearea), PARAM_ALPHANUMEXT);

        if (class_exists(media_file::class) && method_exists(media_file::class, 'require_media_filearea')) {
            return media_file::require_media_filearea($filearea);
        }

        $allowed = [
            'media_original',
            'media_preview',
            'media_thumbnail',
            'media_derivative',
            'media_caption',
            'media_transcript',
            'media_attachment',
        ];

        if (!in_array($filearea, $allowed, true)) {
            throw new invalid_parameter_exception('Invalid media version file area.');
        }

        return $filearea;
    }

    /**
     * Normalise version status.
     *
     * @param string $status Status.
     * @return string
     */
    private static function normalise_status(string $status): string {
        $status = clean_param(trim($status), PARAM_ALPHANUMEXT);

        $allowed = class_exists(media_version::class) && method_exists(media_version::class, 'statuses')
            ? media_version::statuses()
            : ['draft', 'submitted', 'active', 'restricted', 'superseded', 'archived', 'deleted_soft'];

        if (!in_array($status, $allowed, true)) {
            throw new invalid_parameter_exception('Invalid media version status.');
        }

        return $status;
    }

    /**
     * Normalise visibility.
     *
     * @param string $visibility Visibility.
     * @return string
     */
    private static function normalise_visibility(string $visibility): string {
        $visibility = clean_param(trim($visibility), PARAM_ALPHANUMEXT);
        if ($visibility === 'institutional') {
            $visibility = 'institution';
        }

        $allowed = [
            'private',
            'user',
            'group',
            'course',
            'cohort',
            'program',
            'institution',
            'public',
            'restricted',
            'restricted_integrity',
            'restricted_cultural',
        ];

        if (!in_array($visibility, $allowed, true)) {
            throw new invalid_parameter_exception('Invalid media version visibility.');
        }

        return $visibility;
    }

    /**
     * Normalise audience suitability.
     *
     * @param string $suitability Audience suitability.
     * @return string
     */
    private static function normalise_suitability(string $suitability): string {
        $suitability = clean_param(trim($suitability), PARAM_ALPHANUMEXT);

        $allowed = [
            'general',
            'guided',
            'mature',
            'restricted',
            'restricted_cultural',
            'restricted_integrity',
            'staff_only',
        ];

        if (!in_array($suitability, $allowed, true)) {
            throw new invalid_parameter_exception('Invalid audience suitability.');
        }

        return $suitability;
    }

    /**
     * Return whether a table exists.
     *
     * @param string $tablename Table name without Moodle braces.
     * @return bool
     */
    private static function table_exists(string $tablename): bool {
        global $DB;

        return $DB->get_manager()->table_exists(new \xmldb_table($tablename));
    }

    /**
     * Return first existing field from candidates.
     *
     * @param array<string,object> $fields DB fields.
     * @param string[] $candidates Candidate names.
     * @return string|null
     */
    private static function first_existing_field(array $fields, array $candidates): ?string {
        foreach ($candidates as $candidate) {
            if (isset($fields[$candidate])) {
                return $candidate;
            }
        }

        return null;
    }

    /**
     * Return a field value from a record.
     *
     * @param stdClass $record Record.
     * @param string[] $fields Candidate fields.
     * @param mixed $default Default value.
     * @return mixed
     */
    private static function field(stdClass $record, array $fields, mixed $default = null): mixed {
        foreach ($fields as $field) {
            if (property_exists($record, $field) && $record->{$field} !== null && $record->{$field} !== '') {
                return $record->{$field};
            }
        }

        return $default;
    }

    /**
     * Require a positive integer.
     *
     * @param int $value Value.
     * @param string $name Parameter name.
     * @return int
     */
    private static function require_positive_int(int $value, string $name): int {
        if ($value <= 0) {
            throw new invalid_parameter_exception('Invalid ' . $name . '.');
        }

        return $value;
    }
}
