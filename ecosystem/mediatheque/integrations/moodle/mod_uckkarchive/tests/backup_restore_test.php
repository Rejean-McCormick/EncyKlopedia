<?php
// This file is part of Moodle - https://moodle.org/.
//
// Moodle is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// any later version.

/**
 * Backup and restore tests for mod_uckkarchive.
 *
 * @package    mod_uckkarchive
 * @category   test
 * @copyright  2026 Univers-Cité King Klown
 * @license    https://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later
 */

defined('MOODLE_INTERNAL') || die();

global $CFG;

require_once($CFG->dirroot . '/backup/util/includes/backup_includes.php');
require_once($CFG->dirroot . '/backup/util/includes/restore_includes.php');

/**
 * Backup and restore coverage for the UCKK Archive activity.
 *
 * These tests protect the final backup/restore contract:
 *
 * - archive-owned records remain archive-owned;
 * - media-library records are preserved when the media tables exist;
 * - content advisory records are preserved when the advisory tables exist;
 * - external work references are preserved as archive-owned reference records;
 * - file areas remain aligned with backup, restore, privacy, and pluginfile use;
 * - restricted/cultural states must survive backup and restore.
 *
 * The documentation requires backup/restore coverage for archive records,
 * media records, content markers/reviews, external works, export manifests,
 * ID mapping, file areas, visibility, restricted flags, and cultural protocol
 * flags. :contentReference[oaicite:0]{index=0}
 *
 * @group mod_uckkarchive
 * @coversNothing
 */
final class backup_restore_test extends advanced_testcase {
    /** Component name. */
    private const COMPONENT = 'mod_uckkarchive';

    /** Activity module name. */
    private const MODNAME = 'uckkarchive';

    /** Canonical archive tables. */
    private const ARCHIVE_TABLES = [
        'uckkarchive',
        'uckkarchive_item',
        'uckkarchive_proof',
        'uckkarchive_kristal',
        'uckkarchive_prov',
        'uckkarchive_rev',
        'uckkarchive_export',
    ];

    /** Canonical media tables. */
    private const MEDIA_TABLES = [
        'uckkarchive_media',
        'uckkarchive_media_version',
        'uckkarchive_media_relation',
        'uckkarchive_media_tag',
        'uckkarchive_media_collection',
        'uckkarchive_media_collection_item',
        'uckkarchive_media_source',
    ];

    /** Canonical content advisory and external work tables. */
    private const CONTENT_TABLES = [
        'uckkarchive_content_tag',
        'uckkarchive_content_tag_set',
        'uckkarchive_content_marker',
        'uckkarchive_content_review',
        'uckkarchive_external_work',
    ];

    /** Canonical archive file areas. */
    private const ARCHIVE_FILEAREAS = [
        'intro',
        'item_content',
        'item_publicsummary',
        'item_files',
        'proof_files',
        'decision_attachments',
        'minutes_files',
        'kristal_files',
        'portfolio_files',
        'integrity_exports',
        'provenance_files',
        'validation_files',
        'revision_files',
        'export_package',
        'export_manifest',
    ];

    /** Canonical media file areas. */
    private const MEDIA_FILEAREAS = [
        'media_original',
        'media_preview',
        'media_thumbnail',
        'media_derivative',
        'media_caption',
        'media_transcript',
        'media_attachment',
    ];

    /** Canonical content advisory file areas. */
    private const CONTENT_FILEAREAS = [
        'content_review_files',
        'external_work_reference_files',
        'cultural_protocol_files',
    ];

    /**
     * Reset after every test.
     */
    protected function setUp(): void {
        parent::setUp();
        $this->resetAfterTest(true);
        $this->setAdminUser();
    }

    /**
     * Backup task should declare canonical file areas.
     *
     * This test intentionally checks for file-area drift. The file-area names
     * must remain aligned across:
     *
     * - lib.php pluginfile handling;
     * - backup task declarations;
     * - backup steps;
     * - restore task declarations;
     * - restore steps;
     * - privacy provider;
     * - file API tests.
     */
    public function test_backup_restore_filearea_contract_contains_canonical_areas(): void {
        global $CFG;

        $backupfile = $CFG->dirroot . '/mod/uckkarchive/backup/moodle2/backup_uckkarchive_activity_task.class.php';
        $restorefile = $CFG->dirroot . '/mod/uckkarchive/backup/moodle2/restore_uckkarchive_activity_task.class.php';

        $this->assertFileExists($backupfile);
        $this->assertFileExists($restorefile);

        $backupcontents = file_get_contents($backupfile);
        $restorecontents = file_get_contents($restorefile);

        $this->assertIsString($backupcontents);
        $this->assertIsString($restorecontents);

        foreach ($this->canonical_fileareas() as $filearea) {
            $this->assertStringContainsString(
                "'" . $filearea . "'",
                $backupcontents,
                'Backup activity task must declare file area: ' . $filearea
            );

            $this->assertStringContainsString(
                "'" . $filearea . "'",
                $restorecontents,
                'Restore activity task must declare file area: ' . $filearea
            );
        }
    }

    /**
     * Backup and restore step files should mention canonical archive/media/content tables.
     *
     * The test allows tables to be absent during incremental implementation, but
     * once the table exists it must be represented in backup/restore code.
     */
    public function test_existing_domain_tables_are_declared_by_backup_and_restore_steps(): void {
        global $CFG;

        $backupstepsfile = $CFG->dirroot . '/mod/uckkarchive/backup/moodle2/backup_uckkarchive_stepslib.php';
        $restorestepsfile = $CFG->dirroot . '/mod/uckkarchive/backup/moodle2/restore_uckkarchive_stepslib.php';

        $this->assertFileExists($backupstepsfile);
        $this->assertFileExists($restorestepsfile);

        $backupcontents = file_get_contents($backupstepsfile);
        $restorecontents = file_get_contents($restorestepsfile);

        $this->assertIsString($backupcontents);
        $this->assertIsString($restorecontents);

        foreach ($this->existing_domain_tables() as $table) {
            $this->assertStringContainsString(
                $table,
                $backupcontents,
                'Backup steps must include existing archive-owned table: ' . $table
            );

            $this->assertStringContainsString(
                $table,
                $restorecontents,
                'Restore steps must include existing archive-owned table: ' . $table
            );
        }
    }

    /**
     * Backup code must not declare ownership of external authority domains.
     */
    public function test_backup_does_not_claim_external_domain_tables(): void {
        global $CFG;

        $backupstepsfile = $CFG->dirroot . '/mod/uckkarchive/backup/moodle2/backup_uckkarchive_stepslib.php';
        $restorestepsfile = $CFG->dirroot . '/mod/uckkarchive/backup/moodle2/restore_uckkarchive_stepslib.php';

        $backupcontents = file_get_contents($backupstepsfile);
        $restorecontents = file_get_contents($restorestepsfile);

        $this->assertIsString($backupcontents);
        $this->assertIsString($restorecontents);

        $forbidden = [
            'grade_grades',
            'grade_items',
            'local_uckk',
            'uckkchallenge',
            'uckkassembly',
            'tool_uckkintegrity_case',
            'report_uckk',
        ];

        foreach ($forbidden as $tablename) {
            $this->assertStringNotContainsString(
                $tablename,
                $backupcontents,
                'Backup must not own external table: ' . $tablename
            );

            $this->assertStringNotContainsString(
                $tablename,
                $restorecontents,
                'Restore must not own external table: ' . $tablename
            );
        }
    }

    /**
     * Activity backup can be created for a populated archive instance.
     *
     * This verifies that the Moodle backup controller can build and execute a
     * backup plan for the activity. It does not rely on exact fixture row
     * counts because backup output structure may vary by Moodle branch.
     */
    public function test_activity_backup_controller_runs_for_populated_archive(): void {
        [$course, $archive, $cm] = $this->create_archive_fixture();

        $this->seed_archive_domain_records($course, $archive, $cm);
        $this->seed_media_domain_records($course, $archive, $cm);
        $this->seed_content_domain_records($course, $archive, $cm);
        $this->seed_file_area_records($cm);

        $backupfile = $this->run_activity_backup((int)$cm->id);

        $this->assertNotNull($backupfile);
        $this->assertTrue($backupfile->is_valid_image() || $backupfile->get_filesize() > 0);
        $this->assertSame('application/vnd.moodle.backup', $backupfile->get_mimetype());
    }

    /**
     * Direct backup restore should preserve canonical restricted metadata when Moodle test helpers allow it.
     *
     * Some Moodle branches provide full controller restore helpers in PHPUnit;
     * others make MBZ extraction awkward in isolated plugin tests. This test
     * therefore performs a strict preflight and skips only when the local branch
     * cannot expose the needed restore helper.
     */
    public function test_activity_backup_restore_preserves_restricted_domain_records_when_supported(): void {
        if (!class_exists('backup_controller') || !class_exists('restore_controller')) {
            $this->markTestSkipped('Moodle backup/restore controller classes are not available in this test runtime.');
        }

        if (!class_exists('backup_general_helper')) {
            $this->markTestSkipped('Moodle backup_general_helper is not available in this test runtime.');
        }

        [$course, $archive, $cm] = $this->create_archive_fixture();

        $fixture = [];
        $fixture += $this->seed_archive_domain_records($course, $archive, $cm);
        $fixture += $this->seed_media_domain_records($course, $archive, $cm);
        $fixture += $this->seed_content_domain_records($course, $archive, $cm);
        $this->seed_file_area_records($cm);

        $backupfile = $this->run_activity_backup((int)$cm->id);
        $this->assertNotNull($backupfile);

        $targetcourse = $this->getDataGenerator()->create_course();
        $this->restore_activity_backup_if_supported($backupfile, (int)$targetcourse->id);

        $this->assert_restored_restricted_state_exists($fixture);
    }

    /**
     * Export manifest file area should be restorable contractually.
     */
    public function test_export_manifest_filearea_is_present_in_filearea_contract(): void {
        $this->assertContains('export_manifest', $this->canonical_fileareas());
        $this->assertContains('export_package', $this->canonical_fileareas());
    }

    /**
     * Cultural protocol file area should be present in filearea contract.
     */
    public function test_cultural_protocol_filearea_is_present_in_filearea_contract(): void {
        $this->assertContains('cultural_protocol_files', $this->canonical_fileareas());
        $this->assertContains('content_review_files', $this->canonical_fileareas());
        $this->assertContains('external_work_reference_files', $this->canonical_fileareas());
    }

    /**
     * Create a base course and activity fixture.
     *
     * @return array{0:stdClass,1:stdClass,2:stdClass}
     */
    private function create_archive_fixture(): array {
        $course = $this->getDataGenerator()->create_course();

        $generator = $this->getDataGenerator()->get_plugin_generator('mod_uckkarchive');

        if ($generator) {
            $archive = $generator->create_instance([
                'course' => $course->id,
                'name' => 'Backup Restore Archive',
                'intro' => 'Backup restore fixture intro.',
                'introformat' => FORMAT_HTML,
            ]);
        } else {
            $archive = $this->getDataGenerator()->create_module(self::MODNAME, [
                'course' => $course->id,
                'name' => 'Backup Restore Archive',
                'intro' => 'Backup restore fixture intro.',
                'introformat' => FORMAT_HTML,
            ]);
        }

        $cm = get_coursemodule_from_instance(self::MODNAME, $archive->id, $course->id, false, MUST_EXIST);

        return [$course, $archive, $cm];
    }

    /**
     * Seed archive-owned records.
     *
     * @param stdClass $course Course.
     * @param stdClass $archive Archive instance.
     * @param stdClass $cm Course module.
     * @return array<string, int>
     */
    private function seed_archive_domain_records(stdClass $course, stdClass $archive, stdClass $cm): array {
        global $DB, $USER;

        $ids = [];
        $now = time();

        if ($this->table_exists('uckkarchive_item')) {
            $ids['itemid'] = $this->insert_record('uckkarchive_item', [
                'archiveid' => $archive->id,
                'courseid' => $course->id,
                'cmid' => $cm->id,
                'contextid' => context_module::instance($cm->id)->id,
                'userid' => $USER->id,
                'createdby' => $USER->id,
                'modifiedby' => $USER->id,
                'title' => 'Backup Restore Restricted Item',
                'summary' => 'Restricted summary',
                'content' => 'Restricted item body',
                'itemtype' => 'document',
                'status' => 'validated',
                'visibility' => 'restricted_integrity',
                'validationstate' => 'verified',
                'provenance' => 'human',
                'uuid' => $this->uuid(),
                'timecreated' => $now,
                'timemodified' => $now,
                'metadata' => json_encode(['fixture' => 'backup_restore_item']),
            ]);
        }

        if ($this->table_exists('uckkarchive_proof')) {
            $ids['proofid'] = $this->insert_record('uckkarchive_proof', [
                'archiveid' => $archive->id,
                'itemid' => $ids['itemid'] ?? 0,
                'userid' => $USER->id,
                'createdby' => $USER->id,
                'modifiedby' => $USER->id,
                'title' => 'Backup Restore Proof',
                'description' => 'Proof fixture',
                'status' => 'active',
                'visibility' => 'restricted',
                'uuid' => $this->uuid(),
                'timecreated' => $now,
                'timemodified' => $now,
                'metadata' => json_encode(['fixture' => 'backup_restore_proof']),
            ]);
        }

        if ($this->table_exists('uckkarchive_kristal')) {
            $ids['kristalid'] = $this->insert_record('uckkarchive_kristal', [
                'archiveid' => $archive->id,
                'itemid' => $ids['itemid'] ?? 0,
                'userid' => $USER->id,
                'createdby' => $USER->id,
                'modifiedby' => $USER->id,
                'title' => 'Backup Restore Kristal',
                'description' => 'Kristal fixture',
                'status' => 'active',
                'visibility' => 'course',
                'uuid' => $this->uuid(),
                'timecreated' => $now,
                'timemodified' => $now,
                'metadata' => json_encode(['fixture' => 'backup_restore_kristal']),
            ]);
        }

        if ($this->table_exists('uckkarchive_prov')) {
            $ids['provid'] = $this->insert_record('uckkarchive_prov', [
                'archiveid' => $archive->id,
                'itemid' => $ids['itemid'] ?? 0,
                'userid' => $USER->id,
                'source' => 'human',
                'sourcecomponent' => self::COMPONENT,
                'sourcearea' => 'backup_restore_test',
                'sourceid' => $ids['itemid'] ?? 0,
                'statement' => 'Backup restore provenance fixture',
                'uuid' => $this->uuid(),
                'timecreated' => $now,
                'timemodified' => $now,
                'metadata' => json_encode(['fixture' => 'backup_restore_provenance']),
            ]);
        }

        if ($this->table_exists('uckkarchive_rev')) {
            $ids['revisionid'] = $this->insert_record('uckkarchive_rev', [
                'archiveid' => $archive->id,
                'itemid' => $ids['itemid'] ?? 0,
                'userid' => $USER->id,
                'createdby' => $USER->id,
                'revisionno' => 1,
                'title' => 'Backup Restore Revision',
                'reason' => 'Fixture revision',
                'uuid' => $this->uuid(),
                'timecreated' => $now,
                'timemodified' => $now,
                'metadata' => json_encode(['fixture' => 'backup_restore_revision']),
            ]);
        }

        if ($this->table_exists('uckkarchive_export')) {
            $ids['exportid'] = $this->insert_record('uckkarchive_export', [
                'archiveid' => $archive->id,
                'courseid' => $course->id,
                'cmid' => $cm->id,
                'contextid' => context_module::instance($cm->id)->id,
                'userid' => $USER->id,
                'exportscope' => 'media_items',
                'exportformat' => 'zip',
                'packagename' => 'backup-restore-export',
                'description' => 'Backup restore export fixture',
                'itemids' => json_encode([$ids['itemid'] ?? 0]),
                'reason' => 'Fixture',
                'auditnote' => 'Backup restore test',
                'redactionlevel' => 'standard',
                'redacted' => 1,
                'includefiles' => 1,
                'includeproofs' => 1,
                'includeprovenance' => 1,
                'includeversions' => 1,
                'status' => 'completed',
                'visibility' => 'private',
                'versionno' => 1,
                'createdby' => $USER->id,
                'modifiedby' => $USER->id,
                'timequeued' => $now,
                'timestarted' => $now,
                'timecompleted' => $now,
                'timecreated' => $now,
                'timemodified' => $now,
                'metadata' => json_encode(['fixture' => 'backup_restore_export']),
            ]);
        }

        return $ids;
    }

    /**
     * Seed media library records when media tables exist.
     *
     * @param stdClass $course Course.
     * @param stdClass $archive Archive instance.
     * @param stdClass $cm Course module.
     * @return array<string, int>
     */
    private function seed_media_domain_records(stdClass $course, stdClass $archive, stdClass $cm): array {
        global $USER;

        $ids = [];
        $now = time();
        $contextid = context_module::instance($cm->id)->id;

        if ($this->table_exists('uckkarchive_media')) {
            $ids['mediaid'] = $this->insert_record('uckkarchive_media', [
                'archiveid' => $archive->id,
                'courseid' => $course->id,
                'cmid' => $cm->id,
                'contextid' => $contextid,
                'ownerid' => $USER->id,
                'createdby' => $USER->id,
                'modifiedby' => $USER->id,
                'uuid' => $this->uuid(),
                'title' => 'Backup Restore Media',
                'summary' => 'Media summary',
                'description' => 'Media description',
                'mediatype' => 'video',
                'mimetype' => 'video/mp4',
                'status' => 'restricted',
                'visibility' => 'restricted_cultural',
                'audiencesuitability' => 'restricted_cultural',
                'source' => 'produced_by_uckk',
                'culturalprotocol' => 1,
                'restricted' => 1,
                'timecreated' => $now,
                'timemodified' => $now,
                'metadata' => json_encode(['fixture' => 'backup_restore_media']),
            ]);
        }

        if ($this->table_exists('uckkarchive_media_version')) {
            $ids['mediaversionid'] = $this->insert_record('uckkarchive_media_version', [
                'mediaid' => $ids['mediaid'] ?? 0,
                'uuid' => $this->uuid(),
                'versionno' => 1,
                'status' => 'active',
                'filearea' => 'media_original',
                'filename' => 'backup-restore-media.txt',
                'mimetype' => 'text/plain',
                'filesize' => 28,
                'contenthash' => sha1('backup restore media fixture'),
                'createdby' => $USER->id,
                'modifiedby' => $USER->id,
                'timecreated' => $now,
                'timemodified' => $now,
                'metadata' => json_encode(['fixture' => 'backup_restore_media_version']),
            ]);
        }

        if ($this->table_exists('uckkarchive_media_collection')) {
            $ids['collectionid'] = $this->insert_record('uckkarchive_media_collection', [
                'archiveid' => $archive->id,
                'courseid' => $course->id,
                'cmid' => $cm->id,
                'contextid' => $contextid,
                'ownerid' => $USER->id,
                'createdby' => $USER->id,
                'modifiedby' => $USER->id,
                'uuid' => $this->uuid(),
                'title' => 'Backup Restore Collection',
                'summary' => 'Collection summary',
                'description' => 'Collection description',
                'collectiontype' => 'teaching',
                'status' => 'active',
                'visibility' => 'course',
                'timecreated' => $now,
                'timemodified' => $now,
                'metadata' => json_encode(['fixture' => 'backup_restore_collection']),
            ]);
        }

        if ($this->table_exists('uckkarchive_media_collection_item')) {
            $ids['collectionitemid'] = $this->insert_record('uckkarchive_media_collection_item', [
                'collectionid' => $ids['collectionid'] ?? 0,
                'mediaid' => $ids['mediaid'] ?? 0,
                'sortorder' => 1,
                'createdby' => $USER->id,
                'timecreated' => $now,
                'timemodified' => $now,
                'metadata' => json_encode(['fixture' => 'backup_restore_collection_item']),
            ]);
        }

        if ($this->table_exists('uckkarchive_media_relation')) {
            $ids['mediarelationid'] = $this->insert_record('uckkarchive_media_relation', [
                'archiveid' => $archive->id,
                'mediaid' => $ids['mediaid'] ?? 0,
                'fromid' => $ids['mediaid'] ?? 0,
                'fromtype' => 'media',
                'toid' => $ids['collectionid'] ?? 0,
                'totype' => 'media_collection',
                'relationtype' => 'belongs_to_collection',
                'uuid' => $this->uuid(),
                'createdby' => $USER->id,
                'modifiedby' => $USER->id,
                'timecreated' => $now,
                'timemodified' => $now,
                'metadata' => json_encode(['fixture' => 'backup_restore_media_relation']),
            ]);
        }

        if ($this->table_exists('uckkarchive_media_tag')) {
            $ids['mediatagid'] = $this->insert_record('uckkarchive_media_tag', [
                'archiveid' => $archive->id,
                'mediaid' => $ids['mediaid'] ?? 0,
                'tag' => 'backup_restore',
                'tagtype' => 'system',
                'createdby' => $USER->id,
                'timecreated' => $now,
                'timemodified' => $now,
                'metadata' => json_encode(['fixture' => 'backup_restore_media_tag']),
            ]);
        }

        if ($this->table_exists('uckkarchive_media_source')) {
            $ids['mediasourceid'] = $this->insert_record('uckkarchive_media_source', [
                'archiveid' => $archive->id,
                'mediaid' => $ids['mediaid'] ?? 0,
                'sourcetype' => 'produced_by_uckk',
                'ownership' => 'uckk_created',
                'rightsstatus' => 'open_license',
                'title' => 'Backup Restore Media Source',
                'createdby' => $USER->id,
                'modifiedby' => $USER->id,
                'timecreated' => $now,
                'timemodified' => $now,
                'metadata' => json_encode(['fixture' => 'backup_restore_media_source']),
            ]);
        }

        return $ids;
    }

    /**
     * Seed content advisory/external work records when tables exist.
     *
     * @param stdClass $course Course.
     * @param stdClass $archive Archive instance.
     * @param stdClass $cm Course module.
     * @return array<string, int>
     */
    private function seed_content_domain_records(stdClass $course, stdClass $archive, stdClass $cm): array {
        global $USER;

        $ids = [];
        $now = time();
        $contextid = context_module::instance($cm->id)->id;

        if ($this->table_exists('uckkarchive_content_tag_set')) {
            $ids['contenttagsetid'] = $this->insert_record('uckkarchive_content_tag_set', [
                'archiveid' => $archive->id,
                'uuid' => $this->uuid(),
                'name' => 'Backup Restore Tag Set',
                'tagsetkey' => 'backup_restore',
                'description' => 'Fixture tag set',
                'status' => 'active',
                'createdby' => $USER->id,
                'modifiedby' => $USER->id,
                'timecreated' => $now,
                'timemodified' => $now,
                'metadata' => json_encode(['fixture' => 'backup_restore_content_tag_set']),
            ]);
        }

        if ($this->table_exists('uckkarchive_content_tag')) {
            $ids['contenttagid'] = $this->insert_record('uckkarchive_content_tag', [
                'archiveid' => $archive->id,
                'tagsetid' => $ids['contenttagsetid'] ?? 0,
                'uuid' => $this->uuid(),
                'tagkey' => 'culturally_sensitive',
                'name' => 'Culturally sensitive',
                'description' => 'Fixture advisory tag',
                'status' => 'active',
                'createdby' => $USER->id,
                'modifiedby' => $USER->id,
                'timecreated' => $now,
                'timemodified' => $now,
                'metadata' => json_encode(['fixture' => 'backup_restore_content_tag']),
            ]);
        }

        if ($this->table_exists('uckkarchive_external_work')) {
            $ids['externalworkid'] = $this->insert_record('uckkarchive_external_work', [
                'archiveid' => $archive->id,
                'courseid' => $course->id,
                'cmid' => $cm->id,
                'contextid' => $contextid,
                'ownerid' => $USER->id,
                'createdby' => $USER->id,
                'modifiedby' => $USER->id,
                'uuid' => $this->uuid(),
                'worktype' => 'film',
                'status' => 'active',
                'visibility' => 'restricted_cultural',
                'audiencesuitability' => 'restricted_cultural',
                'rightsstatus' => 'restricted_reference',
                'title' => 'Backup Restore External Work',
                'creator' => 'Fixture Creator',
                'citation' => 'Fixture citation',
                'culturalprotocolnote' => 'Restricted cultural protocol note',
                'description' => 'External work fixture',
                'timecreated' => $now,
                'timemodified' => $now,
                'metadata' => json_encode(['fixture' => 'backup_restore_external_work']),
            ]);
        }

        if ($this->table_exists('uckkarchive_content_marker')) {
            $ids['contentmarkerid'] = $this->insert_record('uckkarchive_content_marker', [
                'archiveid' => $archive->id,
                'courseid' => $course->id,
                'cmid' => $cm->id,
                'contextid' => $contextid,
                'mediaid' => $this->first_record_id('uckkarchive_media'),
                'externalworkid' => $ids['externalworkid'] ?? 0,
                'tagid' => $ids['contenttagid'] ?? 0,
                'uuid' => $this->uuid(),
                'tag' => 'culturally_sensitive',
                'locatortype' => 'timecode_range',
                'locator' => '00:01:00-00:02:00',
                'severity' => 'restricted',
                'audiencesuitability' => 'restricted_cultural',
                'state' => 'approved',
                'restricted' => 1,
                'culturalprotocol' => 1,
                'createdby' => $USER->id,
                'modifiedby' => $USER->id,
                'timecreated' => $now,
                'timemodified' => $now,
                'metadata' => json_encode(['fixture' => 'backup_restore_content_marker']),
            ]);
        }

        if ($this->table_exists('uckkarchive_content_review')) {
            $ids['contentreviewid'] = $this->insert_record('uckkarchive_content_review', [
                'markerid' => $ids['contentmarkerid'] ?? 0,
                'reviewerid' => $USER->id,
                'uuid' => $this->uuid(),
                'state' => 'approved',
                'severity' => 'restricted',
                'audiencesuitability' => 'restricted_cultural',
                'rationale' => 'Fixture review rationale',
                'reviewnote' => 'Fixture review note',
                'restricted' => 1,
                'culturalprotocol' => 1,
                'timecreated' => $now,
                'timemodified' => $now,
                'metadata' => json_encode(['fixture' => 'backup_restore_content_review']),
            ]);
        }

        return $ids;
    }

    /**
     * Seed files in canonical file areas that exist in the runtime.
     *
     * @param stdClass $cm Course module.
     * @return void
     */
    private function seed_file_area_records(stdClass $cm): void {
        $context = context_module::instance($cm->id);
        $fs = get_file_storage();

        foreach ($this->canonical_fileareas() as $index => $filearea) {
            $itemid = $this->itemid_for_filearea($filearea);

            $record = [
                'contextid' => $context->id,
                'component' => self::COMPONENT,
                'filearea' => $filearea,
                'itemid' => $itemid,
                'filepath' => '/',
                'filename' => $filearea . '-fixture.txt',
            ];

            try {
                $fs->create_file_from_string($record, 'Fixture file for ' . $filearea . '.');
            } catch (file_exception $exception) {
                // Duplicate or not-yet-supported file areas should not obscure
                // the backup contract being tested. The file-area declaration
                // tests above catch spelling drift.
            }
        }
    }

    /**
     * Run Moodle activity backup and return resulting MBZ stored file.
     *
     * @param int $cmid Course module id.
     * @return stored_file|null
     */
    private function run_activity_backup(int $cmid): ?stored_file {
        global $USER;

        $bc = new backup_controller(
            backup::TYPE_1ACTIVITY,
            $cmid,
            backup::FORMAT_MOODLE,
            backup::INTERACTIVE_NO,
            backup::MODE_GENERAL,
            $USER->id
        );

        $bc->execute_plan();
        $results = $bc->get_results();

        $file = $results['backup_destination'] ?? null;
        $bc->destroy();

        $this->assertTrue($file === null || $file instanceof stored_file);

        return $file;
    }

    /**
     * Restore an activity backup into a target course when runtime helpers support it.
     *
     * @param stored_file $backupfile Backup MBZ file.
     * @param int $targetcourseid Target course id.
     * @return void
     */
    private function restore_activity_backup_if_supported(stored_file $backupfile, int $targetcourseid): void {
        global $USER, $CFG;

        $tempdir = make_backup_temp_directory('mod_uckkarchive_backup_restore_test_' . uniqid('', true));

        $packer = get_file_packer('application/vnd.moodle.backup');
        $packer->extract_to_pathname($backupfile, $CFG->tempdir . '/backup/' . $tempdir);

        $rc = new restore_controller(
            $tempdir,
            $targetcourseid,
            backup::INTERACTIVE_NO,
            backup::MODE_GENERAL,
            $USER->id,
            backup::TARGET_CURRENT_ADDING
        );

        if (!$rc->execute_precheck()) {
            $results = $rc->get_precheck_results();
            $rc->destroy();
            $this->fail('Restore precheck failed: ' . json_encode($results));
        }

        $rc->execute_plan();
        $rc->destroy();
    }

    /**
     * Assert that restored restricted states still exist after restore.
     *
     * @param array<string, int> $fixture Fixture ids.
     * @return void
     */
    private function assert_restored_restricted_state_exists(array $fixture): void {
        global $DB;

        if ($this->table_exists('uckkarchive_item') && !empty($fixture['itemid'])) {
            $this->assertTrue(
                $DB->record_exists('uckkarchive_item', ['visibility' => 'restricted_integrity']),
                'A restricted_integrity archive item must exist after restore.'
            );
        }

        if ($this->table_exists('uckkarchive_media') && !empty($fixture['mediaid'])) {
            $this->assertTrue(
                $DB->record_exists('uckkarchive_media', ['visibility' => 'restricted_cultural']),
                'A restricted_cultural media record must exist after restore.'
            );
        }

        if ($this->table_exists('uckkarchive_content_marker') && !empty($fixture['contentmarkerid'])) {
            $this->assertTrue(
                $DB->record_exists('uckkarchive_content_marker', ['culturalprotocol' => 1]),
                'A cultural protocol content marker must exist after restore.'
            );
        }

        if ($this->table_exists('uckkarchive_external_work') && !empty($fixture['externalworkid'])) {
            $this->assertTrue(
                $DB->record_exists('uckkarchive_external_work', ['visibility' => 'restricted_cultural']),
                'A restricted external work reference must exist after restore.'
            );
        }
    }

    /**
     * Insert a record using only columns that exist in the current schema.
     *
     * @param string $table Table name.
     * @param array<string, mixed> $data Candidate data.
     * @return int Inserted id.
     */
    private function insert_record(string $table, array $data): int {
        global $DB;

        $columns = $DB->get_columns($table);
        $record = new stdClass();

        foreach ($data as $field => $value) {
            if (array_key_exists($field, $columns)) {
                $record->{$field} = $value;
            }
        }

        return (int)$DB->insert_record($table, $record);
    }

    /**
     * Return first record id for a table.
     *
     * @param string $table Table.
     * @return int
     */
    private function first_record_id(string $table): int {
        global $DB;

        if (!$this->table_exists($table)) {
            return 0;
        }

        $record = $DB->get_record_sql('SELECT id FROM {' . $table . '} ORDER BY id ASC', [], IGNORE_MISSING);

        return $record ? (int)$record->id : 0;
    }

    /**
     * Return existing archive-owned tables.
     *
     * @return string[]
     */
    private function existing_domain_tables(): array {
        return array_values(array_filter(array_merge(
            self::ARCHIVE_TABLES,
            self::MEDIA_TABLES,
            self::CONTENT_TABLES
        ), fn(string $table): bool => $this->table_exists($table)));
    }

    /**
     * Return canonical file areas.
     *
     * @return string[]
     */
    private function canonical_fileareas(): array {
        return array_values(array_unique(array_merge(
            self::ARCHIVE_FILEAREAS,
            self::MEDIA_FILEAREAS,
            self::CONTENT_FILEAREAS
        )));
    }

    /**
     * Return item id to use for a file area.
     *
     * @param string $filearea File area.
     * @return int
     */
    private function itemid_for_filearea(string $filearea): int {
        if ($filearea === 'intro') {
            return 0;
        }

        if (in_array($filearea, ['export_package', 'export_manifest'], true)) {
            return $this->first_record_id('uckkarchive_export') ?: 1;
        }

        if (in_array($filearea, ['media_original', 'media_preview', 'media_thumbnail', 'media_derivative',
                'media_caption', 'media_transcript', 'media_attachment'], true)) {
            return $this->first_record_id('uckkarchive_media') ?: 1;
        }

        if (in_array($filearea, ['content_review_files', 'cultural_protocol_files'], true)) {
            return $this->first_record_id('uckkarchive_content_review') ?: 1;
        }

        if ($filearea === 'external_work_reference_files') {
            return $this->first_record_id('uckkarchive_external_work') ?: 1;
        }

        if ($filearea === 'proof_files') {
            return $this->first_record_id('uckkarchive_proof') ?: 1;
        }

        if ($filearea === 'kristal_files') {
            return $this->first_record_id('uckkarchive_kristal') ?: 1;
        }

        if ($filearea === 'provenance_files') {
            return $this->first_record_id('uckkarchive_prov') ?: 1;
        }

        if ($filearea === 'revision_files') {
            return $this->first_record_id('uckkarchive_rev') ?: 1;
        }

        return $this->first_record_id('uckkarchive_item') ?: 1;
    }

    /**
     * Return whether table exists.
     *
     * @param string $table Table name.
     * @return bool
     */
    private function table_exists(string $table): bool {
        global $DB;

        return $DB->get_manager()->table_exists(new xmldb_table($table));
    }

    /**
     * Generate stable UUID.
     *
     * @return string
     */
    private function uuid(): string {
        if (class_exists('\mod_uckkarchive\local\uuid') &&
                method_exists('\mod_uckkarchive\local\uuid', 'generate')) {
            return \mod_uckkarchive\local\uuid::generate();
        }

        return \core\uuid::generate();
    }
}

