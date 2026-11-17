<?php
// This file is part of Moodle - https://moodle.org/
//
// Moodle is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// any later version.

/**
 * Privacy provider tests for mod_uckkarchive.
 *
 * @package    mod_uckkarchive
 * @category   test
 * @copyright  2026 Univers-Cité King Klown
 * @license    https://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later
 */

declare(strict_types=1);

namespace mod_uckkarchive\privacy;

use context_module;
use core_privacy\local\metadata\collection;
use core_privacy\local\request\approved_contextlist;
use core_privacy\local\request\approved_userlist;
use core_privacy\local\request\contextlist;
use core_privacy\local\request\userlist;
use core_privacy\local\request\writer;
use core_privacy\tests\provider_testcase;
use stdClass;

defined('MOODLE_INTERNAL') || die();

global $CFG;
require_once($CFG->dirroot . '/mod/uckkarchive/locallib.php');

/**
 * Tests for the UCKK Archive privacy provider.
 *
 * The archive owns long-lived institutional memory, but user-authored archive
 * records, media records, proofs, provenance, revisions, content advisories,
 * external work references, and export logs can contain personal data. The
 * provider must therefore find, export, anonymise, and remove data without
 * silently breaking Moodle context boundaries.
 *
 * @covers \mod_uckkarchive\privacy\provider
 */
final class privacy_provider_test extends provider_testcase {
    /**
     * Reset DB after each test.
     */
    protected function setUp(): void {
        parent::setUp();
        $this->resetAfterTest(true);
    }

    /**
     * Metadata should declare the archive-owned personal-data tables.
     */
    public function test_get_metadata_declares_archive_media_advisory_and_export_tables(): void {
        $collection = new collection('mod_uckkarchive');
        $collection = provider::get_metadata($collection);
        $items = $collection->get_collection();

        $expected = [
            'uckkarchive',
            'uckkarchive_item',
            'uckkarchive_kristal',
            'uckkarchive_proof',
            'uckkarchive_prov',
            'uckkarchive_rev',
            'uckkarchive_export',
            'uckkarchive_media',
            'uckkarchive_media_version',
            'uckkarchive_media_source',
            'uckkarchive_media_collection',
            'uckkarchive_media_relation',
            'uckkarchive_media_tag',
            'uckkarchive_content_marker',
            'uckkarchive_content_review',
            'uckkarchive_content_tag',
            'uckkarchive_content_tag_set',
            'uckkarchive_external_work',
        ];

        foreach ($expected as $table) {
            $this->assertArrayHasKey(
                $table,
                $items,
                'Privacy metadata must declare table ' . $table . '.'
            );
        }

        $this->assertArrayHasKey('mod_uckkarchive', $items);
    }

    /**
     * Context lookup should include contexts where a user owns archive/media data.
     */
    public function test_get_contexts_for_userid_returns_archive_contexts(): void {
        [$course, $archive, $cm, $context] = $this->create_archive_activity();
        $user = $this->getDataGenerator()->create_user();

        $this->insert_archive_item($archive, $cm, $context, $user, [
            'title' => 'Personal archive item',
            'content' => 'Personal archive content',
        ]);

        if ($this->table_exists('uckkarchive_media')) {
            $media = $this->insert_media($archive, $cm, $context, $user, [
                'title' => 'Personal media',
                'description' => 'Personal media description',
            ]);

            if ($this->table_exists('uckkarchive_content_marker')) {
                $this->insert_content_marker($archive, $cm, $context, $user, $media, [
                    'description' => 'Personal advisory marker',
                ]);
            }
        }

        $contextlist = provider::get_contexts_for_userid((int)$user->id);
        $contextids = $contextlist->get_contextids();

        $this->assertContains((int)$context->id, $contextids);
    }

    /**
     * Context lookup should not return unrelated contexts.
     */
    public function test_get_contexts_for_userid_does_not_return_unrelated_contexts(): void {
        [$course, $archive, $cm, $context] = $this->create_archive_activity();
        $owner = $this->getDataGenerator()->create_user();
        $unrelated = $this->getDataGenerator()->create_user();

        $this->insert_archive_item($archive, $cm, $context, $owner);

        $contextlist = provider::get_contexts_for_userid((int)$unrelated->id);

        $this->assertNotContains((int)$context->id, $contextlist->get_contextids());
    }

    /**
     * Userlist lookup should include users referenced in archive-owned tables.
     */
    public function test_get_users_in_context_finds_users_from_archive_media_and_advisory_records(): void {
        [$course, $archive, $cm, $context] = $this->create_archive_activity();

        $author = $this->getDataGenerator()->create_user();
        $reviewer = $this->getDataGenerator()->create_user();
        $exporter = $this->getDataGenerator()->create_user();

        $this->insert_archive_item($archive, $cm, $context, $author);

        if ($this->table_exists('uckkarchive_media')) {
            $media = $this->insert_media($archive, $cm, $context, $author);

            if ($this->table_exists('uckkarchive_content_marker')) {
                $marker = $this->insert_content_marker($archive, $cm, $context, $author, $media);

                if ($this->table_exists('uckkarchive_content_review')) {
                    $this->insert_content_review($archive, $cm, $context, $reviewer, $marker);
                }
            }
        }

        if ($this->table_exists('uckkarchive_export')) {
            $this->insert_export($archive, $cm, $context, $exporter);
        }

        $userlist = new userlist($context, 'mod_uckkarchive');
        provider::get_users_in_context($userlist);

        $userids = $userlist->get_userids();

        $this->assertContains((int)$author->id, $userids);
        $this->assertContains((int)$reviewer->id, $userids);
        $this->assertContains((int)$exporter->id, $userids);
    }

    /**
     * User data export should write data for the approved context.
     */
    public function test_export_user_data_exports_archive_records(): void {
        [$course, $archive, $cm, $context] = $this->create_archive_activity();
        $user = $this->getDataGenerator()->create_user();

        $this->insert_archive_item($archive, $cm, $context, $user, [
            'title' => 'Exported archive item',
            'summary' => 'Exported summary',
            'content' => 'Exported content',
        ]);

        if ($this->table_exists('uckkarchive_media')) {
            $this->insert_media($archive, $cm, $context, $user, [
                'title' => 'Exported media title',
                'description' => 'Exported media description',
            ]);
        }

        $approved = new approved_contextlist(
            $user,
            'mod_uckkarchive',
            [(int)$context->id]
        );

        provider::export_user_data($approved);

        $writer = writer::with_context($context);
        $data = $writer->get_data([get_string('privacy:path:archives', 'uckkarchive')]);

        $this->assertNotEmpty((array)$data);
        $this->assertObjectHasAttribute('uckkarchive_item', $data);

        $titles = array_map(static function(stdClass $record): string {
            return (string)($record->title ?? '');
        }, $data->uckkarchive_item);

        $this->assertContains('Exported archive item', $titles);
    }

    /**
     * Deleting data for one user should anonymise personal archive records.
     */
    public function test_delete_data_for_user_anonymises_user_records_in_approved_context(): void {
        global $DB;

        [$course, $archive, $cm, $context] = $this->create_archive_activity();
        $user = $this->getDataGenerator()->create_user();

        $item = $this->insert_archive_item($archive, $cm, $context, $user, [
            'title' => 'Item to anonymise',
            'summary' => 'Summary to anonymise',
            'content' => 'Content to anonymise',
        ]);

        $media = null;
        if ($this->table_exists('uckkarchive_media')) {
            $media = $this->insert_media($archive, $cm, $context, $user, [
                'title' => 'Media to anonymise',
                'description' => 'Media description to anonymise',
            ]);
        }

        $approved = new approved_contextlist(
            $user,
            'mod_uckkarchive',
            [(int)$context->id]
        );

        provider::delete_data_for_user($approved);

        $updateditem = $DB->get_record('uckkarchive_item', ['id' => (int)$item->id], '*', MUST_EXIST);

        foreach (['userid', 'createdby', 'modifiedby', 'validatedby'] as $field) {
            if ($this->field_exists('uckkarchive_item', $field)) {
                $this->assertSame(0, (int)$updateditem->{$field});
            }
        }

        foreach (['title', 'summary', 'content', 'description', 'notes'] as $field) {
            if ($this->field_exists('uckkarchive_item', $field)) {
                $this->assertSame(get_string('privacy:deleted', 'uckkarchive'), (string)$updateditem->{$field});
            }
        }

        if ($media !== null) {
            $updatedmedia = $DB->get_record('uckkarchive_media', ['id' => (int)$media->id], '*', MUST_EXIST);

            foreach (['userid', 'ownerid', 'createdby', 'modifiedby'] as $field) {
                if ($this->field_exists('uckkarchive_media', $field)) {
                    $this->assertSame(0, (int)$updatedmedia->{$field});
                }
            }
        }
    }

    /**
     * Deleting data for all users in a context should delete context child records.
     */
    public function test_delete_data_for_all_users_in_context_removes_child_records(): void {
        global $DB;

        [$course, $archive, $cm, $context] = $this->create_archive_activity();
        $user = $this->getDataGenerator()->create_user();

        $item = $this->insert_archive_item($archive, $cm, $context, $user);
        $media = null;

        if ($this->table_exists('uckkarchive_media')) {
            $media = $this->insert_media($archive, $cm, $context, $user);
        }

        provider::delete_data_for_all_users_in_context($context);

        $this->assertFalse($DB->record_exists('uckkarchive_item', ['id' => (int)$item->id]));

        if ($media !== null) {
            $this->assertFalse($DB->record_exists('uckkarchive_media', ['id' => (int)$media->id]));
        }
    }

    /**
     * Deleting data for approved users should affect only approved users.
     */
    public function test_delete_data_for_users_only_anonymises_approved_users(): void {
        global $DB;

        [$course, $archive, $cm, $context] = $this->create_archive_activity();

        $approveduser = $this->getDataGenerator()->create_user();
        $otheruser = $this->getDataGenerator()->create_user();

        $approveditem = $this->insert_archive_item($archive, $cm, $context, $approveduser, [
            'title' => 'Approved user item',
        ]);

        $otheritem = $this->insert_archive_item($archive, $cm, $context, $otheruser, [
            'title' => 'Other user item',
        ]);

        $approveduserlist = new approved_userlist(
            $context,
            'mod_uckkarchive',
            [(int)$approveduser->id]
        );

        provider::delete_data_for_users($approveduserlist);

        $updatedapproved = $DB->get_record('uckkarchive_item', ['id' => (int)$approveditem->id], '*', MUST_EXIST);
        $updatedother = $DB->get_record('uckkarchive_item', ['id' => (int)$otheritem->id], '*', MUST_EXIST);

        if ($this->field_exists('uckkarchive_item', 'userid')) {
            $this->assertSame(0, (int)$updatedapproved->userid);
            $this->assertSame((int)$otheruser->id, (int)$updatedother->userid);
        }

        if ($this->field_exists('uckkarchive_item', 'title')) {
            $this->assertSame(get_string('privacy:deleted', 'uckkarchive'), (string)$updatedapproved->title);
            $this->assertSame('Other user item', (string)$updatedother->title);
        }
    }

    /**
     * File areas attached to user records should be deleted/anonymised with the user data.
     */
    public function test_delete_data_for_user_deletes_files_for_user_records(): void {
        [$course, $archive, $cm, $context] = $this->create_archive_activity();
        $user = $this->getDataGenerator()->create_user();

        $item = $this->insert_archive_item($archive, $cm, $context, $user);
        $file = $this->create_file($context, 'item_attachment', (int)$item->id, 'personal.txt', 'personal file content');

        $this->assertNotFalse($file);

        $approved = new approved_contextlist(
            $user,
            'mod_uckkarchive',
            [(int)$context->id]
        );

        provider::delete_data_for_user($approved);

        $fs = get_file_storage();
        $remaining = $fs->get_area_files(
            (int)$context->id,
            'mod_uckkarchive',
            'item_attachment',
            (int)$item->id,
            'id',
            false
        );

        $this->assertCount(0, $remaining);
    }

    /**
     * Create an archive activity.
     *
     * @return array{0:stdClass,1:stdClass,2:stdClass,3:context_module}
     */
    private function create_archive_activity(): array {
        $course = $this->getDataGenerator()->create_course();

        $archive = $this->getDataGenerator()->create_module('uckkarchive', [
            'course' => (int)$course->id,
            'name' => 'Privacy archive',
            'intro' => 'Privacy archive intro',
            'introformat' => FORMAT_HTML,
            'defaultvisibility' => defined('UCKKARCHIVE_VISIBILITY_COURSE')
                ? UCKKARCHIVE_VISIBILITY_COURSE
                : 'course',
            'requirevalidation' => 1,
            'allowexports' => 1,
        ]);

        $cm = get_coursemodule_from_instance('uckkarchive', $archive->id, $course->id, false, MUST_EXIST);
        $context = context_module::instance($cm->id);

        $this->ensure_instance_context_fields($archive, $cm, $context);

        return [$course, $archive, $cm, $context];
    }

    /**
     * Ensure the instance record has context fields when supported by schema.
     *
     * @param stdClass $archive Archive instance.
     * @param stdClass $cm Course module.
     * @param context_module $context Module context.
     */
    private function ensure_instance_context_fields(stdClass $archive, stdClass $cm, context_module $context): void {
        global $DB;

        $updates = new stdClass();
        $updates->id = (int)$archive->id;

        if ($this->field_exists('uckkarchive', 'courseid')) {
            $updates->courseid = (int)$cm->course;
        }

        if ($this->field_exists('uckkarchive', 'cmid')) {
            $updates->cmid = (int)$cm->id;
        }

        if ($this->field_exists('uckkarchive', 'contextid')) {
            $updates->contextid = (int)$context->id;
        }

        if (count((array)$updates) > 1) {
            $DB->update_record('uckkarchive', $updates);
        }
    }

    /**
     * Insert an archive item.
     *
     * @param stdClass $archive Archive instance.
     * @param stdClass $cm Course module.
     * @param context_module $context Module context.
     * @param stdClass $user User.
     * @param array<string, mixed> $overrides Overrides.
     * @return stdClass
     */
    private function insert_archive_item(
        stdClass $archive,
        stdClass $cm,
        context_module $context,
        stdClass $user,
        array $overrides = []
    ): stdClass {
        $now = time();

        $defaults = [
            'archiveid' => (int)$archive->id,
            'courseid' => (int)$cm->course,
            'cmid' => (int)$cm->id,
            'contextid' => (int)$context->id,
            'userid' => (int)$user->id,
            'createdby' => (int)$user->id,
            'modifiedby' => (int)$user->id,
            'validatedby' => (int)$user->id,
            'itemtype' => defined('UCKKARCHIVE_TYPE_PROOF') ? UCKKARCHIVE_TYPE_PROOF : 'proof',
            'status' => defined('UCKKARCHIVE_STATUS_DRAFT') ? UCKKARCHIVE_STATUS_DRAFT : 'draft',
            'visibility' => defined('UCKKARCHIVE_VISIBILITY_COURSE') ? UCKKARCHIVE_VISIBILITY_COURSE : 'course',
            'title' => 'Privacy archive item',
            'summary' => 'Privacy archive summary',
            'content' => 'Privacy archive content',
            'description' => 'Privacy archive description',
            'notes' => 'Privacy archive notes',
            'metadata' => json_encode(['privacy' => true]),
            'timecreated' => $now,
            'timemodified' => $now,
        ];

        return $this->insert_filtered('uckkarchive_item', array_merge($defaults, $overrides));
    }

    /**
     * Insert media record.
     *
     * @param stdClass $archive Archive instance.
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
        $now = time();

        $defaults = [
            'uuid' => $this->uuid(),
            'archiveid' => (int)$archive->id,
            'courseid' => (int)$cm->course,
            'cmid' => (int)$cm->id,
            'contextid' => (int)$context->id,
            'userid' => (int)$user->id,
            'ownerid' => (int)$user->id,
            'createdby' => (int)$user->id,
            'modifiedby' => (int)$user->id,
            'mediatype' => 'document',
            'mimetype' => 'text/plain',
            'status' => 'active',
            'visibility' => 'course',
            'audiencesuitability' => 'guided',
            'title' => 'Privacy media',
            'description' => 'Privacy media description',
            'metadata' => json_encode(['privacy' => true]),
            'timecreated' => $now,
            'timemodified' => $now,
        ];

        return $this->insert_filtered('uckkarchive_media', array_merge($defaults, $overrides));
    }

    /**
     * Insert content marker.
     *
     * @param stdClass $archive Archive instance.
     * @param stdClass $cm Course module.
     * @param context_module $context Module context.
     * @param stdClass $user User.
     * @param stdClass $media Media record.
     * @param array<string, mixed> $overrides Overrides.
     * @return stdClass
     */
    private function insert_content_marker(
        stdClass $archive,
        stdClass $cm,
        context_module $context,
        stdClass $user,
        stdClass $media,
        array $overrides = []
    ): stdClass {
        $now = time();

        $defaults = [
            'uuid' => $this->uuid(),
            'archiveid' => (int)$archive->id,
            'courseid' => (int)$cm->course,
            'cmid' => (int)$cm->id,
            'contextid' => (int)$context->id,
            'mediaid' => (int)$media->id,
            'userid' => (int)$user->id,
            'createdby' => (int)$user->id,
            'modifiedby' => (int)$user->id,
            'tagkey' => 'violence',
            'severity' => 'moderate',
            'audiencesuitability' => 'guided',
            'visibility' => 'course',
            'locatortype' => 'timecode',
            'locator' => '00:01:20',
            'description' => 'Privacy content marker',
            'note' => 'Privacy content marker note',
            'metadata' => json_encode(['privacy' => true]),
            'timecreated' => $now,
            'timemodified' => $now,
        ];

        return $this->insert_filtered('uckkarchive_content_marker', array_merge($defaults, $overrides));
    }

    /**
     * Insert content review.
     *
     * @param stdClass $archive Archive instance.
     * @param stdClass $cm Course module.
     * @param context_module $context Module context.
     * @param stdClass $user Reviewer user.
     * @param stdClass $marker Content marker.
     * @param array<string, mixed> $overrides Overrides.
     * @return stdClass
     */
    private function insert_content_review(
        stdClass $archive,
        stdClass $cm,
        context_module $context,
        stdClass $user,
        stdClass $marker,
        array $overrides = []
    ): stdClass {
        $now = time();

        $defaults = [
            'uuid' => $this->uuid(),
            'archiveid' => (int)$archive->id,
            'courseid' => (int)$cm->course,
            'cmid' => (int)$cm->id,
            'contextid' => (int)$context->id,
            'markerid' => (int)$marker->id,
            'reviewerid' => (int)$user->id,
            'userid' => (int)$user->id,
            'createdby' => (int)$user->id,
            'modifiedby' => (int)$user->id,
            'state' => 'approved',
            'severity' => 'moderate',
            'audiencesuitability' => 'guided',
            'rationale' => 'Privacy review rationale',
            'reviewnote' => 'Privacy review note',
            'metadata' => json_encode(['privacy' => true]),
            'timecreated' => $now,
            'timemodified' => $now,
        ];

        return $this->insert_filtered('uckkarchive_content_review', array_merge($defaults, $overrides));
    }

    /**
     * Insert export record.
     *
     * @param stdClass $archive Archive instance.
     * @param stdClass $cm Course module.
     * @param context_module $context Module context.
     * @param stdClass $user User.
     * @param array<string, mixed> $overrides Overrides.
     * @return stdClass
     */
    private function insert_export(
        stdClass $archive,
        stdClass $cm,
        context_module $context,
        stdClass $user,
        array $overrides = []
    ): stdClass {
        $now = time();

        $defaults = [
            'archiveid' => (int)$archive->id,
            'courseid' => (int)$cm->course,
            'cmid' => (int)$cm->id,
            'contextid' => (int)$context->id,
            'userid' => (int)$user->id,
            'createdby' => (int)$user->id,
            'modifiedby' => (int)$user->id,
            'exportedby' => (int)$user->id,
            'exportscope' => 'selected',
            'exportformat' => 'json',
            'packagename' => 'privacy-export',
            'description' => 'Privacy export',
            'reason' => 'Privacy export reason',
            'status' => 'completed',
            'visibility' => 'private',
            'metadata' => json_encode(['privacy' => true]),
            'timecreated' => $now,
            'timemodified' => $now,
        ];

        return $this->insert_filtered('uckkarchive_export', array_merge($defaults, $overrides));
    }

    /**
     * Insert a record after filtering to existing table fields.
     *
     * @param string $table Table name.
     * @param array<string, mixed> $data Data.
     * @return stdClass
     */
    private function insert_filtered(string $table, array $data): stdClass {
        global $DB;

        $this->assertTrue($this->table_exists($table), 'Required test table is missing: ' . $table);

        $columns = $DB->get_columns($table);
        $record = new stdClass();

        foreach ($data as $field => $value) {
            if (array_key_exists($field, $columns)) {
                $record->{$field} = $value;
            }
        }

        $record->id = $DB->insert_record($table, $record);

        return $DB->get_record($table, ['id' => (int)$record->id], '*', MUST_EXIST);
    }

    /**
     * Create a file in a plugin file area.
     *
     * @param context_module $context Context.
     * @param string $filearea File area.
     * @param int $itemid Item id.
     * @param string $filename Filename.
     * @param string $content File content.
     * @return \stored_file
     */
    private function create_file(
        context_module $context,
        string $filearea,
        int $itemid,
        string $filename,
        string $content
    ): \stored_file {
        $fs = get_file_storage();

        return $fs->create_file_from_string([
            'contextid' => (int)$context->id,
            'component' => 'mod_uckkarchive',
            'filearea' => $filearea,
            'itemid' => $itemid,
            'filepath' => '/',
            'filename' => $filename,
        ], $content);
    }

    /**
     * Return whether table exists.
     *
     * @param string $table Table name.
     * @return bool
     */
    private function table_exists(string $table): bool {
        global $DB;

        return $DB->get_manager()->table_exists(new \xmldb_table($table));
    }

    /**
     * Return whether field exists.
     *
     * @param string $table Table name.
     * @param string $field Field name.
     * @return bool
     */
    private function field_exists(string $table, string $field): bool {
        global $DB;

        if (!$this->table_exists($table)) {
            return false;
        }

        $columns = $DB->get_columns($table);

        return array_key_exists($field, $columns);
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

        return \core\uuid::generate();
    }
}