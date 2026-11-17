<?php
// This file is part of Moodle - https://moodle.org/
//
// Moodle is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// any later version.

/**
 * Event fired when a UCKK archive media version is created.
 *
 * @package    mod_uckkarchive
 * @copyright  2026 Univers-Cité King Klown
 * @license    https://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later
 */

declare(strict_types=1);

namespace mod_uckkarchive\event;

defined('MOODLE_INTERNAL') || die();

/**
 * Event fired when a media object receives a new version.
 *
 * This event records the creation of a first-class media version record.
 * It does not approve, publish, export, redact, validate, or authorize access
 * to the media file. Those decisions remain in capability-checked services,
 * media policy, content policy, and pluginfile handling.
 *
 * Expected creation:
 *
 * ```php
 * $event = \mod_uckkarchive\event\media_version_created::create([
 *     'objectid' => $version->id,
 *     'context' => $context,
 *     'other' => [
 *         'archiveid' => $archive->id,
 *         'courseid' => $course->id,
 *         'cmid' => $cm->id,
 *         'mediaid' => $media->id,
 *         'versionno' => $version->versionno,
 *         'status' => $version->status,
 *         'filearea' => $version->filearea,
 *         'filename' => $version->filename,
 *     ],
 * ]);
 * $event->add_record_snapshot('course', $course);
 * $event->add_record_snapshot('course_modules', $cm);
 * $event->add_record_snapshot('uckkarchive', $archive);
 * $event->add_record_snapshot('uckkarchive_media', $media);
 * $event->add_record_snapshot('uckkarchive_media_version', $version);
 * $event->trigger();
 * ```
 */
final class media_version_created extends \core\event\base {
    /**
     * Initialise event data.
     */
    protected function init(): void {
        $this->data['crud'] = 'c';
        $this->data['edulevel'] = self::LEVEL_OTHER;
        $this->data['objecttable'] = 'uckkarchive_media_version';
    }

    /**
     * Return localised event name.
     *
     * @return string
     */
    public static function get_name(): string {
        $manager = get_string_manager();

        if ($manager->string_exists('eventmediaversioncreated', 'uckkarchive')) {
            return get_string('eventmediaversioncreated', 'uckkarchive');
        }

        if ($manager->string_exists('event:mediaversioncreated', 'uckkarchive')) {
            return get_string('event:mediaversioncreated', 'uckkarchive');
        }

        return 'Media version created';
    }

    /**
     * Return event description.
     *
     * @return string
     */
    public function get_description(): string {
        $archiveid = $this->other['archiveid'] ?? 0;
        $mediaid = $this->other['mediaid'] ?? 0;
        $versionno = $this->other['versionno'] ?? 0;
        $cmid = $this->other['cmid'] ?? $this->contextinstanceid;

        return "The user with id '{$this->userid}' created media version '{$versionno}' " .
            "with id '{$this->objectid}' for media id '{$mediaid}' in archive instance id " .
            "'{$archiveid}' and course module id '{$cmid}'.";
    }

    /**
     * Return related URL.
     *
     * @return \moodle_url
     */
    public function get_url(): \moodle_url {
        $params = [
            'id' => (int)($this->other['cmid'] ?? $this->contextinstanceid),
        ];

        if (!empty($this->other['mediaid'])) {
            $params['mediaid'] = (int)$this->other['mediaid'];
        }

        if (!empty($this->objectid)) {
            $params['versionid'] = (int)$this->objectid;
        }

        return new \moodle_url('/mod/uckkarchive/media.php', $params);
    }

    /**
     * Return object id mapping for backup and restore.
     *
     * @return array
     */
    public static function get_objectid_mapping(): array {
        return [
            'db' => 'uckkarchive_media_version',
            'restore' => 'uckkarchive_media_version',
        ];
    }

    /**
     * Return mappings for values stored in the other field.
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
            'mediaid' => [
                'db' => 'uckkarchive_media',
                'restore' => 'uckkarchive_media',
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
            throw new \coding_exception('The media_version_created event must use module context.');
        }

        if (empty($this->objectid)) {
            throw new \coding_exception('The media_version_created event requires objectid.');
        }

        if (empty($this->other['archiveid'])) {
            throw new \coding_exception('The media_version_created event requires archiveid in other.');
        }

        if (empty($this->other['courseid'])) {
            throw new \coding_exception('The media_version_created event requires courseid in other.');
        }

        if (empty($this->other['cmid'])) {
            throw new \coding_exception('The media_version_created event requires cmid in other.');
        }

        if (empty($this->other['mediaid'])) {
            throw new \coding_exception('The media_version_created event requires mediaid in other.');
        }

        if (!isset($this->other['versionno'])) {
            throw new \coding_exception('The media_version_created event requires versionno in other.');
        }
    }
}