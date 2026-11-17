<?php
// This file is part of Moodle - https://moodle.org/
//
// Moodle is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// any later version.

/**
 * Event fired when a UCKK archive item is created.
 *
 * @package    mod_uckkarchive
 * @copyright  2026 Univers-Cité King Klown
 * @license    https://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later
 */

declare(strict_types=1);

namespace mod_uckkarchive\event;

defined('MOODLE_INTERNAL') || die();

/**
 * Event fired when a UCKK archive item is created.
 *
 * This event records creation of an archive memory object. It does not validate
 * the archive item, revise it, export it, alter provenance, or decide
 * visibility. Those decisions remain in capability-checked service/controller
 * code.
 */
final class archive_item_created extends \core\event\base {
    /**
     * Initialise event data.
     */
    protected function init(): void {
        $this->data['crud'] = 'c';
        $this->data['edulevel'] = self::LEVEL_PARTICIPATING;
        $this->data['objecttable'] = 'uckkarchive_item';
    }

    /**
     * Return localised event name.
     *
     * @return string
     */
    public static function get_name(): string {
        return get_string('eventarchiveitemcreated', 'uckkarchive');
    }

    /**
     * Return event description.
     *
     * @return string
     */
    public function get_description(): string {
        $archiveid = $this->other['archiveid'] ?? 0;
        $cmid = $this->other['cmid'] ?? $this->contextinstanceid;

        return "The user with id '{$this->userid}' created the UCKK archive item with id " .
            "'{$this->objectid}' in archive instance id '{$archiveid}' and course module id '{$cmid}'.";
    }

    /**
     * Return URL related to the archive item.
     *
     * @return \moodle_url
     */
    public function get_url(): \moodle_url {
        return new \moodle_url('/mod/uckkarchive/item.php', [
            'id' => $this->other['cmid'] ?? $this->contextinstanceid,
            'itemid' => $this->objectid,
        ]);
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
        ];
    }

    /**
     * Validate event data before triggering.
     *
     * Expected creation:
     *
     * $event = \mod_uckkarchive\event\archive_item_created::create([
     *     'objectid' => $item->id,
     *     'context' => $context,
     *     'other' => [
     *         'archiveid' => $archive->id,
     *         'courseid' => $course->id,
     *         'cmid' => $cm->id,
     *         'itemtype' => $item->itemtype,
     *         'status' => $item->status,
     *         'visibility' => $item->visibility,
     *         'provenance' => $item->provenance,
     *     ],
     * ]);
     * $event->add_record_snapshot('course', $course);
     * $event->add_record_snapshot('course_modules', $cm);
     * $event->add_record_snapshot('uckkarchive', $archive);
     * $event->add_record_snapshot('uckkarchive_item', $item);
     * $event->trigger();
     */
    protected function validate_data(): void {
        parent::validate_data();

        if ($this->contextlevel !== CONTEXT_MODULE) {
            throw new \coding_exception('The archive_item_created event must use module context.');
        }

        if (empty($this->objectid)) {
            throw new \coding_exception('The archive_item_created event requires objectid.');
        }

        if (empty($this->other['archiveid'])) {
            throw new \coding_exception('The archive_item_created event requires archiveid in other.');
        }

        if (empty($this->other['courseid'])) {
            throw new \coding_exception('The archive_item_created event requires courseid in other.');
        }

        if (empty($this->other['cmid'])) {
            throw new \coding_exception('The archive_item_created event requires cmid in other.');
        }
    }
}