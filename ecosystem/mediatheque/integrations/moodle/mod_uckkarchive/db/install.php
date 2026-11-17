<?php
// This file is part of Moodle - https://moodle.org/.
//
// Moodle is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// any later version.

/**
 * Post-install seed data for UCKK Archive.
 *
 * @package    mod_uckkarchive
 * @copyright  2026 Univers-Cité King Klown
 * @license    https://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later
 */

defined('MOODLE_INTERNAL') || die();

/** Seed autonomous public media libraries and their site mappings. */
function xmldb_uckkarchive_install(): void {
    global $DB;

    $now = time();
    $defaults = [
        'uckk' => [
            'uuid' => '00000000-0000-4000-8000-00000000a001',
            'slug' => 'uckk',
            'name' => 'Médiathèque UCKK',
        ],
        'ucc' => [
            'uuid' => '00000000-0000-4000-8000-00000000a002',
            'slug' => 'ucc',
            'name' => 'Médiathèque chrétienne',
        ],
        'math' => [
            'uuid' => '00000000-0000-4000-8000-00000000a003',
            'slug' => 'math',
            'name' => 'Bibliothèque mathématique',
        ],
    ];

    foreach ($defaults as $sitekey => $spec) {
        $libraryid = (int)$DB->insert_record('uckkarchive_library', (object)[
            'uuid' => $spec['uuid'],
            'slug' => $spec['slug'],
            'name' => $spec['name'],
            'description' => '',
            'status' => 'active',
            'timecreated' => $now,
            'timemodified' => $now,
            'metadata' => null,
        ]);

        $DB->insert_record('uckkarchive_library_site', (object)[
            'libraryid' => $libraryid,
            'sitekey' => $sitekey,
            'role' => 'primary',
            'sortorder' => 0,
            'status' => 'active',
            'timecreated' => $now,
            'timemodified' => $now,
        ]);
    }
}
