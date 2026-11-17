<?php
// This file is part of Moodle - https://moodle.org/
//
// Moodle is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// any later version.

/**
 * Export controller for UCKK Archives.
 *
 * @package    mod_uckkarchive
 * @copyright  2026 Univers-Cité King Klown
 * @license    https://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later
 */

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
require_once(__DIR__ . '/locallib.php');
require_once($CFG->libdir . '/filelib.php');

defined('MOODLE_INTERNAL') || die();

use core\output\notification;

/**
 * Plugin component.
 */
define('UCKKARCHIVE_EXPORT_COMPONENT', 'mod_uckkarchive');

/**
 * Allowed archive export formats.
 *
 * The synchronous controller exports metadata/manifest payloads. Heavy binary
 * ZIP/package generation is handled by export service records and scheduled
 * package tasks.
 *
 * @return string[]
 */
function uckkarchive_export_allowed_formats(): array {
    return [
        'json',
        'html',
        'csv',
    ];
}

/**
 * Allowed archive export scopes.
 *
 * @return string[]
 */
function uckkarchive_export_allowed_scopes(): array {
    return [
        'archive',
        'item',
        'portfolio',
        'media',
        'collection',
        'external_work',
    ];
}

/**
 * Allowed archive export visibilities.
 *
 * @return string[]
 */
function uckkarchive_export_allowed_visibilities(): array {
    return [
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
}

/**
 * Allowed export redaction levels.
 *
 * @return string[]
 */
function uckkarchive_export_allowed_redaction_levels(): array {
    return [
        'none',
        'hide_identity',
        'hide_restricted',
        'metadata_only',
    ];
}

/**
 * Media file areas that can be listed in manifests.
 *
 * @return string[]
 */
function uckkarchive_export_media_fileareas(): array {
    return [
        'media_original',
        'media_preview',
        'media_thumbnail',
        'media_derivative',
        'media_caption',
        'media_transcript',
        'media_attachment',
    ];
}

/**
 * Return translated string with fallback.
 *
 * @param string $identifier Identifier.
 * @param string $fallback Fallback text.
 * @return string
 */
function uckkarchive_export_string(string $identifier, string $fallback): string {
    if (get_string_manager()->string_exists($identifier, 'uckkarchive')) {
        return get_string($identifier, 'uckkarchive');
    }

    return $fallback;
}

/**
 * Normalise one key against an allow-list.
 *
 * @param string $value Raw value.
 * @param string[] $allowed Allowed values.
 * @param string $default Default value.
 * @return string
 */
function uckkarchive_export_normalise_choice(string $value, array $allowed, string $default): string {
    $value = clean_param($value, PARAM_ALPHANUMEXT);

    return in_array($value, $allowed, true) ? $value : $default;
}

/**
 * Normalise export id list.
 *
 * @param string $raw Raw comma-separated ids.
 * @return int[]
 */
function uckkarchive_export_normalise_ids(string $raw): array {
    if (trim($raw) === '') {
        return [];
    }

    $ids = [];

    foreach (preg_split('/[,\s]+/', $raw) as $part) {
        $id = clean_param($part, PARAM_INT);

        if ($id > 0) {
            $ids[$id] = $id;
        }
    }

    return array_values($ids);
}

/**
 * Check whether a table exists.
 *
 * @param string $table Table name without prefix.
 * @return bool
 */
function uckkarchive_export_table_exists(string $table): bool {
    global $DB;

    return $DB->get_manager()->table_exists(new xmldb_table($table));
}

/**
 * Check whether a field exists.
 *
 * @param string $table Table name without prefix.
 * @param string $field Field name.
 * @return bool
 */
function uckkarchive_export_field_exists(string $table, string $field): bool {
    global $DB;

    if (!uckkarchive_export_table_exists($table)) {
        return false;
    }

    return $DB->get_manager()->field_exists(new xmldb_table($table), new xmldb_field($field));
}

/**
 * Return table column names.
 *
 * @param string $table Table name.
 * @return array<string, bool>
 */
function uckkarchive_export_table_columns(string $table): array {
    global $DB;

    if (!uckkarchive_export_table_exists($table)) {
        return [];
    }

    return array_fill_keys(array_keys($DB->get_columns($table)), true);
}

/**
 * Return first existing column name from candidates.
 *
 * @param string $table Table.
 * @param string[] $candidates Candidate columns.
 * @return string|null
 */
function uckkarchive_export_first_field(string $table, array $candidates): ?string {
    $columns = uckkarchive_export_table_columns($table);

    foreach ($candidates as $candidate) {
        if (isset($columns[$candidate])) {
            return $candidate;
        }
    }

    return null;
}

/**
 * Filter a record to existing table fields.
 *
 * @param string $table Table.
 * @param stdClass $record Record.
 * @return stdClass
 */
function uckkarchive_export_filter_record_for_table(string $table, stdClass $record): stdClass {
    $columns = uckkarchive_export_table_columns($table);
    $filtered = new stdClass();

    foreach ((array)$record as $field => $value) {
        if (isset($columns[$field])) {
            $filtered->{$field} = $value;
        }
    }

    return $filtered;
}

/**
 * Return whether a capability exists in Moodle.
 *
 * @param string $capability Capability name.
 * @return bool
 */
function uckkarchive_export_capability_exists(string $capability): bool {
    global $DB;

    if (function_exists('get_capability_info')) {
        return (bool)get_capability_info($capability);
    }

    return $DB->record_exists('capabilities', ['name' => $capability]);
}

/**
 * Require capability if it exists; otherwise optionally fall back.
 *
 * @param string $capability Capability.
 * @param context_module $context Context.
 * @param string|null $fallback Fallback capability.
 */
function uckkarchive_export_require_capability(string $capability, context_module $context, ?string $fallback = null): void {
    if (uckkarchive_export_capability_exists($capability)) {
        require_capability($capability, $context);
        return;
    }

    if ($fallback !== null) {
        require_capability($fallback, $context);
    }
}

/**
 * Return whether user has a capability when it exists.
 *
 * @param string $capability Capability.
 * @param context_module $context Context.
 * @param string|null $fallback Fallback capability.
 * @return bool
 */
function uckkarchive_export_has_capability(string $capability, context_module $context, ?string $fallback = null): bool {
    if (uckkarchive_export_capability_exists($capability)) {
        return has_capability($capability, $context);
    }

    if ($fallback !== null) {
        return has_capability($fallback, $context);
    }

    return false;
}

/**
 * Return whether a visibility is restricted.
 *
 * @param string $visibility Visibility key.
 * @return bool
 */
function uckkarchive_export_visibility_is_restricted(string $visibility): bool {
    return in_array($visibility, [
        'private',
        'restricted',
        'restricted_integrity',
        'restricted_cultural',
    ], true);
}

/**
 * Return whether a record looks culturally restricted.
 *
 * @param stdClass $record Record.
 * @return bool
 */
function uckkarchive_export_record_is_culturally_restricted(stdClass $record): bool {
    foreach (['visibility', 'audiencesuitability', 'restrictiontype'] as $field) {
        if (!empty($record->{$field}) && (string)$record->{$field} === 'restricted_cultural') {
            return true;
        }
    }

    if (!empty($record->culturalprotocol) || !empty($record->iscultural) || !empty($record->culturallyrestricted)) {
        return true;
    }

    return false;
}

/**
 * Return whether a record is restricted.
 *
 * @param stdClass $record Record.
 * @return bool
 */
function uckkarchive_export_record_is_restricted(stdClass $record): bool {
    if (!empty($record->restricted) || !empty($record->isrestricted)) {
        return true;
    }

    foreach (['visibility', 'audiencesuitability', 'severity'] as $field) {
        if (empty($record->{$field})) {
            continue;
        }

        if (in_array((string)$record->{$field}, [
            'private',
            'restricted',
            'restricted_integrity',
            'restricted_cultural',
            'staff_only',
        ], true)) {
            return true;
        }
    }

    return false;
}

/**
 * Require restricted archive capability when needed.
 *
 * @param string $visibility Visibility key.
 * @param context_module $context Module context.
 */
function uckkarchive_export_require_visibility_capability(string $visibility, context_module $context): void {
    if (!uckkarchive_export_visibility_is_restricted($visibility)) {
        return;
    }

    uckkarchive_export_require_capability(
        'mod/uckkarchive:viewrestricted',
        $context,
        'mod/uckkarchive:export'
    );
}

/**
 * Require access to a restricted record.
 *
 * @param stdClass $record Record.
 * @param context_module $context Context.
 */
function uckkarchive_export_require_record_access(stdClass $record, context_module $context): void {
    $visibility = (string)($record->visibility ?? 'course');
    uckkarchive_export_require_visibility_capability($visibility, $context);

    if (uckkarchive_export_record_is_restricted($record)) {
        uckkarchive_export_require_capability(
            'mod/uckkarchive:viewrestrictedmedia',
            $context,
            'mod/uckkarchive:viewrestricted'
        );
    }

    if (uckkarchive_export_record_is_culturally_restricted($record)) {
        uckkarchive_export_require_capability(
            'mod/uckkarchive:viewculturallyrestricted',
            $context,
            'mod/uckkarchive:viewrestricted'
        );
    }
}

/**
 * Fetch one archive item with visibility protection.
 *
 * @param int $itemid Archive item id.
 * @param stdClass $archive Archive instance.
 * @param context_module $context Module context.
 * @return stdClass
 */
function uckkarchive_export_get_item(int $itemid, stdClass $archive, context_module $context): stdClass {
    global $DB;

    $item = $DB->get_record('uckkarchive_item', [
        'id' => $itemid,
        'archiveid' => $archive->id,
    ], '*', MUST_EXIST);

    uckkarchive_export_require_record_access($item, $context);

    return $item;
}

/**
 * Fetch exportable archive items.
 *
 * @param stdClass $archive Archive instance.
 * @param context_module $context Module context.
 * @param int $itemid Optional single item id.
 * @param string $scope Scope.
 * @param bool $includerestricted Whether restricted data is included.
 * @return stdClass[]
 */
function uckkarchive_export_get_items(
    stdClass $archive,
    context_module $context,
    int $itemid = 0,
    string $scope = 'archive',
    bool $includerestricted = false
): array {
    global $DB;

    if (!uckkarchive_export_table_exists('uckkarchive_item')) {
        return [];
    }

    if ($itemid > 0) {
        return [uckkarchive_export_get_item($itemid, $archive, $context)];
    }

    $conditions = ['archiveid = :archiveid'];
    $params = ['archiveid' => $archive->id];

    if ($scope === 'portfolio' && uckkarchive_export_field_exists('uckkarchive_item', 'itemtype')) {
        $conditions[] = 'itemtype = :itemtype';
        $params['itemtype'] = 'portfolio';
    }

    $items = $DB->get_records_select(
        'uckkarchive_item',
        implode(' AND ', $conditions),
        $params,
        'timecreated ASC, id ASC'
    );

    $exportable = [];

    foreach ($items as $item) {
        if (uckkarchive_export_record_is_restricted($item) && !$includerestricted) {
            continue;
        }

        uckkarchive_export_require_record_access($item, $context);
        $exportable[] = $item;
    }

    return $exportable;
}

/**
 * Fetch records by archive id.
 *
 * @param string $table Table.
 * @param int $archiveid Archive id.
 * @param string $orderby Order by.
 * @return stdClass[]
 */
function uckkarchive_export_get_archive_records(string $table, int $archiveid, string $orderby = 'id ASC'): array {
    global $DB;

    if (!uckkarchive_export_table_exists($table) || !uckkarchive_export_field_exists($table, 'archiveid')) {
        return [];
    }

    return array_values($DB->get_records($table, ['archiveid' => $archiveid], $orderby));
}

/**
 * Fetch records by field.
 *
 * @param string $table Table.
 * @param string $field Field.
 * @param int $value Value.
 * @param string $orderby Order by.
 * @return stdClass[]
 */
function uckkarchive_export_get_records_by_field(string $table, string $field, int $value, string $orderby = 'id ASC'): array {
    global $DB;

    if (!uckkarchive_export_table_exists($table) || !uckkarchive_export_field_exists($table, $field)) {
        return [];
    }

    return array_values($DB->get_records($table, [$field => $value], $orderby));
}

/**
 * Fetch provenance records for an item.
 *
 * @param int $itemid Archive item id.
 * @return stdClass[]
 */
function uckkarchive_export_get_provenance(int $itemid): array {
    return uckkarchive_export_get_records_by_field('uckkarchive_prov', 'itemid', $itemid, 'timecreated ASC, id ASC');
}

/**
 * Fetch revision records for an item.
 *
 * @param int $itemid Archive item id.
 * @return stdClass[]
 */
function uckkarchive_export_get_revisions(int $itemid): array {
    return uckkarchive_export_get_records_by_field('uckkarchive_rev', 'itemid', $itemid, 'timecreated ASC, id ASC');
}

/**
 * Fetch proof records for an item.
 *
 * @param int $itemid Archive item id.
 * @return stdClass[]
 */
function uckkarchive_export_get_proofs(int $itemid): array {
    return uckkarchive_export_get_records_by_field('uckkarchive_proof', 'itemid', $itemid, 'timecreated ASC, id ASC');
}

/**
 * Fetch media records for export.
 *
 * @param stdClass $archive Archive.
 * @param context_module $context Context.
 * @param int[] $mediaids Specific media ids.
 * @param bool $includerestricted Include restricted records.
 * @return stdClass[]
 */
function uckkarchive_export_get_media(
    stdClass $archive,
    context_module $context,
    array $mediaids = [],
    bool $includerestricted = false
): array {
    global $DB;

    if (!uckkarchive_export_table_exists('uckkarchive_media')) {
        return [];
    }

    $params = ['archiveid' => (int)$archive->id];
    $select = 'archiveid = :archiveid';

    if ($mediaids) {
        [$insql, $inparams] = $DB->get_in_or_equal($mediaids, SQL_PARAMS_NAMED, 'mediaid');
        $select .= " AND id {$insql}";
        $params += $inparams;
    }

    $records = $DB->get_records_select('uckkarchive_media', $select, $params, 'timecreated ASC, id ASC');
    $media = [];

    foreach ($records as $record) {
        if (uckkarchive_export_record_is_restricted($record) && !$includerestricted) {
            continue;
        }

        uckkarchive_export_require_record_access($record, $context);
        $media[] = $record;
    }

    return $media;
}

/**
 * Fetch media collection records.
 *
 * @param stdClass $archive Archive.
 * @param context_module $context Context.
 * @param int $collectionid Collection id.
 * @param bool $includerestricted Include restricted.
 * @return stdClass[]
 */
function uckkarchive_export_get_collections(
    stdClass $archive,
    context_module $context,
    int $collectionid = 0,
    bool $includerestricted = false
): array {
    global $DB;

    if (!uckkarchive_export_table_exists('uckkarchive_media_collection')) {
        return [];
    }

    if ($collectionid > 0) {
        $collection = $DB->get_record('uckkarchive_media_collection', [
            'id' => $collectionid,
            'archiveid' => $archive->id,
        ], '*', MUST_EXIST);

        if (uckkarchive_export_record_is_restricted($collection) && !$includerestricted) {
            return [];
        }

        uckkarchive_export_require_record_access($collection, $context);

        return [$collection];
    }

    $records = $DB->get_records('uckkarchive_media_collection', [
        'archiveid' => $archive->id,
    ], 'timecreated ASC, id ASC');

    $collections = [];

    foreach ($records as $record) {
        if (uckkarchive_export_record_is_restricted($record) && !$includerestricted) {
            continue;
        }

        uckkarchive_export_require_record_access($record, $context);
        $collections[] = $record;
    }

    return $collections;
}

/**
 * Fetch media ids in a collection.
 *
 * @param int $collectionid Collection id.
 * @return int[]
 */
function uckkarchive_export_get_collection_media_ids(int $collectionid): array {
    if (!uckkarchive_export_table_exists('uckkarchive_media_collection_item')) {
        return [];
    }

    $records = uckkarchive_export_get_records_by_field(
        'uckkarchive_media_collection_item',
        'collectionid',
        $collectionid,
        'sortorder ASC, id ASC'
    );

    $ids = [];

    foreach ($records as $record) {
        if (!empty($record->mediaid)) {
            $ids[(int)$record->mediaid] = (int)$record->mediaid;
        }
    }

    return array_values($ids);
}

/**
 * Fetch external works.
 *
 * @param stdClass $archive Archive.
 * @param context_module $context Context.
 * @param int $externalworkid External work id.
 * @param bool $includerestricted Include restricted.
 * @return stdClass[]
 */
function uckkarchive_export_get_external_works(
    stdClass $archive,
    context_module $context,
    int $externalworkid = 0,
    bool $includerestricted = false
): array {
    global $DB;

    if (!uckkarchive_export_table_exists('uckkarchive_external_work')) {
        return [];
    }

    if ($externalworkid > 0) {
        $record = $DB->get_record('uckkarchive_external_work', [
            'id' => $externalworkid,
            'archiveid' => $archive->id,
        ], '*', MUST_EXIST);

        if (uckkarchive_export_record_is_restricted($record) && !$includerestricted) {
            return [];
        }

        uckkarchive_export_require_record_access($record, $context);

        return [$record];
    }

    $records = $DB->get_records('uckkarchive_external_work', [
        'archiveid' => $archive->id,
    ], 'timecreated ASC, id ASC');

    $works = [];

    foreach ($records as $record) {
        if (uckkarchive_export_record_is_restricted($record) && !$includerestricted) {
            continue;
        }

        uckkarchive_export_require_record_access($record, $context);
        $works[] = $record;
    }

    return $works;
}

/**
 * Fetch content markers for a target.
 *
 * @param string $targettype Target type.
 * @param int $targetid Target id.
 * @return stdClass[]
 */
function uckkarchive_export_get_content_markers(string $targettype, int $targetid): array {
    global $DB;

    if (!uckkarchive_export_table_exists('uckkarchive_content_marker')) {
        return [];
    }

    if ($targettype === 'media' && uckkarchive_export_field_exists('uckkarchive_content_marker', 'mediaid')) {
        return uckkarchive_export_get_records_by_field(
            'uckkarchive_content_marker',
            'mediaid',
            $targetid,
            'id ASC'
        );
    }

    if ($targettype === 'external_work' && uckkarchive_export_field_exists('uckkarchive_content_marker', 'externalworkid')) {
        return uckkarchive_export_get_records_by_field(
            'uckkarchive_content_marker',
            'externalworkid',
            $targetid,
            'id ASC'
        );
    }

    if (uckkarchive_export_field_exists('uckkarchive_content_marker', 'targettype') &&
            uckkarchive_export_field_exists('uckkarchive_content_marker', 'targetid')) {
        return array_values($DB->get_records('uckkarchive_content_marker', [
            'targettype' => $targettype,
            'targetid' => $targetid,
        ], 'id ASC'));
    }

    return [];
}

/**
 * Fetch content reviews for a marker.
 *
 * @param int $markerid Marker id.
 * @return stdClass[]
 */
function uckkarchive_export_get_content_reviews(int $markerid): array {
    if (!uckkarchive_export_table_exists('uckkarchive_content_review')) {
        return [];
    }

    $field = uckkarchive_export_first_field('uckkarchive_content_review', ['markerid', 'contentmarkerid']);

    if ($field === null) {
        return [];
    }

    return uckkarchive_export_get_records_by_field(
        'uckkarchive_content_review',
        $field,
        $markerid,
        'timecreated ASC, id ASC'
    );
}

/**
 * Fetch media versions.
 *
 * @param int $mediaid Media id.
 * @return stdClass[]
 */
function uckkarchive_export_get_media_versions(int $mediaid): array {
    if (!uckkarchive_export_table_exists('uckkarchive_media_version')) {
        return [];
    }

    $field = uckkarchive_export_first_field('uckkarchive_media_version', ['mediaid']);

    if ($field === null) {
        return [];
    }

    return uckkarchive_export_get_records_by_field(
        'uckkarchive_media_version',
        $field,
        $mediaid,
        'versionno ASC, id ASC'
    );
}

/**
 * Fetch media relations.
 *
 * @param int $mediaid Media id.
 * @return stdClass[]
 */
function uckkarchive_export_get_media_relations(int $mediaid): array {
    global $DB;

    if (!uckkarchive_export_table_exists('uckkarchive_media_relation')) {
        return [];
    }

    $conditions = [];
    $params = [];

    foreach (['mediaid', 'fromid', 'toid', 'sourcemediaid', 'targetmediaid'] as $field) {
        if (!uckkarchive_export_field_exists('uckkarchive_media_relation', $field)) {
            continue;
        }

        $param = 'rel_' . $field;
        $conditions[] = "{$field} = :{$param}";
        $params[$param] = $mediaid;
    }

    if (!$conditions) {
        return [];
    }

    return array_values($DB->get_records_select(
        'uckkarchive_media_relation',
        implode(' OR ', $conditions),
        $params,
        'id ASC'
    ));
}

/**
 * Fetch media tags.
 *
 * @param int $mediaid Media id.
 * @return stdClass[]
 */
function uckkarchive_export_get_media_tags(int $mediaid): array {
    $field = uckkarchive_export_first_field('uckkarchive_media_tag', ['mediaid', 'itemid']);

    if ($field === null) {
        return [];
    }

    return uckkarchive_export_get_records_by_field('uckkarchive_media_tag', $field, $mediaid, 'id ASC');
}

/**
 * Convert a database record to a clean export array.
 *
 * @param stdClass $record Record.
 * @param bool $includemetadata Whether to include metadata JSON.
 * @param bool $redact Whether to redact sensitive fields.
 * @return array<string, mixed>
 */
function uckkarchive_export_record_to_array(
    stdClass $record,
    bool $includemetadata = true,
    bool $redact = false
): array {
    $data = [];

    $restrictedtextfields = [
        'content',
        'description',
        'summary',
        'notes',
        'note',
        'rationale',
        'reviewnote',
        'transcript',
        'caption',
        'locator',
        'locatorlabel',
        'citation',
        'rightsstatement',
        'sourcenote',
        'teachingnote',
        'culturalprotocolnote',
        'auditnote',
    ];

    foreach ((array)$record as $key => $value) {
        if (!$includemetadata && $key === 'metadata') {
            continue;
        }

        if ($redact && in_array($key, $restrictedtextfields, true)) {
            $data[$key] = uckkarchive_export_string('redacted', '[redacted]');
            continue;
        }

        if ($key === 'metadata' && is_string($value) && trim($value) !== '') {
            $decoded = json_decode($value, true);
            $data[$key] = json_last_error() === JSON_ERROR_NONE ? $decoded : $value;
            continue;
        }

        $data[$key] = $value;
    }

    if ($redact) {
        $data['redacted'] = true;
    }

    return $data;
}

/**
 * Convert stored_file metadata to an export-safe array.
 *
 * @param stored_file $file File.
 * @return array<string, mixed>
 */
function uckkarchive_export_file_to_array(stored_file $file): array {
    return [
        'filename' => $file->get_filename(),
        'filepath' => $file->get_filepath(),
        'filesize' => $file->get_filesize(),
        'mimetype' => $file->get_mimetype(),
        'contenthash' => $file->get_contenthash(),
        'timecreated' => $file->get_timecreated(),
        'timemodified' => $file->get_timemodified(),
    ];
}

/**
 * Fetch file metadata for a record.
 *
 * @param context_module $context Context.
 * @param string[] $fileareas File areas.
 * @param int $itemid File item id.
 * @return array<string, array<int, array<string, mixed>>>
 */
function uckkarchive_export_get_file_manifest(context_module $context, array $fileareas, int $itemid): array {
    $fs = get_file_storage();
    $manifest = [];

    foreach ($fileareas as $filearea) {
        $files = $fs->get_area_files(
            $context->id,
            UCKKARCHIVE_EXPORT_COMPONENT,
            $filearea,
            $itemid,
            'filepath, filename',
            false
        );

        $manifest[$filearea] = array_map('uckkarchive_export_file_to_array', array_values($files));
    }

    return $manifest;
}

/**
 * Build one archive item export entry.
 *
 * @param stdClass $item Item.
 * @param context_module $context Context.
 * @param array<string, mixed> $options Options.
 * @return array<string, mixed>
 */
function uckkarchive_export_build_item_entry(stdClass $item, context_module $context, array $options): array {
    $redact = uckkarchive_export_record_is_restricted($item) && empty($options['includerestricted']);
    $entry = uckkarchive_export_record_to_array($item, !empty($options['includemetadata']), $redact);

    if (!empty($options['includeprovenance'])) {
        $entry['provenance_records'] = array_map(
            static function(stdClass $record) use ($options): array {
                return uckkarchive_export_record_to_array($record, !empty($options['includemetadata']));
            },
            uckkarchive_export_get_provenance((int)$item->id)
        );
    }

    if (!empty($options['includerevisions']) || !empty($options['includeversions'])) {
        $entry['revision_records'] = array_map(
            static function(stdClass $record) use ($options): array {
                return uckkarchive_export_record_to_array($record, !empty($options['includemetadata']));
            },
            uckkarchive_export_get_revisions((int)$item->id)
        );
    }

    if (!empty($options['includeproofs'])) {
        $entry['proof_records'] = array_map(
            static function(stdClass $record) use ($options): array {
                return uckkarchive_export_record_to_array($record, !empty($options['includemetadata']));
            },
            uckkarchive_export_get_proofs((int)$item->id)
        );
    }

    if (!empty($options['includefiles'])) {
        $entry['files'] = uckkarchive_export_get_file_manifest($context, [
            'item_content',
            'proof_files',
            'decision_attachments',
            'minutes_files',
            'portfolio_files',
        ], (int)$item->id);
    }

    return $entry;
}

/**
 * Build one media export entry.
 *
 * @param stdClass $media Media.
 * @param context_module $context Context.
 * @param array<string, mixed> $options Options.
 * @return array<string, mixed>
 */
function uckkarchive_export_build_media_entry(stdClass $media, context_module $context, array $options): array {
    $redact = uckkarchive_export_record_is_restricted($media) && empty($options['includerestricted']);
    $entry = uckkarchive_export_record_to_array($media, !empty($options['includemetadata']), $redact);

    if (!empty($options['includeversions'])) {
        $entry['versions'] = array_map(
            static function(stdClass $record) use ($options): array {
                return uckkarchive_export_record_to_array($record, !empty($options['includemetadata']));
            },
            uckkarchive_export_get_media_versions((int)$media->id)
        );
    }

    if (!empty($options['includerelations'])) {
        $entry['relations'] = array_map(
            static function(stdClass $record) use ($options): array {
                return uckkarchive_export_record_to_array($record, !empty($options['includemetadata']));
            },
            uckkarchive_export_get_media_relations((int)$media->id)
        );
    }

    if (!empty($options['includetags'])) {
        $entry['tags'] = array_map(
            static function(stdClass $record) use ($options): array {
                return uckkarchive_export_record_to_array($record, !empty($options['includemetadata']));
            },
            uckkarchive_export_get_media_tags((int)$media->id)
        );
    }

    if (!empty($options['includeadvisories'])) {
        $markers = [];

        foreach (uckkarchive_export_get_content_markers('media', (int)$media->id) as $marker) {
            $markerentry = uckkarchive_export_record_to_array($marker, !empty($options['includemetadata']), $redact);

            if (!empty($options['includereviews'])) {
                $markerentry['reviews'] = array_map(
                    static function(stdClass $record) use ($options): array {
                        return uckkarchive_export_record_to_array($record, !empty($options['includemetadata']));
                    },
                    uckkarchive_export_get_content_reviews((int)$marker->id)
                );
            }

            $markers[] = $markerentry;
        }

        $entry['content_markers'] = $markers;
    }

    if (!empty($options['includefiles'])) {
        $entry['files'] = uckkarchive_export_get_file_manifest(
            $context,
            uckkarchive_export_media_fileareas(),
            (int)$media->id
        );
    }

    return $entry;
}

/**
 * Build one collection export entry.
 *
 * @param stdClass $collection Collection.
 * @param stdClass $archive Archive.
 * @param context_module $context Context.
 * @param array<string, mixed> $options Options.
 * @return array<string, mixed>
 */
function uckkarchive_export_build_collection_entry(
    stdClass $collection,
    stdClass $archive,
    context_module $context,
    array $options
): array {
    $entry = uckkarchive_export_record_to_array(
        $collection,
        !empty($options['includemetadata']),
        uckkarchive_export_record_is_restricted($collection) && empty($options['includerestricted'])
    );

    $mediaids = uckkarchive_export_get_collection_media_ids((int)$collection->id);
    $entry['mediaids'] = $mediaids;

    if (!empty($options['includemedia'])) {
        $entry['media'] = array_map(
            static function(stdClass $media) use ($context, $options): array {
                return uckkarchive_export_build_media_entry($media, $context, $options);
            },
            uckkarchive_export_get_media($archive, $context, $mediaids, !empty($options['includerestricted']))
        );
    }

    return $entry;
}

/**
 * Build one external work export entry.
 *
 * @param stdClass $work External work.
 * @param context_module $context Context.
 * @param array<string, mixed> $options Options.
 * @return array<string, mixed>
 */
function uckkarchive_export_build_external_work_entry(
    stdClass $work,
    context_module $context,
    array $options
): array {
    $redact = uckkarchive_export_record_is_restricted($work) && empty($options['includerestricted']);
    $entry = uckkarchive_export_record_to_array($work, !empty($options['includemetadata']), $redact);

    if (!empty($options['includeadvisories'])) {
        $markers = [];

        foreach (uckkarchive_export_get_content_markers('external_work', (int)$work->id) as $marker) {
            $markerentry = uckkarchive_export_record_to_array($marker, !empty($options['includemetadata']), $redact);

            if (!empty($options['includereviews'])) {
                $markerentry['reviews'] = array_map(
                    static function(stdClass $record) use ($options): array {
                        return uckkarchive_export_record_to_array($record, !empty($options['includemetadata']));
                    },
                    uckkarchive_export_get_content_reviews((int)$marker->id)
                );
            }

            $markers[] = $markerentry;
        }

        $entry['content_markers'] = $markers;
    }

    if (!empty($options['includefiles'])) {
        $entry['files'] = uckkarchive_export_get_file_manifest($context, [
            'external_work_reference_files',
            'cultural_protocol_files',
        ], (int)$work->id);
    }

    return $entry;
}

/**
 * Build export package data.
 *
 * @param stdClass $archive Archive instance.
 * @param stdClass $course Course record.
 * @param cm_info|stdClass $cm Course module record.
 * @param context_module $context Module context.
 * @param array<string, mixed> $options Export options.
 * @return array<string, mixed>
 */
function uckkarchive_export_build_package(
    stdClass $archive,
    stdClass $course,
    $cm,
    context_module $context,
    array $options
): array {
    $itemid = (int)($options['itemid'] ?? 0);
    $mediaid = (int)($options['mediaid'] ?? 0);
    $collectionid = (int)($options['collectionid'] ?? 0);
    $externalworkid = (int)($options['externalworkid'] ?? 0);

    $mediaids = $options['mediaids'] ?? [];
    if ($mediaid > 0) {
        $mediaids[] = $mediaid;
        $mediaids = array_values(array_unique(array_map('intval', $mediaids)));
    }

    $scope = (string)($options['scope'] ?? 'archive');
    $includerestricted = !empty($options['includerestricted']);

    $items = [];
    $media = [];
    $collections = [];
    $externalworks = [];

    if (in_array($scope, ['archive', 'item', 'portfolio'], true)) {
        $items = array_map(
            static function(stdClass $item) use ($context, $options): array {
                return uckkarchive_export_build_item_entry($item, $context, $options);
            },
            uckkarchive_export_get_items($archive, $context, $itemid, $scope, $includerestricted)
        );
    }

    if ($scope === 'archive' && !empty($options['includemedia']) || $scope === 'media') {
        uckkarchive_export_require_capability(
            'mod/uckkarchive:exportmedia',
            $context,
            'mod/uckkarchive:export'
        );

        $media = array_map(
            static function(stdClass $record) use ($context, $options): array {
                return uckkarchive_export_build_media_entry($record, $context, $options);
            },
            uckkarchive_export_get_media($archive, $context, $mediaids, $includerestricted)
        );
    }

    if ($scope === 'archive' && !empty($options['includecollections']) || $scope === 'collection') {
        uckkarchive_export_require_capability(
            'mod/uckkarchive:exportmedia',
            $context,
            'mod/uckkarchive:export'
        );

        $collections = array_map(
            static function(stdClass $record) use ($archive, $context, $options): array {
                return uckkarchive_export_build_collection_entry($record, $archive, $context, $options);
            },
            uckkarchive_export_get_collections($archive, $context, $collectionid, $includerestricted)
        );
    }

    if ($scope === 'archive' && !empty($options['includeexternalworks']) || $scope === 'external_work') {
        $externalworks = array_map(
            static function(stdClass $record) use ($context, $options): array {
                return uckkarchive_export_build_external_work_entry($record, $context, $options);
            },
            uckkarchive_export_get_external_works($archive, $context, $externalworkid, $includerestricted)
        );
    }

    $restrictedcount = 0;

    foreach ([$items, $media, $collections, $externalworks] as $section) {
        foreach ($section as $record) {
            if (!empty($record['redacted']) ||
                    in_array((string)($record['visibility'] ?? ''), ['restricted', 'restricted_integrity', 'restricted_cultural'], true)) {
                $restrictedcount++;
            }
        }
    }

    return [
        'schema' => 'uckkarchive_export_v2',
        'component' => 'mod_uckkarchive',
        'product' => 'UCKK-Moodle',
        'generated_at' => time(),
        'generated_at_label' => userdate(time()),
        'course' => [
            'id' => (int)$course->id,
            'shortname' => $course->shortname,
            'fullname' => format_string($course->fullname),
        ],
        'archive' => [
            'id' => (int)$archive->id,
            'cmid' => (int)$cm->id,
            'name' => format_string($archive->name),
            'status' => $archive->status ?? 'active',
            'visibility' => $archive->visibility ?? 'course',
        ],
        'options' => [
            'scope' => $scope,
            'format' => $options['format'],
            'visibility' => $options['visibility'],
            'itemid' => $itemid,
            'mediaid' => $mediaid,
            'mediaids' => $mediaids,
            'collectionid' => $collectionid,
            'externalworkid' => $externalworkid,
            'includeprovenance' => !empty($options['includeprovenance']),
            'includerevisions' => !empty($options['includerevisions']),
            'includeversions' => !empty($options['includeversions']),
            'includeproofs' => !empty($options['includeproofs']),
            'includemetadata' => !empty($options['includemetadata']),
            'includerestricted' => !empty($options['includerestricted']),
            'includefiles' => !empty($options['includefiles']),
            'includemedia' => !empty($options['includemedia']),
            'includecollections' => !empty($options['includecollections']),
            'includeexternalworks' => !empty($options['includeexternalworks']),
            'includeadvisories' => !empty($options['includeadvisories']),
            'includereviews' => !empty($options['includereviews']),
            'includerelations' => !empty($options['includerelations']),
            'includetags' => !empty($options['includetags']),
            'redactionlevel' => $options['redactionlevel'],
        ],
        'counts' => [
            'items' => count($items),
            'media' => count($media),
            'collections' => count($collections),
            'external_works' => count($externalworks),
            'restricted_or_redacted' => $restrictedcount,
            'total_records' => count($items) + count($media) + count($collections) + count($externalworks),
        ],
        'items' => $items,
        'media' => $media,
        'collections' => $collections,
        'external_works' => $externalworks,
    ];
}

/**
 * Encode export package as JSON.
 *
 * @param array<string, mixed> $package Export package.
 * @return string
 */
function uckkarchive_export_as_json(array $package): string {
    $json = json_encode($package, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);

    return $json === false ? '{}' : $json;
}

/**
 * Encode export package as HTML.
 *
 * @param array<string, mixed> $package Export package.
 * @return string
 */
function uckkarchive_export_as_html(array $package): string {
    $html = '<!doctype html>';
    $html .= '<html lang="en">';
    $html .= '<head>';
    $html .= '<meta charset="utf-8">';
    $html .= '<title>' . s($package['archive']['name']) . '</title>';
    $html .= '</head>';
    $html .= '<body>';
    $html .= '<h1>' . s($package['archive']['name']) . '</h1>';
    $html .= '<p><strong>' . s(uckkarchive_export_string('generatedat', 'Generated at')) . ':</strong> ' .
        s($package['generated_at_label']) . '</p>';
    $html .= '<p><strong>' . s(get_string('course')) . ':</strong> ' . s($package['course']['fullname']) . '</p>';

    $html .= '<h2>' . s(uckkarchive_export_string('exportsummary', 'Export summary')) . '</h2>';
    $html .= '<ul>';
    foreach ($package['counts'] as $key => $value) {
        $html .= '<li><strong>' . s(str_replace('_', ' ', $key)) . ':</strong> ' . s((string)$value) . '</li>';
    }
    $html .= '</ul>';

    $sections = [
        'items' => uckkarchive_export_string('archiveitems', 'Archive items'),
        'media' => uckkarchive_export_string('media', 'Media'),
        'collections' => uckkarchive_export_string('mediacollections', 'Media collections'),
        'external_works' => uckkarchive_export_string('externalworks', 'External works'),
    ];

    foreach ($sections as $sectionkey => $sectionlabel) {
        if (empty($package[$sectionkey])) {
            continue;
        }

        $html .= '<h2>' . s($sectionlabel) . '</h2>';

        foreach ($package[$sectionkey] as $record) {
            $title = $record['title'] ?? $record['name'] ?? $record['label'] ?? $record['uuid'] ?? '#' . ($record['id'] ?? '');
            $html .= '<article>';
            $html .= '<h3>' . s((string)$title) . '</h3>';
            $html .= '<dl>';

            foreach (['id', 'uuid', 'status', 'visibility', 'mediatype', 'worktype', 'audiencesuitability', 'timecreated', 'timemodified'] as $key) {
                if (!array_key_exists($key, $record) || $record[$key] === null || $record[$key] === '') {
                    continue;
                }

                $value = in_array($key, ['timecreated', 'timemodified'], true) ? userdate((int)$record[$key]) : (string)$record[$key];
                $html .= '<dt>' . s($key) . '</dt><dd>' . s($value) . '</dd>';
            }

            $html .= '</dl>';

            foreach (['summary', 'description', 'citation', 'rightsstatement'] as $field) {
                if (!empty($record[$field]) && is_scalar($record[$field])) {
                    $html .= '<p><strong>' . s($field) . ':</strong> ' . s((string)$record[$field]) . '</p>';
                }
            }

            $html .= '</article>';
        }
    }

    $html .= '</body>';
    $html .= '</html>';

    return $html;
}

/**
 * Encode export package as CSV.
 *
 * @param array<string, mixed> $package Export package.
 * @return string
 */
function uckkarchive_export_as_csv(array $package): string {
    $handle = fopen('php://temp', 'r+');

    fputcsv($handle, [
        'section',
        'id',
        'title',
        'status',
        'visibility',
        'type',
        'timecreated',
        'timemodified',
    ]);

    $sections = [
        'items' => 'item',
        'media' => 'media',
        'collections' => 'collection',
        'external_works' => 'external_work',
    ];

    foreach ($sections as $sectionkey => $sectionlabel) {
        foreach ($package[$sectionkey] ?? [] as $record) {
            fputcsv($handle, [
                $sectionlabel,
                $record['id'] ?? '',
                $record['title'] ?? $record['name'] ?? $record['label'] ?? '',
                $record['status'] ?? '',
                $record['visibility'] ?? '',
                $record['itemtype'] ?? $record['mediatype'] ?? $record['worktype'] ?? '',
                !empty($record['timecreated']) ? userdate((int)$record['timecreated']) : '',
                !empty($record['timemodified']) ? userdate((int)$record['timemodified']) : '',
            ]);
        }
    }

    rewind($handle);
    $csv = stream_get_contents($handle);
    fclose($handle);

    return $csv === false ? '' : $csv;
}

/**
 * Render an export package according to format.
 *
 * @param array<string, mixed> $package Export package.
 * @param string $format Export format.
 * @return string
 */
function uckkarchive_export_render_package(array $package, string $format): string {
    if ($format === 'html') {
        return uckkarchive_export_as_html($package);
    }

    if ($format === 'csv') {
        return uckkarchive_export_as_csv($package);
    }

    return uckkarchive_export_as_json($package);
}

/**
 * Return download MIME type for export format.
 *
 * @param string $format Export format.
 * @return string
 */
function uckkarchive_export_mimetype(string $format): string {
    if ($format === 'html') {
        return 'text/html; charset=utf-8';
    }

    if ($format === 'csv') {
        return 'text/csv; charset=utf-8';
    }

    return 'application/json; charset=utf-8';
}

/**
 * Return file extension for export format.
 *
 * @param string $format Export format.
 * @return string
 */
function uckkarchive_export_extension(string $format): string {
    if ($format === 'html') {
        return 'html';
    }

    if ($format === 'csv') {
        return 'csv';
    }

    return 'json';
}

/**
 * Build a safe export filename.
 *
 * @param stdClass $archive Archive record.
 * @param string $format Export format.
 * @param string $scope Scope.
 * @param int $itemid Optional item id.
 * @return string
 */
function uckkarchive_export_filename(stdClass $archive, string $format, string $scope, int $itemid = 0): string {
    $suffix = $itemid > 0 ? '-item-' . $itemid : '-' . $scope;
    $base = clean_filename('uckkarchive-' . $archive->id . $suffix);

    return $base . '-' . date('Ymd-His') . '.' . uckkarchive_export_extension($format);
}

/**
 * Store export payload as plugin file.
 *
 * @param context_module $context Context.
 * @param int $exportid Export id.
 * @param string $filename Filename.
 * @param string $payload Payload.
 * @return stored_file|null
 */
function uckkarchive_export_store_payload_file(
    context_module $context,
    int $exportid,
    string $filename,
    string $payload
): ?stored_file {
    global $USER;

    if ($exportid <= 0) {
        return null;
    }

    $fs = get_file_storage();
    $fs->delete_area_files($context->id, UCKKARCHIVE_EXPORT_COMPONENT, 'export_package', $exportid);

    return $fs->create_file_from_string([
        'contextid' => $context->id,
        'component' => UCKKARCHIVE_EXPORT_COMPONENT,
        'filearea' => 'export_package',
        'itemid' => $exportid,
        'filepath' => '/',
        'filename' => $filename,
        'userid' => $USER->id,
    ], $payload);
}

/**
 * Save export audit record if the export table exists.
 *
 * @param stdClass $archive Archive instance.
 * @param stdClass $course Course.
 * @param context_module $context Module context.
 * @param array<string, mixed> $options Export options.
 * @param string $filename Filename.
 * @param string $payload Export payload.
 * @param array<string, mixed> $package Export package.
 * @return int Export record id, or 0 when table unavailable.
 */
function uckkarchive_export_record_export(
    stdClass $archive,
    stdClass $course,
    context_module $context,
    array $options,
    string $filename,
    string $payload,
    array $package
): int {
    global $DB, $USER;

    if (!uckkarchive_export_table_exists('uckkarchive_export')) {
        return 0;
    }

    $now = time();

    $selected = [
        'itemid' => (int)($options['itemid'] ?? 0),
        'mediaid' => (int)($options['mediaid'] ?? 0),
        'mediaids' => $options['mediaids'] ?? [],
        'collectionid' => (int)($options['collectionid'] ?? 0),
        'externalworkid' => (int)($options['externalworkid'] ?? 0),
    ];

    $metadata = [
        'schema' => 'uckkarchive_export_record_v2',
        'filename' => $filename,
        'filesize' => strlen($payload),
        'contenthash' => sha1($payload),
        'counts' => $package['counts'],
        'options' => $package['options'],
    ];

    $record = (object)[
        'archiveid' => (int)$archive->id,
        'courseid' => (int)$course->id,
        'cmid' => (int)($options['cmid'] ?? 0),
        'contextid' => $context->id,
        'userid' => $USER->id,
        'exportscope' => $options['scope'],
        'exportformat' => $options['format'],
        'packagename' => $filename,
        'description' => 'Synchronous archive export package.',
        'itemids' => json_encode($selected, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES),
        'reason' => (string)($options['reason'] ?? ''),
        'auditnote' => 'Created by export.php controller.',
        'redactionlevel' => $options['redactionlevel'],
        'redacted' => (int)($package['counts']['restricted_or_redacted'] > 0),
        'includefiles' => !empty($options['includefiles']) ? 1 : 0,
        'includeproofs' => !empty($options['includeproofs']) ? 1 : 0,
        'includeprovenance' => !empty($options['includeprovenance']) ? 1 : 0,
        'includeversions' => !empty($options['includeversions']) ? 1 : 0,
        'fileitemid' => null,
        'downloadcount' => 1,
        'lastdownloaded' => $now,
        'timequeued' => $now,
        'timestarted' => $now,
        'timecompleted' => $now,
        'error' => null,
        'status' => 'completed',
        'visibility' => $options['visibility'],
        'versionno' => 1,
        'provenancehash' => sha1($payload),
        'integritycaseid' => null,
        'createdby' => $USER->id,
        'modifiedby' => $USER->id,
        'timecreated' => $now,
        'timemodified' => $now,
        'metadata' => json_encode($metadata, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES),
    ];

    $exportid = (int)$DB->insert_record(
        'uckkarchive_export',
        uckkarchive_export_filter_record_for_table('uckkarchive_export', $record)
    );

    $storedfile = uckkarchive_export_store_payload_file($context, $exportid, $filename, $payload);

    if ($storedfile && uckkarchive_export_field_exists('uckkarchive_export', 'fileitemid')) {
        $DB->set_field('uckkarchive_export', 'fileitemid', $exportid, ['id' => $exportid]);
    }

    return $exportid;
}

/**
 * Trigger archive item exported events.
 *
 * @param array<string, mixed> $package Export package.
 * @param stdClass $archive Archive.
 * @param stdClass $course Course.
 * @param context_module $context Context.
 * @param int $exportid Export id.
 * @param array<string, mixed> $options Options.
 */
function uckkarchive_export_trigger_item_events(
    array $package,
    stdClass $archive,
    stdClass $course,
    context_module $context,
    int $exportid,
    array $options
): void {
    $eventclass = '\mod_uckkarchive\event\archive_item_exported';

    if (!class_exists($eventclass) || $exportid <= 0) {
        return;
    }

    foreach ($package['items'] ?? [] as $item) {
        if (empty($item['id'])) {
            continue;
        }

        $event = $eventclass::create([
            'objectid' => (int)$item['id'],
            'context' => $context,
            'other' => [
                'courseid' => (int)$course->id,
                'cmid' => (int)$options['cmid'],
                'exportid' => $exportid,
                'exporttype' => $options['scope'],
            ],
        ]);

        $event->trigger();
    }
}

/**
 * Trigger media exported events.
 *
 * @param array<string, mixed> $package Export package.
 * @param stdClass $archive Archive.
 * @param stdClass $course Course.
 * @param context_module $context Context.
 * @param int $exportid Export id.
 * @param array<string, mixed> $options Options.
 */
function uckkarchive_export_trigger_media_events(
    array $package,
    stdClass $archive,
    stdClass $course,
    context_module $context,
    int $exportid,
    array $options
): void {
    $eventclass = '\mod_uckkarchive\event\media_exported';

    if (!class_exists($eventclass) || $exportid <= 0) {
        return;
    }

    foreach ($package['media'] ?? [] as $media) {
        if (empty($media['id'])) {
            continue;
        }

        $event = $eventclass::create([
            'objectid' => (int)$media['id'],
            'context' => $context,
            'other' => [
                'archiveid' => (int)$archive->id,
                'courseid' => (int)$course->id,
                'cmid' => (int)$options['cmid'],
                'exportid' => $exportid,
                'exportformat' => $options['format'],
            ],
        ]);

        $event->trigger();
    }
}

/**
 * Trigger export events.
 *
 * @param array<string, mixed> $package Export package.
 * @param stdClass $archive Archive.
 * @param stdClass $course Course.
 * @param context_module $context Context.
 * @param int $exportid Export id.
 * @param array<string, mixed> $options Options.
 */
function uckkarchive_export_trigger_events(
    array $package,
    stdClass $archive,
    stdClass $course,
    context_module $context,
    int $exportid,
    array $options
): void {
    uckkarchive_export_trigger_item_events($package, $archive, $course, $context, $exportid, $options);
    uckkarchive_export_trigger_media_events($package, $archive, $course, $context, $exportid, $options);
}

/**
 * Send export payload to browser.
 *
 * @param string $filename Filename.
 * @param string $format Export format.
 * @param string $payload Export payload.
 */
function uckkarchive_export_send_file(string $filename, string $format, string $payload): void {
    @header('Content-Type: ' . uckkarchive_export_mimetype($format));
    @header('Content-Disposition: attachment; filename="' . $filename . '"');
    @header('Content-Length: ' . strlen($payload));
    @header('Cache-Control: private, max-age=0, must-revalidate');
    @header('Pragma: public');

    echo $payload;
    die;
}

/**
 * Build label for a scope.
 *
 * @param string $scope Scope.
 * @return string
 */
function uckkarchive_export_scope_label(string $scope): string {
    return uckkarchive_export_string('exportscope:' . $scope, ucfirst(str_replace('_', ' ', $scope)));
}

/**
 * Build label for a format.
 *
 * @param string $format Format.
 * @return string
 */
function uckkarchive_export_format_label(string $format): string {
    return uckkarchive_export_string('exportformat:' . $format, strtoupper($format));
}

/**
 * Build label for a visibility.
 *
 * @param string $visibility Visibility.
 * @return string
 */
function uckkarchive_export_visibility_label(string $visibility): string {
    return uckkarchive_export_string('visibility:' . $visibility, ucfirst(str_replace('_', ' ', $visibility)));
}

$id = optional_param('id', 0, PARAM_INT); // Course module id.
$a = optional_param('a', 0, PARAM_INT); // Archive instance id.
$itemid = optional_param('itemid', 0, PARAM_INT);
$mediaid = optional_param('mediaid', 0, PARAM_INT);
$collectionid = optional_param('collectionid', 0, PARAM_INT);
$externalworkid = optional_param('externalworkid', 0, PARAM_INT);
$mediaidsraw = optional_param('mediaids', '', PARAM_RAW_TRIMMED);
$action = optional_param('action', '', PARAM_ALPHAEXT);
$returnurl = optional_param('returnurl', '', PARAM_LOCALURL);

$defaultscope = 'archive';
if ($itemid > 0) {
    $defaultscope = 'item';
} else if ($mediaid > 0 || $mediaidsraw !== '') {
    $defaultscope = 'media';
} else if ($collectionid > 0) {
    $defaultscope = 'collection';
} else if ($externalworkid > 0) {
    $defaultscope = 'external_work';
}

$scope = optional_param('scope', $defaultscope, PARAM_ALPHAEXT);
$format = optional_param('format', 'json', PARAM_ALPHAEXT);
$visibility = optional_param('visibility', 'course', PARAM_ALPHAEXT);
$redactionlevel = optional_param('redactionlevel', 'hide_restricted', PARAM_ALPHAEXT);
$reason = optional_param('reason', '', PARAM_TEXT);

$includeprovenance = optional_param('includeprovenance', 1, PARAM_BOOL);
$includerevisions = optional_param('includerevisions', 1, PARAM_BOOL);
$includeversions = optional_param('includeversions', 1, PARAM_BOOL);
$includeproofs = optional_param('includeproofs', 1, PARAM_BOOL);
$includemetadata = optional_param('includemetadata', 1, PARAM_BOOL);
$includerestricted = optional_param('includerestricted', 0, PARAM_BOOL);
$includefiles = optional_param('includefiles', 1, PARAM_BOOL);
$includemedia = optional_param('includemedia', 1, PARAM_BOOL);
$includecollections = optional_param('includecollections', 1, PARAM_BOOL);
$includeexternalworks = optional_param('includeexternalworks', 1, PARAM_BOOL);
$includeadvisories = optional_param('includeadvisories', 1, PARAM_BOOL);
$includereviews = optional_param('includereviews', 1, PARAM_BOOL);
$includerelations = optional_param('includerelations', 1, PARAM_BOOL);
$includetags = optional_param('includetags', 1, PARAM_BOOL);

if ($id) {
    $cm = get_coursemodule_from_id('uckkarchive', $id, 0, false, MUST_EXIST);
    $course = $DB->get_record('course', ['id' => $cm->course], '*', MUST_EXIST);
    $archive = $DB->get_record('uckkarchive', ['id' => $cm->instance], '*', MUST_EXIST);
} else if ($a) {
    $archive = $DB->get_record('uckkarchive', ['id' => $a], '*', MUST_EXIST);
    $course = $DB->get_record('course', ['id' => $archive->course], '*', MUST_EXIST);
    $cm = get_coursemodule_from_instance('uckkarchive', $archive->id, $course->id, false, MUST_EXIST);
} else {
    throw new moodle_exception('missingparam', 'error', '', 'id');
}

$context = context_module::instance($cm->id);

require_login($course, false, $cm);
require_capability('mod/uckkarchive:view', $context);
require_capability('mod/uckkarchive:export', $context);

$scope = uckkarchive_export_normalise_choice($scope, uckkarchive_export_allowed_scopes(), 'archive');
$format = uckkarchive_export_normalise_choice($format, uckkarchive_export_allowed_formats(), 'json');
$visibility = uckkarchive_export_normalise_choice($visibility, uckkarchive_export_allowed_visibilities(), 'course');
$redactionlevel = uckkarchive_export_normalise_choice(
    $redactionlevel,
    uckkarchive_export_allowed_redaction_levels(),
    'hide_restricted'
);

$mediaids = uckkarchive_export_normalise_ids($mediaidsraw);

if ($includerestricted || uckkarchive_export_visibility_is_restricted($visibility) || $redactionlevel === 'none') {
    uckkarchive_export_require_capability(
        'mod/uckkarchive:viewrestricted',
        $context,
        'mod/uckkarchive:export'
    );
}

if ($scope === 'media' || $scope === 'collection') {
    uckkarchive_export_require_capability(
        'mod/uckkarchive:exportmedia',
        $context,
        'mod/uckkarchive:export'
    );
}

if ($itemid > 0) {
    uckkarchive_export_get_item($itemid, $archive, $context);
}

$viewurl = new moodle_url('/mod/uckkarchive/view.php', ['id' => $cm->id]);
$pageurl = new moodle_url('/mod/uckkarchive/export.php', [
    'id' => $cm->id,
    'itemid' => $itemid,
    'mediaid' => $mediaid,
    'collectionid' => $collectionid,
    'externalworkid' => $externalworkid,
]);

$return = $returnurl !== '' ? new moodle_url($returnurl) : $viewurl;

$PAGE->set_url($pageurl);
$PAGE->set_course($course);
$PAGE->set_cm($cm);
$PAGE->set_context($context);
$PAGE->set_title(format_string($archive->name));
$PAGE->set_heading(format_string($course->fullname));

$completion = new completion_info($course);
$completion->set_module_viewed($cm);

$allowedactions = [
    '',
    'download',
];

if (!in_array($action, $allowedactions, true)) {
    throw new moodle_exception('invalidexportaction', 'uckkarchive');
}

$options = [
    'cmid' => (int)$cm->id,
    'itemid' => $itemid,
    'mediaid' => $mediaid,
    'mediaids' => $mediaids,
    'collectionid' => $collectionid,
    'externalworkid' => $externalworkid,
    'scope' => $scope,
    'format' => $format,
    'visibility' => $visibility,
    'redactionlevel' => $redactionlevel,
    'reason' => $reason,
    'includeprovenance' => $includeprovenance,
    'includerevisions' => $includerevisions,
    'includeversions' => $includeversions,
    'includeproofs' => $includeproofs,
    'includemetadata' => $includemetadata,
    'includerestricted' => $includerestricted,
    'includefiles' => $includefiles,
    'includemedia' => $includemedia,
    'includecollections' => $includecollections,
    'includeexternalworks' => $includeexternalworks,
    'includeadvisories' => $includeadvisories,
    'includereviews' => $includereviews,
    'includerelations' => $includerelations,
    'includetags' => $includetags,
];

if ($action === 'download') {
    require_sesskey();

    $package = uckkarchive_export_build_package($archive, $course, $cm, $context, $options);

    if ((int)$package['counts']['total_records'] === 0) {
        redirect(
            $pageurl,
            uckkarchive_export_string('exportempty', 'There is no exportable content for the selected options.'),
            null,
            notification::NOTIFY_WARNING
        );
    }

    $payload = uckkarchive_export_render_package($package, $format);
    $filename = uckkarchive_export_filename($archive, $format, $scope, $itemid);
    $exportid = uckkarchive_export_record_export($archive, $course, $context, $options, $filename, $payload, $package);

    uckkarchive_export_trigger_events($package, $archive, $course, $context, $exportid, $options);
    uckkarchive_export_send_file($filename, $format, $payload);
}

$preview = uckkarchive_export_build_package($archive, $course, $cm, $context, $options);
$totalcount = (int)$preview['counts']['total_records'];

echo $OUTPUT->header();

echo $OUTPUT->heading(uckkarchive_export_string('exportarchive', 'Export archive'));

echo html_writer::start_div('uckkarchive-export');

echo html_writer::start_div('uckkarchive-export__summary card mb-3');
echo html_writer::start_div('card-body');

echo html_writer::tag('h3', uckkarchive_export_string('exportsummary', 'Export summary'), [
    'class' => 'card-title',
]);

echo html_writer::start_tag('dl', ['class' => 'uckkarchive-export__facts']);

echo html_writer::tag('dt', uckkarchive_export_string('archive', 'Archive'));
echo html_writer::tag('dd', format_string($archive->name));

echo html_writer::tag('dt', get_string('course'));
echo html_writer::tag('dd', format_string($course->fullname));

echo html_writer::tag('dt', uckkarchive_export_string('scope', 'Scope'));
echo html_writer::tag('dd', uckkarchive_export_scope_label($scope));

echo html_writer::tag('dt', uckkarchive_export_string('format', 'Format'));
echo html_writer::tag('dd', uckkarchive_export_format_label($format));

echo html_writer::tag('dt', uckkarchive_export_string('visibility', 'Visibility'));
echo html_writer::tag('dd', uckkarchive_export_visibility_label($visibility));

echo html_writer::tag('dt', uckkarchive_export_string('itemcount', 'Item count'));
echo html_writer::tag('dd', (string)$totalcount);

foreach ($preview['counts'] as $key => $value) {
    if ($key === 'total_records') {
        continue;
    }

    echo html_writer::tag('dt', ucfirst(str_replace('_', ' ', $key)));
    echo html_writer::tag('dd', (string)$value);
}

echo html_writer::end_tag('dl');

echo html_writer::end_div();
echo html_writer::end_div();

if ($totalcount === 0) {
    echo $OUTPUT->notification(
        uckkarchive_export_string('exportempty', 'There is no exportable content for the selected options.'),
        notification::NOTIFY_WARNING
    );
}

echo html_writer::start_tag('form', [
    'method' => 'get',
    'action' => (new moodle_url('/mod/uckkarchive/export.php'))->out(false),
    'class' => 'uckkarchive-export__options card mb-3',
]);

echo html_writer::start_div('card-body');
echo html_writer::tag('h3', uckkarchive_export_string('exportoptions', 'Export options'), ['class' => 'card-title']);

echo html_writer::empty_tag('input', ['type' => 'hidden', 'name' => 'id', 'value' => $cm->id]);

$hiddenids = [
    'itemid' => $itemid,
    'mediaid' => $mediaid,
    'collectionid' => $collectionid,
    'externalworkid' => $externalworkid,
];

foreach ($hiddenids as $name => $value) {
    if ($value > 0) {
        echo html_writer::empty_tag('input', ['type' => 'hidden', 'name' => $name, 'value' => $value]);
    }
}

if ($mediaidsraw !== '') {
    echo html_writer::empty_tag('input', ['type' => 'hidden', 'name' => 'mediaids', 'value' => s($mediaidsraw)]);
}

echo html_writer::start_div('form-group');
echo html_writer::tag('label', uckkarchive_export_string('scope', 'Scope'), ['for' => 'id_scope']);
echo html_writer::select([
    'archive' => uckkarchive_export_scope_label('archive'),
    'item' => uckkarchive_export_scope_label('item'),
    'portfolio' => uckkarchive_export_scope_label('portfolio'),
    'media' => uckkarchive_export_scope_label('media'),
    'collection' => uckkarchive_export_scope_label('collection'),
    'external_work' => uckkarchive_export_scope_label('external_work'),
], 'scope', $scope, false, [
    'id' => 'id_scope',
    'class' => 'custom-select form-control',
]);
echo html_writer::end_div();

echo html_writer::start_div('form-group');
echo html_writer::tag('label', uckkarchive_export_string('format', 'Format'), ['for' => 'id_format']);
echo html_writer::select([
    'json' => uckkarchive_export_format_label('json'),
    'html' => uckkarchive_export_format_label('html'),
    'csv' => uckkarchive_export_format_label('csv'),
], 'format', $format, false, [
    'id' => 'id_format',
    'class' => 'custom-select form-control',
]);
echo html_writer::end_div();

echo html_writer::start_div('form-group');
echo html_writer::tag('label', uckkarchive_export_string('visibility', 'Visibility'), ['for' => 'id_visibility']);
echo html_writer::select([
    'private' => uckkarchive_export_visibility_label('private'),
    'user' => uckkarchive_export_visibility_label('user'),
    'group' => uckkarchive_export_visibility_label('group'),
    'course' => uckkarchive_export_visibility_label('course'),
    'cohort' => uckkarchive_export_visibility_label('cohort'),
    'program' => uckkarchive_export_visibility_label('program'),
    'institution' => uckkarchive_export_visibility_label('institution'),
    'public' => uckkarchive_export_visibility_label('public'),
    'restricted' => uckkarchive_export_visibility_label('restricted'),
    'restricted_integrity' => uckkarchive_export_visibility_label('restricted_integrity'),
    'restricted_cultural' => uckkarchive_export_visibility_label('restricted_cultural'),
], 'visibility', $visibility, false, [
    'id' => 'id_visibility',
    'class' => 'custom-select form-control',
]);
echo html_writer::end_div();

echo html_writer::start_div('form-group');
echo html_writer::tag('label', uckkarchive_export_string('redactionlevel', 'Redaction level'), ['for' => 'id_redactionlevel']);
echo html_writer::select([
    'none' => uckkarchive_export_string('redactionlevel:none', 'None'),
    'hide_identity' => uckkarchive_export_string('redactionlevel:hide_identity', 'Hide identity'),
    'hide_restricted' => uckkarchive_export_string('redactionlevel:hide_restricted', 'Hide restricted text'),
    'metadata_only' => uckkarchive_export_string('redactionlevel:metadata_only', 'Metadata only'),
], 'redactionlevel', $redactionlevel, false, [
    'id' => 'id_redactionlevel',
    'class' => 'custom-select form-control',
]);
echo html_writer::end_div();

echo html_writer::start_div('form-group');
echo html_writer::tag('label', uckkarchive_export_string('reason', 'Reason'), ['for' => 'id_reason']);
echo html_writer::tag('textarea', s($reason), [
    'id' => 'id_reason',
    'name' => 'reason',
    'class' => 'form-control',
    'rows' => 2,
]);
echo html_writer::end_div();

$checkboxes = [
    'includeprovenance' => $includeprovenance,
    'includerevisions' => $includerevisions,
    'includeversions' => $includeversions,
    'includeproofs' => $includeproofs,
    'includemetadata' => $includemetadata,
    'includefiles' => $includefiles,
    'includemedia' => $includemedia,
    'includecollections' => $includecollections,
    'includeexternalworks' => $includeexternalworks,
    'includeadvisories' => $includeadvisories,
    'includereviews' => $includereviews,
    'includerelations' => $includerelations,
    'includetags' => $includetags,
];

if (uckkarchive_export_has_capability('mod/uckkarchive:viewrestricted', $context, 'mod/uckkarchive:export')) {
    $checkboxes['includerestricted'] = $includerestricted;
}

foreach ($checkboxes as $name => $checked) {
    echo html_writer::start_div('form-check');
    echo html_writer::empty_tag('input', [
        'type' => 'checkbox',
        'id' => 'id_' . $name,
        'name' => $name,
        'value' => 1,
        'class' => 'form-check-input',
        'checked' => $checked ? 'checked' : null,
    ]);
    echo html_writer::tag('label', uckkarchive_export_string($name, ucfirst(str_replace('_', ' ', $name))), [
        'for' => 'id_' . $name,
        'class' => 'form-check-label',
    ]);
    echo html_writer::end_div();
}

echo html_writer::tag('button', uckkarchive_export_string('updatepreview', 'Update preview'), [
    'type' => 'submit',
    'class' => 'btn btn-secondary mt-3',
]);

echo html_writer::end_div();
echo html_writer::end_tag('form');

if ($totalcount > 0) {
    echo html_writer::start_div('uckkarchive-export__preview card mb-3');
    echo html_writer::start_div('card-body');

    echo html_writer::tag('h3', uckkarchive_export_string('exportpreview', 'Export preview'), [
        'class' => 'card-title',
    ]);

    $sections = [
        'items' => uckkarchive_export_string('archiveitems', 'Archive items'),
        'media' => uckkarchive_export_string('media', 'Media'),
        'collections' => uckkarchive_export_string('mediacollections', 'Media collections'),
        'external_works' => uckkarchive_export_string('externalworks', 'External works'),
    ];

    foreach ($sections as $sectionkey => $sectionlabel) {
        if (empty($preview[$sectionkey])) {
            continue;
        }

        echo html_writer::tag('h4', $sectionlabel, ['class' => 'h5 mt-3']);
        echo html_writer::start_tag('ul', ['class' => 'uckkarchive-export__item-list']);

        foreach ($preview[$sectionkey] as $record) {
            $title = $record['title'] ?? $record['name'] ?? $record['label'] ?? $record['uuid'] ?? '#' . ($record['id'] ?? '');
            echo html_writer::start_tag('li', ['class' => 'uckkarchive-export__item']);
            echo html_writer::tag('strong', s((string)$title));

            if (!empty($record['status'])) {
                echo html_writer::span(' — ' . s((string)$record['status']), 'uckkarchive-export__item-status');
            }

            if (!empty($record['visibility'])) {
                echo html_writer::span(' — ' . s((string)$record['visibility']), 'uckkarchive-export__item-visibility');
            }

            if (!empty($record['redacted'])) {
                echo html_writer::span(' — ' . s(uckkarchive_export_string('redacted', 'Redacted')), 'uckkarchive-export__item-redacted');
            }

            if (!empty($record['summary']) && is_scalar($record['summary'])) {
                echo html_writer::tag('p', s((string)$record['summary']));
            }

            echo html_writer::end_tag('li');
        }

        echo html_writer::end_tag('ul');
    }

    echo html_writer::end_div();
    echo html_writer::end_div();
}

echo html_writer::start_tag('form', [
    'method' => 'post',
    'action' => (new moodle_url('/mod/uckkarchive/export.php'))->out(false),
    'class' => 'uckkarchive-export__download',
]);

echo html_writer::empty_tag('input', ['type' => 'hidden', 'name' => 'id', 'value' => $cm->id]);
echo html_writer::empty_tag('input', ['type' => 'hidden', 'name' => 'sesskey', 'value' => sesskey()]);
echo html_writer::empty_tag('input', ['type' => 'hidden', 'name' => 'action', 'value' => 'download']);
echo html_writer::empty_tag('input', ['type' => 'hidden', 'name' => 'scope', 'value' => $scope]);
echo html_writer::empty_tag('input', ['type' => 'hidden', 'name' => 'format', 'value' => $format]);
echo html_writer::empty_tag('input', ['type' => 'hidden', 'name' => 'visibility', 'value' => $visibility]);
echo html_writer::empty_tag('input', ['type' => 'hidden', 'name' => 'redactionlevel', 'value' => $redactionlevel]);
echo html_writer::empty_tag('input', ['type' => 'hidden', 'name' => 'reason', 'value' => s($reason)]);
echo html_writer::empty_tag('input', ['type' => 'hidden', 'name' => 'itemid', 'value' => $itemid]);
echo html_writer::empty_tag('input', ['type' => 'hidden', 'name' => 'mediaid', 'value' => $mediaid]);
echo html_writer::empty_tag('input', ['type' => 'hidden', 'name' => 'mediaids', 'value' => s($mediaidsraw)]);
echo html_writer::empty_tag('input', ['type' => 'hidden', 'name' => 'collectionid', 'value' => $collectionid]);
echo html_writer::empty_tag('input', ['type' => 'hidden', 'name' => 'externalworkid', 'value' => $externalworkid]);

foreach ($checkboxes as $name => $checked) {
    echo html_writer::empty_tag('input', [
        'type' => 'hidden',
        'name' => $name,
        'value' => $checked ? 1 : 0,
    ]);
}

echo html_writer::tag('button', uckkarchive_export_string('downloadexport', 'Download export'), [
    'type' => 'submit',
    'class' => 'btn btn-primary',
    'disabled' => $totalcount === 0 ? 'disabled' : null,
]);

echo html_writer::link($return, get_string('cancel'), [
    'class' => 'btn btn-secondary ml-2',
]);

echo html_writer::end_tag('form');

echo html_writer::div(
    uckkarchive_export_string(
        'exportgovernancenotice',
        'Exports are audit logged. Restricted, cultural protocol, and personal data must be handled according to archive policy.'
    ),
    'alert alert-info uckkarchive-export__notice mt-3',
    ['role' => 'status']
);

echo html_writer::end_div();

echo $OUTPUT->footer();

