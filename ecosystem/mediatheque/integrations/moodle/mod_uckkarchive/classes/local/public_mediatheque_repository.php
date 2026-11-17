<?php
// This file is part of Moodle - https://moodle.org/
//
// Moodle is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// any later version.

/**
 * Public Médiathèque repository.
 *
 * @package    mod_uckkarchive
 * @copyright  2026 Univers-Cité King Klown
 * @license    https://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later
 */

declare(strict_types=1);

namespace mod_uckkarchive\local;

use coding_exception;
use context;
use context_module;
use stdClass;
use xmldb_table;

defined('MOODLE_INTERNAL') || die();

/**
 * Repository for the public Médiathèque surface.
 *
 * This class is intentionally a narrow read-only adapter. It exposes only
 * public, active, general-audience, searchable media summaries and never serves
 * original files, private notes, cultural protocol notes, raw metadata, review
 * rationale, or internal database identifiers.
 *
 * It does not replace media_search, media_policy, media_file, content_policy or
 * any existing media-library output class. It only shapes the public subset used
 * by the local_uckk public page and by the public Médiathèque service.
 */
final class public_mediatheque_repository {
    /** Default public page size. */
    public const DEFAULT_PERPAGE = 12;

    /** Maximum public page size. */
    public const MAX_PERPAGE = 48;

    /** Public media object type. */
    public const OBJECT_MEDIA = 'media';

    /** Canonical table names. */
    private const TABLE_MEDIA = 'uckkarchive_media';
    private const TABLE_MEDIA_SOURCE = 'uckkarchive_media_source';
    private const TABLE_MEDIA_TAG = 'uckkarchive_media_tag';
    private const TABLE_COLLECTION = 'uckkarchive_media_collection';
    private const TABLE_COLLECTION_ITEM = 'uckkarchive_media_collection_item';
    private const TABLE_CONTENT_MARKER = 'uckkarchive_content_marker';
    private const TABLE_LIBRARY = 'uckkarchive_library';
    private const TABLE_LIBRARY_BRIDGE = 'uckkarchive_library_bridge';

    /** Public media constraints. */
    private const PUBLIC_STATUS = media_policy::STATUS_ACTIVE;
    private const PUBLIC_VISIBILITY = media_policy::VISIBILITY_PUBLIC;
    private const PUBLIC_AUDIENCE = media_policy::AUDIENCE_GENERAL;

    /** Supported public sort keys. */
    private const SORT_RELEVANCE = 'relevance';
    private const SORT_NEWEST = 'newest';
    private const SORT_TITLE = 'title';
    private const SORT_TYPE = 'type';

    /** Maximum public summary length. */
    private const SUMMARY_LENGTH = 240;

    /** @var media_library_scope|null Library scope registry. */
    private ?media_library_scope $libraryscope = null;

    /** @var array<int,stdClass|null> Small per-request library cache. */
    private array $librarycache = [];

    /**
     * Search public Médiathèque media.
     *
     * archiveid = 0 means site-wide public discovery.
     *
     * Supported filters:
     * - q: free text over title, summary, description and UUID
     * - type: all or media
     * - mediatype: string or array
     * - tag: string or array of media tag keys
     * - collection: collection UUID
     * - source: public source value; matches m.source or m.sourcetype
     * - sort: relevance, newest, title, type
     * - page: one-based page
     * - perpage: page size, max 48
     *
     * @param int $archiveid Archive instance id, or 0 for site-wide.
     * @param context_module|null $context Optional module context.
     * @param array<string, mixed> $filters Public filters.
     * @return stdClass Public result object.
     */
    public function search(int $archiveid = 0, ?context_module $context = null, array $filters = []): stdClass {
        global $DB;

        $this->require_media_table();

        $filters = $this->normalise_filters($filters);
        $page = $this->normalise_page($filters['page'] ?? 1);
        $perpage = $this->normalise_perpage($filters['perpage'] ?? self::DEFAULT_PERPAGE);
        $offset = ($page - 1) * $perpage;

        $query = $this->build_public_media_query($archiveid, $filters, false);
        $countquery = $this->build_public_media_query($archiveid, $filters, true);

        $records = $DB->get_records_sql($query->sql, $query->params, $offset, $perpage);
        $total = (int)$DB->count_records_sql($countquery->sql, $countquery->params);

        $targetlibraryid = max(0, (int)($filters['libraryid'] ?? 0));

        $items = [];
        foreach ($records as $media) {
            if (!$this->is_public_media($media)) {
                continue;
            }

            $items[] = $this->export_media_card($context, $media, $targetlibraryid);
        }

        $result = new stdClass();
        $result->items = array_values($items);
        $result->total = $total;
        $result->pagination = (object)[
            'page' => $page,
            'perpage' => $perpage,
            'total' => $total,
            'hasmore' => ($offset + $perpage) < $total,
        ];
        $result->facets = $this->get_facets($archiveid, $filters);
        $result->notices = [];
        $result->warnings = [];

        return $result;
    }

    /**
     * Get a single public media card by UUID.
     *
     * archiveid = 0 means site-wide lookup.
     *
     * @param int $archiveid Archive instance id, or 0 for site-wide.
     * @param context_module|null $context Optional module context.
     * @param string $uuid Media UUID.
     * @return stdClass|null Public media card or null.
     */
    public function get_media_by_uuid(
        int $archiveid = 0,
        ?context_module $context = null,
        string $uuid = '',
        int $libraryid = 0
    ): ?stdClass {
        global $DB;

        $this->require_media_table();

        $uuid = clean_param(trim($uuid), PARAM_ALPHANUMEXT);
        if ($uuid === '') {
            return null;
        }

        $conditions = ['uuid' => $uuid];
        if ($archiveid > 0) {
            $conditions['archiveid'] = $archiveid;
        }

        $media = $DB->get_record(self::TABLE_MEDIA, $conditions);

        if (!$media || !$this->is_public_media($media)) {
            return null;
        }

        if ($libraryid > 0 && !$this->is_media_visible_in_library((int)$media->id, (int)($media->libraryid ?? 0), $libraryid)) {
            return null;
        }

        return $this->export_media_card($context, $media, $libraryid);
    }

    /**
     * Build public facets from the same public surface.
     *
     * @param int $archiveid Archive instance id, or 0 for site-wide.
     * @param array<string, mixed> $filters Active filters.
     * @return array<int, array<string, mixed>> Public facet groups.
     */
    public function get_facets(int $archiveid = 0, array $filters = []): array {
        $filters = $this->normalise_filters($filters);

        return [
            $this->build_column_facet_group($archiveid, $filters, 'mediatype', 'mediatype'),
            $this->build_source_facet_group($archiveid, $filters),
            $this->build_tag_facet_group($archiveid, $filters),
            $this->build_collection_facet_group($archiveid, $filters),
        ];
    }

    /**
     * Build SQL for public media.
     *
     * @param int $archiveid Archive instance id, or 0 for site-wide.
     * @param array<string, mixed> $filters Public filters.
     * @param bool $countonly Whether the query is a count query.
     * @param bool $withoutfacetedfilters Build base public set for facet derivation.
     * @return stdClass Query object with sql and params.
     */
    private function build_public_media_query(
        int $archiveid,
        array $filters,
        bool $countonly = false,
        bool $withoutfacetedfilters = false
    ): stdClass {
        global $DB;

        $params = [
            'statusactive' => self::PUBLIC_STATUS,
            'visibilitypublic' => self::PUBLIC_VISIBILITY,
            'audiencegeneral' => self::PUBLIC_AUDIENCE,
        ];

        $select = $countonly ? 'COUNT(DISTINCT m.id)' : 'DISTINCT m.*';
        $from = '{' . self::TABLE_MEDIA . '} m';
        $joins = [];
        $where = [
            'm.status = :statusactive',
            'm.visibility = :visibilitypublic',
            'm.audiencesuitability = :audiencegeneral',
            '(m.searchable IS NULL OR m.searchable = 1)',
            '(m.restricted IS NULL OR m.restricted = 0)',
            '(m.culturalprotocol IS NULL OR m.culturalprotocol = 0)',
        ];

        if ($archiveid > 0) {
            $params['archiveid'] = $archiveid;
            $where[] = 'm.archiveid = :archiveid';
        }

        $this->apply_library_scope($filters, $where, $params);

        $type = trim((string)($filters['type'] ?? 'all'));
        if ($type !== '' && $type !== 'all' && $type !== self::OBJECT_MEDIA) {
            $where[] = '1 = 0';
        }

        $q = trim((string)($filters['q'] ?? ''));
        if ($q !== '') {
            $like = '%' . $DB->sql_like_escape($q) . '%';
            $params['qtitle'] = $like;
            $params['qsummary'] = $like;
            $params['qdescription'] = $like;
            $params['quuid'] = $like;
            $where[] = '(' .
                $DB->sql_like('m.title', ':qtitle', false, false) .
                ' OR ' . $DB->sql_like('m.summary', ':qsummary', false, false) .
                ' OR ' . $DB->sql_like('m.description', ':qdescription', false, false) .
                ' OR ' . $DB->sql_like('m.uuid', ':quuid', false, false) .
            ')';
        }

        if (!$withoutfacetedfilters) {
            $this->apply_list_filter($filters, 'mediatype', 'm.mediatype', 'mediatype', $where, $params);

            $source = trim((string)($filters['source'] ?? ''));
            if ($source !== '' && $source !== 'all') {
                $params['sourcevalue'] = clean_param($source, PARAM_ALPHANUMEXT);
                $where[] = '(m.source = :sourcevalue OR m.sourcetype = :sourcevalue)';
            }

            if (!empty($filters['tag']) && $this->table_exists(self::TABLE_MEDIA_TAG)) {
                $joins[] = 'JOIN {' . self::TABLE_MEDIA_TAG . '} mt ON mt.mediaid = m.id';
                $this->apply_list_filter($filters, 'tag', 'mt.tagkey', 'tag', $where, $params);
            }

            $collection = trim((string)($filters['collection'] ?? ''));
            if ($collection !== '' && $this->table_exists(self::TABLE_COLLECTION) && $this->table_exists(self::TABLE_COLLECTION_ITEM)) {
                $joins[] = 'JOIN {' . self::TABLE_COLLECTION_ITEM . '} mci ON mci.mediaid = m.id';
                $joins[] = 'JOIN {' . self::TABLE_COLLECTION . '} mc ON mc.id = mci.collectionid';
                $where[] = 'mc.uuid = :collectionuuid';
                $where[] = 'mc.status = :collectionstatus';
                $where[] = 'mc.visibility = :collectionvisibility';
                $where[] = 'mc.audiencesuitability = :collectionaudience';
                $params['collectionuuid'] = clean_param($collection, PARAM_ALPHANUMEXT);
                $params['collectionstatus'] = self::PUBLIC_STATUS;
                $params['collectionvisibility'] = self::PUBLIC_VISIBILITY;
                $params['collectionaudience'] = self::PUBLIC_AUDIENCE;
            }
        }

        $sql = 'SELECT ' . $select . ' FROM ' . $from;
        if ($joins) {
            $sql .= ' ' . implode(' ', array_unique($joins));
        }
        $sql .= ' WHERE ' . implode(' AND ', $where);

        if (!$countonly && !$withoutfacetedfilters) {
            $sql .= $this->get_order_by((string)($filters['sort'] ?? self::SORT_RELEVANCE));
        }

        return (object)[
            'sql' => $sql,
            'params' => $params,
        ];
    }

    /**
     * Export a media record as a flat public card DTO.
     *
     * @param context_module|null $context Optional module context.
     * @param stdClass $media Media record.
     * @return stdClass Public flat card data.
     */
    private function export_media_card(?context_module $context, stdClass $media, int $targetlibraryid = 0): stdClass {
        $markers = $this->get_public_marker_summary((int)$media->id);
        $thumbnailurl = $this->get_public_thumbnail_url($context, $media);
        $summary = $this->get_public_summary($media);
        $sourcevalue = (string)($media->source ?? $media->sourcetype ?? '');
        $externalsource = $this->get_public_external_source($media);
        $externalurl = (string)$externalsource->url;
        $library = $this->get_library_exposure($media, $targetlibraryid);

        return (object)[
            'uuid' => (string)$media->uuid,
            'objecttype' => self::OBJECT_MEDIA,
            'title' => format_string((string)$media->title),
            'subtitle' => (string)($media->subtitle ?? ''),
            'summary' => $summary,
            'mediatype' => (string)$media->mediatype,
            'mimetype' => (string)($media->mimetype ?? ''),
            'language' => (string)($media->language ?? ''),
            'thumbnailurl' => $thumbnailurl,

            'libraryslug' => $library->slug,
            'libraryname' => $library->name,
            'isbridged' => $library->isbridged,
            'bridgescope' => $library->bridgescope,
            'bridgelabel' => $library->bridgelabel,

            'sourcevalue' => $sourcevalue,
            'sourcelabel' => $this->label($sourcevalue),

            'externalurl' => $externalurl,
            'hasexternalurl' => $externalurl !== '',
            'externalsourcetitle' => (string)$externalsource->title,
            'externalcitation' => (string)$externalsource->citation,
            'externalsourcetype' => (string)$externalsource->sourcetype,

            'license' => (string)($media->license ?? $media->licensekey ?? ''),
            'rightsstatement' => (string)($media->rightsstatement ?? $media->rightsstatus ?? ''),
            'copyallowed' => false,

            'status' => (string)$media->status,
            'visibility' => (string)$media->visibility,
            'validation' => (string)($media->validationstate ?? ''),

            'badges' => $this->build_badges($media, $markers),

            'haspublicadvisory' => $markers->count > 0,
            'advisorysummary' => $markers->summary,
            'haspublicprotocol' => false,
            'culturalprotocolsummary' => '',

            'collectioncount' => $this->count_public_collections((int)$media->id),
            'markercount' => $markers->count,
            'externalworkcount' => 0,

            'canviewdetail' => true,
            'canviewfile' => $thumbnailurl !== '',
            'candownload' => false,
            'canexport' => false,
        ];
    }

    /**
     * Apply one target library plus its explicit incoming bridges.
     *
     * No library id means the low-level repository caller intentionally asked
     * for the legacy/unscoped view (used by internal tests/tools). Public pages
     * always pass a resolved library id through public_mediatheque_service.
     *
     * @param array<string,mixed> $filters Filters.
     * @param string[] $where SQL where clauses.
     * @param array<string,mixed> $params SQL params.
     */
    private function apply_library_scope(array $filters, array &$where, array &$params): void {
        $targetlibraryid = max(0, (int)($filters['libraryid'] ?? 0));
        $libraryrequired = !empty($filters['libraryrequired']);
        if ($targetlibraryid <= 0) {
            if ($libraryrequired) {
                $where[] = '1 = 0';
            }
            return;
        }

        if (!media_library_scope::schema_ready()) {
            // Fail closed rather than falling back to the formerly global view.
            $where[] = '1 = 0';
            return;
        }

        $params += [
            'targetlibraryid' => $targetlibraryid,
            'bridgetargetlibraryid' => $targetlibraryid,
            'bridgestatus' => media_library_scope::STATUS_ACTIVE,
            'bridgescopelibrary' => media_library_scope::SCOPE_LIBRARY,
            'bridgescopecollection' => media_library_scope::SCOPE_COLLECTION,
            'bridgescopemedia' => media_library_scope::SCOPE_MEDIA,
        ];

        $where[] = '(m.libraryid = :targetlibraryid OR EXISTS (
            SELECT 1
              FROM {' . self::TABLE_LIBRARY_BRIDGE . '} lb
             WHERE lb.targetlibraryid = :bridgetargetlibraryid
               AND lb.sourcelibraryid = m.libraryid
               AND lb.status = :bridgestatus
               AND (
                    (lb.scopetype = :bridgescopelibrary AND lb.scopeid = 0)
                 OR (lb.scopetype = :bridgescopemedia AND lb.scopeid = m.id)
                 OR (lb.scopetype = :bridgescopecollection AND EXISTS (
                        SELECT 1
                          FROM {' . self::TABLE_COLLECTION_ITEM . '} lbci
                         WHERE lbci.collectionid = lb.scopeid
                           AND lbci.mediaid = m.id
                    ))
               )
        ))';
    }

    /** Check one media row against a target library and its bridges. */
    private function is_media_visible_in_library(int $mediaid, int $homelibraryid, int $targetlibraryid): bool {
        global $DB;

        if ($targetlibraryid <= 0) {
            return true;
        }
        if ($homelibraryid > 0 && $homelibraryid === $targetlibraryid) {
            return true;
        }
        if (!media_library_scope::schema_ready() || $homelibraryid <= 0 || $mediaid <= 0) {
            return false;
        }

        $sql = 'SELECT 1
                  FROM {' . self::TABLE_LIBRARY_BRIDGE . '} lb
                 WHERE lb.targetlibraryid = :targetlibraryid
                   AND lb.sourcelibraryid = :sourcelibraryid
                   AND lb.status = :status
                   AND (
                        (lb.scopetype = :scopelibrary AND lb.scopeid = 0)
                     OR (lb.scopetype = :scopemedia AND lb.scopeid = :mediaid)
                     OR (lb.scopetype = :scopecollection AND EXISTS (
                            SELECT 1
                              FROM {' . self::TABLE_COLLECTION_ITEM . '} ci
                             WHERE ci.collectionid = lb.scopeid
                               AND ci.mediaid = :collectionmediaid
                        ))
                   )';

        return $DB->record_exists_sql($sql, [
            'targetlibraryid' => $targetlibraryid,
            'sourcelibraryid' => $homelibraryid,
            'status' => media_library_scope::STATUS_ACTIVE,
            'scopelibrary' => media_library_scope::SCOPE_LIBRARY,
            'scopemedia' => media_library_scope::SCOPE_MEDIA,
            'mediaid' => $mediaid,
            'scopecollection' => media_library_scope::SCOPE_COLLECTION,
            'collectionmediaid' => $mediaid,
        ]);
    }

    /** Build public origin/bridge metadata for one media card. */
    private function get_library_exposure(stdClass $media, int $targetlibraryid): stdClass {
        $homelibraryid = max(0, (int)($media->libraryid ?? 0));
        $library = $this->get_library_by_id($homelibraryid);
        $bridge = null;

        if ($targetlibraryid > 0 && $homelibraryid > 0 && $homelibraryid !== $targetlibraryid) {
            $bridge = $this->library_scope()->get_bridge_for_media(
                $targetlibraryid,
                (int)$media->id,
                $homelibraryid
            );
        }

        return (object)[
            'slug' => $library ? (string)$library->slug : '',
            'name' => $library ? format_string((string)$library->name) : '',
            'isbridged' => $bridge !== null,
            'bridgescope' => $bridge ? (string)$bridge->scopetype : '',
            'bridgelabel' => $bridge ? format_string((string)($bridge->label ?? '')) : '',
        ];
    }

    private function get_library_by_id(int $libraryid): ?stdClass {
        if ($libraryid <= 0) {
            return null;
        }
        if (array_key_exists($libraryid, $this->librarycache)) {
            return $this->librarycache[$libraryid];
        }
        $this->librarycache[$libraryid] = $this->library_scope()->resolve_by_id($libraryid);
        return $this->librarycache[$libraryid];
    }

    private function library_scope(): media_library_scope {
        if ($this->libraryscope === null) {
            $this->libraryscope = new media_library_scope();
        }
        return $this->libraryscope;
    }

    /**
     * Return whether the record is safe for the public surface.
     *
     * @param stdClass $media Media record.
     * @return bool
     */
    private function is_public_media(stdClass $media): bool {
        if (!media_policy::can_be_publicly_listed($media)) {
            return false;
        }

        if (isset($media->searchable) && (int)$media->searchable !== 1) {
            return false;
        }

        if (!empty($media->restricted) || !empty($media->culturalprotocol)) {
            return false;
        }

        return true;
    }

    /**
     * Build a public facet group from one media column.
     *
     * @param int $archiveid Archive id or 0.
     * @param array<string, mixed> $filters Filters.
     * @param string $key Facet key.
     * @param string $column Column name.
     * @return array<string, mixed>
     */
    private function build_column_facet_group(int $archiveid, array $filters, string $key, string $column): array {
        global $DB;

        $allowed = ['mediatype'];
        if (!in_array($column, $allowed, true)) {
            throw new coding_exception('Invalid public Médiathèque facet column: ' . $column);
        }

        $base = $this->build_public_media_query($archiveid, $filters, false, true);
        $sql = "SELECT publicmedia.$column AS value, COUNT(1) AS resultcount
                  FROM (" . $base->sql . ") publicmedia
                 WHERE publicmedia.$column IS NOT NULL AND publicmedia.$column <> ''
              GROUP BY publicmedia.$column
              ORDER BY publicmedia.$column ASC";

        $records = $DB->get_records_sql($sql, $base->params, 0, 50);
        $active = (string)($filters[$key] ?? '');

        $items = [];
        foreach ($records as $record) {
            $value = (string)$record->value;
            $items[] = [
                'value' => $value,
                'label' => $this->label($value),
                'count' => (int)$record->resultcount,
                'active' => $active !== '' && $active !== 'all' && $active === $value,
            ];
        }

        return [
            'key' => $key,
            'label' => $this->label($key),
            'items' => $items,
        ];
    }

    /**
     * Build source facet group.
     *
     * @param int $archiveid Archive id or 0.
     * @param array<string, mixed> $filters Filters.
     * @return array<string, mixed>
     */
    private function build_source_facet_group(int $archiveid, array $filters): array {
        global $DB;

        $base = $this->build_public_media_query($archiveid, $filters, false, true);
        $valueexpr = "CASE
                        WHEN publicmedia.source IS NOT NULL AND publicmedia.source <> '' THEN publicmedia.source
                        ELSE publicmedia.sourcetype
                      END";

        $sql = "SELECT $valueexpr AS value, COUNT(1) AS resultcount
                  FROM (" . $base->sql . ") publicmedia
                 WHERE $valueexpr IS NOT NULL AND $valueexpr <> ''
              GROUP BY $valueexpr
              ORDER BY $valueexpr ASC";

        $records = $DB->get_records_sql($sql, $base->params, 0, 50);
        $active = (string)($filters['source'] ?? '');

        $items = [];
        foreach ($records as $record) {
            $value = (string)$record->value;
            $items[] = [
                'value' => $value,
                'label' => $this->label($value),
                'count' => (int)$record->resultcount,
                'active' => $active !== '' && $active !== 'all' && $active === $value,
            ];
        }

        return [
            'key' => 'source',
            'label' => $this->label('source'),
            'items' => $items,
        ];
    }

    /**
     * Build public tag facet group.
     *
     * @param int $archiveid Archive id or 0.
     * @param array<string, mixed> $filters Filters.
     * @return array<string, mixed>
     */
    private function build_tag_facet_group(int $archiveid, array $filters): array {
        global $DB;

        $items = [];

        if ($this->table_exists(self::TABLE_MEDIA_TAG)) {
            $base = $this->build_public_media_query($archiveid, $filters, false, true);
            $sql = "SELECT mt.tagkey AS value, COUNT(1) AS resultcount
                      FROM {" . self::TABLE_MEDIA_TAG . "} mt
                      JOIN (" . $base->sql . ") publicmedia ON publicmedia.id = mt.mediaid
                     WHERE mt.tagkey IS NOT NULL AND mt.tagkey <> ''
                  GROUP BY mt.tagkey
                  ORDER BY mt.tagkey ASC";

            $records = $DB->get_records_sql($sql, $base->params, 0, 50);
            $active = (string)($filters['tag'] ?? '');

            foreach ($records as $record) {
                $value = (string)$record->value;
                $items[] = [
                    'value' => $value,
                    'label' => format_string($value),
                    'count' => (int)$record->resultcount,
                    'active' => $active !== '' && $active === $value,
                ];
            }
        }

        return [
            'key' => 'tag',
            'label' => $this->label('tag'),
            'items' => $items,
        ];
    }

    /**
     * Build public collection facet group.
     *
     * @param int $archiveid Archive id or 0.
     * @param array<string, mixed> $filters Filters.
     * @return array<string, mixed>
     */
    private function build_collection_facet_group(int $archiveid, array $filters): array {
        global $DB;

        $items = [];

        if ($this->table_exists(self::TABLE_COLLECTION) && $this->table_exists(self::TABLE_COLLECTION_ITEM)) {
            $base = $this->build_public_media_query($archiveid, $filters, false, true);
            $params = $base->params;
            $params['collectionstatus'] = self::PUBLIC_STATUS;
            $params['collectionvisibility'] = self::PUBLIC_VISIBILITY;
            $params['collectionaudience'] = self::PUBLIC_AUDIENCE;

            $sql = "SELECT c.uuid AS value, c.title AS label, COUNT(1) AS resultcount
                      FROM {" . self::TABLE_COLLECTION . "} c
                      JOIN {" . self::TABLE_COLLECTION_ITEM . "} ci ON ci.collectionid = c.id
                      JOIN (" . $base->sql . ") publicmedia ON publicmedia.id = ci.mediaid
                     WHERE c.uuid IS NOT NULL AND c.uuid <> ''
                       AND c.title IS NOT NULL AND c.title <> ''
                       AND c.status = :collectionstatus
                       AND c.visibility = :collectionvisibility
                       AND c.audiencesuitability = :collectionaudience
                  GROUP BY c.uuid, c.title
                  ORDER BY c.title ASC";

            $records = $DB->get_records_sql($sql, $params, 0, 50);
            $active = (string)($filters['collection'] ?? '');

            foreach ($records as $record) {
                $value = (string)$record->value;
                $items[] = [
                    'value' => $value,
                    'label' => format_string((string)$record->label),
                    'count' => (int)$record->resultcount,
                    'active' => $active !== '' && $active === $value,
                ];
            }
        }

        return [
            'key' => 'collection',
            'label' => $this->label('collection'),
            'items' => $items,
        ];
    }

    /**
     * Return public marker count and summary.
     *
     * @param int $mediaid Media id.
     * @return stdClass Marker summary.
     */
    private function get_public_marker_summary(int $mediaid): stdClass {
        global $DB;

        $empty = (object)[
            'count' => 0,
            'severity' => '',
            'summary' => '',
        ];

        if (!$this->table_exists(self::TABLE_CONTENT_MARKER)) {
            return $empty;
        }

        $records = $DB->get_records_select(
            self::TABLE_CONTENT_MARKER,
            "targettype = :targettype
             AND targetid = :targetid
             AND visibility = :visibility
             AND reviewstate IN ('reviewed', 'approved')
             AND (restricted IS NULL OR restricted = 0)
             AND (culturalprotocol IS NULL OR culturalprotocol = 0)
             AND (redacted IS NULL OR redacted = 0)",
            [
                'targettype' => 'media',
                'targetid' => $mediaid,
                'visibility' => self::PUBLIC_VISIBILITY,
            ],
            'timemodified DESC, id DESC',
            'id, severity, description',
            0,
            3
        );

        if (!$records) {
            return $empty;
        }

        $descriptions = [];
        $severity = '';
        foreach ($records as $record) {
            if ($severity === '' && !empty($record->severity)) {
                $severity = (string)$record->severity;
            }
            if (!empty($record->description)) {
                $descriptions[] = $this->truncate(clean_text((string)$record->description), 120);
            }
        }

        return (object)[
            'count' => count($records),
            'severity' => $severity,
            'summary' => implode(' ', array_slice($descriptions, 0, 2)),
        ];
    }

    /**
     * Build public badges.
     *
     * @param stdClass $media Media.
     * @param stdClass $markers Marker summary.
     * @return array<int, array<string, string>>
     */
    private function build_badges(stdClass $media, stdClass $markers): array {
        $badges = [];

        if (!empty($media->mediatype)) {
            $badges[] = [
                'key' => 'mediatype',
                'label' => $this->label((string)$media->mediatype),
                'type' => 'type',
            ];
        }

        if ((int)$markers->count > 0) {
            $badges[] = [
                'key' => 'advisory',
                'label' => $this->label('content advisory'),
                'type' => 'advisory',
            ];
        }

        return $badges;
    }

    /**
     * Count public collections for a media record.
     *
     * @param int $mediaid Media id.
     * @return int
     */
    private function count_public_collections(int $mediaid): int {
        global $DB;

        if (!$this->table_exists(self::TABLE_COLLECTION) || !$this->table_exists(self::TABLE_COLLECTION_ITEM)) {
            return 0;
        }

        return (int)$DB->count_records_sql(
            "SELECT COUNT(1)
               FROM {" . self::TABLE_COLLECTION_ITEM . "} ci
               JOIN {" . self::TABLE_COLLECTION . "} c ON c.id = ci.collectionid
              WHERE ci.mediaid = :mediaid
                AND c.status = :collectionstatus
                AND c.visibility = :collectionvisibility
                AND c.audiencesuitability = :collectionaudience",
            [
                'mediaid' => $mediaid,
                'collectionstatus' => self::PUBLIC_STATUS,
                'collectionvisibility' => self::PUBLIC_VISIBILITY,
                'collectionaudience' => self::PUBLIC_AUDIENCE,
            ]
        );
    }

    /**
     * Return a public external source object for a media record.
     *
     * The public Médiathèque may reference third-party media without copying the
     * original file into Moodle. This method exposes only a safe http(s) URL and
     * non-private citation metadata. It never serves original Moodle files.
     *
     * Lookup order:
     * - media.sourceurl when present;
     * - linked media source through media.sourceid;
     * - latest media source linked by mediaid.
     *
     * @param stdClass $media Media record.
     * @return stdClass Public external source DTO.
     */
    private function get_public_external_source(stdClass $media): stdClass {
        $empty = (object)[
            'url' => '',
            'title' => '',
            'citation' => '',
            'sourcetype' => '',
        ];

        $directurl = $this->clean_public_external_url((string)($media->sourceurl ?? ''));
        if ($directurl !== '') {
            return (object)[
                'url' => $directurl,
                'title' => (string)($media->title ?? ''),
                'citation' => '',
                'sourcetype' => (string)($media->sourcetype ?? $media->source ?? ''),
            ];
        }

        if (!$this->table_exists(self::TABLE_MEDIA_SOURCE)) {
            return $empty;
        }

        $source = null;

        if (!empty($media->sourceid)) {
            $source = $this->get_public_media_source_by_id((int)$media->sourceid, (int)$media->id);
        }

        if (!$source && !empty($media->id)) {
            $source = $this->get_latest_public_media_source((int)$media->id);
        }

        if (!$source) {
            return $empty;
        }

        $url = $this->clean_public_external_url((string)($source->sourceurl ?? ''));
        if ($url === '') {
            return $empty;
        }

        return (object)[
            'url' => $url,
            'title' => (string)($source->sourceauthor ?? ''),
            'citation' => (string)($source->citation ?? ''),
            'sourcetype' => (string)($source->sourcetype ?? ''),
        ];
    }

    /**
     * Return a public media source by id when it belongs to the media record.
     *
     * @param int $sourceid Source id.
     * @param int $mediaid Media id.
     * @return stdClass|null Source record.
     */
    private function get_public_media_source_by_id(int $sourceid, int $mediaid): ?stdClass {
        global $DB;

        if ($sourceid <= 0 || $mediaid <= 0) {
            return null;
        }

        $source = $DB->get_record(
            self::TABLE_MEDIA_SOURCE,
            ['id' => $sourceid],
            'id, mediaid, sourcetype, sourceurl, sourceauthor, citation, rightsstatus',
            IGNORE_MISSING
        );

        if (!$source || (int)($source->mediaid ?? 0) !== $mediaid) {
            return null;
        }

        return $source;
    }

    /**
     * Return latest public media source linked by media id.
     *
     * @param int $mediaid Media id.
     * @return stdClass|null Source record.
     */
    private function get_latest_public_media_source(int $mediaid): ?stdClass {
        global $DB;

        if ($mediaid <= 0) {
            return null;
        }

        $records = $DB->get_records_select(
            self::TABLE_MEDIA_SOURCE,
            "mediaid = :mediaid AND sourceurl IS NOT NULL AND sourceurl <> ''",
            ['mediaid' => $mediaid],
            'timemodified DESC, id DESC',
            'id, mediaid, sourcetype, sourceurl, sourceauthor, citation, rightsstatus',
            0,
            1
        );

        if (!$records) {
            return null;
        }

        return reset($records) ?: null;
    }

    /**
     * Clean and validate a public external URL.
     *
     * Only absolute http(s) URLs are exposed. This prevents accidental exposure
     * of local plugin routes, file URLs, JavaScript URLs, or malformed values.
     *
     * @param string $url Raw URL.
     * @return string Public URL, or empty string.
     */
    private function clean_public_external_url(string $url): string {
        $url = trim(clean_param($url, PARAM_URL));

        if ($url === '') {
            return '';
        }

        $parts = parse_url($url);
        if (!is_array($parts)) {
            return '';
        }

        $scheme = strtolower((string)($parts['scheme'] ?? ''));
        $host = trim((string)($parts['host'] ?? ''));

        if (!in_array($scheme, ['http', 'https'], true) || $host === '') {
            return '';
        }

        return $url;
    }

    /**
     * Return public thumbnail URL if a thumbnail exists.
     *
     * @param context_module|null $context Optional module context.
     * @param stdClass $media Media record.
     * @return string
     */
    private function get_public_thumbnail_url(?context_module $context, stdClass $media): string {
        if (!$this->is_public_media($media)) {
            return '';
        }

        if (!$context && !empty($media->contextid)) {
            $resolved = context::instance_by_id((int)$media->contextid, IGNORE_MISSING);
            if ($resolved instanceof context_module) {
                $context = $resolved;
            }
        }

        if (!$context) {
            return '';
        }

        $url = media_file::get_first_file_url($context, media_file::AREA_THUMBNAIL, (int)$media->id);

        return $url ? $url->out(false) : '';
    }

    /**
     * Return a safe public summary.
     *
     * @param stdClass $media Media record.
     * @return string
     */
    private function get_public_summary(stdClass $media): string {
        $summary = trim((string)($media->summary ?? ''));
        if ($summary === '') {
            $summary = trim((string)($media->description ?? ''));
        }

        return $this->truncate(clean_text($summary), self::SUMMARY_LENGTH);
    }

    /**
     * Apply a string-list filter.
     *
     * @param array<string, mixed> $filters Filters.
     * @param string $key Filter key.
     * @param string $column SQL column.
     * @param string $prefix Named parameter prefix.
     * @param array<int, string> $where Where fragments.
     * @param array<string, mixed> $params SQL params.
     * @return void
     */
    private function apply_list_filter(
        array $filters,
        string $key,
        string $column,
        string $prefix,
        array &$where,
        array &$params
    ): void {
        if (!array_key_exists($key, $filters)) {
            return;
        }

        $values = $this->normalise_string_list($filters[$key]);
        if (!$values) {
            return;
        }

        global $DB;
        [$insql, $inparams] = $DB->get_in_or_equal($values, SQL_PARAMS_NAMED, $prefix);
        $where[] = $column . ' ' . $insql;
        $params += $inparams;
    }

    /**
     * Return ORDER BY SQL for public sort key.
     *
     * @param string $sort Sort key.
     * @return string
     */
    private function get_order_by(string $sort): string {
        return match ($sort) {
            self::SORT_NEWEST => ' ORDER BY m.timecreated DESC, m.id DESC',
            self::SORT_TITLE => ' ORDER BY m.title ASC, m.id ASC',
            self::SORT_TYPE => ' ORDER BY m.mediatype ASC, m.title ASC, m.id ASC',
            self::SORT_RELEVANCE => ' ORDER BY m.timemodified DESC, m.id DESC',
            default => ' ORDER BY m.timemodified DESC, m.id DESC',
        };
    }

    /**
     * Normalise filters.
     *
     * @param array<string, mixed> $filters Raw filters.
     * @return array<string, mixed>
     */
    private function normalise_filters(array $filters): array {
        $out = [];

        foreach ($filters as $key => $value) {
            $key = clean_param(strtolower(trim((string)$key)), PARAM_ALPHANUMEXT);
            if ($key === '') {
                continue;
            }

            if (is_string($value)) {
                $value = trim($value);
            }

            $out[$key] = $value;
        }

        return $out;
    }

    /**
     * Normalise a string or array to clean non-empty values.
     *
     * @param mixed $value Raw value.
     * @return array<int, string>
     */
    private function normalise_string_list($value): array {
        if ($value === null || $value === '') {
            return [];
        }

        if (!is_array($value)) {
            $value = [$value];
        }

        $out = [];
        foreach ($value as $item) {
            $item = clean_param(trim((string)$item), PARAM_ALPHANUMEXT);
            if ($item !== '' && $item !== 'all') {
                $out[] = $item;
            }
        }

        return array_values(array_unique($out));
    }

    /**
     * Normalise page.
     *
     * @param mixed $page Raw page.
     * @return int
     */
    private function normalise_page($page): int {
        $page = (int)$page;

        return max(1, $page);
    }

    /**
     * Normalise page size.
     *
     * @param mixed $perpage Raw perpage.
     * @return int
     */
    private function normalise_perpage($perpage): int {
        $perpage = (int)$perpage;
        if ($perpage <= 0) {
            return self::DEFAULT_PERPAGE;
        }

        return min($perpage, self::MAX_PERPAGE);
    }

    /**
     * Return a short display label for a stored enum value.
     *
     * @param string $value Stored value.
     * @return string
     */
    private function label(string $value): string {
        $value = trim($value);
        if ($value === '') {
            return '';
        }

        return format_string(str_replace('_', ' ', $value));
    }

    /**
     * Truncate text safely.
     *
     * @param string $value Text.
     * @param int $maxlength Maximum length.
     * @return string
     */
    private function truncate(string $value, int $maxlength): string {
        $value = trim($value);
        if ($value === '') {
            return '';
        }

        if (\core_text::strlen($value) <= $maxlength) {
            return $value;
        }

        return \core_text::substr($value, 0, max(0, $maxlength - 1)) . '…';
    }

    /**
     * Require media table to exist.
     *
     * @return void
     */
    private function require_media_table(): void {
        if (!$this->table_exists(self::TABLE_MEDIA)) {
            throw new coding_exception('Public Médiathèque requires table ' . self::TABLE_MEDIA . '.');
        }
    }

    /**
     * Check table existence.
     *
     * @param string $table Table name without prefix.
     * @return bool
     */
    private function table_exists(string $table): bool {
        global $DB;

        return $DB->get_manager()->table_exists(new xmldb_table($table));
    }
}
