<?php
// This file is part of Moodle - https://moodle.org/
//
// Moodle is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// any later version.

/**
 * Course-level archive activity listing entry point.
 *
 * In Moodle 5.x, activity module index pages should redirect to the
 * course Activities overview page. The overview page is responsible for
 * listing the visible instances of this activity in the requested course.
 *
 * UCKK archive validation, provenance, revision, export, restricted access,
 * and Kristal workflows are handled by their own controllers and services,
 * not by this course-level listing entry point.
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

defined('MOODLE_INTERNAL') || die();

$courseid = optional_param('id', SITEID, PARAM_INT);

$course = $DB->get_record('course', ['id' => $courseid], '*', MUST_EXIST);

require_login($course);

\core_courseformat\activityoverviewbase::redirect_to_overview_page($courseid, 'uckkarchive');