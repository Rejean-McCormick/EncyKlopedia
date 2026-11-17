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
 * External service for removing media from a media collection.
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

defined('MOODLE_INTERNAL') || die();

require_once($CFG->libdir . '/externallib.php');

/**
 * Remove media from collection external service.
 *
 * This service removes only the collection membership row. It does not delete
 * the media record, media versions, files, derivatives, tags, provenance,
 * content advisory markers, or export history.
 *
 * Target service name:
 *
 * ```text
 * mod_uckkarchive_remove_media_from_collection
 * ```
 */
final class remove_media_from_collection extends external_api {
    /** @var string Media table. */
    private const MEDIA_TABLE = 'uckkarchive_media';

    /** @var string Collection table. */
    private const COLLECTION_TABLE = 'uckkarchive_media_collection';

    /** @var string Collection membership table. */
    private const COLLECTION_ITEM_TABLE = 'uckkarchive_media_collection_item';

    /**
     * Describe service parameters.
     *
     * @return external_function_parameters
     */
    public static function execute_parameters(): external_function_parameters {
        return new external_function_parameters([
            'cmid' => new external_value(PARAM_INT, 'Course module id for the UCKK Archive instance.'),
            'collectionid' => new external_value(PARAM_INT, 'Media collection id.', VALUE_DEFAULT, 0),
            'collectionuuid' => new external_value(PARAM_RAW, 'Media collection UUID.', VALUE_DEFAULT, ''),
            'mediaid' => new external_value(PARAM_INT, 'Media id.', VALUE_DEFAULT, 0),
            'mediauuid' => new external_value(PARAM_RAW, 'Media UUID.', VALUE_DEFAULT, ''),
            'strict' => new external_value(PARAM_BOOL, 'Fail when membership does not exist.', VALUE_DEFAULT, false),
        ]);
    }

    /**
     * Execute service.
     *
     * @param int $cmid Course module id.
     * @param int $collectionid Collection id.
     * @param string $collectionuuid Collection UUID.
     * @param int $mediaid Media id.
     * @param string $mediauuid Media UUID.
     * @param bool $strict Whether missing membership should throw.
     * @return array Result.
     */
    public static function execute(
        int $cmid,
        int $collectionid = 0,
        string $collectionuuid = '',
        int $mediaid = 0,
        string $mediauuid = '',
        bool $strict = false
    ): array {
        global $DB, $USER;

        [
            'cmid' => $cmid,
            'collectionid' => $collectionid,
            'collectionuuid' => $collectionuuid,
            'mediaid' => $mediaid,
            'mediauuid' => $mediauuid,
            'strict' => $strict,
        ] = self::validate_parameters(self::execute_parameters(), [
            'cmid' => $cmid,
            'collectionid' => $collectionid,
            'collectionuuid' => $collectionuuid,
            'mediaid' => $mediaid,
            'mediauuid' => $mediauuid,
            'strict' => $strict,
        ]);

        $cm = get_coursemodule_from_id('uckkarchive', $cmid, 0, false, MUST_EXIST);
        $course = $DB->get_record('course', ['id' => $cm->course], '*', MUST_EXIST);
        $archive = $DB->get_record('uckkarchive', ['id' => $cm->instance], '*', MUST_EXIST);
        $context = context_module::instance($cm->id);

        self::validate_context($context);
        require_login($course, false, $cm);
        require_capability('mod/uckkarchive:managemediacollections', $context);

        self::require_table(self::COLLECTION_TABLE);
        self::require_table(self::COLLECTION_ITEM_TABLE);
        self::require_table(self::MEDIA_TABLE);

        $collection = self::resolve_collection((int)$collectionid, (string)$collectionuuid, (int)$archive->id);
        $media = self::resolve_media((int)$mediaid, (string)$mediauuid, (int)$archive->id);

        self::require_collection_in_context($collection, (int)$archive->id, (int)$course->id, (int)$cm->id, (int)$context->id);
        self::require_media_in_context($media, (int)$archive->id, (int)$course->id, (int)$cm->id, (int)$context->id);

        $membership = self::get_membership((int)$collection->id, (int)$media->id);
        $warnings = [];

        if (!$membership) {
            if ($strict) {
                throw new invalid_parameter_exception('Media is not in the specified collection.');
            }

            $warnings[] = self::warning(
                'media_collection_item',
                0,
                'membershipnotfound',
                'Media was not in the specified collection.'
            );

            return self::response(
                $collection,
                $media,
                null,
                false,
                self::count_collection_media((int)$collection->id),
                $context,
                $warnings
            );
        }

        $transaction = $DB->start_delegated_transaction();

        if (class_exists(media_collection::class) && method_exists(media_collection::class, 'remove_media')) {
            $removed = media_collection::remove_media((int)$collection->id, (int)$media->id);
        } else {
            $removed = self::fallback_remove((int)$collection->id, (int)$media->id);
        }

        $transaction->allow_commit();

        return self::response(
            $collection,
            $media,
            $membership,
            $removed,
            self::count_collection_media((int)$collection->id),
            $context,
            $warnings
        );
    }

    /**
     * Describe service return structure.
     *
     * @return external_single_structure
     */
    public static function execute_returns(): external_single_structure {
        return new external_single_structure([
            'removed' => new external_value(PARAM_BOOL, 'Whether an existing membership was removed.'),
            'collectionid' => new external_value(PARAM_INT, 'Collection id.'),
            'collectionuuid' => new external_value(PARAM_RAW, 'Collection UUID.'),
            'mediaid' => new external_value(PARAM_INT, 'Media id.'),
            'mediauuid' => new external_value(PARAM_RAW, 'Media UUID.'),
            'membershipid' => new external_value(PARAM_INT, 'Removed membership id, or 0 when none existed.'),
            'remainingcount' => new external_value(PARAM_INT, 'Remaining media count in collection.'),
            'canmanage' => new external_value(PARAM_BOOL, 'Whether the current user can manage media collections.'),
            'warnings' => new external_multiple_structure(
                new external_single_structure([
                    'item' => new external_value(PARAM_TEXT, 'Warning item.'),
                    'itemid' => new external_value(PARAM_INT, 'Warning item id.'),
                    'warningcode' => new external_value(PARAM_ALPHANUMEXT, 'Warning code.'),
                    'message' => new external_value(PARAM_TEXT, 'Warning message.'),
                ]),
                'Warnings.',
                VALUE_DEFAULT,
                []
            ),
        ]);
    }

    /**
     * Resolve collection by id or UUID.
     *
     * @param int $collectionid Collection id.
     * @param string $collectionuuid Collection UUID.
     * @param int $archiveid Archive id.
     * @return \stdClass Collection record.
     */
    private static function resolve_collection(int $collectionid, string $collectionuuid, int $archiveid): \stdClass {
        global $DB;

        if ($collectionid > 0) {
            return $DB->get_record(self::COLLECTION_TABLE, ['id' => $collectionid], '*', MUST_EXIST);
        }

        $collectionuuid = trim($collectionuuid);
        if ($collectionuuid === '') {
            throw new invalid_parameter_exception('A collection id or collection UUID is required.');
        }

        $conditions = ['uuid' => $collectionuuid];
        if (self::table_has_column(self::COLLECTION_TABLE, 'archiveid')) {
            $conditions['archiveid'] = $archiveid;
        }

        return $DB->get_record(self::COLLECTION_TABLE, $conditions, '*', MUST_EXIST);
    }

    /**
     * Resolve media by id or UUID.
     *
     * @param int $mediaid Media id.
     * @param string $mediauuid Media UUID.
     * @param int $archiveid Archive id.
     * @return \stdClass Media record.
     */
    private static function resolve_media(int $mediaid, string $mediauuid, int $archiveid): \stdClass {
        global $DB;

        if ($mediaid > 0) {
            return $DB->get_record(self::MEDIA_TABLE, ['id' => $mediaid], '*', MUST_EXIST);
        }

        $mediauuid = trim($mediauuid);
        if ($mediauuid === '') {
            throw new invalid_parameter_exception('A media id or media UUID is required.');
        }

        $conditions = ['uuid' => $mediauuid];
        if (self::table_has_column(self::MEDIA_TABLE, 'archiveid')) {
            $conditions['archiveid'] = $archiveid;
        }

        return $DB->get_record(self::MEDIA_TABLE, $conditions, '*', MUST_EXIST);
    }

    /**
     * Require collection belongs to the current archive/context where columns exist.
     *
     * @param \stdClass $collection Collection record.
     * @param int $archiveid Archive id.
     * @param int $courseid Course id.
     * @param int $cmid Course module id.
     * @param int $contextid Context id.
     * @return void
     */
    private static function require_collection_in_context(
        \stdClass $collection,
        int $archiveid,
        int $courseid,
        int $cmid,
        int $contextid
    ): void {
        self::require_context_field($collection, 'archiveid', $archiveid, 'Collection does not belong to this archive.');
        self::require_context_field($collection, 'courseid', $courseid, 'Collection does not belong to this course.');
        self::require_context_field($collection, 'cmid', $cmid, 'Collection does not belong to this activity.');
        self::require_context_field($collection, 'contextid', $contextid, 'Collection does not belong to this context.');
    }

    /**
     * Require media belongs to the current archive/context where columns exist.
     *
     * @param \stdClass $media Media record.
     * @param int $archiveid Archive id.
     * @param int $courseid Course id.
     * @param int $cmid Course module id.
     * @param int $contextid Context id.
     * @return void
     */
    private static function require_media_in_context(
        \stdClass $media,
        int $archiveid,
        int $courseid,
        int $cmid,
        int $contextid
    ): void {
        self::require_context_field($media, 'archiveid', $archiveid, 'Media does not belong to this archive.');
        self::require_context_field($media, 'courseid', $courseid, 'Media does not belong to this course.');
        self::require_context_field($media, 'cmid', $cmid, 'Media does not belong to this activity.');
        self::require_context_field($media, 'contextid', $contextid, 'Media does not belong to this context.');
    }

    /**
     * Require a context field value if the field exists and has a value.
     *
     * @param \stdClass $record Record.
     * @param string $field Field name.
     * @param int $expected Expected value.
     * @param string $message Error message.
     * @return void
     */
    private static function require_context_field(\stdClass $record, string $field, int $expected, string $message): void {
        if (!property_exists($record, $field) || (int)$record->{$field} === 0) {
            return;
        }

        if ((int)$record->{$field} !== $expected) {
            throw new invalid_parameter_exception($message);
        }
    }

    /**
     * Get existing collection membership.
     *
     * @param int $collectionid Collection id.
     * @param int $mediaid Media id.
     * @return \stdClass|false
     */
    private static function get_membership(int $collectionid, int $mediaid) {
        global $DB;

        return $DB->get_record(self::COLLECTION_ITEM_TABLE, [
            'collectionid' => $collectionid,
            'mediaid' => $mediaid,
        ]);
    }

    /**
     * Fallback removal when local collection service is not available.
     *
     * @param int $collectionid Collection id.
     * @param int $mediaid Media id.
     * @return bool
     */
    private static function fallback_remove(int $collectionid, int $mediaid): bool {
        global $DB;

        return $DB->delete_records(self::COLLECTION_ITEM_TABLE, [
            'collectionid' => $collectionid,
            'mediaid' => $mediaid,
        ]);
    }

    /**
     * Count media in collection.
     *
     * @param int $collectionid Collection id.
     * @return int
     */
    private static function count_collection_media(int $collectionid): int {
        if (class_exists(media_collection::class) && method_exists(media_collection::class, 'count_media')) {
            return (int)media_collection::count_media($collectionid);
        }

        global $DB;
        return (int)$DB->count_records(self::COLLECTION_ITEM_TABLE, ['collectionid' => $collectionid]);
    }

    /**
     * Build response.
     *
     * @param \stdClass $collection Collection.
     * @param \stdClass $media Media.
     * @param \stdClass|null $membership Removed membership.
     * @param bool $removed Removed flag.
     * @param int $remainingcount Remaining count.
     * @param \context_module $context Context.
     * @param array $warnings Warnings.
     * @return array
     */
    private static function response(
        \stdClass $collection,
        \stdClass $media,
        ?\stdClass $membership,
        bool $removed,
        int $remainingcount,
        \context_module $context,
        array $warnings
    ): array {
        return [
            'removed' => $removed,
            'collectionid' => (int)$collection->id,
            'collectionuuid' => (string)($collection->uuid ?? ''),
            'mediaid' => (int)$media->id,
            'mediauuid' => (string)($media->uuid ?? ''),
            'membershipid' => $membership ? (int)$membership->id : 0,
            'remainingcount' => $remainingcount,
            'canmanage' => has_capability('mod/uckkarchive:managemediacollections', $context),
            'warnings' => $warnings,
        ];
    }

    /**
     * Require DB table exists.
     *
     * @param string $tablename Table name.
     * @return void
     */
    private static function require_table(string $tablename): void {
        global $DB;

        if (!$DB->get_manager()->table_exists(new \xmldb_table($tablename))) {
            throw new \coding_exception('Missing required table: ' . $tablename);
        }
    }

    /**
     * Return whether table has column.
     *
     * @param string $tablename Table name.
     * @param string $column Column name.
     * @return bool
     */
    private static function table_has_column(string $tablename, string $column): bool {
        global $DB;

        $columns = $DB->get_columns($tablename);

        return array_key_exists($column, $columns);
    }

    /**
     * Warning payload.
     *
     * @param string $item Warning item.
     * @param int $itemid Item id.
     * @param string $code Warning code.
     * @param string $message Message.
     * @return array
     */
    private static function warning(string $item, int $itemid, string $code, string $message): array {
        return [
            'item' => $item,
            'itemid' => $itemid,
            'warningcode' => clean_param($code, PARAM_ALPHANUMEXT),
            'message' => $message,
        ];
    }
}
