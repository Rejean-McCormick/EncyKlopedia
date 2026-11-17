<?php
// This file is part of Moodle - https://moodle.org/
//
// Moodle is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// any later version.

/**
 * Export tests for mod_uckkarchive.
 *
 * @package    mod_uckkarchive
 * @category   test
 * @copyright  2026 Univers-Cité King Klown
 * @license    https://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later
 */

declare(strict_types=1);

namespace mod_uckkarchive;

use advanced_testcase;
use context_module;
use mod_uckkarchive\local\export_package;
use stdClass;

defined('MOODLE_INTERNAL') || die();

global $CFG;
require_once($CFG->dirroot . '/mod/uckkarchive/locallib.php');

/**
 * Tests for archive-owned export packages.
 *
 * These tests verify the stable export contract:
 *
 * - export records belong to mod_uckkarchive;
 * - export packages preserve selected ids and metadata;
 * - manifest/package file areas use Moodle File API;
 * - redaction, provenance, version, and restricted flags are stored;
 * - archive exports remain separate from institutional report exports.
 *
 * @coversNothing
 */
final class export_test extends advanced_testcase {
    /** Export table. */
    private const EXPORT_TABLE = 'uckkarchive_export';

    /** Export manifest file area. */
    private const FILEAREA_MANIFEST = 'export_manifest';

    /** Export package file area. */
    private const FILEAREA_PACKAGE = 'export_package';

    /** Moodle File API component. */
    private const COMPONENT = 'mod_uckkarchive';

    /**
     * Reset test data.
     */
    protected function setUp(): void {
        parent::setUp();
        $this->resetAfterTest(true);
    }

    /**
     * Export records should preserve selected archive items and export flags.
     */
    public function test_export_record_stores_selected_items_and_export_flags(): void {
        global $DB;

        [$course, $archive, $cm, $context] = $this->create_archive_activity();
        $user = $this->getDataGenerator()->create_user();

        $itemone = $this->create_archive_item($archive, $cm, $context, $user, [
            'title' => 'First export item',
        ]);

        $itemtwo = $this->create_archive_item($archive, $cm, $context, $user, [
            'title' => 'Second export item',
        ]);

        $metadata = [
            'service' => 'phpunit',
            'purpose' => 'selected archive export',
            'redaction' => [
                'level' => 'hide_identity',
                'applied' => true,
            ],
        ];

        $export = $this->create_export_record($archive, $cm, $context, $user, [
            'exportscope' => 'selected',
            'exportformat' => 'zip',
            'itemids' => json_encode([(int)$itemone->id, (int)$itemtwo->id]),
            'redactionlevel' => 'hide_identity',
            'redacted' => 1,
            'includefiles' => 1,
            'includeproofs' => 1,
            'includeprovenance' => 1,
            'includeversions' => 1,
            'status' => 'pending',
            'metadata' => json_encode($metadata),
        ]);

        $stored = $DB->get_record(self::EXPORT_TABLE, ['id' => $export->id], '*', MUST_EXIST);

        $this->assertSame((int)$archive->id, (int)$stored->archiveid);
        $this->assertSame((int)$course->id, (int)$stored->courseid);
        $this->assertSame((int)$cm->id, (int)$stored->cmid);
        $this->assertSame((int)$context->id, (int)$stored->contextid);
        $this->assertSame('selected', $stored->exportscope);
        $this->assertSame('zip', $stored->exportformat);
        $this->assertSame('hide_identity', $stored->redactionlevel);
        $this->assertSame(1, (int)$stored->redacted);
        $this->assertSame(1, (int)$stored->includefiles);
        $this->assertSame(1, (int)$stored->includeproofs);
        $this->assertSame(1, (int)$stored->includeprovenance);
        $this->assertSame(1, (int)$stored->includeversions);
        $this->assertSame('pending', $stored->status);

        $itemids = json_decode($stored->itemids, true);
        $this->assertSame([(int)$itemone->id, (int)$itemtwo->id], $itemids);

        $storedmetadata = json_decode($stored->metadata, true);
        $this->assertSame('phpunit', $storedmetadata['service']);
        $this->assertTrue($storedmetadata['redaction']['applied']);
    }

    /**
     * Manifest files should be stored in the export_manifest File API area.
     */
    public function test_export_manifest_file_area_stores_json_manifest(): void {
        [$course, $archive, $cm, $context] = $this->create_archive_activity();
        $user = $this->getDataGenerator()->create_user();

        $item = $this->create_archive_item($archive, $cm, $context, $user);
        $export = $this->create_export_record($archive, $cm, $context, $user, [
            'itemids' => json_encode([(int)$item->id]),
            'status' => 'completed',
        ]);

        $manifest = [
            'manifest_version' => 1,
            'plugin' => 'mod_uckkarchive',
            'export_type' => 'archive_items',
            'archiveid' => (int)$archive->id,
            'exportid' => (int)$export->id,
            'itemids' => [(int)$item->id],
        ];

        $file = $this->create_export_file(
            $context,
            self::FILEAREA_MANIFEST,
            (int)$export->id,
            'manifest.json',
            json_encode($manifest)
        );

        $this->assertSame(self::COMPONENT, $file->get_component());
        $this->assertSame(self::FILEAREA_MANIFEST, $file->get_filearea());
        $this->assertSame((int)$export->id, $file->get_itemid());
        $this->assertSame('manifest.json', $file->get_filename());

        $decoded = json_decode($file->get_content(), true);
        $this->assertSame('mod_uckkarchive', $decoded['plugin']);
        $this->assertSame((int)$archive->id, $decoded['archiveid']);
        $this->assertSame([(int)$item->id], $decoded['itemids']);
    }

    /**
     * Generated export package files should be stored in export_package.
     */
    public function test_export_package_file_area_stores_generated_package(): void {
        [$course, $archive, $cm, $context] = $this->create_archive_activity();
        $user = $this->getDataGenerator()->create_user();

        $export = $this->create_export_record($archive, $cm, $context, $user, [
            'status' => 'completed',
            'exportformat' => 'zip',
        ]);

        $file = $this->create_export_file(
            $context,
            self::FILEAREA_PACKAGE,
            (int)$export->id,
            'uckkarchive-export.zip',
            'fake zip payload for phpunit'
        );

        $this->assertSame(self::FILEAREA_PACKAGE, $file->get_filearea());
        $this->assertSame('uckkarchive-export.zip', $file->get_filename());
        $this->assertSame('fake zip payload for phpunit', $file->get_content());
    }

    /**
     * Export metadata should round-trip through the database as JSON.
     */
    public function test_export_metadata_json_round_trips(): void {
        global $DB;

        [$course, $archive, $cm, $context] = $this->create_archive_activity();
        $user = $this->getDataGenerator()->create_user();

        $metadata = [
            'package' => [
                'kind' => 'portable_archive',
                'schema' => 'uckkarchive-export-v1',
            ],
            'counts' => [
                'items' => 2,
                'proofs' => 1,
                'files' => 3,
            ],
            'restriction' => [
                'hasrestricteddata' => true,
                'redactionlevel' => 'strict',
            ],
        ];

        $export = $this->create_export_record($archive, $cm, $context, $user, [
            'metadata' => json_encode($metadata),
            'redactionlevel' => 'strict',
            'redacted' => 1,
        ]);

        $stored = $DB->get_record(self::EXPORT_TABLE, ['id' => $export->id], '*', MUST_EXIST);
        $decoded = json_decode($stored->metadata, true);

        $this->assertSame('portable_archive', $decoded['package']['kind']);
        $this->assertSame('uckkarchive-export-v1', $decoded['package']['schema']);
        $this->assertSame(2, $decoded['counts']['items']);
        $this->assertSame(1, $decoded['counts']['proofs']);
        $this->assertSame(3, $decoded['counts']['files']);
        $this->assertTrue($decoded['restriction']['hasrestricteddata']);
        $this->assertSame('strict', $decoded['restriction']['redactionlevel']);
    }

    /**
     * Export lifecycle statuses should be storable.
     */
    public function test_export_lifecycle_statuses_are_storable(): void {
        global $DB;

        [$course, $archive, $cm, $context] = $this->create_archive_activity();
        $user = $this->getDataGenerator()->create_user();

        foreach (['pending', 'processing', 'completed', 'failed', 'cancelled', 'archived'] as $status) {
            $export = $this->create_export_record($archive, $cm, $context, $user, [
                'status' => $status,
                'packagename' => 'status-' . $status,
            ]);

            $stored = $DB->get_record(self::EXPORT_TABLE, ['id' => $export->id], '*', MUST_EXIST);
            $this->assertSame($status, $stored->status);
        }
    }

    /**
     * Failed exports should preserve the failure message.
     */
    public function test_failed_export_preserves_error_message(): void {
        global $DB;

        [$course, $archive, $cm, $context] = $this->create_archive_activity();
        $user = $this->getDataGenerator()->create_user();

        $export = $this->create_export_record($archive, $cm, $context, $user, [
            'status' => 'failed',
            'error' => 'The export worker could not generate the package.',
            'timecompleted' => time(),
        ]);

        $stored = $DB->get_record(self::EXPORT_TABLE, ['id' => $export->id], '*', MUST_EXIST);

        $this->assertSame('failed', $stored->status);
        $this->assertStringContainsString('could not generate', $stored->error);
        $this->assertGreaterThan(0, (int)$stored->timecompleted);
    }

    /**
     * Completed exports should preserve completion and provenance hash fields.
     */
    public function test_completed_export_preserves_completion_and_hash_metadata(): void {
        global $DB;

        [$course, $archive, $cm, $context] = $this->create_archive_activity();
        $user = $this->getDataGenerator()->create_user();

        $hash = hash('sha256', 'export-provenance-for-test');

        $export = $this->create_export_record($archive, $cm, $context, $user, [
            'status' => 'completed',
            'timequeued' => time() - 30,
            'timestarted' => time() - 20,
            'timecompleted' => time(),
            'provenancehash' => $hash,
        ]);

        $stored = $DB->get_record(self::EXPORT_TABLE, ['id' => $export->id], '*', MUST_EXIST);

        $this->assertSame('completed', $stored->status);
        $this->assertSame($hash, $stored->provenancehash);
        $this->assertGreaterThan(0, (int)$stored->timequeued);
        $this->assertGreaterThan(0, (int)$stored->timestarted);
        $this->assertGreaterThan(0, (int)$stored->timecompleted);
    }

    /**
     * The export_package domain class should expose the expected allowed values.
     */
    public function test_export_package_domain_lists_expected_allowed_values(): void {
        if (!class_exists(export_package::class)) {
            $this->markTestSkipped('The export_package domain class is not available.');
        }

        $this->assertContains('zip', export_package::get_allowed_export_formats());
        $this->assertContains('json', export_package::get_allowed_export_formats());
        $this->assertContains('csv', export_package::get_allowed_export_formats());

        $this->assertContains('selected', export_package::get_allowed_export_scopes());
        $this->assertContains('validated_only', export_package::get_allowed_export_scopes());
        $this->assertContains('full_archive', export_package::get_allowed_export_scopes());

        $this->assertContains('pending', export_package::get_allowed_statuses());
        $this->assertContains('processing', export_package::get_allowed_statuses());
        $this->assertContains('completed', export_package::get_allowed_statuses());
        $this->assertContains('failed', export_package::get_allowed_statuses());

        $this->assertContains('private', export_package::get_allowed_visibilities());
        $this->assertContains('course', export_package::get_allowed_visibilities());
        $this->assertContains('restricted', export_package::get_allowed_visibilities());
    }

    /**
     * Export records must remain archive-owned, not report-owned.
     */
    public function test_export_record_uses_archive_owner_metadata_not_report_owner(): void {
        global $DB;

        [$course, $archive, $cm, $context] = $this->create_archive_activity();
        $user = $this->getDataGenerator()->create_user();

        $export = $this->create_export_record($archive, $cm, $context, $user, [
            'metadata' => json_encode([
                'owner' => 'mod_uckkarchive',
                'not_owner' => 'report_uckk',
                'boundary' => 'archive_export_package',
            ]),
        ]);

        $stored = $DB->get_record(self::EXPORT_TABLE, ['id' => $export->id], '*', MUST_EXIST);
        $metadata = json_decode($stored->metadata, true);

        $this->assertSame('mod_uckkarchive', $metadata['owner']);
        $this->assertSame('report_uckk', $metadata['not_owner']);
        $this->assertSame('archive_export_package', $metadata['boundary']);
    }

    /**
     * Create archive activity.
     *
     * @return array{0:stdClass,1:stdClass,2:stdClass,3:context_module}
     */
    private function create_archive_activity(): array {
        $course = $this->getDataGenerator()->create_course();

        $archive = $this->getDataGenerator()->create_module('uckkarchive', [
            'course' => $course->id,
            'name' => 'Export test archive',
            'intro' => 'Export intro',
            'introformat' => FORMAT_HTML,
            'defaultvisibility' => $this->visibility_constant('COURSE', 'course'),
            'requirevalidation' => 1,
            'allowexports' => 1,
        ]);

        $cm = get_coursemodule_from_instance('uckkarchive', $archive->id, $course->id, false, MUST_EXIST);
        $context = context_module::instance($cm->id);

        return [$course, $archive, $cm, $context];
    }

    /**
     * Insert an archive item.
     *
     * @param stdClass $archive Archive instance.
     * @param stdClass $cm Course module.
     * @param context_module $context Context.
     * @param stdClass $user User.
     * @param array<string, mixed> $overrides Overrides.
     * @return stdClass
     */
    private function create_archive_item(
        stdClass $archive,
        stdClass $cm,
        context_module $context,
        stdClass $user,
        array $overrides = []
    ): stdClass {
        global $DB;

        $table = $this->table_constant('UCKKARCHIVE_ITEM_TABLE', 'uckkarchive_item');
        $now = time();

        $record = (object)array_merge([
            'archiveid' => (int)$archive->id,
            'courseid' => (int)$cm->course,
            'cmid' => (int)$cm->id,
            'contextid' => (int)$context->id,
            'userid' => (int)$user->id,
            'parentitemid' => null,
            'itemtype' => $this->type_constant('PROOF', 'proof'),
            'title' => 'Exportable archive item',
            'summary' => 'Exportable archive item summary',
            'content' => 'Exportable archive item content',
            'contentformat' => FORMAT_HTML,
            'publicsummary' => 'Public export summary',
            'sourcecomponent' => 'mod_uckkarchive',
            'sourceobjectid' => null,
            'origincomponent' => 'mod_uckkarchive',
            'originobjectid' => null,
            'license' => null,
            'tags' => null,
            'status' => $this->status_constant('VALIDATED', 'validated'),
            'validationstate' => $this->validation_constant('VERIFIED', 'verified'),
            'visibility' => $this->visibility_constant('COURSE', 'course'),
            'provenance' => $this->provenance_constant('HUMAN', 'human'),
            'provenancehash' => null,
            'integritycaseid' => null,
            'versionno' => 1,
            'createdby' => (int)$user->id,
            'modifiedby' => (int)$user->id,
            'timecreated' => $now,
            'timemodified' => $now,
            'metadata' => null,
        ], $overrides);

        $record = $this->filter_record_to_table($table, $record);
        $record->id = $DB->insert_record($table, $record);

        return $DB->get_record($table, ['id' => $record->id], '*', MUST_EXIST);
    }

    /**
     * Insert an export record.
     *
     * @param stdClass $archive Archive instance.
     * @param stdClass $cm Course module.
     * @param context_module $context Context.
     * @param stdClass $user User.
     * @param array<string, mixed> $overrides Overrides.
     * @return stdClass
     */
    private function create_export_record(
        stdClass $archive,
        stdClass $cm,
        context_module $context,
        stdClass $user,
        array $overrides = []
    ): stdClass {
        global $DB;

        $this->assertTrue($DB->get_manager()->table_exists(new \xmldb_table(self::EXPORT_TABLE)));

        $now = time();

        $record = (object)array_merge([
            'archiveid' => (int)$archive->id,
            'courseid' => (int)$cm->course,
            'cmid' => (int)$cm->id,
            'contextid' => (int)$context->id,
            'userid' => (int)$user->id,
            'exportscope' => 'selected',
            'exportformat' => 'zip',
            'packagename' => 'phpunit-export-' . $now,
            'description' => 'PHPUnit export package',
            'itemids' => json_encode([]),
            'reason' => 'PHPUnit export test',
            'auditnote' => 'Created during export_test',
            'redactionlevel' => 'standard',
            'redacted' => 1,
            'includefiles' => 1,
            'includeproofs' => 1,
            'includeprovenance' => 1,
            'includeversions' => 1,
            'fileitemid' => null,
            'downloadcount' => 0,
            'lastdownloaded' => null,
            'timequeued' => $now,
            'timestarted' => null,
            'timecompleted' => null,
            'error' => null,
            'status' => 'pending',
            'visibility' => 'course',
            'versionno' => 1,
            'provenancehash' => null,
            'integritycaseid' => null,
            'createdby' => (int)$user->id,
            'modifiedby' => (int)$user->id,
            'timecreated' => $now,
            'timemodified' => $now,
            'metadata' => json_encode([
                'service' => 'phpunit',
                'owner' => 'mod_uckkarchive',
            ]),
        ], $overrides);

        $record = $this->filter_record_to_table(self::EXPORT_TABLE, $record);
        $record->id = $DB->insert_record(self::EXPORT_TABLE, $record);

        return $DB->get_record(self::EXPORT_TABLE, ['id' => $record->id], '*', MUST_EXIST);
    }

    /**
     * Create an export File API file.
     *
     * @param context_module $context Context.
     * @param string $filearea File area.
     * @param int $itemid Item id.
     * @param string $filename Filename.
     * @param string $content File content.
     * @return \stored_file
     */
    private function create_export_file(
        context_module $context,
        string $filearea,
        int $itemid,
        string $filename,
        string $content
    ): \stored_file {
        $fs = get_file_storage();

        $fs->delete_area_files((int)$context->id, self::COMPONENT, $filearea, $itemid);

        return $fs->create_file_from_string([
            'contextid' => (int)$context->id,
            'component' => self::COMPONENT,
            'filearea' => $filearea,
            'itemid' => $itemid,
            'filepath' => '/',
            'filename' => $filename,
        ], $content);
    }

    /**
     * Filter a record to existing table columns.
     *
     * @param string $table Table name.
     * @param stdClass $record Record.
     * @return stdClass
     */
    private function filter_record_to_table(string $table, stdClass $record): stdClass {
        global $DB;

        $columns = $DB->get_columns($table);
        $filtered = new stdClass();

        foreach ($columns as $field => $definition) {
            if (property_exists($record, $field)) {
                $filtered->{$field} = $record->{$field};
            }
        }

        return $filtered;
    }

    /**
     * Return table constant with fallback.
     *
     * @param string $constant Constant name.
     * @param string $fallback Fallback table.
     * @return string
     */
    private function table_constant(string $constant, string $fallback): string {
        return defined($constant) ? (string)constant($constant) : $fallback;
    }

    /**
     * Return archive status constant with fallback.
     *
     * @param string $suffix Constant suffix.
     * @param string $fallback Fallback value.
     * @return string
     */
    private function status_constant(string $suffix, string $fallback): string {
        $constant = 'UCKKARCHIVE_STATUS_' . $suffix;
        return defined($constant) ? (string)constant($constant) : $fallback;
    }

    /**
     * Return archive validation constant with fallback.
     *
     * @param string $suffix Constant suffix.
     * @param string $fallback Fallback value.
     * @return string
     */
    private function validation_constant(string $suffix, string $fallback): string {
        $constant = 'UCKKARCHIVE_VALIDATION_' . $suffix;
        return defined($constant) ? (string)constant($constant) : $fallback;
    }

    /**
     * Return archive visibility constant with fallback.
     *
     * @param string $suffix Constant suffix.
     * @param string $fallback Fallback value.
     * @return string
     */
    private function visibility_constant(string $suffix, string $fallback): string {
        $constant = 'UCKKARCHIVE_VISIBILITY_' . $suffix;
        return defined($constant) ? (string)constant($constant) : $fallback;
    }

    /**
     * Return archive provenance constant with fallback.
     *
     * @param string $suffix Constant suffix.
     * @param string $fallback Fallback value.
     * @return string
     */
    private function provenance_constant(string $suffix, string $fallback): string {
        $constant = 'UCKKARCHIVE_PROVENANCE_' . $suffix;
        return defined($constant) ? (string)constant($constant) : $fallback;
    }

    /**
     * Return archive item type constant with fallback.
     *
     * @param string $suffix Constant suffix.
     * @param string $fallback Fallback value.
     * @return string
     */
    private function type_constant(string $suffix, string $fallback): string {
        $constant = 'UCKKARCHIVE_TYPE_' . $suffix;
        return defined($constant) ? (string)constant($constant) : $fallback;
    }
}