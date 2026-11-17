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

/**
 * External service for adding media relations to UCKK Archive.
 *
 * @package    mod_uckkarchive
 * @copyright  2026 UCKK
 * @license    http://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later
 */

namespace mod_uckkarchive\external;

use context_module;
use external_api;
use external_function_parameters;
use external_single_structure;
use external_value;
use invalid_parameter_exception;
use mod_uckkarchive\local\media_policy;
use mod_uckkarchive\local\media_relation;
use stdClass;

defined('MOODLE_INTERNAL') || die();

require_once($CFG->libdir . '/externallib.php');

/**
 * Add media relation external service.
 *
 * This service creates one graph relation between a media object and another
 * module-owned object: media, media version, archive item, proof, Kristal,
 * media collection, content marker, or external work.
 *
 * It validates the relation shape through {@see media_relation}, checks Moodle
 * context/capability gates, verifies that source and target objects exist, and
 * inserts the relation into `{uckkarchive_media_relation}`.
 *
 * The service does not transfer external ownership or bypass cultural,
 * advisory, restricted, export, privacy, or File API policy.
 */
final class add_media_relation extends external_api {
    /** Media relation table. */
    private const TABLE = 'uckkarchive_media_relation';

    /** Media table. */
    private const TABLE_MEDIA = 'uckkarchive_media';

    /** Media version table. */
    private const TABLE_MEDIA_VERSION = 'uckkarchive_media_version';

    /** Archive item table. */
    private const TABLE_ITEM = 'uckkarchive_item';

    /** Proof table. */
    private const TABLE_PROOF = 'uckkarchive_proof';

    /** Kristal table. */
    private const TABLE_KRISTAL = 'uckkarchive_kristal';

    /** Media collection table. */
    private const TABLE_COLLECTION = 'uckkarchive_media_collection';

    /** Content marker table. */
    private const TABLE_CONTENT_MARKER = 'uckkarchive_content_marker';

    /** External work table. */
    private const TABLE_EXTERNAL_WORK = 'uckkarchive_external_work';

    /**
     * Describe service parameters.
     *
     * @return external_function_parameters
     */
    public static function execute_parameters(): external_function_parameters {
        return new external_function_parameters([
            'cmid' => new external_value(PARAM_INT, 'Course module id for the UCKK Archive instance.'),
            'fromtype' => new external_value(PARAM_ALPHANUMEXT, 'Source object type.'),
            'fromid' => new external_value(PARAM_INT, 'Source object id.'),
            'totype' => new external_value(PARAM_ALPHANUMEXT, 'Target object type.'),
            'toid' => new external_value(PARAM_INT, 'Target object id.'),
            'relationtype' => new external_value(PARAM_ALPHANUMEXT, 'Relation type.'),
            'sortorder' => new external_value(PARAM_INT, 'Sort order.', VALUE_DEFAULT, 0),
            'metadatajson' => new external_value(PARAM_RAW, 'Optional JSON metadata.', VALUE_DEFAULT, '{}'),
        ]);
    }

    /**
     * Execute service.
     *
     * @param int $cmid Course module id.
     * @param string $fromtype Source object type.
     * @param int $fromid Source object id.
     * @param string $totype Target object type.
     * @param int $toid Target object id.
     * @param string $relationtype Relation type.
     * @param int $sortorder Sort order.
     * @param string $metadatajson Optional JSON metadata.
     * @return array Result.
     */
    public static function execute(
        int $cmid,
        string $fromtype,
        int $fromid,
        string $totype,
        int $toid,
        string $relationtype,
        int $sortorder = 0,
        string $metadatajson = '{}'
    ): array {
        global $DB, $USER;

        [
            'cmid' => $cmid,
            'fromtype' => $fromtype,
            'fromid' => $fromid,
            'totype' => $totype,
            'toid' => $toid,
            'relationtype' => $relationtype,
            'sortorder' => $sortorder,
            'metadatajson' => $metadatajson,
        ] = self::validate_parameters(self::execute_parameters(), [
            'cmid' => $cmid,
            'fromtype' => $fromtype,
            'fromid' => $fromid,
            'totype' => $totype,
            'toid' => $toid,
            'relationtype' => $relationtype,
            'sortorder' => $sortorder,
            'metadatajson' => $metadatajson,
        ]);

        self::require_table(self::TABLE);

        $cm = get_coursemodule_from_id('uckkarchive', $cmid, 0, false, MUST_EXIST);
        $course = $DB->get_record('course', ['id' => $cm->course], '*', MUST_EXIST);
        $archive = $DB->get_record('uckkarchive', ['id' => $cm->instance], '*', MUST_EXIST);
        $context = context_module::instance($cm->id);

        self::validate_context($context);
        require_login($course, false, $cm);

        $fromtype = self::normalise_object_type($fromtype);
        $totype = self::normalise_object_type($totype);
        $relationtype = self::normalise_relation_type($relationtype);
        $fromid = self::require_positive_id($fromid, 'fromid');
        $toid = self::require_positive_id($toid, 'toid');
        $sortorder = max(0, $sortorder);
        $metadata = self::decode_metadata($metadatajson);

        self::require_relation_capability($context, $fromtype, $totype, $relationtype);

        $fromrecord = self::get_required_target_record($fromtype, $fromid);
        $torecord = self::get_required_target_record($totype, $toid);

        self::require_object_belongs_to_archive($fromtype, $fromrecord, (int)$archive->id);
        self::require_object_belongs_to_archive($totype, $torecord, (int)$archive->id);

        self::require_endpoint_media_policy($context, $fromtype, $fromrecord);
        self::require_endpoint_media_policy($context, $totype, $torecord);

        $relation = media_relation::create(
            (int)$archive->id,
            $fromtype,
            $fromid,
            $totype,
            $toid,
            $relationtype
        )->with_sortorder($sortorder)
            ->with_metadata($metadata)
            ->with_creation((int)$USER->id);

        $record = self::filter_record_for_table($relation->to_record((int)$USER->id));

        $transaction = $DB->start_delegated_transaction();
        $id = (int)$DB->insert_record(self::TABLE, $record);
        $transaction->allow_commit();

        $created = $DB->get_record(self::TABLE, ['id' => $id], '*', MUST_EXIST);

        return self::format_relation_response($created, $context);
    }

    /**
     * Describe service return structure.
     *
     * @return external_single_structure
     */
    public static function execute_returns(): external_single_structure {
        return new external_single_structure([
            'id' => new external_value(PARAM_INT, 'Relation id.'),
            'uuid' => new external_value(PARAM_RAW, 'Stable relation UUID.'),
            'archiveid' => new external_value(PARAM_INT, 'Archive instance id.'),
            'fromtype' => new external_value(PARAM_ALPHANUMEXT, 'Source object type.'),
            'fromid' => new external_value(PARAM_INT, 'Source object id.'),
            'totype' => new external_value(PARAM_ALPHANUMEXT, 'Target object type.'),
            'toid' => new external_value(PARAM_INT, 'Target object id.'),
            'relationtype' => new external_value(PARAM_ALPHANUMEXT, 'Relation type.'),
            'sortorder' => new external_value(PARAM_INT, 'Sort order.'),
            'createdby' => new external_value(PARAM_INT, 'Creator user id.'),
            'timecreated' => new external_value(PARAM_INT, 'Creation timestamp.'),
            'metadatajson' => new external_value(PARAM_RAW, 'JSON metadata.'),
            'caneditmedia' => new external_value(PARAM_BOOL, 'Whether the current user can edit media.'),
            'canmanagecollections' => new external_value(PARAM_BOOL, 'Whether the current user can manage media collections.'),
            'canmanageadvisories' => new external_value(PARAM_BOOL, 'Whether the current user can manage content advisories.'),
            'canmanageexternalworks' => new external_value(PARAM_BOOL, 'Whether the current user can manage external works.'),
        ]);
    }

    /**
     * Require the capability needed for a relation shape.
     *
     * @param context_module $context Module context.
     * @param string $fromtype Source object type.
     * @param string $totype Target object type.
     * @param string $relationtype Relation type.
     * @return void
     */
    private static function require_relation_capability(
        context_module $context,
        string $fromtype,
        string $totype,
        string $relationtype
    ): void {
        if ($fromtype === media_relation::OBJECT_MEDIA_COLLECTION ||
                $totype === media_relation::OBJECT_MEDIA_COLLECTION ||
                $relationtype === media_relation::TYPE_BELONGS_TO_COLLECTION) {
            require_capability('mod/uckkarchive:managemediacollections', $context);
            return;
        }

        if ($fromtype === media_relation::OBJECT_CONTENT_MARKER ||
                $totype === media_relation::OBJECT_CONTENT_MARKER ||
                $relationtype === media_relation::TYPE_CONTAINS_CONTENT_MARKER) {
            require_capability('mod/uckkarchive:manageadvisories', $context);
            return;
        }

        if ($fromtype === media_relation::OBJECT_EXTERNAL_WORK ||
                $totype === media_relation::OBJECT_EXTERNAL_WORK ||
                $relationtype === media_relation::TYPE_REFERENCES_EXTERNAL_WORK) {
            require_capability('mod/uckkarchive:manageexternalworks', $context);
            return;
        }

        require_capability('mod/uckkarchive:editmedia', $context);
    }

    /**
     * Apply media policy for media endpoints.
     *
     * @param context_module $context Module context.
     * @param string $type Endpoint type.
     * @param stdClass $record Endpoint record.
     * @return void
     */
    private static function require_endpoint_media_policy(context_module $context, string $type, stdClass $record): void {
        if ($type !== media_relation::OBJECT_MEDIA) {
            return;
        }

        if (class_exists(media_policy::class) && method_exists(media_policy::class, 'require_edit_media')) {
            media_policy::require_edit_media($context, $record);
            return;
        }

        require_capability('mod/uckkarchive:editmedia', $context);
    }

    /**
     * Get a required endpoint record.
     *
     * @param string $type Object type.
     * @param int $id Object id.
     * @return stdClass
     */
    private static function get_required_target_record(string $type, int $id): stdClass {
        global $DB;

        $table = self::table_for_object_type($type);
        self::require_table($table);

        return $DB->get_record($table, ['id' => $id], '*', MUST_EXIST);
    }

    /**
     * Require that an endpoint record belongs to the current archive when possible.
     *
     * @param string $type Object type.
     * @param stdClass $record Record.
     * @param int $archiveid Archive id.
     * @return void
     */
    private static function require_object_belongs_to_archive(string $type, stdClass $record, int $archiveid): void {
        $field = self::archive_field_for_record($record);

        if ($field === null) {
            return;
        }

        if ((int)$record->{$field} !== $archiveid) {
            throw new invalid_parameter_exception($type . ' does not belong to this UCKK Archive instance.');
        }
    }

    /**
     * Return matching archive id field for a record.
     *
     * @param stdClass $record Record.
     * @return string|null
     */
    private static function archive_field_for_record(stdClass $record): ?string {
        foreach (['archiveid', 'uckkarchiveid'] as $field) {
            if (property_exists($record, $field)) {
                return $field;
            }
        }

        return null;
    }

    /**
     * Return table for object type.
     *
     * @param string $type Object type.
     * @return string
     */
    private static function table_for_object_type(string $type): string {
        return match ($type) {
            media_relation::OBJECT_MEDIA => self::TABLE_MEDIA,
            media_relation::OBJECT_MEDIA_VERSION => self::TABLE_MEDIA_VERSION,
            media_relation::OBJECT_ARCHIVE_ITEM => self::TABLE_ITEM,
            media_relation::OBJECT_PROOF => self::TABLE_PROOF,
            media_relation::OBJECT_KRISTAL => self::TABLE_KRISTAL,
            media_relation::OBJECT_MEDIA_COLLECTION => self::TABLE_COLLECTION,
            media_relation::OBJECT_CONTENT_MARKER => self::TABLE_CONTENT_MARKER,
            media_relation::OBJECT_EXTERNAL_WORK => self::TABLE_EXTERNAL_WORK,
            default => throw new invalid_parameter_exception('Unsupported media relation object type: ' . $type),
        };
    }

    /**
     * Normalize object type through the local relation domain class.
     *
     * @param string $type Raw object type.
     * @return string
     */
    private static function normalise_object_type(string $type): string {
        $candidate = new media_relation([
            'archiveid' => 1,
            'fromtype' => $type,
            'fromid' => 1,
            'totype' => media_relation::OBJECT_MEDIA,
            'toid' => 2,
            'relationtype' => media_relation::TYPE_REFERENCES,
        ]);

        return $candidate->get_fromtype();
    }

    /**
     * Normalize relation type through the local relation domain class.
     *
     * @param string $relationtype Raw relation type.
     * @return string
     */
    private static function normalise_relation_type(string $relationtype): string {
        $candidate = new media_relation([
            'archiveid' => 1,
            'fromtype' => media_relation::OBJECT_MEDIA,
            'fromid' => 1,
            'totype' => media_relation::OBJECT_MEDIA,
            'toid' => 2,
            'relationtype' => $relationtype,
        ]);

        return $candidate->get_relationtype();
    }

    /**
     * Decode metadata JSON.
     *
     * @param string $metadatajson JSON metadata.
     * @return array
     */
    private static function decode_metadata(string $metadatajson): array {
        $metadatajson = trim($metadatajson);

        if ($metadatajson === '') {
            return [];
        }

        $decoded = json_decode($metadatajson, true);

        if (!is_array($decoded)) {
            throw new invalid_parameter_exception('metadatajson must be a JSON object.');
        }

        return $decoded;
    }

    /**
     * Filter a record to real table columns.
     *
     * @param stdClass $record Record.
     * @return stdClass
     */
    private static function filter_record_for_table(stdClass $record): stdClass {
        global $DB;

        $columns = $DB->get_columns(self::TABLE);
        $filtered = new stdClass();

        foreach ($columns as $column => $definition) {
            if (property_exists($record, $column)) {
                $filtered->{$column} = $record->{$column};
            }
        }

        return $filtered;
    }

    /**
     * Format relation response.
     *
     * @param stdClass $relation Relation record.
     * @param context_module $context Context.
     * @return array
     */
    private static function format_relation_response(stdClass $relation, context_module $context): array {
        return [
            'id' => (int)$relation->id,
            'uuid' => (string)($relation->uuid ?? ''),
            'archiveid' => (int)($relation->archiveid ?? $relation->uckkarchiveid ?? 0),
            'fromtype' => (string)($relation->fromtype ?? ''),
            'fromid' => (int)($relation->fromid ?? 0),
            'totype' => (string)($relation->totype ?? ''),
            'toid' => (int)($relation->toid ?? 0),
            'relationtype' => (string)($relation->relationtype ?? ''),
            'sortorder' => (int)($relation->sortorder ?? 0),
            'createdby' => (int)($relation->createdby ?? 0),
            'timecreated' => (int)($relation->timecreated ?? 0),
            'metadatajson' => (string)($relation->metadata ?? '{}'),
            'caneditmedia' => has_capability('mod/uckkarchive:editmedia', $context),
            'canmanagecollections' => has_capability('mod/uckkarchive:managemediacollections', $context),
            'canmanageadvisories' => has_capability('mod/uckkarchive:manageadvisories', $context),
            'canmanageexternalworks' => has_capability('mod/uckkarchive:manageexternalworks', $context),
        ];
    }

    /**
     * Require table exists.
     *
     * @param string $table Table name.
     * @return void
     */
    private static function require_table(string $table): void {
        global $DB;

        if (!$DB->get_manager()->table_exists(new \xmldb_table($table))) {
            throw new \coding_exception('Missing required table {' . $table . '}.');
        }
    }

    /**
     * Require positive id.
     *
     * @param int $id Id.
     * @param string $name Name.
     * @return int
     */
    private static function require_positive_id(int $id, string $name): int {
        if ($id <= 0) {
            throw new invalid_parameter_exception($name . ' must be a positive integer.');
        }

        return $id;
    }
}
