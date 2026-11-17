<?php
// This file is part of Moodle - https://moodle.org/
//
// Moodle is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// any later version.

/**
 * File API tests for mod_uckkarchive.
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
use mod_uckkarchive\local\file_area_registry;
use mod_uckkarchive\local\media_file;
use stored_file;

defined('MOODLE_INTERNAL') || die();

global $CFG;
require_once($CFG->dirroot . '/mod/uckkarchive/lib.php');
require_once($CFG->dirroot . '/mod/uckkarchive/locallib.php');

/**
 * Tests for Moodle File API usage in mod_uckkarchive.
 *
 * These tests verify the activity's File API contract:
 *
 * - all canonical file areas are registered;
 * - archive, media, advisory, and export file areas use component mod_uckkarchive;
 * - files are isolated by context, file area, and item id;
 * - media_file helper stores, retrieves, counts, and deletes media files;
 * - manifest/export file areas can store generated package metadata.
 *
 * @covers \mod_uckkarchive\local\file_area_registry
 * @covers \mod_uckkarchive\local\media_file
 */
final class file_api_test extends advanced_testcase {
    /**
     * Reset database and file storage after each test.
     */
    protected function setUp(): void {
        parent::setUp();
        $this->resetAfterTest(true);
    }

    /**
     * Create an archive activity and return useful objects.
     *
     * @return array{0:\stdClass,1:\stdClass,2:\cm_info|\stdClass,3:context_module}
     */
    private function create_archive_activity(): array {
        $course = $this->getDataGenerator()->create_course();

        $archive = $this->getDataGenerator()->create_module('uckkarchive', [
            'course' => $course->id,
            'name' => 'File API archive',
            'intro' => 'Archive used by file API tests.',
            'introformat' => FORMAT_HTML,
        ]);

        $cm = get_coursemodule_from_instance('uckkarchive', $archive->id, $course->id, false, MUST_EXIST);
        $context = context_module::instance($cm->id);

        return [$course, $archive, $cm, $context];
    }

    /**
     * Registry should expose the canonical component name.
     */
    public function test_file_area_registry_uses_plugin_component(): void {
        $this->assertSame('mod_uckkarchive', file_area_registry::get_component());
        $this->assertTrue(file_area_registry::is_component('mod_uckkarchive'));
        $this->assertFalse(file_area_registry::is_component('core'));
    }

    /**
     * Registry should include archive-owned file areas.
     */
    public function test_registry_contains_archive_fileareas(): void {
        $areas = file_area_registry::get_archive_fileareas();

        $expected = [
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

        foreach ($expected as $area) {
            $this->assertContains($area, $areas, "Missing archive file area: {$area}");
            $this->assertTrue(file_area_registry::is_valid_filearea($area), "{$area} must be valid.");
            $this->assertTrue(file_area_registry::is_archive_filearea($area), "{$area} must be an archive area.");
        }
    }

    /**
     * Registry should include media-owned file areas.
     */
    public function test_registry_contains_media_fileareas(): void {
        $areas = file_area_registry::get_media_fileareas();

        $expected = [
            'media_original',
            'media_preview',
            'media_thumbnail',
            'media_derivative',
            'media_caption',
            'media_transcript',
            'media_attachment',
        ];

        foreach ($expected as $area) {
            $this->assertContains($area, $areas, "Missing media file area: {$area}");
            $this->assertTrue(file_area_registry::is_valid_filearea($area), "{$area} must be valid.");
            $this->assertTrue(file_area_registry::is_media_filearea($area), "{$area} must be a media area.");
        }
    }

    /**
     * Registry should include content advisory file areas.
     */
    public function test_registry_contains_content_advisory_fileareas(): void {
        $areas = file_area_registry::get_content_advisory_fileareas();

        $expected = [
            'content_review_files',
            'external_work_reference_files',
            'cultural_protocol_files',
        ];

        foreach ($expected as $area) {
            $this->assertContains($area, $areas, "Missing content advisory file area: {$area}");
            $this->assertTrue(file_area_registry::is_valid_filearea($area), "{$area} must be valid.");
            $this->assertTrue(
                file_area_registry::is_content_advisory_filearea($area),
                "{$area} must be a content advisory area."
            );
        }
    }

    /**
     * All file areas must be unique.
     */
    public function test_registered_fileareas_are_unique(): void {
        $areas = file_area_registry::get_all_fileareas();

        $this->assertNotEmpty($areas);
        $this->assertSameSize($areas, array_unique($areas));
    }

    /**
     * Legacy file area names should normalize to canonical names when known.
     */
    public function test_file_area_registry_normalizes_known_legacy_names(): void {
        $map = file_area_registry::get_legacy_filearea_map();

        foreach ($map as $legacy => $canonical) {
            $this->assertSame($canonical, file_area_registry::normalize_filearea($legacy));
            $this->assertTrue(file_area_registry::is_valid_filearea($canonical));
        }
    }

    /**
     * Direct Moodle File API storage should isolate records by file area.
     */
    public function test_moodle_file_api_isolates_files_by_filearea(): void {
        [$course, $archive, $cm, $context] = $this->create_archive_activity();

        $fs = get_file_storage();

        $itemfile = $this->create_stored_file(
            $context,
            'item_files',
            100,
            'shared-name.txt',
            'archive item file'
        );

        $prooffile = $this->create_stored_file(
            $context,
            'proof_files',
            100,
            'shared-name.txt',
            'proof file'
        );

        $this->assertInstanceOf(stored_file::class, $itemfile);
        $this->assertInstanceOf(stored_file::class, $prooffile);

        $this->assertNotEquals($itemfile->get_id(), $prooffile->get_id());
        $this->assertSame('item_files', $itemfile->get_filearea());
        $this->assertSame('proof_files', $prooffile->get_filearea());

        $this->assertSame(
            'archive item file',
            $fs->get_file(
                $context->id,
                'mod_uckkarchive',
                'item_files',
                100,
                '/',
                'shared-name.txt'
            )->get_content()
        );

        $this->assertSame(
            'proof file',
            $fs->get_file(
                $context->id,
                'mod_uckkarchive',
                'proof_files',
                100,
                '/',
                'shared-name.txt'
            )->get_content()
        );
    }

    /**
     * Direct Moodle File API storage should isolate records by item id.
     */
    public function test_moodle_file_api_isolates_files_by_itemid(): void {
        [$course, $archive, $cm, $context] = $this->create_archive_activity();

        $fs = get_file_storage();

        $fileone = $this->create_stored_file(
            $context,
            'media_original',
            10,
            'original.txt',
            'media 10'
        );

        $filetwo = $this->create_stored_file(
            $context,
            'media_original',
            20,
            'original.txt',
            'media 20'
        );

        $this->assertNotEquals($fileone->get_id(), $filetwo->get_id());

        $this->assertSame(
            'media 10',
            $fs->get_file($context->id, 'mod_uckkarchive', 'media_original', 10, '/', 'original.txt')->get_content()
        );

        $this->assertSame(
            'media 20',
            $fs->get_file($context->id, 'mod_uckkarchive', 'media_original', 20, '/', 'original.txt')->get_content()
        );
    }

    /**
     * Direct Moodle File API storage should isolate records by context.
     */
    public function test_moodle_file_api_isolates_files_by_context(): void {
        [$courseone, $archiveone, $cmone, $contextone] = $this->create_archive_activity();
        [$coursetwo, $archivetwo, $cmtwo, $contexttwo] = $this->create_archive_activity();

        $fs = get_file_storage();

        $this->create_stored_file($contextone, 'media_thumbnail', 99, 'thumb.txt', 'context one');
        $this->create_stored_file($contexttwo, 'media_thumbnail', 99, 'thumb.txt', 'context two');

        $this->assertSame(
            'context one',
            $fs->get_file($contextone->id, 'mod_uckkarchive', 'media_thumbnail', 99, '/', 'thumb.txt')->get_content()
        );

        $this->assertSame(
            'context two',
            $fs->get_file($contexttwo->id, 'mod_uckkarchive', 'media_thumbnail', 99, '/', 'thumb.txt')->get_content()
        );
    }

    /**
     * Media file helper should create, retrieve, count, and delete media files.
     */
    public function test_media_file_helper_creates_retrieves_counts_and_deletes_file(): void {
        [$course, $archive, $cm, $context] = $this->create_archive_activity();

        $file = media_file::create_file_from_string(
            $context,
            'media_original',
            321,
            'interview.txt',
            'Interview transcript source text'
        );

        $this->assertInstanceOf(stored_file::class, $file);
        $this->assertSame('mod_uckkarchive', $file->get_component());
        $this->assertSame('media_original', $file->get_filearea());
        $this->assertSame(321, $file->get_itemid());
        $this->assertSame('interview.txt', $file->get_filename());
        $this->assertSame('Interview transcript source text', $file->get_content());

        $this->assertTrue(media_file::has_files($context, 'media_original', 321));
        $this->assertSame(1, media_file::count_files($context, 'media_original', 321));

        $retrieved = media_file::get_file($context, 'media_original', 321, 'interview.txt');

        $this->assertInstanceOf(stored_file::class, $retrieved);
        $this->assertSame($file->get_id(), $retrieved->get_id());

        $metadata = media_file::get_file_metadata($retrieved);

        $this->assertSame('media_original', $metadata['filearea']);
        $this->assertSame('interview.txt', $metadata['filename']);
        $this->assertSame($retrieved->get_filesize(), $metadata['filesize']);
        $this->assertArrayHasKey('url', $metadata);

        media_file::delete_area_files($context, 'media_original', 321);

        $this->assertFalse(media_file::has_files($context, 'media_original', 321));
        $this->assertSame(0, media_file::count_files($context, 'media_original', 321));
    }

    /**
     * Media file helper should reject non-media file areas.
     */
    public function test_media_file_helper_rejects_non_media_filearea(): void {
        [$course, $archive, $cm, $context] = $this->create_archive_activity();

        $this->expectException(\invalid_parameter_exception::class);

        media_file::create_file_from_string(
            $context,
            'item_files',
            1,
            'wrong-area.txt',
            'This belongs to archive item files, not media_file helper.'
        );
    }

    /**
     * Media file helper should generate pluginfile URLs.
     */
    public function test_media_file_helper_generates_file_urls(): void {
        [$course, $archive, $cm, $context] = $this->create_archive_activity();

        $file = media_file::create_file_from_string(
            $context,
            'media_preview',
            654,
            'preview.txt',
            'preview content'
        );

        $url = media_file::get_file_url($file, false);
        $downloadurl = media_file::get_file_url($file, true);

        $this->assertInstanceOf(\moodle_url::class, $url);
        $this->assertInstanceOf(\moodle_url::class, $downloadurl);

        $this->assertStringContainsString('/pluginfile.php/', $url->out(false));
        $this->assertStringContainsString('/mod_uckkarchive/media_preview/654/preview.txt', $url->out(false));
        $this->assertStringContainsString('forcedownload=1', $downloadurl->out(false));
    }

    /**
     * Media helper should prepare draft areas from stored media files.
     */
    public function test_media_file_helper_prepares_draft_area(): void {
        global $USER;

        [$course, $archive, $cm, $context] = $this->create_archive_activity();

        media_file::create_file_from_string(
            $context,
            'media_caption',
            777,
            'caption.vtt',
            'WEBVTT'
        );

        $draftitemid = file_get_unused_draft_itemid();

        media_file::prepare_draft_area(
            $draftitemid,
            $context,
            'media_caption',
            777,
            [
                'subdirs' => 0,
                'maxfiles' => -1,
                'accepted_types' => '*',
            ]
        );

        $fs = get_file_storage();
        $draftcontext = \context_user::instance($USER->id);
        $draftfile = $fs->get_file(
            $draftcontext->id,
            'user',
            'draft',
            $draftitemid,
            '/',
            'caption.vtt'
        );

        $this->assertInstanceOf(stored_file::class, $draftfile);
        $this->assertSame('WEBVTT', $draftfile->get_content());
    }

    /**
     * Export manifest area should store generated manifest JSON.
     */
    public function test_export_manifest_area_can_store_manifest_json(): void {
        [$course, $archive, $cm, $context] = $this->create_archive_activity();

        $manifest = [
            'manifest_version' => 1,
            'plugin' => 'mod_uckkarchive',
            'archiveid' => (int)$archive->id,
            'cmid' => (int)$cm->id,
            'media' => [
                [
                    'id' => 12,
                    'title' => 'Media export target',
                ],
            ],
        ];

        $file = $this->create_stored_file(
            $context,
            'export_manifest',
            456,
            'manifest.json',
            json_encode($manifest, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES)
        );

        $this->assertInstanceOf(stored_file::class, $file);
        $this->assertSame('export_manifest', $file->get_filearea());
        $this->assertSame('manifest.json', $file->get_filename());

        $decoded = json_decode($file->get_content(), true);

        $this->assertIsArray($decoded);
        $this->assertSame('mod_uckkarchive', $decoded['plugin']);
        $this->assertSame((int)$archive->id, $decoded['archiveid']);
        $this->assertSame((int)$cm->id, $decoded['cmid']);
    }

    /**
     * Cultural protocol file area should be treated as a sensitive file area.
     */
    public function test_cultural_protocol_filearea_is_sensitive(): void {
        $this->assertTrue(file_area_registry::is_sensitive_filearea('cultural_protocol_files'));
        $this->assertTrue(file_area_registry::is_content_advisory_filearea('cultural_protocol_files'));
    }

    /**
     * Export file areas should be included in export group.
     */
    public function test_export_fileareas_are_grouped(): void {
        $areas = file_area_registry::get_export_fileareas();

        $this->assertContains('export_package', $areas);
        $this->assertContains('export_manifest', $areas);
        $this->assertTrue(file_area_registry::is_export_filearea('export_package'));
        $this->assertTrue(file_area_registry::is_export_filearea('export_manifest'));
    }

    /**
     * Delete all media helper should remove only media-owned areas for an item.
     */
    public function test_delete_all_media_area_files_removes_media_areas_only(): void {
        [$course, $archive, $cm, $context] = $this->create_archive_activity();

        $fs = get_file_storage();

        media_file::create_file_from_string($context, 'media_original', 909, 'original.txt', 'original');
        media_file::create_file_from_string($context, 'media_preview', 909, 'preview.txt', 'preview');
        media_file::create_file_from_string($context, 'media_thumbnail', 909, 'thumb.txt', 'thumb');

        $this->create_stored_file($context, 'item_files', 909, 'item.txt', 'item');

        media_file::delete_all_media_area_files($context, 909);

        $this->assertFalse(media_file::has_files($context, 'media_original', 909));
        $this->assertFalse(media_file::has_files($context, 'media_preview', 909));
        $this->assertFalse(media_file::has_files($context, 'media_thumbnail', 909));

        $this->assertInstanceOf(
            stored_file::class,
            $fs->get_file($context->id, 'mod_uckkarchive', 'item_files', 909, '/', 'item.txt')
        );
    }

    /**
     * Create stored file helper.
     *
     * @param context_module $context Module context.
     * @param string $filearea File area.
     * @param int $itemid Item id.
     * @param string $filename Filename.
     * @param string $content Content.
     * @return stored_file
     */
    private function create_stored_file(
        context_module $context,
        string $filearea,
        int $itemid,
        string $filename,
        string $content
    ): stored_file {
        $fs = get_file_storage();

        $record = [
            'contextid' => $context->id,
            'component' => 'mod_uckkarchive',
            'filearea' => $filearea,
            'itemid' => $itemid,
            'filepath' => '/',
            'filename' => $filename,
        ];

        return $fs->create_file_from_string($record, $content);
    }
}
