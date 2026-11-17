<?php
// This file is part of Moodle - https://moodle.org/
//
// Moodle is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// any later version.

/**
 * Add an item to a UCKK archive activity.
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
require_once($CFG->dirroot . '/mod/uckkarchive/locallib.php');

defined('MOODLE_INTERNAL') || die();

use core\output\notification;
use mod_uckkarchive\event\archive_item_created;
use mod_uckkarchive\form\archive_item_form;

$id = optional_param('id', 0, PARAM_INT); // Course module id.
$a = optional_param('a', 0, PARAM_INT); // Archive instance id.
$returnurl = optional_param('returnurl', '', PARAM_LOCALURL);

// Optional origin data supplied by challenge, assembly, course format, integrity,
// reports, portfolio, media, or external-work flows.
$origincomponent = optional_param('origincomponent', '', PARAM_COMPONENT);
$originarea = optional_param('originarea', '', PARAM_ALPHANUMEXT);
$originid = optional_param('originid', 0, PARAM_INT);
$origintype = optional_param('origintype', '', PARAM_ALPHANUMEXT);

if ($id) {
    $cm = get_coursemodule_from_id('uckkarchive', $id, 0, false, MUST_EXIST);
    $course = $DB->get_record('course', ['id' => $cm->course], '*', MUST_EXIST);
    $archive = $DB->get_record('uckkarchive', ['id' => $cm->instance], '*', MUST_EXIST);
} else if ($a) {
    $archive = $DB->get_record('uckkarchive', ['id' => $a], '*', MUST_EXIST);
    $courseid = property_exists($archive, 'course') ? (int)$archive->course : (int)($archive->courseid ?? 0);
    $course = $DB->get_record('course', ['id' => $courseid], '*', MUST_EXIST);
    $cm = get_coursemodule_from_instance('uckkarchive', $archive->id, $course->id, false, MUST_EXIST);
} else {
    throw new moodle_exception('missingparam', 'error', '', 'id');
}

$context = context_module::instance($cm->id);

require_login($course, false, $cm);
require_capability('mod/uckkarchive:view', $context);
require_capability('mod/uckkarchive:additem', $context);

$viewurl = new moodle_url('/mod/uckkarchive/view.php', ['id' => $cm->id]);
$mediaurl = new moodle_url('/mod/uckkarchive/media.php', ['id' => $cm->id]);

$pageparams = [
    'id' => $cm->id,
    'origincomponent' => $origincomponent,
    'originarea' => $originarea,
    'originid' => $originid,
    'origintype' => $origintype,
];

if ($returnurl !== '') {
    $pageparams['returnurl'] = $returnurl;
}

$pageurl = new moodle_url('/mod/uckkarchive/add.php', $pageparams);
$return = $returnurl !== '' ? new moodle_url($returnurl) : $viewurl;

$PAGE->set_url($pageurl);
$PAGE->set_course($course);
$PAGE->set_cm($cm);
$PAGE->set_context($context);
$PAGE->set_title(format_string($archive->name));
$PAGE->set_heading(format_string($course->fullname));

$completion = new completion_info($course);
$completion->set_module_viewed($cm);

$allowedtypes = [
    'proof',
    'decision',
    'course_work',
    'challenge_result',
    'assembly_minutes',
    'integrity_case_summary',
    'kristal',
    'reflection',
    'portfolio_item',
    'version_record',
    'media_reference',
    'external_work_reference',
    'content_advisory_reference',
];

$allowedstatuses = [
    'draft',
    'submitted',
    'under_review',
];

$allowedvisibilities = [
    'private',
    'course',
    'cohort',
    'program',
    'institution',
    'institutional',
    'public',
    'restricted',
    'restricted_integrity',
    'restricted_cultural',
];

$allowedprovenance = [
    'human',
    'ai_assisted',
    'imported',
    'system',
    'archive',
    'assembly',
    'challenge',
    'integrity',
    'media',
    'external_work',
];

$allowedvalidation = [
    'unverified',
    'human_reviewed',
];

$defaultvisibility = get_config('uckkarchive', 'defaultvisibility') ?: 'course';
if (!in_array($defaultvisibility, $allowedvisibilities, true)) {
    $defaultvisibility = 'course';
}

$draftitemid = file_get_submitted_draft_itemid('itemfiles');
file_prepare_draft_area(
    $draftitemid,
    $context->id,
    'mod_uckkarchive',
    'item_files',
    0,
    [
        'subdirs' => 0,
        'maxbytes' => get_max_upload_file_size(),
        'maxfiles' => 20,
        'accepted_types' => '*',
    ]
);

$draftproofid = file_get_submitted_draft_itemid('proof_files');
file_prepare_draft_area(
    $draftproofid,
    $context->id,
    'mod_uckkarchive',
    'proof_files',
    0,
    [
        'subdirs' => 0,
        'maxbytes' => get_max_upload_file_size(),
        'maxfiles' => 20,
        'accepted_types' => '*',
    ]
);

$form = new archive_item_form($pageurl, [
    'course' => $course,
    'cm' => $cm,
    'archive' => $archive,
    'context' => $context,
    'allowedtypes' => $allowedtypes,
    'allowedstatuses' => $allowedstatuses,
    'allowedvisibilities' => $allowedvisibilities,
    'allowedprovenance' => $allowedprovenance,
    'allowedvalidation' => $allowedvalidation,
    'draftitemid' => $draftitemid,
    'draftproofid' => $draftproofid,
    'origincomponent' => $origincomponent,
    'originarea' => $originarea,
    'originid' => $originid,
    'origintype' => $origintype,
]);

if ($form->is_cancelled()) {
    redirect($return);
}

$defaultdata = new stdClass();
$defaultdata->id = $cm->id;
$defaultdata->archiveid = $archive->id;
$defaultdata->courseid = $course->id;
$defaultdata->cmid = $cm->id;
$defaultdata->contextid = $context->id;
$defaultdata->itemtype = $origintype !== '' && in_array($origintype, $allowedtypes, true) ? $origintype : 'proof';
$defaultdata->status = 'draft';
$defaultdata->visibility = $defaultvisibility;
$defaultdata->provenance = $origincomponent !== '' ? 'imported' : 'human';
$defaultdata->validationstate = 'unverified';
$defaultdata->origincomponent = $origincomponent;
$defaultdata->originarea = $originarea;
$defaultdata->originid = $originid;
$defaultdata->itemfiles = $draftitemid;
$defaultdata->proof_files = $draftproofid;

$editoroptions = [
    'context' => $context,
    'maxfiles' => EDITOR_UNLIMITED_FILES,
    'maxbytes' => get_max_upload_file_size(),
    'trusttext' => false,
    'noclean' => false,
    'subdirs' => false,
];

$summaryeditoroptions = [
    'context' => $context,
    'maxfiles' => 0,
    'maxbytes' => 0,
    'trusttext' => false,
    'noclean' => false,
    'subdirs' => false,
];

$defaultdata = file_prepare_standard_editor(
    $defaultdata,
    'content',
    $editoroptions,
    $context,
    'mod_uckkarchive',
    'item_content',
    0
);

$defaultdata = file_prepare_standard_editor(
    $defaultdata,
    'publicsummary',
    $summaryeditoroptions,
    $context,
    'mod_uckkarchive',
    'item_publicsummary',
    0
);

$form->set_data($defaultdata);

if ($data = $form->get_data()) {
    require_sesskey();

    if (!in_array($data->itemtype, $allowedtypes, true)) {
        throw new moodle_exception('invalidarchiveitemtype', 'uckkarchive');
    }

    if (!in_array($data->status, $allowedstatuses, true)) {
        throw new moodle_exception('invalidarchivestatus', 'uckkarchive');
    }

    if (!in_array($data->visibility, $allowedvisibilities, true)) {
        throw new moodle_exception('invalidarchivevisibility', 'uckkarchive');
    }

    if (!in_array($data->provenance, $allowedprovenance, true)) {
        throw new moodle_exception('invalidarchiveprovenance', 'uckkarchive');
    }

    if (!in_array($data->validationstate, $allowedvalidation, true)) {
        throw new moodle_exception('invalidarchivevalidationstate', 'uckkarchive');
    }

    $metadata = [
        'origin' => [
            'component' => clean_param((string)($data->origincomponent ?? ''), PARAM_COMPONENT),
            'area' => clean_param((string)($data->originarea ?? ''), PARAM_ALPHANUMEXT),
            'id' => (int)($data->originid ?? 0),
            'type' => clean_param((string)$origintype, PARAM_ALPHANUMEXT),
        ],
        'created_from' => 'mod_uckkarchive/add.php',
        'ai_policy' => [
            'non_sovereign' => true,
            'requires_human_validation' => true,
        ],
        'media_advisory_ready' => true,
    ];

    if (!empty($data->metadatajson)) {
        $decoded = json_decode((string)$data->metadatajson, true);

        if (json_last_error() !== JSON_ERROR_NONE || !is_array($decoded)) {
            throw new moodle_exception('invalidmetadatajson', 'uckkarchive');
        }

        $metadata = array_replace_recursive($metadata, $decoded);
    }

    $now = time();

    $record = new stdClass();
    $record->archiveid = (int)$archive->id;
    $record->courseid = (int)$course->id;
    $record->cmid = (int)$cm->id;
    $record->contextid = (int)$context->id;
    $record->userid = (int)$USER->id;
    $record->itemtype = $data->itemtype;
    $record->title = trim((string)$data->title);
    $record->content = '';
    $record->contentformat = FORMAT_HTML;
    $record->publicsummary = '';
    $record->publicsummaryformat = FORMAT_HTML;
    $record->sourceurl = trim((string)($data->sourceurl ?? ''));
    $record->sourcetitle = trim((string)($data->sourcetitle ?? ''));
    $record->sourceauthor = trim((string)($data->sourceauthor ?? ''));
    $record->sourcedate = (int)($data->sourcedate ?? 0);
    $record->origincomponent = clean_param((string)($data->origincomponent ?? ''), PARAM_COMPONENT);
    $record->originarea = clean_param((string)($data->originarea ?? ''), PARAM_ALPHANUMEXT);
    $record->originid = (int)($data->originid ?? 0);
    $record->status = $data->status;
    $record->visibility = $data->visibility;
    $record->validationstate = $data->validationstate;
    $record->provenance = $data->provenance;
    $record->provenancehash = '';
    $record->versionno = 1;
    $record->createdby = (int)$USER->id;
    $record->modifiedby = (int)$USER->id;
    $record->timecreated = $now;
    $record->timemodified = $now;
    $record->metadata = json_encode($metadata, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);

    if ($record->metadata === false) {
        throw new moodle_exception('invalidmetadatajson', 'uckkarchive');
    }

    $transaction = $DB->start_delegated_transaction();

    $itemid = (int)$DB->insert_record('uckkarchive_item', $record);

    $data = file_postupdate_standard_editor(
        $data,
        'content',
        $editoroptions,
        $context,
        'mod_uckkarchive',
        'item_content',
        $itemid
    );

    $data = file_postupdate_standard_editor(
        $data,
        'publicsummary',
        $summaryeditoroptions,
        $context,
        'mod_uckkarchive',
        'item_publicsummary',
        $itemid
    );

    $updaterecord = new stdClass();
    $updaterecord->id = $itemid;
    $updaterecord->content = $data->content;
    $updaterecord->contentformat = (int)$data->contentformat;
    $updaterecord->publicsummary = $data->publicsummary;
    $updaterecord->publicsummaryformat = (int)$data->publicsummaryformat;
    $updaterecord->timemodified = time();

    if (!empty($updaterecord->content)) {
        $updaterecord->provenancehash = hash(
            'sha256',
            $updaterecord->content . '|' . $record->sourceurl . '|' . $record->sourceauthor . '|' . $record->provenance
        );
    }

    $DB->update_record('uckkarchive_item', $updaterecord);

    file_save_draft_area_files(
        (int)$data->itemfiles,
        $context->id,
        'mod_uckkarchive',
        'item_files',
        $itemid,
        [
            'subdirs' => 0,
            'maxbytes' => get_max_upload_file_size(),
            'maxfiles' => 20,
            'accepted_types' => '*',
        ]
    );

    file_save_draft_area_files(
        (int)$data->proof_files,
        $context->id,
        'mod_uckkarchive',
        'proof_files',
        $itemid,
        [
            'subdirs' => 0,
            'maxbytes' => get_max_upload_file_size(),
            'maxfiles' => 20,
            'accepted_types' => '*',
        ]
    );

    $revision = new stdClass();
    $revision->archiveid = (int)$archive->id;
    $revision->itemid = $itemid;
    $revision->courseid = (int)$course->id;
    $revision->cmid = (int)$cm->id;
    $revision->contextid = (int)$context->id;
    $revision->userid = (int)$USER->id;
    $revision->revisiontype = 'created';
    $revision->previousstatus = null;
    $revision->newstatus = $record->status;
    $revision->previousvisibility = null;
    $revision->newvisibility = $record->visibility;
    $revision->reason = trim((string)($data->reason ?? get_string('archiveitemcreated', 'uckkarchive')));
    $revision->status = 'active';
    $revision->visibility = $record->visibility;
    $revision->provenance = $record->provenance;
    $revision->versionno = 1;
    $revision->createdby = (int)$USER->id;
    $revision->modifiedby = (int)$USER->id;
    $revision->timecreated = time();
    $revision->timemodified = time();
    $revision->metadata = json_encode([
        'created_item_id' => $itemid,
        'origincomponent' => $record->origincomponent,
        'originarea' => $record->originarea,
        'originid' => $record->originid,
        'item_files_filearea' => 'item_files',
        'proof_files_filearea' => 'proof_files',
        'content_filearea' => 'item_content',
        'publicsummary_filearea' => 'item_publicsummary',
    ], JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);

    if ($revision->metadata === false) {
        $revision->metadata = '{}';
    }

    if ($DB->get_manager()->table_exists('uckkarchive_rev')) {
        $DB->insert_record('uckkarchive_rev', $revision);
    }

    $createditem = $DB->get_record('uckkarchive_item', ['id' => $itemid], '*', MUST_EXIST);

    $transaction->allow_commit();

    if (class_exists(archive_item_created::class)) {
        $event = archive_item_created::create([
            'objectid' => $itemid,
            'context' => $context,
            'other' => [
                'archiveid' => (int)$archive->id,
                'courseid' => (int)$course->id,
                'cmid' => (int)$cm->id,
                'itemtype' => $record->itemtype,
                'status' => $record->status,
                'visibility' => $record->visibility,
                'validationstate' => $record->validationstate,
                'provenance' => $record->provenance,
                'origincomponent' => $record->origincomponent,
                'originarea' => $record->originarea,
                'originid' => $record->originid,
            ],
        ]);

        $event->add_record_snapshot('course', $course);
        $event->add_record_snapshot('course_modules', $cm);
        $event->add_record_snapshot('uckkarchive', $archive);
        $event->add_record_snapshot('uckkarchive_item', $createditem);
        $event->trigger();
    }

    $itemurl = new moodle_url('/mod/uckkarchive/item.php', [
        'id' => $cm->id,
        'itemid' => $itemid,
    ]);

    redirect($itemurl, get_string('archiveitemcreated', 'uckkarchive'), null, notification::NOTIFY_SUCCESS);
}

echo $OUTPUT->header();

echo $OUTPUT->heading(get_string('addarchiveitem', 'uckkarchive'));

echo html_writer::div(
    get_string('archiveaddnotice', 'uckkarchive'),
    'alert alert-info uckkarchive-add__notice',
    ['role' => 'status']
);

if ($origincomponent !== '' || $originid > 0) {
    echo html_writer::start_div('uckkarchive-add__origin card mb-3');
    echo html_writer::start_div('card-body');

    echo html_writer::tag('h3', get_string('originrecord', 'uckkarchive'), [
        'class' => 'card-title',
    ]);

    echo html_writer::start_tag('dl');

    if ($origincomponent !== '') {
        echo html_writer::tag('dt', get_string('origincomponent', 'uckkarchive'));
        echo html_writer::tag('dd', s($origincomponent));
    }

    if ($originarea !== '') {
        echo html_writer::tag('dt', get_string('originarea', 'uckkarchive'));
        echo html_writer::tag('dd', s($originarea));
    }

    if ($originid > 0) {
        echo html_writer::tag('dt', get_string('originid', 'uckkarchive'));
        echo html_writer::tag('dd', (string)$originid);
    }

    if ($origintype !== '') {
        echo html_writer::tag('dt', get_string('origintype', 'uckkarchive'));
        echo html_writer::tag('dd', s($origintype));
    }

    echo html_writer::end_tag('dl');

    echo html_writer::end_div();
    echo html_writer::end_div();
}

echo html_writer::start_div('uckkarchive-add__actions mb-3');

echo html_writer::link($viewurl, get_string('backtoarchive', 'uckkarchive'), [
    'class' => 'btn btn-secondary mr-2',
]);

if (has_capability('mod/uckkarchive:viewmedia', $context) ||
        has_capability('mod/uckkarchive:addmedia', $context) ||
        has_capability('mod/uckkarchive:managemedia', $context)) {
    echo html_writer::link($mediaurl, get_string('medialibrary', 'uckkarchive'), [
        'class' => 'btn btn-outline-secondary',
    ]);
}

echo html_writer::end_div();

$form->display();

echo html_writer::link($return, get_string('cancel'), [
    'class' => 'btn btn-secondary mt-3',
]);

echo $OUTPUT->footer();