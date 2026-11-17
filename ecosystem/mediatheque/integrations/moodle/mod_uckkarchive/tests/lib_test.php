<?php
// This file is part of Moodle - https://moodle.org/
//
// Moodle is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// any later version.

/**
 * Tests for UCKK Archive lib.php callbacks.
 *
 * @package    mod_uckkarchive
 * @category   test
 * @copyright  2026 Univers-Cité King Klown
 * @license    https://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later
 */

declare(strict_types=1);

namespace mod_uckkarchive;

use cached_cm_info;
use context_module;
use stdClass;

defined('MOODLE_INTERNAL') || die();

global $CFG;
require_once($CFG->dirroot . '/mod/uckkarchive/lib.php');

/**
 * Unit tests for UCKK Archive activity callbacks.
 */
final class lib_test extends \advanced_testcase {
    /**
     * Reset database state before each test.
     */
    protected function setUp(): void {
        parent::setUp();
        $this->resetAfterTest(true);
    }

    /**
     * The activity declares the expected Moodle feature support.
     */
    public function test_supports_expected_features(): void {
        $this->assertTrue(uckkarchive_supports(FEATURE_MOD_INTRO));
        $this->assertTrue(uckkarchive_supports(FEATURE_SHOW_DESCRIPTION));
        $this->assertTrue(uckkarchive_supports(FEATURE_COMPLETION_TRACKS_VIEWS));
        $this->assertTrue(uckkarchive_supports(FEATURE_COMPLETION_HAS_RULES));
        $this->assertTrue(uckkarchive_supports(FEATURE_BACKUP_MOODLE2));
        $this->assertTrue(uckkarchive_supports(FEATURE_GROUPS));
        $this->assertTrue(uckkarchive_supports(FEATURE_GROUPINGS));

        // UCKK Archive is institutional memory, not a gradebook activity.
        $this->assertFalse(uckkarchive_supports(FEATURE_GRADE_HAS_GRADE));
        $this->assertFalse(uckkarchive_supports(FEATURE_GRADE_OUTCOMES));
        $this->assertFalse(uckkarchive_supports(FEATURE_RATE));
        $this->assertFalse(uckkarchive_supports(FEATURE_PLAGIARISM));

        $this->assertSame(MOD_PURPOSE_CONTENT, uckkarchive_supports(FEATURE_MOD_PURPOSE));

        // Unknown features must not be claimed.
        $this->assertNull(uckkarchive_supports('unknown_uckk_feature'));
    }

    /**
     * Adding an archive instance stores canonical archive configuration.
     */
    public function test_add_instance_creates_archive_record(): void {
        global $DB;

        $course = $this->getDataGenerator()->create_course();
        $data = $this->get_valid_instance_data((int)$course->id);

        $id = uckkarchive_add_instance($data, null);

        $this->assertGreaterThan(0, $id);

        $record = $DB->get_record('uckkarchive', ['id' => $id], '*', MUST_EXIST);

        $this->assertSame((int)$course->id, (int)$record->course);
        $this->assertSame($data->name, $record->name);
        $this->assertSame($data->intro, $record->intro);
        $this->assertSame((int)$data->introformat, (int)$record->introformat);
        $this->assertSame('active', $record->status);
        $this->assertSame('course', $record->visibility);
        $this->assertSame(1, (int)$record->completionrequireitem);
        $this->assertSame(0, (int)$record->completionrequirevalidation);
        $this->assertSame(1, (int)$record->versionno);

        $this->assertGreaterThan(0, (int)$record->createdby);
        $this->assertGreaterThan(0, (int)$record->modifiedby);
        $this->assertGreaterThan(0, (int)$record->timecreated);
        $this->assertGreaterThan(0, (int)$record->timemodified);

        $metadata = json_decode((string)$record->metadata, true);
        $this->assertIsArray($metadata);
        $this->assertSame('lib_test', $metadata['fixture']);
    }

    /**
     * Updating an archive instance changes editable configuration without
     * creating a second instance.
     */
    public function test_update_instance_updates_archive_record(): void {
        global $DB;

        $course = $this->getDataGenerator()->create_course();
        $data = $this->get_valid_instance_data((int)$course->id);

        $id = uckkarchive_add_instance($data, null);

        $data->id = $id;
        $data->instance = $id;
        $data->name = 'Updated UCKK archive';
        $data->intro = '<p>Updated archive intro.</p>';
        $data->status = 'pending_review';
        $data->visibility = 'restricted_integrity';
        $data->completionrequireitem = 1;
        $data->completionrequirevalidation = 1;
        $data->metadata = [
            'fixture' => 'lib_test',
            'updated' => true,
        ];

        $this->assertTrue(uckkarchive_update_instance($data, null));

        $records = $DB->get_records('uckkarchive');
        $this->assertCount(1, $records);

        $record = $DB->get_record('uckkarchive', ['id' => $id], '*', MUST_EXIST);

        $this->assertSame('Updated UCKK archive', $record->name);
        $this->assertSame('<p>Updated archive intro.</p>', $record->intro);
        $this->assertSame('pending_review', $record->status);
        $this->assertSame('restricted_integrity', $record->visibility);
        $this->assertSame(1, (int)$record->completionrequireitem);
        $this->assertSame(1, (int)$record->completionrequirevalidation);

        $metadata = json_decode((string)$record->metadata, true);
        $this->assertIsArray($metadata);
        $this->assertTrue($metadata['updated']);
    }

    /**
     * Deleting an archive instance removes the main record.
     */
    public function test_delete_instance_removes_archive_record(): void {
        global $DB;

        $course = $this->getDataGenerator()->create_course();
        $data = $this->get_valid_instance_data((int)$course->id);
        $id = uckkarchive_add_instance($data, null);

        $this->assertTrue($DB->record_exists('uckkarchive', ['id' => $id]));
        $this->assertTrue(uckkarchive_delete_instance($id));
        $this->assertFalse($DB->record_exists('uckkarchive', ['id' => $id]));
    }

    /**
     * Deleting a missing archive instance is a no-op.
     */
    public function test_delete_missing_instance_returns_false(): void {
        $this->assertFalse(uckkarchive_delete_instance(999999));
    }

    /**
     * Status normalisation preserves canonical statuses and falls back safely.
     *
     * @dataProvider normalise_status_provider
     * @param string|null $input Raw input.
     * @param string $expected Expected status.
     */
    public function test_normalise_status(?string $input, string $expected): void {
        $this->assertSame($expected, uckkarchive_normalise_status($input));
    }

    /**
     * Data provider for {@see self::test_normalise_status()}.
     *
     * @return \Generator
     */
    public static function normalise_status_provider(): \Generator {
        yield 'draft' => ['draft', 'draft'];
        yield 'active' => ['active', 'active'];
        yield 'pending review' => ['pending_review', 'pending_review'];
        yield 'validated' => ['validated', 'validated'];
        yield 'rejected' => ['rejected', 'rejected'];
        yield 'correction required' => ['correction_required', 'correction_required'];
        yield 'contested' => ['contested', 'contested'];
        yield 'invalidated' => ['invalidated', 'invalidated'];
        yield 'closed' => ['closed', 'closed'];
        yield 'archived' => ['archived', 'archived'];
        yield 'unknown defaults active' => ['unknown_status', 'active'];
        yield 'empty defaults active' => ['', 'active'];
        yield 'null defaults active' => [null, 'active'];
    }

    /**
     * Visibility normalisation preserves canonical visibilities and falls back
     * safely to course visibility.
     *
     * @dataProvider normalise_visibility_provider
     * @param string|null $input Raw input.
     * @param string $expected Expected visibility.
     */
    public function test_normalise_visibility(?string $input, string $expected): void {
        $this->assertSame($expected, uckkarchive_normalise_visibility($input));
    }

    /**
     * Data provider for {@see self::test_normalise_visibility()}.
     *
     * @return \Generator
     */
    public static function normalise_visibility_provider(): \Generator {
        yield 'private' => ['private', 'private'];
        yield 'user' => ['user', 'user'];
        yield 'group' => ['group', 'group'];
        yield 'course' => ['course', 'course'];
        yield 'cohort' => ['cohort', 'cohort'];
        yield 'program' => ['program', 'program'];
        yield 'institution' => ['institution', 'institution'];
        yield 'public' => ['public', 'public'];
        yield 'restricted' => ['restricted', 'restricted'];
        yield 'restricted cultural' => ['restricted_cultural', 'restricted_cultural'];
        yield 'restricted integrity' => ['restricted_integrity', 'restricted_integrity'];
        yield 'hidden' => ['hidden', 'hidden'];
        yield 'archived' => ['archived', 'archived'];
        yield 'unknown defaults course' => ['unknown_visibility', 'course'];
        yield 'empty defaults course' => ['', 'course'];
        yield 'null defaults course' => [null, 'course'];
    }

    /**
     * Metadata normalisation accepts arrays, stdClass values, and valid JSON.
     */
    public function test_normalise_metadata_accepts_supported_inputs(): void {
        $array = [
            'source' => 'phpunit',
            'nested' => [
                'ok' => true,
            ],
        ];

        $arrayjson = uckkarchive_normalise_metadata($array);
        $this->assertNotNull($arrayjson);

        $decodedarray = json_decode($arrayjson, true);
        $this->assertSame('phpunit', $decodedarray['source']);
        $this->assertTrue($decodedarray['nested']['ok']);

        $object = new stdClass();
        $object->source = 'object';

        $objectjson = uckkarchive_normalise_metadata($object);
        $this->assertNotNull($objectjson);

        $decodedobject = json_decode($objectjson, true);
        $this->assertSame('object', $decodedobject['source']);

        $json = uckkarchive_normalise_metadata('{"source":"json"}');
        $this->assertNotNull($json);

        $decodedjson = json_decode($json, true);
        $this->assertSame('json', $decodedjson['source']);
    }

    /**
     * Metadata normalisation rejects invalid metadata.
     */
    public function test_normalise_metadata_rejects_invalid_inputs(): void {
        $this->assertNull(uckkarchive_normalise_metadata(null));
        $this->assertNull(uckkarchive_normalise_metadata(''));
        $this->assertNull(uckkarchive_normalise_metadata('not json'));
        $this->assertNull(uckkarchive_normalise_metadata(42));
    }

    /**
     * The archive declares canonical archive, media, export, and advisory file areas.
     */
    public function test_get_fileareas_returns_canonical_archive_media_and_advisory_fileareas(): void {
        $fileareas = uckkarchive_get_fileareas();

        $expected = [
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
            'media_original',
            'media_preview',
            'media_thumbnail',
            'media_derivative',
            'media_caption',
            'media_transcript',
            'media_attachment',
            'content_review_files',
            'external_work_reference_files',
            'cultural_protocol_files',
        ];

        foreach ($expected as $filearea) {
            $this->assertContains($filearea, $fileareas, 'Missing file area: ' . $filearea);
        }

        $this->assertSame(
            count($fileareas),
            count(array_unique($fileareas)),
            'File areas must not contain duplicates.'
        );
    }

    /**
     * File areas map to their owning archive tables.
     *
     * @dataProvider filearea_table_provider
     * @param string $filearea File area.
     * @param string $expectedtable Expected table.
     */
    public function test_get_filearea_table(string $filearea, string $expectedtable): void {
        $this->assertSame($expectedtable, uckkarchive_get_filearea_table($filearea));
    }

    /**
     * Data provider for {@see self::test_get_filearea_table()}.
     *
     * @return \Generator
     */
    public static function filearea_table_provider(): \Generator {
        yield 'item content' => ['item_content', 'uckkarchive_item'];
        yield 'item public summary' => ['item_publicsummary', 'uckkarchive_item'];
        yield 'item files' => ['item_files', 'uckkarchive_item'];
        yield 'proof files' => ['proof_files', 'uckkarchive_proof'];
        yield 'kristal files' => ['kristal_files', 'uckkarchive_kristal'];
        yield 'integrity exports' => ['integrity_exports', 'uckkarchive_export'];
        yield 'decision attachments' => ['decision_attachments', 'uckkarchive_item'];
        yield 'minutes files' => ['minutes_files', 'uckkarchive_item'];
        yield 'portfolio files' => ['portfolio_files', 'uckkarchive_item'];
        yield 'provenance files' => ['provenance_files', 'uckkarchive_prov'];
        yield 'validation files' => ['validation_files', 'uckkarchive_rev'];
        yield 'revision files' => ['revision_files', 'uckkarchive_rev'];
        yield 'export package' => ['export_package', 'uckkarchive_export'];
        yield 'export manifest' => ['export_manifest', 'uckkarchive_export'];

        yield 'media original' => ['media_original', 'uckkarchive_media_version'];
        yield 'media preview' => ['media_preview', 'uckkarchive_media_version'];
        yield 'media thumbnail' => ['media_thumbnail', 'uckkarchive_media_version'];
        yield 'media derivative' => ['media_derivative', 'uckkarchive_media_version'];
        yield 'media caption' => ['media_caption', 'uckkarchive_media_version'];
        yield 'media transcript' => ['media_transcript', 'uckkarchive_media_version'];
        yield 'media attachment' => ['media_attachment', 'uckkarchive_media_version'];

        yield 'content review files' => ['content_review_files', 'uckkarchive_content_review'];
        yield 'external work reference files' => ['external_work_reference_files', 'uckkarchive_external_work'];
        yield 'cultural protocol files' => ['cultural_protocol_files', 'uckkarchive_content_marker'];
        yield 'unknown' => ['unknown_filearea', ''];
    }

    /**
     * Course module info exposes user-facing name, intro, and custom data.
     */
    public function test_get_coursemodule_info_returns_instance_display_data(): void {
        global $DB;

        $course = $this->getDataGenerator()->create_course();
        $data = $this->get_valid_instance_data((int)$course->id);
        $id = uckkarchive_add_instance($data, null);

        $module = $DB->get_record('modules', ['name' => 'uckkarchive'], '*', MUST_EXIST);

        $cm = (object)[
            'id' => 123,
            'course' => $course->id,
            'module' => $module->id,
            'instance' => $id,
            'modname' => 'uckkarchive',
            'name' => $data->name,
        ];

        $info = uckkarchive_get_coursemodule_info($cm);

        $this->assertInstanceOf(cached_cm_info::class, $info);
        $this->assertSame($data->name, $info->name);
        $this->assertIsArray($info->customdata);
        $this->assertSame('active', $info->customdata['status']);
        $this->assertSame('course', $info->customdata['visibility']);
    }

    /**
     * Completion is false when the completion item rule is enabled and no user item
     * exists.
     */
    public function test_completion_add_item_rule_requires_user_item(): void {
        $course = $this->getDataGenerator()->create_course();
        $user = $this->getDataGenerator()->create_user();

        $data = $this->get_valid_instance_data((int)$course->id);
        $data->completionrequireitem = 1;
        $data->completionrequirevalidation = 0;

        $archiveid = uckkarchive_add_instance($data, null);

        $cm = (object)[
            'instance' => $archiveid,
        ];

        $this->assertFalse(uckkarchive_get_completion_state($course, $cm, (int)$user->id, COMPLETION_AND));
    }

    /**
     * Completion is true when the completion item rule is enabled and a user item
     * exists.
     */
    public function test_completion_add_item_rule_passes_when_user_item_exists(): void {
        global $DB;

        $course = $this->getDataGenerator()->create_course();
        $user = $this->getDataGenerator()->create_user();

        $data = $this->get_valid_instance_data((int)$course->id);
        $data->completionrequireitem = 1;
        $data->completionrequirevalidation = 0;

        $archiveid = uckkarchive_add_instance($data, null);

        $this->insert_archive_item($archiveid, (int)$course->id, (int)$user->id, [
            'status' => 'draft',
        ]);

        $cm = (object)[
            'instance' => $archiveid,
        ];

        $this->assertTrue(uckkarchive_get_completion_state($course, $cm, (int)$user->id, COMPLETION_AND));
        $this->assertTrue($DB->record_exists('uckkarchive_item', ['archiveid' => $archiveid]));
    }

    /**
     * Completion validation rule requires a validated user item.
     */
    public function test_completion_validation_rule_requires_validated_user_item(): void {
        $course = $this->getDataGenerator()->create_course();
        $user = $this->getDataGenerator()->create_user();

        $data = $this->get_valid_instance_data((int)$course->id);
        $data->completionrequireitem = 0;
        $data->completionrequirevalidation = 1;

        $archiveid = uckkarchive_add_instance($data, null);

        $this->insert_archive_item($archiveid, (int)$course->id, (int)$user->id, [
            'status' => 'draft',
        ]);

        $cm = (object)[
            'instance' => $archiveid,
        ];

        $this->assertFalse(uckkarchive_get_completion_state($course, $cm, (int)$user->id, COMPLETION_AND));

        $this->insert_archive_item($archiveid, (int)$course->id, (int)$user->id, [
            'title' => 'Validated archive item',
            'status' => 'validated',
        ]);

        $this->assertTrue(uckkarchive_get_completion_state($course, $cm, (int)$user->id, COMPLETION_AND));
    }

    /**
     * User outline is empty when the user has no archive activity.
     */
    public function test_user_outline_returns_null_without_activity(): void {
        $course = $this->getDataGenerator()->create_course();
        $user = $this->getDataGenerator()->create_user();

        $data = $this->get_valid_instance_data((int)$course->id);
        $archiveid = uckkarchive_add_instance($data, null);
        $archive = $this->get_archive_record($archiveid);

        $mod = (object)[
            'id' => 1,
            'instance' => $archiveid,
        ];

        $this->assertNull(uckkarchive_user_outline($course, $user, $mod, $archive));
    }

    /**
     * User outline reports item/proof activity.
     */
    public function test_user_outline_reports_user_archive_activity(): void {
        global $DB;

        $course = $this->getDataGenerator()->create_course();
        $user = $this->getDataGenerator()->create_user();

        $data = $this->get_valid_instance_data((int)$course->id);
        $archiveid = uckkarchive_add_instance($data, null);
        $archive = $this->get_archive_record($archiveid);

        $this->insert_archive_item($archiveid, (int)$course->id, (int)$user->id);

        if ($DB->get_manager()->table_exists('uckkarchive_proof')) {
            $this->insert_archive_proof($archiveid, (int)$course->id, (int)$user->id);
        }

        $mod = (object)[
            'id' => 1,
            'instance' => $archiveid,
        ];

        $outline = uckkarchive_user_outline($course, $user, $mod, $archive);

        $this->assertInstanceOf(stdClass::class, $outline);
        $this->assertGreaterThan(0, $outline->time);
        $this->assertStringContainsString('1', $outline->info);
    }

    /**
     * File-area item checks allow normal course visibility.
     */
    public function test_can_view_filearea_item_allows_course_visible_item(): void {
        $course = $this->getDataGenerator()->create_course();
        $user = $this->getDataGenerator()->create_user();
        $this->setUser($user);

        [$archive, $cm] = $this->create_archive_module($course, [
            'visibility' => 'course',
        ]);

        $context = context_module::instance((int)$cm->id);

        $itemid = $this->insert_archive_item((int)$archive->id, (int)$course->id, (int)$user->id, [
            'cmid' => (int)$cm->id,
            'contextid' => (int)$context->id,
            'visibility' => 'course',
        ]);

        $this->assertTrue(uckkarchive_can_view_filearea_item($cm, $context, 'decision_attachments', $itemid));
    }

    /**
     * Restricted file-area items require restricted archive capability.
     */
    public function test_can_view_filearea_item_requires_capability_for_restricted_item(): void {
        $course = $this->getDataGenerator()->create_course();
        $owner = $this->getDataGenerator()->create_user();
        $viewer = $this->getDataGenerator()->create_user();

        [$archive, $cm] = $this->create_archive_module($course, [
            'visibility' => 'course',
        ]);

        $context = context_module::instance((int)$cm->id);

        $itemid = $this->insert_archive_item((int)$archive->id, (int)$course->id, (int)$owner->id, [
            'cmid' => (int)$cm->id,
            'contextid' => (int)$context->id,
            'visibility' => 'restricted_integrity',
        ]);

        $this->setUser($viewer);
        $this->assertFalse(uckkarchive_can_view_filearea_item($cm, $context, 'decision_attachments', $itemid));

        $this->assign_capability_to_user((int)$viewer->id, 'mod/uckkarchive:viewrestricted', $context);
        $this->assertTrue(uckkarchive_can_view_filearea_item($cm, $context, 'decision_attachments', $itemid));
    }


    /**
     * Deleting an archive instance removes owned media, advisory, and external-work records.
     */
    public function test_delete_instance_removes_media_advisory_and_external_work_records(): void {
        global $DB;

        $this->require_tables([
            'uckkarchive_media',
            'uckkarchive_media_version',
            'uckkarchive_content_marker',
            'uckkarchive_content_review',
            'uckkarchive_external_work',
        ]);

        $course = $this->getDataGenerator()->create_course();
        $user = $this->getDataGenerator()->create_user();

        [$archive, $cm] = $this->create_archive_module($course);
        $context = context_module::instance((int)$cm->id);

        $mediaid = $this->insert_media((int)$archive->id, (int)$course->id, (int)$cm->id, (int)$context->id, (int)$user->id);
        $versionid = $this->insert_media_version(
            (int)$archive->id,
            (int)$course->id,
            (int)$cm->id,
            (int)$context->id,
            (int)$user->id,
            $mediaid
        );
        $markerid = $this->insert_content_marker(
            (int)$archive->id,
            (int)$course->id,
            (int)$cm->id,
            (int)$context->id,
            (int)$user->id,
            $mediaid
        );
        $reviewid = $this->insert_content_review(
            (int)$archive->id,
            (int)$course->id,
            (int)$cm->id,
            (int)$context->id,
            (int)$user->id,
            $markerid
        );
        $externalworkid = $this->insert_external_work(
            (int)$archive->id,
            (int)$course->id,
            (int)$cm->id,
            (int)$context->id,
            (int)$user->id
        );

        $this->assertTrue($DB->record_exists('uckkarchive_media', ['id' => $mediaid]));
        $this->assertTrue(uckkarchive_delete_instance((int)$archive->id));

        $this->assertFalse($DB->record_exists('uckkarchive_media', ['id' => $mediaid]));
        $this->assertFalse($DB->record_exists('uckkarchive_media_version', ['id' => $versionid]));
        $this->assertFalse($DB->record_exists('uckkarchive_content_marker', ['id' => $markerid]));
        $this->assertFalse($DB->record_exists('uckkarchive_content_review', ['id' => $reviewid]));
        $this->assertFalse($DB->record_exists('uckkarchive_external_work', ['id' => $externalworkid]));
    }

    /**
     * Media file-area checks allow normal course-visible media version files.
     */
    public function test_can_view_filearea_item_allows_course_visible_media_version(): void {
        $this->require_tables([
            'uckkarchive_media',
            'uckkarchive_media_version',
        ]);

        $course = $this->getDataGenerator()->create_course();
        $user = $this->getDataGenerator()->create_user();
        $this->setUser($user);

        [$archive, $cm] = $this->create_archive_module($course);
        $context = context_module::instance((int)$cm->id);

        $mediaid = $this->insert_media((int)$archive->id, (int)$course->id, (int)$cm->id, (int)$context->id, (int)$user->id, [
            'visibility' => 'course',
        ]);
        $versionid = $this->insert_media_version(
            (int)$archive->id,
            (int)$course->id,
            (int)$cm->id,
            (int)$context->id,
            (int)$user->id,
            $mediaid,
            [
                'visibility' => 'course',
            ]
        );

        $this->assertTrue(uckkarchive_can_view_filearea_item($cm, $context, 'media_original', $versionid));
    }

    /**
     * Restricted media file-area checks require restricted-media authority.
     */
    public function test_can_view_filearea_item_requires_capability_for_restricted_media_version(): void {
        $this->require_tables([
            'uckkarchive_media',
            'uckkarchive_media_version',
        ]);

        $course = $this->getDataGenerator()->create_course();
        $owner = $this->getDataGenerator()->create_user();
        $viewer = $this->getDataGenerator()->create_user();

        [$archive, $cm] = $this->create_archive_module($course);
        $context = context_module::instance((int)$cm->id);

        $mediaid = $this->insert_media((int)$archive->id, (int)$course->id, (int)$cm->id, (int)$context->id, (int)$owner->id, [
            'visibility' => 'restricted',
        ]);
        $versionid = $this->insert_media_version(
            (int)$archive->id,
            (int)$course->id,
            (int)$cm->id,
            (int)$context->id,
            (int)$owner->id,
            $mediaid,
            [
                'visibility' => 'restricted',
            ]
        );

        $this->setUser($viewer);
        $this->assertFalse(uckkarchive_can_view_filearea_item($cm, $context, 'media_original', $versionid));

        $this->assign_capability_to_user((int)$viewer->id, 'mod/uckkarchive:viewrestrictedmedia', $context);
        $this->assertTrue(uckkarchive_can_view_filearea_item($cm, $context, 'media_original', $versionid));
    }

    /**
     * External-work and advisory file areas resolve to their owning records.
     */
    public function test_can_view_filearea_item_resolves_external_work_and_advisory_fileareas(): void {
        $this->require_tables([
            'uckkarchive_external_work',
            'uckkarchive_content_marker',
            'uckkarchive_content_review',
        ]);

        $course = $this->getDataGenerator()->create_course();
        $user = $this->getDataGenerator()->create_user();
        $this->setUser($user);

        [$archive, $cm] = $this->create_archive_module($course);
        $context = context_module::instance((int)$cm->id);

        $externalworkid = $this->insert_external_work(
            (int)$archive->id,
            (int)$course->id,
            (int)$cm->id,
            (int)$context->id,
            (int)$user->id,
            ['visibility' => 'course']
        );
        $markerid = $this->insert_content_marker(
            (int)$archive->id,
            (int)$course->id,
            (int)$cm->id,
            (int)$context->id,
            (int)$user->id,
            0,
            ['visibility' => 'course']
        );
        $reviewid = $this->insert_content_review(
            (int)$archive->id,
            (int)$course->id,
            (int)$cm->id,
            (int)$context->id,
            (int)$user->id,
            $markerid,
            ['visibility' => 'course']
        );

        $this->assertTrue(
            uckkarchive_can_view_filearea_item($cm, $context, 'external_work_reference_files', $externalworkid)
        );
        $this->assertTrue(
            uckkarchive_can_view_filearea_item($cm, $context, 'cultural_protocol_files', $markerid)
        );
        $this->assertTrue(
            uckkarchive_can_view_filearea_item($cm, $context, 'content_review_files', $reviewid)
        );
    }

    /**
     * Course reset keeps archive data as institutional memory.
     */
    public function test_reset_userdata_reports_archive_preservation(): void {
        $data = new stdClass();
        $data->courseid = 1;

        $result = uckkarchive_reset_userdata($data);

        $this->assertCount(1, $result);
        $this->assertFalse($result[0]['error']);
        $this->assertIsString($result[0]['item']);
    }

    /**
     * Build valid activity instance data for add/update callbacks.
     *
     * @param int $courseid Course id.
     * @return stdClass
     */
    private function get_valid_instance_data(int $courseid): stdClass {
        $data = new stdClass();
        $data->course = $courseid;
        $data->name = 'UCKK archive test';
        $data->intro = '<p>Archive intro.</p>';
        $data->introformat = FORMAT_HTML;
        $data->status = 'active';
        $data->visibility = 'course';
        $data->timeopen = 0;
        $data->timeclose = 0;
        $data->completionrequireitem = 1;
        $data->completionrequirevalidation = 0;
        $data->metadata = [
            'fixture' => 'lib_test',
        ];

        return $data;
    }

    /**
     * Create a real course module for uckkarchive if the activity generator is
     * available. Falls back to direct instance creation plus a manually created
     * course module record.
     *
     * @param stdClass $course Course record.
     * @param array<string, mixed> $overrides Instance overrides.
     * @return array{0: stdClass, 1: stdClass}
     */
    private function create_archive_module(stdClass $course, array $overrides = []): array {
        global $DB;

        $generator = $this->getDataGenerator()->get_plugin_generator('mod_uckkarchive');

        if ($generator !== null && method_exists($generator, 'create_instance')) {
            $archive = $generator->create_instance(array_merge([
                'course' => $course->id,
                'name' => 'UCKK archive module',
            ], $overrides));

            $cm = get_coursemodule_from_instance('uckkarchive', $archive->id, $course->id, false, MUST_EXIST);

            return [$archive, $cm];
        }

        $data = $this->get_valid_instance_data((int)$course->id);

        foreach ($overrides as $key => $value) {
            $data->{$key} = $value;
        }

        $archiveid = uckkarchive_add_instance($data, null);
        $module = $DB->get_record('modules', ['name' => 'uckkarchive'], '*', MUST_EXIST);

        $cm = new stdClass();
        $cm->course = $course->id;
        $cm->module = $module->id;
        $cm->instance = $archiveid;
        $cm->section = 0;
        $cm->idnumber = '';
        $cm->added = time();
        $cm->score = 0;
        $cm->indent = 0;
        $cm->visible = 1;
        $cm->visibleold = 1;
        $cm->groupmode = 0;
        $cm->groupingid = 0;
        $cm->completion = 0;
        $cm->completiongradeitemnumber = null;
        $cm->completionview = 0;
        $cm->completionexpected = 0;
        $cm->availability = null;
        $cm->showdescription = 0;
        $cm->deletioninprogress = 0;
        $cm->downloadcontent = 1;
        $cm->lang = '';
        $cm->id = $DB->insert_record('course_modules', $cm);

        $cm->modname = 'uckkarchive';
        $cm->name = $data->name;

        $archive = $DB->get_record('uckkarchive', ['id' => $archiveid], '*', MUST_EXIST);

        return [$archive, $cm];
    }

    /**
     * Insert a minimal archive item for tests.
     *
     * @param int $archiveid Archive instance id.
     * @param int $courseid Course id.
     * @param int $userid User id.
     * @param array<string, mixed> $overrides Field overrides.
     * @return int Archive item id.
     */
    private function insert_archive_item(int $archiveid, int $courseid, int $userid, array $overrides = []): int {
        $now = time();

        return $this->insert_filtered_record('uckkarchive_item', array_merge([
            'archiveid' => $archiveid,
            'courseid' => $courseid,
            'cmid' => 0,
            'contextid' => 0,
            'userid' => $userid,
            'itemtype' => 'proof',
            'title' => 'Archive item',
            'summary' => 'Archive item summary.',
            'content' => 'Archive item content.',
            'sourcecomponent' => 'mod_uckkarchive',
            'sourceid' => 0,
            'sourceref' => null,
            'status' => 'draft',
            'visibility' => 'course',
            'provenance' => 'human',
            'validationstate' => 'unverified',
            'provenancehash' => null,
            'versionno' => 1,
            'sortorder' => 0,
            'createdby' => $userid,
            'modifiedby' => $userid,
            'timecreated' => $now,
            'timemodified' => $now,
            'metadata' => json_encode(['fixture' => 'lib_test']),
        ], $overrides));
    }

    /**
     * Insert a minimal archive proof for tests.
     *
     * @param int $archiveid Archive instance id.
     * @param int $courseid Course id.
     * @param int $userid User id.
     * @param array<string, mixed> $overrides Field overrides.
     * @return int Archive proof id.
     */
    private function insert_archive_proof(int $archiveid, int $courseid, int $userid, array $overrides = []): int {
        $now = time();

        return $this->insert_filtered_record('uckkarchive_proof', array_merge([
            'archiveid' => $archiveid,
            'itemid' => 0,
            'courseid' => $courseid,
            'cmid' => 0,
            'contextid' => 0,
            'userid' => $userid,
            'prooftype' => 'text',
            'title' => 'Archive proof',
            'summary' => 'Archive proof summary.',
            'content' => 'Archive proof content.',
            'sourcecomponent' => 'mod_uckkarchive',
            'sourceid' => 0,
            'sourceref' => null,
            'status' => 'draft',
            'visibility' => 'course',
            'provenance' => 'human',
            'validationstate' => 'unverified',
            'provenancehash' => null,
            'versionno' => 1,
            'createdby' => $userid,
            'modifiedby' => $userid,
            'timecreated' => $now,
            'timemodified' => $now,
            'metadata' => json_encode(['fixture' => 'lib_test']),
        ], $overrides));
    }


    /**
     * Insert a minimal media record.
     *
     * @param int $archiveid Archive instance id.
     * @param int $courseid Course id.
     * @param int $cmid Course module id.
     * @param int $contextid Context id.
     * @param int $userid User id.
     * @param array<string, mixed> $overrides Field overrides.
     * @return int Media id.
     */
    private function insert_media(
        int $archiveid,
        int $courseid,
        int $cmid,
        int $contextid,
        int $userid,
        array $overrides = []
    ): int {
        $now = time();

        return $this->insert_filtered_record('uckkarchive_media', array_merge([
            'uuid' => $this->uuid(),
            'archiveid' => $archiveid,
            'courseid' => $courseid,
            'cmid' => $cmid,
            'contextid' => $contextid,
            'ownerid' => $userid,
            'userid' => $userid,
            'createdby' => $userid,
            'modifiedby' => $userid,
            'sourceid' => 0,
            'title' => 'Media item',
            'subtitle' => '',
            'description' => 'Media description.',
            'mediatype' => 'document',
            'mimetype' => 'text/plain',
            'status' => 'active',
            'visibility' => 'course',
            'audiencesuitability' => 'guided',
            'licensekey' => '',
            'rightsstatement' => '',
            'language' => 'fr',
            'duration' => 0,
            'pagecount' => 1,
            'hashoriginal' => '',
            'currentversionid' => 0,
            'provenanceid' => 0,
            'metadata' => json_encode(['fixture' => 'lib_test']),
            'timecreated' => $now,
            'timemodified' => $now,
        ], $overrides));
    }

    /**
     * Insert a minimal media version record.
     *
     * @param int $archiveid Archive instance id.
     * @param int $courseid Course id.
     * @param int $cmid Course module id.
     * @param int $contextid Context id.
     * @param int $userid User id.
     * @param int $mediaid Media id.
     * @param array<string, mixed> $overrides Field overrides.
     * @return int Media version id.
     */
    private function insert_media_version(
        int $archiveid,
        int $courseid,
        int $cmid,
        int $contextid,
        int $userid,
        int $mediaid,
        array $overrides = []
    ): int {
        $now = time();

        return $this->insert_filtered_record('uckkarchive_media_version', array_merge([
            'uuid' => $this->uuid(),
            'archiveid' => $archiveid,
            'courseid' => $courseid,
            'cmid' => $cmid,
            'contextid' => $contextid,
            'mediaid' => $mediaid,
            'versionno' => 1,
            'versionnumber' => 1,
            'label' => 'Version 1',
            'status' => 'active',
            'visibility' => 'course',
            'filearea' => 'media_original',
            'filename' => 'media.txt',
            'filesize' => 10,
            'mimetype' => 'text/plain',
            'contenthash' => sha1('media'),
            'iscurrent' => 1,
            'createdby' => $userid,
            'modifiedby' => $userid,
            'metadata' => json_encode(['fixture' => 'lib_test']),
            'timecreated' => $now,
            'timemodified' => $now,
        ], $overrides));
    }

    /**
     * Insert a minimal content marker record.
     *
     * @param int $archiveid Archive instance id.
     * @param int $courseid Course id.
     * @param int $cmid Course module id.
     * @param int $contextid Context id.
     * @param int $userid User id.
     * @param int $mediaid Optional media id.
     * @param array<string, mixed> $overrides Field overrides.
     * @return int Content marker id.
     */
    private function insert_content_marker(
        int $archiveid,
        int $courseid,
        int $cmid,
        int $contextid,
        int $userid,
        int $mediaid = 0,
        array $overrides = []
    ): int {
        $now = time();

        return $this->insert_filtered_record('uckkarchive_content_marker', array_merge([
            'uuid' => $this->uuid(),
            'archiveid' => $archiveid,
            'courseid' => $courseid,
            'cmid' => $cmid,
            'contextid' => $contextid,
            'mediaid' => $mediaid,
            'targettype' => $mediaid > 0 ? 'media' : 'external_work',
            'targetid' => $mediaid,
            'targetuuid' => '',
            'tagid' => 0,
            'tagsetid' => 0,
            'tagkey' => 'violence',
            'locatortype' => 'timecode',
            'locatorvalue' => '00:01:00',
            'locatorstart' => '00:01:00',
            'locatorend' => '00:02:00',
            'locatorsort' => 60,
            'severity' => 'moderate',
            'visibility' => 'course',
            'audiencesuitability' => 'guided',
            'reviewstate' => 'pending_review',
            'reviewedby' => 0,
            'timereviewed' => 0,
            'note' => 'Marker note.',
            'teachingcontext' => 'Teaching context.',
            'culturalprotocolnote' => '',
            'reviewrationale' => '',
            'createdby' => $userid,
            'modifiedby' => $userid,
            'metadata' => json_encode(['fixture' => 'lib_test']),
            'timecreated' => $now,
            'timemodified' => $now,
        ], $overrides));
    }

    /**
     * Insert a minimal content review record.
     *
     * @param int $archiveid Archive instance id.
     * @param int $courseid Course id.
     * @param int $cmid Course module id.
     * @param int $contextid Context id.
     * @param int $userid User id.
     * @param int $markerid Marker id.
     * @param array<string, mixed> $overrides Field overrides.
     * @return int Content review id.
     */
    private function insert_content_review(
        int $archiveid,
        int $courseid,
        int $cmid,
        int $contextid,
        int $userid,
        int $markerid,
        array $overrides = []
    ): int {
        $now = time();

        return $this->insert_filtered_record('uckkarchive_content_review', array_merge([
            'uuid' => $this->uuid(),
            'archiveid' => $archiveid,
            'courseid' => $courseid,
            'cmid' => $cmid,
            'contextid' => $contextid,
            'markerid' => $markerid,
            'reviewerid' => $userid,
            'userid' => $userid,
            'createdby' => $userid,
            'modifiedby' => $userid,
            'state' => 'approved',
            'severity' => 'moderate',
            'audiencesuitability' => 'guided',
            'visibility' => 'course',
            'rationale' => 'Review rationale.',
            'reviewnote' => 'Review note.',
            'metadata' => json_encode(['fixture' => 'lib_test']),
            'timecreated' => $now,
            'timemodified' => $now,
        ], $overrides));
    }

    /**
     * Insert a minimal external work record.
     *
     * @param int $archiveid Archive instance id.
     * @param int $courseid Course id.
     * @param int $cmid Course module id.
     * @param int $contextid Context id.
     * @param int $userid User id.
     * @param array<string, mixed> $overrides Field overrides.
     * @return int External work id.
     */
    private function insert_external_work(
        int $archiveid,
        int $courseid,
        int $cmid,
        int $contextid,
        int $userid,
        array $overrides = []
    ): int {
        $now = time();

        return $this->insert_filtered_record('uckkarchive_external_work', array_merge([
            'uuid' => $this->uuid(),
            'archiveid' => $archiveid,
            'courseid' => $courseid,
            'cmid' => $cmid,
            'contextid' => $contextid,
            'ownerid' => $userid,
            'userid' => $userid,
            'createdby' => $userid,
            'modifiedby' => $userid,
            'worktype' => 'film',
            'status' => 'active',
            'visibility' => 'course',
            'audiencesuitability' => 'guided',
            'rightsstatus' => 'licensed_external',
            'title' => 'External work',
            'subtitle' => '',
            'creator' => 'Creator',
            'publisher' => 'Publisher',
            'publicationyear' => 2020,
            'language' => 'fr',
            'sourceurl' => 'https://example.test/external-work',
            'identifier' => 'EXT-001',
            'identifiertype' => 'local_identifier',
            'citation' => 'External work citation.',
            'rightsstatement' => 'Rights statement.',
            'licensekey' => 'licensed',
            'sourcenote' => 'Source note.',
            'teachingnote' => 'Teaching note.',
            'culturalprotocolnote' => '',
            'description' => 'External work description.',
            'provenanceid' => 0,
            'metadata' => json_encode(['fixture' => 'lib_test']),
            'timecreated' => $now,
            'timemodified' => $now,
        ], $overrides));
    }

    /**
     * Insert a record while ignoring fields that are not present in the active schema.
     *
     * @param string $table Table name.
     * @param array<string, mixed> $data Data.
     * @return int Inserted id.
     */
    private function insert_filtered_record(string $table, array $data): int {
        global $DB;

        $this->assertTrue($this->table_exists($table), 'Missing table required by test: ' . $table);

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
     * Require tables for a test.
     *
     * @param string[] $tables Table names.
     */
    private function require_tables(array $tables): void {
        foreach ($tables as $table) {
            if (!$this->table_exists($table)) {
                $this->markTestSkipped('Required table is not installed yet: ' . $table);
            }
        }
    }

    /**
     * Return whether a table exists.
     *
     * @param string $table Table name.
     * @return bool
     */
    private function table_exists(string $table): bool {
        global $DB;

        return $DB->get_manager()->table_exists(new \xmldb_table($table));
    }

    /**
     * Return a UUID.
     *
     * @return string
     */
    private function uuid(): string {
        if (class_exists('\core\uuid')) {
            return \core\uuid::generate();
        }

        return sprintf(
            '%04x%04x-%04x-%04x-%04x-%04x%04x%04x',
            random_int(0, 0xffff),
            random_int(0, 0xffff),
            random_int(0, 0xffff),
            random_int(0, 0x0fff) | 0x4000,
            random_int(0, 0x3fff) | 0x8000,
            random_int(0, 0xffff),
            random_int(0, 0xffff),
            random_int(0, 0xffff)
        );
    }

    /**
     * Load an archive record.
     *
     * @param int $archiveid Archive id.
     * @return stdClass
     */
    private function get_archive_record(int $archiveid): stdClass {
        global $DB;

        return $DB->get_record('uckkarchive', ['id' => $archiveid], '*', MUST_EXIST);
    }

    /**
     * Assign a capability to a user in a specific context.
     *
     * @param int $userid User id.
     * @param string $capability Capability name.
     * @param \context $context Context.
     */
    private function assign_capability_to_user(int $userid, string $capability, \context $context): void {
        $roleid = $this->getDataGenerator()->create_role([
            'shortname' => 'uckkarchivetest' . substr(md5($capability . $userid . $context->id), 0, 8),
            'name' => 'UCKK archive test role',
            'archetype' => '',
        ]);

        assign_capability(
            $capability,
            CAP_ALLOW,
            $roleid,
            $context->id,
            true
        );

        role_assign($roleid, $userid, $context->id);
        accesslib_clear_all_caches_for_unit_testing();
    }
}

