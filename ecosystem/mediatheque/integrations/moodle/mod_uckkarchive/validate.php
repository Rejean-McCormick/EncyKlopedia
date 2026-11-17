<?php
// This file is part of Moodle - https://moodle.org/
//
// Moodle is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// any later version.

/**
 * Archive item validation controller.
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

defined('MOODLE_INTERNAL') || die();

use core\output\notification;
use mod_uckkarchive\event\archive_item_validated;
use mod_uckkarchive\form\validation_form;
use mod_uckkarchive\output\content_advisory_panel;

$id = optional_param('id', 0, PARAM_INT); // Course module id.
$a = optional_param('a', 0, PARAM_INT); // Archive activity instance id.
$itemid = optional_param('itemid', 0, PARAM_INT);
$returnurl = optional_param('returnurl', '', PARAM_LOCALURL);

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
require_capability('mod/uckkarchive:validateitem', $context);

$baseurl = new moodle_url('/mod/uckkarchive/validate.php', ['id' => $cm->id]);

$PAGE->set_url($baseurl);
$PAGE->set_course($course);
$PAGE->set_cm($cm);
$PAGE->set_context($context);
$PAGE->set_heading(format_string($course->fullname));
$PAGE->set_title(get_string('validatearchiveitems', 'uckkarchive'));

$completion = new completion_info($course);
$completion->set_module_viewed($cm);

if ($itemid <= 0) {
    uckkarchive_validate_render_queue($archive, $course, $cm, $context);
    exit;
}

$item = $DB->get_record('uckkarchive_item', [
    'id' => $itemid,
    'archiveid' => $archive->id,
], '*', MUST_EXIST);

$pageurl = new moodle_url('/mod/uckkarchive/validate.php', [
    'id' => $cm->id,
    'itemid' => $item->id,
]);

$itemurl = new moodle_url('/mod/uckkarchive/item.php', [
    'id' => $cm->id,
    'itemid' => $item->id,
]);

$return = $returnurl !== '' ? new moodle_url($returnurl) : $itemurl;

$PAGE->set_url($pageurl);
$PAGE->set_title(format_string($item->title ?? $archive->name));

if (!uckkarchive_validate_can_validate_item($archive, $item, $cm, $context, $USER)) {
    echo $OUTPUT->header();
    echo $OUTPUT->heading(get_string('validateitem', 'uckkarchive'));
    echo $OUTPUT->notification(get_string('cannotvalidateitem', 'uckkarchive'), notification::NOTIFY_ERROR);
    echo $OUTPUT->continue_button($return);
    echo $OUTPUT->footer();
    exit;
}

$proofs = uckkarchive_validate_get_item_proofs($item, $context, $USER);
$provenance = uckkarchive_validate_get_item_provenance($item, $context, $USER);
$revisions = uckkarchive_validate_get_item_revisions($item, $context, $USER);
$contentmarkers = uckkarchive_validate_get_content_markers($archive, $item, $context, $USER);
$contentreviews = uckkarchive_validate_get_content_reviews($contentmarkers);
$warnings = uckkarchive_validate_get_validation_warnings(
    $archive,
    $item,
    $proofs,
    $provenance,
    $contentmarkers,
    $context,
    $USER
);

$form = new validation_form($pageurl, [
    'archive' => $archive,
    'item' => $item,
    'course' => $course,
    'cm' => $cm,
    'context' => $context,
    'proofs' => $proofs,
    'provenance' => $provenance,
    'revisions' => $revisions,
    'contentmarkers' => $contentmarkers,
    'contentreviews' => $contentreviews,
    'warnings' => $warnings,
    'returnurl' => $return->out_as_local_url(false),
]);

if ($form->is_cancelled()) {
    redirect($return);
}

$defaultdata = new stdClass();
$defaultdata->id = $cm->id;
$defaultdata->itemid = $item->id;
$defaultdata->returnurl = $return->out_as_local_url(false);
$defaultdata->validationstate = $item->validationstate ?? 'unverified';
$defaultdata->status = $item->status ?? 'pending_review';
$defaultdata->visibility = $item->visibility ?? 'course';
$defaultdata->provenancecheck = 0;
$defaultdata->proofcheck = 0;
$defaultdata->privacycheck = 0;
$defaultdata->integritycheck = 0;
$defaultdata->contentadvisorycheck = empty($contentmarkers) ? 1 : 0;
$defaultdata->archivepolicy = $item->archivepolicy ?? 'standard';
$defaultdata->validationnotes = '';
$defaultdata->publicsummary = $item->publicsummary ?? '';
$defaultdata->restrictednotes = '';

$form->set_data($defaultdata);

if ($data = $form->get_data()) {
    require_sesskey();

    $validationdata = [
        'validationstate' => clean_param((string)$data->validationstate, PARAM_ALPHANUMEXT),
        'status' => clean_param((string)$data->status, PARAM_ALPHANUMEXT),
        'visibility' => clean_param((string)$data->visibility, PARAM_ALPHANUMEXT),
        'archivepolicy' => clean_param((string)$data->archivepolicy, PARAM_ALPHANUMEXT),
        'provenancecheck' => !empty($data->provenancecheck) ? 1 : 0,
        'proofcheck' => !empty($data->proofcheck) ? 1 : 0,
        'privacycheck' => !empty($data->privacycheck) ? 1 : 0,
        'integritycheck' => !empty($data->integritycheck) ? 1 : 0,
        'contentadvisorycheck' => !empty($data->contentadvisorycheck) ? 1 : 0,
        'validationnotes' => (string)($data->validationnotes ?? ''),
        'publicsummary' => (string)($data->publicsummary ?? ''),
        'restrictednotes' => (string)($data->restrictednotes ?? ''),
    ];

    $validateditem = uckkarchive_validate_apply_item_validation(
        $archive,
        $item,
        $cm,
        $course,
        $context,
        $USER,
        $validationdata
    );

    $event = archive_item_validated::create([
        'objectid' => $validateditem->id,
        'context' => $context,
        'other' => [
            'archiveid' => $archive->id,
            'cmid' => $cm->id,
            'courseid' => $course->id,
            'status' => $validateditem->status,
            'validationstate' => $validateditem->validationstate ?? $validationdata['validationstate'],
            'visibility' => $validateditem->visibility,
            'contentmarkercount' => count($contentmarkers),
        ],
    ]);
    $event->add_record_snapshot('course', $course);
    $event->add_record_snapshot('course_modules', $cm);
    $event->add_record_snapshot('uckkarchive', $archive);
    $event->add_record_snapshot('uckkarchive_item', $validateditem);
    $event->trigger();

    redirect(
        new moodle_url('/mod/uckkarchive/item.php', [
            'id' => $cm->id,
            'itemid' => $validateditem->id,
        ]),
        get_string('itemvalidated', 'uckkarchive'),
        null,
        notification::NOTIFY_SUCCESS
    );
}

echo $OUTPUT->header();

echo $OUTPUT->heading(get_string('validateitem', 'uckkarchive'));

echo html_writer::start_div('uckkarchive-validate');

uckkarchive_validate_render_item_summary($archive, $item, $proofs, $provenance, $revisions, $contentmarkers);

uckkarchive_validate_render_warnings($warnings);

uckkarchive_validate_render_content_advisory_panel(
    $archive,
    $cm,
    $context,
    $item,
    $contentmarkers,
    $contentreviews
);

uckkarchive_validate_render_proofs($proofs);

uckkarchive_validate_render_provenance($provenance);

uckkarchive_validate_render_revisions($revisions);

$form->display();

echo html_writer::link($return, get_string('backtoarchiveitem', 'uckkarchive'), [
    'class' => 'btn btn-secondary mt-3',
]);

echo html_writer::div(
    get_string('validationgovernancenotice', 'uckkarchive'),
    'alert alert-info uckkarchive-validate__notice mt-3',
    ['role' => 'status']
);

echo html_writer::end_div();

echo $OUTPUT->footer();

/**
 * Render validation queue when no item id is supplied.
 *
 * @param stdClass $archive Archive instance.
 * @param stdClass $course Course.
 * @param stdClass $cm Course module.
 * @param context_module $context Context.
 * @return void
 */
function uckkarchive_validate_render_queue(
    stdClass $archive,
    stdClass $course,
    stdClass $cm,
    context_module $context
): void {
    global $DB, $OUTPUT, $PAGE;

    $PAGE->set_title(get_string('validatearchiveitems', 'uckkarchive'));

    $params = [
        'archiveid' => (int)$archive->id,
        'pendingstatus' => 'pending_review',
        'correctionstatus' => 'correction_required',
        'draftstatus' => 'draft',
        'unverified' => 'unverified',
        'contested' => 'contested',
    ];

    $items = $DB->get_records_select(
        'uckkarchive_item',
        'archiveid = :archiveid
             AND (
                    status IN (:pendingstatus, :correctionstatus, :draftstatus)
                 OR validationstate IN (:unverified, :contested)
             )',
        $params,
        'timemodified DESC, id DESC',
        'id, archiveid, title, itemtype, status, validationstate, visibility, createdby, timecreated, timemodified',
        0,
        100
    );

    echo $OUTPUT->header();
    echo $OUTPUT->heading(get_string('validatearchiveitems', 'uckkarchive'));

    echo html_writer::start_div('uckkarchive-validation-queue');

    if (empty($items)) {
        echo html_writer::div(
            get_string('archiveviewempty', 'uckkarchive'),
            'alert alert-info',
            ['role' => 'status']
        );
        echo html_writer::link(
            new moodle_url('/mod/uckkarchive/view.php', ['id' => $cm->id]),
            get_string('backtoarchive', 'uckkarchive'),
            ['class' => 'btn btn-secondary']
        );
        echo html_writer::end_div();
        echo $OUTPUT->footer();
        return;
    }

    $table = new html_table();
    $table->attributes['class'] = 'generaltable uckkarchive-validation-queue__table';
    $table->head = [
        get_string('title', 'uckkarchive'),
        get_string('itemtype', 'uckkarchive'),
        get_string('status', 'uckkarchive'),
        get_string('validationstate', 'uckkarchive'),
        get_string('visibility', 'uckkarchive'),
        get_string('timemodified', 'uckkarchive'),
        get_string('actions', 'uckkarchive'),
    ];

    foreach ($items as $item) {
        $validateurl = new moodle_url('/mod/uckkarchive/validate.php', [
            'id' => $cm->id,
            'itemid' => $item->id,
        ]);

        $itemurl = new moodle_url('/mod/uckkarchive/item.php', [
            'id' => $cm->id,
            'itemid' => $item->id,
        ]);

        $actions = html_writer::link($itemurl, get_string('view', 'uckkarchive'), [
            'class' => 'btn btn-secondary btn-sm mr-1',
        ]);
        $actions .= html_writer::link($validateurl, get_string('validate', 'uckkarchive'), [
            'class' => 'btn btn-primary btn-sm',
        ]);

        $table->data[] = [
            html_writer::link($itemurl, format_string($item->title ?? get_string('archiveitem', 'uckkarchive'))),
            s($item->itemtype ?? ''),
            s($item->status ?? ''),
            s($item->validationstate ?? ''),
            s($item->visibility ?? ''),
            !empty($item->timemodified) ? userdate((int)$item->timemodified) : '',
            $actions,
        ];
    }

    echo html_writer::table($table);

    echo html_writer::div(
        get_string('validationgovernancenotice', 'uckkarchive'),
        'alert alert-info mt-3',
        ['role' => 'status']
    );

    echo html_writer::end_div();

    echo $OUTPUT->footer();
}

/**
 * Return whether current user can validate an item.
 *
 * @param stdClass $archive Archive.
 * @param stdClass $item Item.
 * @param stdClass $cm Course module.
 * @param context_module $context Context.
 * @param stdClass $user User.
 * @return bool
 */
function uckkarchive_validate_can_validate_item(
    stdClass $archive,
    stdClass $item,
    stdClass $cm,
    context_module $context,
    stdClass $user
): bool {
    if (function_exists('uckkarchive_can_validate_item')) {
        return uckkarchive_can_validate_item($archive, $item, $cm, $context, $user);
    }

    if (!has_capability('mod/uckkarchive:validateitem', $context)) {
        return false;
    }

    if (($item->status ?? '') === 'deleted_soft') {
        return false;
    }

    return true;
}

/**
 * Apply validation.
 *
 * @param stdClass $archive Archive.
 * @param stdClass $item Item.
 * @param stdClass $cm Course module.
 * @param stdClass $course Course.
 * @param context_module $context Context.
 * @param stdClass $user User.
 * @param array<string, mixed> $validationdata Validation data.
 * @return stdClass Updated item.
 */
function uckkarchive_validate_apply_item_validation(
    stdClass $archive,
    stdClass $item,
    stdClass $cm,
    stdClass $course,
    context_module $context,
    stdClass $user,
    array $validationdata
): stdClass {
    global $DB;

    if (function_exists('uckkarchive_validate_item')) {
        return uckkarchive_validate_item(
            $archive,
            $item,
            $cm,
            $course,
            $context,
            $user,
            $validationdata
        );
    }

    $record = new stdClass();
    $record->id = (int)$item->id;
    $record->status = $validationdata['status'];
    $record->validationstate = $validationdata['validationstate'];
    $record->visibility = $validationdata['visibility'];
    $record->archivepolicy = $validationdata['archivepolicy'];
    $record->validationnotes = $validationdata['validationnotes'];
    $record->publicsummary = $validationdata['publicsummary'];
    $record->restrictednotes = $validationdata['restrictednotes'];
    $record->validatedby = (int)$user->id;
    $record->timevalidated = time();
    $record->modifiedby = (int)$user->id;
    $record->timemodified = time();

    $columns = $DB->get_columns('uckkarchive_item');
    foreach (array_keys((array)$record) as $field) {
        if ($field !== 'id' && !array_key_exists($field, $columns)) {
            unset($record->{$field});
        }
    }

    $DB->update_record('uckkarchive_item', $record);

    return $DB->get_record('uckkarchive_item', ['id' => (int)$item->id], '*', MUST_EXIST);
}

/**
 * Load item proofs.
 *
 * @param stdClass $item Item.
 * @param context_module $context Context.
 * @param stdClass $user User.
 * @return array<int, stdClass>
 */
function uckkarchive_validate_get_item_proofs(stdClass $item, context_module $context, stdClass $user): array {
    if (function_exists('uckkarchive_get_item_proofs')) {
        return uckkarchive_get_item_proofs($item, $context, $user);
    }

    return [];
}

/**
 * Load item provenance.
 *
 * @param stdClass $item Item.
 * @param context_module $context Context.
 * @param stdClass $user User.
 * @return array<int, stdClass>
 */
function uckkarchive_validate_get_item_provenance(stdClass $item, context_module $context, stdClass $user): array {
    if (function_exists('uckkarchive_get_item_provenance')) {
        return uckkarchive_get_item_provenance($item, $context, $user);
    }

    return [];
}

/**
 * Load item revisions.
 *
 * @param stdClass $item Item.
 * @param context_module $context Context.
 * @param stdClass $user User.
 * @return array<int, stdClass>
 */
function uckkarchive_validate_get_item_revisions(stdClass $item, context_module $context, stdClass $user): array {
    if (function_exists('uckkarchive_get_item_revisions')) {
        return uckkarchive_get_item_revisions($item, $context, $user);
    }

    return [];
}

/**
 * Load archive-item content advisory markers.
 *
 * @param stdClass $archive Archive.
 * @param stdClass $item Item.
 * @param context_module $context Context.
 * @param stdClass $user User.
 * @return array<int, stdClass>
 */
function uckkarchive_validate_get_content_markers(
    stdClass $archive,
    stdClass $item,
    context_module $context,
    stdClass $user
): array {
    global $DB;

    if (class_exists('\mod_uckkarchive\local\content_marker')) {
        try {
            $markers = \mod_uckkarchive\local\content_marker::list_by_target(
                'archive_item',
                (int)$item->id,
                ['archiveid' => (int)$archive->id],
                0,
                0
            );

            if (class_exists('\mod_uckkarchive\local\content_policy') &&
                    method_exists('\mod_uckkarchive\local\content_policy', 'filter_markers')) {
                $markers = \mod_uckkarchive\local\content_policy::filter_markers($context, $markers, (int)$user->id);
            }

            return array_values($markers);
        } catch (Throwable $e) {
            debugging($e->getMessage(), DEBUG_DEVELOPER);
        }
    }

    if (!uckkarchive_validate_table_exists('uckkarchive_content_marker')) {
        return [];
    }

    $params = [
        'archiveid' => (int)$archive->id,
        'targettype' => 'archive_item',
        'targetid' => (int)$item->id,
    ];

    return array_values($DB->get_records(
        'uckkarchive_content_marker',
        $params,
        'severity DESC, timemodified DESC, id DESC'
    ));
}

/**
 * Load content reviews for markers.
 *
 * @param array<int, stdClass> $markers Markers.
 * @return array<int, stdClass>
 */
function uckkarchive_validate_get_content_reviews(array $markers): array {
    global $DB;

    if (empty($markers)) {
        return [];
    }

    $reviews = [];

    foreach ($markers as $marker) {
        if (class_exists('\mod_uckkarchive\local\content_review') &&
                method_exists('\mod_uckkarchive\local\content_review', 'get_for_marker')) {
            try {
                $markerreviews = \mod_uckkarchive\local\content_review::get_for_marker((int)$marker->id);

                foreach ($markerreviews as $review) {
                    $reviews[] = $review;
                }

                continue;
            } catch (Throwable $e) {
                debugging($e->getMessage(), DEBUG_DEVELOPER);
            }
        }

        if (uckkarchive_validate_table_exists('uckkarchive_content_review')) {
            $markerreviews = $DB->get_records(
                'uckkarchive_content_review',
                ['markerid' => (int)$marker->id],
                'timemodified DESC, id DESC'
            );

            foreach ($markerreviews as $review) {
                $reviews[] = $review;
            }
        }
    }

    return $reviews;
}

/**
 * Load validation warnings.
 *
 * @param stdClass $archive Archive.
 * @param stdClass $item Item.
 * @param array<int, stdClass> $proofs Proofs.
 * @param array<int, stdClass> $provenance Provenance records.
 * @param array<int, stdClass> $contentmarkers Content markers.
 * @param context_module $context Context.
 * @param stdClass $user User.
 * @return array<int, stdClass|string>
 */
function uckkarchive_validate_get_validation_warnings(
    stdClass $archive,
    stdClass $item,
    array $proofs,
    array $provenance,
    array $contentmarkers,
    context_module $context,
    stdClass $user
): array {
    if (function_exists('uckkarchive_get_validation_warnings')) {
        return uckkarchive_get_validation_warnings($archive, $item, $proofs, $provenance, $context, $user);
    }

    $warnings = [];

    if (empty($provenance)) {
        $warnings[] = (object)[
            'message' => get_string('provenancerequired', 'uckkarchive'),
            'severity' => 'warning',
        ];
    }

    if (empty($proofs) && empty($item->sourceurl)) {
        $warnings[] = (object)[
            'message' => get_string('contentorsourcefilesrequired', 'uckkarchive'),
            'severity' => 'warning',
        ];
    }

    if (!empty($contentmarkers)) {
        $warnings[] = (object)[
            'message' => get_string('contentadvisories', 'uckkarchive'),
            'severity' => 'info',
        ];
    }

    if (($item->visibility ?? '') === 'public' && ($item->validationstate ?? '') !== 'verified') {
        $warnings[] = (object)[
            'message' => get_string('publicvalidationrequired', 'uckkarchive'),
            'severity' => 'danger',
        ];
    }

    return $warnings;
}

/**
 * Render archive item summary.
 *
 * @param stdClass $archive Archive.
 * @param stdClass $item Item.
 * @param array<int, stdClass> $proofs Proofs.
 * @param array<int, stdClass> $provenance Provenance.
 * @param array<int, stdClass> $revisions Revisions.
 * @param array<int, stdClass> $contentmarkers Content markers.
 * @return void
 */
function uckkarchive_validate_render_item_summary(
    stdClass $archive,
    stdClass $item,
    array $proofs,
    array $provenance,
    array $revisions,
    array $contentmarkers
): void {
    echo html_writer::start_div('uckkarchive-validate__summary card mb-3');
    echo html_writer::start_div('card-body');

    echo html_writer::tag('h3', format_string($item->title ?? get_string('archiveitem', 'uckkarchive')), [
        'class' => 'card-title',
    ]);

    echo html_writer::start_tag('dl', ['class' => 'uckkarchive-validate__facts row']);

    uckkarchive_validate_render_fact(get_string('archive', 'uckkarchive'), format_string($archive->name));
    uckkarchive_validate_render_fact(get_string('archiveitem', 'uckkarchive'), format_string($item->title ?? ''));

    if (!empty($item->itemtype)) {
        uckkarchive_validate_render_fact(get_string('itemtype', 'uckkarchive'), s($item->itemtype));
    }

    if (!empty($item->status)) {
        uckkarchive_validate_render_fact(get_string('status', 'uckkarchive'), s($item->status));
    }

    if (!empty($item->validationstate)) {
        uckkarchive_validate_render_fact(get_string('validationstate', 'uckkarchive'), s($item->validationstate));
    }

    if (!empty($item->visibility)) {
        uckkarchive_validate_render_fact(get_string('visibility', 'uckkarchive'), s($item->visibility));
    }

    if (!empty($item->provenance)) {
        uckkarchive_validate_render_fact(get_string('provenance', 'uckkarchive'), s($item->provenance));
    }

    if (!empty($item->timecreated)) {
        uckkarchive_validate_render_fact(get_string('timecreated', 'uckkarchive'), userdate((int)$item->timecreated));
    }

    if (!empty($item->timemodified)) {
        uckkarchive_validate_render_fact(get_string('timemodified', 'uckkarchive'), userdate((int)$item->timemodified));
    }

    uckkarchive_validate_render_fact(get_string('proofs', 'uckkarchive'), (string)count($proofs));
    uckkarchive_validate_render_fact(get_string('provenancerecords', 'uckkarchive'), (string)count($provenance));
    uckkarchive_validate_render_fact(get_string('revisions', 'uckkarchive'), (string)count($revisions));
    uckkarchive_validate_render_fact(get_string('contentmarkers', 'uckkarchive'), (string)count($contentmarkers));

    echo html_writer::end_tag('dl');

    echo html_writer::end_div();
    echo html_writer::end_div();
}

/**
 * Render one summary fact.
 *
 * @param string $label Label.
 * @param string $value Value.
 * @return void
 */
function uckkarchive_validate_render_fact(string $label, string $value): void {
    echo html_writer::tag('dt', $label, ['class' => 'col-sm-3']);
    echo html_writer::tag('dd', $value, ['class' => 'col-sm-9']);
}

/**
 * Render warnings.
 *
 * @param array<int, stdClass|string> $warnings Warnings.
 * @return void
 */
function uckkarchive_validate_render_warnings(array $warnings): void {
    if (empty($warnings)) {
        return;
    }

    echo html_writer::start_div('uckkarchive-validate__warnings', ['role' => 'status']);

    foreach ($warnings as $warning) {
        $message = is_object($warning) ? ($warning->message ?? '') : (string)$warning;
        $severity = is_object($warning) ? ($warning->severity ?? 'warning') : 'warning';

        $class = match ($severity) {
            'danger', 'error' => 'alert-danger',
            'info', 'notice' => 'alert-info',
            'success', 'clear' => 'alert-success',
            default => 'alert-warning',
        };

        if (trim((string)$message) !== '') {
            echo html_writer::div(format_string((string)$message), 'alert ' . $class);
        }
    }

    echo html_writer::end_div();
}

/**
 * Render content advisory panel.
 *
 * @param stdClass $archive Archive.
 * @param stdClass $cm Course module.
 * @param context_module $context Context.
 * @param stdClass $item Item.
 * @param array<int, stdClass> $contentmarkers Content markers.
 * @param array<int, stdClass> $contentreviews Content reviews.
 * @return void
 */
function uckkarchive_validate_render_content_advisory_panel(
    stdClass $archive,
    stdClass $cm,
    context_module $context,
    stdClass $item,
    array $contentmarkers,
    array $contentreviews
): void {
    global $OUTPUT;

    if (empty($contentmarkers)) {
        return;
    }

    if (class_exists(content_advisory_panel::class)) {
        $panel = new content_advisory_panel(
            (int)$archive->id,
            (int)$cm->id,
            (int)$context->id,
            'archive_item',
            (int)$item->id,
            format_string($item->title ?? ''),
            $contentmarkers,
            $contentreviews,
            [],
            [],
            [],
            [
                'canview' => true,
                'canmanage' => has_capability('mod/uckkarchive:manageadvisories', $context),
                'canreview' => has_capability('mod/uckkarchive:validateitem', $context),
                'canedit' => has_capability('mod/uckkarchive:manageadvisories', $context),
                'candelete' => has_capability('mod/uckkarchive:manageadvisories', $context),
                'canexport' => has_capability('mod/uckkarchive:export', $context),
                'canviewrestricted' => has_capability('mod/uckkarchive:viewrestricted', $context),
                'canviewcultural' => has_capability('mod/uckkarchive:viewculturallyrestricted', $context),
            ]
        );

        echo $OUTPUT->render_from_template(
            'mod_uckkarchive/content_advisory_panel',
            $panel->export_for_template($OUTPUT)
        );

        return;
    }

    echo html_writer::start_div('uckkarchive-validate__content-markers card mb-3');
    echo html_writer::start_div('card-body');

    echo html_writer::tag('h3', get_string('contentadvisories', 'uckkarchive'), [
        'class' => 'card-title',
    ]);

    echo html_writer::start_tag('ul', ['class' => 'uckkarchive-validate__content-marker-list']);

    foreach ($contentmarkers as $marker) {
        echo html_writer::tag('li', format_string($marker->description ?? $marker->tagkey ?? get_string('contentmarker', 'uckkarchive')));
    }

    echo html_writer::end_tag('ul');

    echo html_writer::end_div();
    echo html_writer::end_div();
}

/**
 * Render proofs.
 *
 * @param array<int, stdClass> $proofs Proofs.
 * @return void
 */
function uckkarchive_validate_render_proofs(array $proofs): void {
    if (empty($proofs)) {
        return;
    }

    echo html_writer::start_div('uckkarchive-validate__proofs card mb-3');
    echo html_writer::start_div('card-body');

    echo html_writer::tag('h3', get_string('proofrecords', 'uckkarchive'), [
        'class' => 'card-title',
    ]);

    echo html_writer::start_tag('ul', ['class' => 'uckkarchive-validate__proof-list']);

    foreach ($proofs as $proof) {
        echo html_writer::start_tag('li');

        if (!empty($proof->url)) {
            echo html_writer::link(new moodle_url($proof->url), format_string($proof->title ?? get_string('proof', 'uckkarchive')));
        } else {
            echo html_writer::tag('strong', format_string($proof->title ?? get_string('proof', 'uckkarchive')));
        }

        if (!empty($proof->prooftype)) {
            echo html_writer::span(' — ' . s($proof->prooftype), 'uckkarchive-validate__proof-type');
        }

        if (!empty($proof->validationstate)) {
            echo html_writer::span(' — ' . s($proof->validationstate), 'uckkarchive-validate__proof-validation');
        }

        echo html_writer::end_tag('li');
    }

    echo html_writer::end_tag('ul');

    echo html_writer::end_div();
    echo html_writer::end_div();
}

/**
 * Render provenance records.
 *
 * @param array<int, stdClass> $provenance Provenance records.
 * @return void
 */
function uckkarchive_validate_render_provenance(array $provenance): void {
    if (empty($provenance)) {
        return;
    }

    echo html_writer::start_div('uckkarchive-validate__provenance card mb-3');
    echo html_writer::start_div('card-body');

    echo html_writer::tag('h3', get_string('provenancerecords', 'uckkarchive'), [
        'class' => 'card-title',
    ]);

    echo html_writer::start_tag('ul', ['class' => 'uckkarchive-validate__provenance-list']);

    foreach ($provenance as $record) {
        echo html_writer::start_tag('li');

        echo html_writer::tag('strong', s($record->sourcetype ?? get_string('provenance', 'uckkarchive')));

        if (!empty($record->summary)) {
            echo html_writer::tag('p', s($record->summary));
        }

        if (!empty($record->validationstate)) {
            echo html_writer::span(s($record->validationstate), 'badge badge-secondary');
        }

        echo html_writer::end_tag('li');
    }

    echo html_writer::end_tag('ul');

    echo html_writer::end_div();
    echo html_writer::end_div();
}

/**
 * Render revisions.
 *
 * @param array<int, stdClass> $revisions Revisions.
 * @return void
 */
function uckkarchive_validate_render_revisions(array $revisions): void {
    if (empty($revisions)) {
        return;
    }

    echo html_writer::start_div('uckkarchive-validate__revisions card mb-3');
    echo html_writer::start_div('card-body');

    echo html_writer::tag('h3', get_string('revisionhistory', 'uckkarchive'), [
        'class' => 'card-title',
    ]);

    echo html_writer::start_tag('ul', ['class' => 'uckkarchive-validate__revision-list']);

    foreach ($revisions as $revision) {
        $label = get_string('revision', 'uckkarchive');

        if (!empty($revision->versionno)) {
            $label .= ' ' . s($revision->versionno);
        }

        if (!empty($revision->timemodified)) {
            $label .= ' — ' . userdate((int)$revision->timemodified);
        }

        echo html_writer::tag('li', $label);
    }

    echo html_writer::end_tag('ul');

    echo html_writer::end_div();
    echo html_writer::end_div();
}

/**
 * Return whether a table exists.
 *
 * @param string $table Table name.
 * @return bool
 */
function uckkarchive_validate_table_exists(string $table): bool {
    global $DB;

    return $DB->get_manager()->table_exists(new xmldb_table($table));
}