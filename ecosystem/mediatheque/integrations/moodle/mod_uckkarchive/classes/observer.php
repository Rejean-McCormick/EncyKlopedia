<?php
// This file is part of Moodle - https://moodle.org/
//
// Moodle is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// any later version.

/**
 * Archive observers for stable Moodle lifecycle events.
 *
 * @package    mod_uckkarchive
 * @copyright  2026 Univers-Cité King Klown
 * @license    https://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later
 */

namespace mod_uckkarchive;

defined('MOODLE_INTERNAL') || die();

require_once(dirname(__DIR__) . '/locallib.php');

/**
 * Stable Moodle event observers for archive housekeeping.
 */
class observer {
    /**
     * Mark archive records as archived when a course module is deleted.
     *
     * @param \core\event\course_module_deleted $event Event.
     * @return void
     */
    public static function course_module_deleted(\core\event\course_module_deleted $event): void {
        global $DB;

        $cmid = (int)$event->objectid;
        if ($cmid <= 0) {
            return;
        }

        $now = time();
        $DB->execute(
            "UPDATE {uckkarchive_item}
                SET status = ?, timemodified = ?
              WHERE cmid = ? AND status <> ?",
            [UCKKARCHIVE_STATUS_ARCHIVED, $now, $cmid, UCKKARCHIVE_STATUS_ARCHIVED]
        );

        if ($DB->get_manager()->table_exists(UCKKARCHIVE_EXPORT_TABLE)) {
            $DB->execute(
                "UPDATE {" . UCKKARCHIVE_EXPORT_TABLE . "}
                    SET status = ?, timemodified = ?
                  WHERE cmid = ? AND status NOT IN (?, ?)",
                ['cancelled', $now, $cmid, 'completed', 'cancelled']
            );
        }
    }

    /**
     * Mark archive records as archived when a course is deleted.
     *
     * @param \core\event\course_deleted $event Event.
     * @return void
     */
    public static function course_deleted(\core\event\course_deleted $event): void {
        global $DB;

        $courseid = (int)$event->objectid;
        if ($courseid <= 0) {
            return;
        }

        $now = time();
        $DB->execute(
            "UPDATE {uckkarchive_item}
                SET status = ?, timemodified = ?
              WHERE courseid = ? AND status <> ?",
            [UCKKARCHIVE_STATUS_ARCHIVED, $now, $courseid, UCKKARCHIVE_STATUS_ARCHIVED]
        );
    }

    /**
     * Scrub nullable user ownership references when a user is deleted.
     *
     * @param \core\event\user_deleted $event Event.
     * @return void
     */
    public static function user_deleted(\core\event\user_deleted $event): void {
        global $DB;

        $userid = (int)$event->objectid;
        if ($userid <= 0) {
            return;
        }

        foreach ([UCKKARCHIVE_ITEM_TABLE, UCKKARCHIVE_KRISTAL_TABLE, UCKKARCHIVE_PROOF_TABLE, UCKKARCHIVE_PROVENANCE_TABLE, UCKKARCHIVE_REVISION_TABLE, UCKKARCHIVE_EXPORT_TABLE] as $table) {
            if ($DB->get_manager()->table_exists($table) && $DB->get_manager()->field_exists($table, 'userid')) {
                $DB->set_field($table, 'userid', null, ['userid' => $userid]);
            }
            if ($DB->get_manager()->table_exists($table) && $DB->get_manager()->field_exists($table, 'authorid')) {
                $DB->set_field($table, 'authorid', null, ['authorid' => $userid]);
            }
        }
    }
}
