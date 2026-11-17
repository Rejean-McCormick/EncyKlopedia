<?php
// This file is part of Moodle - https://moodle.org/
//
// Moodle is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// any later version.
//
// Moodle is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with Moodle. If not, see <https://www.gnu.org/licenses/>.

declare(strict_types=1);

namespace mod_uckkarchive\local;

defined('MOODLE_INTERNAL') || die();

global $CFG;
require_once($CFG->dirroot . '/repository/lib.php');

/**
 * Central registry for all File API areas owned by mod_uckkarchive.
 *
 * This class is the single source of truth for archive, media, content
 * advisory, external-work, export, generated, and sensitive file areas.
 *
 * Controllers, services, pluginfile handling, privacy provider, backup,
 * restore, and tests should use this registry instead of hard-coding
 * file-area names.
 *
 * This class does not grant access. Runtime access remains the responsibility
 * of archive_policy, media_policy, content_policy, and the pluginfile handler.
 *
 * @package    mod_uckkarchive
 * @copyright  2026 UCKK
 * @license    https://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later
 */
final class file_area_registry {
    /** Moodle File API component. */
    public const COMPONENT = 'mod_uckkarchive';

    /** Activity introduction files. */
    public const INTRO = 'intro';

    /** Rich editor files attached to an archive item body/content. */
    public const ITEM_CONTENT = 'item_content';

    /** Files attached to an archive item public summary. */
    public const ITEM_PUBLICSUMMARY = 'item_publicsummary';

    /** General files attached to an archive item. */
    public const ITEM_FILES = 'item_files';

    /** Proof/evidence files. */
    public const PROOF_FILES = 'proof_files';

    /** Assembly decision attachments preserved by the archive. */
    public const DECISION_ATTACHMENTS = 'decision_attachments';

    /** Assembly minutes or institutional memory files. */
    public const MINUTES_FILES = 'minutes_files';

    /** Kristal-related files. */
    public const KRISTAL_FILES = 'kristal_files';

    /** Portfolio-linked archive files. */
    public const PORTFOLIO_FILES = 'portfolio_files';

    /** Integrity-related archive export files. */
    public const INTEGRITY_EXPORTS = 'integrity_exports';

    /** Provenance source packages and supporting files. */
    public const PROVENANCE_FILES = 'provenance_files';

    /** Validation supporting files. */
    public const VALIDATION_FILES = 'validation_files';

    /** Revision supporting files. */
    public const REVISION_FILES = 'revision_files';

    /** Generated archive/media export package. */
    public const EXPORT_PACKAGE = 'export_package';

    /** Generated archive/media export manifest. */
    public const EXPORT_MANIFEST = 'export_manifest';

    /** Original media file. */
    public const MEDIA_ORIGINAL = 'media_original';

    /** Preview media file. */
    public const MEDIA_PREVIEW = 'media_preview';

    /** Media thumbnail file. */
    public const MEDIA_THUMBNAIL = 'media_thumbnail';

    /** Generated media derivative file. */
    public const MEDIA_DERIVATIVE = 'media_derivative';

    /** Media caption file. */
    public const MEDIA_CAPTION = 'media_caption';

    /** Media transcript file. */
    public const MEDIA_TRANSCRIPT = 'media_transcript';

    /** Additional media attachment file. */
    public const MEDIA_ATTACHMENT = 'media_attachment';

    /** Content review supporting files. */
    public const CONTENT_REVIEW_FILES = 'content_review_files';

    /** External work reference supporting files. */
    public const EXTERNAL_WORK_REFERENCE_FILES = 'external_work_reference_files';

    /** Cultural protocol supporting files. */
    public const CULTURAL_PROTOCOL_FILES = 'cultural_protocol_files';

    /**
     * Constructor is private because this is a static registry.
     */
    private function __construct() {
    }

    /**
     * Return the Moodle File API component name.
     *
     * @return string
     */
    public static function get_component(): string {
        return self::COMPONENT;
    }

    /**
     * Return all archive file areas.
     *
     * @return string[]
     */
    public static function get_archive_fileareas(): array {
        return [
            self::INTRO,
            self::ITEM_CONTENT,
            self::ITEM_PUBLICSUMMARY,
            self::ITEM_FILES,
            self::PROOF_FILES,
            self::DECISION_ATTACHMENTS,
            self::MINUTES_FILES,
            self::KRISTAL_FILES,
            self::PORTFOLIO_FILES,
            self::INTEGRITY_EXPORTS,
            self::PROVENANCE_FILES,
            self::VALIDATION_FILES,
            self::REVISION_FILES,
        ];
    }

    /**
     * Return all media-library file areas.
     *
     * @return string[]
     */
    public static function get_media_fileareas(): array {
        return [
            self::MEDIA_ORIGINAL,
            self::MEDIA_PREVIEW,
            self::MEDIA_THUMBNAIL,
            self::MEDIA_DERIVATIVE,
            self::MEDIA_CAPTION,
            self::MEDIA_TRANSCRIPT,
            self::MEDIA_ATTACHMENT,
        ];
    }

    /**
     * Return all content-advisory and external-work file areas.
     *
     * @return string[]
     */
    public static function get_content_advisory_fileareas(): array {
        return [
            self::CONTENT_REVIEW_FILES,
            self::EXTERNAL_WORK_REFERENCE_FILES,
            self::CULTURAL_PROTOCOL_FILES,
        ];
    }

    /**
     * Return all export file areas.
     *
     * @return string[]
     */
    public static function get_export_fileareas(): array {
        return [
            self::EXPORT_PACKAGE,
            self::EXPORT_MANIFEST,
            self::INTEGRITY_EXPORTS,
        ];
    }

    /**
     * Return every canonical file area owned by this plugin.
     *
     * @return string[]
     */
    public static function get_all_fileareas(): array {
        return self::unique_fileareas(array_merge(
            self::get_archive_fileareas(),
            self::get_media_fileareas(),
            self::get_content_advisory_fileareas(),
            self::get_export_fileareas()
        ));
    }

    /**
     * Return file areas normally served through pluginfile.php.
     *
     * This list includes all canonical areas. Access must still be checked by
     * the caller or pluginfile handler.
     *
     * @return string[]
     */
    public static function get_pluginfile_fileareas(): array {
        return self::get_all_fileareas();
    }

    /**
     * Return file areas that contain generated files.
     *
     * @return string[]
     */
    public static function get_generated_fileareas(): array {
        return [
            self::EXPORT_PACKAGE,
            self::EXPORT_MANIFEST,
            self::MEDIA_PREVIEW,
            self::MEDIA_THUMBNAIL,
            self::MEDIA_DERIVATIVE,
        ];
    }

    /**
     * Return media file areas that contain generated files.
     *
     * @return string[]
     */
    public static function get_generated_media_fileareas(): array {
        return [
            self::MEDIA_PREVIEW,
            self::MEDIA_THUMBNAIL,
            self::MEDIA_DERIVATIVE,
        ];
    }

    /**
     * Return file areas that commonly require stricter privacy/restriction checks.
     *
     * This does not mean all files in these areas are always hidden. Runtime
     * access must still be decided by archive_policy, media_policy, and
     * content_policy.
     *
     * @return string[]
     */
    public static function get_sensitive_fileareas(): array {
        return [
            self::PROOF_FILES,
            self::DECISION_ATTACHMENTS,
            self::MINUTES_FILES,
            self::INTEGRITY_EXPORTS,
            self::PROVENANCE_FILES,
            self::VALIDATION_FILES,
            self::REVISION_FILES,
            self::EXPORT_PACKAGE,
            self::EXPORT_MANIFEST,
            self::MEDIA_ORIGINAL,
            self::MEDIA_ATTACHMENT,
            self::MEDIA_TRANSCRIPT,
            self::CONTENT_REVIEW_FILES,
            self::EXTERNAL_WORK_REFERENCE_FILES,
            self::CULTURAL_PROTOCOL_FILES,
        ];
    }

    /**
     * Return file areas that may be served to users when policy checks pass.
     *
     * Generated private/internal areas may still be excluded by policy.
     *
     * @return string[]
     */
    public static function get_downloadable_fileareas(): array {
        return [
            self::ITEM_CONTENT,
            self::ITEM_PUBLICSUMMARY,
            self::ITEM_FILES,
            self::PROOF_FILES,
            self::DECISION_ATTACHMENTS,
            self::MINUTES_FILES,
            self::KRISTAL_FILES,
            self::PORTFOLIO_FILES,
            self::PROVENANCE_FILES,
            self::VALIDATION_FILES,
            self::REVISION_FILES,
            self::EXPORT_PACKAGE,
            self::MEDIA_ORIGINAL,
            self::MEDIA_PREVIEW,
            self::MEDIA_THUMBNAIL,
            self::MEDIA_DERIVATIVE,
            self::MEDIA_CAPTION,
            self::MEDIA_TRANSCRIPT,
            self::MEDIA_ATTACHMENT,
            self::CONTENT_REVIEW_FILES,
            self::EXTERNAL_WORK_REFERENCE_FILES,
            self::CULTURAL_PROTOCOL_FILES,
        ];
    }

    /**
     * Return file areas that usually support draft upload/edit forms.
     *
     * @return string[]
     */
    public static function get_draftable_fileareas(): array {
        return [
            self::ITEM_CONTENT,
            self::ITEM_PUBLICSUMMARY,
            self::ITEM_FILES,
            self::PROOF_FILES,
            self::DECISION_ATTACHMENTS,
            self::MINUTES_FILES,
            self::KRISTAL_FILES,
            self::PORTFOLIO_FILES,
            self::PROVENANCE_FILES,
            self::VALIDATION_FILES,
            self::REVISION_FILES,
            self::MEDIA_ORIGINAL,
            self::MEDIA_CAPTION,
            self::MEDIA_TRANSCRIPT,
            self::MEDIA_ATTACHMENT,
            self::CONTENT_REVIEW_FILES,
            self::EXTERNAL_WORK_REFERENCE_FILES,
            self::CULTURAL_PROTOCOL_FILES,
        ];
    }

    /**
     * Return file areas that should be included in backup/restore declarations.
     *
     * @return string[]
     */
    public static function get_backup_fileareas(): array {
        return self::get_all_fileareas();
    }

    /**
     * Return file areas that should be declared in the privacy provider.
     *
     * @return string[]
     */
    public static function get_privacy_fileareas(): array {
        return self::get_all_fileareas();
    }

    /**
     * Return the group name for a file area.
     *
     * @param string $filearea File area.
     * @return string|null One of archive, media, content_advisory, export, or null.
     */
    public static function get_group(string $filearea): ?string {
        $filearea = self::clean_filearea($filearea);

        if (self::is_archive_filearea($filearea)) {
            return 'archive';
        }

        if (self::is_media_filearea($filearea)) {
            return 'media';
        }

        if (self::is_content_advisory_filearea($filearea)) {
            return 'content_advisory';
        }

        if (self::is_export_filearea($filearea)) {
            return 'export';
        }

        return null;
    }

    /**
     * Return canonical metadata for one file area.
     *
     * @param string $filearea File area.
     * @return array<string, mixed>|null
     */
    public static function get_filearea_metadata(string $filearea): ?array {
        $filearea = self::normalize_filearea($filearea);

        if ($filearea === null) {
            return null;
        }

        return [
            'component' => self::COMPONENT,
            'filearea' => $filearea,
            'group' => self::get_group($filearea),
            'generated' => self::is_generated_filearea($filearea),
            'generatedmedia' => self::is_generated_media_filearea($filearea),
            'export' => self::is_export_filearea($filearea),
            'sensitive' => self::is_sensitive_filearea($filearea),
            'downloadable' => self::is_downloadable_filearea($filearea),
            'draftable' => self::is_draftable_filearea($filearea),
            'backup' => self::is_backup_filearea($filearea),
            'privacy' => self::is_privacy_filearea($filearea),
        ];
    }

    /**
     * Return canonical file-area metadata for documentation, diagnostics, and tests.
     *
     * @return array<string, array<string, mixed>>
     */
    public static function get_metadata(): array {
        $metadata = [];

        foreach (self::get_all_fileareas() as $filearea) {
            $metadata[$filearea] = self::get_filearea_metadata($filearea);
        }

        return $metadata;
    }

    /**
     * Return canonical file areas grouped by functional domain.
     *
     * @return array<string, string[]>
     */
    public static function get_grouped_fileareas(): array {
        return [
            'archive' => self::get_archive_fileareas(),
            'media' => self::get_media_fileareas(),
            'content_advisory' => self::get_content_advisory_fileareas(),
            'export' => self::get_export_fileareas(),
        ];
    }

    /**
     * Return backup/restore mapping metadata.
     *
     * Backup code can use this method to avoid drifting from the canonical
     * file-area registry.
     *
     * @return array<int, array<string, mixed>>
     */
    public static function get_backup_filearea_metadata(): array {
        $rows = [];

        foreach (self::get_backup_fileareas() as $filearea) {
            $rows[] = [
                'component' => self::COMPONENT,
                'filearea' => $filearea,
                'itemid' => self::uses_itemid($filearea),
            ];
        }

        return $rows;
    }

    /**
     * Return whether this file area normally uses itemid-scoped files.
     *
     * The Moodle intro area is instance-scoped and normally uses itemid 0.
     * Most other plugin file areas are record-scoped and use the owning
     * record id as itemid.
     *
     * @param string $filearea File area.
     * @return bool
     */
    public static function uses_itemid(string $filearea): bool {
        $filearea = self::normalize_filearea($filearea);

        if ($filearea === null) {
            return false;
        }

        return $filearea !== self::INTRO;
    }

    /**
     * Check whether a file area is canonical for this plugin.
     *
     * @param string $filearea File area.
     * @return bool
     */
    public static function is_valid_filearea(string $filearea): bool {
        return in_array(self::clean_filearea($filearea), self::get_all_fileareas(), true);
    }

    /**
     * Check whether a file area belongs to the archive group.
     *
     * @param string $filearea File area.
     * @return bool
     */
    public static function is_archive_filearea(string $filearea): bool {
        return in_array(self::clean_filearea($filearea), self::get_archive_fileareas(), true);
    }

    /**
     * Check whether a file area belongs to the media group.
     *
     * @param string $filearea File area.
     * @return bool
     */
    public static function is_media_filearea(string $filearea): bool {
        return in_array(self::clean_filearea($filearea), self::get_media_fileareas(), true);
    }

    /**
     * Check whether a file area belongs to the content advisory group.
     *
     * @param string $filearea File area.
     * @return bool
     */
    public static function is_content_advisory_filearea(string $filearea): bool {
        return in_array(self::clean_filearea($filearea), self::get_content_advisory_fileareas(), true);
    }

    /**
     * Check whether a file area is generated.
     *
     * @param string $filearea File area.
     * @return bool
     */
    public static function is_generated_filearea(string $filearea): bool {
        return in_array(self::clean_filearea($filearea), self::get_generated_fileareas(), true);
    }

    /**
     * Check whether a media file area is generated.
     *
     * @param string $filearea File area.
     * @return bool
     */
    public static function is_generated_media_filearea(string $filearea): bool {
        return in_array(self::clean_filearea($filearea), self::get_generated_media_fileareas(), true);
    }

    /**
     * Check whether a file area is export-related.
     *
     * @param string $filearea File area.
     * @return bool
     */
    public static function is_export_filearea(string $filearea): bool {
        return in_array(self::clean_filearea($filearea), self::get_export_fileareas(), true);
    }

    /**
     * Check whether a file area is commonly sensitive.
     *
     * @param string $filearea File area.
     * @return bool
     */
    public static function is_sensitive_filearea(string $filearea): bool {
        return in_array(self::clean_filearea($filearea), self::get_sensitive_fileareas(), true);
    }

    /**
     * Check whether a file area may be served to users when policy checks pass.
     *
     * @param string $filearea File area.
     * @return bool
     */
    public static function is_downloadable_filearea(string $filearea): bool {
        return in_array(self::clean_filearea($filearea), self::get_downloadable_fileareas(), true);
    }

    /**
     * Check whether a file area supports draft upload/edit forms.
     *
     * @param string $filearea File area.
     * @return bool
     */
    public static function is_draftable_filearea(string $filearea): bool {
        return in_array(self::clean_filearea($filearea), self::get_draftable_fileareas(), true);
    }

    /**
     * Check whether a file area belongs in backup/restore handling.
     *
     * @param string $filearea File area.
     * @return bool
     */
    public static function is_backup_filearea(string $filearea): bool {
        return in_array(self::clean_filearea($filearea), self::get_backup_fileareas(), true);
    }

    /**
     * Check whether a file area belongs in privacy-provider handling.
     *
     * @param string $filearea File area.
     * @return bool
     */
    public static function is_privacy_filearea(string $filearea): bool {
        return in_array(self::clean_filearea($filearea), self::get_privacy_fileareas(), true);
    }

    /**
     * Check whether a file area may be served by pluginfile.php.
     *
     * @param string $filearea File area.
     * @return bool
     */
    public static function is_pluginfile_filearea(string $filearea): bool {
        return in_array(self::clean_filearea($filearea), self::get_pluginfile_fileareas(), true);
    }

    /**
     * Return true when the provided component belongs to this plugin.
     *
     * @param string $component Moodle File API component.
     * @return bool
     */
    public static function is_component(string $component): bool {
        return self::clean_component($component) === self::COMPONENT;
    }

    /**
     * Validate component and file area together.
     *
     * @param string $component Moodle File API component.
     * @param string $filearea File area.
     * @return bool
     */
    public static function is_valid_component_filearea(string $component, string $filearea): bool {
        return self::is_component($component) && self::is_valid_filearea($filearea);
    }

    /**
     * Return legacy/non-canonical file areas that may appear in older installs.
     *
     * These names are not part of the target architecture. They are exposed
     * only so upgrade, restore, and compatibility code can safely migrate,
     * normalize, or reject them.
     *
     * @return array<string, string> Map of legacy file area => canonical file area.
     */
    public static function get_legacy_filearea_map(): array {
        return [
            'public_summary' => self::ITEM_PUBLICSUMMARY,
            'item_attachment' => self::ITEM_FILES,
            'item_attachments' => self::ITEM_FILES,
            'archive_attachment' => self::ITEM_FILES,
            'archive_attachments' => self::ITEM_FILES,
            'archiveitemfiles' => self::ITEM_FILES,
            'itemfiles' => self::ITEM_FILES,

            'proof_attachment' => self::PROOF_FILES,
            'proof_attachments' => self::PROOF_FILES,
            'evidence_package' => self::PROOF_FILES,

            'decision_files' => self::DECISION_ATTACHMENTS,
            'decision_attachment' => self::DECISION_ATTACHMENTS,
            'assembly_decision_files' => self::DECISION_ATTACHMENTS,

            'minutes_attachment' => self::MINUTES_FILES,
            'minutes_attachments' => self::MINUTES_FILES,

            'kristal_attachment' => self::KRISTAL_FILES,
            'kristal_attachments' => self::KRISTAL_FILES,

            'portfolio_attachment' => self::PORTFOLIO_FILES,
            'portfolio_attachments' => self::PORTFOLIO_FILES,

            'provenance_attachment' => self::PROVENANCE_FILES,
            'provenance_attachments' => self::PROVENANCE_FILES,
            'source_package' => self::PROVENANCE_FILES,

            'validation_attachment' => self::VALIDATION_FILES,
            'validation_attachments' => self::VALIDATION_FILES,

            'revision_attachment' => self::REVISION_FILES,
            'revision_attachments' => self::REVISION_FILES,

            'integrity_export' => self::INTEGRITY_EXPORTS,
            'integrity_exports' => self::INTEGRITY_EXPORTS,

            'export_file' => self::EXPORT_PACKAGE,
            'export_files' => self::EXPORT_PACKAGE,
            'export_packages' => self::EXPORT_PACKAGE,
            'archive_export_package' => self::EXPORT_PACKAGE,
            'public_package' => self::EXPORT_PACKAGE,
            'restricted_package' => self::EXPORT_PACKAGE,

            'manifest_file' => self::EXPORT_MANIFEST,
            'manifest_files' => self::EXPORT_MANIFEST,
            'mbz_manifest' => self::EXPORT_MANIFEST,

            'media_file' => self::MEDIA_ORIGINAL,
            'media_files' => self::MEDIA_ORIGINAL,
            'mediafiles' => self::MEDIA_ORIGINAL,
            'media_original_file' => self::MEDIA_ORIGINAL,

            'media_previews' => self::MEDIA_PREVIEW,
            'media_preview_file' => self::MEDIA_PREVIEW,

            'media_thumbnails' => self::MEDIA_THUMBNAIL,
            'media_thumbnail_file' => self::MEDIA_THUMBNAIL,

            'media_derivatives' => self::MEDIA_DERIVATIVE,
            'media_derivative_file' => self::MEDIA_DERIVATIVE,

            'caption_file' => self::MEDIA_CAPTION,
            'caption_files' => self::MEDIA_CAPTION,
            'media_caption_file' => self::MEDIA_CAPTION,

            'transcript_file' => self::MEDIA_TRANSCRIPT,
            'transcript_files' => self::MEDIA_TRANSCRIPT,
            'media_transcript_file' => self::MEDIA_TRANSCRIPT,

            'media_attachment_file' => self::MEDIA_ATTACHMENT,
            'media_attachments' => self::MEDIA_ATTACHMENT,

            'review_file' => self::CONTENT_REVIEW_FILES,
            'review_files' => self::CONTENT_REVIEW_FILES,
            'contentreviewfiles' => self::CONTENT_REVIEW_FILES,
            'content_review_file' => self::CONTENT_REVIEW_FILES,

            'external_reference_file' => self::EXTERNAL_WORK_REFERENCE_FILES,
            'external_reference_files' => self::EXTERNAL_WORK_REFERENCE_FILES,
            'external_work_file' => self::EXTERNAL_WORK_REFERENCE_FILES,
            'external_work_files' => self::EXTERNAL_WORK_REFERENCE_FILES,

            'cultural_file' => self::CULTURAL_PROTOCOL_FILES,
            'cultural_files' => self::CULTURAL_PROTOCOL_FILES,
            'cultural_protocol_file' => self::CULTURAL_PROTOCOL_FILES,
        ];
    }

    /**
     * Resolve a canonical or legacy file area to its canonical target.
     *
     * @param string $filearea File area.
     * @return string|null Canonical file area or null when unknown.
     */
    public static function normalize_filearea(string $filearea): ?string {
        $filearea = self::clean_filearea($filearea);

        if (self::is_valid_filearea($filearea)) {
            return $filearea;
        }

        $legacy = self::get_legacy_filearea_map();

        return $legacy[$filearea] ?? null;
    }

    /**
     * British-English alias for normalize_filearea().
     *
     * @param string $filearea File area.
     * @return string|null Canonical file area or null when unknown.
     */
    public static function normalise_filearea(string $filearea): ?string {
        return self::normalize_filearea($filearea);
    }

    /**
     * Require and return a canonical file area.
     *
     * @param string $filearea File area.
     * @return string Canonical file area.
     * @throws \invalid_parameter_exception
     */
    public static function require_filearea(string $filearea): string {
        $canonical = self::normalize_filearea($filearea);

        if ($canonical === null) {
            throw new \invalid_parameter_exception('Unknown mod_uckkarchive file area: ' . $filearea);
        }

        return $canonical;
    }

    /**
     * Check whether a file area is a known legacy/non-canonical name.
     *
     * @param string $filearea File area.
     * @return bool
     */
    public static function is_legacy_filearea(string $filearea): bool {
        return array_key_exists(self::clean_filearea($filearea), self::get_legacy_filearea_map());
    }

    /**
     * Return whether a legacy file area maps to a specific canonical target.
     *
     * @param string $legacyfilearea Legacy file area.
     * @param string $canonicalfilearea Canonical file area.
     * @return bool
     */
    public static function legacy_maps_to(string $legacyfilearea, string $canonicalfilearea): bool {
        $legacyfilearea = self::clean_filearea($legacyfilearea);
        $canonicalfilearea = self::clean_filearea($canonicalfilearea);

        return (self::get_legacy_filearea_map()[$legacyfilearea] ?? null) === $canonicalfilearea;
    }

    /**
     * Return File API options for a canonical file area.
     *
     * These are default UI/form options only. Services and forms may further
     * restrict size, accepted types, or max files.
     *
     * @param string $filearea File area.
     * @param array<string, mixed> $overrides Option overrides.
     * @return array<string, mixed>
     */
    public static function get_file_options(string $filearea, array $overrides = []): array {
        $filearea = self::require_filearea($filearea);

        $options = [
            'subdirs' => self::allows_subdirs($filearea),
            'maxbytes' => 0,
            'maxfiles' => self::default_maxfiles($filearea),
            'accepted_types' => self::default_accepted_types($filearea),
            'return_types' => \FILE_INTERNAL,
        ];

        return array_merge($options, $overrides);
    }

    /**
     * Return whether an area allows subdirectories.
     *
     * @param string $filearea File area.
     * @return bool
     */
    public static function allows_subdirs(string $filearea): bool {
        $filearea = self::require_filearea($filearea);

        return in_array($filearea, [
            self::ITEM_FILES,
            self::PROOF_FILES,
            self::DECISION_ATTACHMENTS,
            self::MINUTES_FILES,
            self::KRISTAL_FILES,
            self::PORTFOLIO_FILES,
            self::PROVENANCE_FILES,
            self::VALIDATION_FILES,
            self::REVISION_FILES,
            self::EXPORT_PACKAGE,
            self::MEDIA_ATTACHMENT,
            self::CONTENT_REVIEW_FILES,
            self::EXTERNAL_WORK_REFERENCE_FILES,
            self::CULTURAL_PROTOCOL_FILES,
        ], true);
    }

    /**
     * Return default maxfiles for an area.
     *
     * @param string $filearea File area.
     * @return int
     */
    public static function default_maxfiles(string $filearea): int {
        $filearea = self::require_filearea($filearea);

        return match ($filearea) {
            self::INTRO,
            self::ITEM_CONTENT,
            self::ITEM_PUBLICSUMMARY,
            self::MEDIA_ORIGINAL,
            self::MEDIA_PREVIEW,
            self::MEDIA_THUMBNAIL,
            self::EXPORT_MANIFEST => 1,
            default => -1,
        };
    }

    /**
     * Return default accepted file types for an area.
     *
     * @param string $filearea File area.
     * @return string[]|string
     */
    public static function default_accepted_types(string $filearea): array|string {
        $filearea = self::require_filearea($filearea);

        return match ($filearea) {
            self::MEDIA_THUMBNAIL => ['image'],
            self::MEDIA_CAPTION => ['.vtt', '.srt', '.sbv', '.sub', '.ttml', '.dfxp'],
            self::MEDIA_TRANSCRIPT => ['.txt', '.md', '.pdf', '.doc', '.docx', '.odt'],
            self::EXPORT_MANIFEST => ['.json'],
            self::EXPORT_PACKAGE,
            self::INTEGRITY_EXPORTS => ['.zip', '.json', '.csv', '.pdf', '.html'],
            default => '*',
        };
    }

    /**
     * Return unique normalized file areas in stable order.
     *
     * @param string[] $fileareas File areas.
     * @return string[]
     */
    private static function unique_fileareas(array $fileareas): array {
        $seen = [];
        $result = [];

        foreach ($fileareas as $filearea) {
            $filearea = self::clean_filearea((string)$filearea);
            if ($filearea === '' || isset($seen[$filearea])) {
                continue;
            }

            $seen[$filearea] = true;
            $result[] = $filearea;
        }

        return $result;
    }

    /**
     * Clean a component name.
     *
     * @param string $component Component name.
     * @return string
     */
    private static function clean_component(string $component): string {
        return clean_param(trim($component), PARAM_COMPONENT);
    }

    /**
     * Clean a file-area name.
     *
     * @param string $filearea File area.
     * @return string
     */
    private static function clean_filearea(string $filearea): string {
        return clean_param(trim($filearea), PARAM_AREA);
    }
}
