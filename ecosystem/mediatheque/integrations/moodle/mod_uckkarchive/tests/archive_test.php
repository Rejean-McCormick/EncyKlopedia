<?php
// This file is part of Moodle - https://moodle.org/
//
// Moodle is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// any later version.

/**
 * Tests for mod_uckkarchive helper layer.
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
use mod_uckkarchive\local\content_marker;
use mod_uckkarchive\local\external_work;
use mod_uckkarchive\local\file_area_registry;
use mod_uckkarchive\local\media;
use mod_uckkarchive\local\media_collection;
use mod_uckkarchive\local\media_version;
use stdClass;

defined('MOODLE_INTERNAL') || die();

global $CFG;
require_once($CFG->dirroot . '/mod/uckkarchive/locallib.php');

/**
 * Tests for archive local helpers.
 *
 * These tests intentionally target stable procedural helpers from locallib.php
 * and lightweight local-domain integration points. Workflow-heavy behaviour
 * belongs in service-specific tests.
 *
 * @coversNothing
 */
final class archive_test extends advanced_testcase {
    /**
     * Reset DB after each test.
     */
    protected function setUp(): void {
        parent::setUp();
        $this->resetAfterTest(true);
    }

    /**
     * Canonical archive status list should contain the expected workflow states.
     */
    public function test_get_statuses_returns_canonical_archive_item_statuses(): void {
        $statuses = uckkarchive_get_statuses();

        $this->assertContains(UCKKARCHIVE_STATUS_DRAFT, $statuses);
        $this->assertContains(UCKKARCHIVE_STATUS_SUBMITTED, $statuses);
        $this->assertContains(UCKKARCHIVE_STATUS_UNDER_REVIEW, $statuses);
        $this->assertContains(UCKKARCHIVE_STATUS_VALIDATED, $statuses);
        $this->assertContains(UCKKARCHIVE_STATUS_PUBLISHED, $statuses);
        $this->assertContains(UCKKARCHIVE_STATUS_RESTRICTED, $statuses);
        $this->assertContains(UCKKARCHIVE_STATUS_CONTESTED, $statuses);
        $this->assertContains(UCKKARCHIVE_STATUS_INVALIDATED, $statuses);
        $this->assertContains(UCKKARCHIVE_STATUS_SUPERSEDED, $statuses);
        $this->assertContains(UCKKARCHIVE_STATUS_ARCHIVED, $statuses);
    }

    /**
     * Visibility list should use the canonical UCKK archive visibility values.
     */
    public function test_get_visibilities_returns_canonical_archive_visibilities(): void {
        $visibilities = uckkarchive_get_visibilities();

        $this->assertContains(UCKKARCHIVE_VISIBILITY_PRIVATE, $visibilities);
        $this->assertContains(UCKKARCHIVE_VISIBILITY_COURSE, $visibilities);
        $this->assertContains(UCKKARCHIVE_VISIBILITY_COHORT, $visibilities);
        $this->assertContains(UCKKARCHIVE_VISIBILITY_PROGRAM, $visibilities);
        $this->assertContains(UCKKARCHIVE_VISIBILITY_INSTITUTION, $visibilities);
        $this->assertContains(UCKKARCHIVE_VISIBILITY_PUBLIC, $visibilities);
        $this->assertContains(UCKKARCHIVE_VISIBILITY_RESTRICTED_INTEGRITY, $visibilities);
    }

    /**
     * Archive item types should include all canonical archive memory objects.
     */
    public function test_get_item_types_returns_canonical_archive_item_types(): void {
        $types = uckkarchive_get_item_types();

        $this->assertContains(UCKKARCHIVE_TYPE_PROOF, $types);
        $this->assertContains(UCKKARCHIVE_TYPE_DECISION, $types);
        $this->assertContains(UCKKARCHIVE_TYPE_MINUTES, $types);
        $this->assertContains(UCKKARCHIVE_TYPE_CHALLENGE_RESULT, $types);
        $this->assertContains(UCKKARCHIVE_TYPE_COURSE_WORK, $types);
        $this->assertContains(UCKKARCHIVE_TYPE_PORTFOLIO_ITEM, $types);
        $this->assertContains(UCKKARCHIVE_TYPE_KRISTAL, $types);
        $this->assertContains(UCKKARCHIVE_TYPE_INTEGRITY_SUMMARY, $types);
        $this->assertContains(UCKKARCHIVE_TYPE_PUBLIC_SUMMARY, $types);
    }

    /**
     * Provenance sources should include human, system, AI-assisted, and UCKK module origins.
     */
    public function test_get_provenance_sources_returns_canonical_sources(): void {
        $sources = uckkarchive_get_provenance_sources();

        $this->assertContains(UCKKARCHIVE_PROVENANCE_HUMAN, $sources);
        $this->assertContains(UCKKARCHIVE_PROVENANCE_AI_ASSISTED, $sources);
        $this->assertContains(UCKKARCHIVE_PROVENANCE_IMPORTED, $sources);
        $this->assertContains(UCKKARCHIVE_PROVENANCE_SYSTEM, $sources);
        $this->assertContains(UCKKARCHIVE_PROVENANCE_ARCHIVE, $sources);
        $this->assertContains(UCKKARCHIVE_PROVENANCE_ASSEMBLY, $sources);
        $this->assertContains(UCKKARCHIVE_PROVENANCE_CHALLENGE, $sources);
        $this->assertContains(UCKKARCHIVE_PROVENANCE_INTEGRITY, $sources);
    }

    /**
     * Invalid status values should fall back to draft.
     */
    public function test_normalise_status_falls_back_to_draft(): void {
        $this->assertSame(UCKKARCHIVE_STATUS_DRAFT, uckkarchive_normalise_status('not-a-status'));
        $this->assertSame(UCKKARCHIVE_STATUS_DRAFT, uckkarchive_normalise_status(null));
        $this->assertSame(UCKKARCHIVE_STATUS_VALIDATED, uckkarchive_normalise_status(UCKKARCHIVE_STATUS_VALIDATED));
    }

    /**
     * Invalid validation states should fall back to unverified.
     */
    public function test_normalise_validation_state_falls_back_to_unverified(): void {
        $this->assertSame(UCKKARCHIVE_VALIDATION_UNVERIFIED, uckkarchive_normalise_validation_state('not-a-state'));
        $this->assertSame(UCKKARCHIVE_VALIDATION_UNVERIFIED, uckkarchive_normalise_validation_state(null));
        $this->assertSame(
            UCKKARCHIVE_VALIDATION_VERIFIED,
            uckkarchive_normalise_validation_state(UCKKARCHIVE_VALIDATION_VERIFIED)
        );
    }

    /**
     * Invalid visibility values should fall back to course visibility.
     */
    public function test_normalise_visibility_falls_back_to_course(): void {
        $this->assertSame(UCKKARCHIVE_VISIBILITY_COURSE, uckkarchive_normalise_visibility('not-a-visibility'));
        $this->assertSame(UCKKARCHIVE_VISIBILITY_COURSE, uckkarchive_normalise_visibility(null));
        $this->assertSame(UCKKARCHIVE_VISIBILITY_PUBLIC, uckkarchive_normalise_visibility(UCKKARCHIVE_VISIBILITY_PUBLIC));
    }

    /**
     * Invalid item types should fall back to proof.
     */
    public function test_normalise_item_type_falls_back_to_proof(): void {
        $this->assertSame(UCKKARCHIVE_TYPE_PROOF, uckkarchive_normalise_item_type('not-a-type'));
        $this->assertSame(UCKKARCHIVE_TYPE_PROOF, uckkarchive_normalise_item_type(null));
        $this->assertSame(UCKKARCHIVE_TYPE_KRISTAL, uckkarchive_normalise_item_type(UCKKARCHIVE_TYPE_KRISTAL));
    }

    /**
     * Invalid provenance sources should fall back to human.
     */
    public function test_normalise_provenance_source_falls_back_to_human(): void {
        $this->assertSame(UCKKARCHIVE_PROVENANCE_HUMAN, uckkarchive_normalise_provenance_source('not-a-source'));
        $this->assertSame(UCKKARCHIVE_PROVENANCE_HUMAN, uckkarchive_normalise_provenance_source(null));
        $this->assertSame(
            UCKKARCHIVE_PROVENANCE_AI_ASSISTED,
            uckkarchive_normalise_provenance_source(UCKKARCHIVE_PROVENANCE_AI_ASSISTED)
        );
    }

    /**
     * Metadata encoding and decoding should be stable and safe.
     */
    public function test_metadata_encoding_and_decoding_round_trip(): void {
        $metadata = [
            'origin' => 'test',
            'visibility' => UCKKARCHIVE_VISIBILITY_COURSE,
            'nested' => [
                'source' => UCKKARCHIVE_PROVENANCE_HUMAN,
            ],
        ];

        $encoded = uckkarchive_encode_metadata($metadata);

        $this->assertIsString($encoded);
        $this->assertSame($metadata, uckkarchive_decode_metadata($encoded));
        $this->assertSame([], uckkarchive_decode_metadata(null));
        $this->assertSame([], uckkarchive_decode_metadata('not json'));
        $this->assertNull(uckkarchive_encode_metadata([]));
        $this->assertNull(uckkarchive_encode_metadata(null));
    }

    /**
     * Provenance hashes should be deterministic for equivalent payloads.
     */
    public function test_compute_provenance_hash_is_deterministic(): void {
        $payloada = [
            'itemid' => 12,
            'source' => 'archive',
            'provenance' => UCKKARCHIVE_PROVENANCE_HUMAN,
        ];

        $payloadb = [
            'provenance' => UCKKARCHIVE_PROVENANCE_HUMAN,
            'source' => 'archive',
            'itemid' => 12,
        ];

        $hasha = uckkarchive_compute_provenance_hash($payloada);
        $hashb = uckkarchive_compute_provenance_hash($payloadb);

        $this->assertSame($hasha, $hashb);
        $this->assertMatchesRegularExpression('/^[a-f0-9]{64}$/', $hasha);
    }

    /**
     * URL helpers should generate stable archive URLs.
     */
    public function test_url_helpers_generate_expected_paths(): void {
        $this->assertSame('/mod/uckkarchive/view.php?id=42', uckkarchive_view_url(42)->out_as_local_url(false));
        $this->assertSame('/mod/uckkarchive/index.php?id=7', uckkarchive_index_url(7)->out_as_local_url(false));
        $this->assertSame(
            '/mod/uckkarchive/item.php?id=42&amp;itemid=9',
            uckkarchive_item_url(42, 9)->out_as_local_url(false)
        );
        $this->assertSame('/mod/uckkarchive/add.php?id=42', uckkarchive_add_url(42)->out_as_local_url(false));
        $this->assertSame(
            '/mod/uckkarchive/validate.php?id=42&amp;itemid=9',
            uckkarchive_validate_url(42, 9)->out_as_local_url(false)
        );
        $this->assertSame('/mod/uckkarchive/export.php?id=42', uckkarchive_export_url(42)->out_as_local_url(false));
    }

    /**
     * File area registry should expose canonical archive, media, content advisory, and export areas.
     */
    public function test_file_area_registry_lists_canonical_fileareas(): void {
        $this->assertSame('mod_uckkarchive', file_area_registry::get_component());

        $archiveareas = file_area_registry::get_archive_fileareas();
        $mediaareas = file_area_registry::get_media_fileareas();
        $contentareas = file_area_registry::get_content_advisory_fileareas();
        $exportareas = file_area_registry::get_export_fileareas();
        $allareas = file_area_registry::get_all_fileareas();

        $this->assertContains(file_area_registry::INTRO, $archiveareas);
        $this->assertContains(file_area_registry::ITEM_CONTENT, $archiveareas);
        $this->assertContains(file_area_registry::ITEM_FILES, $archiveareas);
        $this->assertContains(file_area_registry::PROOF_FILES, $archiveareas);

        $this->assertContains(file_area_registry::MEDIA_ORIGINAL, $mediaareas);
        $this->assertContains(file_area_registry::MEDIA_PREVIEW, $mediaareas);
        $this->assertContains(file_area_registry::MEDIA_THUMBNAIL, $mediaareas);
        $this->assertContains(file_area_registry::MEDIA_DERIVATIVE, $mediaareas);
        $this->assertContains(file_area_registry::MEDIA_CAPTION, $mediaareas);
        $this->assertContains(file_area_registry::MEDIA_TRANSCRIPT, $mediaareas);
        $this->assertContains(file_area_registry::MEDIA_ATTACHMENT, $mediaareas);

        $this->assertContains(file_area_registry::CONTENT_REVIEW_FILES, $contentareas);
        $this->assertContains(file_area_registry::EXTERNAL_WORK_REFERENCE_FILES, $contentareas);
        $this->assertContains(file_area_registry::CULTURAL_PROTOCOL_FILES, $contentareas);

        $this->assertContains(file_area_registry::EXPORT_PACKAGE, $exportareas);
        $this->assertContains(file_area_registry::EXPORT_MANIFEST, $exportareas);

        $this->assertContains(file_area_registry::MEDIA_ORIGINAL, $allareas);
        $this->assertContains(file_area_registry::CONTENT_REVIEW_FILES, $allareas);
        $this->assertTrue(file_area_registry::is_valid_filearea(file_area_registry::MEDIA_ORIGINAL));
        $this->assertTrue(file_area_registry::is_media_filearea(file_area_registry::MEDIA_ORIGINAL));
        $this->assertTrue(file_area_registry::is_content_advisory_filearea(file_area_registry::CONTENT_REVIEW_FILES));
        $this->assertTrue(file_area_registry::is_export_filearea(file_area_registry::EXPORT_PACKAGE));
    }

    /**
     * Media domain constants should expose canonical statuses, visibilities, suitability, and types.
     */
    public function test_media_domain_lists_canonical_values(): void {
        $this->assertContains(media::STATUS_DRAFT, media::statuses());
        $this->assertContains(media::STATUS_ACTIVE, media::statuses());
        $this->assertContains(media::STATUS_RESTRICTED, media::statuses());
        $this->assertContains(media::STATUS_ARCHIVED, media::statuses());
        $this->assertContains(media::STATUS_DELETED_SOFT, media::statuses());

        $this->assertContains(media::VISIBILITY_PRIVATE, media::visibilities());
        $this->assertContains(media::VISIBILITY_COURSE, media::visibilities());
        $this->assertContains(media::VISIBILITY_PUBLIC, media::visibilities());
        $this->assertContains(media::VISIBILITY_RESTRICTED_INTEGRITY, media::visibilities());
        $this->assertContains(media::VISIBILITY_RESTRICTED_CULTURAL, media::visibilities());

        $this->assertContains(media::SUITABILITY_GENERAL, media::audience_suitabilities());
        $this->assertContains(media::SUITABILITY_GUIDED, media::audience_suitabilities());
        $this->assertContains(media::SUITABILITY_RESTRICTED_CULTURAL, media::audience_suitabilities());

        $this->assertContains(media::TYPE_IMAGE, media::mediatypes());
        $this->assertContains(media::TYPE_VIDEO, media::mediatypes());
        $this->assertContains(media::TYPE_AUDIO, media::mediatypes());
        $this->assertContains(media::TYPE_DOCUMENT, media::mediatypes());
        $this->assertContains(media::TYPE_EXTERNAL_REFERENCE, media::mediatypes());
    }

    /**
     * External work domain constants should expose canonical values.
     */
    public function test_external_work_domain_lists_canonical_values(): void {
        $this->assertContains(external_work::TYPE_BOOK, external_work::work_types());
        $this->assertContains(external_work::TYPE_FILM, external_work::work_types());
        $this->assertContains(external_work::TYPE_WEBSITE, external_work::work_types());
        $this->assertContains(external_work::TYPE_EXTERNAL_VIDEO, external_work::work_types());
        $this->assertContains(external_work::TYPE_OTHER, external_work::work_types());

        $this->assertContains(external_work::STATUS_DRAFT, external_work::statuses());
        $this->assertContains(external_work::STATUS_ACTIVE, external_work::statuses());
        $this->assertContains(external_work::STATUS_RESTRICTED, external_work::statuses());
        $this->assertContains(external_work::STATUS_ARCHIVED, external_work::statuses());

        $this->assertContains(external_work::RIGHTS_UNKNOWN, external_work::rights_statuses());
        $this->assertContains(external_work::RIGHTS_LICENSED_EXTERNAL, external_work::rights_statuses());
        $this->assertContains(external_work::RIGHTS_OPEN_LICENSE, external_work::rights_statuses());
        $this->assertContains(external_work::RIGHTS_RESTRICTED_REFERENCE, external_work::rights_statuses());
    }

    /**
     * Content marker domain constants should expose canonical values.
     */
    public function test_content_marker_domain_lists_canonical_values(): void {
        $this->assertContains(content_marker::TARGET_MEDIA, content_marker::target_types());
        $this->assertContains(content_marker::TARGET_MEDIA_VERSION, content_marker::target_types());
        $this->assertContains(content_marker::TARGET_ARCHIVE_ITEM, content_marker::target_types());
        $this->assertContains(content_marker::TARGET_EXTERNAL_WORK, content_marker::target_types());

        $this->assertContains(content_marker::SEVERITY_NOTICE, content_marker::severities());
        $this->assertContains(content_marker::SEVERITY_MODERATE, content_marker::severities());
        $this->assertContains(content_marker::SEVERITY_STRONG, content_marker::severities());
        $this->assertContains(content_marker::SEVERITY_RESTRICTED, content_marker::severities());

        $this->assertContains(content_marker::REVIEW_DRAFT, content_marker::review_states());
        $this->assertContains(content_marker::REVIEW_PENDING, content_marker::review_states());
        $this->assertContains(content_marker::REVIEW_APPROVED, content_marker::review_states());
        $this->assertContains(content_marker::REVIEW_CONTESTED, content_marker::review_states());

        $this->assertContains(content_marker::LOCATOR_TIMECODE, content_marker::locator_types());
        $this->assertContains(content_marker::LOCATOR_PAGE, content_marker::locator_types());
        $this->assertContains(content_marker::LOCATOR_MANUAL_REFERENCE, content_marker::locator_types());
    }

    /**
     * Archive page records should resolve course, cm, archive instance, and module context.
     */
    public function test_get_page_records_resolves_module_context(): void {
        [$course, $archive, $cm, $context] = $this->create_archive_activity();

        [$resolvedcourse, $resolvedcm, $resolvedarchive, $resolvedcontext] = uckkarchive_get_page_records((int)$cm->id);

        $this->assertSame((int)$course->id, (int)$resolvedcourse->id);
        $this->assertSame((int)$cm->id, (int)$resolvedcm->id);
        $this->assertSame((int)$archive->id, (int)$resolvedarchive->id);
        $this->assertSame((int)$context->id, (int)$resolvedcontext->id);
    }

    /**
     * Public/course-visible items should be visible to users with view capability.
     */
    public function test_can_view_item_allows_course_visible_item(): void {
        [$course, $archive, $cm, $context] = $this->create_archive_activity();
        $user = $this->create_user_with_capability($course, $context, 'mod/uckkarchive:view');

        $item = $this->create_archive_item($archive, $cm, $context, $user, [
            'visibility' => UCKKARCHIVE_VISIBILITY_COURSE,
            'status' => UCKKARCHIVE_STATUS_VALIDATED,
        ]);

        $this->assertTrue(uckkarchive_can_view_item($item, $context, $user));
    }

    /**
     * Restricted integrity items should require the restricted-view capability.
     */
    public function test_can_view_item_restricts_integrity_visibility(): void {
        [$course, $archive, $cm, $context] = $this->create_archive_activity();

        $ordinaryuser = $this->create_user_with_capability($course, $context, 'mod/uckkarchive:view');
        $restricteduser = $this->create_user_with_capability($course, $context, 'mod/uckkarchive:view');
        $this->assign_capability_to_user($course, $restricteduser, 'mod/uckkarchive:viewrestricted');

        $item = $this->create_archive_item($archive, $cm, $context, $ordinaryuser, [
            'visibility' => UCKKARCHIVE_VISIBILITY_RESTRICTED_INTEGRITY,
            'status' => UCKKARCHIVE_STATUS_VALIDATED,
        ]);

        $this->assertFalse(uckkarchive_can_view_item($item, $context, $ordinaryuser));
        $this->assertTrue(uckkarchive_can_view_item($item, $context, $restricteduser));
    }

    /**
     * Private items should only be visible to their owner unless services apply a higher policy.
     */
    public function test_can_view_item_restricts_private_visibility_to_owner(): void {
        [$course, $archive, $cm, $context] = $this->create_archive_activity();

        $owner = $this->create_user_with_capability($course, $context, 'mod/uckkarchive:view');
        $otheruser = $this->create_user_with_capability($course, $context, 'mod/uckkarchive:view');

        $item = $this->create_archive_item($archive, $cm, $context, $owner, [
            'visibility' => UCKKARCHIVE_VISIBILITY_PRIVATE,
            'userid' => $owner->id,
        ]);

        $this->assertTrue(uckkarchive_can_view_item($item, $context, $owner));
        $this->assertFalse(uckkarchive_can_view_item($item, $context, $otheruser));
    }

    /**
     * Export helper should include display-safe fields for archive item cards.
     */
    public function test_prepare_item_export_returns_template_ready_data(): void {
        [$course, $archive, $cm, $context] = $this->create_archive_activity();
        $user = $this->getDataGenerator()->create_user();

        $item = $this->create_archive_item($archive, $cm, $context, $user, [
            'title' => 'Validated proof',
            'itemtype' => UCKKARCHIVE_TYPE_PROOF,
            'status' => UCKKARCHIVE_STATUS_VALIDATED,
            'validationstate' => UCKKARCHIVE_VALIDATION_VERIFIED,
            'visibility' => UCKKARCHIVE_VISIBILITY_COURSE,
            'summary' => 'A short summary',
            'metadata' => uckkarchive_encode_metadata(['test' => true]),
        ]);

        $export = uckkarchive_prepare_item_export($item, $cm, $context);

        $this->assertSame((int)$item->id, $export->id);
        $this->assertSame((int)$cm->id, $export->cmid);
        $this->assertSame((int)$context->id, $export->contextid);
        $this->assertSame('Validated proof', $export->title);
        $this->assertSame(UCKKARCHIVE_TYPE_PROOF, $export->itemtype);
        $this->assertSame(UCKKARCHIVE_STATUS_VALIDATED, $export->status);
        $this->assertSame(UCKKARCHIVE_VALIDATION_VERIFIED, $export->validationstate);
        $this->assertSame(UCKKARCHIVE_VISIBILITY_COURSE, $export->visibility);
        $this->assertTrue($export->hassummary);
        $this->assertSame(['test' => true], $export->metadata);
    }

    /**
     * Visible item query should omit restricted integrity records for ordinary viewers.
     */
    public function test_get_visible_items_filters_restricted_records_for_ordinary_user(): void {
        [$course, $archive, $cm, $context] = $this->create_archive_activity();

        $ordinaryuser = $this->create_user_with_capability($course, $context, 'mod/uckkarchive:view');
        $restricteduser = $this->create_user_with_capability($course, $context, 'mod/uckkarchive:view');
        $this->assign_capability_to_user($course, $restricteduser, 'mod/uckkarchive:viewrestricted');

        $this->create_archive_item($archive, $cm, $context, $ordinaryuser, [
            'title' => 'Course item',
            'visibility' => UCKKARCHIVE_VISIBILITY_COURSE,
        ]);

        $this->create_archive_item($archive, $cm, $context, $ordinaryuser, [
            'title' => 'Restricted item',
            'visibility' => UCKKARCHIVE_VISIBILITY_RESTRICTED_INTEGRITY,
        ]);

        $ordinaryitems = uckkarchive_get_visible_items($archive, $context, $ordinaryuser);
        $restricteditems = uckkarchive_get_visible_items($archive, $context, $restricteduser);

        $this->assertCount(1, $ordinaryitems);
        $this->assertCount(2, $restricteditems);
    }

    /**
     * Revision helper should insert a revision record with provenance hash.
     */
    public function test_create_revision_inserts_revision_record(): void {
        global $DB;

        [$course, $archive, $cm, $context] = $this->create_archive_activity();
        $user = $this->getDataGenerator()->create_user();

        $olditem = $this->create_archive_item($archive, $cm, $context, $user, [
            'title' => 'Old title',
            'versionno' => 1,
        ]);

        $newitem = clone $olditem;
        $newitem->title = 'New title';
        $newitem->versionno = 2;

        $revisionid = uckkarchive_create_revision($olditem, $newitem, 'Test revision', (int)$user->id);

        $revision = $DB->get_record(UCKKARCHIVE_REVISION_TABLE, ['id' => $revisionid], '*', MUST_EXIST);

        $this->assertSame((int)$archive->id, (int)$revision->archiveid);
        $this->assertSame((int)$olditem->id, (int)$revision->itemid);
        $this->assertSame(2, (int)$revision->versionno);
        $this->assertSame('Test revision', $revision->changereason);
        $this->assertMatchesRegularExpression('/^[a-f0-9]{64}$/', $revision->provenancehash);
    }

    /**
     * Provenance helper should insert a provenance record linked to an archive item.
     */
    public function test_create_provenance_record_inserts_record(): void {
        global $DB;

        [$course, $archive, $cm, $context] = $this->create_archive_activity();
        $user = $this->getDataGenerator()->create_user();

        $item = $this->create_archive_item($archive, $cm, $context, $user);

        $provenanceid = uckkarchive_create_provenance_record(
            (int)$archive->id,
            (int)$item->id,
            (int)$context->id,
            (int)$user->id,
            'mod_uckkchallenge',
            123,
            'Challenge proof package',
            UCKKARCHIVE_PROVENANCE_CHALLENGE,
            [
                'courseid' => $course->id,
                'cmid' => $cm->id,
                'visibility' => UCKKARCHIVE_VISIBILITY_COURSE,
            ]
        );

        $record = $DB->get_record(UCKKARCHIVE_PROVENANCE_TABLE, ['id' => $provenanceid], '*', MUST_EXIST);

        $this->assertSame((int)$archive->id, (int)$record->archiveid);
        $this->assertSame((int)$item->id, (int)$record->itemid);
        $this->assertSame('mod_uckkchallenge', $record->origincomponent);
        $this->assertSame(123, (int)$record->originobjectid);
        $this->assertSame(UCKKARCHIVE_PROVENANCE_CHALLENGE, $record->provenance);
        $this->assertMatchesRegularExpression('/^[a-f0-9]{64}$/', $record->provenancehash);
    }

    /**
     * Media create/export should round-trip through the local media domain.
     */
    public function test_media_create_and_export_record_round_trip(): void {
        $this->assertTrue($this->table_exists(media::TABLE), 'Media table must exist for media library tests.');

        [$course, $archive, $cm, $context] = $this->create_archive_activity();
        $user = $this->getDataGenerator()->create_user();

        $record = media::create([
            'archiveid' => (int)$archive->id,
            'courseid' => (int)$course->id,
            'cmid' => (int)$cm->id,
            'contextid' => (int)$context->id,
            'userid' => (int)$user->id,
            'ownerid' => (int)$user->id,
            'title' => 'Test media',
            'summary' => 'Test media summary',
            'description' => 'Test media description',
            'mediatype' => media::TYPE_VIDEO,
            'mimetype' => 'video/mp4',
            'status' => media::STATUS_ACTIVE,
            'visibility' => media::VISIBILITY_COURSE,
            'audiencesuitability' => media::SUITABILITY_GUIDED,
            'source' => 'uckk',
            'metadata' => ['test' => true],
        ], (int)$user->id);

        $this->assertGreaterThan(0, (int)$record->id);
        $this->assertSame('Test media', $record->title);
        $this->assertSame(media::TYPE_VIDEO, $record->mediatype);
        $this->assertSame(media::STATUS_ACTIVE, $record->status);
        $this->assertMatchesRegularExpression('/^[0-9a-fA-F-]{36}$/', $record->uuid);

        $export = media::export_record($record);

        $this->assertSame((int)$record->id, (int)$export->id);
        $this->assertSame('Test media', $export->title);
        $this->assertSame(media::TYPE_VIDEO, $export->mediatype);
        $this->assertSame(media::VISIBILITY_COURSE, $export->visibility);
        $this->assertSame(['test' => true], $export->metadata);
    }

    /**
     * Media versions should be creatable and selectable as current.
     */
    public function test_media_version_create_initial_and_make_current(): void {
        $this->assertTrue($this->table_exists(media::TABLE), 'Media table must exist for version tests.');
        $this->assertTrue($this->table_exists(media_version::TABLE), 'Media version table must exist.');

        [$course, $archive, $cm, $context] = $this->create_archive_activity();
        $user = $this->getDataGenerator()->create_user();

        $media = media::create([
            'archiveid' => (int)$archive->id,
            'courseid' => (int)$course->id,
            'cmid' => (int)$cm->id,
            'contextid' => (int)$context->id,
            'userid' => (int)$user->id,
            'ownerid' => (int)$user->id,
            'title' => 'Versioned media',
            'mediatype' => media::TYPE_DOCUMENT,
            'mimetype' => 'application/pdf',
            'status' => media::STATUS_ACTIVE,
            'visibility' => media::VISIBILITY_COURSE,
        ], (int)$user->id);

        $initial = media_version::create_initial($media, null, [
            'label' => 'Initial version',
            'filearea' => media_version::FILEAREA_ORIGINAL,
            'filename' => 'initial.pdf',
            'mimetype' => 'application/pdf',
            'contenthash' => str_repeat('a', 40),
            'filesize' => 1234,
            'metadata' => ['initial' => true],
        ]);

        $this->assertSame((int)$media->id, (int)$initial->mediaid);
        $this->assertSame(1, (int)$initial->versionnumber);
        $this->assertSame(1, (int)$initial->iscurrent);
        $this->assertSame(1, media_version::count_versions((int)$media->id));

        $second = media_version::create($media, [
            'label' => 'Second version',
            'filearea' => media_version::FILEAREA_ORIGINAL,
            'filename' => 'second.pdf',
            'mimetype' => 'application/pdf',
            'contenthash' => str_repeat('b', 40),
            'filesize' => 2345,
            'metadata' => ['second' => true],
        ]);

        media_version::make_current((int)$second->id);

        $current = media_version::get_current((int)$media->id, MUST_EXIST);

        $this->assertSame((int)$second->id, (int)$current->id);
        $this->assertSame(2, media_version::count_versions((int)$media->id));

        $summary = media_version::export_summary($current);
        $this->assertSame((int)$second->id, (int)$summary['id']);
        $this->assertSame('Second version', $summary['label']);
    }

    /**
     * Media collections should add, count, list, and remove media.
     */
    public function test_media_collection_adds_lists_and_removes_media(): void {
        $this->assertTrue($this->table_exists(media::TABLE), 'Media table must exist for collection tests.');
        $this->assertTrue($this->table_exists('uckkarchive_media_collection'), 'Media collection table must exist.');
        $this->assertTrue($this->table_exists('uckkarchive_media_collection_item'), 'Collection item table must exist.');

        [$course, $archive, $cm, $context] = $this->create_archive_activity();
        $user = $this->getDataGenerator()->create_user();

        $media = media::create([
            'archiveid' => (int)$archive->id,
            'courseid' => (int)$course->id,
            'cmid' => (int)$cm->id,
            'contextid' => (int)$context->id,
            'userid' => (int)$user->id,
            'ownerid' => (int)$user->id,
            'title' => 'Collection media',
            'mediatype' => media::TYPE_IMAGE,
            'mimetype' => 'image/png',
            'status' => media::STATUS_ACTIVE,
            'visibility' => media::VISIBILITY_COURSE,
        ], (int)$user->id);

        $collection = media_collection::create([
            'archiveid' => (int)$archive->id,
            'courseid' => (int)$course->id,
            'cmid' => (int)$cm->id,
            'contextid' => (int)$context->id,
            'title' => 'Teaching collection',
            'description' => 'Collection description',
            'visibility' => media_collection::VISIBILITY_COURSE,
            'status' => media_collection::STATUS_ACTIVE,
            'metadata' => ['purpose' => 'test'],
        ], (int)$user->id);

        $membership = media_collection::add_media((int)$collection->id, (int)$media->id, (int)$user->id, 10, [
            'role' => 'primary',
        ]);

        $this->assertGreaterThan(0, (int)$membership->id);
        $this->assertSame(1, media_collection::count_media((int)$collection->id));
        $this->assertTrue(media_collection::contains_media((int)$collection->id, (int)$media->id));

        $listed = media_collection::get_media((int)$collection->id);
        $this->assertCount(1, $listed);
        $this->assertSame((int)$media->id, (int)reset($listed)->id);

        $this->assertTrue(media_collection::remove_media((int)$collection->id, (int)$media->id));
        $this->assertSame(0, media_collection::count_media((int)$collection->id));
    }

    /**
     * External work create/export should round-trip through the local domain.
     */
    public function test_external_work_create_and_export_record_round_trip(): void {
        $this->assertTrue($this->table_exists(external_work::TABLE), 'External work table must exist.');

        [$course, $archive, $cm, $context] = $this->create_archive_activity();
        $user = $this->getDataGenerator()->create_user();

        $work = external_work::create([
            'archiveid' => (int)$archive->id,
            'courseid' => (int)$course->id,
            'cmid' => (int)$cm->id,
            'contextid' => (int)$context->id,
            'ownerid' => (int)$user->id,
            'userid' => (int)$user->id,
            'title' => 'External film',
            'worktype' => external_work::TYPE_FILM,
            'creator' => 'Film creator',
            'publisher' => 'Film publisher',
            'publicationyear' => 2024,
            'language' => 'en',
            'sourceurl' => 'https://example.test/external-film',
            'citation' => 'Film creator. External film. 2024.',
            'rightsstatus' => external_work::RIGHTS_LICENSED_EXTERNAL,
            'visibility' => external_work::VISIBILITY_COURSE,
            'audiencesuitability' => external_work::SUITABILITY_GUIDED,
            'status' => external_work::STATUS_ACTIVE,
            'metadata' => ['test' => true],
        ], (int)$user->id);

        $this->assertGreaterThan(0, (int)$work->id);
        $this->assertSame('External film', $work->title);
        $this->assertSame(external_work::TYPE_FILM, $work->worktype);
        $this->assertSame(external_work::STATUS_ACTIVE, $work->status);

        $export = external_work::export_record($work);

        $this->assertSame((int)$work->id, (int)$export->id);
        $this->assertSame('External film', $export->title);
        $this->assertSame(external_work::TYPE_FILM, $export->worktype);
        $this->assertSame(external_work::RIGHTS_LICENSED_EXTERNAL, $export->rightsstatus);
        $this->assertSame(['test' => true], $export->metadata);
    }

    /**
     * Content marker create/list should work for media targets.
     */
    public function test_content_marker_create_and_list_by_media(): void {
        $this->assertTrue($this->table_exists(media::TABLE), 'Media table must exist for marker tests.');
        $this->assertTrue($this->table_exists(content_marker::TABLE), 'Content marker table must exist.');

        [$course, $archive, $cm, $context] = $this->create_archive_activity();
        $user = $this->getDataGenerator()->create_user();

        $media = media::create([
            'archiveid' => (int)$archive->id,
            'courseid' => (int)$course->id,
            'cmid' => (int)$cm->id,
            'contextid' => (int)$context->id,
            'userid' => (int)$user->id,
            'ownerid' => (int)$user->id,
            'title' => 'Advisory media',
            'mediatype' => media::TYPE_VIDEO,
            'mimetype' => 'video/mp4',
            'status' => media::STATUS_ACTIVE,
            'visibility' => media::VISIBILITY_COURSE,
        ], (int)$user->id);

        $marker = content_marker::create([
            'archiveid' => (int)$archive->id,
            'courseid' => (int)$course->id,
            'cmid' => (int)$cm->id,
            'contextid' => (int)$context->id,
            'mediaid' => (int)$media->id,
            'targettype' => content_marker::TARGET_MEDIA,
            'targetid' => (int)$media->id,
            'tagkey' => 'violence',
            'category' => 'content_warning',
            'severity' => content_marker::SEVERITY_MODERATE,
            'audiencesuitability' => content_marker::SUITABILITY_GUIDED,
            'reviewstate' => content_marker::REVIEW_PENDING,
            'visibility' => content_marker::VISIBILITY_COURSE,
            'locatortype' => content_marker::LOCATOR_TIMECODE,
            'locatorvalue' => '00:01:20',
            'locatorstart' => '00:01:20',
            'description' => 'Moderate scene advisory.',
            'note' => 'Provide context before screening.',
            'metadata' => ['test' => true],
        ], (int)$user->id);

        $this->assertGreaterThan(0, (int)$marker->id);
        $this->assertSame(content_marker::TARGET_MEDIA, $marker->targettype);
        $this->assertSame(content_marker::SEVERITY_MODERATE, $marker->severity);
        $this->assertSame(content_marker::REVIEW_PENDING, $marker->reviewstate);

        $markers = content_marker::list_by_media((int)$media->id);

        $this->assertCount(1, $markers);
        $this->assertSame((int)$marker->id, (int)reset($markers)->id);

        $reviewed = content_marker::set_review_state(
            (int)$marker->id,
            content_marker::REVIEW_APPROVED,
            'Reviewed in test.',
            (int)$user->id
        );

        $this->assertSame(content_marker::REVIEW_APPROVED, $reviewed->reviewstate);
    }

    /**
     * Item state helpers should reflect canonical workflow rules.
     */
    public function test_item_state_helpers(): void {
        $draft = (object)['status' => UCKKARCHIVE_STATUS_DRAFT];
        $submitted = (object)['status' => UCKKARCHIVE_STATUS_SUBMITTED];
        $validated = (object)['status' => UCKKARCHIVE_STATUS_VALIDATED];
        $invalidated = (object)['status' => UCKKARCHIVE_STATUS_INVALIDATED];
        $archived = (object)['status' => UCKKARCHIVE_STATUS_ARCHIVED];

        $this->assertTrue(uckkarchive_item_can_submit($draft));
        $this->assertFalse(uckkarchive_item_can_submit($submitted));

        $this->assertTrue(uckkarchive_item_can_validate($submitted));
        $this->assertFalse(uckkarchive_item_can_validate($draft));

        $this->assertTrue(uckkarchive_item_can_revise($validated));
        $this->assertFalse(uckkarchive_item_can_revise($invalidated));
        $this->assertFalse(uckkarchive_item_can_revise($archived));

        $this->assertTrue(uckkarchive_item_can_export($validated));
        $this->assertFalse(uckkarchive_item_can_export($draft));

        $this->assertTrue(uckkarchive_is_terminal_status(UCKKARCHIVE_STATUS_ARCHIVED));
        $this->assertFalse(uckkarchive_is_terminal_status(UCKKARCHIVE_STATUS_DRAFT));
    }

    /**
     * Create a course, archive module instance, course module, and context.
     *
     * @return array{0: stdClass, 1: stdClass, 2: stdClass, 3: context_module}
     */
    private function create_archive_activity(): array {
        $course = $this->getDataGenerator()->create_course();

        $archive = $this->getDataGenerator()->create_module('uckkarchive', [
            'course' => $course->id,
            'name' => 'Test UCKK archive',
            'intro' => 'Archive intro',
            'introformat' => FORMAT_HTML,
            'defaultvisibility' => UCKKARCHIVE_VISIBILITY_COURSE,
            'requirevalidation' => 1,
            'allowexports' => 1,
        ]);

        $cm = get_coursemodule_from_instance('uckkarchive', $archive->id, $course->id, false, MUST_EXIST);
        $context = context_module::instance($cm->id);

        return [$course, $archive, $cm, $context];
    }

    /**
     * Create a user enrolled in the course with a module capability.
     *
     * @param stdClass $course Course.
     * @param context_module $context Module context.
     * @param string $capability Capability.
     * @return stdClass
     */
    private function create_user_with_capability(stdClass $course, context_module $context, string $capability): stdClass {
        $user = $this->getDataGenerator()->create_user();

        $this->getDataGenerator()->enrol_user($user->id, $course->id, 'student');
        $this->assign_capability_to_user($course, $user, $capability);

        return $user;
    }

    /**
     * Assign a capability to a user in the course context.
     *
     * @param stdClass $course Course.
     * @param stdClass $user User.
     * @param string $capability Capability.
     */
    private function assign_capability_to_user(stdClass $course, stdClass $user, string $capability): void {
        $roleid = $this->getDataGenerator()->create_role();

        assign_capability($capability, CAP_ALLOW, $roleid, \context_course::instance($course->id), true);
        role_assign($roleid, $user->id, \context_course::instance($course->id));
        accesslib_clear_all_caches_for_unit_testing();
    }

    /**
     * Insert an archive item.
     *
     * @param stdClass $archive Archive instance.
     * @param stdClass $cm Course module.
     * @param context_module $context Module context.
     * @param stdClass $user User.
     * @param array<string, mixed> $overrides Field overrides.
     * @return stdClass
     */
    private function create_archive_item(
        stdClass $archive,
        stdClass $cm,
        context_module $context,
        stdClass $user,
        array $overrides = []
    ): stdClass {
        $now = time();

        $record = (object)array_merge([
            'archiveid' => (int)$archive->id,
            'courseid' => (int)$cm->course,
            'cmid' => (int)$cm->id,
            'contextid' => (int)$context->id,
            'userid' => (int)$user->id,
            'parentitemid' => null,
            'itemtype' => UCKKARCHIVE_TYPE_PROOF,
            'title' => 'Archive item',
            'summary' => 'Archive item summary',
            'content' => 'Archive item content',
            'contentformat' => FORMAT_HTML,
            'publicsummary' => 'Public summary',
            'sourcecomponent' => 'mod_uckkarchive',
            'sourceobjectid' => null,
            'origincomponent' => 'mod_uckkarchive',
            'originobjectid' => null,
            'license' => null,
            'tags' => null,
            'status' => UCKKARCHIVE_STATUS_VALIDATED,
            'validationstate' => UCKKARCHIVE_VALIDATION_VERIFIED,
            'visibility' => UCKKARCHIVE_VISIBILITY_COURSE,
            'provenance' => UCKKARCHIVE_PROVENANCE_HUMAN,
            'provenancehash' => null,
            'integritycaseid' => null,
            'versionno' => 1,
            'createdby' => (int)$user->id,
            'modifiedby' => (int)$user->id,
            'timecreated' => $now,
            'timemodified' => $now,
            'metadata' => null,
        ], $overrides);

        return $this->insert_filtered(UCKKARCHIVE_ITEM_TABLE, $record);
    }

    /**
     * Insert a record after filtering to fields that exist in the current schema.
     *
     * @param string $table Table name.
     * @param stdClass $record Record.
     * @return stdClass Inserted record.
     */
    private function insert_filtered(string $table, stdClass $record): stdClass {
        global $DB;

        $columns = $DB->get_columns($table);
        $filtered = new stdClass();

        foreach (get_object_vars($record) as $field => $value) {
            if (array_key_exists($field, $columns)) {
                $filtered->{$field} = $value;
            }
        }

        $filtered->id = $DB->insert_record($table, $filtered);

        return $DB->get_record($table, ['id' => $filtered->id], '*', MUST_EXIST);
    }

    /**
     * Return whether a table exists in the current test database.
     *
     * @param string $table Table name.
     * @return bool
     */
    private function table_exists(string $table): bool {
        global $DB;

        return $DB->get_manager()->table_exists(new \xmldb_table($table));
    }
}