<?php
// This file is part of Moodle - https://moodle.org/
//
// Moodle is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// any later version.

namespace mod_uckkarchive\local;

defined('MOODLE_INTERNAL') || die();

/**
 * Metadata validation and normalization helper for UCKK Archive.
 *
 * This class validates structured metadata used by archive records, media
 * records, media versions, content advisories, content markers, external works,
 * provenance records, and export manifests.
 *
 * The class is intentionally static and dependency-light so it can be reused by:
 *
 * - external service parameter validation;
 * - forms;
 * - local domain classes;
 * - backup/restore helpers;
 * - export manifest generation;
 * - privacy provider filtering;
 * - tests.
 *
 * @package     mod_uckkarchive
 */
final class metadata_validator {

    /** Maximum JSON metadata size accepted by generic helpers. */
    public const MAX_JSON_BYTES = 1048576;

    /** Maximum nesting depth for arbitrary metadata. */
    public const MAX_DEPTH = 16;

    /** Maximum length for normalized metadata keys. */
    public const MAX_KEY_LENGTH = 64;

    /** Maximum length for tag keys. */
    public const MAX_TAG_KEY_LENGTH = 80;

    /** Maximum length for short string values. */
    public const MAX_SHORT_TEXT_LENGTH = 1024;

    /** Maximum length for long string values. */
    public const MAX_LONG_TEXT_LENGTH = 65535;

    /** @var string[] Archive item statuses. */
    public const ARCHIVE_STATUSES = [
        'draft',
        'submitted',
        'under_review',
        'validated',
        'published',
        'restricted',
        'contested',
        'invalidated',
        'superseded',
        'archived',
    ];

    /** @var string[] Media statuses. */
    public const MEDIA_STATUSES = [
        'draft',
        'submitted',
        'active',
        'restricted',
        'superseded',
        'archived',
        'deleted_soft',
    ];

    /** @var string[] Validation states. */
    public const VALIDATION_STATES = [
        'unverified',
        'human_reviewed',
        'verified',
        'contested',
        'invalidated',
        'archived',
    ];

    /** @var string[] Review states for content advisory review records. */
    public const REVIEW_STATES = [
        'draft',
        'pending_review',
        'reviewed',
        'approved',
        'contested',
        'retired',
    ];

    /** @var string[] Visibility values. */
    public const VISIBILITIES = [
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

    /** @var string[] Audience suitability values. */
    public const AUDIENCE_SUITABILITY = [
        'general',
        'guided',
        'mature',
        'restricted',
        'restricted_cultural',
        'restricted_integrity',
        'staff_only',
    ];

    /** @var string[] Content advisory severity values. */
    public const ADVISORY_SEVERITIES = [
        'notice',
        'moderate',
        'strong',
        'restricted',
    ];

    /** @var string[] Locator types for media/external work content markers. */
    public const LOCATOR_TYPES = [
        'timecode',
        'timecode_range',
        'page',
        'page_range',
        'chapter',
        'chapter_range',
        'section',
        'section_range',
        'paragraph',
        'paragraph_range',
        'scene',
        'track',
        'timestamp',
        'url_fragment',
        'manual_reference',
    ];

    /** @var string[] Media relation types. */
    public const RELATION_TYPES = [
        'belongs_to_item',
        'belongs_to_kristal',
        'belongs_to_collection',
        'is_derivative_of',
        'is_translation_of',
        'is_excerpt_of',
        'is_proof_for',
        'is_source_for',
        'replaces',
        'references',
        'duplicates',
        'references_external_work',
        'contains_content_marker',
    ];

    /** @var string[] Provenance values. */
    public const PROVENANCE_TYPES = [
        'human',
        'ai_assisted',
        'imported',
        'system',
        'archive',
        'assembly',
        'challenge',
        'integrity',
        'media',
        'external_work',
        'content_review',
    ];

    /** @var string[] Media source types. */
    public const MEDIA_SOURCE_TYPES = [
        'produced_by_uckk',
        'submitted_to_uckk',
        'imported',
        'external_reference_only',
        'licensed_external',
        'public_domain',
        'fair_use_reference',
        'restricted_reference',
    ];

    /** @var string[] Source ownership values. */
    public const SOURCE_OWNERSHIP_VALUES = [
        'uckk_created',
        'uckk_commissioned',
        'member_submitted',
        'partner_submitted',
        'external_reference',
        'third_party_copyright',
        'public_domain',
        'open_license',
        'unknown_source',
    ];

    /** @var string[] External work types. */
    public const EXTERNAL_WORK_TYPES = [
        'film',
        'book',
        'article',
        'podcast',
        'website',
        'external_video',
        'external_image',
        'public_archive_item',
        'third_party_pdf',
        'other',
    ];

    /** @var string[] Media types. */
    public const MEDIA_TYPES = [
        'image',
        'video',
        'audio',
        'document',
        'pdf',
        'transcript',
        'caption',
        'thumbnail',
        'preview',
        'derivative',
        'attachment',
        'source_package',
        'other',
    ];

    /**
     * Private constructor for static utility class.
     */
    private function __construct() {
    }

    /**
     * Decode and normalize a JSON metadata string.
     *
     * @param string|null $json JSON string, empty string, or null.
     * @param string $fieldname Field name used in error messages.
     * @param int $maxbytes Maximum accepted byte length.
     * @return array Normalized metadata array.
     */
    public static function decode_json(?string $json, string $fieldname = 'metadata',
            int $maxbytes = self::MAX_JSON_BYTES): array {
        if ($json === null || trim($json) === '') {
            return [];
        }

        if (strlen($json) > $maxbytes) {
            throw new \invalid_parameter_exception($fieldname . ' exceeds maximum size.');
        }

        $decoded = json_decode($json, true);

        if (json_last_error() !== JSON_ERROR_NONE || !is_array($decoded)) {
            throw new \invalid_parameter_exception($fieldname . ' must be a valid JSON object.');
        }

        return self::normalize_metadata($decoded);
    }

    /**
     * Encode normalized metadata as JSON.
     *
     * @param array $metadata Metadata array.
     * @return string JSON string.
     */
    public static function encode_json(array $metadata): string {
        $metadata = self::normalize_metadata($metadata);
        $json = json_encode($metadata, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);

        if ($json === false) {
            throw new \coding_exception('Unable to encode metadata as JSON.');
        }

        if (strlen($json) > self::MAX_JSON_BYTES) {
            throw new \invalid_parameter_exception('metadata exceeds maximum size.');
        }

        return $json;
    }

    /**
     * Normalize metadata recursively.
     *
     * @param mixed $value Input value.
     * @param int $depth Current recursion depth.
     * @return mixed Normalized value.
     */
    public static function normalize_value($value, int $depth = 0) {
        if ($depth > self::MAX_DEPTH) {
            throw new \invalid_parameter_exception('metadata nesting is too deep.');
        }

        if (is_array($value)) {
            $normalized = [];
            foreach ($value as $key => $child) {
                if (is_string($key)) {
                    $key = self::normalize_metadata_key($key);
                }
                $normalized[$key] = self::normalize_value($child, $depth + 1);
            }
            return $normalized;
        }

        if (is_string($value)) {
            $value = trim($value);
            if (\core_text::strlen($value) > self::MAX_LONG_TEXT_LENGTH) {
                throw new \invalid_parameter_exception('metadata text value is too long.');
            }
            return $value;
        }

        if (is_int($value) || is_float($value) || is_bool($value) || $value === null) {
            return $value;
        }

        throw new \invalid_parameter_exception('metadata contains an unsupported value type.');
    }

    /**
     * Normalize full metadata object.
     *
     * @param array $metadata Metadata object.
     * @return array Normalized metadata object.
     */
    public static function normalize_metadata(array $metadata): array {
        $normalized = self::normalize_value($metadata);

        if (!is_array($normalized)) {
            throw new \invalid_parameter_exception('metadata must be an object.');
        }

        return $normalized;
    }

    /**
     * Normalize a metadata key.
     *
     * @param string $key Metadata key.
     * @return string Normalized key.
     */
    public static function normalize_metadata_key(string $key): string {
        $key = trim($key);
        $key = strtolower($key);

        if ($key === '') {
            throw new \invalid_parameter_exception('metadata keys must not be empty.');
        }

        if (\core_text::strlen($key) > self::MAX_KEY_LENGTH) {
            throw new \invalid_parameter_exception('metadata key is too long.');
        }

        if (!preg_match('/^[a-z][a-z0-9_]*$/', $key)) {
            throw new \invalid_parameter_exception('metadata key has invalid format: ' . $key);
        }

        return $key;
    }

    /**
     * Validate that required keys exist.
     *
     * @param array $metadata Metadata object.
     * @param string[] $required Required keys.
     * @param string $fieldname Field name used in error messages.
     */
    public static function require_keys(array $metadata, array $required, string $fieldname = 'metadata'): void {
        foreach ($required as $key) {
            if (!array_key_exists($key, $metadata)) {
                throw new \invalid_parameter_exception($fieldname . ' is missing required key: ' . $key);
            }
        }
    }

    /**
     * Validate allowed keys.
     *
     * @param array $metadata Metadata object.
     * @param string[] $allowed Allowed keys.
     * @param string $fieldname Field name used in error messages.
     * @param bool $strict Whether unknown keys should fail.
     */
    public static function validate_keys(array $metadata, array $allowed, string $fieldname = 'metadata',
            bool $strict = true): void {
        if (!$strict) {
            return;
        }

        $allowedmap = array_flip($allowed);

        foreach (array_keys($metadata) as $key) {
            if (is_string($key) && !isset($allowedmap[$key])) {
                throw new \invalid_parameter_exception($fieldname . ' contains unknown key: ' . $key);
            }
        }
    }

    /**
     * Validate enum value.
     *
     * @param string|null $value Value to validate.
     * @param string[] $allowed Allowed values.
     * @param string $fieldname Field name used in error messages.
     * @param bool $required Whether value is required.
     * @return string|null Normalized value.
     */
    public static function enum(?string $value, array $allowed, string $fieldname, bool $required = false): ?string {
        if ($value === null || trim($value) === '') {
            if ($required) {
                throw new \invalid_parameter_exception($fieldname . ' is required.');
            }
            return null;
        }

        $value = strtolower(trim($value));
        $value = self::normalize_legacy_value($value, $fieldname);

        if (!in_array($value, $allowed, true)) {
            throw new \invalid_parameter_exception($fieldname . ' has invalid value: ' . $value);
        }

        return $value;
    }

    /**
     * Normalize selected legacy values.
     *
     * @param string $value Value.
     * @param string $fieldname Field name.
     * @return string Normalized value.
     */
    private static function normalize_legacy_value(string $value, string $fieldname): string {
        if ($fieldname === 'visibility' && $value === 'institutional') {
            return 'institution';
        }

        return $value;
    }

    /**
     * Validate visibility.
     *
     * @param string|null $value Visibility value.
     * @param bool $required Whether required.
     * @return string|null
     */
    public static function visibility(?string $value, bool $required = false): ?string {
        return self::enum($value, self::VISIBILITIES, 'visibility', $required);
    }

    /**
     * Validate archive item status.
     *
     * @param string|null $value Status value.
     * @param bool $required Whether required.
     * @return string|null
     */
    public static function archive_status(?string $value, bool $required = false): ?string {
        return self::enum($value, self::ARCHIVE_STATUSES, 'status', $required);
    }

    /**
     * Validate media status.
     *
     * @param string|null $value Status value.
     * @param bool $required Whether required.
     * @return string|null
     */
    public static function media_status(?string $value, bool $required = false): ?string {
        return self::enum($value, self::MEDIA_STATUSES, 'status', $required);
    }

    /**
     * Validate validation state.
     *
     * @param string|null $value Validation state.
     * @param bool $required Whether required.
     * @return string|null
     */
    public static function validation_state(?string $value, bool $required = false): ?string {
        return self::enum($value, self::VALIDATION_STATES, 'validationstate', $required);
    }

    /**
     * Validate content review state.
     *
     * @param string|null $value Review state.
     * @param bool $required Whether required.
     * @return string|null
     */
    public static function review_state(?string $value, bool $required = false): ?string {
        return self::enum($value, self::REVIEW_STATES, 'reviewstate', $required);
    }

    /**
     * Validate audience suitability.
     *
     * @param string|null $value Suitability value.
     * @param bool $required Whether required.
     * @return string|null
     */
    public static function audience_suitability(?string $value, bool $required = false): ?string {
        return self::enum($value, self::AUDIENCE_SUITABILITY, 'audiencesuitability', $required);
    }

    /**
     * Validate advisory severity.
     *
     * @param string|null $value Severity value.
     * @param bool $required Whether required.
     * @return string|null
     */
    public static function advisory_severity(?string $value, bool $required = false): ?string {
        return self::enum($value, self::ADVISORY_SEVERITIES, 'severity', $required);
    }

    /**
     * Validate locator type.
     *
     * @param string|null $value Locator type.
     * @param bool $required Whether required.
     * @return string|null
     */
    public static function locator_type(?string $value, bool $required = false): ?string {
        return self::enum($value, self::LOCATOR_TYPES, 'locatortype', $required);
    }

    /**
     * Validate media relation type.
     *
     * @param string|null $value Relation type.
     * @param bool $required Whether required.
     * @return string|null
     */
    public static function relation_type(?string $value, bool $required = false): ?string {
        return self::enum($value, self::RELATION_TYPES, 'relationtype', $required);
    }

    /**
     * Validate provenance type.
     *
     * @param string|null $value Provenance type.
     * @param bool $required Whether required.
     * @return string|null
     */
    public static function provenance_type(?string $value, bool $required = false): ?string {
        return self::enum($value, self::PROVENANCE_TYPES, 'provenance', $required);
    }

    /**
     * Validate media source type.
     *
     * @param string|null $value Source type.
     * @param bool $required Whether required.
     * @return string|null
     */
    public static function media_source_type(?string $value, bool $required = false): ?string {
        return self::enum($value, self::MEDIA_SOURCE_TYPES, 'sourcetype', $required);
    }

    /**
     * Validate source ownership value.
     *
     * @param string|null $value Source ownership value.
     * @param bool $required Whether required.
     * @return string|null
     */
    public static function source_ownership(?string $value, bool $required = false): ?string {
        return self::enum($value, self::SOURCE_OWNERSHIP_VALUES, 'sourceownership', $required);
    }

    /**
     * Validate external work type.
     *
     * @param string|null $value External work type.
     * @param bool $required Whether required.
     * @return string|null
     */
    public static function external_work_type(?string $value, bool $required = false): ?string {
        return self::enum($value, self::EXTERNAL_WORK_TYPES, 'worktype', $required);
    }

    /**
     * Validate media type.
     *
     * @param string|null $value Media type.
     * @param bool $required Whether required.
     * @return string|null
     */
    public static function media_type(?string $value, bool $required = false): ?string {
        return self::enum($value, self::MEDIA_TYPES, 'mediatype', $required);
    }

    /**
     * Normalize and validate tag key.
     *
     * @param string $tagkey Tag key.
     * @param string $fieldname Field name used in error messages.
     * @return string Normalized tag key.
     */
    public static function tag_key(string $tagkey, string $fieldname = 'tagkey'): string {
        $tagkey = strtolower(trim($tagkey));
        $tagkey = preg_replace('/[\s\-]+/', '_', $tagkey);

        if ($tagkey === '') {
            throw new \invalid_parameter_exception($fieldname . ' is required.');
        }

        if (\core_text::strlen($tagkey) > self::MAX_TAG_KEY_LENGTH) {
            throw new \invalid_parameter_exception($fieldname . ' is too long.');
        }

        if (!preg_match('/^[a-z][a-z0-9_]*$/', $tagkey)) {
            throw new \invalid_parameter_exception($fieldname . ' has invalid format: ' . $tagkey);
        }

        return $tagkey;
    }

    /**
     * Validate UUID.
     *
     * @param string|null $uuid UUID.
     * @param string $fieldname Field name used in error messages.
     * @param bool $required Whether required.
     * @return string|null Normalized UUID.
     */
    public static function uuid(?string $uuid, string $fieldname = 'uuid', bool $required = false): ?string {
        if ($uuid === null || trim($uuid) === '') {
            if ($required) {
                throw new \invalid_parameter_exception($fieldname . ' is required.');
            }
            return null;
        }

        $uuid = strtolower(trim($uuid));

        if (!preg_match('/^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/', $uuid)) {
            throw new \invalid_parameter_exception($fieldname . ' must be a valid UUID.');
        }

        return $uuid;
    }

    /**
     * Validate a content locator.
     *
     * @param array $locator Locator data.
     * @return array Normalized locator data.
     */
    public static function locator(array $locator): array {
        $locator = self::normalize_metadata($locator);

        self::require_keys($locator, ['type'], 'locator');
        self::validate_keys($locator, [
            'type',
            'value',
            'start',
            'end',
            'label',
            'note',
        ], 'locator', false);

        $locator['type'] = self::locator_type((string)$locator['type'], true);

        foreach (['value', 'start', 'end', 'label', 'note'] as $key) {
            if (array_key_exists($key, $locator) && $locator[$key] !== null) {
                if (!is_scalar($locator[$key])) {
                    throw new \invalid_parameter_exception('locator.' . $key . ' must be scalar.');
                }
                $locator[$key] = self::short_text((string)$locator[$key], 'locator.' . $key, false);
            }
        }

        if (!array_key_exists('value', $locator)
                && !array_key_exists('start', $locator)
                && !array_key_exists('end', $locator)) {
            throw new \invalid_parameter_exception('locator must include value, start, or end.');
        }

        return $locator;
    }

    /**
     * Validate a short text field.
     *
     * @param string|null $value Value.
     * @param string $fieldname Field name.
     * @param bool $required Whether required.
     * @return string|null Normalized value.
     */
    public static function short_text(?string $value, string $fieldname, bool $required = false): ?string {
        if ($value === null || trim($value) === '') {
            if ($required) {
                throw new \invalid_parameter_exception($fieldname . ' is required.');
            }
            return null;
        }

        $value = trim($value);

        if (\core_text::strlen($value) > self::MAX_SHORT_TEXT_LENGTH) {
            throw new \invalid_parameter_exception($fieldname . ' is too long.');
        }

        return $value;
    }

    /**
     * Validate a long text field.
     *
     * @param string|null $value Value.
     * @param string $fieldname Field name.
     * @param bool $required Whether required.
     * @return string|null Normalized value.
     */
    public static function long_text(?string $value, string $fieldname, bool $required = false): ?string {
        if ($value === null || trim($value) === '') {
            if ($required) {
                throw new \invalid_parameter_exception($fieldname . ' is required.');
            }
            return null;
        }

        $value = trim($value);

        if (\core_text::strlen($value) > self::MAX_LONG_TEXT_LENGTH) {
            throw new \invalid_parameter_exception($fieldname . ' is too long.');
        }

        return $value;
    }

    /**
     * Validate media metadata object.
     *
     * @param array $metadata Metadata.
     * @return array Normalized metadata.
     */
    public static function media_metadata(array $metadata): array {
        $metadata = self::normalize_metadata($metadata);

        $allowed = [
            'title',
            'description',
            'mediatype',
            'mimetype',
            'duration',
            'width',
            'height',
            'pages',
            'language',
            'license',
            'rightsnote',
            'source',
            'technical',
            'ai_assisted',
            'audiencesuitability',
            'visibility',
            'tags',
        ];

        self::validate_keys($metadata, $allowed, 'media metadata', false);

        if (isset($metadata['mediatype'])) {
            $metadata['mediatype'] = self::media_type((string)$metadata['mediatype'], true);
        }

        if (isset($metadata['visibility'])) {
            $metadata['visibility'] = self::visibility((string)$metadata['visibility'], true);
        }

        if (isset($metadata['audiencesuitability'])) {
            $metadata['audiencesuitability'] =
                self::audience_suitability((string)$metadata['audiencesuitability'], true);
        }

        if (isset($metadata['tags']) && is_array($metadata['tags'])) {
            $metadata['tags'] = self::tag_list($metadata['tags']);
        }

        return $metadata;
    }

    /**
     * Validate content marker metadata object.
     *
     * @param array $metadata Metadata.
     * @return array Normalized metadata.
     */
    public static function content_marker_metadata(array $metadata): array {
        $metadata = self::normalize_metadata($metadata);

        $allowed = [
            'tagkey',
            'tagsetkey',
            'severity',
            'audiencesuitability',
            'visibility',
            'reviewstate',
            'locator',
            'note',
            'teachingnote',
            'culturalprotocolnote',
            'requirescontext',
        ];

        self::validate_keys($metadata, $allowed, 'content marker metadata', false);

        if (isset($metadata['tagkey'])) {
            $metadata['tagkey'] = self::tag_key((string)$metadata['tagkey']);
        }

        if (isset($metadata['tagsetkey'])) {
            $metadata['tagsetkey'] = self::tag_key((string)$metadata['tagsetkey'], 'tagsetkey');
        }

        if (isset($metadata['severity'])) {
            $metadata['severity'] = self::advisory_severity((string)$metadata['severity'], true);
        }

        if (isset($metadata['audiencesuitability'])) {
            $metadata['audiencesuitability'] =
                self::audience_suitability((string)$metadata['audiencesuitability'], true);
        }

        if (isset($metadata['visibility'])) {
            $metadata['visibility'] = self::visibility((string)$metadata['visibility'], true);
        }

        if (isset($metadata['reviewstate'])) {
            $metadata['reviewstate'] = self::review_state((string)$metadata['reviewstate'], true);
        }

        if (isset($metadata['locator'])) {
            if (!is_array($metadata['locator'])) {
                throw new \invalid_parameter_exception('locator must be an object.');
            }
            $metadata['locator'] = self::locator($metadata['locator']);
        }

        return $metadata;
    }

    /**
     * Validate external work metadata object.
     *
     * @param array $metadata Metadata.
     * @return array Normalized metadata.
     */
    public static function external_work_metadata(array $metadata): array {
        $metadata = self::normalize_metadata($metadata);

        $allowed = [
            'worktype',
            'title',
            'creator',
            'year',
            'publisher',
            'sourceurl',
            'identifier',
            'citation',
            'rightsnote',
            'visibility',
            'audiencesuitability',
            'tags',
        ];

        self::validate_keys($metadata, $allowed, 'external work metadata', false);

        if (isset($metadata['worktype'])) {
            $metadata['worktype'] = self::external_work_type((string)$metadata['worktype'], true);
        }

        if (isset($metadata['visibility'])) {
            $metadata['visibility'] = self::visibility((string)$metadata['visibility'], true);
        }

        if (isset($metadata['audiencesuitability'])) {
            $metadata['audiencesuitability'] =
                self::audience_suitability((string)$metadata['audiencesuitability'], true);
        }

        if (isset($metadata['tags']) && is_array($metadata['tags'])) {
            $metadata['tags'] = self::tag_list($metadata['tags']);
        }

        return $metadata;
    }

    /**
     * Validate media source metadata object.
     *
     * @param array $metadata Metadata.
     * @return array Normalized metadata.
     */
    public static function media_source_metadata(array $metadata): array {
        $metadata = self::normalize_metadata($metadata);

        $allowed = [
            'sourcetype',
            'sourceownership',
            'creator',
            'owner',
            'license',
            'rightsnote',
            'citation',
            'url',
            'identifier',
            'provenance',
        ];

        self::validate_keys($metadata, $allowed, 'media source metadata', false);

        if (isset($metadata['sourcetype'])) {
            $metadata['sourcetype'] = self::media_source_type((string)$metadata['sourcetype'], true);
        }

        if (isset($metadata['sourceownership'])) {
            $metadata['sourceownership'] = self::source_ownership((string)$metadata['sourceownership'], true);
        }

        if (isset($metadata['provenance'])) {
            $metadata['provenance'] = self::provenance_type((string)$metadata['provenance'], true);
        }

        return $metadata;
    }

    /**
     * Validate export manifest metadata object.
     *
     * @param array $metadata Metadata.
     * @return array Normalized metadata.
     */
    public static function manifest_metadata(array $metadata): array {
        $metadata = self::normalize_metadata($metadata);

        foreach (['mediauuids', 'mediaversionuuids', 'externalworkuuids', 'contentmarkeruuids'] as $key) {
            if (isset($metadata[$key]) && is_array($metadata[$key])) {
                $metadata[$key] = self::uuid_list($metadata[$key], $key);
            }
        }

        if (isset($metadata['visibility'])) {
            $metadata['visibility'] = self::visibility((string)$metadata['visibility'], true);
        }

        if (isset($metadata['audiencesuitability'])) {
            $metadata['audiencesuitability'] =
                self::audience_suitability((string)$metadata['audiencesuitability'], true);
        }

        return $metadata;
    }

    /**
     * Normalize list of tag keys.
     *
     * @param array $tags Tags.
     * @return string[] Normalized unique tag keys.
     */
    public static function tag_list(array $tags): array {
        $normalized = [];

        foreach ($tags as $tag) {
            if (!is_scalar($tag)) {
                throw new \invalid_parameter_exception('tag list values must be scalar.');
            }

            $tag = self::tag_key((string)$tag);
            $normalized[$tag] = $tag;
        }

        return array_values($normalized);
    }

    /**
     * Normalize list of UUIDs.
     *
     * @param array $uuids UUIDs.
     * @param string $fieldname Field name.
     * @return string[] Normalized unique UUIDs.
     */
    public static function uuid_list(array $uuids, string $fieldname = 'uuids'): array {
        $normalized = [];

        foreach ($uuids as $uuid) {
            if (!is_scalar($uuid)) {
                throw new \invalid_parameter_exception($fieldname . ' values must be scalar.');
            }

            $uuid = self::uuid((string)$uuid, $fieldname, true);
            $normalized[$uuid] = $uuid;
        }

        return array_values($normalized);
    }

    /**
     * Validate a Moodle database id.
     *
     * @param mixed $value Value.
     * @param string $fieldname Field name.
     * @param bool $required Whether required.
     * @return int|null Positive integer id or null.
     */
    public static function id($value, string $fieldname = 'id', bool $required = false): ?int {
        if ($value === null || $value === '') {
            if ($required) {
                throw new \invalid_parameter_exception($fieldname . ' is required.');
            }
            return null;
        }

        if (!is_numeric($value) || (int)$value < 1) {
            throw new \invalid_parameter_exception($fieldname . ' must be a positive integer.');
        }

        return (int)$value;
    }

    /**
     * Ensure metadata is safe for storage in JSON fields.
     *
     * @param array|string|null $metadata Metadata array or JSON string.
     * @param string $fieldname Field name.
     * @return array Normalized metadata array.
     */
    public static function ensure_array($metadata, string $fieldname = 'metadata'): array {
        if ($metadata === null || $metadata === '') {
            return [];
        }

        if (is_string($metadata)) {
            return self::decode_json($metadata, $fieldname);
        }

        if (is_array($metadata)) {
            return self::normalize_metadata($metadata);
        }

        throw new \invalid_parameter_exception($fieldname . ' must be an object or JSON object string.');
    }

    /**
     * Return whether an array is associative.
     *
     * @param array $value Value.
     * @return bool
     */
    public static function is_assoc(array $value): bool {
        if ($value === []) {
            return true;
        }

        return array_keys($value) !== range(0, count($value) - 1);
    }
}
