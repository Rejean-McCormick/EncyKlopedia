<?php
// This file is part of Moodle - https://moodle.org/
//
// Moodle is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// any later version.

/**
 * External service for updating a media collection.
 *
 * @package    mod_uckkarchive
 * @copyright  2026 Univers-Cité King Klown
 * @license    https://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later
 */

declare(strict_types=1);

namespace mod_uckkarchive\external;

defined('MOODLE_INTERNAL') || die();

global $CFG;
require_once($CFG->libdir . '/externallib.php');
require_once(dirname(__DIR__, 2) . '/locallib.php');

use context_module;
use core_external\external_api;
use core_external\external_function_parameters;
use core_external\external_multiple_structure;
use core_external\external_single_structure;
use core_external\external_value;
use invalid_parameter_exception;
use mod_uckkarchive\local\media_collection;
use moodle_exception;
use stdClass;
use xmldb_table;

/**
 * Update a media collection owned by the current UCKK Archive activity.
 *
 * Target service name:
 *
 * ```text
 * mod_uckkarchive_update_media_collection
 * ```
 *
 * This endpoint updates collection metadata only. It does not add or remove
 * media membership rows. Membership changes belong to:
 *
 * ```text
 * add_media_to_collection.php
 * remove_media_from_collection.php
 * ```
 */
final class update_media_collection extends external_api {
    /** Media collection table. */
    private const COLLECTION_TABLE = 'uckkarchive_media_collection';

    /** Media collection membership table. */
    private const COLLECTION_ITEM_TABLE = 'uckkarchive_media_collection_item';

    /** Allowed visibility values. */
    private const VISIBILITIES = [
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

    /** Allowed collection statuses when the column exists. */
    private const STATUSES = [
        'draft',
        'active',
        'restricted',
        'archived',
        'deleted_soft',
    ];

    /**
     * Define service parameters.
     *
     * @return external_function_parameters
     */
    public static function execute_parameters(): external_function_parameters {
        return new external_function_parameters([
            'cmid' => new external_value(PARAM_INT, 'Course module id.'),
            'collectionid' => new external_value(PARAM_INT, 'Media collection id.', VALUE_DEFAULT, 0),
            'collectionuuid' => new external_value(PARAM_RAW, 'Media collection UUID.', VALUE_DEFAULT, ''),
            'data' => new external_single_structure([
                'title' => new external_value(PARAM_TEXT, 'Collection title.', VALUE_DEFAULT, ''),
                'description' => new external_value(PARAM_RAW, 'Collection description.', VALUE_DEFAULT, ''),
                'visibility' => new external_value(PARAM_ALPHANUMEXT, 'Collection visibility.', VALUE_DEFAULT, ''),
                'purpose' => new external_value(PARAM_ALPHANUMEXT, 'Collection purpose.', VALUE_DEFAULT, ''),
                'status' => new external_value(PARAM_ALPHANUMEXT, 'Collection status.', VALUE_DEFAULT, ''),
                'sortorder' => new external_value(PARAM_INT, 'Collection sort order.', VALUE_DEFAULT, 0),
                'metadatajson' => new external_value(PARAM_RAW, 'Collection metadata as JSON object.', VALUE_DEFAULT, ''),
            ], 'Collection update data.', VALUE_DEFAULT, []),
            'sesskey' => new external_value(PARAM_RAW, 'Optional sesskey for AJAX callers.', VALUE_DEFAULT, ''),
        ]);
    }

    /**
     * Execute service.
     *
     * @param int $cmid Course module id.
     * @param int $collectionid Collection id.
     * @param string $collectionuuid Collection UUID.
     * @param array<string, mixed> $data Update data.
     * @param string $sesskey Optional sesskey.
     * @return array<string, mixed>
     */
    public static function execute(
        int $cmid,
        int $collectionid = 0,
        string $collectionuuid = '',
        array $data = [],
        string $sesskey = ''
    ): array {
        global $DB, $USER;

        $params = self::validate_parameters(self::execute_parameters(), [
            'cmid' => $cmid,
            'collectionid' => $collectionid,
            'collectionuuid' => $collectionuuid,
            'data' => $data,
            'sesskey' => $sesskey,
        ]);

        if (trim((string)$params['sesskey']) !== '') {
            require_sesskey();
        }

        [$course, $cm, $archive, $context] = self::load_page((int)$params['cmid']);

        self::validate_context($context);
        require_login($course, false, $cm);
        require_capability('mod/uckkarchive:managemediacollections', $context);

        self::require_table(self::COLLECTION_TABLE);

        $collection = self::resolve_collection(
            (int)$params['collectionid'],
            (string)$params['collectionuuid'],
            (int)$archive->id
        );

        self::require_collection_in_context(
            $collection,
            (int)$archive->id,
            (int)$course->id,
            (int)$cm->id,
            (int)$context->id
        );

        $update = self::build_update_record(
            $collection,
            (array)$params['data'],
            (int)$USER->id
        );

        if (count((array)$update) <= 2) {
            return [
                'status' => 'unchanged',
                'collection' => self::export_collection($collection, $context),
                'permissions' => self::get_permissions($context),
                'warnings' => [
                    self::warning(
                        'media_collection',
                        (int)$collection->id,
                        'noupdatefields',
                        'No supported update fields were provided.'
                    ),
                ],
            ];
        }

        $transaction = $DB->start_delegated_transaction();

        if (class_exists(media_collection::class) && method_exists(media_collection::class, 'update')) {
            $updated = media_collection::update((int)$collection->id, (array)$params['data']);
        } else {
            $DB->update_record(self::COLLECTION_TABLE, self::filter_record_for_table($update));
            $updated = self::get_collection((int)$collection->id);
        }

        $transaction->allow_commit();

        return [
            'status' => 'updated',
            'collection' => self::export_collection($updated, $context),
            'permissions' => self::get_permissions($context),
            'warnings' => [],
        ];
    }

    /**
     * Define service return structure.
     *
     * @return external_single_structure
     */
    public static function execute_returns(): external_single_structure {
        return new external_single_structure([
            'status' => new external_value(PARAM_ALPHANUMEXT, 'Operation status.'),
            'collection' => self::collection_structure(),
            'permissions' => self::permissions_structure(),
            'warnings' => self::warnings_structure(),
        ]);
    }

    /**
     * Return collection response structure.
     *
     * @return external_single_structure
     */
    private static function collection_structure(): external_single_structure {
        return new external_single_structure([
            'id' => new external_value(PARAM_INT, 'Collection id.'),
            'uuid' => new external_value(PARAM_RAW, 'Collection UUID.'),
            'archiveid' => new external_value(PARAM_INT, 'Archive id.'),
            'courseid' => new external_value(PARAM_INT, 'Course id.'),
            'cmid' => new external_value(PARAM_INT, 'Course module id.'),
            'contextid' => new external_value(PARAM_INT, 'Context id.'),
            'title' => new external_value(PARAM_TEXT, 'Collection title.'),
            'description' => new external_value(PARAM_RAW, 'Collection description.'),
            'visibility' => new external_value(PARAM_ALPHANUMEXT, 'Collection visibility.'),
            'purpose' => new external_value(PARAM_ALPHANUMEXT, 'Collection purpose.'),
            'status' => new external_value(PARAM_ALPHANUMEXT, 'Collection status.'),
            'sortorder' => new external_value(PARAM_INT, 'Sort order.'),
            'itemcount' => new external_value(PARAM_INT, 'Number of media items in collection.'),
            'createdby' => new external_value(PARAM_INT, 'Creator user id.'),
            'modifiedby' => new external_value(PARAM_INT, 'Modifier user id.'),
            'metadatajson' => new external_value(PARAM_RAW, 'Metadata JSON.'),
            'timecreated' => new external_value(PARAM_INT, 'Creation time.'),
            'timemodified' => new external_value(PARAM_INT, 'Modification time.'),
        ]);
    }

    /**
     * Return permissions response structure.
     *
     * @return external_single_structure
     */
    private static function permissions_structure(): external_single_structure {
        return new external_single_structure([
            'viewmedia' => new external_value(PARAM_BOOL, 'Can view media.'),
            'managemediacollections' => new external_value(PARAM_BOOL, 'Can manage media collections.'),
            'addmedia' => new external_value(PARAM_BOOL, 'Can add media.'),
            'editmedia' => new external_value(PARAM_BOOL, 'Can edit media.'),
            'exportmedia' => new external_value(PARAM_BOOL, 'Can export media.'),
            'viewrestrictedmedia' => new external_value(PARAM_BOOL, 'Can view restricted media.'),
        ]);
    }

    /**
     * Return warnings response structure.
     *
     * @return external_multiple_structure
     */
    private static function warnings_structure(): external_multiple_structure {
        return new external_multiple_structure(
            new external_single_structure([
                'item' => new external_value(PARAM_TEXT, 'Warning item.'),
                'itemid' => new external_value(PARAM_INT, 'Warning item id.'),
                'warningcode' => new external_value(PARAM_ALPHANUMEXT, 'Warning code.'),
                'message' => new external_value(PARAM_TEXT, 'Warning message.'),
            ]),
            'Warnings.',
            VALUE_DEFAULT,
            []
        );
    }

    /**
     * Load archive page.
     *
     * @param int $cmid Course module id.
     * @return array{0:stdClass,1:stdClass,2:stdClass,3:context_module}
     */
    private static function load_page(int $cmid): array {
        if (function_exists('uckkarchive_require_page')) {
            [$course, $cm, $archive, $context] = \uckkarchive_require_page($cmid, 0);
            return [$course, $cm, $archive, $context];
        }

        global $DB;

        $cm = get_coursemodule_from_id('uckkarchive', $cmid, 0, false, MUST_EXIST);
        $course = $DB->get_record('course', ['id' => $cm->course], '*', MUST_EXIST);
        $archive = $DB->get_record('uckkarchive', ['id' => $cm->instance], '*', MUST_EXIST);
        $context = context_module::instance($cm->id);

        return [$course, $cm, $archive, $context];
    }

    /**
     * Resolve collection by id or UUID.
     *
     * @param int $collectionid Collection id.
     * @param string $collectionuuid Collection UUID.
     * @param int $archiveid Archive id.
     * @return stdClass
     */
    private static function resolve_collection(int $collectionid, string $collectionuuid, int $archiveid): stdClass {
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
        } else if (self::table_has_column(self::COLLECTION_TABLE, 'uckkarchiveid')) {
            $conditions['uckkarchiveid'] = $archiveid;
        }

        return $DB->get_record(self::COLLECTION_TABLE, $conditions, '*', MUST_EXIST);
    }

    /**
     * Return collection by id.
     *
     * @param int $collectionid Collection id.
     * @return stdClass
     */
    private static function get_collection(int $collectionid): stdClass {
        global $DB;

        return $DB->get_record(self::COLLECTION_TABLE, ['id' => $collectionid], '*', MUST_EXIST);
    }

    /**
     * Build update record.
     *
     * @param stdClass $collection Current collection.
     * @param array<string, mixed> $data Raw data.
     * @param int $userid User id.
     * @return stdClass
     */
    private static function build_update_record(stdClass $collection, array $data, int $userid): stdClass {
        $record = new stdClass();
        $record->id = (int)$collection->id;
        $record->timemodified = time();

        if (array_key_exists('title', $data) && trim((string)$data['title']) !== '') {
            $record->title = clean_param((string)$data['title'], PARAM_TEXT);
        }

        if (array_key_exists('description', $data)) {
            $record->description = clean_param((string)$data['description'], PARAM_RAW);
        }

        if (array_key_exists('visibility', $data) && trim((string)$data['visibility']) !== '') {
            $record->visibility = self::normalise_visibility((string)$data['visibility']);
        }

        if (array_key_exists('purpose', $data) && trim((string)$data['purpose']) !== '') {
            $record->purpose = clean_param((string)$data['purpose'], PARAM_ALPHANUMEXT);
        }

        if (array_key_exists('status', $data) && trim((string)$data['status']) !== '') {
            $record->status = self::normalise_status((string)$data['status']);
        }

        if (array_key_exists('sortorder', $data)) {
            $record->sortorder = max(0, (int)$data['sortorder']);
        }

        if (array_key_exists('metadatajson', $data) && trim((string)$data['metadatajson']) !== '') {
            $record->metadata = self::normalise_metadata_json((string)$data['metadatajson']);
        }

        if (self::table_has_column(self::COLLECTION_TABLE, 'modifiedby')) {
            $record->modifiedby = $userid;
        } else if (self::table_has_column(self::COLLECTION_TABLE, 'usermodified')) {
            $record->usermodified = $userid;
        }

        return $record;
    }

    /**
     * Export collection.
     *
     * @param stdClass $collection Collection record.
     * @param context_module $context Context.
     * @return array<string, mixed>
     */
    private static function export_collection(stdClass $collection, context_module $context): array {
        $archiveid = (int)self::field($collection, ['archiveid', 'uckkarchiveid'], 0);

        return [
            'id' => (int)$collection->id,
            'uuid' => (string)self::field($collection, ['uuid'], ''),
            'archiveid' => $archiveid,
            'courseid' => (int)self::field($collection, ['courseid'], 0),
            'cmid' => (int)self::field($collection, ['cmid'], 0),
            'contextid' => (int)self::field($collection, ['contextid'], 0),
            'title' => format_string((string)self::field($collection, ['title', 'name'], '')),
            'description' => format_text((string)self::field($collection, ['description', 'summary'], ''), FORMAT_HTML, [
                'context' => $context,
                'para' => false,
            ]),
            'visibility' => (string)self::field($collection, ['visibility'], 'restricted'),
            'purpose' => (string)self::field($collection, ['purpose'], ''),
            'status' => (string)self::field($collection, ['status'], 'active'),
            'sortorder' => (int)self::field($collection, ['sortorder'], 0),
            'itemcount' => self::count_collection_items((int)$collection->id),
            'createdby' => (int)self::field($collection, ['createdby', 'userid'], 0),
            'modifiedby' => (int)self::field($collection, ['modifiedby', 'usermodified'], 0),
            'metadatajson' => self::metadata_to_json(self::field($collection, ['metadata'], '{}')),
            'timecreated' => (int)self::field($collection, ['timecreated'], 0),
            'timemodified' => (int)self::field($collection, ['timemodified'], 0),
        ];
    }

    /**
     * Return permissions payload.
     *
     * @param context_module $context Context.
     * @return array<string, bool>
     */
    private static function get_permissions(context_module $context): array {
        return [
            'viewmedia' => has_capability('mod/uckkarchive:viewmedia', $context),
            'managemediacollections' => has_capability('mod/uckkarchive:managemediacollections', $context),
            'addmedia' => has_capability('mod/uckkarchive:addmedia', $context),
            'editmedia' => has_capability('mod/uckkarchive:editmedia', $context),
            'exportmedia' => has_capability('mod/uckkarchive:exportmedia', $context),
            'viewrestrictedmedia' => has_capability('mod/uckkarchive:viewrestrictedmedia', $context),
        ];
    }

    /**
     * Require collection belongs to current context when those fields exist.
     *
     * @param stdClass $collection Collection record.
     * @param int $archiveid Archive id.
     * @param int $courseid Course id.
     * @param int $cmid Course module id.
     * @param int $contextid Context id.
     * @return void
     */
    private static function require_collection_in_context(
        stdClass $collection,
        int $archiveid,
        int $courseid,
        int $cmid,
        int $contextid
    ): void {
        self::require_context_field($collection, 'archiveid', $archiveid, 'Collection does not belong to this archive.');
        self::require_context_field($collection, 'uckkarchiveid', $archiveid, 'Collection does not belong to this archive.');
        self::require_context_field($collection, 'courseid', $courseid, 'Collection does not belong to this course.');
        self::require_context_field($collection, 'cmid', $cmid, 'Collection does not belong to this activity.');
        self::require_context_field($collection, 'contextid', $contextid, 'Collection does not belong to this context.');
    }

    /**
     * Require matching context field if present.
     *
     * @param stdClass $record Record.
     * @param string $field Field name.
     * @param int $expected Expected value.
     * @param string $message Error message.
     * @return void
     */
    private static function require_context_field(stdClass $record, string $field, int $expected, string $message): void {
        if (!property_exists($record, $field) || (int)$record->{$field} === 0) {
            return;
        }

        if ((int)$record->{$field} !== $expected) {
            throw new invalid_parameter_exception($message);
        }
    }

    /**
     * Filter record to existing columns.
     *
     * @param stdClass $record Record.
     * @return stdClass
     */
    private static function filter_record_for_table(stdClass $record): stdClass {
        global $DB;

        $columns = $DB->get_columns(self::COLLECTION_TABLE);
        $filtered = new stdClass();

        foreach ($columns as $name => $definition) {
            if (property_exists($record, $name)) {
                $filtered->{$name} = $record->{$name};
            }
        }

        return $filtered;
    }

    /**
     * Count collection item rows.
     *
     * @param int $collectionid Collection id.
     * @return int
     */
    private static function count_collection_items(int $collectionid): int {
        global $DB;

        if ($collectionid <= 0 || !self::table_exists(self::COLLECTION_ITEM_TABLE)) {
            return 0;
        }

        if (class_exists(media_collection::class) && method_exists(media_collection::class, 'count_media')) {
            return (int)media_collection::count_media($collectionid);
        }

        if (self::table_has_column(self::COLLECTION_ITEM_TABLE, 'collectionid')) {
            return (int)$DB->count_records(self::COLLECTION_ITEM_TABLE, ['collectionid' => $collectionid]);
        }

        if (self::table_has_column(self::COLLECTION_ITEM_TABLE, 'mediacollectionid')) {
            return (int)$DB->count_records(self::COLLECTION_ITEM_TABLE, ['mediacollectionid' => $collectionid]);
        }

        return 0;
    }

    /**
     * Normalize visibility.
     *
     * @param string $visibility Visibility.
     * @return string
     */
    private static function normalise_visibility(string $visibility): string {
        $visibility = clean_param(strtolower(trim($visibility)), PARAM_ALPHANUMEXT);

        if ($visibility === 'institutional') {
            $visibility = 'institution';
        }

        if (!in_array($visibility, self::VISIBILITIES, true)) {
            throw new invalid_parameter_exception('Invalid collection visibility.');
        }

        return $visibility;
    }

    /**
     * Normalize status.
     *
     * @param string $status Status.
     * @return string
     */
    private static function normalise_status(string $status): string {
        $status = clean_param(strtolower(trim($status)), PARAM_ALPHANUMEXT);

        if (!in_array($status, self::STATUSES, true)) {
            throw new invalid_parameter_exception('Invalid collection status.');
        }

        return $status;
    }

    /**
     * Normalize metadata JSON.
     *
     * @param string $json JSON.
     * @return string
     */
    private static function normalise_metadata_json(string $json): string {
        $json = trim($json);

        if ($json === '') {
            return '{}';
        }

        $decoded = json_decode($json, true);

        if (!is_array($decoded)) {
            throw new invalid_parameter_exception('metadatajson must be a valid JSON object.');
        }

        return self::metadata_to_json($decoded);
    }

    /**
     * Convert metadata to stable JSON string.
     *
     * @param mixed $metadata Metadata.
     * @return string
     */
    private static function metadata_to_json($metadata): string {
        if (is_string($metadata)) {
            $decoded = json_decode($metadata, true);
            $metadata = is_array($decoded) ? $decoded : [];
        }

        if (!is_array($metadata)) {
            $metadata = [];
        }

        $json = json_encode($metadata, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);

        return $json === false ? '{}' : $json;
    }

    /**
     * Return first available field.
     *
     * @param stdClass $record Record.
     * @param string[] $fields Field candidates.
     * @param mixed $default Default.
     * @return mixed
     */
    private static function field(stdClass $record, array $fields, $default = null) {
        foreach ($fields as $field) {
            if (property_exists($record, $field) && $record->{$field} !== null && $record->{$field} !== '') {
                return $record->{$field};
            }
        }

        return $default;
    }

    /**
     * Require DB table exists.
     *
     * @param string $tablename Table name.
     * @return void
     * @throws moodle_exception
     */
    private static function require_table(string $tablename): void {
        if (!self::table_exists($tablename)) {
            throw new moodle_exception('missingtable', 'error', '', $tablename);
        }
    }

    /**
     * Return whether table exists.
     *
     * @param string $tablename Table name.
     * @return bool
     */
    private static function table_exists(string $tablename): bool {
        global $DB;

        return $DB->get_manager()->table_exists(new xmldb_table($tablename));
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

        if (!self::table_exists($tablename)) {
            return false;
        }

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
     * @return array<string, mixed>
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
