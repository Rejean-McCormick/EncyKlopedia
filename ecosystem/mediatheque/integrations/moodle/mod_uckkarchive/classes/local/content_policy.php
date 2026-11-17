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
 * Content advisory and cultural protocol policy.
 *
 * This class is the server-side authority for:
 *
 * - content advisory visibility;
 * - cultural protocol restrictions;
 * - content marker access;
 * - content review access;
 * - advisory export filtering;
 * - redaction of advisory records for unauthorized users;
 * - safe display rules for advisory panels, media cards, external works, and exports.
 *
 * UI, AMD modules, templates, forms, and output classes must not replace this
 * policy layer.
 *
 * @package     mod_uckkarchive
 */
final class content_policy {

    /** Capability: view non-restricted content advisories. */
    public const CAP_VIEW_ADVISORIES = 'mod/uckkarchive:viewadvisories';

    /** Capability: create/manage advisory tags, tag sets, markers, and vocabulary. */
    public const CAP_MANAGE_ADVISORIES = 'mod/uckkarchive:manageadvisories';

    /** Capability: review/approve/contest content advisory markers. */
    public const CAP_REVIEW_ADVISORIES = 'mod/uckkarchive:reviewadvisories';

    /** Capability: view culturally restricted material. */
    public const CAP_VIEW_CULTURALLY_RESTRICTED = 'mod/uckkarchive:viewculturallyrestricted';

    /** Capability: view normal media records. */
    public const CAP_VIEW_MEDIA = 'mod/uckkarchive:viewmedia';

    /** Capability: view restricted media records. */
    public const CAP_VIEW_RESTRICTED_MEDIA = 'mod/uckkarchive:viewrestrictedmedia';

    /** Capability: view restricted archive records. */
    public const CAP_VIEW_RESTRICTED = 'mod/uckkarchive:viewrestricted';

    /** Capability: export archive records. */
    public const CAP_EXPORT = 'mod/uckkarchive:export';

    /** Capability: export media records. */
    public const CAP_EXPORT_MEDIA = 'mod/uckkarchive:exportmedia';

    /** Capability: manage external works. */
    public const CAP_MANAGE_EXTERNAL_WORKS = 'mod/uckkarchive:manageexternalworks';

    /** Redaction mode: hide the full record. */
    public const REDACT_HIDE = 'hide';

    /** Redaction mode: show minimal safe placeholder. */
    public const REDACT_PLACEHOLDER = 'placeholder';

    /** Redaction mode: show label without sensitive locator/details. */
    public const REDACT_LABEL_ONLY = 'label_only';

    /** Redaction mode: show full data. */
    public const REDACT_NONE = 'none';

    /** @var string[] Visibility values treated as restricted by default. */
    public const RESTRICTED_VISIBILITIES = [
        'restricted',
        'restricted_integrity',
        'restricted_cultural',
        'staff_only',
    ];

    /** @var string[] Audience suitability values treated as restricted by default. */
    public const RESTRICTED_SUITABILITY = [
        'restricted',
        'restricted_cultural',
        'restricted_integrity',
        'staff_only',
    ];

    /** @var string[] Severity values that require stronger handling. */
    public const STRONG_SEVERITIES = [
        'strong',
        'restricted',
    ];

    /** @var string[] Advisory tag keys that are cultural protocol sensitive by convention. */
    public const CULTURAL_TAG_KEYS = [
        'culturally_sensitive',
        'sacred_content',
        'ceremonial_content',
        'restricted_knowledge',
        'community_permission_required',
        'elder_review_required',
        'seasonal_or_contextual_access',
        'not_for_public_export',
    ];

    /** @var string[] Advisory tag keys that should not be shown as casual public metadata. */
    public const SENSITIVE_TAG_KEYS = [
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
    ];

    /**
     * Private constructor for static utility class.
     */
    private function __construct() {
    }

    /**
     * Returns whether the user can view ordinary advisories in context.
     *
     * @param \context $context Moodle context.
     * @param int|null $userid User id, or null for current user.
     * @return bool
     */
    public static function can_view_advisories(\context $context, ?int $userid = null): bool {
        return self::has_capability(self::CAP_VIEW_ADVISORIES, $context, $userid)
            || self::has_capability(self::CAP_MANAGE_ADVISORIES, $context, $userid)
            || self::has_capability(self::CAP_REVIEW_ADVISORIES, $context, $userid);
    }

    /**
     * Require permission to view advisory records.
     *
     * @param \context $context Moodle context.
     */
    public static function require_view_advisories(\context $context): void {
        if (!self::can_view_advisories($context)) {
            throw new \required_capability_exception($context, self::CAP_VIEW_ADVISORIES, 'nopermissions', '');
        }
    }

    /**
     * Returns whether the user can manage advisory vocabulary and markers.
     *
     * @param \context $context Moodle context.
     * @param int|null $userid User id, or null for current user.
     * @return bool
     */
    public static function can_manage_advisories(\context $context, ?int $userid = null): bool {
        return self::has_capability(self::CAP_MANAGE_ADVISORIES, $context, $userid);
    }

    /**
     * Require permission to manage advisory records.
     *
     * @param \context $context Moodle context.
     */
    public static function require_manage_advisories(\context $context): void {
        require_capability(self::CAP_MANAGE_ADVISORIES, $context);
    }

    /**
     * Returns whether the user can review advisory records.
     *
     * @param \context $context Moodle context.
     * @param int|null $userid User id, or null for current user.
     * @return bool
     */
    public static function can_review_advisories(\context $context, ?int $userid = null): bool {
        return self::has_capability(self::CAP_REVIEW_ADVISORIES, $context, $userid)
            || self::can_manage_advisories($context, $userid);
    }

    /**
     * Require permission to review advisory records.
     *
     * @param \context $context Moodle context.
     */
    public static function require_review_advisories(\context $context): void {
        if (!self::can_review_advisories($context)) {
            throw new \required_capability_exception($context, self::CAP_REVIEW_ADVISORIES, 'nopermissions', '');
        }
    }

    /**
     * Returns whether the user can view culturally restricted material.
     *
     * @param \context $context Moodle context.
     * @param int|null $userid User id, or null for current user.
     * @return bool
     */
    public static function can_view_culturally_restricted(\context $context, ?int $userid = null): bool {
        return self::has_capability(self::CAP_VIEW_CULTURALLY_RESTRICTED, $context, $userid)
            || self::can_manage_advisories($context, $userid)
            || self::can_review_advisories($context, $userid);
    }

    /**
     * Returns whether the user can view restricted integrity/archive records.
     *
     * @param \context $context Moodle context.
     * @param int|null $userid User id, or null for current user.
     * @return bool
     */
    public static function can_view_restricted(\context $context, ?int $userid = null): bool {
        return self::has_capability(self::CAP_VIEW_RESTRICTED, $context, $userid)
            || self::has_capability(self::CAP_VIEW_RESTRICTED_MEDIA, $context, $userid)
            || self::can_manage_advisories($context, $userid)
            || self::can_review_advisories($context, $userid);
    }

    /**
     * Returns whether the user can export advisory data in context.
     *
     * @param \context $context Moodle context.
     * @param int|null $userid User id, or null for current user.
     * @return bool
     */
    public static function can_export_advisories(\context $context, ?int $userid = null): bool {
        return self::has_capability(self::CAP_EXPORT, $context, $userid)
            || self::has_capability(self::CAP_EXPORT_MEDIA, $context, $userid);
    }

    /**
     * Returns whether a content marker can be viewed by the user.
     *
     * The marker may be a DB record with direct fields, or a synthetic object
     * prepared by a service. Common fields are:
     *
     * - visibility
     * - audiencesuitability
     * - severity
     * - reviewstate
     * - tagkey
     * - iscultural
     * - isrestricted
     *
     * @param \context $context Moodle context.
     * @param \stdClass $marker Marker record.
     * @param int|null $userid User id, or null for current user.
     * @return bool
     */
    public static function can_view_marker(\context $context, \stdClass $marker, ?int $userid = null): bool {
        if (!self::can_view_advisories($context, $userid)) {
            return false;
        }

        if (self::is_hidden_review_state($marker) && !self::can_review_advisories($context, $userid)) {
            return false;
        }

        if (self::is_culturally_restricted($marker) && !self::can_view_culturally_restricted($context, $userid)) {
            return false;
        }

        if (self::is_restricted_marker($marker) && !self::can_view_restricted($context, $userid)) {
            return false;
        }

        return true;
    }

    /**
     * Returns whether a marker can be created or edited.
     *
     * @param \context $context Moodle context.
     * @param \stdClass|null $marker Existing marker or null.
     * @param int|null $userid User id, or null for current user.
     * @return bool
     */
    public static function can_edit_marker(\context $context, ?\stdClass $marker = null, ?int $userid = null): bool {
        if (!self::can_manage_advisories($context, $userid)) {
            return false;
        }

        if ($marker && self::is_culturally_restricted($marker)
                && !self::can_view_culturally_restricted($context, $userid)) {
            return false;
        }

        return true;
    }

    /**
     * Returns whether a marker can be deleted.
     *
     * Deletion should usually soft-delete or retire markers, not physically
     * remove reviewed/culturally restricted advisory records.
     *
     * @param \context $context Moodle context.
     * @param \stdClass $marker Marker record.
     * @param int|null $userid User id, or null for current user.
     * @return bool
     */
    public static function can_delete_marker(\context $context, \stdClass $marker, ?int $userid = null): bool {
        if (!self::can_manage_advisories($context, $userid)) {
            return false;
        }

        $reviewstate = self::field_string($marker, 'reviewstate', 'draft');
        if (in_array($reviewstate, ['approved', 'reviewed', 'contested'], true)) {
            return self::can_review_advisories($context, $userid);
        }

        return true;
    }

    /**
     * Returns whether a marker can be reviewed.
     *
     * @param \context $context Moodle context.
     * @param \stdClass $marker Marker record.
     * @param int|null $userid User id, or null for current user.
     * @return bool
     */
    public static function can_review_marker(\context $context, \stdClass $marker, ?int $userid = null): bool {
        if (!self::can_review_advisories($context, $userid)) {
            return false;
        }

        if (self::is_culturally_restricted($marker)
                && !self::can_view_culturally_restricted($context, $userid)) {
            return false;
        }

        return true;
    }

    /**
     * Returns whether a marker can be exported.
     *
     * @param \context $context Moodle context.
     * @param \stdClass $marker Marker record.
     * @param int|null $userid User id, or null for current user.
     * @return bool
     */
    public static function can_export_marker(\context $context, \stdClass $marker, ?int $userid = null): bool {
        if (!self::can_export_advisories($context, $userid)) {
            return false;
        }

        return self::can_view_marker($context, $marker, $userid);
    }

    /**
     * Determine whether advisory panel should be shown.
     *
     * @param \context $context Moodle context.
     * @param \stdClass[] $markers Marker records.
     * @param int|null $userid User id, or null for current user.
     * @return bool
     */
    public static function should_show_advisory_panel(\context $context, array $markers, ?int $userid = null): bool {
        if (!self::can_view_advisories($context, $userid)) {
            return false;
        }

        foreach ($markers as $marker) {
            if ($marker instanceof \stdClass && self::redaction_mode($context, $marker, $userid) !== self::REDACT_HIDE) {
                return true;
            }
        }

        return false;
    }

    /**
     * Filter marker records to those displayable to a user.
     *
     * @param \context $context Moodle context.
     * @param \stdClass[] $markers Marker records.
     * @param int|null $userid User id, or null for current user.
     * @param bool $redact Whether to include redacted placeholders.
     * @return \stdClass[] Filtered marker records.
     */
    public static function filter_markers(\context $context, array $markers, ?int $userid = null,
            bool $redact = true): array {
        $out = [];

        foreach ($markers as $marker) {
            if (!$marker instanceof \stdClass) {
                continue;
            }

            $mode = self::redaction_mode($context, $marker, $userid);

            if ($mode === self::REDACT_HIDE) {
                continue;
            }

            $out[] = $redact ? self::redact_marker($marker, $mode) : clone($marker);
        }

        return $out;
    }

    /**
     * Return marker redaction mode for a user.
     *
     * @param \context $context Moodle context.
     * @param \stdClass $marker Marker record.
     * @param int|null $userid User id, or null for current user.
     * @return string Redaction mode.
     */
    public static function redaction_mode(\context $context, \stdClass $marker, ?int $userid = null): string {
        if (!self::can_view_advisories($context, $userid)) {
            return self::REDACT_HIDE;
        }

        if (self::is_hidden_review_state($marker) && !self::can_review_advisories($context, $userid)) {
            return self::REDACT_HIDE;
        }

        if (self::is_culturally_restricted($marker)
                && !self::can_view_culturally_restricted($context, $userid)) {
            return self::REDACT_PLACEHOLDER;
        }

        if (self::is_restricted_marker($marker)
                && !self::can_view_restricted($context, $userid)) {
            return self::REDACT_LABEL_ONLY;
        }

        return self::REDACT_NONE;
    }

    /**
     * Redact marker according to mode.
     *
     * @param \stdClass $marker Marker record.
     * @param string $mode Redaction mode.
     * @return \stdClass Redacted marker.
     */
    public static function redact_marker(\stdClass $marker, string $mode): \stdClass {
        $safe = clone($marker);

        if ($mode === self::REDACT_NONE) {
            return $safe;
        }

        $safe->redacted = true;
        $safe->redactionmode = $mode;

        if ($mode === self::REDACT_PLACEHOLDER) {
            $safe->tagkey = 'restricted_cultural';
            $safe->label = get_string('restrictedculturalcontent', 'uckkarchive');
            $safe->severity = 'restricted';
            $safe->audiencesuitability = 'restricted_cultural';
            $safe->visibility = 'restricted_cultural';
            $safe->note = '';
            $safe->teachingnote = '';
            $safe->culturalprotocolnote = '';
            $safe->locatorjson = '';
            $safe->locator = null;
            return $safe;
        }

        if ($mode === self::REDACT_LABEL_ONLY) {
            $safe->note = '';
            $safe->teachingnote = '';
            $safe->culturalprotocolnote = '';
            $safe->locatorjson = '';
            $safe->locator = null;
            return $safe;
        }

        return $safe;
    }

    /**
     * Validate and normalize marker data before saving.
     *
     * @param array $data Marker input data.
     * @return array Normalized data.
     */
    public static function normalize_marker_input(array $data): array {
        $data = metadata_validator::normalize_metadata($data);

        if (isset($data['tagkey'])) {
            $data['tagkey'] = metadata_validator::tag_key((string)$data['tagkey']);
        }

        if (isset($data['tagsetkey'])) {
            $data['tagsetkey'] = metadata_validator::tag_key((string)$data['tagsetkey'], 'tagsetkey');
        }

        if (isset($data['severity'])) {
            $data['severity'] = metadata_validator::advisory_severity((string)$data['severity'], true);
        }

        if (isset($data['visibility'])) {
            $data['visibility'] = metadata_validator::visibility((string)$data['visibility'], true);
        }

        if (isset($data['audiencesuitability'])) {
            $data['audiencesuitability'] =
                metadata_validator::audience_suitability((string)$data['audiencesuitability'], true);
        }

        if (isset($data['reviewstate'])) {
            $data['reviewstate'] = metadata_validator::review_state((string)$data['reviewstate'], true);
        }

        if (isset($data['locator'])) {
            if (!is_array($data['locator'])) {
                throw new \invalid_parameter_exception('locator must be an object.');
            }
            $data['locator'] = metadata_validator::locator($data['locator']);
        }

        if (isset($data['metadata']) && is_array($data['metadata'])) {
            $data['metadata'] = metadata_validator::content_marker_metadata($data['metadata']);
        }

        return $data;
    }

    /**
     * Return default visibility for a marker with a given tag/severity.
     *
     * @param string|null $tagkey Tag key.
     * @param string|null $severity Severity.
     * @return string Visibility.
     */
    public static function default_marker_visibility(?string $tagkey = null, ?string $severity = null): string {
        $tagkey = $tagkey ? metadata_validator::tag_key($tagkey) : '';

        if ($tagkey !== '' && in_array($tagkey, self::CULTURAL_TAG_KEYS, true)) {
            return 'restricted_cultural';
        }

        if ($severity === 'restricted') {
            return 'restricted';
        }

        return 'course';
    }

    /**
     * Return default review state for a marker with a given tag/severity.
     *
     * @param string|null $tagkey Tag key.
     * @param string|null $severity Severity.
     * @return string Review state.
     */
    public static function default_review_state(?string $tagkey = null, ?string $severity = null): string {
        $tagkey = $tagkey ? metadata_validator::tag_key($tagkey) : '';

        if ($severity === 'restricted' || in_array($tagkey, self::CULTURAL_TAG_KEYS, true)) {
            return 'pending_review';
        }

        return 'draft';
    }

    /**
     * Return default audience suitability for a marker with a given tag/severity.
     *
     * @param string|null $tagkey Tag key.
     * @param string|null $severity Severity.
     * @return string Audience suitability.
     */
    public static function default_audience_suitability(?string $tagkey = null, ?string $severity = null): string {
        $tagkey = $tagkey ? metadata_validator::tag_key($tagkey) : '';

        if (in_array($tagkey, self::CULTURAL_TAG_KEYS, true)) {
            return 'restricted_cultural';
        }

        if ($severity === 'restricted') {
            return 'restricted';
        }

        if ($severity === 'strong') {
            return 'mature';
        }

        return 'guided';
    }

    /**
     * Returns whether marker is culturally restricted.
     *
     * @param \stdClass $marker Marker record.
     * @return bool
     */
    public static function is_culturally_restricted(\stdClass $marker): bool {
        if (!empty($marker->iscultural) || !empty($marker->culturalprotocol)) {
            return true;
        }

        $visibility = self::field_string($marker, 'visibility');
        if ($visibility === 'restricted_cultural') {
            return true;
        }

        $suitability = self::field_string($marker, 'audiencesuitability');
        if ($suitability === 'restricted_cultural') {
            return true;
        }

        $tagkey = self::field_string($marker, 'tagkey');
        return in_array($tagkey, self::CULTURAL_TAG_KEYS, true);
    }

    /**
     * Returns whether marker is restricted.
     *
     * @param \stdClass $marker Marker record.
     * @return bool
     */
    public static function is_restricted_marker(\stdClass $marker): bool {
        if (!empty($marker->isrestricted)) {
            return true;
        }

        $visibility = self::field_string($marker, 'visibility');
        if (in_array($visibility, self::RESTRICTED_VISIBILITIES, true)) {
            return true;
        }

        $suitability = self::field_string($marker, 'audiencesuitability');
        if (in_array($suitability, self::RESTRICTED_SUITABILITY, true)) {
            return true;
        }

        $severity = self::field_string($marker, 'severity');
        if (in_array($severity, self::STRONG_SEVERITIES, true)) {
            return true;
        }

        return self::is_culturally_restricted($marker);
    }

    /**
     * Returns whether marker review state is hidden from ordinary advisory viewers.
     *
     * @param \stdClass $marker Marker record.
     * @return bool
     */
    public static function is_hidden_review_state(\stdClass $marker): bool {
        $reviewstate = self::field_string($marker, 'reviewstate', 'draft');
        return in_array($reviewstate, ['draft', 'pending_review', 'contested', 'retired'], true);
    }

    /**
     * Returns whether a marker should show an advisory before content access.
     *
     * @param \stdClass $marker Marker record.
     * @return bool
     */
    public static function requires_context_warning(\stdClass $marker): bool {
        if (!empty($marker->requirescontext)) {
            return true;
        }

        $severity = self::field_string($marker, 'severity');
        if (in_array($severity, self::STRONG_SEVERITIES, true)) {
            return true;
        }

        $tagkey = self::field_string($marker, 'tagkey');
        return in_array($tagkey, self::SENSITIVE_TAG_KEYS, true);
    }

    /**
     * Returns whether the user can see a locator for a marker.
     *
     * @param \context $context Moodle context.
     * @param \stdClass $marker Marker record.
     * @param int|null $userid User id, or null for current user.
     * @return bool
     */
    public static function can_view_locator(\context $context, \stdClass $marker, ?int $userid = null): bool {
        if (!self::can_view_marker($context, $marker, $userid)) {
            return false;
        }

        if (self::is_restricted_marker($marker) && !self::can_view_restricted($context, $userid)) {
            return false;
        }

        if (self::is_culturally_restricted($marker)
                && !self::can_view_culturally_restricted($context, $userid)) {
            return false;
        }

        return true;
    }

    /**
     * Build a safe display summary for a marker.
     *
     * @param \context $context Moodle context.
     * @param \stdClass $marker Marker record.
     * @param int|null $userid User id, or null for current user.
     * @return array Display summary.
     */
    public static function marker_display_summary(\context $context, \stdClass $marker, ?int $userid = null): array {
        $mode = self::redaction_mode($context, $marker, $userid);
        $safe = self::redact_marker($marker, $mode);

        return [
            'id' => isset($safe->id) ? (int)$safe->id : 0,
            'uuid' => isset($safe->uuid) ? (string)$safe->uuid : '',
            'tagkey' => self::field_string($safe, 'tagkey'),
            'label' => self::field_string($safe, 'label', self::field_string($safe, 'tagkey')),
            'severity' => self::field_string($safe, 'severity', 'notice'),
            'visibility' => self::field_string($safe, 'visibility', 'course'),
            'audiencesuitability' => self::field_string($safe, 'audiencesuitability', 'guided'),
            'reviewstate' => self::field_string($safe, 'reviewstate', 'draft'),
            'redacted' => !empty($safe->redacted),
            'redactionmode' => self::field_string($safe, 'redactionmode', self::REDACT_NONE),
            'requirescontext' => self::requires_context_warning($safe),
            'cultural' => self::is_culturally_restricted($safe),
            'restricted' => self::is_restricted_marker($safe),
            'showlocator' => self::can_view_locator($context, $marker, $userid),
        ];
    }

    /**
     * Returns whether content advisory data may be included in an export manifest.
     *
     * @param \context $context Moodle context.
     * @param \stdClass $marker Marker record.
     * @param int|null $userid User id, or null for current user.
     * @return bool
     */
    public static function include_marker_in_export_manifest(\context $context, \stdClass $marker,
            ?int $userid = null): bool {
        if (!self::can_export_marker($context, $marker, $userid)) {
            return false;
        }

        if (self::field_string($marker, 'tagkey') === 'not_for_public_export') {
            return self::can_view_culturally_restricted($context, $userid);
        }

        return true;
    }

    /**
     * Prepare marker for export manifest.
     *
     * @param \context $context Moodle context.
     * @param \stdClass $marker Marker record.
     * @param int|null $userid User id, or null for current user.
     * @return array|null Export-safe marker data, or null when excluded.
     */
    public static function export_marker_data(\context $context, \stdClass $marker, ?int $userid = null): ?array {
        if (!self::include_marker_in_export_manifest($context, $marker, $userid)) {
            return null;
        }

        $mode = self::redaction_mode($context, $marker, $userid);
        $safe = self::redact_marker($marker, $mode);

        return [
            'uuid' => isset($safe->uuid) ? (string)$safe->uuid : '',
            'tagkey' => self::field_string($safe, 'tagkey'),
            'tagsetkey' => self::field_string($safe, 'tagsetkey'),
            'severity' => self::field_string($safe, 'severity', 'notice'),
            'visibility' => self::field_string($safe, 'visibility', 'course'),
            'audiencesuitability' => self::field_string($safe, 'audiencesuitability', 'guided'),
            'reviewstate' => self::field_string($safe, 'reviewstate', 'draft'),
            'redacted' => !empty($safe->redacted),
            'redactionmode' => self::field_string($safe, 'redactionmode', self::REDACT_NONE),
        ];
    }

    /**
     * Check capability wrapper that supports explicit user ids.
     *
     * @param string $capability Capability.
     * @param \context $context Context.
     * @param int|null $userid User id, or null for current user.
     * @return bool
     */
    private static function has_capability(string $capability, \context $context, ?int $userid = null): bool {
        global $USER;

        if ($userid === null || (isset($USER->id) && (int)$userid === (int)$USER->id)) {
            return has_capability($capability, $context);
        }

        return has_capability($capability, $context, $userid, false);
    }

    /**
     * Safely read a lower-case string field from a record.
     *
     * @param \stdClass $record Record.
     * @param string $field Field.
     * @param string $default Default.
     * @return string Lower-case trimmed value.
     */
    private static function field_string(\stdClass $record, string $field, string $default = ''): string {
        if (!isset($record->{$field}) || $record->{$field} === null) {
            return $default;
        }

        if (!is_scalar($record->{$field})) {
            return $default;
        }

        return strtolower(trim((string)$record->{$field}));
    }
}
