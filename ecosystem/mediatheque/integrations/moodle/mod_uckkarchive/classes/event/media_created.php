<?php
// This file is part of Moodle - https://moodle.org/
//
// Moodle is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// any later version.

/**
 * Event fired when a UCKK Archive media record is created.
 *
 * @package    mod_uckkarchive
 * @copyright  2026 Univers-Cité King Klown
 * @license    https://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later
 */

declare(strict_types=1);

namespace mod_uckkarchive\event;

defined('MOODLE_INTERNAL') || die();

/**
 * Event fired when a media record is created.
 *
 * This event records successful creation of a first-class media object.
 * It does not validate the media, approve content advisories, decide cultural
 * protocol access, export files, publish restricted material, or grant any
 * authority by itself.
 *
 * Expected creation:
 *
 * $event = \mod_uckkarchive\event\media_created::create([
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
 *         'audiencesuitability' => $media->audiencesuitability,
 *         'sourceid' => $media->sourceid ?? 0,
 *         'currentversionid' => $media->currentversionid ?? 0,
 *     ],
 * ]);
 * $event->add_record_snapshot('course', $course);
 * $event->add_record_snapshot('course_modules', $cm);
 * $event->add_record_snapshot('uckkarchive', $archive);
 * $event->add_record_snapshot('uckkarchive_media', $media);
 * $event->trigger();
 */
final class media_created extends \core\event\base {
    /**
     * Initialise event data.
     */
    protected function init(): void {
        $this->data['crud'] = 'c';
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

        if ($manager->string_exists('eventmediacreated', 'uckkarchive')) {
            return get_string('eventmediacreated', 'uckkarchive');
        }

        if ($manager->string_exists('event:mediacreated', 'uckkarchive')) {
            return get_string('event:mediacreated', 'uckkarchive');
        }

        return 'Media created';
    }

    /**
     * Return event description.
     *
     * @return string
     */
    public function get_description(): string {
        $archiveid = $this->other['archiveid'] ?? 0;
        $cmid = $this->other['cmid'] ?? $this->contextinstanceid;
        $mediatype = $this->other['mediatype'] ?? '';
        $status = $this->other['status'] ?? '';
        $visibility = $this->other['visibility'] ?? '';

        return "The user with id '{$this->userid}' created the UCKK archive media record with id " .
            "'{$this->objectid}' in archive instance id '{$archiveid}' and course module id '{$cmid}'. " .
            "Media type is '{$mediatype}', status is '{$status}', and visibility is '{$visibility}'.";
    }

    /**
     * Return URL related to the media record.
     *
     * @return \moodle_url
     */
    public function get_url(): \moodle_url {
        return new \moodle_url('/mod/uckkarchive/media.php', [
            'id' => $this->other['cmid'] ?? $this->contextinstanceid,
            'mediaid' => $this->objectid,
        ]);
    }

    /**
     * Return object id mapping for backup and restore.
     *
     * @return array
     */
    public static function get_objectid_mapping(): array {
        return [
            'db' => 'uckkarchive_media',
            'restore' => 'uckkarchive_media',
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
            'sourceid' => [
                'db' => 'uckkarchive_media_source',
                'restore' => 'uckkarchive_media_source',
            ],
            'currentversionid' => [
                'db' => 'uckkarchive_media_version',
                'restore' => 'uckkarchive_media_version',
            ],
        ];
    }

    /**
     * Validate required event data.
     *
     * @return void
     * @throws \coding_exception
     */
    protected function validate_data(): void {
        parent::validate_data();

        if ($this->contextlevel !== CONTEXT_MODULE) {
            throw new \coding_exception('The media_created event must use module context.');
        }

        if (empty($this->objectid)) {
            throw new \coding_exception('The media_created event requires objectid.');
        }

        if (empty($this->other['archiveid'])) {
            throw new \coding_exception('The media_created event requires archiveid in other.');
        }

        if (empty($this->other['courseid'])) {
            throw new \coding_exception('The media_created event requires courseid in other.');
        }

        if (empty($this->other['cmid'])) {
            throw new \coding_exception('The media_created event requires cmid in other.');
        }

        if (!array_key_exists('mediatype', $this->other)) {
            throw new \coding_exception('The media_created event requires mediatype in other.');
        }

        if (!array_key_exists('status', $this->other)) {
            throw new \coding_exception('The media_created event requires status in other.');
        }

        if (!array_key_exists('visibility', $this->other)) {
            throw new \coding_exception('The media_created event requires visibility in other.');
        }
    }
}