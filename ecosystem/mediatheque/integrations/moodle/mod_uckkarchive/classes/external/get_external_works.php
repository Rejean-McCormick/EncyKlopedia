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
 * External service for listing external works referenced by UCKK Archive.
 *
 * @package    mod_uckkarchive
 * @copyright  2026 UCKK
 * @license    http://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later
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
use moodle_exception;
use stdClass;

/**
 * Return a filtered, permission-aware list of external works.
 *
 * External works are foreign or third-party works referenced by the archive
 * without necessarily copying the work into Moodle File API storage.
 *
 * This endpoint is read-only. It may be used by AJAX UI, media forms,
 * content advisory panels, course media workflows, or external-service clients.
 *
 * Target service name:
 *
 * ```text
 * mod_uckkarchive_get_external_works
 * ```
 */
final class get_external_works extends external_api {
    /** External work table. */
    private const TABLE_EXTERNAL_WORK = 'uckkarchive_external_work';

    /** Content marker table. */
    private const TABLE_CONTENT_MARKER = 'uckkarchive_content_marker';

    /** Media source table. */
    private const TABLE_MEDIA_SOURCE = 'uckkarchive_media_source';

    /** Default page size. */
    private const DEFAULT_PERPAGE = 20;

    /** Maximum page size. */
    private const MAX_PERPAGE = 100;

    /**
     * Return service parameters.
     *
     * @return external_function_parameters
     */
    public static function execute_parameters(): external_function_parameters {
        return new external_function_parameters([
            'cmid' => new external_value(PARAM_INT, 'Course module id.'),
            'query' => new external_value(PARAM_TEXT, 'Search query.', VALUE_DEFAULT, ''),
            'filters' => new external_single_structure([
                'worktype' => new external_value(PARAM_ALPHANUMEXT, 'External work type.', VALUE_DEFAULT, ''),
                'status' => new external_value(PARAM_ALPHANUMEXT, 'External work status.', VALUE_DEFAULT, ''),
                'visibility' => new external_value(PARAM_ALPHANUMEXT, 'Visibility.', VALUE_DEFAULT, ''),
                'sourceownership' => new external_value(PARAM_ALPHANUMEXT, 'Source ownership.', VALUE_DEFAULT, ''),
                'audiencesuitability' => new external_value(PARAM_ALPHANUMEXT, 'Audience suitability.', VALUE_DEFAULT, ''),
                'creator' => new external_value(PARAM_TEXT, 'Creator filter.', VALUE_DEFAULT, ''),
                'publisher' => new external_value(PARAM_TEXT, 'Publisher filter.', VALUE_DEFAULT, ''),
                'identifier' => new external_value(PARAM_TEXT, 'Identifier filter.', VALUE_DEFAULT, ''),
                'hasmarkers' => new external_value(PARAM_BOOL, 'Require content markers.', VALUE_DEFAULT, false),
                'hasrestricted' => new external_value(PARAM_BOOL, 'Require restricted works.', VALUE_DEFAULT, false),
                'createdfrom' => new external_value(PARAM_INT, 'Created from unix timestamp.', VALUE_DEFAULT, 0),
                'createdto' => new external_value(PARAM_INT, 'Created to unix timestamp.', VALUE_DEFAULT, 0),
                'modifiedfrom' => new external_value(PARAM_INT, 'Modified from unix timestamp.', VALUE_DEFAULT, 0),
                'modifiedto' => new external_value(PARAM_INT, 'Modified to unix timestamp.', VALUE_DEFAULT, 0),
            ], 'Filters.', VALUE_DEFAULT, []),
            'page' => new external_value(PARAM_INT, 'Zero-based page number.', VALUE_DEFAULT, 0),
            'perpage' => new external_value(PARAM_INT, 'Items per page.', VALUE_DEFAULT, self::DEFAULT_PERPAGE),
            'sort' => new external_value(PARAM_ALPHANUMEXT, 'Sort field.', VALUE_DEFAULT, 'timemodified'),
            'direction' => new external_value(PARAM_ALPHA, 'Sort direction: asc or desc.', VALUE_DEFAULT, 'desc'),
        ]);
    }

    /**
     * Execute service.
     *
     * @param int $cmid Course module id.
     * @param string $query Search query.
     * @param array $filters Filters.
     * @param int $page Zero-based page.
     * @param int $perpage Page size.
     * @param string $sort Sort field.
     * @param string $direction Sort direction.
     * @return array
     */
    public static function execute(
        int $cmid,
        string $query = '',
        array $filters = [],
        int $page = 0,
        int $perpage = self::DEFAULT_PERPAGE,
        string $sort = 'timemodified',
        string $direction = 'desc'
    ): array {
        global $DB;

        $params = self::validate_parameters(self::execute_parameters(), [
            'cmid' => $cmid,
            'query' => $query,
            'filters' => $filters,
            'page' => $page,
            'perpage' => $perpage,
            'sort' => $sort,
            'direction' => $direction,
        ]);

        [$course, $cm, $archive, $context] = self::load_page((int)$params['cmid']);
        self::validate_context($context);
        require_login($course, false, $cm);

        self::require_read_capability($context);

        $query = clean_param((string)$params['query'], PARAM_TEXT);
        $filters = self::normalise_filters((array)$params['filters']);
        $page = max(0, (int)$params['page']);
        $perpage = min(self::MAX_PERPAGE, max(1, (int)$params['perpage']));
        $sort = self::normalise_sort((string)$params['sort']);
        $direction = self::normalise_direction((string)$params['direction']);

        if (!self::table_exists(self::TABLE_EXTERNAL_WORK)) {
            return self::empty_response(
                $page,
                $perpage,
                self::get_permissions($context),
                self::warning('external_work', 0, 'externalworktablenotfound', 'External work table is not installed yet.')
            );
        }

        $columns = self::get_columns(self::TABLE_EXTERNAL_WORK);
        $built = self::build_query((int)$archive->id, $columns, $query, $filters, $sort, $direction);
        $records = $DB->get_records_sql($built['sql'], $built['params']);

        $visible = [];

        foreach ($records as $record) {
            if (!self::can_view_external_work($record, $context)) {
                continue;
            }

            $visible[] = self::format_external_work($record, $context);
        }

        $total = count($visible);
        $externalworks = array_slice($visible, $page * $perpage, $perpage);

        return [
            'externalworks' => $externalworks,
            'pagination' => [
                'page' => $page,
                'perpage' => $perpage,
                'total' => $total,
                'returned' => count($externalworks),
                'hasmore' => (($page + 1) * $perpage) < $total,
            ],
            'permissions' => self::get_permissions($context),
            'warnings' => [],
        ];
    }

    /**
     * Return service response structure.
     *
     * @return external_single_structure
     */
    public static function execute_returns(): external_single_structure {
        return new external_single_structure([
            'externalworks' => new external_multiple_structure(
                self::external_work_structure(),
                'Permission-filtered external works.'
            ),
            'pagination' => new external_single_structure([
                'page' => new external_value(PARAM_INT, 'Current zero-based page.'),
                'perpage' => new external_value(PARAM_INT, 'Items per page.'),
                'total' => new external_value(PARAM_INT, 'Total visible records.'),
                'returned' => new external_value(PARAM_INT, 'Returned records.'),
                'hasmore' => new external_value(PARAM_BOOL, 'Whether more visible records exist.'),
            ]),
            'permissions' => self::permissions_structure(),
            'warnings' => self::warnings_structure(),
        ]);
    }

    /**
     * Return external work structure.
     *
     * @return external_single_structure
     */
    private static function external_work_structure(): external_single_structure {
        return new external_single_structure([
            'id' => new external_value(PARAM_INT, 'External work id.'),
            'uuid' => new external_value(PARAM_RAW, 'Stable UUID.'),
            'archiveid' => new external_value(PARAM_INT, 'Archive id.'),
            'worktype' => new external_value(PARAM_ALPHANUMEXT, 'Work type.'),
            'title' => new external_value(PARAM_TEXT, 'Title.'),
            'creator' => new external_value(PARAM_TEXT, 'Creator.'),
            'publisher' => new external_value(PARAM_TEXT, 'Publisher.'),
            'publicationdate' => new external_value(PARAM_TEXT, 'Publication date.'),
            'identifier' => new external_value(PARAM_TEXT, 'Identifier.'),
            'identifiertype' => new external_value(PARAM_ALPHANUMEXT, 'Identifier type.'),
            'url' => new external_value(PARAM_URL, 'Reference URL.', VALUE_OPTIONAL),
            'citation' => new external_value(PARAM_RAW, 'Citation.'),
            'citationformat' => new external_value(PARAM_ALPHANUMEXT, 'Citation format.'),
            'rightsstatement' => new external_value(PARAM_RAW, 'Rights statement.'),
            'sourceownership' => new external_value(PARAM_ALPHANUMEXT, 'Source ownership.'),
            'status' => new external_value(PARAM_ALPHANUMEXT, 'Status.'),
            'visibility' => new external_value(PARAM_ALPHANUMEXT, 'Visibility.'),
            'audiencesuitability' => new external_value(PARAM_ALPHANUMEXT, 'Audience suitability.'),
            'createdby' => new external_value(PARAM_INT, 'Creator user id.'),
            'modifiedby' => new external_value(PARAM_INT, 'Modifier user id.'),
            'timecreated' => new external_value(PARAM_INT, 'Creation timestamp.'),
            'timemodified' => new external_value(PARAM_INT, 'Modified timestamp.'),
            'hasmarkers' => new external_value(PARAM_BOOL, 'Has content advisory markers.'),
            'isrestricted' => new external_value(PARAM_BOOL, 'Restricted work.'),
            'isculturalrestricted' => new external_value(PARAM_BOOL, 'Culturally restricted work.'),
            'metadatajson' => new external_value(PARAM_RAW, 'Permission-filtered JSON metadata.'),
        ]);
    }

    /**
     * Return permissions structure.
     *
     * @return external_single_structure
     */
    private static function permissions_structure(): external_single_structure {
        return new external_single_structure([
            'viewmedia' => new external_value(PARAM_BOOL, 'Can view media.'),
            'viewadvisories' => new external_value(PARAM_BOOL, 'Can view advisories.'),
            'manageadvisories' => new external_value(PARAM_BOOL, 'Can manage advisories.'),
            'manageexternalworks' => new external_value(PARAM_BOOL, 'Can manage external works.'),
            'viewrestrictedmedia' => new external_value(PARAM_BOOL, 'Can view restricted media.'),
            'viewrestricted' => new external_value(PARAM_BOOL, 'Can view restricted archive records.'),
            'viewculturallyrestricted' => new external_value(PARAM_BOOL, 'Can view culturally restricted records.'),
        ]);
    }

    /**
     * Return warnings structure.
     *
     * @return external_multiple_structure
     */
    private static function warnings_structure(): external_multiple_structure {
        return new external_multiple_structure(new external_single_structure([
            'item' => new external_value(PARAM_TEXT, 'Warning item.'),
            'itemid' => new external_value(PARAM_INT, 'Warning item id.'),
            'warningcode' => new external_value(PARAM_ALPHANUMEXT, 'Warning code.'),
            'message' => new external_value(PARAM_TEXT, 'Warning message.'),
        ]));
    }

    /**
     * Load page objects.
     *
     * @param int $cmid Course module id.
     * @return array
     */
    private static function load_page(int $cmid): array {
        if ($cmid <= 0) {
            throw new invalid_parameter_exception('cmid must be a positive integer.');
        }

        [$course, $cm, $archive, $context] = \uckkarchive_require_page($cmid, 0);

        return [$course, $cm, $archive, $context];
    }

    /**
     * Require read capability for external works.
     *
     * @param context_module $context Context.
     * @return void
     */
    private static function require_read_capability(context_module $context): void {
        if (has_capability('mod/uckkarchive:manageexternalworks', $context) ||
                has_capability('mod/uckkarchive:viewadvisories', $context) ||
                has_capability('mod/uckkarchive:viewmedia', $context)) {
            return;
        }

        require_capability('mod/uckkarchive:manageexternalworks', $context);
    }

    /**
     * Build SQL query.
     *
     * @param int $archiveid Archive id.
     * @param array $columns Columns.
     * @param string $query Search query.
     * @param array $filters Filters.
     * @param string $sort Sort.
     * @param string $direction Direction.
     * @return array
     */
    private static function build_query(
        int $archiveid,
        array $columns,
        string $query,
        array $filters,
        string $sort,
        string $direction
    ): array {
        global $DB;

        $joins = [];
        $where = ['1 = 1'];
        $params = [];

        $archivefield = self::first_column($columns, ['archiveid', 'uckkarchiveid']);
        if ($archivefield !== null) {
            $where[] = "ew.{$archivefield} = :archiveid";
            $params['archiveid'] = $archiveid;
        }

        self::add_exact_filter($where, $params, $columns, 'worktype', $filters['worktype']);
        self::add_exact_filter($where, $params, $columns, 'status', $filters['status']);
        self::add_exact_filter($where, $params, $columns, 'visibility', $filters['visibility']);
        self::add_exact_filter($where, $params, $columns, 'sourceownership', $filters['sourceownership']);
        self::add_exact_filter($where, $params, $columns, 'audiencesuitability', $filters['audiencesuitability']);

        self::add_like_filter($where, $params, $columns, 'creator', $filters['creator']);
        self::add_like_filter($where, $params, $columns, 'publisher', $filters['publisher']);
        self::add_like_filter($where, $params, $columns, 'identifier', $filters['identifier']);

        self::add_time_filter($where, $params, $columns, 'timecreated', 'createdfrom', '>=', (int)$filters['createdfrom']);
        self::add_time_filter($where, $params, $columns, 'timecreated', 'createdto', '<=', (int)$filters['createdto']);
        self::add_time_filter($where, $params, $columns, 'timemodified', 'modifiedfrom', '>=', (int)$filters['modifiedfrom']);
        self::add_time_filter($where, $params, $columns, 'timemodified', 'modifiedto', '<=', (int)$filters['modifiedto']);

        if ($query !== '') {
            $searchparts = [];
            foreach (['title', 'creator', 'publisher', 'identifier', 'citation', 'rightsstatement'] as $field) {
                if (self::column_exists($columns, $field)) {
                    $searchparts[] = $DB->sql_like("ew.{$field}", ':query', false, false);
                }
            }

            if (!empty($searchparts)) {
                $where[] = '(' . implode(' OR ', $searchparts) . ')';
                $params['query'] = '%' . $query . '%';
            }
        }

        if (!empty($filters['hasrestricted']) && self::column_exists($columns, 'visibility')) {
            [$sql, $restrictedparams] = self::restricted_visibility_sql('ew.visibility', 'rv');
            $where[] = $sql;
            $params += $restrictedparams;
        }

        if (!empty($filters['hasmarkers']) && self::table_exists(self::TABLE_CONTENT_MARKER)) {
            $markercolumns = self::get_columns(self::TABLE_CONTENT_MARKER);
            $externalworkfield = self::first_column($markercolumns, ['externalworkid', 'external_work_id']);

            if ($externalworkfield !== null) {
                $joins[] = "JOIN {" . self::TABLE_CONTENT_MARKER . "} cm ON cm.{$externalworkfield} = ew.id";
            }
        }

        $sortfield = self::first_column($columns, [$sort]);
        if ($sortfield === null) {
            $sortfield = self::first_column($columns, ['timemodified', 'timecreated', 'title', 'id']) ?? 'id';
        }

        $joinsql = implode("\n", array_unique($joins));
        $wheresql = implode(' AND ', $where);

        $sql = "SELECT DISTINCT ew.*
                  FROM {" . self::TABLE_EXTERNAL_WORK . "} ew
                       {$joinsql}
                 WHERE {$wheresql}
              ORDER BY ew.{$sortfield} {$direction}, ew.id {$direction}";

        return [
            'sql' => $sql,
            'params' => $params,
        ];
    }

    /**
     * Format one external work.
     *
     * @param stdClass $record Record.
     * @param context_module $context Context.
     * @return array
     */
    private static function format_external_work(stdClass $record, context_module $context): array {
        $isrestricted = self::is_restricted($record);
        $isculturalrestricted = self::is_culturally_restricted($record);
        $canviewrestricted = self::can_view_restricted($record, $context);

        $citation = (string)self::field($record, ['citation'], '');
        $rights = (string)self::field($record, ['rightsstatement', 'rights'], '');
        $metadata = (string)self::field($record, ['metadata'], '{}');
        $url = (string)self::field($record, ['url', 'sourceurl'], '');

        if ($isrestricted && !$canviewrestricted) {
            $citation = '';
            $rights = '';
            $metadata = '{}';
            $url = '';
        }

        $data = [
            'id' => (int)$record->id,
            'uuid' => (string)self::field($record, ['uuid'], ''),
            'archiveid' => (int)self::field($record, ['archiveid', 'uckkarchiveid'], 0),
            'worktype' => (string)self::field($record, ['worktype', 'type'], ''),
            'title' => format_string((string)self::field($record, ['title'], '')),
            'creator' => format_string((string)self::field($record, ['creator', 'author'], '')),
            'publisher' => format_string((string)self::field($record, ['publisher'], '')),
            'publicationdate' => (string)self::field($record, ['publicationdate', 'year'], ''),
            'identifier' => (string)self::field($record, ['identifier'], ''),
            'identifiertype' => (string)self::field($record, ['identifier_type', 'identifiertype'], ''),
            'citation' => format_text($citation, FORMAT_PLAIN, ['para' => false]),
            'citationformat' => (string)self::field($record, ['citationformat', 'citation_format'], ''),
            'rightsstatement' => format_text($rights, FORMAT_PLAIN, ['para' => false]),
            'sourceownership' => (string)self::field($record, ['sourceownership'], 'unknown_source'),
            'status' => (string)self::field($record, ['status'], 'active'),
            'visibility' => (string)self::field($record, ['visibility'], 'course'),
            'audiencesuitability' => (string)self::field($record, ['audiencesuitability'], 'guided'),
            'createdby' => (int)self::field($record, ['createdby', 'userid'], 0),
            'modifiedby' => (int)self::field($record, ['modifiedby'], 0),
            'timecreated' => (int)self::field($record, ['timecreated'], 0),
            'timemodified' => (int)self::field($record, ['timemodified'], 0),
            'hasmarkers' => self::has_content_markers((int)$record->id),
            'isrestricted' => $isrestricted,
            'isculturalrestricted' => $isculturalrestricted,
            'metadatajson' => $metadata !== '' ? $metadata : '{}',
        ];

        if ($url !== '') {
            $data['url'] = $url;
        }

        return $data;
    }

    /**
     * Return whether current user can view one external work.
     *
     * @param stdClass $record Record.
     * @param context_module $context Context.
     * @return bool
     */
    private static function can_view_external_work(stdClass $record, context_module $context): bool {
        if ((string)self::field($record, ['status'], '') === 'deleted_soft') {
            return has_capability('mod/uckkarchive:manageexternalworks', $context);
        }

        if (self::is_restricted($record)) {
            return self::can_view_restricted($record, $context);
        }

        return has_capability('mod/uckkarchive:viewmedia', $context) ||
            has_capability('mod/uckkarchive:viewadvisories', $context) ||
            has_capability('mod/uckkarchive:manageexternalworks', $context);
    }

    /**
     * Return whether record is restricted.
     *
     * @param stdClass $record Record.
     * @return bool
     */
    private static function is_restricted(stdClass $record): bool {
        $visibility = (string)self::field($record, ['visibility'], '');
        $status = (string)self::field($record, ['status'], '');

        return in_array($visibility, ['restricted', 'restricted_integrity', 'restricted_cultural'], true) ||
            in_array($status, ['restricted'], true) ||
            !empty($record->restricted);
    }

    /**
     * Return whether record is culturally restricted.
     *
     * @param stdClass $record Record.
     * @return bool
     */
    private static function is_culturally_restricted(stdClass $record): bool {
        return (string)self::field($record, ['visibility'], '') === 'restricted_cultural' ||
            !empty($record->culturalprotocol);
    }

    /**
     * Return whether current user can view restricted work details.
     *
     * @param stdClass $record Record.
     * @param context_module $context Context.
     * @return bool
     */
    private static function can_view_restricted(stdClass $record, context_module $context): bool {
        if (self::is_culturally_restricted($record)) {
            return has_capability('mod/uckkarchive:viewculturallyrestricted', $context);
        }

        return has_capability('mod/uckkarchive:viewrestrictedmedia', $context) ||
            has_capability('mod/uckkarchive:viewrestricted', $context) ||
            has_capability('mod/uckkarchive:manageexternalworks', $context);
    }

    /**
     * Return permissions.
     *
     * @param context_module $context Context.
     * @return array
     */
    private static function get_permissions(context_module $context): array {
        return [
            'viewmedia' => has_capability('mod/uckkarchive:viewmedia', $context),
            'viewadvisories' => has_capability('mod/uckkarchive:viewadvisories', $context),
            'manageadvisories' => has_capability('mod/uckkarchive:manageadvisories', $context),
            'manageexternalworks' => has_capability('mod/uckkarchive:manageexternalworks', $context),
            'viewrestrictedmedia' => has_capability('mod/uckkarchive:viewrestrictedmedia', $context),
            'viewrestricted' => has_capability('mod/uckkarchive:viewrestricted', $context),
            'viewculturallyrestricted' => has_capability('mod/uckkarchive:viewculturallyrestricted', $context),
        ];
    }

    /**
     * Normalize filters.
     *
     * @param array $filters Raw filters.
     * @return array
     */
    private static function normalise_filters(array $filters): array {
        $defaults = [
            'worktype' => '',
            'status' => '',
            'visibility' => '',
            'sourceownership' => '',
            'audiencesuitability' => '',
            'creator' => '',
            'publisher' => '',
            'identifier' => '',
            'hasmarkers' => false,
            'hasrestricted' => false,
            'createdfrom' => 0,
            'createdto' => 0,
            'modifiedfrom' => 0,
            'modifiedto' => 0,
        ];

        $filters = array_merge($defaults, $filters);

        foreach (['worktype', 'status', 'visibility', 'sourceownership', 'audiencesuitability'] as $field) {
            $filters[$field] = clean_param((string)$filters[$field], PARAM_ALPHANUMEXT);
        }

        foreach (['creator', 'publisher', 'identifier'] as $field) {
            $filters[$field] = clean_param((string)$filters[$field], PARAM_TEXT);
        }

        foreach (['createdfrom', 'createdto', 'modifiedfrom', 'modifiedto'] as $field) {
            $filters[$field] = max(0, (int)$filters[$field]);
        }

        $filters['hasmarkers'] = !empty($filters['hasmarkers']);
        $filters['hasrestricted'] = !empty($filters['hasrestricted']);

        return $filters;
    }

    /**
     * Normalize sort.
     *
     * @param string $sort Sort.
     * @return string
     */
    private static function normalise_sort(string $sort): string {
        $sort = clean_param($sort, PARAM_ALPHANUMEXT);
        $allowed = ['title', 'worktype', 'creator', 'publisher', 'publicationdate', 'timecreated', 'timemodified'];

        return in_array($sort, $allowed, true) ? $sort : 'timemodified';
    }

    /**
     * Normalize direction.
     *
     * @param string $direction Direction.
     * @return string
     */
    private static function normalise_direction(string $direction): string {
        $direction = strtolower(clean_param($direction, PARAM_ALPHA));

        return $direction === 'asc' ? 'ASC' : 'DESC';
    }

    /**
     * Add exact filter.
     *
     * @param array $where Where.
     * @param array $params Params.
     * @param array $columns Columns.
     * @param string $field Field.
     * @param string $value Value.
     * @return void
     */
    private static function add_exact_filter(array &$where, array &$params, array $columns, string $field, string $value): void {
        if ($value === '' || !self::column_exists($columns, $field)) {
            return;
        }

        $where[] = "ew.{$field} = :{$field}";
        $params[$field] = $value;
    }

    /**
     * Add LIKE filter.
     *
     * @param array $where Where.
     * @param array $params Params.
     * @param array $columns Columns.
     * @param string $field Field.
     * @param string $value Value.
     * @return void
     */
    private static function add_like_filter(array &$where, array &$params, array $columns, string $field, string $value): void {
        global $DB;

        if ($value === '' || !self::column_exists($columns, $field)) {
            return;
        }

        $where[] = $DB->sql_like("ew.{$field}", ':' . $field, false, false);
        $params[$field] = '%' . $value . '%';
    }

    /**
     * Add time filter.
     *
     * @param array $where Where.
     * @param array $params Params.
     * @param array $columns Columns.
     * @param string $field Field.
     * @param string $paramname Param.
     * @param string $operator Operator.
     * @param int $value Value.
     * @return void
     */
    private static function add_time_filter(
        array &$where,
        array &$params,
        array $columns,
        string $field,
        string $paramname,
        string $operator,
        int $value
    ): void {
        if ($value <= 0 || !self::column_exists($columns, $field)) {
            return;
        }

        $where[] = "ew.{$field} {$operator} :{$paramname}";
        $params[$paramname] = $value;
    }

    /**
     * Return restricted visibility SQL.
     *
     * @param string $field Field expression.
     * @param string $prefix Parameter prefix.
     * @return array
     */
    private static function restricted_visibility_sql(string $field, string $prefix): array {
        $values = ['restricted', 'restricted_integrity', 'restricted_cultural'];
        $params = [];
        $placeholders = [];

        foreach ($values as $index => $value) {
            $key = $prefix . $index;
            $params[$key] = $value;
            $placeholders[] = ':' . $key;
        }

        return [
            $field . ' IN (' . implode(',', $placeholders) . ')',
            $params,
        ];
    }

    /**
     * Return whether external work has content markers.
     *
     * @param int $externalworkid External work id.
     * @return bool
     */
    private static function has_content_markers(int $externalworkid): bool {
        global $DB;

        if ($externalworkid <= 0 || !self::table_exists(self::TABLE_CONTENT_MARKER)) {
            return false;
        }

        $columns = self::get_columns(self::TABLE_CONTENT_MARKER);
        $field = self::first_column($columns, ['externalworkid', 'external_work_id']);

        if ($field === null) {
            return false;
        }

        return $DB->record_exists(self::TABLE_CONTENT_MARKER, [$field => $externalworkid]);
    }

    /**
     * Return empty response.
     *
     * @param int $page Page.
     * @param int $perpage Per page.
     * @param array $permissions Permissions.
     * @param array|null $warning Warning.
     * @return array
     */
    private static function empty_response(int $page, int $perpage, array $permissions, ?array $warning = null): array {
        return [
            'externalworks' => [],
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
     * Return warning.
     *
     * @param string $item Item.
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

    /**
     * Return field value.
     *
     * @param stdClass $record Record.
     * @param array $fields Candidate fields.
     * @param mixed $default Default.
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
     * Return first existing column.
     *
     * @param array $columns Columns.
     * @param array $candidates Candidates.
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

    /**
     * Return whether column exists.
     *
     * @param array $columns Columns.
     * @param string $field Field.
     * @return bool
     */
    private static function column_exists(array $columns, string $field): bool {
        return array_key_exists($field, $columns);
    }

    /**
     * Return whether table exists.
     *
     * @param string $table Table name.
     * @return bool
     */
    private static function table_exists(string $table): bool {
        global $DB;

        return $DB->get_manager()->table_exists(new \xmldb_table($table));
    }

    /**
     * Return table columns.
     *
     * @param string $table Table name.
     * @return array
     */
    private static function get_columns(string $table): array {
        global $DB;

        return $DB->get_columns($table);
    }
}
