<?php
// This file is part of Moodle - https://moodle.org/
//
// Moodle is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// any later version.

/**
 * Library callbacks for the UCKK Archive activity module.
 *
 * @package    mod_uckkarchive
 * @copyright  2026 Univers-Cité King Klown
 * @license    https://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later
 */

defined('MOODLE_INTERNAL') || die();

require_once(__DIR__ . '/locallib.php');

/**
 * Component name.
 */
defined('UCKKARCHIVE_COMPONENT') || define('UCKKARCHIVE_COMPONENT', 'mod_uckkarchive');
/**
 * Main instance table.
 */
defined('UCKKARCHIVE_TABLE') || define('UCKKARCHIVE_TABLE', 'uckkarchive');
/**
 * Common statuses.
 */
defined('UCKKARCHIVE_STATUS_DRAFT') || define('UCKKARCHIVE_STATUS_DRAFT', 'draft');
defined('UCKKARCHIVE_STATUS_ACTIVE') || define('UCKKARCHIVE_STATUS_ACTIVE', 'active');
defined('UCKKARCHIVE_STATUS_PENDING_REVIEW') || define('UCKKARCHIVE_STATUS_PENDING_REVIEW', 'pending_review');
defined('UCKKARCHIVE_STATUS_VALIDATED') || define('UCKKARCHIVE_STATUS_VALIDATED', 'validated');
defined('UCKKARCHIVE_STATUS_REJECTED') || define('UCKKARCHIVE_STATUS_REJECTED', 'rejected');
defined('UCKKARCHIVE_STATUS_CORRECTION_REQUIRED') || define('UCKKARCHIVE_STATUS_CORRECTION_REQUIRED', 'correction_required');
defined('UCKKARCHIVE_STATUS_CONTESTED') || define('UCKKARCHIVE_STATUS_CONTESTED', 'contested');
defined('UCKKARCHIVE_STATUS_INVALIDATED') || define('UCKKARCHIVE_STATUS_INVALIDATED', 'invalidated');
defined('UCKKARCHIVE_STATUS_CLOSED') || define('UCKKARCHIVE_STATUS_CLOSED', 'closed');
defined('UCKKARCHIVE_STATUS_ARCHIVED') || define('UCKKARCHIVE_STATUS_ARCHIVED', 'archived');
defined('UCKKARCHIVE_STATUS_DELETED_SOFT') || define('UCKKARCHIVE_STATUS_DELETED_SOFT', 'deleted_soft');
defined('UCKKARCHIVE_STATUS_RESTRICTED') || define('UCKKARCHIVE_STATUS_RESTRICTED', 'restricted');
/**
 * Common visibilities.
 */
defined('UCKKARCHIVE_VISIBILITY_PRIVATE') || define('UCKKARCHIVE_VISIBILITY_PRIVATE', 'private');
defined('UCKKARCHIVE_VISIBILITY_USER') || define('UCKKARCHIVE_VISIBILITY_USER', 'user');
defined('UCKKARCHIVE_VISIBILITY_GROUP') || define('UCKKARCHIVE_VISIBILITY_GROUP', 'group');
defined('UCKKARCHIVE_VISIBILITY_COURSE') || define('UCKKARCHIVE_VISIBILITY_COURSE', 'course');
defined('UCKKARCHIVE_VISIBILITY_COHORT') || define('UCKKARCHIVE_VISIBILITY_COHORT', 'cohort');
defined('UCKKARCHIVE_VISIBILITY_PROGRAM') || define('UCKKARCHIVE_VISIBILITY_PROGRAM', 'program');
defined('UCKKARCHIVE_VISIBILITY_INSTITUTION') || define('UCKKARCHIVE_VISIBILITY_INSTITUTION', 'institution');
defined('UCKKARCHIVE_VISIBILITY_PUBLIC') || define('UCKKARCHIVE_VISIBILITY_PUBLIC', 'public');
defined('UCKKARCHIVE_VISIBILITY_RESTRICTED') || define('UCKKARCHIVE_VISIBILITY_RESTRICTED', 'restricted');
defined('UCKKARCHIVE_VISIBILITY_RESTRICTED_INTEGRITY') || define('UCKKARCHIVE_VISIBILITY_RESTRICTED_INTEGRITY', 'restricted_integrity');
defined('UCKKARCHIVE_VISIBILITY_RESTRICTED_CULTURAL') || define('UCKKARCHIVE_VISIBILITY_RESTRICTED_CULTURAL', 'restricted_cultural');
defined('UCKKARCHIVE_VISIBILITY_HIDDEN') || define('UCKKARCHIVE_VISIBILITY_HIDDEN', 'hidden');
defined('UCKKARCHIVE_VISIBILITY_ARCHIVED') || define('UCKKARCHIVE_VISIBILITY_ARCHIVED', 'archived');
/**
 * Required archive file areas.
 */
defined('UCKKARCHIVE_FILEAREA_PROOF_FILES') || define('UCKKARCHIVE_FILEAREA_PROOF_FILES', 'proof_files');
defined('UCKKARCHIVE_FILEAREA_DECISION_ATTACHMENTS') || define('UCKKARCHIVE_FILEAREA_DECISION_ATTACHMENTS', 'decision_attachments');
defined('UCKKARCHIVE_FILEAREA_MINUTES_FILES') || define('UCKKARCHIVE_FILEAREA_MINUTES_FILES', 'minutes_files');
defined('UCKKARCHIVE_FILEAREA_KRISTAL_FILES') || define('UCKKARCHIVE_FILEAREA_KRISTAL_FILES', 'kristal_files');
defined('UCKKARCHIVE_FILEAREA_PORTFOLIO_FILES') || define('UCKKARCHIVE_FILEAREA_PORTFOLIO_FILES', 'portfolio_files');
defined('UCKKARCHIVE_FILEAREA_INTEGRITY_EXPORTS') || define('UCKKARCHIVE_FILEAREA_INTEGRITY_EXPORTS', 'integrity_exports');
defined('UCKKARCHIVE_FILEAREA_MEDIA_ORIGINAL') || define('UCKKARCHIVE_FILEAREA_MEDIA_ORIGINAL', 'media_original');
defined('UCKKARCHIVE_FILEAREA_MEDIA_PREVIEW') || define('UCKKARCHIVE_FILEAREA_MEDIA_PREVIEW', 'media_preview');
defined('UCKKARCHIVE_FILEAREA_MEDIA_THUMBNAIL') || define('UCKKARCHIVE_FILEAREA_MEDIA_THUMBNAIL', 'media_thumbnail');
defined('UCKKARCHIVE_FILEAREA_MEDIA_DERIVATIVE') || define('UCKKARCHIVE_FILEAREA_MEDIA_DERIVATIVE', 'media_derivative');
defined('UCKKARCHIVE_FILEAREA_MEDIA_CAPTION') || define('UCKKARCHIVE_FILEAREA_MEDIA_CAPTION', 'media_caption');
defined('UCKKARCHIVE_FILEAREA_MEDIA_TRANSCRIPT') || define('UCKKARCHIVE_FILEAREA_MEDIA_TRANSCRIPT', 'media_transcript');
defined('UCKKARCHIVE_FILEAREA_MEDIA_ATTACHMENT') || define('UCKKARCHIVE_FILEAREA_MEDIA_ATTACHMENT', 'media_attachment');
defined('UCKKARCHIVE_FILEAREA_CONTENT_REVIEW_FILES') || define('UCKKARCHIVE_FILEAREA_CONTENT_REVIEW_FILES', 'content_review_files');
defined('UCKKARCHIVE_FILEAREA_EXTERNAL_WORK_REFERENCE_FILES') || define('UCKKARCHIVE_FILEAREA_EXTERNAL_WORK_REFERENCE_FILES', 'external_work_reference_files');
defined('UCKKARCHIVE_FILEAREA_CULTURAL_PROTOCOL_FILES') || define('UCKKARCHIVE_FILEAREA_CULTURAL_PROTOCOL_FILES', 'cultural_protocol_files');
defined('UCKKARCHIVE_FILEAREA_EXPORT_MANIFEST') || define('UCKKARCHIVE_FILEAREA_EXPORT_MANIFEST', 'export_manifest');
defined('UCKKARCHIVE_FILEAREA_EXPORT_PACKAGE') || define('UCKKARCHIVE_FILEAREA_EXPORT_PACKAGE', 'export_package');
/**
 * Return supported Moodle features.
 *
 * @param string $feature Feature constant.
 * @return mixed
 */
function uckkarchive_supports($feature) {
    switch ($feature) {
        case FEATURE_MOD_INTRO:
        case FEATURE_SHOW_DESCRIPTION:
        case FEATURE_COMPLETION_TRACKS_VIEWS:
        case FEATURE_COMPLETION_HAS_RULES:
        case FEATURE_BACKUP_MOODLE2:
        case FEATURE_GROUPS:
        case FEATURE_GROUPINGS:
            return true;

        case FEATURE_GRADE_HAS_GRADE:
        case FEATURE_GRADE_OUTCOMES:
        case FEATURE_RATE:
        case FEATURE_PLAGIARISM:
            return false;

        case FEATURE_MOD_PURPOSE:
            return MOD_PURPOSE_CONTENT;

        default:
            return null;
    }
}

/**
 * Add a new UCKK archive instance.
 *
 * @param stdClass $archive Submitted module data.
 * @param mod_uckkarchive_mod_form|null $mform Module form.
 * @return int New instance id.
 */
function uckkarchive_add_instance(stdClass $archive, $mform = null): int {
    global $DB, $USER;

    $now = time();

    $archive->timecreated = $now;
    $archive->timemodified = $now;
    $archive->createdby = (int)$USER->id;
    $archive->modifiedby = (int)$USER->id;

    $record = uckkarchive_prepare_instance_record($archive, true);
    $record->id = $DB->insert_record(UCKKARCHIVE_TABLE, $record);

    $archive->id = (int)$record->id;
    $archive->completionrequireitem = (int)$record->completionrequireitem;
    $archive->completionrequirevalidation = (int)$record->completionrequirevalidation;

    uckkarchive_update_calendar_events($archive);
    uckkarchive_update_completion_metadata($archive);

    return (int)$archive->id;
}

/**
 * Update an existing UCKK archive instance.
 *
 * @param stdClass $archive Submitted module data.
 * @param mod_uckkarchive_mod_form|null $mform Module form.
 * @return bool
 */
function uckkarchive_update_instance(stdClass $archive, $mform = null): bool {
    global $DB, $USER;

    $archive->id = (int)$archive->instance;
    $archive->timemodified = time();
    $archive->modifiedby = (int)$USER->id;

    $record = uckkarchive_prepare_instance_record($archive, false);
    $result = $DB->update_record(UCKKARCHIVE_TABLE, $record);

    $archive->completionrequireitem = (int)$record->completionrequireitem;
    $archive->completionrequirevalidation = (int)$record->completionrequirevalidation;

    uckkarchive_update_calendar_events($archive);
    uckkarchive_update_completion_metadata($archive);

    return $result;
}

/**
 * Delete an archive instance and owned archive records.
 *
 * This removes records owned by this activity instance. Cross-plugin source
 * records remain owned by their original components.
 *
 * @param int $id Archive instance id.
 * @return bool
 */
function uckkarchive_delete_instance($id): bool {
    global $DB;

    $id = (int)$id;

    if (!$archive = $DB->get_record(UCKKARCHIVE_TABLE, ['id' => $id])) {
        return false;
    }

    $cm = get_coursemodule_from_instance('uckkarchive', $id, $archive->course ?? 0, false, IGNORE_MISSING);

    if ($cm) {
        $context = context_module::instance($cm->id, IGNORE_MISSING);

        if ($context) {
            $fs = get_file_storage();
            $fs->delete_area_files($context->id, UCKKARCHIVE_COMPONENT);
        }
    }

    foreach ([
        'uckkarchive_content_review',
        'uckkarchive_content_marker',
        'uckkarchive_media_collection_item',
        'uckkarchive_media_collection',
        'uckkarchive_media_relation',
        'uckkarchive_media_tag',
        'uckkarchive_media_source',
        'uckkarchive_media_version',
        'uckkarchive_media',
        'uckkarchive_external_work',
        'uckkarchive_export',
        'uckkarchive_rev',
        'uckkarchive_prov',
        'uckkarchive_proof',
        'uckkarchive_kristal',
        'uckkarchive_item',
    ] as $table) {
        uckkarchive_delete_records_by_archiveid($table, $id);
    }

    $DB->delete_records('event', [
        'modulename' => 'uckkarchive',
        'instance' => $id,
    ]);

    $DB->delete_records(UCKKARCHIVE_TABLE, ['id' => $id]);

    return true;
}

/**
 * Return a brief user activity outline for participation reports.
 *
 * @param stdClass $course Course record.
 * @param stdClass $user User record.
 * @param cm_info|stdClass $mod Course module.
 * @param stdClass $archive Archive instance.
 * @return stdClass|null
 */
function uckkarchive_user_outline($course, $user, $mod, $archive): ?stdClass {
    global $DB;

    $archiveid = (int)$archive->id;
    $userid = (int)$user->id;

    $itemcount = uckkarchive_count_user_records('uckkarchive_item', $archiveid, $userid);
    $proofcount = uckkarchive_count_user_records('uckkarchive_proof', $archiveid, $userid);
    $mediacount = uckkarchive_count_user_records('uckkarchive_media', $archiveid, $userid, ['userid', 'ownerid', 'createdby']);

    $lastactivity = uckkarchive_get_user_last_activity_time($archiveid, $userid);

    if ($itemcount === 0 && $proofcount === 0 && $mediacount === 0 && $lastactivity === 0) {
        return null;
    }

    $result = new stdClass();
    $result->info = get_string('useroutline', 'uckkarchive', [
        'items' => $itemcount,
        'proofs' => $proofcount,
        'media' => $mediacount,
    ]);
    $result->time = $lastactivity;

    return $result;
}

/**
 * Print detailed user activity for participation reports.
 *
 * @param stdClass $course Course record.
 * @param stdClass $user User record.
 * @param cm_info|stdClass $mod Course module.
 * @param stdClass $archive Archive instance.
 */
function uckkarchive_user_complete($course, $user, $mod, $archive): void {
    global $DB, $OUTPUT;

    $archiveid = (int)$archive->id;
    $userid = (int)$user->id;

    $items = $DB->get_records_select(
        'uckkarchive_item',
        'archiveid = :archiveid AND (userid = :userid OR createdby = :createdby)',
        [
            'archiveid' => $archiveid,
            'userid' => $userid,
            'createdby' => $userid,
        ],
        'timemodified DESC',
        'id, title, status, visibility, timemodified',
        0,
        10
    );

    $media = [];
    if (uckkarchive_lib_table_exists('uckkarchive_media')) {
        $media = $DB->get_records_select(
            'uckkarchive_media',
            'archiveid = :archiveid AND (userid = :userid OR ownerid = :ownerid OR createdby = :createdby)',
            [
                'archiveid' => $archiveid,
                'userid' => $userid,
                'ownerid' => $userid,
                'createdby' => $userid,
            ],
            'timemodified DESC',
            'id, title, status, visibility, timemodified',
            0,
            10
        );
    }

    if (!$items && !$media) {
        echo $OUTPUT->notification(get_string('nouserarchiveitems', 'uckkarchive'), 'info');
        return;
    }

    echo html_writer::start_tag('ul', ['class' => 'uckkarchive-user-complete']);

    foreach ($items as $item) {
        $label = format_string($item->title ?? get_string('archiveitem', 'uckkarchive'));

        if (!empty($item->status)) {
            $label .= ' — ' . s($item->status);
        }

        if (!empty($item->timemodified)) {
            $label .= ' — ' . userdate((int)$item->timemodified);
        }

        echo html_writer::tag('li', $label);
    }

    foreach ($media as $mediaitem) {
        $label = format_string($mediaitem->title ?? get_string('media', 'uckkarchive'));

        if (!empty($mediaitem->status)) {
            $label .= ' — ' . s($mediaitem->status);
        }

        if (!empty($mediaitem->timemodified)) {
            $label .= ' — ' . userdate((int)$mediaitem->timemodified);
        }

        echo html_writer::tag('li', $label);
    }

    echo html_writer::end_tag('ul');
}

/**
 * Return cached course-module information.
 *
 * @param stdClass $coursemodule Course module record.
 * @return cached_cm_info|null
 */
function uckkarchive_get_coursemodule_info(stdClass $coursemodule): ?cached_cm_info {
    global $DB;

    $archive = $DB->get_record(
        UCKKARCHIVE_TABLE,
        ['id' => $coursemodule->instance],
        'id, name, intro, introformat, status, visibility, defaultvisibility, archivepolicy, timemodified',
        IGNORE_MISSING
    );

    if (!$archive) {
        return null;
    }

    $info = new cached_cm_info();
    $info->name = format_string($archive->name);

    if (!empty($archive->intro)) {
        $info->content = format_module_intro('uckkarchive', $archive, $coursemodule->id, false);
    }

    $customdata = [
        'status' => $archive->status ?? UCKKARCHIVE_STATUS_ACTIVE,
        'visibility' => $archive->visibility ?? UCKKARCHIVE_VISIBILITY_COURSE,
        'defaultvisibility' => $archive->defaultvisibility ?? UCKKARCHIVE_VISIBILITY_COURSE,
        'archivepolicy' => $archive->archivepolicy ?? 'validated',
        'timemodified' => (int)($archive->timemodified ?? 0),
    ];

    $info->customdata = $customdata;

    return $info;
}

/**
 * Serve files from the UCKK archive file areas.
 *
 * @param stdClass $course Course record.
 * @param cm_info|stdClass $cm Course module.
 * @param context $context Module context.
 * @param string $filearea File area.
 * @param array $args Path arguments.
 * @param bool $forcedownload Whether to force download.
 * @param array $options Additional send options.
 * @return bool
 */
function uckkarchive_pluginfile($course, $cm, $context, $filearea, $args, $forcedownload, array $options = []): bool {
    if ($context->contextlevel !== CONTEXT_MODULE) {
        return false;
    }

    require_login($course, false, $cm);

    if ($filearea === 'intro') {
        require_capability('mod/uckkarchive:view', $context);
        $itemid = (int)array_shift($args);

        if ($itemid !== 0) {
            return false;
        }
    } else {
        if (!in_array($filearea, uckkarchive_get_fileareas(), true)) {
            return false;
        }

        if (empty($args)) {
            return false;
        }

        $itemid = (int)array_shift($args);

        if ($itemid <= 0) {
            return false;
        }

        if (!uckkarchive_can_view_filearea_item($cm, $context, $filearea, $itemid)) {
            return false;
        }

        if (!uckkarchive_can_download_filearea($context, $filearea)) {
            return false;
        }
    }

    if (empty($args)) {
        return false;
    }

    $filename = array_pop($args);
    $filepath = '/' . implode('/', $args) . '/';

    if ($filepath === '//') {
        $filepath = '/';
    }

    $fs = get_file_storage();
    $file = $fs->get_file(
        $context->id,
        UCKKARCHIVE_COMPONENT,
        $filearea,
        (int)$itemid,
        $filepath,
        $filename
    );

    if (!$file || $file->is_directory()) {
        return false;
    }

    send_stored_file($file, 0, 0, $forcedownload, $options);

    return true;
}

/**
 * Return custom completion state.
 *
 * @param stdClass $course Course record.
 * @param cm_info|stdClass $cm Course module.
 * @param int $userid User id.
 * @param int $type Completion aggregation type.
 * @return bool
 */
function uckkarchive_get_completion_state($course, $cm, $userid, $type): bool {
    global $DB;

    $archive = $DB->get_record(
        UCKKARCHIVE_TABLE,
        ['id' => $cm->instance],
        'id, completionrequireitem, completionrequirevalidation',
        IGNORE_MISSING
    );

    if (!$archive) {
        return (bool)$type;
    }

    $conditions = [];

    if (!empty($archive->completionrequireitem)) {
        $conditions[] = $DB->record_exists_select(
            'uckkarchive_item',
            'archiveid = :archiveid AND (userid = :userid OR createdby = :createdby)',
            [
                'archiveid' => $archive->id,
                'userid' => $userid,
                'createdby' => $userid,
            ]
        );
    }

    if (!empty($archive->completionrequirevalidation)) {
        $conditions[] = $DB->record_exists_select(
            'uckkarchive_item',
            'archiveid = :archiveid
                 AND status = :status
                 AND (userid = :userid OR createdby = :createdby)',
            [
                'archiveid' => $archive->id,
                'status' => UCKKARCHIVE_STATUS_VALIDATED,
                'userid' => $userid,
                'createdby' => $userid,
            ]
        );
    }

    if (empty($conditions)) {
        return (bool)$type;
    }

    if ($type === COMPLETION_AND) {
        return !in_array(false, $conditions, true);
    }

    return in_array(true, $conditions, true);
}

/**
 * Reset course user data.
 *
 * Archive activities are institutional memory by default. User-owned records
 * are not removed during course reset unless future reset settings explicitly
 * request destructive action.
 *
 * @param stdClass $data Reset data.
 * @return array<int, array<string, mixed>>
 */
function uckkarchive_reset_userdata(stdClass $data): array {
    return [
        [
            'component' => get_string('modulenameplural', 'uckkarchive'),
            'item' => get_string('resetarchivespreserved', 'uckkarchive'),
            'error' => false,
        ],
    ];
}

/**
 * Refresh calendar events for all or one course.
 *
 * @param int $courseid Course id or 0 for all courses.
 * @return bool
 */
function uckkarchive_refresh_events($courseid = 0): bool {
    global $DB;

    $params = [];
    $coursesql = '';

    if (!empty($courseid)) {
        $coursesql = 'WHERE course = :courseid';
        $params['courseid'] = $courseid;
    }

    $archives = $DB->get_records_sql(
        "SELECT *
           FROM {uckkarchive}
           {$coursesql}",
        $params
    );

    foreach ($archives as $archive) {
        uckkarchive_update_calendar_events($archive);
    }

    return true;
}

/**
 * Extend module navigation.
 *
 * @param navigation_node $navref Navigation node.
 * @param stdClass $course Course record.
 * @param stdClass $module Course module record.
 * @param cm_info $cm Course module info.
 */
function uckkarchive_extend_navigation(navigation_node $navref, stdClass $course, stdClass $module, cm_info $cm): void {
    $context = context_module::instance($cm->id);

    if (has_capability('mod/uckkarchive:additem', $context)) {
        $navref->add(
            get_string('addarchiveitem', 'uckkarchive'),
            new moodle_url('/mod/uckkarchive/add.php', ['id' => $cm->id]),
            navigation_node::TYPE_SETTING,
            null,
            'uckkarchive_add_item',
            new pix_icon('t/add', '')
        );
    }

    if (uckkarchive_lib_has_capability('mod/uckkarchive:viewmedia', $context)) {
        $navref->add(
            get_string('medialibrary', 'uckkarchive'),
            new moodle_url('/mod/uckkarchive/media.php', ['id' => $cm->id]),
            navigation_node::TYPE_SETTING,
            null,
            'uckkarchive_media_library',
            new pix_icon('i/media', '')
        );
    }

    if (has_capability('mod/uckkarchive:validateitem', $context)) {
        $navref->add(
            get_string('validatearchiveitems', 'uckkarchive'),
            new moodle_url('/mod/uckkarchive/validate.php', ['id' => $cm->id]),
            navigation_node::TYPE_SETTING,
            null,
            'uckkarchive_validate_items',
            new pix_icon('i/checked', '')
        );
    }

    if (uckkarchive_lib_has_capability('mod/uckkarchive:export', $context)) {
        $navref->add(
            get_string('exportarchive', 'uckkarchive'),
            new moodle_url('/mod/uckkarchive/export.php', ['id' => $cm->id]),
            navigation_node::TYPE_SETTING,
            null,
            'uckkarchive_export',
            new pix_icon('t/download', '')
        );
    }
}

/**
 * Return the latest user activity timestamp for one archive.
 *
 * @param int $archiveid Archive instance id.
 * @param int $userid User id.
 * @return int
 */
function uckkarchive_get_user_last_activity_time(int $archiveid, int $userid): int {
    global $DB;

    $times = [];

    foreach ([
        'uckkarchive_item' => ['userid', 'createdby', 'modifiedby'],
        'uckkarchive_kristal' => ['createdby', 'modifiedby'],
        'uckkarchive_proof' => ['userid', 'createdby', 'modifiedby'],
        'uckkarchive_prov' => ['createdby', 'modifiedby'],
        'uckkarchive_rev' => ['createdby', 'modifiedby'],
        'uckkarchive_export' => ['userid', 'createdby', 'modifiedby', 'exportedby'],
        'uckkarchive_media' => ['userid', 'ownerid', 'createdby', 'modifiedby'],
        'uckkarchive_media_version' => ['userid', 'createdby', 'modifiedby'],
        'uckkarchive_media_source' => ['userid', 'createdby', 'modifiedby'],
        'uckkarchive_media_collection' => ['userid', 'ownerid', 'createdby', 'modifiedby'],
        'uckkarchive_media_relation' => ['userid', 'createdby', 'modifiedby'],
        'uckkarchive_media_tag' => ['userid', 'createdby', 'modifiedby'],
        'uckkarchive_content_marker' => ['userid', 'createdby', 'modifiedby'],
        'uckkarchive_content_review' => ['userid', 'reviewerid', 'createdby', 'modifiedby'],
        'uckkarchive_external_work' => ['userid', 'ownerid', 'createdby', 'modifiedby'],
    ] as $table => $userfields) {
        if (!uckkarchive_lib_table_exists($table) || !uckkarchive_table_has_field($table, 'archiveid')) {
            continue;
        }

        $columns = uckkarchive_existing_fields($table, $userfields);
        if (empty($columns)) {
            continue;
        }

        $conditions = [];
        $params = [
            'archiveid' => $archiveid,
            'userid' => $userid,
        ];

        foreach ($columns as $column) {
            $conditions[] = "{$column} = :userid";
        }

        $timefield = uckkarchive_table_has_field($table, 'timemodified') ? 'timemodified' : 'timecreated';

        if (!uckkarchive_table_has_field($table, $timefield)) {
            continue;
        }

        $time = $DB->get_field_sql(
            "SELECT MAX({$timefield})
               FROM {{$table}}
              WHERE archiveid = :archiveid
                AND (" . implode(' OR ', $conditions) . ")",
            $params
        );

        if ($time) {
            $times[] = (int)$time;
        }
    }

    return empty($times) ? 0 : max($times);
}

/**
 * Update calendar events for an archive instance.
 *
 * @param stdClass $archive Archive data.
 */
function uckkarchive_update_calendar_events(stdClass $archive): void {
    global $DB, $CFG;

    require_once($CFG->dirroot . '/calendar/lib.php');

    $instanceid = (int)($archive->id ?? $archive->instance ?? 0);

    if ($instanceid <= 0) {
        return;
    }

    $DB->delete_records('event', [
        'modulename' => 'uckkarchive',
        'instance' => $instanceid,
    ]);
}

/**
 * Create one calendar event.
 *
 * @param stdClass $archive Archive data.
 * @param int $cmid Course module id.
 * @param int $time Event timestamp.
 * @param string $name Event name.
 * @param string $eventtype Event type suffix.
 */
function uckkarchive_create_calendar_event(stdClass $archive, int $cmid, int $time, string $name, string $eventtype): void {
    global $CFG;

    require_once($CFG->dirroot . '/calendar/lib.php');

    $event = new stdClass();
    $event->name = $name;
    $event->description = format_module_intro('uckkarchive', $archive, $cmid, false);
    $event->format = FORMAT_HTML;
    $event->courseid = (int)$archive->course;
    $event->groupid = 0;
    $event->userid = 0;
    $event->modulename = 'uckkarchive';
    $event->instance = (int)$archive->id;
    $event->type = CALENDAR_EVENT_TYPE_ACTION;
    $event->eventtype = 'uckkarchive_' . $eventtype;
    $event->timestart = $time;
    $event->timeduration = 0;
    $event->visible = instance_is_visible('uckkarchive', $archive);

    calendar_event::create($event, false);
}

/**
 * Update completion-related metadata after instance save.
 *
 * @param stdClass $archive Archive data.
 */
function uckkarchive_update_completion_metadata(stdClass $archive): void {
    global $DB;

    if (empty($archive->id)) {
        return;
    }

    $record = new stdClass();
    $record->id = (int)$archive->id;
    $record->timemodified = time();

    if (isset($archive->completionrequireitem)) {
        $record->completionrequireitem = empty($archive->completionrequireitem) ? 0 : 1;
    }

    if (isset($archive->completionrequirevalidation)) {
        $record->completionrequirevalidation = empty($archive->completionrequirevalidation) ? 0 : 1;
    }

    $DB->update_record(UCKKARCHIVE_TABLE, $record);
}

/**
 * Return supported archive file areas.
 *
 * @return string[]
 */
function uckkarchive_get_fileareas(): array {
    if (class_exists('\mod_uckkarchive\local\file_area_registry') &&
            method_exists('\mod_uckkarchive\local\file_area_registry', 'get_fileareas')) {
        $areas = \mod_uckkarchive\local\file_area_registry::get_fileareas();

        if (is_array($areas) && !empty($areas)) {
            return array_values(array_unique(array_map('strval', $areas)));
        }
    }

    return [
        UCKKARCHIVE_FILEAREA_PROOF_FILES,
        UCKKARCHIVE_FILEAREA_DECISION_ATTACHMENTS,
        UCKKARCHIVE_FILEAREA_MINUTES_FILES,
        UCKKARCHIVE_FILEAREA_KRISTAL_FILES,
        UCKKARCHIVE_FILEAREA_PORTFOLIO_FILES,
        UCKKARCHIVE_FILEAREA_INTEGRITY_EXPORTS,
        UCKKARCHIVE_FILEAREA_MEDIA_ORIGINAL,
        UCKKARCHIVE_FILEAREA_MEDIA_PREVIEW,
        UCKKARCHIVE_FILEAREA_MEDIA_THUMBNAIL,
        UCKKARCHIVE_FILEAREA_MEDIA_DERIVATIVE,
        UCKKARCHIVE_FILEAREA_MEDIA_CAPTION,
        UCKKARCHIVE_FILEAREA_MEDIA_TRANSCRIPT,
        UCKKARCHIVE_FILEAREA_MEDIA_ATTACHMENT,
        UCKKARCHIVE_FILEAREA_CONTENT_REVIEW_FILES,
        UCKKARCHIVE_FILEAREA_EXTERNAL_WORK_REFERENCE_FILES,
        UCKKARCHIVE_FILEAREA_CULTURAL_PROTOCOL_FILES,
        UCKKARCHIVE_FILEAREA_EXPORT_MANIFEST,
        UCKKARCHIVE_FILEAREA_EXPORT_PACKAGE,
    ];
}

/**
 * Return whether the current user can view a file-area record.
 *
 * @param cm_info|stdClass $cm Course module.
 * @param context $context Module context.
 * @param string $filearea File area.
 * @param int $itemid File item id.
 * @return bool
 */
function uckkarchive_can_view_filearea_item($cm, context $context, string $filearea, int $itemid): bool {
    global $DB, $USER;

    if ($itemid <= 0) {
        return false;
    }

    $record = null;
    $table = '';

    foreach (uckkarchive_get_filearea_tables($filearea) as $candidate) {
        if (!uckkarchive_lib_table_exists($candidate)) {
            continue;
        }

        $candidate_record = $DB->get_record($candidate, ['id' => $itemid], '*', IGNORE_MISSING);

        if (!$candidate_record) {
            continue;
        }

        if (uckkarchive_record_matches_archive($candidate, $candidate_record, (int)$cm->instance)) {
            $record = $candidate_record;
            $table = $candidate;
            break;
        }
    }

    if (!$record) {
        return false;
    }

    if (!uckkarchive_lib_has_capability('mod/uckkarchive:view', $context) &&
            !uckkarchive_lib_has_capability('mod/uckkarchive:viewmedia', $context)) {
        return false;
    }

    $visibility = uckkarchive_lib_normalise_visibility($record->visibility ?? UCKKARCHIVE_VISIBILITY_COURSE);

    if (uckkarchive_lib_is_restricted_visibility($visibility)) {
        if ($visibility === UCKKARCHIVE_VISIBILITY_RESTRICTED_CULTURAL) {
            return uckkarchive_lib_has_capability('mod/uckkarchive:viewculturallyrestricted', $context) ||
                uckkarchive_lib_has_capability('mod/uckkarchive:manageadvisories', $context) ||
                uckkarchive_lib_has_capability('mod/uckkarchive:viewrestricted', $context) ||
                uckkarchive_lib_has_capability('mod/uckkarchive:viewrestrictedmedia', $context);
        }

        return uckkarchive_lib_has_capability('mod/uckkarchive:viewrestricted', $context) ||
            uckkarchive_lib_has_capability('mod/uckkarchive:viewrestrictedmedia', $context);
    }

    if (in_array($visibility, [
        UCKKARCHIVE_VISIBILITY_HIDDEN,
        UCKKARCHIVE_VISIBILITY_ARCHIVED,
    ], true)) {
        return uckkarchive_lib_has_capability('mod/uckkarchive:viewrestricted', $context) ||
            uckkarchive_lib_has_capability('mod/uckkarchive:manageadvisories', $context);
    }

    if (!empty($record->userid) && (int)$record->userid === (int)$USER->id) {
        return true;
    }

    if (!empty($record->ownerid) && (int)$record->ownerid === (int)$USER->id) {
        return true;
    }

    if (!empty($record->createdby) && (int)$record->createdby === (int)$USER->id) {
        return true;
    }

    if (uckkarchive_filearea_is_media($filearea)) {
        return uckkarchive_lib_has_capability('mod/uckkarchive:viewmedia', $context);
    }

    if (uckkarchive_filearea_is_advisory($filearea)) {
        return uckkarchive_lib_has_capability('mod/uckkarchive:viewadvisories', $context) ||
            uckkarchive_lib_has_capability('mod/uckkarchive:manageadvisories', $context);
    }

    if (uckkarchive_filearea_is_export($filearea)) {
        return uckkarchive_lib_has_capability('mod/uckkarchive:export', $context) ||
            uckkarchive_lib_has_capability('mod/uckkarchive:exportmedia', $context);
    }

    return in_array($visibility, [
        UCKKARCHIVE_VISIBILITY_COURSE,
        UCKKARCHIVE_VISIBILITY_GROUP,
        UCKKARCHIVE_VISIBILITY_COHORT,
        UCKKARCHIVE_VISIBILITY_PROGRAM,
        UCKKARCHIVE_VISIBILITY_INSTITUTION,
        UCKKARCHIVE_VISIBILITY_PUBLIC,
    ], true);
}

/**
 * Return whether the current user may download a file area.
 *
 * @param context $context Module context.
 * @param string $filearea File area.
 * @return bool
 */
function uckkarchive_can_download_filearea(context $context, string $filearea): bool {
    if (uckkarchive_filearea_is_media($filearea)) {
        if (in_array($filearea, [
            UCKKARCHIVE_FILEAREA_MEDIA_PREVIEW,
            UCKKARCHIVE_FILEAREA_MEDIA_THUMBNAIL,
            UCKKARCHIVE_FILEAREA_MEDIA_CAPTION,
            UCKKARCHIVE_FILEAREA_MEDIA_TRANSCRIPT,
        ], true)) {
            return uckkarchive_lib_has_capability('mod/uckkarchive:viewmedia', $context) ||
                uckkarchive_lib_has_capability('mod/uckkarchive:downloadmedia', $context);
        }

        return uckkarchive_lib_has_capability('mod/uckkarchive:downloadmedia', $context);
    }

    if (uckkarchive_filearea_is_advisory($filearea)) {
        return uckkarchive_lib_has_capability('mod/uckkarchive:viewadvisories', $context) ||
            uckkarchive_lib_has_capability('mod/uckkarchive:manageadvisories', $context);
    }

    if (uckkarchive_filearea_is_export($filearea)) {
        return uckkarchive_lib_has_capability('mod/uckkarchive:export', $context) ||
            uckkarchive_lib_has_capability('mod/uckkarchive:exportmedia', $context);
    }

    return uckkarchive_lib_has_capability('mod/uckkarchive:view', $context);
}

/**
 * Map file area to owner tables.
 *
 * Media file areas may be itemid = media.id or itemid = media_version.id,
 * depending on whether the file is attached to the current media record or a
 * concrete version record.
 *
 * @param string $filearea File area.
 * @return string[]
 */
function uckkarchive_get_filearea_tables(string $filearea): array {
    return match ($filearea) {
        UCKKARCHIVE_FILEAREA_PROOF_FILES => ['uckkarchive_proof'],
        UCKKARCHIVE_FILEAREA_KRISTAL_FILES => ['uckkarchive_kristal'],
        UCKKARCHIVE_FILEAREA_INTEGRITY_EXPORTS,
        UCKKARCHIVE_FILEAREA_EXPORT_MANIFEST,
        UCKKARCHIVE_FILEAREA_EXPORT_PACKAGE => ['uckkarchive_export'],
        UCKKARCHIVE_FILEAREA_DECISION_ATTACHMENTS,
        UCKKARCHIVE_FILEAREA_MINUTES_FILES,
        UCKKARCHIVE_FILEAREA_PORTFOLIO_FILES => ['uckkarchive_item'],
        UCKKARCHIVE_FILEAREA_MEDIA_ORIGINAL,
        UCKKARCHIVE_FILEAREA_MEDIA_PREVIEW,
        UCKKARCHIVE_FILEAREA_MEDIA_THUMBNAIL,
        UCKKARCHIVE_FILEAREA_MEDIA_DERIVATIVE,
        UCKKARCHIVE_FILEAREA_MEDIA_CAPTION,
        UCKKARCHIVE_FILEAREA_MEDIA_TRANSCRIPT,
        UCKKARCHIVE_FILEAREA_MEDIA_ATTACHMENT => ['uckkarchive_media', 'uckkarchive_media_version'],
        UCKKARCHIVE_FILEAREA_CONTENT_REVIEW_FILES => ['uckkarchive_content_review'],
        UCKKARCHIVE_FILEAREA_EXTERNAL_WORK_REFERENCE_FILES => ['uckkarchive_external_work'],
        UCKKARCHIVE_FILEAREA_CULTURAL_PROTOCOL_FILES => ['uckkarchive_content_marker'],
        default => [],
    };
}

/**
 * Map file area to primary owner table.
 *
 * @param string $filearea File area.
 * @return string
 */
function uckkarchive_get_filearea_table(string $filearea): string {
    $tables = uckkarchive_get_filearea_tables($filearea);

    return $tables[0] ?? '';
}

/**
 * Return whether a file area belongs to the media subsystem.
 *
 * @param string $filearea File area.
 * @return bool
 */
function uckkarchive_filearea_is_media(string $filearea): bool {
    return in_array($filearea, [
        UCKKARCHIVE_FILEAREA_MEDIA_ORIGINAL,
        UCKKARCHIVE_FILEAREA_MEDIA_PREVIEW,
        UCKKARCHIVE_FILEAREA_MEDIA_THUMBNAIL,
        UCKKARCHIVE_FILEAREA_MEDIA_DERIVATIVE,
        UCKKARCHIVE_FILEAREA_MEDIA_CAPTION,
        UCKKARCHIVE_FILEAREA_MEDIA_TRANSCRIPT,
        UCKKARCHIVE_FILEAREA_MEDIA_ATTACHMENT,
    ], true);
}

/**
 * Return whether a file area belongs to content advisory/cultural protocol data.
 *
 * @param string $filearea File area.
 * @return bool
 */
function uckkarchive_filearea_is_advisory(string $filearea): bool {
    return in_array($filearea, [
        UCKKARCHIVE_FILEAREA_CONTENT_REVIEW_FILES,
        UCKKARCHIVE_FILEAREA_CULTURAL_PROTOCOL_FILES,
    ], true);
}

/**
 * Return whether a file area is an export area.
 *
 * @param string $filearea File area.
 * @return bool
 */
function uckkarchive_filearea_is_export(string $filearea): bool {
    return in_array($filearea, [
        UCKKARCHIVE_FILEAREA_INTEGRITY_EXPORTS,
        UCKKARCHIVE_FILEAREA_EXPORT_MANIFEST,
        UCKKARCHIVE_FILEAREA_EXPORT_PACKAGE,
    ], true);
}

/**
 * Return whether a table exists.
 *
 * @param string $table Table name without prefix.
 * @return bool
 */
function uckkarchive_lib_table_exists(string $table): bool {
    global $DB;

    return $DB->get_manager()->table_exists(new xmldb_table($table));
}

/**
 * Return whether a table has a field.
 *
 * @param string $table Table name without prefix.
 * @param string $field Field name.
 * @return bool
 */
function uckkarchive_table_has_field(string $table, string $field): bool {
    global $DB;

    if (!uckkarchive_lib_table_exists($table)) {
        return false;
    }

    $columns = $DB->get_columns($table);

    return array_key_exists($field, $columns);
}

/**
 * Return existing fields from a candidate list.
 *
 * @param string $table Table name without prefix.
 * @param string[] $fields Candidate fields.
 * @return string[]
 */
function uckkarchive_existing_fields(string $table, array $fields): array {
    global $DB;

    if (!uckkarchive_lib_table_exists($table)) {
        return [];
    }

    $columns = $DB->get_columns($table);
    $existing = [];

    foreach ($fields as $field) {
        if (array_key_exists($field, $columns)) {
            $existing[] = $field;
        }
    }

    return $existing;
}

/**
 * Delete records by archiveid when the table/field exists.
 *
 * @param string $table Table name without prefix.
 * @param int $archiveid Archive id.
 * @return void
 */
function uckkarchive_delete_records_by_archiveid(string $table, int $archiveid): void {
    global $DB;

    if (!uckkarchive_lib_table_exists($table) || !uckkarchive_table_has_field($table, 'archiveid')) {
        return;
    }

    $DB->delete_records($table, ['archiveid' => $archiveid]);
}

/**
 * Count records associated with a user.
 *
 * @param string $table Table name without prefix.
 * @param int $archiveid Archive id.
 * @param int $userid User id.
 * @param string[] $userfields User field candidates.
 * @return int
 */
function uckkarchive_count_user_records(
    string $table,
    int $archiveid,
    int $userid,
    array $userfields = ['userid', 'createdby']
): int {
    global $DB;

    if (!uckkarchive_lib_table_exists($table) || !uckkarchive_table_has_field($table, 'archiveid')) {
        return 0;
    }

    $fields = uckkarchive_existing_fields($table, $userfields);

    if (empty($fields)) {
        return 0;
    }

    $conditions = [];
    foreach ($fields as $field) {
        $conditions[] = "{$field} = :userid";
    }

    return (int)$DB->count_records_select(
        $table,
        'archiveid = :archiveid AND (' . implode(' OR ', $conditions) . ')',
        [
            'archiveid' => $archiveid,
            'userid' => $userid,
        ]
    );
}

/**
 * Return whether a known capability is granted.
 *
 * Unknown capabilities are treated as unavailable so this file can remain
 * compatible while db/access.php is being expanded.
 *
 * @param string $capability Capability name.
 * @param context $context Context.
 * @return bool
 */
function uckkarchive_lib_has_capability(string $capability, context $context): bool {
    if (function_exists('get_capability_info') && !get_capability_info($capability)) {
        return false;
    }

    return has_capability($capability, $context);
}

/**
 * Return whether a visibility value is restricted.
 *
 * @param string $visibility Visibility.
 * @return bool
 */
function uckkarchive_lib_is_restricted_visibility(string $visibility): bool {
    return in_array($visibility, [
        UCKKARCHIVE_VISIBILITY_RESTRICTED,
        UCKKARCHIVE_VISIBILITY_RESTRICTED_INTEGRITY,
        UCKKARCHIVE_VISIBILITY_RESTRICTED_CULTURAL,
    ], true);
}

/**
 * Return whether a file-area owner record belongs to this archive instance.
 *
 * @param string $table Table name.
 * @param stdClass $record Owner record.
 * @param int $archiveid Archive instance id.
 * @return bool
 */
function uckkarchive_record_matches_archive(string $table, stdClass $record, int $archiveid): bool {
    global $DB;

    if ($archiveid <= 0) {
        return false;
    }

    if (!empty($record->archiveid)) {
        return (int)$record->archiveid === $archiveid;
    }

    if ($table === 'uckkarchive_media_version' && !empty($record->mediaid) && uckkarchive_lib_table_exists('uckkarchive_media')) {
        $media = $DB->get_record('uckkarchive_media', ['id' => (int)$record->mediaid], 'id, archiveid', IGNORE_MISSING);

        return $media && (int)$media->archiveid === $archiveid;
    }

    if ($table === 'uckkarchive_content_review' && !empty($record->markerid) &&
            uckkarchive_lib_table_exists('uckkarchive_content_marker')) {
        $marker = $DB->get_record(
            'uckkarchive_content_marker',
            ['id' => (int)$record->markerid],
            'id, archiveid',
            IGNORE_MISSING
        );

        return $marker && (int)$marker->archiveid === $archiveid;
    }

    return false;
}

/**
 * Build a database-safe archive instance record.
 *
 * This function is deliberately schema-owned. Moodle form/moduleinfo objects may
 * contain Moodle form/moduleinfo objects may contain fields that are not columns
 * in the uckkarchive table; they must not be passed directly to
 * insert_record()/update_record().
 *
 * @param stdClass $data Raw module data.
 * @param bool $isnew Whether this is a new instance.
 * @return stdClass Database-safe instance record.
 */
function uckkarchive_prepare_instance_record(stdClass $data, bool $isnew): stdClass {
    global $USER, $DB;

    $record = new stdClass();

    if (!$isnew) {
        $record->id = (int)($data->id ?? $data->instance ?? 0);
    }

    $record->course = (int)($data->course ?? 0);
    $record->name = trim((string)($data->name ?? ''));
    $record->intro = $data->intro ?? '';
    $record->introformat = (int)($data->introformat ?? FORMAT_HTML);

    $record->archivecode = uckkarchive_optional_text($data->archivecode ?? null, 100);
    $record->archivetype = clean_param((string)($data->archivetype ?? 'course'), PARAM_ALPHANUMEXT);
    $record->archivepolicy = clean_param((string)($data->archivepolicy ?? 'validated'), PARAM_ALPHANUMEXT);

    $visibility = uckkarchive_lib_normalise_visibility($data->visibility ?? UCKKARCHIVE_VISIBILITY_COURSE);
    $record->visibility = $visibility;
    $record->defaultvisibility = uckkarchive_lib_normalise_visibility($data->defaultvisibility ?? $visibility);

    $record->requirevalidation = empty($data->requirevalidation) ? 0 : 1;
    $record->allowpublicitems = empty($data->allowpublicitems) ? 0 : 1;
    $record->allowexports = isset($data->allowexports) ? (empty($data->allowexports) ? 0 : 1) : 1;

    $record->completionrequireitem = empty($data->completionrequireitem ?? 0) ? 0 : 1;
    $record->completionrequirevalidation = empty($data->completionrequirevalidation ?? 0) ? 0 : 1;

    $record->status = uckkarchive_lib_normalise_status($data->status ?? UCKKARCHIVE_STATUS_ACTIVE);
    $record->versionno = max(1, (int)($data->versionno ?? 1));
    $record->metadata = uckkarchive_normalise_metadata($data->metadata ?? null);

    $record->timemodified = (int)($data->timemodified ?? time());
    $record->modifiedby = (int)($data->modifiedby ?? $USER->id ?? 0);

    if ($isnew) {
        $record->timecreated = (int)($data->timecreated ?? time());
        $record->createdby = (int)($data->createdby ?? $USER->id ?? 0);
    } else if (!empty($record->id)) {
        $current = $DB->get_record(UCKKARCHIVE_TABLE, ['id' => $record->id], 'id, timecreated, createdby, versionno', IGNORE_MISSING);

        if ($current) {
            $record->timecreated = (int)$current->timecreated;
            $record->createdby = (int)$current->createdby;
            $record->versionno = max((int)$current->versionno, $record->versionno);
        }
    }

    return $record;
}

/**
 * Return a clipped optional text value or null.
 *
 * @param mixed $value Raw value.
 * @param int $maxlength Maximum length.
 * @return string|null
 */
function uckkarchive_optional_text(mixed $value, int $maxlength): ?string {
    if ($value === null) {
        return null;
    }

    $value = trim((string)$value);

    if ($value === '') {
        return null;
    }

    return core_text::substr(clean_param($value, PARAM_TEXT), 0, $maxlength);
}

/**
 * Normalise archive status.
 *
 * @param string|null $status Raw status.
 * @return string
 */
function uckkarchive_lib_normalise_status(?string $status): string {
    $status = clean_param((string)$status, PARAM_ALPHANUMEXT);

    $allowed = [
        UCKKARCHIVE_STATUS_DRAFT,
        UCKKARCHIVE_STATUS_ACTIVE,
        UCKKARCHIVE_STATUS_PENDING_REVIEW,
        UCKKARCHIVE_STATUS_VALIDATED,
        UCKKARCHIVE_STATUS_REJECTED,
        UCKKARCHIVE_STATUS_CORRECTION_REQUIRED,
        UCKKARCHIVE_STATUS_CONTESTED,
        UCKKARCHIVE_STATUS_INVALIDATED,
        UCKKARCHIVE_STATUS_CLOSED,
        UCKKARCHIVE_STATUS_ARCHIVED,
        UCKKARCHIVE_STATUS_DELETED_SOFT,
        UCKKARCHIVE_STATUS_RESTRICTED,
    ];

    return in_array($status, $allowed, true) ? $status : UCKKARCHIVE_STATUS_ACTIVE;
}

/**
 * Normalise archive visibility.
 *
 * @param string|null $visibility Raw visibility.
 * @return string
 */
function uckkarchive_lib_normalise_visibility(?string $visibility): string {
    $visibility = clean_param((string)$visibility, PARAM_ALPHANUMEXT);

    $allowed = [
        UCKKARCHIVE_VISIBILITY_PRIVATE,
        UCKKARCHIVE_VISIBILITY_USER,
        UCKKARCHIVE_VISIBILITY_GROUP,
        UCKKARCHIVE_VISIBILITY_COURSE,
        UCKKARCHIVE_VISIBILITY_COHORT,
        UCKKARCHIVE_VISIBILITY_PROGRAM,
        UCKKARCHIVE_VISIBILITY_INSTITUTION,
        UCKKARCHIVE_VISIBILITY_PUBLIC,
        UCKKARCHIVE_VISIBILITY_RESTRICTED,
        UCKKARCHIVE_VISIBILITY_RESTRICTED_INTEGRITY,
        UCKKARCHIVE_VISIBILITY_RESTRICTED_CULTURAL,
        UCKKARCHIVE_VISIBILITY_HIDDEN,
        UCKKARCHIVE_VISIBILITY_ARCHIVED,
    ];

    return in_array($visibility, $allowed, true) ? $visibility : UCKKARCHIVE_VISIBILITY_COURSE;
}

/**
 * Normalise metadata to JSON string or null.
 *
 * @param mixed $metadata Metadata value.
 * @return string|null
 */
function uckkarchive_normalise_metadata(mixed $metadata): ?string {
    if ($metadata === null || $metadata === '') {
        return null;
    }

    if (is_string($metadata)) {
        $decoded = json_decode($metadata, true);

        if (json_last_error() === JSON_ERROR_NONE && is_array($decoded)) {
            return json_encode($decoded, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
        }

        return null;
    }

    if ($metadata instanceof stdClass) {
        $metadata = (array)$metadata;
    }

    if (is_array($metadata)) {
        return json_encode($metadata, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
    }

    return null;
}