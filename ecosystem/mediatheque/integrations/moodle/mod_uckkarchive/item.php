<?php
// This file is part of Moodle - https://moodle.org/
//
// Moodle is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// any later version.

/**
 * Archive item controller for UCKK Archives.
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
require_once(__DIR__ . '/locallib.php');

defined('MOODLE_INTERNAL') || die();

use core\output\notification;
use mod_uckkarchive\event\archive_item_exported;
use mod_uckkarchive\event\archive_item_revised;
use mod_uckkarchive\local\archive_item;
use mod_uckkarchive\output\archive_item_card;
use mod_uckkarchive\output\provenance_panel;

/**
 * Return whether a plugin table exists.
 *
 * @param string $table Table name.
 * @return bool
 */
function mod_uckkarchive_item_table_exists(string $table): bool {
    global $DB;

    return $DB->get_manager()->table_exists(new xmldb_table($table));
}

/**
 * Return table columns.
 *
 * @param string $table Table name.
 * @return array
 */
function mod_uckkarchive_item_columns(string $table): array {
    global $DB;

    static $cache = [];

    if (!array_key_exists($table, $cache)) {
        $cache[$table] = mod_uckkarchive_item_table_exists($table) ? $DB->get_columns($table) : [];
    }

    return $cache[$table];
}

/**
 * Return whether table field exists.
 *
 * @param string $table Table name.
 * @param string $field Field name.
 * @return bool
 */
function mod_uckkarchive_item_field_exists(string $table, string $field): bool {
    return array_key_exists($field, mod_uckkarchive_item_columns($table));
}

/**
 * Return first available object field.
 *
 * @param stdClass $record Record.
 * @param string[] $fields Candidate fields.
 * @param mixed $default Default.
 * @return mixed
 */
function mod_uckkarchive_item_first_field(stdClass $record, array $fields, mixed $default = null): mixed {
    foreach ($fields as $field) {
        if (property_exists($record, $field) && $record->{$field} !== null && $record->{$field} !== '') {
            return $record->{$field};
        }
    }

    return $default;
}

/**
 * Return component string or readable fallback.
 *
 * @param string $identifier String identifier.
 * @param string $fallback Fallback.
 * @return string
 */
function mod_uckkarchive_item_string(string $identifier, string $fallback): string {
    return get_string_manager()->string_exists($identifier, 'uckkarchive')
        ? get_string($identifier, 'uckkarchive')
        : $fallback;
}

/**
 * Convert key to readable label.
 *
 * @param string $key Key.
 * @return string
 */
function mod_uckkarchive_item_label_from_key(string $key): string {
    $key = trim($key);

    if ($key === '') {
        return '';
    }

    return ucfirst(str_replace('_', ' ', $key));
}

/**
 * Return safe class.
 *
 * @param string $prefix Prefix.
 * @param string $value Value.
 * @return string
 */
function mod_uckkarchive_item_css_class(string $prefix, string $value): string {
    $value = clean_param(strtolower(trim($value)), PARAM_ALPHANUMEXT);
    $value = str_replace('_', '-', $value);

    return $prefix . '-' . $value;
}

/**
 * Normalize archive item status.
 *
 * @param string $status Status.
 * @return string
 */
function mod_uckkarchive_item_normalise_status(string $status): string {
    $status = clean_param(strtolower(trim($status)), PARAM_ALPHANUMEXT);

    $allowed = [
        'draft',
        'submitted',
        'under_review',
        'validated',
        'published',
        'restricted',
        'contested',
        'invalidated',
        'superseded',
        'archived',
        'hidden',
    ];

    if ($status === 'pending_review') {
        $status = 'under_review';
    }

    return in_array($status, $allowed, true) ? $status : 'draft';
}

/**
 * Normalize visibility.
 *
 * @param string $visibility Visibility.
 * @return string
 */
function mod_uckkarchive_item_normalise_visibility(string $visibility): string {
    $visibility = clean_param(strtolower(trim($visibility)), PARAM_ALPHANUMEXT);

    if ($visibility === 'institutional') {
        $visibility = 'institution';
    }

    $allowed = [
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
        'hidden',
        'archived',
    ];

    return in_array($visibility, $allowed, true) ? $visibility : 'course';
}

/**
 * Return whether current user can see restricted visibility.
 *
 * @param string $visibility Visibility.
 * @param context $context Context.
 * @return bool
 */
function mod_uckkarchive_item_can_see_visibility(string $visibility, context $context): bool {
    $visibility = mod_uckkarchive_item_normalise_visibility($visibility);

    if ($visibility === 'restricted_cultural') {
        return has_capability('mod/uckkarchive:viewculturallyrestricted', $context)
            || has_capability('mod/uckkarchive:viewrestrictedmedia', $context)
            || has_capability('mod/uckkarchive:viewrestricted', $context);
    }

    if (in_array($visibility, ['restricted', 'restricted_integrity', 'hidden', 'archived'], true)) {
        return has_capability('mod/uckkarchive:viewrestricted', $context)
            || has_capability('mod/uckkarchive:viewrestrictedmedia', $context);
    }

    return true;
}

/**
 * Return whether current user can see an archive item.
 *
 * @param stdClass $item Item.
 * @param context $context Context.
 * @return bool
 */
function mod_uckkarchive_item_can_see_item(stdClass $item, context $context): bool {
    global $USER;

    $visibility = mod_uckkarchive_item_normalise_visibility((string)($item->visibility ?? 'course'));
    $status = mod_uckkarchive_item_normalise_status((string)($item->status ?? 'draft'));

    if ($status === 'hidden' && !has_capability('mod/uckkarchive:viewrestricted', $context)) {
        return false;
    }

    if ($visibility === 'private') {
        $ownerid = (int)($item->userid ?? $item->authorid ?? $item->ownerid ?? $item->createdby ?? 0);

        return $ownerid === (int)$USER->id
            || has_capability('mod/uckkarchive:validateitem', $context)
            || has_capability('mod/uckkarchive:viewrestricted', $context);
    }

    return mod_uckkarchive_item_can_see_visibility($visibility, $context);
}

/**
 * Return whether current user can see media.
 *
 * @param stdClass $media Media record.
 * @param context $context Context.
 * @return bool
 */
function mod_uckkarchive_item_can_see_media(stdClass $media, context $context): bool {
    global $USER;

    if (!has_capability('mod/uckkarchive:viewmedia', $context)) {
        return false;
    }

    $visibility = mod_uckkarchive_item_normalise_visibility((string)($media->visibility ?? 'course'));
    $status = clean_param(strtolower((string)($media->status ?? 'active')), PARAM_ALPHANUMEXT);

    if ($status === 'deleted_soft' && !has_capability('mod/uckkarchive:deletemedia', $context)) {
        return false;
    }

    if ($visibility === 'private') {
        $ownerid = (int)($media->ownerid ?? $media->userid ?? $media->createdby ?? 0);

        return $ownerid === (int)$USER->id
            || has_capability('mod/uckkarchive:editmedia', $context)
            || has_capability('mod/uckkarchive:viewrestrictedmedia', $context);
    }

    return mod_uckkarchive_item_can_see_visibility($visibility, $context);
}

/**
 * Filter record to existing table fields.
 *
 * @param string $table Table.
 * @param stdClass $record Record.
 * @return stdClass
 */
function mod_uckkarchive_item_filter_record(string $table, stdClass $record): stdClass {
    $columns = mod_uckkarchive_item_columns($table);
    $filtered = new stdClass();

    foreach (get_object_vars($record) as $field => $value) {
        if (array_key_exists($field, $columns)) {
            $filtered->{$field} = $value;
        }
    }

    return $filtered;
}

/**
 * Insert record after filtering to table schema.
 *
 * @param string $table Table.
 * @param stdClass $record Record.
 * @return int
 */
function mod_uckkarchive_item_insert_record(string $table, stdClass $record): int {
    global $DB;

    if (!mod_uckkarchive_item_table_exists($table)) {
        throw new moodle_exception('missingtable', 'error', '', $table);
    }

    $filtered = mod_uckkarchive_item_filter_record($table, $record);

    if (empty((array)$filtered)) {
        throw new moodle_exception('invalidrecord', 'error', '', $table);
    }

    return (int)$DB->insert_record($table, $filtered);
}

/**
 * Update record fields after filtering to table schema.
 *
 * @param string $table Table.
 * @param int $id Record id.
 * @param array<string, mixed> $fields Fields.
 * @return void
 */
function mod_uckkarchive_item_update_fields(string $table, int $id, array $fields): void {
    global $DB;

    if (!mod_uckkarchive_item_table_exists($table)) {
        return;
    }

    $record = new stdClass();
    $record->id = $id;

    foreach ($fields as $field => $value) {
        $record->{$field} = $value;
    }

    $filtered = mod_uckkarchive_item_filter_record($table, $record);

    if (count((array)$filtered) > 1) {
        $DB->update_record($table, $filtered);
    }
}

/**
 * Return item archive id.
 *
 * @param stdClass $item Item.
 * @param stdClass|null $archive Archive.
 * @return int
 */
function mod_uckkarchive_item_archiveid(stdClass $item, ?stdClass $archive): int {
    return (int)($item->archiveid ?? $item->uckkarchiveid ?? ($archive->id ?? 0));
}

/**
 * Return media export data.
 *
 * @param stdClass $media Media.
 * @param cm_info|stdClass|null $cm Course module.
 * @param context $context Context.
 * @return stdClass
 */
function mod_uckkarchive_item_export_media_row(stdClass $media, cm_info|stdClass|null $cm, context $context): stdClass {
    $title = (string)mod_uckkarchive_item_first_field($media, ['title', 'name', 'filename'], get_string('media', 'uckkarchive'));
    $description = (string)mod_uckkarchive_item_first_field($media, ['description', 'summary', 'caption'], '');

    $status = clean_param((string)($media->status ?? 'active'), PARAM_ALPHANUMEXT);
    $visibility = mod_uckkarchive_item_normalise_visibility((string)($media->visibility ?? 'course'));
    $mediatype = clean_param((string)($media->mediatype ?? $media->type ?? 'document'), PARAM_ALPHANUMEXT);

    $row = new stdClass();
    $row->id = (int)$media->id;
    $row->uuid = (string)($media->uuid ?? '');
    $row->title = format_string($title);
    $row->description = format_text($description, FORMAT_HTML, ['context' => $context]);
    $row->hasdescription = trim(strip_tags($description)) !== '';
    $row->status = $status;
    $row->statuslabel = mod_uckkarchive_item_string('mediastatus_' . $status, mod_uckkarchive_item_label_from_key($status));
    $row->statusclass = mod_uckkarchive_item_css_class('status', $status);
    $row->visibility = $visibility;
    $row->visibilitylabel = mod_uckkarchive_item_string(
        'visibility:' . str_replace('_', '', $visibility),
        mod_uckkarchive_item_label_from_key($visibility)
    );
    $row->visibilityclass = mod_uckkarchive_item_css_class('visibility', $visibility);
    $row->mediatype = $mediatype;
    $row->mediatypelabel = mod_uckkarchive_item_string('mediatype_' . $mediatype, mod_uckkarchive_item_label_from_key($mediatype));
    $row->mimetype = (string)($media->mimetype ?? '');
    $row->hasmimetype = $row->mimetype !== '';
    $row->timemodified = (int)($media->timemodified ?? 0);
    $row->timemodifiedlabel = $row->timemodified > 0 ? userdate($row->timemodified) : '';
    $row->url = $cm ? (new moodle_url('/mod/uckkarchive/media.php', [
        'id' => $cm->id,
        'mediaid' => $row->id,
    ]))->out(false) : '';

    return $row;
}

/**
 * Load media linked to item.
 *
 * @param stdClass $item Item.
 * @param stdClass|null $archive Archive.
 * @param cm_info|stdClass|null $cm Course module.
 * @param context $context Context.
 * @return stdClass[]
 */
function mod_uckkarchive_item_get_linked_media(
    stdClass $item,
    ?stdClass $archive,
    cm_info|stdClass|null $cm,
    context $context
): array {
    global $DB;

    if (!mod_uckkarchive_item_table_exists('uckkarchive_media')) {
        return [];
    }

    if (!has_capability('mod/uckkarchive:viewmedia', $context)) {
        return [];
    }

    $mediaids = [];
    $mediacolumns = mod_uckkarchive_item_columns('uckkarchive_media');

    foreach (['itemid', 'archiveitemid'] as $field) {
        if (array_key_exists($field, $mediacolumns)) {
            $records = $DB->get_records('uckkarchive_media', [$field => (int)$item->id], 'timemodified DESC, id DESC');
            foreach ($records as $record) {
                $mediaids[(int)$record->id] = (int)$record->id;
            }
        }
    }

    if (mod_uckkarchive_item_table_exists('uckkarchive_media_relation')) {
        $relationcolumns = mod_uckkarchive_item_columns('uckkarchive_media_relation');

        if (array_key_exists('itemid', $relationcolumns) && array_key_exists('mediaid', $relationcolumns)) {
            $relations = $DB->get_records('uckkarchive_media_relation', ['itemid' => (int)$item->id]);
            foreach ($relations as $relation) {
                if (!empty($relation->mediaid)) {
                    $mediaids[(int)$relation->mediaid] = (int)$relation->mediaid;
                }
            }
        }

        if (array_key_exists('targettype', $relationcolumns) &&
                array_key_exists('targetid', $relationcolumns) &&
                array_key_exists('sourceid', $relationcolumns)) {
            $relations = $DB->get_records('uckkarchive_media_relation', [
                'targettype' => 'archive_item',
                'targetid' => (int)$item->id,
            ]);

            foreach ($relations as $relation) {
                if (!empty($relation->sourceid)) {
                    $mediaids[(int)$relation->sourceid] = (int)$relation->sourceid;
                }
            }
        }
    }

    $rows = [];
    foreach ($mediaids as $mediaid) {
        $media = $DB->get_record('uckkarchive_media', ['id' => $mediaid], '*', IGNORE_MISSING);
        if (!$media || !mod_uckkarchive_item_can_see_media($media, $context)) {
            continue;
        }

        $rows[] = mod_uckkarchive_item_export_media_row($media, $cm, $context);
    }

    return $rows;
}

/**
 * Load content markers linked to an item.
 *
 * @param stdClass $item Item.
 * @param stdClass|null $archive Archive.
 * @param context $context Context.
 * @return stdClass[]
 */
function mod_uckkarchive_item_get_content_markers(stdClass $item, ?stdClass $archive, context $context): array {
    global $DB;

    if (!mod_uckkarchive_item_table_exists('uckkarchive_content_marker')) {
        return [];
    }

    if (!has_capability('mod/uckkarchive:viewadvisories', $context)) {
        return [];
    }

    $columns = mod_uckkarchive_item_columns('uckkarchive_content_marker');
    $clauses = [];
    $params = [];

    if (array_key_exists('itemid', $columns)) {
        $clauses[] = 'itemid = :itemid';
        $params['itemid'] = (int)$item->id;
    }

    if (array_key_exists('archiveitemid', $columns)) {
        $clauses[] = 'archiveitemid = :archiveitemid';
        $params['archiveitemid'] = (int)$item->id;
    }

    if (array_key_exists('targettype', $columns) && array_key_exists('targetid', $columns)) {
        $clauses[] = '(targettype = :targettype AND targetid = :targetid)';
        $params['targettype'] = 'archive_item';
        $params['targetid'] = (int)$item->id;
    }

    if (empty($clauses)) {
        return [];
    }

    $records = $DB->get_records_select(
        'uckkarchive_content_marker',
        implode(' OR ', $clauses),
        $params,
        array_key_exists('timemodified', $columns) ? 'timemodified DESC, id DESC' : 'id DESC'
    );

    $visible = [];

    foreach ($records as $record) {
        $visibility = mod_uckkarchive_item_normalise_visibility((string)($record->visibility ?? 'course'));

        if (!mod_uckkarchive_item_can_see_visibility($visibility, $context)) {
            continue;
        }

        $visible[] = $record;
    }

    return array_values($visible);
}

/**
 * Load content reviews for markers.
 *
 * @param stdClass[] $markers Markers.
 * @param context $context Context.
 * @return stdClass[]
 */
function mod_uckkarchive_item_get_content_reviews(array $markers, context $context): array {
    global $DB;

    if (empty($markers) || !mod_uckkarchive_item_table_exists('uckkarchive_content_review')) {
        return [];
    }

    if (!has_capability('mod/uckkarchive:viewadvisories', $context)) {
        return [];
    }

    $columns = mod_uckkarchive_item_columns('uckkarchive_content_review');
    $markerfield = array_key_exists('markerid', $columns) ? 'markerid' : (
        array_key_exists('contentmarkerid', $columns) ? 'contentmarkerid' : ''
    );

    if ($markerfield === '') {
        return [];
    }

    $reviews = [];

    foreach ($markers as $marker) {
        $records = $DB->get_records('uckkarchive_content_review', [$markerfield => (int)$marker->id]);
        foreach ($records as $record) {
            $reviews[] = $record;
        }
    }

    return $reviews;
}

/**
 * Create item export package row.
 *
 * @param stdClass $item Item.
 * @param stdClass|null $archive Archive.
 * @param stdClass $course Course.
 * @param cm_info|stdClass|null $cm Course module.
 * @param context $context Context.
 * @return int
 */
function mod_uckkarchive_item_create_export(
    stdClass $item,
    ?stdClass $archive,
    stdClass $course,
    cm_info|stdClass|null $cm,
    context $context
): int {
    global $USER;

    $now = time();

    $export = new stdClass();
    $export->archiveid = mod_uckkarchive_item_archiveid($item, $archive);
    $export->itemid = (int)$item->id;
    $export->courseid = (int)$course->id;
    $export->cmid = $cm ? (int)$cm->id : 0;
    $export->contextid = (int)$context->id;
    $export->userid = (int)$USER->id;
    $export->createdby = (int)$USER->id;
    $export->modifiedby = (int)$USER->id;
    $export->exportedby = (int)$USER->id;
    $export->exportscope = 'selected';
    $export->exporttype = 'item_summary';
    $export->exportformat = 'json';
    $export->packagename = 'archive-item-' . (int)$item->id . '-' . $now . '.json';
    $export->title = (string)($item->title ?? $item->name ?? get_string('archiveitem', 'uckkarchive'));
    $export->summary = (string)($item->summary ?? '');
    $export->description = get_string('archiveitem', 'uckkarchive');
    $export->itemids = json_encode([(int)$item->id], JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
    $export->reason = 'item_summary';
    $export->auditnote = 'Created from mod/uckkarchive/item.php';
    $export->redactionlevel = 'standard';
    $export->redacted = 0;
    $export->includefiles = 0;
    $export->includeproofs = 1;
    $export->includeprovenance = 1;
    $export->includeversions = 1;
    $export->status = 'pending';
    $export->visibility = mod_uckkarchive_item_normalise_visibility((string)($item->visibility ?? 'course'));
    $export->versionno = 1;
    $export->timecreated = $now;
    $export->timemodified = $now;
    $export->metadata = json_encode([
        'source' => 'mod_uckkarchive_item_page',
        'itemid' => (int)$item->id,
    ], JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);

    return mod_uckkarchive_item_insert_record('uckkarchive_export', $export);
}

/**
 * Render content advisory panel for item if available.
 *
 * @param stdClass $item Item.
 * @param stdClass|null $archive Archive.
 * @param cm_info|stdClass|null $cm Course module.
 * @param context $context Context.
 * @param stdClass[] $markers Content markers.
 * @param stdClass[] $reviews Content reviews.
 * @return string
 */
function mod_uckkarchive_item_render_advisory_panel(
    stdClass $item,
    ?stdClass $archive,
    cm_info|stdClass|null $cm,
    context $context,
    array $markers,
    array $reviews
): string {
    global $OUTPUT;

    if (empty($markers)) {
        return '';
    }

    if (class_exists('\mod_uckkarchive\output\content_advisory_panel')) {
        $panel = new \mod_uckkarchive\output\content_advisory_panel(
            mod_uckkarchive_item_archiveid($item, $archive),
            $cm ? (int)$cm->id : 0,
            (int)$context->id,
            'archive_item',
            (int)$item->id,
            (string)($item->title ?? $item->name ?? get_string('archiveitem', 'uckkarchive')),
            array_values($markers),
            array_values($reviews),
            [],
            [],
            [],
            [
                'canview' => has_capability('mod/uckkarchive:viewadvisories', $context),
                'canmanage' => has_capability('mod/uckkarchive:manageadvisories', $context),
                'canreview' => has_capability('mod/uckkarchive:reviewadvisories', $context),
                'canedit' => has_capability('mod/uckkarchive:manageadvisories', $context),
                'candelete' => has_capability('mod/uckkarchive:manageadvisories', $context),
                'canexport' => has_capability('mod/uckkarchive:export', $context),
                'canviewrestricted' => has_capability('mod/uckkarchive:viewrestricted', $context),
                'canviewcultural' => has_capability('mod/uckkarchive:viewculturallyrestricted', $context),
            ]
        );

        return $OUTPUT->render($panel);
    }

    $html = html_writer::start_div('uckkarchive-item-page__content-advisories card mb-3');
    $html .= html_writer::start_div('card-body');
    $html .= html_writer::tag('h3', get_string('contentadvisories', 'uckkarchive'), ['class' => 'card-title']);
    $html .= html_writer::start_tag('ul');

    foreach ($markers as $marker) {
        $label = (string)mod_uckkarchive_item_first_field($marker, ['taglabel', 'label', 'tagkey'], get_string('contentmarker', 'uckkarchive'));
        $severity = (string)($marker->severity ?? 'notice');

        $html .= html_writer::start_tag('li');
        $html .= html_writer::tag('strong', s($label));
        $html .= html_writer::span(s($severity), 'badge badge-secondary ml-2');

        if (!empty($marker->description)) {
            $html .= html_writer::tag('p', format_text($marker->description, FORMAT_HTML, ['context' => $context]));
        }

        $html .= html_writer::end_tag('li');
    }

    $html .= html_writer::end_tag('ul');
    $html .= html_writer::end_div();
    $html .= html_writer::end_div();

    return $html;
}

$id = optional_param('id', 0, PARAM_INT); // Course module id.
$a = optional_param('a', 0, PARAM_INT); // Archive instance id.
$itemid = optional_param('itemid', 0, PARAM_INT);
$action = optional_param('action', '', PARAM_ALPHAEXT);
$returnurl = optional_param('returnurl', '', PARAM_LOCALURL);

if ($itemid <= 0 && $id <= 0 && $a <= 0) {
    throw new moodle_exception('missingparam', 'error', '', 'itemid');
}

if ($itemid > 0) {
    $item = $DB->get_record('uckkarchive_item', ['id' => $itemid], '*', MUST_EXIST);

    if (!empty($item->cmid)) {
        $cm = get_coursemodule_from_id('uckkarchive', (int)$item->cmid, 0, false, MUST_EXIST);
        $course = $DB->get_record('course', ['id' => $cm->course], '*', MUST_EXIST);
        $archive = $DB->get_record('uckkarchive', ['id' => $cm->instance], '*', MUST_EXIST);
    } else if (!empty($item->archiveid)) {
        $archive = $DB->get_record('uckkarchive', ['id' => $item->archiveid], '*', MUST_EXIST);
        $courseid = (int)($archive->course ?? $archive->courseid ?? 0);
        $course = $DB->get_record('course', ['id' => $courseid], '*', MUST_EXIST);
        $cm = get_coursemodule_from_instance('uckkarchive', $archive->id, $course->id, false, MUST_EXIST);
    } else if (!empty($item->courseid)) {
        $course = $DB->get_record('course', ['id' => $item->courseid], '*', MUST_EXIST);
        $cm = null;
        $archive = null;
    } else {
        throw new moodle_exception('invalidarchiveitemcontext', 'uckkarchive');
    }
} else if ($id > 0) {
    $cm = get_coursemodule_from_id('uckkarchive', $id, 0, false, MUST_EXIST);
    $course = $DB->get_record('course', ['id' => $cm->course], '*', MUST_EXIST);
    $archive = $DB->get_record('uckkarchive', ['id' => $cm->instance], '*', MUST_EXIST);
    $item = null;
} else {
    $archive = $DB->get_record('uckkarchive', ['id' => $a], '*', MUST_EXIST);
    $courseid = (int)($archive->course ?? $archive->courseid ?? 0);
    $course = $DB->get_record('course', ['id' => $courseid], '*', MUST_EXIST);
    $cm = get_coursemodule_from_instance('uckkarchive', $archive->id, $course->id, false, MUST_EXIST);
    $item = null;
}

if ($cm) {
    $context = context_module::instance($cm->id);
    require_login($course, false, $cm);
} else {
    $context = context_course::instance($course->id);
    require_login($course);
}

require_capability('mod/uckkarchive:view', $context);

if ($item === null) {
    throw new moodle_exception('missingparam', 'error', '', 'itemid');
}

$itemid = (int)$item->id;

if (!mod_uckkarchive_item_can_see_item($item, $context)) {
    throw new required_capability_exception($context, 'mod/uckkarchive:viewrestricted', 'nopermissions', '');
}

$pageurl = new moodle_url('/mod/uckkarchive/item.php', [
    'itemid' => $itemid,
]);

$archiveurl = $cm
    ? new moodle_url('/mod/uckkarchive/view.php', ['id' => $cm->id])
    : new moodle_url('/mod/uckkarchive/index.php', ['id' => $course->id]);

$return = $returnurl !== '' ? new moodle_url($returnurl) : $archiveurl;

$allowedactions = [
    '',
    'markviewed',
    'revise',
    'requestvalidation',
    'export',
];

if (!in_array($action, $allowedactions, true)) {
    throw new moodle_exception('invalidarchiveitemaction', 'uckkarchive');
}

$PAGE->set_url($pageurl);
$PAGE->set_course($course);
if ($cm) {
    $PAGE->set_cm($cm);
}
$PAGE->set_context($context);
$PAGE->set_title(format_string($item->title ?? $item->name ?? get_string('archiveitem', 'uckkarchive')));
$PAGE->set_heading(format_string($course->fullname));

$PAGE->requires->js_call_amd('mod_uckkarchive/archive', 'init', [[
    'cmid' => $cm ? (int)$cm->id : 0,
    'archiveid' => $archive ? (int)$archive->id : 0,
    'itemid' => $itemid,
    'contextid' => (int)$context->id,
]]);

if ($cm && has_capability('mod/uckkarchive:viewmedia', $context)) {
    $PAGE->requires->js_call_amd('mod_uckkarchive/media', 'init', [[
        'cmid' => (int)$cm->id,
        'archiveid' => $archive ? (int)$archive->id : 0,
        'itemid' => $itemid,
        'contextid' => (int)$context->id,
    ]]);
}

if ($cm && has_capability('mod/uckkarchive:viewadvisories', $context)) {
    $PAGE->requires->js_call_amd('mod_uckkarchive/content_advisory', 'init', [[
        'cmid' => (int)$cm->id,
        'archiveid' => $archive ? (int)$archive->id : 0,
        'targettype' => 'archive_item',
        'targetid' => $itemid,
        'contextid' => (int)$context->id,
    ]]);
}

if ($cm) {
    $completion = new completion_info($course);
    $completion->set_module_viewed($cm);
}

$itemvisibility = mod_uckkarchive_item_normalise_visibility((string)($item->visibility ?? 'course'));

if ($action !== '') {
    require_sesskey();

    switch ($action) {
        case 'markviewed':
            redirect($pageurl);
            break;

        case 'revise':
            require_capability('mod/uckkarchive:reviseitem', $context);

            $summary = required_param('summary', PARAM_TEXT);
            $now = time();

            $revision = new stdClass();
            $revision->archiveid = mod_uckkarchive_item_archiveid($item, $archive);
            $revision->itemid = $itemid;
            $revision->courseid = (int)$course->id;
            $revision->cmid = $cm ? (int)$cm->id : 0;
            $revision->contextid = (int)$context->id;
            $revision->userid = (int)$USER->id;
            $revision->createdby = (int)$USER->id;
            $revision->modifiedby = (int)$USER->id;
            $revision->summary = $summary;
            $revision->reason = $summary;
            $revision->status = 'under_review';
            $revision->validationstate = 'human_reviewed';
            $revision->visibility = $itemvisibility;
            $revision->versionno = ((int)($item->versionno ?? 1)) + 1;
            $revision->timecreated = $now;
            $revision->timemodified = $now;
            $revision->metadata = json_encode([
                'source' => 'mod_uckkarchive_item_page',
                'action' => 'revise',
            ], JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);

            $revisionid = mod_uckkarchive_item_insert_record('uckkarchive_rev', $revision);

            mod_uckkarchive_item_update_fields('uckkarchive_item', $itemid, [
                'status' => 'under_review',
                'validationstate' => 'human_reviewed',
                'versionno' => $revision->versionno,
                'modifiedby' => (int)$USER->id,
                'timemodified' => $now,
            ]);

            if (class_exists('\mod_uckkarchive\event\archive_item_revised')) {
                $event = archive_item_revised::create([
                    'objectid' => $itemid,
                    'context' => $context,
                    'other' => [
                        'courseid' => (int)$course->id,
                        'cmid' => $cm ? (int)$cm->id : 0,
                        'archiveid' => mod_uckkarchive_item_archiveid($item, $archive),
                        'revisionid' => $revisionid,
                    ],
                ]);
                $event->add_record_snapshot('course', $course);
                if ($cm) {
                    $event->add_record_snapshot('course_modules', $cm);
                }
                $event->add_record_snapshot('uckkarchive_item', $item);
                $event->trigger();
            }

            redirect($pageurl, get_string('archiveitemrevised', 'uckkarchive'), null, notification::NOTIFY_SUCCESS);
            break;

        case 'requestvalidation':
            require_capability('mod/uckkarchive:validateitem', $context);

            mod_uckkarchive_item_update_fields('uckkarchive_item', $itemid, [
                'status' => 'under_review',
                'validationstate' => 'human_reviewed',
                'modifiedby' => (int)$USER->id,
                'timemodified' => time(),
            ]);

            redirect($pageurl, get_string('validationrequested', 'uckkarchive'), null, notification::NOTIFY_SUCCESS);
            break;

        case 'export':
            require_capability('mod/uckkarchive:export', $context);

            $exportid = mod_uckkarchive_item_create_export($item, $archive, $course, $cm, $context);

            if (class_exists('\mod_uckkarchive\event\archive_item_exported')) {
                $event = archive_item_exported::create([
                    'objectid' => $itemid,
                    'context' => $context,
                    'other' => [
                        'courseid' => (int)$course->id,
                        'cmid' => $cm ? (int)$cm->id : 0,
                        'archiveid' => mod_uckkarchive_item_archiveid($item, $archive),
                        'exportid' => $exportid,
                        'exporttype' => 'item_summary',
                        'exportformat' => 'json',
                    ],
                ]);
                $event->add_record_snapshot('course', $course);
                if ($cm) {
                    $event->add_record_snapshot('course_modules', $cm);
                }
                $event->add_record_snapshot('uckkarchive_item', $item);
                $event->trigger();
            }

            redirect(
                new moodle_url('/mod/uckkarchive/export.php', [
                    'id' => $cm ? $cm->id : 0,
                    'itemid' => $itemid,
                    'exportid' => $exportid,
                ]),
                get_string('archiveexportqueued', 'uckkarchive'),
                null,
                notification::NOTIFY_SUCCESS
            );
            break;
    }
}

$item = $DB->get_record('uckkarchive_item', ['id' => $itemid], '*', MUST_EXIST);

$proofs = mod_uckkarchive_item_table_exists('uckkarchive_proof')
    ? $DB->get_records('uckkarchive_proof', ['itemid' => $itemid], 'timecreated ASC, id ASC')
    : [];

$provenance = mod_uckkarchive_item_table_exists('uckkarchive_prov')
    ? $DB->get_records('uckkarchive_prov', ['itemid' => $itemid], 'timecreated ASC, id ASC')
    : [];

$revisions = mod_uckkarchive_item_table_exists('uckkarchive_rev')
    ? $DB->get_records('uckkarchive_rev', ['itemid' => $itemid], 'versionno DESC, timecreated DESC, id DESC')
    : [];

$exports = mod_uckkarchive_item_table_exists('uckkarchive_export')
    ? $DB->get_records('uckkarchive_export', ['itemid' => $itemid], 'timecreated DESC, id DESC')
    : [];

$linkedmedia = mod_uckkarchive_item_get_linked_media($item, $archive, $cm, $context);
$contentmarkers = mod_uckkarchive_item_get_content_markers($item, $archive, $context);
$contentreviews = mod_uckkarchive_item_get_content_reviews($contentmarkers, $context);

$kristal = null;
if (!empty($item->kristalid) && mod_uckkarchive_item_table_exists('uckkarchive_kristal')) {
    $kristal = $DB->get_record('uckkarchive_kristal', ['id' => $item->kristalid], '*', IGNORE_MISSING);
}

$itemmodel = archive_item::from_record($item);

$canrevise = has_capability('mod/uckkarchive:reviseitem', $context);
$canvalidate = has_capability('mod/uckkarchive:validateitem', $context);
$canexport = has_capability('mod/uckkarchive:export', $context);
$canviewrestricted = has_capability('mod/uckkarchive:viewrestricted', $context);
$canviewmedia = has_capability('mod/uckkarchive:viewmedia', $context);
$canviewadvisories = has_capability('mod/uckkarchive:viewadvisories', $context);

$actions = [];

if ($canrevise) {
    $actions[] = [
        'key' => 'revise',
        'label' => get_string('revisearchiveitem', 'uckkarchive'),
        'url' => $pageurl,
        'method' => 'POST',
        'primary' => false,
        'requiresummary' => true,
    ];
}

if ($canvalidate) {
    $actions[] = [
        'key' => 'requestvalidation',
        'label' => get_string('requestvalidation', 'uckkarchive'),
        'url' => $pageurl,
        'method' => 'POST',
        'primary' => true,
        'requiresummary' => false,
    ];
}

if ($canexport) {
    $actions[] = [
        'key' => 'export',
        'label' => get_string('exportarchiveitem', 'uckkarchive'),
        'url' => $pageurl,
        'method' => 'POST',
        'primary' => false,
        'requiresummary' => false,
    ];
}

$card = new archive_item_card(
    $itemmodel->to_export(),
    [
        'course' => $course,
        'cm' => $cm,
        'context' => $context,
        'proofs' => array_values($proofs),
        'kristal' => $kristal,
        'revisions' => array_values($revisions),
        'exports' => array_values($exports),
        'media' => array_values($linkedmedia),
        'contentmarkers' => array_values($contentmarkers),
        'actions' => $actions,
        'canviewrestricted' => $canviewrestricted,
        'canviewmedia' => $canviewmedia,
        'canviewadvisories' => $canviewadvisories,
    ]
);

$provpanel = new provenance_panel(
    $itemid,
    $context->id,
    array_values($provenance),
    [
        'canviewrestricted' => $canviewrestricted,
    ]
);

echo $OUTPUT->header();

echo $OUTPUT->heading(format_string($item->title ?? $item->name ?? get_string('archiveitem', 'uckkarchive')));

echo html_writer::start_div('uckkarchive-item-page', [
    'data-region' => 'uckkarchive-item-page',
    'data-item-id' => $itemid,
    'data-archive-id' => $archive ? (int)$archive->id : 0,
    'data-cm-id' => $cm ? (int)$cm->id : 0,
]);

echo $OUTPUT->render($card);

echo html_writer::start_div('uckkarchive-item-page__details card mb-3');
echo html_writer::start_div('card-body');

echo html_writer::tag('h3', get_string('archiveitemdetails', 'uckkarchive'), [
    'class' => 'card-title',
]);

echo html_writer::start_tag('dl', ['class' => 'uckkarchive-item-page__facts']);

echo html_writer::tag('dt', get_string('status'));
echo html_writer::tag('dd', s($item->status ?? ''));

echo html_writer::tag('dt', get_string('visibility', 'uckkarchive'));
echo html_writer::tag('dd', s($item->visibility ?? ''));

echo html_writer::tag('dt', get_string('version', 'uckkarchive'));
echo html_writer::tag('dd', (string)($item->versionno ?? 1));

if (!empty($item->provenance)) {
    echo html_writer::tag('dt', get_string('provenance', 'uckkarchive'));
    echo html_writer::tag('dd', s($item->provenance));
}

if (!empty($item->validationstate)) {
    echo html_writer::tag('dt', get_string('validationstate', 'uckkarchive'));
    echo html_writer::tag('dd', s($item->validationstate));
}

if (!empty($item->timecreated)) {
    echo html_writer::tag('dt', get_string('timecreated', 'uckkarchive'));
    echo html_writer::tag('dd', userdate($item->timecreated));
}

if (!empty($item->timemodified)) {
    echo html_writer::tag('dt', get_string('timemodified', 'moodle'));
    echo html_writer::tag('dd', userdate($item->timemodified));
}

echo html_writer::end_tag('dl');

if (!empty($item->summary)) {
    echo html_writer::tag('h4', get_string('summary', 'uckkarchive'));
    echo format_text($item->summary, FORMAT_HTML, ['context' => $context]);
}

if (!empty($item->content)) {
    echo html_writer::tag('h4', get_string('archiveitemcontent', 'uckkarchive'));
    echo format_text($item->content, FORMAT_HTML, ['context' => $context]);
}

echo html_writer::end_div();
echo html_writer::end_div();

if (!empty($linkedmedia)) {
    echo html_writer::start_div('uckkarchive-item-page__media card mb-3', [
        'data-region' => 'uckkarchive-linked-media',
    ]);
    echo html_writer::start_div('card-body');

    echo html_writer::tag('h3', get_string('media', 'uckkarchive'), [
        'class' => 'card-title',
    ]);

    echo html_writer::start_tag('ul', ['class' => 'uckkarchive-item-page__media-list']);

    foreach ($linkedmedia as $media) {
        echo html_writer::start_tag('li', ['class' => 'uckkarchive-item-page__media-item mb-2']);

        if (!empty($media->url)) {
            echo html_writer::link(new moodle_url($media->url), $media->title);
        } else {
            echo html_writer::tag('strong', $media->title);
        }

        echo html_writer::span(s($media->mediatypelabel), 'badge badge-secondary ml-2');
        echo html_writer::span(s($media->statuslabel), 'badge badge-light ml-1');

        if (!empty($media->hasdescription)) {
            echo html_writer::div($media->description, 'uckkarchive-item-page__media-description mt-1');
        }

        echo html_writer::end_tag('li');
    }

    echo html_writer::end_tag('ul');

    echo html_writer::end_div();
    echo html_writer::end_div();
}

echo mod_uckkarchive_item_render_advisory_panel($item, $archive, $cm, $context, $contentmarkers, $contentreviews);

if (!empty($proofs)) {
    echo html_writer::start_div('uckkarchive-item-page__proofs card mb-3');
    echo html_writer::start_div('card-body');

    echo html_writer::tag('h3', get_string('proofs', 'uckkarchive'), [
        'class' => 'card-title',
    ]);

    echo html_writer::start_tag('ul', ['class' => 'uckkarchive-item-page__proof-list']);

    foreach ($proofs as $proof) {
        echo html_writer::start_tag('li', ['class' => 'uckkarchive-item-page__proof']);

        echo html_writer::tag('strong', format_string($proof->title ?? $proof->prooftype ?? get_string('proof', 'uckkarchive')));

        if (!empty($proof->status)) {
            echo html_writer::span(s($proof->status), 'badge badge-secondary ml-2');
        }

        if (!empty($proof->summary)) {
            echo html_writer::tag('p', s($proof->summary));
        }

        if (!empty($proof->sourceurl)) {
            echo html_writer::link(new moodle_url($proof->sourceurl), s($proof->sourceurl));
        }

        echo html_writer::end_tag('li');
    }

    echo html_writer::end_tag('ul');

    echo html_writer::end_div();
    echo html_writer::end_div();
}

echo $OUTPUT->render($provpanel);

if (!empty($revisions)) {
    echo html_writer::start_div('uckkarchive-item-page__revisions card mb-3');
    echo html_writer::start_div('card-body');

    echo html_writer::tag('h3', get_string('revisionhistory', 'uckkarchive'), [
        'class' => 'card-title',
    ]);

    echo html_writer::start_tag('ol', ['class' => 'uckkarchive-item-page__revision-list']);

    foreach ($revisions as $revision) {
        echo html_writer::start_tag('li', ['class' => 'uckkarchive-item-page__revision']);

        echo html_writer::tag(
            'strong',
            get_string('versionx', 'uckkarchive', (int)($revision->versionno ?? 1))
        );

        if (!empty($revision->status)) {
            echo html_writer::span(s($revision->status), 'badge badge-secondary ml-2');
        }

        if (!empty($revision->summary)) {
            echo html_writer::tag('p', s($revision->summary));
        }

        if (!empty($revision->timecreated)) {
            echo html_writer::tag('p', userdate($revision->timecreated), [
                'class' => 'text-muted',
            ]);
        }

        echo html_writer::end_tag('li');
    }

    echo html_writer::end_tag('ol');

    echo html_writer::end_div();
    echo html_writer::end_div();
}

if (!empty($exports) && $canexport) {
    echo html_writer::start_div('uckkarchive-item-page__exports card mb-3');
    echo html_writer::start_div('card-body');

    echo html_writer::tag('h3', get_string('exports', 'uckkarchive'), [
        'class' => 'card-title',
    ]);

    echo html_writer::start_tag('ul');

    foreach ($exports as $export) {
        echo html_writer::start_tag('li');

        echo s($export->exporttype ?? $export->exportformat ?? get_string('export', 'uckkarchive'));

        if (!empty($export->status)) {
            echo html_writer::span(' — ' . s($export->status), 'text-muted');
        }

        if (!empty($export->timecreated)) {
            echo html_writer::span(' — ' . userdate($export->timecreated), 'text-muted');
        }

        echo html_writer::end_tag('li');
    }

    echo html_writer::end_tag('ul');

    echo html_writer::end_div();
    echo html_writer::end_div();
}

if (!empty($actions)) {
    echo html_writer::start_div('uckkarchive-item-page__actions card mb-3');
    echo html_writer::start_div('card-body');

    echo html_writer::tag('h3', get_string('archiveitemactions', 'uckkarchive'), [
        'class' => 'card-title',
    ]);

    foreach ($actions as $actionrow) {
        echo html_writer::start_tag('form', [
            'method' => strtolower((string)$actionrow['method']),
            'action' => $actionrow['url']->out(false),
            'class' => 'uckkarchive-item-page__action-form mb-3',
        ]);

        echo html_writer::empty_tag('input', [
            'type' => 'hidden',
            'name' => 'sesskey',
            'value' => sesskey(),
        ]);

        echo html_writer::empty_tag('input', [
            'type' => 'hidden',
            'name' => 'itemid',
            'value' => $itemid,
        ]);

        echo html_writer::empty_tag('input', [
            'type' => 'hidden',
            'name' => 'action',
            'value' => $actionrow['key'],
        ]);

        if (!empty($actionrow['requiresummary'])) {
            $summaryid = 'id_' . clean_param((string)$actionrow['key'], PARAM_ALPHANUMEXT) . '_summary';

            echo html_writer::start_div('form-group');
            echo html_writer::tag('label', get_string('summary', 'uckkarchive'), [
                'for' => $summaryid,
            ]);
            echo html_writer::tag('textarea', '', [
                'id' => $summaryid,
                'name' => 'summary',
                'class' => 'form-control',
                'rows' => 3,
                'maxlength' => 4000,
                'required' => 'required',
            ]);
            echo html_writer::end_div();
        }

        echo html_writer::tag('button', $actionrow['label'], [
            'type' => 'submit',
            'class' => !empty($actionrow['primary']) ? 'btn btn-primary' : 'btn btn-secondary',
        ]);

        echo html_writer::end_tag('form');
    }

    echo html_writer::end_div();
    echo html_writer::end_div();
}

echo html_writer::div(
    get_string('archiveitemgovernancenotice', 'uckkarchive'),
    'alert alert-info uckkarchive-item-page__notice',
    ['role' => 'status']
);

echo html_writer::link($return, get_string('backtoarchive', 'uckkarchive'), [
    'class' => 'btn btn-secondary',
]);

echo html_writer::end_div();

echo $OUTPUT->footer();
