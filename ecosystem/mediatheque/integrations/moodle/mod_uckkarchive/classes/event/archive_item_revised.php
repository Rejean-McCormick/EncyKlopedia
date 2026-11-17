<?php
// This file is part of Moodle - https://moodle.org/
//
// Moodle is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// any later version.

/**
 * Event fired when a UCKK archive item is revised.
 *
 * @package    mod_uckkarchive
 * @copyright  2026 Univers-Cité King Klown
 * @license    https://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later
 */

declare(strict_types=1);

namespace mod_uckkarchive\event;

defined('MOODLE_INTERNAL') || die();

/**
 * Event fired when an archive item receives a new revision.
 *
 * This event records the revision of an archive item. It does not validate,
 * publish, export, redact, or decide integrity state by itself.
 *
 * Expected creation:
 *
 * $event = \mod_uckkarchive\event\archive_item_revised::create([
 *     'objectid' => $item->id,
 *     'context' => $context,
 *     'other' => [
 *         'archiveid' => $archive->id,
 *         'revisionid' => $revision->id,
 *         'courseid' => $course->id,
 *         'cmid' => $cm->id,
 *         'fromversion' => $previousversion,
 *         'toversion' => $item->versionno,
 *         'status' => $item->status,
 *         'visibility' => $item->visibility,
 *         'validationstate' => $item->validationstate ?? 'unverified',
 *     ],
 * ]);
 * $event->add_record_snapshot('course', $course);
 * $event->add_record_snapshot('course_modules', $cm);
 * $event->add_record_snapshot('uckkarchive', $archive);
 * $event->add_record_snapshot('uckkarchive_item', $item);
 * $event->add_record_snapshot('uckkarchive_rev', $revision);
 * $event->trigger();
 */
final class archive_item_revised extends \core\event\base {
    /**
     * Initialise event data.
     */
    protected function init(): void {
        $this->data['crud'] = 'u';
        $this->data['edulevel'] = self::LEVEL_OTHER;
        $this->data['objecttable'] = 'uckkarchive_item';
    }

    /**
     * Return localised event name.
     *
     * @return string
     */
    public static function get_name(): string {
        return get_string('eventarchiveitemrevised', 'uckkarchive');
    }

    /**
     * Return event description.
     *
     * @return string
     */
    public function get_description(): string {
        $revisionid = $this->other['revisionid'] ?? 0;
        $archiveid = $this->other['archiveid'] ?? 0;
        $fromversion = $this->other['fromversion'] ?? '';
        $toversion = $this->other['toversion'] ?? '';

        return "The user with id '{$this->userid}' revised the UCKK archive item with id " .
            "'{$this->objectid}' in archive '{$archiveid}', creating revision '{$revisionid}' " .
            "from version '{$fromversion}' to version '{$toversion}' in course module " .
            "'{$this->contextinstanceid}'.";
    }

    /**
     * Return the URL related to the revised archive item.
     *
     * @return \moodle_url
     */
    public function get_url(): \moodle_url {
        $params = [
            'id' => $this->contextinstanceid,
            'itemid' => $this->objectid,
        ];

        if (!empty($this->other['revisionid'])) {
            $params['revisionid'] = $this->other['revisionid'];
        }

        return new \moodle_url('/mod/uckkarchive/item.php', $params);
    }

    /**
     * Return object id mapping for backup and restore.
     *
     * @return array
     */
    public static function get_objectid_mapping(): array {
        return [
            'db' => 'uckkarchive_item',
            'restore' => 'uckkarchive_item',
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
            'revisionid' => [
                'db' => 'uckkarchive_rev',
                'restore' => 'uckkarchive_rev',
            ],
            'courseid' => [
                'db' => 'course',
                'restore' => 'course',
            ],
            'cmid' => [
                'db' => 'course_modules',
                'restore' => 'course_module',
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
            throw new \coding_exception('The archive_item_revised event must use module context.');
        }

        if (empty($this->objectid)) {
            throw new \coding_exception('The archive_item_revised event requires objectid.');
        }

        if (empty($this->other['archiveid'])) {
            throw new \coding_exception('The archive_item_revised event requires archiveid in other.');
        }

        if (empty($this->other['revisionid'])) {
            throw new \coding_exception('The archive_item_revised event requires revisionid in other.');
        }

        if (empty($this->other['courseid'])) {
            throw new \coding_exception('The archive_item_revised event requires courseid in other.');
        }

        if (empty($this->other['cmid'])) {
            throw new \coding_exception('The archive_item_revised event requires cmid in other.');
        }

        if (!array_key_exists('fromversion', $this->other)) {
            throw new \coding_exception('The archive_item_revised event requires fromversion in other.');
        }

        if (empty($this->other['toversion'])) {
            throw new \coding_exception('The archive_item_revised event requires toversion in other.');
        }
    }
}