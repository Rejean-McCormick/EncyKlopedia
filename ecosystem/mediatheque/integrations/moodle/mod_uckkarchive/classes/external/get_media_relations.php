<?php
// This file is part of Moodle - https://moodle.org/
//
// Moodle is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// any later version.

/**
 * Return permission-filtered media relations.
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
use mod_uckkarchive\local\media_policy;
use mod_uckkarchive\local\media_relation;
use moodle_exception;
use stdClass;

/**
 * External service for retrieving the media relation graph.
 *
 * This endpoint reads `uckkarchive_media_relation`.
 *
 * It supports:
 *
 * - media-centric reads by `mediaid` or `mediauuid`;
 * - direct graph reads by `fromtype/fromid` and/or `totype/toid`;
 * - relation type filtering;
 * - direction filtering;
 * - relation metadata inclusion;
 * - optional related object summaries.
 *
 * Permission rule:
 *
 * - the caller must have `mod/uckkarchive:viewmedia`;
 * - if a relation endpoint is a media object, that media object must also be
 *   visible to the caller;
 * - content marker relations require `mod/uckkarchive:viewadvisories`;
 * - restricted/cultural media remain hidden unless the caller has the required
 *   capability through `media_policy`.
 */
final class get_media_relations extends external_api {
    /** Media relation table. */
    private const TABLE_RELATION = 'uckkarchive_media_relation';

    /** Media table. */
    private const TABLE_MEDIA = 'uckkarchive_media';

    /** Content marker table. */
    private const TABLE_CONTENT_MARKER = 'uckkarchive_content_marker';

    /** External work table. */
    private const TABLE_EXTERNAL_WORK = 'uckkarchive_external_work';

    /** Media collection table. */
    private const TABLE_MEDIA_COLLECTION = 'uckkarchive_media_collection';

    /** Default page size. */
    private const DEFAULT_PERPAGE = 50;

    /** Maximum page size. */
    private const MAX_PERPAGE = 200;

    /** Direction: media appears as source. */
    private const DIRECTION_FROM = 'from';

    /** Direction: media appears as target. */
    private const DIRECTION_TO = 'to';

    /** Direction: media appears on either side. */
    private const DIRECTION_ANY = 'any';

    /** Direction: exact from/to filters only. */
    private const DIRECTION_EXACT = 'exact';

    /**
     * Load the Moodle page context.
     *
     * @param int $cmid Course module id.
     * @return array{0:stdClass,1:stdClass,2:stdClass,3:context_module}
     */
    protected static function load_page(int $cmid): array {
        [$course, $cm, $archive, $context] = \uckkarchive_require_page($cmid, 0);

        return [$course, $cm, $archive, $context];
    }

    /**
     * Return service parameters.
     *
     * @return external_function_parameters
     */
    public static function execute_parameters(): external_function_parameters {
        return new external_function_parameters([
            'cmid' => new external_value(PARAM_INT, 'Course module id'),
            'mediaid' => new external_value(PARAM_INT, 'Media id used for media-centric lookup', VALUE_DEFAULT, 0),
            'mediauuid' => new external_value(PARAM_TEXT, 'Media UUID used for media-centric lookup', VALUE_DEFAULT, ''),
            'direction' => new external_value(PARAM_ALPHA, 'Relation direction: any, from, to, exact', VALUE_DEFAULT, self::DIRECTION_ANY),
            'fromtype' => new external_value(PARAM_ALPHANUMEXT, 'Source object type filter', VALUE_DEFAULT, ''),
            'fromid' => new external_value(PARAM_INT, 'Source object id filter', VALUE_DEFAULT, 0),
            'totype' => new external_value(PARAM_ALPHANUMEXT, 'Target object type filter', VALUE_DEFAULT, ''),
            'toid' => new external_value(PARAM_INT, 'Target object id filter', VALUE_DEFAULT, 0),
            'relationtype' => new external_value(PARAM_ALPHANUMEXT, 'Relation type filter', VALUE_DEFAULT, ''),
            'include' => new external_multiple_structure(
                new external_value(PARAM_ALPHANUMEXT, 'Include value: metadata, related, permissions'),
                'Additional response sections',
                VALUE_DEFAULT,
                []
            ),
            'page' => new external_value(PARAM_INT, 'Zero-based page number', VALUE_DEFAULT, 0),
            'perpage' => new external_value(PARAM_INT, 'Relations per page', VALUE_DEFAULT, self::DEFAULT_PERPAGE),
            'sort' => new external_value(PARAM_ALPHANUMEXT, 'Sort field: sortorder, timecreated, relationtype, id', VALUE_DEFAULT, 'sortorder'),
            'directionorder' => new external_value(PARAM_ALPHA, 'Sort direction: asc or desc', VALUE_DEFAULT, 'asc'),
        ]);
    }

    /**
     * Execute the service.
     *
     * @param int $cmid Course module id.
     * @param int $mediaid Media id.
     * @param string $mediauuid Media UUID.
     * @param string $direction Relation direction.
     * @param string $fromtype Source type.
     * @param int $fromid Source id.
     * @param string $totype Target type.
     * @param int $toid Target id.
     * @param string $relationtype Relation type.
     * @param string[] $include Include values.
     * @param int $page Page.
     * @param int $perpage Per page.
     * @param string $sort Sort field.
     * @param string $directionorder Sort direction.
     * @return array<string, mixed>
     */
    public static function execute(
        int $cmid,
        int $mediaid = 0,
        string $mediauuid = '',
        string $direction = self::DIRECTION_ANY,
        string $fromtype = '',
        int $fromid = 0,
        string $totype = '',
        int $toid = 0,
        string $relationtype = '',
        array $include = [],
        int $page = 0,
        int $perpage = self::DEFAULT_PERPAGE,
        string $sort = 'sortorder',
        string $directionorder = 'asc'
    ): array {
        global $DB;

        $params = self::validate_parameters(self::execute_parameters(), [
            'cmid' => $cmid,
            'mediaid' => $mediaid,
            'mediauuid' => $mediauuid,
            'direction' => $direction,
            'fromtype' => $fromtype,
            'fromid' => $fromid,
            'totype' => $totype,
            'toid' => $toid,
            'relationtype' => $relationtype,
            'include' => $include,
            'page' => $page,
            'perpage' => $perpage,
            'sort' => $sort,
            'directionorder' => $directionorder,
        ]);

        [$course, $cm, $archive, $context] = self::load_page((int)$params['cmid']);
        self::validate_context($context);

        require_capability('mod/uckkarchive:viewmedia', $context);

        $warnings = [];

        if (!self::table_exists(self::TABLE_RELATION)) {
            return self::empty_response(
                self::normalise_page((int)$params['page']),
                self::normalise_perpage((int)$params['perpage']),
                self::permissions($context),
                [self::warning('relation', 0, 'relationtablenotfound', 'Media relation table is not installed yet.')]
            );
        }

        $media = self::load_media_filter((int)$archive->id, (int)$params['mediaid'], (string)$params['mediauuid']);
        if ($media && !self::can_view_media($context, $media)) {
            throw new moodle_exception('nopermissions', 'error', '', 'Cannot view this media object.');
        }

        $filters = [
            'archiveid' => (int)$archive->id,
            'media' => $media,
            'direction' => self::normalise_direction((string)$params['direction']),
            'fromtype' => self::normalise_object_type((string)$params['fromtype']),
            'fromid' => max(0, (int)$params['fromid']),
            'totype' => self::normalise_object_type((string)$params['totype']),
            'toid' => max(0, (int)$params['toid']),
            'relationtype' => self::normalise_relation_type((string)$params['relationtype']),
        ];

        self::validate_filter_combination($filters);

        $include = self::normalise_include((array)$params['include']);
        $page = self::normalise_page((int)$params['page']);
        $perpage = self::normalise_perpage((int)$params['perpage']);
        $sort = self::normalise_sort((string)$params['sort']);
        $directionorder = self::normalise_sort_direction((string)$params['directionorder']);

        $query = self::build_query($filters, $sort, $directionorder);
        $records = $DB->get_records_sql($query['sql'], $query['params']);

        $visible = [];

        foreach ($records as $record) {
            if (!self::can_view_relation($context, $record)) {
                $warnings[] = self::warning(
                    'relation',
                    (int)$record->id,
                    'relationhidden',
                    'A media relation was hidden because one endpoint is not visible to the current user.'
                );
                continue;
            }

            $visible[] = self::export_relation($context, $record, $include);
        }

        $total = count($visible);
        $pageitems = array_slice($visible, $page * $perpage, $perpage);

        return [
            'relations' => $pageitems,
            'pagination' => [
                'page' => $page,
                'perpage' => $perpage,
                'total' => $total,
                'returned' => count($pageitems),
                'hasmore' => (($page + 1) * $perpage) < $total,
            ],
            'permissions' => self::permissions($context),
            'warnings' => $warnings,
        ];
    }

    /**
     * Return service response structure.
     *
     * @return external_single_structure
     */
    public static function execute_returns(): external_single_structure {
        return new external_single_structure([
            'relations' => new external_multiple_structure(
                new external_single_structure([
                    'id' => new external_value(PARAM_INT, 'Relation id'),
                    'uuid' => new external_value(PARAM_TEXT, 'Relation UUID'),
                    'archiveid' => new external_value(PARAM_INT, 'Archive id'),
                    'fromtype' => new external_value(PARAM_ALPHANUMEXT, 'Source object type'),
                    'fromid' => new external_value(PARAM_INT, 'Source object id'),
                    'totype' => new external_value(PARAM_ALPHANUMEXT, 'Target object type'),
                    'toid' => new external_value(PARAM_INT, 'Target object id'),
                    'relationtype' => new external_value(PARAM_ALPHANUMEXT, 'Relation type'),
                    'sortorder' => new external_value(PARAM_INT, 'Sort order'),
                    'createdby' => new external_value(PARAM_INT, 'Creator user id'),
                    'timecreated' => new external_value(PARAM_INT, 'Creation timestamp'),
                    'metadata' => new external_value(PARAM_RAW, 'Relation metadata JSON', VALUE_OPTIONAL),
                    'from' => self::related_object_structure('Source object summary', VALUE_OPTIONAL),
                    'to' => self::related_object_structure('Target object summary', VALUE_OPTIONAL),
                ])
            ),
            'pagination' => new external_single_structure([
                'page' => new external_value(PARAM_INT, 'Current zero-based page'),
                'perpage' => new external_value(PARAM_INT, 'Relations per page'),
                'total' => new external_value(PARAM_INT, 'Total visible relations'),
                'returned' => new external_value(PARAM_INT, 'Returned visible relations'),
                'hasmore' => new external_value(PARAM_BOOL, 'Whether more visible relations exist'),
            ]),
            'permissions' => new external_single_structure([
                'viewmedia' => new external_value(PARAM_BOOL, 'Can view media'),
                'viewrestrictedmedia' => new external_value(PARAM_BOOL, 'Can view restricted media'),
                'viewculturallyrestricted' => new external_value(PARAM_BOOL, 'Can view culturally restricted media'),
                'editmedia' => new external_value(PARAM_BOOL, 'Can edit media'),
                'managemediacollections' => new external_value(PARAM_BOOL, 'Can manage media collections'),
                'manageadvisories' => new external_value(PARAM_BOOL, 'Can manage advisories'),
                'viewadvisories' => new external_value(PARAM_BOOL, 'Can view advisories'),
                'manageexternalworks' => new external_value(PARAM_BOOL, 'Can manage external works'),
            ]),
            'warnings' => new external_multiple_structure(
                new external_single_structure([
                    'item' => new external_value(PARAM_TEXT, 'Warning item'),
                    'itemid' => new external_value(PARAM_INT, 'Warning item id'),
                    'warningcode' => new external_value(PARAM_ALPHANUMEXT, 'Warning code'),
                    'message' => new external_value(PARAM_TEXT, 'Warning message'),
                ])
            ),
        ]);
    }

    /**
     * Related object response structure.
     *
     * @param string $description Description.
     * @param int $required Required flag.
     * @return external_single_structure
     */
    protected static function related_object_structure(string $description, int $required = VALUE_REQUIRED): external_single_structure {
        return new external_single_structure([
            'type' => new external_value(PARAM_ALPHANUMEXT, 'Object type'),
            'id' => new external_value(PARAM_INT, 'Object id'),
            'uuid' => new external_value(PARAM_TEXT, 'Object UUID'),
            'title' => new external_value(PARAM_TEXT, 'Object title'),
            'status' => new external_value(PARAM_ALPHANUMEXT, 'Object status'),
            'visibility' => new external_value(PARAM_ALPHANUMEXT, 'Object visibility'),
            'available' => new external_value(PARAM_BOOL, 'Whether the object summary was found and visible'),
        ], $description, $required);
    }

    /**
     * Build query.
     *
     * @param array<string, mixed> $filters Filters.
     * @param string $sort Sort field.
     * @param string $directionorder Sort direction.
     * @return array{sql:string,params:array<string,mixed>}
     */
    protected static function build_query(array $filters, string $sort, string $directionorder): array {
        $params = ['archiveid' => (int)$filters['archiveid']];
        $where = ['archiveid = :archiveid'];

        if ($filters['media']) {
            $mediaid = (int)$filters['media']->id;
            $params['mediaid'] = $mediaid;

            switch ($filters['direction']) {
                case self::DIRECTION_FROM:
                    $where[] = 'fromtype = :mediafromtype AND fromid = :mediaid';
                    $params['mediafromtype'] = 'media';
                    break;

                case self::DIRECTION_TO:
                    $where[] = 'totype = :mediatotype AND toid = :mediaid';
                    $params['mediatotype'] = 'media';
                    break;

                case self::DIRECTION_EXACT:
                    // Do not add automatic media-centric filters. Exact mode uses explicit from/to filters below.
                    break;

                case self::DIRECTION_ANY:
                default:
                    $where[] = '((fromtype = :mediafromtype AND fromid = :mediafromid) OR ' .
                        '(totype = :mediatotype AND toid = :mediatounid))';
                    $params['mediafromtype'] = 'media';
                    $params['mediafromid'] = $mediaid;
                    $params['mediatotype'] = 'media';
                    $params['mediatounid'] = $mediaid;
                    break;
            }
        }

        if ($filters['fromtype'] !== '') {
            $where[] = 'fromtype = :fromtype';
            $params['fromtype'] = $filters['fromtype'];
        }

        if ($filters['fromid'] > 0) {
            $where[] = 'fromid = :fromid';
            $params['fromid'] = $filters['fromid'];
        }

        if ($filters['totype'] !== '') {
            $where[] = 'totype = :totype';
            $params['totype'] = $filters['totype'];
        }

        if ($filters['toid'] > 0) {
            $where[] = 'toid = :toid';
            $params['toid'] = $filters['toid'];
        }

        if ($filters['relationtype'] !== '') {
            $where[] = 'relationtype = :relationtype';
            $params['relationtype'] = $filters['relationtype'];
        }

        $sql = "SELECT *
                  FROM {" . self::TABLE_RELATION . "}
                 WHERE " . implode(' AND ', $where) . "
              ORDER BY {$sort} {$directionorder}, id {$directionorder}";

        return [
            'sql' => $sql,
            'params' => $params,
        ];
    }

    /**
     * Load a media filter record.
     *
     * @param int $archiveid Archive id.
     * @param int $mediaid Media id.
     * @param string $mediauuid Media UUID.
     * @return stdClass|null
     */
    protected static function load_media_filter(int $archiveid, int $mediaid, string $mediauuid): ?stdClass {
        global $DB;

        $mediauuid = trim($mediauuid);

        if ($mediaid <= 0 && $mediauuid === '') {
            return null;
        }

        if (!self::table_exists(self::TABLE_MEDIA)) {
            throw new moodle_exception('missingtable', 'error', '', self::TABLE_MEDIA);
        }

        $conditions = ['archiveid' => $archiveid];

        if ($mediaid > 0) {
            $conditions['id'] = $mediaid;
        } else {
            $conditions['uuid'] = $mediauuid;
        }

        return $DB->get_record(self::TABLE_MEDIA, $conditions, '*', MUST_EXIST);
    }

    /**
     * Export one relation.
     *
     * @param context_module $context Context.
     * @param stdClass $record Relation record.
     * @param string[] $include Include values.
     * @return array<string, mixed>
     */
    protected static function export_relation(context_module $context, stdClass $record, array $include): array {
        $relation = [
            'id' => (int)$record->id,
            'uuid' => (string)($record->uuid ?? ''),
            'archiveid' => (int)($record->archiveid ?? 0),
            'fromtype' => (string)($record->fromtype ?? ''),
            'fromid' => (int)($record->fromid ?? 0),
            'totype' => (string)($record->totype ?? ''),
            'toid' => (int)($record->toid ?? 0),
            'relationtype' => (string)($record->relationtype ?? ''),
            'sortorder' => (int)($record->sortorder ?? 0),
            'createdby' => (int)($record->createdby ?? 0),
            'timecreated' => (int)($record->timecreated ?? 0),
        ];

        if (in_array('metadata', $include, true)) {
            $relation['metadata'] = self::normalise_metadata_json($record->metadata ?? '{}');
        }

        if (in_array('related', $include, true)) {
            $relation['from'] = self::related_object_summary($context, (string)$record->fromtype, (int)$record->fromid);
            $relation['to'] = self::related_object_summary($context, (string)$record->totype, (int)$record->toid);
        }

        return $relation;
    }

    /**
     * Return whether current user can view relation.
     *
     * @param context_module $context Context.
     * @param stdClass $relation Relation record.
     * @return bool
     */
    protected static function can_view_relation(context_module $context, stdClass $relation): bool {
        if (self::relation_touches_content_marker($relation) &&
                !has_capability('mod/uckkarchive:viewadvisories', $context)) {
            return false;
        }

        foreach ([['type' => $relation->fromtype ?? '', 'id' => (int)($relation->fromid ?? 0)],
                  ['type' => $relation->totype ?? '', 'id' => (int)($relation->toid ?? 0)]] as $endpoint) {
            if ($endpoint['type'] !== 'media') {
                continue;
            }

            $media = self::load_object_record(self::TABLE_MEDIA, $endpoint['id']);
            if (!$media || !self::can_view_media($context, $media)) {
                return false;
            }
        }

        return true;
    }

    /**
     * Return whether current user can view media.
     *
     * @param context_module $context Context.
     * @param stdClass $media Media record.
     * @return bool
     */
    protected static function can_view_media(context_module $context, stdClass $media): bool {
        if (class_exists(media_policy::class)) {
            return media_policy::can_view_media($context, $media);
        }

        if (!has_capability('mod/uckkarchive:viewmedia', $context)) {
            return false;
        }

        $visibility = (string)($media->visibility ?? '');
        if (in_array($visibility, ['restricted', 'restricted_integrity'], true)) {
            return has_capability('mod/uckkarchive:viewrestrictedmedia', $context);
        }

        if ($visibility === 'restricted_cultural') {
            return has_capability('mod/uckkarchive:viewculturallyrestricted', $context);
        }

        return true;
    }

    /**
     * Return whether relation touches content marker/advisory.
     *
     * @param stdClass $relation Relation record.
     * @return bool
     */
    protected static function relation_touches_content_marker(stdClass $relation): bool {
        return ($relation->fromtype ?? '') === 'content_marker' ||
            ($relation->totype ?? '') === 'content_marker' ||
            ($relation->relationtype ?? '') === 'contains_content_marker';
    }

    /**
     * Return related object summary.
     *
     * @param context_module $context Context.
     * @param string $type Object type.
     * @param int $id Object id.
     * @return array<string, mixed>
     */
    protected static function related_object_summary(context_module $context, string $type, int $id): array {
        $type = self::normalise_object_type($type);
        $id = max(0, $id);

        $fallback = [
            'type' => $type,
            'id' => $id,
            'uuid' => '',
            'title' => '',
            'status' => '',
            'visibility' => '',
            'available' => false,
        ];

        if ($id <= 0) {
            return $fallback;
        }

        $table = self::table_for_object_type($type);
        if ($table === null || !self::table_exists($table)) {
            return $fallback;
        }

        $record = self::load_object_record($table, $id);
        if (!$record) {
            return $fallback;
        }

        if ($type === 'media' && !self::can_view_media($context, $record)) {
            return $fallback;
        }

        if ($type === 'content_marker' && !has_capability('mod/uckkarchive:viewadvisories', $context)) {
            return $fallback;
        }

        return [
            'type' => $type,
            'id' => $id,
            'uuid' => (string)($record->uuid ?? ''),
            'title' => self::object_title($record),
            'status' => (string)($record->status ?? $record->state ?? ''),
            'visibility' => (string)($record->visibility ?? ''),
            'available' => true,
        ];
    }

    /**
     * Return table for object type.
     *
     * @param string $type Object type.
     * @return string|null
     */
    protected static function table_for_object_type(string $type): ?string {
        return match ($type) {
            'media' => self::TABLE_MEDIA,
            'content_marker' => self::TABLE_CONTENT_MARKER,
            'external_work' => self::TABLE_EXTERNAL_WORK,
            'media_collection' => self::TABLE_MEDIA_COLLECTION,
            default => null,
        };
    }

    /**
     * Load one object record by id.
     *
     * @param string $table Table.
     * @param int $id Id.
     * @return stdClass|null
     */
    protected static function load_object_record(string $table, int $id): ?stdClass {
        global $DB;

        if ($id <= 0 || !self::table_exists($table)) {
            return null;
        }

        return $DB->get_record($table, ['id' => $id], '*', IGNORE_MISSING) ?: null;
    }

    /**
     * Return object title.
     *
     * @param stdClass $record Record.
     * @return string
     */
    protected static function object_title(stdClass $record): string {
        foreach (['title', 'name', 'label', 'tagkey', 'worktitle'] as $field) {
            if (property_exists($record, $field) && trim((string)$record->{$field}) !== '') {
                return format_string((string)$record->{$field});
            }
        }

        return '';
    }

    /**
     * Validate filter combination.
     *
     * @param array<string, mixed> $filters Filters.
     * @return void
     */
    protected static function validate_filter_combination(array $filters): void {
        if (!$filters['media'] &&
                $filters['fromtype'] === '' &&
                $filters['fromid'] <= 0 &&
                $filters['totype'] === '' &&
                $filters['toid'] <= 0 &&
                $filters['relationtype'] === '') {
            throw new invalid_parameter_exception('At least one relation filter is required.');
        }

        if ($filters['fromid'] > 0 && $filters['fromtype'] === '') {
            throw new invalid_parameter_exception('fromtype is required when fromid is provided.');
        }

        if ($filters['toid'] > 0 && $filters['totype'] === '') {
            throw new invalid_parameter_exception('totype is required when toid is provided.');
        }
    }

    /**
     * Normalize direction.
     *
     * @param string $direction Direction.
     * @return string
     */
    protected static function normalise_direction(string $direction): string {
        $direction = strtolower(clean_param(trim($direction), PARAM_ALPHA));

        return in_array($direction, [
            self::DIRECTION_ANY,
            self::DIRECTION_FROM,
            self::DIRECTION_TO,
            self::DIRECTION_EXACT,
        ], true) ? $direction : self::DIRECTION_ANY;
    }

    /**
     * Normalize object type.
     *
     * @param string $type Object type.
     * @return string
     */
    protected static function normalise_object_type(string $type): string {
        $type = strtolower(clean_param(trim($type), PARAM_ALPHANUMEXT));
        if ($type === '') {
            return '';
        }

        if (class_exists(media_relation::class)) {
            try {
                $probe = media_relation::create(1, 'media', 1, $type, 1);
                return $probe->get_totype();
            } catch (\Throwable $ignored) {
                // Fall through to local normalisation.
            }
        }

        return match ($type) {
            'item', 'archiveitem', 'archive_item' => 'archive_item',
            'media', 'media_item', 'media_object' => 'media',
            'version', 'media_version' => 'media_version',
            'collection', 'mediacollection', 'media_collection' => 'media_collection',
            'collectionitem', 'collection_item', 'media_collection_item' => 'media_collection_item',
            'marker', 'contentmarker', 'content_marker' => 'content_marker',
            'externalwork', 'external_work', 'work' => 'external_work',
            'kristal' => 'kristal',
            'proof' => 'proof',
            default => $type,
        };
    }

    /**
     * Normalize relation type.
     *
     * @param string $relationtype Relation type.
     * @return string
     */
    protected static function normalise_relation_type(string $relationtype): string {
        $relationtype = strtolower(clean_param(trim($relationtype), PARAM_ALPHANUMEXT));
        if ($relationtype === '') {
            return '';
        }

        if (class_exists(media_relation::class) &&
                method_exists(media_relation::class, 'get_allowed_relation_types') &&
                !in_array($relationtype, media_relation::get_allowed_relation_types(), true)) {
            throw new invalid_parameter_exception('Invalid relation type: ' . $relationtype);
        }

        return $relationtype;
    }

    /**
     * Normalize include values.
     *
     * @param string[] $include Include values.
     * @return string[]
     */
    protected static function normalise_include(array $include): array {
        $allowed = ['metadata', 'related', 'permissions'];
        $clean = [];

        foreach ($include as $value) {
            $value = clean_param((string)$value, PARAM_ALPHANUMEXT);
            if (in_array($value, $allowed, true)) {
                $clean[] = $value;
            }
        }

        return array_values(array_unique($clean));
    }

    /**
     * Normalize page.
     *
     * @param int $page Page.
     * @return int
     */
    protected static function normalise_page(int $page): int {
        return max(0, $page);
    }

    /**
     * Normalize per page.
     *
     * @param int $perpage Per page.
     * @return int
     */
    protected static function normalise_perpage(int $perpage): int {
        return min(self::MAX_PERPAGE, max(1, $perpage));
    }

    /**
     * Normalize sort field.
     *
     * @param string $sort Sort field.
     * @return string
     */
    protected static function normalise_sort(string $sort): string {
        $sort = clean_param(trim($sort), PARAM_ALPHANUMEXT);
        $allowed = ['id', 'sortorder', 'timecreated', 'relationtype'];

        return in_array($sort, $allowed, true) ? $sort : 'sortorder';
    }

    /**
     * Normalize sort direction.
     *
     * @param string $direction Direction.
     * @return string
     */
    protected static function normalise_sort_direction(string $direction): string {
        $direction = strtolower(clean_param(trim($direction), PARAM_ALPHA));

        return $direction === 'desc' ? 'DESC' : 'ASC';
    }

    /**
     * Normalize metadata JSON.
     *
     * @param mixed $metadata Metadata.
     * @return string
     */
    protected static function normalise_metadata_json(mixed $metadata): string {
        if (is_array($metadata) || is_object($metadata)) {
            return json_encode($metadata, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES) ?: '{}';
        }

        $metadata = trim((string)$metadata);
        if ($metadata === '') {
            return '{}';
        }

        $decoded = json_decode($metadata, true);
        if (!is_array($decoded)) {
            return '{}';
        }

        return json_encode($decoded, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES) ?: '{}';
    }

    /**
     * Return permissions payload.
     *
     * @param context_module $context Context.
     * @return array<string, bool>
     */
    protected static function permissions(context_module $context): array {
        return [
            'viewmedia' => has_capability('mod/uckkarchive:viewmedia', $context),
            'viewrestrictedmedia' => has_capability('mod/uckkarchive:viewrestrictedmedia', $context),
            'viewculturallyrestricted' => has_capability('mod/uckkarchive:viewculturallyrestricted', $context),
            'editmedia' => has_capability('mod/uckkarchive:editmedia', $context),
            'managemediacollections' => has_capability('mod/uckkarchive:managemediacollections', $context),
            'manageadvisories' => has_capability('mod/uckkarchive:manageadvisories', $context),
            'viewadvisories' => has_capability('mod/uckkarchive:viewadvisories', $context),
            'manageexternalworks' => has_capability('mod/uckkarchive:manageexternalworks', $context),
        ];
    }

    /**
     * Return empty response.
     *
     * @param int $page Page.
     * @param int $perpage Per page.
     * @param array<string, bool> $permissions Permissions.
     * @param array<int, array<string, mixed>> $warnings Warnings.
     * @return array<string, mixed>
     */
    protected static function empty_response(int $page, int $perpage, array $permissions, array $warnings = []): array {
        return [
            'relations' => [],
            'pagination' => [
                'page' => $page,
                'perpage' => $perpage,
                'total' => 0,
                'returned' => 0,
                'hasmore' => false,
            ],
            'permissions' => $permissions,
            'warnings' => $warnings,
        ];
    }

    /**
     * Return warning payload.
     *
     * @param string $item Item.
     * @param int $itemid Item id.
     * @param string $code Code.
     * @param string $message Message.
     * @return array<string, mixed>
     */
    protected static function warning(string $item, int $itemid, string $code, string $message): array {
        return [
            'item' => $item,
            'itemid' => $itemid,
            'warningcode' => clean_param($code, PARAM_ALPHANUMEXT),
            'message' => $message,
        ];
    }

    /**
     * Return whether table exists.
     *
     * @param string $tablename Table name.
     * @return bool
     */
    protected static function table_exists(string $tablename): bool {
        global $DB;

        return $DB->get_manager()->table_exists(new \xmldb_table($tablename));
    }
}
