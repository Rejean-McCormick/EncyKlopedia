<?php
// This file is part of Moodle - https://moodle.org/
//
// Moodle is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// any later version.

/**
 * Return permission-filtered content advisory markers.
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
use mod_uckkarchive\local\content_marker;
use mod_uckkarchive\local\content_policy;
use moodle_exception;
use stdClass;
use xmldb_table;

/**
 * Return content advisory markers for media, archive items, media versions, or external works.
 *
 * Target service name:
 *
 * ```text
 * mod_uckkarchive_get_content_markers
 * ```
 *
 * The service returns only markers that the current user is allowed to see.
 * Restricted markers, culturally restricted markers, unreviewed markers, and
 * hidden review states are filtered or redacted by content_policy.
 */
class get_content_markers extends external_api {
    /** Content marker table. */
    private const MARKER_TABLE = 'uckkarchive_content_marker';

    /** Media table. */
    private const MEDIA_TABLE = 'uckkarchive_media';

    /** Archive item table. */
    private const ITEM_TABLE = 'uckkarchive_item';

    /** Media version table. */
    private const MEDIA_VERSION_TABLE = 'uckkarchive_media_version';

    /** External work table. */
    private const EXTERNAL_WORK_TABLE = 'uckkarchive_external_work';

    /** Default page size. */
    private const DEFAULT_PERPAGE = 20;

    /** Maximum page size. */
    private const MAX_PERPAGE = 100;

    /**
     * Define service parameters.
     *
     * @return external_function_parameters
     */
    public static function execute_parameters(): external_function_parameters {
        return new external_function_parameters([
            'cmid' => new external_value(PARAM_INT, 'Course module id'),
            'mediaid' => new external_value(PARAM_INT, 'Media id', VALUE_DEFAULT, 0),
            'mediauuid' => new external_value(PARAM_TEXT, 'Media UUID', VALUE_DEFAULT, ''),
            'versionid' => new external_value(PARAM_INT, 'Media version id', VALUE_DEFAULT, 0),
            'versionuuid' => new external_value(PARAM_TEXT, 'Media version UUID', VALUE_DEFAULT, ''),
            'itemid' => new external_value(PARAM_INT, 'Archive item id', VALUE_DEFAULT, 0),
            'itemuuid' => new external_value(PARAM_TEXT, 'Archive item UUID', VALUE_DEFAULT, ''),
            'externalworkid' => new external_value(PARAM_INT, 'External work id', VALUE_DEFAULT, 0),
            'externalworkuuid' => new external_value(PARAM_TEXT, 'External work UUID', VALUE_DEFAULT, ''),
            'targettype' => new external_value(PARAM_ALPHANUMEXT, 'Explicit marker target type', VALUE_DEFAULT, ''),
            'targetid' => new external_value(PARAM_INT, 'Explicit marker target id', VALUE_DEFAULT, 0),
            'targetuuid' => new external_value(PARAM_TEXT, 'Explicit marker target UUID', VALUE_DEFAULT, ''),
            'filters' => new external_single_structure([
                'tagkey' => new external_value(PARAM_ALPHANUMEXT, 'Content tag key', VALUE_DEFAULT, ''),
                'tagsetid' => new external_value(PARAM_INT, 'Content tag set id', VALUE_DEFAULT, 0),
                'reviewstate' => new external_value(PARAM_ALPHANUMEXT, 'Review state', VALUE_DEFAULT, ''),
                'severity' => new external_value(PARAM_ALPHANUMEXT, 'Severity', VALUE_DEFAULT, ''),
                'visibility' => new external_value(PARAM_ALPHANUMEXT, 'Visibility', VALUE_DEFAULT, ''),
                'audiencesuitability' => new external_value(PARAM_ALPHANUMEXT, 'Audience suitability', VALUE_DEFAULT, ''),
                'locatortype' => new external_value(PARAM_ALPHANUMEXT, 'Locator type', VALUE_DEFAULT, ''),
                'query' => new external_value(PARAM_TEXT, 'Search note or teaching context', VALUE_DEFAULT, ''),
                'include_retired' => new external_value(PARAM_BOOL, 'Include retired markers', VALUE_DEFAULT, false),
            ], 'Content marker filters', VALUE_DEFAULT, []),
            'page' => new external_value(PARAM_INT, 'Zero-based page number', VALUE_DEFAULT, 0),
            'perpage' => new external_value(PARAM_INT, 'Items per page', VALUE_DEFAULT, self::DEFAULT_PERPAGE),
            'sort' => new external_value(PARAM_ALPHANUMEXT, 'Sort field', VALUE_DEFAULT, 'locatorsort'),
            'direction' => new external_value(PARAM_ALPHA, 'Sort direction: asc or desc', VALUE_DEFAULT, 'asc'),
        ]);
    }

    /**
     * Execute the service.
     *
     * @param int $cmid Course module id.
     * @param int $mediaid Media id.
     * @param string $mediauuid Media UUID.
     * @param int $versionid Media version id.
     * @param string $versionuuid Media version UUID.
     * @param int $itemid Archive item id.
     * @param string $itemuuid Archive item UUID.
     * @param int $externalworkid External work id.
     * @param string $externalworkuuid External work UUID.
     * @param string $targettype Explicit target type.
     * @param int $targetid Explicit target id.
     * @param string $targetuuid Explicit target UUID.
     * @param array<string, mixed> $filters Filters.
     * @param int $page Zero-based page number.
     * @param int $perpage Page size.
     * @param string $sort Sort field.
     * @param string $direction Sort direction.
     * @return array<string, mixed>
     */
    public static function execute(
        int $cmid,
        int $mediaid = 0,
        string $mediauuid = '',
        int $versionid = 0,
        string $versionuuid = '',
        int $itemid = 0,
        string $itemuuid = '',
        int $externalworkid = 0,
        string $externalworkuuid = '',
        string $targettype = '',
        int $targetid = 0,
        string $targetuuid = '',
        array $filters = [],
        int $page = 0,
        int $perpage = self::DEFAULT_PERPAGE,
        string $sort = 'locatorsort',
        string $direction = 'asc'
    ): array {
        global $DB;

        $params = self::validate_parameters(self::execute_parameters(), [
            'cmid' => $cmid,
            'mediaid' => $mediaid,
            'mediauuid' => $mediauuid,
            'versionid' => $versionid,
            'versionuuid' => $versionuuid,
            'itemid' => $itemid,
            'itemuuid' => $itemuuid,
            'externalworkid' => $externalworkid,
            'externalworkuuid' => $externalworkuuid,
            'targettype' => $targettype,
            'targetid' => $targetid,
            'targetuuid' => $targetuuid,
            'filters' => $filters,
            'page' => $page,
            'perpage' => $perpage,
            'sort' => $sort,
            'direction' => $direction,
        ]);

        [$course, $cm, $archive, $context] = self::load_page((int)$params['cmid']);
        self::validate_context($context);
        require_login($course, false, $cm);

        content_policy::require_view_advisories($context);

        $page = max(0, (int)$params['page']);
        $perpage = min(self::MAX_PERPAGE, max(1, (int)$params['perpage']));
        $filters = self::normalise_filters((array)$params['filters']);
        $sort = self::normalise_sort((string)$params['sort']);
        $direction = self::normalise_direction((string)$params['direction']);

        if (!self::table_exists(self::MARKER_TABLE)) {
            return self::empty_response(
                $page,
                $perpage,
                self::get_permissions($context),
                self::warning('content_marker', 0, 'markertablenotfound', 'Content marker table is not installed yet.')
            );
        }

        [$resolvedtype, $resolvedid, $resolveduuid] = self::resolve_target(
            (int)$archive->id,
            (int)$params['mediaid'],
            (string)$params['mediauuid'],
            (int)$params['versionid'],
            (string)$params['versionuuid'],
            (int)$params['itemid'],
            (string)$params['itemuuid'],
            (int)$params['externalworkid'],
            (string)$params['externalworkuuid'],
            (string)$params['targettype'],
            (int)$params['targetid'],
            (string)$params['targetuuid']
        );

        $records = self::load_markers(
            (int)$archive->id,
            (int)$course->id,
            (int)$cm->id,
            (int)$context->id,
            $resolvedtype,
            $resolvedid,
            $resolveduuid,
            $filters,
            $sort,
            $direction
        );

        $records = content_policy::filter_markers($context, $records, null, true);

        $total = count($records);
        $records = array_slice($records, $page * $perpage, $perpage);

        $markers = [];
        foreach ($records as $record) {
            $markers[] = self::export_marker($context, $record);
        }

        return [
            'markers' => $markers,
            'pagination' => [
                'page' => $page,
                'perpage' => $perpage,
                'total' => $total,
                'returned' => count($markers),
                'hasmore' => (($page + 1) * $perpage) < $total,
            ],
            'permissions' => self::get_permissions($context),
            'warnings' => [],
        ];
    }

    /**
     * Define return structure.
     *
     * @return external_single_structure
     */
    public static function execute_returns(): external_single_structure {
        return new external_single_structure([
            'markers' => new external_multiple_structure(self::marker_structure(), 'Content markers'),
            'pagination' => new external_single_structure([
                'page' => new external_value(PARAM_INT, 'Current zero-based page'),
                'perpage' => new external_value(PARAM_INT, 'Items per page'),
                'total' => new external_value(PARAM_INT, 'Total visible records'),
                'returned' => new external_value(PARAM_INT, 'Returned records'),
                'hasmore' => new external_value(PARAM_BOOL, 'Whether more visible records exist'),
            ]),
            'permissions' => self::permissions_structure(),
            'warnings' => self::warnings_structure(),
        ]);
    }

    /**
     * Return content marker response structure.
     *
     * @return external_single_structure
     */
    private static function marker_structure(): external_single_structure {
        return new external_single_structure([
            'id' => new external_value(PARAM_INT, 'Marker id'),
            'uuid' => new external_value(PARAM_TEXT, 'Marker UUID'),
            'archiveid' => new external_value(PARAM_INT, 'Archive id'),
            'courseid' => new external_value(PARAM_INT, 'Course id'),
            'cmid' => new external_value(PARAM_INT, 'Course module id'),
            'contextid' => new external_value(PARAM_INT, 'Context id'),
            'targettype' => new external_value(PARAM_ALPHANUMEXT, 'Target type'),
            'targetid' => new external_value(PARAM_INT, 'Target id'),
            'targetuuid' => new external_value(PARAM_TEXT, 'Target UUID'),
            'tagid' => new external_value(PARAM_INT, 'Tag id'),
            'tagsetid' => new external_value(PARAM_INT, 'Tag set id'),
            'tagkey' => new external_value(PARAM_ALPHANUMEXT, 'Tag key'),
            'locatortype' => new external_value(PARAM_ALPHANUMEXT, 'Locator type'),
            'locatorvalue' => new external_value(PARAM_RAW, 'Locator value'),
            'locatorstart' => new external_value(PARAM_RAW, 'Locator start'),
            'locatorend' => new external_value(PARAM_RAW, 'Locator end'),
            'locatorsort' => new external_value(PARAM_INT, 'Locator sort value'),
            'severity' => new external_value(PARAM_ALPHANUMEXT, 'Severity'),
            'visibility' => new external_value(PARAM_ALPHANUMEXT, 'Visibility'),
            'audiencesuitability' => new external_value(PARAM_ALPHANUMEXT, 'Audience suitability'),
            'reviewstate' => new external_value(PARAM_ALPHANUMEXT, 'Review state'),
            'reviewedby' => new external_value(PARAM_INT, 'Reviewer user id'),
            'timereviewed' => new external_value(PARAM_INT, 'Review time'),
            'note' => new external_value(PARAM_RAW, 'Marker note'),
            'teachingcontext' => new external_value(PARAM_RAW, 'Teaching context'),
            'culturalprotocolnote' => new external_value(PARAM_RAW, 'Cultural protocol note'),
            'reviewrationale' => new external_value(PARAM_RAW, 'Review rationale'),
            'createdby' => new external_value(PARAM_INT, 'Creator user id'),
            'modifiedby' => new external_value(PARAM_INT, 'Modifier user id'),
            'metadatajson' => new external_value(PARAM_RAW, 'Metadata JSON'),
            'redacted' => new external_value(PARAM_BOOL, 'Whether marker was redacted'),
            'redactionmode' => new external_value(PARAM_ALPHANUMEXT, 'Redaction mode'),
            'timecreated' => new external_value(PARAM_INT, 'Creation time'),
            'timemodified' => new external_value(PARAM_INT, 'Modified time'),
        ]);
    }

    /**
     * Return permission response structure.
     *
     * @return external_single_structure
     */
    private static function permissions_structure(): external_single_structure {
        return new external_single_structure([
            'viewadvisories' => new external_value(PARAM_BOOL, 'Can view content advisories'),
            'manageadvisories' => new external_value(PARAM_BOOL, 'Can manage content advisories'),
            'reviewadvisories' => new external_value(PARAM_BOOL, 'Can review content advisories'),
            'viewculturallyrestricted' => new external_value(PARAM_BOOL, 'Can view culturally restricted advisories'),
            'viewrestricted' => new external_value(PARAM_BOOL, 'Can view restricted archive material'),
            'viewrestrictedmedia' => new external_value(PARAM_BOOL, 'Can view restricted media'),
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
     * Load archive page context.
     *
     * @param int $cmid Course module id.
     * @return array{0:stdClass,1:stdClass,2:stdClass,3:context_module}
     */
    private static function load_page(int $cmid): array {
        [$course, $cm, $archive, $context] = \uckkarchive_require_page($cmid, 0);

        return [$course, $cm, $archive, $context];
    }

    /**
     * Resolve target from explicit or convenience parameters.
     *
     * @param int $archiveid Archive id.
     * @param int $mediaid Media id.
     * @param string $mediauuid Media UUID.
     * @param int $versionid Version id.
     * @param string $versionuuid Version UUID.
     * @param int $itemid Archive item id.
     * @param string $itemuuid Archive item UUID.
     * @param int $externalworkid External work id.
     * @param string $externalworkuuid External work UUID.
     * @param string $targettype Explicit target type.
     * @param int $targetid Explicit target id.
     * @param string $targetuuid Explicit target UUID.
     * @return array{0:string,1:int,2:string}
     */
    private static function resolve_target(
        int $archiveid,
        int $mediaid,
        string $mediauuid,
        int $versionid,
        string $versionuuid,
        int $itemid,
        string $itemuuid,
        int $externalworkid,
        string $externalworkuuid,
        string $targettype,
        int $targetid,
        string $targetuuid
    ): array {
        $targettype = clean_param($targettype, PARAM_ALPHANUMEXT);
        $targetuuid = trim($targetuuid);

        if ($targettype !== '' && $targetid > 0) {
            return [$targettype, $targetid, $targetuuid];
        }

        if ($mediaid > 0 || $mediauuid !== '') {
            return [
                content_marker::TARGET_MEDIA,
                $mediaid > 0 ? $mediaid : self::id_from_uuid(self::MEDIA_TABLE, $mediauuid, $archiveid),
                $mediauuid,
            ];
        }

        if ($versionid > 0 || $versionuuid !== '') {
            return [
                content_marker::TARGET_MEDIA_VERSION,
                $versionid > 0 ? $versionid : self::id_from_uuid(self::MEDIA_VERSION_TABLE, $versionuuid, $archiveid),
                $versionuuid,
            ];
        }

        if ($itemid > 0 || $itemuuid !== '') {
            return [
                content_marker::TARGET_ARCHIVE_ITEM,
                $itemid > 0 ? $itemid : self::id_from_uuid(self::ITEM_TABLE, $itemuuid, $archiveid),
                $itemuuid,
            ];
        }

        if ($externalworkid > 0 || $externalworkuuid !== '') {
            return [
                content_marker::TARGET_EXTERNAL_WORK,
                $externalworkid > 0 ? $externalworkid : self::id_from_uuid(self::EXTERNAL_WORK_TABLE, $externalworkuuid, $archiveid),
                $externalworkuuid,
            ];
        }

        if ($targettype !== '' && $targetuuid !== '') {
            return [$targettype, 0, $targetuuid];
        }

        return ['', 0, ''];
    }

    /**
     * Load marker records.
     *
     * @param int $archiveid Archive id.
     * @param int $courseid Course id.
     * @param int $cmid Course module id.
     * @param int $contextid Context id.
     * @param string $targettype Target type.
     * @param int $targetid Target id.
     * @param string $targetuuid Target UUID.
     * @param array<string, mixed> $filters Filters.
     * @param string $sort Sort field.
     * @param string $direction Direction.
     * @return stdClass[]
     */
    private static function load_markers(
        int $archiveid,
        int $courseid,
        int $cmid,
        int $contextid,
        string $targettype,
        int $targetid,
        string $targetuuid,
        array $filters,
        string $sort,
        string $direction
    ): array {
        global $DB;

        $columns = $DB->get_columns(self::MARKER_TABLE);
        $where = ['1 = 1'];
        $params = [];

        self::add_int_filter($where, $params, $columns, 'archiveid', $archiveid);
        self::add_int_filter($where, $params, $columns, 'courseid', $courseid);
        self::add_int_filter($where, $params, $columns, 'cmid', $cmid);
        self::add_int_filter($where, $params, $columns, 'contextid', $contextid);

        if ($targettype !== '' && self::column_exists($columns, 'targettype')) {
            $where[] = 'targettype = :targettype';
            $params['targettype'] = $targettype;
        }

        if ($targetid > 0 && self::column_exists($columns, 'targetid')) {
            $where[] = 'targetid = :targetid';
            $params['targetid'] = $targetid;
        }

        if ($targetuuid !== '' && self::column_exists($columns, 'targetuuid')) {
            $where[] = 'targetuuid = :targetuuid';
            $params['targetuuid'] = $targetuuid;
        }

        foreach ([
            'tagkey',
            'reviewstate',
            'severity',
            'visibility',
            'audiencesuitability',
            'locatortype',
        ] as $field) {
            if ($filters[$field] !== '' && self::column_exists($columns, $field)) {
                $where[] = "{$field} = :{$field}";
                $params[$field] = $filters[$field];
            }
        }

        if (!empty($filters['tagsetid']) && self::column_exists($columns, 'tagsetid')) {
            $where[] = 'tagsetid = :tagsetid';
            $params['tagsetid'] = (int)$filters['tagsetid'];
        }

        if (empty($filters['include_retired']) && self::column_exists($columns, 'reviewstate')) {
            $where[] = 'reviewstate <> :retiredstate';
            $params['retiredstate'] = content_marker::REVIEW_RETIRED;
        }

        if ($filters['query'] !== '') {
            $queryparts = [];
            if (self::column_exists($columns, 'note')) {
                $queryparts[] = $DB->sql_like('note', ':querynote', false, false);
                $params['querynote'] = '%' . $DB->sql_like_escape($filters['query']) . '%';
            }
            if (self::column_exists($columns, 'teachingcontext')) {
                $queryparts[] = $DB->sql_like('teachingcontext', ':querycontext', false, false);
                $params['querycontext'] = '%' . $DB->sql_like_escape($filters['query']) . '%';
            }
            if ($queryparts) {
                $where[] = '(' . implode(' OR ', $queryparts) . ')';
            }
        }

        $sort = self::column_exists($columns, $sort) ? $sort : (self::column_exists($columns, 'locatorsort') ? 'locatorsort' : 'id');

        $sql = 'SELECT *
                  FROM {' . self::MARKER_TABLE . '}
                 WHERE ' . implode(' AND ', $where) . "
              ORDER BY {$sort} {$direction}, id ASC";

        return array_values($DB->get_records_sql($sql, $params));
    }

    /**
     * Export marker record for service response.
     *
     * @param context_module $context Context.
     * @param stdClass $record Marker record.
     * @return array<string, mixed>
     */
    private static function export_marker(context_module $context, stdClass $record): array {
        $data = content_marker::export_record($record);

        return [
            'id' => (int)$data['id'],
            'uuid' => (string)$data['uuid'],
            'archiveid' => (int)$data['archiveid'],
            'courseid' => (int)$data['courseid'],
            'cmid' => (int)$data['cmid'],
            'contextid' => (int)$data['contextid'],
            'targettype' => (string)$data['targettype'],
            'targetid' => (int)$data['targetid'],
            'targetuuid' => (string)$data['targetuuid'],
            'tagid' => (int)$data['tagid'],
            'tagsetid' => (int)$data['tagsetid'],
            'tagkey' => (string)$data['tagkey'],
            'locatortype' => (string)$data['locatortype'],
            'locatorvalue' => (string)$data['locatorvalue'],
            'locatorstart' => (string)$data['locatorstart'],
            'locatorend' => (string)$data['locatorend'],
            'locatorsort' => (int)$data['locatorsort'],
            'severity' => (string)$data['severity'],
            'visibility' => (string)$data['visibility'],
            'audiencesuitability' => (string)$data['audiencesuitability'],
            'reviewstate' => (string)$data['reviewstate'],
            'reviewedby' => (int)$data['reviewedby'],
            'timereviewed' => (int)$data['timereviewed'],
            'note' => format_text((string)$data['note'], FORMAT_PLAIN, ['context' => $context]),
            'teachingcontext' => format_text((string)$data['teachingcontext'], FORMAT_PLAIN, ['context' => $context]),
            'culturalprotocolnote' => format_text((string)$data['culturalprotocolnote'], FORMAT_PLAIN, ['context' => $context]),
            'reviewrationale' => format_text((string)$data['reviewrationale'], FORMAT_PLAIN, ['context' => $context]),
            'createdby' => (int)$data['createdby'],
            'modifiedby' => (int)$data['modifiedby'],
            'metadatajson' => self::encode_json($data['metadata']),
            'redacted' => !empty($record->redacted),
            'redactionmode' => (string)($record->redactionmode ?? 'none'),
            'timecreated' => (int)$data['timecreated'],
            'timemodified' => (int)$data['timemodified'],
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
            'viewadvisories' => content_policy::can_view_advisories($context),
            'manageadvisories' => content_policy::can_manage_advisories($context),
            'reviewadvisories' => content_policy::can_review_advisories($context),
            'viewculturallyrestricted' => content_policy::can_view_culturally_restricted($context),
            'viewrestricted' => has_capability('mod/uckkarchive:viewrestricted', $context),
            'viewrestrictedmedia' => has_capability('mod/uckkarchive:viewrestrictedmedia', $context),
        ];
    }

    /**
     * Return empty response.
     *
     * @param int $page Page.
     * @param int $perpage Per page.
     * @param array<string, bool> $permissions Permissions.
     * @param array<string, mixed>|null $warning Optional warning.
     * @return array<string, mixed>
     */
    private static function empty_response(int $page, int $perpage, array $permissions, ?array $warning = null): array {
        return [
            'markers' => [],
            'pagination' => [
                'page' => $page,
                'perpage' => $perpage,
                'total' => 0,
                'returned' => 0,
                'hasmore' => false,
            ],
            'permissions' => $permissions,
            'warnings' => $warning ? [$warning] : [],
        ];
    }

    /**
     * Normalize filters.
     *
     * @param array<string, mixed> $filters Raw filters.
     * @return array<string, mixed>
     */
    private static function normalise_filters(array $filters): array {
        $defaults = [
            'tagkey' => '',
            'tagsetid' => 0,
            'reviewstate' => '',
            'severity' => '',
            'visibility' => '',
            'audiencesuitability' => '',
            'locatortype' => '',
            'query' => '',
            'include_retired' => false,
        ];

        $filters = array_merge($defaults, $filters);

        foreach (['tagkey', 'reviewstate', 'severity', 'visibility', 'audiencesuitability', 'locatortype'] as $key) {
            $filters[$key] = clean_param((string)$filters[$key], PARAM_ALPHANUMEXT);
        }

        $filters['tagsetid'] = max(0, (int)$filters['tagsetid']);
        $filters['query'] = clean_param((string)$filters['query'], PARAM_TEXT);
        $filters['include_retired'] = !empty($filters['include_retired']);

        return $filters;
    }

    /**
     * Normalize sort field.
     *
     * @param string $sort Sort field.
     * @return string
     */
    private static function normalise_sort(string $sort): string {
        $sort = clean_param($sort, PARAM_ALPHANUMEXT);
        $allowed = [
            'locatorsort',
            'timecreated',
            'timemodified',
            'severity',
            'reviewstate',
            'audiencesuitability',
        ];

        return in_array($sort, $allowed, true) ? $sort : 'locatorsort';
    }

    /**
     * Normalize direction.
     *
     * @param string $direction Direction.
     * @return string
     */
    private static function normalise_direction(string $direction): string {
        $direction = strtolower(clean_param($direction, PARAM_ALPHA));

        return $direction === 'desc' ? 'DESC' : 'ASC';
    }

    /**
     * Return id by UUID for a target table.
     *
     * @param string $table Table name.
     * @param string $uuid UUID.
     * @param int $archiveid Archive id.
     * @return int
     */
    private static function id_from_uuid(string $table, string $uuid, int $archiveid): int {
        global $DB;

        $uuid = trim($uuid);
        if ($uuid === '') {
            return 0;
        }

        if (!self::table_exists($table)) {
            return 0;
        }

        $conditions = ['uuid' => $uuid];
        $columns = $DB->get_columns($table);

        if (array_key_exists('archiveid', $columns)) {
            $conditions['archiveid'] = $archiveid;
        } else if (array_key_exists('uckkarchiveid', $columns)) {
            $conditions['uckkarchiveid'] = $archiveid;
        }

        $record = $DB->get_record($table, $conditions, 'id', IGNORE_MISSING);

        return $record ? (int)$record->id : 0;
    }

    /**
     * Add integer filter if column exists and value is non-zero.
     *
     * @param string[] $where Where clauses.
     * @param array<string, mixed> $params Params.
     * @param array<string, object> $columns Columns.
     * @param string $field Field.
     * @param int $value Value.
     * @return void
     */
    private static function add_int_filter(array &$where, array &$params, array $columns, string $field, int $value): void {
        if ($value <= 0 || !self::column_exists($columns, $field)) {
            return;
        }

        $where[] = "{$field} = :{$field}";
        $params[$field] = $value;
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
     * Return whether column exists.
     *
     * @param array<string, object> $columns Columns.
     * @param string $field Field.
     * @return bool
     */
    private static function column_exists(array $columns, string $field): bool {
        return array_key_exists($field, $columns);
    }

    /**
     * Return warning payload.
     *
     * @param string $item Item.
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

    /**
     * Encode data as JSON for external response.
     *
     * @param mixed $data Data.
     * @return string
     */
    private static function encode_json(mixed $data): string {
        $json = json_encode($data, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);

        return $json === false ? '{}' : $json;
    }
}
