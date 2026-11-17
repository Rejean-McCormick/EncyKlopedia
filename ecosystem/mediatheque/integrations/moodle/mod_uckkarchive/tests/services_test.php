<?php
// This file is part of Moodle - https://moodle.org/
//
// Moodle is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// any later version.

/**
 * External service tests for mod_uckkarchive.
 *
 * @package    mod_uckkarchive
 * @category   test
 * @copyright  2026 Univers-Cité King Klown
 * @license    https://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later
 */

declare(strict_types=1);

namespace mod_uckkarchive;

defined('MOODLE_INTERNAL') || die();

global $CFG;

require_once($CFG->dirroot . '/webservice/tests/helpers.php');

/**
 * Tests for UCKK Archive external service classes.
 *
 * These tests focus on the service boundary:
 *
 * - services resolve module context correctly;
 * - services require the expected capabilities;
 * - services return data matching their declared external structures;
 * - media/content/external-work services do not expose restricted records to
 *   users without authority;
 * - service methods degrade predictably when optional tables/classes are not
 *   installed yet.
 *
 * Most tests insert records directly because the services themselves are the
 * unit under test. Domain-layer behaviour is covered by dedicated local class
 * tests.
 *
 * @coversNothing
 */
final class services_test extends \advanced_testcase {
    /** Plugin component. */
    private const COMPONENT = 'mod_uckkarchive';

    /** Main media table. */
    private const TABLE_MEDIA = 'uckkarchive_media';

    /** Media version table. */
    private const TABLE_MEDIA_VERSION = 'uckkarchive_media_version';

    /** Content marker table. */
    private const TABLE_CONTENT_MARKER = 'uckkarchive_content_marker';

    /** Content tag table. */
    private const TABLE_CONTENT_TAG = 'uckkarchive_content_tag';

    /** Content tag set table. */
    private const TABLE_CONTENT_TAG_SET = 'uckkarchive_content_tag_set';

    /** External work table. */
    private const TABLE_EXTERNAL_WORK = 'uckkarchive_external_work';

    /** Export table. */
    private const TABLE_EXPORT = 'uckkarchive_export';

    /**
     * Basic fixture.
     *
     * @return array<string, mixed>
     */
    private function create_activity_fixture(): array {
        $this->resetAfterTest(true);

        $generator = $this->getDataGenerator();
        $course = $generator->create_course();

        /** @var \stdClass $archive */
        $archive = $generator->create_module('uckkarchive', [
            'course' => $course->id,
            'name' => 'Services test archive',
        ]);

        $cm = get_coursemodule_from_instance('uckkarchive', $archive->id, $course->id, false, MUST_EXIST);
        $context = \context_module::instance((int)$cm->id);

        return [
            'course' => $course,
            'archive' => $archive,
            'cm' => $cm,
            'context' => $context,
        ];
    }

    /**
     * Create a user enrolled in the course with module capabilities.
     *
     * @param \stdClass $course Course.
     * @param \context_module $context Context.
     * @param string[] $capabilities Capabilities.
     * @return \stdClass
     */
    private function create_user_with_capabilities(\stdClass $course, \context_module $context, array $capabilities): \stdClass {
        $generator = $this->getDataGenerator();

        $user = $generator->create_user();
        $roleid = $generator->create_role();

        $generator->enrol_user((int)$user->id, (int)$course->id, $roleid);

        foreach ($capabilities as $capability) {
            if (get_capability_info($capability)) {
                assign_capability($capability, CAP_ALLOW, $roleid, $context->id, true);
            }
        }

        accesslib_clear_all_caches_for_unit_testing();

        return $user;
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
     * Require a table or skip the current test.
     *
     * @param string $table Table name.
     */
    private function require_table(string $table): void {
        if (!$this->table_exists($table)) {
            $this->markTestSkipped("Required table {$table} is not installed in this schema.");
        }
    }

    /**
     * Return first available column from candidates.
     *
     * @param string $table Table.
     * @param string[] $candidates Candidate columns.
     * @return string|null
     */
    private function first_column(string $table, array $candidates): ?string {
        global $DB;

        if (!$this->table_exists($table)) {
            return null;
        }

        $columns = $DB->get_columns($table);

        foreach ($candidates as $candidate) {
            if (array_key_exists($candidate, $columns)) {
                return $candidate;
            }
        }

        return null;
    }

    /**
     * Insert a record using only fields available in the target table.
     *
     * @param string $table Table name.
     * @param array<string, mixed> $record Record data.
     * @return \stdClass Inserted record.
     */
    private function insert_record(string $table, array $record): \stdClass {
        global $DB;

        $this->require_table($table);

        $columns = $DB->get_columns($table);
        $filtered = new \stdClass();

        foreach ($record as $field => $value) {
            if (array_key_exists($field, $columns)) {
                $filtered->{$field} = $value;
            }
        }

        if (array_key_exists('timecreated', $columns) && !property_exists($filtered, 'timecreated')) {
            $filtered->timecreated = time();
        }

        if (array_key_exists('timemodified', $columns) && !property_exists($filtered, 'timemodified')) {
            $filtered->timemodified = time();
        }

        if (array_key_exists('uuid', $columns) && !property_exists($filtered, 'uuid')) {
            $filtered->uuid = \core\uuid::generate();
        }

        $filtered->id = $DB->insert_record($table, $filtered);

        return $DB->get_record($table, ['id' => $filtered->id], '*', MUST_EXIST);
    }

    /**
     * Create a basic media record.
     *
     * @param array<string, mixed> $fixture Activity fixture.
     * @param array<string, mixed> $overrides Override values.
     * @return \stdClass
     */
    private function create_media(array $fixture, array $overrides = []): \stdClass {
        $now = time();

        return $this->insert_record(self::TABLE_MEDIA, array_merge([
            'archiveid' => (int)$fixture['archive']->id,
            'courseid' => (int)$fixture['course']->id,
            'cmid' => (int)$fixture['cm']->id,
            'contextid' => (int)$fixture['context']->id,
            'uuid' => \core\uuid::generate(),
            'title' => 'Services media',
            'description' => 'Media record created by services_test.',
            'mediatype' => 'image',
            'mimetype' => 'image/png',
            'status' => 'active',
            'visibility' => 'course',
            'audiencesuitability' => 'guided',
            'createdby' => (int)get_admin()->id,
            'modifiedby' => (int)get_admin()->id,
            'timecreated' => $now,
            'timemodified' => $now,
            'metadata' => json_encode(['fixture' => 'services_test']),
        ], $overrides));
    }

    /**
     * Create a basic content tag.
     *
     * @param array<string, mixed> $fixture Activity fixture.
     * @param array<string, mixed> $overrides Overrides.
     * @return \stdClass
     */
    private function create_content_tag(array $fixture, array $overrides = []): \stdClass {
        return $this->insert_record(self::TABLE_CONTENT_TAG, array_merge([
            'archiveid' => (int)$fixture['archive']->id,
            'courseid' => (int)$fixture['course']->id,
            'cmid' => (int)$fixture['cm']->id,
            'contextid' => (int)$fixture['context']->id,
            'uuid' => \core\uuid::generate(),
            'tagkey' => 'violence_notice',
            'name' => 'Violence notice',
            'label' => 'Violence notice',
            'description' => 'A content advisory test tag.',
            'category' => 'general_advisory',
            'severity' => 'notice',
            'defaultaudience' => 'guided',
            'reviewstate' => 'approved',
            'active' => 1,
            'sortorder' => 10,
            'metadata' => json_encode(['fixture' => 'services_test']),
            'timecreated' => time(),
            'timemodified' => time(),
        ], $overrides));
    }

    /**
     * Create a basic content marker.
     *
     * @param array<string, mixed> $fixture Fixture.
     * @param \stdClass $media Media.
     * @param \stdClass $tag Tag.
     * @param array<string, mixed> $overrides Overrides.
     * @return \stdClass
     */
    private function create_content_marker(
        array $fixture,
        \stdClass $media,
        \stdClass $tag,
        array $overrides = []
    ): \stdClass {
        return $this->insert_record(self::TABLE_CONTENT_MARKER, array_merge([
            'archiveid' => (int)$fixture['archive']->id,
            'courseid' => (int)$fixture['course']->id,
            'cmid' => (int)$fixture['cm']->id,
            'contextid' => (int)$fixture['context']->id,
            'uuid' => \core\uuid::generate(),
            'mediaid' => (int)$media->id,
            'tagid' => (int)$tag->id,
            'tagkey' => $tag->tagkey ?? 'violence_notice',
            'locatortype' => 'whole_work',
            'locator' => '',
            'severity' => 'notice',
            'audiencesuitability' => 'guided',
            'reviewstate' => 'approved',
            'visibility' => 'course',
            'restricted' => 0,
            'createdby' => (int)get_admin()->id,
            'modifiedby' => (int)get_admin()->id,
            'metadata' => json_encode(['fixture' => 'services_test']),
            'timecreated' => time(),
            'timemodified' => time(),
        ], $overrides));
    }

    /**
     * Create a basic external work.
     *
     * @param array<string, mixed> $fixture Fixture.
     * @param array<string, mixed> $overrides Overrides.
     * @return \stdClass
     */
    private function create_external_work(array $fixture, array $overrides = []): \stdClass {
        return $this->insert_record(self::TABLE_EXTERNAL_WORK, array_merge([
            'archiveid' => (int)$fixture['archive']->id,
            'courseid' => (int)$fixture['course']->id,
            'cmid' => (int)$fixture['cm']->id,
            'contextid' => (int)$fixture['context']->id,
            'uuid' => \core\uuid::generate(),
            'worktype' => 'film',
            'status' => 'active',
            'visibility' => 'course',
            'audiencesuitability' => 'guided',
            'rightsstatus' => 'unknown',
            'title' => 'External work test',
            'creator' => 'Service Test',
            'publicationyear' => 2026,
            'sourceurl' => 'https://example.invalid/work',
            'identifier' => 'svc-test-001',
            'identifiertype' => 'local',
            'citation' => 'Service Test. External work test.',
            'metadata' => json_encode(['fixture' => 'services_test']),
            'timecreated' => time(),
            'timemodified' => time(),
        ], $overrides));
    }

    /**
     * Test media listing service return contract.
     *
     * @return void
     */
    public function test_get_media_returns_permission_filtered_media(): void {
        $fixture = $this->create_activity_fixture();

        $this->require_table(self::TABLE_MEDIA);

        $user = $this->create_user_with_capabilities($fixture['course'], $fixture['context'], [
            'mod/uckkarchive:view',
            'mod/uckkarchive:viewmedia',
        ]);

        $this->create_media($fixture, [
            'title' => 'Visible media',
            'visibility' => 'course',
            'status' => 'active',
        ]);

        $this->setUser($user);

        $result = \mod_uckkarchive\external\get_media::execute(
            (int)$fixture['cm']->id,
            [],
            0,
            10,
            'timemodified',
            'desc',
            []
        );

        $clean = \core_external\external_api::clean_returnvalue(
            \mod_uckkarchive\external\get_media::execute_returns(),
            $result
        );

        $this->assertArrayHasKey('media', $clean);
        $this->assertArrayHasKey('pagination', $clean);
        $this->assertArrayHasKey('permissions', $clean);
        $this->assertArrayHasKey('warnings', $clean);
        $this->assertGreaterThanOrEqual(1, $clean['pagination']['total']);
        $this->assertTrue($clean['permissions']['viewmedia']);
    }

    /**
     * Test media listing requires viewmedia.
     *
     * @return void
     */
    public function test_get_media_requires_viewmedia_capability(): void {
        $fixture = $this->create_activity_fixture();

        $this->require_table(self::TABLE_MEDIA);

        $user = $this->create_user_with_capabilities($fixture['course'], $fixture['context'], []);
        $this->setUser($user);

        $this->expectException(\required_capability_exception::class);

        \mod_uckkarchive\external\get_media::execute((int)$fixture['cm']->id);
    }

    /**
     * Test get_media_item service can return a visible media record.
     *
     * @return void
     */
    public function test_get_media_item_returns_record(): void {
        $fixture = $this->create_activity_fixture();

        $this->require_table(self::TABLE_MEDIA);

        $media = $this->create_media($fixture, [
            'title' => 'Single media',
            'visibility' => 'course',
        ]);

        $user = $this->create_user_with_capabilities($fixture['course'], $fixture['context'], [
            'mod/uckkarchive:view',
            'mod/uckkarchive:viewmedia',
        ]);

        $this->setUser($user);

        $result = \mod_uckkarchive\external\get_media_item::execute(
            (int)$fixture['cm']->id,
            (int)$media->id,
            '',
            []
        );

        $clean = \core_external\external_api::clean_returnvalue(
            \mod_uckkarchive\external\get_media_item::execute_returns(),
            $result
        );

        $this->assertSame((int)$media->id, (int)$clean['media']['id']);
        $this->assertSame('Single media', $clean['media']['title']);
    }

    /**
     * Test update_media changes editable fields.
     *
     * @return void
     */
    public function test_update_media_changes_title(): void {
        global $DB;

        $fixture = $this->create_activity_fixture();

        $this->require_table(self::TABLE_MEDIA);

        $media = $this->create_media($fixture, [
            'title' => 'Old media title',
            'visibility' => 'course',
        ]);

        $user = $this->create_user_with_capabilities($fixture['course'], $fixture['context'], [
            'mod/uckkarchive:view',
            'mod/uckkarchive:viewmedia',
            'mod/uckkarchive:editmedia',
        ]);

        $this->setUser($user);

        $result = \mod_uckkarchive\external\update_media::execute(
            (int)$fixture['cm']->id,
            (int)$fixture['archive']->id,
            (int)$media->id,
            '',
            'New media title',
            '',
            '',
            '',
            '',
            '',
            '',
            '',
            '',
            '',
            0,
            '',
            'PHPUnit update'
        );

        $clean = \core_external\external_api::clean_returnvalue(
            \mod_uckkarchive\external\update_media::execute_returns(),
            $result
        );

        $updated = $DB->get_record(self::TABLE_MEDIA, ['id' => (int)$media->id], '*', MUST_EXIST);

        $this->assertSame('updated', $clean['status']);
        $this->assertSame('New media title', $updated->title);
        $this->assertContains('title', $clean['changedfields']);
    }

    /**
     * Test delete_media soft-deletes a media record.
     *
     * @return void
     */
    public function test_delete_media_soft_deletes_record(): void {
        global $DB;

        $fixture = $this->create_activity_fixture();

        $this->require_table(self::TABLE_MEDIA);

        $media = $this->create_media($fixture, [
            'status' => 'active',
            'visibility' => 'course',
        ]);

        $user = $this->create_user_with_capabilities($fixture['course'], $fixture['context'], [
            'mod/uckkarchive:view',
            'mod/uckkarchive:viewmedia',
            'mod/uckkarchive:deletemedia',
        ]);

        $this->setUser($user);

        $result = \mod_uckkarchive\external\delete_media::execute(
            (int)$fixture['cm']->id,
            (int)$media->id,
            '',
            'PHPUnit delete',
            false
        );

        $clean = \core_external\external_api::clean_returnvalue(
            \mod_uckkarchive\external\delete_media::execute_returns(),
            $result
        );

        $updated = $DB->get_record(self::TABLE_MEDIA, ['id' => (int)$media->id], '*', MUST_EXIST);

        $this->assertSame((int)$media->id, (int)$clean['mediaid']);
        $this->assertSame('deleted_soft', $updated->status);
    }

    /**
     * Test search_media returns matching records.
     *
     * @return void
     */
    public function test_search_media_returns_matching_media(): void {
        $fixture = $this->create_activity_fixture();

        $this->require_table(self::TABLE_MEDIA);

        $this->create_media($fixture, [
            'title' => 'Needle media title',
            'visibility' => 'course',
            'status' => 'active',
        ]);

        $this->create_media($fixture, [
            'title' => 'Other media title',
            'visibility' => 'course',
            'status' => 'active',
        ]);

        $user = $this->create_user_with_capabilities($fixture['course'], $fixture['context'], [
            'mod/uckkarchive:view',
            'mod/uckkarchive:viewmedia',
        ]);

        $this->setUser($user);

        $result = \mod_uckkarchive\external\search_media::execute(
            (int)$fixture['cm']->id,
            'Needle',
            [],
            0,
            20,
            'timemodified',
            'desc'
        );

        $clean = \core_external\external_api::clean_returnvalue(
            \mod_uckkarchive\external\search_media::execute_returns(),
            $result
        );

        $this->assertArrayHasKey('media', $clean);
        $titles = array_map(static fn(array $record): string => $record['title'], $clean['media']);
        $this->assertContains('Needle media title', $titles);
    }

    /**
     * Test get_media_versions returns versions for media.
     *
     * @return void
     */
    public function test_get_media_versions_returns_version_records(): void {
        $fixture = $this->create_activity_fixture();

        $this->require_table(self::TABLE_MEDIA);
        $this->require_table(self::TABLE_MEDIA_VERSION);

        $media = $this->create_media($fixture, [
            'visibility' => 'course',
            'status' => 'active',
        ]);

        $version = $this->insert_record(self::TABLE_MEDIA_VERSION, [
            'uuid' => \core\uuid::generate(),
            'mediaid' => (int)$media->id,
            'versionno' => 1,
            'versionnumber' => 1,
            'label' => 'Initial version',
            'status' => 'active',
            'filearea' => 'media_original',
            'filename' => 'example.png',
            'mimetype' => 'image/png',
            'filesize' => 100,
            'createdby' => (int)get_admin()->id,
            'modifiedby' => (int)get_admin()->id,
            'metadata' => json_encode(['fixture' => 'services_test']),
            'timecreated' => time(),
            'timemodified' => time(),
        ]);

        $user = $this->create_user_with_capabilities($fixture['course'], $fixture['context'], [
            'mod/uckkarchive:view',
            'mod/uckkarchive:viewmedia',
            'mod/uckkarchive:downloadmedia',
        ]);

        $this->setUser($user);

        $result = \mod_uckkarchive\external\get_media_versions::execute(
            (int)$fixture['cm']->id,
            (int)$media->id,
            [
                'deleted' => false,
                'files' => false,
                'metadata' => true,
                'hashes' => true,
            ]
        );

        $clean = \core_external\external_api::clean_returnvalue(
            \mod_uckkarchive\external\get_media_versions::execute_returns(),
            $result
        );

        $this->assertSame((int)$media->id, (int)$clean['mediaid']);
        $this->assertCount(1, $clean['versions']);
        $this->assertSame((int)$version->id, (int)$clean['versions'][0]['id']);
    }

    /**
     * Test export_media creates an export request.
     *
     * @return void
     */
    public function test_export_media_creates_export_record(): void {
        global $DB;

        $fixture = $this->create_activity_fixture();

        $this->require_table(self::TABLE_MEDIA);
        $this->require_table(self::TABLE_EXPORT);

        $media = $this->create_media($fixture, [
            'visibility' => 'course',
            'status' => 'active',
        ]);

        $user = $this->create_user_with_capabilities($fixture['course'], $fixture['context'], [
            'mod/uckkarchive:view',
            'mod/uckkarchive:viewmedia',
            'mod/uckkarchive:export',
            'mod/uckkarchive:exportmedia',
            'mod/uckkarchive:downloadmedia',
        ]);

        $this->setUser($user);

        $result = \mod_uckkarchive\external\export_media::execute(
            (int)$fixture['cm']->id,
            [(int)$media->id],
            'zip',
            [
                'includeoriginals' => false,
                'includederivatives' => false,
                'includethumbnails' => false,
                'includepreviews' => false,
                'includecaptions' => false,
                'includetranscripts' => false,
                'includeattachments' => false,
                'includeversions' => false,
                'includerelations' => false,
                'includetags' => false,
                'includeadvisories' => false,
                'includeexternalrefs' => false,
                'redactionlevel' => 'standard',
                'visibility' => 'private',
            ],
            'PHPUnit export'
        );

        $clean = \core_external\external_api::clean_returnvalue(
            \mod_uckkarchive\external\export_media::execute_returns(),
            $result
        );

        $this->assertGreaterThan(0, $clean['exportid']);
        $this->assertSame(1, $clean['mediaexported']);
        $this->assertSame(0, $clean['mediaexcluded']);
        $this->assertTrue($DB->record_exists(self::TABLE_EXPORT, ['id' => $clean['exportid']]));
    }

    /**
     * Test content marker retrieval service.
     *
     * @return void
     */
    public function test_get_content_markers_returns_media_markers(): void {
        $fixture = $this->create_activity_fixture();

        $this->require_table(self::TABLE_MEDIA);
        $this->require_table(self::TABLE_CONTENT_TAG);
        $this->require_table(self::TABLE_CONTENT_MARKER);

        $media = $this->create_media($fixture);
        $tag = $this->create_content_tag($fixture);
        $marker = $this->create_content_marker($fixture, $media, $tag);

        $user = $this->create_user_with_capabilities($fixture['course'], $fixture['context'], [
            'mod/uckkarchive:view',
            'mod/uckkarchive:viewmedia',
            'mod/uckkarchive:viewadvisories',
        ]);

        $this->setUser($user);

        $result = \mod_uckkarchive\external\get_content_markers::execute(
            (int)$fixture['cm']->id,
            [
                'mediaid' => (int)$media->id,
            ],
            [
                'restricted' => false,
                'reviews' => false,
            ]
        );

        $clean = \core_external\external_api::clean_returnvalue(
            \mod_uckkarchive\external\get_content_markers::execute_returns(),
            $result
        );

        $this->assertArrayHasKey('markers', $clean);

        $ids = array_map(static fn(array $record): int => (int)$record['id'], $clean['markers']);
        $this->assertContains((int)$marker->id, $ids);
    }

    /**
     * Test update_content_marker modifies marker state.
     *
     * @return void
     */
    public function test_update_content_marker_changes_review_state(): void {
        global $DB;

        $fixture = $this->create_activity_fixture();

        $this->require_table(self::TABLE_MEDIA);
        $this->require_table(self::TABLE_CONTENT_TAG);
        $this->require_table(self::TABLE_CONTENT_MARKER);

        $media = $this->create_media($fixture);
        $tag = $this->create_content_tag($fixture);
        $marker = $this->create_content_marker($fixture, $media, $tag, [
            'reviewstate' => 'draft',
        ]);

        $user = $this->create_user_with_capabilities($fixture['course'], $fixture['context'], [
            'mod/uckkarchive:view',
            'mod/uckkarchive:viewmedia',
            'mod/uckkarchive:viewadvisories',
            'mod/uckkarchive:manageadvisories',
        ]);

        $this->setUser($user);

        $result = \mod_uckkarchive\external\update_content_marker::execute(
            (int)$fixture['cm']->id,
            (int)$marker->id,
            [
                'reviewstate' => 'approved',
                'severity' => 'notice',
                'audiencesuitability' => 'guided',
            ],
            'PHPUnit marker update'
        );

        $clean = \core_external\external_api::clean_returnvalue(
            \mod_uckkarchive\external\update_content_marker::execute_returns(),
            $result
        );

        $updated = $DB->get_record(self::TABLE_CONTENT_MARKER, ['id' => (int)$marker->id], '*', MUST_EXIST);

        $this->assertSame('updated', $clean['status']);
        $this->assertSame('approved', $updated->reviewstate);
    }

    /**
     * Test delete_content_marker soft-deletes or removes marker according to implementation.
     *
     * @return void
     */
    public function test_delete_content_marker_returns_deleted_status(): void {
        $fixture = $this->create_activity_fixture();

        $this->require_table(self::TABLE_MEDIA);
        $this->require_table(self::TABLE_CONTENT_TAG);
        $this->require_table(self::TABLE_CONTENT_MARKER);

        $media = $this->create_media($fixture);
        $tag = $this->create_content_tag($fixture);
        $marker = $this->create_content_marker($fixture, $media, $tag);

        $user = $this->create_user_with_capabilities($fixture['course'], $fixture['context'], [
            'mod/uckkarchive:view',
            'mod/uckkarchive:viewmedia',
            'mod/uckkarchive:viewadvisories',
            'mod/uckkarchive:manageadvisories',
        ]);

        $this->setUser($user);

        $result = \mod_uckkarchive\external\delete_content_marker::execute(
            (int)$fixture['cm']->id,
            (int)$marker->id,
            false,
            'PHPUnit marker delete'
        );

        $clean = \core_external\external_api::clean_returnvalue(
            \mod_uckkarchive\external\delete_content_marker::execute_returns(),
            $result
        );

        $this->assertSame((int)$marker->id, (int)$clean['markerid']);
        $this->assertContains($clean['status'], ['deleted', 'deleted_soft']);
    }

    /**
     * Test content tag listing service.
     *
     * @return void
     */
    public function test_get_content_tags_returns_tags(): void {
        $fixture = $this->create_activity_fixture();

        $this->require_table(self::TABLE_CONTENT_TAG);

        $tag = $this->create_content_tag($fixture, [
            'tagkey' => 'services_tag',
            'label' => 'Services tag',
        ]);

        $user = $this->create_user_with_capabilities($fixture['course'], $fixture['context'], [
            'mod/uckkarchive:view',
            'mod/uckkarchive:viewadvisories',
        ]);

        $this->setUser($user);

        $result = \mod_uckkarchive\external\get_content_tags::execute(
            (int)$fixture['cm']->id,
            [
                'active' => true,
            ]
        );

        $clean = \core_external\external_api::clean_returnvalue(
            \mod_uckkarchive\external\get_content_tags::execute_returns(),
            $result
        );

        $this->assertArrayHasKey('tags', $clean);
        $tagkeys = array_map(static fn(array $record): string => $record['tagkey'], $clean['tags']);
        $this->assertContains($tag->tagkey, $tagkeys);
    }

    /**
     * Test content tag set listing service.
     *
     * @return void
     */
    public function test_get_content_tag_sets_returns_sets(): void {
        $fixture = $this->create_activity_fixture();

        $this->require_table(self::TABLE_CONTENT_TAG_SET);

        $set = $this->insert_record(self::TABLE_CONTENT_TAG_SET, [
            'archiveid' => (int)$fixture['archive']->id,
            'courseid' => (int)$fixture['course']->id,
            'cmid' => (int)$fixture['cm']->id,
            'contextid' => (int)$fixture['context']->id,
            'uuid' => \core\uuid::generate(),
            'setkey' => 'services_set',
            'name' => 'Services set',
            'label' => 'Services set',
            'description' => 'Service test tag set.',
            'active' => 1,
            'sortorder' => 1,
            'metadata' => json_encode(['fixture' => 'services_test']),
            'timecreated' => time(),
            'timemodified' => time(),
        ]);

        $user = $this->create_user_with_capabilities($fixture['course'], $fixture['context'], [
            'mod/uckkarchive:view',
            'mod/uckkarchive:viewadvisories',
        ]);

        $this->setUser($user);

        $result = \mod_uckkarchive\external\get_content_tag_sets::execute(
            (int)$fixture['cm']->id,
            [
                'active' => true,
            ]
        );

        $clean = \core_external\external_api::clean_returnvalue(
            \mod_uckkarchive\external\get_content_tag_sets::execute_returns(),
            $result
        );

        $this->assertArrayHasKey('tagsets', $clean);
        $ids = array_map(static fn(array $record): int => (int)$record['id'], $clean['tagsets']);
        $this->assertContains((int)$set->id, $ids);
    }

    /**
     * Test external work retrieval service.
     *
     * @return void
     */
    public function test_get_external_work_returns_record(): void {
        $fixture = $this->create_activity_fixture();

        $this->require_table(self::TABLE_EXTERNAL_WORK);

        $work = $this->create_external_work($fixture, [
            'title' => 'Single external work',
        ]);

        $user = $this->create_user_with_capabilities($fixture['course'], $fixture['context'], [
            'mod/uckkarchive:view',
            'mod/uckkarchive:viewmedia',
            'mod/uckkarchive:viewadvisories',
        ]);

        $this->setUser($user);

        $result = \mod_uckkarchive\external\get_external_work::execute(
            (int)$fixture['cm']->id,
            (int)$work->id,
            ''
        );

        $clean = \core_external\external_api::clean_returnvalue(
            \mod_uckkarchive\external\get_external_work::execute_returns(),
            $result
        );

        $this->assertSame((int)$work->id, (int)$clean['externalwork']['id']);
        $this->assertSame('Single external work', $clean['externalwork']['title']);
    }

    /**
     * Test external work search/listing service.
     *
     * @return void
     */
    public function test_get_external_works_returns_records(): void {
        $fixture = $this->create_activity_fixture();

        $this->require_table(self::TABLE_EXTERNAL_WORK);

        $work = $this->create_external_work($fixture, [
            'title' => 'List external work',
        ]);

        $user = $this->create_user_with_capabilities($fixture['course'], $fixture['context'], [
            'mod/uckkarchive:view',
            'mod/uckkarchive:viewmedia',
            'mod/uckkarchive:viewadvisories',
        ]);

        $this->setUser($user);

        $result = \mod_uckkarchive\external\get_external_works::execute(
            (int)$fixture['cm']->id,
            [
                'query' => 'List external',
            ],
            0,
            20,
            'timemodified',
            'desc'
        );

        $clean = \core_external\external_api::clean_returnvalue(
            \mod_uckkarchive\external\get_external_works::execute_returns(),
            $result
        );

        $this->assertArrayHasKey('externalworks', $clean);

        $ids = array_map(static fn(array $record): int => (int)$record['id'], $clean['externalworks']);
        $this->assertContains((int)$work->id, $ids);
    }

    /**
     * Test update_external_work modifies title.
     *
     * @return void
     */
    public function test_update_external_work_changes_title(): void {
        global $DB;

        $fixture = $this->create_activity_fixture();

        $this->require_table(self::TABLE_EXTERNAL_WORK);

        $work = $this->create_external_work($fixture, [
            'title' => 'Old work title',
        ]);

        $user = $this->create_user_with_capabilities($fixture['course'], $fixture['context'], [
            'mod/uckkarchive:view',
            'mod/uckkarchive:viewmedia',
            'mod/uckkarchive:viewadvisories',
            'mod/uckkarchive:manageadvisories',
        ]);

        $this->setUser($user);

        $result = \mod_uckkarchive\external\update_external_work::execute(
            (int)$fixture['cm']->id,
            (int)$work->id,
            '',
            [
                'title' => 'New work title',
            ],
            'PHPUnit external work update'
        );

        $clean = \core_external\external_api::clean_returnvalue(
            \mod_uckkarchive\external\update_external_work::execute_returns(),
            $result
        );

        $updated = $DB->get_record(self::TABLE_EXTERNAL_WORK, ['id' => (int)$work->id], '*', MUST_EXIST);

        $this->assertSame('updated', $clean['status']);
        $this->assertSame('New work title', $updated->title);
        $this->assertContains('title', $clean['changedfields']);
    }

    /**
     * Test service declarations exist for generated services.
     *
     * @return void
     */
    public function test_generated_service_classes_expose_external_contracts(): void {
        $classes = [
            \mod_uckkarchive\external\add_content_marker::class,
            \mod_uckkarchive\external\add_external_work::class,
            \mod_uckkarchive\external\add_media_collection::class,
            \mod_uckkarchive\external\add_media_relation::class,
            \mod_uckkarchive\external\add_media_to_collection::class,
            \mod_uckkarchive\external\add_media_version::class,
            \mod_uckkarchive\external\delete_content_marker::class,
            \mod_uckkarchive\external\export_collection::class,
            \mod_uckkarchive\external\export_media::class,
            \mod_uckkarchive\external\get_content_markers::class,
            \mod_uckkarchive\external\get_content_tag_sets::class,
            \mod_uckkarchive\external\get_content_tags::class,
            \mod_uckkarchive\external\get_external_work::class,
            \mod_uckkarchive\external\get_external_works::class,
            \mod_uckkarchive\external\get_media_card::class,
            \mod_uckkarchive\external\get_media_collection::class,
            \mod_uckkarchive\external\get_media_collections::class,
            \mod_uckkarchive\external\get_media_relations::class,
            \mod_uckkarchive\external\get_media_versions::class,
            \mod_uckkarchive\external\remove_media_from_collection::class,
            \mod_uckkarchive\external\remove_media_relation::class,
            \mod_uckkarchive\external\review_content_marker::class,
            \mod_uckkarchive\external\tag_media::class,
            \mod_uckkarchive\external\untag_media::class,
            \mod_uckkarchive\external\update_content_marker::class,
            \mod_uckkarchive\external\update_external_work::class,
            \mod_uckkarchive\external\update_media_collection::class,
        ];

        foreach ($classes as $class) {
            $this->assertTrue(class_exists($class), "{$class} must exist.");
            $this->assertTrue(method_exists($class, 'execute_parameters'), "{$class} must define execute_parameters().");
            $this->assertTrue(method_exists($class, 'execute'), "{$class} must define execute().");
            $this->assertTrue(method_exists($class, 'execute_returns'), "{$class} must define execute_returns().");
        }
    }

    /**
     * Test restricted media is not visible to ordinary media viewers.
     *
     * @return void
     */
    public function test_restricted_media_is_filtered_from_get_media_for_regular_user(): void {
        $fixture = $this->create_activity_fixture();

        $this->require_table(self::TABLE_MEDIA);

        $this->create_media($fixture, [
            'title' => 'Restricted services media',
            'visibility' => 'restricted',
            'status' => 'restricted',
        ]);

        $user = $this->create_user_with_capabilities($fixture['course'], $fixture['context'], [
            'mod/uckkarchive:view',
            'mod/uckkarchive:viewmedia',
        ]);

        $this->setUser($user);

        $result = \mod_uckkarchive\external\get_media::execute(
            (int)$fixture['cm']->id,
            [],
            0,
            50,
            'timemodified',
            'desc',
            []
        );

        $clean = \core_external\external_api::clean_returnvalue(
            \mod_uckkarchive\external\get_media::execute_returns(),
            $result
        );

        $titles = array_map(static fn(array $record): string => $record['title'], $clean['media']);

        $this->assertNotContains('Restricted services media', $titles);
    }

    /**
     * Test restricted media can be visible with restricted capability.
     *
     * @return void
     */
    public function test_restricted_media_can_be_returned_to_restricted_viewer(): void {
        $fixture = $this->create_activity_fixture();

        $this->require_table(self::TABLE_MEDIA);

        $this->create_media($fixture, [
            'title' => 'Restricted visible media',
            'visibility' => 'restricted',
            'status' => 'restricted',
        ]);

        $user = $this->create_user_with_capabilities($fixture['course'], $fixture['context'], [
            'mod/uckkarchive:view',
            'mod/uckkarchive:viewmedia',
            'mod/uckkarchive:viewrestrictedmedia',
        ]);

        $this->setUser($user);

        $result = \mod_uckkarchive\external\get_media::execute(
            (int)$fixture['cm']->id,
            [],
            0,
            50,
            'timemodified',
            'desc',
            []
        );

        $clean = \core_external\external_api::clean_returnvalue(
            \mod_uckkarchive\external\get_media::execute_returns(),
            $result
        );

        $titles = array_map(static fn(array $record): string => $record['title'], $clean['media']);

        $this->assertContains('Restricted visible media', $titles);
    }
}

