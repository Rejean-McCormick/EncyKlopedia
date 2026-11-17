<?php
// This file is part of Moodle - https://moodle.org/
//
// Moodle is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// any later version.

/**
 * Tests for the public Médiathèque repository.
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
use mod_uckkarchive\local\media_library_scope;
use mod_uckkarchive\local\public_mediatheque_repository;
use stdClass;

defined('MOODLE_INTERNAL') || die();

global $CFG;
require_once($CFG->dirroot . '/mod/uckkarchive/locallib.php');

/**
 * Tests for the public Médiathèque repository.
 *
 * This test class protects the public repository contract used by the
 * local_uckk public Médiathèque façade. It does not duplicate the full
 * internal media-library test suite.
 *
 * Repository responsibilities tested here:
 *
 * - return public-facing media only;
 * - support archive-scoped and site-wide public search;
 * - support simple public query and media-type filters;
 * - return grouped public facets;
 * - avoid leaking private/raw fields.
 *
 * @covers \mod_uckkarchive\local\public_mediatheque_repository
 */
final class public_mediatheque_repository_test extends advanced_testcase {
    /** Media table. */
    private const TABLE_MEDIA = 'uckkarchive_media';

    /**
     * Reset state after each test.
     *
     * @return void
     */
    protected function setUp(): void {
        parent::setUp();
        $this->resetAfterTest(true);
    }

    /**
     * Public search should return only active public media.
     *
     * @return void
     */
    public function test_search_returns_only_public_active_media(): void {
        $this->require_tables([self::TABLE_MEDIA]);

        $course = $this->getDataGenerator()->create_course();
        $user = $this->getDataGenerator()->create_user();
        $this->setUser($user);

        [$archive, $cm] = $this->create_archive_module($course);
        $context = context_module::instance((int)$cm->id);

        $this->insert_media($archive, $cm, $context, $user, [
            'title' => 'Public active media',
            'status' => 'active',
            'visibility' => 'public',
            'audiencesuitability' => 'general',
            'restricted' => 0,
            'culturalprotocol' => 0,
            'searchable' => 1,
        ]);

        $this->insert_media($archive, $cm, $context, $user, [
            'title' => 'Draft public media',
            'status' => 'draft',
            'visibility' => 'public',
            'audiencesuitability' => 'general',
            'restricted' => 0,
            'culturalprotocol' => 0,
            'searchable' => 1,
        ]);

        $this->insert_media($archive, $cm, $context, $user, [
            'title' => 'Course only media',
            'status' => 'active',
            'visibility' => 'course',
            'audiencesuitability' => 'general',
            'restricted' => 0,
            'culturalprotocol' => 0,
            'searchable' => 1,
        ]);

        $this->insert_media($archive, $cm, $context, $user, [
            'title' => 'Restricted public media',
            'status' => 'active',
            'visibility' => 'restricted',
            'audiencesuitability' => 'restricted',
            'restricted' => 1,
            'culturalprotocol' => 1,
            'searchable' => 1,
        ]);

        $repository = new public_mediatheque_repository();
        $result = $repository->search((int)$archive->id, $context, [
            'type' => 'media',
            'page' => 1,
            'perpage' => 12,
        ]);

        $titles = $this->extract_titles($this->extract_items($result));

        $this->assertContains('Public active media', $titles);
        $this->assertNotContains('Draft public media', $titles);
        $this->assertNotContains('Course only media', $titles);
        $this->assertNotContains('Restricted public media', $titles);
    }

    /**
     * Library partitions should be isolated by default and bridges directional.
     *
     * @return void
     */
    public function test_library_partition_and_directional_media_bridge(): void {
        $this->require_tables([
            self::TABLE_MEDIA,
            media_library_scope::TABLE_LIBRARY,
            media_library_scope::TABLE_LIBRARY_SITE,
            media_library_scope::TABLE_LIBRARY_BRIDGE,
        ]);

        $course = $this->getDataGenerator()->create_course();
        $user = $this->getDataGenerator()->create_user();
        $this->setUser($user);

        [$archive, $cm] = $this->create_archive_module($course);
        $context = context_module::instance((int)$cm->id);

        $scope = new media_library_scope();
        $ucclibrary = $scope->resolve_by_slug(media_library_scope::LIBRARY_UCC)
            ?? $scope->create_library(media_library_scope::LIBRARY_UCC, 'Médiathèque chrétienne');
        $mathlibrary = $scope->resolve_by_slug(media_library_scope::LIBRARY_MATH)
            ?? $scope->create_library(media_library_scope::LIBRARY_MATH, 'Bibliothèque mathématique');

        $uccmedia = $this->insert_media($archive, $cm, $context, $user, [
            'title' => 'UCC only media',
            'libraryid' => (int)$ucclibrary->id,
        ]);
        $this->insert_media($archive, $cm, $context, $user, [
            'title' => 'Math only media',
            'libraryid' => (int)$mathlibrary->id,
        ]);

        $repository = new public_mediatheque_repository();
        $uccresult = $repository->search((int)$archive->id, $context, [
            'type' => 'media',
            'libraryid' => (int)$ucclibrary->id,
            'libraryrequired' => true,
            'page' => 1,
            'perpage' => 12,
        ]);
        $ucctitles = $this->extract_titles($this->extract_items($uccresult));
        $this->assertContains('UCC only media', $ucctitles);
        $this->assertNotContains('Math only media', $ucctitles);

        $scope->create_bridge(
            media_library_scope::LIBRARY_UCC,
            media_library_scope::LIBRARY_MATH,
            media_library_scope::SCOPE_MEDIA,
            (int)$uccmedia->id,
            'UCC vers math'
        );

        $mathresult = $repository->search((int)$archive->id, $context, [
            'type' => 'media',
            'libraryid' => (int)$mathlibrary->id,
            'libraryrequired' => true,
            'page' => 1,
            'perpage' => 12,
        ]);
        $mathitems = $this->extract_items($mathresult);
        $mathtitles = $this->extract_titles($mathitems);
        $this->assertContains('Math only media', $mathtitles);
        $this->assertContains('UCC only media', $mathtitles);

        $bridged = null;
        foreach ($mathitems as $item) {
            $title = is_object($item) ? (string)($item->title ?? '') : (string)($item['title'] ?? '');
            if ($title === 'UCC only media') {
                $bridged = $item;
                break;
            }
        }
        $this->assertNotNull($bridged);
        $this->assertTrue((bool)(is_object($bridged) ? $bridged->isbridged : $bridged['isbridged']));

        // The bridge is UCC -> Math only. It must not expose Math content back into UCC.
        $uccafterbridge = $repository->search((int)$archive->id, $context, [
            'type' => 'media',
            'libraryid' => (int)$ucclibrary->id,
            'libraryrequired' => true,
            'page' => 1,
            'perpage' => 12,
        ]);
        $uccaftertitles = $this->extract_titles($this->extract_items($uccafterbridge));
        $this->assertNotContains('Math only media', $uccaftertitles);
    }

    /**
     * Archive-scoped search should not leak media from another archive.
     *
     * @return void
     */
    public function test_search_is_scoped_to_archive_when_archiveid_is_supplied(): void {
        $this->require_tables([self::TABLE_MEDIA]);

        $course = $this->getDataGenerator()->create_course();
        $user = $this->getDataGenerator()->create_user();
        $this->setUser($user);

        [$archiveone, $cmone] = $this->create_archive_module($course, ['name' => 'Archive one']);
        [$archivetwo, $cmtwo] = $this->create_archive_module($course, ['name' => 'Archive two']);

        $contextone = context_module::instance((int)$cmone->id);
        $contexttwo = context_module::instance((int)$cmtwo->id);

        $this->insert_media($archiveone, $cmone, $contextone, $user, [
            'title' => 'Archive one public media',
            'status' => 'active',
            'visibility' => 'public',
            'audiencesuitability' => 'general',
            'restricted' => 0,
            'culturalprotocol' => 0,
            'searchable' => 1,
        ]);

        $this->insert_media($archivetwo, $cmtwo, $contexttwo, $user, [
            'title' => 'Archive two public media',
            'status' => 'active',
            'visibility' => 'public',
            'audiencesuitability' => 'general',
            'restricted' => 0,
            'culturalprotocol' => 0,
            'searchable' => 1,
        ]);

        $repository = new public_mediatheque_repository();
        $result = $repository->search((int)$archiveone->id, $contextone, [
            'type' => 'media',
            'page' => 1,
            'perpage' => 12,
        ]);

        $titles = $this->extract_titles($this->extract_items($result));

        $this->assertContains('Archive one public media', $titles);
        $this->assertNotContains('Archive two public media', $titles);
    }

    /**
     * Site-wide public search should work with archiveid = 0 and no context.
     *
     * @return void
     */
    public function test_search_supports_site_wide_public_scope(): void {
        $this->require_tables([self::TABLE_MEDIA]);

        $course = $this->getDataGenerator()->create_course();
        $user = $this->getDataGenerator()->create_user();
        $this->setUser($user);

        [$archiveone, $cmone] = $this->create_archive_module($course, ['name' => 'Site-wide archive one']);
        [$archivetwo, $cmtwo] = $this->create_archive_module($course, ['name' => 'Site-wide archive two']);

        $contextone = context_module::instance((int)$cmone->id);
        $contexttwo = context_module::instance((int)$cmtwo->id);

        $this->insert_media($archiveone, $cmone, $contextone, $user, [
            'title' => 'Site wide one public media',
            'summary' => 'Visible from site-wide public search.',
            'description' => 'Visible from site-wide public search.',
            'status' => 'active',
            'visibility' => 'public',
            'audiencesuitability' => 'general',
            'restricted' => 0,
            'culturalprotocol' => 0,
            'searchable' => 1,
        ]);

        $this->insert_media($archivetwo, $cmtwo, $contexttwo, $user, [
            'title' => 'Site wide two public media',
            'summary' => 'Visible from site-wide public search.',
            'description' => 'Visible from site-wide public search.',
            'status' => 'active',
            'visibility' => 'public',
            'audiencesuitability' => 'general',
            'restricted' => 0,
            'culturalprotocol' => 0,
            'searchable' => 1,
        ]);

        $repository = new public_mediatheque_repository();
        $result = $repository->search(0, null, [
            'type' => 'media',
            'q' => 'Site wide',
            'page' => 1,
            'perpage' => 12,
        ]);

        $titles = $this->extract_titles($this->extract_items($result));

        $this->assertContains('Site wide one public media', $titles);
        $this->assertContains('Site wide two public media', $titles);
    }

    /**
     * Public search should support query and media type filters.
     *
     * @return void
     */
    public function test_search_filters_by_query_and_mediatype(): void {
        $this->require_tables([self::TABLE_MEDIA]);

        $course = $this->getDataGenerator()->create_course();
        $user = $this->getDataGenerator()->create_user();
        $this->setUser($user);

        [$archive, $cm] = $this->create_archive_module($course);
        $context = context_module::instance((int)$cm->id);

        $this->insert_media($archive, $cm, $context, $user, [
            'title' => 'Alpha public video',
            'summary' => 'A public video about Alpha.',
            'description' => 'A public video about Alpha.',
            'mediatype' => 'video',
            'mimetype' => 'video/mp4',
            'status' => 'active',
            'visibility' => 'public',
            'audiencesuitability' => 'general',
            'restricted' => 0,
            'culturalprotocol' => 0,
            'searchable' => 1,
        ]);

        $this->insert_media($archive, $cm, $context, $user, [
            'title' => 'Alpha public image',
            'summary' => 'A public image about Alpha.',
            'description' => 'A public image about Alpha.',
            'mediatype' => 'image',
            'mimetype' => 'image/png',
            'status' => 'active',
            'visibility' => 'public',
            'audiencesuitability' => 'general',
            'restricted' => 0,
            'culturalprotocol' => 0,
            'searchable' => 1,
        ]);

        $this->insert_media($archive, $cm, $context, $user, [
            'title' => 'Beta public video',
            'summary' => 'A public video about Beta.',
            'description' => 'A public video about Beta.',
            'mediatype' => 'video',
            'mimetype' => 'video/mp4',
            'status' => 'active',
            'visibility' => 'public',
            'audiencesuitability' => 'general',
            'restricted' => 0,
            'culturalprotocol' => 0,
            'searchable' => 1,
        ]);

        $repository = new public_mediatheque_repository();
        $result = $repository->search((int)$archive->id, $context, [
            'type' => 'media',
            'q' => 'Alpha',
            'mediatype' => 'video',
            'page' => 1,
            'perpage' => 12,
        ]);

        $titles = $this->extract_titles($this->extract_items($result));

        $this->assertContains('Alpha public video', $titles);
        $this->assertNotContains('Alpha public image', $titles);
        $this->assertNotContains('Beta public video', $titles);
    }

    /**
     * Repository result should expose canonical pagination and total fields.
     *
     * @return void
     */
    public function test_search_returns_pagination_total_and_policy_envelope(): void {
        $this->require_tables([self::TABLE_MEDIA]);

        $course = $this->getDataGenerator()->create_course();
        $user = $this->getDataGenerator()->create_user();
        $this->setUser($user);

        [$archive, $cm] = $this->create_archive_module($course);
        $context = context_module::instance((int)$cm->id);

        $this->insert_media($archive, $cm, $context, $user, [
            'title' => 'Pagination public media',
            'status' => 'active',
            'visibility' => 'public',
            'audiencesuitability' => 'general',
            'restricted' => 0,
            'culturalprotocol' => 0,
            'searchable' => 1,
        ]);

        $repository = new public_mediatheque_repository();
        $result = $repository->search((int)$archive->id, $context, [
            'type' => 'media',
            'q' => 'Pagination',
            'page' => 1,
            'perpage' => 12,
        ]);

        $this->assertIsObject($result);
        $this->assertObjectHasProperty('items', $result);
        $this->assertObjectHasProperty('total', $result);
        $this->assertObjectHasProperty('pagination', $result);
        $this->assertObjectHasProperty('facets', $result);
        $this->assertObjectHasProperty('notices', $result);
        $this->assertObjectHasProperty('warnings', $result);

        $this->assertGreaterThanOrEqual(1, (int)$result->total);
        $this->assertSame(1, (int)$result->pagination->page);
        $this->assertSame(12, (int)$result->pagination->perpage);
        $this->assertGreaterThanOrEqual(1, (int)$result->pagination->total);
        $this->assertIsBool((bool)$result->pagination->hasmore);
    }

    /**
     * Facets should be grouped and built from public-visible records only.
     *
     * @return void
     */
    public function test_public_facets_are_grouped_and_do_not_include_hidden_media(): void {
        $this->require_tables([self::TABLE_MEDIA]);

        $course = $this->getDataGenerator()->create_course();
        $user = $this->getDataGenerator()->create_user();
        $this->setUser($user);

        [$archive, $cm] = $this->create_archive_module($course);
        $context = context_module::instance((int)$cm->id);

        $this->insert_media($archive, $cm, $context, $user, [
            'title' => 'Public video facet',
            'mediatype' => 'video',
            'mimetype' => 'video/mp4',
            'status' => 'active',
            'visibility' => 'public',
            'audiencesuitability' => 'general',
            'restricted' => 0,
            'culturalprotocol' => 0,
            'searchable' => 1,
        ]);

        $this->insert_media($archive, $cm, $context, $user, [
            'title' => 'Restricted audio facet',
            'mediatype' => 'audio',
            'mimetype' => 'audio/mpeg',
            'status' => 'active',
            'visibility' => 'restricted',
            'audiencesuitability' => 'restricted',
            'restricted' => 1,
            'culturalprotocol' => 1,
            'searchable' => 1,
        ]);

        $repository = new public_mediatheque_repository();
        $result = $repository->search((int)$archive->id, $context, [
            'type' => 'media',
            'page' => 1,
            'perpage' => 12,
        ]);

        $this->assertObjectHasProperty('facets', $result);
        $this->assertIsArray($result->facets);

        foreach ($result->facets as $facet) {
            $facet = $this->as_array($facet);

            $this->assertArrayHasKey('key', $facet);
            $this->assertArrayHasKey('label', $facet);
            $this->assertArrayHasKey('items', $facet);
            $this->assertIsArray($facet['items']);

            foreach ($facet['items'] as $item) {
                $item = $this->as_array($item);

                $this->assertArrayHasKey('value', $item);
                $this->assertArrayHasKey('label', $item);
                $this->assertArrayHasKey('count', $item);
                $this->assertArrayHasKey('active', $item);
            }
        }

        $facetvalues = $this->flatten_facet_values($result->facets);

        $this->assertContains('video', $facetvalues);
        $this->assertNotContains('audio', $facetvalues);
    }

    /**
     * Public DTO should not expose private fields or raw metadata.
     *
     * @return void
     */
    public function test_public_item_does_not_expose_private_fields(): void {
        $this->require_tables([self::TABLE_MEDIA]);

        $course = $this->getDataGenerator()->create_course();
        $user = $this->getDataGenerator()->create_user();
        $this->setUser($user);

        [$archive, $cm] = $this->create_archive_module($course);
        $context = context_module::instance((int)$cm->id);

        $this->insert_media($archive, $cm, $context, $user, [
            'title' => 'Privacy safe public media',
            'summary' => 'Safe public summary.',
            'description' => 'Safe public description.',
            'mediatype' => 'document',
            'mimetype' => 'application/pdf',
            'status' => 'active',
            'visibility' => 'public',
            'audiencesuitability' => 'general',
            'restricted' => 0,
            'culturalprotocol' => 0,
            'searchable' => 1,
            'provenancehash' => hash('sha256', 'private-provenance-hash'),
            'integritycaseid' => 12345,
            'sourceobjectid' => 98765,
            'metadata' => json_encode([
                'public' => 'allowed',
                'internalnote' => 'must not leak',
                'culturalprotocolnote' => 'must not leak',
            ]),
        ]);

        $repository = new public_mediatheque_repository();
        $result = $repository->search((int)$archive->id, $context, [
            'type' => 'media',
            'q' => 'Privacy safe',
            'page' => 1,
            'perpage' => 12,
        ]);

        $items = $this->extract_items($result);
        $this->assertNotEmpty($items);

        $item = $this->as_array($items[0]);

        $this->assertSame('Privacy safe public media', (string)$item['title']);

        $this->assertArrayNotHasKey('metadata', $item);
        $this->assertArrayNotHasKey('internalnote', $item);
        $this->assertArrayNotHasKey('private_note', $item);
        $this->assertArrayNotHasKey('culturalprotocolnote', $item);
        $this->assertArrayNotHasKey('provenancehash', $item);
        $this->assertArrayNotHasKey('integritycaseid', $item);
        $this->assertArrayNotHasKey('sourceobjectid', $item);
        $this->assertArrayNotHasKey('fileurl', $item);
        $this->assertArrayNotHasKey('downloadurl', $item);

        $this->assertArrayHasKey('uuid', $item);
        $this->assertArrayHasKey('objecttype', $item);
        $this->assertArrayHasKey('title', $item);
        $this->assertArrayHasKey('summary', $item);
        $this->assertArrayHasKey('mediatype', $item);
        $this->assertArrayHasKey('visibility', $item);
        $this->assertArrayHasKey('canviewdetail', $item);
        $this->assertArrayHasKey('canviewfile', $item);
        $this->assertArrayHasKey('candownload', $item);
        $this->assertArrayHasKey('canexport', $item);

        $this->assertFalse((bool)$item['candownload']);
        $this->assertFalse((bool)$item['canexport']);

        $encoded = json_encode($item, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
        $this->assertIsString($encoded);
        $this->assertStringNotContainsString('internalnote', $encoded);
        $this->assertStringNotContainsString('culturalprotocolnote', $encoded);
        $this->assertStringNotContainsString('private-provenance-hash', $encoded);
    }

    /**
     * Require the listed database tables or skip the test.
     *
     * @param string[] $tables Table names.
     * @return void
     */
    private function require_tables(array $tables): void {
        global $DB;

        $manager = $DB->get_manager();

        foreach ($tables as $table) {
            if (!$manager->table_exists(new \xmldb_table($table))) {
                $this->markTestSkipped('Required table is not installed: ' . $table);
            }
        }
    }

    /**
     * Create a UCKK Archive course module.
     *
     * @param stdClass $course Course.
     * @param array<string, mixed> $overrides Instance overrides.
     * @return array{0: stdClass, 1: stdClass}
     */
    private function create_archive_module(stdClass $course, array $overrides = []): array {
        global $DB;

        $data = array_merge([
            'course' => (int)$course->id,
            'name' => 'UCKK archive test',
            'intro' => '<p>Archive intro.</p>',
            'introformat' => FORMAT_HTML,
        ], $overrides);

        $archive = $this->getDataGenerator()->create_module('uckkarchive', $data);

        $cm = get_coursemodule_from_instance(
            'uckkarchive',
            (int)$archive->id,
            (int)$course->id,
            false,
            MUST_EXIST
        );

        return [
            $DB->get_record('uckkarchive', ['id' => (int)$archive->id], '*', MUST_EXIST),
            $cm,
        ];
    }

    /**
     * Insert a media record directly for repository tests.
     *
     * @param stdClass $archive Archive.
     * @param stdClass $cm Course module.
     * @param context_module $context Module context.
     * @param stdClass $user User.
     * @param array<string, mixed> $overrides Overrides.
     * @return stdClass
     */
    private function insert_media(
        stdClass $archive,
        stdClass $cm,
        context_module $context,
        stdClass $user,
        array $overrides = []
    ): stdClass {
        global $DB;

        $now = time();

        $record = (object)array_merge([
            'uuid' => $this->uuid(),
            'archiveid' => (int)$archive->id,
            'uckkarchiveid' => (int)$archive->id,
            'courseid' => (int)$archive->course,
            'course' => (int)$archive->course,
            'cmid' => (int)$cm->id,
            'contextid' => (int)$context->id,
            'userid' => (int)$user->id,
            'ownerid' => (int)$user->id,
            'createdby' => (int)$user->id,
            'modifiedby' => (int)$user->id,
            'currentversionid' => 0,
            'externalworkid' => 0,
            'sourceid' => 0,
            'mediatype' => 'image',
            'mimetype' => 'image/png',
            'status' => 'active',
            'visibility' => 'public',
            'audiencesuitability' => 'general',
            'source' => 'produced_by_uckk',
            'sourcetype' => 'produced_by_uckk',
            'sourceurl' => '',
            'sourcecomponent' => '',
            'sourceobjectid' => 0,
            'license' => '',
            'licensekey' => '',
            'rightsstatus' => '',
            'rightsstatement' => '',
            'language' => 'fr',
            'provenance' => 'human',
            'provenancehash' => '',
            'integritycaseid' => 0,
            'title' => 'Public media',
            'subtitle' => '',
            'summary' => 'Public media summary.',
            'description' => 'Public media description.',
            'descriptionformat' => FORMAT_HTML,
            'metadata' => json_encode(['fixture' => 'public_mediatheque_repository_test']),
            'restricted' => 0,
            'culturalprotocol' => 0,
            'searchable' => 1,
            'versionno' => 1,
            'timecreated' => $now,
            'timemodified' => $now,
        ], $overrides);

        $record = $this->filter_record_to_table(self::TABLE_MEDIA, $record);
        $record->id = $DB->insert_record(self::TABLE_MEDIA, $record);

        return $DB->get_record(self::TABLE_MEDIA, ['id' => (int)$record->id], '*', MUST_EXIST);
    }

    /**
     * Extract items from repository result.
     *
     * @param mixed $result Repository result.
     * @return array<int, mixed>
     */
    private function extract_items($result): array {
        if ($result instanceof stdClass && isset($result->items) && is_array($result->items)) {
            return array_values($result->items);
        }

        if (is_array($result) && array_key_exists('items', $result) && is_array($result['items'])) {
            return array_values($result['items']);
        }

        if (is_array($result)) {
            return array_values($result);
        }

        $this->fail('Repository search result must be a stdClass payload or an array payload containing items.');
    }

    /**
     * Extract titles from item payloads.
     *
     * @param array<int, mixed> $items Items.
     * @return string[]
     */
    private function extract_titles(array $items): array {
        $titles = [];

        foreach ($items as $item) {
            if (is_array($item)) {
                $titles[] = (string)($item['title'] ?? '');
                continue;
            }

            if (is_object($item)) {
                $titles[] = (string)($item->title ?? '');
            }
        }

        return array_values(array_filter($titles, static fn(string $title): bool => $title !== ''));
    }

    /**
     * Flatten facet values from grouped facet payloads.
     *
     * @param mixed $facets Facets.
     * @return string[]
     */
    private function flatten_facet_values($facets): array {
        $values = [];

        $walk = static function($node) use (&$walk, &$values): void {
            if (is_scalar($node)) {
                $values[] = (string)$node;
                return;
            }

            if (is_object($node)) {
                $node = get_object_vars($node);
            }

            if (!is_array($node)) {
                return;
            }

            foreach ($node as $key => $value) {
                if (in_array($key, ['value', 'key', 'mediatype'], true) && is_scalar($value)) {
                    $values[] = (string)$value;
                    continue;
                }

                $walk($value);
            }
        };

        $walk($facets);

        return array_values(array_unique(array_filter($values, static fn(string $value): bool => $value !== '')));
    }

    /**
     * Cast array/object to array.
     *
     * @param mixed $value Value.
     * @return array<string, mixed>
     */
    private function as_array($value): array {
        if ($value instanceof stdClass) {
            return get_object_vars($value);
        }

        if (is_array($value)) {
            return $value;
        }

        return [];
    }

    /**
     * Filter a fixture record to the fields installed for a table.
     *
     * @param string $table Table name.
     * @param stdClass $record Record.
     * @return stdClass
     */
    private function filter_record_to_table(string $table, stdClass $record): stdClass {
        global $DB;

        $columns = $DB->get_columns($table);
        $filtered = new stdClass();

        foreach (get_object_vars($record) as $field => $value) {
            if (array_key_exists($field, $columns)) {
                $filtered->{$field} = $value;
            }
        }

        return $filtered;
    }

    /**
     * Return a UUID.
     *
     * @return string
     */
    private function uuid(): string {
        if (class_exists('\\mod_uckkarchive\\local\\uuid') &&
                method_exists('\\mod_uckkarchive\\local\\uuid', 'generate')) {
            return \mod_uckkarchive\local\uuid::generate();
        }

        if (class_exists('\\core\\uuid') && method_exists('\\core\\uuid', 'generate')) {
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
}