<?php
// This file is part of Moodle - https://moodle.org/
//
// Moodle is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// any later version.

/**
 * PHPUnit tests for UCKK Archive content advisory domain.
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
use mod_uckkarchive\local\content_policy;
use mod_uckkarchive\local\content_review;
use mod_uckkarchive\local\content_tag;
use mod_uckkarchive\local\content_tag_set;
use stdClass;

defined('MOODLE_INTERNAL') || die();

global $CFG;
require_once($CFG->dirroot . '/mod/uckkarchive/locallib.php');

/**
 * Tests for content advisories, advisory tags, marker records, reviews,
 * redaction rules, and export-safe marker data.
 *
 * @coversNothing
 */
final class content_advisory_test extends advanced_testcase {
    /**
     * Required content advisory tables.
     */
    private const REQUIRED_TABLES = [
        'uckkarchive_content_tag',
        'uckkarchive_content_tag_set',
        'uckkarchive_content_marker',
        'uckkarchive_content_review',
        'uckkarchive_external_work',
        'uckkarchive_media_source',
    ];

    /**
     * Reset database state.
     */
    protected function setUp(): void {
        parent::setUp();
        $this->resetAfterTest(true);
    }

    /**
     * The content advisory schema must exist.
     */
    public function test_content_advisory_tables_exist(): void {
        global $DB;

        $manager = $DB->get_manager();

        foreach (self::REQUIRED_TABLES as $table) {
            $this->assertTrue(
                $manager->table_exists(new \xmldb_table($table)),
                'Missing required content advisory table: ' . $table
            );
        }
    }

    /**
     * Domain vocabularies should expose the required final-state values.
     */
    public function test_domain_enumerations_include_required_content_advisory_values(): void {
        $this->assertContains('draft', content_marker::review_states());
        $this->assertContains('pending_review', content_marker::review_states());
        $this->assertContains('reviewed', content_marker::review_states());
        $this->assertContains('approved', content_marker::review_states());
        $this->assertContains('contested', content_marker::review_states());
        $this->assertContains('retired', content_marker::review_states());

        $this->assertContains('notice', content_marker::severities());
        $this->assertContains('moderate', content_marker::severities());
        $this->assertContains('strong', content_marker::severities());
        $this->assertContains('restricted', content_marker::severities());

        $this->assertContains('media', content_marker::target_types());
        $this->assertContains('media_version', content_marker::target_types());
        $this->assertContains('archive_item', content_marker::target_types());
        $this->assertContains('external_work', content_marker::target_types());
        $this->assertContains('manual_reference', content_marker::target_types());

        $this->assertContains('timecode', content_marker::locator_types());
        $this->assertContains('timecode_range', content_marker::locator_types());
        $this->assertContains('page', content_marker::locator_types());
        $this->assertContains('chapter', content_marker::locator_types());
        $this->assertContains('section', content_marker::locator_types());
        $this->assertContains('paragraph', content_marker::locator_types());
        $this->assertContains('scene', content_marker::locator_types());
        $this->assertContains('url_fragment', content_marker::locator_types());
        $this->assertContains('manual_reference', content_marker::locator_types());

        $this->assertContains('general', content_marker::audience_suitabilities());
        $this->assertContains('guided', content_marker::audience_suitabilities());
        $this->assertContains('mature', content_marker::audience_suitabilities());
        $this->assertContains('restricted', content_marker::audience_suitabilities());
        $this->assertContains('restricted_cultural', content_marker::audience_suitabilities());
        $this->assertContains('restricted_integrity', content_marker::audience_suitabilities());
        $this->assertContains('staff_only', content_marker::audience_suitabilities());

        $this->assertContains('draft', content_review::get_states());
        $this->assertContains('pending_review', content_review::get_states());
        $this->assertContains('reviewed', content_review::get_states());
        $this->assertContains('approved', content_review::get_states());
        $this->assertContains('contested', content_review::get_states());
        $this->assertContains('retired', content_review::get_states());
    }

    /**
     * Seed content tags and baseline tag sets should be installable/idempotent.
     */
    public function test_seed_tags_and_baseline_tag_sets_are_created_idempotently(): void {
        $this->skip_if_content_advisory_schema_missing();

        content_tag::ensure_seed_data();
        content_tag::ensure_seed_data();

        $sexualviolence = content_tag::get_by_key('sexual_violence');
        $cultural = content_tag::get_by_key('culturally_sensitive');
        $sacred = content_tag::get_by_key('sacred_content');
        $notforpublicexport = content_tag::get_by_key('not_for_public_export');

        $this->assertSame('sexual_violence', $sexualviolence->tagkey);
        $this->assertSame('strong', $sexualviolence->severity);

        $this->assertSame('culturally_sensitive', $cultural->tagkey);
        $this->assertSame(1, (int)$cultural->iscultural);

        $this->assertSame('sacred_content', $sacred->tagkey);
        $this->assertSame(1, (int)$sacred->restrictsdefault);

        $this->assertSame('not_for_public_export', $notforpublicexport->tagkey);
        $this->assertSame(1, (int)$notforpublicexport->restrictsdefault);

        content_tag_set::ensure_baseline_sets();
        content_tag_set::ensure_baseline_sets();

        $general = content_tag_set::get_by_key('general_advisories');
        $protocols = content_tag_set::get_by_key('cultural_protocols');
        $classroom = content_tag_set::get_by_key('classroom_suitability');
        $integrity = content_tag_set::get_by_key('integrity_sensitive');
        $youth = content_tag_set::get_by_key('youth_access');

        $this->assertSame('general_advisories', $general->tagsetkey);
        $this->assertSame('cultural_protocols', $protocols->tagsetkey);
        $this->assertSame('classroom_suitability', $classroom->tagsetkey);
        $this->assertSame('integrity_sensitive', $integrity->tagsetkey);
        $this->assertSame('youth_access', $youth->tagsetkey);

        $this->assertSame(1, (int)$general->locked);
        $this->assertSame(1, (int)$protocols->locked);
        $this->assertSame('restricted_cultural', $protocols->visibility);
    }

    /**
     * Content marker creation, update, review state, and export should round-trip.
     */
    public function test_content_marker_create_update_review_and_export_roundtrip(): void {
        $this->skip_if_content_advisory_schema_missing();

        [$course, $archive, $cm, $context] = $this->create_archive_activity();
        $user = $this->getDataGenerator()->create_user();
        $this->getDataGenerator()->enrol_user($user->id, $course->id, 'student');
        $this->setUser($user);

        content_tag::ensure_seed_data();
        content_tag_set::ensure_baseline_sets();

        $tag = content_tag::get_by_key('requires_context');
        $tagset = content_tag_set::get_by_key('general_advisories');

        $marker = content_marker::create([
            'archiveid' => (int)$archive->id,
            'courseid' => (int)$course->id,
            'cmid' => (int)$cm->id,
            'contextid' => (int)$context->id,
            'targettype' => 'manual_reference',
            'targetid' => 0,
            'targetuuid' => 'manual-reference-1',
            'tagid' => (int)$tag->id,
            'tagsetid' => (int)$tagset->id,
            'tagkey' => 'requires_context',
            'locatortype' => 'manual_reference',
            'locatorvalue' => 'Manual reference paragraph 1',
            'severity' => 'notice',
            'visibility' => 'course',
            'audiencesuitability' => 'guided',
            'reviewstate' => 'draft',
            'note' => 'Advisory note',
            'teachingcontext' => 'Use with introduction.',
            'metadata' => [
                'source' => 'phpunit',
            ],
        ], (int)$user->id);

        $this->assertGreaterThan(0, (int)$marker->id);
        $this->assertNotEmpty($marker->uuid);
        $this->assertSame('manual_reference', $marker->targettype);
        $this->assertSame('requires_context', $marker->tagkey);
        $this->assertSame('draft', $marker->reviewstate);

        $updated = content_marker::update((int)$marker->id, [
            'severity' => 'moderate',
            'note' => 'Updated advisory note',
            'teachingcontext' => 'Provide context before display.',
        ], (int)$user->id);

        $this->assertSame('moderate', $updated->severity);
        $this->assertSame('Updated advisory note', $updated->note);

        $reviewed = content_marker::set_review_state(
            (int)$marker->id,
            'approved',
            'Reviewed and approved for guided classroom use.',
            (int)$user->id
        );

        $this->assertSame('approved', $reviewed->reviewstate);
        $this->assertSame((int)$user->id, (int)$reviewed->reviewedby);
        $this->assertGreaterThan(0, (int)$reviewed->timereviewed);

        $export = content_marker::export_record($reviewed);

        $this->assertSame((int)$marker->id, $export['id']);
        $this->assertSame('requires_context', $export['tagkey']);
        $this->assertSame('approved', $export['reviewstate']);
        $this->assertSame('moderate', $export['severity']);
        $this->assertSame('manual_reference', $export['targettype']);
        $this->assertSame('manual_reference', $export['locatortype']);
        $this->assertIsArray($export['metadata']);
    }

    /**
     * Content reviews should support pending, approved, contested and retired states.
     */
    public function test_content_review_lifecycle_for_marker(): void {
        $this->skip_if_content_advisory_schema_missing();

        [$course, $archive, $cm, $context] = $this->create_archive_activity();
        $reviewer = $this->getDataGenerator()->create_user();
        $this->getDataGenerator()->enrol_user($reviewer->id, $course->id, 'teacher');
        $this->setUser($reviewer);

        $marker = $this->create_manual_marker($archive, $course, $cm, $context, $reviewer, [
            'tagkey' => 'not_for_children',
            'severity' => 'strong',
            'audiencesuitability' => 'mature',
            'reviewstate' => 'pending_review',
        ]);

        $pending = content_review::create_pending((int)$marker->id, (int)$reviewer->id, [
            'severity' => 'strong',
            'audiencesuitability' => 'mature',
            'rationale' => 'Needs review before classroom use.',
            'metadata' => [
                'source' => 'phpunit',
            ],
        ]);

        $this->assertSame('pending_review', $pending->state);
        $this->assertSame((int)$marker->id, (int)$pending->markerid);
        $this->assertSame((int)$reviewer->id, (int)$pending->reviewerid);

        $approved = content_review::approve(
            (int)$marker->id,
            (int)$reviewer->id,
            'Approved with guided classroom framing.',
            [
                'severity' => 'strong',
                'audiencesuitability' => 'mature',
            ]
        );

        $this->assertSame('approved', $approved->state);
        $this->assertTrue(content_review::is_marker_approved((int)$marker->id));

        $contested = content_review::contest(
            (int)$marker->id,
            (int)$reviewer->id,
            'Learner support note needs revision.',
            [
                'severity' => 'strong',
                'audiencesuitability' => 'guided',
            ]
        );

        $this->assertSame('contested', $contested->state);

        $retired = content_review::retire(
            (int)$marker->id,
            (int)$reviewer->id,
            'Marker superseded by more precise advisory.',
            [
                'severity' => 'notice',
                'audiencesuitability' => 'guided',
            ]
        );

        $this->assertSame('retired', $retired->state);

        $reviews = content_review::get_for_marker((int)$marker->id);

        $this->assertNotEmpty($reviews);
        $this->assertContains('retired', array_map(static fn(stdClass $record): string => $record->state, $reviews));

        $export = content_review::to_export_array($retired);

        $this->assertSame((int)$retired->id, $export['id']);
        $this->assertSame('retired', $export['state']);
        $this->assertSame((int)$marker->id, $export['markerid']);
        $this->assertIsArray($export['metadata']);
    }

    /**
     * Content policy should hide advisory records from users without advisory view authority.
     */
    public function test_content_policy_hides_markers_without_view_advisory_authority(): void {
        $this->skip_if_content_advisory_schema_missing();

        [$course, $archive, $cm, $context] = $this->create_archive_activity();

        $creator = $this->getDataGenerator()->create_user();
        $viewer = $this->getDataGenerator()->create_user();

        $this->getDataGenerator()->enrol_user($creator->id, $course->id, 'teacher');
        $this->getDataGenerator()->enrol_user($viewer->id, $course->id, 'student');

        $this->setUser($creator);

        $marker = $this->create_manual_marker($archive, $course, $cm, $context, $creator, [
            'tagkey' => 'requires_context',
            'severity' => 'notice',
            'visibility' => 'course',
            'audiencesuitability' => 'guided',
            'reviewstate' => 'approved',
        ]);

        $filtered = content_policy::filter_markers($context, [$marker], (int)$viewer->id);

        $this->assertSame([], $filtered);
        $this->assertFalse(content_policy::can_view_marker($context, $marker, (int)$viewer->id));
    }

    /**
     * Cultural markers should redact into placeholder mode for advisory viewers
     * who lack cultural restriction authority.
     */
    public function test_content_policy_redacts_culturally_restricted_marker_to_placeholder(): void {
        $this->skip_if_content_advisory_schema_missing();

        if (!$this->capability_exists('mod/uckkarchive:viewadvisories')) {
            $this->markTestSkipped('mod/uckkarchive:viewadvisories capability is not installed yet.');
        }

        [$course, $archive, $cm, $context] = $this->create_archive_activity();

        $creator = $this->getDataGenerator()->create_user();
        $viewer = $this->create_user_with_capability($course, $context, 'mod/uckkarchive:viewadvisories');

        $this->getDataGenerator()->enrol_user($creator->id, $course->id, 'teacher');

        $this->setUser($creator);

        $marker = $this->create_manual_marker($archive, $course, $cm, $context, $creator, [
            'tagkey' => 'sacred_content',
            'severity' => 'restricted',
            'visibility' => 'restricted_cultural',
            'audiencesuitability' => 'restricted_cultural',
            'reviewstate' => 'approved',
            'note' => 'Restricted advisory note',
            'teachingcontext' => 'Restricted teaching context',
            'culturalprotocolnote' => 'Restricted cultural protocol note',
        ]);

        $summary = content_policy::marker_display_summary($context, $marker, (int)$viewer->id);

        $this->assertTrue($summary['redacted']);
        $this->assertSame('placeholder', $summary['redactionmode']);
        $this->assertSame('restricted_cultural', $summary['tagkey']);
        $this->assertSame('restricted', $summary['severity']);
        $this->assertSame('restricted_cultural', $summary['audiencesuitability']);
    }

    /**
     * Export data for a marker should be policy-filtered.
     */
    public function test_export_marker_data_returns_safe_marker_summary(): void {
        $this->skip_if_content_advisory_schema_missing();

        if (!$this->capability_exists('mod/uckkarchive:viewadvisories')
                || !$this->capability_exists('mod/uckkarchive:export')) {
            $this->markTestSkipped('Advisory/export capabilities are not installed yet.');
        }

        [$course, $archive, $cm, $context] = $this->create_archive_activity();

        $creator = $this->getDataGenerator()->create_user();
        $exporter = $this->create_user_with_capability($course, $context, 'mod/uckkarchive:viewadvisories');
        $this->assign_capability_to_user($course, $exporter, 'mod/uckkarchive:export');

        $this->getDataGenerator()->enrol_user($creator->id, $course->id, 'teacher');

        $this->setUser($creator);

        $marker = $this->create_manual_marker($archive, $course, $cm, $context, $creator, [
            'tagkey' => 'requires_context',
            'severity' => 'notice',
            'visibility' => 'course',
            'audiencesuitability' => 'guided',
            'reviewstate' => 'approved',
        ]);

        $export = content_policy::export_marker_data($context, $marker, (int)$exporter->id);

        $this->assertNotNull($export);
        $this->assertSame('requires_context', $export['tagkey']);
        $this->assertSame('notice', $export['severity']);
        $this->assertSame('course', $export['visibility']);
        $this->assertSame('approved', $export['reviewstate']);
        $this->assertFalse($export['redacted']);
    }

    /**
     * Create a test archive activity.
     *
     * @return array{0:stdClass,1:stdClass,2:stdClass,3:context_module}
     */
    private function create_archive_activity(): array {
        $course = $this->getDataGenerator()->create_course();

        $archive = $this->getDataGenerator()->create_module('uckkarchive', [
            'course' => $course->id,
            'name' => 'Content advisory archive',
            'intro' => 'Content advisory test archive',
            'introformat' => FORMAT_HTML,
            'defaultvisibility' => defined('UCKKARCHIVE_VISIBILITY_COURSE') ? UCKKARCHIVE_VISIBILITY_COURSE : 'course',
            'requirevalidation' => 1,
            'allowexports' => 1,
        ]);

        $cm = get_coursemodule_from_instance('uckkarchive', $archive->id, $course->id, false, MUST_EXIST);
        $context = context_module::instance($cm->id);

        return [$course, $archive, $cm, $context];
    }

    /**
     * Create a manual reference marker.
     *
     * @param stdClass $archive Archive activity instance.
     * @param stdClass $course Course.
     * @param stdClass $cm Course module.
     * @param context_module $context Module context.
     * @param stdClass $user Acting user.
     * @param array<string,mixed> $overrides Field overrides.
     * @return stdClass
     */
    private function create_manual_marker(
        stdClass $archive,
        stdClass $course,
        stdClass $cm,
        context_module $context,
        stdClass $user,
        array $overrides = []
    ): stdClass {
        content_tag::ensure_seed_data();

        $defaults = [
            'archiveid' => (int)$archive->id,
            'courseid' => (int)$course->id,
            'cmid' => (int)$cm->id,
            'contextid' => (int)$context->id,
            'targettype' => 'manual_reference',
            'targetid' => 0,
            'targetuuid' => 'manual-reference-' . random_string(8),
            'tagkey' => 'requires_context',
            'locatortype' => 'manual_reference',
            'locatorvalue' => 'Manual reference',
            'severity' => 'notice',
            'visibility' => 'course',
            'audiencesuitability' => 'guided',
            'reviewstate' => 'draft',
            'note' => 'Advisory note',
            'teachingcontext' => 'Teaching context',
            'culturalprotocolnote' => '',
            'metadata' => [
                'source' => 'phpunit',
            ],
        ];

        return content_marker::create(array_merge($defaults, $overrides), (int)$user->id);
    }

    /**
     * Create user with capability in course context.
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
     * @return void
     */
    private function assign_capability_to_user(stdClass $course, stdClass $user, string $capability): void {
        $roleid = $this->getDataGenerator()->create_role();
        $coursecontext = \context_course::instance($course->id);

        assign_capability($capability, CAP_ALLOW, $roleid, $coursecontext, true);
        role_assign($roleid, $user->id, $coursecontext);

        accesslib_clear_all_caches_for_unit_testing();
    }

    /**
     * Skip tests that require not-yet-installed content advisory schema.
     *
     * The explicit schema test above fails when tables are missing. Domain tests
     * skip to avoid hiding the actual schema failure behind fatal table errors.
     *
     * @return void
     */
    private function skip_if_content_advisory_schema_missing(): void {
        global $DB;

        $manager = $DB->get_manager();

        foreach (self::REQUIRED_TABLES as $table) {
            if (!$manager->table_exists(new \xmldb_table($table))) {
                $this->markTestSkipped('Content advisory schema is not installed yet. Missing table: ' . $table);
            }
        }
    }

    /**
     * Return whether a capability exists in installed access definitions.
     *
     * @param string $capability Capability name.
     * @return bool
     */
    private function capability_exists(string $capability): bool {
        return function_exists('get_capability_info') && (bool)get_capability_info($capability);
    }
}