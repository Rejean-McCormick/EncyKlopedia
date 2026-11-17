<?php
// This file is part of Moodle - https://moodle.org/
//
// Moodle is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// any later version.

/**
 * Media domain object and persistence service for UCKK Archive.
 *
 * @package    mod_uckkarchive
 * @copyright  2026 Univers-Cité King Klown
 * @license    https://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later
 */

declare(strict_types=1);

namespace mod_uckkarchive\local;

use dml_exception;
use invalid_parameter_exception;
use moodle_exception;
use stdClass;

defined('MOODLE_INTERNAL') || die();

/**
 * Media domain object and persistence service.
 *
 * A media object is a first-class managed entity in the archive/media library.
 * It is not the same as a single Moodle file. One media record may have versions,
 * derivatives, thumbnails, transcripts, captions, attachments, content markers,
 * relations, collections, source metadata, provenance, and export identity.
 *
 * This class owns media record normalisation and database persistence. It does
 * not make final access decisions. Access, download, export, and restriction
 * rules belong in media_policy and content_policy.
 */
final class media {
    /** Table name. */
    public const TABLE = 'uckkarchive_media';

    /** Media status: draft. */
    public const STATUS_DRAFT = 'draft';

    /** Media status: submitted. */
    public const STATUS_SUBMITTED = 'submitted';

    /** Media status: active. */
    public const STATUS_ACTIVE = 'active';

    /** Media status: restricted. */
    public const STATUS_RESTRICTED = 'restricted';

    /** Media status: superseded. */
    public const STATUS_SUPERSEDED = 'superseded';

    /** Media status: archived. */
    public const STATUS_ARCHIVED = 'archived';

    /** Media status: soft-deleted. */
    public const STATUS_DELETED_SOFT = 'deleted_soft';

    /** Visibility: private. */
    public const VISIBILITY_PRIVATE = 'private';

    /** Visibility: user. */
    public const VISIBILITY_USER = 'user';

    /** Visibility: group. */
    public const VISIBILITY_GROUP = 'group';

    /** Visibility: course. */
    public const VISIBILITY_COURSE = 'course';

    /** Visibility: cohort. */
    public const VISIBILITY_COHORT = 'cohort';

    /** Visibility: program. */
    public const VISIBILITY_PROGRAM = 'program';

    /** Visibility: institution. */
    public const VISIBILITY_INSTITUTION = 'institution';

    /** Visibility: public. */
    public const VISIBILITY_PUBLIC = 'public';

    /** Visibility: restricted. */
    public const VISIBILITY_RESTRICTED = 'restricted';

    /** Visibility: restricted integrity. */
    public const VISIBILITY_RESTRICTED_INTEGRITY = 'restricted_integrity';

    /** Visibility: restricted cultural. */
    public const VISIBILITY_RESTRICTED_CULTURAL = 'restricted_cultural';

    /** Audience suitability: general. */
    public const SUITABILITY_GENERAL = 'general';

    /** Audience suitability: guided. */
    public const SUITABILITY_GUIDED = 'guided';

    /** Audience suitability: mature. */
    public const SUITABILITY_MATURE = 'mature';

    /** Audience suitability: restricted. */
    public const SUITABILITY_RESTRICTED = 'restricted';

    /** Audience suitability: restricted cultural. */
    public const SUITABILITY_RESTRICTED_CULTURAL = 'restricted_cultural';

    /** Audience suitability: restricted integrity. */
    public const SUITABILITY_RESTRICTED_INTEGRITY = 'restricted_integrity';

    /** Audience suitability: staff only. */
    public const SUITABILITY_STAFF_ONLY = 'staff_only';

    /** Media type: image. */
    public const TYPE_IMAGE = 'image';

    /** Media type: video. */
    public const TYPE_VIDEO = 'video';

    /** Media type: audio. */
    public const TYPE_AUDIO = 'audio';

    /** Media type: document. */
    public const TYPE_DOCUMENT = 'document';

    /** Media type: PDF. */
    public const TYPE_PDF = 'pdf';

    /** Media type: transcript. */
    public const TYPE_TRANSCRIPT = 'transcript';

    /** Media type: caption. */
    public const TYPE_CAPTION = 'caption';

    /** Media type: thumbnail. */
    public const TYPE_THUMBNAIL = 'thumbnail';

    /** Media type: preview. */
    public const TYPE_PREVIEW = 'preview';

    /** Media type: derivative. */
    public const TYPE_DERIVATIVE = 'derivative';

    /** Media type: source package. */
    public const TYPE_SOURCE_PACKAGE = 'source_package';

    /** Media type: stored Kristal/Kristall artifact. */
    public const TYPE_KRISTAL_ARTIFACT = 'kristal_artifact';

    /** Media type: external reference. */
    public const TYPE_EXTERNAL_REFERENCE = 'external_reference';

    /** Media type: other. */
    public const TYPE_OTHER = 'other';

    /** @var stdClass Media record. */
    private stdClass $record;

    /**
     * Constructor.
     *
     * @param stdClass $record Media record.
     */
    private function __construct(stdClass $record) {
        $this->record = self::normalise_record($record, false);
    }

    /**
     * Build a media domain object from a database record.
     *
     * @param stdClass $record Media record.
     * @return self
     */
    public static function from_record(stdClass $record): self {
        return new self($record);
    }

    /**
     * Fetch one media record by id.
     *
     * @param int $id Media id.
     * @param int $strictness Moodle strictness constant.
     * @return stdClass|null
     * @throws dml_exception
     */
    public static function get_record(int $id, int $strictness = IGNORE_MISSING): ?stdClass {
        global $DB;

        if ($id <= 0) {
            if ($strictness === MUST_EXIST) {
                throw new invalid_parameter_exception('Invalid media id.');
            }
            return null;
        }

        return $DB->get_record(self::TABLE, ['id' => $id], '*', $strictness) ?: null;
    }

    /**
     * Fetch one media record by UUID.
     *
     * @param string $uuid Stable UUID.
     * @param int $strictness Moodle strictness constant.
     * @return stdClass|null
     * @throws dml_exception
     */
    public static function get_record_by_uuid(string $uuid, int $strictness = IGNORE_MISSING): ?stdClass {
        global $DB;

        $uuid = self::normalise_uuid($uuid);
        if ($uuid === '') {
            if ($strictness === MUST_EXIST) {
                throw new invalid_parameter_exception('Invalid media uuid.');
            }
            return null;
        }

        return $DB->get_record(self::TABLE, ['uuid' => $uuid], '*', $strictness) ?: null;
    }

    /**
     * Fetch one media domain object by id.
     *
     * @param int $id Media id.
     * @param int $strictness Moodle strictness constant.
     * @return self|null
     * @throws dml_exception
     */
    public static function get(int $id, int $strictness = IGNORE_MISSING): ?self {
        $record = self::get_record($id, $strictness);
        return $record ? self::from_record($record) : null;
    }

    /**
     * Fetch one media domain object by UUID.
     *
     * @param string $uuid Media UUID.
     * @param int $strictness Moodle strictness constant.
     * @return self|null
     * @throws dml_exception
     */
    public static function get_by_uuid(string $uuid, int $strictness = IGNORE_MISSING): ?self {
        $record = self::get_record_by_uuid($uuid, $strictness);
        return $record ? self::from_record($record) : null;
    }

    /**
     * Create a media record.
     *
     * This method validates and persists the media metadata only. File promotion
     * to Moodle File API and media version creation are handled by media_file and
     * media_version.
     *
     * @param array<string, mixed>|stdClass $data Media data.
     * @param int|null $userid Acting user id, defaults to current user.
     * @return stdClass Created media record.
     * @throws dml_exception
     * @throws moodle_exception
     */
    public static function create($data, ?int $userid = null): stdClass {
        global $DB, $USER;

        self::require_table();

        $userid = $userid ?? (int)($USER->id ?? 0);
        $now = time();

        $record = self::normalise_record(self::as_object($data), true);

        // Every media item has exactly one home library once the partition schema is available.
        // Root UCKK is the compatibility fallback for legacy callers that do not select a library.
        if (empty($record->libraryid) && media_library_scope::schema_ready()) {
            $libraryscope = new media_library_scope();
            $rootlibrary = $libraryscope->resolve_by_slug(media_library_scope::LIBRARY_UCKK);
            if ($rootlibrary) {
                $record->libraryid = (int)$rootlibrary->id;
            }
        }

        $record->uuid = !empty($record->uuid) ? self::normalise_uuid((string)$record->uuid) : self::generate_uuid();
        $record->status = self::normalise_status((string)($record->status ?? self::STATUS_DRAFT));
        $record->visibility = self::normalise_visibility((string)($record->visibility ?? self::VISIBILITY_COURSE));
        $record->audiencesuitability = self::normalise_suitability(
            (string)($record->audiencesuitability ?? self::SUITABILITY_GUIDED)
        );
        $record->mediatype = self::normalise_mediatype((string)($record->mediatype ?? self::TYPE_OTHER));
        $record->metadata = self::encode_metadata($record->metadata ?? []);

        if (empty($record->createdby)) {
            $record->createdby = $userid;
        }
        if (empty($record->modifiedby)) {
            $record->modifiedby = $userid;
        }
        if (empty($record->ownerid)) {
            $record->ownerid = $userid;
        }

        $record->timecreated = (int)($record->timecreated ?? $now);
        $record->timemodified = (int)($record->timemodified ?? $now);

        self::validate_required_create_fields($record);

        $record = self::filter_to_table_fields($record);
        $record->id = $DB->insert_record(self::TABLE, $record);

        return self::get_record((int)$record->id, MUST_EXIST);
    }

    /**
     * Update a media record.
     *
     * @param int $id Media id.
     * @param array<string, mixed>|stdClass $data Updated data.
     * @param int|null $userid Acting user id, defaults to current user.
     * @return stdClass Updated media record.
     * @throws dml_exception
     * @throws moodle_exception
     */
    public static function update(int $id, $data, ?int $userid = null): stdClass {
        global $DB, $USER;

        self::require_table();

        $current = self::get_record($id, MUST_EXIST);
        $update = self::as_object($data);

        $record = clone $current;
        foreach (get_object_vars($update) as $field => $value) {
            if ($field === 'id') {
                continue;
            }
            $record->{$field} = $value;
        }

        $record = self::normalise_record($record, false);
        $record->status = self::normalise_status((string)($record->status ?? self::STATUS_DRAFT));
        $record->visibility = self::normalise_visibility((string)($record->visibility ?? self::VISIBILITY_COURSE));
        $record->audiencesuitability = self::normalise_suitability(
            (string)($record->audiencesuitability ?? self::SUITABILITY_GUIDED)
        );
        $record->mediatype = self::normalise_mediatype((string)($record->mediatype ?? self::TYPE_OTHER));
        $record->metadata = self::encode_metadata($record->metadata ?? []);

        $record->id = $id;
        $record->modifiedby = $userid ?? (int)($USER->id ?? 0);
        $record->timemodified = time();

        $DB->update_record(self::TABLE, self::filter_to_table_fields($record));

        return self::get_record($id, MUST_EXIST);
    }

    /**
     * Mark a media record as soft-deleted.
     *
     * @param int $id Media id.
     * @param int|null $userid Acting user id.
     * @return stdClass Updated media record.
     * @throws dml_exception
     * @throws moodle_exception
     */
    public static function soft_delete(int $id, ?int $userid = null): stdClass {
        return self::update($id, [
            'status' => self::STATUS_DELETED_SOFT,
        ], $userid);
    }

    /**
     * Set media status.
     *
     * @param int $id Media id.
     * @param string $status New status.
     * @param int|null $userid Acting user id.
     * @return stdClass Updated media record.
     * @throws dml_exception
     * @throws moodle_exception
     */
    public static function set_status(int $id, string $status, ?int $userid = null): stdClass {
        return self::update($id, ['status' => self::normalise_status($status)], $userid);
    }

    /**
     * Set media visibility.
     *
     * @param int $id Media id.
     * @param string $visibility New visibility.
     * @param int|null $userid Acting user id.
     * @return stdClass Updated media record.
     * @throws dml_exception
     * @throws moodle_exception
     */
    public static function set_visibility(int $id, string $visibility, ?int $userid = null): stdClass {
        return self::update($id, ['visibility' => self::normalise_visibility($visibility)], $userid);
    }

    /**
     * Set the current version id.
     *
     * @param int $id Media id.
     * @param int $versionid Version id.
     * @param int|null $userid Acting user id.
     * @return stdClass Updated media record.
     * @throws dml_exception
     * @throws moodle_exception
     */
    public static function set_current_version(int $id, int $versionid, ?int $userid = null): stdClass {
        if ($versionid <= 0) {
            throw new invalid_parameter_exception('Invalid media version id.');
        }

        return self::update($id, ['currentversionid' => $versionid], $userid);
    }

    /**
     * List media records for an archive instance.
     *
     * @param int $archiveid Archive instance id.
     * @param array<string, mixed> $filters Optional filters.
     * @param int $limitfrom Offset.
     * @param int $limitnum Limit.
     * @return array<int, stdClass>
     * @throws dml_exception
     */
    public static function list_by_archive(
        int $archiveid,
        array $filters = [],
        int $limitfrom = 0,
        int $limitnum = 50
    ): array {
        global $DB;

        if ($archiveid <= 0) {
            return [];
        }

        [$where, $params] = self::build_filter_sql($archiveid, $filters);
        $records = $DB->get_records_select(self::TABLE, $where, $params, 'timemodified DESC, id DESC', '*', $limitfrom, $limitnum);

        return array_values($records);
    }

    /**
     * Count media records for an archive instance.
     *
     * @param int $archiveid Archive instance id.
     * @param array<string, mixed> $filters Optional filters.
     * @return int
     * @throws dml_exception
     */
    public static function count_by_archive(int $archiveid, array $filters = []): int {
        global $DB;

        if ($archiveid <= 0) {
            return 0;
        }

        [$where, $params] = self::build_filter_sql($archiveid, $filters);
        return $DB->count_records_select(self::TABLE, $where, $params);
    }

    /**
     * Return the wrapped record.
     *
     * @return stdClass
     */
    public function to_record(): stdClass {
        return clone $this->record;
    }

    /**
     * Export the media object for services/output.
     *
     * This is not a privacy export and must be called only after policy filtering.
     *
     * @return array<string, mixed>
     */
    public function to_export(): array {
        return self::export_record($this->record);
    }

    /**
     * Export a media record.
     *
     * @param stdClass $record Media record.
     * @return array<string, mixed>
     */
    public static function export_record(stdClass $record): array {
        $record = self::normalise_record($record, false);
        $metadata = self::decode_metadata($record->metadata ?? null);

        return [
            'id' => (int)($record->id ?? 0),
            'uuid' => (string)($record->uuid ?? ''),
            'archiveid' => (int)($record->archiveid ?? 0),
            'courseid' => (int)($record->courseid ?? 0),
            'cmid' => (int)($record->cmid ?? 0),
            'contextid' => (int)($record->contextid ?? 0),
            'ownerid' => (int)($record->ownerid ?? 0),
            'createdby' => (int)($record->createdby ?? 0),
            'modifiedby' => (int)($record->modifiedby ?? 0),
            'sourceid' => (int)($record->sourceid ?? 0),
            'title' => (string)($record->title ?? ''),
            'subtitle' => (string)($record->subtitle ?? ''),
            'description' => (string)($record->description ?? ''),
            'mediatype' => (string)($record->mediatype ?? self::TYPE_OTHER),
            'mimetype' => (string)($record->mimetype ?? ''),
            'status' => (string)($record->status ?? self::STATUS_DRAFT),
            'visibility' => (string)($record->visibility ?? self::VISIBILITY_COURSE),
            'audiencesuitability' => (string)($record->audiencesuitability ?? self::SUITABILITY_GUIDED),
            'licensekey' => (string)($record->licensekey ?? ''),
            'rightsstatement' => (string)($record->rightsstatement ?? ''),
            'language' => (string)($record->language ?? ''),
            'duration' => (int)($record->duration ?? 0),
            'pagecount' => (int)($record->pagecount ?? 0),
            'hashoriginal' => (string)($record->hashoriginal ?? ''),
            'currentversionid' => (int)($record->currentversionid ?? 0),
            'provenanceid' => (int)($record->provenanceid ?? 0),
            'metadata' => $metadata,
            'timecreated' => (int)($record->timecreated ?? 0),
            'timemodified' => (int)($record->timemodified ?? 0),
        ];
    }

    /**
     * Return allowed media statuses.
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
     * Return allowed visibility values.
     *
     * @return string[]
     */
    public static function visibilities(): array {
        return [
            self::VISIBILITY_PRIVATE,
            self::VISIBILITY_USER,
            self::VISIBILITY_GROUP,
            self::VISIBILITY_COURSE,
            self::VISIBILITY_COHORT,
            self::VISIBILITY_PROGRAM,
            self::VISIBILITY_INSTITUTION,
            self::VISIBILITY_PUBLIC,
            self::VISIBILITY_RESTRICTED,
            self::VISIBILITY_RESTRICTED_INTEGRITY,
            self::VISIBILITY_RESTRICTED_CULTURAL,
        ];
    }

    /**
     * Return allowed audience suitability values.
     *
     * @return string[]
     */
    public static function audience_suitabilities(): array {
        return [
            self::SUITABILITY_GENERAL,
            self::SUITABILITY_GUIDED,
            self::SUITABILITY_MATURE,
            self::SUITABILITY_RESTRICTED,
            self::SUITABILITY_RESTRICTED_CULTURAL,
            self::SUITABILITY_RESTRICTED_INTEGRITY,
            self::SUITABILITY_STAFF_ONLY,
        ];
    }

    /**
     * Return allowed media types.
     *
     * @return string[]
     */
    public static function mediatypes(): array {
        return [
            self::TYPE_IMAGE,
            self::TYPE_VIDEO,
            self::TYPE_AUDIO,
            self::TYPE_DOCUMENT,
            self::TYPE_PDF,
            self::TYPE_TRANSCRIPT,
            self::TYPE_CAPTION,
            self::TYPE_THUMBNAIL,
            self::TYPE_PREVIEW,
            self::TYPE_DERIVATIVE,
            self::TYPE_SOURCE_PACKAGE,
            self::TYPE_KRISTAL_ARTIFACT,
            self::TYPE_EXTERNAL_REFERENCE,
            self::TYPE_OTHER,
        ];
    }

    /**
     * Normalise a full record.
     *
     * @param stdClass $record Input record.
     * @param bool $forcreate Whether this record is being created.
     * @return stdClass
     */
    private static function normalise_record(stdClass $record, bool $forcreate): stdClass {
        $normalised = new stdClass();

        foreach (get_object_vars($record) as $field => $value) {
            $normalised->{$field} = $value;
        }

        foreach ([
            'id',
            'archiveid',
            'libraryid',
            'courseid',
            'cmid',
            'contextid',
            'ownerid',
            'createdby',
            'modifiedby',
            'sourceid',
            'duration',
            'pagecount',
            'currentversionid',
            'provenanceid',
            'timecreated',
            'timemodified',
        ] as $field) {
            if (isset($normalised->{$field}) && $normalised->{$field} !== null && $normalised->{$field} !== '') {
                $normalised->{$field} = (int)$normalised->{$field};
            }
        }

        foreach ([
            'uuid',
            'title',
            'subtitle',
            'description',
            'mediatype',
            'mimetype',
            'status',
            'visibility',
            'audiencesuitability',
            'licensekey',
            'rightsstatement',
            'language',
            'hashoriginal',
        ] as $field) {
            if (isset($normalised->{$field}) && $normalised->{$field} !== null) {
                $normalised->{$field} = trim((string)$normalised->{$field});
            }
        }

        if (isset($normalised->visibility)) {
            $normalised->visibility = self::normalise_visibility((string)$normalised->visibility);
        }

        if (isset($normalised->status)) {
            $normalised->status = self::normalise_status((string)$normalised->status);
        }

        if (isset($normalised->audiencesuitability)) {
            $normalised->audiencesuitability = self::normalise_suitability((string)$normalised->audiencesuitability);
        }

        if (isset($normalised->mediatype)) {
            $normalised->mediatype = self::normalise_mediatype((string)$normalised->mediatype);
        }

        if ($forcreate && empty($normalised->uuid)) {
            $normalised->uuid = self::generate_uuid();
        }

        return $normalised;
    }

    /**
     * Validate required create fields.
     *
     * @param stdClass $record Media record.
     * @throws invalid_parameter_exception
     */
    private static function validate_required_create_fields(stdClass $record): void {
        foreach (['archiveid', 'courseid', 'cmid', 'contextid', 'title'] as $field) {
            if (empty($record->{$field})) {
                throw new invalid_parameter_exception('Missing required media field: ' . $field);
            }
        }
    }

    /**
     * Build filter SQL for archive media lists.
     *
     * @param int $archiveid Archive id.
     * @param array<string, mixed> $filters Filters.
     * @return array{0:string,1:array<string,mixed>}
     */
    private static function build_filter_sql(int $archiveid, array $filters): array {
        global $DB;

        $where = ['archiveid = :archiveid'];
        $params = ['archiveid' => $archiveid];

        if (!empty($filters['status'])) {
            $where[] = 'status = :status';
            $params['status'] = self::normalise_status((string)$filters['status']);
        }

        if (!empty($filters['visibility'])) {
            $where[] = 'visibility = :visibility';
            $params['visibility'] = self::normalise_visibility((string)$filters['visibility']);
        }

        if (!empty($filters['mediatype'])) {
            $where[] = 'mediatype = :mediatype';
            $params['mediatype'] = self::normalise_mediatype((string)$filters['mediatype']);
        }

        if (!empty($filters['audiencesuitability'])) {
            $where[] = 'audiencesuitability = :audiencesuitability';
            $params['audiencesuitability'] = self::normalise_suitability((string)$filters['audiencesuitability']);
        }

        if (!empty($filters['query'])) {
            $query = trim((string)$filters['query']);
            if ($query !== '') {
                $likesql = $DB->sql_like('title', ':querytitle', false, false);
                $likesqldesc = $DB->sql_like('description', ':querydesc', false, false);
                $where[] = '(' . $likesql . ' OR ' . $likesqldesc . ')';
                $params['querytitle'] = '%' . $DB->sql_like_escape($query) . '%';
                $params['querydesc'] = '%' . $DB->sql_like_escape($query) . '%';
            }
        }

        if (!empty($filters['include_deleted']) && (int)$filters['include_deleted'] === 1) {
            // Keep all statuses.
        } else {
            $where[] = 'status <> :deletedsoft';
            $params['deletedsoft'] = self::STATUS_DELETED_SOFT;
        }

        return [implode(' AND ', $where), $params];
    }

    /**
     * Convert input to stdClass.
     *
     * @param array<string, mixed>|stdClass $data Input data.
     * @return stdClass
     */
    private static function as_object($data): stdClass {
        if ($data instanceof stdClass) {
            return clone $data;
        }

        $object = new stdClass();
        foreach ((array)$data as $key => $value) {
            $object->{$key} = $value;
        }
        return $object;
    }

    /**
     * Filter a record to columns that exist in the target table.
     *
     * This protects early iterative builds where docs and schema may be updated
     * together. Required fields are still validated before insertion.
     *
     * @param stdClass $record Input record.
     * @return stdClass
     * @throws dml_exception
     */
    private static function filter_to_table_fields(stdClass $record): stdClass {
        global $DB;

        $columns = $DB->get_columns(self::TABLE);
        $filtered = new stdClass();

        foreach (get_object_vars($record) as $field => $value) {
            if (array_key_exists($field, $columns)) {
                $filtered->{$field} = $value;
            }
        }

        return $filtered;
    }

    /**
     * Ensure media table exists.
     *
     * @throws moodle_exception
     */
    private static function require_table(): void {
        global $DB;

        if (!$DB->get_manager()->table_exists(self::TABLE)) {
            throw new moodle_exception('missingmediatable', 'uckkarchive', '', self::TABLE);
        }
    }

    /**
     * Normalise status.
     *
     * @param string $status Status.
     * @return string
     * @throws invalid_parameter_exception
     */
    private static function normalise_status(string $status): string {
        $status = trim($status);
        if ($status === '') {
            return self::STATUS_DRAFT;
        }

        if (!in_array($status, self::statuses(), true)) {
            throw new invalid_parameter_exception('Invalid media status: ' . $status);
        }

        return $status;
    }

    /**
     * Normalise visibility.
     *
     * @param string $visibility Visibility.
     * @return string
     * @throws invalid_parameter_exception
     */
    private static function normalise_visibility(string $visibility): string {
        $visibility = trim($visibility);

        if ($visibility === 'institutional') {
            $visibility = self::VISIBILITY_INSTITUTION;
        }

        if ($visibility === '') {
            return self::VISIBILITY_COURSE;
        }

        if (!in_array($visibility, self::visibilities(), true)) {
            throw new invalid_parameter_exception('Invalid media visibility: ' . $visibility);
        }

        return $visibility;
    }

    /**
     * Normalise audience suitability.
     *
     * @param string $suitability Audience suitability.
     * @return string
     * @throws invalid_parameter_exception
     */
    private static function normalise_suitability(string $suitability): string {
        $suitability = trim($suitability);

        if ($suitability === '') {
            return self::SUITABILITY_GUIDED;
        }

        if (!in_array($suitability, self::audience_suitabilities(), true)) {
            throw new invalid_parameter_exception('Invalid audience suitability: ' . $suitability);
        }

        return $suitability;
    }

    /**
     * Normalise media type.
     *
     * @param string $mediatype Media type.
     * @return string
     * @throws invalid_parameter_exception
     */
    private static function normalise_mediatype(string $mediatype): string {
        $mediatype = trim($mediatype);

        if ($mediatype === '') {
            return self::TYPE_OTHER;
        }

        if (!in_array($mediatype, self::mediatypes(), true)) {
            throw new invalid_parameter_exception('Invalid media type: ' . $mediatype);
        }

        return $mediatype;
    }

    /**
     * Normalise a UUID string.
     *
     * @param string $uuid UUID.
     * @return string
     */
    private static function normalise_uuid(string $uuid): string {
        $uuid = strtolower(trim($uuid));

        if (!preg_match('/^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/', $uuid)) {
            return '';
        }

        return $uuid;
    }

    /**
     * Generate a UUID.
     *
     * @return string
     * @throws moodle_exception
     */
    private static function generate_uuid(): string {
        if (class_exists('\\mod_uckkarchive\\local\\uuid') && method_exists('\\mod_uckkarchive\\local\\uuid', 'generate')) {
            return \mod_uckkarchive\local\uuid::generate();
        }

        try {
            $data = random_bytes(16);
        } catch (\Throwable $e) {
            throw new moodle_exception('cannotgenerateuuid', 'uckkarchive');
        }

        $data[6] = chr((ord($data[6]) & 0x0f) | 0x40);
        $data[8] = chr((ord($data[8]) & 0x3f) | 0x80);

        return vsprintf('%s%s-%s-%s-%s-%s%s%s', str_split(bin2hex($data), 4));
    }

    /**
     * Encode metadata as JSON.
     *
     * @param mixed $metadata Metadata.
     * @return string
     */
    private static function encode_metadata($metadata): string {
        if ($metadata === null || $metadata === '') {
            return '{}';
        }

        if (is_string($metadata)) {
            $decoded = json_decode($metadata);
            return json_last_error() === JSON_ERROR_NONE ? $metadata : json_encode(['raw' => $metadata]);
        }

        $encoded = json_encode($metadata, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);

        return $encoded === false ? '{}' : $encoded;
    }

    /**
     * Decode metadata JSON.
     *
     * @param mixed $metadata Metadata value.
     * @return array<string, mixed>
     */
    private static function decode_metadata($metadata): array {
        if (is_array($metadata)) {
            return $metadata;
        }

        if ($metadata instanceof stdClass) {
            return (array)$metadata;
        }

        if (!is_string($metadata) || trim($metadata) === '') {
            return [];
        }

        $decoded = json_decode($metadata, true);

        return is_array($decoded) ? $decoded : [];
    }
}
