<?php
// This file is part of Moodle - https://moodle.org/.
//
// Moodle is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// any later version.

/**
 * Tests for UCKK Archive external work domain records.
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
use invalid_parameter_exception;
use mod_uckkarchive\local\external_work;
use moodle_exception;
use stdClass;

defined('MOODLE_INTERNAL') || die();

global $CFG;
require_once($CFG->dirroot . '/mod/uckkarchive/locallib.php');
require_once($CFG->dirroot . '/mod/uckkarchive/classes/local/external_work.php');

/**
 * Tests for external work references.
 *
 * External works are archive-owned references to outside material. They may
 * represent films, books, articles, websites, external videos, external images,
 * third-party PDFs, public archive references, or other works used by media and
 * content advisory records.
 *
 * These tests target the local domain/persistence class. Service-level tests
 * should cover capability checks, context validation, and permission-filtered
 * responses.
 *
 * @covers \mod_uckkarchive\local\external_work
 */
final class external_work_test extends advanced_testcase {
    /** @var stdClass Course fixture. */
    private stdClass $course;

    /** @var stdClass Module instance fixture. */
    private stdClass $archive;

    /** @var stdClass Course module fixture. */
    private stdClass $cm;

    /** @var context_module Module context fixture. */
    private context_module $context;

    /** @var stdClass User fixture. */
    private stdClass $user;

    /**
     * Reset database after each test and create a module fixture.
     */
    protected function setUp(): void {
        parent::setUp();
        $this->resetAfterTest(true);

        if (!$this->external_work_table_exists()) {
            $this->markTestSkipped('uckkarchive_external_work table is not installed.');
        }

        $this->course = $this->getDataGenerator()->create_course();
        $this->archive = $this->getDataGenerator()->create_module('uckkarchive', [
            'course' => $this->course->id,
            'name' => 'Archive for external work tests',
        ]);

        $this->cm = get_coursemodule_from_instance(
            'uckkarchive',
            $this->archive->id,
            $this->course->id,
            false,
            MUST_EXIST
        );

        $this->context = context_module::instance($this->cm->id);
        $this->user = $this->getDataGenerator()->create_user();

        $this->setUser($this->user);
    }

    /**
     * The class exposes canonical controlled vocabularies.
     */
    public function test_controlled_vocabularies_are_available(): void {
        $this->assertContains(external_work::TYPE_FILM, external_work::work_types());
        $this->assertContains(external_work::TYPE_BOOK, external_work::work_types());
        $this->assertContains(external_work::TYPE_ARTICLE, external_work::work_types());
        $this->assertContains(external_work::TYPE_EXTERNAL_VIDEO, external_work::work_types());
        $this->assertContains(external_work::TYPE_THIRD_PARTY_PDF, external_work::work_types());
        $this->assertContains(external_work::TYPE_OTHER, external_work::work_types());

        $this->assertContains(external_work::STATUS_DRAFT, external_work::statuses());
        $this->assertContains(external_work::STATUS_ACTIVE, external_work::statuses());
        $this->assertContains(external_work::STATUS_RESTRICTED, external_work::statuses());
        $this->assertContains(external_work::STATUS_ARCHIVED, external_work::statuses());
        $this->assertContains(external_work::STATUS_DELETED_SOFT, external_work::statuses());

        $this->assertContains(external_work::RIGHTS_UNKNOWN, external_work::rights_statuses());
        $this->assertContains(external_work::RIGHTS_THIRD_PARTY, external_work::rights_statuses());
        $this->assertContains(external_work::RIGHTS_OPEN_LICENSE, external_work::rights_statuses());
        $this->assertContains(external_work::RIGHTS_RESTRICTED_REFERENCE, external_work::rights_statuses());

        $this->assertContains(external_work::VISIBILITY_PRIVATE, external_work::visibilities());
        $this->assertContains(external_work::VISIBILITY_COURSE, external_work::visibilities());
        $this->assertContains(external_work::VISIBILITY_RESTRICTED_CULTURAL, external_work::visibilities());

        $this->assertContains(external_work::SUITABILITY_GUIDED, external_work::audience_suitabilities());
        $this->assertContains(external_work::SUITABILITY_RESTRICTED_CULTURAL, external_work::audience_suitabilities());
        $this->assertContains(external_work::SUITABILITY_STAFF_ONLY, external_work::audience_suitabilities());
    }

    /**
     * External work records can be created and fetched.
     */
    public function test_create_external_work_persists_normalised_record(): void {
        $record = external_work::create($this->external_work_data([
            'worktype' => external_work::TYPE_FILM,
            'title' => 'Maïna',
            'creator' => 'Michel Poulette',
            'publicationyear' => 2013,
            'sourceurl' => 'https://example.test/maina',
            'identifier' => 'maina-2013',
            'identifiertype' => 'slug',
            'metadata' => [
                'fixture' => 'create',
                'language_note' => 'fr',
            ],
        ]), (int)$this->user->id);

        $this->assertGreaterThan(0, (int)$record->id);
        $this->assertNotEmpty($record->uuid);
        $this->assertSame((int)$this->archive->id, (int)$record->archiveid);
        $this->assertSame((int)$this->course->id, (int)$record->courseid);
        $this->assertSame((int)$this->cm->id, (int)$record->cmid);
        $this->assertSame((int)$this->context->id, (int)$record->contextid);
        $this->assertSame((int)$this->user->id, (int)$record->ownerid);
        $this->assertSame(external_work::TYPE_FILM, $record->worktype);
        $this->assertSame(external_work::STATUS_DRAFT, $record->status);
        $this->assertSame(external_work::VISIBILITY_COURSE, $record->visibility);
        $this->assertSame(external_work::SUITABILITY_GUIDED, $record->audiencesuitability);
        $this->assertSame(external_work::RIGHTS_UNKNOWN, $record->rightsstatus);
        $this->assertSame('Maïna', $record->title);
        $this->assertSame('Michel Poulette', $record->creator);
        $this->assertSame(2013, (int)$record->publicationyear);

        $byid = external_work::get_record((int)$record->id, MUST_EXIST);
        $byuuid = external_work::get_record_by_uuid((string)$record->uuid, MUST_EXIST);

        $this->assertSame((int)$record->id, (int)$byid->id);
        $this->assertSame((int)$record->id, (int)$byuuid->id);
    }

    /**
     * Exported record contains stable service/output fields and decoded metadata.
     */
    public function test_export_record_returns_stable_array(): void {
        $record = external_work::create($this->external_work_data([
            'worktype' => external_work::TYPE_BOOK,
            'title' => 'The Body Keeps the Score',
            'creator' => 'Bessel van der Kolk',
            'publicationyear' => 2014,
            'rightsstatus' => external_work::RIGHTS_THIRD_PARTY,
            'metadata' => [
                'fixture' => 'export',
                'recommended_locator' => 'page_range',
            ],
        ]), (int)$this->user->id);

        $export = external_work::export_record($record);

        $this->assertSame((int)$record->id, $export['id']);
        $this->assertSame((string)$record->uuid, $export['uuid']);
        $this->assertSame((int)$this->archive->id, $export['archiveid']);
        $this->assertSame(external_work::TYPE_BOOK, $export['worktype']);
        $this->assertSame(external_work::RIGHTS_THIRD_PARTY, $export['rightsstatus']);
        $this->assertSame('The Body Keeps the Score', $export['title']);
        $this->assertSame('Bessel van der Kolk', $export['creator']);
        $this->assertSame(2014, $export['publicationyear']);
        $this->assertIsArray($export['metadata']);
        $this->assertSame('export', $export['metadata']['fixture']);
        $this->assertArrayHasKey('timecreated', $export);
        $this->assertArrayHasKey('timemodified', $export);
    }

    /**
     * Update merges incoming fields, normalises enums, and preserves identity.
     */
    public function test_update_external_work_changes_selected_fields(): void {
        $record = external_work::create($this->external_work_data([
            'title' => 'Draft external reference',
            'status' => external_work::STATUS_DRAFT,
            'rightsstatus' => external_work::RIGHTS_UNKNOWN,
        ]), (int)$this->user->id);

        $updater = $this->getDataGenerator()->create_user();

        $updated = external_work::update((int)$record->id, [
            'title' => 'Approved external reference',
            'status' => external_work::STATUS_ACTIVE,
            'visibility' => external_work::VISIBILITY_RESTRICTED,
            'audiencesuitability' => external_work::SUITABILITY_RESTRICTED,
            'rightsstatus' => external_work::RIGHTS_RESTRICTED_REFERENCE,
            'citation' => 'Citation text for classroom reference.',
            'metadata' => [
                'fixture' => 'update',
                'requires_context' => true,
            ],
        ], (int)$updater->id);

        $this->assertSame((int)$record->id, (int)$updated->id);
        $this->assertSame((string)$record->uuid, (string)$updated->uuid);
        $this->assertSame('Approved external reference', $updated->title);
        $this->assertSame(external_work::STATUS_ACTIVE, $updated->status);
        $this->assertSame(external_work::VISIBILITY_RESTRICTED, $updated->visibility);
        $this->assertSame(external_work::SUITABILITY_RESTRICTED, $updated->audiencesuitability);
        $this->assertSame(external_work::RIGHTS_RESTRICTED_REFERENCE, $updated->rightsstatus);
        $this->assertSame((int)$updater->id, (int)$updated->modifiedby);
        $this->assertGreaterThanOrEqual((int)$record->timemodified, (int)$updated->timemodified);

        $export = external_work::export_record($updated);
        $this->assertSame('update', $export['metadata']['fixture']);
        $this->assertTrue($export['metadata']['requires_context']);
    }

    /**
     * Updating with invalid work type fails.
     */
    public function test_update_rejects_invalid_work_type(): void {
        $record = external_work::create($this->external_work_data(), (int)$this->user->id);

        $this->expectException(invalid_parameter_exception::class);
        external_work::update((int)$record->id, [
            'worktype' => 'not_a_valid_work_type',
        ], (int)$this->user->id);
    }

    /**
     * Updating with invalid status fails.
     */
    public function test_update_rejects_invalid_status(): void {
        $record = external_work::create($this->external_work_data(), (int)$this->user->id);

        $this->expectException(invalid_parameter_exception::class);
        external_work::update((int)$record->id, [
            'status' => 'published_to_the_universe',
        ], (int)$this->user->id);
    }

    /**
     * Updating with invalid rights status fails.
     */
    public function test_update_rejects_invalid_rights_status(): void {
        $record = external_work::create($this->external_work_data(), (int)$this->user->id);

        $this->expectException(invalid_parameter_exception::class);
        external_work::update((int)$record->id, [
            'rightsstatus' => 'invented_rights_status',
        ], (int)$this->user->id);
    }

    /**
     * Missing title is rejected on creation.
     */
    public function test_create_requires_title(): void {
        $data = $this->external_work_data();
        unset($data['title']);

        $this->expectException(moodle_exception::class);
        external_work::create($data, (int)$this->user->id);
    }

    /**
     * Missing archive id is rejected on creation.
     */
    public function test_create_requires_archiveid(): void {
        $data = $this->external_work_data();
        unset($data['archiveid']);

        $this->expectException(moodle_exception::class);
        external_work::create($data, (int)$this->user->id);
    }

    /**
     * Records can be listed by archive and filtered by status, type, visibility, and rights status.
     */
    public function test_list_by_archive_filters_records(): void {
        $activebook = external_work::create($this->external_work_data([
            'title' => 'Active book',
            'worktype' => external_work::TYPE_BOOK,
            'status' => external_work::STATUS_ACTIVE,
            'visibility' => external_work::VISIBILITY_COURSE,
            'rightsstatus' => external_work::RIGHTS_OPEN_LICENSE,
        ]), (int)$this->user->id);

        external_work::create($this->external_work_data([
            'title' => 'Restricted film',
            'worktype' => external_work::TYPE_FILM,
            'status' => external_work::STATUS_RESTRICTED,
            'visibility' => external_work::VISIBILITY_RESTRICTED_CULTURAL,
            'rightsstatus' => external_work::RIGHTS_RESTRICTED_REFERENCE,
        ]), (int)$this->user->id);

        $matches = external_work::list_by_archive((int)$this->archive->id, [
            'worktype' => external_work::TYPE_BOOK,
            'status' => external_work::STATUS_ACTIVE,
            'visibility' => external_work::VISIBILITY_COURSE,
            'rightsstatus' => external_work::RIGHTS_OPEN_LICENSE,
        ]);

        $this->assertCount(1, $matches);
        $this->assertSame((int)$activebook->id, (int)$matches[0]->id);
    }

    /**
     * Records from another archive are not returned by list_by_archive.
     */
    public function test_list_by_archive_does_not_cross_archive_boundary(): void {
        $ownrecord = external_work::create($this->external_work_data([
            'title' => 'Current archive record',
        ]), (int)$this->user->id);

        $othercourse = $this->getDataGenerator()->create_course();
        $otherarchive = $this->getDataGenerator()->create_module('uckkarchive', [
            'course' => $othercourse->id,
            'name' => 'Other archive',
        ]);
        $othercm = get_coursemodule_from_instance('uckkarchive', $otherarchive->id, $othercourse->id, false, MUST_EXIST);
        $othercontext = context_module::instance($othercm->id);

        external_work::create([
            'archiveid' => (int)$otherarchive->id,
            'courseid' => (int)$othercourse->id,
            'cmid' => (int)$othercm->id,
            'contextid' => (int)$othercontext->id,
            'ownerid' => (int)$this->user->id,
            'worktype' => external_work::TYPE_WEBSITE,
            'status' => external_work::STATUS_ACTIVE,
            'visibility' => external_work::VISIBILITY_COURSE,
            'audiencesuitability' => external_work::SUITABILITY_GUIDED,
            'rightsstatus' => external_work::RIGHTS_UNKNOWN,
            'title' => 'Other archive record',
        ], (int)$this->user->id);

        $matches = external_work::list_by_archive((int)$this->archive->id);

        $this->assertNotEmpty($matches);

        $ids = array_map(static fn(stdClass $record): int => (int)$record->id, $matches);
        $this->assertContains((int)$ownrecord->id, $ids);
        $this->assertNotContains((int)$otherarchive->id, $ids);
    }

    /**
     * Count uses the same filter rules as list queries.
     */
    public function test_count_returns_filtered_count(): void {
        external_work::create($this->external_work_data([
            'title' => 'Open license work',
            'rightsstatus' => external_work::RIGHTS_OPEN_LICENSE,
        ]), (int)$this->user->id);

        external_work::create($this->external_work_data([
            'title' => 'Third party work',
            'rightsstatus' => external_work::RIGHTS_THIRD_PARTY,
        ]), (int)$this->user->id);

        $count = external_work::count([
            'archiveid' => (int)$this->archive->id,
            'rightsstatus' => external_work::RIGHTS_OPEN_LICENSE,
        ]);

        $this->assertSame(1, $count);
    }

    /**
     * Search matches title, creator, citation, identifier, URL, or description.
     */
    public function test_search_finds_external_work_by_query(): void {
        $expected = external_work::create($this->external_work_data([
            'title' => 'Trauma-informed teaching reference',
            'creator' => 'Archive Research Group',
            'identifier' => 'trauma-informed-ref',
            'description' => 'Reference used for advisory locator testing.',
        ]), (int)$this->user->id);

        external_work::create($this->external_work_data([
            'title' => 'Unrelated reference',
            'creator' => 'Someone else',
            'identifier' => 'unrelated',
        ]), (int)$this->user->id);

        $matches = external_work::search((int)$this->archive->id, 'trauma-informed');

        $ids = array_map(static fn(stdClass $record): int => (int)$record->id, $matches);

        $this->assertContains((int)$expected->id, $ids);
    }

    /**
     * Archive helper sets status to archived.
     */
    public function test_archive_sets_status_to_archived(): void {
        $record = external_work::create($this->external_work_data([
            'status' => external_work::STATUS_ACTIVE,
        ]), (int)$this->user->id);

        $updated = external_work::archive((int)$record->id, (int)$this->user->id);

        $this->assertSame(external_work::STATUS_ARCHIVED, $updated->status);
    }

    /**
     * Soft delete helper sets status to deleted_soft.
     */
    public function test_soft_delete_sets_status_to_deleted_soft(): void {
        $record = external_work::create($this->external_work_data([
            'status' => external_work::STATUS_ACTIVE,
        ]), (int)$this->user->id);

        $updated = external_work::soft_delete((int)$record->id, (int)$this->user->id);

        $this->assertSame(external_work::STATUS_DELETED_SOFT, $updated->status);
    }

    /**
     * Setters update controlled status and visibility fields.
     */
    public function test_set_status_and_visibility_update_record(): void {
        $record = external_work::create($this->external_work_data(), (int)$this->user->id);

        $statusupdated = external_work::set_status(
            (int)$record->id,
            external_work::STATUS_ACTIVE,
            (int)$this->user->id
        );

        $this->assertSame(external_work::STATUS_ACTIVE, $statusupdated->status);

        $visibilityupdated = external_work::set_visibility(
            (int)$record->id,
            external_work::VISIBILITY_RESTRICTED_CULTURAL,
            (int)$this->user->id
        );

        $this->assertSame(external_work::VISIBILITY_RESTRICTED_CULTURAL, $visibilityupdated->visibility);
    }

    /**
     * Restricted and cultural fields are preserved for policy-filtered callers.
     */
    public function test_restricted_external_work_preserves_cultural_protocol_metadata(): void {
        $record = external_work::create($this->external_work_data([
            'title' => 'Cultural protocol reference',
            'status' => external_work::STATUS_RESTRICTED,
            'visibility' => external_work::VISIBILITY_RESTRICTED_CULTURAL,
            'audiencesuitability' => external_work::SUITABILITY_RESTRICTED_CULTURAL,
            'rightsstatus' => external_work::RIGHTS_RESTRICTED_REFERENCE,
            'culturalprotocolnote' => 'Elder review required before public classroom use.',
            'metadata' => [
                'community_permission_required' => true,
                'not_for_public_export' => true,
            ],
        ]), (int)$this->user->id);

        $export = external_work::export_record($record);

        $this->assertSame(external_work::STATUS_RESTRICTED, $export['status']);
        $this->assertSame(external_work::VISIBILITY_RESTRICTED_CULTURAL, $export['visibility']);
        $this->assertSame(external_work::SUITABILITY_RESTRICTED_CULTURAL, $export['audiencesuitability']);
        $this->assertSame(external_work::RIGHTS_RESTRICTED_REFERENCE, $export['rightsstatus']);
        $this->assertSame('Elder review required before public classroom use.', $export['culturalprotocolnote']);
        $this->assertTrue($export['metadata']['community_permission_required']);
        $this->assertTrue($export['metadata']['not_for_public_export']);
    }

    /**
     * Instance wrapper exposes the same export data as static export.
     */
    public function test_from_record_wrapper_exports_record(): void {
        $record = external_work::create($this->external_work_data([
            'title' => 'Wrapper export reference',
        ]), (int)$this->user->id);

        $wrapper = external_work::from_record($record);
        $export = $wrapper->to_export();

        $this->assertSame((int)$record->id, $export['id']);
        $this->assertSame('Wrapper export reference', $export['title']);
        $this->assertSame((int)$this->archive->id, $export['archiveid']);
    }

    /**
     * Build base fixture data.
     *
     * @param array<string, mixed> $overrides Override fields.
     * @return array<string, mixed>
     */
    private function external_work_data(array $overrides = []): array {
        return array_merge([
            'archiveid' => (int)$this->archive->id,
            'courseid' => (int)$this->course->id,
            'cmid' => (int)$this->cm->id,
            'contextid' => (int)$this->context->id,
            'ownerid' => (int)$this->user->id,
            'createdby' => (int)$this->user->id,
            'modifiedby' => (int)$this->user->id,
            'worktype' => external_work::TYPE_OTHER,
            'status' => external_work::STATUS_DRAFT,
            'visibility' => external_work::VISIBILITY_COURSE,
            'audiencesuitability' => external_work::SUITABILITY_GUIDED,
            'rightsstatus' => external_work::RIGHTS_UNKNOWN,
            'title' => 'External work fixture',
            'subtitle' => '',
            'creator' => 'Fixture creator',
            'publisher' => '',
            'publicationyear' => 0,
            'language' => 'en',
            'sourceurl' => 'https://example.test/external-work',
            'identifier' => '',
            'identifiertype' => '',
            'citation' => '',
            'rightsstatement' => '',
            'licensekey' => '',
            'sourcenote' => '',
            'teachingnote' => '',
            'culturalprotocolnote' => '',
            'description' => 'External work test fixture.',
            'provenanceid' => 0,
            'metadata' => [
                'fixture' => 'external_work_test',
            ],
        ], $overrides);
    }

    /**
     * Return whether the external work table exists.
     *
     * @return bool
     */
    private function external_work_table_exists(): bool {
        global $DB;

        return $DB->get_manager()->table_exists(new \xmldb_table('uckkarchive_external_work'));
    }
}
