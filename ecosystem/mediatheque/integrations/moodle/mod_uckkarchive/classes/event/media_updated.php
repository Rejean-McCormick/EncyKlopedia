<?php
// This file is part of Moodle - https://moodle.org/
//
// Moodle is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// any later version.

/**
 * Event fired when UCKK Archive media is updated.
 *
 * @package    mod_uckkarchive
 * @copyright  2026 Univers-Cité King Klown
 * @license    https://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later
 */

declare(strict_types=1);

namespace mod_uckkarchive\event;

defined('MOODLE_INTERNAL') || die();

/**
 * Event fired when a media record is updated.
 *
 * This event records that a media object changed. It does not decide
 * visibility, restriction, cultural access, File API access, advisory state,
 * validation state, or export eligibility. Those decisions remain in
 * capability-checked domain services and pluginfile handling.
 *
 * Expected creation:
 *
 * $event = \mod_uckkarchive\event\media_updated::create([
 *     'objectid' => $media->id,
 *     'context' => $context,
 *     'other' => [
 *         'archiveid' => $archive->id,
 *         'courseid' => $course->id,
 *         'cmid' => $cm->id,
 *         'uuid' => $media->uuid,
 *         'mediatype' => $media->mediatype,
 *         'status' => $media->status,
 *         'visibility' => $media->visibility,
 *         'changedfields' => 'title,status,visibility',
 *     ],
 * ]);
 * $event->add_record_snapshot('course', $course);
 * $event->add_record_snapshot('course_modules', $cm);
 * $event->add_record_snapshot('uckkarchive', $archive);
 * $event->add_record_snapshot('uckkarchive_media', $media);
 * $event->trigger();
 */
final class media_updated extends \core\event\base {
    /**
     * Initialise event data.
     */
    protected function init(): void {
        $this->data['crud'] = 'u';
        $this->data['edulevel'] = self::LEVEL_PARTICIPATING;
        $this->data['objecttable'] = 'uckkarchive_media';
    }

    /**
     * Return localised event name.
     *
     * @return string
     */
    public static function get_name(): string {
        $manager = get_string_manager();

        if ($manager->string_exists('eventmediaupdated', 'uckkarchive')) {
            return get_string('eventmediaupdated', 'uckkarchive');
        }

        if ($manager->string_exists('event:mediaupdated', 'uckkarchive')) {
            return get_string('event:mediaupdated', 'uckkarchive');
        }

        return 'Media updated';
    }

    /**
     * Return event description.
     *
     * @return string
     */
    public function get_description(): string {
        $archiveid = $this->other['archiveid'] ?? 0;
        $cmid = $this->other['cmid'] ?? $this->contextinstanceid;
        $uuid = $this->other['uuid'] ?? '';
        $status = $this->other['status'] ?? '';
        $visibility = $this->other['visibility'] ?? '';
        $changedfields = $this->other['changedfields'] ?? '';

        return "The user with id '{$this->userid}' updated the UCKK Archive media record with id " .
            "'{$this->objectid}' and UUID '{$uuid}' in archive instance id '{$archiveid}' " .
            "and course module id '{$cmid}'. Status is '{$status}', visibility is " .
            "'{$visibility}', and changed fields are '{$changedfields}'.";
    }

    /**
     * Return URL related to the media record.
     *
     * @return \moodle_url
     */
    public function get_url(): \moodle_url {
        return new \moodle_url('/mod/uckkarchive/media.php', [
            'id' => (int)($this->other['cmid'] ?? $this->contextinstanceid),
            'mediaid' => $this->objectid,
        ]);
    }

    /**
     * Return object id mapping for backup and restore.
     *
     * @return array<string, string>
     */
    public static function get_objectid_mapping(): array {
        return [
            'db' => 'uckkarchive_media',
            'restore' => 'uckkarchive_media',
        ];
    }

    /**
     * Return mappings for values stored in the other field.
     *
     * @return array<string, array<string, string>>
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
            'versionid' => [
                'db' => 'uckkarchive_media_version',
                'restore' => 'uckkarchive_media_version',
            ],
            'collectionid' => [
                'db' => 'uckkarchive_media_collection',
                'restore' => 'uckkarchive_media_collection',
            ],
        ];
    }

    /**
     * Validate event data before triggering.
     *
     * @throws \coding_exception
     */
    protected function validate_data(): void {
        parent::validate_data();

        if ($this->contextlevel !== CONTEXT_MODULE) {
            throw new \coding_exception('The media_updated event must use module context.');
        }

        if (empty($this->objectid)) {
            throw new \coding_exception('The media_updated event requires objectid.');
        }

        if (empty($this->other['archiveid'])) {
            throw new \coding_exception('The media_updated event requires archiveid in other.');
        }

        if (empty($this->other['courseid'])) {
            throw new \coding_exception('The media_updated event requires courseid in other.');
        }

        if (empty($this->other['cmid'])) {
            throw new \coding_exception('The media_updated event requires cmid in other.');
        }

        if (!array_key_exists('uuid', $this->other)) {
            throw new \coding_exception('The media_updated event requires uuid in other.');
        }

        if (!array_key_exists('status', $this->other)) {
            throw new \coding_exception('The media_updated event requires status in other.');
        }

        if (!array_key_exists('visibility', $this->other)) {
            throw new \coding_exception('The media_updated event requires visibility in other.');
        }
    }
}