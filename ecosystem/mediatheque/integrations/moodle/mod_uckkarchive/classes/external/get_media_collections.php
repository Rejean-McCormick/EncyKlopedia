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

/**
 * Return media collections for the UCKK Archive media library.
 *
 * @package    mod_uckkarchive
 * @copyright  2026 UCKK
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
use moodle_exception;
use required_capability_exception;
use stdClass;

/**
 * External service for listing media collections.
 *
 * Target service name:
 *
 * ```text
 * mod_uckkarchive_get_media_collections
 * ```
 *
 * This service is read-only. It returns collection records visible to the
 * current user and never exposes restricted collection metadata to users who
 * lack restricted-media access.
 */
class get_media_collections extends external_api {

    /** @var string Collection table. */
    private const COLLECTION_TABLE = 'uckkarchive_media_collection';

    /** @var string Collection membership table. */
    private const COLLECTION_ITEM_TABLE = 'uckkarchive_media_collection_item';

    /** @var string Media table. */
    private const MEDIA_TABLE = 'uckkarchive_media';

    /** @var int Default page size. */
    private const DEFAULT_PERPAGE = 20;

    /** @var int Maximum page size. */
    private const MAX_PERPAGE = 100;

    /** @var string Restricted visibility. */
    private const VISIBILITY_RESTRICTED = 'restricted';

    /** @var string Restricted integrity visibility. */
    private const VISIBILITY_RESTRICTED_INTEGRITY = 'restricted_integrity';

    /** @var string Restricted cultural visibility. */
    private const VISIBILITY_RESTRICTED_CULTURAL = 'restricted_cultural';

    /**
     * Define service parameters.
     *
     * @return external_function_parameters
     */
    public static function execute_parameters(): external_function_parameters {
        return new external_function_parameters([
            'cmid' => new external_value(
                PARAM_INT,
                'Course module id for the uckkarchive activity.'
            ),
            'filters' => new external_single_structure([
                'visibility' => new external_value(
                    PARAM_ALPHANUMEXT,
                    'Visibility filter.',
                    VALUE_DEFAULT,
                    ''
                ),
                'purpose' => new external_value(
                    PARAM_ALPHANUMEXT,
                    'Collection purpose filter.',
                    VALUE_DEFAULT,
                    ''
                ),
                'ownerid' => new external_value(
                    PARAM_INT,
                    'Owner user id filter.',
                    VALUE_DEFAULT,
                    0
                ),
                'search' => new external_value(
                    PARAM_TEXT,
                    'Search text for title/description.',
                    VALUE_DEFAULT,
                    ''
                ),
                'hasitems' => new external_value(
                    PARAM_BOOL,
                    'Only return collections with at least one media item.',
                    VALUE_DEFAULT,
                    false
                ),
                'createdfrom' => new external_value(
                    PARAM_INT,
                    'Created from unix timestamp.',
                    VALUE_DEFAULT,
                    0
                ),
                'createdto' => new external_value(
                    PARAM_INT,
                    'Created to unix timestamp.',
                    VALUE_DEFAULT,
                    0
                ),
                'modifiedfrom' => new external_value(
                    PARAM_INT,
                    'Modified from unix timestamp.',
                    VALUE_DEFAULT,
                    0
                ),
                'modifiedto' => new external_value(
                    PARAM_INT,
                    'Modified to unix timestamp.',
                    VALUE_DEFAULT,
                    0
                ),
            ], 'Collection filters.', VALUE_DEFAULT, []),
            'page' => new external_value(
                PARAM_INT,
                'Zero-based page number.',
                VALUE_DEFAULT,
                0
            ),
            'perpage' => new external_value(
                PARAM_INT,
                'Items per page.',
                VALUE_DEFAULT,
                self::DEFAULT_PERPAGE
            ),
            'sort' => new external_value(
                PARAM_ALPHANUMEXT,
                'Sort field: title, purpose, visibility, timecreated, timemodified.',
                VALUE_DEFAULT,
                'timemodified'
            ),
            'direction' => new external_value(
                PARAM_ALPHA,
                'Sort direction: asc or desc.',
                VALUE_DEFAULT,
                'desc'
            ),
            'includeitems' => new external_value(
                PARAM_BOOL,
                'Include a small preview list of media item ids.',
                VALUE_DEFAULT,
                false
            ),
        ]);
    }

    /**
     * Execute the service.
     *
     * @param int $cmid Course module id.
     * @param array<string, mixed> $filters Filters.
     * @param int $page Zero-based page number.
     * @param int $perpage Items per page.
     * @param string $sort Sort field.
     * @param string $direction Sort direction.
     * @param bool $includeitems Include item preview.
     * @return array<string, mixed>
     * @throws invalid_parameter_exception
     * @throws moodle_exception
     * @throws required_capability_exception
     */
    public static function execute(
        int $cmid,
        array $filters = [],
        int $page = 0,
        int $perpage = self::DEFAULT_PERPAGE,
        string $sort = 'timemodified',
        string $direction = 'desc',
        bool $includeitems = false
    ): array {
        global $DB;

        $params = self::validate_parameters(self::execute_parameters(), [
            'cmid' => $cmid,
            'filters' => $filters,
            'page' => $page,
            'perpage' => $perpage,
            'sort' => $sort,
            'direction' => $direction,
            'includeitems' => $includeitems,
        ]);

        [$course, $cm, $archive, $context] = self::load_page((int)$params['cmid']);
        self::validate_context($context);

        require_capability('mod/uckkarchive:viewmedia', $context);

        $page = max(0, (int)$params['page']);
        $perpage = min(self::MAX_PERPAGE, max(1, (int)$params['perpage']));
        $filters = self::normalise_filters((array)$params['filters']);
        $sort = self::normalise_sort((string)$params['sort']);
        $direction = self::normalise_direction((string)$params['direction']);
        $includeitems = !empty($params['includeitems']);

        if (!self::table_exists(self::COLLECTION_TABLE)) {
            return self::empty_response(
                $page,
                $perpage,
                self::get_permissions($context),
                self::warning(
                    'media_collection',
                    0,
                    'collectiontablenotfound',
                    'Media collection table is not installed yet.'
                )
            );
        }

        $columns = self::get_columns(self::COLLECTION_TABLE);
        $query = self::build_query((int)$archive->id, $columns, $filters, $sort, $direction);
        $records = $DB->get_records_sql($query['sql'], $query['params']);

        $visible = [];

        foreach ($records as $record) {
            if (!self::can_view_collection($record, $context)) {
                continue;
            }

            $visible[] = self::export_collection($record, $context, $includeitems);
        }

        $total = count($visible);
        $collections = array_slice($visible, $page * $perpage, $perpage);

        return [
            'collections' => $collections,
            'pagination' => [
                'page' => $page,
                'perpage' => $perpage,
                'total' => $total,
                'returned' => count($collections),
                'hasmore' => (($page + 1) * $perpage) < $total,
            ],
            'permissions' => self::get_permissions($context),
            'warnings' => [],
        ];
    }

    /**
     * Define service returns.
     *
     * @return external_single_structure
     */
    public static function execute_returns(): external_single_structure {
        return new external_single_structure([
            'collections' => new external_multiple_structure(
                self::collection_structure(),
                'Permission-filtered media collections.'
            ),
            'pagination' => new external_single_structure([
                'page' => new external_value(PARAM_INT, 'Current zero-based page.'),
                'perpage' => new external_value(PARAM_INT, 'Items per page.'),
                'total' => new external_value(PARAM_INT, 'Total visible collections.'),
                'returned' => new external_value(PARAM_INT, 'Returned collections.'),
                'hasmore' => new external_value(PARAM_BOOL, 'Whether more visible collections exist.'),
            ]),
            'permissions' => self::permissions_structure(),
            'warnings' => self::warnings_structure(),
        ]);
    }

    /**
     * Return collection structure.
     *
     * @return external_single_structure
     */
    private static function collection_structure(): external_single_structure {
        return new external_single_structure([
            'id' => new external_value(PARAM_INT, 'Collection id.'),
            'uuid' => new external_value(PARAM_RAW, 'Collection UUID.'),
            'archiveid' => new external_value(PARAM_INT, 'Archive instance id.'),
            'title' => new external_value(PARAM_TEXT, 'Collection title.'),
            'description' => new external_value(PARAM_RAW, 'Permission-filtered description.'),
            'purpose' => new external_value(PARAM_ALPHANUMEXT, 'Collection purpose.'),
            'visibility' => new external_value(PARAM_ALPHANUMEXT, 'Collection visibility.'),
            'audiencesuitability' => new external_value(PARAM_ALPHANUMEXT, 'Audience suitability.'),
            'ownerid' => new external_value(PARAM_INT, 'Owner user id.'),
            'createdby' => new external_value(PARAM_INT, 'Creator user id.'),
            'modifiedby' => new external_value(PARAM_INT, 'Modifier user id.'),
            'timecreated' => new external_value(PARAM_INT, 'Creation timestamp.'),
            'timemodified' => new external_value(PARAM_INT, 'Modified timestamp.'),
            'itemcount' => new external_value(PARAM_INT, 'Number of media items in the collection.'),
            'isrestricted' => new external_value(PARAM_BOOL, 'Whether collection is restricted.'),
            'isculturalrestricted' => new external_value(PARAM_BOOL, 'Whether collection is culturally restricted.'),
            'items' => new external_multiple_structure(
                new external_single_structure([
                    'mediaid' => new external_value(PARAM_INT, 'Media id.'),
                    'sortorder' => new external_value(PARAM_INT, 'Sort order.'),
                ]),
                'Preview list of media ids in collection.',
                VALUE_OPTIONAL
            ),
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
            'addmedia' => new external_value(PARAM_BOOL, 'Can add media.'),
            'editmedia' => new external_value(PARAM_BOOL, 'Can edit media.'),
            'managemediacollections' => new external_value(PARAM_BOOL, 'Can manage media collections.'),
            'viewrestrictedmedia' => new external_value(PARAM_BOOL, 'Can view restricted media.'),
            'viewculturallyrestricted' => new external_value(PARAM_BOOL, 'Can view culturally restricted material.'),
        ]);
    }

    /**
     * Return warnings structure.
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
     * Load Moodle page objects.
     *
     * @param int $cmid Course module id.
     * @return array{0:stdClass,1:stdClass,2:stdClass,3:context_module}
     */
    private static function load_page(int $cmid): array {
        [$course, $cm, $archive, $context] = \uckkarchive_require_page($cmid, 0);
        return [$course, $cm, $archive, $context];
    }

    /**
     * Build collection list SQL.
     *
     * @param int $archiveid Archive id.
     * @param array<string, object> $columns Collection table columns.
     * @param array<string, mixed> $filters Filters.
     * @param string $sort Sort field.
     * @param string $direction Sort direction.
     * @return array{sql:string,params:array<string,mixed>}
     */
    private static function build_query(
        int $archiveid,
        array $columns,
        array $filters,
        string $sort,
        string $direction
    ): array {
        $params = [];
        $joins = [];
        $where = ['1 = 1'];

        $archivefield = self::first_column($columns, ['archiveid', 'uckkarchiveid']);
        if ($archivefield !== null) {
            $where[] = "c.{$archivefield} = :archiveid";
            $params['archiveid'] = $archiveid;
        }

        self::add_string_filter($where, $params, $columns, 'c', ['visibility'], 'visibility', $filters['visibility']);
        self::add_string_filter($where, $params, $columns, 'c', ['purpose', 'collectiontype', 'type'], 'purpose', $filters['purpose']);
        self::add_int_filter($where, $params, $columns, 'c', ['ownerid', 'userid', 'createdby'], 'ownerid', (int)$filters['ownerid']);
        self::add_time_filter($where, $params, $columns, 'c', 'timecreated', 'createdfrom', '>=', (int)$filters['createdfrom']);
        self::add_time_filter($where, $params, $columns, 'c', 'timecreated', 'createdto', '<=', (int)$filters['createdto']);
        self::add_time_filter($where, $params, $columns, 'c', 'timemodified', 'modifiedfrom', '>=', (int)$filters['modifiedfrom']);
        self::add_time_filter($where, $params, $columns, 'c', 'timemodified', 'modifiedto', '<=', (int)$filters['modifiedto']);

        if ($filters['search'] !== '') {
            $searchparts = [];
            if (self::column_exists($columns, 'title')) {
                $searchparts[] = self::sql_like('c.title', ':search');
            }
            if (self::column_exists($columns, 'description')) {
                $searchparts[] = self::sql_like('c.description', ':search');
            }
            if (!empty($searchparts)) {
                $where[] = '(' . implode(' OR ', $searchparts) . ')';
                $params['search'] = '%' . $filters['search'] . '%';
            }
        }

        if (!empty($filters['hasitems']) && self::table_exists(self::COLLECTION_ITEM_TABLE)) {
            $membershipcolumns = self::get_columns(self::COLLECTION_ITEM_TABLE);
            $collectionfield = self::first_column($membershipcolumns, ['collectionid', 'mediacollectionid']);
            if ($collectionfield !== null) {
                $joins[] = "JOIN {" . self::COLLECTION_ITEM_TABLE . "} ci ON ci.{$collectionfield} = c.id";
            }
        }

        $sortfield = self::first_column($columns, [$sort]);
        if ($sortfield === null) {
            $sortfield = self::first_column($columns, ['timemodified', 'timecreated', 'id']) ?? 'id';
        }

        $sql = "SELECT DISTINCT c.*
                  FROM {" . self::COLLECTION_TABLE . "} c
                       " . implode("\n", array_unique($joins)) . "
                 WHERE " . implode(' AND ', $where) . "
              ORDER BY c.{$sortfield} {$direction}, c.id {$direction}";

        return [
            'sql' => $sql,
            'params' => $params,
        ];
    }

    /**
     * Export one collection.
     *
     * @param stdClass $record Collection record.
     * @param context_module $context Module context.
     * @param bool $includeitems Include item preview.
     * @return array<string, mixed>
     */
    private static function export_collection(stdClass $record, context_module $context, bool $includeitems): array {
        $isrestricted = self::is_restricted_collection($record);
        $isculturalrestricted = self::is_culturally_restricted_collection($record);
        $canseefull = self::can_view_restricted_collection($context, $record);

        $description = (string)self::field($record, ['description', 'summary'], '');
        if ($isrestricted && !$canseefull) {
            $description = '';
        }

        $collection = [
            'id' => (int)$record->id,
            'uuid' => (string)self::field($record, ['uuid'], ''),
            'archiveid' => (int)self::field($record, ['archiveid', 'uckkarchiveid'], 0),
            'title' => format_string((string)self::field($record, ['title', 'name'], get_string('collection', 'mod_uckkarchive'))),
            'description' => format_text($description, FORMAT_HTML, ['para' => false]),
            'purpose' => (string)self::field($record, ['purpose', 'collectiontype', 'type'], ''),
            'visibility' => (string)self::field($record, ['visibility'], 'restricted'),
            'audiencesuitability' => (string)self::field($record, ['audiencesuitability'], ''),
            'ownerid' => (int)self::field($record, ['ownerid', 'userid', 'createdby'], 0),
            'createdby' => (int)self::field($record, ['createdby', 'userid', 'ownerid'], 0),
            'modifiedby' => (int)self::field($record, ['modifiedby'], 0),
            'timecreated' => (int)self::field($record, ['timecreated'], 0),
            'timemodified' => (int)self::field($record, ['timemodified'], 0),
            'itemcount' => self::count_collection_items((int)$record->id),
            'isrestricted' => $isrestricted,
            'isculturalrestricted' => $isculturalrestricted,
        ];

        if ($includeitems) {
            $collection['items'] = self::get_collection_item_preview((int)$record->id, $context);
        }

        return $collection;
    }

    /**
     * Return whether the user may view a collection.
     *
     * @param stdClass $record Collection record.
     * @param context_module $context Module context.
     * @return bool
     */
    private static function can_view_collection(stdClass $record, context_module $context): bool {
        global $USER;

        if (self::is_restricted_collection($record)) {
            return self::can_view_restricted_collection($context, $record);
        }

        $visibility = (string)self::field($record, ['visibility'], 'restricted');

        if ($visibility === 'private') {
            $ownerid = (int)self::field($record, ['ownerid', 'userid', 'createdby'], 0);
            if ($ownerid > 0 && $ownerid === (int)$USER->id) {
                return true;
            }

            return has_capability('mod/uckkarchive:managemediacollections', $context);
        }

        return has_capability('mod/uckkarchive:viewmedia', $context);
    }

    /**
     * Return whether user may see restricted collection data.
     *
     * @param context_module $context Module context.
     * @param stdClass $record Collection record.
     * @return bool
     */
    private static function can_view_restricted_collection(context_module $context, stdClass $record): bool {
        if (self::is_culturally_restricted_collection($record)) {
            return has_capability('mod/uckkarchive:viewculturallyrestricted', $context);
        }

        return has_capability('mod/uckkarchive:viewrestrictedmedia', $context) ||
            has_capability('mod/uckkarchive:viewrestricted', $context);
    }

    /**
     * Return whether collection is restricted.
     *
     * @param stdClass $record Collection record.
     * @return bool
     */
    private static function is_restricted_collection(stdClass $record): bool {
        $visibility = (string)self::field($record, ['visibility'], '');

        return in_array($visibility, [
            self::VISIBILITY_RESTRICTED,
            self::VISIBILITY_RESTRICTED_INTEGRITY,
            self::VISIBILITY_RESTRICTED_CULTURAL,
        ], true) || !empty($record->restricted);
    }

    /**
     * Return whether collection is culturally restricted.
     *
     * @param stdClass $record Collection record.
     * @return bool
     */
    private static function is_culturally_restricted_collection(stdClass $record): bool {
        $visibility = (string)self::field($record, ['visibility'], '');

        return $visibility === self::VISIBILITY_RESTRICTED_CULTURAL || !empty($record->culturalprotocol);
    }

    /**
     * Count collection items.
     *
     * @param int $collectionid Collection id.
     * @return int
     */
    private static function count_collection_items(int $collectionid): int {
        global $DB;

        if ($collectionid <= 0 || !self::table_exists(self::COLLECTION_ITEM_TABLE)) {
            return 0;
        }

        $columns = self::get_columns(self::COLLECTION_ITEM_TABLE);
        $collectionfield = self::first_column($columns, ['collectionid', 'mediacollectionid']);
        if ($collectionfield === null) {
            return 0;
        }

        return (int)$DB->count_records(self::COLLECTION_ITEM_TABLE, [$collectionfield => $collectionid]);
    }

    /**
     * Return collection item preview.
     *
     * @param int $collectionid Collection id.
     * @param context_module $context Module context.
     * @return array<int, array<string, int>>
     */
    private static function get_collection_item_preview(int $collectionid, context_module $context): array {
        global $DB;

        if ($collectionid <= 0 || !self::table_exists(self::COLLECTION_ITEM_TABLE)) {
            return [];
        }

        $columns = self::get_columns(self::COLLECTION_ITEM_TABLE);
        $collectionfield = self::first_column($columns, ['collectionid', 'mediacollectionid']);
        $mediafield = self::first_column($columns, ['mediaid', 'itemid']);
        $sortfield = self::first_column($columns, ['sortorder', 'position', 'id']);

        if ($collectionfield === null || $mediafield === null) {
            return [];
        }

        $records = $DB->get_records(
            self::COLLECTION_ITEM_TABLE,
            [$collectionfield => $collectionid],
            $sortfield ? "{$sortfield} ASC" : 'id ASC',
            '*',
            0,
            20
        );

        $items = [];
        foreach ($records as $record) {
            $mediaid = (int)$record->{$mediafield};
            if ($mediaid <= 0 || !self::can_view_media_id($mediaid, $context)) {
                continue;
            }

            $items[] = [
                'mediaid' => $mediaid,
                'sortorder' => isset($record->sortorder) ? (int)$record->sortorder : 0,
            ];
        }

        return $items;
    }

    /**
     * Return whether user may view a media id.
     *
     * @param int $mediaid Media id.
     * @param context_module $context Module context.
     * @return bool
     */
    private static function can_view_media_id(int $mediaid, context_module $context): bool {
        global $DB;

        if ($mediaid <= 0 || !self::table_exists(self::MEDIA_TABLE)) {
            return false;
        }

        $media = $DB->get_record(self::MEDIA_TABLE, ['id' => $mediaid]);
        if (!$media) {
            return false;
        }

        $visibility = (string)self::field($media, ['visibility'], '');
        if (in_array($visibility, [
            self::VISIBILITY_RESTRICTED,
            self::VISIBILITY_RESTRICTED_INTEGRITY,
            self::VISIBILITY_RESTRICTED_CULTURAL,
        ], true)) {
            if ($visibility === self::VISIBILITY_RESTRICTED_CULTURAL) {
                return has_capability('mod/uckkarchive:viewculturallyrestricted', $context);
            }

            return has_capability('mod/uckkarchive:viewrestrictedmedia', $context);
        }

        return has_capability('mod/uckkarchive:viewmedia', $context);
    }

    /**
     * Return permissions summary.
     *
     * @param context_module $context Module context.
     * @return array<string, bool>
     */
    private static function get_permissions(context_module $context): array {
        return [
            'viewmedia' => has_capability('mod/uckkarchive:viewmedia', $context),
            'addmedia' => has_capability('mod/uckkarchive:addmedia', $context),
            'editmedia' => has_capability('mod/uckkarchive:editmedia', $context),
            'managemediacollections' => has_capability('mod/uckkarchive:managemediacollections', $context),
            'viewrestrictedmedia' => has_capability('mod/uckkarchive:viewrestrictedmedia', $context),
            'viewculturallyrestricted' => has_capability('mod/uckkarchive:viewculturallyrestricted', $context),
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
            'visibility' => '',
            'purpose' => '',
            'ownerid' => 0,
            'search' => '',
            'hasitems' => false,
            'createdfrom' => 0,
            'createdto' => 0,
            'modifiedfrom' => 0,
            'modifiedto' => 0,
        ];

        $filters = array_merge($defaults, $filters);

        foreach (['visibility', 'purpose'] as $key) {
            $filters[$key] = clean_param((string)$filters[$key], PARAM_ALPHANUMEXT);
        }

        $filters['search'] = clean_param((string)$filters['search'], PARAM_TEXT);

        foreach (['ownerid', 'createdfrom', 'createdto', 'modifiedfrom', 'modifiedto'] as $key) {
            $filters[$key] = max(0, (int)$filters[$key]);
        }

        $filters['hasitems'] = !empty($filters['hasitems']);

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
        $allowed = ['title', 'purpose', 'visibility', 'timecreated', 'timemodified'];

        return in_array($sort, $allowed, true) ? $sort : 'timemodified';
    }

    /**
     * Normalize sort direction.
     *
     * @param string $direction Direction.
     * @return string
     */
    private static function normalise_direction(string $direction): string {
        $direction = strtolower(clean_param($direction, PARAM_ALPHA));
        return $direction === 'asc' ? 'ASC' : 'DESC';
    }

    /**
     * Add string filter when a column exists.
     *
     * @param string[] $where Where clauses.
     * @param array<string, mixed> $params SQL params.
     * @param array<string, object> $columns Columns.
     * @param string $alias SQL alias.
     * @param string[] $candidates Candidate fields.
     * @param string $paramname Parameter name.
     * @param string $value Value.
     * @return void
     */
    private static function add_string_filter(
        array &$where,
        array &$params,
        array $columns,
        string $alias,
        array $candidates,
        string $paramname,
        string $value
    ): void {
        if ($value === '') {
            return;
        }

        $field = self::first_column($columns, $candidates);
        if ($field === null) {
            return;
        }

        $where[] = "{$alias}.{$field} = :{$paramname}";
        $params[$paramname] = $value;
    }

    /**
     * Add integer filter when a column exists.
     *
     * @param string[] $where Where clauses.
     * @param array<string, mixed> $params SQL params.
     * @param array<string, object> $columns Columns.
     * @param string $alias SQL alias.
     * @param string[] $candidates Candidate fields.
     * @param string $paramname Parameter name.
     * @param int $value Value.
     * @return void
     */
    private static function add_int_filter(
        array &$where,
        array &$params,
        array $columns,
        string $alias,
        array $candidates,
        string $paramname,
        int $value
    ): void {
        if ($value <= 0) {
            return;
        }

        $field = self::first_column($columns, $candidates);
        if ($field === null) {
            return;
        }

        $where[] = "{$alias}.{$field} = :{$paramname}";
        $params[$paramname] = $value;
    }

    /**
     * Add timestamp filter when a column exists.
     *
     * @param string[] $where Where clauses.
     * @param array<string, mixed> $params SQL params.
     * @param array<string, object> $columns Columns.
     * @param string $alias SQL alias.
     * @param string $field Field.
     * @param string $paramname Parameter name.
     * @param string $operator Operator.
     * @param int $value Value.
     * @return void
     */
    private static function add_time_filter(
        array &$where,
        array &$params,
        array $columns,
        string $alias,
        string $field,
        string $paramname,
        string $operator,
        int $value
    ): void {
        if ($value <= 0 || !self::column_exists($columns, $field)) {
            return;
        }

        $where[] = "{$alias}.{$field} {$operator} :{$paramname}";
        $params[$paramname] = $value;
    }

    /**
     * Return SQL LIKE expression.
     *
     * @param string $field Field.
     * @param string $param Placeholder.
     * @return string
     */
    private static function sql_like(string $field, string $param): string {
        global $DB;
        return $DB->sql_like($field, $param, false, false);
    }

    /**
     * Return whether a table exists.
     *
     * @param string $tablename Table name without braces.
     * @return bool
     */
    private static function table_exists(string $tablename): bool {
        global $DB;
        return $DB->get_manager()->table_exists(new \xmldb_table($tablename));
    }

    /**
     * Return DB columns.
     *
     * @param string $tablename Table name.
     * @return array<string, object>
     */
    private static function get_columns(string $tablename): array {
        global $DB;
        return $DB->get_columns($tablename);
    }

    /**
     * Return whether column exists.
     *
     * @param array<string, object> $columns Columns.
     * @param string $field Field name.
     * @return bool
     */
    private static function column_exists(array $columns, string $field): bool {
        return array_key_exists($field, $columns);
    }

    /**
     * Return first matching column.
     *
     * @param array<string, object> $columns Columns.
     * @param string[] $candidates Candidate field names.
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
     * Return first existing field value.
     *
     * @param stdClass $record Record.
     * @param string[] $fields Candidate fields.
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
     * Empty response helper.
     *
     * @param int $page Page.
     * @param int $perpage Per page.
     * @param array<string, bool> $permissions Permissions.
     * @param array<string, mixed>|null $warning Warning.
     * @return array<string, mixed>
     */
    private static function empty_response(
        int $page,
        int $perpage,
        array $permissions,
        ?array $warning = null
    ): array {
        return [
            'collections' => [],
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
     * Warning helper.
     *
     * @param string $item Item.
     * @param int $itemid Item id.
     * @param string $warningcode Warning code.
     * @param string $message Message.
     * @return array<string, mixed>
     */
    private static function warning(string $item, int $itemid, string $warningcode, string $message): array {
        return [
            'item' => $item,
            'itemid' => $itemid,
            'warningcode' => clean_param($warningcode, PARAM_ALPHANUMEXT),
            'message' => $message,
        ];
    }
}
