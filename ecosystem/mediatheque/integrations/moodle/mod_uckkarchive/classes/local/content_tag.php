<?php
// This file is part of Moodle - https://moodle.org/
//
// Moodle is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// any later version.

/**
 * Content advisory tag domain helper for UCKK Archive.
 *
 * @package    mod_uckkarchive
 * @copyright  2026 Univers-Cité King Klown
 * @license    https://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later
 */

declare(strict_types=1);

namespace mod_uckkarchive\local;

use coding_exception;
use core_text;
use context;
use dml_exception;
use invalid_parameter_exception;
use moodle_exception;
use stdClass;

defined('MOODLE_INTERNAL') || die();

/**
 * Domain helper for content advisory and cultural protocol tags.
 *
 * Content tags are reusable vocabulary records used by content markers,
 * content reviews, external works, media records, and advisory panels.
 *
 * This class owns tag creation, validation, seed data, and safe retrieval.
 * It does not decide final access to media or archive records. Access and
 * restriction decisions belong in content_policy.php and media_policy.php.
 */
final class content_tag {
    /** Database table name without prefix. */
    public const TABLE = 'uckkarchive_content_tag';

    /** Metadata table field. */
    public const FIELD_METADATA = 'metadata';

    /** Tag category: general advisory. */
    public const CATEGORY_GENERAL = 'general_advisory';

    /** Tag category: cultural protocol. */
    public const CATEGORY_CULTURAL = 'cultural_protocol';

    /** Tag category: classroom suitability. */
    public const CATEGORY_CLASSROOM = 'classroom_suitability';

    /** Tag category: integrity-sensitive. */
    public const CATEGORY_INTEGRITY = 'integrity_sensitive';

    /** Tag category: youth access. */
    public const CATEGORY_YOUTH = 'youth_access';

    /** Tag category: source/rights advisory. */
    public const CATEGORY_SOURCE = 'source_rights';

    /** Severity: notice. */
    public const SEVERITY_NOTICE = 'notice';

    /** Severity: moderate. */
    public const SEVERITY_MODERATE = 'moderate';

    /** Severity: strong. */
    public const SEVERITY_STRONG = 'strong';

    /** Severity: restricted. */
    public const SEVERITY_RESTRICTED = 'restricted';

    /** Audience suitability: general. */
    public const AUDIENCE_GENERAL = 'general';

    /** Audience suitability: guided. */
    public const AUDIENCE_GUIDED = 'guided';

    /** Audience suitability: mature. */
    public const AUDIENCE_MATURE = 'mature';

    /** Audience suitability: restricted. */
    public const AUDIENCE_RESTRICTED = 'restricted';

    /** Audience suitability: restricted cultural. */
    public const AUDIENCE_RESTRICTED_CULTURAL = 'restricted_cultural';

    /** Audience suitability: restricted integrity. */
    public const AUDIENCE_RESTRICTED_INTEGRITY = 'restricted_integrity';

    /** Audience suitability: staff only. */
    public const AUDIENCE_STAFF_ONLY = 'staff_only';

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

    /** Capability: manage advisories. */
    public const CAP_MANAGE_ADVISORIES = 'mod/uckkarchive:manageadvisories';

    /** Capability: review advisories. */
    public const CAP_REVIEW_ADVISORIES = 'mod/uckkarchive:reviewadvisories';

    /** Capability: view advisories. */
    public const CAP_VIEW_ADVISORIES = 'mod/uckkarchive:viewadvisories';

    /** Capability: view culturally restricted material. */
    public const CAP_VIEW_CULTURALLY_RESTRICTED = 'mod/uckkarchive:viewculturallyrestricted';

    /** Supported categories. */
    private const CATEGORIES = [
        self::CATEGORY_GENERAL,
        self::CATEGORY_CULTURAL,
        self::CATEGORY_CLASSROOM,
        self::CATEGORY_INTEGRITY,
        self::CATEGORY_YOUTH,
        self::CATEGORY_SOURCE,
    ];

    /** Supported severities. */
    private const SEVERITIES = [
        self::SEVERITY_NOTICE,
        self::SEVERITY_MODERATE,
        self::SEVERITY_STRONG,
        self::SEVERITY_RESTRICTED,
    ];

    /** Supported audience suitability values. */
    private const AUDIENCE_VALUES = [
        self::AUDIENCE_GENERAL,
        self::AUDIENCE_GUIDED,
        self::AUDIENCE_MATURE,
        self::AUDIENCE_RESTRICTED,
        self::AUDIENCE_RESTRICTED_CULTURAL,
        self::AUDIENCE_RESTRICTED_INTEGRITY,
        self::AUDIENCE_STAFF_ONLY,
    ];

    /** Supported review states. */
    private const REVIEW_STATES = [
        self::REVIEW_DRAFT,
        self::REVIEW_PENDING,
        self::REVIEW_REVIEWED,
        self::REVIEW_APPROVED,
        self::REVIEW_CONTESTED,
        self::REVIEW_RETIRED,
    ];

    /**
     * Default seed tags.
     *
     * Keys are canonical machine keys. Labels are English defaults; Moodle
     * language strings can override UI display later.
     *
     * @var array<string, array<string, mixed>>
     */
    private const SEED_TAGS = [
        'sexual_violence' => [
            'label' => 'Sexual violence',
            'category' => self::CATEGORY_GENERAL,
            'severity' => self::SEVERITY_STRONG,
            'audience' => self::AUDIENCE_MATURE,
            'description' => 'Content includes or discusses sexual violence.',
        ],
        'violence' => [
            'label' => 'Violence',
            'category' => self::CATEGORY_GENERAL,
            'severity' => self::SEVERITY_MODERATE,
            'audience' => self::AUDIENCE_GUIDED,
            'description' => 'Content includes violence or violent events.',
        ],
        'racism' => [
            'label' => 'Racism',
            'category' => self::CATEGORY_GENERAL,
            'severity' => self::SEVERITY_MODERATE,
            'audience' => self::AUDIENCE_GUIDED,
            'description' => 'Content includes or discusses racism.',
        ],
        'colonial_violence' => [
            'label' => 'Colonial violence',
            'category' => self::CATEGORY_GENERAL,
            'severity' => self::SEVERITY_STRONG,
            'audience' => self::AUDIENCE_GUIDED,
            'description' => 'Content includes or discusses colonial violence.',
        ],
        'death' => [
            'label' => 'Death',
            'category' => self::CATEGORY_GENERAL,
            'severity' => self::SEVERITY_MODERATE,
            'audience' => self::AUDIENCE_GUIDED,
            'description' => 'Content includes death, dying, or loss.',
        ],
        'self_harm' => [
            'label' => 'Self-harm',
            'category' => self::CATEGORY_GENERAL,
            'severity' => self::SEVERITY_STRONG,
            'audience' => self::AUDIENCE_MATURE,
            'description' => 'Content includes or discusses self-harm.',
        ],
        'substance_use' => [
            'label' => 'Substance use',
            'category' => self::CATEGORY_GENERAL,
            'severity' => self::SEVERITY_MODERATE,
            'audience' => self::AUDIENCE_GUIDED,
            'description' => 'Content includes or discusses substance use.',
        ],
        'nudity' => [
            'label' => 'Nudity',
            'category' => self::CATEGORY_GENERAL,
            'severity' => self::SEVERITY_MODERATE,
            'audience' => self::AUDIENCE_GUIDED,
            'description' => 'Content includes nudity.',
        ],
        'explicit_language' => [
            'label' => 'Explicit language',
            'category' => self::CATEGORY_GENERAL,
            'severity' => self::SEVERITY_NOTICE,
            'audience' => self::AUDIENCE_GUIDED,
            'description' => 'Content includes explicit language.',
        ],
        'culturally_sensitive' => [
            'label' => 'Culturally sensitive',
            'category' => self::CATEGORY_CULTURAL,
            'severity' => self::SEVERITY_STRONG,
            'audience' => self::AUDIENCE_RESTRICTED_CULTURAL,
            'description' => 'Content may require cultural context, protocol, or restricted access.',
            'iscultural' => 1,
        ],
        'sacred_content' => [
            'label' => 'Sacred content',
            'category' => self::CATEGORY_CULTURAL,
            'severity' => self::SEVERITY_RESTRICTED,
            'audience' => self::AUDIENCE_RESTRICTED_CULTURAL,
            'description' => 'Content is sacred or ceremonial and requires cultural protocol.',
            'iscultural' => 1,
            'restrictsdefault' => 1,
        ],
        'ceremonial_content' => [
            'label' => 'Ceremonial content',
            'category' => self::CATEGORY_CULTURAL,
            'severity' => self::SEVERITY_RESTRICTED,
            'audience' => self::AUDIENCE_RESTRICTED_CULTURAL,
            'description' => 'Content relates to ceremony and requires appropriate context.',
            'iscultural' => 1,
            'restrictsdefault' => 1,
        ],
        'restricted_knowledge' => [
            'label' => 'Restricted knowledge',
            'category' => self::CATEGORY_CULTURAL,
            'severity' => self::SEVERITY_RESTRICTED,
            'audience' => self::AUDIENCE_RESTRICTED_CULTURAL,
            'description' => 'Content includes knowledge that is not appropriate for unrestricted access.',
            'iscultural' => 1,
            'restrictsdefault' => 1,
        ],
        'grief_or_mourning' => [
            'label' => 'Grief or mourning',
            'category' => self::CATEGORY_GENERAL,
            'severity' => self::SEVERITY_MODERATE,
            'audience' => self::AUDIENCE_GUIDED,
            'description' => 'Content may involve grief, mourning, or bereavement.',
        ],
        'requires_context' => [
            'label' => 'Requires context',
            'category' => self::CATEGORY_CLASSROOM,
            'severity' => self::SEVERITY_NOTICE,
            'audience' => self::AUDIENCE_GUIDED,
            'description' => 'Content should be presented with context or guidance.',
        ],
        'not_for_children' => [
            'label' => 'Not for children',
            'category' => self::CATEGORY_YOUTH,
            'severity' => self::SEVERITY_STRONG,
            'audience' => self::AUDIENCE_MATURE,
            'description' => 'Content is not suitable for children.',
        ],
        'community_permission_required' => [
            'label' => 'Community permission required',
            'category' => self::CATEGORY_CULTURAL,
            'severity' => self::SEVERITY_RESTRICTED,
            'audience' => self::AUDIENCE_RESTRICTED_CULTURAL,
            'description' => 'Access or use requires community permission.',
            'iscultural' => 1,
            'restrictsdefault' => 1,
        ],
        'elder_review_required' => [
            'label' => 'Elder review required',
            'category' => self::CATEGORY_CULTURAL,
            'severity' => self::SEVERITY_RESTRICTED,
            'audience' => self::AUDIENCE_RESTRICTED_CULTURAL,
            'description' => 'Content requires review by an authorized elder or cultural reviewer.',
            'iscultural' => 1,
            'restrictsdefault' => 1,
        ],
        'seasonal_or_contextual_access' => [
            'label' => 'Seasonal or contextual access',
            'category' => self::CATEGORY_CULTURAL,
            'severity' => self::SEVERITY_STRONG,
            'audience' => self::AUDIENCE_RESTRICTED_CULTURAL,
            'description' => 'Access may depend on season, role, place, or context.',
            'iscultural' => 1,
        ],
        'not_for_public_export' => [
            'label' => 'Not for public export',
            'category' => self::CATEGORY_SOURCE,
            'severity' => self::SEVERITY_RESTRICTED,
            'audience' => self::AUDIENCE_RESTRICTED,
            'description' => 'Content must not be included in public exports.',
            'restrictsdefault' => 1,
        ],
    ];

    /**
     * Static helper only.
     */
    private function __construct() {
    }

    /**
     * Return the table name.
     *
     * @return string
     */
    public static function table(): string {
        return self::TABLE;
    }

    /**
     * Return supported tag categories.
     *
     * @return string[]
     */
    public static function get_categories(): array {
        return self::CATEGORIES;
    }

    /**
     * Return supported severities.
     *
     * @return string[]
     */
    public static function get_severities(): array {
        return self::SEVERITIES;
    }

    /**
     * Return supported audience values.
     *
     * @return string[]
     */
    public static function get_audience_values(): array {
        return self::AUDIENCE_VALUES;
    }

    /**
     * Return supported review states.
     *
     * @return string[]
     */
    public static function get_review_states(): array {
        return self::REVIEW_STATES;
    }

    /**
     * Return canonical seed tags.
     *
     * @return array<string, array<string, mixed>>
     */
    public static function get_seed_tags(): array {
        return self::SEED_TAGS;
    }

    /**
     * Get a tag by id.
     *
     * @param int $id Tag id.
     * @param int $strictness MUST_EXIST or IGNORE_MISSING.
     * @return stdClass|false
     * @throws dml_exception
     */
    public static function get_by_id(int $id, int $strictness = MUST_EXIST) {
        global $DB;

        return $DB->get_record(self::TABLE, ['id' => $id], '*', $strictness);
    }

    /**
     * Get a tag by UUID.
     *
     * @param string $uuid Tag UUID.
     * @param int $strictness MUST_EXIST or IGNORE_MISSING.
     * @return stdClass|false
     * @throws dml_exception
     */
    public static function get_by_uuid(string $uuid, int $strictness = MUST_EXIST) {
        global $DB;

        $uuid = self::normalise_uuid($uuid);
        return $DB->get_record(self::TABLE, ['uuid' => $uuid], '*', $strictness);
    }

    /**
     * Get a tag by key.
     *
     * @param string $tagkey Tag key.
     * @param int $strictness MUST_EXIST or IGNORE_MISSING.
     * @return stdClass|false
     * @throws dml_exception
     */
    public static function get_by_key(string $tagkey, int $strictness = MUST_EXIST) {
        global $DB;

        $tagkey = self::normalise_key($tagkey);
        return $DB->get_record(self::TABLE, ['tagkey' => $tagkey], '*', $strictness);
    }

    /**
     * Get all tags, optionally filtered.
     *
     * @param array<string, mixed> $filters Filters.
     * @return stdClass[]
     * @throws dml_exception
     */
    public static function get_all(array $filters = []): array {
        global $DB;

        $where = [];
        $params = [];

        if (array_key_exists('active', $filters)) {
            $where[] = 'active = :active';
            $params['active'] = (int)$filters['active'];
        }

        if (!empty($filters['category'])) {
            $where[] = 'category = :category';
            $params['category'] = self::normalise_category((string)$filters['category']);
        }

        if (!empty($filters['severity'])) {
            $where[] = 'severity = :severity';
            $params['severity'] = self::normalise_severity((string)$filters['severity']);
        }

        if (!empty($filters['iscultural'])) {
            $where[] = 'iscultural = :iscultural';
            $params['iscultural'] = 1;
        }

        if (!empty($filters['restrictsdefault'])) {
            $where[] = 'restrictsdefault = :restrictsdefault';
            $params['restrictsdefault'] = 1;
        }

        $sql = 'SELECT * FROM {' . self::TABLE . '}';
        if ($where) {
            $sql .= ' WHERE ' . implode(' AND ', $where);
        }
        $sql .= ' ORDER BY sortorder ASC, category ASC, label ASC, tagkey ASC';

        return $DB->get_records_sql($sql, $params);
    }

    /**
     * Create a content tag.
     *
     * @param array|stdClass $data Tag data.
     * @param context|null $context Optional context for capability enforcement.
     * @param stdClass|null $user Optional user.
     * @return stdClass Created tag.
     * @throws dml_exception
     * @throws moodle_exception
     */
    public static function create($data, ?context $context = null, ?stdClass $user = null): stdClass {
        global $DB;

        if ($context !== null) {
            self::require_manage($context, $user);
        }

        $record = self::prepare_record($data, true);
        $record->id = $DB->insert_record(self::TABLE, $record);

        return self::get_by_id((int)$record->id);
    }

    /**
     * Update a content tag.
     *
     * @param int $id Tag id.
     * @param array|stdClass $data Updated fields.
     * @param context|null $context Optional context for capability enforcement.
     * @param stdClass|null $user Optional user.
     * @return stdClass Updated tag.
     * @throws dml_exception
     * @throws moodle_exception
     */
    public static function update(int $id, $data, ?context $context = null, ?stdClass $user = null): stdClass {
        global $DB;

        if ($context !== null) {
            self::require_manage($context, $user);
        }

        $existing = self::get_by_id($id);
        $record = self::prepare_record($data, false, $existing);
        $record->id = $id;

        $DB->update_record(self::TABLE, $record);

        return self::get_by_id($id);
    }

    /**
     * Retire a tag without deleting it.
     *
     * @param int $id Tag id.
     * @param context|null $context Optional context for capability enforcement.
     * @param stdClass|null $user Optional user.
     * @return stdClass Retired tag.
     * @throws dml_exception
     * @throws moodle_exception
     */
    public static function retire(int $id, ?context $context = null, ?stdClass $user = null): stdClass {
        return self::update($id, [
            'active' => 0,
            'reviewstate' => self::REVIEW_RETIRED,
        ], $context, $user);
    }

    /**
     * Re-activate a retired/inactive tag.
     *
     * @param int $id Tag id.
     * @param context|null $context Optional context for capability enforcement.
     * @param stdClass|null $user Optional user.
     * @return stdClass Activated tag.
     * @throws dml_exception
     * @throws moodle_exception
     */
    public static function activate(int $id, ?context $context = null, ?stdClass $user = null): stdClass {
        return self::update($id, [
            'active' => 1,
            'reviewstate' => self::REVIEW_APPROVED,
        ], $context, $user);
    }

    /**
     * Ensure baseline content advisory tags exist.
     *
     * Existing tags are not overwritten. This method is safe for install,
     * upgrade, and test setup.
     *
     * @return int Number of tags created.
     * @throws dml_exception
     */
    public static function ensure_seed_data(): int {
        global $DB;

        $created = 0;

        foreach (self::SEED_TAGS as $tagkey => $seed) {
            $tagkey = self::normalise_key($tagkey);

            if ($DB->record_exists(self::TABLE, ['tagkey' => $tagkey])) {
                continue;
            }

            $record = self::prepare_record([
                'tagkey' => $tagkey,
                'label' => $seed['label'] ?? $tagkey,
                'description' => $seed['description'] ?? '',
                'category' => $seed['category'] ?? self::CATEGORY_GENERAL,
                'severity' => $seed['severity'] ?? self::SEVERITY_NOTICE,
                'defaultaudience' => $seed['audience'] ?? self::AUDIENCE_GUIDED,
                'iscultural' => $seed['iscultural'] ?? 0,
                'restrictsdefault' => $seed['restrictsdefault'] ?? 0,
                'active' => 1,
                'reviewstate' => self::REVIEW_APPROVED,
                'sortorder' => $created,
                'metadata' => [
                    'seeded' => true,
                    'seedkey' => $tagkey,
                ],
            ], true);

            $DB->insert_record(self::TABLE, $record);
            $created++;
        }

        return $created;
    }

    /**
     * Convert a tag record to a safe public/exportable array.
     *
     * @param stdClass|array $tag Tag record.
     * @param bool $includemetadata Include decoded metadata.
     * @return array<string, mixed>
     */
    public static function to_export_array($tag, bool $includemetadata = false): array {
        $data = [
            'id' => (int)self::field($tag, 'id', 0),
            'uuid' => (string)self::field($tag, 'uuid', ''),
            'tagkey' => (string)self::field($tag, 'tagkey', ''),
            'label' => (string)self::field($tag, 'label', ''),
            'description' => (string)self::field($tag, 'description', ''),
            'category' => (string)self::field($tag, 'category', self::CATEGORY_GENERAL),
            'severity' => (string)self::field($tag, 'severity', self::SEVERITY_NOTICE),
            'defaultaudience' => (string)self::field($tag, 'defaultaudience', self::AUDIENCE_GUIDED),
            'iscultural' => (int)self::field($tag, 'iscultural', 0),
            'restrictsdefault' => (int)self::field($tag, 'restrictsdefault', 0),
            'reviewstate' => (string)self::field($tag, 'reviewstate', self::REVIEW_DRAFT),
            'active' => (int)self::field($tag, 'active', 1),
        ];

        if ($includemetadata) {
            $data['metadata'] = self::decode_metadata(self::field($tag, self::FIELD_METADATA, ''));
        }

        return $data;
    }

    /**
     * Does a tag imply cultural protocol handling?
     *
     * @param stdClass|array $tag Tag record.
     * @return bool
     */
    public static function is_cultural($tag): bool {
        if ((int)self::field($tag, 'iscultural', 0) === 1) {
            return true;
        }

        return self::normalise_category((string)self::field($tag, 'category', self::CATEGORY_GENERAL)) === self::CATEGORY_CULTURAL;
    }

    /**
     * Does a tag imply restricted-by-default handling?
     *
     * @param stdClass|array $tag Tag record.
     * @return bool
     */
    public static function restricts_by_default($tag): bool {
        if ((int)self::field($tag, 'restrictsdefault', 0) === 1) {
            return true;
        }

        return self::normalise_severity((string)self::field($tag, 'severity', self::SEVERITY_NOTICE)) === self::SEVERITY_RESTRICTED;
    }

    /**
     * Does a tag require human review before approval?
     *
     * @param stdClass|array $tag Tag record.
     * @return bool
     */
    public static function requires_review($tag): bool {
        if (self::is_cultural($tag)) {
            return true;
        }

        if (self::restricts_by_default($tag)) {
            return true;
        }

        $state = self::normalise_review_state((string)self::field($tag, 'reviewstate', self::REVIEW_DRAFT));

        return !in_array($state, [self::REVIEW_REVIEWED, self::REVIEW_APPROVED], true);
    }

    /**
     * Can the user view advisory tags in this context?
     *
     * @param context $context Moodle context.
     * @param stdClass|null $user Optional user.
     * @return bool
     */
    public static function can_view(context $context, ?stdClass $user = null): bool {
        return self::has_capability($context, self::CAP_VIEW_ADVISORIES, $user) ||
            self::has_capability($context, self::CAP_MANAGE_ADVISORIES, $user) ||
            self::has_capability($context, self::CAP_REVIEW_ADVISORIES, $user);
    }

    /**
     * Can the user manage advisory tags?
     *
     * @param context $context Moodle context.
     * @param stdClass|null $user Optional user.
     * @return bool
     */
    public static function can_manage(context $context, ?stdClass $user = null): bool {
        return self::has_capability($context, self::CAP_MANAGE_ADVISORIES, $user);
    }

    /**
     * Can the user review advisory tags?
     *
     * @param context $context Moodle context.
     * @param stdClass|null $user Optional user.
     * @return bool
     */
    public static function can_review(context $context, ?stdClass $user = null): bool {
        return self::has_capability($context, self::CAP_REVIEW_ADVISORIES, $user);
    }

    /**
     * Require advisory viewing.
     *
     * @param context $context Moodle context.
     * @param stdClass|null $user Optional user.
     * @throws moodle_exception
     */
    public static function require_view(context $context, ?stdClass $user = null): void {
        if (!self::can_view($context, $user)) {
            self::throw_policy_exception(self::CAP_VIEW_ADVISORIES, 'Cannot view content advisory tags.');
        }
    }

    /**
     * Require advisory management.
     *
     * @param context $context Moodle context.
     * @param stdClass|null $user Optional user.
     * @throws moodle_exception
     */
    public static function require_manage(context $context, ?stdClass $user = null): void {
        if (!self::can_manage($context, $user)) {
            self::throw_policy_exception(self::CAP_MANAGE_ADVISORIES, 'Cannot manage content advisory tags.');
        }
    }

    /**
     * Require advisory review capability.
     *
     * @param context $context Moodle context.
     * @param stdClass|null $user Optional user.
     * @throws moodle_exception
     */
    public static function require_review(context $context, ?stdClass $user = null): void {
        if (!self::can_review($context, $user)) {
            self::throw_policy_exception(self::CAP_REVIEW_ADVISORIES, 'Cannot review content advisory tags.');
        }
    }

    /**
     * Normalise a tag key.
     *
     * @param string $tagkey Raw tag key.
     * @return string
     */
    public static function normalise_key(string $tagkey): string {
        $tagkey = trim(core_text::strtolower($tagkey));
        $tagkey = str_replace([' ', '-', '.', ':', '/', '\\'], '_', $tagkey);
        $tagkey = preg_replace('/[^a-z0-9_]+/u', '', $tagkey);
        $tagkey = preg_replace('/_+/', '_', $tagkey);
        $tagkey = trim((string)$tagkey, '_');

        if ($tagkey === '') {
            throw new invalid_parameter_exception('Content tag key cannot be empty.');
        }

        if (core_text::strlen($tagkey) > 100) {
            throw new invalid_parameter_exception('Content tag key is too long.');
        }

        return $tagkey;
    }

    /**
     * Normalise category.
     *
     * @param string|null $category Raw category.
     * @return string
     */
    public static function normalise_category(?string $category): string {
        $category = clean_param((string)($category ?? ''), PARAM_ALPHANUMEXT);

        if (!in_array($category, self::CATEGORIES, true)) {
            return self::CATEGORY_GENERAL;
        }

        return $category;
    }

    /**
     * Normalise severity.
     *
     * @param string|null $severity Raw severity.
     * @return string
     */
    public static function normalise_severity(?string $severity): string {
        $severity = clean_param((string)($severity ?? ''), PARAM_ALPHANUMEXT);

        if (!in_array($severity, self::SEVERITIES, true)) {
            return self::SEVERITY_NOTICE;
        }

        return $severity;
    }

    /**
     * Normalise default audience.
     *
     * @param string|null $audience Raw audience.
     * @return string
     */
    public static function normalise_audience(?string $audience): string {
        $audience = clean_param((string)($audience ?? ''), PARAM_ALPHANUMEXT);

        if (!in_array($audience, self::AUDIENCE_VALUES, true)) {
            return self::AUDIENCE_GUIDED;
        }

        return $audience;
    }

    /**
     * Normalise review state.
     *
     * @param string|null $state Raw review state.
     * @return string
     */
    public static function normalise_review_state(?string $state): string {
        $state = clean_param((string)($state ?? ''), PARAM_ALPHANUMEXT);

        if (!in_array($state, self::REVIEW_STATES, true)) {
            return self::REVIEW_DRAFT;
        }

        return $state;
    }

    /**
     * Prepare a DB record for insert/update.
     *
     * @param array|stdClass $data Input data.
     * @param bool $creating Is this an insert?
     * @param stdClass|null $existing Existing record for update.
     * @return stdClass Prepared record.
     */
    private static function prepare_record($data, bool $creating, ?stdClass $existing = null): stdClass {
        $data = (array)$data;
        $now = time();

        $record = new stdClass();

        if ($creating) {
            $record->uuid = !empty($data['uuid']) ? self::normalise_uuid((string)$data['uuid']) : self::new_uuid();
            $record->timecreated = $now;
            $record->createdby = self::current_userid();
        }

        if (array_key_exists('uuid', $data) && !$creating) {
            $record->uuid = self::normalise_uuid((string)$data['uuid']);
        }

        if ($creating || array_key_exists('tagkey', $data)) {
            $record->tagkey = self::normalise_key((string)($data['tagkey'] ?? ''));
        }

        if ($creating || array_key_exists('label', $data)) {
            $record->label = self::normalise_text((string)($data['label'] ?? ($record->tagkey ?? '')), 255);
        }

        if ($creating || array_key_exists('description', $data)) {
            $record->description = self::normalise_long_text((string)($data['description'] ?? ''));
        }

        if ($creating || array_key_exists('category', $data)) {
            $record->category = self::normalise_category((string)($data['category'] ?? self::CATEGORY_GENERAL));
        }

        if ($creating || array_key_exists('severity', $data)) {
            $record->severity = self::normalise_severity((string)($data['severity'] ?? self::SEVERITY_NOTICE));
        }

        if ($creating || array_key_exists('defaultaudience', $data) || array_key_exists('audience', $data)) {
            $record->defaultaudience = self::normalise_audience((string)($data['defaultaudience'] ?? $data['audience'] ??
                self::AUDIENCE_GUIDED));
        }

        if ($creating || array_key_exists('iscultural', $data)) {
            $record->iscultural = (int)!empty($data['iscultural']);
        }

        if ($creating || array_key_exists('restrictsdefault', $data)) {
            $record->restrictsdefault = (int)!empty($data['restrictsdefault']);
        }

        if ($creating || array_key_exists('reviewstate', $data)) {
            $record->reviewstate = self::normalise_review_state((string)($data['reviewstate'] ?? self::REVIEW_DRAFT));
        }

        if ($creating || array_key_exists('active', $data)) {
            $record->active = (int)($data['active'] ?? 1);
        }

        if ($creating || array_key_exists('sortorder', $data)) {
            $record->sortorder = (int)($data['sortorder'] ?? 0);
        }

        if ($creating || array_key_exists('metadata', $data)) {
            $record->metadata = self::encode_metadata($data['metadata'] ?? []);
        }

        if (!$creating && $existing !== null) {
            foreach (['uuid', 'tagkey', 'label', 'description', 'category', 'severity', 'defaultaudience',
                'iscultural', 'restrictsdefault', 'reviewstate', 'active', 'sortorder', 'metadata'] as $field) {
                if (!property_exists($record, $field) && property_exists($existing, $field)) {
                    $record->{$field} = $existing->{$field};
                }
            }
        }

        $record->timemodified = $now;
        $record->modifiedby = self::current_userid();

        return $record;
    }

    /**
     * Normalise short text.
     *
     * @param string $text Raw text.
     * @param int $maxlen Maximum length.
     * @return string
     */
    private static function normalise_text(string $text, int $maxlen): string {
        $text = trim($text);
        $text = clean_param($text, PARAM_TEXT);

        if ($text === '') {
            throw new invalid_parameter_exception('Required text value cannot be empty.');
        }

        if (core_text::strlen($text) > $maxlen) {
            $text = core_text::substr($text, 0, $maxlen);
        }

        return $text;
    }

    /**
     * Normalise long plain text.
     *
     * @param string $text Raw text.
     * @return string
     */
    private static function normalise_long_text(string $text): string {
        $text = trim($text);
        return clean_param($text, PARAM_TEXT);
    }

    /**
     * Encode metadata to JSON.
     *
     * @param mixed $metadata Metadata array/object/string.
     * @return string
     */
    private static function encode_metadata($metadata): string {
        if (is_string($metadata)) {
            $decoded = json_decode($metadata, true);
            if (json_last_error() === JSON_ERROR_NONE && is_array($decoded)) {
                $metadata = $decoded;
            } else {
                $metadata = ['value' => $metadata];
            }
        }

        if ($metadata instanceof stdClass) {
            $metadata = (array)$metadata;
        }

        if (!is_array($metadata)) {
            $metadata = [];
        }

        return json_encode($metadata, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
    }

    /**
     * Decode JSON metadata.
     *
     * @param mixed $metadata Encoded metadata.
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

    /**
     * Normalise UUID string.
     *
     * @param string $uuid UUID.
     * @return string
     */
    private static function normalise_uuid(string $uuid): string {
        $uuid = trim(core_text::strtolower($uuid));

        if (!preg_match('/^[a-f0-9-]{32,36}$/', $uuid)) {
            throw new invalid_parameter_exception('Invalid UUID.');
        }

        return $uuid;
    }

    /**
     * Generate a stable UUID.
     *
     * @return string
     */
    private static function new_uuid(): string {
        $uuidclass = '\\mod_uckkarchive\\local\\uuid';

        if (class_exists($uuidclass) && method_exists($uuidclass, 'generate')) {
            return (string)$uuidclass::generate();
        }

        $bytes = random_bytes(16);
        $bytes[6] = chr((ord($bytes[6]) & 0x0f) | 0x40);
        $bytes[8] = chr((ord($bytes[8]) & 0x3f) | 0x80);

        return vsprintf('%s%s-%s-%s-%s-%s%s%s', str_split(bin2hex($bytes), 4));
    }

    /**
     * Get current user id safely.
     *
     * @return int
     */
    private static function current_userid(): int {
        global $USER;
        return (int)($USER->id ?? 0);
    }

    /**
     * Capability wrapper.
     *
     * @param context $context Moodle context.
     * @param string $capability Capability.
     * @param stdClass|null $user Optional user.
     * @return bool
     */
    private static function has_capability(context $context, string $capability, ?stdClass $user = null): bool {
        $userid = $user !== null && !empty($user->id) ? (int)$user->id : null;
        return has_capability($capability, $context, $userid);
    }

    /**
     * Get field from object/array.
     *
     * @param stdClass|array|null $record Record.
     * @param string $field Field.
     * @param mixed $default Default.
     * @return mixed
     */
    private static function field($record, string $field, $default = null) {
        if ($record instanceof stdClass && property_exists($record, $field)) {
            return $record->{$field};
        }

        if (is_array($record) && array_key_exists($field, $record)) {
            return $record[$field];
        }

        return $default;
    }

    /**
     * Throw consistent policy exception.
     *
     * @param string $capability Capability.
     * @param string $debug Debug text.
     * @throws moodle_exception
     */
    private static function throw_policy_exception(string $capability, string $debug): void {
        throw new moodle_exception('nopermissions', 'error', '', $capability, $debug);
    }
}
