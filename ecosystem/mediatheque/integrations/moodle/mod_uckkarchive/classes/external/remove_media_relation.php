<?php
// This file is part of Moodle - https://moodle.org/.
//
// Moodle is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// any later version.

/**
 * External service for removing a media relation.
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
require_once(dirname(__DIR__) . '/local/media_relation.php');

use context_module;
use core_external\external_api;
use core_external\external_function_parameters;
use core_external\external_multiple_structure;
use core_external\external_single_structure;
use core_external\external_value;
use invalid_parameter_exception;
use mod_uckkarchive\local\media_relation;
use moodle_exception;
use stdClass;

/**
 * Removes one media graph relation.
 *
 * Relations describe graph meaning between media, archive items, Kristals,
 * collections, external works, content markers, proofs, and versions. Removing
 * a relation must not delete media files, transfer ownership, or make restricted
 * material visible.
 *
 * The service accepts either:
 *
 * - a direct `relationid`; or
 * - a relation key: `fromtype`, `fromid`, `totype`, `toid`, and optionally
 *   `relationtype`.
 *
 * If the relation table supports a `status` field, the service marks the
 * relation as removed/deleted. Otherwise it physically deletes the relation row.
 */
final class remove_media_relation extends external_api {
    /** Media relation table. */
    private const TABLE_RELATION = 'uckkarchive_media_relation';

    /** Capability required for relation mutation. */
    private const CAP_EDIT_MEDIA = 'mod/uckkarchive:editmedia';

    /** Capability for media read. */
    private const CAP_VIEW_MEDIA = 'mod/uckkarchive:viewmedia';

    /** Capability for restricted media read. */
    private const CAP_VIEW_RESTRICTED_MEDIA = 'mod/uckkarchive:viewrestrictedmedia';

    /** Capability for collection management. */
    private const CAP_MANAGE_COLLECTIONS = 'mod/uckkarchive:managemediacollections';

    /** Capability for export. */
    private const CAP_EXPORT_MEDIA = 'mod/uckkarchive:exportmedia';

    /**
     * Return external service parameters.
     *
     * @return external_function_parameters
     */
    public static function execute_parameters(): external_function_parameters {
        return new external_function_parameters([
            'cmid' => new external_value(PARAM_INT, 'Course module id'),
            'relationid' => new external_value(PARAM_INT, 'Media relation id. Preferred removal key.', VALUE_DEFAULT, 0),
            'fromtype' => new external_value(PARAM_ALPHANUMEXT, 'Source object type when relationid is not provided.', VALUE_DEFAULT, ''),
            'fromid' => new external_value(PARAM_INT, 'Source object id when relationid is not provided.', VALUE_DEFAULT, 0),
            'totype' => new external_value(PARAM_ALPHANUMEXT, 'Target object type when relationid is not provided.', VALUE_DEFAULT, ''),
            'toid' => new external_value(PARAM_INT, 'Target object id when relationid is not provided.', VALUE_DEFAULT, 0),
            'relationtype' => new external_value(PARAM_ALPHANUMEXT, 'Relation type filter when relationid is not provided.', VALUE_DEFAULT, ''),
            'reason' => new external_value(PARAM_TEXT, 'Optional removal reason.', VALUE_DEFAULT, ''),
        ]);
    }

    /**
     * Execute the service.
     *
     * @param int $cmid Course module id.
     * @param int $relationid Relation id.
     * @param string $fromtype Source object type.
     * @param int $fromid Source object id.
     * @param string $totype Target object type.
     * @param int $toid Target object id.
     * @param string $relationtype Relation type.
     * @param string $reason Removal reason.
     * @return array<string, mixed>
     */
    public static function execute(
        int $cmid,
        int $relationid = 0,
        string $fromtype = '',
        int $fromid = 0,
        string $totype = '',
        int $toid = 0,
        string $relationtype = '',
        string $reason = ''
    ): array {
        $params = self::validate_parameters(self::execute_parameters(), [
            'cmid' => $cmid,
            'relationid' => $relationid,
            'fromtype' => $fromtype,
            'fromid' => $fromid,
            'totype' => $totype,
            'toid' => $toid,
            'relationtype' => $relationtype,
            'reason' => $reason,
        ]);

        [$course, $cm, $archive, $context] = self::load_page((int)$params['cmid']);
        self::validate_context($context);

        require_capability(self::CAP_EDIT_MEDIA, $context);

        $permissions = self::get_permissions($context);

        if (!self::table_exists(self::TABLE_RELATION)) {
            return self::response(
                false,
                false,
                self::empty_relation(),
                $permissions,
                [self::warning('media_relation', 0, 'relationtablenotfound', 'Media relation table is not installed yet.')]
            );
        }

        $relation = self::load_relation(
            (int)$params['relationid'],
            (int)$archive->id,
            (string)$params['fromtype'],
            (int)$params['fromid'],
            (string)$params['totype'],
            (int)$params['toid'],
            (string)$params['relationtype']
        );

        if (!$relation) {
            return self::response(
                false,
                false,
                self::empty_relation(),
                $permissions,
                [self::warning('media_relation', max(0, (int)$params['relationid']), 'relationnotfound', 'Media relation was not found.')]
            );
        }

        if (!self::belongs_to_archive($relation, (int)$archive->id)) {
            return self::response(
                false,
                false,
                self::empty_relation(),
                $permissions,
                [self::warning('media_relation', (int)$relation->id, 'relationnotfound', 'Media relation was not found.')]
            );
        }

        self::validate_relation_record($relation);

        $removed = self::remove_relation($relation, (string)$params['reason']);

        return self::response(
            $removed,
            true,
            self::export_relation($relation),
            $permissions,
            []
        );
    }

    /**
     * Return service response structure.
     *
     * @return external_single_structure
     */
    public static function execute_returns(): external_single_structure {
        return new external_single_structure([
            'removed' => new external_value(PARAM_BOOL, 'Whether the relation was removed by this call'),
            'found' => new external_value(PARAM_BOOL, 'Whether the relation existed and belonged to the archive'),
            'relation' => self::relation_structure(),
            'permissions' => self::permissions_structure(),
            'warnings' => self::warnings_structure(),
        ]);
    }

    /**
     * Return relation response structure.
     *
     * @return external_single_structure
     */
    private static function relation_structure(): external_single_structure {
        return new external_single_structure([
            'id' => new external_value(PARAM_INT, 'Relation id'),
            'uuid' => new external_value(PARAM_TEXT, 'Relation UUID'),
            'archiveid' => new external_value(PARAM_INT, 'Archive instance id'),
            'fromtype' => new external_value(PARAM_ALPHANUMEXT, 'Source object type'),
            'fromid' => new external_value(PARAM_INT, 'Source object id'),
            'totype' => new external_value(PARAM_ALPHANUMEXT, 'Target object type'),
            'toid' => new external_value(PARAM_INT, 'Target object id'),
            'relationtype' => new external_value(PARAM_ALPHANUMEXT, 'Relation type'),
            'sortorder' => new external_value(PARAM_INT, 'Sort order'),
            'status' => new external_value(PARAM_ALPHANUMEXT, 'Relation status'),
            'createdby' => new external_value(PARAM_INT, 'Creator user id'),
            'timecreated' => new external_value(PARAM_INT, 'Created timestamp'),
            'timemodified' => new external_value(PARAM_INT, 'Modified timestamp'),
            'metadatajson' => new external_value(PARAM_RAW, 'Relation metadata JSON'),
        ]);
    }

    /**
     * Return permissions response structure.
     *
     * @return external_single_structure
     */
    private static function permissions_structure(): external_single_structure {
        return new external_single_structure([
            'viewmedia' => new external_value(PARAM_BOOL, 'Can view media'),
            'editmedia' => new external_value(PARAM_BOOL, 'Can edit media'),
            'viewrestrictedmedia' => new external_value(PARAM_BOOL, 'Can view restricted media'),
            'managemediacollections' => new external_value(PARAM_BOOL, 'Can manage media collections'),
            'exportmedia' => new external_value(PARAM_BOOL, 'Can export media'),
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
                'item' => new external_value(PARAM_TEXT, 'Warning item'),
                'itemid' => new external_value(PARAM_INT, 'Warning item id'),
                'warningcode' => new external_value(PARAM_ALPHANUMEXT, 'Warning code'),
                'message' => new external_value(PARAM_TEXT, 'Warning message'),
            ])
        );
    }

    /**
     * Load Moodle page context.
     *
     * @param int $cmid Course module id.
     * @return array{0:stdClass,1:stdClass,2:stdClass,3:context_module}
     */
    private static function load_page(int $cmid): array {
        [$course, $cm, $archive, $context] = \uckkarchive_require_page($cmid, 0);
        return [$course, $cm, $archive, $context];
    }

    /**
     * Load relation by id or relation key.
     *
     * @param int $relationid Relation id.
     * @param int $archiveid Archive instance id.
     * @param string $fromtype Source type.
     * @param int $fromid Source id.
     * @param string $totype Target type.
     * @param int $toid Target id.
     * @param string $relationtype Relation type.
     * @return stdClass|null
     */
    private static function load_relation(
        int $relationid,
        int $archiveid,
        string $fromtype,
        int $fromid,
        string $totype,
        int $toid,
        string $relationtype
    ): ?stdClass {
        global $DB;

        if ($relationid > 0) {
            $record = $DB->get_record(self::TABLE_RELATION, ['id' => $relationid], '*', IGNORE_MISSING);
            return $record ?: null;
        }

        $fromtype = self::normalise_object_type($fromtype);
        $totype = self::normalise_object_type($totype);
        $fromid = self::require_positive_int($fromid, 'fromid');
        $toid = self::require_positive_int($toid, 'toid');

        if ($relationtype !== '') {
            $relationtype = self::normalise_relation_type($relationtype);
        }

        $columns = self::get_columns(self::TABLE_RELATION);
        $archivefield = self::first_column($columns, ['archiveid', 'uckkarchiveid']);
        $fromtypefield = self::first_column($columns, ['fromtype', 'sourceobjecttype', 'sourcetype', 'source_type']);
        $fromidfield = self::first_column($columns, ['fromid', 'sourceobjectid', 'sourceid', 'source_id']);
        $totypefield = self::first_column($columns, ['totype', 'targetobjecttype', 'targettype', 'target_type']);
        $toidfield = self::first_column($columns, ['toid', 'targetobjectid', 'targetid', 'target_id']);
        $relationtypefield = self::first_column($columns, ['relationtype', 'type', 'relation']);

        if ($fromtypefield === null || $fromidfield === null || $totypefield === null || $toidfield === null) {
            throw new moodle_exception('invalidrecord', 'error', '', self::TABLE_RELATION);
        }

        $where = [
            "r.{$fromtypefield} = :fromtype",
            "r.{$fromidfield} = :fromid",
            "r.{$totypefield} = :totype",
            "r.{$toidfield} = :toid",
        ];
        $params = [
            'fromtype' => $fromtype,
            'fromid' => $fromid,
            'totype' => $totype,
            'toid' => $toid,
        ];

        if ($archivefield !== null && $archiveid > 0) {
            $where[] = "r.{$archivefield} = :archiveid";
            $params['archiveid'] = $archiveid;
        }

        if ($relationtypefield !== null && $relationtype !== '') {
            $where[] = "r.{$relationtypefield} = :relationtype";
            $params['relationtype'] = $relationtype;
        }

        if (self::column_exists($columns, 'status')) {
            $where[] = "r.status NOT IN (:deletedsoft, :removed)";
            $params['deletedsoft'] = 'deleted_soft';
            $params['removed'] = 'removed';
        }

        $sql = "SELECT r.*
                  FROM {" . self::TABLE_RELATION . "} r
                 WHERE " . implode(' AND ', $where) . "
              ORDER BY r.id DESC";

        $record = $DB->get_record_sql($sql, $params, IGNORE_MULTIPLE);

        return $record ?: null;
    }

    /**
     * Remove relation row.
     *
     * @param stdClass $relation Relation record.
     * @param string $reason Optional reason.
     * @return bool
     */
    private static function remove_relation(stdClass $relation, string $reason): bool {
        global $DB, $USER;

        $columns = self::get_columns(self::TABLE_RELATION);

        if (self::column_exists($columns, 'status')) {
            $record = new stdClass();
            $record->id = (int)$relation->id;
            $record->status = 'removed';

            if (self::column_exists($columns, 'timemodified')) {
                $record->timemodified = time();
            }

            if (self::column_exists($columns, 'modifiedby')) {
                $record->modifiedby = (int)$USER->id;
            }

            if (self::column_exists($columns, 'deletedby')) {
                $record->deletedby = (int)$USER->id;
            }

            if (self::column_exists($columns, 'deletereason')) {
                $record->deletereason = self::normalise_reason($reason);
            }

            if (self::column_exists($columns, 'removereason')) {
                $record->removereason = self::normalise_reason($reason);
            }

            return $DB->update_record(self::TABLE_RELATION, $record);
        }

        return $DB->delete_records(self::TABLE_RELATION, ['id' => (int)$relation->id]);
    }

    /**
     * Validate relation record through the local model when possible.
     *
     * @param stdClass $relation Relation record.
     * @return void
     */
    private static function validate_relation_record(stdClass $relation): void {
        try {
            $domain = media_relation::from_record($relation);
            $domain->validate();
        } catch (\Throwable $exception) {
            // Existing records may come from older schema names. Hard-fail only
            // if the record lacks the minimum removal identifiers.
            if ((int)($relation->id ?? 0) <= 0) {
                throw $exception;
            }
        }
    }

    /**
     * Export one relation record.
     *
     * @param stdClass $relation Relation record.
     * @return array<string, mixed>
     */
    private static function export_relation(stdClass $relation): array {
        $metadata = self::field($relation, ['metadata', 'metadatajson'], '{}');

        return [
            'id' => (int)self::field($relation, ['id'], 0),
            'uuid' => (string)self::field($relation, ['uuid'], ''),
            'archiveid' => (int)self::field($relation, ['archiveid', 'uckkarchiveid'], 0),
            'fromtype' => (string)self::field($relation, ['fromtype', 'sourceobjecttype', 'sourcetype', 'source_type'], ''),
            'fromid' => (int)self::field($relation, ['fromid', 'sourceobjectid', 'sourceid', 'source_id'], 0),
            'totype' => (string)self::field($relation, ['totype', 'targetobjecttype', 'targettype', 'target_type'], ''),
            'toid' => (int)self::field($relation, ['toid', 'targetobjectid', 'targetid', 'target_id'], 0),
            'relationtype' => (string)self::field($relation, ['relationtype', 'type', 'relation'], ''),
            'sortorder' => (int)self::field($relation, ['sortorder'], 0),
            'status' => 'removed',
            'createdby' => (int)self::field($relation, ['createdby', 'userid'], 0),
            'timecreated' => (int)self::field($relation, ['timecreated'], 0),
            'timemodified' => time(),
            'metadatajson' => self::normalise_metadata_json($metadata),
        ];
    }

    /**
     * Return empty relation payload.
     *
     * @return array<string, mixed>
     */
    private static function empty_relation(): array {
        return [
            'id' => 0,
            'uuid' => '',
            'archiveid' => 0,
            'fromtype' => '',
            'fromid' => 0,
            'totype' => '',
            'toid' => 0,
            'relationtype' => '',
            'sortorder' => 0,
            'status' => '',
            'createdby' => 0,
            'timecreated' => 0,
            'timemodified' => 0,
            'metadatajson' => '{}',
        ];
    }

    /**
     * Build standard response.
     *
     * @param bool $removed Removed flag.
     * @param bool $found Found flag.
     * @param array<string, mixed> $relation Relation payload.
     * @param array<string, bool> $permissions Permissions.
     * @param array<int, array<string, mixed>> $warnings Warnings.
     * @return array<string, mixed>
     */
    private static function response(
        bool $removed,
        bool $found,
        array $relation,
        array $permissions,
        array $warnings
    ): array {
        return [
            'removed' => $removed,
            'found' => $found,
            'relation' => $relation,
            'permissions' => $permissions,
            'warnings' => $warnings,
        ];
    }

    /**
     * Return permissions.
     *
     * @param context_module $context Module context.
     * @return array<string, bool>
     */
    private static function get_permissions(context_module $context): array {
        return [
            'viewmedia' => has_capability(self::CAP_VIEW_MEDIA, $context),
            'editmedia' => has_capability(self::CAP_EDIT_MEDIA, $context),
            'viewrestrictedmedia' => has_capability(self::CAP_VIEW_RESTRICTED_MEDIA, $context),
            'managemediacollections' => has_capability(self::CAP_MANAGE_COLLECTIONS, $context),
            'exportmedia' => has_capability(self::CAP_EXPORT_MEDIA, $context),
        ];
    }

    /**
     * Build warning payload.
     *
     * @param string $item Warning item.
     * @param int $itemid Warning item id.
     * @param string $code Warning code.
     * @param string $message Warning message.
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

    /**
     * Return whether relation belongs to current archive instance.
     *
     * @param stdClass $relation Relation record.
     * @param int $archiveid Archive id.
     * @return bool
     */
    private static function belongs_to_archive(stdClass $relation, int $archiveid): bool {
        $relationarchiveid = (int)self::field($relation, ['archiveid', 'uckkarchiveid'], 0);

        return $archiveid <= 0 || $relationarchiveid <= 0 || $relationarchiveid === $archiveid;
    }

    /**
     * Normalize object type.
     *
     * @param string $type Object type.
     * @return string
     */
    private static function normalise_object_type(string $type): string {
        $type = clean_param(strtolower(trim($type)), PARAM_ALPHANUMEXT);

        if ($type === '') {
            throw new invalid_parameter_exception('Object type is required.');
        }

        if (class_exists(media_relation::class) && method_exists(media_relation::class, 'get_allowed_object_types')) {
            $allowed = media_relation::get_allowed_object_types();
            if (!in_array($type, $allowed, true)) {
                throw new invalid_parameter_exception('Invalid relation object type: ' . $type);
            }
        }

        return $type;
    }

    /**
     * Normalize relation type.
     *
     * @param string $type Relation type.
     * @return string
     */
    private static function normalise_relation_type(string $type): string {
        $type = clean_param(strtolower(trim($type)), PARAM_ALPHANUMEXT);

        if ($type === '') {
            throw new invalid_parameter_exception('Relation type is required.');
        }

        if (class_exists(media_relation::class) && method_exists(media_relation::class, 'get_allowed_relation_types')) {
            $allowed = media_relation::get_allowed_relation_types();
            if (!in_array($type, $allowed, true)) {
                throw new invalid_parameter_exception('Invalid media relation type: ' . $type);
            }
        }

        return $type;
    }

    /**
     * Require positive int.
     *
     * @param int $value Value.
     * @param string $name Param name.
     * @return int
     */
    private static function require_positive_int(int $value, string $name): int {
        if ($value <= 0) {
            throw new invalid_parameter_exception('Invalid ' . $name . '.');
        }

        return $value;
    }

    /**
     * Normalize reason.
     *
     * @param string $reason Reason.
     * @return string
     */
    private static function normalise_reason(string $reason): string {
        return clean_param(trim($reason), PARAM_TEXT);
    }

    /**
     * Normalize metadata JSON.
     *
     * @param mixed $metadata Metadata value.
     * @return string
     */
    private static function normalise_metadata_json(mixed $metadata): string {
        if (is_string($metadata)) {
            $metadata = trim($metadata);
            if ($metadata === '') {
                return '{}';
            }

            $decoded = json_decode($metadata, true);
            if (is_array($decoded)) {
                return json_encode($decoded, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES) ?: '{}';
            }

            return '{}';
        }

        if ($metadata instanceof stdClass) {
            $metadata = (array)$metadata;
        }

        if (!is_array($metadata)) {
            return '{}';
        }

        return json_encode($metadata, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES) ?: '{}';
    }

    /**
     * Return field value using candidate names.
     *
     * @param stdClass $record Record.
     * @param string[] $fields Candidate fields.
     * @param mixed $default Default value.
     * @return mixed
     */
    private static function field(stdClass $record, array $fields, mixed $default = null): mixed {
        foreach ($fields as $field) {
            if (property_exists($record, $field) && $record->{$field} !== null && $record->{$field} !== '') {
                return $record->{$field};
            }
        }

        return $default;
    }

    /**
     * Return whether table exists.
     *
     * @param string $tablename Table name without braces.
     * @return bool
     */
    private static function table_exists(string $tablename): bool {
        global $DB;

        return $DB->get_manager()->table_exists(new \xmldb_table($tablename));
    }

    /**
     * Return table columns.
     *
     * @param string $tablename Table name without braces.
     * @return array<string, object>
     */
    private static function get_columns(string $tablename): array {
        global $DB;

        return $DB->get_columns($tablename);
    }

    /**
     * Return whether a column exists.
     *
     * @param array<string, object> $columns Columns.
     * @param string $field Field name.
     * @return bool
     */
    private static function column_exists(array $columns, string $field): bool {
        return array_key_exists($field, $columns);
    }

    /**
     * Return first existing column.
     *
     * @param array<string, object> $columns Columns.
     * @param string[] $candidates Candidate fields.
     * @return string|null
     */
    private static function first_column(array $columns, array $candidates): ?string {
        foreach ($candidates as $candidate) {
            if (self::column_exists($columns, $candidate)) {
                return $candidate;
            }
        }

        return null;
    }
}
