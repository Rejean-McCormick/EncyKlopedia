<?php
// This file is part of Moodle - https://moodle.org/
//
// Moodle is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// any later version.

/**
 * Event fired when a UCKK Archive media collection is created.
 *
 * @package    mod_uckkarchive
 * @copyright  2026 Univers-Cité King Klown
 * @license    https://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later
 */

declare(strict_types=1);

namespace mod_uckkarchive\event;

defined('MOODLE_INTERNAL') || die();

/**
 * Event fired when a media collection is created.
 *
 * This event records the successful creation of a media collection in the
 * UCKK Archive media library. It does not grant access, change media
 * visibility, override cultural protocol restrictions, export files, or decide
 * policy. Those decisions remain in capability-checked service/controller code.
 *
 * Expected creation:
 *
 * $event = \mod_uckkarchive\event\media_collection_created::create([
 *     'objectid' => $collection->id,
 *     'context' => $context,
 *     'other' => [
 *         'archiveid' => $archive->id,
 *         'courseid' => $course->id,
 *         'cmid' => $cm->id,
 *         'uuid' => $collection->uuid ?? '',
 *         'status' => $collection->status ?? 'active',
 *         'visibility' => $collection->visibility ?? 'course',
 *         'collectiontype' => $collection->collectiontype ?? '',
 *         'ownerid' => $collection->ownerid ?? 0,
 *         'itemcount' => $collection->itemcount ?? 0,
 *     ],
 * ]);
 * $event->add_record_snapshot('course', $course);
 * $event->add_record_snapshot('course_modules', $cm);
 * $event->add_record_snapshot('uckkarchive', $archive);
 * $event->add_record_snapshot('uckkarchive_media_collection', $collection);
 * $event->trigger();
 */
final class media_collection_created extends \core\event\base {
    /**
     * Initialise event data.
     */
    protected function init(): void {
        $this->data['crud'] = 'c';
        $this->data['edulevel'] = self::LEVEL_PARTICIPATING;
        $this->data['objecttable'] = 'uckkarchive_media_collection';
    }

    /**
     * Return localised event name.
     *
     * @return string
     */
    public static function get_name(): string {
        return get_string('eventmediacollectioncreated', 'uckkarchive');
    }

    /**
     * Return event description.
     *
     * @return string
     */
    public function get_description(): string {
        $archiveid = $this->other['archiveid'] ?? 0;
        $cmid = $this->other['cmid'] ?? $this->contextinstanceid;
        $visibility = $this->other['visibility'] ?? '';
        $status = $this->other['status'] ?? '';

        return "The user with id '{$this->userid}' created the UCKK Archive media collection " .
            "with id '{$this->objectid}' in archive instance id '{$archiveid}' and course " .
            "module id '{$cmid}'. Collection status is '{$status}' and visibility is '{$visibility}'.";
    }

    /**
     * Return related URL.
     *
     * @return \moodle_url
     */
    public function get_url(): \moodle_url {
        return new \moodle_url('/mod/uckkarchive/media.php', [
            'id' => $this->other['cmid'] ?? $this->contextinstanceid,
            'collectionid' => $this->objectid,
        ]);
    }

    /**
     * Return object id mapping for backup and restore.
     *
     * @return array
     */
    public static function get_objectid_mapping(): array {
        return [
            'db' => 'uckkarchive_media_collection',
            'restore' => 'uckkarchive_media_collection',
        ];
    }

    /**
     * Return mappings for ids stored in the other field.
     *
     * @return array
     */
    public static function get_other_mapping(): array {
        return [
            'archiveid' => [
                'db' => 'uckkarchive',
                'restore' => 'uckkarchive',
            ],
            'courseid' => [
                'db' => 'course',
                'restore' => 'course',
            ],
            'cmid' => [
                'db' => 'course_modules',
                'restore' => 'course_module',
            ],
            'ownerid' => [
                'db' => 'user',
                'restore' => 'user',
            ],
        ];
    }

    /**
     * Validate required event data.
     *
     * Required safe payload:
     *
     * - objectid: media collection id;
     * - context: module context;
     * - other.archiveid;
     * - other.courseid;
     * - other.cmid.
     *
     * Optional safe payload:
     *
     * - other.uuid;
     * - other.status;
     * - other.visibility;
     * - other.collectiontype;
     * - other.ownerid;
     * - other.itemcount.
     *
     * The event payload must not include raw media content, file contents,
     * private cultural protocol notes, private reviewer notes, or redacted
     * metadata.
     *
     * @return void
     */
    protected function validate_data(): void {
        parent::validate_data();

        if ($this->contextlevel !== CONTEXT_MODULE) {
            throw new \coding_exception('The media_collection_created event must use module context.');
        }

        if (empty($this->objectid)) {
            throw new \coding_exception('The media_collection_created event requires objectid.');
        }

        if (empty($this->other['archiveid'])) {
            throw new \coding_exception('The media_collection_created event requires archiveid in other.');
        }

        if (empty($this->other['courseid'])) {
            throw new \coding_exception('The media_collection_created event requires courseid in other.');
        }

        if (empty($this->other['cmid'])) {
            throw new \coding_exception('The media_collection_created event requires cmid in other.');
        }

        if (array_key_exists('itemcount', $this->other) && (int)$this->other['itemcount'] < 0) {
            throw new \coding_exception('The media_collection_created event itemcount cannot be negative.');
        }
    }
}