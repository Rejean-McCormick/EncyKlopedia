<?php
// This file is part of Moodle - https://moodle.org/.
//
// Moodle is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// any later version.
//
// Moodle is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with Moodle.  If not, see <http://www.gnu.org/licenses/>.

/**
 * External service for adding media to UCKK Archive.
 *
 * @package    mod_uckkarchive
 * @copyright  2026 UCKK
 * @license    http://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later
 */

namespace mod_uckkarchive\external;

use context_module;
use external_api;
use external_function_parameters;
use external_multiple_structure;
use external_single_structure;
use external_value;
use invalid_parameter_exception;
use mod_uckkarchive\local\media;
use mod_uckkarchive\local\media_library_scope;

defined('MOODLE_INTERNAL') || die();

require_once($CFG->libdir . '/externallib.php');

/**
 * Add media external service.
 *
 * This service creates a first-class archive media record. It does not expose
 * unrestricted file access. File movement, derivative generation, advisory
 * handling, and export behavior remain governed by local policy classes.
 */
final class add_media extends external_api {
    /**
     * Describe service parameters.
     *
     * @return external_function_parameters
     */
    public static function execute_parameters(): external_function_parameters {
        return new external_function_parameters([
            'cmid' => new external_value(PARAM_INT, 'Course module id for the UCKK Archive instance.'),
            'title' => new external_value(PARAM_TEXT, 'Media title.'),
            'description' => new external_value(PARAM_RAW, 'Media description.', VALUE_DEFAULT, ''),
            'mediatype' => new external_value(PARAM_ALPHANUMEXT, 'Media type: image, video, audio, document, text, dataset, external_reference, other.', VALUE_DEFAULT, 'other'),
            'sourcetype' => new external_value(PARAM_ALPHANUMEXT, 'Source type.', VALUE_DEFAULT, 'submitted_to_uckk'),
            'sourceownership' => new external_value(PARAM_ALPHANUMEXT, 'Source ownership.', VALUE_DEFAULT, 'unknown_source'),
            'visibility' => new external_value(PARAM_ALPHANUMEXT, 'Visibility.', VALUE_DEFAULT, 'course'),
            'status' => new external_value(PARAM_ALPHANUMEXT, 'Media lifecycle status.', VALUE_DEFAULT, 'draft'),
            'audiencesuitability' => new external_value(PARAM_ALPHANUMEXT, 'Audience suitability.', VALUE_DEFAULT, 'guided'),
            'draftitemid' => new external_value(PARAM_INT, 'Draft file item id containing uploaded files.', VALUE_DEFAULT, 0),
            'collectionid' => new external_value(PARAM_INT, 'Optional collection id to add the media to.', VALUE_DEFAULT, 0),
            'metadata' => new external_single_structure([
                'creator' => new external_value(PARAM_TEXT, 'Creator or author.', VALUE_DEFAULT, ''),
                'rights' => new external_value(PARAM_TEXT, 'Rights statement.', VALUE_DEFAULT, ''),
                'license' => new external_value(PARAM_TEXT, 'License statement.', VALUE_DEFAULT, ''),
                'language' => new external_value(PARAM_ALPHANUMEXT, 'Language code.', VALUE_DEFAULT, ''),
                'keywords' => new external_multiple_structure(
                    new external_value(PARAM_TEXT, 'Keyword.'),
                    'Keywords.',
                    VALUE_DEFAULT,
                    []
                ),
                'notes' => new external_value(PARAM_RAW, 'Internal notes.', VALUE_DEFAULT, ''),
            ], 'Optional media metadata.', VALUE_DEFAULT, []),
            'libraryslug' => new external_value(
                PARAM_ALPHANUMEXT,
                'Home media-library slug. Defaults to the root UCKK library for backward compatibility.',
                VALUE_DEFAULT,
                media_library_scope::LIBRARY_UCKK
            ),
        ]);
    }

    /**
     * Execute service.
     *
     * @param int $cmid Course module id.
     * @param string $title Media title.
     * @param string $description Media description.
     * @param string $mediatype Media type.
     * @param string $sourcetype Source type.
     * @param string $sourceownership Source ownership.
     * @param string $visibility Visibility.
     * @param string $status Status.
     * @param string $audiencesuitability Audience suitability.
     * @param int $draftitemid Draft file item id.
     * @param int $collectionid Optional collection id.
     * @param array $metadata Metadata.
     * @param string $libraryslug Home media-library slug.
     * @return array Result.
     */
    public static function execute(
        int $cmid,
        string $title,
        string $description = '',
        string $mediatype = 'other',
        string $sourcetype = 'submitted_to_uckk',
        string $sourceownership = 'unknown_source',
        string $visibility = 'course',
        string $status = 'draft',
        string $audiencesuitability = 'guided',
        int $draftitemid = 0,
        int $collectionid = 0,
        array $metadata = [],
        string $libraryslug = media_library_scope::LIBRARY_UCKK
    ): array {
        global $DB, $USER;

        [
            'cmid' => $cmid,
            'title' => $title,
            'description' => $description,
            'mediatype' => $mediatype,
            'sourcetype' => $sourcetype,
            'sourceownership' => $sourceownership,
            'visibility' => $visibility,
            'status' => $status,
            'audiencesuitability' => $audiencesuitability,
            'draftitemid' => $draftitemid,
            'collectionid' => $collectionid,
            'metadata' => $metadata,
            'libraryslug' => $libraryslug,
        ] = self::validate_parameters(self::execute_parameters(), [
            'cmid' => $cmid,
            'title' => $title,
            'description' => $description,
            'mediatype' => $mediatype,
            'sourcetype' => $sourcetype,
            'sourceownership' => $sourceownership,
            'visibility' => $visibility,
            'status' => $status,
            'audiencesuitability' => $audiencesuitability,
            'draftitemid' => $draftitemid,
            'collectionid' => $collectionid,
            'metadata' => $metadata,
            'libraryslug' => $libraryslug,
        ]);

        $cm = get_coursemodule_from_id('uckkarchive', $cmid, 0, false, MUST_EXIST);
        $course = $DB->get_record('course', ['id' => $cm->course], '*', MUST_EXIST);
        $archive = $DB->get_record('uckkarchive', ['id' => $cm->instance], '*', MUST_EXIST);
        $context = context_module::instance($cm->id);

        self::validate_context($context);
        require_login($course, false, $cm);
        require_capability('mod/uckkarchive:addmedia', $context);

        self::require_allowed_value($mediatype, self::allowed_media_types(), 'Invalid media type.');
        self::require_allowed_value($sourcetype, self::allowed_source_types(), 'Invalid source type.');
        self::require_allowed_value($sourceownership, self::allowed_source_ownership(), 'Invalid source ownership.');
        self::require_allowed_value($visibility, self::allowed_visibility(), 'Invalid visibility.');
        self::require_allowed_value($status, self::allowed_statuses(), 'Invalid media status.');
        self::require_allowed_value($audiencesuitability, self::allowed_audience_suitability(), 'Invalid audience suitability.');

        $libraryscope = new media_library_scope();
        $library = $libraryscope->resolve_by_slug($libraryslug);
        if (!$library) {
            throw new invalid_parameter_exception('Unknown media-library slug: ' . $libraryslug);
        }
        if ($libraryslug !== media_library_scope::LIBRARY_UCKK) {
            require_capability('mod/uckkarchive:managelibraries', \context_system::instance());
        }

        $record = [
            'libraryid' => (int)$library->id,
            'archiveid' => (int)$archive->id,
            'courseid' => (int)$course->id,
            'cmid' => (int)$cm->id,
            'contextid' => (int)$context->id,
            'title' => $title,
            'description' => $description,
            'mediatype' => $mediatype,
            'sourcetype' => $sourcetype,
            'sourceownership' => $sourceownership,
            'visibility' => self::normalize_visibility($visibility),
            'status' => $status,
            'audiencesuitability' => $audiencesuitability,
            'draftitemid' => $draftitemid,
            'metadata' => $metadata,
        ];

        $transaction = $DB->start_delegated_transaction();

        if (!class_exists(media::class) || !method_exists(media::class, 'create')) {
            throw new \coding_exception('The media domain service must implement mod_uckkarchive\\local\\media::create().');
        }

        $media = media::create($record, (int)$USER->id);

        if ($draftitemid > 0 && method_exists(media::class, 'save_draft_files')) {
            media::save_draft_files((int)$media->id, $draftitemid, (int)$USER->id);
            $media = method_exists(media::class, 'get') ? media::get((int)$media->id) : $media;
        }

        if ($collectionid > 0) {
            self::add_to_collection((int)$collectionid, (int)$media->id, (int)$USER->id);
        }

        $transaction->allow_commit();

        return self::format_media_response($media, $context);
    }

    /**
     * Describe service return structure.
     *
     * @return external_single_structure
     */
    public static function execute_returns(): external_single_structure {
        return new external_single_structure([
            'id' => new external_value(PARAM_INT, 'Media id.'),
            'uuid' => new external_value(PARAM_RAW, 'Stable media UUID.'),
            'archiveid' => new external_value(PARAM_INT, 'Archive instance id.'),
            'courseid' => new external_value(PARAM_INT, 'Course id.'),
            'cmid' => new external_value(PARAM_INT, 'Course module id.'),
            'contextid' => new external_value(PARAM_INT, 'Context id.'),
            'title' => new external_value(PARAM_TEXT, 'Media title.'),
            'description' => new external_value(PARAM_RAW, 'Media description.'),
            'mediatype' => new external_value(PARAM_ALPHANUMEXT, 'Media type.'),
            'sourcetype' => new external_value(PARAM_ALPHANUMEXT, 'Source type.'),
            'sourceownership' => new external_value(PARAM_ALPHANUMEXT, 'Source ownership.'),
            'visibility' => new external_value(PARAM_ALPHANUMEXT, 'Visibility.'),
            'status' => new external_value(PARAM_ALPHANUMEXT, 'Lifecycle status.'),
            'audiencesuitability' => new external_value(PARAM_ALPHANUMEXT, 'Audience suitability.'),
            'timecreated' => new external_value(PARAM_INT, 'Created timestamp.'),
            'timemodified' => new external_value(PARAM_INT, 'Modified timestamp.'),
            'canview' => new external_value(PARAM_BOOL, 'Whether the current user can view this media.'),
            'canedit' => new external_value(PARAM_BOOL, 'Whether the current user can edit this media.'),
            'candownload' => new external_value(PARAM_BOOL, 'Whether the current user can download this media.'),
        ]);
    }

    /**
     * Add created media to collection when the collection service exists.
     *
     * @param int $collectionid Collection id.
     * @param int $mediaid Media id.
     * @param int $userid User id.
     * @return void
     */
    private static function add_to_collection(int $collectionid, int $mediaid, int $userid): void {
        $collectionclass = 'mod_uckkarchive\\local\\media_collection';

        if (!class_exists($collectionclass) || !method_exists($collectionclass, 'add_media')) {
            throw new \coding_exception('The media collection service must implement add_media().');
        }

        $collectionclass::add_media($collectionid, $mediaid, $userid);
    }

    /**
     * Format media record for external response.
     *
     * @param \stdClass $media Media record.
     * @param \context_module $context Context.
     * @return array
     */
    private static function format_media_response(\stdClass $media, \context_module $context): array {
        return [
            'id' => (int)$media->id,
            'uuid' => (string)($media->uuid ?? ''),
            'archiveid' => (int)($media->archiveid ?? 0),
            'courseid' => (int)($media->courseid ?? 0),
            'cmid' => (int)($media->cmid ?? 0),
            'contextid' => (int)($media->contextid ?? $context->id),
            'title' => (string)($media->title ?? ''),
            'description' => (string)($media->description ?? ''),
            'mediatype' => (string)($media->mediatype ?? 'other'),
            'sourcetype' => (string)($media->sourcetype ?? 'submitted_to_uckk'),
            'sourceownership' => (string)($media->sourceownership ?? 'unknown_source'),
            'visibility' => (string)($media->visibility ?? 'restricted'),
            'status' => (string)($media->status ?? 'draft'),
            'audiencesuitability' => (string)($media->audiencesuitability ?? 'guided'),
            'timecreated' => (int)($media->timecreated ?? 0),
            'timemodified' => (int)($media->timemodified ?? 0),
            'canview' => has_capability('mod/uckkarchive:viewmedia', $context),
            'canedit' => has_capability('mod/uckkarchive:editmedia', $context),
            'candownload' => has_capability('mod/uckkarchive:downloadmedia', $context),
        ];
    }

    /**
     * Validate allowed value.
     *
     * @param string $value Value.
     * @param string[] $allowed Allowed values.
     * @param string $message Error message.
     * @return void
     */
    private static function require_allowed_value(string $value, array $allowed, string $message): void {
        if (!in_array($value, $allowed, true)) {
            throw new invalid_parameter_exception($message);
        }
    }

    /**
     * Normalize compatibility visibility values.
     *
     * @param string $visibility Visibility.
     * @return string
     */
    private static function normalize_visibility(string $visibility): string {
        return $visibility === 'institutional' ? 'institution' : $visibility;
    }

    /**
     * Allowed media types.
     *
     * @return string[]
     */
    private static function allowed_media_types(): array {
        return [
            'image',
            'video',
            'audio',
            'document',
            'text',
            'dataset',
            'external_reference',
            'other',
        ];
    }

    /**
     * Allowed source types.
     *
     * @return string[]
     */
    private static function allowed_source_types(): array {
        return [
            'produced_by_uckk',
            'submitted_to_uckk',
            'imported',
            'external_reference_only',
            'licensed_external',
            'public_domain',
            'fair_use_reference',
            'restricted_reference',
        ];
    }

    /**
     * Allowed source ownership values.
     *
     * @return string[]
     */
    private static function allowed_source_ownership(): array {
        return [
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
    }

    /**
     * Allowed visibility values.
     *
     * @return string[]
     */
    private static function allowed_visibility(): array {
        return [
            'private',
            'user',
            'group',
            'course',
            'cohort',
            'program',
            'institution',
            'institutional',
            'public',
            'restricted',
            'restricted_integrity',
            'restricted_cultural',
        ];
    }

    /**
     * Allowed lifecycle statuses.
     *
     * @return string[]
     */
    private static function allowed_statuses(): array {
        return [
            'draft',
            'submitted',
            'active',
            'restricted',
            'superseded',
            'archived',
            'deleted_soft',
        ];
    }

    /**
     * Allowed audience suitability values.
     *
     * @return string[]
     */
    private static function allowed_audience_suitability(): array {
        return [
            'general',
            'guided',
            'mature',
            'restricted',
            'not_for_children',
            'review_required',
            'unknown',
        ];
    }
}
