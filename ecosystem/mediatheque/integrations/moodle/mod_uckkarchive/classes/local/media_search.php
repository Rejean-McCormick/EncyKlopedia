<?php
// This file is part of Moodle - https://moodle.org/
//
// Moodle is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// any later version.

namespace mod_uckkarchive\local;

defined('MOODLE_INTERNAL') || die();

use context_module;
use stdClass;

/**
 * Permission-aware media search for mod_uckkarchive.
 *
 * This class builds server-side filtered media searches for the self-contained
 * archive/media/content-advisory system.
 *
 * It searches media metadata and can filter by:
 * - title/description text;
 * - media type;
 * - MIME type;
 * - status;
 * - visibility;
 * - audience suitability;
 * - media source;
 * - media tags;
 * - media collections;
 * - content advisory tags;
 * - external work references.
 *
 * Security rule:
 * Search is never the security boundary by itself. Query filters prevent common
 * leaks, and callers must still use media_policy before serving downloads,
 * previews, exports, or full metadata.
 *
 * @package    mod_uckkarchive
 * @copyright  2026 Univers-Cité King Klown
 * @license    https://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later
 */
final class media_search {
    /** Default page size. */
    public const DEFAULT_LIMIT = 50;

    /** Maximum page size. */
    public const MAX_LIMIT = 200;

    /** Sort by newest media first. */
    public const SORT_NEWEST = 'newest';

    /** Sort by oldest media first. */
    public const SORT_OLDEST = 'oldest';

    /** Sort by title ascending. */
    public const SORT_TITLE_ASC = 'title_asc';

    /** Sort by title descending. */
    public const SORT_TITLE_DESC = 'title_desc';

    /** Sort by modified time descending. */
    public const SORT_MODIFIED = 'modified';

    /** Canonical media table. */
    private const TABLE_MEDIA = 'uckkarchive_media';

    /** Media source table. */
    private const TABLE_MEDIA_SOURCE = 'uckkarchive_media_source';

    /** Media tag table. */
    private const TABLE_MEDIA_TAG = 'uckkarchive_media_tag';

    /** Media collection membership table. */
    private const TABLE_COLLECTION_ITEM = 'uckkarchive_media_collection_item';

    /** Media relation table. */
    private const TABLE_RELATION = 'uckkarchive_media_relation';

    /** Content marker table. */
    private const TABLE_CONTENT_MARKER = 'uckkarchive_content_marker';

    /** Content tag table. */
    private const TABLE_CONTENT_TAG = 'uckkarchive_content_tag';

    /**
     * Search media records.
     *
     * Supported filters:
     * - q: free text
     * - mediatype: string or array
     * - mimetype: string or array
     * - status: string or array
     * - visibility: string or array
     * - audiencesuitability: string or array
     * - sourcetype: string or array
     * - sourceownership: string or array
     * - tag: string or array
     * - contenttag: string or array
     * - collectionid: int
     * - externalworkid: int
     * - include_restricted: bool
     * - include_deleted: bool
     * - sort: one of SORT_* constants
     *
     * @param int $archiveid Archive instance id.
     * @param context_module $context Module context.
     * @param array $filters Search filters.
     * @param int $limit Page size.
     * @param int $offset Offset.
     * @param int|null $userid User id, null for current user.
     * @return array List of media records.
     */
    public static function search(int $archiveid, context_module $context, array $filters = [],
            int $limit = self::DEFAULT_LIMIT, int $offset = 0, ?int $userid = null): array {
        global $DB;

        self::require_target_tables();
        self::validate_archiveid($archiveid);

        $limit = self::normalize_limit($limit);
        $offset = max(0, $offset);

        $query = self::build_query($archiveid, $context, $filters, false, $userid);

        $records = $DB->get_records_sql($query->sql, $query->params, $offset, $limit);
        if (!$records) {
            return [];
        }

        return array_values($records);
    }

    /**
     * Count media search results.
     *
     * @param int $archiveid Archive instance id.
     * @param context_module $context Module context.
     * @param array $filters Search filters.
     * @param int|null $userid User id, null for current user.
     * @return int
     */
    public static function count(int $archiveid, context_module $context, array $filters = [],
            ?int $userid = null): int {
        global $DB;

        self::require_target_tables();
        self::validate_archiveid($archiveid);

        $query = self::build_query($archiveid, $context, $filters, true, $userid);

        return (int)$DB->count_records_sql($query->sql, $query->params);
    }

    /**
     * Return a combined result object with items and total count.
     *
     * @param int $archiveid Archive instance id.
     * @param context_module $context Module context.
     * @param array $filters Search filters.
     * @param int $limit Page size.
     * @param int $offset Offset.
     * @param int|null $userid User id, null for current user.
     * @return stdClass
     */
    public static function search_with_count(int $archiveid, context_module $context, array $filters = [],
            int $limit = self::DEFAULT_LIMIT, int $offset = 0, ?int $userid = null): stdClass {
        $result = new stdClass();
        $result->items = self::search($archiveid, $context, $filters, $limit, $offset, $userid);
        $result->total = self::count($archiveid, $context, $filters, $userid);
        $result->limit = self::normalize_limit($limit);
        $result->offset = max(0, $offset);

        return $result;
    }

    /**
     * Build SQL and parameters for a search/count query.
     *
     * @param int $archiveid Archive instance id.
     * @param context_module $context Module context.
     * @param array $filters Search filters.
     * @param bool $countonly Whether this is a count query.
     * @param int|null $userid User id.
     * @return stdClass Object with ->sql and ->params.
     */
    public static function build_query(int $archiveid, context_module $context, array $filters = [],
            bool $countonly = false, ?int $userid = null): stdClass {
        global $DB, $USER;

        self::validate_archiveid($archiveid);

        $userid = $userid ?? (int)$USER->id;
        $filters = self::normalize_filters($filters);

        $params = [
            'archiveid' => $archiveid,
        ];

        $select = $countonly ? 'COUNT(DISTINCT m.id)' : 'DISTINCT m.*';
        $from = '{' . self::TABLE_MEDIA . '} m';
        $joins = [];
        $where = ['m.archiveid = :archiveid'];

        if (!self::include_deleted($filters)) {
            $where[] = self::sql_not_in('m.status', ['deleted_soft'], 'notdeleted', $params);
        }

        self::apply_text_filter($filters, $where, $params);
        self::apply_in_filter($filters, 'mediatype', 'm.mediatype', 'mediatype', $where, $params);
        self::apply_in_filter($filters, 'mimetype', 'm.mimetype', 'mimetype', $where, $params);
        self::apply_in_filter($filters, 'status', 'm.status', 'status', $where, $params);
        self::apply_in_filter($filters, 'visibility', 'm.visibility', 'visibility', $where, $params);
        self::apply_in_filter($filters, 'audiencesuitability', 'm.audiencesuitability', 'audience', $where, $params);

        self::apply_source_filters($filters, $joins, $where, $params);
        self::apply_tag_filter($filters, $joins, $where, $params);
        self::apply_collection_filter($filters, $joins, $where, $params);
        self::apply_external_work_filter($filters, $joins, $where, $params);
        self::apply_content_tag_filter($filters, $joins, $where, $params);
        self::apply_access_filter($context, $filters, $where, $params, $userid);

        $sql = 'SELECT ' . $select . ' FROM ' . $from;
        if ($joins) {
            $sql .= ' ' . implode(' ', array_unique($joins));
        }
        $sql .= ' WHERE ' . implode(' AND ', $where);

        if (!$countonly) {
            $sql .= self::get_order_by($filters['sort'] ?? self::SORT_MODIFIED);
        }

        $query = new stdClass();
        $query->sql = $sql;
        $query->params = $params;

        return $query;
    }

    /**
     * Return quick filter options for UI facets.
     *
     * The returned values are permission-filtered with the same basic visibility
     * rules as media searches.
     *
     * @param int $archiveid Archive instance id.
     * @param context_module $context Module context.
     * @param int|null $userid User id.
     * @return stdClass
     */
    public static function get_filter_options(int $archiveid, context_module $context, ?int $userid = null): stdClass {
        global $DB;

        self::require_target_tables();
        self::validate_archiveid($archiveid);

        $basefilters = [
            'include_deleted' => false,
            'include_restricted' => self::can_view_restricted_media($context, $userid),
        ];

        $query = self::build_query($archiveid, $context, $basefilters, false, $userid);
        $subsql = $query->sql;
        $params = $query->params;

        $options = new stdClass();
        $options->mediatypes = self::get_distinct_column_from_subquery($subsql, $params, 'mediatype');
        $options->statuses = self::get_distinct_column_from_subquery($subsql, $params, 'status');
        $options->visibilities = self::get_distinct_column_from_subquery($subsql, $params, 'visibility');
        $options->audiencesuitabilities = self::get_distinct_column_from_subquery($subsql, $params, 'audiencesuitability');

        if (self::table_exists(self::TABLE_MEDIA_TAG)) {
            $sql = "SELECT DISTINCT t.tagkey
                      FROM {" . self::TABLE_MEDIA_TAG . "} t
                      JOIN (" . $subsql . ") visiblemedia ON visiblemedia.id = t.mediaid
                     WHERE t.tagkey IS NOT NULL AND t.tagkey <> ''
                  ORDER BY t.tagkey ASC";
            $options->tags = array_values($DB->get_fieldset_sql($sql, $params));
        } else {
            $options->tags = [];
        }

        return $options;
    }

    /**
     * Apply text search filter.
     *
     * @param array $filters Filters.
     * @param array $where Where clauses.
     * @param array $params Params.
     * @return void
     */
    private static function apply_text_filter(array $filters, array &$where, array &$params): void {
        global $DB;

        $q = trim((string)($filters['q'] ?? ''));
        if ($q === '') {
            return;
        }

        $like = '%' . $DB->sql_like_escape($q) . '%';
        $params['qtitle'] = $like;
        $params['qdescription'] = $like;
        $params['quuid'] = $like;

        $where[] = '(' .
            $DB->sql_like('m.title', ':qtitle', false, false) .
            ' OR ' .
            $DB->sql_like('m.description', ':qdescription', false, false) .
            ' OR ' .
            $DB->sql_like('m.uuid', ':quuid', false, false) .
        ')';
    }

    /**
     * Apply source filters.
     *
     * @param array $filters Filters.
     * @param array $joins Joins.
     * @param array $where Where clauses.
     * @param array $params Params.
     * @return void
     */
    private static function apply_source_filters(array $filters, array &$joins, array &$where, array &$params): void {
        if (!self::table_exists(self::TABLE_MEDIA_SOURCE)) {
            return;
        }

        if (isset($filters['sourcetype']) || isset($filters['sourceownership'])) {
            $joins[] = 'LEFT JOIN {' . self::TABLE_MEDIA_SOURCE . '} ms ON ms.id = m.sourceid';
        }

        self::apply_in_filter($filters, 'sourcetype', 'ms.sourcetype', 'sourcetype', $where, $params);
        self::apply_in_filter($filters, 'sourceownership', 'ms.sourceownership', 'sourceownership', $where, $params);
    }

    /**
     * Apply media tag filter.
     *
     * @param array $filters Filters.
     * @param array $joins Joins.
     * @param array $where Where clauses.
     * @param array $params Params.
     * @return void
     */
    private static function apply_tag_filter(array $filters, array &$joins, array &$where, array &$params): void {
        if (empty($filters['tag']) || !self::table_exists(self::TABLE_MEDIA_TAG)) {
            return;
        }

        $joins[] = 'JOIN {' . self::TABLE_MEDIA_TAG . '} mt ON mt.mediaid = m.id';
        $values = self::normalize_list($filters['tag']);

        if ($values) {
            [$sql, $inparams] = self::get_in_or_equal('mt.tagkey', $values, 'tag');
            $where[] = $sql;
            $params += $inparams;
        }
    }

    /**
     * Apply collection membership filter.
     *
     * @param array $filters Filters.
     * @param array $joins Joins.
     * @param array $where Where clauses.
     * @param array $params Params.
     * @return void
     */
    private static function apply_collection_filter(array $filters, array &$joins, array &$where, array &$params): void {
        $collectionid = (int)($filters['collectionid'] ?? 0);
        if ($collectionid <= 0 || !self::table_exists(self::TABLE_COLLECTION_ITEM)) {
            return;
        }

        $joins[] = 'JOIN {' . self::TABLE_COLLECTION_ITEM . '} mci ON mci.mediaid = m.id';
        $where[] = 'mci.collectionid = :collectionid';
        $params['collectionid'] = $collectionid;
    }

    /**
     * Apply external work relation filter.
     *
     * @param array $filters Filters.
     * @param array $joins Joins.
     * @param array $where Where clauses.
     * @param array $params Params.
     * @return void
     */
    private static function apply_external_work_filter(array $filters, array &$joins, array &$where, array &$params): void {
        $externalworkid = (int)($filters['externalworkid'] ?? 0);
        if ($externalworkid <= 0 || !self::table_exists(self::TABLE_RELATION)) {
            return;
        }

        $joins[] = 'JOIN {' . self::TABLE_RELATION . '} mer_external ON mer_external.sourcemediaid = m.id';
        $where[] = 'mer_external.relationtype = :externalrelationtype';
        $where[] = 'mer_external.targettype = :externalrelationtarget';
        $where[] = 'mer_external.targetid = :externalworkid';
        $params['externalrelationtype'] = 'references_external_work';
        $params['externalrelationtarget'] = 'external_work';
        $params['externalworkid'] = $externalworkid;
    }

    /**
     * Apply content advisory tag filter.
     *
     * @param array $filters Filters.
     * @param array $joins Joins.
     * @param array $where Where clauses.
     * @param array $params Params.
     * @return void
     */
    private static function apply_content_tag_filter(array $filters, array &$joins, array &$where, array &$params): void {
        if (empty($filters['contenttag'])
                || !self::table_exists(self::TABLE_CONTENT_MARKER)
                || !self::table_exists(self::TABLE_CONTENT_TAG)) {
            return;
        }

        $joins[] = 'JOIN {' . self::TABLE_CONTENT_MARKER . '} cmk ON cmk.targettype = :contentmarkertarget
                   AND cmk.targetid = m.id';
        $joins[] = 'JOIN {' . self::TABLE_CONTENT_TAG . '} ct ON ct.id = cmk.tagid';

        $params['contentmarkertarget'] = 'media';

        $values = self::normalize_list($filters['contenttag']);
        if ($values) {
            [$sql, $inparams] = self::get_in_or_equal('ct.tagkey', $values, 'contenttag');
            $where[] = $sql;
            $params += $inparams;
        }

        if (!self::can_review_advisories(null)) {
            $where[] = "(cmk.reviewstate IS NULL OR cmk.reviewstate IN ('reviewed', 'approved'))";
        }
    }

    /**
     * Apply visibility/access filter.
     *
     * This is intentionally conservative. Full access decisions remain in
     * media_policy before serving full records or files.
     *
     * @param context_module $context Context.
     * @param array $filters Filters.
     * @param array $where Where clauses.
     * @param array $params Params.
     * @param int|null $userid User id.
     * @return void
     */
    private static function apply_access_filter(context_module $context, array $filters, array &$where,
            array &$params, ?int $userid = null): void {
        $include = !empty($filters['include_restricted']);
        $canviewrestricted = self::can_view_restricted_media($context, $userid);
        $canviewcultural = self::can_view_culturally_restricted($context, $userid);

        if ($include && $canviewrestricted && $canviewcultural) {
            return;
        }

        $blocked = [
            'restricted_integrity',
            'staff_only',
        ];

        if (!$canviewrestricted) {
            $blocked[] = 'restricted';
        }

        if (!$canviewcultural) {
            $blocked[] = 'restricted_cultural';
        }

        $where[] = self::sql_not_in('m.visibility', array_values(array_unique($blocked)), 'blockedvisibility', $params);
    }

    /**
     * Apply an IN filter from filters to SQL.
     *
     * @param array $filters Filters.
     * @param string $key Filter key.
     * @param string $column SQL column.
     * @param string $prefix Param prefix.
     * @param array $where Where clauses.
     * @param array $params Params.
     * @return void
     */
    private static function apply_in_filter(array $filters, string $key, string $column, string $prefix,
            array &$where, array &$params): void {
        if (!isset($filters[$key])) {
            return;
        }

        $values = self::normalize_list($filters[$key]);
        if (!$values) {
            return;
        }

        [$sql, $inparams] = self::get_in_or_equal($column, $values, $prefix);
        $where[] = $sql;
        $params += $inparams;
    }

    /**
     * Build an IN or equality SQL fragment.
     *
     * @param string $column Column name.
     * @param array $values Values.
     * @param string $prefix Param prefix.
     * @return array SQL fragment and params.
     */
    private static function get_in_or_equal(string $column, array $values, string $prefix): array {
        global $DB;

        $values = array_values(array_unique(array_filter(array_map('strval', $values), static function($value): bool {
            return $value !== '';
        })));

        if (count($values) === 1) {
            return [$column . ' = :' . $prefix . '0', [$prefix . '0' => reset($values)]];
        }

        [$insql, $params] = $DB->get_in_or_equal($values, SQL_PARAMS_NAMED, $prefix);
        return [$column . ' ' . $insql, $params];
    }

    /**
     * Build a NOT IN SQL fragment.
     *
     * @param string $column Column name.
     * @param array $values Values.
     * @param string $prefix Param prefix.
     * @param array $params Existing params, appended to by reference.
     * @return string SQL fragment.
     */
    private static function sql_not_in(string $column, array $values, string $prefix, array &$params): string {
        global $DB;

        [$insql, $inparams] = $DB->get_in_or_equal($values, SQL_PARAMS_NAMED, $prefix, false);
        $params += $inparams;

        return '(' . $column . ' IS NULL OR ' . $column . ' ' . $insql . ')';
    }

    /**
     * Normalize filter values.
     *
     * @param array $filters Raw filters.
     * @return array
     */
    private static function normalize_filters(array $filters): array {
        $normalized = [];

        foreach ($filters as $key => $value) {
            $key = strtolower(trim((string)$key));
            if ($key === '') {
                continue;
            }

            if (is_string($value)) {
                $value = trim($value);
            }

            $normalized[$key] = $value;
        }

        return $normalized;
    }

    /**
     * Normalize a value into a string list.
     *
     * @param mixed $value Value.
     * @return array
     */
    private static function normalize_list($value): array {
        if ($value === null || $value === '') {
            return [];
        }

        if (!is_array($value)) {
            $value = [$value];
        }

        $out = [];
        foreach ($value as $item) {
            $item = trim((string)$item);
            if ($item !== '') {
                $out[] = $item;
            }
        }

        return array_values(array_unique($out));
    }

    /**
     * Determine if deleted records should be included.
     *
     * @param array $filters Filters.
     * @return bool
     */
    private static function include_deleted(array $filters): bool {
        return !empty($filters['include_deleted']);
    }

    /**
     * Normalize page size.
     *
     * @param int $limit Limit.
     * @return int
     */
    private static function normalize_limit(int $limit): int {
        if ($limit <= 0) {
            return self::DEFAULT_LIMIT;
        }

        return min($limit, self::MAX_LIMIT);
    }

    /**
     * Return ORDER BY clause.
     *
     * @param string $sort Sort key.
     * @return string
     */
    private static function get_order_by(string $sort): string {
        switch ($sort) {
            case self::SORT_TITLE_ASC:
                return ' ORDER BY m.title ASC, m.id ASC';

            case self::SORT_TITLE_DESC:
                return ' ORDER BY m.title DESC, m.id DESC';

            case self::SORT_OLDEST:
                return ' ORDER BY m.timecreated ASC, m.id ASC';

            case self::SORT_NEWEST:
                return ' ORDER BY m.timecreated DESC, m.id DESC';

            case self::SORT_MODIFIED:
            default:
                return ' ORDER BY m.timemodified DESC, m.id DESC';
        }
    }

    /**
     * Get distinct values for a column from a visible media subquery.
     *
     * @param string $subsql SQL returning media records.
     * @param array $params Params.
     * @param string $column Column.
     * @return array
     */
    private static function get_distinct_column_from_subquery(string $subsql, array $params, string $column): array {
        global $DB;

        $allowed = [
            'mediatype',
            'status',
            'visibility',
            'audiencesuitability',
        ];

        if (!in_array($column, $allowed, true)) {
            throw new \coding_exception('Invalid media search facet column: ' . $column);
        }

        $sql = "SELECT DISTINCT visiblemedia.$column
                  FROM ($subsql) visiblemedia
                 WHERE visiblemedia.$column IS NOT NULL AND visiblemedia.$column <> ''
              ORDER BY visiblemedia.$column ASC";

        return array_values($DB->get_fieldset_sql($sql, $params));
    }

    /**
     * Check whether current/user can view restricted media.
     *
     * @param context_module $context Module context.
     * @param int|null $userid User id.
     * @return bool
     */
    private static function can_view_restricted_media(context_module $context, ?int $userid = null): bool {
        return has_capability('mod/uckkarchive:viewrestrictedmedia', $context, $userid)
            || has_capability('mod/uckkarchive:viewrestricted', $context, $userid);
    }

    /**
     * Check whether current/user can view culturally restricted material.
     *
     * @param context_module $context Module context.
     * @param int|null $userid User id.
     * @return bool
     */
    private static function can_view_culturally_restricted(context_module $context, ?int $userid = null): bool {
        return has_capability('mod/uckkarchive:viewculturallyrestricted', $context, $userid);
    }

    /**
     * Check whether current user can review advisories.
     *
     * @param context_module|null $context Module context.
     * @return bool
     */
    private static function can_review_advisories(?context_module $context): bool {
        if ($context === null) {
            return false;
        }

        return has_capability('mod/uckkarchive:reviewadvisories', $context);
    }

    /**
     * Validate archive id.
     *
     * @param int $archiveid Archive id.
     * @return void
     */
    private static function validate_archiveid(int $archiveid): void {
        if ($archiveid <= 0) {
            throw new \coding_exception('Invalid mod_uckkarchive archive id.');
        }
    }

    /**
     * Require target media table.
     *
     * @return void
     */
    private static function require_target_tables(): void {
        if (!self::table_exists(self::TABLE_MEDIA)) {
            throw new \coding_exception('Media search requires table ' . self::TABLE_MEDIA . '.');
        }
    }

    /**
     * Check table existence.
     *
     * @param string $table Table name without prefix.
     * @return bool
     */
    private static function table_exists(string $table): bool {
        global $DB;

        return $DB->get_manager()->table_exists($table);
    }
}
