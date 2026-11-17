<?php
// This file is part of Moodle - https://moodle.org/
//
// Moodle is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// any later version.

/**
 * Upgrade steps for the UCKK Archive activity module.
 *
 * @package    mod_uckkarchive
 * @copyright  2026 Univers-Cité King Klown
 * @license    https://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later
 */

defined('MOODLE_INTERNAL') || die();

/**
 * Execute upgrade steps for mod_uckkarchive.
 *
 * Clean installs use db/install.xml. This file is only used when Moodle detects
 * an already-installed older version of the plugin.
 *
 * Important:
 * - Do not call mod_uckkarchive service classes from here.
 * - Do not render output from here.
 * - Do not run archive validation, export generation, privacy deletion, or
 *   integrity workflows from here.
 * - Use XMLDB/database manager operations for schema changes.
 * - Add one version-gated block per schema/data migration.
 *
 * @param int $oldversion Previously installed plugin version.
 * @return bool
 */
function xmldb_uckkarchive_upgrade($oldversion): bool {
    if ($oldversion < 2026051200) {
        // Initial stable release baseline.
        //
        // The complete initial archive schema is defined in db/install.xml and
        // is used for clean installs. This block is conservative for
        // development/pre-release sites that already had the module installed.
        uckkarchive_upgrade_repair_initial_indexes();

        upgrade_mod_savepoint(true, 2026051200, 'uckkarchive');
    }

    if ($oldversion < 2026052700) {
        // Add the self-contained media library, content advisory, and external
        // work schema introduced after the initial archive-only baseline.
        uckkarchive_upgrade_create_media_advisory_external_tables();

        upgrade_mod_savepoint(true, 2026052700, 'uckkarchive');
    }

    if ($oldversion < 2026052701) {
        // Expand export records so media/collection exports can store scope,
        // redaction, package, manifest, provenance, and processing status.
        uckkarchive_upgrade_extend_export_table();

        upgrade_mod_savepoint(true, 2026052701, 'uckkarchive');
    }

    if ($oldversion < 2026052702) {
        // Repair and add indexes for archive, media, advisory, external work,
        // and export lookup paths.
        uckkarchive_upgrade_repair_initial_indexes();
        uckkarchive_upgrade_repair_media_advisory_external_indexes();

        upgrade_mod_savepoint(true, 2026052702, 'uckkarchive');
    }

    if ($oldversion < 2026052703) {
        // Add canonical media source and rights fields introduced after the
        // first media-library upgrade snapshot. Existing records are backfilled
        // from legacy source and metadata values where possible.
        uckkarchive_upgrade_extend_media_source_record_fields();

        upgrade_mod_savepoint(true, 2026052703, 'uckkarchive');
    }

    if ($oldversion < 2026060400) {
        // Add the public-search exposure flag used by the public mediatheque
        // repository. Older development databases may have public media rows
        // without this column, which causes the public explorer SQL to fail.
        uckkarchive_upgrade_add_media_searchable_field();

        upgrade_mod_savepoint(true, 2026060400, 'uckkarchive');
    }

    if ($oldversion < 2026060401) {
        // Add audience suitability to media collections for the public
        // mediatheque repository collection-count query.
        uckkarchive_upgrade_add_media_collection_audience_field();

        upgrade_mod_savepoint(true, 2026060401, 'uckkarchive');
    }

    if ($oldversion < 2026092802) {
        // Split the formerly site-wide public mediatheque into autonomous
        // libraries. Existing media/collections become part of the canonical
        // UCKK library; UCC and Math start isolated. Explicit directional
        // bridges can then share a whole library, one collection, or one media
        // object without duplicating media rows or UUIDs.
        uckkarchive_upgrade_create_library_bridge_schema();

        upgrade_mod_savepoint(true, 2026092802, 'uckkarchive');
    }

    if ($oldversion < 2026100300) {
        // Add a dedicated Kristal artifact catalog for stable semantic refs,
        // hierarchy, and immutable stored versions. This is deliberately
        // separate from the legacy uckkarchive_kristal insight table.
        uckkarchive_upgrade_create_kristal_artifact_catalog();

        upgrade_mod_savepoint(true, 2026100300, 'uckkarchive');
    }

    return true;
}


/**
 * Create the semantic-identity-safe Kristal artifact catalog.
 *
 * The catalog stores references and bytes/version bindings only. Kristal/Kristall
 * remains authoritative for KQ/KP/KA/KS, Mesh, assertions, and crystallization.
 *
 * @return void
 */
function uckkarchive_upgrade_create_kristal_artifact_catalog(): void {
    uckkarchive_upgrade_create_table_if_missing('uckkarchive_kartifact', [
        uckkarchive_upgrade_field('id', XMLDB_TYPE_INTEGER, '10', true, true),
        uckkarchive_upgrade_field('uuid', XMLDB_TYPE_CHAR, '36', true, false, ''),
        uckkarchive_upgrade_field('libraryid', XMLDB_TYPE_INTEGER, '10', true, false, 0),
        uckkarchive_upgrade_field('kristalref', XMLDB_TYPE_CHAR, '255', true, false, ''),
        uckkarchive_upgrade_field('kind', XMLDB_TYPE_CHAR, '32', true, false, 'course'),
        uckkarchive_upgrade_field('parentid', XMLDB_TYPE_INTEGER, '10'),
        uckkarchive_upgrade_field('voiecode', XMLDB_TYPE_CHAR, '32'),
        uckkarchive_upgrade_field('coursecode', XMLDB_TYPE_CHAR, '64'),
        uckkarchive_upgrade_field('title', XMLDB_TYPE_CHAR, '255', true, false, ''),
        uckkarchive_upgrade_field('status', XMLDB_TYPE_CHAR, '32', true, false, 'stub'),
        uckkarchive_upgrade_field('portablecontract', XMLDB_TYPE_CHAR, '64', true, false, 'kristal_state/6.0'),
        uckkarchive_upgrade_field('kristallbaseline', XMLDB_TYPE_CHAR, '64', true, false, '7.0.0-draft.3.2'),
        uckkarchive_upgrade_field('mediaid', XMLDB_TYPE_INTEGER, '10'),
        uckkarchive_upgrade_field('currentversionid', XMLDB_TYPE_INTEGER, '10'),
        uckkarchive_upgrade_field('sortorder', XMLDB_TYPE_INTEGER, '10', true, false, 0),
        uckkarchive_upgrade_field('metadata', XMLDB_TYPE_TEXT),
        uckkarchive_upgrade_field('timecreated', XMLDB_TYPE_INTEGER, '10', true, false, 0),
        uckkarchive_upgrade_field('timemodified', XMLDB_TYPE_INTEGER, '10', true, false, 0),
    ], [
        new xmldb_key('primary', XMLDB_KEY_PRIMARY, ['id']),
        new xmldb_key('libraryid', XMLDB_KEY_FOREIGN, ['libraryid'], 'uckkarchive_library', ['id']),
        new xmldb_key('parentid', XMLDB_KEY_FOREIGN, ['parentid'], 'uckkarchive_kartifact', ['id']),
        new xmldb_key('mediaid', XMLDB_KEY_FOREIGN, ['mediaid'], 'uckkarchive_media', ['id']),
    ], [
        new xmldb_index('uuid', XMLDB_INDEX_UNIQUE, ['uuid']),
        new xmldb_index('library-ref', XMLDB_INDEX_UNIQUE, ['libraryid', 'kristalref']),
        new xmldb_index('parent-sort', XMLDB_INDEX_NOTUNIQUE, ['parentid', 'sortorder']),
        new xmldb_index('kind', XMLDB_INDEX_NOTUNIQUE, ['kind']),
        new xmldb_index('coursecode', XMLDB_INDEX_NOTUNIQUE, ['coursecode']),
        new xmldb_index('voiecode', XMLDB_INDEX_NOTUNIQUE, ['voiecode']),
        new xmldb_index('status', XMLDB_INDEX_NOTUNIQUE, ['status']),
    ]);

    uckkarchive_upgrade_create_table_if_missing('uckkarchive_kversion', [
        uckkarchive_upgrade_field('id', XMLDB_TYPE_INTEGER, '10', true, true),
        uckkarchive_upgrade_field('uuid', XMLDB_TYPE_CHAR, '36', true, false, ''),
        uckkarchive_upgrade_field('artifactid', XMLDB_TYPE_INTEGER, '10', true, false, 0),
        uckkarchive_upgrade_field('mediaid', XMLDB_TYPE_INTEGER, '10', true, false, 0),
        uckkarchive_upgrade_field('mediaversionid', XMLDB_TYPE_INTEGER, '10', true, false, 0),
        uckkarchive_upgrade_field('versionlabel', XMLDB_TYPE_CHAR, '128', true, false, 'stub'),
        uckkarchive_upgrade_field('stateid', XMLDB_TYPE_CHAR, '128'),
        uckkarchive_upgrade_field('releaseid', XMLDB_TYPE_CHAR, '128'),
        uckkarchive_upgrade_field('sha256', XMLDB_TYPE_CHAR, '64', true, false, ''),
        uckkarchive_upgrade_field('status', XMLDB_TYPE_CHAR, '32', true, false, 'stub'),
        uckkarchive_upgrade_field('portablecontract', XMLDB_TYPE_CHAR, '64', true, false, 'kristal_state/6.0'),
        uckkarchive_upgrade_field('kristallbaseline', XMLDB_TYPE_CHAR, '64', true, false, '7.0.0-draft.3.2'),
        uckkarchive_upgrade_field('observedat', XMLDB_TYPE_INTEGER, '10', true, false, 0),
        uckkarchive_upgrade_field('metadata', XMLDB_TYPE_TEXT),
        uckkarchive_upgrade_field('timecreated', XMLDB_TYPE_INTEGER, '10', true, false, 0),
        uckkarchive_upgrade_field('timemodified', XMLDB_TYPE_INTEGER, '10', true, false, 0),
    ], [
        new xmldb_key('primary', XMLDB_KEY_PRIMARY, ['id']),
        new xmldb_key('artifactid', XMLDB_KEY_FOREIGN, ['artifactid'], 'uckkarchive_kartifact', ['id']),
        new xmldb_key('mediaid', XMLDB_KEY_FOREIGN, ['mediaid'], 'uckkarchive_media', ['id']),
        new xmldb_key('mediaversionid', XMLDB_KEY_FOREIGN, ['mediaversionid'], 'uckkarchive_media_version', ['id']),
    ], [
        new xmldb_index('uuid', XMLDB_INDEX_UNIQUE, ['uuid']),
        new xmldb_index('artifact-sha', XMLDB_INDEX_UNIQUE, ['artifactid', 'sha256']),
        new xmldb_index('artifactid', XMLDB_INDEX_NOTUNIQUE, ['artifactid']),
        new xmldb_index('status', XMLDB_INDEX_NOTUNIQUE, ['status']),
        new xmldb_index('stateid', XMLDB_INDEX_NOTUNIQUE, ['stateid']),
        new xmldb_index('releaseid', XMLDB_INDEX_NOTUNIQUE, ['releaseid']),
    ]);
}

/**
 * Create autonomous media-library scope and bridge schema.
 *
 * Existing public media are conservatively assigned to the UCKK root library.
 * Alternate Univers-Cité sites therefore become separated by default and only
 * see content explicitly assigned to their own library or exposed by a bridge.
 *
 * @return void
 */
function uckkarchive_upgrade_create_library_bridge_schema(): void {
    global $DB;

    uckkarchive_upgrade_create_table_if_missing('uckkarchive_library', [
        uckkarchive_upgrade_field('id', XMLDB_TYPE_INTEGER, '10', true, true),
        uckkarchive_upgrade_field('uuid', XMLDB_TYPE_CHAR, '36', true, false, ''),
        uckkarchive_upgrade_field('slug', XMLDB_TYPE_CHAR, '100', true, false, ''),
        uckkarchive_upgrade_field('name', XMLDB_TYPE_CHAR, '255', true, false, ''),
        uckkarchive_upgrade_field('description', XMLDB_TYPE_TEXT),
        uckkarchive_upgrade_field('status', XMLDB_TYPE_CHAR, '32', true, false, 'active'),
        uckkarchive_upgrade_field('createdby', XMLDB_TYPE_INTEGER, '10'),
        uckkarchive_upgrade_field('modifiedby', XMLDB_TYPE_INTEGER, '10'),
        uckkarchive_upgrade_field('timecreated', XMLDB_TYPE_INTEGER, '10', true, false, 0),
        uckkarchive_upgrade_field('timemodified', XMLDB_TYPE_INTEGER, '10', true, false, 0),
        uckkarchive_upgrade_field('metadata', XMLDB_TYPE_TEXT),
    ], [
        new xmldb_key('primary', XMLDB_KEY_PRIMARY, ['id']),
    ], [
        new xmldb_index('uuid', XMLDB_INDEX_UNIQUE, ['uuid']),
        new xmldb_index('slug', XMLDB_INDEX_UNIQUE, ['slug']),
        new xmldb_index('status', XMLDB_INDEX_NOTUNIQUE, ['status']),
    ]);

    uckkarchive_upgrade_create_table_if_missing('uckkarchive_library_site', [
        uckkarchive_upgrade_field('id', XMLDB_TYPE_INTEGER, '10', true, true),
        uckkarchive_upgrade_field('libraryid', XMLDB_TYPE_INTEGER, '10', true, false, 0),
        uckkarchive_upgrade_field('sitekey', XMLDB_TYPE_CHAR, '64', true, false, ''),
        uckkarchive_upgrade_field('role', XMLDB_TYPE_CHAR, '32', true, false, 'primary'),
        uckkarchive_upgrade_field('sortorder', XMLDB_TYPE_INTEGER, '10', true, false, 0),
        uckkarchive_upgrade_field('status', XMLDB_TYPE_CHAR, '32', true, false, 'active'),
        uckkarchive_upgrade_field('timecreated', XMLDB_TYPE_INTEGER, '10', true, false, 0),
        uckkarchive_upgrade_field('timemodified', XMLDB_TYPE_INTEGER, '10', true, false, 0),
    ], [
        new xmldb_key('primary', XMLDB_KEY_PRIMARY, ['id']),
    ], [
        new xmldb_index('site-library', XMLDB_INDEX_UNIQUE, ['sitekey', 'libraryid']),
        new xmldb_index('site-role', XMLDB_INDEX_NOTUNIQUE, ['sitekey', 'role']),
        new xmldb_index('libraryid', XMLDB_INDEX_NOTUNIQUE, ['libraryid']),
        new xmldb_index('status', XMLDB_INDEX_NOTUNIQUE, ['status']),
    ]);

    uckkarchive_upgrade_add_field_if_missing(
        'uckkarchive_media',
        uckkarchive_upgrade_field('libraryid', XMLDB_TYPE_INTEGER, '10')
    );
    uckkarchive_upgrade_add_field_if_missing(
        'uckkarchive_media_collection',
        uckkarchive_upgrade_field('libraryid', XMLDB_TYPE_INTEGER, '10')
    );
    uckkarchive_upgrade_add_index_if_possible(
        'uckkarchive_media',
        new xmldb_index('libraryid', XMLDB_INDEX_NOTUNIQUE, ['libraryid'])
    );
    uckkarchive_upgrade_add_index_if_possible(
        'uckkarchive_media_collection',
        new xmldb_index('libraryid', XMLDB_INDEX_NOTUNIQUE, ['libraryid'])
    );

    uckkarchive_upgrade_create_table_if_missing('uckkarchive_library_bridge', [
        uckkarchive_upgrade_field('id', XMLDB_TYPE_INTEGER, '10', true, true),
        uckkarchive_upgrade_field('uuid', XMLDB_TYPE_CHAR, '36', true, false, ''),
        uckkarchive_upgrade_field('sourcelibraryid', XMLDB_TYPE_INTEGER, '10', true, false, 0),
        uckkarchive_upgrade_field('targetlibraryid', XMLDB_TYPE_INTEGER, '10', true, false, 0),
        uckkarchive_upgrade_field('scopetype', XMLDB_TYPE_CHAR, '32', true, false, 'library'),
        uckkarchive_upgrade_field('scopeid', XMLDB_TYPE_INTEGER, '10', true, false, 0),
        uckkarchive_upgrade_field('label', XMLDB_TYPE_CHAR, '255'),
        uckkarchive_upgrade_field('status', XMLDB_TYPE_CHAR, '32', true, false, 'active'),
        uckkarchive_upgrade_field('createdby', XMLDB_TYPE_INTEGER, '10'),
        uckkarchive_upgrade_field('modifiedby', XMLDB_TYPE_INTEGER, '10'),
        uckkarchive_upgrade_field('timecreated', XMLDB_TYPE_INTEGER, '10', true, false, 0),
        uckkarchive_upgrade_field('timemodified', XMLDB_TYPE_INTEGER, '10', true, false, 0),
        uckkarchive_upgrade_field('metadata', XMLDB_TYPE_TEXT),
    ], [
        new xmldb_key('primary', XMLDB_KEY_PRIMARY, ['id']),
    ], [
        new xmldb_index('uuid', XMLDB_INDEX_UNIQUE, ['uuid']),
        new xmldb_index('bridge-scope', XMLDB_INDEX_UNIQUE, ['sourcelibraryid', 'targetlibraryid', 'scopetype', 'scopeid']),
        new xmldb_index('target-status', XMLDB_INDEX_NOTUNIQUE, ['targetlibraryid', 'status']),
        new xmldb_index('source-status', XMLDB_INDEX_NOTUNIQUE, ['sourcelibraryid', 'status']),
    ]);

    $now = time();
    $defaults = [
        'uckk' => ['uuid' => '00000000-0000-4000-8000-00000000a001', 'name' => 'Médiathèque UCKK'],
        'ucc' => ['uuid' => '00000000-0000-4000-8000-00000000a002', 'name' => 'Médiathèque chrétienne'],
        'math' => ['uuid' => '00000000-0000-4000-8000-00000000a003', 'name' => 'Bibliothèque mathématique'],
    ];

    $libraryids = [];
    foreach ($defaults as $sitekey => $spec) {
        $library = $DB->get_record('uckkarchive_library', ['slug' => $sitekey], '*', IGNORE_MISSING);
        if (!$library) {
            $library = (object)[
                'uuid' => $spec['uuid'],
                'slug' => $sitekey,
                'name' => $spec['name'],
                'description' => '',
                'status' => 'active',
                'timecreated' => $now,
                'timemodified' => $now,
                'metadata' => null,
            ];
            $library->id = (int)$DB->insert_record('uckkarchive_library', $library);
        }
        $libraryids[$sitekey] = (int)$library->id;

        if (!$DB->record_exists('uckkarchive_library_site', [
            'libraryid' => (int)$library->id,
            'sitekey' => $sitekey,
        ])) {
            $DB->insert_record('uckkarchive_library_site', (object)[
                'libraryid' => (int)$library->id,
                'sitekey' => $sitekey,
                'role' => 'primary',
                'sortorder' => 0,
                'status' => 'active',
                'timecreated' => $now,
                'timemodified' => $now,
            ]);
        }
    }

    // Legacy global media cannot reliably be attributed to an alternate site.
    // Keep it in the root UCKK library instead of leaking it into every library.
    if (!empty($libraryids['uckk'])) {
        $DB->execute(
            'UPDATE {uckkarchive_media} SET libraryid = :libraryid WHERE libraryid IS NULL OR libraryid = 0',
            ['libraryid' => $libraryids['uckk']]
        );
        $DB->execute(
            'UPDATE {uckkarchive_media_collection} SET libraryid = :libraryid WHERE libraryid IS NULL OR libraryid = 0',
            ['libraryid' => $libraryids['uckk']]
        );
    }
}

/**
 * Create media, content advisory, and external work tables when upgrading an
 * older installation.
 *
 * @return void
 */
function uckkarchive_upgrade_create_media_advisory_external_tables(): void {
    uckkarchive_upgrade_create_table_if_missing('uckkarchive_media', [
        uckkarchive_upgrade_field('id', XMLDB_TYPE_INTEGER, '10', true, true),
        uckkarchive_upgrade_field('uuid', XMLDB_TYPE_CHAR, '36', true, false, ''),
        uckkarchive_upgrade_field('archiveid', XMLDB_TYPE_INTEGER, '10', true, false, 0),
        uckkarchive_upgrade_field('courseid', XMLDB_TYPE_INTEGER, '10', true, false, 0),
        uckkarchive_upgrade_field('cmid', XMLDB_TYPE_INTEGER, '10', true, false, 0),
        uckkarchive_upgrade_field('contextid', XMLDB_TYPE_INTEGER, '10', true, false, 0),
        uckkarchive_upgrade_field('userid', XMLDB_TYPE_INTEGER, '10', true, false, 0),
        uckkarchive_upgrade_field('ownerid', XMLDB_TYPE_INTEGER, '10', true, false, 0),
        uckkarchive_upgrade_field('createdby', XMLDB_TYPE_INTEGER, '10', true, false, 0),
        uckkarchive_upgrade_field('modifiedby', XMLDB_TYPE_INTEGER, '10', true, false, 0),
        uckkarchive_upgrade_field('currentversionid', XMLDB_TYPE_INTEGER, '10', true, false, 0),
        uckkarchive_upgrade_field('externalworkid', XMLDB_TYPE_INTEGER, '10', true, false, 0),
        uckkarchive_upgrade_field('sourceid', XMLDB_TYPE_INTEGER, '10', true, false, 0),
        uckkarchive_upgrade_field('mediatype', XMLDB_TYPE_CHAR, '50', true, false, ''),
        uckkarchive_upgrade_field('mimetype', XMLDB_TYPE_CHAR, '100', true, false, ''),
        uckkarchive_upgrade_field('status', XMLDB_TYPE_CHAR, '50', true, false, 'draft'),
        uckkarchive_upgrade_field('visibility', XMLDB_TYPE_CHAR, '50', true, false, 'course'),
        uckkarchive_upgrade_field('audiencesuitability', XMLDB_TYPE_CHAR, '50', true, false, 'guided'),
        uckkarchive_upgrade_field('searchable', XMLDB_TYPE_INTEGER, '1', true, false, 1),
        uckkarchive_upgrade_field('source', XMLDB_TYPE_CHAR, '50', true, false, ''),
        uckkarchive_upgrade_field('sourcetype', XMLDB_TYPE_CHAR, '64', false),
        uckkarchive_upgrade_field('sourceurl', XMLDB_TYPE_TEXT),
        uckkarchive_upgrade_field('license', XMLDB_TYPE_CHAR, '128', false),
        uckkarchive_upgrade_field('licensekey', XMLDB_TYPE_CHAR, '128', false),
        uckkarchive_upgrade_field('rightsstatement', XMLDB_TYPE_TEXT),
        uckkarchive_upgrade_field('rightsstatus', XMLDB_TYPE_CHAR, '64', true, false, 'unknown'),
        uckkarchive_upgrade_field('title', XMLDB_TYPE_CHAR, '255', true, false, ''),
        uckkarchive_upgrade_field('summary', XMLDB_TYPE_TEXT),
        uckkarchive_upgrade_field('description', XMLDB_TYPE_TEXT),
        uckkarchive_upgrade_field('metadata', XMLDB_TYPE_TEXT),
        uckkarchive_upgrade_field('restricted', XMLDB_TYPE_INTEGER, '1', true, false, 0),
        uckkarchive_upgrade_field('culturalprotocol', XMLDB_TYPE_INTEGER, '1', true, false, 0),
        uckkarchive_upgrade_field('timecreated', XMLDB_TYPE_INTEGER, '10', true, false, 0),
        uckkarchive_upgrade_field('timemodified', XMLDB_TYPE_INTEGER, '10', true, false, 0),
    ], [
        new xmldb_key('primary', XMLDB_KEY_PRIMARY, ['id']),
        new xmldb_key('uuid', XMLDB_KEY_UNIQUE, ['uuid']),
    ], [
        new xmldb_index('archiveid', XMLDB_INDEX_NOTUNIQUE, ['archiveid']),
        new xmldb_index('courseid', XMLDB_INDEX_NOTUNIQUE, ['courseid']),
        new xmldb_index('cmid', XMLDB_INDEX_NOTUNIQUE, ['cmid']),
        new xmldb_index('contextid', XMLDB_INDEX_NOTUNIQUE, ['contextid']),
        new xmldb_index('status', XMLDB_INDEX_NOTUNIQUE, ['status']),
        new xmldb_index('visibility', XMLDB_INDEX_NOTUNIQUE, ['visibility']),
        new xmldb_index('mediatype', XMLDB_INDEX_NOTUNIQUE, ['mediatype']),
        new xmldb_index('ownerid', XMLDB_INDEX_NOTUNIQUE, ['ownerid']),
    ]);

    uckkarchive_upgrade_create_table_if_missing('uckkarchive_media_version', [
        uckkarchive_upgrade_field('id', XMLDB_TYPE_INTEGER, '10', true, true),
        uckkarchive_upgrade_field('uuid', XMLDB_TYPE_CHAR, '36', true, false, ''),
        uckkarchive_upgrade_field('mediaid', XMLDB_TYPE_INTEGER, '10', true, false, 0),
        uckkarchive_upgrade_field('versionnumber', XMLDB_TYPE_INTEGER, '10', true, false, 0),
        uckkarchive_upgrade_field('versionno', XMLDB_TYPE_INTEGER, '10', true, false, 0),
        uckkarchive_upgrade_field('label', XMLDB_TYPE_CHAR, '255', true, false, ''),
        uckkarchive_upgrade_field('status', XMLDB_TYPE_CHAR, '50', true, false, 'active'),
        uckkarchive_upgrade_field('filearea', XMLDB_TYPE_CHAR, '100', true, false, ''),
        uckkarchive_upgrade_field('filepath', XMLDB_TYPE_CHAR, '255', true, false, '/'),
        uckkarchive_upgrade_field('filename', XMLDB_TYPE_CHAR, '255', true, false, ''),
        uckkarchive_upgrade_field('filesize', XMLDB_TYPE_INTEGER, '10', true, false, 0),
        uckkarchive_upgrade_field('mimetype', XMLDB_TYPE_CHAR, '100', true, false, ''),
        uckkarchive_upgrade_field('contenthash', XMLDB_TYPE_CHAR, '40', true, false, ''),
        uckkarchive_upgrade_field('iscurrent', XMLDB_TYPE_INTEGER, '1', true, false, 0),
        uckkarchive_upgrade_field('metadata', XMLDB_TYPE_TEXT),
        uckkarchive_upgrade_field('createdby', XMLDB_TYPE_INTEGER, '10', true, false, 0),
        uckkarchive_upgrade_field('modifiedby', XMLDB_TYPE_INTEGER, '10', true, false, 0),
        uckkarchive_upgrade_field('timecreated', XMLDB_TYPE_INTEGER, '10', true, false, 0),
        uckkarchive_upgrade_field('timemodified', XMLDB_TYPE_INTEGER, '10', true, false, 0),
    ], [
        new xmldb_key('primary', XMLDB_KEY_PRIMARY, ['id']),
        new xmldb_key('uuid', XMLDB_KEY_UNIQUE, ['uuid']),
    ], [
        new xmldb_index('mediaid', XMLDB_INDEX_NOTUNIQUE, ['mediaid']),
        new xmldb_index('media_version', XMLDB_INDEX_NOTUNIQUE, ['mediaid', 'versionnumber']),
        new xmldb_index('status', XMLDB_INDEX_NOTUNIQUE, ['status']),
        new xmldb_index('iscurrent', XMLDB_INDEX_NOTUNIQUE, ['iscurrent']),
    ]);

    uckkarchive_upgrade_create_table_if_missing('uckkarchive_media_source', [
        uckkarchive_upgrade_field('id', XMLDB_TYPE_INTEGER, '10', true, true),
        uckkarchive_upgrade_field('uuid', XMLDB_TYPE_CHAR, '36', true, false, ''),
        uckkarchive_upgrade_field('archiveid', XMLDB_TYPE_INTEGER, '10', true, false, 0),
        uckkarchive_upgrade_field('mediaid', XMLDB_TYPE_INTEGER, '10', true, false, 0),
        uckkarchive_upgrade_field('externalworkid', XMLDB_TYPE_INTEGER, '10', true, false, 0),
        uckkarchive_upgrade_field('sourcecomponent', XMLDB_TYPE_CHAR, '100', true, false, ''),
        uckkarchive_upgrade_field('sourceitemid', XMLDB_TYPE_INTEGER, '10', true, false, 0),
        uckkarchive_upgrade_field('sourcetype', XMLDB_TYPE_CHAR, '50', true, false, ''),
        uckkarchive_upgrade_field('sourceurl', XMLDB_TYPE_CHAR, '1333', false),
        uckkarchive_upgrade_field('title', XMLDB_TYPE_CHAR, '255', true, false, ''),
        uckkarchive_upgrade_field('citation', XMLDB_TYPE_TEXT),
        uckkarchive_upgrade_field('rightsstatus', XMLDB_TYPE_CHAR, '50', true, false, ''),
        uckkarchive_upgrade_field('metadata', XMLDB_TYPE_TEXT),
        uckkarchive_upgrade_field('createdby', XMLDB_TYPE_INTEGER, '10', true, false, 0),
        uckkarchive_upgrade_field('modifiedby', XMLDB_TYPE_INTEGER, '10', true, false, 0),
        uckkarchive_upgrade_field('timecreated', XMLDB_TYPE_INTEGER, '10', true, false, 0),
        uckkarchive_upgrade_field('timemodified', XMLDB_TYPE_INTEGER, '10', true, false, 0),
    ], [
        new xmldb_key('primary', XMLDB_KEY_PRIMARY, ['id']),
        new xmldb_key('uuid', XMLDB_KEY_UNIQUE, ['uuid']),
    ], [
        new xmldb_index('archiveid', XMLDB_INDEX_NOTUNIQUE, ['archiveid']),
        new xmldb_index('mediaid', XMLDB_INDEX_NOTUNIQUE, ['mediaid']),
        new xmldb_index('externalworkid', XMLDB_INDEX_NOTUNIQUE, ['externalworkid']),
    ]);

    uckkarchive_upgrade_create_table_if_missing('uckkarchive_media_collection', [
        uckkarchive_upgrade_field('id', XMLDB_TYPE_INTEGER, '10', true, true),
        uckkarchive_upgrade_field('uuid', XMLDB_TYPE_CHAR, '36', true, false, ''),
        uckkarchive_upgrade_field('archiveid', XMLDB_TYPE_INTEGER, '10', true, false, 0),
        uckkarchive_upgrade_field('courseid', XMLDB_TYPE_INTEGER, '10', true, false, 0),
        uckkarchive_upgrade_field('cmid', XMLDB_TYPE_INTEGER, '10', true, false, 0),
        uckkarchive_upgrade_field('contextid', XMLDB_TYPE_INTEGER, '10', true, false, 0),
        uckkarchive_upgrade_field('ownerid', XMLDB_TYPE_INTEGER, '10', true, false, 0),
        uckkarchive_upgrade_field('createdby', XMLDB_TYPE_INTEGER, '10', true, false, 0),
        uckkarchive_upgrade_field('modifiedby', XMLDB_TYPE_INTEGER, '10', true, false, 0),
        uckkarchive_upgrade_field('title', XMLDB_TYPE_CHAR, '255', true, false, ''),
        uckkarchive_upgrade_field('summary', XMLDB_TYPE_TEXT),
        uckkarchive_upgrade_field('description', XMLDB_TYPE_TEXT),
        uckkarchive_upgrade_field('status', XMLDB_TYPE_CHAR, '50', true, false, 'active'),
        uckkarchive_upgrade_field('visibility', XMLDB_TYPE_CHAR, '50', true, false, 'course'),
        uckkarchive_upgrade_field('audiencesuitability', XMLDB_TYPE_CHAR, '64', true, false, 'guided'),
        uckkarchive_upgrade_field('sortorder', XMLDB_TYPE_INTEGER, '10', true, false, 0),
        uckkarchive_upgrade_field('metadata', XMLDB_TYPE_TEXT),
        uckkarchive_upgrade_field('timecreated', XMLDB_TYPE_INTEGER, '10', true, false, 0),
        uckkarchive_upgrade_field('timemodified', XMLDB_TYPE_INTEGER, '10', true, false, 0),
    ], [
        new xmldb_key('primary', XMLDB_KEY_PRIMARY, ['id']),
        new xmldb_key('uuid', XMLDB_KEY_UNIQUE, ['uuid']),
    ], [
        new xmldb_index('archiveid', XMLDB_INDEX_NOTUNIQUE, ['archiveid']),
        new xmldb_index('status', XMLDB_INDEX_NOTUNIQUE, ['status']),
        new xmldb_index('visibility', XMLDB_INDEX_NOTUNIQUE, ['visibility']),
        new xmldb_index('ownerid', XMLDB_INDEX_NOTUNIQUE, ['ownerid']),
    ]);

    uckkarchive_upgrade_create_table_if_missing('uckkarchive_media_collection_item', [
        uckkarchive_upgrade_field('id', XMLDB_TYPE_INTEGER, '10', true, true),
        uckkarchive_upgrade_field('collectionid', XMLDB_TYPE_INTEGER, '10', true, false, 0),
        uckkarchive_upgrade_field('mediaid', XMLDB_TYPE_INTEGER, '10', true, false, 0),
        uckkarchive_upgrade_field('sortorder', XMLDB_TYPE_INTEGER, '10', true, false, 0),
        uckkarchive_upgrade_field('addedby', XMLDB_TYPE_INTEGER, '10', true, false, 0),
        uckkarchive_upgrade_field('timecreated', XMLDB_TYPE_INTEGER, '10', true, false, 0),
    ], [
        new xmldb_key('primary', XMLDB_KEY_PRIMARY, ['id']),
    ], [
        new xmldb_index('collectionid', XMLDB_INDEX_NOTUNIQUE, ['collectionid']),
        new xmldb_index('mediaid', XMLDB_INDEX_NOTUNIQUE, ['mediaid']),
        new xmldb_index('collection_media', XMLDB_INDEX_UNIQUE, ['collectionid', 'mediaid']),
    ]);

    uckkarchive_upgrade_create_table_if_missing('uckkarchive_media_relation', [
        uckkarchive_upgrade_field('id', XMLDB_TYPE_INTEGER, '10', true, true),
        uckkarchive_upgrade_field('uuid', XMLDB_TYPE_CHAR, '36', true, false, ''),
        uckkarchive_upgrade_field('archiveid', XMLDB_TYPE_INTEGER, '10', true, false, 0),
        uckkarchive_upgrade_field('mediaid', XMLDB_TYPE_INTEGER, '10', true, false, 0),
        uckkarchive_upgrade_field('sourcemediaid', XMLDB_TYPE_INTEGER, '10', true, false, 0),
        uckkarchive_upgrade_field('targetmediaid', XMLDB_TYPE_INTEGER, '10', true, false, 0),
        uckkarchive_upgrade_field('targetid', XMLDB_TYPE_INTEGER, '10', true, false, 0),
        uckkarchive_upgrade_field('targettype', XMLDB_TYPE_CHAR, '50', true, false, ''),
        uckkarchive_upgrade_field('relationtype', XMLDB_TYPE_CHAR, '50', true, false, ''),
        uckkarchive_upgrade_field('type', XMLDB_TYPE_CHAR, '50', true, false, ''),
        uckkarchive_upgrade_field('status', XMLDB_TYPE_CHAR, '50', true, false, 'active'),
        uckkarchive_upgrade_field('note', XMLDB_TYPE_TEXT),
        uckkarchive_upgrade_field('metadata', XMLDB_TYPE_TEXT),
        uckkarchive_upgrade_field('createdby', XMLDB_TYPE_INTEGER, '10', true, false, 0),
        uckkarchive_upgrade_field('modifiedby', XMLDB_TYPE_INTEGER, '10', true, false, 0),
        uckkarchive_upgrade_field('timecreated', XMLDB_TYPE_INTEGER, '10', true, false, 0),
        uckkarchive_upgrade_field('timemodified', XMLDB_TYPE_INTEGER, '10', true, false, 0),
    ], [
        new xmldb_key('primary', XMLDB_KEY_PRIMARY, ['id']),
        new xmldb_key('uuid', XMLDB_KEY_UNIQUE, ['uuid']),
    ], [
        new xmldb_index('archiveid', XMLDB_INDEX_NOTUNIQUE, ['archiveid']),
        new xmldb_index('mediaid', XMLDB_INDEX_NOTUNIQUE, ['mediaid']),
        new xmldb_index('sourcemediaid', XMLDB_INDEX_NOTUNIQUE, ['sourcemediaid']),
        new xmldb_index('targetmediaid', XMLDB_INDEX_NOTUNIQUE, ['targetmediaid']),
        new xmldb_index('relationtype', XMLDB_INDEX_NOTUNIQUE, ['relationtype']),
    ]);

    uckkarchive_upgrade_create_table_if_missing('uckkarchive_media_tag', [
        uckkarchive_upgrade_field('id', XMLDB_TYPE_INTEGER, '10', true, true),
        uckkarchive_upgrade_field('uuid', XMLDB_TYPE_CHAR, '36', true, false, ''),
        uckkarchive_upgrade_field('archiveid', XMLDB_TYPE_INTEGER, '10', true, false, 0),
        uckkarchive_upgrade_field('mediaid', XMLDB_TYPE_INTEGER, '10', true, false, 0),
        uckkarchive_upgrade_field('tag', XMLDB_TYPE_CHAR, '100', true, false, ''),
        uckkarchive_upgrade_field('tagkey', XMLDB_TYPE_CHAR, '100', true, false, ''),
        uckkarchive_upgrade_field('name', XMLDB_TYPE_CHAR, '255', true, false, ''),
        uckkarchive_upgrade_field('rawname', XMLDB_TYPE_CHAR, '255', true, false, ''),
        uckkarchive_upgrade_field('tagtype', XMLDB_TYPE_CHAR, '50', true, false, ''),
        uckkarchive_upgrade_field('type', XMLDB_TYPE_CHAR, '50', true, false, ''),
        uckkarchive_upgrade_field('createdby', XMLDB_TYPE_INTEGER, '10', true, false, 0),
        uckkarchive_upgrade_field('timecreated', XMLDB_TYPE_INTEGER, '10', true, false, 0),
        uckkarchive_upgrade_field('timemodified', XMLDB_TYPE_INTEGER, '10', true, false, 0),
    ], [
        new xmldb_key('primary', XMLDB_KEY_PRIMARY, ['id']),
        new xmldb_key('uuid', XMLDB_KEY_UNIQUE, ['uuid']),
    ], [
        new xmldb_index('archiveid', XMLDB_INDEX_NOTUNIQUE, ['archiveid']),
        new xmldb_index('mediaid', XMLDB_INDEX_NOTUNIQUE, ['mediaid']),
        new xmldb_index('tagkey', XMLDB_INDEX_NOTUNIQUE, ['tagkey']),
        new xmldb_index('tag', XMLDB_INDEX_NOTUNIQUE, ['tag']),
    ]);

    uckkarchive_upgrade_create_table_if_missing('uckkarchive_content_tag_set', [
        uckkarchive_upgrade_field('id', XMLDB_TYPE_INTEGER, '10', true, true),
        uckkarchive_upgrade_field('uuid', XMLDB_TYPE_CHAR, '36', true, false, ''),
        uckkarchive_upgrade_field('tagsetkey', XMLDB_TYPE_CHAR, '100', true, false, ''),
        uckkarchive_upgrade_field('setkey', XMLDB_TYPE_CHAR, '100', true, false, ''),
        uckkarchive_upgrade_field('label', XMLDB_TYPE_CHAR, '255', true, false, ''),
        uckkarchive_upgrade_field('description', XMLDB_TYPE_TEXT),
        uckkarchive_upgrade_field('status', XMLDB_TYPE_CHAR, '50', true, false, 'active'),
        uckkarchive_upgrade_field('version', XMLDB_TYPE_CHAR, '50', true, false, ''),
        uckkarchive_upgrade_field('sortorder', XMLDB_TYPE_INTEGER, '10', true, false, 0),
        uckkarchive_upgrade_field('metadata', XMLDB_TYPE_TEXT),
        uckkarchive_upgrade_field('timecreated', XMLDB_TYPE_INTEGER, '10', true, false, 0),
        uckkarchive_upgrade_field('timemodified', XMLDB_TYPE_INTEGER, '10', true, false, 0),
    ], [
        new xmldb_key('primary', XMLDB_KEY_PRIMARY, ['id']),
        new xmldb_key('uuid', XMLDB_KEY_UNIQUE, ['uuid']),
    ], [
        new xmldb_index('tagsetkey', XMLDB_INDEX_NOTUNIQUE, ['tagsetkey']),
        new xmldb_index('status', XMLDB_INDEX_NOTUNIQUE, ['status']),
    ]);

    uckkarchive_upgrade_create_table_if_missing('uckkarchive_content_tag', [
        uckkarchive_upgrade_field('id', XMLDB_TYPE_INTEGER, '10', true, true),
        uckkarchive_upgrade_field('uuid', XMLDB_TYPE_CHAR, '36', true, false, ''),
        uckkarchive_upgrade_field('tagsetid', XMLDB_TYPE_INTEGER, '10', true, false, 0),
        uckkarchive_upgrade_field('tagkey', XMLDB_TYPE_CHAR, '100', true, false, ''),
        uckkarchive_upgrade_field('label', XMLDB_TYPE_CHAR, '255', true, false, ''),
        uckkarchive_upgrade_field('category', XMLDB_TYPE_CHAR, '100', true, false, ''),
        uckkarchive_upgrade_field('description', XMLDB_TYPE_TEXT),
        uckkarchive_upgrade_field('defaultseverity', XMLDB_TYPE_CHAR, '50', true, false, 'notice'),
        uckkarchive_upgrade_field('severity', XMLDB_TYPE_CHAR, '50', true, false, 'notice'),
        uckkarchive_upgrade_field('defaultaudiencesuitability', XMLDB_TYPE_CHAR, '50', true, false, 'guided'),
        uckkarchive_upgrade_field('audiencesuitability', XMLDB_TYPE_CHAR, '50', true, false, 'guided'),
        uckkarchive_upgrade_field('defaultreviewstate', XMLDB_TYPE_CHAR, '50', true, false, 'pending_review'),
        uckkarchive_upgrade_field('iscultural', XMLDB_TYPE_INTEGER, '1', true, false, 0),
        uckkarchive_upgrade_field('restrictsbydefault', XMLDB_TYPE_INTEGER, '1', true, false, 0),
        uckkarchive_upgrade_field('requiresreview', XMLDB_TYPE_INTEGER, '1', true, false, 1),
        uckkarchive_upgrade_field('status', XMLDB_TYPE_CHAR, '50', true, false, 'active'),
        uckkarchive_upgrade_field('sortorder', XMLDB_TYPE_INTEGER, '10', true, false, 0),
        uckkarchive_upgrade_field('metadata', XMLDB_TYPE_TEXT),
        uckkarchive_upgrade_field('createdby', XMLDB_TYPE_INTEGER, '10', true, false, 0),
        uckkarchive_upgrade_field('modifiedby', XMLDB_TYPE_INTEGER, '10', true, false, 0),
        uckkarchive_upgrade_field('timecreated', XMLDB_TYPE_INTEGER, '10', true, false, 0),
        uckkarchive_upgrade_field('timemodified', XMLDB_TYPE_INTEGER, '10', true, false, 0),
    ], [
        new xmldb_key('primary', XMLDB_KEY_PRIMARY, ['id']),
        new xmldb_key('uuid', XMLDB_KEY_UNIQUE, ['uuid']),
    ], [
        new xmldb_index('tagsetid', XMLDB_INDEX_NOTUNIQUE, ['tagsetid']),
        new xmldb_index('tagkey', XMLDB_INDEX_NOTUNIQUE, ['tagkey']),
        new xmldb_index('category', XMLDB_INDEX_NOTUNIQUE, ['category']),
        new xmldb_index('status', XMLDB_INDEX_NOTUNIQUE, ['status']),
    ]);

    uckkarchive_upgrade_create_table_if_missing('uckkarchive_content_marker', [
        uckkarchive_upgrade_field('id', XMLDB_TYPE_INTEGER, '10', true, true),
        uckkarchive_upgrade_field('uuid', XMLDB_TYPE_CHAR, '36', true, false, ''),
        uckkarchive_upgrade_field('archiveid', XMLDB_TYPE_INTEGER, '10', true, false, 0),
        uckkarchive_upgrade_field('courseid', XMLDB_TYPE_INTEGER, '10', true, false, 0),
        uckkarchive_upgrade_field('cmid', XMLDB_TYPE_INTEGER, '10', true, false, 0),
        uckkarchive_upgrade_field('contextid', XMLDB_TYPE_INTEGER, '10', true, false, 0),
        uckkarchive_upgrade_field('mediaid', XMLDB_TYPE_INTEGER, '10', true, false, 0),
        uckkarchive_upgrade_field('externalworkid', XMLDB_TYPE_INTEGER, '10', true, false, 0),
        uckkarchive_upgrade_field('targettype', XMLDB_TYPE_CHAR, '50', true, false, ''),
        uckkarchive_upgrade_field('targetid', XMLDB_TYPE_INTEGER, '10', true, false, 0),
        uckkarchive_upgrade_field('userid', XMLDB_TYPE_INTEGER, '10', true, false, 0),
        uckkarchive_upgrade_field('createdby', XMLDB_TYPE_INTEGER, '10', true, false, 0),
        uckkarchive_upgrade_field('modifiedby', XMLDB_TYPE_INTEGER, '10', true, false, 0),
        uckkarchive_upgrade_field('tagkey', XMLDB_TYPE_CHAR, '100', true, false, ''),
        uckkarchive_upgrade_field('tag', XMLDB_TYPE_CHAR, '100', true, false, ''),
        uckkarchive_upgrade_field('contenttag', XMLDB_TYPE_CHAR, '100', true, false, ''),
        uckkarchive_upgrade_field('advisorytag', XMLDB_TYPE_CHAR, '100', true, false, ''),
        uckkarchive_upgrade_field('tagcategory', XMLDB_TYPE_CHAR, '100', true, false, ''),
        uckkarchive_upgrade_field('severity', XMLDB_TYPE_CHAR, '50', true, false, 'notice'),
        uckkarchive_upgrade_field('audiencesuitability', XMLDB_TYPE_CHAR, '50', true, false, 'guided'),
        uckkarchive_upgrade_field('reviewstate', XMLDB_TYPE_CHAR, '50', true, false, 'pending_review'),
        uckkarchive_upgrade_field('visibility', XMLDB_TYPE_CHAR, '50', true, false, 'course'),
        uckkarchive_upgrade_field('locatortype', XMLDB_TYPE_CHAR, '50', true, false, ''),
        uckkarchive_upgrade_field('locator', XMLDB_TYPE_CHAR, '255', true, false, ''),
        uckkarchive_upgrade_field('locatorvalue', XMLDB_TYPE_CHAR, '255', true, false, ''),
        uckkarchive_upgrade_field('locatorstart', XMLDB_TYPE_CHAR, '100', true, false, ''),
        uckkarchive_upgrade_field('locatorend', XMLDB_TYPE_CHAR, '100', true, false, ''),
        uckkarchive_upgrade_field('locatorlabel', XMLDB_TYPE_CHAR, '255', true, false, ''),
        uckkarchive_upgrade_field('description', XMLDB_TYPE_TEXT),
        uckkarchive_upgrade_field('note', XMLDB_TYPE_TEXT),
        uckkarchive_upgrade_field('culturalprotocol', XMLDB_TYPE_INTEGER, '1', true, false, 0),
        uckkarchive_upgrade_field('restricted', XMLDB_TYPE_INTEGER, '1', true, false, 0),
        uckkarchive_upgrade_field('requirescontext', XMLDB_TYPE_INTEGER, '1', true, false, 0),
        uckkarchive_upgrade_field('redacted', XMLDB_TYPE_INTEGER, '1', true, false, 0),
        uckkarchive_upgrade_field('metadata', XMLDB_TYPE_TEXT),
        uckkarchive_upgrade_field('timecreated', XMLDB_TYPE_INTEGER, '10', true, false, 0),
        uckkarchive_upgrade_field('timemodified', XMLDB_TYPE_INTEGER, '10', true, false, 0),
    ], [
        new xmldb_key('primary', XMLDB_KEY_PRIMARY, ['id']),
        new xmldb_key('uuid', XMLDB_KEY_UNIQUE, ['uuid']),
    ], [
        new xmldb_index('archiveid', XMLDB_INDEX_NOTUNIQUE, ['archiveid']),
        new xmldb_index('mediaid', XMLDB_INDEX_NOTUNIQUE, ['mediaid']),
        new xmldb_index('externalworkid', XMLDB_INDEX_NOTUNIQUE, ['externalworkid']),
        new xmldb_index('target', XMLDB_INDEX_NOTUNIQUE, ['targettype', 'targetid']),
        new xmldb_index('tagkey', XMLDB_INDEX_NOTUNIQUE, ['tagkey']),
        new xmldb_index('severity', XMLDB_INDEX_NOTUNIQUE, ['severity']),
        new xmldb_index('reviewstate', XMLDB_INDEX_NOTUNIQUE, ['reviewstate']),
        new xmldb_index('visibility', XMLDB_INDEX_NOTUNIQUE, ['visibility']),
    ]);

    uckkarchive_upgrade_create_table_if_missing('uckkarchive_content_review', [
        uckkarchive_upgrade_field('id', XMLDB_TYPE_INTEGER, '10', true, true),
        uckkarchive_upgrade_field('uuid', XMLDB_TYPE_CHAR, '36', true, false, ''),
        uckkarchive_upgrade_field('archiveid', XMLDB_TYPE_INTEGER, '10', true, false, 0),
        uckkarchive_upgrade_field('courseid', XMLDB_TYPE_INTEGER, '10', true, false, 0),
        uckkarchive_upgrade_field('cmid', XMLDB_TYPE_INTEGER, '10', true, false, 0),
        uckkarchive_upgrade_field('contextid', XMLDB_TYPE_INTEGER, '10', true, false, 0),
        uckkarchive_upgrade_field('markerid', XMLDB_TYPE_INTEGER, '10', true, false, 0),
        uckkarchive_upgrade_field('reviewerid', XMLDB_TYPE_INTEGER, '10', true, false, 0),
        uckkarchive_upgrade_field('userid', XMLDB_TYPE_INTEGER, '10', true, false, 0),
        uckkarchive_upgrade_field('createdby', XMLDB_TYPE_INTEGER, '10', true, false, 0),
        uckkarchive_upgrade_field('modifiedby', XMLDB_TYPE_INTEGER, '10', true, false, 0),
        uckkarchive_upgrade_field('state', XMLDB_TYPE_CHAR, '50', true, false, 'draft'),
        uckkarchive_upgrade_field('severity', XMLDB_TYPE_CHAR, '50', true, false, 'notice'),
        uckkarchive_upgrade_field('audiencesuitability', XMLDB_TYPE_CHAR, '50', true, false, 'guided'),
        uckkarchive_upgrade_field('rationale', XMLDB_TYPE_TEXT),
        uckkarchive_upgrade_field('reviewnote', XMLDB_TYPE_TEXT),
        uckkarchive_upgrade_field('culturalprotocol', XMLDB_TYPE_INTEGER, '1', true, false, 0),
        uckkarchive_upgrade_field('restricted', XMLDB_TYPE_INTEGER, '1', true, false, 0),
        uckkarchive_upgrade_field('metadata', XMLDB_TYPE_TEXT),
        uckkarchive_upgrade_field('timecreated', XMLDB_TYPE_INTEGER, '10', true, false, 0),
        uckkarchive_upgrade_field('timemodified', XMLDB_TYPE_INTEGER, '10', true, false, 0),
    ], [
        new xmldb_key('primary', XMLDB_KEY_PRIMARY, ['id']),
        new xmldb_key('uuid', XMLDB_KEY_UNIQUE, ['uuid']),
    ], [
        new xmldb_index('markerid', XMLDB_INDEX_NOTUNIQUE, ['markerid']),
        new xmldb_index('reviewerid', XMLDB_INDEX_NOTUNIQUE, ['reviewerid']),
        new xmldb_index('state', XMLDB_INDEX_NOTUNIQUE, ['state']),
    ]);

    uckkarchive_upgrade_create_table_if_missing('uckkarchive_external_work', [
        uckkarchive_upgrade_field('id', XMLDB_TYPE_INTEGER, '10', true, true),
        uckkarchive_upgrade_field('uuid', XMLDB_TYPE_CHAR, '36', true, false, ''),
        uckkarchive_upgrade_field('archiveid', XMLDB_TYPE_INTEGER, '10', true, false, 0),
        uckkarchive_upgrade_field('courseid', XMLDB_TYPE_INTEGER, '10', true, false, 0),
        uckkarchive_upgrade_field('cmid', XMLDB_TYPE_INTEGER, '10', true, false, 0),
        uckkarchive_upgrade_field('contextid', XMLDB_TYPE_INTEGER, '10', true, false, 0),
        uckkarchive_upgrade_field('ownerid', XMLDB_TYPE_INTEGER, '10', true, false, 0),
        uckkarchive_upgrade_field('createdby', XMLDB_TYPE_INTEGER, '10', true, false, 0),
        uckkarchive_upgrade_field('modifiedby', XMLDB_TYPE_INTEGER, '10', true, false, 0),
        uckkarchive_upgrade_field('worktype', XMLDB_TYPE_CHAR, '50', true, false, 'other'),
        uckkarchive_upgrade_field('status', XMLDB_TYPE_CHAR, '50', true, false, 'active'),
        uckkarchive_upgrade_field('visibility', XMLDB_TYPE_CHAR, '50', true, false, 'course'),
        uckkarchive_upgrade_field('audiencesuitability', XMLDB_TYPE_CHAR, '50', true, false, 'guided'),
        uckkarchive_upgrade_field('rightsstatus', XMLDB_TYPE_CHAR, '50', true, false, 'unknown'),
        uckkarchive_upgrade_field('title', XMLDB_TYPE_CHAR, '255', true, false, ''),
        uckkarchive_upgrade_field('subtitle', XMLDB_TYPE_CHAR, '255', true, false, ''),
        uckkarchive_upgrade_field('creator', XMLDB_TYPE_CHAR, '255', true, false, ''),
        uckkarchive_upgrade_field('publisher', XMLDB_TYPE_CHAR, '255', true, false, ''),
        uckkarchive_upgrade_field('publicationyear', XMLDB_TYPE_INTEGER, '10', true, false, 0),
        uckkarchive_upgrade_field('language', XMLDB_TYPE_CHAR, '20', true, false, ''),
        uckkarchive_upgrade_field('sourceurl', XMLDB_TYPE_CHAR, '1333', false),
        uckkarchive_upgrade_field('identifier', XMLDB_TYPE_CHAR, '255', true, false, ''),
        uckkarchive_upgrade_field('identifiertype', XMLDB_TYPE_CHAR, '50', true, false, ''),
        uckkarchive_upgrade_field('citation', XMLDB_TYPE_TEXT),
        uckkarchive_upgrade_field('rightsstatement', XMLDB_TYPE_TEXT),
        uckkarchive_upgrade_field('licensekey', XMLDB_TYPE_CHAR, '100', true, false, ''),
        uckkarchive_upgrade_field('sourcenote', XMLDB_TYPE_TEXT),
        uckkarchive_upgrade_field('teachingnote', XMLDB_TYPE_TEXT),
        uckkarchive_upgrade_field('culturalprotocolnote', XMLDB_TYPE_TEXT),
        uckkarchive_upgrade_field('description', XMLDB_TYPE_TEXT),
        uckkarchive_upgrade_field('provenanceid', XMLDB_TYPE_INTEGER, '10', true, false, 0),
        uckkarchive_upgrade_field('metadata', XMLDB_TYPE_TEXT),
        uckkarchive_upgrade_field('timecreated', XMLDB_TYPE_INTEGER, '10', true, false, 0),
        uckkarchive_upgrade_field('timemodified', XMLDB_TYPE_INTEGER, '10', true, false, 0),
    ], [
        new xmldb_key('primary', XMLDB_KEY_PRIMARY, ['id']),
        new xmldb_key('uuid', XMLDB_KEY_UNIQUE, ['uuid']),
    ], [
        new xmldb_index('archiveid', XMLDB_INDEX_NOTUNIQUE, ['archiveid']),
        new xmldb_index('worktype', XMLDB_INDEX_NOTUNIQUE, ['worktype']),
        new xmldb_index('status', XMLDB_INDEX_NOTUNIQUE, ['status']),
        new xmldb_index('visibility', XMLDB_INDEX_NOTUNIQUE, ['visibility']),
        new xmldb_index('ownerid', XMLDB_INDEX_NOTUNIQUE, ['ownerid']),
    ]);
}

/**
 * Add fields needed by media/advisory/export workflows to uckkarchive_export.
 *
 * @return void
 */
function uckkarchive_upgrade_extend_export_table(): void {
    $fields = [
        uckkarchive_upgrade_field('courseid', XMLDB_TYPE_INTEGER, '10', true, false, 0),
        uckkarchive_upgrade_field('cmid', XMLDB_TYPE_INTEGER, '10', true, false, 0),
        uckkarchive_upgrade_field('contextid', XMLDB_TYPE_INTEGER, '10', true, false, 0),
        uckkarchive_upgrade_field('userid', XMLDB_TYPE_INTEGER, '10', true, false, 0),
        uckkarchive_upgrade_field('exportscope', XMLDB_TYPE_CHAR, '50', true, false, 'archive_items'),
        uckkarchive_upgrade_field('exportformat', XMLDB_TYPE_CHAR, '50', true, false, 'json'),
        uckkarchive_upgrade_field('packagename', XMLDB_TYPE_CHAR, '255', true, false, ''),
        uckkarchive_upgrade_field('description', XMLDB_TYPE_TEXT),
        uckkarchive_upgrade_field('itemids', XMLDB_TYPE_TEXT),
        uckkarchive_upgrade_field('reason', XMLDB_TYPE_TEXT),
        uckkarchive_upgrade_field('auditnote', XMLDB_TYPE_TEXT),
        uckkarchive_upgrade_field('redactionlevel', XMLDB_TYPE_CHAR, '50', true, false, 'standard'),
        uckkarchive_upgrade_field('redacted', XMLDB_TYPE_INTEGER, '1', true, false, 0),
        uckkarchive_upgrade_field('includefiles', XMLDB_TYPE_INTEGER, '1', true, false, 0),
        uckkarchive_upgrade_field('includeproofs', XMLDB_TYPE_INTEGER, '1', true, false, 0),
        uckkarchive_upgrade_field('includeprovenance', XMLDB_TYPE_INTEGER, '1', true, false, 1),
        uckkarchive_upgrade_field('includeversions', XMLDB_TYPE_INTEGER, '1', true, false, 0),
        uckkarchive_upgrade_field('fileitemid', XMLDB_TYPE_INTEGER, '10', false, false, null),
        uckkarchive_upgrade_field('downloadcount', XMLDB_TYPE_INTEGER, '10', true, false, 0),
        uckkarchive_upgrade_field('lastdownloaded', XMLDB_TYPE_INTEGER, '10', false, false, null),
        uckkarchive_upgrade_field('timequeued', XMLDB_TYPE_INTEGER, '10', false, false, null),
        uckkarchive_upgrade_field('timestarted', XMLDB_TYPE_INTEGER, '10', false, false, null),
        uckkarchive_upgrade_field('timecompleted', XMLDB_TYPE_INTEGER, '10', false, false, null),
        uckkarchive_upgrade_field('error', XMLDB_TYPE_TEXT),
        uckkarchive_upgrade_field('visibility', XMLDB_TYPE_CHAR, '50', true, false, 'private'),
        uckkarchive_upgrade_field('versionno', XMLDB_TYPE_INTEGER, '10', true, false, 1),
        uckkarchive_upgrade_field('provenancehash', XMLDB_TYPE_CHAR, '64', true, false, ''),
        uckkarchive_upgrade_field('integritycaseid', XMLDB_TYPE_INTEGER, '10', false, false, null),
        uckkarchive_upgrade_field('metadata', XMLDB_TYPE_TEXT),
        uckkarchive_upgrade_field('createdby', XMLDB_TYPE_INTEGER, '10', true, false, 0),
        uckkarchive_upgrade_field('modifiedby', XMLDB_TYPE_INTEGER, '10', true, false, 0),
        uckkarchive_upgrade_field('timecreated', XMLDB_TYPE_INTEGER, '10', true, false, 0),
        uckkarchive_upgrade_field('timemodified', XMLDB_TYPE_INTEGER, '10', true, false, 0),
    ];

    foreach ($fields as $field) {
        uckkarchive_upgrade_add_field_if_missing('uckkarchive_export', $field);
    }
}

/**
 * Add canonical source and rights fields directly to media records.
 *
 * Early development upgrades created uckkarchive_media with only the legacy
 * source column. The media form and controller now persist sourcetype,
 * sourceurl, license, licensekey, rightsstatement, and rightsstatus directly on
 * uckkarchive_media. Without these columns, those submitted values are filtered
 * out before database insertion.
 *
 * @return void
 */
function uckkarchive_upgrade_extend_media_source_record_fields(): void {
    global $DB;

    $tablename = 'uckkarchive_media';

    $fields = [
        uckkarchive_upgrade_field('sourcetype', XMLDB_TYPE_CHAR, '64', false),
        uckkarchive_upgrade_field('sourceurl', XMLDB_TYPE_TEXT),
        uckkarchive_upgrade_field('license', XMLDB_TYPE_CHAR, '128', false),
        uckkarchive_upgrade_field('licensekey', XMLDB_TYPE_CHAR, '128', false),
        uckkarchive_upgrade_field('rightsstatement', XMLDB_TYPE_TEXT),
        uckkarchive_upgrade_field('rightsstatus', XMLDB_TYPE_CHAR, '64', true, false, 'unknown'),
    ];

    foreach ($fields as $field) {
        uckkarchive_upgrade_add_field_if_missing($tablename, $field);
    }

    if (!uckkarchive_upgrade_table_has_fields($tablename, ['source', 'sourcetype'])) {
        return;
    }

    $DB->execute(
        "UPDATE {uckkarchive_media}
            SET sourcetype = source
          WHERE (sourcetype IS NULL OR sourcetype = '')
            AND source IS NOT NULL
            AND source <> ''"
    );

    $DB->execute(
        "UPDATE {uckkarchive_media}
            SET source = sourcetype
          WHERE (source IS NULL OR source = '')
            AND sourcetype IS NOT NULL
            AND sourcetype <> ''"
    );

    if (uckkarchive_upgrade_table_has_fields($tablename, ['license', 'licensekey'])) {
        $DB->execute(
            "UPDATE {uckkarchive_media}
                SET licensekey = license
              WHERE (licensekey IS NULL OR licensekey = '')
                AND license IS NOT NULL
                AND license <> ''"
        );
    }

    if (uckkarchive_upgrade_table_has_fields($tablename, ['rightsstatus'])) {
        $DB->execute(
            "UPDATE {uckkarchive_media}
                SET rightsstatus = 'unknown'
              WHERE rightsstatus IS NULL
                 OR rightsstatus = ''"
        );
    }

    if (uckkarchive_upgrade_table_has_fields($tablename, ['sourceurl', 'metadata'])) {
        uckkarchive_upgrade_backfill_media_sourceurls_from_metadata();
    }
}

/**
 * Add the public-search exposure flag to media records.
 *
 * The public mediatheque repository filters media rows with:
 *
 *     (searchable IS NULL OR searchable = 1)
 *
 * Development databases created before the public explorer contract may be
 * missing this column, causing a DML read exception before any items can be
 * returned.
 *
 * @return void
 */
function uckkarchive_upgrade_add_media_searchable_field(): void {
    global $DB;

    $tablename = 'uckkarchive_media';

    uckkarchive_upgrade_add_field_if_missing(
        $tablename,
        uckkarchive_upgrade_field('searchable', XMLDB_TYPE_INTEGER, '1', true, false, 1)
    );

    if (!uckkarchive_upgrade_table_has_fields($tablename, ['searchable'])) {
        return;
    }

    $DB->execute(
        "UPDATE {uckkarchive_media}
            SET searchable = 1
          WHERE searchable IS NULL"
    );
}

/**
 * Add audience suitability to media collections.
 *
 * The public mediatheque repository filters media collections with:
 *
 *     c.audiencesuitability = 'general'
 *
 * Development databases created before the public explorer contract may be
 * missing this column, causing a DML read exception while building media cards.
 *
 * @return void
 */
function uckkarchive_upgrade_add_media_collection_audience_field(): void {
    global $DB;

    $tablename = 'uckkarchive_media_collection';

    uckkarchive_upgrade_add_field_if_missing(
        $tablename,
        uckkarchive_upgrade_field('audiencesuitability', XMLDB_TYPE_CHAR, '64', true, false, 'guided')
    );

    if (!uckkarchive_upgrade_table_has_fields($tablename, ['audiencesuitability'])) {
        return;
    }

    $DB->execute(
        "UPDATE {uckkarchive_media_collection}
            SET audiencesuitability = ?
          WHERE status = ?
            AND visibility = ?
            AND (audiencesuitability IS NULL OR audiencesuitability = '' OR audiencesuitability = ?)",
        ['general', 'active', 'public', 'guided']
    );

    $DB->execute(
        "UPDATE {uckkarchive_media_collection}
            SET audiencesuitability = ?
          WHERE audiencesuitability IS NULL
             OR audiencesuitability = ''",
        ['guided']
    );
}

/**
 * Backfill media source URLs from structured metadata when available.
 *
 * @return void
 */
function uckkarchive_upgrade_backfill_media_sourceurls_from_metadata(): void {
    global $DB;

    $recordset = $DB->get_recordset('uckkarchive_media', null, '', 'id, sourceurl, metadata');

    foreach ($recordset as $record) {
        if (!empty($record->sourceurl)) {
            continue;
        }

        if (empty($record->metadata) || !is_string($record->metadata)) {
            continue;
        }

        $metadata = json_decode($record->metadata, true);
        if (json_last_error() !== JSON_ERROR_NONE || !is_array($metadata)) {
            continue;
        }

        $sourceurl = uckkarchive_upgrade_extract_media_sourceurl_from_metadata($metadata);
        if ($sourceurl === '') {
            continue;
        }

        $DB->set_field('uckkarchive_media', 'sourceurl', $sourceurl, ['id' => (int)$record->id]);
    }

    $recordset->close();
}

/**
 * Extract a source URL from legacy media metadata.
 *
 * @param array<string,mixed> $metadata Metadata array.
 * @return string
 */
function uckkarchive_upgrade_extract_media_sourceurl_from_metadata(array $metadata): string {
    foreach (['sourceurl', 'externalurl', 'url'] as $field) {
        if (!empty($metadata[$field]) && is_string($metadata[$field])) {
            $url = clean_param((string)$metadata[$field], PARAM_URL);
            if ($url !== '') {
                return $url;
            }
        }
    }

    foreach (['citation', 'externalworkidentifier', 'externalworknote', 'notes_raw'] as $field) {
        if (empty($metadata[$field]) || !is_string($metadata[$field])) {
            continue;
        }

        if (preg_match('~https?://[^\s<>"\']+~u', (string)$metadata[$field], $matches)) {
            $url = clean_param($matches[0], PARAM_URL);
            if ($url !== '') {
                return $url;
            }
        }
    }

    return '';
}

/**
 * Repair indexes expected by the initial archive schema when upgrading from an
 * early development snapshot.
 *
 * @return void
 */
function uckkarchive_upgrade_repair_initial_indexes(): void {
    $indexes = [
        'uckkarchive_item' => [
            ['archiveid', ['archiveid']],
            ['status', ['status']],
            ['visibility', ['visibility']],
            ['source', ['sourcecomponent', 'sourceid']],
            ['userid', ['userid']],
            ['createdby', ['createdby']],
        ],
        'uckkarchive_kristal' => [
            ['archiveid', ['archiveid']],
            ['itemid', ['itemid']],
            ['proofid', ['proofid']],
            ['status', ['status']],
            ['visibility', ['visibility']],
            ['validation', ['validationstate']],
            ['source', ['sourcecomponent', 'sourceid']],
        ],
        'uckkarchive_proof' => [
            ['archiveid', ['archiveid']],
            ['itemid', ['itemid']],
            ['status', ['status']],
            ['visibility', ['visibility']],
            ['provenance', ['provenance']],
            ['userid', ['userid']],
        ],
        'uckkarchive_prov' => [
            ['archiveid', ['archiveid']],
            ['itemid', ['itemid']],
            ['source', ['sourcecomponent', 'sourceid']],
            ['provenance', ['provenance']],
        ],
        'uckkarchive_rev' => [
            ['archiveid', ['archiveid']],
            ['itemid', ['itemid']],
            ['version', ['versionno']],
            ['createdby', ['createdby']],
        ],
        'uckkarchive_export' => [
            ['archiveid', ['archiveid']],
            ['status', ['status']],
            ['visibility', ['visibility']],
            ['createdby', ['createdby']],
            ['userid', ['userid']],
            ['exportscope', ['exportscope']],
            ['exportformat', ['exportformat']],
        ],
    ];

    uckkarchive_upgrade_add_indexes($indexes);
}

/**
 * Repair indexes expected by media/advisory/external-work schema.
 *
 * @return void
 */
function uckkarchive_upgrade_repair_media_advisory_external_indexes(): void {
    $indexes = [
        'uckkarchive_media' => [
            ['archiveid', ['archiveid']],
            ['courseid', ['courseid']],
            ['cmid', ['cmid']],
            ['contextid', ['contextid']],
            ['status', ['status']],
            ['visibility', ['visibility']],
            ['mediatype', ['mediatype']],
            ['ownerid', ['ownerid']],
        ],
        'uckkarchive_media_version' => [
            ['mediaid', ['mediaid']],
            ['media_version', ['mediaid', 'versionnumber']],
            ['status', ['status']],
            ['iscurrent', ['iscurrent']],
        ],
        'uckkarchive_media_source' => [
            ['archiveid', ['archiveid']],
            ['mediaid', ['mediaid']],
            ['externalworkid', ['externalworkid']],
        ],
        'uckkarchive_media_collection' => [
            ['archiveid', ['archiveid']],
            ['status', ['status']],
            ['visibility', ['visibility']],
            ['ownerid', ['ownerid']],
        ],
        'uckkarchive_media_collection_item' => [
            ['collectionid', ['collectionid']],
            ['mediaid', ['mediaid']],
            ['collection_media', ['collectionid', 'mediaid'], XMLDB_INDEX_UNIQUE],
        ],
        'uckkarchive_media_relation' => [
            ['archiveid', ['archiveid']],
            ['mediaid', ['mediaid']],
            ['sourcemediaid', ['sourcemediaid']],
            ['targetmediaid', ['targetmediaid']],
            ['relationtype', ['relationtype']],
        ],
        'uckkarchive_media_tag' => [
            ['archiveid', ['archiveid']],
            ['mediaid', ['mediaid']],
            ['tagkey', ['tagkey']],
            ['tag', ['tag']],
        ],
        'uckkarchive_content_tag_set' => [
            ['tagsetkey', ['tagsetkey']],
            ['status', ['status']],
        ],
        'uckkarchive_content_tag' => [
            ['tagsetid', ['tagsetid']],
            ['tagkey', ['tagkey']],
            ['category', ['category']],
            ['status', ['status']],
        ],
        'uckkarchive_content_marker' => [
            ['archiveid', ['archiveid']],
            ['mediaid', ['mediaid']],
            ['externalworkid', ['externalworkid']],
            ['target', ['targettype', 'targetid']],
            ['tagkey', ['tagkey']],
            ['severity', ['severity']],
            ['reviewstate', ['reviewstate']],
            ['visibility', ['visibility']],
        ],
        'uckkarchive_content_review' => [
            ['markerid', ['markerid']],
            ['reviewerid', ['reviewerid']],
            ['state', ['state']],
        ],
        'uckkarchive_external_work' => [
            ['archiveid', ['archiveid']],
            ['worktype', ['worktype']],
            ['status', ['status']],
            ['visibility', ['visibility']],
            ['ownerid', ['ownerid']],
        ],
    ];

    uckkarchive_upgrade_add_indexes($indexes);
}

/**
 * Create a table if missing. If the table already exists, add missing fields
 * and indexes only.
 *
 * @param string $tablename Table name without braces.
 * @param xmldb_field[] $fields Fields.
 * @param xmldb_key[] $keys Keys.
 * @param xmldb_index[] $indexes Indexes.
 * @return void
 */
function uckkarchive_upgrade_create_table_if_missing(
    string $tablename,
    array $fields,
    array $keys = [],
    array $indexes = []
): void {
    global $DB;

    $dbman = $DB->get_manager();
    $table = new xmldb_table($tablename);

    foreach ($fields as $field) {
        $table->addField($field);
    }

    foreach ($keys as $key) {
        $table->addKey($key);
    }

    foreach ($indexes as $index) {
        $table->addIndex($index);
    }

    if (!$dbman->table_exists($table)) {
        $dbman->create_table($table);
        return;
    }

    foreach ($fields as $field) {
        uckkarchive_upgrade_add_field_if_missing($tablename, $field);
    }

    foreach ($indexes as $index) {
        uckkarchive_upgrade_add_index_if_possible($tablename, $index);
    }
}

/**
 * Build an XMLDB field.
 *
 * @param string $name Field name.
 * @param int $type XMLDB type.
 * @param string|null $precision Precision.
 * @param bool $notnull Not null.
 * @param bool $sequence Auto sequence.
 * @param mixed $default Default value.
 * @return xmldb_field
 */
function uckkarchive_upgrade_field(
    string $name,
    int $type,
    ?string $precision = null,
    bool $notnull = false,
    bool $sequence = false,
    mixed $default = null
): xmldb_field {
    return new xmldb_field($name, $type, $precision, null, $notnull, $sequence, $default);
}

/**
 * Add a field if missing.
 *
 * @param string $tablename Table name without braces.
 * @param xmldb_field $field Field definition.
 * @return void
 */
function uckkarchive_upgrade_add_field_if_missing(string $tablename, xmldb_field $field): void {
    global $DB;

    $dbman = $DB->get_manager();
    $table = new xmldb_table($tablename);

    if (!$dbman->table_exists($table)) {
        return;
    }

    if (!$dbman->field_exists($table, $field)) {
        $dbman->add_field($table, $field);
    }
}

/**
 * Add indexes for a grouped table specification.
 *
 * @param array<string, array<int, array<int, mixed>>> $indexes Index map.
 * @return void
 */
function uckkarchive_upgrade_add_indexes(array $indexes): void {
    foreach ($indexes as $tablename => $tableindexes) {
        foreach ($tableindexes as $indexspec) {
            $indexname = (string)$indexspec[0];
            $fields = $indexspec[1];
            $type = $indexspec[2] ?? XMLDB_INDEX_NOTUNIQUE;

            if (!is_array($fields)) {
                continue;
            }

            $index = new xmldb_index($indexname, $type, $fields);
            uckkarchive_upgrade_add_index_if_possible($tablename, $index);
        }
    }
}

/**
 * Add index if the table and all fields exist.
 *
 * @param string $tablename Table name without braces.
 * @param xmldb_index $index Index.
 * @return void
 */
function uckkarchive_upgrade_add_index_if_possible(string $tablename, xmldb_index $index): void {
    global $DB;

    $dbman = $DB->get_manager();
    $table = new xmldb_table($tablename);

    if (!$dbman->table_exists($table)) {
        return;
    }

    if (!uckkarchive_upgrade_table_has_fields($tablename, $index->getFields())) {
        return;
    }

    if (!$dbman->index_exists($table, $index)) {
        $dbman->add_index($table, $index);
    }
}

/**
 * Return whether a table contains all requested fields.
 *
 * @param string $tablename Table name without braces.
 * @param string[] $fields Field names.
 * @return bool
 */
function uckkarchive_upgrade_table_has_fields(string $tablename, array $fields): bool {
    global $DB;

    $table = new xmldb_table($tablename);
    $dbman = $DB->get_manager();

    if (!$dbman->table_exists($table)) {
        return false;
    }

    $columns = $DB->get_columns($tablename);

    foreach ($fields as $field) {
        if (!array_key_exists($field, $columns)) {
            return false;
        }
    }

    return true;
}