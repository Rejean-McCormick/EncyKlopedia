<?php
// This file is part of Moodle - https://moodle.org/
//
// Moodle is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// any later version.

/**
 * Media policy helper for UCKK Archive.
 *
 * @package    mod_uckkarchive
 * @copyright  2026 Univers-Cité King Klown
 * @license    https://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later
 */

declare(strict_types=1);

namespace mod_uckkarchive\local;

use coding_exception;
use context;
use moodle_exception;
use stdClass;

defined('MOODLE_INTERNAL') || die();

/**
 * Central media policy object.
 *
 * This class does not write to the database. It centralises media access
 * decisions used by controllers, forms, external services, File API handlers,
 * renderables, scheduled tasks, privacy provider, backup/restore code, and
 * tests.
 *
 * The class intentionally accepts loosely-shaped record objects because early
 * implementation stages, external service payloads, privacy export data, and
 * upgrade migrations may not all hydrate the same table joins.
 */
final class media_policy {
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

    /** Legacy visibility spelling accepted for normalisation only. */
    public const VISIBILITY_INSTITUTIONAL = 'institutional';

    /** Visibility: public. */
    public const VISIBILITY_PUBLIC = 'public';

    /** Visibility: restricted. */
    public const VISIBILITY_RESTRICTED = 'restricted';

    /** Visibility: restricted integrity. */
    public const VISIBILITY_RESTRICTED_INTEGRITY = 'restricted_integrity';

    /** Visibility: restricted cultural. */
    public const VISIBILITY_RESTRICTED_CULTURAL = 'restricted_cultural';

    /** Visibility: staff only. */
    public const VISIBILITY_STAFF_ONLY = 'staff_only';

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

    /** File area: original. */
    public const FILEAREA_ORIGINAL = 'media_original';

    /** File area: preview. */
    public const FILEAREA_PREVIEW = 'media_preview';

    /** File area: thumbnail. */
    public const FILEAREA_THUMBNAIL = 'media_thumbnail';

    /** File area: derivative. */
    public const FILEAREA_DERIVATIVE = 'media_derivative';

    /** File area: captions. */
    public const FILEAREA_CAPTION = 'media_caption';

    /** File area: transcript. */
    public const FILEAREA_TRANSCRIPT = 'media_transcript';

    /** File area: attachment. */
    public const FILEAREA_ATTACHMENT = 'media_attachment';

    /** Capability: view ordinary media. */
    public const CAP_VIEW_MEDIA = 'mod/uckkarchive:viewmedia';

    /** Capability: add media. */
    public const CAP_ADD_MEDIA = 'mod/uckkarchive:addmedia';

    /** Capability: edit media metadata. */
    public const CAP_EDIT_MEDIA = 'mod/uckkarchive:editmedia';

    /** Capability: delete/retire media. */
    public const CAP_DELETE_MEDIA = 'mod/uckkarchive:deletemedia';

    /** Capability: download media files. */
    public const CAP_DOWNLOAD_MEDIA = 'mod/uckkarchive:downloadmedia';

    /** Capability: add media versions. */
    public const CAP_VERSION_MEDIA = 'mod/uckkarchive:versionmedia';

    /** Capability: manage collections. */
    public const CAP_MANAGE_COLLECTIONS = 'mod/uckkarchive:managemediacollections';

    /** Capability: export media. */
    public const CAP_EXPORT_MEDIA = 'mod/uckkarchive:exportmedia';

    /** Capability: view restricted media. */
    public const CAP_VIEW_RESTRICTED_MEDIA = 'mod/uckkarchive:viewrestrictedmedia';

    /** Capability: view culturally restricted records. */
    public const CAP_VIEW_CULTURALLY_RESTRICTED = 'mod/uckkarchive:viewculturallyrestricted';

    /** Archive capability used as fallback for restricted archive records. */
    public const CAP_VIEW_RESTRICTED_ARCHIVE = 'mod/uckkarchive:viewrestricted';

    /** Content capability used for advisory visibility. */
    public const CAP_VIEW_ADVISORIES = 'mod/uckkarchive:viewadvisories';

    /** Content capability used for advisory review/approval. */
    public const CAP_REVIEW_ADVISORIES = 'mod/uckkarchive:reviewadvisories';

    /** Activity view fallback capability. */
    public const CAP_VIEW_ACTIVITY = 'mod/uckkarchive:view';

    /** Supported media statuses. */
    private const STATUSES = [
        self::STATUS_DRAFT,
        self::STATUS_SUBMITTED,
        self::STATUS_ACTIVE,
        self::STATUS_RESTRICTED,
        self::STATUS_SUPERSEDED,
        self::STATUS_ARCHIVED,
        self::STATUS_DELETED_SOFT,
    ];

    /** Supported visibility values. */
    private const VISIBILITIES = [
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
        self::VISIBILITY_STAFF_ONLY,
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

    /** Canonical media file areas. */
    private const FILEAREAS = [
        self::FILEAREA_ORIGINAL,
        self::FILEAREA_PREVIEW,
        self::FILEAREA_THUMBNAIL,
        self::FILEAREA_DERIVATIVE,
        self::FILEAREA_CAPTION,
        self::FILEAREA_TRANSCRIPT,
        self::FILEAREA_ATTACHMENT,
    ];

    /**
     * Static helper only.
     */
    private function __construct() {
    }

    /**
     * Return canonical media status values.
     *
     * @return string[]
     */
    public static function get_statuses(): array {
        return self::STATUSES;
    }

    /**
     * Return canonical media visibility values.
     *
     * @return string[]
     */
    public static function get_visibilities(): array {
        return self::VISIBILITIES;
    }

    /**
     * Return canonical audience suitability values.
     *
     * @return string[]
     */
    public static function get_audience_values(): array {
        return self::AUDIENCE_VALUES;
    }

    /**
     * Return canonical media File API areas.
     *
     * @return string[]
     */
    public static function get_fileareas(): array {
        return self::FILEAREAS;
    }

    /**
     * Can a user see the media library surface in this context?
     *
     * @param context $context Moodle context.
     * @param stdClass|null $user Optional user record.
     * @return bool
     */
    public static function can_view_library(context $context, ?stdClass $user = null): bool {
        return self::has_any_capability($context, [
            self::CAP_VIEW_MEDIA,
            self::CAP_VIEW_ACTIVITY,
        ], $user);
    }

    /**
     * Require access to the media library surface.
     *
     * @param context $context Moodle context.
     * @param stdClass|null $user Optional user record.
     */
    public static function require_view_library(context $context, ?stdClass $user = null): void {
        self::require_any_capability($context, [
            self::CAP_VIEW_MEDIA,
            self::CAP_VIEW_ACTIVITY,
        ], $user);
    }

    /**
     * Can a user add a media object?
     *
     * @param context $context Moodle context.
     * @param stdClass|null $user Optional user record.
     * @return bool
     */
    public static function can_add_media(context $context, ?stdClass $user = null): bool {
        return self::has_capability($context, self::CAP_ADD_MEDIA, $user);
    }

    /**
     * Require permission to add a media object.
     *
     * @param context $context Moodle context.
     * @param stdClass|null $user Optional user record.
     */
    public static function require_add_media(context $context, ?stdClass $user = null): void {
        self::require_capability($context, self::CAP_ADD_MEDIA, $user);
    }

    /**
     * Can a user view a specific media object?
     *
     * @param context $context Moodle context.
     * @param stdClass|array $media Media record or array.
     * @param stdClass|null $user Optional user record.
     * @return bool
     */
    public static function can_view_media(context $context, $media, ?stdClass $user = null): bool {
        if (!self::can_view_library($context, $user)) {
            return false;
        }

        if (!self::passes_status_for_view($media, $user)) {
            return false;
        }

        if (!self::passes_visibility_for_view($context, $media, $user)) {
            return false;
        }

        if (!self::passes_audience_policy($context, $media, 'view', $user)) {
            return false;
        }

        if (!self::passes_content_policy($context, $media, 'view', $user)) {
            return false;
        }

        return true;
    }

    /**
     * Require permission to view a specific media object.
     *
     * @param context $context Moodle context.
     * @param stdClass|array $media Media record or array.
     * @param stdClass|null $user Optional user record.
     */
    public static function require_view_media(context $context, $media, ?stdClass $user = null): void {
        if (!self::can_view_media($context, $media, $user)) {
            self::throw_policy_exception($context, self::CAP_VIEW_MEDIA, 'Cannot view this media record.');
        }
    }

    /**
     * Can a user edit media metadata?
     *
     * @param context $context Moodle context.
     * @param stdClass|array $media Media record or array.
     * @param stdClass|null $user Optional user record.
     * @return bool
     */
    public static function can_edit_media(context $context, $media, ?stdClass $user = null): bool {
        if (!self::has_capability($context, self::CAP_EDIT_MEDIA, $user)) {
            return false;
        }

        if (self::is_deleted_soft($media)) {
            return false;
        }

        if (self::is_owned_by_user($media, $user) && self::is_draft($media)) {
            return true;
        }

        if (!self::passes_restricted_policy($context, $media, 'edit', $user)) {
            return false;
        }

        return !self::is_locked_by_retention_or_redaction($media, 'edit');
    }

    /**
     * Require permission to edit media.
     *
     * @param context $context Moodle context.
     * @param stdClass|array $media Media record or array.
     * @param stdClass|null $user Optional user record.
     */
    public static function require_edit_media(context $context, $media, ?stdClass $user = null): void {
        if (!self::can_edit_media($context, $media, $user)) {
            self::throw_policy_exception($context, self::CAP_EDIT_MEDIA, 'Cannot edit this media record.');
        }
    }

    /**
     * Can a user soft-delete or retire media?
     *
     * @param context $context Moodle context.
     * @param stdClass|array $media Media record or array.
     * @param stdClass|null $user Optional user record.
     * @return bool
     */
    public static function can_delete_media(context $context, $media, ?stdClass $user = null): bool {
        if (!self::has_capability($context, self::CAP_DELETE_MEDIA, $user)) {
            return false;
        }

        if (self::is_deleted_soft($media)) {
            return false;
        }

        if (!self::passes_restricted_policy($context, $media, 'delete', $user)) {
            return false;
        }

        return !self::is_locked_by_retention_or_redaction($media, 'delete');
    }

    /**
     * Require permission to delete media.
     *
     * @param context $context Moodle context.
     * @param stdClass|array $media Media record or array.
     * @param stdClass|null $user Optional user record.
     */
    public static function require_delete_media(context $context, $media, ?stdClass $user = null): void {
        if (!self::can_delete_media($context, $media, $user)) {
            self::throw_policy_exception($context, self::CAP_DELETE_MEDIA, 'Cannot delete this media record.');
        }
    }

    /**
     * Can a user add a new media version?
     *
     * @param context $context Moodle context.
     * @param stdClass|array $media Media record or array.
     * @param stdClass|null $user Optional user record.
     * @return bool
     */
    public static function can_version_media(context $context, $media, ?stdClass $user = null): bool {
        if (!self::has_capability($context, self::CAP_VERSION_MEDIA, $user)) {
            return false;
        }

        if (self::is_deleted_soft($media)) {
            return false;
        }

        if (!self::passes_restricted_policy($context, $media, 'version', $user)) {
            return false;
        }

        return !self::is_locked_by_retention_or_redaction($media, 'version');
    }

    /**
     * Require permission to add a new media version.
     *
     * @param context $context Moodle context.
     * @param stdClass|array $media Media record or array.
     * @param stdClass|null $user Optional user record.
     */
    public static function require_version_media(context $context, $media, ?stdClass $user = null): void {
        if (!self::can_version_media($context, $media, $user)) {
            self::throw_policy_exception($context, self::CAP_VERSION_MEDIA, 'Cannot add a media version.');
        }
    }

    /**
     * Can a user manage media collections?
     *
     * @param context $context Moodle context.
     * @param stdClass|null $user Optional user record.
     * @return bool
     */
    public static function can_manage_collections(context $context, ?stdClass $user = null): bool {
        return self::has_capability($context, self::CAP_MANAGE_COLLECTIONS, $user);
    }

    /**
     * Can a user view a media collection shell?
     *
     * A collection never overrides media-level restrictions. This only answers
     * whether the collection metadata/shell may be viewed.
     *
     * @param context $context Moodle context.
     * @param stdClass|array|null $collection Collection record or array.
     * @param stdClass|null $user Optional user record.
     * @return bool
     */
    public static function can_view_collection(context $context, $collection = null, ?stdClass $user = null): bool {
        if (!self::can_view_library($context, $user)) {
            return false;
        }

        if ($collection === null) {
            return true;
        }

        return self::passes_visibility_for_view($context, $collection, $user);
    }

    /**
     * Can a user export media?
     *
     * @param context $context Moodle context.
     * @param stdClass|array $media Media record or array.
     * @param stdClass|null $user Optional user record.
     * @return bool
     */
    public static function can_export_media(context $context, $media, ?stdClass $user = null): bool {
        if (!self::has_capability($context, self::CAP_EXPORT_MEDIA, $user)) {
            return false;
        }

        if (!self::can_view_media($context, $media, $user)) {
            return false;
        }

        if (!self::passes_restricted_policy($context, $media, 'export', $user)) {
            return false;
        }

        if (!self::passes_audience_policy($context, $media, 'export', $user)) {
            return false;
        }

        if (!self::passes_content_policy($context, $media, 'export', $user)) {
            return false;
        }

        return !self::is_locked_by_retention_or_redaction($media, 'export');
    }

    /**
     * Require media export permission.
     *
     * @param context $context Moodle context.
     * @param stdClass|array $media Media record or array.
     * @param stdClass|null $user Optional user record.
     */
    public static function require_export_media(context $context, $media, ?stdClass $user = null): void {
        if (!self::can_export_media($context, $media, $user)) {
            self::throw_policy_exception($context, self::CAP_EXPORT_MEDIA, 'Cannot export this media record.');
        }
    }

    /**
     * Can a user download a file related to a media object?
     *
     * @param context $context Moodle context.
     * @param stdClass|array $media Media record or array.
     * @param string $filearea Canonical media file area.
     * @param stdClass|array|null $version Optional media version record.
     * @param stdClass|null $user Optional user record.
     * @return bool
     */
    public static function can_download_filearea(context $context, $media, string $filearea, $version = null,
            ?stdClass $user = null): bool {
        $filearea = self::normalise_filearea($filearea);

        if (!self::can_access_filearea($context, $media, $filearea, $version, $user)) {
            return false;
        }

        if (in_array($filearea, [
            self::FILEAREA_ORIGINAL,
            self::FILEAREA_DERIVATIVE,
            self::FILEAREA_CAPTION,
            self::FILEAREA_TRANSCRIPT,
            self::FILEAREA_ATTACHMENT,
        ], true)) {
            return self::has_capability($context, self::CAP_DOWNLOAD_MEDIA, $user);
        }

        return true;
    }

    /**
     * Require permission to download a media file area.
     *
     * @param context $context Moodle context.
     * @param stdClass|array $media Media record or array.
     * @param string $filearea Canonical media file area.
     * @param stdClass|array|null $version Optional media version record.
     * @param stdClass|null $user Optional user record.
     */
    public static function require_download_filearea(context $context, $media, string $filearea, $version = null,
            ?stdClass $user = null): void {
        if (!self::can_download_filearea($context, $media, $filearea, $version, $user)) {
            self::throw_policy_exception($context, self::CAP_DOWNLOAD_MEDIA, 'Cannot download this media file.');
        }
    }

    /**
     * Can a user access a media File API area at all?
     *
     * This is used before deciding whether the area requires downloadmedia.
     *
     * @param context $context Moodle context.
     * @param stdClass|array $media Media record or array.
     * @param string $filearea Canonical media file area.
     * @param stdClass|array|null $version Optional media version record.
     * @param stdClass|null $user Optional user record.
     * @return bool
     */
    public static function can_access_filearea(context $context, $media, string $filearea, $version = null,
            ?stdClass $user = null): bool {
        $filearea = self::normalise_filearea($filearea);

        if (!self::can_view_media($context, $media, $user)) {
            return false;
        }

        if ($version !== null && !self::passes_version_policy($context, $media, $version, $user)) {
            return false;
        }

        if ($filearea === self::FILEAREA_THUMBNAIL) {
            return self::can_view_thumbnail($context, $media, $user);
        }

        if ($filearea === self::FILEAREA_PREVIEW) {
            return self::can_view_preview($context, $media, $user);
        }

        if ($filearea === self::FILEAREA_ORIGINAL) {
            return self::can_view_original($context, $media, $user);
        }

        return self::passes_restricted_policy($context, $media, 'filearea:' . $filearea, $user);
    }

    /**
     * Can a user view a thumbnail for this media?
     *
     * @param context $context Moodle context.
     * @param stdClass|array $media Media record or array.
     * @param stdClass|null $user Optional user record.
     * @return bool
     */
    public static function can_view_thumbnail(context $context, $media, ?stdClass $user = null): bool {
        if (!self::can_view_media($context, $media, $user)) {
            return false;
        }

        if (self::is_restricted_media($media)) {
            return self::can_view_restricted_media($context, $media, $user);
        }

        return true;
    }

    /**
     * Can a user view a preview for this media?
     *
     * @param context $context Moodle context.
     * @param stdClass|array $media Media record or array.
     * @param stdClass|null $user Optional user record.
     * @return bool
     */
    public static function can_view_preview(context $context, $media, ?stdClass $user = null): bool {
        if (!self::can_view_media($context, $media, $user)) {
            return false;
        }

        if (self::is_restricted_media($media)) {
            return self::can_view_restricted_media($context, $media, $user);
        }

        return true;
    }

    /**
     * Can a user view the original file?
     *
     * Viewing the original is stricter than viewing a media card or preview.
     *
     * @param context $context Moodle context.
     * @param stdClass|array $media Media record or array.
     * @param stdClass|null $user Optional user record.
     * @return bool
     */
    public static function can_view_original(context $context, $media, ?stdClass $user = null): bool {
        if (!self::can_view_media($context, $media, $user)) {
            return false;
        }

        if (!self::has_capability($context, self::CAP_DOWNLOAD_MEDIA, $user)) {
            return false;
        }

        return self::passes_restricted_policy($context, $media, 'original', $user);
    }

    /**
     * Can this media appear in ordinary search results?
     *
     * @param context $context Moodle context.
     * @param stdClass|array $media Media record or array.
     * @param stdClass|null $user Optional user record.
     * @return bool
     */
    public static function can_appear_in_search(context $context, $media, ?stdClass $user = null): bool {
        if (!self::can_view_media($context, $media, $user)) {
            return false;
        }

        if (self::is_restricted_media($media)) {
            return self::can_view_restricted_media($context, $media, $user);
        }

        return true;
    }

    /**
     * Can this media appear in a public or unauthenticated surface?
     *
     * This does not mean the file should be served without Moodle checks. It is
     * only a policy helper for public listings/export summaries.
     *
     * @param stdClass|array $media Media record or array.
     * @return bool
     */
    public static function can_be_publicly_listed($media): bool {
        if (self::is_deleted_soft($media)) {
            return false;
        }

        if (self::normalise_status(self::field($media, 'status', self::STATUS_DRAFT)) !== self::STATUS_ACTIVE) {
            return false;
        }

        if (self::normalise_visibility(self::field($media, 'visibility', self::VISIBILITY_PRIVATE)) !== self::VISIBILITY_PUBLIC) {
            return false;
        }

        $audience = self::normalise_audience(self::field($media, 'audiencesuitability',
            self::field($media, 'audience_suitability', self::AUDIENCE_GUIDED)));

        return $audience === self::AUDIENCE_GENERAL;
    }

    /**
     * Can a user view restricted media?
     *
     * @param context $context Moodle context.
     * @param stdClass|array|null $media Optional media record or array.
     * @param stdClass|null $user Optional user record.
     * @return bool
     */
    public static function can_view_restricted_media(context $context, $media = null, ?stdClass $user = null): bool {
        if ($media !== null && self::is_culturally_restricted($media)) {
            return self::can_view_culturally_restricted($context, $media, $user);
        }

        return self::has_any_capability($context, [
            self::CAP_VIEW_RESTRICTED_MEDIA,
            self::CAP_VIEW_RESTRICTED_ARCHIVE,
        ], $user);
    }

    /**
     * Can a user view culturally restricted media?
     *
     * @param context $context Moodle context.
     * @param stdClass|array|null $media Optional media record or array.
     * @param stdClass|null $user Optional user record.
     * @return bool
     */
    public static function can_view_culturally_restricted(context $context, $media = null, ?stdClass $user = null): bool {
        if (!self::has_capability($context, self::CAP_VIEW_CULTURALLY_RESTRICTED, $user)) {
            return false;
        }

        if ($media !== null && !self::passes_content_policy($context, $media, 'cultural_view', $user)) {
            return false;
        }

        return true;
    }

    /**
     * Does the media require restricted access?
     *
     * @param stdClass|array $media Media record or array.
     * @return bool
     */
    public static function is_restricted_media($media): bool {
        $visibility = self::normalise_visibility(self::field($media, 'visibility', self::VISIBILITY_PRIVATE));
        $status = self::normalise_status(self::field($media, 'status', self::STATUS_DRAFT));
        $audience = self::normalise_audience(self::field($media, 'audiencesuitability',
            self::field($media, 'audience_suitability', self::AUDIENCE_GUIDED)));

        if (in_array($visibility, [
            self::VISIBILITY_RESTRICTED,
            self::VISIBILITY_RESTRICTED_INTEGRITY,
            self::VISIBILITY_RESTRICTED_CULTURAL,
            self::VISIBILITY_STAFF_ONLY,
        ], true)) {
            return true;
        }

        if ($status === self::STATUS_RESTRICTED) {
            return true;
        }

        if (in_array($audience, [
            self::AUDIENCE_RESTRICTED,
            self::AUDIENCE_RESTRICTED_INTEGRITY,
            self::AUDIENCE_RESTRICTED_CULTURAL,
            self::AUDIENCE_STAFF_ONLY,
        ], true)) {
            return true;
        }

        return self::flag($media, 'restricted') || self::flag($media, 'isrestricted');
    }

    /**
     * Does the media require cultural access?
     *
     * @param stdClass|array $media Media record or array.
     * @return bool
     */
    public static function is_culturally_restricted($media): bool {
        $visibility = self::normalise_visibility(self::field($media, 'visibility', self::VISIBILITY_PRIVATE));
        $audience = self::normalise_audience(self::field($media, 'audiencesuitability',
            self::field($media, 'audience_suitability', self::AUDIENCE_GUIDED)));

        if ($visibility === self::VISIBILITY_RESTRICTED_CULTURAL || $audience === self::AUDIENCE_RESTRICTED_CULTURAL) {
            return true;
        }

        return self::flag($media, 'restrictedcultural') ||
            self::flag($media, 'isculturallyrestricted') ||
            self::flag($media, 'requiresculturalaccess');
    }

    /**
     * Does the media require restricted integrity access?
     *
     * @param stdClass|array $media Media record or array.
     * @return bool
     */
    public static function is_integrity_restricted($media): bool {
        $visibility = self::normalise_visibility(self::field($media, 'visibility', self::VISIBILITY_PRIVATE));
        $audience = self::normalise_audience(self::field($media, 'audiencesuitability',
            self::field($media, 'audience_suitability', self::AUDIENCE_GUIDED)));

        if ($visibility === self::VISIBILITY_RESTRICTED_INTEGRITY || $audience === self::AUDIENCE_RESTRICTED_INTEGRITY) {
            return true;
        }

        return self::flag($media, 'restrictedintegrity') ||
            self::flag($media, 'isintegrityrestricted') ||
            self::field($media, 'sourcecomponent', '') === 'tool_uckkintegrity' ||
            self::field($media, 'provenance', '') === 'integrity';
    }

    /**
     * Is the media soft-deleted?
     *
     * @param stdClass|array $media Media record or array.
     * @return bool
     */
    public static function is_deleted_soft($media): bool {
        return self::normalise_status(self::field($media, 'status', self::STATUS_DRAFT)) === self::STATUS_DELETED_SOFT;
    }

    /**
     * Is the media draft?
     *
     * @param stdClass|array $media Media record or array.
     * @return bool
     */
    public static function is_draft($media): bool {
        return self::normalise_status(self::field($media, 'status', self::STATUS_DRAFT)) === self::STATUS_DRAFT;
    }

    /**
     * Is the media owner the user?
     *
     * @param stdClass|array $media Media record or array.
     * @param stdClass|null $user Optional user record.
     * @return bool
     */
    public static function is_owned_by_user($media, ?stdClass $user = null): bool {
        $userid = self::get_user_id($user);

        if ($userid <= 0) {
            return false;
        }

        $owners = [
            (int)self::field($media, 'userid', 0),
            (int)self::field($media, 'ownerid', 0),
            (int)self::field($media, 'createdby', 0),
            (int)self::field($media, 'submittedby', 0),
        ];

        return in_array($userid, array_filter($owners), true);
    }

    /**
     * Normalise media status.
     *
     * @param string|null $status Raw status.
     * @return string
     */
    public static function normalise_status(?string $status): string {
        $status = clean_param((string)($status ?? ''), PARAM_ALPHANUMEXT);

        if ($status === 'deleted') {
            return self::STATUS_DELETED_SOFT;
        }

        if ($status === 'published') {
            return self::STATUS_ACTIVE;
        }

        if (!in_array($status, self::STATUSES, true)) {
            return self::STATUS_DRAFT;
        }

        return $status;
    }

    /**
     * Normalise visibility.
     *
     * @param string|null $visibility Raw visibility.
     * @return string
     */
    public static function normalise_visibility(?string $visibility): string {
        $visibility = clean_param((string)($visibility ?? ''), PARAM_ALPHANUMEXT);

        if ($visibility === self::VISIBILITY_INSTITUTIONAL) {
            return self::VISIBILITY_INSTITUTION;
        }

        if ($visibility === 'staff') {
            return self::VISIBILITY_STAFF_ONLY;
        }

        if (!in_array($visibility, self::VISIBILITIES, true)) {
            return self::VISIBILITY_PRIVATE;
        }

        return $visibility;
    }

    /**
     * Normalise audience suitability.
     *
     * @param string|null $audience Raw audience value.
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
     * Normalise file area.
     *
     * @param string $filearea Raw file area.
     * @return string
     */
    public static function normalise_filearea(string $filearea): string {
        $filearea = clean_param($filearea, PARAM_ALPHANUMEXT);

        if (!in_array($filearea, self::FILEAREAS, true)) {
            throw new coding_exception("Unknown media file area: {$filearea}");
        }

        return $filearea;
    }

    /**
     * Check whether a file area is a canonical media area.
     *
     * @param string $filearea File area.
     * @return bool
     */
    public static function is_media_filearea(string $filearea): bool {
        $filearea = clean_param($filearea, PARAM_ALPHANUMEXT);
        return in_array($filearea, self::FILEAREAS, true);
    }

    /**
     * Get the required base capability for a media file area.
     *
     * @param string $filearea File area.
     * @return string
     */
    public static function get_filearea_capability(string $filearea): string {
        $filearea = self::normalise_filearea($filearea);

        if (in_array($filearea, [
            self::FILEAREA_ORIGINAL,
            self::FILEAREA_DERIVATIVE,
            self::FILEAREA_CAPTION,
            self::FILEAREA_TRANSCRIPT,
            self::FILEAREA_ATTACHMENT,
        ], true)) {
            return self::CAP_DOWNLOAD_MEDIA;
        }

        return self::CAP_VIEW_MEDIA;
    }

    /**
     * Does media state allow ordinary viewing?
     *
     * @param stdClass|array $media Media record or array.
     * @param stdClass|null $user Optional user record.
     * @return bool
     */
    private static function passes_status_for_view($media, ?stdClass $user = null): bool {
        $status = self::normalise_status(self::field($media, 'status', self::STATUS_DRAFT));

        if ($status === self::STATUS_DELETED_SOFT) {
            return false;
        }

        if (in_array($status, [self::STATUS_DRAFT, self::STATUS_SUBMITTED], true)) {
            return self::is_owned_by_user($media, $user);
        }

        return true;
    }

    /**
     * Does visibility allow the user to view?
     *
     * @param context $context Moodle context.
     * @param stdClass|array $media Media record or array.
     * @param stdClass|null $user Optional user record.
     * @return bool
     */
    private static function passes_visibility_for_view(context $context, $media, ?stdClass $user = null): bool {
        $visibility = self::normalise_visibility(self::field($media, 'visibility', self::VISIBILITY_PRIVATE));

        if ($visibility === self::VISIBILITY_PUBLIC ||
                $visibility === self::VISIBILITY_COURSE ||
                $visibility === self::VISIBILITY_INSTITUTION ||
                $visibility === self::VISIBILITY_PROGRAM ||
                $visibility === self::VISIBILITY_COHORT ||
                $visibility === self::VISIBILITY_GROUP) {
            return true;
        }

        if ($visibility === self::VISIBILITY_PRIVATE || $visibility === self::VISIBILITY_USER) {
            return self::is_owned_by_user($media, $user) ||
                self::has_any_capability($context, [
                    self::CAP_EDIT_MEDIA,
                    self::CAP_VIEW_RESTRICTED_MEDIA,
                ], $user);
        }

        return self::passes_restricted_policy($context, $media, 'view', $user);
    }

    /**
     * Check restricted media policy.
     *
     * @param context $context Moodle context.
     * @param stdClass|array $media Media record or array.
     * @param string $operation Operation identifier.
     * @param stdClass|null $user Optional user record.
     * @return bool
     */
    private static function passes_restricted_policy(context $context, $media, string $operation,
            ?stdClass $user = null): bool {
        if (self::is_culturally_restricted($media)) {
            return self::can_view_culturally_restricted($context, $media, $user);
        }

        if (self::is_integrity_restricted($media)) {
            return self::has_any_capability($context, [
                self::CAP_VIEW_RESTRICTED_MEDIA,
                self::CAP_VIEW_RESTRICTED_ARCHIVE,
            ], $user);
        }

        if (self::is_restricted_media($media)) {
            return self::has_capability($context, self::CAP_VIEW_RESTRICTED_MEDIA, $user);
        }

        if (self::normalise_visibility(self::field($media, 'visibility', self::VISIBILITY_PRIVATE)) === self::VISIBILITY_STAFF_ONLY) {
            return self::has_any_capability($context, [
                self::CAP_EDIT_MEDIA,
                self::CAP_VIEW_RESTRICTED_MEDIA,
            ], $user);
        }

        return true;
    }

    /**
     * Check audience suitability policy.
     *
     * @param context $context Moodle context.
     * @param stdClass|array $media Media record or array.
     * @param string $operation Operation identifier.
     * @param stdClass|null $user Optional user record.
     * @return bool
     */
    private static function passes_audience_policy(context $context, $media, string $operation,
            ?stdClass $user = null): bool {
        $audience = self::normalise_audience(self::field($media, 'audiencesuitability',
            self::field($media, 'audience_suitability', self::AUDIENCE_GUIDED)));

        if (in_array($audience, [self::AUDIENCE_GENERAL, self::AUDIENCE_GUIDED, self::AUDIENCE_MATURE], true)) {
            return true;
        }

        if ($audience === self::AUDIENCE_RESTRICTED_CULTURAL) {
            return self::can_view_culturally_restricted($context, $media, $user);
        }

        if ($audience === self::AUDIENCE_RESTRICTED_INTEGRITY) {
            return self::has_any_capability($context, [
                self::CAP_VIEW_RESTRICTED_MEDIA,
                self::CAP_VIEW_RESTRICTED_ARCHIVE,
            ], $user);
        }

        if ($audience === self::AUDIENCE_STAFF_ONLY) {
            return self::has_any_capability($context, [
                self::CAP_EDIT_MEDIA,
                self::CAP_VIEW_RESTRICTED_MEDIA,
            ], $user);
        }

        return self::has_capability($context, self::CAP_VIEW_RESTRICTED_MEDIA, $user);
    }

    /**
     * Check content advisory policy.
     *
     * If content_policy exists and exposes can_access_media(), defer to it.
     * If not, apply conservative fail-closed behavior for marked sensitive
     * records.
     *
     * @param context $context Moodle context.
     * @param stdClass|array $media Media record or array.
     * @param string $operation Operation identifier.
     * @param stdClass|null $user Optional user record.
     * @return bool
     */
    private static function passes_content_policy(context $context, $media, string $operation,
            ?stdClass $user = null): bool {
        $contentpolicy = '\\mod_uckkarchive\\local\\content_policy';

        if (class_exists($contentpolicy) && method_exists($contentpolicy, 'can_access_media')) {
            return (bool)$contentpolicy::can_access_media($context, $media, $operation, $user);
        }

        if (self::flag($media, 'requirescontentreview') ||
                self::flag($media, 'hasrestrictedadvisory') ||
                self::flag($media, 'hasculturalprotocol') ||
                self::flag($media, 'requiresguidedaccess')) {
            return self::has_any_capability($context, [
                self::CAP_VIEW_ADVISORIES,
                self::CAP_REVIEW_ADVISORIES,
                self::CAP_VIEW_RESTRICTED_MEDIA,
                self::CAP_VIEW_CULTURALLY_RESTRICTED,
            ], $user);
        }

        $reviewstate = clean_param((string)self::field($media, 'contentreviewstate', ''), PARAM_ALPHANUMEXT);

        if (in_array($reviewstate, ['pending_review', 'draft', 'contested'], true)) {
            return self::has_any_capability($context, [
                self::CAP_REVIEW_ADVISORIES,
                self::CAP_VIEW_RESTRICTED_MEDIA,
            ], $user);
        }

        return true;
    }

    /**
     * Check media version policy.
     *
     * @param context $context Moodle context.
     * @param stdClass|array $media Media record or array.
     * @param stdClass|array $version Version record or array.
     * @param stdClass|null $user Optional user record.
     * @return bool
     */
    private static function passes_version_policy(context $context, $media, $version, ?stdClass $user = null): bool {
        $status = self::normalise_status(self::field($version, 'status',
            self::field($media, 'status', self::STATUS_DRAFT)));

        if ($status === self::STATUS_DELETED_SOFT) {
            return false;
        }

        if (self::flag($version, 'restricted') || self::flag($version, 'redacted')) {
            return self::can_view_restricted_media($context, $media, $user);
        }

        return true;
    }

    /**
     * Is this media locked for an operation by retention or redaction?
     *
     * @param stdClass|array $media Media record or array.
     * @param string $operation Operation identifier.
     * @return bool
     */
    private static function is_locked_by_retention_or_redaction($media, string $operation): bool {
        if (self::flag($media, 'locked')) {
            return true;
        }

        if (self::flag($media, 'redacted') && in_array($operation, ['export', 'download', 'original'], true)) {
            return true;
        }

        $retention = clean_param((string)self::field($media, 'retentionclass',
            self::field($media, 'retention_class', '')), PARAM_ALPHANUMEXT);

        if (in_array($retention, ['restricted_integrity', 'institutional_memory'], true) &&
                in_array($operation, ['delete', 'purge'], true)) {
            return true;
        }

        return false;
    }

    /**
     * Wrapper around Moodle has_capability.
     *
     * @param context $context Moodle context.
     * @param string $capability Capability.
     * @param stdClass|null $user Optional user.
     * @return bool
     */
    private static function has_capability(context $context, string $capability, ?stdClass $user = null): bool {
        $userid = self::get_user_id($user);
        return has_capability($capability, $context, $userid > 0 ? $userid : null);
    }

    /**
     * Wrapper around Moodle require_capability.
     *
     * @param context $context Moodle context.
     * @param string $capability Capability.
     * @param stdClass|null $user Optional user.
     */
    private static function require_capability(context $context, string $capability, ?stdClass $user = null): void {
        $userid = self::get_user_id($user);
        require_capability($capability, $context, $userid > 0 ? $userid : null);
    }

    /**
     * Does the user have at least one of the capabilities?
     *
     * @param context $context Moodle context.
     * @param string[] $capabilities Capabilities.
     * @param stdClass|null $user Optional user.
     * @return bool
     */
    private static function has_any_capability(context $context, array $capabilities, ?stdClass $user = null): bool {
        foreach ($capabilities as $capability) {
            if (self::has_capability($context, $capability, $user)) {
                return true;
            }
        }

        return false;
    }

    /**
     * Require at least one capability.
     *
     * @param context $context Moodle context.
     * @param string[] $capabilities Capabilities.
     * @param stdClass|null $user Optional user.
     */
    private static function require_any_capability(context $context, array $capabilities, ?stdClass $user = null): void {
        foreach ($capabilities as $capability) {
            if (self::has_capability($context, $capability, $user)) {
                return;
            }
        }

        self::throw_policy_exception($context, reset($capabilities) ?: self::CAP_VIEW_ACTIVITY, 'Missing media capability.');
    }

    /**
     * Extract user id from optional user/current user.
     *
     * @param stdClass|null $user Optional user.
     * @return int
     */
    private static function get_user_id(?stdClass $user = null): int {
        global $USER;

        if ($user !== null && !empty($user->id)) {
            return (int)$user->id;
        }

        return (int)($USER->id ?? 0);
    }

    /**
     * Get a field from a record/array using multiple shape conventions.
     *
     * @param stdClass|array|null $record Record or array.
     * @param string $name Field name.
     * @param mixed $default Default value.
     * @return mixed
     */
    private static function field($record, string $name, $default = null) {
        if ($record === null) {
            return $default;
        }

        if (is_array($record)) {
            return array_key_exists($name, $record) ? $record[$name] : $default;
        }

        if ($record instanceof stdClass) {
            return property_exists($record, $name) ? $record->{$name} : $default;
        }

        return $default;
    }

    /**
     * Read a boolean-ish flag from a record.
     *
     * @param stdClass|array|null $record Record or array.
     * @param string $name Field name.
     * @return bool
     */
    private static function flag($record, string $name): bool {
        $value = self::field($record, $name, false);

        if (is_bool($value)) {
            return $value;
        }

        if (is_numeric($value)) {
            return (int)$value === 1;
        }

        if (is_string($value)) {
            return in_array(strtolower($value), ['1', 'true', 'yes', 'on'], true);
        }

        return false;
    }

    /**
     * Throw a consistent policy exception.
     *
     * @param context $context Moodle context.
     * @param string $capability Capability name.
     * @param string $debug Debug message.
     * @throws moodle_exception
     */
    private static function throw_policy_exception(context $context, string $capability, string $debug): void {
        throw new moodle_exception('nopermissions', 'error', '', $capability, $debug);
    }
}
