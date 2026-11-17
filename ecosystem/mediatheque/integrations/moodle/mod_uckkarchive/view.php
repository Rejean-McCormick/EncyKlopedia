<?php
// This file is part of Moodle - https://moodle.org/
//
// Moodle is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// any later version.

/**
 * Main view page for a UCKK Archive activity.
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

/**
 * Return true when a table exists.
 *
 * @param string $tablename Moodle table name without braces.
 * @return bool
 */
function mod_uckkarchive_view_table_exists(string $tablename): bool {
    global $DB;

    return $DB->get_manager()->table_exists(new xmldb_table($tablename));
}

/**
 * Return database columns for a table.
 *
 * @param string $tablename Table name.
 * @return array
 */
function mod_uckkarchive_view_columns(string $tablename): array {
    global $DB;

    if (!mod_uckkarchive_view_table_exists($tablename)) {
        return [];
    }

    return $DB->get_columns($tablename);
}

/**
 * Return whether a table field exists.
 *
 * @param string $tablename Table name.
 * @param string $field Field name.
 * @return bool
 */
function mod_uckkarchive_view_field_exists(string $tablename, string $field): bool {
    return array_key_exists($field, mod_uckkarchive_view_columns($tablename));
}

/**
 * Return a field from an object using the first available candidate.
 *
 * @param stdClass $record Record.
 * @param string[] $fields Candidate fields.
 * @param mixed $default Default value.
 * @return mixed
 */
function mod_uckkarchive_view_first_field(stdClass $record, array $fields, mixed $default = null): mixed {
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
function mod_uckkarchive_view_string(string $identifier, string $fallback): string {
    return get_string_manager()->string_exists($identifier, 'uckkarchive')
        ? get_string($identifier, 'uckkarchive')
        : $fallback;
}

/**
 * Convert a machine key to a readable label.
 *
 * @param string $key Key.
 * @return string
 */
function mod_uckkarchive_view_label_from_key(string $key): string {
    $key = trim($key);

    if ($key === '') {
        return '';
    }

    return ucfirst(str_replace('_', ' ', $key));
}

/**
 * Return a CSS class suffix.
 *
 * @param string $prefix Prefix.
 * @param string $value Value.
 * @return string
 */
function mod_uckkarchive_view_css_class(string $prefix, string $value): string {
    $value = clean_param(strtolower(trim($value)), PARAM_ALPHANUMEXT);
    $value = str_replace('_', '-', $value);

    return $prefix . '-' . $value;
}

/**
 * Normalise archive item status for CSS/template output.
 *
 * @param string $status Raw status.
 * @return string
 */
function mod_uckkarchive_view_normalise_status(string $status): string {
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

    return in_array($status, $allowed, true) ? $status : 'draft';
}

/**
 * Normalise media status.
 *
 * @param string $status Raw status.
 * @return string
 */
function mod_uckkarchive_view_normalise_media_status(string $status): string {
    $status = clean_param(strtolower(trim($status)), PARAM_ALPHANUMEXT);

    $allowed = [
        'draft',
        'submitted',
        'active',
        'restricted',
        'superseded',
        'archived',
        'deleted_soft',
    ];

    return in_array($status, $allowed, true) ? $status : 'draft';
}

/**
 * Normalise archive/media visibility.
 *
 * @param string $visibility Raw visibility.
 * @return string
 */
function mod_uckkarchive_view_normalise_visibility(string $visibility): string {
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
 * Return whether current user may see a restricted/cultural record.
 *
 * @param string $visibility Visibility.
 * @param context_module $context Context.
 * @return bool
 */
function mod_uckkarchive_view_can_see_visibility(string $visibility, context_module $context): bool {
    $visibility = mod_uckkarchive_view_normalise_visibility($visibility);

    if ($visibility === 'restricted_cultural') {
        return has_capability('mod/uckkarchive:viewculturallyrestricted', $context)
            || has_capability('mod/uckkarchive:viewrestrictedmedia', $context)
            || has_capability('mod/uckkarchive:viewrestricted', $context);
    }

    if (in_array($visibility, ['restricted', 'restricted_integrity'], true)) {
        return has_capability('mod/uckkarchive:viewrestricted', $context)
            || has_capability('mod/uckkarchive:viewrestrictedmedia', $context);
    }

    if (in_array($visibility, ['hidden', 'archived'], true)) {
        return has_capability('mod/uckkarchive:validateitem', $context)
            || has_capability('mod/uckkarchive:viewrestricted', $context);
    }

    return true;
}

/**
 * Return whether the current user may see one archive item.
 *
 * This controller keeps only the final UI gate here. Detailed archive visibility
 * decisions should also be enforced by service/output classes.
 *
 * @param stdClass $item Archive item.
 * @param context_module $context Module context.
 * @return bool
 */
function mod_uckkarchive_view_can_see_item(stdClass $item, context_module $context): bool {
    global $USER;

    $visibility = mod_uckkarchive_view_normalise_visibility((string)($item->visibility ?? 'course'));
    $status = mod_uckkarchive_view_normalise_status((string)($item->status ?? 'draft'));

    if ($status === 'hidden' && !has_capability('mod/uckkarchive:validateitem', $context)) {
        return false;
    }

    if ($visibility === 'private') {
        $ownerid = (int)($item->userid ?? $item->authorid ?? $item->createdby ?? 0);

        return $ownerid === (int)$USER->id
            || has_capability('mod/uckkarchive:validateitem', $context)
            || has_capability('mod/uckkarchive:viewrestricted', $context);
    }

    return mod_uckkarchive_view_can_see_visibility($visibility, $context);
}

/**
 * Return whether the current user may see one media record.
 *
 * @param stdClass $media Media record.
 * @param context_module $context Module context.
 * @return bool
 */
function mod_uckkarchive_view_can_see_media(stdClass $media, context_module $context): bool {
    global $USER;

    if (!has_capability('mod/uckkarchive:viewmedia', $context)) {
        return false;
    }

    $visibility = mod_uckkarchive_view_normalise_visibility((string)($media->visibility ?? 'course'));
    $status = mod_uckkarchive_view_normalise_media_status((string)($media->status ?? 'draft'));

    if ($status === 'deleted_soft' && !has_capability('mod/uckkarchive:deletemedia', $context)) {
        return false;
    }

    if ($visibility === 'private') {
        $ownerid = (int)($media->ownerid ?? $media->userid ?? $media->createdby ?? 0);

        return $ownerid === (int)$USER->id
            || has_capability('mod/uckkarchive:editmedia', $context)
            || has_capability('mod/uckkarchive:viewrestrictedmedia', $context);
    }

    return mod_uckkarchive_view_can_see_visibility($visibility, $context);
}

/**
 * Convert an archive item record into template data.
 *
 * @param stdClass $item Archive item record.
 * @param cm_info|stdClass $cm Course module.
 * @param context_module $context Module context.
 * @return stdClass
 */
function mod_uckkarchive_view_export_item(stdClass $item, cm_info|stdClass $cm, context_module $context): stdClass {
    $status = mod_uckkarchive_view_normalise_status((string)($item->status ?? 'draft'));
    $visibility = mod_uckkarchive_view_normalise_visibility((string)($item->visibility ?? 'course'));
    $itemtype = clean_param((string)($item->itemtype ?? $item->type ?? 'proof'), PARAM_ALPHANUMEXT);

    $title = (string)mod_uckkarchive_view_first_field($item, ['title', 'name', 'subject'], get_string('archiveitem', 'uckkarchive'));
    $summary = (string)mod_uckkarchive_view_first_field($item, ['summary', 'publicsummary', 'description'], '');

    $data = new stdClass();
    $data->id = (int)($item->id ?? 0);
    $data->archiveid = (int)($item->archiveid ?? $item->uckkarchiveid ?? 0);
    $data->title = format_string($title);
    $data->summary = format_text($summary, FORMAT_HTML, ['context' => $context]);
    $data->hassummary = trim(strip_tags($summary)) !== '';
    $data->itemtype = $itemtype;
    $data->itemtypelabel = mod_uckkarchive_view_string(
        'itemtype:' . str_replace('_', '', $itemtype),
        mod_uckkarchive_view_label_from_key($itemtype)
    );
    $data->status = $status;
    $data->statuslabel = mod_uckkarchive_view_string(
        'status:' . str_replace('_', '', $status),
        mod_uckkarchive_view_label_from_key($status)
    );
    $data->statusclass = mod_uckkarchive_view_css_class('status', $status);
    $data->visibility = $visibility;
    $data->visibilitylabel = mod_uckkarchive_view_string(
        'visibility:' . str_replace('_', '', $visibility),
        mod_uckkarchive_view_label_from_key($visibility)
    );
    $data->visibilityclass = mod_uckkarchive_view_css_class('visibility', $visibility);
    $data->url = (new moodle_url('/mod/uckkarchive/item.php', [
        'id' => $cm->id,
        'itemid' => $data->id,
    ]))->out(false);

    $data->timecreated = (int)($item->timecreated ?? 0);
    $data->timecreatedlabel = $data->timecreated > 0 ? userdate($data->timecreated) : '';
    $data->hastimecreated = $data->timecreated > 0;

    $data->timemodified = (int)($item->timemodified ?? 0);
    $data->timemodifiedlabel = $data->timemodified > 0 ? userdate($data->timemodified) : '';
    $data->hastimemodified = $data->timemodified > 0;

    $data->versionno = (int)($item->versionno ?? 1);
    $data->hasversion = $data->versionno > 1;
    $data->versionlabel = get_string('versionx', 'uckkarchive', $data->versionno);

    $data->hasprovenance = !empty($item->provenance)
        || !empty($item->origincomponent)
        || !empty($item->sourcecomponent)
        || !empty($item->provenancehash);

    $data->provenance = [
        'sourcecomponent' => (string)($item->sourcecomponent ?? $item->origincomponent ?? $item->provenance ?? ''),
        'sourceid' => (int)($item->sourceid ?? $item->originobjectid ?? 0),
        'hash' => (string)($item->provenancehash ?? ''),
    ];

    return $data;
}

/**
 * Convert a media record into template data.
 *
 * @param stdClass $media Media record.
 * @param cm_info|stdClass $cm Course module.
 * @param context_module $context Module context.
 * @return stdClass
 */
function mod_uckkarchive_view_export_media(stdClass $media, cm_info|stdClass $cm, context_module $context): stdClass {
    $status = mod_uckkarchive_view_normalise_media_status((string)($media->status ?? 'draft'));
    $visibility = mod_uckkarchive_view_normalise_visibility((string)($media->visibility ?? 'course'));
    $mediatype = clean_param((string)($media->mediatype ?? $media->type ?? 'document'), PARAM_ALPHANUMEXT);

    $title = (string)mod_uckkarchive_view_first_field($media, ['title', 'name', 'filename'], get_string('media', 'uckkarchive'));
    $description = (string)mod_uckkarchive_view_first_field($media, ['description', 'summary', 'caption'], '');

    $data = new stdClass();
    $data->id = (int)($media->id ?? 0);
    $data->uuid = (string)($media->uuid ?? '');
    $data->archiveid = (int)($media->archiveid ?? $media->uckkarchiveid ?? 0);
    $data->title = format_string($title);
    $data->description = format_text($description, FORMAT_HTML, ['context' => $context]);
    $data->hasdescription = trim(strip_tags($description)) !== '';

    $data->mediatype = $mediatype;
    $data->mediatypelabel = mod_uckkarchive_view_string(
        'mediatype_' . $mediatype,
        mod_uckkarchive_view_label_from_key($mediatype)
    );
    $data->mediatypeclass = mod_uckkarchive_view_css_class('media-type', $mediatype);

    $data->mimetype = (string)($media->mimetype ?? '');
    $data->hasmimetype = $data->mimetype !== '';

    $data->status = $status;
    $data->statuslabel = mod_uckkarchive_view_string(
        'mediastatus_' . $status,
        mod_uckkarchive_view_label_from_key($status)
    );
    $data->statusclass = mod_uckkarchive_view_css_class('status', $status);

    $data->visibility = $visibility;
    $data->visibilitylabel = mod_uckkarchive_view_string(
        'visibility:' . str_replace('_', '', $visibility),
        mod_uckkarchive_view_label_from_key($visibility)
    );
    $data->visibilityclass = mod_uckkarchive_view_css_class('visibility', $visibility);

    $data->audiencesuitability = clean_param(
        (string)($media->audiencesuitability ?? 'guided'),
        PARAM_ALPHANUMEXT
    );
    $data->audiencesuitabilitylabel = mod_uckkarchive_view_string(
        'audiencesuitability_' . $data->audiencesuitability,
        mod_uckkarchive_view_label_from_key($data->audiencesuitability)
    );
    $data->audiencesuitabilityclass = mod_uckkarchive_view_css_class(
        'audience-suitability',
        $data->audiencesuitability
    );

    $data->url = (new moodle_url('/mod/uckkarchive/media.php', [
        'id' => $cm->id,
        'mediaid' => $data->id,
    ]))->out(false);

    $data->editurl = (new moodle_url('/mod/uckkarchive/media.php', [
        'id' => $cm->id,
        'mediaid' => $data->id,
        'action' => 'edit',
    ]))->out(false);

    $data->versionurl = (new moodle_url('/mod/uckkarchive/media.php', [
        'id' => $cm->id,
        'mediaid' => $data->id,
        'action' => 'versions',
    ]))->out(false);

    $data->timecreated = (int)($media->timecreated ?? 0);
    $data->timecreatedlabel = $data->timecreated > 0 ? userdate($data->timecreated) : '';
    $data->hastimecreated = $data->timecreated > 0;

    $data->timemodified = (int)($media->timemodified ?? 0);
    $data->timemodifiedlabel = $data->timemodified > 0 ? userdate($data->timemodified) : '';
    $data->hastimemodified = $data->timemodified > 0;

    $data->isrestricted = in_array($visibility, ['restricted', 'restricted_integrity', 'restricted_cultural'], true)
        || $status === 'restricted';
    $data->isculturalrestricted = $visibility === 'restricted_cultural'
        || $data->audiencesuitability === 'restricted_cultural';

    $data->canedit = has_capability('mod/uckkarchive:editmedia', $context);
    $data->candelete = has_capability('mod/uckkarchive:deletemedia', $context);
    $data->candownload = has_capability('mod/uckkarchive:downloadmedia', $context);
    $data->canversion = has_capability('mod/uckkarchive:versionmedia', $context);
    $data->canexport = has_capability('mod/uckkarchive:exportmedia', $context);

    return $data;
}

/**
 * Load visible archive items for this activity.
 *
 * @param stdClass $archive Archive instance.
 * @param cm_info|stdClass $cm Course module.
 * @param context_module $context Module context.
 * @param int $limit Maximum items.
 * @return stdClass[]
 */
function mod_uckkarchive_view_get_items(stdClass $archive, cm_info|stdClass $cm, context_module $context, int $limit = 50): array {
    global $DB;

    if (!mod_uckkarchive_view_table_exists('uckkarchive_item')) {
        return [];
    }

    $columns = mod_uckkarchive_view_columns('uckkarchive_item');
    $conditions = [];

    if (array_key_exists('archiveid', $columns)) {
        $conditions['archiveid'] = (int)$archive->id;
    } else if (array_key_exists('uckkarchiveid', $columns)) {
        $conditions['uckkarchiveid'] = (int)$archive->id;
    }

    if (empty($conditions)) {
        return [];
    }

    $sort = array_key_exists('timemodified', $columns) ? 'timemodified DESC, id DESC' : 'id DESC';
    $items = $DB->get_records('uckkarchive_item', $conditions, $sort, '*', 0, $limit);

    $visible = [];

    foreach ($items as $item) {
        if (!mod_uckkarchive_view_can_see_item($item, $context)) {
            continue;
        }

        $visible[] = mod_uckkarchive_view_export_item($item, $cm, $context);
    }

    return $visible;
}

/**
 * Load visible media rows for this archive activity.
 *
 * @param stdClass $archive Archive instance.
 * @param cm_info|stdClass $cm Course module.
 * @param context_module $context Module context.
 * @param int $limit Maximum rows.
 * @return stdClass[]
 */
function mod_uckkarchive_view_get_media(stdClass $archive, cm_info|stdClass $cm, context_module $context, int $limit = 24): array {
    global $DB;

    if (!mod_uckkarchive_view_table_exists('uckkarchive_media')) {
        return [];
    }

    if (!has_capability('mod/uckkarchive:viewmedia', $context)) {
        return [];
    }

    $columns = mod_uckkarchive_view_columns('uckkarchive_media');
    $conditions = [];

    if (array_key_exists('archiveid', $columns)) {
        $conditions['archiveid'] = (int)$archive->id;
    } else if (array_key_exists('uckkarchiveid', $columns)) {
        $conditions['uckkarchiveid'] = (int)$archive->id;
    }

    if (empty($conditions)) {
        return [];
    }

    $sort = array_key_exists('timemodified', $columns) ? 'timemodified DESC, id DESC' : 'id DESC';
    $records = $DB->get_records('uckkarchive_media', $conditions, $sort, '*', 0, $limit);

    $rows = [];

    foreach ($records as $record) {
        if (!mod_uckkarchive_view_can_see_media($record, $context)) {
            continue;
        }

        $rows[] = mod_uckkarchive_view_export_media($record, $cm, $context);
    }

    return $rows;
}

/**
 * Load visible Kristal rows for this archive activity.
 *
 * @param stdClass $archive Archive instance.
 * @param cm_info|stdClass $cm Course module.
 * @param context_module $context Module context.
 * @param int $limit Maximum rows.
 * @return stdClass[]
 */
function mod_uckkarchive_view_get_kristals(stdClass $archive, cm_info|stdClass $cm, context_module $context, int $limit = 20): array {
    global $DB;

    if (!mod_uckkarchive_view_table_exists('uckkarchive_kristal')) {
        return [];
    }

    $columns = mod_uckkarchive_view_columns('uckkarchive_kristal');
    $conditions = [];

    if (array_key_exists('archiveid', $columns)) {
        $conditions['archiveid'] = (int)$archive->id;
    } else if (array_key_exists('uckkarchiveid', $columns)) {
        $conditions['uckkarchiveid'] = (int)$archive->id;
    }

    if (empty($conditions)) {
        return [];
    }

    $sort = array_key_exists('timemodified', $columns) ? 'timemodified DESC, id DESC' : 'id DESC';
    $records = $DB->get_records('uckkarchive_kristal', $conditions, $sort, '*', 0, $limit);
    $rows = [];

    foreach ($records as $record) {
        $status = mod_uckkarchive_view_normalise_status((string)($record->status ?? 'draft'));
        $visibility = mod_uckkarchive_view_normalise_visibility((string)($record->visibility ?? 'course'));

        if (!mod_uckkarchive_view_can_see_visibility($visibility, $context)) {
            continue;
        }

        $title = (string)mod_uckkarchive_view_first_field($record, ['title', 'name', 'concept'], get_string('kristal', 'uckkarchive'));
        $summary = (string)mod_uckkarchive_view_first_field($record, ['summary', 'description', 'body'], '');

        $row = new stdClass();
        $row->id = (int)$record->id;
        $row->title = format_string($title);
        $row->summary = format_text($summary, FORMAT_HTML, ['context' => $context]);
        $row->hassummary = trim(strip_tags($summary)) !== '';
        $row->status = $status;
        $row->statuslabel = mod_uckkarchive_view_string(
            'status:' . str_replace('_', '', $status),
            mod_uckkarchive_view_label_from_key($status)
        );
        $row->statusclass = mod_uckkarchive_view_css_class('status', $status);
        $row->visibility = $visibility;
        $row->visibilitylabel = mod_uckkarchive_view_string(
            'visibility:' . str_replace('_', '', $visibility),
            mod_uckkarchive_view_label_from_key($visibility)
        );
        $row->visibilityclass = mod_uckkarchive_view_css_class('visibility', $visibility);
        $row->url = (new moodle_url('/mod/uckkarchive/item.php', [
            'id' => $cm->id,
            'kristalid' => $row->id,
        ]))->out(false);

        $rows[] = $row;
    }

    return $rows;
}

/**
 * Count content markers for this archive.
 *
 * @param stdClass $archive Archive instance.
 * @param context_module $context Module context.
 * @return int
 */
function mod_uckkarchive_view_count_content_markers(stdClass $archive, context_module $context): int {
    global $DB;

    if (!mod_uckkarchive_view_table_exists('uckkarchive_content_marker')) {
        return 0;
    }

    if (!has_capability('mod/uckkarchive:viewadvisories', $context)) {
        return 0;
    }

    $columns = mod_uckkarchive_view_columns('uckkarchive_content_marker');
    $conditions = [];

    if (array_key_exists('archiveid', $columns)) {
        $conditions['archiveid'] = (int)$archive->id;
    } else if (array_key_exists('uckkarchiveid', $columns)) {
        $conditions['uckkarchiveid'] = (int)$archive->id;
    }

    if (empty($conditions)) {
        return 0;
    }

    return (int)$DB->count_records('uckkarchive_content_marker', $conditions);
}

/**
 * Count external works for this archive.
 *
 * @param stdClass $archive Archive instance.
 * @param context_module $context Module context.
 * @return int
 */
function mod_uckkarchive_view_count_external_works(stdClass $archive, context_module $context): int {
    global $DB;

    if (!mod_uckkarchive_view_table_exists('uckkarchive_external_work')) {
        return 0;
    }

    if (!has_capability('mod/uckkarchive:viewadvisories', $context) &&
            !has_capability('mod/uckkarchive:manageexternalworks', $context)) {
        return 0;
    }

    $columns = mod_uckkarchive_view_columns('uckkarchive_external_work');
    $conditions = [];

    if (array_key_exists('archiveid', $columns)) {
        $conditions['archiveid'] = (int)$archive->id;
    } else if (array_key_exists('uckkarchiveid', $columns)) {
        $conditions['uckkarchiveid'] = (int)$archive->id;
    }

    if (empty($conditions)) {
        return 0;
    }

    return (int)$DB->count_records('uckkarchive_external_work', $conditions);
}

/**
 * Count records by status.
 *
 * @param stdClass[] $items Exported item rows.
 * @return stdClass[]
 */
function mod_uckkarchive_view_get_status_counts(array $items): array {
    $counts = [];

    foreach ($items as $item) {
        $key = (string)$item->status;

        if (!isset($counts[$key])) {
            $counts[$key] = (object)[
                'status' => $key,
                'label' => mod_uckkarchive_view_string(
                    'status:' . str_replace('_', '', $key),
                    mod_uckkarchive_view_label_from_key($key)
                ),
                'count' => 0,
                'class' => mod_uckkarchive_view_css_class('status', $key),
            ];
        }

        $counts[$key]->count++;
    }

    return array_values($counts);
}

/**
 * Build archive view template context.
 *
 * @param stdClass $archive Archive instance.
 * @param stdClass $course Course.
 * @param cm_info|stdClass $cm Course module.
 * @param context_module $context Module context.
 * @param string $tab Active tab.
 * @return stdClass
 */
function mod_uckkarchive_view_build_context(
    stdClass $archive,
    stdClass $course,
    cm_info|stdClass $cm,
    context_module $context,
    string $tab
): stdClass {
    global $USER;

    $items = mod_uckkarchive_view_get_items($archive, $cm, $context);
    $media = mod_uckkarchive_view_get_media($archive, $cm, $context);
    $kristals = mod_uckkarchive_view_get_kristals($archive, $cm, $context);
    $contentmarkercount = mod_uckkarchive_view_count_content_markers($archive, $context);
    $externalworkcount = mod_uckkarchive_view_count_external_works($archive, $context);

    $intro = '';
    if (!empty($archive->intro)) {
        $intro = format_module_intro('uckkarchive', $archive, $cm->id);
    }

    $status = mod_uckkarchive_view_normalise_status((string)($archive->status ?? 'validated'));
    $visibility = mod_uckkarchive_view_normalise_visibility((string)($archive->visibility ?? 'course'));

    $contextdata = new stdClass();
    $contextdata->uniqid = 'uckkarchive-view-' . $cm->id;
    $contextdata->id = (int)$archive->id;
    $contextdata->cmid = (int)$cm->id;
    $contextdata->courseid = (int)$course->id;
    $contextdata->contextid = (int)$context->id;
    $contextdata->title = format_string($archive->name);
    $contextdata->intro = $intro;
    $contextdata->hasintro = trim(strip_tags($intro)) !== '';

    $contextdata->status = $status;
    $contextdata->statuslabel = mod_uckkarchive_view_string(
        'status:' . str_replace('_', '', $status),
        mod_uckkarchive_view_label_from_key($status)
    );
    $contextdata->statusclass = mod_uckkarchive_view_css_class('status', $status);

    $contextdata->visibility = $visibility;
    $contextdata->visibilitylabel = mod_uckkarchive_view_string(
        'visibility:' . str_replace('_', '', $visibility),
        mod_uckkarchive_view_label_from_key($visibility)
    );
    $contextdata->visibilityclass = mod_uckkarchive_view_css_class('visibility', $visibility);

    $contextdata->activeitems = $tab === 'items';
    $contextdata->activemedia = $tab === 'media';
    $contextdata->activeadvisories = $tab === 'advisories';
    $contextdata->activekristals = $tab === 'kristals';
    $contextdata->activeprovenance = $tab === 'provenance';
    $contextdata->activevalidation = $tab === 'validation';
    $contextdata->activeexports = $tab === 'exports';

    $contextdata->items = $items;
    $contextdata->hasitems = !empty($items);
    $contextdata->itemcount = count($items);

    $contextdata->media = $media;
    $contextdata->hasmedia = !empty($media);
    $contextdata->mediacount = count($media);

    $contextdata->kristals = $kristals;
    $contextdata->haskristals = !empty($kristals);
    $contextdata->kristalcount = count($kristals);

    $contextdata->contentmarkercount = $contentmarkercount;
    $contextdata->hascontentmarkers = $contentmarkercount > 0;
    $contextdata->externalworkcount = $externalworkcount;
    $contextdata->hasexternalworks = $externalworkcount > 0;

    $contextdata->statuscounts = mod_uckkarchive_view_get_status_counts($items);
    $contextdata->hasstatuscounts = !empty($contextdata->statuscounts);

    $contextdata->canadditem = has_capability('mod/uckkarchive:additem', $context);
    $contextdata->canvalidate = has_capability('mod/uckkarchive:validateitem', $context);
    $contextdata->canrevise = has_capability('mod/uckkarchive:reviseitem', $context);
    $contextdata->canviewrestricted = has_capability('mod/uckkarchive:viewrestricted', $context);
    $contextdata->canexport = has_capability('mod/uckkarchive:export', $context);

    $contextdata->canviewmedia = has_capability('mod/uckkarchive:viewmedia', $context);
    $contextdata->canaddmedia = has_capability('mod/uckkarchive:addmedia', $context);
    $contextdata->caneditmedia = has_capability('mod/uckkarchive:editmedia', $context);
    $contextdata->candownloadmedia = has_capability('mod/uckkarchive:downloadmedia', $context);
    $contextdata->canexportmedia = has_capability('mod/uckkarchive:exportmedia', $context);
    $contextdata->canmanagemediacollections = has_capability('mod/uckkarchive:managemediacollections', $context);

    $contextdata->canviewadvisories = has_capability('mod/uckkarchive:viewadvisories', $context);
    $contextdata->canmanageadvisories = has_capability('mod/uckkarchive:manageadvisories', $context);
    $contextdata->canreviewadvisories = has_capability('mod/uckkarchive:reviewadvisories', $context);
    $contextdata->canviewculturallyrestricted = has_capability('mod/uckkarchive:viewculturallyrestricted', $context);
    $contextdata->canmanageexternalworks = has_capability('mod/uckkarchive:manageexternalworks', $context);

    $contextdata->additemurl = (new moodle_url('/mod/uckkarchive/add.php', ['id' => $cm->id]))->out(false);
    $contextdata->mediaurl = (new moodle_url('/mod/uckkarchive/media.php', ['id' => $cm->id]))->out(false);
    $contextdata->addmediaurl = (new moodle_url('/mod/uckkarchive/media.php', [
        'id' => $cm->id,
        'action' => 'addmedia',
    ]))->out(false);
    $contextdata->collectionsurl = (new moodle_url('/mod/uckkarchive/media.php', [
        'id' => $cm->id,
        'action' => 'collections',
    ]))->out(false);
    $contextdata->advisoriesurl = (new moodle_url('/mod/uckkarchive/media.php', [
        'id' => $cm->id,
        'action' => 'advisories',
    ]))->out(false);
    $contextdata->externalworksurl = (new moodle_url('/mod/uckkarchive/media.php', [
        'id' => $cm->id,
        'action' => 'externalworks',
    ]))->out(false);
    $contextdata->validateurl = (new moodle_url('/mod/uckkarchive/validate.php', ['id' => $cm->id]))->out(false);
    $contextdata->exporturl = (new moodle_url('/mod/uckkarchive/export.php', ['id' => $cm->id]))->out(false);
    $contextdata->mediaexporturl = (new moodle_url('/mod/uckkarchive/export.php', [
        'id' => $cm->id,
        'scope' => 'media',
    ]))->out(false);

    $contextdata->tabs = [
        (object)[
            'key' => 'items',
            'label' => get_string('archiveitems', 'uckkarchive'),
            'url' => (new moodle_url('/mod/uckkarchive/view.php', ['id' => $cm->id, 'tab' => 'items']))->out(false),
            'active' => $tab === 'items',
            'count' => count($items),
            'visible' => true,
        ],
        (object)[
            'key' => 'media',
            'label' => get_string('media', 'uckkarchive'),
            'url' => (new moodle_url('/mod/uckkarchive/view.php', ['id' => $cm->id, 'tab' => 'media']))->out(false),
            'active' => $tab === 'media',
            'count' => count($media),
            'visible' => $contextdata->canviewmedia,
        ],
        (object)[
            'key' => 'advisories',
            'label' => get_string('contentadvisories', 'uckkarchive'),
            'url' => (new moodle_url('/mod/uckkarchive/view.php', ['id' => $cm->id, 'tab' => 'advisories']))->out(false),
            'active' => $tab === 'advisories',
            'count' => $contentmarkercount,
            'visible' => $contextdata->canviewadvisories,
        ],
        (object)[
            'key' => 'kristals',
            'label' => get_string('kristals', 'uckkarchive'),
            'url' => (new moodle_url('/mod/uckkarchive/view.php', ['id' => $cm->id, 'tab' => 'kristals']))->out(false),
            'active' => $tab === 'kristals',
            'count' => count($kristals),
            'visible' => true,
        ],
        (object)[
            'key' => 'provenance',
            'label' => get_string('provenance', 'uckkarchive'),
            'url' => (new moodle_url('/mod/uckkarchive/view.php', ['id' => $cm->id, 'tab' => 'provenance']))->out(false),
            'active' => $tab === 'provenance',
            'count' => 0,
            'visible' => true,
        ],
        (object)[
            'key' => 'validation',
            'label' => get_string('validation', 'uckkarchive'),
            'url' => (new moodle_url('/mod/uckkarchive/view.php', ['id' => $cm->id, 'tab' => 'validation']))->out(false),
            'active' => $tab === 'validation',
            'count' => 0,
            'visible' => $contextdata->canvalidate,
        ],
        (object)[
            'key' => 'exports',
            'label' => get_string('exports', 'uckkarchive'),
            'url' => (new moodle_url('/mod/uckkarchive/view.php', ['id' => $cm->id, 'tab' => 'exports']))->out(false),
            'active' => $tab === 'exports',
            'count' => 0,
            'visible' => $contextdata->canexport || $contextdata->canexportmedia,
        ],
    ];

    $contextdata->actions = [];

    if ($contextdata->canadditem) {
        $contextdata->actions[] = (object)[
            'key' => 'additem',
            'label' => get_string('addarchiveitem', 'uckkarchive'),
            'url' => $contextdata->additemurl,
            'primary' => true,
            'secondary' => false,
            'danger' => false,
        ];
    }

    if ($contextdata->canaddmedia) {
        $contextdata->actions[] = (object)[
            'key' => 'addmedia',
            'label' => get_string('addmedia', 'uckkarchive'),
            'url' => $contextdata->addmediaurl,
            'primary' => false,
            'secondary' => true,
            'danger' => false,
        ];
    }

    if ($contextdata->canmanagemediacollections) {
        $contextdata->actions[] = (object)[
            'key' => 'collections',
            'label' => get_string('mediacollections', 'uckkarchive'),
            'url' => $contextdata->collectionsurl,
            'primary' => false,
            'secondary' => true,
            'danger' => false,
        ];
    }

    if ($contextdata->canmanageadvisories) {
        $contextdata->actions[] = (object)[
            'key' => 'advisories',
            'label' => get_string('contentadvisories', 'uckkarchive'),
            'url' => $contextdata->advisoriesurl,
            'primary' => false,
            'secondary' => true,
            'danger' => false,
        ];
    }

    if ($contextdata->canmanageexternalworks) {
        $contextdata->actions[] = (object)[
            'key' => 'externalworks',
            'label' => get_string('externalworks', 'uckkarchive'),
            'url' => $contextdata->externalworksurl,
            'primary' => false,
            'secondary' => true,
            'danger' => false,
        ];
    }

    if ($contextdata->canvalidate) {
        $contextdata->actions[] = (object)[
            'key' => 'validate',
            'label' => get_string('validatearchiveitems', 'uckkarchive'),
            'url' => $contextdata->validateurl,
            'primary' => false,
            'secondary' => true,
            'danger' => false,
        ];
    }

    if ($contextdata->canexport) {
        $contextdata->actions[] = (object)[
            'key' => 'export',
            'label' => get_string('exportarchive', 'uckkarchive'),
            'url' => $contextdata->exporturl,
            'primary' => false,
            'secondary' => true,
            'danger' => false,
        ];
    }

    if ($contextdata->canexportmedia) {
        $contextdata->actions[] = (object)[
            'key' => 'exportmedia',
            'label' => get_string('exportmedia', 'uckkarchive'),
            'url' => $contextdata->mediaexporturl,
            'primary' => false,
            'secondary' => true,
            'danger' => false,
        ];
    }

    $contextdata->hasactions = !empty($contextdata->actions);

    $contextdata->provenance = (object)[
        'component' => 'mod_uckkarchive',
        'objectid' => (int)$archive->id,
        'contextid' => (int)$context->id,
        'hasitemswithprovenance' => !empty(array_filter($items, static fn(stdClass $item): bool => !empty($item->hasprovenance))),
        'mediahasportableidentity' => !empty(array_filter($media, static fn(stdClass $mediaitem): bool => !empty($mediaitem->uuid))),
    ];

    $contextdata->validation = (object)[
        'pendingcount' => count(array_filter($items, static fn(stdClass $item): bool => in_array($item->status, ['submitted', 'under_review'], true))),
        'validatedcount' => count(array_filter($items, static fn(stdClass $item): bool => in_array($item->status, ['validated', 'published', 'archived'], true))),
        'contestedcount' => count(array_filter($items, static fn(stdClass $item): bool => $item->status === 'contested')),
    ];

    $contextdata->advisorysummary = (object)[
        'contentmarkercount' => $contentmarkercount,
        'externalworkcount' => $externalworkcount,
        'canviewadvisories' => $contextdata->canviewadvisories,
        'canmanageadvisories' => $contextdata->canmanageadvisories,
        'canreviewadvisories' => $contextdata->canreviewadvisories,
        'canmanageexternalworks' => $contextdata->canmanageexternalworks,
        'advisoriesurl' => $contextdata->advisoriesurl,
        'externalworksurl' => $contextdata->externalworksurl,
    ];

    $contextdata->exports = (object)[
        'canexport' => $contextdata->canexport,
        'canexportmedia' => $contextdata->canexportmedia,
        'exporturl' => $contextdata->exporturl,
        'mediaexporturl' => $contextdata->mediaexporturl,
    ];

    $contextdata->notice = get_string('archivememorynotice', 'uckkarchive');
    $contextdata->restrictednotice = $contextdata->canviewrestricted
        ? get_string('restrictedvisibletoyou', 'uckkarchive')
        : '';

    $contextdata->userid = (int)$USER->id;

    return $contextdata;
}

$id = optional_param('id', 0, PARAM_INT); // Course module id.
$u = optional_param('u', 0, PARAM_INT); // Archive instance id.
$tab = optional_param('tab', 'items', PARAM_ALPHAEXT);

if ($id) {
    $cm = get_coursemodule_from_id('uckkarchive', $id, 0, false, MUST_EXIST);
    $course = $DB->get_record('course', ['id' => $cm->course], '*', MUST_EXIST);
    $archive = $DB->get_record('uckkarchive', ['id' => $cm->instance], '*', MUST_EXIST);
} else if ($u) {
    $archive = $DB->get_record('uckkarchive', ['id' => $u], '*', MUST_EXIST);
    $courseid = (int)($archive->course ?? $archive->courseid ?? 0);
    $course = $DB->get_record('course', ['id' => $courseid], '*', MUST_EXIST);
    $cm = get_coursemodule_from_instance('uckkarchive', $archive->id, $course->id, false, MUST_EXIST);
} else {
    throw new moodle_exception('missingparam', 'error', '', 'id');
}

$context = context_module::instance($cm->id);

require_login($course, false, $cm);
require_capability('mod/uckkarchive:view', $context);

$allowedtabs = [
    'items',
    'media',
    'advisories',
    'kristals',
    'provenance',
    'validation',
    'exports',
];

if (!in_array($tab, $allowedtabs, true)) {
    throw new moodle_exception('invalidarchivetab', 'uckkarchive');
}

if ($tab === 'media' && !has_capability('mod/uckkarchive:viewmedia', $context)) {
    throw new required_capability_exception($context, 'mod/uckkarchive:viewmedia', 'nopermissions', '');
}

if ($tab === 'advisories' && !has_capability('mod/uckkarchive:viewadvisories', $context)) {
    throw new required_capability_exception($context, 'mod/uckkarchive:viewadvisories', 'nopermissions', '');
}

if ($tab === 'validation' && !has_capability('mod/uckkarchive:validateitem', $context)) {
    throw new required_capability_exception($context, 'mod/uckkarchive:validateitem', 'nopermissions', '');
}

if ($tab === 'exports' &&
        !has_capability('mod/uckkarchive:export', $context) &&
        !has_capability('mod/uckkarchive:exportmedia', $context)) {
    throw new required_capability_exception($context, 'mod/uckkarchive:export', 'nopermissions', '');
}

$pageurl = new moodle_url('/mod/uckkarchive/view.php', [
    'id' => $cm->id,
    'tab' => $tab,
]);

$PAGE->set_url($pageurl);
$PAGE->set_course($course);
$PAGE->set_cm($cm);
$PAGE->set_context($context);
$PAGE->set_title(format_string($archive->name));
$PAGE->set_heading(format_string($course->fullname));
$PAGE->requires->js_call_amd('mod_uckkarchive/archive', 'init', [[
    'cmid' => (int)$cm->id,
    'archiveid' => (int)$archive->id,
    'contextid' => (int)$context->id,
    'tab' => $tab,
]]);

if (has_capability('mod/uckkarchive:viewmedia', $context)) {
    $PAGE->requires->js_call_amd('mod_uckkarchive/media', 'init', [[
        'cmid' => (int)$cm->id,
        'archiveid' => (int)$archive->id,
        'contextid' => (int)$context->id,
    ]]);
}

if (has_capability('mod/uckkarchive:viewadvisories', $context)) {
    $PAGE->requires->js_call_amd('mod_uckkarchive/content_advisory', 'init', [[
        'cmid' => (int)$cm->id,
        'archiveid' => (int)$archive->id,
        'contextid' => (int)$context->id,
    ]]);
}

$completion = new completion_info($course);
$completion->set_module_viewed($cm);

// Trigger a view event only if the event class exists in this build.
if (class_exists('\mod_uckkarchive\event\archive_viewed')) {
    $event = \mod_uckkarchive\event\archive_viewed::create([
        'objectid' => (int)$archive->id,
        'context' => $context,
        'other' => [
            'courseid' => (int)$course->id,
            'cmid' => (int)$cm->id,
            'tab' => $tab,
        ],
    ]);

    $event->add_record_snapshot('course', $course);
    $event->add_record_snapshot('course_modules', $cm);
    $event->add_record_snapshot('uckkarchive', $archive);
    $event->trigger();
}

$templatecontext = mod_uckkarchive_view_build_context($archive, $course, $cm, $context, $tab);

echo $OUTPUT->header();

if (class_exists('\mod_uckkarchive\output\archive_view')) {
    $renderable = new \mod_uckkarchive\output\archive_view($templatecontext);
    echo $OUTPUT->render($renderable);
} else {
    echo $OUTPUT->render_from_template('mod_uckkarchive/archive_view', $templatecontext);
}

echo $OUTPUT->footer();

