<?php
// This file is part of Moodle - https://moodle.org/
//
// Moodle is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// any later version.

/**
 * Return a filtered, permission-aware media library list.
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
use moodle_exception;
use stdClass;

/**
 * Return a filtered, permission-aware media library list.
 *
 * This is a read service. It resolves Moodle context, validates parameters,
 * checks media view capability, applies visibility restrictions, redacts
 * unsafe fields, and returns a stable response for AJAX/External Services.
 *
 * Target service name:
 *
 * ```text
 * mod_uckkarchive_get_media
 * ```
 */
class get_media extends external_api {
    /** Media table. */
    private const MEDIA_TABLE = 'uckkarchive_media';

    /** Media collection membership table. */
    private const COLLECTION_ITEM_TABLE = 'uckkarchive_media_collection_item';

    /** Media tag table. */
    private const MEDIA_TAG_TABLE = 'uckkarchive_media_tag';

    /** Content marker table. */
    private const CONTENT_MARKER_TABLE = 'uckkarchive_content_marker';

    /** Default pagination size. */
    private const DEFAULT_PERPAGE = 20;

    /** Maximum pagination size. */
    private const MAX_PERPAGE = 100;

    /**
     * Load the Moodle page context for this activity.
     *
     * @param int $cmid Course module id.
     * @return array{0:stdClass,1:stdClass,2:stdClass,3:context_module}
     */
    protected static function load_page(int $cmid): array {
        [$course, $cm, $archive, $context] = \uckkarchive_require_page($cmid, 0);
        return [$course, $cm, $archive, $context];
    }

    /**
     * Define service parameters.
     *
     * @return external_function_parameters
     */
    public static function execute_parameters(): external_function_parameters {
        return new external_function_parameters([
            'cmid' => new external_value(PARAM_INT, 'Course module id'),
            'filters' => new external_single_structure([
                'mediatype' => new external_value(PARAM_ALPHANUMEXT, 'Media type filter', VALUE_DEFAULT, ''),
                'status' => new external_value(PARAM_ALPHANUMEXT, 'Media lifecycle status filter', VALUE_DEFAULT, ''),
                'visibility' => new external_value(PARAM_ALPHANUMEXT, 'Visibility filter', VALUE_DEFAULT, ''),
                'source' => new external_value(PARAM_ALPHANUMEXT, 'Media source filter', VALUE_DEFAULT, ''),
                'ownerid' => new external_value(PARAM_INT, 'Owner user id filter', VALUE_DEFAULT, 0),
                'tag' => new external_value(PARAM_TEXT, 'Media tag filter', VALUE_DEFAULT, ''),
                'contenttag' => new external_value(PARAM_ALPHANUMEXT, 'Content advisory tag filter', VALUE_DEFAULT, ''),
                'collectionid' => new external_value(PARAM_INT, 'Media collection id filter', VALUE_DEFAULT, 0),
                'hasadvisory' => new external_value(PARAM_BOOL, 'Require media with content advisory markers', VALUE_DEFAULT, false),
                'hasrestricted' => new external_value(PARAM_BOOL, 'Require restricted media', VALUE_DEFAULT, false),
                'hastranscript' => new external_value(PARAM_BOOL, 'Require media with transcript files', VALUE_DEFAULT, false),
                'hascaption' => new external_value(PARAM_BOOL, 'Require media with caption files', VALUE_DEFAULT, false),
                'hasthumbnail' => new external_value(PARAM_BOOL, 'Require media with thumbnail files', VALUE_DEFAULT, false),
                'createdfrom' => new external_value(PARAM_INT, 'Created from unix timestamp', VALUE_DEFAULT, 0),
                'createdto' => new external_value(PARAM_INT, 'Created to unix timestamp', VALUE_DEFAULT, 0),
                'modifiedfrom' => new external_value(PARAM_INT, 'Modified from unix timestamp', VALUE_DEFAULT, 0),
                'modifiedto' => new external_value(PARAM_INT, 'Modified to unix timestamp', VALUE_DEFAULT, 0),
            ], 'Media filters', VALUE_DEFAULT, []),
            'page' => new external_value(PARAM_INT, 'Zero-based page number', VALUE_DEFAULT, 0),
            'perpage' => new external_value(PARAM_INT, 'Items per page', VALUE_DEFAULT, self::DEFAULT_PERPAGE),
            'sort' => new external_value(PARAM_ALPHANUMEXT, 'Sort field', VALUE_DEFAULT, 'timemodified'),
            'direction' => new external_value(PARAM_ALPHA, 'Sort direction: asc or desc', VALUE_DEFAULT, 'desc'),
            'include' => new external_multiple_structure(
                new external_value(PARAM_ALPHANUMEXT, 'Include value'),
                'Optional include values: files, permissions, counts',
                VALUE_DEFAULT,
                []
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
     * @param string[] $include Include values.
     * @return array<string, mixed>
     */
    public static function execute(
        int $cmid,
        array $filters = [],
        int $page = 0,
        int $perpage = self::DEFAULT_PERPAGE,
        string $sort = 'timemodified',
        string $direction = 'desc',
        array $include = []
    ): array {
        global $DB;

        $params = self::validate_parameters(self::execute_parameters(), [
            'cmid' => $cmid,
            'filters' => $filters,
            'page' => $page,
            'perpage' => $perpage,
            'sort' => $sort,
            'direction' => $direction,
            'include' => $include,
        ]);

        [$course, $cm, $archive, $context] = self::load_page((int)$params['cmid']);
        self::validate_context($context);

        require_capability('mod/uckkarchive:viewmedia', $context);

        $warnings = [];
        $page = max(0, (int)$params['page']);
        $perpage = min(self::MAX_PERPAGE, max(1, (int)$params['perpage']));
        $include = self::normalise_include((array)$params['include']);
        $sort = self::normalise_sort((string)$params['sort']);
        $direction = self::normalise_direction((string)$params['direction']);
        $filters = self::normalise_filters((array)$params['filters']);

        if (!self::table_exists(self::MEDIA_TABLE)) {
            return self::empty_response(
                $page,
                $perpage,
                self::get_permissions($context),
                self::warning('media', 0, 'mediatablenotfound', 'Media table is not installed yet.')
            );
        }

        $columns = self::get_columns(self::MEDIA_TABLE);
        $query = self::build_query((int)$archive->id, $columns, $filters, $sort, $direction);

        $records = $DB->get_records_sql($query['sql'], $query['params']);

        $visible = [];

        foreach ($records as $record) {
            if (!self::can_view_record($record, $context)) {
                continue;
            }

            $visible[] = self::export_media_record($record, $context, $include);
        }

        $total = count($visible);
        $media = array_slice($visible, $page * $perpage, $perpage);

        return [
            'media' => $media,
            'pagination' => [
                'page' => $page,
                'perpage' => $perpage,
                'total' => $total,
                'returned' => count($media),
                'hasmore' => (($page + 1) * $perpage) < $total,
            ],
            'permissions' => self::get_permissions($context),
            'warnings' => $warnings,
        ];
    }

    /**
     * Return external response structure.
     *
     * @return external_single_structure
     */
    public static function execute_returns(): external_single_structure {
        return new external_single_structure([
            'media' => new external_multiple_structure(
                self::media_structure(),
                'Permission-filtered media records'
            ),
            'pagination' => new external_single_structure([
                'page' => new external_value(PARAM_INT, 'Current zero-based page'),
                'perpage' => new external_value(PARAM_INT, 'Items per page'),
                'total' => new external_value(PARAM_INT, 'Total records before permission post-filter'),
                'returned' => new external_value(PARAM_INT, 'Returned records after permission post-filter'),
                'hasmore' => new external_value(PARAM_BOOL, 'Whether more records exist'),
            ]),
            'permissions' => self::permissions_structure(),
            'warnings' => self::warnings_structure(),
        ]);
    }

    /**
     * Return media response structure.
     *
     * @return external_single_structure
     */
    protected static function media_structure(): external_single_structure {
        return new external_single_structure([
            'id' => new external_value(PARAM_INT, 'Media id'),
            'uuid' => new external_value(PARAM_TEXT, 'Media UUID'),
            'archiveid' => new external_value(PARAM_INT, 'Archive instance id'),
            'title' => new external_value(PARAM_TEXT, 'Media title'),
            'summary' => new external_value(PARAM_RAW, 'Permission-filtered summary'),
            'description' => new external_value(PARAM_RAW, 'Permission-filtered description'),
            'mediatype' => new external_value(PARAM_ALPHANUMEXT, 'Media type'),
            'mimetype' => new external_value(PARAM_TEXT, 'MIME type'),
            'status' => new external_value(PARAM_ALPHANUMEXT, 'Lifecycle status'),
            'visibility' => new external_value(PARAM_ALPHANUMEXT, 'Visibility'),
            'source' => new external_value(PARAM_ALPHANUMEXT, 'Source type'),
            'ownerid' => new external_value(PARAM_INT, 'Owner user id'),
            'createdby' => new external_value(PARAM_INT, 'Creator user id'),
            'modifiedby' => new external_value(PARAM_INT, 'Modifier user id'),
            'timecreated' => new external_value(PARAM_INT, 'Creation time'),
            'timemodified' => new external_value(PARAM_INT, 'Modified time'),
            'isrestricted' => new external_value(PARAM_BOOL, 'Restricted media'),
            'isculturalrestricted' => new external_value(PARAM_BOOL, 'Culturally restricted media'),
            'hasadvisory' => new external_value(PARAM_BOOL, 'Has content advisory markers'),
            'hasthumbnail' => new external_value(PARAM_BOOL, 'Has thumbnail file'),
            'hascaption' => new external_value(PARAM_BOOL, 'Has caption file'),
            'hastranscript' => new external_value(PARAM_BOOL, 'Has transcript file'),
            'thumbnailurl' => new external_value(PARAM_RAW, 'Thumbnail URL', VALUE_OPTIONAL),
            'previewurl' => new external_value(PARAM_RAW, 'Preview URL', VALUE_OPTIONAL),
            'files' => new external_multiple_structure(
                new external_single_structure([
                    'filearea' => new external_value(PARAM_ALPHANUMEXT, 'File area'),
                    'filename' => new external_value(PARAM_FILE, 'Filename'),
                    'filesize' => new external_value(PARAM_INT, 'File size'),
                    'mimetype' => new external_value(PARAM_TEXT, 'MIME type'),
                    'url' => new external_value(PARAM_RAW, 'Pluginfile URL'),
                ]),
                'Included file metadata',
                VALUE_OPTIONAL
            ),
        ]);
    }

    /**
     * Return permissions response structure.
     *
     * @return external_single_structure
     */
    protected static function permissions_structure(): external_single_structure {
        return new external_single_structure([
            'viewmedia' => new external_value(PARAM_BOOL, 'Can view media'),
            'addmedia' => new external_value(PARAM_BOOL, 'Can add media'),
            'editmedia' => new external_value(PARAM_BOOL, 'Can edit media'),
            'deletemedia' => new external_value(PARAM_BOOL, 'Can delete media'),
            'downloadmedia' => new external_value(PARAM_BOOL, 'Can download media'),
            'versionmedia' => new external_value(PARAM_BOOL, 'Can version media'),
            'managemediacollections' => new external_value(PARAM_BOOL, 'Can manage media collections'),
            'exportmedia' => new external_value(PARAM_BOOL, 'Can export media'),
            'viewrestrictedmedia' => new external_value(PARAM_BOOL, 'Can view restricted media'),
            'viewadvisories' => new external_value(PARAM_BOOL, 'Can view content advisories'),
            'manageadvisories' => new external_value(PARAM_BOOL, 'Can manage content advisories'),
            'viewculturallyrestricted' => new external_value(PARAM_BOOL, 'Can view culturally restricted material'),
        ]);
    }

    /**
     * Return warnings response structure.
     *
     * @return external_multiple_structure
     */
    protected static function warnings_structure(): external_multiple_structure {
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
     * Build the media SQL query.
     *
     * @param int $archiveid Archive id.
     * @param array<string, object> $columns Media table columns.
     * @param array<string, mixed> $filters Filters.
     * @param string $sort Sort field.
     * @param string $direction Sort direction.
     * @return array{sql:string,countsql:string,params:array<string,mixed>}
     */
    protected static function build_query(
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
            $where[] = "m.{$archivefield} = :archiveid";
            $params['archiveid'] = $archiveid;
        }

        self::add_string_filter($where, $params, $columns, 'm', ['mediatype', 'type'], 'mediatype', $filters['mediatype']);
        self::add_string_filter($where, $params, $columns, 'm', ['status'], 'status', $filters['status']);
        self::add_string_filter($where, $params, $columns, 'm', ['visibility'], 'visibility', $filters['visibility']);
        self::add_string_filter($where, $params, $columns, 'm', ['source', 'sourcetype'], 'source', $filters['source']);
        self::add_int_filter($where, $params, $columns, 'm', ['ownerid', 'userid', 'createdby'], 'ownerid', (int)$filters['ownerid']);
        self::add_time_filter($where, $params, $columns, 'm', 'timecreated', 'createdfrom', '>=', (int)$filters['createdfrom']);
        self::add_time_filter($where, $params, $columns, 'm', 'timecreated', 'createdto', '<=', (int)$filters['createdto']);
        self::add_time_filter($where, $params, $columns, 'm', 'timemodified', 'modifiedfrom', '>=', (int)$filters['modifiedfrom']);
        self::add_time_filter($where, $params, $columns, 'm', 'timemodified', 'modifiedto', '<=', (int)$filters['modifiedto']);

        if (!empty($filters['hasrestricted']) && self::column_exists($columns, 'visibility')) {
            [$sql, $visibilityparams] = self::restricted_visibility_sql('m.visibility', 'rv');
            $where[] = $sql;
            $params += $visibilityparams;
        }

        if (!empty($filters['collectionid']) && self::table_exists(self::COLLECTION_ITEM_TABLE)) {
            $collectioncolumns = self::get_columns(self::COLLECTION_ITEM_TABLE);
            $mediafield = self::first_column($collectioncolumns, ['mediaid', 'itemid']);
            $collectionfield = self::first_column($collectioncolumns, ['collectionid', 'mediacollectionid']);

            if ($mediafield !== null && $collectionfield !== null) {
                $joins[] = "JOIN {" . self::COLLECTION_ITEM_TABLE . "} mci ON mci.{$mediafield} = m.id";
                $where[] = "mci.{$collectionfield} = :collectionid";
                $params['collectionid'] = (int)$filters['collectionid'];
            }
        }

        if ($filters['tag'] !== '' && self::table_exists(self::MEDIA_TAG_TABLE)) {
            $tagcolumns = self::get_columns(self::MEDIA_TAG_TABLE);
            $mediafield = self::first_column($tagcolumns, ['mediaid', 'itemid']);
            $tagfield = self::first_column($tagcolumns, ['tag', 'tagkey', 'name', 'rawname']);

            if ($mediafield !== null && $tagfield !== null) {
                $joins[] = "JOIN {" . self::MEDIA_TAG_TABLE . "} mt ON mt.{$mediafield} = m.id";
                $where[] = $DBLIKE = self::sql_like("mt.{$tagfield}", ':tag');
                $params['tag'] = '%' . $filters['tag'] . '%';
            }
        }

        if (($filters['contenttag'] !== '' || !empty($filters['hasadvisory'])) &&
                self::table_exists(self::CONTENT_MARKER_TABLE)) {
            $markercolumns = self::get_columns(self::CONTENT_MARKER_TABLE);
            $mediafield = self::first_column($markercolumns, ['mediaid']);
            $tagfield = self::first_column($markercolumns, ['tag', 'tagkey', 'contenttag', 'advisorytag']);

            if ($mediafield !== null) {
                $joins[] = "JOIN {" . self::CONTENT_MARKER_TABLE . "} cmk ON cmk.{$mediafield} = m.id";

                if ($filters['contenttag'] !== '' && $tagfield !== null) {
                    $where[] = "cmk.{$tagfield} = :contenttag";
                    $params['contenttag'] = $filters['contenttag'];
                }
            }
        }

        $sortfield = self::first_column($columns, [$sort]);
        if ($sortfield === null) {
            $sortfield = self::first_column($columns, ['timemodified', 'timecreated', 'id']) ?? 'id';
        }

        $joinsql = implode("\n", array_unique($joins));
        $wheresql = implode(' AND ', $where);

        $sql = "SELECT DISTINCT m.*
                  FROM {" . self::MEDIA_TABLE . "} m
                       {$joinsql}
                 WHERE {$wheresql}
              ORDER BY m.{$sortfield} {$direction}, m.id {$direction}";

        $countsql = "SELECT COUNT(DISTINCT m.id)
                       FROM {" . self::MEDIA_TABLE . "} m
                            {$joinsql}
                      WHERE {$wheresql}";

        return [
            'sql' => $sql,
            'countsql' => $countsql,
            'params' => $params,
        ];
    }

    /**
     * Export one media record.
     *
     * @param stdClass $record Media record.
     * @param context_module $context Module context.
     * @param string[] $include Include values.
     * @return array<string, mixed>
     */
    protected static function export_media_record(stdClass $record, context_module $context, array $include): array {
        $isrestricted = self::is_restricted_record($record);
        $isculturalrestricted = self::is_culturally_restricted_record($record);
        $canseefullrestricted = self::can_view_restricted($context, $record);

        $title = self::field($record, ['title', 'name'], get_string('media', 'uckkarchive'));
        $summary = self::field($record, ['summary', 'description', 'publicsummary'], '');
        $description = self::field($record, ['description', 'body', 'notes'], '');

        if ($isrestricted && !$canseefullrestricted) {
            $summary = '';
            $description = '';
        }

        $media = [
            'id' => (int)$record->id,
            'uuid' => (string)self::field($record, ['uuid'], ''),
            'archiveid' => (int)self::field($record, ['archiveid', 'uckkarchiveid'], 0),
            'title' => format_string((string)$title),
            'summary' => format_text((string)$summary, FORMAT_HTML, ['para' => false]),
            'description' => format_text((string)$description, FORMAT_HTML, ['para' => false]),
            'mediatype' => (string)self::field($record, ['mediatype', 'type'], ''),
            'mimetype' => (string)self::field($record, ['mimetype', 'mime'], ''),
            'status' => (string)self::field($record, ['status'], 'draft'),
            'visibility' => (string)self::field($record, ['visibility'], 'restricted'),
            'source' => (string)self::field($record, ['source', 'sourcetype'], ''),
            'ownerid' => (int)self::field($record, ['ownerid', 'userid'], 0),
            'createdby' => (int)self::field($record, ['createdby', 'userid', 'ownerid'], 0),
            'modifiedby' => (int)self::field($record, ['modifiedby'], 0),
            'timecreated' => (int)self::field($record, ['timecreated'], 0),
            'timemodified' => (int)self::field($record, ['timemodified'], 0),
            'isrestricted' => $isrestricted,
            'isculturalrestricted' => $isculturalrestricted,
            'hasadvisory' => self::has_advisory((int)$record->id),
            'hasthumbnail' => self::has_media_file($context, 'media_thumbnail', (int)$record->id),
            'hascaption' => self::has_media_file($context, 'media_caption', (int)$record->id),
            'hastranscript' => self::has_media_file($context, 'media_transcript', (int)$record->id),
        ];

        $thumbnailurl = self::get_first_media_file_url($context, 'media_thumbnail', (int)$record->id, false);
        if ($thumbnailurl !== null) {
            $media['thumbnailurl'] = $thumbnailurl;
        }

        $previewurl = self::get_first_media_file_url($context, 'media_preview', (int)$record->id, false);
        if ($previewurl !== null) {
            $media['previewurl'] = $previewurl;
        }

        if (in_array('files', $include, true) && has_capability('mod/uckkarchive:downloadmedia', $context)) {
            $media['files'] = self::get_file_metadata($context, (int)$record->id);
        }

        return $media;
    }

    /**
     * Return whether current user may see a record.
     *
     * @param stdClass $record Media record.
     * @param context_module $context Module context.
     * @return bool
     */
    protected static function can_view_record(stdClass $record, context_module $context): bool {
        global $USER;

        if ((string)self::field($record, ['status'], '') === 'deleted_soft') {
            return has_capability('mod/uckkarchive:deletemedia', $context);
        }

        $visibility = (string)self::field($record, ['visibility'], 'restricted');

        if ($visibility === 'private') {
            $ownerid = (int)self::field($record, ['ownerid', 'userid', 'createdby'], 0);
            if ($ownerid > 0 && $ownerid === (int)$USER->id) {
                return true;
            }

            return has_capability('mod/uckkarchive:editmedia', $context) ||
                has_capability('mod/uckkarchive:viewrestrictedmedia', $context);
        }

        if (self::is_restricted_record($record)) {
            return self::can_view_restricted($context, $record);
        }

        return has_capability('mod/uckkarchive:viewmedia', $context);
    }

    /**
     * Return whether the current user may see restricted fields for a record.
     *
     * @param context_module $context Module context.
     * @param stdClass $record Media record.
     * @return bool
     */
    protected static function can_view_restricted(context_module $context, stdClass $record): bool {
        if (has_capability('mod/uckkarchive:viewrestrictedmedia', $context) ||
                has_capability('mod/uckkarchive:viewrestricted', $context)) {
            return true;
        }

        if (self::is_culturally_restricted_record($record)) {
            return has_capability('mod/uckkarchive:viewculturallyrestricted', $context);
        }

        return false;
    }

    /**
     * Return whether a record is restricted.
     *
     * @param stdClass $record Media record.
     * @return bool
     */
    protected static function is_restricted_record(stdClass $record): bool {
        $status = (string)self::field($record, ['status'], '');
        $visibility = (string)self::field($record, ['visibility'], '');

        return in_array($status, ['restricted'], true) ||
            in_array($visibility, ['restricted', 'restricted_integrity', 'restricted_cultural'], true) ||
            !empty($record->restricted);
    }

    /**
     * Return whether a record is culturally restricted.
     *
     * @param stdClass $record Media record.
     * @return bool
     */
    protected static function is_culturally_restricted_record(stdClass $record): bool {
        $visibility = (string)self::field($record, ['visibility'], '');

        return $visibility === 'restricted_cultural' || !empty($record->culturalprotocol);
    }

    /**
     * Return permissions summary.
     *
     * @param context_module $context Module context.
     * @return array<string, bool>
     */
    protected static function get_permissions(context_module $context): array {
        return [
            'viewmedia' => has_capability('mod/uckkarchive:viewmedia', $context),
            'addmedia' => has_capability('mod/uckkarchive:addmedia', $context),
            'editmedia' => has_capability('mod/uckkarchive:editmedia', $context),
            'deletemedia' => has_capability('mod/uckkarchive:deletemedia', $context),
            'downloadmedia' => has_capability('mod/uckkarchive:downloadmedia', $context),
            'versionmedia' => has_capability('mod/uckkarchive:versionmedia', $context),
            'managemediacollections' => has_capability('mod/uckkarchive:managemediacollections', $context),
            'exportmedia' => has_capability('mod/uckkarchive:exportmedia', $context),
            'viewrestrictedmedia' => has_capability('mod/uckkarchive:viewrestrictedmedia', $context),
            'viewadvisories' => has_capability('mod/uckkarchive:viewadvisories', $context),
            'manageadvisories' => has_capability('mod/uckkarchive:manageadvisories', $context),
            'viewculturallyrestricted' => has_capability('mod/uckkarchive:viewculturallyrestricted', $context),
        ];
    }

    /**
     * Return an empty response.
     *
     * @param int $page Page.
     * @param int $perpage Per page.
     * @param array<string, bool> $permissions Permissions.
     * @param array<string, mixed>|null $warning Optional warning.
     * @return array<string, mixed>
     */
    protected static function empty_response(int $page, int $perpage, array $permissions, ?array $warning = null): array {
        return [
            'media' => [],
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
     * Return warning payload.
     *
     * @param string $item Warning item.
     * @param int $itemid Item id.
     * @param string $code Warning code.
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
     * Normalize filters.
     *
     * @param array<string, mixed> $filters Raw filters.
     * @return array<string, mixed>
     */
    protected static function normalise_filters(array $filters): array {
        $defaults = [
            'mediatype' => '',
            'status' => '',
            'visibility' => '',
            'source' => '',
            'ownerid' => 0,
            'tag' => '',
            'contenttag' => '',
            'collectionid' => 0,
            'hasadvisory' => false,
            'hasrestricted' => false,
            'hastranscript' => false,
            'hascaption' => false,
            'hasthumbnail' => false,
            'createdfrom' => 0,
            'createdto' => 0,
            'modifiedfrom' => 0,
            'modifiedto' => 0,
        ];

        $filters = array_merge($defaults, $filters);

        foreach (['mediatype', 'status', 'visibility', 'source', 'contenttag'] as $key) {
            $filters[$key] = clean_param((string)$filters[$key], PARAM_ALPHANUMEXT);
        }

        $filters['tag'] = clean_param((string)$filters['tag'], PARAM_TEXT);

        foreach (['ownerid', 'collectionid', 'createdfrom', 'createdto', 'modifiedfrom', 'modifiedto'] as $key) {
            $filters[$key] = max(0, (int)$filters[$key]);
        }

        foreach (['hasadvisory', 'hasrestricted', 'hastranscript', 'hascaption', 'hasthumbnail'] as $key) {
            $filters[$key] = !empty($filters[$key]);
        }

        return $filters;
    }

    /**
     * Normalize include values.
     *
     * @param string[] $include Include values.
     * @return string[]
     */
    protected static function normalise_include(array $include): array {
        $allowed = ['files', 'permissions', 'counts'];
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
     * Normalize sort.
     *
     * @param string $sort Sort.
     * @return string
     */
    protected static function normalise_sort(string $sort): string {
        $sort = clean_param($sort, PARAM_ALPHANUMEXT);
        $allowed = ['title', 'mediatype', 'status', 'visibility', 'timecreated', 'timemodified'];

        return in_array($sort, $allowed, true) ? $sort : 'timemodified';
    }

    /**
     * Normalize direction.
     *
     * @param string $direction Direction.
     * @return string
     */
    protected static function normalise_direction(string $direction): string {
        $direction = strtolower(clean_param($direction, PARAM_ALPHA));

        return $direction === 'asc' ? 'ASC' : 'DESC';
    }

    /**
     * Add string filter when column exists.
     *
     * @param string[] $where Where clauses.
     * @param array<string, mixed> $params Params.
     * @param array<string, object> $columns Columns.
     * @param string $alias SQL alias.
     * @param string[] $candidates Candidate fields.
     * @param string $paramname Parameter name.
     * @param string $value Value.
     * @return void
     */
    protected static function add_string_filter(
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
     * Add integer filter when column exists.
     *
     * @param string[] $where Where clauses.
     * @param array<string, mixed> $params Params.
     * @param array<string, object> $columns Columns.
     * @param string $alias SQL alias.
     * @param string[] $candidates Candidate fields.
     * @param string $paramname Parameter name.
     * @param int $value Value.
     * @return void
     */
    protected static function add_int_filter(
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
     * Add time filter when column exists.
     *
     * @param string[] $where Where clauses.
     * @param array<string, mixed> $params Params.
     * @param array<string, object> $columns Columns.
     * @param string $alias SQL alias.
     * @param string $field Field.
     * @param string $paramname Parameter name.
     * @param string $operator Operator.
     * @param int $value Value.
     * @return void
     */
    protected static function add_time_filter(
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
     * Return SQL LIKE expression using Moodle DB API.
     *
     * @param string $field Field expression.
     * @param string $param Parameter placeholder.
     * @return string
     */
    protected static function sql_like(string $field, string $param): string {
        global $DB;

        return $DB->sql_like($field, $param, false, false);
    }

    /**
     * Return restricted visibility SQL.
     *
     * @param string $field Field expression.
     * @param string $prefix Param prefix.
     * @return array{0:string,1:array<string,string>}
     */
    protected static function restricted_visibility_sql(string $field, string $prefix): array {
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
     * Return whether a table exists.
     *
     * @param string $tablename Table name without braces.
     * @return bool
     */
    protected static function table_exists(string $tablename): bool {
        global $DB;

        return $DB->get_manager()->table_exists(new \xmldb_table($tablename));
    }

    /**
     * Return DB columns for a table.
     *
     * @param string $tablename Table name.
     * @return array<string, object>
     */
    protected static function get_columns(string $tablename): array {
        global $DB;

        return $DB->get_columns($tablename);
    }

    /**
     * Return whether a column exists in the supplied column array.
     *
     * @param array<string, object> $columns Columns.
     * @param string $field Field name.
     * @return bool
     */
    protected static function column_exists(array $columns, string $field): bool {
        return array_key_exists($field, $columns);
    }

    /**
     * Return first existing column name from candidates.
     *
     * @param array<string, object> $columns Columns.
     * @param string[] $candidates Candidate field names.
     * @return string|null
     */
    protected static function first_column(array $columns, array $candidates): ?string {
        foreach ($candidates as $candidate) {
            if (self::column_exists($columns, $candidate)) {
                return $candidate;
            }
        }

        return null;
    }

    /**
     * Return field value from record using candidates.
     *
     * @param stdClass $record Record.
     * @param string[] $fields Candidate field names.
     * @param mixed $default Default.
     * @return mixed
     */
    protected static function field(stdClass $record, array $fields, mixed $default = null): mixed {
        foreach ($fields as $field) {
            if (property_exists($record, $field) && $record->{$field} !== null && $record->{$field} !== '') {
                return $record->{$field};
            }
        }

        return $default;
    }

    /**
     * Return whether media has advisory marker records.
     *
     * @param int $mediaid Media id.
     * @return bool
     */
    protected static function has_advisory(int $mediaid): bool {
        global $DB;

        if ($mediaid <= 0 || !self::table_exists(self::CONTENT_MARKER_TABLE)) {
            return false;
        }

        $columns = self::get_columns(self::CONTENT_MARKER_TABLE);
        $mediafield = self::first_column($columns, ['mediaid']);

        if ($mediafield === null) {
            return false;
        }

        return $DB->record_exists(self::CONTENT_MARKER_TABLE, [$mediafield => $mediaid]);
    }

    /**
     * Return whether media has a file in a file area.
     *
     * @param context_module $context Module context.
     * @param string $filearea File area.
     * @param int $mediaid Media id.
     * @return bool
     */
    protected static function has_media_file(context_module $context, string $filearea, int $mediaid): bool {
        if (class_exists('\\mod_uckkarchive\\local\\media_file')) {
            return \mod_uckkarchive\local\media_file::has_files($context, $filearea, $mediaid);
        }

        $fs = get_file_storage();
        $files = $fs->get_area_files(
            (int)$context->id,
            'mod_uckkarchive',
            $filearea,
            $mediaid,
            'filename',
            false
        );

        foreach ($files as $file) {
            if (!$file->is_directory()) {
                return true;
            }
        }

        return false;
    }

    /**
     * Return first media file URL if present.
     *
     * @param context_module $context Module context.
     * @param string $filearea File area.
     * @param int $mediaid Media id.
     * @param bool $forcedownload Force download.
     * @return string|null
     */
    protected static function get_first_media_file_url(
        context_module $context,
        string $filearea,
        int $mediaid,
        bool $forcedownload
    ): ?string {
        if (class_exists('\\mod_uckkarchive\\local\\media_file')) {
            $url = \mod_uckkarchive\local\media_file::get_first_file_url($context, $filearea, $mediaid, $forcedownload);

            return $url ? $url->out(false) : null;
        }

        $fs = get_file_storage();
        $files = $fs->get_area_files(
            (int)$context->id,
            'mod_uckkarchive',
            $filearea,
            $mediaid,
            'filename',
            false
        );

        foreach ($files as $file) {
            if (!$file->is_directory()) {
                return \moodle_url::make_pluginfile_url(
                    $file->get_contextid(),
                    $file->get_component(),
                    $file->get_filearea(),
                    $file->get_itemid(),
                    $file->get_filepath(),
                    $file->get_filename(),
                    $forcedownload
                )->out(false);
            }
        }

        return null;
    }

    /**
     * Return optional file metadata.
     *
     * @param context_module $context Module context.
     * @param int $mediaid Media id.
     * @return array<int, array<string, mixed>>
     */
    protected static function get_file_metadata(context_module $context, int $mediaid): array {
        $metadata = [];
        $areas = [
            'media_original',
            'media_preview',
            'media_thumbnail',
            'media_derivative',
            'media_caption',
            'media_transcript',
            'media_attachment',
        ];

        foreach ($areas as $area) {
            $fs = get_file_storage();
            $files = $fs->get_area_files((int)$context->id, 'mod_uckkarchive', $area, $mediaid, 'filename', false);

            foreach ($files as $file) {
                if ($file->is_directory()) {
                    continue;
                }

                $metadata[] = [
                    'filearea' => $area,
                    'filename' => $file->get_filename(),
                    'filesize' => $file->get_filesize(),
                    'mimetype' => $file->get_mimetype(),
                    'url' => \moodle_url::make_pluginfile_url(
                        $file->get_contextid(),
                        $file->get_component(),
                        $file->get_filearea(),
                        $file->get_itemid(),
                        $file->get_filepath(),
                        $file->get_filename(),
                        true
                    )->out(false),
                ];
            }
        }

        return $metadata;
    }
}
