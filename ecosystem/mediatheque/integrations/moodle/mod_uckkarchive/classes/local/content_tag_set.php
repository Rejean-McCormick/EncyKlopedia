<?php
// This file is part of Moodle - https://moodle.org/
//
// Moodle is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// any later version.

/**
 * Content tag set domain service for mod_uckkarchive.
 *
 * Content tag sets group content advisory tags into reusable vocabularies.
 * Examples include general advisories, cultural protocols, classroom
 * suitability, integrity-sensitive content, and youth-access vocabularies.
 *
 * @package    mod_uckkarchive
 * @copyright  2026 Univers-Cité King Klown
 * @license    https://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later
 */

declare(strict_types=1);

namespace mod_uckkarchive\local;

defined('MOODLE_INTERNAL') || die();

use dml_exception;
use invalid_parameter_exception;
use moodle_exception;
use stdClass;
use xmldb_table;

/**
 * Domain service for content tag sets.
 */
final class content_tag_set {
    /** @var string Content tag set table. */
    public const TABLE = 'uckkarchive_content_tag_set';

    /** @var string Content tag table. */
    public const TAG_TABLE = 'uckkarchive_content_tag';

    /** @var string Active status. */
    public const STATUS_ACTIVE = 'active';

    /** @var string Draft status. */
    public const STATUS_DRAFT = 'draft';

    /** @var string Archived status. */
    public const STATUS_ARCHIVED = 'archived';

    /** @var string Retired status. */
    public const STATUS_RETIRED = 'retired';

    /** @var string General advisory tag set key. */
    public const SET_GENERAL_ADVISORIES = 'general_advisories';

    /** @var string Cultural protocols tag set key. */
    public const SET_CULTURAL_PROTOCOLS = 'cultural_protocols';

    /** @var string Classroom suitability tag set key. */
    public const SET_CLASSROOM_SUITABILITY = 'classroom_suitability';

    /** @var string Integrity-sensitive tag set key. */
    public const SET_INTEGRITY_SENSITIVE = 'integrity_sensitive';

    /** @var string Youth access tag set key. */
    public const SET_YOUTH_ACCESS = 'youth_access';

    /**
     * Return canonical baseline tag sets.
     *
     * @return array<string,array<string,mixed>>
     */
    public static function baseline_sets(): array {
        return [
            self::SET_GENERAL_ADVISORIES => [
                'name' => 'General advisories',
                'description' => 'General content advisory vocabulary for sensitive or unsuitable material.',
                'purpose' => 'general_advisory',
                'visibility' => 'course',
                'audiencesuitability' => 'guided',
                'status' => self::STATUS_ACTIVE,
                'locked' => 1,
                'sortorder' => 10,
            ],
            self::SET_CULTURAL_PROTOCOLS => [
                'name' => 'Cultural protocols',
                'description' => 'Cultural protocol vocabulary for culturally sensitive, sacred, restricted, contextual, or community-governed material.',
                'purpose' => 'cultural_protocol',
                'visibility' => 'restricted_cultural',
                'audiencesuitability' => 'restricted_cultural',
                'status' => self::STATUS_ACTIVE,
                'locked' => 1,
                'sortorder' => 20,
            ],
            self::SET_CLASSROOM_SUITABILITY => [
                'name' => 'Classroom suitability',
                'description' => 'Suitability vocabulary for guided teaching, maturity, context, and learner-facing access decisions.',
                'purpose' => 'classroom_suitability',
                'visibility' => 'course',
                'audiencesuitability' => 'guided',
                'status' => self::STATUS_ACTIVE,
                'locked' => 1,
                'sortorder' => 30,
            ],
            self::SET_INTEGRITY_SENSITIVE => [
                'name' => 'Integrity-sensitive',
                'description' => 'Vocabulary for restricted case material, evidence sensitivity, appeal-sensitive records, and witness-sensitive material.',
                'purpose' => 'integrity_sensitive',
                'visibility' => 'restricted_integrity',
                'audiencesuitability' => 'restricted_integrity',
                'status' => self::STATUS_ACTIVE,
                'locked' => 1,
                'sortorder' => 40,
            ],
            self::SET_YOUTH_ACCESS => [
                'name' => 'Youth access',
                'description' => 'Vocabulary for youth suitability, not-for-children material, guided access, and maturity restrictions.',
                'purpose' => 'youth_access',
                'visibility' => 'course',
                'audiencesuitability' => 'guided',
                'status' => self::STATUS_ACTIVE,
                'locked' => 1,
                'sortorder' => 50,
            ],
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
            self::STATUS_ARCHIVED,
            self::STATUS_RETIRED,
        ];
    }

    /**
     * Get a tag set by id.
     *
     * @param int $id Tag set id.
     * @param int $strictness Moodle record strictness.
     * @return stdClass|false
     * @throws dml_exception
     */
    public static function get(int $id, int $strictness = MUST_EXIST): stdClass|false {
        global $DB;

        if ($id <= 0) {
            throw new invalid_parameter_exception('Invalid content tag set id.');
        }

        return $DB->get_record(self::TABLE, ['id' => $id], '*', $strictness);
    }

    /**
     * Get a tag set by key.
     *
     * @param string $key Tag set key.
     * @param int $strictness Moodle record strictness.
     * @return stdClass|false
     * @throws dml_exception
     */
    public static function get_by_key(string $key, int $strictness = MUST_EXIST): stdClass|false {
        global $DB;

        $key = self::normalise_key($key);

        return $DB->get_record(self::TABLE, ['tagsetkey' => $key], '*', $strictness);
    }

    /**
     * Get a tag set by UUID.
     *
     * @param string $uuid Tag set UUID.
     * @param int $strictness Moodle record strictness.
     * @return stdClass|false
     * @throws dml_exception
     */
    public static function get_by_uuid(string $uuid, int $strictness = MUST_EXIST): stdClass|false {
        global $DB;

        $uuid = trim($uuid);
        if ($uuid === '') {
            throw new invalid_parameter_exception('Invalid content tag set UUID.');
        }

        return $DB->get_record(self::TABLE, ['uuid' => $uuid], '*', $strictness);
    }

    /**
     * Return all tag sets filtered by status.
     *
     * @param string|null $status Optional status.
     * @param bool $includehidden Whether hidden records are included.
     * @return stdClass[]
     * @throws dml_exception
     */
    public static function get_all(?string $status = self::STATUS_ACTIVE, bool $includehidden = false): array {
        global $DB;

        $conditions = [];
        if ($status !== null && $status !== '') {
            $conditions['status'] = self::normalise_status($status);
        }
        if (!$includehidden && self::field_exists(self::TABLE, 'visible')) {
            $conditions['visible'] = 1;
        }

        return $DB->get_records(self::TABLE, $conditions, 'sortorder ASC, name ASC, id ASC');
    }

    /**
     * Create a tag set.
     *
     * @param array<string,mixed> $data Tag set data.
     * @return stdClass Created tag set.
     * @throws dml_exception
     */
    public static function create(array $data): stdClass {
        global $DB, $USER;

        $now = time();

        $record = new stdClass();
        $record->uuid = self::normalise_uuid($data['uuid'] ?? null);
        $record->tagsetkey = self::normalise_key((string)($data['tagsetkey'] ?? $data['key'] ?? ''));
        $record->name = self::clean_text($data['name'] ?? '');
        $record->description = self::clean_text($data['description'] ?? '');
        $record->purpose = self::normalise_purpose((string)($data['purpose'] ?? $record->tagsetkey));
        $record->visibility = self::clean_visibility($data['visibility'] ?? 'course');
        $record->audiencesuitability = self::clean_audience($data['audiencesuitability'] ?? 'guided');
        $record->status = self::normalise_status((string)($data['status'] ?? self::STATUS_ACTIVE));
        $record->visible = !isset($data['visible']) || !empty($data['visible']) ? 1 : 0;
        $record->locked = !empty($data['locked']) ? 1 : 0;
        $record->sortorder = (int)($data['sortorder'] ?? 0);
        $record->createdby = (int)($data['createdby'] ?? ($USER->id ?? 0));
        $record->modifiedby = (int)($data['modifiedby'] ?? ($USER->id ?? 0));
        $record->timecreated = (int)($data['timecreated'] ?? $now);
        $record->timemodified = (int)($data['timemodified'] ?? $now);
        $record->metadata = self::encode_metadata($data['metadata'] ?? []);

        self::validate_record($record);

        if ($DB->record_exists(self::TABLE, ['tagsetkey' => $record->tagsetkey])) {
            throw new moodle_exception('contenttagsetkeyexists', 'uckkarchive', '', $record->tagsetkey);
        }

        $record = self::filter_to_existing_fields($record, self::TABLE);
        $record->id = $DB->insert_record(self::TABLE, $record);

        return self::get((int)$record->id);
    }

    /**
     * Create a tag set if it does not already exist.
     *
     * @param string $key Tag set key.
     * @param array<string,mixed> $data Tag set data.
     * @return stdClass Existing or created tag set.
     * @throws dml_exception
     */
    public static function ensure(string $key, array $data = []): stdClass {
        global $DB;

        $key = self::normalise_key($key);
        $existing = $DB->get_record(self::TABLE, ['tagsetkey' => $key], '*', IGNORE_MISSING);
        if ($existing) {
            return $existing;
        }

        $data['tagsetkey'] = $key;

        return self::create($data);
    }

    /**
     * Ensure baseline tag sets exist.
     *
     * Existing records are not overwritten.
     *
     * @return array<string,stdClass>
     * @throws dml_exception
     */
    public static function ensure_baseline_sets(): array {
        $sets = [];

        foreach (self::baseline_sets() as $key => $data) {
            $sets[$key] = self::ensure($key, $data);
        }

        return $sets;
    }

    /**
     * Update a tag set.
     *
     * Locked baseline tag sets may still receive metadata correction, but their
     * key is immutable.
     *
     * @param int $id Tag set id.
     * @param array<string,mixed> $data Update data.
     * @return stdClass Updated record.
     * @throws dml_exception
     */
    public static function update(int $id, array $data): stdClass {
        global $DB, $USER;

        $record = self::get($id);
        $oldkey = (string)$record->tagsetkey;

        if (array_key_exists('tagsetkey', $data) || array_key_exists('key', $data)) {
            $newkey = self::normalise_key((string)($data['tagsetkey'] ?? $data['key']));
            if ($newkey !== $oldkey) {
                if (!empty($record->locked)) {
                    throw new moodle_exception('cannotrenamelockedcontenttagset', 'uckkarchive');
                }
                if ($DB->record_exists_select(
                    self::TABLE,
                    'tagsetkey = :tagsetkey AND id <> :id',
                    ['tagsetkey' => $newkey, 'id' => $id]
                )) {
                    throw new moodle_exception('contenttagsetkeyexists', 'uckkarchive', '', $newkey);
                }
                $record->tagsetkey = $newkey;
            }
        }

        $fields = [
            'name',
            'description',
            'purpose',
            'visibility',
            'audiencesuitability',
            'status',
            'visible',
            'locked',
            'sortorder',
            'metadata',
        ];

        foreach ($fields as $field) {
            if (!array_key_exists($field, $data)) {
                continue;
            }

            switch ($field) {
                case 'name':
                case 'description':
                    $record->{$field} = self::clean_text($data[$field]);
                    break;

                case 'purpose':
                    $record->{$field} = self::normalise_purpose((string)$data[$field]);
                    break;

                case 'visibility':
                    $record->{$field} = self::clean_visibility($data[$field]);
                    break;

                case 'audiencesuitability':
                    $record->{$field} = self::clean_audience($data[$field]);
                    break;

                case 'status':
                    $record->{$field} = self::normalise_status((string)$data[$field]);
                    break;

                case 'visible':
                case 'locked':
                    $record->{$field} = !empty($data[$field]) ? 1 : 0;
                    break;

                case 'sortorder':
                    $record->{$field} = (int)$data[$field];
                    break;

                case 'metadata':
                    $record->{$field} = self::encode_metadata($data[$field]);
                    break;
            }
        }

        $record->modifiedby = (int)($USER->id ?? 0);
        $record->timemodified = time();

        self::validate_record($record);

        $DB->update_record(self::TABLE, self::filter_to_existing_fields($record, self::TABLE));

        return self::get($id);
    }

    /**
     * Archive a tag set.
     *
     * This keeps the vocabulary for historical markers and exports but removes
     * it from normal active selection.
     *
     * @param int $id Tag set id.
     * @return stdClass Updated tag set.
     * @throws dml_exception
     */
    public static function archive(int $id): stdClass {
        return self::update($id, [
            'status' => self::STATUS_ARCHIVED,
            'visible' => 0,
        ]);
    }

    /**
     * Retire a tag set.
     *
     * Retired sets remain preserved for provenance and exports.
     *
     * @param int $id Tag set id.
     * @return stdClass Updated tag set.
     * @throws dml_exception
     */
    public static function retire(int $id): stdClass {
        return self::update($id, [
            'status' => self::STATUS_RETIRED,
            'visible' => 0,
        ]);
    }

    /**
     * Return tags that belong to a tag set.
     *
     * This supports either `tagsetid` or `tagsetkey` schemas. The target schema
     * should use one canonical linkage, but this method remains tolerant during
     * staged generation and upgrade work.
     *
     * @param int|string|stdClass $tagset Tag set id, key, or record.
     * @param bool $activeonly Whether only active/visible tags are returned.
     * @return stdClass[]
     * @throws dml_exception
     */
    public static function get_tags(int|string|stdClass $tagset, bool $activeonly = true): array {
        global $DB;

        $record = self::resolve($tagset);

        if (!self::table_exists(self::TAG_TABLE)) {
            return [];
        }

        $conditions = [];
        if (self::field_exists(self::TAG_TABLE, 'tagsetid')) {
            $conditions['tagsetid'] = (int)$record->id;
        } else if (self::field_exists(self::TAG_TABLE, 'tagsetkey')) {
            $conditions['tagsetkey'] = (string)$record->tagsetkey;
        } else {
            return [];
        }

        if ($activeonly && self::field_exists(self::TAG_TABLE, 'status')) {
            $conditions['status'] = self::STATUS_ACTIVE;
        }

        if ($activeonly && self::field_exists(self::TAG_TABLE, 'visible')) {
            $conditions['visible'] = 1;
        }

        return $DB->get_records(self::TAG_TABLE, $conditions, 'sortorder ASC, label ASC, name ASC, id ASC');
    }

    /**
     * Resolve a tag set from id, key, or record.
     *
     * @param int|string|stdClass $tagset Tag set id, key, or record.
     * @return stdClass
     * @throws dml_exception
     */
    public static function resolve(int|string|stdClass $tagset): stdClass {
        if ($tagset instanceof stdClass) {
            if (empty($tagset->id)) {
                throw new invalid_parameter_exception('Invalid content tag set record.');
            }

            return $tagset;
        }

        if (is_int($tagset) || ctype_digit((string)$tagset)) {
            return self::get((int)$tagset);
        }

        return self::get_by_key((string)$tagset);
    }

    /**
     * Convert a tag set to a safe summary payload.
     *
     * @param stdClass $record Tag set.
     * @param bool $includetags Include tag summaries when available.
     * @return array<string,mixed>
     * @throws dml_exception
     */
    public static function export_summary(stdClass $record, bool $includetags = false): array {
        $summary = [
            'id' => (int)($record->id ?? 0),
            'uuid' => (string)($record->uuid ?? ''),
            'tagsetkey' => (string)($record->tagsetkey ?? ''),
            'name' => (string)($record->name ?? ''),
            'description' => (string)($record->description ?? ''),
            'purpose' => (string)($record->purpose ?? ''),
            'visibility' => (string)($record->visibility ?? ''),
            'audiencesuitability' => (string)($record->audiencesuitability ?? ''),
            'status' => (string)($record->status ?? ''),
            'visible' => !empty($record->visible),
            'locked' => !empty($record->locked),
            'sortorder' => (int)($record->sortorder ?? 0),
            'timecreated' => (int)($record->timecreated ?? 0),
            'timemodified' => (int)($record->timemodified ?? 0),
            'metadata' => self::decode_metadata((string)($record->metadata ?? '')),
        ];

        if ($includetags) {
            $summary['tags'] = array_map(static function(stdClass $tag): array {
                return [
                    'id' => (int)($tag->id ?? 0),
                    'uuid' => (string)($tag->uuid ?? ''),
                    'tagkey' => (string)($tag->tagkey ?? $tag->key ?? ''),
                    'label' => (string)($tag->label ?? $tag->name ?? ''),
                    'severity' => (string)($tag->severity ?? ''),
                    'category' => (string)($tag->category ?? ''),
                    'status' => (string)($tag->status ?? ''),
                    'visible' => !isset($tag->visible) || !empty($tag->visible),
                ];
            }, self::get_tags($record));
        }

        return $summary;
    }

    /**
     * Validate a tag set record.
     *
     * @param stdClass $record Candidate record.
     * @return void
     */
    private static function validate_record(stdClass $record): void {
        if (empty($record->uuid)) {
            throw new invalid_parameter_exception('Content tag set UUID is required.');
        }

        if (empty($record->tagsetkey)) {
            throw new invalid_parameter_exception('Content tag set key is required.');
        }

        if (empty($record->name)) {
            throw new invalid_parameter_exception('Content tag set name is required.');
        }

        self::normalise_status((string)$record->status);
    }

    /**
     * Normalise a tag set key.
     *
     * @param string $key Raw key.
     * @return string
     */
    private static function normalise_key(string $key): string {
        $key = trim(core_text::strtolower($key));
        $key = preg_replace('/[^a-z0-9_]+/', '_', $key) ?? '';
        $key = trim($key, '_');

        if ($key === '') {
            throw new invalid_parameter_exception('Content tag set key is required.');
        }

        if (core_text::strlen($key) > 100) {
            throw new invalid_parameter_exception('Content tag set key is too long.');
        }

        return $key;
    }

    /**
     * Normalise purpose.
     *
     * @param string $purpose Raw purpose.
     * @return string
     */
    private static function normalise_purpose(string $purpose): string {
        $purpose = trim(core_text::strtolower($purpose));
        $purpose = preg_replace('/[^a-z0-9_]+/', '_', $purpose) ?? '';
        $purpose = trim($purpose, '_');

        return $purpose !== '' ? $purpose : 'general_advisory';
    }

    /**
     * Normalise status.
     *
     * @param string $status Raw status.
     * @return string
     */
    private static function normalise_status(string $status): string {
        $status = clean_param($status, PARAM_ALPHANUMEXT);

        if (!in_array($status, self::statuses(), true)) {
            throw new invalid_parameter_exception('Invalid content tag set status.');
        }

        return $status;
    }

    /**
     * Clean visibility value.
     *
     * @param mixed $visibility Raw value.
     * @return string
     */
    private static function clean_visibility(mixed $visibility): string {
        $visibility = clean_param((string)$visibility, PARAM_ALPHANUMEXT);
        if ($visibility === 'institutional') {
            return 'institution';
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

        return in_array($visibility, $allowed, true) ? $visibility : 'restricted';
    }

    /**
     * Clean audience suitability value.
     *
     * @param mixed $audience Raw value.
     * @return string
     */
    private static function clean_audience(mixed $audience): string {
        $audience = clean_param((string)$audience, PARAM_ALPHANUMEXT);
        $allowed = [
            'general',
            'guided',
            'mature',
            'restricted',
            'restricted_cultural',
            'restricted_integrity',
            'staff_only',
        ];

        return in_array($audience, $allowed, true) ? $audience : 'guided';
    }

    /**
     * Clean text.
     *
     * @param mixed $value Raw value.
     * @return string
     */
    private static function clean_text(mixed $value): string {
        return trim(clean_param((string)$value, PARAM_TEXT));
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

        return self::fallback_uuidv4();
    }

    /**
     * Fallback UUID v4 generator for staged generation.
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
     * Encode metadata.
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

            return json_encode(['raw' => $metadata], JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES) ?: '{}';
        }

        if (!is_array($metadata) && !is_object($metadata)) {
            return '{}';
        }

        return json_encode($metadata, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES) ?: '{}';
    }

    /**
     * Decode metadata.
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

    /**
     * Return whether a table exists.
     *
     * @param string $table Table name without braces.
     * @return bool
     */
    private static function table_exists(string $table): bool {
        global $DB;

        $dbman = $DB->get_manager();
        return $dbman->table_exists(new xmldb_table($table));
    }

    /**
     * Return whether a field exists.
     *
     * @param string $table Table name without braces.
     * @param string $field Field name.
     * @return bool
     */
    private static function field_exists(string $table, string $field): bool {
        global $DB;

        if (!self::table_exists($table)) {
            return false;
        }

        $dbman = $DB->get_manager();
        return $dbman->field_exists(new xmldb_table($table), $field);
    }

    /**
     * Remove properties that are not present in the target DB table.
     *
     * This keeps the class tolerant during staged implementation while the
     * install.xml/upgrade.php schema is being generated.
     *
     * @param stdClass $record Record.
     * @param string $table Table name without braces.
     * @return stdClass Filtered record.
     */
    private static function filter_to_existing_fields(stdClass $record, string $table): stdClass {
        global $DB;

        $columns = $DB->get_columns($table);
        $filtered = new stdClass();

        foreach ((array)$record as $field => $value) {
            if (array_key_exists($field, $columns)) {
                $filtered->{$field} = $value;
            }
        }

        return $filtered;
    }
}
