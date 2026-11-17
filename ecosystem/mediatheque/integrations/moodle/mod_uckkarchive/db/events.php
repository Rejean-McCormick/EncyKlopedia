<?php
// This file is part of Moodle - https://moodle.org/
//
// Moodle is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// any later version.

/**
 * Event observers for UCKK Archive.
 *
 * @package    mod_uckkarchive
 * @copyright  2026 Univers-Cité King Klown
 * @license    https://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later
 */

defined('MOODLE_INTERNAL') || die();

/**
 * UCKK Archive event observers.
 *
 * This file only registers observers for stable Moodle lifecycle events.
 *
 * Domain events emitted by this plugin, such as:
 *
 * - archive_item_created
 * - archive_item_revised
 * - archive_item_validated
 * - archive_item_exported
 * - media_created
 * - media_updated
 * - media_exported
 * - media_version_created
 * - media_collection_created
 * - content_marker_created
 * - content_marker_reviewed
 * - external_work_created
 *
 * are audit events. They are not observed here by default.
 *
 * Cross-plugin archival actions from challenges, assemblies, integrity reviews,
 * reports, seed tools, or import scripts must call mod_uckkarchive external
 * services or local domain classes directly unless the source plugin event
 * classes are guaranteed to exist in every target installation.
 *
 * The observer class must ensure that lifecycle cleanup/anonymisation covers
 * all archive-owned records, including:
 *
 * - archive items
 * - Kristals
 * - proofs
 * - provenance
 * - revisions
 * - exports
 * - media
 * - media versions
 * - media sources
 * - media collections
 * - media relations
 * - media tags
 * - content advisory tags
 * - content advisory tag sets
 * - content markers
 * - content reviews
 * - external works
 * - Moodle File API areas owned by mod_uckkarchive
 */
$observers = [
    [
        'eventname' => '\core\event\course_module_deleted',
        'callback' => '\mod_uckkarchive\observer::course_module_deleted',
        'internal' => false,
        'priority' => 9999,
    ],
    [
        'eventname' => '\core\event\course_deleted',
        'callback' => '\mod_uckkarchive\observer::course_deleted',
        'internal' => false,
        'priority' => 9999,
    ],
    [
        'eventname' => '\core\event\user_deleted',
        'callback' => '\mod_uckkarchive\observer::user_deleted',
        'internal' => false,
        'priority' => 9999,
    ],
];
