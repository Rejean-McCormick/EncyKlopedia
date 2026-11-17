<?php
// This file is part of Moodle - https://moodle.org/
//
// Moodle is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// any later version.

/**
 * Media tag domain service for the UCKK Archive activity module.
 *
 * @package    mod_uckkarchive
 * @copyright  2026 Univers-Cité King Klown
 * @license    https://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later
 */

namespace mod_uckkarchive\local;

use core_text;
use dml_exception;
use invalid_parameter_exception;
use moodle_exception;
use stdClass;

defined('MOODLE_INTERNAL') || die();

/**
 * Manages ordinary media-library tags.
 *
 * Media tags describe normal media classification such as topic, format,
 * language, course use, pedagogical theme, source category, or search labels.
 *
 * Content advisories and cultural protocol tags are intentionally not stored
 * here. They belong to:
 *
 * - uckkarchive_content_tag
 * - uckkarchive_content_tag_set
 * - uckkarchive_content_marker
 * - uckkarchive_content_review
 *
 * This class does not decide access. Access is owned by media_policy and
 * content_policy. This class only validates and persists ordinary media tags.
 */
class media_tag {
    /** @var string Database table for media tags. */
    public const TABLE = 'uckkarchive_media_tag';

    /** @var int Maximum normalized tag key length. */
    public const MAX_KEY_LENGTH = 100;

    /** @var int Maximum label length. */
    public const MAX_LABEL_LENGTH = 255;

    /** @var string Tag type: topic. */
    public const TYPE_TOPIC = 'topic';

    /** @var string Tag type: format. */
    public const TYPE_FORMAT = 'format';

    /** @var string Tag type: course use. */
    public const TYPE_COURSE_USE = 'course_use';

    /** @var string Tag type: language. */
    public const TYPE_LANGUAGE = 'language';

    /** @var string Tag type: region. */
    public const TYPE_REGION = 'region';

    /** @var string Tag type: pedagogical theme. */
    public const TYPE_PEDAGOGICAL_THEME = 'pedagogical_theme';

    /** @var string Tag type: source category. */
    public const TYPE_SOURCE_CATEGORY = 'source_category';

    /** @var string Tag type: review state. */
    public const TYPE_REVIEW_STATE = 'review_state';

    /** @var string Tag source: human. */
    public const SOURCE_HUMAN = 'human';

    /** @var string Tag source: imported. */
    public const SOURCE_IMPORTED = 'imported';

    /** @var string Tag source: system. */
    public const SOURCE_SYSTEM = 'system';

    /** @var string Tag source: ai suggestion. */
    public const SOURCE_AI_SUGGESTED = 'ai_suggested';

    /**
     * Return valid media tag types.
     *
     * @return string[]
     */
    public static function valid_types(): array {
        return [
            self::TYPE_TOPIC,
            self::TYPE_FORMAT,
            self::TYPE_COURSE_USE,
            self::TYPE_LANGUAGE,
            self::TYPE_REGION,
            self::TYPE_PEDAGOGICAL_THEME,
            self::TYPE_SOURCE_CATEGORY,
            self::TYPE_REVIEW_STATE,
        ];
    }

    /**
     * Return valid media tag sources.
     *
     * @return string[]
     */
    public static function valid_sources(): array {
        return [
            self::SOURCE_HUMAN,
            self::SOURCE_IMPORTED,
            self::SOURCE_SYSTEM,
            self::SOURCE_AI_SUGGESTED,
        ];
    }

    /**
     * Create a media tag.
     *
     * The tag key is unique per media object and tag type.
     *
     * @param int $mediaid Media id.
     * @param string $tagkey Tag key or label.
     * @param array $options Optional fields.
     * @return stdClass Created tag record.
     * @throws dml_exception
     * @throws invalid_parameter_exception
     */
    public static function create(int $mediaid, string $tagkey, array $options = []): stdClass {
        global $DB, $USER;

        self::require_positive_id($mediaid, 'mediaid');

        $key = self::normalise_key($tagkey);
        self::validate_key($key);

        $type = self::normalise_type($options['tagtype'] ?? self::TYPE_TOPIC);
        $source = self::normalise_source($options['source'] ?? self::SOURCE_HUMAN);

        if (self::exists($mediaid, $key, $type)) {
            throw new invalid_parameter_exception('Duplicate media tag for media object: ' . $key);
        }

        $now = time();

        $record = (object)[
            'uuid' => $options['uuid'] ?? self::generate_uuid(),
            'mediaid' => $mediaid,
            'tagkey' => $key,
            'label' => self::normalise_label($options['label'] ?? $tagkey),
            'tagtype' => $type,
            'source' => $source,
            'userid' => (int)($options['userid'] ?? $USER->id ?? 0),
            'weight' => (int)($options['weight'] ?? 0),
            'metadata' => self::encode_metadata($options['metadata'] ?? []),
            'timecreated' => $now,
            'timemodified' => $now,
        ];

        $record->id = $DB->insert_record(self::TABLE, $record);

        return self::get($record->id);
    }

    /**
     * Create the tag if it does not exist, otherwise update metadata/label/source.
     *
     * @param int $mediaid Media id.
     * @param string $tagkey Tag key or label.
     * @param array $options Optional fields.
     * @return stdClass Tag record.
     * @throws dml_exception
     * @throws invalid_parameter_exception
     */
    public static function add_or_update(int $mediaid, string $tagkey, array $options = []): stdClass {
        global $DB, $USER;

        self::require_positive_id($mediaid, 'mediaid');

        $key = self::normalise_key($tagkey);
        self::validate_key($key);

        $type = self::normalise_type($options['tagtype'] ?? self::TYPE_TOPIC);
        $existing = $DB->get_record(self::TABLE, [
            'mediaid' => $mediaid,
            'tagkey' => $key,
            'tagtype' => $type,
        ]);

        if (!$existing) {
            return self::create($mediaid, $key, $options + ['label' => $tagkey, 'tagtype' => $type]);
        }

        $updates = [
            'label' => $options['label'] ?? $existing->label,
            'source' => $options['source'] ?? $existing->source,
            'weight' => $options['weight'] ?? $existing->weight,
            'metadata' => $options['metadata'] ?? self::decode_metadata($existing->metadata ?? ''),
            'userid' => $options['userid'] ?? ($USER->id ?? $existing->userid ?? 0),
        ];

        return self::update((int)$existing->id, $updates);
    }

    /**
     * Update a media tag.
     *
     * @param int $tagid Tag id.
     * @param array $fields Fields to update.
     * @return stdClass Updated tag record.
     * @throws dml_exception
     * @throws invalid_parameter_exception
     */
    public static function update(int $tagid, array $fields): stdClass {
        global $DB;

        self::require_positive_id($tagid, 'tagid');

        $record = self::get($tagid);

        if (array_key_exists('tagkey', $fields)) {
            $record->tagkey = self::normalise_key((string)$fields['tagkey']);
            self::validate_key($record->tagkey);
        }

        if (array_key_exists('label', $fields)) {
            $record->label = self::normalise_label((string)$fields['label']);
        }

        if (array_key_exists('tagtype', $fields)) {
            $record->tagtype = self::normalise_type((string)$fields['tagtype']);
        }

        if (array_key_exists('source', $fields)) {
            $record->source = self::normalise_source((string)$fields['source']);
        }

        if (array_key_exists('weight', $fields)) {
            $record->weight = (int)$fields['weight'];
        }

        if (array_key_exists('userid', $fields)) {
            $record->userid = (int)$fields['userid'];
        }

        if (array_key_exists('metadata', $fields)) {
            $record->metadata = self::encode_metadata($fields['metadata']);
        }

        if (self::duplicate_exists((int)$record->id, (int)$record->mediaid, $record->tagkey, $record->tagtype)) {
            throw new invalid_parameter_exception('Duplicate media tag for media object: ' . $record->tagkey);
        }

        $record->timemodified = time();

        $DB->update_record(self::TABLE, $record);

        return self::get($tagid);
    }

    /**
     * Delete a media tag.
     *
     * @param int $tagid Tag id.
     * @return bool
     * @throws dml_exception
     */
    public static function delete(int $tagid): bool {
        global $DB;

        self::require_positive_id($tagid, 'tagid');

        return $DB->delete_records(self::TABLE, ['id' => $tagid]);
    }

    /**
     * Delete all tags for a media object.
     *
     * @param int $mediaid Media id.
     * @return bool
     * @throws dml_exception
     */
    public static function delete_for_media(int $mediaid): bool {
        global $DB;

        self::require_positive_id($mediaid, 'mediaid');

        return $DB->delete_records(self::TABLE, ['mediaid' => $mediaid]);
    }

    /**
     * Get a media tag.
     *
     * @param int $tagid Tag id.
     * @return stdClass
     * @throws dml_exception
     * @throws moodle_exception
     */
    public static function get(int $tagid): stdClass {
        global $DB;

        self::require_positive_id($tagid, 'tagid');

        $record = $DB->get_record(self::TABLE, ['id' => $tagid], '*', MUST_EXIST);
        self::normalise_record($record);

        return $record;
    }

    /**
     * List media tags for a media object.
     *
     * @param int $mediaid Media id.
     * @param array $filters Optional filters: tagtype, source, q.
     * @return stdClass[]
     * @throws dml_exception
     */
    public static function list_for_media(int $mediaid, array $filters = []): array {
        global $DB;

        self::require_positive_id($mediaid, 'mediaid');

        $conditions = ['mediaid' => $mediaid];
        $where = ['mediaid = :mediaid'];
        $params = $conditions;

        if (!empty($filters['tagtype'])) {
            $params['tagtype'] = self::normalise_type((string)$filters['tagtype']);
            $where[] = 'tagtype = :tagtype';
        }

        if (!empty($filters['source'])) {
            $params['source'] = self::normalise_source((string)$filters['source']);
            $where[] = 'source = :source';
        }

        if (!empty($filters['q'])) {
            $params['q'] = '%' . $DB->sql_like_escape((string)$filters['q']) . '%';
            $where[] = $DB->sql_like('label', ':q', false) . ' OR ' . $DB->sql_like('tagkey', ':q', false);
        }

        $sql = 'SELECT *
                  FROM {' . self::TABLE . '}
                 WHERE ' . implode(' AND ', array_map(static function(string $clause): string {
                    return str_contains($clause, ' OR ') ? '(' . $clause . ')' : $clause;
                 }, $where)) . '
              ORDER BY weight DESC, tagtype ASC, label ASC, tagkey ASC';

        $records = $DB->get_records_sql($sql, $params);

        foreach ($records as $record) {
            self::normalise_record($record);
        }

        return array_values($records);
    }

    /**
     * List tags by normalized key.
     *
     * @param string $tagkey Tag key.
     * @param string|null $tagtype Optional tag type.
     * @return stdClass[]
     * @throws dml_exception
     */
    public static function list_by_key(string $tagkey, ?string $tagtype = null): array {
        global $DB;

        $key = self::normalise_key($tagkey);
        self::validate_key($key);

        $conditions = ['tagkey' => $key];

        if ($tagtype !== null) {
            $conditions['tagtype'] = self::normalise_type($tagtype);
        }

        $records = $DB->get_records(self::TABLE, $conditions, 'mediaid ASC, label ASC');

        foreach ($records as $record) {
            self::normalise_record($record);
        }

        return array_values($records);
    }

    /**
     * Return whether a tag exists for a media object.
     *
     * @param int $mediaid Media id.
     * @param string $tagkey Tag key.
     * @param string $tagtype Tag type.
     * @return bool
     * @throws dml_exception
     */
    public static function exists(int $mediaid, string $tagkey, string $tagtype = self::TYPE_TOPIC): bool {
        global $DB;

        self::require_positive_id($mediaid, 'mediaid');

        return $DB->record_exists(self::TABLE, [
            'mediaid' => $mediaid,
            'tagkey' => self::normalise_key($tagkey),
            'tagtype' => self::normalise_type($tagtype),
        ]);
    }

    /**
     * Convert a list of tag records to export-safe arrays.
     *
     * @param stdClass[] $tags Tag records.
     * @param bool $includeprivate Whether metadata should be included.
     * @return array
     */
    public static function export_list(array $tags, bool $includeprivate = false): array {
        $export = [];

        foreach ($tags as $tag) {
            self::normalise_record($tag);

            $row = [
                'id' => (int)$tag->id,
                'uuid' => (string)($tag->uuid ?? ''),
                'mediaid' => (int)$tag->mediaid,
                'tagkey' => (string)$tag->tagkey,
                'label' => (string)$tag->label,
                'tagtype' => (string)$tag->tagtype,
                'source' => (string)$tag->source,
                'weight' => (int)($tag->weight ?? 0),
                'userid' => (int)($tag->userid ?? 0),
                'timecreated' => (int)($tag->timecreated ?? 0),
                'timemodified' => (int)($tag->timemodified ?? 0),
            ];

            if ($includeprivate) {
                $row['metadata'] = self::decode_metadata($tag->metadata ?? '');
            }

            $export[] = $row;
        }

        return $export;
    }

    /**
     * Normalize tag key.
     *
     * @param string $value Input tag.
     * @return string
     */
    public static function normalise_key(string $value): string {
        $value = trim($value);
        $value = core_text::strtolower($value);
        $value = preg_replace('/[^\p{L}\p{N}_-]+/u', '_', $value) ?? '';
        $value = preg_replace('/_+/', '_', $value) ?? '';
        $value = trim($value, '_-');

        return substr($value, 0, self::MAX_KEY_LENGTH);
    }

    /**
     * Validate a normalized key.
     *
     * @param string $key Normalized key.
     * @throws invalid_parameter_exception
     */
    public static function validate_key(string $key): void {
        if ($key === '') {
            throw new invalid_parameter_exception('Media tag key cannot be empty.');
        }

        if (strlen($key) > self::MAX_KEY_LENGTH) {
            throw new invalid_parameter_exception('Media tag key is too long.');
        }

        if (!preg_match('/^[\p{L}\p{N}][\p{L}\p{N}_-]*$/u', $key)) {
            throw new invalid_parameter_exception('Invalid media tag key.');
        }

        if (self::is_content_advisory_key($key)) {
            throw new invalid_parameter_exception(
                'Content advisory and cultural protocol tags must use the content advisory subsystem.'
            );
        }
    }

    /**
     * Normalize label.
     *
     * @param string $label Label.
     * @return string
     */
    public static function normalise_label(string $label): string {
        $label = trim($label);

        if ($label === '') {
            return '';
        }

        return core_text::substr($label, 0, self::MAX_LABEL_LENGTH);
    }

    /**
     * Return whether a key belongs to content advisory vocabulary.
     *
     * These tags are blocked from ordinary media tags so that suitability,
     * restriction, and cultural protocol policy remains in content_policy.
     *
     * @param string $key Normalized key.
     * @return bool
     */
    public static function is_content_advisory_key(string $key): bool {
        static $reserved = [
            'sexual_violence',
            'violence',
            'racism',
            'colonial_violence',
            'death',
            'self_harm',
            'substance_use',
            'nudity',
            'explicit_language',
            'culturally_sensitive',
            'sacred_content',
            'ceremonial_content',
            'restricted_knowledge',
            'grief_or_mourning',
            'requires_context',
            'not_for_children',
            'community_permission_required',
            'elder_review_required',
            'seasonal_or_contextual_access',
            'not_for_public_export',
        ];

        return in_array($key, $reserved, true);
    }

    /**
     * Normalize tag type.
     *
     * @param string $type Tag type.
     * @return string
     * @throws invalid_parameter_exception
     */
    public static function normalise_type(string $type): string {
        $type = self::normalise_key($type);

        if (!in_array($type, self::valid_types(), true)) {
            throw new invalid_parameter_exception('Invalid media tag type: ' . $type);
        }

        return $type;
    }

    /**
     * Normalize tag source.
     *
     * @param string $source Source value.
     * @return string
     * @throws invalid_parameter_exception
     */
    public static function normalise_source(string $source): string {
        $source = self::normalise_key($source);

        if (!in_array($source, self::valid_sources(), true)) {
            throw new invalid_parameter_exception('Invalid media tag source: ' . $source);
        }

        return $source;
    }

    /**
     * Decode metadata JSON.
     *
     * @param mixed $metadata Metadata.
     * @return array
     */
    public static function decode_metadata($metadata): array {
        if ($metadata === null || $metadata === '') {
            return [];
        }

        if (is_array($metadata)) {
            return $metadata;
        }

        if ($metadata instanceof stdClass) {
            return (array)$metadata;
        }

        if (is_string($metadata)) {
            $decoded = json_decode($metadata, true);
            return is_array($decoded) ? $decoded : ['value' => $metadata];
        }

        if (is_scalar($metadata)) {
            return ['value' => $metadata];
        }

        return [];
    }

    /**
     * Encode metadata as JSON.
     *
     * @param mixed $metadata Metadata.
     * @return string
     */
    public static function encode_metadata($metadata): string {
        $metadata = self::decode_metadata($metadata);

        return json_encode($metadata, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
    }

    /**
     * Normalize a record in-place.
     *
     * @param stdClass $record Tag record.
     */
    protected static function normalise_record(stdClass $record): void {
        $record->id = (int)($record->id ?? 0);
        $record->mediaid = (int)($record->mediaid ?? 0);
        $record->tagkey = (string)($record->tagkey ?? '');
        $record->label = (string)($record->label ?? '');
        $record->tagtype = (string)($record->tagtype ?? self::TYPE_TOPIC);
        $record->source = (string)($record->source ?? self::SOURCE_HUMAN);
        $record->userid = (int)($record->userid ?? 0);
        $record->weight = (int)($record->weight ?? 0);
        $record->timecreated = (int)($record->timecreated ?? 0);
        $record->timemodified = (int)($record->timemodified ?? 0);

        if (!property_exists($record, 'uuid') || empty($record->uuid)) {
            $record->uuid = '';
        }

        if (!property_exists($record, 'metadata')) {
            $record->metadata = '';
        }
    }

    /**
     * Return whether another row already uses the same media/key/type.
     *
     * @param int $tagid Current tag id.
     * @param int $mediaid Media id.
     * @param string $tagkey Tag key.
     * @param string $tagtype Tag type.
     * @return bool
     * @throws dml_exception
     */
    protected static function duplicate_exists(int $tagid, int $mediaid, string $tagkey, string $tagtype): bool {
        global $DB;

        $sql = 'SELECT id
                  FROM {' . self::TABLE . '}
                 WHERE mediaid = :mediaid
                   AND tagkey = :tagkey
                   AND tagtype = :tagtype
                   AND id <> :tagid';

        return $DB->record_exists_sql($sql, [
            'mediaid' => $mediaid,
            'tagkey' => $tagkey,
            'tagtype' => $tagtype,
            'tagid' => $tagid,
        ]);
    }

    /**
     * Require a positive id.
     *
     * @param int $id Id.
     * @param string $name Parameter name.
     * @throws invalid_parameter_exception
     */
    protected static function require_positive_id(int $id, string $name): void {
        if ($id <= 0) {
            throw new invalid_parameter_exception($name . ' must be a positive integer.');
        }
    }

    /**
     * Generate a UUID.
     *
     * @return string
     */
    protected static function generate_uuid(): string {
        if (class_exists('\\mod_uckkarchive\\local\\uuid')) {
            return uuid::generate();
        }

        if (function_exists('random_bytes')) {
            $bytes = random_bytes(16);
            $bytes[6] = chr((ord($bytes[6]) & 0x0f) | 0x40);
            $bytes[8] = chr((ord($bytes[8]) & 0x3f) | 0x80);

            return vsprintf('%s%s-%s-%s-%s-%s%s%s', str_split(bin2hex($bytes), 4));
        }

        return uniqid('uckkarchive-', true);
    }
}
