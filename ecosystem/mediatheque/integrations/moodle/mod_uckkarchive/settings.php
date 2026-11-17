<?php
// This file is part of Moodle - https://moodle.org/
//
// Moodle is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// any later version.

/**
 * Admin settings for the UCKK Archive activity module.
 *
 * @package    mod_uckkarchive
 * @copyright  2026 Univers-Cité King Klown
 * @license    https://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later
 */

defined('MOODLE_INTERNAL') || die();

if ($ADMIN->fulltree) {
    $settings->add(new admin_setting_heading(
        'mod_uckkarchive/general',
        get_string('pluginname', 'mod_uckkarchive'),
        ''
    ));

    $libraryurl = new moodle_url('/mod/uckkarchive/library_admin.php');
    $settings->add(new admin_setting_description(
        'mod_uckkarchive/libraryadminlink',
        get_string('libraryadmin', 'mod_uckkarchive'),
        html_writer::link($libraryurl, get_string('libraryadminlink', 'mod_uckkarchive'))
    ));
}