<?php
// This file is part of Moodle - https://moodle.org/
//
// Moodle is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// any later version.

/**
 * Public Médiathèque service.
 *
 * @package    mod_uckkarchive
 * @copyright  2026 Univers-Cité King Klown
 * @license    https://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later
 */

declare(strict_types=1);

namespace mod_uckkarchive\local;

defined('MOODLE_INTERNAL') || die();

use context_module;
use moodle_url;
use stdClass;

/**
 * Coordinates the public Médiathèque explorer payload.
 *
 * This service is intentionally thin:
 *
 * - normalises public request parameters;
 * - resolves public search scope;
 * - calls the public Médiathèque repository;
 * - returns public DTOs only;
 * - adds pagination, notices, warnings and empty states;
 * - never renders templates;
 * - never serves files directly;
 * - never makes final access decisions in JavaScript or Mustache.
 *
 * The repository must return policy-filtered records. This service still
 * redacts conservatively when shaping the public DTO.
 */
final class public_mediatheque_service {
    /** Public page key. */
    public const PAGE_KEY = 'mediatheque';

    /** Public explorer key. */
    public const EXPLORER_KEY = 'mediatheque_explorer';

    /** Surface owner. */
    public const SURFACE = 'local_uckk';

    /** Data owner. */
    public const COMPONENT = 'mod_uckkarchive';

    /** Default page size. */
    public const DEFAULT_PERPAGE = 12;

    /** Maximum page size. */
    public const MAX_PERPAGE = 48;

    /** Default sort. */
    public const DEFAULT_SORT = 'relevance';

    /** Public object: all. */
    public const OBJECT_ALL = 'all';

    /** Public object: media. */
    public const OBJECT_MEDIA = 'media';

    /** Public object: collection. */
    public const OBJECT_COLLECTION = 'collection';

    /** Public object: external work. */
    public const OBJECT_EXTERNAL_WORK = 'external_work';

    /** Public object: archive item. */
    public const OBJECT_ARCHIVE_ITEM = 'archive_item';

    /** Public object: content marker. */
    public const OBJECT_CONTENT_MARKER = 'content_marker';

    /** @var public_mediatheque_repository Repository. */
    private public_mediatheque_repository $repository;

    /** @var media_library_scope Library/site scope resolver. */
    private media_library_scope $libraryscope;

    /**
     * Constructor.
     *
     * @param public_mediatheque_repository|null $repository Optional repository for tests.
     */
    public function __construct(
        ?public_mediatheque_repository $repository = null,
        ?media_library_scope $libraryscope = null
    ) {
        $this->repository = $repository ?? new public_mediatheque_repository();
        $this->libraryscope = $libraryscope ?? new media_library_scope();
    }

    /**
     * Build a public explorer search payload.
     *
     * Expected request keys:
     *
     * - cmid
     * - archiveid
     * - q or query
     * - type
     * - mediatype
     * - collection
     * - tag
     * - source
     * - advisory
     * - cultural
     * - audience
     * - lang
     * - validation
     * - sort
     * - page
     * - perpage
     *
     * archiveid = 0 and cmid = 0 means site-wide public discovery.
     *
     * @param array<string,mixed> $request Raw request.
     * @param context_module|null $context Optional module context.
     * @param stdClass|null $user Optional acting user.
     * @return array<string,mixed> Public explorer DTO.
     */
    public function search(array $request = [], ?context_module $context = null, ?stdClass $user = null): array {
        [$archiveid, $context] = $this->resolve_scope($request, $context);
        $filters = $this->normalise_request($request);
        $library = $this->resolve_library_for_site((string)$filters['sitekey']);
        $repositoryfilters = $filters;
        $repositoryfilters['libraryrequired'] = true;
        $repositoryfilters['libraryid'] = $library ? (int)$library->id : 0;

        $result = $this->repository->search($archiveid, $context, $repositoryfilters);

        $items = $this->normalise_items($this->get_array_value($result, 'items'));
        $total = max(0, $this->get_int_value($result, 'total', count($items)));
        $page = (int)$filters['page'];
        $perpage = (int)$filters['perpage'];

        return [
            'context' => [
                'component' => self::COMPONENT,
                'surface' => self::SURFACE,
                'page' => self::PAGE_KEY,
                'explorer' => self::EXPLORER_KEY,
                'anonymous' => empty($user) || empty($user->id),
                'policyfiltered' => true,
                'sitekey' => (string)$filters['sitekey'],
                'libraryslug' => $library ? (string)$library->slug : '',
                'libraryname' => $library ? format_string((string)$library->name) : '',
            ],
            'filters' => $filters,
            'facets' => $this->normalise_facets($this->get_array_value($result, 'facets')),
            'items' => $items,
            'pagination' => [
                'page' => $page,
                'perpage' => $perpage,
                'total' => $total,
                'hasmore' => ($page * $perpage) < $total,
            ],
            'notices' => $this->build_notices($this->get_array_value($result, 'notices')),
            'warnings' => $this->build_warnings($this->get_array_value($result, 'warnings')),
            'empty' => [
                'isempty' => empty($items),
                'message' => empty($items)
                    ? get_string('mediatheque_empty', 'mod_uckkarchive')
                    : '',
            ],
        ];
    }

    /**
     * Build a public item detail payload.
     *
     * Expected request keys:
     *
     * - cmid
     * - archiveid
     * - item or uuid
     * - type
     *
     * archiveid = 0 and cmid = 0 means site-wide public discovery.
     *
     * The first implemented public detail object is media. Other public object
     * types are intentionally returned fail-closed until their repository
     * lookup methods exist.
     *
     * @param array<string,mixed> $request Raw request.
     * @param context_module|null $context Optional module context.
     * @param stdClass|null $user Optional acting user.
     * @return array<string,mixed> Public item detail DTO.
     */
    public function get_item(array $request = [], ?context_module $context = null, ?stdClass $user = null): array {
        [$archiveid, $context] = $this->resolve_scope($request, $context);
        $sitekey = media_library_scope::clean_site_key((string)($request['sitekey'] ?? media_library_scope::SITE_UCKK));
        if ($sitekey === '') {
            $sitekey = media_library_scope::SITE_UCKK;
        }
        $library = $this->resolve_library_for_site($sitekey);
        $libraryid = $library ? (int)$library->id : 0;

        $type = $this->allow(
            $request['type'] ?? self::OBJECT_MEDIA,
            $this->allowed_object_types(false),
            self::OBJECT_MEDIA
        );

        $uuid = $this->clean_optional_key($request['uuid'] ?? $request['item'] ?? null) ?? '';

        $warnings = [];
        $item = [];

        if ($uuid === '') {
            $warnings[] = [
                'item' => 'mediatheque',
                'itemid' => '0',
                'warningcode' => 'missing_public_item_uuid',
                'message' => 'Missing public item UUID.',
            ];
        } else if ($type !== self::OBJECT_MEDIA) {
            $warnings[] = [
                'item' => 'mediatheque',
                'itemid' => '0',
                'warningcode' => 'unsupported_public_item_type',
                'message' => 'This public item type is not yet available for detail rendering.',
            ];
        } else {
            $record = $library
                ? $this->repository->get_media_by_uuid($archiveid, $context, $uuid, $libraryid)
                : null;

            if ($record) {
                $item = $this->normalise_item($record);
            }
        }

        return [
            'context' => [
                'component' => self::COMPONENT,
                'surface' => self::SURFACE,
                'page' => self::PAGE_KEY,
                'explorer' => self::EXPLORER_KEY,
                'anonymous' => empty($user) || empty($user->id),
                'policyfiltered' => true,
                'sitekey' => $sitekey,
                'libraryslug' => $library ? (string)$library->slug : '',
                'libraryname' => $library ? format_string((string)$library->name) : '',
            ],
            'request' => [
                'cmid' => max(0, (int)($request['cmid'] ?? 0)),
                'archiveid' => max(0, (int)($request['archiveid'] ?? 0)),
                'item' => $uuid,
                'uuid' => $uuid,
                'type' => $type,
                'sitekey' => $sitekey,
            ],
            'item' => $item,
            'notices' => $this->build_notices([]),
            'warnings' => $this->build_warnings($warnings),
            'empty' => [
                'isempty' => empty($item),
                'message' => empty($item)
                    ? get_string('mediatheque_empty', 'mod_uckkarchive')
                    : '',
            ],
        ];
    }

    /** Resolve the primary autonomous media library for one public site. */
    private function resolve_library_for_site(string $sitekey): ?stdClass {
        return $this->libraryscope->resolve_primary_for_site($sitekey);
    }

    /**
     * Resolve public search scope.
     *
     * archiveid = 0 and cmid = 0 means site-wide public discovery.
     *
     * @param array<string,mixed> $request Request.
     * @param context_module|null $context Context.
     * @return array{0:int,1:?context_module}
     */
    private function resolve_scope(array $request, ?context_module $context): array {
        global $DB;

        $cmid = max(0, (int)($request['cmid'] ?? 0));
        $archiveid = max(0, (int)($request['archiveid'] ?? 0));

        if ($cmid > 0 && !$context) {
            $cm = get_coursemodule_from_id('uckkarchive', $cmid, 0, false, IGNORE_MISSING);

            if ($cm) {
                $context = context_module::instance((int)$cm->id);

                if ($archiveid <= 0 && !empty($cm->instance)) {
                    $archiveid = (int)$cm->instance;
                }
            }
        }

        if ($archiveid > 0 && !$context) {
            $archive = $DB->get_record('uckkarchive', ['id' => $archiveid], 'id, course', IGNORE_MISSING);

            if ($archive) {
                $cm = get_coursemodule_from_instance(
                    'uckkarchive',
                    $archiveid,
                    (int)$archive->course,
                    false,
                    IGNORE_MISSING
                );

                if ($cm) {
                    $context = context_module::instance((int)$cm->id);
                }
            }
        }

        return [$archiveid, $context];
    }

    /**
     * Normalise raw public request parameters.
     *
     * @param array<string,mixed> $request Raw request.
     * @return array<string,mixed> Normalised request.
     */
    public function normalise_request(array $request): array {
        $nested = isset($request['filters']) && is_array($request['filters'])
            ? $request['filters']
            : [];

        $request = array_merge($nested, $request);

        $page = max(1, (int)($request['page'] ?? 1));
        $perpage = (int)($request['perpage'] ?? self::DEFAULT_PERPAGE);
        $perpage = min(self::MAX_PERPAGE, max(1, $perpage));

        $sitekey = media_library_scope::clean_site_key((string)($request['sitekey'] ?? media_library_scope::SITE_UCKK));
        if ($sitekey === '') {
            $sitekey = media_library_scope::SITE_UCKK;
        }

        return [
            'cmid' => max(0, (int)($request['cmid'] ?? 0)),
            'archiveid' => max(0, (int)($request['archiveid'] ?? 0)),
            'sitekey' => $sitekey,
            'q' => $this->clean_text($request['q'] ?? $request['query'] ?? ''),
            'type' => $this->allow(
                $request['type'] ?? self::OBJECT_ALL,
                $this->allowed_object_types(),
                self::OBJECT_ALL
            ),
            'mediatype' => $this->allow(
                $request['mediatype'] ?? 'all',
                [
                    'all',
                    'video',
                    'audio',
                    'text',
                    'code',
                    'image',
                    'pdf',
                    'document',
                    'book',
                    'external_reference',
                    'other',
                ],
                'all'
            ),
            'collection' => $this->clean_optional_key($request['collection'] ?? null) ?? '',
            'tag' => $this->clean_optional_key($request['tag'] ?? null) ?? '',
            'source' => $this->allow_nullable(
                $request['source'] ?? null,
                ['produced_by_uckk', 'submitted_to_uckk', 'imported', 'external_reference_only']
            ) ?? '',
            'advisory' => $this->allow(
                $request['advisory'] ?? 'all',
                ['all', 'none', 'has_advisory', 'has_public_advisory'],
                'all'
            ),
            'cultural' => $this->allow(
                $request['cultural'] ?? 'all',
                ['all', 'none', 'has_public_protocol'],
                'all'
            ),
            'audience' => $this->allow(
                $request['audience'] ?? 'all',
                ['all', 'general', 'guided', 'mature', 'restricted'],
                'all'
            ),
            'lang' => $this->clean_optional_key($request['lang'] ?? null) ?? '',
            'validation' => $this->allow(
                $request['validation'] ?? 'all',
                ['all', 'human_reviewed', 'verified', 'archived'],
                'all'
            ),
            'sort' => $this->allow(
                $request['sort'] ?? self::DEFAULT_SORT,
                ['relevance', 'newest', 'title', 'type', 'collection', 'validated'],
                self::DEFAULT_SORT
            ),
            'page' => $page,
            'perpage' => $perpage,
        ];
    }

    /**
     * Normalise public item DTOs.
     *
     * @param array<int,array<string,mixed>|stdClass> $items Raw policy-filtered items.
     * @return array<int,array<string,mixed>> Public DTOs.
     */
    private function normalise_items(array $items): array {
        $normalised = [];

        foreach ($items as $item) {
            $normalised[] = $this->normalise_item($item);
        }

        return $normalised;
    }

    /**
     * Normalise one public item DTO.
     *
     * @param array<string,mixed>|stdClass $item Raw item.
     * @return array<string,mixed> Public DTO.
     */
    private function normalise_item($item): array {
        $uuid = $this->get_string_value($item, 'uuid');
        $objecttype = $this->allow(
            $this->get_string_value($item, 'objecttype', self::OBJECT_MEDIA),
            $this->allowed_object_types(false),
            self::OBJECT_MEDIA
        );

        $title = $this->get_string_value($item, 'title', get_string('untitled', 'moodle'));
        $summary = $this->truncate($this->get_string_value($item, 'summary'));

        $source = $this->get_array_or_object_value($item, 'source');
        $rights = $this->get_array_or_object_value($item, 'rights');
        $statusraw = $this->get_array_or_object_value($item, 'status');
        $visibilityraw = $this->get_array_or_object_value($item, 'visibility');
        $validationraw = $this->get_array_or_object_value($item, 'validation');
        $advisories = $this->get_array_or_object_value($item, 'advisories');
        $culturalprotocol = $this->get_array_or_object_value($item, 'culturalprotocol');
        $relations = $this->get_array_or_object_value($item, 'relations');
        $actions = $this->get_array_or_object_value($item, 'actions');
        $libraryraw = $this->get_array_or_object_value($item, 'library');

        $libraryslug = $this->get_string_value($item, 'libraryslug');
        if ($libraryslug === '') {
            $libraryslug = $this->get_string_value($libraryraw, 'slug');
        }
        $libraryname = $this->get_string_value($item, 'libraryname');
        if ($libraryname === '') {
            $libraryname = $this->get_string_value($libraryraw, 'name');
        }
        $isbridged = $this->get_bool_value($item, 'isbridged') || $this->get_bool_value($libraryraw, 'isbridged');
        $bridgescope = $this->get_string_value($item, 'bridgescope');
        if ($bridgescope === '') {
            $bridgescope = $this->get_string_value($libraryraw, 'bridgescope');
        }
        $bridgelabel = $this->get_string_value($item, 'bridgelabel');
        if ($bridgelabel === '') {
            $bridgelabel = $this->get_string_value($libraryraw, 'bridgelabel');
        }

        $sourcevalue = $this->get_string_value($item, 'sourcevalue');
        if ($sourcevalue === '') {
            $sourcevalue = $this->get_string_value($source, 'value');
        }

        $sourcelabel = $this->get_string_value($item, 'sourcelabel');
        if ($sourcelabel === '') {
            $sourcelabel = $this->get_string_value($source, 'label');
        }

        $license = $this->get_nullable_string_value($item, 'license');
        if ($license === null) {
            $license = $this->get_nullable_string_value($rights, 'license');
        }

        $rightsstatement = $this->get_nullable_string_value($item, 'rightsstatement');
        if ($rightsstatement === null) {
            $rightsstatement = $this->get_nullable_string_value($rights, 'rightsstatement');
        }

        $status = $this->get_string_value($item, 'status');
        if ($status === '' || $status === 'Array') {
            $status = $this->get_string_value($statusraw, 'value', 'active');
        }

        $visibility = $this->get_string_value($item, 'visibility');
        if ($visibility === '' || $visibility === 'Array') {
            $visibility = $this->get_string_value($visibilityraw, 'value', 'public');
        }

        $validation = $this->get_string_value($item, 'validation');
        if ($validation === '' || $validation === 'Array') {
            $validation = $this->get_string_value($validationraw, 'value');
        }

        $haspublicadvisory = $this->get_bool_value($item, 'haspublicadvisory');
        if (!$haspublicadvisory) {
            $haspublicadvisory = $this->get_bool_value($advisories, 'haspublicadvisory');
        }

        $advisorysummary = $this->get_nullable_string_value($item, 'advisorysummary');
        if ($advisorysummary === null) {
            $advisorysummary = $this->get_nullable_string_value($advisories, 'summary');
        }

        $haspublicprotocol = $this->get_bool_value($item, 'haspublicprotocol');
        if (!$haspublicprotocol) {
            $haspublicprotocol = $this->get_bool_value($culturalprotocol, 'haspublicprotocol');
        }

        $culturalprotocolsummary = $this->get_nullable_string_value($item, 'culturalprotocolsummary');
        if ($culturalprotocolsummary === null) {
            $culturalprotocolsummary = $this->get_nullable_string_value($culturalprotocol, 'summary');
        }

        $externalurl = $this->external_url($item, $source, $actions);
        $hasexternalurl = $externalurl !== '';

        return [
            'uuid' => $uuid,
            'objecttype' => $objecttype,
            'title' => format_string($title),
            'subtitle' => $this->get_string_value($item, 'subtitle'),
            'summary' => $summary,
            'mediatype' => $this->get_string_value($item, 'mediatype'),
            'mimetype' => $this->get_string_value($item, 'mimetype'),
            'language' => $this->get_string_value($item, 'language'),
            'thumbnailurl' => $this->get_string_value($item, 'thumbnailurl'),
            'detailurl' => $this->detail_url($uuid, $objecttype),
            'library' => [
                'slug' => $libraryslug,
                'name' => $libraryname,
                'isbridged' => $isbridged,
                'bridgescope' => $bridgescope,
                'bridgelabel' => $bridgelabel,
            ],
            'externalurl' => $externalurl,
            'hasexternalurl' => $hasexternalurl,
            'externalactionlabel' => $this->external_action_label(),
            'source' => [
                'value' => $sourcevalue,
                'label' => $sourcelabel,
                'url' => $externalurl,
                'hasurl' => $hasexternalurl,
            ],
            'rights' => [
                'license' => $license ?? '',
                'rightsstatement' => $rightsstatement ?? '',
                'copyallowed' => $this->get_bool_value($item, 'copyallowed')
                    || $this->get_bool_value($rights, 'copyallowed'),
            ],
            'status' => [
                'value' => $status,
                'label' => $this->status_label($status),
            ],
            'visibility' => [
                'value' => $visibility,
                'label' => $this->visibility_label($visibility),
            ],
            'validation' => [
                'value' => $validation,
                'label' => $validation !== '' ? $this->validation_label($validation) : '',
            ],
            'badges' => $this->normalise_badges($this->get_array_value($item, 'badges')),
            'advisories' => [
                'haspublicadvisory' => $haspublicadvisory,
                'summary' => $advisorysummary ?? '',
            ],
            'culturalprotocol' => [
                'haspublicprotocol' => $haspublicprotocol,
                'summary' => $culturalprotocolsummary ?? '',
            ],
            'relations' => [
                'collectioncount' => $this->get_int_value($item, 'collectioncount')
                    ?: $this->get_int_value($relations, 'collectioncount'),
                'markercount' => $this->get_int_value($item, 'markercount')
                    ?: $this->get_int_value($relations, 'markercount'),
                'externalworkcount' => $this->get_int_value($item, 'externalworkcount')
                    ?: $this->get_int_value($relations, 'externalworkcount'),
            ],
            'actions' => [
                'canviewdetail' => $this->get_bool_value($item, 'canviewdetail', true)
                    || $this->get_bool_value($actions, 'canviewdetail', true),
                'canviewfile' => $this->get_bool_value($item, 'canviewfile')
                    || $this->get_bool_value($actions, 'canviewfile'),
                'candownload' => $this->get_bool_value($item, 'candownload')
                    || $this->get_bool_value($actions, 'candownload'),
                'canopenexternal' => $hasexternalurl,
                'canexport' => false,
            ],
        ];
    }

    /**
     * Normalise facet payloads.
     *
     * Canonical output:
     *
     * [
     *     [
     *         'key' => 'mediatype',
     *         'label' => 'Format',
     *         'items' => [
     *             ['value' => 'video', 'label' => 'Vidéo', 'count' => 3, 'active' => false],
     *         ],
     *     ],
     * ]
     *
     * @param array<int|string,array<string,mixed>|stdClass|array<int,mixed>> $facets Raw facets.
     * @return array<int,array<string,mixed>> Public facets.
     */
    private function normalise_facets(array $facets): array {
        $normalised = [];

        if (!$this->is_list_array($facets)) {
            foreach ($facets as $key => $items) {
                $normalised[] = $this->normalise_facet_group([
                    'key' => (string)$key,
                    'label' => $this->facet_label((string)$key),
                    'items' => is_array($items) ? $items : [],
                ]);
            }

            return $normalised;
        }

        foreach ($facets as $facet) {
            $normalised[] = $this->normalise_facet_group($facet);
        }

        return $normalised;
    }

    /**
     * Normalise one facet group.
     *
     * @param array<string,mixed>|stdClass $facet Raw group.
     * @return array<string,mixed>
     */
    private function normalise_facet_group($facet): array {
        $items = [];

        foreach ($this->get_array_value($facet, 'items') as $item) {
            if (is_scalar($item)) {
                $value = trim((string)$item);
                $items[] = [
                    'value' => $value,
                    'label' => format_string($value),
                    'count' => 0,
                    'active' => false,
                ];
                continue;
            }

            $items[] = [
                'value' => $this->get_string_value($item, 'value'),
                'label' => $this->get_string_value($item, 'label'),
                'count' => $this->get_int_value($item, 'count'),
                'active' => $this->get_bool_value($item, 'active'),
            ];
        }

        return [
            'key' => $this->get_string_value($facet, 'key'),
            'label' => $this->get_string_value($facet, 'label'),
            'items' => $items,
        ];
    }

    /**
     * Build public notices.
     *
     * @param array<int,array<string,mixed>|stdClass|string> $notices Repository notices.
     * @return array<int,array<string,string>>
     */
    private function build_notices(array $notices): array {
        $normalised = [[
            'type' => 'info',
            'code' => 'restricted_content_notice',
            'message' => get_string('mediatheque_restricted_notice', 'mod_uckkarchive'),
        ]];

        foreach ($notices as $notice) {
            if (is_string($notice)) {
                $normalised[] = [
                    'type' => 'info',
                    'code' => 'repository_notice',
                    'message' => $notice,
                ];
                continue;
            }

            $normalised[] = [
                'type' => $this->allow(
                    $this->get_string_value($notice, 'type', 'info'),
                    ['info', 'warning', 'danger', 'success'],
                    'info'
                ),
                'code' => $this->get_string_value($notice, 'code', 'repository_notice'),
                'message' => $this->get_string_value($notice, 'message'),
            ];
        }

        return $normalised;
    }

    /**
     * Build public warnings.
     *
     * @param array<int,array<string,mixed>|stdClass|string> $warnings Repository warnings.
     * @return array<int,array<string,string>>
     */
    private function build_warnings(array $warnings): array {
        $normalised = [];

        foreach ($warnings as $warning) {
            if (is_string($warning)) {
                $normalised[] = [
                    'item' => 'mediatheque',
                    'itemid' => '0',
                    'warningcode' => 'public_warning',
                    'message' => $warning,
                ];
                continue;
            }

            $normalised[] = [
                'item' => $this->get_string_value($warning, 'item', 'mediatheque'),
                'itemid' => (string)$this->get_int_value($warning, 'itemid'),
                'warningcode' => $this->get_string_value($warning, 'warningcode', 'public_warning'),
                'message' => $this->get_string_value($warning, 'message'),
            ];
        }

        return $normalised;
    }

    /**
     * Normalise badge payloads.
     *
     * @param array<int,array<string,mixed>|stdClass|string> $badges Raw badges.
     * @return array<int,array<string,string>>
     */
    private function normalise_badges(array $badges): array {
        $normalised = [];

        foreach ($badges as $badge) {
            if (is_string($badge)) {
                $normalised[] = [
                    'key' => clean_param($badge, PARAM_ALPHANUMEXT),
                    'label' => format_string($badge),
                    'type' => 'badge',
                ];
                continue;
            }

            $normalised[] = [
                'key' => clean_param($this->get_string_value($badge, 'key'), PARAM_ALPHANUMEXT),
                'label' => format_string($this->get_string_value($badge, 'label')),
                'type' => clean_param($this->get_string_value($badge, 'type', 'badge'), PARAM_ALPHANUMEXT),
            ];
        }

        return $normalised;
    }

    /**
     * Resolve a public external media URL from the repository DTO.
     *
     * The repository remains responsible for exposing only public-safe source
     * URLs. This service only normalises values that are already present in the
     * public DTO, for example media source URLs such as SoundCloud, YouTube,
     * article URLs or public code repository URLs.
     *
     * @param array<string,mixed>|stdClass $item Raw item.
     * @param array<string,mixed>|stdClass $source Source payload.
     * @param array<string,mixed>|stdClass $actions Action payload.
     * @return string Public external URL, or empty string.
     */
    private function external_url($item, $source, $actions): string {
        $candidates = [
            [$item, ['externalurl', 'sourceurl', 'canonicalurl', 'publicurl', 'remoteurl', 'url']],
            [$source, ['externalurl', 'sourceurl', 'canonicalurl', 'publicurl', 'remoteurl', 'url']],
            [$actions, ['externalurl', 'sourceurl', 'canonicalurl', 'publicurl', 'remoteurl', 'url']],
        ];

        foreach ($candidates as [$payload, $keys]) {
            foreach ($keys as $key) {
                $url = $this->get_nullable_string_value($payload, $key);

                if ($url === null) {
                    continue;
                }

                $url = trim(clean_param($url, PARAM_URL));

                if ($url === '') {
                    continue;
                }

                if (!preg_match('#^https?://#i', $url)) {
                    continue;
                }

                return $url;
            }
        }

        return '';
    }

    /**
     * Public label for an external media action.
     *
     * @return string Action label.
     */
    private function external_action_label(): string {
        return get_string_manager()->string_exists('mediatheque_action_open_external', 'mod_uckkarchive')
            ? get_string('mediatheque_action_open_external', 'mod_uckkarchive')
            : 'Ouvrir la référence externe';
    }

    /**
     * Build public detail URL.
     *
     * @param string $uuid Public UUID.
     * @param string $objecttype Public object type.
     * @return string URL.
     */
    private function detail_url(string $uuid, string $objecttype): string {
        if ($uuid === '') {
            return '';
        }

        return (new moodle_url('/local/uckk/mediatheque.php', [
            'item' => $uuid,
            'type' => $objecttype,
        ]))->out(false);
    }

    /**
     * Allowed public object types.
     *
     * @param bool $includeall Include all.
     * @return string[]
     */
    private function allowed_object_types(bool $includeall = true): array {
        $types = [
            self::OBJECT_MEDIA,
            self::OBJECT_COLLECTION,
            self::OBJECT_EXTERNAL_WORK,
            self::OBJECT_ARCHIVE_ITEM,
            self::OBJECT_CONTENT_MARKER,
        ];

        if ($includeall) {
            array_unshift($types, self::OBJECT_ALL);
        }

        return $types;
    }

    /**
     * Clean plain text.
     *
     * @param mixed $value Value.
     * @return string Cleaned value.
     */
    private function clean_text($value): string {
        return trim(clean_param((string)$value, PARAM_TEXT));
    }

    /**
     * Clean nullable key.
     *
     * @param mixed $value Value.
     * @return string|null Clean key.
     */
    private function clean_optional_key($value): ?string {
        $value = trim(clean_param((string)($value ?? ''), PARAM_ALPHANUMEXT));

        return $value === '' ? null : $value;
    }

    /**
     * Keep only allowed values.
     *
     * @param mixed $value Value.
     * @param string[] $allowed Allowed values.
     * @param string $default Default.
     * @return string Clean value.
     */
    private function allow($value, array $allowed, string $default): string {
        $value = trim(clean_param((string)$value, PARAM_ALPHANUMEXT));

        return in_array($value, $allowed, true) ? $value : $default;
    }

    /**
     * Keep only allowed nullable values.
     *
     * @param mixed $value Value.
     * @param string[] $allowed Allowed values.
     * @return string|null Clean value.
     */
    private function allow_nullable($value, array $allowed): ?string {
        $value = trim(clean_param((string)($value ?? ''), PARAM_ALPHANUMEXT));

        if ($value === '') {
            return null;
        }

        return in_array($value, $allowed, true) ? $value : null;
    }

    /**
     * Truncate public summaries.
     *
     * @param string $value Raw summary.
     * @return string Truncated summary.
     */
    private function truncate(string $value): string {
        $value = trim($value);

        if (\core_text::strlen($value) <= 240) {
            return $value;
        }

        return \core_text::substr($value, 0, 237) . '...';
    }

    /**
     * Read string value from array/object.
     *
     * @param mixed $source Source.
     * @param string $key Key.
     * @param string $default Default.
     * @return string Value.
     */
    private function get_string_value($source, string $key, string $default = ''): string {
        $value = $this->get_value($source, $key, $default);

        if (is_array($value) || is_object($value)) {
            return $default;
        }

        return trim((string)$value);
    }

    /**
     * Read nullable string value from array/object.
     *
     * @param mixed $source Source.
     * @param string $key Key.
     * @return string|null Value.
     */
    private function get_nullable_string_value($source, string $key): ?string {
        $value = $this->get_value($source, $key, '');

        if (is_array($value) || is_object($value)) {
            return null;
        }

        $value = trim((string)$value);

        return $value === '' ? null : $value;
    }

    /**
     * Read int value from array/object.
     *
     * @param mixed $source Source.
     * @param string $key Key.
     * @param int $default Default.
     * @return int Value.
     */
    private function get_int_value($source, string $key, int $default = 0): int {
        $value = $this->get_value($source, $key, $default);

        if (is_array($value) || is_object($value)) {
            return $default;
        }

        return (int)$value;
    }

    /**
     * Read bool value from array/object.
     *
     * @param mixed $source Source.
     * @param string $key Key.
     * @param bool $default Default.
     * @return bool Value.
     */
    private function get_bool_value($source, string $key, bool $default = false): bool {
        $value = $this->get_value($source, $key, $default);

        if (is_array($value) || is_object($value)) {
            return $default;
        }

        return (bool)$value;
    }

    /**
     * Read array value from array/object.
     *
     * @param mixed $source Source.
     * @param string $key Key.
     * @return array<int|string,mixed> Value.
     */
    private function get_array_value($source, string $key): array {
        $value = $this->get_value($source, $key, []);

        if (is_array($value)) {
            return $value;
        }

        if ($value instanceof stdClass) {
            return get_object_vars($value);
        }

        return [];
    }

    /**
     * Read array/object value from array/object.
     *
     * @param mixed $source Source.
     * @param string $key Key.
     * @return array<string,mixed>|stdClass Empty array if missing.
     */
    private function get_array_or_object_value($source, string $key) {
        $value = $this->get_value($source, $key, []);

        if (is_array($value) || $value instanceof stdClass) {
            return $value;
        }

        return [];
    }

    /**
     * Read value from array/object.
     *
     * @param mixed $source Source.
     * @param string $key Key.
     * @param mixed $default Default.
     * @return mixed Value.
     */
    private function get_value($source, string $key, $default = null) {
        if (is_array($source)) {
            return $source[$key] ?? $default;
        }

        if (is_object($source) && property_exists($source, $key)) {
            return $source->{$key};
        }

        return $default;
    }

    /**
     * Whether array uses consecutive numeric keys.
     *
     * @param array<int|string,mixed> $array Array.
     * @return bool
     */
    private function is_list_array(array $array): bool {
        if ($array === []) {
            return true;
        }

        return array_keys($array) === range(0, count($array) - 1);
    }

    /**
     * Get public facet label.
     *
     * @param string $key Facet key.
     * @return string Label.
     */
    private function facet_label(string $key): string {
        $stringkey = 'mediatheque_filter_' . clean_param($key, PARAM_ALPHANUMEXT);

        return get_string_manager()->string_exists($stringkey, 'mod_uckkarchive')
            ? get_string($stringkey, 'mod_uckkarchive')
            : format_string($key);
    }

    /**
     * Get public status label.
     *
     * @param string $status Status.
     * @return string Label.
     */
    private function status_label(string $status): string {
        $key = 'status_' . clean_param($status, PARAM_ALPHANUMEXT);

        return get_string_manager()->string_exists($key, 'mod_uckkarchive')
            ? get_string($key, 'mod_uckkarchive')
            : format_string($status);
    }

    /**
     * Get public visibility label.
     *
     * @param string $visibility Visibility.
     * @return string Label.
     */
    private function visibility_label(string $visibility): string {
        $key = 'visibility_' . clean_param($visibility, PARAM_ALPHANUMEXT);

        return get_string_manager()->string_exists($key, 'mod_uckkarchive')
            ? get_string($key, 'mod_uckkarchive')
            : format_string($visibility);
    }

    /**
     * Get public validation label.
     *
     * @param string $validation Validation state.
     * @return string Label.
     */
    private function validation_label(string $validation): string {
        $key = 'validationstate_' . clean_param($validation, PARAM_ALPHANUMEXT);

        return get_string_manager()->string_exists($key, 'mod_uckkarchive')
            ? get_string($key, 'mod_uckkarchive')
            : format_string($validation);
    }
}