<?php
// This file is part of Moodle - https://moodle.org/
//
// Moodle is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// any later version.

/**
 * Content advisory review domain logic for UCKK Archive.
 *
 * @package    mod_uckkarchive
 * @copyright  2026 Univers-Cité King Klown
 * @license    https://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later
 */

declare(strict_types=1);

namespace mod_uckkarchive\local;

use coding_exception;
use core\event\base as base_event;
use invalid_parameter_exception;
use moodle_exception;
use stdClass;

defined('MOODLE_INTERNAL') || die();

/**
 * Domain service for human review of content advisory markers.
 *
 * This class manages `uckkarchive_content_review`.
 *
 * Review records are used for:
 *
 * - content advisories;
 * - trigger/content warnings;
 * - cultural protocol notes;
 * - audience suitability decisions;
 * - culturally restricted access decisions;
 * - restricted integrity advisory decisions;
 * - contested or retired marker decisions.
 *
 * AI may suggest content markers, advisory tags, or notes.
 * AI cannot approve a content review.
 *
 * Authority boundary:
 *
 * - this class stores review records and review state;
 * - `content_policy` decides who may view, manage, approve, contest, or export;
 * - templates and AMD modules only render permission-filtered review data.
 */
final class content_review {
    /** Review table. */
    public const TABLE = 'uckkarchive_content_review';

    /** Draft review. */
    public const STATE_DRAFT = 'draft';

    /** Review is waiting for a human reviewer. */
    public const STATE_PENDING = 'pending_review';

    /** Review has been completed, without necessarily approving the marker. */
    public const STATE_REVIEWED = 'reviewed';

    /** Marker/advisory has been approved by a human reviewer. */
    public const STATE_APPROVED = 'approved';

    /** Marker/advisory is contested. */
    public const STATE_CONTESTED = 'contested';

    /** Marker/advisory has been retired from active use. */
    public const STATE_RETIRED = 'retired';

    /** Suitability: general audience. */
    public const SUITABILITY_GENERAL = 'general';

    /** Suitability: guided access or instructional context recommended. */
    public const SUITABILITY_GUIDED = 'guided';

    /** Suitability: mature audience. */
    public const SUITABILITY_MATURE = 'mature';

    /** Suitability: restricted. */
    public const SUITABILITY_RESTRICTED = 'restricted';

    /** Suitability: culturally restricted. */
    public const SUITABILITY_RESTRICTED_CULTURAL = 'restricted_cultural';

    /** Suitability: integrity restricted. */
    public const SUITABILITY_RESTRICTED_INTEGRITY = 'restricted_integrity';

    /** Suitability: staff only. */
    public const SUITABILITY_STAFF_ONLY = 'staff_only';

    /** Severity: notice. */
    public const SEVERITY_NOTICE = 'notice';

    /** Severity: moderate. */
    public const SEVERITY_MODERATE = 'moderate';

    /** Severity: strong. */
    public const SEVERITY_STRONG = 'strong';

    /** Severity: restricted. */
    public const SEVERITY_RESTRICTED = 'restricted';

    /**
     * Return valid review states.
     *
     * @return string[]
     */
    public static function get_states(): array {
        return [
            self::STATE_DRAFT,
            self::STATE_PENDING,
            self::STATE_REVIEWED,
            self::STATE_APPROVED,
            self::STATE_CONTESTED,
            self::STATE_RETIRED,
        ];
    }

    /**
     * Return valid audience suitability values.
     *
     * @return string[]
     */
    public static function get_suitability_values(): array {
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
     * Return valid severity values.
     *
     * @return string[]
     */
    public static function get_severity_values(): array {
        return [
            self::SEVERITY_NOTICE,
            self::SEVERITY_MODERATE,
            self::SEVERITY_STRONG,
            self::SEVERITY_RESTRICTED,
        ];
    }

    /**
     * Create a draft or pending content review.
     *
     * @param int $markerid Content marker id.
     * @param int $reviewerid Reviewer user id.
     * @param array<string, mixed> $data Optional review data.
     * @return stdClass Created review record.
     */
    public static function create(int $markerid, int $reviewerid, array $data = []): stdClass {
        global $DB;

        self::require_table();

        $markerid = self::require_positive_int($markerid, 'markerid');
        $reviewerid = self::require_positive_int($reviewerid, 'reviewerid');

        $now = time();

        $record = new stdClass();
        $record->uuid = self::get_or_create_uuid($data['uuid'] ?? null);
        $record->markerid = $markerid;
        $record->reviewerid = $reviewerid;
        $record->state = self::normalise_state((string)($data['state'] ?? self::STATE_DRAFT));
        $record->severity = self::normalise_severity((string)($data['severity'] ?? self::SEVERITY_NOTICE));
        $record->audiencesuitability = self::normalise_suitability(
            (string)($data['audiencesuitability'] ?? self::SUITABILITY_GUIDED)
        );
        $record->rationale = self::normalise_text((string)($data['rationale'] ?? ''));
        $record->reviewnote = self::normalise_text((string)($data['reviewnote'] ?? ''));
        $record->culturalprotocol = !empty($data['culturalprotocol']) ? 1 : 0;
        $record->restricted = !empty($data['restricted']) ? 1 : 0;
        $record->timecreated = $now;
        $record->timemodified = $now;

        $metadata = $data['metadata'] ?? [];
        if (!is_array($metadata)) {
            $metadata = self::decode_json((string)$metadata);
        }
        $record->metadata = self::encode_json(self::normalise_metadata($metadata));

        $id = $DB->insert_record(self::TABLE, self::filter_record_for_table($record));
        $created = self::get($id);

        self::trigger_review_event($created, 'created');

        return $created;
    }

    /**
     * Create a pending review for a marker.
     *
     * @param int $markerid Content marker id.
     * @param int $reviewerid Reviewer user id.
     * @param array<string, mixed> $data Optional review data.
     * @return stdClass
     */
    public static function create_pending(int $markerid, int $reviewerid, array $data = []): stdClass {
        $data['state'] = self::STATE_PENDING;

        return self::create($markerid, $reviewerid, $data);
    }

    /**
     * Return one content review by id.
     *
     * @param int $id Review id.
     * @param int $strictness Moodle strictness constant.
     * @return stdClass|null
     */
    public static function get(int $id, int $strictness = MUST_EXIST): ?stdClass {
        global $DB;

        self::require_table();

        $id = self::require_positive_int($id, 'id');

        $record = $DB->get_record(self::TABLE, ['id' => $id], '*', $strictness);

        return $record ? self::hydrate_record($record) : null;
    }

    /**
     * Return one content review by UUID.
     *
     * @param string $uuid Review UUID.
     * @param int $strictness Moodle strictness constant.
     * @return stdClass|null
     */
    public static function get_by_uuid(string $uuid, int $strictness = MUST_EXIST): ?stdClass {
        global $DB;

        self::require_table();

        $uuid = self::require_uuid($uuid);
        $record = $DB->get_record(self::TABLE, ['uuid' => $uuid], '*', $strictness);

        return $record ? self::hydrate_record($record) : null;
    }

    /**
     * Return reviews for a marker.
     *
     * @param int $markerid Content marker id.
     * @param array<string, mixed> $filters Optional filters.
     * @return stdClass[]
     */
    public static function get_for_marker(int $markerid, array $filters = []): array {
        global $DB;

        self::require_table();

        $conditions = ['markerid' => self::require_positive_int($markerid, 'markerid')];

        if (!empty($filters['state'])) {
            $conditions['state'] = self::normalise_state((string)$filters['state']);
        }

        if (!empty($filters['reviewerid'])) {
            $conditions['reviewerid'] = self::require_positive_int((int)$filters['reviewerid'], 'reviewerid');
        }

        $sort = clean_param((string)($filters['sort'] ?? 'timemodified DESC, id DESC'), PARAM_TEXT);
        $records = $DB->get_records(self::TABLE, $conditions, $sort);

        return array_map([self::class, 'hydrate_record'], array_values($records));
    }

    /**
     * Return the latest review for a marker.
     *
     * @param int $markerid Content marker id.
     * @param string|null $state Optional state.
     * @return stdClass|null
     */
    public static function get_latest_for_marker(int $markerid, ?string $state = null): ?stdClass {
        global $DB;

        self::require_table();

        $params = ['markerid' => self::require_positive_int($markerid, 'markerid')];
        $where = 'markerid = :markerid';

        if ($state !== null) {
            $params['state'] = self::normalise_state($state);
            $where .= ' AND state = :state';
        }

        $record = $DB->get_record_select(
            self::TABLE,
            $where,
            $params,
            '*',
            IGNORE_MULTIPLE
        );

        if (!$record) {
            return null;
        }

        // Moodle get_record_select cannot apply order without SQL here, so use full query for correctness.
        $sql = "SELECT *
                  FROM {" . self::TABLE . "}
                 WHERE {$where}
              ORDER BY timemodified DESC, id DESC";
        $record = $DB->get_record_sql($sql, $params, IGNORE_MULTIPLE);

        return $record ? self::hydrate_record($record) : null;
    }

    /**
     * Update one review.
     *
     * @param int $id Review id.
     * @param array<string, mixed> $data Update data.
     * @return stdClass Updated review.
     */
    public static function update(int $id, array $data): stdClass {
        global $DB;

        self::require_table();

        $current = self::get($id);
        $update = new stdClass();
        $update->id = $current->id;

        if (array_key_exists('state', $data)) {
            $update->state = self::normalise_state((string)$data['state']);
        }

        if (array_key_exists('reviewerid', $data)) {
            $update->reviewerid = self::require_positive_int((int)$data['reviewerid'], 'reviewerid');
        }

        if (array_key_exists('severity', $data)) {
            $update->severity = self::normalise_severity((string)$data['severity']);
        }

        if (array_key_exists('audiencesuitability', $data)) {
            $update->audiencesuitability = self::normalise_suitability((string)$data['audiencesuitability']);
        }

        if (array_key_exists('rationale', $data)) {
            $update->rationale = self::normalise_text((string)$data['rationale']);
        }

        if (array_key_exists('reviewnote', $data)) {
            $update->reviewnote = self::normalise_text((string)$data['reviewnote']);
        }

        if (array_key_exists('culturalprotocol', $data)) {
            $update->culturalprotocol = !empty($data['culturalprotocol']) ? 1 : 0;
        }

        if (array_key_exists('restricted', $data)) {
            $update->restricted = !empty($data['restricted']) ? 1 : 0;
        }

        if (array_key_exists('metadata', $data)) {
            $metadata = $data['metadata'];
            if (!is_array($metadata)) {
                $metadata = self::decode_json((string)$metadata);
            }
            $update->metadata = self::encode_json(self::normalise_metadata($metadata));
        }

        $update->timemodified = time();

        $DB->update_record(self::TABLE, self::filter_record_for_table($update));

        $updated = self::get($id);
        self::trigger_review_event($updated, 'updated');

        return $updated;
    }

    /**
     * Review a content marker.
     *
     * @param int $markerid Content marker id.
     * @param int $reviewerid Reviewer user id.
     * @param string $state Target review state.
     * @param array<string, mixed> $data Review data.
     * @return stdClass Review record.
     */
    public static function review_marker(int $markerid, int $reviewerid, string $state, array $data = []): stdClass {
        $data['state'] = self::normalise_state($state);

        $latest = self::get_latest_for_marker($markerid);
        if ($latest && in_array($latest->state, [self::STATE_DRAFT, self::STATE_PENDING], true)) {
            $data['reviewerid'] = $reviewerid;

            return self::update((int)$latest->id, $data);
        }

        return self::create($markerid, $reviewerid, $data);
    }

    /**
     * Approve a content marker.
     *
     * @param int $markerid Content marker id.
     * @param int $reviewerid Reviewer user id.
     * @param string $rationale Approval rationale.
     * @param array<string, mixed> $data Additional data.
     * @return stdClass
     */
    public static function approve(int $markerid, int $reviewerid, string $rationale = '', array $data = []): stdClass {
        $data['state'] = self::STATE_APPROVED;
        $data['rationale'] = $rationale !== '' ? $rationale : ($data['rationale'] ?? '');

        return self::review_marker($markerid, $reviewerid, self::STATE_APPROVED, $data);
    }

    /**
     * Mark a content marker as reviewed.
     *
     * @param int $markerid Content marker id.
     * @param int $reviewerid Reviewer user id.
     * @param string $rationale Review rationale.
     * @param array<string, mixed> $data Additional data.
     * @return stdClass
     */
    public static function mark_reviewed(int $markerid, int $reviewerid, string $rationale = '', array $data = []): stdClass {
        $data['state'] = self::STATE_REVIEWED;
        $data['rationale'] = $rationale !== '' ? $rationale : ($data['rationale'] ?? '');

        return self::review_marker($markerid, $reviewerid, self::STATE_REVIEWED, $data);
    }

    /**
     * Contest a content marker review.
     *
     * @param int $markerid Content marker id.
     * @param int $reviewerid Reviewer user id.
     * @param string $rationale Contest rationale.
     * @param array<string, mixed> $data Additional data.
     * @return stdClass
     */
    public static function contest(int $markerid, int $reviewerid, string $rationale, array $data = []): stdClass {
        $data['state'] = self::STATE_CONTESTED;
        $data['rationale'] = $rationale;

        return self::review_marker($markerid, $reviewerid, self::STATE_CONTESTED, $data);
    }

    /**
     * Retire a content marker review.
     *
     * @param int $markerid Content marker id.
     * @param int $reviewerid Reviewer user id.
     * @param string $rationale Retirement rationale.
     * @param array<string, mixed> $data Additional data.
     * @return stdClass
     */
    public static function retire(int $markerid, int $reviewerid, string $rationale, array $data = []): stdClass {
        $data['state'] = self::STATE_RETIRED;
        $data['rationale'] = $rationale;

        return self::review_marker($markerid, $reviewerid, self::STATE_RETIRED, $data);
    }

    /**
     * Return whether a marker has an approved review.
     *
     * @param int $markerid Content marker id.
     * @return bool
     */
    public static function is_marker_approved(int $markerid): bool {
        return self::get_latest_for_marker($markerid, self::STATE_APPROVED) !== null;
    }

    /**
     * Return whether a marker has a pending review.
     *
     * @param int $markerid Content marker id.
     * @return bool
     */
    public static function has_pending_review(int $markerid): bool {
        return self::get_latest_for_marker($markerid, self::STATE_PENDING) !== null;
    }

    /**
     * Return whether a review state is valid.
     *
     * @param string $state Review state.
     * @return bool
     */
    public static function is_valid_state(string $state): bool {
        return in_array(self::clean_key($state), self::get_states(), true);
    }

    /**
     * Return whether a suitability value is valid.
     *
     * @param string $suitability Audience suitability.
     * @return bool
     */
    public static function is_valid_suitability(string $suitability): bool {
        return in_array(self::clean_key($suitability), self::get_suitability_values(), true);
    }

    /**
     * Return whether a severity value is valid.
     *
     * @param string $severity Severity.
     * @return bool
     */
    public static function is_valid_severity(string $severity): bool {
        return in_array(self::clean_key($severity), self::get_severity_values(), true);
    }

    /**
     * Convert a database record into a hydrated domain record.
     *
     * @param stdClass $record Database record.
     * @return stdClass
     */
    public static function hydrate_record(stdClass $record): stdClass {
        $record->id = (int)$record->id;
        $record->markerid = isset($record->markerid) ? (int)$record->markerid : 0;
        $record->reviewerid = isset($record->reviewerid) ? (int)$record->reviewerid : 0;
        $record->state = self::normalise_state((string)($record->state ?? self::STATE_DRAFT));
        $record->severity = self::normalise_severity((string)($record->severity ?? self::SEVERITY_NOTICE));
        $record->audiencesuitability = self::normalise_suitability(
            (string)($record->audiencesuitability ?? self::SUITABILITY_GUIDED)
        );
        $record->culturalprotocol = !empty($record->culturalprotocol) ? 1 : 0;
        $record->restricted = !empty($record->restricted) ? 1 : 0;
        $record->metadata = self::decode_json((string)($record->metadata ?? '{}'));
        $record->timecreated = isset($record->timecreated) ? (int)$record->timecreated : 0;
        $record->timemodified = isset($record->timemodified) ? (int)$record->timemodified : 0;

        return $record;
    }

    /**
     * Return review as exportable array.
     *
     * @param stdClass $review Review record.
     * @return array<string, mixed>
     */
    public static function to_export_array(stdClass $review): array {
        $review = self::hydrate_record($review);

        return [
            'id' => $review->id,
            'uuid' => $review->uuid ?? '',
            'markerid' => $review->markerid,
            'reviewerid' => $review->reviewerid,
            'state' => $review->state,
            'severity' => $review->severity,
            'audiencesuitability' => $review->audiencesuitability,
            'rationale' => $review->rationale ?? '',
            'reviewnote' => $review->reviewnote ?? '',
            'culturalprotocol' => (bool)$review->culturalprotocol,
            'restricted' => (bool)$review->restricted,
            'metadata' => $review->metadata,
            'timecreated' => $review->timecreated,
            'timemodified' => $review->timemodified,
        ];
    }

    /**
     * Delete one review.
     *
     * Caller must already have policy approval.
     *
     * @param int $id Review id.
     * @return bool
     */
    public static function delete(int $id): bool {
        global $DB;

        self::require_table();

        $review = self::get($id);
        $deleted = $DB->delete_records(self::TABLE, ['id' => $review->id]);

        if ($deleted) {
            self::trigger_review_event($review, 'deleted');
        }

        return $deleted;
    }

    /**
     * Delete all reviews for a marker.
     *
     * Caller must already have policy approval.
     *
     * @param int $markerid Content marker id.
     * @return bool
     */
    public static function delete_for_marker(int $markerid): bool {
        global $DB;

        self::require_table();

        $markerid = self::require_positive_int($markerid, 'markerid');
        $reviews = self::get_for_marker($markerid);

        $deleted = $DB->delete_records(self::TABLE, ['markerid' => $markerid]);

        if ($deleted) {
            foreach ($reviews as $review) {
                self::trigger_review_event($review, 'deleted');
            }
        }

        return $deleted;
    }

    /**
     * Ensure the review table exists.
     *
     * @return void
     * @throws moodle_exception
     */
    private static function require_table(): void {
        global $DB;

        $manager = $DB->get_manager();
        $table = new \xmldb_table(self::TABLE);

        if (!$manager->table_exists($table)) {
            throw new moodle_exception('missingtable', 'error', '', self::TABLE);
        }
    }

    /**
     * Filter record properties to known table columns.
     *
     * This makes the class safe while schema is being built incrementally.
     *
     * @param stdClass $record Record.
     * @return stdClass
     */
    private static function filter_record_for_table(stdClass $record): stdClass {
        global $DB;

        $columns = $DB->get_columns(self::TABLE);
        $filtered = new stdClass();

        foreach ($columns as $name => $definition) {
            if (property_exists($record, $name)) {
                $filtered->{$name} = $record->{$name};
            }
        }

        return $filtered;
    }

    /**
     * Normalize a review state.
     *
     * @param string $state Review state.
     * @return string
     */
    private static function normalise_state(string $state): string {
        $state = self::clean_key($state);

        if (!self::is_valid_state($state)) {
            throw new invalid_parameter_exception('Invalid content review state: ' . $state);
        }

        return $state;
    }

    /**
     * Normalize audience suitability.
     *
     * @param string $suitability Audience suitability.
     * @return string
     */
    private static function normalise_suitability(string $suitability): string {
        $suitability = self::clean_key($suitability);

        if (!self::is_valid_suitability($suitability)) {
            throw new invalid_parameter_exception('Invalid audience suitability: ' . $suitability);
        }

        return $suitability;
    }

    /**
     * Normalize severity.
     *
     * @param string $severity Severity.
     * @return string
     */
    private static function normalise_severity(string $severity): string {
        $severity = self::clean_key($severity);

        if (!self::is_valid_severity($severity)) {
            throw new invalid_parameter_exception('Invalid content advisory severity: ' . $severity);
        }

        return $severity;
    }

    /**
     * Clean a machine key.
     *
     * @param string $key Key.
     * @return string
     */
    private static function clean_key(string $key): string {
        return clean_param(\core_text::strtolower(trim($key)), PARAM_ALPHANUMEXT);
    }

    /**
     * Normalize free text.
     *
     * @param string $text Text.
     * @return string
     */
    private static function normalise_text(string $text): string {
        return clean_param(trim($text), PARAM_TEXT);
    }

    /**
     * Normalize metadata recursively enough for JSON storage.
     *
     * @param array<string, mixed> $metadata Metadata.
     * @return array<string, mixed>
     */
    private static function normalise_metadata(array $metadata): array {
        $clean = [];

        foreach ($metadata as $key => $value) {
            $cleankey = clean_param((string)$key, PARAM_ALPHANUMEXT);

            if ($cleankey === '') {
                continue;
            }

            if (is_array($value)) {
                $clean[$cleankey] = self::normalise_metadata($value);
                continue;
            }

            if (is_bool($value) || is_int($value) || is_float($value) || $value === null) {
                $clean[$cleankey] = $value;
                continue;
            }

            $clean[$cleankey] = clean_param((string)$value, PARAM_TEXT);
        }

        return $clean;
    }

    /**
     * Encode JSON safely.
     *
     * @param array<string, mixed> $data Data.
     * @return string
     */
    private static function encode_json(array $data): string {
        $json = json_encode($data, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);

        if ($json === false) {
            throw new coding_exception('Unable to encode content review metadata.');
        }

        return $json;
    }

    /**
     * Decode JSON safely.
     *
     * @param string $json JSON string.
     * @return array<string, mixed>
     */
    private static function decode_json(string $json): array {
        $json = trim($json);
        if ($json === '') {
            return [];
        }

        $data = json_decode($json, true);
        if (!is_array($data)) {
            return [];
        }

        return $data;
    }

    /**
     * Require positive integer.
     *
     * @param int $value Value.
     * @param string $name Name.
     * @return int
     */
    private static function require_positive_int(int $value, string $name): int {
        if ($value <= 0) {
            throw new invalid_parameter_exception('Invalid ' . $name . '.');
        }

        return $value;
    }

    /**
     * Return a UUID.
     *
     * @param mixed $uuid Optional UUID.
     * @return string
     */
    private static function get_or_create_uuid(mixed $uuid = null): string {
        if (is_string($uuid) && trim($uuid) !== '') {
            return self::require_uuid($uuid);
        }

        if (class_exists(uuid::class) && method_exists(uuid::class, 'generate')) {
            return uuid::generate();
        }

        return \core\uuid::generate();
    }

    /**
     * Validate a UUID-ish string.
     *
     * @param string $uuid UUID.
     * @return string
     */
    private static function require_uuid(string $uuid): string {
        $uuid = trim($uuid);

        if ($uuid === '') {
            throw new invalid_parameter_exception('Invalid UUID.');
        }

        if (class_exists(uuid::class) && method_exists(uuid::class, 'validate')) {
            if (!uuid::validate($uuid)) {
                throw new invalid_parameter_exception('Invalid UUID.');
            }

            return $uuid;
        }

        return clean_param($uuid, PARAM_ALPHANUMEXT);
    }

    /**
     * Trigger content marker reviewed event when available.
     *
     * @param stdClass $review Review record.
     * @param string $action Action label.
     * @return void
     */
    private static function trigger_review_event(stdClass $review, string $action): void {
        $eventclass = '\\mod_uckkarchive\\event\\content_marker_reviewed';

        if (!class_exists($eventclass) || !is_subclass_of($eventclass, base_event::class)) {
            return;
        }

        $other = [
            'uuid' => $review->uuid ?? '',
            'markerid' => $review->markerid ?? 0,
            'state' => $review->state ?? '',
            'action' => $action,
        ];

        $data = [
            'objectid' => (int)$review->id,
            'context' => \context_system::instance(),
            'relateduserid' => !empty($review->reviewerid) ? (int)$review->reviewerid : null,
            'other' => $other,
        ];

        try {
            $event = $eventclass::create($data);
            $event->trigger();
        } catch (\Throwable $ignored) {
            // Events must not break review persistence.
        }
    }
}
