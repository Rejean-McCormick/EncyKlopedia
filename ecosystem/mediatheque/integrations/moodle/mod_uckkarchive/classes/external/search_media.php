<?php
// This file is part of Moodle - https://moodle.org/
//
// Moodle is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// any later version.

/**
 * External service: search media.
 *
 * @package    mod_uckkarchive
 * @copyright  2026 Univers-Cité King Klown
 * @license    https://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later
 */

namespace mod_uckkarchive\external;

defined('MOODLE_INTERNAL') || die();

use context_module;
use invalid_parameter_exception;
use mod_uckkarchive\local\media_tag;
use stdClass;

/**
 * Searches the UCKK Archive media library.
 *
 * This endpoint is intended for AJAX and external-service consumers.
 *
 * It performs Moodle-native security checks:
 *
 * - resolves the course module context;
 * - requires login;
 * - validates context;
 * - requires mod/uckkarchive:viewmedia;
 * - requires mod/uckkarchive:viewrestrictedmedia before restricted media is included.
 *
 * It does not expose content advisory or cultural protocol details. Those are
 * handled by dedicated content advisory services.
 */
class search_media extends \external_api {
    /** @var int Default result limit. */
    private const DEFAULT_LIMIT = 20;

    /** @var int Maximum result limit. */
    private const MAX_LIMIT = 100;

    /** @var string Default sort field. */
    private const DEFAULT_SORT = 'timemodified';

    /** @var string Default sort direction. */
    private const DEFAULT_DIRECTION = 'DESC';

    /** @var string Media table. */
    private const MEDIA_TABLE = 'uckkarchive_media';

    /** @var string Media tag table. */
    private const MEDIA_TAG_TABLE = 'uckkarchive_media_tag';

    /** @var string Media collection item table. */
    private const COLLECTION_ITEM_TABLE = 'uckkarchive_media_collection_item';

    /** @var string Media version table. */
    private const MEDIA_VERSION_TABLE = 'uckkarchive_media_version';

    /**
     * Returns service parameters.
     *
     * @return \external_function_parameters
     */
    public static function execute_parameters(): \external_function_parameters {
        return new \external_function_parameters([
            'cmid' => new \external_value(PARAM_INT, 'Course module id.'),
            'query' => new \external_value(PARAM_RAW, 'Search text.', VALUE_DEFAULT, ''),
            'mediatype' => new \external_value(PARAM_ALPHANUMEXT, 'Optional media type filter.', VALUE_DEFAULT, ''),
            'status' => new \external_value(PARAM_ALPHANUMEXT, 'Optional status filter.', VALUE_DEFAULT, 'active'),
            'visibility' => new \external_value(PARAM_ALPHANUMEXT, 'Optional visibility filter.', VALUE_DEFAULT, ''),
            'audiencesuitability' => new \external_value(
                PARAM_ALPHANUMEXT,
                'Optional audience suitability filter.',
                VALUE_DEFAULT,
                ''
            ),
            'sourceid' => new \external_value(PARAM_INT, 'Optional media source id filter.', VALUE_DEFAULT, 0),
            'collectionid' => new \external_value(PARAM_INT, 'Optional collection id filter.', VALUE_DEFAULT, 0),
            'tagkeys' => new \external_value(
                PARAM_RAW,
                'Optional comma-separated ordinary media tag keys.',
                VALUE_DEFAULT,
                ''
            ),
            'includerestricted' => new \external_value(
                PARAM_BOOL,
                'Whether restricted media may be included. Requires restricted-media capability.',
                VALUE_DEFAULT,
                false
            ),
            'limit' => new \external_value(PARAM_INT, 'Maximum number of records.', VALUE_DEFAULT, self::DEFAULT_LIMIT),
            'offset' => new \external_value(PARAM_INT, 'Offset for pagination.', VALUE_DEFAULT, 0),
            'sort' => new \external_value(PARAM_ALPHANUMEXT, 'Sort field.', VALUE_DEFAULT, self::DEFAULT_SORT),
            'direction' => new \external_value(PARAM_ALPHA, 'Sort direction: ASC or DESC.', VALUE_DEFAULT, self::DEFAULT_DIRECTION),
        ]);
    }

    /**
     * Execute media search.
     *
     * @param int $cmid Course module id.
     * @param string $query Search text.
     * @param string $mediatype Media type filter.
     * @param string $status Status filter.
     * @param string $visibility Visibility filter.
     * @param string $audiencesuitability Audience suitability filter.
     * @param int $sourceid Media source id filter.
     * @param int $collectionid Collection id filter.
     * @param string $tagkeys Comma-separated media tag keys.
     * @param bool $includerestricted Include restricted media.
     * @param int $limit Result limit.
     * @param int $offset Result offset.
     * @param string $sort Sort field.
     * @param string $direction Sort direction.
     * @return array
     */
    public static function execute(
        int $cmid,
        string $query = '',
        string $mediatype = '',
        string $status = 'active',
        string $visibility = '',
        string $audiencesuitability = '',
        int $sourceid = 0,
        int $collectionid = 0,
        string $tagkeys = '',
        bool $includerestricted = false,
        int $limit = self::DEFAULT_LIMIT,
        int $offset = 0,
        string $sort = self::DEFAULT_SORT,
        string $direction = self::DEFAULT_DIRECTION
    ): array {
        global $DB;

        $params = self::validate_parameters(self::execute_parameters(), [
            'cmid' => $cmid,
            'query' => $query,
            'mediatype' => $mediatype,
            'status' => $status,
            'visibility' => $visibility,
            'audiencesuitability' => $audiencesuitability,
            'sourceid' => $sourceid,
            'collectionid' => $collectionid,
            'tagkeys' => $tagkeys,
            'includerestricted' => $includerestricted,
            'limit' => $limit,
            'offset' => $offset,
            'sort' => $sort,
            'direction' => $direction,
        ]);

        [$course, $cm] = get_course_and_cm_from_cmid($params['cmid'], 'uckkarchive');
        $context = context_module::instance($cm->id);

        require_login($course, true, $cm);
        self::validate_context($context);
        require_capability('mod/uckkarchive:viewmedia', $context);

        $canviewrestricted = has_capability('mod/uckkarchive:viewrestrictedmedia', $context);
        $includerestricted = (bool)$params['includerestricted'] && $canviewrestricted;

        $limit = self::normalise_limit((int)$params['limit']);
        $offset = max(0, (int)$params['offset']);
        $sort = self::normalise_sort((string)$params['sort']);
        $direction = self::normalise_direction((string)$params['direction']);
        $tagkeylist = self::normalise_tagkeys((string)$params['tagkeys']);

        $where = ['m.uckkarchiveid = :uckkarchiveid'];
        $sqlparams = ['uckkarchiveid' => (int)$cm->instance];

        self::add_text_search_clause($where, $sqlparams, trim((string)$params['query']));
        self::add_exact_clause($where, $sqlparams, 'm.mediatype', 'mediatype', (string)$params['mediatype']);
        self::add_exact_clause($where, $sqlparams, 'm.status', 'status', (string)$params['status']);
        self::add_exact_clause($where, $sqlparams, 'm.visibility', 'visibility', (string)$params['visibility']);
        self::add_exact_clause(
            $where,
            $sqlparams,
            'm.audiencesuitability',
            'audiencesuitability',
            (string)$params['audiencesuitability']
        );

        if ((int)$params['sourceid'] > 0) {
            $where[] = 'm.sourceid = :sourceid';
            $sqlparams['sourceid'] = (int)$params['sourceid'];
        }

        if ((int)$params['collectionid'] > 0) {
            $where[] = 'EXISTS (
                SELECT 1
                  FROM {' . self::COLLECTION_ITEM_TABLE . '} ci
                 WHERE ci.mediaid = m.id
                   AND ci.collectionid = :collectionid
            )';
            $sqlparams['collectionid'] = (int)$params['collectionid'];
        }

        if (!empty($tagkeylist)) {
            self::add_tag_filter_clause($where, $sqlparams, $tagkeylist);
        }

        if (!$includerestricted) {
            $where[] = "m.status <> 'restricted'";
            $where[] = "m.visibility NOT IN ('restricted', 'restricted_integrity', 'restricted_cultural')";
        }

        $wheresql = implode("\n AND ", $where);

        $countsql = 'SELECT COUNT(1)
                       FROM {' . self::MEDIA_TABLE . '} m
                      WHERE ' . $wheresql;

        $total = (int)$DB->count_records_sql($countsql, $sqlparams);

        $sql = 'SELECT m.*
                  FROM {' . self::MEDIA_TABLE . '} m
                 WHERE ' . $wheresql . '
              ORDER BY ' . $sort . ' ' . $direction . ', m.id DESC';

        $records = $DB->get_records_sql($sql, $sqlparams, $offset, $limit);

        $items = [];
        foreach ($records as $record) {
            $items[] = self::format_media_record($record, $context, $canviewrestricted);
        }

        $result = [
            'cmid' => (int)$cm->id,
            'contextid' => (int)$context->id,
            'total' => $total,
            'limit' => $limit,
            'offset' => $offset,
            'hasmore' => ($offset + count($items)) < $total,
            'canviewrestricted' => $canviewrestricted,
            'items' => $items,
            'warnings' => [],
        ];

        return self::clean_returnvalue(self::execute_returns(), $result);
    }

    /**
     * Returns service response structure.
     *
     * @return \external_single_structure
     */
    public static function execute_returns(): \external_single_structure {
        return new \external_single_structure([
            'cmid' => new \external_value(PARAM_INT, 'Course module id.'),
            'contextid' => new \external_value(PARAM_INT, 'Context id.'),
            'total' => new \external_value(PARAM_INT, 'Total matching records.'),
            'limit' => new \external_value(PARAM_INT, 'Returned result limit.'),
            'offset' => new \external_value(PARAM_INT, 'Returned result offset.'),
            'hasmore' => new \external_value(PARAM_BOOL, 'Whether additional records exist.'),
            'canviewrestricted' => new \external_value(PARAM_BOOL, 'Whether the current user can view restricted media.'),
            'items' => new \external_multiple_structure(self::media_return_structure(), 'Media results.'),
            'warnings' => new \external_multiple_structure(
                new \external_single_structure([
                    'code' => new \external_value(PARAM_ALPHANUMEXT, 'Warning code.'),
                    'message' => new \external_value(PARAM_TEXT, 'Warning message.'),
                ]),
                'Warnings.',
                VALUE_DEFAULT,
                []
            ),
        ]);
    }

    /**
     * Media return structure.
     *
     * @return \external_single_structure
     */
    protected static function media_return_structure(): \external_single_structure {
        return new \external_single_structure([
            'id' => new \external_value(PARAM_INT, 'Media id.'),
            'uuid' => new \external_value(PARAM_RAW, 'Media UUID.'),
            'title' => new \external_value(PARAM_TEXT, 'Media title.'),
            'description' => new \external_value(PARAM_RAW, 'Media description.'),
            'mediatype' => new \external_value(PARAM_ALPHANUMEXT, 'Media type.'),
            'mimetype' => new \external_value(PARAM_RAW, 'MIME type.'),
            'status' => new \external_value(PARAM_ALPHANUMEXT, 'Media lifecycle status.'),
            'visibility' => new \external_value(PARAM_ALPHANUMEXT, 'Visibility value.'),
            'audiencesuitability' => new \external_value(PARAM_ALPHANUMEXT, 'Audience suitability.'),
            'sourceid' => new \external_value(PARAM_INT, 'Media source id.'),
            'currentversionid' => new \external_value(PARAM_INT, 'Current media version id.'),
            'filename' => new \external_value(PARAM_FILE, 'Current version filename.', VALUE_DEFAULT, ''),
            'filesize' => new \external_value(PARAM_INT, 'Current version file size.', VALUE_DEFAULT, 0),
            'filehash' => new \external_value(PARAM_RAW, 'Current version file hash.', VALUE_DEFAULT, ''),
            'timecreated' => new \external_value(PARAM_INT, 'Time created.'),
            'timemodified' => new \external_value(PARAM_INT, 'Time modified.'),
            'createdby' => new \external_value(PARAM_INT, 'Creator user id.'),
            'modifiedby' => new \external_value(PARAM_INT, 'Modifier user id.'),
            'tags' => new \external_multiple_structure(
                new \external_single_structure([
                    'id' => new \external_value(PARAM_INT, 'Tag id.'),
                    'uuid' => new \external_value(PARAM_RAW, 'Tag UUID.'),
                    'tagkey' => new \external_value(PARAM_ALPHANUMEXT, 'Tag key.'),
                    'label' => new \external_value(PARAM_TEXT, 'Tag label.'),
                    'tagtype' => new \external_value(PARAM_ALPHANUMEXT, 'Tag type.'),
                    'source' => new \external_value(PARAM_ALPHANUMEXT, 'Tag source.'),
                    'weight' => new \external_value(PARAM_INT, 'Tag weight.'),
                ]),
                'Ordinary media tags.'
            ),
            'restricted' => new \external_value(PARAM_BOOL, 'Whether record is restricted.'),
        ]);
    }

    /**
     * Format one media record for external return.
     *
     * @param stdClass $record Media record.
     * @param context_module $context Context.
     * @param bool $canviewrestricted Whether current user can view restricted records.
     * @return array
     */
    protected static function format_media_record(stdClass $record, context_module $context, bool $canviewrestricted): array {
        global $DB;

        $version = null;
        if (!empty($record->currentversionid)) {
            $version = $DB->get_record(self::MEDIA_VERSION_TABLE, ['id' => (int)$record->currentversionid]);
        }

        $restricted = self::is_restricted_record($record);

        if ($restricted && !$canviewrestricted) {
            return [
                'id' => (int)$record->id,
                'uuid' => (string)($record->uuid ?? ''),
                'title' => get_string('restrictedmedia', 'uckkarchive'),
                'description' => '',
                'mediatype' => (string)($record->mediatype ?? ''),
                'mimetype' => '',
                'status' => (string)($record->status ?? ''),
                'visibility' => (string)($record->visibility ?? ''),
                'audiencesuitability' => (string)($record->audiencesuitability ?? ''),
                'sourceid' => 0,
                'currentversionid' => 0,
                'filename' => '',
                'filesize' => 0,
                'filehash' => '',
                'timecreated' => 0,
                'timemodified' => 0,
                'createdby' => 0,
                'modifiedby' => 0,
                'tags' => [],
                'restricted' => true,
            ];
        }

        return [
            'id' => (int)$record->id,
            'uuid' => (string)($record->uuid ?? ''),
            'title' => format_string((string)($record->title ?? ''), true, ['context' => $context]),
            'description' => self::format_description((string)($record->description ?? ''), $context),
            'mediatype' => (string)($record->mediatype ?? ''),
            'mimetype' => (string)($record->mimetype ?? ''),
            'status' => (string)($record->status ?? ''),
            'visibility' => (string)($record->visibility ?? ''),
            'audiencesuitability' => (string)($record->audiencesuitability ?? ''),
            'sourceid' => (int)($record->sourceid ?? 0),
            'currentversionid' => (int)($record->currentversionid ?? 0),
            'filename' => $version ? (string)($version->filename ?? '') : '',
            'filesize' => $version ? (int)($version->filesize ?? 0) : 0,
            'filehash' => $version ? (string)($version->filehash ?? '') : '',
            'timecreated' => (int)($record->timecreated ?? 0),
            'timemodified' => (int)($record->timemodified ?? 0),
            'createdby' => (int)($record->createdby ?? 0),
            'modifiedby' => (int)($record->modifiedby ?? 0),
            'tags' => self::format_tags((int)$record->id),
            'restricted' => $restricted,
        ];
    }

    /**
     * Format media description.
     *
     * @param string $description Description.
     * @param context_module $context Context.
     * @return string
     */
    protected static function format_description(string $description, context_module $context): string {
        if ($description === '') {
            return '';
        }

        return format_text($description, FORMAT_HTML, [
            'context' => $context,
            'filter' => true,
            'para' => false,
        ]);
    }

    /**
     * Format ordinary media tags.
     *
     * @param int $mediaid Media id.
     * @return array
     */
    protected static function format_tags(int $mediaid): array {
        global $DB;

        $records = $DB->get_records(
            self::MEDIA_TAG_TABLE,
            ['mediaid' => $mediaid],
            'weight DESC, tagtype ASC, label ASC, tagkey ASC'
        );

        $tags = [];
        foreach ($records as $record) {
            $tags[] = [
                'id' => (int)$record->id,
                'uuid' => (string)($record->uuid ?? ''),
                'tagkey' => (string)($record->tagkey ?? ''),
                'label' => (string)($record->label ?? ''),
                'tagtype' => (string)($record->tagtype ?? ''),
                'source' => (string)($record->source ?? ''),
                'weight' => (int)($record->weight ?? 0),
            ];
        }

        return $tags;
    }

    /**
     * Add text search clause.
     *
     * @param array $where SQL where clauses.
     * @param array $params SQL parameters.
     * @param string $query Query text.
     */
    protected static function add_text_search_clause(array &$where, array &$params, string $query): void {
        global $DB;

        if ($query === '') {
            return;
        }

        $params['querytitle'] = '%' . $DB->sql_like_escape($query) . '%';
        $params['querydesc'] = '%' . $DB->sql_like_escape($query) . '%';
        $params['querymeta'] = '%' . $DB->sql_like_escape($query) . '%';

        $where[] = '(' .
            $DB->sql_like('m.title', ':querytitle', false) .
            ' OR ' .
            $DB->sql_like('m.description', ':querydesc', false) .
            ' OR ' .
            $DB->sql_like('m.metadata', ':querymeta', false) .
        ')';
    }

    /**
     * Add an exact string clause when value is not empty.
     *
     * @param array $where SQL where clauses.
     * @param array $params SQL params.
     * @param string $field SQL field name.
     * @param string $paramname SQL param name.
     * @param string $value Value.
     */
    protected static function add_exact_clause(
        array &$where,
        array &$params,
        string $field,
        string $paramname,
        string $value
    ): void {
        $value = trim($value);

        if ($value === '') {
            return;
        }

        $where[] = $field . ' = :' . $paramname;
        $params[$paramname] = $value;
    }

    /**
     * Add tag filtering clause.
     *
     * All requested tags must be present.
     *
     * @param array $where SQL where clauses.
     * @param array $params SQL params.
     * @param string[] $tagkeylist Normalized tag keys.
     */
    protected static function add_tag_filter_clause(array &$where, array &$params, array $tagkeylist): void {
        foreach ($tagkeylist as $index => $tagkey) {
            $param = 'tagkey' . $index;
            $where[] = 'EXISTS (
                SELECT 1
                  FROM {' . self::MEDIA_TAG_TABLE . '} mt' . $index . '
                 WHERE mt' . $index . '.mediaid = m.id
                   AND mt' . $index . '.tagkey = :' . $param . '
            )';
            $params[$param] = $tagkey;
        }
    }

    /**
     * Normalize tag keys.
     *
     * @param string $tagkeys Comma-separated keys.
     * @return string[]
     */
    protected static function normalise_tagkeys(string $tagkeys): array {
        if (trim($tagkeys) === '') {
            return [];
        }

        $parts = preg_split('/\s*,\s*/', trim($tagkeys));
        $keys = [];

        foreach ($parts as $part) {
            if ($part === '') {
                continue;
            }

            if (class_exists(media_tag::class)) {
                $key = media_tag::normalise_key($part);
                if ($key !== '' && !media_tag::is_content_advisory_key($key)) {
                    $keys[$key] = $key;
                }
                continue;
            }

            $key = strtolower(trim($part));
            $key = preg_replace('/[^a-z0-9_-]+/', '_', $key);
            $key = trim($key, '_-');

            if ($key !== '') {
                $keys[$key] = $key;
            }
        }

        return array_values($keys);
    }

    /**
     * Normalize limit.
     *
     * @param int $limit Limit.
     * @return int
     */
    protected static function normalise_limit(int $limit): int {
        if ($limit <= 0) {
            return self::DEFAULT_LIMIT;
        }

        return min($limit, self::MAX_LIMIT);
    }

    /**
     * Normalize sort field to a safe SQL expression.
     *
     * @param string $sort Sort field.
     * @return string SQL field.
     */
    protected static function normalise_sort(string $sort): string {
        $allowed = [
            'id' => 'm.id',
            'title' => 'm.title',
            'mediatype' => 'm.mediatype',
            'status' => 'm.status',
            'visibility' => 'm.visibility',
            'timecreated' => 'm.timecreated',
            'timemodified' => 'm.timemodified',
        ];

        $sort = strtolower(trim($sort));

        return $allowed[$sort] ?? $allowed[self::DEFAULT_SORT];
    }

    /**
     * Normalize sort direction.
     *
     * @param string $direction Direction.
     * @return string ASC or DESC.
     */
    protected static function normalise_direction(string $direction): string {
        $direction = strtoupper(trim($direction));

        return $direction === 'ASC' ? 'ASC' : 'DESC';
    }

    /**
     * Return whether a media record is restricted.
     *
     * @param stdClass $record Media record.
     * @return bool
     */
    protected static function is_restricted_record(stdClass $record): bool {
        $status = (string)($record->status ?? '');
        $visibility = (string)($record->visibility ?? '');

        return $status === 'restricted' ||
            in_array($visibility, ['restricted', 'restricted_integrity', 'restricted_cultural'], true);
    }
}
