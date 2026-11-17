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
 * External service for creating a media collection.
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
use mod_uckkarchive\local\media_collection;
use mod_uckkarchive\local\media_library_scope;

defined('MOODLE_INTERNAL') || die();

require_once($CFG->libdir . '/externallib.php');

/**
 * Create a media collection.
 *
 * This service creates a first-class collection in the internal media library.
 * It does not duplicate media files and it does not override media-level
 * restrictions. Membership is handled by add_media_to_collection.
 */
final class add_media_collection extends external_api {
    /**
     * Describe service parameters.
     *
     * @return external_function_parameters
     */
    public static function execute_parameters(): external_function_parameters {
        return new external_function_parameters([
            'cmid' => new external_value(PARAM_INT, 'Course module id for the UCKK Archive instance.'),
            'title' => new external_value(PARAM_TEXT, 'Collection title.'),
            'description' => new external_value(PARAM_RAW, 'Collection description.', VALUE_DEFAULT, ''),
            'purpose' => new external_value(PARAM_TEXT, 'Collection purpose.', VALUE_DEFAULT, ''),
            'visibility' => new external_value(PARAM_ALPHANUMEXT, 'Collection visibility.', VALUE_DEFAULT, 'course'),
            'status' => new external_value(PARAM_ALPHANUMEXT, 'Collection lifecycle status.', VALUE_DEFAULT, 'draft'),
            'metadata' => new external_single_structure([
                'summary' => new external_value(PARAM_RAW, 'Short summary.', VALUE_DEFAULT, ''),
                'audience' => new external_value(PARAM_TEXT, 'Intended audience.', VALUE_DEFAULT, ''),
                'teachingcontext' => new external_value(PARAM_RAW, 'Teaching or use context.', VALUE_DEFAULT, ''),
                'rightsnote' => new external_value(PARAM_RAW, 'Rights or use note.', VALUE_DEFAULT, ''),
                'culturalprotocol' => new external_value(PARAM_BOOL, 'Whether cultural protocol handling applies.', VALUE_DEFAULT, false),
                'restrictednote' => new external_value(PARAM_RAW, 'Restricted access note.', VALUE_DEFAULT, ''),
                'keywords' => new external_multiple_structure(
                    new external_value(PARAM_TEXT, 'Keyword.'),
                    'Collection keywords.',
                    VALUE_DEFAULT,
                    []
                ),
            ], 'Optional collection metadata.', VALUE_DEFAULT, []),
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
     * @param string $title Collection title.
     * @param string $description Collection description.
     * @param string $purpose Collection purpose.
     * @param string $visibility Visibility.
     * @param string $status Status.
     * @param array $metadata Metadata.
     * @param string $libraryslug Home media-library slug.
     * @return array Result.
     */
    public static function execute(
        int $cmid,
        string $title,
        string $description = '',
        string $purpose = '',
        string $visibility = 'course',
        string $status = 'draft',
        array $metadata = [],
        string $libraryslug = media_library_scope::LIBRARY_UCKK
    ): array {
        global $DB, $USER;

        [
            'cmid' => $cmid,
            'title' => $title,
            'description' => $description,
            'purpose' => $purpose,
            'visibility' => $visibility,
            'status' => $status,
            'metadata' => $metadata,
            'libraryslug' => $libraryslug,
        ] = self::validate_parameters(self::execute_parameters(), [
            'cmid' => $cmid,
            'title' => $title,
            'description' => $description,
            'purpose' => $purpose,
            'visibility' => $visibility,
            'status' => $status,
            'metadata' => $metadata,
            'libraryslug' => $libraryslug,
        ]);

        $cm = get_coursemodule_from_id('uckkarchive', $cmid, 0, false, MUST_EXIST);
        $course = $DB->get_record('course', ['id' => $cm->course], '*', MUST_EXIST);
        $archive = $DB->get_record('uckkarchive', ['id' => $cm->instance], '*', MUST_EXIST);
        $context = context_module::instance($cm->id);

        self::validate_context($context);
        require_login($course, false, $cm);
        require_capability('mod/uckkarchive:managemediacollections', $context);

        $title = self::require_title($title);
        $visibility = self::normalize_visibility($visibility);
        $status = self::normalize_status($status);

        $libraryscope = new media_library_scope();
        $library = $libraryscope->resolve_by_slug($libraryslug);
        if (!$library) {
            throw new invalid_parameter_exception('Unknown media-library slug: ' . $libraryslug);
        }
        if ($libraryslug !== media_library_scope::LIBRARY_UCKK) {
            require_capability('mod/uckkarchive:managelibraries', \context_system::instance());
        }

        if (!class_exists(media_collection::class) || !method_exists(media_collection::class, 'create')) {
            throw new \coding_exception(
                'The media collection domain service must implement mod_uckkarchive\\local\\media_collection::create().'
            );
        }

        $record = [
            'archiveid' => (int)$archive->id,
            'libraryid' => (int)$library->id,
            'courseid' => (int)$course->id,
            'cmid' => (int)$cm->id,
            'contextid' => (int)$context->id,
            'title' => $title,
            'description' => self::clean_raw_text($description),
            'purpose' => self::clean_short_text($purpose),
            'visibility' => $visibility,
            'status' => $status,
            'metadata' => self::clean_metadata($metadata),
        ];

        $transaction = $DB->start_delegated_transaction();

        $collection = media_collection::create($record, (int)$USER->id);

        self::trigger_collection_created_event($collection, $context, $archive, $course, $cm);

        $transaction->allow_commit();

        return self::format_collection_response($collection, $context);
    }

    /**
     * Describe service return structure.
     *
     * @return external_single_structure
     */
    public static function execute_returns(): external_single_structure {
        return new external_single_structure([
            'id' => new external_value(PARAM_INT, 'Collection id.'),
            'uuid' => new external_value(PARAM_RAW, 'Stable collection UUID.'),
            'archiveid' => new external_value(PARAM_INT, 'Archive instance id.'),
            'courseid' => new external_value(PARAM_INT, 'Course id.'),
            'cmid' => new external_value(PARAM_INT, 'Course module id.'),
            'contextid' => new external_value(PARAM_INT, 'Context id.'),
            'title' => new external_value(PARAM_TEXT, 'Collection title.'),
            'description' => new external_value(PARAM_RAW, 'Collection description.'),
            'purpose' => new external_value(PARAM_TEXT, 'Collection purpose.'),
            'visibility' => new external_value(PARAM_ALPHANUMEXT, 'Visibility.'),
            'status' => new external_value(PARAM_ALPHANUMEXT, 'Lifecycle status.'),
            'itemcount' => new external_value(PARAM_INT, 'Number of media records in the collection.'),
            'metadata' => new external_value(PARAM_RAW, 'JSON metadata.'),
            'timecreated' => new external_value(PARAM_INT, 'Created timestamp.'),
            'timemodified' => new external_value(PARAM_INT, 'Modified timestamp.'),
            'canview' => new external_value(PARAM_BOOL, 'Whether current user can view media collections.'),
            'canmanage' => new external_value(PARAM_BOOL, 'Whether current user can manage media collections.'),
            'canexport' => new external_value(PARAM_BOOL, 'Whether current user can export media collections.'),
        ]);
    }

    /**
     * Format collection record for external response.
     *
     * @param \stdClass $collection Collection record.
     * @param context_module $context Module context.
     * @return array
     */
    private static function format_collection_response(\stdClass $collection, context_module $context): array {
        $itemcount = 0;

        if (class_exists(media_collection::class) && method_exists(media_collection::class, 'count_media')) {
            $itemcount = media_collection::count_media((int)$collection->id);
        }

        return [
            'id' => (int)$collection->id,
            'uuid' => (string)($collection->uuid ?? ''),
            'archiveid' => (int)($collection->archiveid ?? 0),
            'courseid' => (int)($collection->courseid ?? 0),
            'cmid' => (int)($collection->cmid ?? 0),
            'contextid' => (int)($collection->contextid ?? $context->id),
            'title' => (string)($collection->title ?? ''),
            'description' => (string)($collection->description ?? ''),
            'purpose' => (string)($collection->purpose ?? ''),
            'visibility' => (string)($collection->visibility ?? 'restricted'),
            'status' => (string)($collection->status ?? 'draft'),
            'itemcount' => $itemcount,
            'metadata' => (string)($collection->metadata ?? '{}'),
            'timecreated' => (int)($collection->timecreated ?? 0),
            'timemodified' => (int)($collection->timemodified ?? 0),
            'canview' => has_capability('mod/uckkarchive:viewmedia', $context),
            'canmanage' => has_capability('mod/uckkarchive:managemediacollections', $context),
            'canexport' => has_capability('mod/uckkarchive:exportmedia', $context),
        ];
    }

    /**
     * Trigger collection-created event when the event class exists.
     *
     * @param \stdClass $collection Collection record.
     * @param context_module $context Module context.
     * @param \stdClass $archive Archive instance.
     * @param \stdClass $course Course.
     * @param \stdClass $cm Course module.
     * @return void
     */
    private static function trigger_collection_created_event(
        \stdClass $collection,
        context_module $context,
        \stdClass $archive,
        \stdClass $course,
        \stdClass $cm
    ): void {
        $eventclass = '\\mod_uckkarchive\\event\\media_collection_created';

        if (!class_exists($eventclass)) {
            return;
        }

        $event = $eventclass::create([
            'objectid' => (int)$collection->id,
            'context' => $context,
            'other' => [
                'archiveid' => (int)$archive->id,
                'courseid' => (int)$course->id,
                'cmid' => (int)$cm->id,
                'uuid' => (string)($collection->uuid ?? ''),
                'visibility' => (string)($collection->visibility ?? ''),
                'status' => (string)($collection->status ?? ''),
            ],
        ]);

        if (method_exists($event, 'add_record_snapshot')) {
            $event->add_record_snapshot('course', $course);
            $event->add_record_snapshot('course_modules', $cm);
            $event->add_record_snapshot('uckkarchive', $archive);
            $event->add_record_snapshot('uckkarchive_media_collection', $collection);
        }

        $event->trigger();
    }

    /**
     * Require a non-empty collection title.
     *
     * @param string $title Raw title.
     * @return string
     */
    private static function require_title(string $title): string {
        $title = trim($title);

        if ($title === '') {
            throw new invalid_parameter_exception('Missing required field: title.');
        }

        return self::truncate(clean_param($title, PARAM_TEXT), 255);
    }

    /**
     * Clean short text.
     *
     * @param string $value Raw value.
     * @return string
     */
    private static function clean_short_text(string $value): string {
        return self::truncate(clean_param(trim($value), PARAM_TEXT), 100);
    }

    /**
     * Clean raw text.
     *
     * @param string $value Raw value.
     * @return string
     */
    private static function clean_raw_text(string $value): string {
        return clean_param(trim($value), PARAM_RAW);
    }

    /**
     * Clean metadata from external parameters.
     *
     * @param array $metadata Metadata.
     * @return array
     */
    private static function clean_metadata(array $metadata): array {
        $clean = [];

        $clean['summary'] = self::clean_raw_text((string)($metadata['summary'] ?? ''));
        $clean['audience'] = self::clean_short_text((string)($metadata['audience'] ?? ''));
        $clean['teachingcontext'] = self::clean_raw_text((string)($metadata['teachingcontext'] ?? ''));
        $clean['rightsnote'] = self::clean_raw_text((string)($metadata['rightsnote'] ?? ''));
        $clean['culturalprotocol'] = !empty($metadata['culturalprotocol']);
        $clean['restrictednote'] = self::clean_raw_text((string)($metadata['restrictednote'] ?? ''));

        $keywords = [];
        foreach ((array)($metadata['keywords'] ?? []) as $keyword) {
            $keyword = self::truncate(clean_param(trim((string)$keyword), PARAM_TEXT), 100);
            if ($keyword !== '') {
                $keywords[] = $keyword;
            }
        }

        $clean['keywords'] = array_values(array_unique($keywords));

        return $clean;
    }

    /**
     * Normalize compatibility visibility values.
     *
     * @param string $visibility Visibility.
     * @return string
     */
    private static function normalize_visibility(string $visibility): string {
        $visibility = trim($visibility);
        $visibility = $visibility === 'institutional' ? 'institution' : $visibility;

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

        if (!in_array($visibility, $allowed, true)) {
            throw new invalid_parameter_exception('Invalid media collection visibility.');
        }

        return $visibility;
    }

    /**
     * Normalize collection lifecycle status.
     *
     * @param string $status Status.
     * @return string
     */
    private static function normalize_status(string $status): string {
        $status = trim($status);

        $allowed = [
            'draft',
            'active',
            'restricted',
            'archived',
            'deleted_soft',
        ];

        if (!in_array($status, $allowed, true)) {
            throw new invalid_parameter_exception('Invalid media collection status.');
        }

        return $status;
    }

    /**
     * Truncate string safely.
     *
     * @param string $value Value.
     * @param int $maxlength Maximum length.
     * @return string
     */
    private static function truncate(string $value, int $maxlength): string {
        if (function_exists('core_text::substr')) {
            return \core_text::substr($value, 0, $maxlength);
        }

        return mb_substr($value, 0, $maxlength);
    }
}
