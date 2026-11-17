<?php
// This file is part of Moodle - https://moodle.org/
//
// Moodle is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// any later version.

/**
 * Media library controller for a UCKK Archive activity.
 *
 * This page is the Moodle-facing entry point for the self-contained media
 * library owned by mod_uckkarchive. It resolves the Moodle course/module
 * context, checks capabilities, normalises request filters, loads
 * permission-aware media records, and delegates rendering to output classes.
 *
 * @package    mod_uckkarchive
 * @copyright  2026 Univers-Cité King Klown
 * @license    https://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later
 */

declare(strict_types=1);

$moodleconfig = null;

if (!empty($_SERVER['DOCUMENT_ROOT'])) {
    $candidate = rtrim($_SERVER['DOCUMENT_ROOT'], "\\/") . DIRECTORY_SEPARATOR . 'config.php';
    if (is_readable($candidate)) {
        $moodleconfig = $candidate;
    }
}

if ($moodleconfig === null) {
    $candidate = dirname(__DIR__, 2) . DIRECTORY_SEPARATOR . 'config.php';
    if (is_readable($candidate)) {
        $moodleconfig = $candidate;
    }
}

if ($moodleconfig === null) {
    throw new \RuntimeException('Cannot locate Moodle config.php.');
}

require_once($moodleconfig);
require_once($CFG->dirroot . '/mod/uckkarchive/lib.php');
require_once($CFG->dirroot . '/mod/uckkarchive/locallib.php');

defined('MOODLE_INTERNAL') || die();

use core\output\notification;
use mod_uckkarchive\local\context_resolver;
use mod_uckkarchive\form\media_form;
use mod_uckkarchive\local\media as media_record;
use mod_uckkarchive\local\media_collection;
use mod_uckkarchive\local\media_policy;
use mod_uckkarchive\local\media_search;
use mod_uckkarchive\output\media_library;
use mod_uckkarchive\output\media_library_editor;

/**
 * Get a component string with fallback.
 *
 * @param string $identifier String identifier.
 * @param string $fallback Fallback value.
 * @return string
 */
function mod_uckkarchive_media_string(string $identifier, string $fallback = ''): string {
    $manager = get_string_manager();

    foreach (['uckkarchive', 'mod_uckkarchive'] as $component) {
        if ($manager->string_exists($identifier, $component)) {
            return get_string($identifier, $component);
        }
    }

    return $fallback !== '' ? $fallback : $identifier;
}

/**
 * Return whether a database table exists.
 *
 * @param string $table Table name without Moodle braces.
 * @return bool
 */
function mod_uckkarchive_media_table_exists(string $table): bool {
    global $DB;

    return $DB->get_manager()->table_exists(new xmldb_table($table));
}

/**
 * Normalise a request value against an allow-list.
 *
 * @param string $value Raw value.
 * @param string[] $allowed Allowed values.
 * @param string $default Default value.
 * @return string
 */
function mod_uckkarchive_media_normalise_choice(string $value, array $allowed, string $default = ''): string {
    $value = clean_param(trim($value), PARAM_ALPHANUMEXT);

    return in_array($value, $allowed, true) ? $value : $default;
}

/**
 * Normalise the media controller action.
 *
 * @param string $action Raw action.
 * @return string
 */
function mod_uckkarchive_media_normalise_action(string $action): string {
    $action = clean_param(strtolower(trim($action)), PARAM_ALPHANUMEXT);

    $aliases = [
        'upload' => 'add',
        'addmedia' => 'add',
        'new' => 'add',
        'newmedia' => 'add',
        'addcollection' => 'addcollection',
        'newcollection' => 'addcollection',
        'collectionedit' => 'addcollection',
        'contentadvisories' => 'advisories',
        'content_advisories' => 'advisories',
        'externalwork' => 'externalwork',
        'externalworks' => 'externalwork',
        'external_work' => 'externalwork',
    ];

    $action = $aliases[$action] ?? $action;

    return mod_uckkarchive_media_normalise_choice($action, [
        'library',
        'view',
        'collection',
        'add',
        'addcollection',
        'edit',
        'versions',
        'advisories',
        'externalwork',
    ], 'library');
}

/**
 * Resolve the archive activity, course module, course, context, and optional
 * target record from the request.
 *
 * Target records must take precedence over the course module id. Otherwise URLs
 * like `/mod/uckkarchive/media.php?id=33&mediaid=1&action=view` resolve only
 * the activity shell and leave the selected media record unavailable.
 *
 * @param int $id Course module id.
 * @param int $a Archive instance id.
 * @param int $mediaid Media id.
 * @param int $collectionid Media collection id.
 * @param int $externalworkid External work id.
 * @param int $contentmarkerid Content marker id.
 * @return stdClass Resolution object.
 */
function mod_uckkarchive_media_resolve_request(
    int $id,
    int $a,
    int $mediaid,
    int $collectionid,
    int $externalworkid,
    int $contentmarkerid
): stdClass {
    if ($mediaid > 0) {
        return context_resolver::from_media($mediaid);
    }

    if ($collectionid > 0) {
        return context_resolver::from_media_collection($collectionid);
    }

    if ($externalworkid > 0) {
        return context_resolver::from_external_work($externalworkid);
    }

    if ($contentmarkerid > 0) {
        return context_resolver::from_content_marker($contentmarkerid);
    }

    if ($id > 0) {
        return context_resolver::from_cmid($id);
    }

    if ($a > 0) {
        return context_resolver::from_archive($a);
    }

    throw new moodle_exception('missingparam', 'error', '', 'id');
}

/**
 * Convert old sort request parameters into media_search sort values.
 *
 * @param string $sort Raw sort.
 * @param string $dir Raw direction.
 * @return string
 */
function mod_uckkarchive_media_normalise_sort(string $sort, string $dir): string {
    $sort = clean_param(strtolower(trim($sort)), PARAM_ALPHANUMEXT);
    $dir = strtolower(trim($dir)) === 'asc' ? 'asc' : 'desc';

    if ($sort === 'title') {
        return $dir === 'asc' ? media_search::SORT_TITLE_ASC : media_search::SORT_TITLE_DESC;
    }

    if ($sort === 'timecreated') {
        return $dir === 'asc' ? media_search::SORT_OLDEST : media_search::SORT_NEWEST;
    }

    if ($sort === 'newest') {
        return media_search::SORT_NEWEST;
    }

    if ($sort === 'oldest') {
        return media_search::SORT_OLDEST;
    }

    if ($sort === 'title_asc') {
        return media_search::SORT_TITLE_ASC;
    }

    if ($sort === 'title_desc') {
        return media_search::SORT_TITLE_DESC;
    }

    if ($sort === 'modified' || $sort === 'timemodified') {
        return media_search::SORT_MODIFIED;
    }

    return media_search::SORT_MODIFIED;
}

/**
 * Build a clean filter payload for search and output layers.
 *
 * @param int $mediaid Selected media id.
 * @param int $collectionid Selected collection id.
 * @param int $externalworkid Selected external work id.
 * @param string $action Current action.
 * @return array<string,mixed>
 */
function mod_uckkarchive_media_build_filters(
    int $mediaid,
    int $collectionid,
    int $externalworkid,
    string $action
): array {
    $allowedtypes = [
        'image',
        'video',
        'audio',
        'document',
        'text',
        'dataset',
        'pdf',
        'transcript',
        'caption',
        'thumbnail',
        'preview',
        'derivative',
        'attachment',
        'external_reference',
        'external',
        'other',
    ];

    $allowedstatuses = [
        'draft',
        'submitted',
        'active',
        'restricted',
        'superseded',
        'archived',
        'deleted_soft',
    ];

    $allowedvisibilities = [
        'private',
        'user',
        'group',
        'course',
        'cohort',
        'program',
        'institution',
        'public',
        'restricted',
        'restricted_integrity',
        'restricted_cultural',
    ];

    $allowedsuitability = [
        'general',
        'guided',
        'mature',
        'restricted',
        'restricted_cultural',
        'restricted_integrity',
        'staff_only',
        'not_for_children',
        'review_required',
        'unknown',
    ];

    $allowedsourcetypes = [
        'produced_by_uckk',
        'submitted_to_uckk',
        'imported',
        'external_reference_only',
        'licensed_external',
        'public_domain',
        'fair_use_reference',
        'restricted_reference',
    ];

    $allowedsourceownership = [
        'uckk',
        'student',
        'teacher',
        'partner',
        'external',
        'unknown',
    ];

    $q = optional_param('q', '', PARAM_NOTAGS);
    if ($q === '') {
        $q = optional_param('search', '', PARAM_NOTAGS);
    }

    $tag = optional_param('tag', '', PARAM_TAG);
    $contenttag = optional_param('contenttag', '', PARAM_ALPHANUMEXT);
    if ($contenttag === '') {
        $contenttag = optional_param('advisory', '', PARAM_ALPHANUMEXT);
    }

    $mediatype = optional_param('mediatype', '', PARAM_ALPHANUMEXT);
    $status = optional_param('status', '', PARAM_ALPHANUMEXT);
    $visibility = optional_param('visibility', '', PARAM_ALPHANUMEXT);
    $audience = optional_param('audiencesuitability', '', PARAM_ALPHANUMEXT);
    if ($audience === '') {
        $audience = optional_param('audience', '', PARAM_ALPHANUMEXT);
    }

    $sourcetype = optional_param('sourcetype', '', PARAM_ALPHANUMEXT);
    if ($sourcetype === '') {
        $sourcetype = optional_param('source', '', PARAM_ALPHANUMEXT);
    }

    $sourceownership = optional_param('sourceownership', '', PARAM_ALPHANUMEXT);
    $sort = optional_param('sort', 'modified', PARAM_ALPHANUMEXT);
    $dir = optional_param('dir', 'desc', PARAM_ALPHA);

    $page = max(0, optional_param('page', 0, PARAM_INT));
    $perpage = min(100, max(1, optional_param('perpage', 24, PARAM_INT)));
    $includedeleted = optional_param('include_deleted', 0, PARAM_BOOL);
    $includerestricted = optional_param('include_restricted', 0, PARAM_BOOL);

    $filters = [
        'action' => $action,
        'mediaid' => $mediaid,
        'collectionid' => $collectionid,
        'externalworkid' => $externalworkid,
        'q' => trim($q),
        'search' => trim($q),
        'tag' => trim($tag),
        'contenttag' => clean_param($contenttag, PARAM_ALPHANUMEXT),
        'mediatype' => mod_uckkarchive_media_normalise_choice($mediatype, $allowedtypes),
        'status' => mod_uckkarchive_media_normalise_choice($status, $allowedstatuses),
        'visibility' => mod_uckkarchive_media_normalise_choice($visibility, $allowedvisibilities),
        'audiencesuitability' => mod_uckkarchive_media_normalise_choice($audience, $allowedsuitability),
        'sourcetype' => mod_uckkarchive_media_normalise_choice($sourcetype, $allowedsourcetypes),
        'sourceownership' => mod_uckkarchive_media_normalise_choice($sourceownership, $allowedsourceownership),
        'sort' => mod_uckkarchive_media_normalise_sort($sort, $dir),
        'dir' => strtolower($dir) === 'asc' ? 'asc' : 'desc',
        'page' => $page,
        'perpage' => $perpage,
        'include_deleted' => $includedeleted ? 1 : 0,
        'include_restricted' => $includerestricted ? 1 : 0,
    ];

    $filters['audience'] = $filters['audiencesuitability'];

    return $filters;
}

/**
 * Require capabilities implied by the requested action and filters.
 *
 * @param context_module $context Module context.
 * @param string $action Action.
 * @param array<string,mixed> $filters Filters.
 * @param stdClass|null $media Selected media.
 * @param stdClass|null $collection Selected collection.
 * @return void
 */
function mod_uckkarchive_media_require_action_capabilities(
    context_module $context,
    string $action,
    array $filters,
    ?stdClass $media,
    ?stdClass $collection
): void {
    require_capability('mod/uckkarchive:view', $context);
    media_policy::require_view_library($context);

    if ($media !== null) {
        media_policy::require_view_media($context, $media);
    }

    if ($collection !== null && !media_policy::can_view_collection($context, $collection)) {
        throw new required_capability_exception($context, 'mod/uckkarchive:viewmedia', 'nopermissions', '');
    }

    if ($action === 'add') {
        media_policy::require_add_media($context);
    }

    if ($action === 'addcollection') {
        require_capability('mod/uckkarchive:managemediacollections', $context);
    }

    if ($action === 'view') {
        if ($media === null) {
            throw new moodle_exception('missingparam', 'error', '', 'mediaid');
        }

        media_policy::require_view_media($context, $media);
    }

    if ($action === 'edit') {
        if ($media === null) {
            throw new moodle_exception('missingparam', 'error', '', 'mediaid');
        }

        media_policy::require_edit_media($context, $media);
    }

    if ($action === 'versions') {
        if ($media === null) {
            throw new moodle_exception('missingparam', 'error', '', 'mediaid');
        }

        media_policy::require_version_media($context, $media);
    }

    if ($action === 'advisories') {
        require_capability('mod/uckkarchive:viewadvisories', $context);
    }

    if ($action === 'externalwork') {
        require_capability('mod/uckkarchive:manageexternalworks', $context);
    }

    $restrictedvisibility = in_array((string)$filters['visibility'], [
        'restricted',
        'restricted_integrity',
    ], true);

    $restrictedaudience = in_array((string)$filters['audiencesuitability'], [
        'restricted',
        'restricted_integrity',
        'staff_only',
    ], true);

    if ($restrictedvisibility || $restrictedaudience || (string)$filters['status'] === 'restricted') {
        require_capability('mod/uckkarchive:viewrestrictedmedia', $context);
    }

    if ((string)$filters['visibility'] === 'restricted_cultural'
            || (string)$filters['audiencesuitability'] === 'restricted_cultural') {
        require_capability('mod/uckkarchive:viewculturallyrestricted', $context);
    }

    if (!empty($filters['include_deleted'])) {
        require_capability('mod/uckkarchive:editmedia', $context);
    }
}

/**
 * Build the current page URL from clean parameters.
 *
 * @param int $cmid Course module id.
 * @param array<string,mixed> $filters Filters.
 * @return moodle_url
 */
function mod_uckkarchive_media_build_page_url(int $cmid, array $filters): moodle_url {
    $params = [
        'id' => $cmid,
    ];

    foreach ([
        'action',
        'mediaid',
        'collectionid',
        'externalworkid',
        'q',
        'tag',
        'contenttag',
        'mediatype',
        'status',
        'visibility',
        'audiencesuitability',
        'sourcetype',
        'sourceownership',
        'sort',
        'dir',
        'page',
        'perpage',
        'include_deleted',
        'include_restricted',
    ] as $key) {
        if (!array_key_exists($key, $filters)) {
            continue;
        }

        $value = $filters[$key];

        if ($value === '' || $value === null || $value === 0 || $value === 'library') {
            continue;
        }

        $params[$key] = $value;
    }

    return new moodle_url('/mod/uckkarchive/media.php', $params);
}

/**
 * Return whether the current action opens the unified media-library editor.
 *
 * @param string $action Current action.
 * @return bool
 */
function mod_uckkarchive_media_is_editor_action(string $action): bool {
    return in_array($action, ['add', 'edit'], true);
}

/**
 * Return whether the current action opens the media detail view.
 *
 * @param string $action Current action.
 * @return bool
 */
function mod_uckkarchive_media_is_detail_action(string $action): bool {
    return $action === 'view';
}

/**
 * Build a Moodle form URL for the media-library editor.
 *
 * @param int $cmid Course module id.
 * @param string $action Current action.
 * @param int $mediaid Optional media id.
 * @return moodle_url
 */
function mod_uckkarchive_media_editor_form_url(int $cmid, string $action, int $mediaid = 0): moodle_url {
    $params = [
        'id' => $cmid,
        'action' => $action,
    ];

    if ($mediaid > 0) {
        $params['mediaid'] = $mediaid;
    }

    return new moodle_url('/mod/uckkarchive/media.php', $params);
}

/**
 * Prepare a media record for the existing media form.
 *
 * @param stdClass $media Media record.
 * @param stdClass $course Course record.
 * @param stdClass $cm Course module record.
 * @param stdClass $archive Archive instance.
 * @param context_module $context Module context.
 * @return stdClass
 */
function mod_uckkarchive_media_prepare_editor_form_data(
    stdClass $media,
    stdClass $course,
    stdClass $cm,
    stdClass $archive,
    context_module $context
): stdClass {
    $data = clone $media;

    $data->id = (int)$cm->id;
    $data->mediaid = (int)($media->id ?? 0);
    $data->archiveid = (int)$archive->id;
    $data->courseid = (int)$course->id;
    $data->cmid = (int)$cm->id;
    $data->contextid = (int)$context->id;

    if (!empty($media->licensekey) && empty($data->license)) {
        $data->license = (string)$media->licensekey;
    }

    if (!empty($media->rightsstatement) && empty($data->rightsnote)) {
        $data->rightsnote = (string)$media->rightsstatement;
    }

    if (!empty($media->rightsstatus) && empty($data->rightsnote)) {
        $data->rightsnote = (string)$media->rightsstatus;
    }

    if (!empty($media->source) && empty($data->sourcetype)) {
        $data->sourcetype = (string)$media->source;
    }

    if (!empty($media->metadata) && is_string($media->metadata)) {
        $decoded = json_decode($media->metadata, true);
        if (json_last_error() === JSON_ERROR_NONE && is_array($decoded)) {
            $data->metadata = json_encode($decoded, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
            $data->creator = (string)($decoded['creator'] ?? ($data->creator ?? ''));
            $data->datecreated = (string)($decoded['datecreated'] ?? ($data->datecreated ?? ''));
            $data->tags = !empty($decoded['keywords']) && is_array($decoded['keywords'])
                ? implode(', ', array_map('strval', $decoded['keywords']))
                : (string)($data->tags ?? '');
            $data->internalnote = (string)($decoded['notes'] ?? ($data->internalnote ?? ''));
        }
    }

    return $data;
}

/**
 * Convert submitted media form data into media persistence fields.
 *
 * @param stdClass $data Submitted form data.
 * @param stdClass $course Course record.
 * @param stdClass $cm Course module record.
 * @param stdClass $archive Archive instance.
 * @param context_module $context Module context.
 * @return array<string,mixed>
 */
function mod_uckkarchive_media_editor_record_from_form(
    stdClass $data,
    stdClass $course,
    stdClass $cm,
    stdClass $archive,
    context_module $context
): array {
    $metadata = mod_uckkarchive_media_editor_metadata_from_form($data);

    return [
        'archiveid' => (int)$archive->id,
        'courseid' => (int)$course->id,
        'cmid' => (int)$cm->id,
        'contextid' => (int)$context->id,
        'externalworkid' => (int)($data->externalworkid ?? 0),
        'title' => (string)($data->title ?? ''),
        'summary' => (string)($data->summary ?? ''),
        'description' => (string)($data->description ?? ''),
        'mediatype' => (string)($data->mediatype ?? 'document'),
        'sourcetype' => (string)($data->sourcetype ?? ''),
        'source' => (string)($data->sourcetype ?? ''),
        'sourceurl' => (string)($data->sourceurl ?? ''),
        'license' => (string)($data->license ?? ''),
        'licensekey' => (string)($data->license ?? ''),
        'rightsstatement' => (string)($data->rightsnote ?? ''),
        'status' => (string)($data->status ?? 'draft'),
        'visibility' => (string)($data->visibility ?? 'course'),
        'audiencesuitability' => (string)($data->audiencesuitability ?? 'guided'),
        'culturalprotocol' => !empty($data->culturalprotocolrequired) ? 1 : 0,
        'restricted' => mod_uckkarchive_media_editor_is_restricted_form_data($data) ? 1 : 0,
        'language' => (string)($data->language ?? ''),
        'metadata' => $metadata,
    ];
}

/**
 * Convert media-form metadata fields into a structured metadata array.
 *
 * @param stdClass $data Submitted form data.
 * @return array<string,mixed>
 */
function mod_uckkarchive_media_editor_metadata_from_form(stdClass $data): array {
    $metadata = [];

    $rawmetadata = trim((string)($data->metadata ?? ''));
    if ($rawmetadata !== '') {
        $decoded = json_decode($rawmetadata, true);
        if (json_last_error() === JSON_ERROR_NONE && is_array($decoded)) {
            $metadata = $decoded;
        } else {
            $metadata['notes_raw'] = $rawmetadata;
        }
    }

    foreach ([
        'creator',
        'datecreated',
        'alttext',
        'transcriptsummary',
        'collectionhint',
        'advisoryhint',
        'advisoryseverity',
        'culturalprotocolnote',
        'sourceownership',
        'citation',
        'externalworktitle',
        'externalworktype',
        'externalworkcreator',
        'externalworkyear',
        'externalworkidentifier',
        'externalworknote',
        'internalnote',
    ] as $field) {
        if (isset($data->{$field}) && trim((string)$data->{$field}) !== '') {
            $metadata[$field] = (string)$data->{$field};
        }
    }

    $tags = trim((string)($data->tags ?? ''));
    if ($tags !== '') {
        $decodedtags = json_decode($tags, true);
        if (json_last_error() === JSON_ERROR_NONE && is_array($decodedtags)) {
            $metadata['keywords'] = array_values(array_map('strval', $decodedtags));
        } else {
            $metadata['keywords'] = array_values(array_filter(array_map('trim', explode(',', $tags)), 'strlen'));
        }
    }

    if (!empty($data->hasadvisory)) {
        $metadata['hasadvisory'] = true;
    }

    if (!empty($data->culturalprotocolrequired)) {
        $metadata['culturalprotocolrequired'] = true;
    }

    return $metadata;
}

/**
 * Whether submitted form data implies restricted handling.
 *
 * @param stdClass $data Submitted form data.
 * @return bool
 */
function mod_uckkarchive_media_editor_is_restricted_form_data(stdClass $data): bool {
    $visibility = (string)($data->visibility ?? '');
    $audience = (string)($data->audiencesuitability ?? '');
    $status = (string)($data->status ?? '');

    return in_array($visibility, ['restricted', 'restricted_integrity', 'restricted_cultural'], true)
        || in_array($audience, ['restricted', 'restricted_integrity', 'restricted_cultural', 'staff_only'], true)
        || $status === 'restricted'
        || !empty($data->culturalprotocolrequired);
}

/**
 * Load media records for the current request.
 *
 * @param int $archiveid Archive id.
 * @param context_module $context Module context.
 * @param array<string,mixed> $filters Search filters.
 * @return stdClass Object with items, total, page, and perpage.
 */
function mod_uckkarchive_media_load_media(int $archiveid, context_module $context, array $filters): stdClass {
    $result = new stdClass();
    $result->items = [];
    $result->total = 0;
    $result->page = max(0, (int)$filters['page']);
    $result->perpage = max(1, (int)$filters['perpage']);

    if (!mod_uckkarchive_media_table_exists('uckkarchive_media')) {
        return $result;
    }

    $offset = $result->page * $result->perpage;

    if ((int)$filters['collectionid'] > 0
            && mod_uckkarchive_media_table_exists('uckkarchive_media_collection_item')) {
        $collectionid = (int)$filters['collectionid'];

        $result->items = array_values(media_collection::get_media($collectionid, $offset, $result->perpage));
        $result->total = media_collection::count_media($collectionid);

        return $result;
    }

    $search = media_search::search_with_count(
        $archiveid,
        $context,
        $filters,
        $result->perpage,
        $offset
    );

    $result->items = array_values($search->items ?? []);
    $result->total = (int)($search->total ?? 0);

    return $result;
}

/**
 * Load media collections for the current archive.
 *
 * @param int $archiveid Archive id.
 * @param array<string,mixed> $filters Current filters.
 * @return array<int,stdClass>
 */
function mod_uckkarchive_media_load_collections(int $archiveid, array $filters): array {
    if (!mod_uckkarchive_media_table_exists('uckkarchive_media_collection')) {
        return [];
    }

    $collectionfilters = [];

    if (!empty($filters['search'])) {
        $collectionfilters['search'] = $filters['search'];
    }

    if (!empty($filters['visibility'])) {
        $collectionfilters['visibility'] = $filters['visibility'];
    }

    return array_values(media_collection::get_collections_by_archive($archiveid, $collectionfilters, 0, 100));
}

/**
 * Trigger a media-library view event when possible.
 *
 * @param context_module $context Module context.
 * @param stdClass $archive Archive instance.
 * @param stdClass $course Course record.
 * @param stdClass $cm Course module.
 * @param array<string,mixed> $filters Filters.
 * @return void
 */
function mod_uckkarchive_media_trigger_view_event(
    context_module $context,
    stdClass $archive,
    stdClass $course,
    stdClass $cm,
    array $filters
): void {
    $eventclass = '\\mod_uckkarchive\\event\\archive_viewed';

    if (!class_exists($eventclass)) {
        return;
    }

    $event = $eventclass::create([
        'context' => $context,
        'objectid' => (int)$archive->id,
        'other' => [
            'courseid' => (int)$course->id,
            'cmid' => (int)$cm->id,
            'archiveid' => (int)$archive->id,
            'area' => 'media_library',
            'action' => (string)$filters['action'],
            'mediaid' => (int)$filters['mediaid'],
            'collectionid' => (int)$filters['collectionid'],
        ],
    ]);

    $event->add_record_snapshot('course', $course);
    $event->add_record_snapshot('course_modules', $cm);
    $event->add_record_snapshot('uckkarchive', $archive);
    $event->trigger();
}

$id = optional_param('id', 0, PARAM_INT); // Course module id.
$a = optional_param('a', 0, PARAM_INT); // Archive instance id.
$mediaid = optional_param('mediaid', 0, PARAM_INT);
$collectionid = optional_param('collectionid', 0, PARAM_INT);
$externalworkid = optional_param('externalworkid', 0, PARAM_INT);
$contentmarkerid = optional_param('contentmarkerid', 0, PARAM_INT);
$action = mod_uckkarchive_media_normalise_action(optional_param('action', 'library', PARAM_ALPHANUMEXT));
$returnurl = optional_param('returnurl', '', PARAM_LOCALURL);

if ($mediaid > 0 && $action === 'library') {
    $action = 'view';
}

if ($collectionid > 0 && $action === 'library') {
    $action = 'collection';
}

if ($externalworkid > 0 && $action === 'library') {
    $action = 'externalwork';
}

if ($contentmarkerid > 0 && $action === 'library') {
    $action = 'advisories';
}

$resolution = mod_uckkarchive_media_resolve_request(
    $id,
    $a,
    $mediaid,
    $collectionid,
    $externalworkid,
    $contentmarkerid
);

$course = $resolution->course;
$cm = $resolution->cm;
$archive = $resolution->archive;
$context = $resolution->context;
$media = $resolution->media ?? null;
$collection = $resolution->collection ?? null;

if ($media !== null) {
    $mediaid = (int)$media->id;
}

if ($collection !== null) {
    $collectionid = (int)$collection->id;
}

$filters = mod_uckkarchive_media_build_filters($mediaid, $collectionid, $externalworkid, $action);

require_login($course, false, $cm);
mod_uckkarchive_media_require_action_capabilities($context, $action, $filters, $media, $collection);

$pageurl = mod_uckkarchive_media_build_page_url((int)$cm->id, $filters);
$libraryurl = new moodle_url('/mod/uckkarchive/media.php', ['id' => (int)$cm->id]);
$viewurl = new moodle_url('/mod/uckkarchive/view.php', ['id' => (int)$cm->id]);
$return = $returnurl !== '' ? new moodle_url($returnurl) : $libraryurl;

$PAGE->set_url($pageurl);
$PAGE->set_course($course);
$PAGE->set_cm($cm);
$PAGE->set_context($context);
$PAGE->set_pagelayout('incourse');

$pagetitle = format_string($archive->name) . ': ' . mod_uckkarchive_media_string('medialibrary', 'Media library');
if (mod_uckkarchive_media_is_detail_action($action) && $media !== null) {
    $pagetitle = format_string($archive->name) . ': ' . format_string((string)($media->title ?? ''));
}

$PAGE->set_title($pagetitle);
$PAGE->set_heading(format_string($course->fullname));

$PAGE->navbar->add(format_string($archive->name), $viewurl);
$PAGE->navbar->add(mod_uckkarchive_media_string('medialibrary', 'Media library'), $libraryurl);

if (mod_uckkarchive_media_is_detail_action($action) && $media !== null) {
    $PAGE->navbar->add(format_string((string)($media->title ?? '')), $pageurl);
}

$editorform = null;
if (mod_uckkarchive_media_is_editor_action($action)) {
    $formurl = mod_uckkarchive_media_editor_form_url((int)$cm->id, $action, $mediaid);
    $editorform = new media_form($formurl, [
        'context' => $context,
        'course' => $course,
        'cm' => $cm,
        'archive' => $archive,
        'archiveid' => (int)$archive->id,
        'courseid' => (int)$course->id,
        'cmid' => (int)$cm->id,
        'contextid' => (int)$context->id,
        'returnurl' => $libraryurl->out(false),
    ]);

    if ($media !== null) {
        $editorform->set_data(mod_uckkarchive_media_prepare_editor_form_data($media, $course, $cm, $archive, $context));
    }

    if ($editorform->is_cancelled()) {
        redirect($libraryurl);
    }

    if (($formdata = $editorform->get_data()) !== null) {
        $record = mod_uckkarchive_media_editor_record_from_form($formdata, $course, $cm, $archive, $context);

        if ($action === 'edit') {
            if ($media === null) {
                throw new moodle_exception('missingparam', 'error', '', 'mediaid');
            }

            $saved = media_record::update($mediaid, $record);
            $message = mod_uckkarchive_media_string('mediaupdated', 'Media updated.');
        } else {
            $saved = media_record::create($record);
            $message = mod_uckkarchive_media_string('mediacreated', 'Media created.');
        }

        redirect(
            new moodle_url('/mod/uckkarchive/media.php', [
                'id' => (int)$cm->id,
                'mediaid' => (int)$saved->id,
                'action' => 'edit',
            ]),
            $message,
            null,
            notification::NOTIFY_SUCCESS
        );
    }
}

$PAGE->requires->js_call_amd('mod_uckkarchive/media', 'init', [[
    'root' => 'uckkarchive-media-library',
    'cmid' => (int)$cm->id,
    'archiveid' => (int)$archive->id,
    'contextid' => (int)$context->id,
    'mediaid' => $mediaid,
    'collectionid' => $collectionid,
    'action' => $action,
]]);

if (mod_uckkarchive_media_is_editor_action($action)) {
    $PAGE->requires->js_call_amd('mod_uckkarchive/media_library_editor', 'init', [[
        'root' => 'uckkarchive-media-library-editor',
        'cmid' => (int)$cm->id,
        'archiveid' => (int)$archive->id,
        'contextid' => (int)$context->id,
        'mediaid' => $mediaid,
        'action' => $action,
    ]]);
}

if ($action === 'collection' || $action === 'addcollection') {
    $PAGE->requires->js_call_amd('mod_uckkarchive/media_collection', 'init', [[
        'root' => 'uckkarchive-media-library',
        'cmid' => (int)$cm->id,
        'archiveid' => (int)$archive->id,
        'collectionid' => $collectionid,
    ]]);
}

if ($action === 'advisories') {
    $PAGE->requires->js_call_amd('mod_uckkarchive/content_advisory', 'init', [[
        'root' => 'uckkarchive-media-library',
        'cmid' => (int)$cm->id,
        'archiveid' => (int)$archive->id,
        'mediaid' => $mediaid,
        'contentmarkerid' => $contentmarkerid,
    ]]);
}

if ($action === 'externalwork') {
    $PAGE->requires->js_call_amd('mod_uckkarchive/external_work', 'init', [[
        'root' => 'uckkarchive-media-library',
        'cmid' => (int)$cm->id,
        'archiveid' => (int)$archive->id,
        'externalworkid' => $externalworkid,
    ]]);
}

$completion = new completion_info($course);
$completion->set_module_viewed($cm);

mod_uckkarchive_media_trigger_view_event($context, $archive, $course, $cm, $filters);

echo $OUTPUT->header();

try {
    $notificationmessage = '';
    $notificationtype = notification::NOTIFY_INFO;

    if (!mod_uckkarchive_media_table_exists('uckkarchive_media')) {
        $notificationmessage = mod_uckkarchive_media_string(
            'medialibrarynotinstalled',
            'The media library database tables are not installed yet.'
        );
        $notificationtype = notification::NOTIFY_WARNING;
    }

    $mediaresult = mod_uckkarchive_media_load_media((int)$archive->id, $context, $filters);
    $collections = mod_uckkarchive_media_load_collections((int)$archive->id, $filters);

    $renderer = $PAGE->get_renderer('mod_uckkarchive');
    $detailclass = '\\mod_uckkarchive\\output\\media_detail';

    if (mod_uckkarchive_media_is_detail_action($action)
            && $media !== null
            && class_exists($detailclass)
            && method_exists($renderer, 'render_media_detail')) {
        $renderable = new $detailclass(
            $context,
            $course,
            $cm,
            $archive,
            $media,
            $filters,
            $notificationmessage,
            $notificationtype
        );

        echo $renderer->render($renderable);
    } else if (mod_uckkarchive_media_is_editor_action($action) && $editorform !== null) {
        ob_start();
        $editorform->display();
        $formhtml = (string)ob_get_clean();

        $renderable = new media_library_editor(
            $context,
            $course,
            $cm,
            $archive,
            $media,
            $formhtml,
            $action,
            $notificationmessage,
            $notificationtype
        );

        echo $renderer->render($renderable);
    } else {
        if (mod_uckkarchive_media_is_detail_action($action) && $media !== null) {
            $mediaresult->items = [$media];
            $mediaresult->total = 1;
            $mediaresult->page = 0;
            $collections = [];
        }

        $renderable = new media_library(
            $context,
            $course,
            $cm,
            $archive,
            $mediaresult->items,
            $collections,
            $filters,
            (int)$mediaresult->total,
            (int)$mediaresult->page,
            (int)$mediaresult->perpage,
            $notificationmessage,
            $notificationtype
        );

        echo $renderer->render($renderable);
    }
} catch (required_capability_exception $exception) {
    debugging($exception->getMessage(), DEBUG_DEVELOPER, $exception->getTrace());

    echo $OUTPUT->notification(
        mod_uckkarchive_media_string('nopermissiontoviewmedia', 'You do not have permission to view this media library.'),
        notification::NOTIFY_ERROR
    );
    echo $OUTPUT->continue_button($return);
} catch (Throwable $exception) {
    debugging($exception->getMessage(), DEBUG_DEVELOPER, $exception->getTrace());

    echo $OUTPUT->notification(
        mod_uckkarchive_media_string('medialibraryerror', 'The media library could not be loaded.'),
        notification::NOTIFY_ERROR
    );
    echo $OUTPUT->continue_button($return);
}

echo $OUTPUT->footer();
