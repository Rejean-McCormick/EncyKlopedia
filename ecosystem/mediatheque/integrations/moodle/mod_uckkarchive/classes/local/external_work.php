<?php
// This file is part of Moodle - https://moodle.org/
//
// Moodle is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// any later version.

/**
 * External work domain object and persistence service for UCKK Archive.
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
 * External work domain object and persistence service.
 *
 * External works are foreign or third-party works referenced by the archive
 * without necessarily copying the work into Moodle File API storage. The archive
 * may store metadata, citations, teaching notes, content advisories, cultural
 * protocol notes, locators, rights notes, and references for the external work.
 *
 * This class owns external work normalisation and persistence. It does not imply
 * copyright ownership, access authority, or file ownership over the third-party
 * work. Access, display, export, redaction, and cultural protocol decisions
 * belong in content_policy, media_policy, and export policy code.
 */
final class external_work {
    /** Table name. */
    public const TABLE = 'uckkarchive_external_work';

    /** Work type: film. */
    public const TYPE_FILM = 'film';

    /** Work type: book. */
    public const TYPE_BOOK = 'book';

    /** Work type: article. */
    public const TYPE_ARTICLE = 'article';

    /** Work type: podcast. */
    public const TYPE_PODCAST = 'podcast';

    /** Work type: website. */
    public const TYPE_WEBSITE = 'website';

    /** Work type: external video. */
    public const TYPE_EXTERNAL_VIDEO = 'external_video';

    /** Work type: external image. */
    public const TYPE_EXTERNAL_IMAGE = 'external_image';

    /** Work type: public archive item. */
    public const TYPE_PUBLIC_ARCHIVE_ITEM = 'public_archive_item';

    /** Work type: third-party PDF. */
    public const TYPE_THIRD_PARTY_PDF = 'third_party_pdf';

    /** Work type: other. */
    public const TYPE_OTHER = 'other';

    /** Work status: draft. */
    public const STATUS_DRAFT = 'draft';

    /** Work status: active. */
    public const STATUS_ACTIVE = 'active';

    /** Work status: restricted. */
    public const STATUS_RESTRICTED = 'restricted';

    /** Work status: archived. */
    public const STATUS_ARCHIVED = 'archived';

    /** Work status: soft-deleted. */
    public const STATUS_DELETED_SOFT = 'deleted_soft';

    /** Rights status: unknown source. */
    public const RIGHTS_UNKNOWN = 'unknown';

    /** Rights status: third-party copyright. */
    public const RIGHTS_THIRD_PARTY = 'third_party_copyright';

    /** Rights status: licensed external. */
    public const RIGHTS_LICENSED_EXTERNAL = 'licensed_external';

    /** Rights status: public domain. */
    public const RIGHTS_PUBLIC_DOMAIN = 'public_domain';

    /** Rights status: open license. */
    public const RIGHTS_OPEN_LICENSE = 'open_license';

    /** Rights status: fair-use reference. */
    public const RIGHTS_FAIR_USE_REFERENCE = 'fair_use_reference';

    /** Rights status: restricted reference. */
    public const RIGHTS_RESTRICTED_REFERENCE = 'restricted_reference';

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

    /** @var stdClass External work record. */
    private stdClass $record;

    /**
     * Constructor.
     *
     * @param stdClass $record External work record.
     */
    private function __construct(stdClass $record) {
        $this->record = self::normalise_record($record, false);
    }

    /**
     * Build an external work domain object from a database record.
     *
     * @param stdClass $record External work record.
     * @return self
     */
    public static function from_record(stdClass $record): self {
        return new self($record);
    }

    /**
     * Fetch one external work record by id.
     *
     * @param int $id External work id.
     * @param int $strictness Moodle strictness constant.
     * @return stdClass|null
     * @throws dml_exception
     */
    public static function get_record(int $id, int $strictness = IGNORE_MISSING): ?stdClass {
        global $DB;

        if ($id <= 0) {
            if ($strictness === MUST_EXIST) {
                throw new invalid_parameter_exception('Invalid external work id.');
            }
            return null;
        }

        return $DB->get_record(self::TABLE, ['id' => $id], '*', $strictness) ?: null;
    }

    /**
     * Fetch one external work record by UUID.
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
                throw new invalid_parameter_exception('Invalid external work uuid.');
            }
            return null;
        }

        return $DB->get_record(self::TABLE, ['uuid' => $uuid], '*', $strictness) ?: null;
    }

    /**
     * Fetch one external work domain object by id.
     *
     * @param int $id External work id.
     * @param int $strictness Moodle strictness constant.
     * @return self|null
     * @throws dml_exception
     */
    public static function get(int $id, int $strictness = IGNORE_MISSING): ?self {
        $record = self::get_record($id, $strictness);
        return $record ? self::from_record($record) : null;
    }

    /**
     * Fetch one external work domain object by UUID.
     *
     * @param string $uuid External work UUID.
     * @param int $strictness Moodle strictness constant.
     * @return self|null
     * @throws dml_exception
     */
    public static function get_by_uuid(string $uuid, int $strictness = IGNORE_MISSING): ?self {
        $record = self::get_record_by_uuid($uuid, $strictness);
        return $record ? self::from_record($record) : null;
    }

    /**
     * Create an external work reference.
     *
     * @param array<string, mixed>|stdClass $data External work data.
     * @param int|null $userid Acting user id, defaults to current user.
     * @return stdClass Created external work record.
     * @throws dml_exception
     * @throws moodle_exception
     */
    public static function create($data, ?int $userid = null): stdClass {
        global $DB, $USER;

        self::require_table();

        $userid = $userid ?? (int)($USER->id ?? 0);
        $now = time();

        $record = self::normalise_record(self::as_object($data), true);
        $record->uuid = !empty($record->uuid) ? self::normalise_uuid((string)$record->uuid) : self::generate_uuid();
        $record->worktype = self::normalise_work_type((string)($record->worktype ?? self::TYPE_OTHER));
        $record->status = self::normalise_status((string)($record->status ?? self::STATUS_DRAFT));
        $record->visibility = self::normalise_visibility((string)($record->visibility ?? self::VISIBILITY_COURSE));
        $record->audiencesuitability = self::normalise_suitability(
            (string)($record->audiencesuitability ?? self::SUITABILITY_GUIDED)
        );
        $record->rightsstatus = self::normalise_rights_status(
            (string)($record->rightsstatus ?? self::RIGHTS_UNKNOWN)
        );
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
     * Update an external work reference.
     *
     * @param int $id External work id.
     * @param array<string, mixed>|stdClass $data Updated data.
     * @param int|null $userid Acting user id, defaults to current user.
     * @return stdClass Updated external work record.
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
        $record->worktype = self::normalise_work_type((string)($record->worktype ?? self::TYPE_OTHER));
        $record->status = self::normalise_status((string)($record->status ?? self::STATUS_DRAFT));
        $record->visibility = self::normalise_visibility((string)($record->visibility ?? self::VISIBILITY_COURSE));
        $record->audiencesuitability = self::normalise_suitability(
            (string)($record->audiencesuitability ?? self::SUITABILITY_GUIDED)
        );
        $record->rightsstatus = self::normalise_rights_status(
            (string)($record->rightsstatus ?? self::RIGHTS_UNKNOWN)
        );
        $record->metadata = self::encode_metadata($record->metadata ?? []);

        $record->id = $id;
        $record->modifiedby = $userid ?? (int)($USER->id ?? 0);
        $record->timemodified = time();

        $DB->update_record(self::TABLE, self::filter_to_table_fields($record));

        return self::get_record($id, MUST_EXIST);
    }

    /**
     * Mark an external work as soft-deleted.
     *
     * @param int $id External work id.
     * @param int|null $userid Acting user id.
     * @return stdClass Updated external work record.
     * @throws dml_exception
     * @throws moodle_exception
     */
    public static function soft_delete(int $id, ?int $userid = null): stdClass {
        return self::update($id, ['status' => self::STATUS_DELETED_SOFT], $userid);
    }

    /**
     * Archive an external work.
     *
     * @param int $id External work id.
     * @param int|null $userid Acting user id.
     * @return stdClass Updated external work record.
     * @throws dml_exception
     * @throws moodle_exception
     */
    public static function archive(int $id, ?int $userid = null): stdClass {
        return self::update($id, ['status' => self::STATUS_ARCHIVED], $userid);
    }

    /**
     * Set external work status.
     *
     * @param int $id External work id.
     * @param string $status New status.
     * @param int|null $userid Acting user id.
     * @return stdClass Updated external work record.
     * @throws dml_exception
     * @throws moodle_exception
     */
    public static function set_status(int $id, string $status, ?int $userid = null): stdClass {
        return self::update($id, ['status' => self::normalise_status($status)], $userid);
    }

    /**
     * Set external work visibility.
     *
     * @param int $id External work id.
     * @param string $visibility New visibility.
     * @param int|null $userid Acting user id.
     * @return stdClass Updated external work record.
     * @throws dml_exception
     * @throws moodle_exception
     */
    public static function set_visibility(int $id, string $visibility, ?int $userid = null): stdClass {
        return self::update($id, ['visibility' => self::normalise_visibility($visibility)], $userid);
    }

    /**
     * List external works for an archive instance.
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

        $filters['archiveid'] = $archiveid;
        [$where, $params] = self::build_filter_sql($filters);

        $records = $DB->get_records_select(
            self::TABLE,
            $where,
            $params,
            'timemodified DESC, id DESC',
            '*',
            $limitfrom,
            $limitnum
        );

        return array_values($records);
    }

    /**
     * Count external works matching filters.
     *
     * @param array<string, mixed> $filters Filters.
     * @return int
     * @throws dml_exception
     */
    public static function count(array $filters = []): int {
        global $DB;

        [$where, $params] = self::build_filter_sql($filters);
        return $DB->count_records_select(self::TABLE, $where, $params);
    }

    /**
     * Search external works by title, creator, citation, identifier, or source URL.
     *
     * @param int $archiveid Archive instance id.
     * @param string $query Search query.
     * @param array<string, mixed> $filters Optional filters.
     * @param int $limitfrom Offset.
     * @param int $limitnum Limit.
     * @return array<int, stdClass>
     * @throws dml_exception
     */
    public static function search(
        int $archiveid,
        string $query,
        array $filters = [],
        int $limitfrom = 0,
        int $limitnum = 50
    ): array {
        $filters['archiveid'] = $archiveid;
        $filters['query'] = $query;

        return self::list_by_archive($archiveid, $filters, $limitfrom, $limitnum);
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
     * Export this external work for services/output.
     *
     * This is not a privacy export and must be called only after policy
     * filtering. Restricted details, cultural protocol notes, and third-party
     * data must be filtered before being sent to users who cannot see them.
     *
     * @return array<string, mixed>
     */
    public function to_export(): array {
        return self::export_record($this->record);
    }

    /**
     * Export an external work record.
     *
     * @param stdClass $record External work record.
     * @return array<string, mixed>
     */
    public static function export_record(stdClass $record): array {
        $record = self::normalise_record($record, false);

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
            'worktype' => (string)($record->worktype ?? self::TYPE_OTHER),
            'status' => (string)($record->status ?? self::STATUS_DRAFT),
            'visibility' => (string)($record->visibility ?? self::VISIBILITY_COURSE),
            'audiencesuitability' => (string)($record->audiencesuitability ?? self::SUITABILITY_GUIDED),
            'rightsstatus' => (string)($record->rightsstatus ?? self::RIGHTS_UNKNOWN),
            'title' => (string)($record->title ?? ''),
            'subtitle' => (string)($record->subtitle ?? ''),
            'creator' => (string)($record->creator ?? ''),
            'publisher' => (string)($record->publisher ?? ''),
            'publicationyear' => (int)($record->publicationyear ?? 0),
            'language' => (string)($record->language ?? ''),
            'sourceurl' => (string)($record->sourceurl ?? ''),
            'identifier' => (string)($record->identifier ?? ''),
            'identifiertype' => (string)($record->identifiertype ?? ''),
            'citation' => (string)($record->citation ?? ''),
            'rightsstatement' => (string)($record->rightsstatement ?? ''),
            'licensekey' => (string)($record->licensekey ?? ''),
            'sourcenote' => (string)($record->sourcenote ?? ''),
            'teachingnote' => (string)($record->teachingnote ?? ''),
            'culturalprotocolnote' => (string)($record->culturalprotocolnote ?? ''),
            'description' => (string)($record->description ?? ''),
            'provenanceid' => (int)($record->provenanceid ?? 0),
            'metadata' => self::decode_metadata($record->metadata ?? null),
            'timecreated' => (int)($record->timecreated ?? 0),
            'timemodified' => (int)($record->timemodified ?? 0),
        ];
    }

    /**
     * Return allowed external work types.
     *
     * @return string[]
     */
    public static function work_types(): array {
        return [
            self::TYPE_FILM,
            self::TYPE_BOOK,
            self::TYPE_ARTICLE,
            self::TYPE_PODCAST,
            self::TYPE_WEBSITE,
            self::TYPE_EXTERNAL_VIDEO,
            self::TYPE_EXTERNAL_IMAGE,
            self::TYPE_PUBLIC_ARCHIVE_ITEM,
            self::TYPE_THIRD_PARTY_PDF,
            self::TYPE_OTHER,
        ];
    }

    /**
     * Return allowed statuses.
     *
     * @return string[]
     */
    public static function statuses(): array {
        return [
            self::STATUS_DRAFT,
            self::STATUS_ACTIVE,
            self::STATUS_RESTRICTED,
            self::STATUS_ARCHIVED,
            self::STATUS_DELETED_SOFT,
        ];
    }

    /**
     * Return allowed rights statuses.
     *
     * @return string[]
     */
    public static function rights_statuses(): array {
        return [
            self::RIGHTS_UNKNOWN,
            self::RIGHTS_THIRD_PARTY,
            self::RIGHTS_LICENSED_EXTERNAL,
            self::RIGHTS_PUBLIC_DOMAIN,
            self::RIGHTS_OPEN_LICENSE,
            self::RIGHTS_FAIR_USE_REFERENCE,
            self::RIGHTS_RESTRICTED_REFERENCE,
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
     * Build filter SQL.
     *
     * @param array<string, mixed> $filters Filters.
     * @return array{0:string,1:array<string,mixed>}
     */
    private static function build_filter_sql(array $filters): array {
        global $DB;

        $where = ['1 = 1'];
        $params = [];

        foreach (['archiveid', 'courseid', 'cmid', 'contextid', 'ownerid', 'createdby'] as $field) {
            if (!empty($filters[$field])) {
                $where[] = $field . ' = :' . $field;
                $params[$field] = (int)$filters[$field];
            }
        }

        if (!empty($filters['worktype'])) {
            $where[] = 'worktype = :worktype';
            $params['worktype'] = self::normalise_work_type((string)$filters['worktype']);
        }

        if (!empty($filters['status'])) {
            $where[] = 'status = :status';
            $params['status'] = self::normalise_status((string)$filters['status']);
        }

        if (!empty($filters['visibility'])) {
            $where[] = 'visibility = :visibility';
            $params['visibility'] = self::normalise_visibility((string)$filters['visibility']);
        }

        if (!empty($filters['audiencesuitability'])) {
            $where[] = 'audiencesuitability = :audiencesuitability';
            $params['audiencesuitability'] = self::normalise_suitability((string)$filters['audiencesuitability']);
        }

        if (!empty($filters['rightsstatus'])) {
            $where[] = 'rightsstatus = :rightsstatus';
            $params['rightsstatus'] = self::normalise_rights_status((string)$filters['rightsstatus']);
        }

        if (!empty($filters['identifier'])) {
            $where[] = 'identifier = :identifier';
            $params['identifier'] = trim((string)$filters['identifier']);
        }

        if (!empty($filters['query'])) {
            $query = trim((string)$filters['query']);
            if ($query !== '') {
                $likes = [];
                foreach (['title', 'creator', 'citation', 'identifier', 'sourceurl', 'description'] as $field) {
                    $param = 'query_' . $field;
                    $likes[] = $DB->sql_like($field, ':' . $param, false, false);
                    $params[$param] = '%' . $DB->sql_like_escape($query) . '%';
                }
                $where[] = '(' . implode(' OR ', $likes) . ')';
            }
        }

        if (empty($filters['include_deleted'])) {
            $where[] = 'status <> :deletedsoft';
            $params['deletedsoft'] = self::STATUS_DELETED_SOFT;
        }

        return [implode(' AND ', $where), $params];
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
            'courseid',
            'cmid',
            'contextid',
            'ownerid',
            'createdby',
            'modifiedby',
            'publicationyear',
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
            'worktype',
            'status',
            'visibility',
            'audiencesuitability',
            'rightsstatus',
            'title',
            'subtitle',
            'creator',
            'publisher',
            'language',
            'sourceurl',
            'identifier',
            'identifiertype',
            'citation',
            'rightsstatement',
            'licensekey',
            'sourcenote',
            'teachingnote',
            'culturalprotocolnote',
            'description',
        ] as $field) {
            if (isset($normalised->{$field}) && $normalised->{$field} !== null) {
                $normalised->{$field} = trim((string)$normalised->{$field});
            }
        }

        if (isset($normalised->uuid)) {
            $normalised->uuid = self::normalise_uuid((string)$normalised->uuid);
        }

        if (isset($normalised->worktype)) {
            $normalised->worktype = self::normalise_work_type((string)$normalised->worktype);
        }

        if (isset($normalised->status)) {
            $normalised->status = self::normalise_status((string)$normalised->status);
        }

        if (isset($normalised->visibility)) {
            $normalised->visibility = self::normalise_visibility((string)$normalised->visibility);
        }

        if (isset($normalised->audiencesuitability)) {
            $normalised->audiencesuitability = self::normalise_suitability((string)$normalised->audiencesuitability);
        }

        if (isset($normalised->rightsstatus)) {
            $normalised->rightsstatus = self::normalise_rights_status((string)$normalised->rightsstatus);
        }

        if ($forcreate && empty($normalised->uuid)) {
            $normalised->uuid = self::generate_uuid();
        }

        return $normalised;
    }

    /**
     * Validate required create fields.
     *
     * @param stdClass $record External work record.
     * @throws invalid_parameter_exception
     */
    private static function validate_required_create_fields(stdClass $record): void {
        foreach (['archiveid', 'courseid', 'cmid', 'contextid', 'title', 'worktype'] as $field) {
            if (empty($record->{$field})) {
                throw new invalid_parameter_exception('Missing required external work field: ' . $field);
            }
        }

        if (empty($record->creator) && empty($record->publisher) && empty($record->sourceurl)) {
            throw new invalid_parameter_exception('External work requires creator, publisher, or source URL.');
        }

        if (empty($record->citation) && empty($record->sourceurl) && empty($record->identifier)) {
            throw new invalid_parameter_exception('External work requires citation, source URL, or identifier.');
        }
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
     * This keeps early iterative builds resilient while install.xml and local
     * services are being completed together.
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
     * Ensure external work table exists.
     *
     * @throws moodle_exception
     */
    private static function require_table(): void {
        global $DB;

        if (!$DB->get_manager()->table_exists(self::TABLE)) {
            throw new moodle_exception('missingexternalworktable', 'uckkarchive', '', self::TABLE);
        }
    }

    /**
     * Normalise work type.
     *
     * @param string $worktype Work type.
     * @return string
     * @throws invalid_parameter_exception
     */
    private static function normalise_work_type(string $worktype): string {
        $worktype = trim($worktype);
        if ($worktype === '') {
            return self::TYPE_OTHER;
        }

        if (!in_array($worktype, self::work_types(), true)) {
            throw new invalid_parameter_exception('Invalid external work type: ' . $worktype);
        }

        return $worktype;
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
            throw new invalid_parameter_exception('Invalid external work status: ' . $status);
        }

        return $status;
    }

    /**
     * Normalise rights status.
     *
     * @param string $rightsstatus Rights status.
     * @return string
     * @throws invalid_parameter_exception
     */
    private static function normalise_rights_status(string $rightsstatus): string {
        $rightsstatus = trim($rightsstatus);
        if ($rightsstatus === '') {
            return self::RIGHTS_UNKNOWN;
        }

        if (!in_array($rightsstatus, self::rights_statuses(), true)) {
            throw new invalid_parameter_exception('Invalid external work rights status: ' . $rightsstatus);
        }

        return $rightsstatus;
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
            throw new invalid_parameter_exception('Invalid external work visibility: ' . $visibility);
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
            throw new invalid_parameter_exception('Invalid external work audience suitability: ' . $suitability);
        }

        return $suitability;
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
