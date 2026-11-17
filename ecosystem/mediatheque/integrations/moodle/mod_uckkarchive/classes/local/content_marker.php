<?php
// This file is part of Moodle - https://moodle.org/
//
// Moodle is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// any later version.

/**
 * Content marker domain object and persistence service for UCKK Archive.
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
 * Content marker domain object and persistence service.
 *
 * A content marker links a content advisory or cultural protocol tag to a
 * precise location in a media object, media version, archive item, external
 * work, or manual reference. It is used for content warnings, trigger
 * warnings, cultural protocol handling, classroom suitability, export
 * filtering, privacy filtering, and responsible access decisions.
 *
 * This class owns marker normalisation and persistence. It does not make final
 * access decisions. Access, review, redaction, and cultural protocol authority
 * belong in content_policy and media_policy.
 */
final class content_marker {
    /** Table name. */
    public const TABLE = 'uckkarchive_content_marker';

    /** Review state: draft. */
    public const REVIEW_DRAFT = 'draft';

    /** Review state: pending review. */
    public const REVIEW_PENDING = 'pending_review';

    /** Review state: reviewed. */
    public const REVIEW_REVIEWED = 'reviewed';

    /** Review state: approved. */
    public const REVIEW_APPROVED = 'approved';

    /** Review state: contested. */
    public const REVIEW_CONTESTED = 'contested';

    /** Review state: retired. */
    public const REVIEW_RETIRED = 'retired';

    /** Severity: notice. */
    public const SEVERITY_NOTICE = 'notice';

    /** Severity: moderate. */
    public const SEVERITY_MODERATE = 'moderate';

    /** Severity: strong. */
    public const SEVERITY_STRONG = 'strong';

    /** Severity: restricted. */
    public const SEVERITY_RESTRICTED = 'restricted';

    /** Target type: media. */
    public const TARGET_MEDIA = 'media';

    /** Target type: media version. */
    public const TARGET_MEDIA_VERSION = 'media_version';

    /** Target type: archive item. */
    public const TARGET_ARCHIVE_ITEM = 'archive_item';

    /** Target type: proof. */
    public const TARGET_PROOF = 'proof';

    /** Target type: Kristal. */
    public const TARGET_KRISTAL = 'kristal';

    /** Target type: external work. */
    public const TARGET_EXTERNAL_WORK = 'external_work';

    /** Target type: collection. */
    public const TARGET_COLLECTION = 'collection';

    /** Target type: manual reference. */
    public const TARGET_MANUAL_REFERENCE = 'manual_reference';

    /** Locator type: timecode. */
    public const LOCATOR_TIMECODE = 'timecode';

    /** Locator type: timecode range. */
    public const LOCATOR_TIMECODE_RANGE = 'timecode_range';

    /** Locator type: page. */
    public const LOCATOR_PAGE = 'page';

    /** Locator type: page range. */
    public const LOCATOR_PAGE_RANGE = 'page_range';

    /** Locator type: chapter. */
    public const LOCATOR_CHAPTER = 'chapter';

    /** Locator type: chapter range. */
    public const LOCATOR_CHAPTER_RANGE = 'chapter_range';

    /** Locator type: section. */
    public const LOCATOR_SECTION = 'section';

    /** Locator type: section range. */
    public const LOCATOR_SECTION_RANGE = 'section_range';

    /** Locator type: paragraph. */
    public const LOCATOR_PARAGRAPH = 'paragraph';

    /** Locator type: paragraph range. */
    public const LOCATOR_PARAGRAPH_RANGE = 'paragraph_range';

    /** Locator type: scene. */
    public const LOCATOR_SCENE = 'scene';

    /** Locator type: track. */
    public const LOCATOR_TRACK = 'track';

    /** Locator type: timestamp. */
    public const LOCATOR_TIMESTAMP = 'timestamp';

    /** Locator type: URL fragment. */
    public const LOCATOR_URL_FRAGMENT = 'url_fragment';

    /** Locator type: manual reference. */
    public const LOCATOR_MANUAL_REFERENCE = 'manual_reference';

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

    /** @var stdClass Marker record. */
    private stdClass $record;

    /**
     * Constructor.
     *
     * @param stdClass $record Marker record.
     */
    private function __construct(stdClass $record) {
        $this->record = self::normalise_record($record, false);
    }

    /**
     * Build a domain object from a database record.
     *
     * @param stdClass $record Marker record.
     * @return self
     */
    public static function from_record(stdClass $record): self {
        return new self($record);
    }

    /**
     * Fetch one marker record by id.
     *
     * @param int $id Marker id.
     * @param int $strictness Moodle strictness constant.
     * @return stdClass|null
     * @throws dml_exception
     */
    public static function get_record(int $id, int $strictness = IGNORE_MISSING): ?stdClass {
        global $DB;

        if ($id <= 0) {
            if ($strictness === MUST_EXIST) {
                throw new invalid_parameter_exception('Invalid content marker id.');
            }
            return null;
        }

        return $DB->get_record(self::TABLE, ['id' => $id], '*', $strictness) ?: null;
    }

    /**
     * Fetch one marker record by UUID.
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
                throw new invalid_parameter_exception('Invalid content marker uuid.');
            }
            return null;
        }

        return $DB->get_record(self::TABLE, ['uuid' => $uuid], '*', $strictness) ?: null;
    }

    /**
     * Fetch one marker domain object by id.
     *
     * @param int $id Marker id.
     * @param int $strictness Moodle strictness constant.
     * @return self|null
     * @throws dml_exception
     */
    public static function get(int $id, int $strictness = IGNORE_MISSING): ?self {
        $record = self::get_record($id, $strictness);
        return $record ? self::from_record($record) : null;
    }

    /**
     * Fetch one marker domain object by UUID.
     *
     * @param string $uuid Marker UUID.
     * @param int $strictness Moodle strictness constant.
     * @return self|null
     * @throws dml_exception
     */
    public static function get_by_uuid(string $uuid, int $strictness = IGNORE_MISSING): ?self {
        $record = self::get_record_by_uuid($uuid, $strictness);
        return $record ? self::from_record($record) : null;
    }

    /**
     * Create a content marker.
     *
     * @param array<string, mixed>|stdClass $data Marker data.
     * @param int|null $userid Acting user id, defaults to current user.
     * @return stdClass Created marker record.
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
        $record->targettype = self::normalise_target_type((string)($record->targettype ?? self::TARGET_MANUAL_REFERENCE));
        $record->locatortype = self::normalise_locator_type((string)($record->locatortype ?? self::LOCATOR_MANUAL_REFERENCE));
        $record->reviewstate = self::normalise_review_state((string)($record->reviewstate ?? self::REVIEW_DRAFT));
        $record->severity = self::normalise_severity((string)($record->severity ?? self::SEVERITY_NOTICE));
        $record->visibility = self::normalise_visibility((string)($record->visibility ?? self::VISIBILITY_COURSE));
        $record->audiencesuitability = self::normalise_suitability(
            (string)($record->audiencesuitability ?? self::SUITABILITY_GUIDED)
        );
        $record->metadata = self::encode_metadata($record->metadata ?? []);

        if (empty($record->createdby)) {
            $record->createdby = $userid;
        }
        if (empty($record->modifiedby)) {
            $record->modifiedby = $userid;
        }

        $record->timecreated = (int)($record->timecreated ?? $now);
        $record->timemodified = (int)($record->timemodified ?? $now);

        self::validate_required_create_fields($record);

        $record = self::filter_to_table_fields($record);
        $record->id = $DB->insert_record(self::TABLE, $record);

        return self::get_record((int)$record->id, MUST_EXIST);
    }

    /**
     * Update a content marker.
     *
     * @param int $id Marker id.
     * @param array<string, mixed>|stdClass $data Updated data.
     * @param int|null $userid Acting user id, defaults to current user.
     * @return stdClass Updated marker record.
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
        $record->targettype = self::normalise_target_type((string)($record->targettype ?? self::TARGET_MANUAL_REFERENCE));
        $record->locatortype = self::normalise_locator_type((string)($record->locatortype ?? self::LOCATOR_MANUAL_REFERENCE));
        $record->reviewstate = self::normalise_review_state((string)($record->reviewstate ?? self::REVIEW_DRAFT));
        $record->severity = self::normalise_severity((string)($record->severity ?? self::SEVERITY_NOTICE));
        $record->visibility = self::normalise_visibility((string)($record->visibility ?? self::VISIBILITY_COURSE));
        $record->audiencesuitability = self::normalise_suitability(
            (string)($record->audiencesuitability ?? self::SUITABILITY_GUIDED)
        );
        $record->metadata = self::encode_metadata($record->metadata ?? []);

        $record->id = $id;
        $record->modifiedby = $userid ?? (int)($USER->id ?? 0);
        $record->timemodified = time();

        $DB->update_record(self::TABLE, self::filter_to_table_fields($record));

        return self::get_record($id, MUST_EXIST);
    }

    /**
     * Move a marker into a review state.
     *
     * @param int $id Marker id.
     * @param string $reviewstate Review state.
     * @param string $rationale Review rationale or note.
     * @param int|null $userid Acting user id, defaults to current user.
     * @return stdClass Updated marker record.
     * @throws dml_exception
     * @throws moodle_exception
     */
    public static function set_review_state(
        int $id,
        string $reviewstate,
        string $rationale = '',
        ?int $userid = null
    ): stdClass {
        global $USER;

        $userid = $userid ?? (int)($USER->id ?? 0);
        $state = self::normalise_review_state($reviewstate);

        $data = [
            'reviewstate' => $state,
            'reviewrationale' => $rationale,
            'reviewedby' => $userid,
            'timereviewed' => time(),
        ];

        return self::update($id, $data, $userid);
    }

    /**
     * Retire a marker without deleting it.
     *
     * @param int $id Marker id.
     * @param string $rationale Retirement rationale.
     * @param int|null $userid Acting user id.
     * @return stdClass Updated marker record.
     * @throws dml_exception
     * @throws moodle_exception
     */
    public static function retire(int $id, string $rationale = '', ?int $userid = null): stdClass {
        return self::set_review_state($id, self::REVIEW_RETIRED, $rationale, $userid);
    }

    /**
     * List markers for a target.
     *
     * @param string $targettype Target type.
     * @param int $targetid Target id.
     * @param array<string, mixed> $filters Optional filters.
     * @param int $limitfrom Offset.
     * @param int $limitnum Limit.
     * @return array<int, stdClass>
     * @throws dml_exception
     */
    public static function list_by_target(
        string $targettype,
        int $targetid,
        array $filters = [],
        int $limitfrom = 0,
        int $limitnum = 50
    ): array {
        global $DB;

        if ($targetid <= 0) {
            return [];
        }

        $filters['targettype'] = self::normalise_target_type($targettype);
        $filters['targetid'] = $targetid;

        [$where, $params] = self::build_filter_sql($filters);

        $records = $DB->get_records_select(
            self::TABLE,
            $where,
            $params,
            'locatorsort ASC, timecreated ASC, id ASC',
            '*',
            $limitfrom,
            $limitnum
        );

        return array_values($records);
    }

    /**
     * List markers for a media object.
     *
     * @param int $mediaid Media id.
     * @param array<string, mixed> $filters Optional filters.
     * @param int $limitfrom Offset.
     * @param int $limitnum Limit.
     * @return array<int, stdClass>
     * @throws dml_exception
     */
    public static function list_by_media(
        int $mediaid,
        array $filters = [],
        int $limitfrom = 0,
        int $limitnum = 50
    ): array {
        return self::list_by_target(self::TARGET_MEDIA, $mediaid, $filters, $limitfrom, $limitnum);
    }

    /**
     * List markers for an external work.
     *
     * @param int $externalworkid External work id.
     * @param array<string, mixed> $filters Optional filters.
     * @param int $limitfrom Offset.
     * @param int $limitnum Limit.
     * @return array<int, stdClass>
     * @throws dml_exception
     */
    public static function list_by_external_work(
        int $externalworkid,
        array $filters = [],
        int $limitfrom = 0,
        int $limitnum = 50
    ): array {
        return self::list_by_target(self::TARGET_EXTERNAL_WORK, $externalworkid, $filters, $limitfrom, $limitnum);
    }

    /**
     * Count markers matching filters.
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
     * Return wrapped marker record.
     *
     * @return stdClass
     */
    public function to_record(): stdClass {
        return clone $this->record;
    }

    /**
     * Export this marker for services/output.
     *
     * This is not a privacy export and must be called only after policy filtering.
     *
     * @return array<string, mixed>
     */
    public function to_export(): array {
        return self::export_record($this->record);
    }

    /**
     * Export a marker record.
     *
     * @param stdClass $record Marker record.
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
            'targettype' => (string)($record->targettype ?? self::TARGET_MANUAL_REFERENCE),
            'targetid' => (int)($record->targetid ?? 0),
            'targetuuid' => (string)($record->targetuuid ?? ''),
            'tagid' => (int)($record->tagid ?? 0),
            'tagsetid' => (int)($record->tagsetid ?? 0),
            'tagkey' => (string)($record->tagkey ?? ''),
            'locatortype' => (string)($record->locatortype ?? self::LOCATOR_MANUAL_REFERENCE),
            'locatorvalue' => (string)($record->locatorvalue ?? ''),
            'locatorstart' => (string)($record->locatorstart ?? ''),
            'locatorend' => (string)($record->locatorend ?? ''),
            'locatorsort' => (int)($record->locatorsort ?? 0),
            'severity' => (string)($record->severity ?? self::SEVERITY_NOTICE),
            'visibility' => (string)($record->visibility ?? self::VISIBILITY_COURSE),
            'audiencesuitability' => (string)($record->audiencesuitability ?? self::SUITABILITY_GUIDED),
            'reviewstate' => (string)($record->reviewstate ?? self::REVIEW_DRAFT),
            'reviewedby' => (int)($record->reviewedby ?? 0),
            'timereviewed' => (int)($record->timereviewed ?? 0),
            'note' => (string)($record->note ?? ''),
            'teachingcontext' => (string)($record->teachingcontext ?? ''),
            'culturalprotocolnote' => (string)($record->culturalprotocolnote ?? ''),
            'reviewrationale' => (string)($record->reviewrationale ?? ''),
            'createdby' => (int)($record->createdby ?? 0),
            'modifiedby' => (int)($record->modifiedby ?? 0),
            'metadata' => self::decode_metadata($record->metadata ?? null),
            'timecreated' => (int)($record->timecreated ?? 0),
            'timemodified' => (int)($record->timemodified ?? 0),
        ];
    }

    /**
     * Return allowed review states.
     *
     * @return string[]
     */
    public static function review_states(): array {
        return [
            self::REVIEW_DRAFT,
            self::REVIEW_PENDING,
            self::REVIEW_REVIEWED,
            self::REVIEW_APPROVED,
            self::REVIEW_CONTESTED,
            self::REVIEW_RETIRED,
        ];
    }

    /**
     * Return allowed severity values.
     *
     * @return string[]
     */
    public static function severities(): array {
        return [
            self::SEVERITY_NOTICE,
            self::SEVERITY_MODERATE,
            self::SEVERITY_STRONG,
            self::SEVERITY_RESTRICTED,
        ];
    }

    /**
     * Return allowed target types.
     *
     * @return string[]
     */
    public static function target_types(): array {
        return [
            self::TARGET_MEDIA,
            self::TARGET_MEDIA_VERSION,
            self::TARGET_ARCHIVE_ITEM,
            self::TARGET_PROOF,
            self::TARGET_KRISTAL,
            self::TARGET_EXTERNAL_WORK,
            self::TARGET_COLLECTION,
            self::TARGET_MANUAL_REFERENCE,
        ];
    }

    /**
     * Return allowed locator types.
     *
     * @return string[]
     */
    public static function locator_types(): array {
        return [
            self::LOCATOR_TIMECODE,
            self::LOCATOR_TIMECODE_RANGE,
            self::LOCATOR_PAGE,
            self::LOCATOR_PAGE_RANGE,
            self::LOCATOR_CHAPTER,
            self::LOCATOR_CHAPTER_RANGE,
            self::LOCATOR_SECTION,
            self::LOCATOR_SECTION_RANGE,
            self::LOCATOR_PARAGRAPH,
            self::LOCATOR_PARAGRAPH_RANGE,
            self::LOCATOR_SCENE,
            self::LOCATOR_TRACK,
            self::LOCATOR_TIMESTAMP,
            self::LOCATOR_URL_FRAGMENT,
            self::LOCATOR_MANUAL_REFERENCE,
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

        foreach (['archiveid', 'courseid', 'cmid', 'contextid', 'targetid', 'tagid', 'tagsetid'] as $field) {
            if (!empty($filters[$field])) {
                $where[] = $field . ' = :' . $field;
                $params[$field] = (int)$filters[$field];
            }
        }

        if (!empty($filters['targettype'])) {
            $where[] = 'targettype = :targettype';
            $params['targettype'] = self::normalise_target_type((string)$filters['targettype']);
        }

        if (!empty($filters['targetuuid'])) {
            $where[] = 'targetuuid = :targetuuid';
            $params['targetuuid'] = trim((string)$filters['targetuuid']);
        }

        if (!empty($filters['tagkey'])) {
            $where[] = 'tagkey = :tagkey';
            $params['tagkey'] = self::normalise_tag_key((string)$filters['tagkey']);
        }

        if (!empty($filters['reviewstate'])) {
            $where[] = 'reviewstate = :reviewstate';
            $params['reviewstate'] = self::normalise_review_state((string)$filters['reviewstate']);
        }

        if (!empty($filters['severity'])) {
            $where[] = 'severity = :severity';
            $params['severity'] = self::normalise_severity((string)$filters['severity']);
        }

        if (!empty($filters['visibility'])) {
            $where[] = 'visibility = :visibility';
            $params['visibility'] = self::normalise_visibility((string)$filters['visibility']);
        }

        if (!empty($filters['audiencesuitability'])) {
            $where[] = 'audiencesuitability = :audiencesuitability';
            $params['audiencesuitability'] = self::normalise_suitability((string)$filters['audiencesuitability']);
        }

        if (!empty($filters['query'])) {
            $query = trim((string)$filters['query']);
            if ($query !== '') {
                $notesql = $DB->sql_like('note', ':querynote', false, false);
                $contextsql = $DB->sql_like('teachingcontext', ':querycontext', false, false);
                $where[] = '(' . $notesql . ' OR ' . $contextsql . ')';
                $params['querynote'] = '%' . $DB->sql_like_escape($query) . '%';
                $params['querycontext'] = '%' . $DB->sql_like_escape($query) . '%';
            }
        }

        if (empty($filters['include_retired'])) {
            $where[] = 'reviewstate <> :retiredstate';
            $params['retiredstate'] = self::REVIEW_RETIRED;
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
            'targetid',
            'tagid',
            'tagsetid',
            'locatorsort',
            'reviewedby',
            'timereviewed',
            'createdby',
            'modifiedby',
            'timecreated',
            'timemodified',
        ] as $field) {
            if (isset($normalised->{$field}) && $normalised->{$field} !== null && $normalised->{$field} !== '') {
                $normalised->{$field} = (int)$normalised->{$field};
            }
        }

        foreach ([
            'uuid',
            'targettype',
            'targetuuid',
            'tagkey',
            'locatortype',
            'locatorvalue',
            'locatorstart',
            'locatorend',
            'severity',
            'visibility',
            'audiencesuitability',
            'reviewstate',
            'note',
            'teachingcontext',
            'culturalprotocolnote',
            'reviewrationale',
        ] as $field) {
            if (isset($normalised->{$field}) && $normalised->{$field} !== null) {
                $normalised->{$field} = trim((string)$normalised->{$field});
            }
        }

        if (isset($normalised->targettype)) {
            $normalised->targettype = self::normalise_target_type((string)$normalised->targettype);
        }

        if (isset($normalised->locatortype)) {
            $normalised->locatortype = self::normalise_locator_type((string)$normalised->locatortype);
        }

        if (isset($normalised->tagkey)) {
            $normalised->tagkey = self::normalise_tag_key((string)$normalised->tagkey);
        }

        if (isset($normalised->reviewstate)) {
            $normalised->reviewstate = self::normalise_review_state((string)$normalised->reviewstate);
        }

        if (isset($normalised->severity)) {
            $normalised->severity = self::normalise_severity((string)$normalised->severity);
        }

        if (isset($normalised->visibility)) {
            $normalised->visibility = self::normalise_visibility((string)$normalised->visibility);
        }

        if (isset($normalised->audiencesuitability)) {
            $normalised->audiencesuitability = self::normalise_suitability((string)$normalised->audiencesuitability);
        }

        if ($forcreate && empty($normalised->uuid)) {
            $normalised->uuid = self::generate_uuid();
        }

        return $normalised;
    }

    /**
     * Validate required create fields.
     *
     * @param stdClass $record Marker record.
     * @throws invalid_parameter_exception
     */
    private static function validate_required_create_fields(stdClass $record): void {
        foreach (['archiveid', 'courseid', 'cmid', 'contextid', 'targettype', 'locatortype'] as $field) {
            if (empty($record->{$field})) {
                throw new invalid_parameter_exception('Missing required content marker field: ' . $field);
            }
        }

        if (empty($record->tagid) && empty($record->tagkey)) {
            throw new invalid_parameter_exception('A content marker requires tagid or tagkey.');
        }

        if ($record->targettype !== self::TARGET_MANUAL_REFERENCE && empty($record->targetid) && empty($record->targetuuid)) {
            throw new invalid_parameter_exception('A content marker requires targetid or targetuuid.');
        }

        if (empty($record->locatorvalue) && empty($record->locatorstart) && empty($record->locatorend)) {
            throw new invalid_parameter_exception('A content marker requires locator information.');
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
     * Ensure marker table exists.
     *
     * @throws moodle_exception
     */
    private static function require_table(): void {
        global $DB;

        if (!$DB->get_manager()->table_exists(self::TABLE)) {
            throw new moodle_exception('missingcontentmarkertable', 'uckkarchive', '', self::TABLE);
        }
    }

    /**
     * Normalise target type.
     *
     * @param string $targettype Target type.
     * @return string
     * @throws invalid_parameter_exception
     */
    private static function normalise_target_type(string $targettype): string {
        $targettype = trim($targettype);
        if ($targettype === '') {
            return self::TARGET_MANUAL_REFERENCE;
        }

        if (!in_array($targettype, self::target_types(), true)) {
            throw new invalid_parameter_exception('Invalid content marker target type: ' . $targettype);
        }

        return $targettype;
    }

    /**
     * Normalise locator type.
     *
     * @param string $locatortype Locator type.
     * @return string
     * @throws invalid_parameter_exception
     */
    private static function normalise_locator_type(string $locatortype): string {
        $locatortype = trim($locatortype);
        if ($locatortype === '') {
            return self::LOCATOR_MANUAL_REFERENCE;
        }

        if (!in_array($locatortype, self::locator_types(), true)) {
            throw new invalid_parameter_exception('Invalid content marker locator type: ' . $locatortype);
        }

        return $locatortype;
    }

    /**
     * Normalise review state.
     *
     * @param string $reviewstate Review state.
     * @return string
     * @throws invalid_parameter_exception
     */
    private static function normalise_review_state(string $reviewstate): string {
        $reviewstate = trim($reviewstate);
        if ($reviewstate === '') {
            return self::REVIEW_DRAFT;
        }

        if (!in_array($reviewstate, self::review_states(), true)) {
            throw new invalid_parameter_exception('Invalid content marker review state: ' . $reviewstate);
        }

        return $reviewstate;
    }

    /**
     * Normalise severity.
     *
     * @param string $severity Severity.
     * @return string
     * @throws invalid_parameter_exception
     */
    private static function normalise_severity(string $severity): string {
        $severity = trim($severity);
        if ($severity === '') {
            return self::SEVERITY_NOTICE;
        }

        if (!in_array($severity, self::severities(), true)) {
            throw new invalid_parameter_exception('Invalid content marker severity: ' . $severity);
        }

        return $severity;
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
            throw new invalid_parameter_exception('Invalid content marker visibility: ' . $visibility);
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
            throw new invalid_parameter_exception('Invalid content marker audience suitability: ' . $suitability);
        }

        return $suitability;
    }

    /**
     * Normalise tag key.
     *
     * @param string $tagkey Tag key.
     * @return string
     * @throws invalid_parameter_exception
     */
    private static function normalise_tag_key(string $tagkey): string {
        $tagkey = strtolower(trim($tagkey));

        if ($tagkey === '') {
            return '';
        }

        if (!preg_match('/^[a-z0-9_:-]+$/', $tagkey)) {
            throw new invalid_parameter_exception('Invalid content tag key: ' . $tagkey);
        }

        return $tagkey;
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
