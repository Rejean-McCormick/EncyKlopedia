<?php
// This file is part of Moodle - https://moodle.org/.
//
// Moodle is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// any later version.

/**
 * Public Médiathèque external service tests.
 *
 * @package    mod_uckkarchive
 * @category   test
 * @copyright  2026 Univers-Cité King Klown
 * @license    https://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later
 */

declare(strict_types=1);

namespace mod_uckkarchive\external;

defined('MOODLE_INTERNAL') || die();

global $CFG;
require_once($CFG->dirroot . '/webservice/tests/helpers.php');
require_once($CFG->dirroot . '/mod/uckkarchive/locallib.php');

use context_module;
use stdClass;

/**
 * Tests for the public Médiathèque search endpoint.
 *
 * These tests validate the public façade contract only. They do not replace
 * the internal media-library tests. The public endpoint must return a stable,
 * permission-filtered DTO for the local_uckk public Médiathèque page.
 *
 * @covers \mod_uckkarchive\external\search_mediatheque
 */
final class search_mediatheque_test extends \advanced_testcase {
    /** Media table. */
    private const TABLE_MEDIA = 'uckkarchive_media';

    /**
     * Reset state.
     *
     * @return void
     */
    protected function setUp(): void {
        parent::setUp();
        $this->resetAfterTest(true);
    }

    /**
     * Service class must expose Moodle external-service contract.
     *
     * @return void
     */
    public function test_service_class_declares_external_contract(): void {
        $this->assertTrue(
            class_exists(search_mediatheque::class),
            search_mediatheque::class . ' must exist.'
        );

        $this->assertTrue(method_exists(search_mediatheque::class, 'execute_parameters'));
        $this->assertTrue(method_exists(search_mediatheque::class, 'execute'));
        $this->assertTrue(method_exists(search_mediatheque::class, 'execute_returns'));
    }

    /**
     * Anonymous cmid-scoped search returns only public active media.
     *
     * @return void
     */
    public function test_public_search_returns_only_public_active_media(): void {
        $fixture = $this->create_activity_fixture();

        $this->require_table(self::TABLE_MEDIA);

        $this->create_media($fixture, [
            'title' => 'Public needle video',
            'summary' => 'Visible public media',
            'description' => 'Visible public media',
            'mediatype' => 'video',
            'status' => 'active',
            'visibility' => 'public',
            'audiencesuitability' => 'general',
            'restricted' => 0,
            'culturalprotocol' => 0,
            'searchable' => 1,
        ]);

        $this->create_media($fixture, [
            'title' => 'Draft needle video',
            'summary' => 'Draft must stay hidden',
            'description' => 'Draft must stay hidden',
            'mediatype' => 'video',
            'status' => 'draft',
            'visibility' => 'public',
            'audiencesuitability' => 'general',
            'restricted' => 0,
            'culturalprotocol' => 0,
            'searchable' => 1,
        ]);

        $this->create_media($fixture, [
            'title' => 'Restricted needle video',
            'summary' => 'Restricted must stay hidden',
            'description' => 'Restricted must stay hidden',
            'mediatype' => 'video',
            'status' => 'active',
            'visibility' => 'restricted',
            'audiencesuitability' => 'restricted',
            'restricted' => 1,
            'culturalprotocol' => 1,
            'searchable' => 1,
        ]);

        $this->setUser(0);

        $result = search_mediatheque::execute(
            (int)$fixture['cm']->id,
            0,
            'needle',
            [],
            1,
            12,
            'relevance'
        );

        $clean = \core_external\external_api::clean_returnvalue(
            search_mediatheque::execute_returns(),
            $result
        );

        $titles = $this->extract_titles($clean);

        $this->assertContains('Public needle video', $titles);
        $this->assertNotContains('Draft needle video', $titles);
        $this->assertNotContains('Restricted needle video', $titles);
    }

    /**
     * Site-wide public search works without cmid or archiveid.
     *
     * @return void
     */
    public function test_public_search_supports_site_wide_scope(): void {
        $fixture = $this->create_activity_fixture();

        $this->require_table(self::TABLE_MEDIA);

        $this->create_media($fixture, [
            'title' => 'Site wide public media',
            'summary' => 'Visible from site-wide public Médiathèque',
            'description' => 'Visible from site-wide public Médiathèque',
            'mediatype' => 'audio',
            'status' => 'active',
            'visibility' => 'public',
            'audiencesuitability' => 'general',
            'restricted' => 0,
            'culturalprotocol' => 0,
            'searchable' => 1,
        ]);

        $this->setUser(0);

        $result = search_mediatheque::execute(
            0,
            0,
            'Site wide',
            [],
            1,
            12,
            'relevance'
        );

        $clean = \core_external\external_api::clean_returnvalue(
            search_mediatheque::execute_returns(),
            $result
        );

        $titles = $this->extract_titles($clean);

        $this->assertContains('Site wide public media', $titles);
        $this->assertSame('mod_uckkarchive', $clean['context']['component']);
        $this->assertSame('local_uckk', $clean['context']['surface']);
        $this->assertSame('mediatheque', $clean['context']['page']);
        $this->assertSame('mediatheque_explorer', $clean['context']['explorer']);
        $this->assertTrue((bool)$clean['context']['policyfiltered']);
    }

    /**
     * Archive-scoped public search works when archiveid is supplied.
     *
     * @return void
     */
    public function test_public_search_supports_archive_scope(): void {
        $first = $this->create_activity_fixture();
        $second = $this->create_activity_fixture();

        $this->require_table(self::TABLE_MEDIA);

        $this->create_media($first, [
            'title' => 'Archive scoped visible media',
            'summary' => 'Visible in first archive scope',
            'description' => 'Visible in first archive scope',
            'mediatype' => 'document',
            'status' => 'active',
            'visibility' => 'public',
            'audiencesuitability' => 'general',
            'restricted' => 0,
            'culturalprotocol' => 0,
            'searchable' => 1,
        ]);

        $this->create_media($second, [
            'title' => 'Other archive visible media',
            'summary' => 'Should not appear in first archive scope',
            'description' => 'Should not appear in first archive scope',
            'mediatype' => 'document',
            'status' => 'active',
            'visibility' => 'public',
            'audiencesuitability' => 'general',
            'restricted' => 0,
            'culturalprotocol' => 0,
            'searchable' => 1,
        ]);

        $this->setUser(0);

        $result = search_mediatheque::execute(
            0,
            (int)$first['archive']->id,
            'archive',
            [],
            1,
            12,
            'relevance'
        );

        $clean = \core_external\external_api::clean_returnvalue(
            search_mediatheque::execute_returns(),
            $result
        );

        $titles = $this->extract_titles($clean);

        $this->assertContains('Archive scoped visible media', $titles);
        $this->assertNotContains('Other archive visible media', $titles);
    }

    /**
     * Public search supports filters and pagination.
     *
     * @return void
     */
    public function test_public_search_supports_filters_and_pagination(): void {
        $fixture = $this->create_activity_fixture();

        $this->require_table(self::TABLE_MEDIA);

        $this->create_media($fixture, [
            'title' => 'Public video result',
            'mediatype' => 'video',
            'status' => 'active',
            'visibility' => 'public',
            'audiencesuitability' => 'general',
            'restricted' => 0,
            'culturalprotocol' => 0,
            'searchable' => 1,
        ]);

        $this->create_media($fixture, [
            'title' => 'Public image result',
            'mediatype' => 'image',
            'status' => 'active',
            'visibility' => 'public',
            'audiencesuitability' => 'general',
            'restricted' => 0,
            'culturalprotocol' => 0,
            'searchable' => 1,
        ]);

        $this->setUser(0);

        $result = search_mediatheque::execute(
            (int)$fixture['cm']->id,
            0,
            '',
            ['mediatype' => 'video'],
            1,
            12,
            'title'
        );

        $clean = \core_external\external_api::clean_returnvalue(
            search_mediatheque::execute_returns(),
            $result
        );

        $titles = $this->extract_titles($clean);

        $this->assertContains('Public video result', $titles);
        $this->assertNotContains('Public image result', $titles);

        $this->assertSame(1, (int)$clean['pagination']['page']);
        $this->assertSame(12, (int)$clean['pagination']['perpage']);
        $this->assertArrayHasKey('total', $clean['pagination']);
        $this->assertArrayHasKey('hasmore', $clean['pagination']);
    }

    /**
     * Public DTO must not expose private fields or raw metadata.
     *
     * @return void
     */
    public function test_public_response_does_not_expose_private_fields(): void {
        $fixture = $this->create_activity_fixture();

        $this->require_table(self::TABLE_MEDIA);

        $this->create_media($fixture, [
            'title' => 'Public privacy-safe media',
            'summary' => 'Safe public summary',
            'description' => 'Safe public description',
            'mediatype' => 'document',
            'status' => 'active',
            'visibility' => 'public',
            'audiencesuitability' => 'general',
            'restricted' => 0,
            'culturalprotocol' => 0,
            'searchable' => 1,
            'provenancehash' => hash('sha256', 'private-provenance-hash'),
            'integritycaseid' => 12345,
            'metadata' => json_encode([
                'public' => 'allowed',
                'internalnote' => 'must not leak',
                'culturalprotocolnote' => 'must not leak',
            ]),
        ]);

        $this->setUser(0);

        $result = search_mediatheque::execute(
            (int)$fixture['cm']->id,
            0,
            'privacy-safe',
            [],
            1,
            12,
            'relevance'
        );

        $clean = \core_external\external_api::clean_returnvalue(
            search_mediatheque::execute_returns(),
            $result
        );

        $this->assertNotEmpty($clean['items']);

        $item = $clean['items'][0];

        $this->assertSame('Public privacy-safe media', $item['title']);

        $this->assertArrayNotHasKey('metadata', $item);
        $this->assertArrayNotHasKey('internalnote', $item);
        $this->assertArrayNotHasKey('private_note', $item);
        $this->assertArrayNotHasKey('culturalprotocolnote', $item);
        $this->assertArrayNotHasKey('provenancehash', $item);
        $this->assertArrayNotHasKey('integritycaseid', $item);
        $this->assertArrayNotHasKey('sourceobjectid', $item);
        $this->assertArrayNotHasKey('fileurl', $item);
        $this->assertArrayNotHasKey('downloadurl', $item);

        $encoded = json_encode($item, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
        $this->assertIsString($encoded);
        $this->assertStringNotContainsString('internalnote', $encoded);
        $this->assertStringNotContainsString('culturalprotocolnote', $encoded);
        $this->assertStringNotContainsString('private-provenance-hash', $encoded);

        $this->assertArrayHasKey('actions', $item);
        $this->assertArrayHasKey('canviewdetail', $item['actions']);
        $this->assertArrayHasKey('canviewfile', $item['actions']);
        $this->assertArrayHasKey('candownload', $item['actions']);
        $this->assertArrayHasKey('canexport', $item['actions']);

        $this->assertFalse((bool)$item['actions']['candownload']);
        $this->assertFalse((bool)$item['actions']['canexport']);
    }

    /**
     * Public response uses canonical envelope.
     *
     * @return void
     */
    public function test_public_response_uses_canonical_envelope(): void {
        $fixture = $this->create_activity_fixture();

        $this->require_table(self::TABLE_MEDIA);

        $this->create_media($fixture, [
            'title' => 'Envelope media',
            'mediatype' => 'audio',
            'status' => 'active',
            'visibility' => 'public',
            'audiencesuitability' => 'general',
            'restricted' => 0,
            'culturalprotocol' => 0,
            'searchable' => 1,
        ]);

        $this->setUser(0);

        $result = search_mediatheque::execute(
            (int)$fixture['cm']->id,
            0,
            'Envelope',
            [],
            1,
            12,
            'relevance'
        );

        $clean = \core_external\external_api::clean_returnvalue(
            search_mediatheque::execute_returns(),
            $result
        );

        $this->assertArrayHasKey('context', $clean);
        $this->assertArrayHasKey('filters', $clean);
        $this->assertArrayHasKey('facets', $clean);
        $this->assertArrayHasKey('items', $clean);
        $this->assertArrayHasKey('pagination', $clean);
        $this->assertArrayHasKey('notices', $clean);
        $this->assertArrayHasKey('warnings', $clean);
        $this->assertArrayHasKey('empty', $clean);

        $this->assertSame('mod_uckkarchive', $clean['context']['component']);
        $this->assertSame('local_uckk', $clean['context']['surface']);
        $this->assertSame('mediatheque', $clean['context']['page']);
        $this->assertSame('mediatheque_explorer', $clean['context']['explorer']);
        $this->assertTrue((bool)$clean['context']['policyfiltered']);

        $this->assertSame(1, (int)$clean['pagination']['page']);
        $this->assertSame(12, (int)$clean['pagination']['perpage']);

        $this->assertIsArray($clean['notices']);
        $this->assertIsArray($clean['warnings']);
        $this->assertIsArray($clean['facets']);
        $this->assertIsArray($clean['items']);

        $this->assertArrayHasKey('isempty', $clean['empty']);
        $this->assertArrayHasKey('message', $clean['empty']);
    }

    /**
     * Public response exposes canonical item structure only.
     *
     * @return void
     */
    public function test_public_item_uses_canonical_structure(): void {
        $fixture = $this->create_activity_fixture();

        $this->require_table(self::TABLE_MEDIA);

        $this->create_media($fixture, [
            'title' => 'Canonical item media',
            'summary' => 'Canonical item summary',
            'description' => 'Canonical item description',
            'mediatype' => 'image',
            'mimetype' => 'image/png',
            'status' => 'active',
            'visibility' => 'public',
            'audiencesuitability' => 'general',
            'language' => 'fr',
            'restricted' => 0,
            'culturalprotocol' => 0,
            'searchable' => 1,
        ]);

        $this->setUser(0);

        $result = search_mediatheque::execute(
            (int)$fixture['cm']->id,
            0,
            'Canonical item',
            [],
            1,
            12,
            'relevance'
        );

        $clean = \core_external\external_api::clean_returnvalue(
            search_mediatheque::execute_returns(),
            $result
        );

        $this->assertNotEmpty($clean['items']);

        $item = $clean['items'][0];

        $this->assertArrayHasKey('uuid', $item);
        $this->assertArrayHasKey('objecttype', $item);
        $this->assertArrayHasKey('title', $item);
        $this->assertArrayHasKey('subtitle', $item);
        $this->assertArrayHasKey('summary', $item);
        $this->assertArrayHasKey('mediatype', $item);
        $this->assertArrayHasKey('mimetype', $item);
        $this->assertArrayHasKey('language', $item);
        $this->assertArrayHasKey('thumbnailurl', $item);
        $this->assertArrayHasKey('detailurl', $item);
        $this->assertArrayHasKey('source', $item);
        $this->assertArrayHasKey('rights', $item);
        $this->assertArrayHasKey('status', $item);
        $this->assertArrayHasKey('visibility', $item);
        $this->assertArrayHasKey('validation', $item);
        $this->assertArrayHasKey('badges', $item);
        $this->assertArrayHasKey('advisories', $item);
        $this->assertArrayHasKey('culturalprotocol', $item);
        $this->assertArrayHasKey('relations', $item);
        $this->assertArrayHasKey('actions', $item);

        $this->assertSame('media', $item['objecttype']);
        $this->assertSame('Canonical item media', $item['title']);
        $this->assertSame('image', $item['mediatype']);

        $this->assertArrayHasKey('value', $item['source']);
        $this->assertArrayHasKey('label', $item['source']);

        $this->assertArrayHasKey('license', $item['rights']);
        $this->assertArrayHasKey('rightsstatement', $item['rights']);
        $this->assertArrayHasKey('copyallowed', $item['rights']);

        $this->assertArrayHasKey('value', $item['status']);
        $this->assertArrayHasKey('label', $item['status']);

        $this->assertArrayHasKey('value', $item['visibility']);
        $this->assertArrayHasKey('label', $item['visibility']);
    }

    /**
     * Public facets use canonical grouped structure.
     *
     * @return void
     */
    public function test_public_facets_use_grouped_structure(): void {
        $fixture = $this->create_activity_fixture();

        $this->require_table(self::TABLE_MEDIA);

        $this->create_media($fixture, [
            'title' => 'Facet video media',
            'mediatype' => 'video',
            'source' => 'produced_by_uckk',
            'sourcetype' => 'produced_by_uckk',
            'status' => 'active',
            'visibility' => 'public',
            'audiencesuitability' => 'general',
            'restricted' => 0,
            'culturalprotocol' => 0,
            'searchable' => 1,
        ]);

        $this->setUser(0);

        $result = search_mediatheque::execute(
            (int)$fixture['cm']->id,
            0,
            'Facet',
            [],
            1,
            12,
            'relevance'
        );

        $clean = \core_external\external_api::clean_returnvalue(
            search_mediatheque::execute_returns(),
            $result
        );

        $this->assertIsArray($clean['facets']);

        foreach ($clean['facets'] as $facet) {
            $this->assertArrayHasKey('key', $facet);
            $this->assertArrayHasKey('label', $facet);
            $this->assertArrayHasKey('items', $facet);
            $this->assertIsArray($facet['items']);

            foreach ($facet['items'] as $item) {
                $this->assertArrayHasKey('value', $item);
                $this->assertArrayHasKey('label', $item);
                $this->assertArrayHasKey('count', $item);
                $this->assertArrayHasKey('active', $item);
            }
        }
    }

    /**
     * Notices and warnings use canonical public structures.
     *
     * @return void
     */
    public function test_public_notices_and_warnings_use_canonical_structure(): void {
        $fixture = $this->create_activity_fixture();

        $this->require_table(self::TABLE_MEDIA);

        $this->create_media($fixture, [
            'title' => 'Notice media',
            'mediatype' => 'video',
            'status' => 'active',
            'visibility' => 'public',
            'audiencesuitability' => 'general',
            'restricted' => 0,
            'culturalprotocol' => 0,
            'searchable' => 1,
        ]);

        $this->setUser(0);

        $result = search_mediatheque::execute(
            (int)$fixture['cm']->id,
            0,
            'Notice',
            [],
            1,
            12,
            'relevance'
        );

        $clean = \core_external\external_api::clean_returnvalue(
            search_mediatheque::execute_returns(),
            $result
        );

        $this->assertIsArray($clean['notices']);
        $this->assertIsArray($clean['warnings']);

        foreach ($clean['notices'] as $notice) {
            $this->assertArrayHasKey('type', $notice);
            $this->assertArrayHasKey('code', $notice);
            $this->assertArrayHasKey('message', $notice);
        }

        foreach ($clean['warnings'] as $warning) {
            $this->assertArrayHasKey('item', $warning);
            $this->assertArrayHasKey('itemid', $warning);
            $this->assertArrayHasKey('warningcode', $warning);
            $this->assertArrayHasKey('message', $warning);
        }
    }

    /**
     * Create a basic activity fixture.
     *
     * @return array<string, mixed>
     */
    private function create_activity_fixture(): array {
        $generator = $this->getDataGenerator();

        $course = $generator->create_course();

        /** @var stdClass $archive */
        $archive = $generator->create_module('uckkarchive', [
            'course' => $course->id,
            'name' => 'Médiathèque public search test',
        ]);

        $cm = get_coursemodule_from_instance(
            'uckkarchive',
            (int)$archive->id,
            (int)$course->id,
            false,
            MUST_EXIST
        );

        $context = context_module::instance((int)$cm->id);

        return [
            'course' => $course,
            'archive' => $archive,
            'cm' => $cm,
            'context' => $context,
        ];
    }

    /**
     * Create media record.
     *
     * @param array<string, mixed> $fixture Fixture.
     * @param array<string, mixed> $overrides Overrides.
     * @return stdClass
     */
    private function create_media(array $fixture, array $overrides = []): stdClass {
        global $DB;

        $this->require_table(self::TABLE_MEDIA);

        $now = time();
        $admin = get_admin();

        $record = (object)array_merge([
            'uuid' => $this->uuid(),
            'archiveid' => (int)$fixture['archive']->id,
            'uckkarchiveid' => (int)$fixture['archive']->id,
            'courseid' => (int)$fixture['course']->id,
            'course' => (int)$fixture['course']->id,
            'cmid' => (int)$fixture['cm']->id,
            'contextid' => (int)$fixture['context']->id,
            'userid' => (int)$admin->id,
            'ownerid' => (int)$admin->id,
            'createdby' => (int)$admin->id,
            'modifiedby' => (int)$admin->id,
            'title' => 'Public test media',
            'subtitle' => '',
            'summary' => 'Public test summary',
            'description' => 'Public test description',
            'descriptionformat' => FORMAT_HTML,
            'mediatype' => 'video',
            'mimetype' => 'video/mp4',
            'source' => 'produced_by_uckk',
            'sourcetype' => 'produced_by_uckk',
            'sourceurl' => '',
            'sourcecomponent' => '',
            'sourceobjectid' => 0,
            'license' => '',
            'licensekey' => '',
            'rightsstatus' => '',
            'rightsstatement' => '',
            'status' => 'active',
            'visibility' => 'public',
            'audiencesuitability' => 'general',
            'language' => 'fr',
            'validationstate' => '',
            'provenance' => 'human',
            'provenancehash' => '',
            'integritycaseid' => 0,
            'culturalprotocol' => 0,
            'restricted' => 0,
            'searchable' => 1,
            'versionno' => 1,
            'metadata' => json_encode(['fixture' => 'search_mediatheque_test']),
            'timecreated' => $now,
            'timemodified' => $now,
        ], $overrides);

        $record = $this->filter_to_table_fields(self::TABLE_MEDIA, $record);
        $record->id = $DB->insert_record(self::TABLE_MEDIA, $record);

        return $DB->get_record(self::TABLE_MEDIA, ['id' => (int)$record->id], '*', MUST_EXIST);
    }

    /**
     * Extract titles from search payload.
     *
     * @param array<string, mixed> $payload Cleaned service payload.
     * @return array<int, string>
     */
    private function extract_titles(array $payload): array {
        $items = $payload['items'] ?? [];

        if (!is_array($items)) {
            return [];
        }

        return array_values(array_map(
            static fn(array $item): string => (string)($item['title'] ?? ''),
            $items
        ));
    }

    /**
     * Require table or skip.
     *
     * @param string $table Table.
     * @return void
     */
    private function require_table(string $table): void {
        if (!$this->table_exists($table)) {
            $this->markTestSkipped("Required table {$table} is not installed.");
        }
    }

    /**
     * Check table exists.
     *
     * @param string $table Table.
     * @return bool
     */
    private function table_exists(string $table): bool {
        global $DB;

        return $DB->get_manager()->table_exists(new \xmldb_table($table));
    }

    /**
     * Filter record fields to table columns.
     *
     * @param string $table Table.
     * @param stdClass $record Record.
     * @return stdClass
     */
    private function filter_to_table_fields(string $table, stdClass $record): stdClass {
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
     * Generate UUID.
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