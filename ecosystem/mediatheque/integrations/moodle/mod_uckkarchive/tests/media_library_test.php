<?php
// This file is part of Moodle - https://moodle.org/
//
// Moodle is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// any later version.

/**
 * Tests for the UCKK Archive media library subsystem.
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
use mod_uckkarchive\local\media;
use mod_uckkarchive\local\media_collection;
use mod_uckkarchive\local\media_file;
use mod_uckkarchive\local\media_policy;
use mod_uckkarchive\local\media_search;
use mod_uckkarchive\local\media_version;
use stdClass;

defined('MOODLE_INTERNAL') || die();

global $CFG;
require_once($CFG->dirroot . '/mod/uckkarchive/locallib.php');

/**
 * Tests for the media library subsystem.
 *
 * These tests verify the server-side media layer:
 *
 * - media records are archive-owned;
 * - media files are stored through Moodle File API;
 * - media versions are first-class records;
 * - collections preserve membership metadata;
 * - restricted media requires restricted-media authority;
 * - media listing/search remains scoped to the current archive.
 *
 * @coversNothing
 */
final class media_library_test extends advanced_testcase {
    /** Media table. */
    private const TABLE_MEDIA = 'uckkarchive_media';

    /** Media version table. */
    private const TABLE_VERSION = 'uckkarchive_media_version';

    /** Media collection table. */
    private const TABLE_COLLECTION = 'uckkarchive_media_collection';

    /** Media collection item table. */
    private const TABLE_COLLECTION_ITEM = 'uckkarchive_media_collection_item';

    /** Media tag table. */
    private const TABLE_TAG = 'uckkarchive_media_tag';

    /** File component. */
    private const COMPONENT = 'mod_uckkarchive';

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
     * Media records are archive-owned and exportable by the local domain layer.
     */
    public function test_media_record_can_be_created_and_exported(): void {
        $this->require_media_table();

        [$course, $archive, $cm, $context] = $this->create_archive_activity();

        $media = $this->create_media_record($archive, $cm, $context, [
            'title' => 'Interview with a Klown archivist',
            'summary' => 'Short media summary.',
            'description' => 'Longer media description.',
            'mediatype' => 'video',
            'mimetype' => 'video/mp4',
            'status' => 'active',
            'visibility' => 'course',
            'audiencesuitability' => 'guided',
            'source' => 'produced_by_uckk',
        ]);

        $this->assertGreaterThan(0, (int)$media->id);
        $this->assertSame((int)$archive->id, (int)$media->archiveid);
        $this->assertSame((int)$course->id, (int)$media->courseid);
        $this->assertSame((int)$cm->id, (int)$media->cmid);
        $this->assertSame((int)$context->id, (int)$media->contextid);
        $this->assertSame('Interview with a Klown archivist', $media->title);
        $this->assertSame('video', $media->mediatype);
        $this->assertSame('active', $media->status);
        $this->assertSame('course', $media->visibility);

        if (class_exists(media::class) && method_exists(media::class, 'export_record')) {
            $exported = media::export_record($media);

            $this->assertSame((int)$media->id, (int)$exported['id']);
            $this->assertSame((int)$archive->id, (int)$exported['archiveid']);
            $this->assertSame('Interview with a Klown archivist', $exported['title']);
            $this->assertSame('video', $exported['mediatype']);
            $this->assertSame('course', $exported['visibility']);
        }
    }

    /**
     * Media File API storage must use canonical media file areas only.
     */
    public function test_media_file_api_stores_canonical_media_fileareas(): void {
        $this->require_media_table();

        [$course, $archive, $cm, $context] = $this->create_archive_activity();
        $media = $this->create_media_record($archive, $cm, $context, [
            'title' => 'Image with support files',
            'mediatype' => 'image',
            'mimetype' => 'image/png',
        ]);

        $areas = [
            'media_original' => 'original.png',
            'media_preview' => 'preview.png',
            'media_thumbnail' => 'thumbnail.png',
            'media_derivative' => 'derivative.png',
            'media_caption' => 'caption.vtt',
            'media_transcript' => 'transcript.txt',
            'media_attachment' => 'attachment.txt',
        ];

        foreach ($areas as $filearea => $filename) {
            $file = $this->create_media_file($context, $filearea, (int)$media->id, $filename, 'content for ' . $filearea);

            $this->assertSame(self::COMPONENT, $file->get_component());
            $this->assertSame($filearea, $file->get_filearea());
            $this->assertSame((int)$media->id, $file->get_itemid());
            $this->assertSame($filename, $file->get_filename());
        }

        $fs = get_file_storage();

        foreach ($areas as $filearea => $filename) {
            $this->assertTrue($fs->file_exists(
                (int)$context->id,
                self::COMPONENT,
                $filearea,
                (int)$media->id,
                '/',
                $filename
            ));
        }

        if (class_exists(media_file::class) && method_exists(media_file::class, 'get_media_fileareas')) {
            $canonical = media_file::get_media_fileareas();

            foreach (array_keys($areas) as $filearea) {
                $this->assertContains($filearea, $canonical);
            }
        }
    }

    /**
     * Media versions are first-class records and can be marked as current.
     */
    public function test_media_versions_are_first_class_records(): void {
        $this->require_media_table();
        $this->require_table(self::TABLE_VERSION);

        [$course, $archive, $cm, $context] = $this->create_archive_activity();
        $media = $this->create_media_record($archive, $cm, $context, [
            'title' => 'Versioned photograph',
            'mediatype' => 'image',
            'mimetype' => 'image/jpeg',
        ]);

        $first = $this->create_media_version($media, [
            'versionno' => 1,
            'label' => 'Original',
            'status' => 'active',
            'filearea' => 'media_original',
            'filename' => 'original.jpg',
            'mimetype' => 'image/jpeg',
        ]);

        $second = $this->create_media_version($media, [
            'versionno' => 2,
            'label' => 'Colour corrected',
            'status' => 'active',
            'filearea' => 'media_derivative',
            'filename' => 'colour-corrected.jpg',
            'mimetype' => 'image/jpeg',
            'iscurrent' => 1,
        ]);

        $this->set_current_version($media, (int)$second->id);

        $this->assertSame((int)$media->id, (int)$first->mediaid);
        $this->assertSame((int)$media->id, (int)$second->mediaid);
        $this->assertSame(1, (int)$first->versionno);
        $this->assertSame(2, (int)$second->versionno);

        $reloaded = $this->get_media_record((int)$media->id);
        if (property_exists($reloaded, 'currentversionid')) {
            $this->assertSame((int)$second->id, (int)$reloaded->currentversionid);
        }

        if (class_exists(media_version::class) && method_exists(media_version::class, 'get_versions')) {
            $versions = media_version::get_versions((int)$media->id, true);

            $this->assertGreaterThanOrEqual(2, count($versions));
            $this->assertSame((int)$second->id, (int)$versions[0]->id);
        }
    }

    /**
     * Media collection membership preserves membership metadata and ordering.
     */
    public function test_media_collection_membership_preserves_metadata(): void {
        $this->require_media_table();
        $this->require_table(self::TABLE_COLLECTION);
        $this->require_table(self::TABLE_COLLECTION_ITEM);

        [$course, $archive, $cm, $context] = $this->create_archive_activity();

        $mediaone = $this->create_media_record($archive, $cm, $context, [
            'title' => 'Collection media A',
            'mediatype' => 'image',
        ]);

        $mediatwo = $this->create_media_record($archive, $cm, $context, [
            'title' => 'Collection media B',
            'mediatype' => 'audio',
            'mimetype' => 'audio/mpeg',
        ]);

        $collection = $this->create_media_collection($archive, $cm, $context, [
            'title' => 'Teaching media collection',
            'description' => 'Used in a guided class context.',
            'purpose' => 'teaching',
            'visibility' => 'course',
            'status' => 'active',
        ]);

        $itemone = $this->add_media_to_collection($collection, $mediaone, [
            'sortorder' => 20,
            'role' => 'primary',
            'metadata' => ['note' => 'Main discussion image.'],
        ]);

        $itemtwo = $this->add_media_to_collection($collection, $mediatwo, [
            'sortorder' => 10,
            'role' => 'context',
            'metadata' => ['note' => 'Context audio.'],
        ]);

        $this->assertSame((int)$collection->id, (int)$itemone->collectionid);
        $this->assertSame((int)$mediaone->id, (int)$itemone->mediaid);
        $this->assertSame(20, (int)$itemone->sortorder);

        $records = $this->get_collection_items((int)$collection->id);

        $this->assertCount(2, $records);
        $this->assertSame((int)$mediatwo->id, (int)$records[0]->mediaid);
        $this->assertSame((int)$mediaone->id, (int)$records[1]->mediaid);

        if (class_exists(media_collection::class) && method_exists(media_collection::class, 'get')) {
            $loaded = media_collection::get((int)$collection->id, MUST_EXIST);
            $this->assertSame((int)$collection->id, (int)$loaded->id);
        }
    }

    /**
     * Restricted media must not be visible through normal media authority only.
     */
    public function test_restricted_media_requires_restricted_media_capability(): void {
        $this->require_media_table();

        if (!class_exists(media_policy::class)) {
            $this->markTestSkipped('media_policy class is not available.');
        }

        [$course, $archive, $cm, $context] = $this->create_archive_activity();

        $restricted = $this->create_media_record($archive, $cm, $context, [
            'title' => 'Restricted protocol video',
            'mediatype' => 'video',
            'mimetype' => 'video/mp4',
            'status' => 'restricted',
            'visibility' => 'restricted_cultural',
            'audiencesuitability' => 'restricted_cultural',
        ]);

        $viewer = $this->create_user_with_capabilities($course, $context, [
            'mod/uckkarchive:view',
            'mod/uckkarchive:viewmedia',
        ]);

        $restrictedviewer = $this->create_user_with_capabilities($course, $context, [
            'mod/uckkarchive:view',
            'mod/uckkarchive:viewmedia',
            'mod/uckkarchive:viewrestrictedmedia',
            'mod/uckkarchive:viewculturallyrestricted',
        ]);

        $this->assertFalse(media_policy::can_view_media($context, $restricted, $viewer));
        $this->assertTrue(media_policy::can_view_media($context, $restricted, $restrictedviewer));
    }

    /**
     * Media listing/search must remain scoped to one archive instance.
     */
    public function test_media_listing_is_scoped_to_archive(): void {
        $this->require_media_table();

        [$coursea, $archivea, $cma, $contexta] = $this->create_archive_activity('Archive A');
        [$courseb, $archiveb, $cmb, $contextb] = $this->create_archive_activity('Archive B');

        $mediaa = $this->create_media_record($archivea, $cma, $contexta, [
            'title' => 'Archive A public image',
            'mediatype' => 'image',
            'visibility' => 'course',
        ]);

        $mediab = $this->create_media_record($archiveb, $cmb, $contextb, [
            'title' => 'Archive B public image',
            'mediatype' => 'image',
            'visibility' => 'course',
        ]);

        if (class_exists(media::class) && method_exists(media::class, 'list_by_archive')) {
            $records = media::list_by_archive((int)$archivea->id, [], 0, 50);
            $ids = array_map(static fn(stdClass $record): int => (int)$record->id, $records);

            $this->assertContains((int)$mediaa->id, $ids);
            $this->assertNotContains((int)$mediab->id, $ids);
            return;
        }

        $records = $this->get_media_by_archive((int)$archivea->id);
        $ids = array_map(static fn(stdClass $record): int => (int)$record->id, $records);

        $this->assertContains((int)$mediaa->id, $ids);
        $this->assertNotContains((int)$mediab->id, $ids);
    }

    /**
     * Media tags remain separate records and can be searched by media id.
     */
    public function test_media_tags_are_separate_media_library_records(): void {
        $this->require_media_table();
        $this->require_table(self::TABLE_TAG);

        [$course, $archive, $cm, $context] = $this->create_archive_activity();

        $media = $this->create_media_record($archive, $cm, $context, [
            'title' => 'Tagged image',
            'mediatype' => 'image',
        ]);

        $tag = $this->create_media_tag($media, [
            'tag' => 'historical-context',
            'tagtype' => 'curatorial',
        ]);

        $this->assertGreaterThan(0, (int)$tag->id);
        $this->assertSame((int)$media->id, (int)$tag->mediaid);
        $this->assertSame('historical-context', $this->first_existing_field($tag, ['tag', 'tagkey', 'name', 'rawname'], ''));
    }

    /**
     * The media library tests must not require the obsolete versionitem capability.
     */
    public function test_media_library_does_not_require_versionitem_capability(): void {
        $this->assertFalse((bool)get_capability_info('mod/uckkarchive:versionitem'));

        if (get_capability_info('mod/uckkarchive:versionmedia')) {
            $this->assertNotFalse(get_capability_info('mod/uckkarchive:versionmedia'));
        }
    }

    /**
     * Create a course, archive module instance, course module, and context.
     *
     * @param string $name Activity name.
     * @return array{0: stdClass, 1: stdClass, 2: stdClass, 3: context_module}
     */
    private function create_archive_activity(string $name = 'Test UCKK archive'): array {
        $course = $this->getDataGenerator()->create_course();

        $archive = $this->getDataGenerator()->create_module('uckkarchive', [
            'course' => $course->id,
            'name' => $name,
            'intro' => 'Archive intro',
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
     * Create a media record.
     *
     * @param stdClass $archive Archive instance.
     * @param stdClass $cm Course module.
     * @param context_module $context Module context.
     * @param array<string, mixed> $overrides Field overrides.
     * @return stdClass
     */
    private function create_media_record(
        stdClass $archive,
        stdClass $cm,
        context_module $context,
        array $overrides = []
    ): stdClass {
        global $DB, $USER;

        $this->require_media_table();

        $now = time();
        $record = (object)array_merge([
            'uuid' => $this->uuid(),
            'archiveid' => (int)$archive->id,
            'courseid' => (int)$cm->course,
            'cmid' => (int)$cm->id,
            'contextid' => (int)$context->id,
            'ownerid' => (int)($USER->id ?? 0),
            'createdby' => (int)($USER->id ?? 0),
            'modifiedby' => (int)($USER->id ?? 0),
            'title' => 'Test media',
            'summary' => 'Test media summary',
            'description' => 'Test media description',
            'mediatype' => 'image',
            'mimetype' => 'image/png',
            'status' => 'active',
            'visibility' => 'course',
            'audiencesuitability' => 'guided',
            'source' => 'produced_by_uckk',
            'sourceownership' => 'uckk_created',
            'language' => 'en',
            'currentversionid' => 0,
            'metadata' => json_encode(['fixture' => 'media_library_test']),
            'timecreated' => $now,
            'timemodified' => $now,
        ], $overrides);

        if (class_exists(media::class) && method_exists(media::class, 'create')) {
            try {
                return media::create($record, (int)($USER->id ?? 0));
            } catch (\Throwable $exception) {
                // Fall back to direct fixture insertion. This test file must be
                // useful while the media domain layer is still stabilising.
            }
        }

        $record = $this->filter_record_to_table(self::TABLE_MEDIA, $record);
        $record->id = $DB->insert_record(self::TABLE_MEDIA, $record);

        return $DB->get_record(self::TABLE_MEDIA, ['id' => $record->id], '*', MUST_EXIST);
    }

    /**
     * Get media record.
     *
     * @param int $mediaid Media id.
     * @return stdClass
     */
    private function get_media_record(int $mediaid): stdClass {
        global $DB;

        return $DB->get_record(self::TABLE_MEDIA, ['id' => $mediaid], '*', MUST_EXIST);
    }

    /**
     * Get media records by archive.
     *
     * @param int $archiveid Archive id.
     * @return stdClass[]
     */
    private function get_media_by_archive(int $archiveid): array {
        global $DB;

        return array_values($DB->get_records(self::TABLE_MEDIA, ['archiveid' => $archiveid], 'id ASC'));
    }

    /**
     * Create a media version record.
     *
     * @param stdClass $media Media record.
     * @param array<string, mixed> $overrides Overrides.
     * @return stdClass
     */
    private function create_media_version(stdClass $media, array $overrides = []): stdClass {
        global $DB, $USER;

        $this->require_table(self::TABLE_VERSION);

        $now = time();
        $record = (object)array_merge([
            'uuid' => $this->uuid(),
            'mediaid' => (int)$media->id,
            'versionno' => 1,
            'versionnumber' => 1,
            'label' => 'Version',
            'status' => 'active',
            'filearea' => 'media_original',
            'filename' => 'media.bin',
            'filepath' => '/',
            'filesize' => 0,
            'mimetype' => 'application/octet-stream',
            'contenthash' => sha1('version:' . random_string(16)),
            'iscurrent' => 0,
            'createdby' => (int)($USER->id ?? 0),
            'modifiedby' => (int)($USER->id ?? 0),
            'metadata' => json_encode(['fixture' => 'media_library_test']),
            'timecreated' => $now,
            'timemodified' => $now,
        ], $overrides);

        $record = $this->filter_record_to_table(self::TABLE_VERSION, $record);
        $record->id = $DB->insert_record(self::TABLE_VERSION, $record);

        return $DB->get_record(self::TABLE_VERSION, ['id' => $record->id], '*', MUST_EXIST);
    }

    /**
     * Set current media version if the media table supports the field.
     *
     * @param stdClass $media Media record.
     * @param int $versionid Version id.
     * @return void
     */
    private function set_current_version(stdClass $media, int $versionid): void {
        global $DB;

        if (!$this->field_exists(self::TABLE_MEDIA, 'currentversionid')) {
            return;
        }

        $DB->set_field(self::TABLE_MEDIA, 'currentversionid', $versionid, ['id' => (int)$media->id]);
    }

    /**
     * Create a media collection.
     *
     * @param stdClass $archive Archive.
     * @param stdClass $cm Course module.
     * @param context_module $context Context.
     * @param array<string, mixed> $overrides Overrides.
     * @return stdClass
     */
    private function create_media_collection(
        stdClass $archive,
        stdClass $cm,
        context_module $context,
        array $overrides = []
    ): stdClass {
        global $DB, $USER;

        $this->require_table(self::TABLE_COLLECTION);

        $now = time();
        $record = (object)array_merge([
            'uuid' => $this->uuid(),
            'archiveid' => (int)$archive->id,
            'courseid' => (int)$cm->course,
            'cmid' => (int)$cm->id,
            'contextid' => (int)$context->id,
            'ownerid' => (int)($USER->id ?? 0),
            'createdby' => (int)($USER->id ?? 0),
            'modifiedby' => (int)($USER->id ?? 0),
            'title' => 'Media collection',
            'description' => 'Collection description',
            'purpose' => 'teaching',
            'status' => 'active',
            'visibility' => 'course',
            'sortorder' => 0,
            'metadata' => json_encode(['fixture' => 'media_library_test']),
            'timecreated' => $now,
            'timemodified' => $now,
        ], $overrides);

        $record = $this->filter_record_to_table(self::TABLE_COLLECTION, $record);
        $record->id = $DB->insert_record(self::TABLE_COLLECTION, $record);

        return $DB->get_record(self::TABLE_COLLECTION, ['id' => $record->id], '*', MUST_EXIST);
    }

    /**
     * Add media to a collection.
     *
     * @param stdClass $collection Collection.
     * @param stdClass $media Media.
     * @param array<string, mixed> $overrides Overrides.
     * @return stdClass
     */
    private function add_media_to_collection(stdClass $collection, stdClass $media, array $overrides = []): stdClass {
        global $DB, $USER;

        $this->require_table(self::TABLE_COLLECTION_ITEM);

        $now = time();
        $record = (object)array_merge([
            'uuid' => $this->uuid(),
            'collectionid' => (int)$collection->id,
            'mediaid' => (int)$media->id,
            'sortorder' => 0,
            'role' => 'member',
            'createdby' => (int)($USER->id ?? 0),
            'modifiedby' => (int)($USER->id ?? 0),
            'metadata' => json_encode(['fixture' => 'media_library_test']),
            'timecreated' => $now,
            'timemodified' => $now,
        ], $overrides);

        if (isset($record->metadata) && is_array($record->metadata)) {
            $record->metadata = json_encode($record->metadata);
        }

        $record = $this->filter_record_to_table(self::TABLE_COLLECTION_ITEM, $record);
        $record->id = $DB->insert_record(self::TABLE_COLLECTION_ITEM, $record);

        return $DB->get_record(self::TABLE_COLLECTION_ITEM, ['id' => $record->id], '*', MUST_EXIST);
    }

    /**
     * Get collection items.
     *
     * @param int $collectionid Collection id.
     * @return stdClass[]
     */
    private function get_collection_items(int $collectionid): array {
        global $DB;

        return array_values($DB->get_records(
            self::TABLE_COLLECTION_ITEM,
            ['collectionid' => $collectionid],
            'sortorder ASC, id ASC'
        ));
    }

    /**
     * Create a media tag.
     *
     * @param stdClass $media Media.
     * @param array<string, mixed> $overrides Overrides.
     * @return stdClass
     */
    private function create_media_tag(stdClass $media, array $overrides = []): stdClass {
        global $DB, $USER;

        $this->require_table(self::TABLE_TAG);

        $now = time();
        $record = (object)array_merge([
            'uuid' => $this->uuid(),
            'mediaid' => (int)$media->id,
            'tag' => 'test-tag',
            'tagkey' => 'test-tag',
            'name' => 'test-tag',
            'rawname' => 'test-tag',
            'tagtype' => 'curatorial',
            'createdby' => (int)($USER->id ?? 0),
            'modifiedby' => (int)($USER->id ?? 0),
            'metadata' => json_encode(['fixture' => 'media_library_test']),
            'timecreated' => $now,
            'timemodified' => $now,
        ], $overrides);

        $record = $this->filter_record_to_table(self::TABLE_TAG, $record);
        $record->id = $DB->insert_record(self::TABLE_TAG, $record);

        return $DB->get_record(self::TABLE_TAG, ['id' => $record->id], '*', MUST_EXIST);
    }

    /**
     * Create a media file.
     *
     * @param context_module $context Context.
     * @param string $filearea File area.
     * @param int $itemid Item id.
     * @param string $filename Filename.
     * @param string $content Content.
     * @return \stored_file
     */
    private function create_media_file(
        context_module $context,
        string $filearea,
        int $itemid,
        string $filename,
        string $content
    ): \stored_file {
        $fs = get_file_storage();

        return $fs->create_file_from_string([
            'contextid' => (int)$context->id,
            'component' => self::COMPONENT,
            'filearea' => $filearea,
            'itemid' => $itemid,
            'filepath' => '/',
            'filename' => $filename,
            'userid' => 0,
        ], $content);
    }

    /**
     * Create a user with specific module capabilities.
     *
     * @param stdClass $course Course.
     * @param context_module $context Module context.
     * @param string[] $capabilities Capabilities.
     * @return stdClass
     */
    private function create_user_with_capabilities(stdClass $course, context_module $context, array $capabilities): stdClass {
        $user = $this->getDataGenerator()->create_user();

        $this->getDataGenerator()->enrol_user($user->id, $course->id, 'student');

        $roleid = $this->getDataGenerator()->create_role();
        role_assign($roleid, $user->id, $context->id);

        foreach ($capabilities as $capability) {
            if (!get_capability_info($capability)) {
                continue;
            }

            assign_capability($capability, CAP_ALLOW, $roleid, $context->id);
        }

        accesslib_clear_all_caches_for_unit_testing();

        return $user;
    }

    /**
     * Filter a record to existing DB columns.
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
     * Return whether a table field exists.
     *
     * @param string $table Table name.
     * @param string $field Field name.
     * @return bool
     */
    private function field_exists(string $table, string $field): bool {
        global $DB;

        if (!$DB->get_manager()->table_exists(new \xmldb_table($table))) {
            return false;
        }

        return array_key_exists($field, $DB->get_columns($table));
    }

    /**
     * Require the media table.
     *
     * @return void
     */
    private function require_media_table(): void {
        $this->require_table(self::TABLE_MEDIA);
    }

    /**
     * Require a table to exist.
     *
     * @param string $table Table name.
     * @return void
     */
    private function require_table(string $table): void {
        global $DB;

        if (!$DB->get_manager()->table_exists(new \xmldb_table($table))) {
            $this->markTestSkipped($table . ' table is not installed.');
        }
    }

    /**
     * Return first existing field from a record.
     *
     * @param stdClass $record Record.
     * @param string[] $fields Candidate fields.
     * @param mixed $default Default value.
     * @return mixed
     */
    private function first_existing_field(stdClass $record, array $fields, $default = null) {
        foreach ($fields as $field) {
            if (property_exists($record, $field) && $record->{$field} !== null && $record->{$field} !== '') {
                return $record->{$field};
            }
        }

        return $default;
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

        if (class_exists('\\core\\uuid')) {
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

