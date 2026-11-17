<?php
// This file is part of Moodle - https://moodle.org/.
//
// Moodle is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// any later version.

/**
 * Public Médiathèque search endpoint.
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
require_once(dirname(__DIR__) . '/local/public_mediatheque_service.php');

use core_external\external_api;
use core_external\external_function_parameters;
use core_external\external_multiple_structure;
use core_external\external_single_structure;
use core_external\external_value;
use mod_uckkarchive\local\public_mediatheque_service;

/**
 * Search the public Médiathèque.
 *
 * Target AJAX service:
 *
 * ```text
 * mod_uckkarchive_search_mediatheque
 * ```
 *
 * This endpoint is intentionally a thin public façade. It validates public
 * request parameters, delegates all archive/media/content-policy decisions to
 * {@see public_mediatheque_service}, and returns only permission-filtered DTOs.
 *
 * It must not:
 * - expose raw media records;
 * - expose direct original-file URLs;
 * - expose private review notes;
 * - expose restricted cultural protocol notes;
 * - decide access in JavaScript or templates;
 * - duplicate the internal media library search engine.
 */
final class search_mediatheque extends external_api {
    /** Default page size. */
    private const DEFAULT_PERPAGE = 12;

    /** Maximum public page size. */
    private const MAX_PERPAGE = 48;

    /**
     * Define service parameters.
     *
     * @return external_function_parameters
     */
    public static function execute_parameters(): external_function_parameters {
        return new external_function_parameters([
            'cmid' => new external_value(
                PARAM_INT,
                'Optional UCKK Archive course module id. Use 0 for site-level public discovery.',
                VALUE_DEFAULT,
                0
            ),
            'archiveid' => new external_value(
                PARAM_INT,
                'Optional UCKK Archive instance id. Use 0 when cmid is supplied or when searching public site scope.',
                VALUE_DEFAULT,
                0
            ),
            'query' => new external_value(
                PARAM_RAW,
                'Free-text public search query.',
                VALUE_DEFAULT,
                ''
            ),
            'filters' => new external_single_structure([
                'type' => new external_value(
                    PARAM_ALPHANUMEXT,
                    'Object type: all, media, collection, external_work, archive_item, or content_marker.',
                    VALUE_DEFAULT,
                    'all'
                ),
                'mediatype' => new external_value(
                    PARAM_ALPHANUMEXT,
                    'Media type filter.',
                    VALUE_DEFAULT,
                    'all'
                ),
                'collection' => new external_value(
                    PARAM_TEXT,
                    'Collection UUID or empty string.',
                    VALUE_DEFAULT,
                    ''
                ),
                'tag' => new external_value(
                    PARAM_TAG,
                    'Public tag key or empty string.',
                    VALUE_DEFAULT,
                    ''
                ),
                'source' => new external_value(
                    PARAM_ALPHANUMEXT,
                    'Source filter.',
                    VALUE_DEFAULT,
                    ''
                ),
                'advisory' => new external_value(
                    PARAM_ALPHANUMEXT,
                    'Advisory filter: all, none, has_advisory, or has_public_advisory.',
                    VALUE_DEFAULT,
                    'all'
                ),
                'cultural' => new external_value(
                    PARAM_ALPHANUMEXT,
                    'Cultural protocol filter: all, none, or has_public_protocol.',
                    VALUE_DEFAULT,
                    'all'
                ),
                'audience' => new external_value(
                    PARAM_ALPHANUMEXT,
                    'Audience filter: all, general, guided, mature, or restricted.',
                    VALUE_DEFAULT,
                    'all'
                ),
                'lang' => new external_value(
                    PARAM_LANG,
                    'Language code or empty string.',
                    VALUE_DEFAULT,
                    ''
                ),
                'validation' => new external_value(
                    PARAM_ALPHANUMEXT,
                    'Validation filter: all, human_reviewed, verified, or archived.',
                    VALUE_DEFAULT,
                    'all'
                ),
            ], 'Public Médiathèque filters.', VALUE_DEFAULT, []),
            'page' => new external_value(
                PARAM_INT,
                'One-based page number.',
                VALUE_DEFAULT,
                1
            ),
            'perpage' => new external_value(
                PARAM_INT,
                'Items per page.',
                VALUE_DEFAULT,
                self::DEFAULT_PERPAGE
            ),
            'sort' => new external_value(
                PARAM_ALPHANUMEXT,
                'Sort: relevance, newest, title, type, collection, or validated.',
                VALUE_DEFAULT,
                'relevance'
            ),
            'sitekey' => new external_value(
                PARAM_ALPHANUMEXT,
                'Public Univers-Cité site key used to resolve its primary media library.',
                VALUE_DEFAULT,
                'uckk'
            ),
        ]);
    }

    /**
     * Execute public Médiathèque search.
     *
     * `cmid = 0` and `archiveid = 0` is valid and means site-wide public discovery.
     *
     * @param int $cmid Optional course module id.
     * @param int $archiveid Optional archive instance id.
     * @param string $query Search query.
     * @param array<string, mixed> $filters Public filters.
     * @param int $page Page number.
     * @param int $perpage Page size.
     * @param string $sort Sort key.
     * @return array<string, mixed>
     */
    public static function execute(
        int $cmid = 0,
        int $archiveid = 0,
        string $query = '',
        array $filters = [],
        int $page = 1,
        int $perpage = self::DEFAULT_PERPAGE,
        string $sort = 'relevance',
        string $sitekey = 'uckk'
    ): array {
        global $USER;

        $params = self::validate_parameters(self::execute_parameters(), [
            'cmid' => $cmid,
            'archiveid' => $archiveid,
            'query' => $query,
            'filters' => $filters,
            'page' => $page,
            'perpage' => $perpage,
            'sort' => $sort,
            'sitekey' => $sitekey,
        ]);

        $cmid = max(0, (int)$params['cmid']);
        $archiveid = max(0, (int)$params['archiveid']);
        $page = max(1, (int)$params['page']);
        $perpage = max(1, min(self::MAX_PERPAGE, (int)$params['perpage']));
        $query = trim((string)$params['query']);
        $sort = self::clean_sort((string)$params['sort']);
        $sitekey = clean_param(strtolower(trim((string)$params['sitekey'])), PARAM_ALPHANUMEXT);
        if ($sitekey === '') {
            $sitekey = 'uckk';
        }
        $filters = self::clean_filters((array)$params['filters']);

        $request = [
            'cmid' => $cmid,
            'archiveid' => $archiveid,
            'q' => $query,
            'query' => $query,
            'type' => $filters['type'],
            'mediatype' => $filters['mediatype'],
            'collection' => $filters['collection'],
            'tag' => $filters['tag'],
            'source' => $filters['source'],
            'advisory' => $filters['advisory'],
            'cultural' => $filters['cultural'],
            'audience' => $filters['audience'],
            'lang' => $filters['lang'],
            'validation' => $filters['validation'],
            'page' => $page,
            'perpage' => $perpage,
            'sort' => $sort,
            'sitekey' => $sitekey,
        ];

        $service = new public_mediatheque_service();
        $response = $service->search($request, null, $USER);

        return self::normalise_response($response, $request);
    }

    /**
     * Define service return structure.
     *
     * @return external_single_structure
     */
    public static function execute_returns(): external_single_structure {
        return new external_single_structure([
            'context' => new external_single_structure([
                'component' => new external_value(PARAM_COMPONENT, 'Owning data component.'),
                'surface' => new external_value(PARAM_COMPONENT, 'Rendering surface component.'),
                'page' => new external_value(PARAM_ALPHANUMEXT, 'Public page key.'),
                'explorer' => new external_value(PARAM_ALPHANUMEXT, 'Explorer component key.'),
                'anonymous' => new external_value(PARAM_BOOL, 'Whether the response was built for an anonymous/guest context.'),
                'policyfiltered' => new external_value(PARAM_BOOL, 'Whether the response was policy-filtered.'),
                'sitekey' => new external_value(PARAM_ALPHANUMEXT, 'Resolved public site key.', VALUE_DEFAULT, 'uckk'),
                'libraryslug' => new external_value(PARAM_ALPHANUMEXT, 'Resolved primary library slug.', VALUE_DEFAULT, ''),
                'libraryname' => new external_value(PARAM_TEXT, 'Resolved primary library name.', VALUE_DEFAULT, ''),
            ]),
            'filters' => new external_single_structure([
                'sitekey' => new external_value(PARAM_ALPHANUMEXT, 'Applied public site key.', VALUE_DEFAULT, 'uckk'),
                'q' => new external_value(PARAM_RAW, 'Applied query.'),
                'query' => new external_value(PARAM_RAW, 'Applied query alias.'),
                'type' => new external_value(PARAM_ALPHANUMEXT, 'Applied object type filter.'),
                'mediatype' => new external_value(PARAM_ALPHANUMEXT, 'Applied media type filter.'),
                'collection' => new external_value(PARAM_TEXT, 'Applied collection UUID.'),
                'tag' => new external_value(PARAM_TAG, 'Applied tag key.'),
                'source' => new external_value(PARAM_ALPHANUMEXT, 'Applied source filter.'),
                'advisory' => new external_value(PARAM_ALPHANUMEXT, 'Applied advisory filter.'),
                'cultural' => new external_value(PARAM_ALPHANUMEXT, 'Applied cultural protocol filter.'),
                'audience' => new external_value(PARAM_ALPHANUMEXT, 'Applied audience filter.'),
                'lang' => new external_value(PARAM_LANG, 'Applied language filter.'),
                'validation' => new external_value(PARAM_ALPHANUMEXT, 'Applied validation filter.'),
                'sort' => new external_value(PARAM_ALPHANUMEXT, 'Applied sort key.'),
                'page' => new external_value(PARAM_INT, 'Applied page.'),
                'perpage' => new external_value(PARAM_INT, 'Applied page size.'),
            ]),
            'facets' => new external_multiple_structure(
                new external_single_structure([
                    'key' => new external_value(PARAM_ALPHANUMEXT, 'Facet key.'),
                    'label' => new external_value(PARAM_TEXT, 'Facet label.'),
                    'items' => new external_multiple_structure(
                        new external_single_structure([
                            'value' => new external_value(PARAM_TEXT, 'Facet value.'),
                            'label' => new external_value(PARAM_TEXT, 'Facet value label.'),
                            'count' => new external_value(PARAM_INT, 'Visible result count.'),
                            'active' => new external_value(PARAM_BOOL, 'Whether this facet value is active.'),
                        ])
                    ),
                ])
            ),
            'items' => new external_multiple_structure(self::item_structure()),
            'pagination' => new external_single_structure([
                'page' => new external_value(PARAM_INT, 'Current page.'),
                'perpage' => new external_value(PARAM_INT, 'Items per page.'),
                'total' => new external_value(PARAM_INT, 'Total visible items.'),
                'hasmore' => new external_value(PARAM_BOOL, 'Whether more results exist.'),
            ]),
            'notices' => new external_multiple_structure(
                new external_single_structure([
                    'type' => new external_value(PARAM_ALPHANUMEXT, 'Notice type.'),
                    'code' => new external_value(PARAM_ALPHANUMEXT, 'Notice code.'),
                    'message' => new external_value(PARAM_TEXT, 'Notice message.'),
                ])
            ),
            'warnings' => new external_multiple_structure(
                new external_single_structure([
                    'item' => new external_value(PARAM_ALPHANUMEXT, 'Warning item.', VALUE_DEFAULT, 'mediatheque'),
                    'itemid' => new external_value(PARAM_TEXT, 'Warning item id.', VALUE_DEFAULT, '0'),
                    'warningcode' => new external_value(PARAM_ALPHANUMEXT, 'Warning code.'),
                    'message' => new external_value(PARAM_TEXT, 'Warning message.'),
                ])
            ),
            'empty' => new external_single_structure([
                'isempty' => new external_value(PARAM_BOOL, 'Whether no visible results matched.'),
                'message' => new external_value(PARAM_TEXT, 'Empty-state message.'),
            ]),
        ]);
    }

    /**
     * Public item DTO structure.
     *
     * @return external_single_structure
     */
    private static function item_structure(): external_single_structure {
        return new external_single_structure([
            'uuid' => new external_value(PARAM_TEXT, 'Public object UUID.'),
            'objecttype' => new external_value(
                PARAM_ALPHANUMEXT,
                'Object type: media, collection, external_work, archive_item, or content_marker.'
            ),
            'title' => new external_value(PARAM_TEXT, 'Public title.'),
            'subtitle' => new external_value(PARAM_TEXT, 'Public subtitle.', VALUE_DEFAULT, ''),
            'summary' => new external_value(PARAM_RAW, 'Public summary.', VALUE_DEFAULT, ''),
            'mediatype' => new external_value(PARAM_ALPHANUMEXT, 'Media type.', VALUE_DEFAULT, ''),
            'mimetype' => new external_value(PARAM_TEXT, 'MIME type.', VALUE_DEFAULT, ''),
            'language' => new external_value(PARAM_LANG, 'Language code.', VALUE_DEFAULT, ''),
            'thumbnailurl' => new external_value(PARAM_URL, 'Authorised thumbnail URL.', VALUE_DEFAULT, ''),
            'detailurl' => new external_value(PARAM_LOCALURL, 'Public detail URL.', VALUE_DEFAULT, ''),
            'library' => new external_single_structure([
                'slug' => new external_value(PARAM_ALPHANUMEXT, 'Home library slug.', VALUE_DEFAULT, ''),
                'name' => new external_value(PARAM_TEXT, 'Home library name.', VALUE_DEFAULT, ''),
                'isbridged' => new external_value(PARAM_BOOL, 'Whether this item is visible through a bridge.'),
                'bridgescope' => new external_value(PARAM_ALPHANUMEXT, 'Bridge scope: library, collection, media, or empty.', VALUE_DEFAULT, ''),
                'bridgelabel' => new external_value(PARAM_TEXT, 'Optional bridge label.', VALUE_DEFAULT, ''),
            ]),
            'source' => new external_single_structure([
                'value' => new external_value(PARAM_ALPHANUMEXT, 'Source value.', VALUE_DEFAULT, ''),
                'label' => new external_value(PARAM_TEXT, 'Source label.', VALUE_DEFAULT, ''),
            ]),
            'rights' => new external_single_structure([
                'license' => new external_value(PARAM_TEXT, 'Public licence key.', VALUE_DEFAULT, ''),
                'rightsstatement' => new external_value(PARAM_RAW, 'Public rights statement.', VALUE_DEFAULT, ''),
                'copyallowed' => new external_value(PARAM_BOOL, 'Whether public copying is allowed.'),
            ]),
            'status' => new external_single_structure([
                'value' => new external_value(PARAM_ALPHANUMEXT, 'Public status value.'),
                'label' => new external_value(PARAM_TEXT, 'Public status label.'),
            ]),
            'visibility' => new external_single_structure([
                'value' => new external_value(PARAM_ALPHANUMEXT, 'Public visibility value.'),
                'label' => new external_value(PARAM_TEXT, 'Public visibility label.'),
            ]),
            'validation' => new external_single_structure([
                'value' => new external_value(PARAM_ALPHANUMEXT, 'Public validation value.', VALUE_DEFAULT, ''),
                'label' => new external_value(PARAM_TEXT, 'Public validation label.', VALUE_DEFAULT, ''),
            ]),
            'badges' => new external_multiple_structure(
                new external_single_structure([
                    'key' => new external_value(PARAM_ALPHANUMEXT, 'Badge key.'),
                    'label' => new external_value(PARAM_TEXT, 'Badge label.'),
                    'type' => new external_value(PARAM_ALPHANUMEXT, 'Badge type.'),
                ])
            ),
            'advisories' => new external_single_structure([
                'haspublicadvisory' => new external_value(PARAM_BOOL, 'Whether a public advisory summary is visible.'),
                'summary' => new external_value(PARAM_RAW, 'Public advisory summary.', VALUE_DEFAULT, ''),
            ]),
            'culturalprotocol' => new external_single_structure([
                'haspublicprotocol' => new external_value(PARAM_BOOL, 'Whether a public cultural protocol summary is visible.'),
                'summary' => new external_value(PARAM_RAW, 'Public cultural protocol summary.', VALUE_DEFAULT, ''),
            ]),
            'relations' => new external_single_structure([
                'collectioncount' => new external_value(PARAM_INT, 'Visible collection count.'),
                'markercount' => new external_value(PARAM_INT, 'Visible marker count.'),
                'externalworkcount' => new external_value(PARAM_INT, 'Visible external work count.'),
            ]),
            'actions' => new external_single_structure([
                'canviewdetail' => new external_value(PARAM_BOOL, 'Whether public detail may be opened.'),
                'canviewfile' => new external_value(PARAM_BOOL, 'Whether a file preview may be opened.'),
                'candownload' => new external_value(PARAM_BOOL, 'Whether download is allowed.'),
                'canexport' => new external_value(PARAM_BOOL, 'Whether export is allowed.'),
            ]),
        ]);
    }

    /**
     * Clean filter values.
     *
     * @param array<string, mixed> $filters Raw filters.
     * @return array<string, string>
     */
    private static function clean_filters(array $filters): array {
        $defaults = [
            'type' => 'all',
            'mediatype' => 'all',
            'collection' => '',
            'tag' => '',
            'source' => '',
            'advisory' => 'all',
            'cultural' => 'all',
            'audience' => 'all',
            'lang' => '',
            'validation' => 'all',
        ];

        $filters = array_merge($defaults, $filters);

        $filters['type'] = self::allow_value((string)$filters['type'], [
            'all',
            'media',
            'collection',
            'external_work',
            'archive_item',
            'content_marker',
        ], 'all');

        $filters['advisory'] = self::allow_value((string)$filters['advisory'], [
            'all',
            'none',
            'has_advisory',
            'has_public_advisory',
        ], 'all');

        $filters['cultural'] = self::allow_value((string)$filters['cultural'], [
            'all',
            'none',
            'has_public_protocol',
        ], 'all');

        $filters['audience'] = self::allow_value((string)$filters['audience'], [
            'all',
            'general',
            'guided',
            'mature',
            'restricted',
        ], 'all');

        $filters['validation'] = self::allow_value((string)$filters['validation'], [
            'all',
            'human_reviewed',
            'verified',
            'archived',
        ], 'all');

        $filters['mediatype'] = trim((string)$filters['mediatype']) !== ''
            ? clean_param((string)$filters['mediatype'], PARAM_ALPHANUMEXT)
            : 'all';
        $filters['collection'] = clean_param((string)$filters['collection'], PARAM_TEXT);
        $filters['tag'] = clean_param((string)$filters['tag'], PARAM_TAG);
        $filters['source'] = clean_param((string)$filters['source'], PARAM_ALPHANUMEXT);
        $filters['lang'] = clean_param((string)$filters['lang'], PARAM_LANG);

        return $filters;
    }

    /**
     * Clean sort key.
     *
     * @param string $sort Sort key.
     * @return string
     */
    private static function clean_sort(string $sort): string {
        return self::allow_value($sort, [
            'relevance',
            'newest',
            'title',
            'type',
            'collection',
            'validated',
        ], 'relevance');
    }

    /**
     * Normalise service response to the declared external return shape.
     *
     * @param array<string, mixed> $response Service response.
     * @param array<string, mixed> $request Normalised request.
     * @return array<string, mixed>
     */
    private static function normalise_response(array $response, array $request): array {
        $response['context'] = self::normalise_context($response['context'] ?? []);
        $response['filters'] = self::normalise_applied_filters($response['filters'] ?? [], $request);
        $response['facets'] = self::normalise_facets($response['facets'] ?? []);
        $response['items'] = is_array($response['items'] ?? null) ? array_values($response['items']) : [];
        $response['pagination'] = self::normalise_pagination($response['pagination'] ?? [], $request, count($response['items']));
        $response['notices'] = self::normalise_notices($response['notices'] ?? []);
        $response['warnings'] = self::normalise_warnings($response['warnings'] ?? []);
        $response['empty'] = self::normalise_empty($response['empty'] ?? [], empty($response['items']));

        return $response;
    }

    /**
     * Normalise context block.
     *
     * @param mixed $context Context block.
     * @return array<string, mixed>
     */
    private static function normalise_context($context): array {
        $context = is_array($context) ? $context : (array)$context;

        return [
            'component' => clean_param((string)($context['component'] ?? 'mod_uckkarchive'), PARAM_COMPONENT),
            'surface' => clean_param((string)($context['surface'] ?? 'local_uckk'), PARAM_COMPONENT),
            'page' => clean_param((string)($context['page'] ?? 'mediatheque'), PARAM_ALPHANUMEXT),
            'explorer' => clean_param((string)($context['explorer'] ?? 'mediatheque_explorer'), PARAM_ALPHANUMEXT),
            'anonymous' => !empty($context['anonymous']),
            'policyfiltered' => array_key_exists('policyfiltered', $context) ? !empty($context['policyfiltered']) : true,
            'sitekey' => clean_param((string)($context['sitekey'] ?? 'uckk'), PARAM_ALPHANUMEXT),
            'libraryslug' => clean_param((string)($context['libraryslug'] ?? ''), PARAM_ALPHANUMEXT),
            'libraryname' => (string)($context['libraryname'] ?? ''),
        ];
    }

    /**
     * Normalise applied filters.
     *
     * @param mixed $filters Applied filters.
     * @param array<string, mixed> $request Request defaults.
     * @return array<string, mixed>
     */
    private static function normalise_applied_filters($filters, array $request): array {
        $filters = is_array($filters) ? $filters : (array)$filters;

        $q = (string)($filters['q'] ?? $filters['query'] ?? $request['q'] ?? '');

        return [
            'sitekey' => clean_param((string)($filters['sitekey'] ?? $request['sitekey'] ?? 'uckk'), PARAM_ALPHANUMEXT),
            'q' => $q,
            'query' => $q,
            'type' => (string)($filters['type'] ?? $request['type'] ?? 'all'),
            'mediatype' => (string)($filters['mediatype'] ?? $request['mediatype'] ?? 'all'),
            'collection' => (string)($filters['collection'] ?? $request['collection'] ?? ''),
            'tag' => (string)($filters['tag'] ?? $request['tag'] ?? ''),
            'source' => (string)($filters['source'] ?? $request['source'] ?? ''),
            'advisory' => (string)($filters['advisory'] ?? $request['advisory'] ?? 'all'),
            'cultural' => (string)($filters['cultural'] ?? $request['cultural'] ?? 'all'),
            'audience' => (string)($filters['audience'] ?? $request['audience'] ?? 'all'),
            'lang' => (string)($filters['lang'] ?? $request['lang'] ?? ''),
            'validation' => (string)($filters['validation'] ?? $request['validation'] ?? 'all'),
            'sort' => (string)($filters['sort'] ?? $request['sort'] ?? 'relevance'),
            'page' => (int)($filters['page'] ?? $request['page'] ?? 1),
            'perpage' => (int)($filters['perpage'] ?? $request['perpage'] ?? self::DEFAULT_PERPAGE),
        ];
    }

    /**
     * Normalise public facets.
     *
     * @param mixed $facets Facets.
     * @return array<int, array<string, mixed>>
     */
    private static function normalise_facets($facets): array {
        if (!is_array($facets)) {
            return [];
        }

        $normalised = [];

        foreach ($facets as $facet) {
            $facet = is_array($facet) ? $facet : (array)$facet;
            $items = [];

            foreach ((array)($facet['items'] ?? []) as $item) {
                $item = is_array($item) ? $item : (array)$item;
                $items[] = [
                    'value' => (string)($item['value'] ?? ''),
                    'label' => (string)($item['label'] ?? ''),
                    'count' => (int)($item['count'] ?? 0),
                    'active' => !empty($item['active']),
                ];
            }

            $normalised[] = [
                'key' => clean_param((string)($facet['key'] ?? ''), PARAM_ALPHANUMEXT),
                'label' => (string)($facet['label'] ?? ''),
                'items' => $items,
            ];
        }

        return $normalised;
    }

    /**
     * Normalise pagination.
     *
     * @param mixed $pagination Pagination.
     * @param array<string, mixed> $request Request.
     * @param int $fallbacktotal Fallback total.
     * @return array<string, mixed>
     */
    private static function normalise_pagination($pagination, array $request, int $fallbacktotal): array {
        $pagination = is_array($pagination) ? $pagination : (array)$pagination;

        $page = max(1, (int)($pagination['page'] ?? $request['page'] ?? 1));
        $perpage = max(1, min(self::MAX_PERPAGE, (int)($pagination['perpage'] ?? $request['perpage'] ?? self::DEFAULT_PERPAGE)));
        $total = max(0, (int)($pagination['total'] ?? $fallbacktotal));

        return [
            'page' => $page,
            'perpage' => $perpage,
            'total' => $total,
            'hasmore' => array_key_exists('hasmore', $pagination)
                ? !empty($pagination['hasmore'])
                : (($page * $perpage) < $total),
        ];
    }

    /**
     * Normalise public notices.
     *
     * @param mixed $notices Notices.
     * @return array<int, array<string, string>>
     */
    private static function normalise_notices($notices): array {
        if (!is_array($notices)) {
            return [];
        }

        $normalised = [];

        foreach ($notices as $notice) {
            $notice = is_array($notice) ? $notice : (array)$notice;
            $normalised[] = [
                'type' => clean_param((string)($notice['type'] ?? 'info'), PARAM_ALPHANUMEXT),
                'code' => clean_param((string)($notice['code'] ?? 'notice'), PARAM_ALPHANUMEXT),
                'message' => (string)($notice['message'] ?? ''),
            ];
        }

        return $normalised;
    }

    /**
     * Normalise Moodle-style warnings.
     *
     * @param mixed $warnings Warnings.
     * @return array<int, array<string, string>>
     */
    private static function normalise_warnings($warnings): array {
        if (!is_array($warnings)) {
            return [];
        }

        $normalised = [];

        foreach ($warnings as $warning) {
            $warning = is_array($warning) ? $warning : (array)$warning;
            $normalised[] = [
                'item' => clean_param((string)($warning['item'] ?? 'mediatheque'), PARAM_ALPHANUMEXT),
                'itemid' => (string)($warning['itemid'] ?? '0'),
                'warningcode' => clean_param((string)($warning['warningcode'] ?? 'public_warning'), PARAM_ALPHANUMEXT),
                'message' => (string)($warning['message'] ?? ''),
            ];
        }

        return $normalised;
    }

    /**
     * Normalise empty-state block.
     *
     * @param mixed $empty Empty block.
     * @param bool $isempty Whether items are empty.
     * @return array<string, mixed>
     */
    private static function normalise_empty($empty, bool $isempty): array {
        $empty = is_array($empty) ? $empty : (array)$empty;

        return [
            'isempty' => array_key_exists('isempty', $empty) ? !empty($empty['isempty']) : $isempty,
            'message' => (string)($empty['message'] ?? ''),
        ];
    }

    /**
     * Restrict a value to a known set.
     *
     * @param string $value Value.
     * @param array<int, string> $allowed Allowed values.
     * @param string $default Default value.
     * @return string
     */
    private static function allow_value(string $value, array $allowed, string $default): string {
        $value = trim($value);

        return in_array($value, $allowed, true) ? $value : $default;
    }
}