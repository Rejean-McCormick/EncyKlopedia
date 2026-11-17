<?php
// This file is part of Moodle - https://moodle.org/
//
// Moodle is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// any later version.

/**
 * Media version domain service for mod_uckkarchive.
 *
 * Media versions are first-class records. The archive never silently
 * overwrites an original media file. Replacements, corrections, captions,
 * transcripts, generated derivatives, and technical changes are represented
 * through version records or related media files.
 *
 * @package    mod_uckkarchive
 * @copyright  2026 Univers-Cité King Klown
 * @license    https://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later
 */

declare(strict_types=1);

namespace mod_uckkarchive\local;

defined('MOODLE_INTERNAL') || die();

use coding_exception;
use context_module;
use dml_exception;
use invalid_parameter_exception;
use moodle_exception;
use stored_file;
use stdClass;

/**
 * Domain service for media versions.
 */
final class media_version {
    /** @var string Media table. */
    public const MEDIA_TABLE = 'uckkarchive_media';

    /** @var string Media version table. */
    public const TABLE = 'uckkarchive_media_version';

    /** @var string Draft status. */
    public const STATUS_DRAFT = 'draft';

    /** @var string Submitted status. */
    public const STATUS_SUBMITTED = 'submitted';

    /** @var string Active status. */
    public const STATUS_ACTIVE = 'active';

    /** @var string Restricted status. */
    public const STATUS_RESTRICTED = 'restricted';

    /** @var string Superseded status. */
    public const STATUS_SUPERSEDED = 'superseded';

    /** @var string Archived status. */
    public const STATUS_ARCHIVED = 'archived';

    /** @var string Soft deleted status. */
    public const STATUS_DELETED_SOFT = 'deleted_soft';

    /** @var string Original media file area. */
    public const FILEAREA_ORIGINAL = 'media_original';

    /** @var string Preview media file area. */
    public const FILEAREA_PREVIEW = 'media_preview';

    /** @var string Thumbnail media file area. */
    public const FILEAREA_THUMBNAIL = 'media_thumbnail';

    /** @var string Derivative media file area. */
    public const FILEAREA_DERIVATIVE = 'media_derivative';

    /** @var string Caption media file area. */
    public const FILEAREA_CAPTION = 'media_caption';

    /** @var string Transcript media file area. */
    public const FILEAREA_TRANSCRIPT = 'media_transcript';

    /** @var string Attachment media file area. */
    public const FILEAREA_ATTACHMENT = 'media_attachment';

    /** @var string Default file path. */
    private const DEFAULT_FILEPATH = '/';

    /**
     * Return allowed version statuses.
     *
     * @return string[]
     */
    public static function statuses(): array {
        return [
            self::STATUS_DRAFT,
            self::STATUS_SUBMITTED,
            self::STATUS_ACTIVE,
            self::STATUS_RESTRICTED,
            self::STATUS_SUPERSEDED,
            self::STATUS_ARCHIVED,
            self::STATUS_DELETED_SOFT,
        ];
    }

    /**
     * Return allowed media file areas for version records.
     *
     * @return string[]
     */
    public static function fileareas(): array {
        return [
            self::FILEAREA_ORIGINAL,
            self::FILEAREA_PREVIEW,
            self::FILEAREA_THUMBNAIL,
            self::FILEAREA_DERIVATIVE,
            self::FILEAREA_CAPTION,
            self::FILEAREA_TRANSCRIPT,
            self::FILEAREA_ATTACHMENT,
        ];
    }

    /**
     * Get one version by id.
     *
     * @param int $id Version id.
     * @param int $strictness Moodle record strictness.
     * @return stdClass|false
     * @throws dml_exception
     */
    public static function get(int $id, int $strictness = MUST_EXIST): stdClass|false {
        global $DB;

        if ($id <= 0) {
            throw new invalid_parameter_exception('Invalid media version id.');
        }

        return $DB->get_record(self::TABLE, ['id' => $id], '*', $strictness);
    }

    /**
     * Get one version by UUID.
     *
     * @param string $uuid Version UUID.
     * @param int $strictness Moodle record strictness.
     * @return stdClass|false
     * @throws dml_exception
     */
    public static function get_by_uuid(string $uuid, int $strictness = MUST_EXIST): stdClass|false {
        global $DB;

        $uuid = trim($uuid);
        if ($uuid === '') {
            throw new invalid_parameter_exception('Invalid media version UUID.');
        }

        return $DB->get_record(self::TABLE, ['uuid' => $uuid], '*', $strictness);
    }

    /**
     * Get all versions for a media object.
     *
     * @param int $mediaid Media id.
     * @param bool $includedeleted Whether soft-deleted versions are included.
     * @return stdClass[]
     * @throws dml_exception
     */
    public static function get_versions(int $mediaid, bool $includedeleted = false): array {
        global $DB;

        if ($mediaid <= 0) {
            throw new invalid_parameter_exception('Invalid media id.');
        }

        $conditions = ['mediaid' => $mediaid];

        if ($includedeleted) {
            return $DB->get_records(self::TABLE, $conditions, 'versionnumber DESC, id DESC');
        }

        $sql = 'mediaid = :mediaid AND status <> :deletedstatus';
        $params = [
            'mediaid' => $mediaid,
            'deletedstatus' => self::STATUS_DELETED_SOFT,
        ];

        return $DB->get_records_select(self::TABLE, $sql, $params, 'versionnumber DESC, id DESC');
    }

    /**
     * Get current version for a media object.
     *
     * @param int $mediaid Media id.
     * @param int $strictness Moodle record strictness.
     * @return stdClass|false
     * @throws dml_exception
     */
    public static function get_current(int $mediaid, int $strictness = IGNORE_MISSING): stdClass|false {
        global $DB;

        if ($mediaid <= 0) {
            throw new invalid_parameter_exception('Invalid media id.');
        }

        $media = $DB->get_record(self::MEDIA_TABLE, ['id' => $mediaid], '*', MUST_EXIST);
        if (!empty($media->currentversionid)) {
            return $DB->get_record(self::TABLE, ['id' => $media->currentversionid], '*', $strictness);
        }

        return $DB->get_record(
            self::TABLE,
            ['mediaid' => $mediaid, 'iscurrent' => 1],
            '*',
            $strictness
        );
    }

    /**
     * Create the initial version for a media record.
     *
     * @param stdClass $media Media record.
     * @param stored_file|null $file Stored file linked to this version.
     * @param array<string,mixed> $data Version data overrides.
     * @return stdClass Created version record.
     * @throws coding_exception
     * @throws dml_exception
     * @throws moodle_exception
     */
    public static function create_initial(stdClass $media, ?stored_file $file = null, array $data = []): stdClass {
        if (empty($media->id)) {
            throw new invalid_parameter_exception('Media record must contain an id.');
        }

        if (self::count_versions((int)$media->id) > 0) {
            throw new moodle_exception('mediaversionalreadyexists', 'uckkarchive');
        }

        $data['versionnumber'] = 1;
        $data['iscurrent'] = 1;

        return self::create($media, $data, $file);
    }

    /**
     * Create a new version for a media record.
     *
     * @param stdClass $media Media record.
     * @param array<string,mixed> $data Version data.
     * @param stored_file|null $file Stored file linked to this version.
     * @return stdClass Created version record.
     * @throws dml_exception
     */
    public static function create(stdClass $media, array $data = [], ?stored_file $file = null): stdClass {
        global $DB, $USER;

        if (empty($media->id)) {
            throw new invalid_parameter_exception('Media record must contain an id.');
        }

        $mediaid = (int)$media->id;
        $now = time();

        $version = new stdClass();
        $version->uuid = self::normalise_uuid($data['uuid'] ?? null);
        $version->mediaid = $mediaid;
        $version->archiveid = (int)($data['archiveid'] ?? ($media->archiveid ?? 0));
        $version->courseid = (int)($data['courseid'] ?? ($media->courseid ?? ($media->course ?? 0)));
        $version->cmid = (int)($data['cmid'] ?? ($media->cmid ?? 0));
        $version->contextid = (int)($data['contextid'] ?? ($media->contextid ?? 0));
        $version->versionnumber = (int)($data['versionnumber'] ?? self::next_version_number($mediaid));
        $version->label = self::clean_optional_text($data['label'] ?? '');
        $version->summary = self::clean_optional_text($data['summary'] ?? '');
        $version->filearea = self::normalise_filearea((string)($data['filearea'] ?? self::FILEAREA_ORIGINAL));
        $version->fileitemid = (int)($data['fileitemid'] ?? 0);
        $version->filepath = self::normalise_filepath((string)($data['filepath'] ?? self::DEFAULT_FILEPATH));
        $version->filename = self::clean_optional_text($data['filename'] ?? '');
        $version->contenthash = self::clean_optional_text($data['contenthash'] ?? '');
        $version->filesize = (int)($data['filesize'] ?? 0);
        $version->mimetype = self::clean_optional_text($data['mimetype'] ?? '');
        $version->mediatype = self::clean_optional_text($data['mediatype'] ?? ($media->mediatype ?? ''));
        $version->status = self::normalise_status((string)($data['status'] ?? ($media->status ?? self::STATUS_DRAFT)));
        $version->visibility = self::clean_optional_text($data['visibility'] ?? ($media->visibility ?? 'restricted'));
        $version->audiencesuitability = self::clean_optional_text(
            $data['audiencesuitability'] ?? ($media->audiencesuitability ?? 'guided')
        );
        $version->sourceversionid = (int)($data['sourceversionid'] ?? 0);
        $version->iscurrent = !empty($data['iscurrent']) ? 1 : 0;
        $version->createdby = (int)($data['createdby'] ?? ($USER->id ?? 0));
        $version->modifiedby = (int)($data['modifiedby'] ?? ($USER->id ?? 0));
        $version->timecreated = (int)($data['timecreated'] ?? $now);
        $version->timemodified = (int)($data['timemodified'] ?? $now);
        $version->metadata = self::encode_metadata($data['metadata'] ?? []);

        if ($file !== null) {
            self::apply_file_metadata($version, $file);
        }

        self::validate_record($version);

        $transaction = $DB->start_delegated_transaction();

        if (!empty($version->iscurrent)) {
            self::clear_current_flag($mediaid);
        }

        $version->id = $DB->insert_record(self::TABLE, $version);

        if (!empty($version->iscurrent)) {
            self::update_media_current_version($mediaid, (int)$version->id, $version->status);
        }

        $transaction->allow_commit();

        return self::get((int)$version->id);
    }

    /**
     * Create a new version by media id.
     *
     * @param int $mediaid Media id.
     * @param array<string,mixed> $data Version data.
     * @param stored_file|null $file Stored file linked to this version.
     * @return stdClass Created version record.
     * @throws dml_exception
     */
    public static function create_for_mediaid(int $mediaid, array $data = [], ?stored_file $file = null): stdClass {
        global $DB;

        if ($mediaid <= 0) {
            throw new invalid_parameter_exception('Invalid media id.');
        }

        $media = $DB->get_record(self::MEDIA_TABLE, ['id' => $mediaid], '*', MUST_EXIST);

        return self::create($media, $data, $file);
    }

    /**
     * Mark a version as the current version.
     *
     * @param int $versionid Version id.
     * @return stdClass Updated version record.
     * @throws dml_exception
     */
    public static function make_current(int $versionid): stdClass {
        global $DB, $USER;

        $version = self::get($versionid);
        $mediaid = (int)$version->mediaid;

        $transaction = $DB->start_delegated_transaction();

        self::clear_current_flag($mediaid);

        $version->iscurrent = 1;
        $version->modifiedby = (int)($USER->id ?? 0);
        $version->timemodified = time();

        if ($version->status === self::STATUS_DRAFT || $version->status === self::STATUS_SUBMITTED) {
            $version->status = self::STATUS_ACTIVE;
        }

        $DB->update_record(self::TABLE, $version);
        self::update_media_current_version($mediaid, $versionid, $version->status);

        $transaction->allow_commit();

        return self::get($versionid);
    }

    /**
     * Update version metadata without changing the binary file.
     *
     * This is for administrative metadata corrections. File replacements must
     * create a new media version instead.
     *
     * @param int $versionid Version id.
     * @param array<string,mixed> $data Metadata fields.
     * @return stdClass Updated version record.
     * @throws dml_exception
     */
    public static function update_metadata(int $versionid, array $data): stdClass {
        global $DB, $USER;

        $version = self::get($versionid);

        $allowed = [
            'label',
            'summary',
            'status',
            'visibility',
            'audiencesuitability',
            'metadata',
        ];

        foreach ($allowed as $field) {
            if (!array_key_exists($field, $data)) {
                continue;
            }

            if ($field === 'status') {
                $version->status = self::normalise_status((string)$data[$field]);
                continue;
            }

            if ($field === 'metadata') {
                $version->metadata = self::encode_metadata($data[$field]);
                continue;
            }

            $version->{$field} = self::clean_optional_text($data[$field]);
        }

        $version->modifiedby = (int)($USER->id ?? 0);
        $version->timemodified = time();

        self::validate_record($version);

        $DB->update_record(self::TABLE, $version);

        if (!empty($version->iscurrent)) {
            self::update_media_current_version((int)$version->mediaid, (int)$version->id, $version->status);
        }

        return self::get($versionid);
    }

    /**
     * Soft-delete a media version.
     *
     * @param int $versionid Version id.
     * @return stdClass Updated version record.
     * @throws dml_exception
     * @throws moodle_exception
     */
    public static function soft_delete(int $versionid): stdClass {
        global $DB, $USER;

        $version = self::get($versionid);

        if (!empty($version->iscurrent)) {
            throw new moodle_exception('cannotdeletecurrentmediaversion', 'uckkarchive');
        }

        $version->status = self::STATUS_DELETED_SOFT;
        $version->modifiedby = (int)($USER->id ?? 0);
        $version->timemodified = time();

        $DB->update_record(self::TABLE, $version);

        return self::get($versionid);
    }

    /**
     * Count versions for a media object.
     *
     * @param int $mediaid Media id.
     * @return int
     * @throws dml_exception
     */
    public static function count_versions(int $mediaid): int {
        global $DB;

        if ($mediaid <= 0) {
            throw new invalid_parameter_exception('Invalid media id.');
        }

        return (int)$DB->count_records(self::TABLE, ['mediaid' => $mediaid]);
    }

    /**
     * Get the next version number for a media object.
     *
     * @param int $mediaid Media id.
     * @return int
     * @throws dml_exception
     */
    public static function next_version_number(int $mediaid): int {
        global $DB;

        if ($mediaid <= 0) {
            throw new invalid_parameter_exception('Invalid media id.');
        }

        $max = $DB->get_field_sql(
            'SELECT MAX(versionnumber) FROM {' . self::TABLE . '} WHERE mediaid = :mediaid',
            ['mediaid' => $mediaid]
        );

        return ((int)$max) + 1;
    }

    /**
     * Build a safe export payload for a version record.
     *
     * This method returns metadata only. It does not serve the file and does
     * not bypass pluginfile or media policy.
     *
     * @param stdClass $version Version record.
     * @return array<string,mixed>
     */
    public static function export_summary(stdClass $version): array {
        return [
            'id' => (int)($version->id ?? 0),
            'uuid' => (string)($version->uuid ?? ''),
            'mediaid' => (int)($version->mediaid ?? 0),
            'versionnumber' => (int)($version->versionnumber ?? 0),
            'label' => (string)($version->label ?? ''),
            'summary' => (string)($version->summary ?? ''),
            'filearea' => (string)($version->filearea ?? ''),
            'filename' => (string)($version->filename ?? ''),
            'contenthash' => (string)($version->contenthash ?? ''),
            'filesize' => (int)($version->filesize ?? 0),
            'mimetype' => (string)($version->mimetype ?? ''),
            'mediatype' => (string)($version->mediatype ?? ''),
            'status' => (string)($version->status ?? ''),
            'visibility' => (string)($version->visibility ?? ''),
            'audiencesuitability' => (string)($version->audiencesuitability ?? ''),
            'iscurrent' => !empty($version->iscurrent),
            'timecreated' => (int)($version->timecreated ?? 0),
            'timemodified' => (int)($version->timemodified ?? 0),
            'metadata' => self::decode_metadata((string)($version->metadata ?? '')),
        ];
    }

    /**
     * Apply stored file metadata to a version record.
     *
     * @param stdClass $version Version record being created.
     * @param stored_file $file Stored file.
     * @return void
     */
    private static function apply_file_metadata(stdClass $version, stored_file $file): void {
        $version->filearea = self::normalise_filearea($file->get_filearea());
        $version->fileitemid = (int)$file->get_itemid();
        $version->filepath = self::normalise_filepath($file->get_filepath());
        $version->filename = $file->get_filename();
        $version->contenthash = $file->get_contenthash();
        $version->filesize = (int)$file->get_filesize();
        $version->mimetype = (string)$file->get_mimetype();
    }

    /**
     * Validate a version record before persistence.
     *
     * @param stdClass $version Version record.
     * @return void
     */
    private static function validate_record(stdClass $version): void {
        if (empty($version->uuid)) {
            throw new invalid_parameter_exception('Media version UUID is required.');
        }

        if (empty($version->mediaid) || (int)$version->mediaid <= 0) {
            throw new invalid_parameter_exception('Media id is required.');
        }

        if (empty($version->versionnumber) || (int)$version->versionnumber <= 0) {
            throw new invalid_parameter_exception('Version number is required.');
        }

        self::normalise_status((string)$version->status);
        self::normalise_filearea((string)$version->filearea);
    }

    /**
     * Clear current flag for all versions of a media record.
     *
     * @param int $mediaid Media id.
     * @return void
     * @throws dml_exception
     */
    private static function clear_current_flag(int $mediaid): void {
        global $DB, $USER;

        $DB->set_field(
            self::TABLE,
            'iscurrent',
            0,
            ['mediaid' => $mediaid]
        );

        // Keep timemodified meaningful for databases where set_field only updates
        // the target column.
        $records = $DB->get_records(self::TABLE, ['mediaid' => $mediaid, 'iscurrent' => 0], '', 'id');
        if ($records) {
            [$insql, $params] = $DB->get_in_or_equal(array_keys($records), SQL_PARAMS_NAMED);
            $params['modifiedby'] = (int)($USER->id ?? 0);
            $params['timemodified'] = time();
            $DB->execute(
                'UPDATE {' . self::TABLE . '}
                    SET modifiedby = :modifiedby, timemodified = :timemodified
                  WHERE id ' . $insql,
                $params
            );
        }
    }

    /**
     * Update the parent media record with the current version pointer.
     *
     * @param int $mediaid Media id.
     * @param int $versionid Version id.
     * @param string $status Version status.
     * @return void
     * @throws dml_exception
     */
    private static function update_media_current_version(int $mediaid, int $versionid, string $status): void {
        global $DB, $USER;

        $media = $DB->get_record(self::MEDIA_TABLE, ['id' => $mediaid], '*', MUST_EXIST);
        $media->currentversionid = $versionid;
        $media->timemodified = time();
        $media->modifiedby = (int)($USER->id ?? 0);

        if (property_exists($media, 'status') && $status !== self::STATUS_DELETED_SOFT) {
            $media->status = $status;
        }

        $DB->update_record(self::MEDIA_TABLE, $media);
    }

    /**
     * Normalise UUID.
     *
     * @param mixed $uuid Candidate UUID.
     * @return string
     */
    private static function normalise_uuid(mixed $uuid): string {
        $uuid = is_string($uuid) ? trim($uuid) : '';

        if ($uuid !== '') {
            return $uuid;
        }

        if (class_exists(uuid::class)) {
            return uuid::generate();
        }

        // Fallback keeps this class usable during staged generation before
        // classes/local/uuid.php is loaded. The final plugin should use uuid.
        return self::fallback_uuidv4();
    }

    /**
     * Fallback UUID v4 generator.
     *
     * @return string
     */
    private static function fallback_uuidv4(): string {
        $data = random_bytes(16);
        $data[6] = chr((ord($data[6]) & 0x0f) | 0x40);
        $data[8] = chr((ord($data[8]) & 0x3f) | 0x80);

        return vsprintf('%s%s-%s-%s-%s-%s%s%s', str_split(bin2hex($data), 4));
    }

    /**
     * Normalise media version status.
     *
     * @param string $status Candidate status.
     * @return string
     */
    private static function normalise_status(string $status): string {
        $status = clean_param($status, PARAM_ALPHANUMEXT);

        if (!in_array($status, self::statuses(), true)) {
            throw new invalid_parameter_exception('Invalid media version status.');
        }

        return $status;
    }

    /**
     * Normalise file area.
     *
     * @param string $filearea Candidate file area.
     * @return string
     */
    private static function normalise_filearea(string $filearea): string {
        $filearea = clean_param($filearea, PARAM_ALPHANUMEXT);

        if (!in_array($filearea, self::fileareas(), true)) {
            throw new invalid_parameter_exception('Invalid media version file area.');
        }

        return $filearea;
    }

    /**
     * Normalise file path.
     *
     * @param string $filepath Candidate file path.
     * @return string
     */
    private static function normalise_filepath(string $filepath): string {
        $filepath = trim($filepath);
        if ($filepath === '') {
            return self::DEFAULT_FILEPATH;
        }

        if ($filepath[0] !== '/') {
            $filepath = '/' . $filepath;
        }

        if (!str_ends_with($filepath, '/')) {
            $filepath .= '/';
        }

        return clean_param($filepath, PARAM_PATH);
    }

    /**
     * Clean optional text field.
     *
     * @param mixed $value Raw value.
     * @return string
     */
    private static function clean_optional_text(mixed $value): string {
        if ($value === null) {
            return '';
        }

        return trim(clean_param((string)$value, PARAM_TEXT));
    }

    /**
     * Encode metadata to JSON.
     *
     * @param mixed $metadata Metadata.
     * @return string
     */
    private static function encode_metadata(mixed $metadata): string {
        if (is_string($metadata)) {
            $metadata = trim($metadata);
            if ($metadata === '') {
                return '{}';
            }

            json_decode($metadata);
            if (json_last_error() === JSON_ERROR_NONE) {
                return $metadata;
            }

            return json_encode(['raw' => $metadata], JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
        }

        if (!is_array($metadata) && !is_object($metadata)) {
            return '{}';
        }

        $json = json_encode($metadata, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);

        return $json === false ? '{}' : $json;
    }

    /**
     * Decode metadata JSON.
     *
     * @param string $metadata Metadata JSON.
     * @return array<string,mixed>
     */
    private static function decode_metadata(string $metadata): array {
        $metadata = trim($metadata);
        if ($metadata === '') {
            return [];
        }

        $decoded = json_decode($metadata, true);

        return is_array($decoded) ? $decoded : [];
    }
}
