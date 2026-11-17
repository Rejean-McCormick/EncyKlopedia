<?php
// This file is part of Moodle - https://moodle.org/
//
// Moodle is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// any later version.

/**
 * Event fired when a UCKK archive item is validated.
 *
 * @package    mod_uckkarchive
 * @copyright  2026 Univers-Cité King Klown
 * @license    https://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later
 */

declare(strict_types=1);

namespace mod_uckkarchive\event;

defined('MOODLE_INTERNAL') || die();

/**
 * Event fired when an archive item is validated.
 *
 * This is a privileged archive event. It records that an authorised reviewer
 * validated an archive item. It does not itself decide validation, change
 * visibility, update provenance, revise evidence, or publish the item.
 */
final class archive_item_validated extends \core\event\base {
    /**
     * Initialise event data.
     */
    protected function init(): void {
        $this->data['crud'] = 'u';
        $this->data['edulevel'] = self::LEVEL_TEACHING;
        $this->data['objecttable'] = 'uckkarchive_item';
    }

    /**
     * Return localised event name.
     *
     * @return string
     */
    public static function get_name(): string {
        return get_string('eventarchiveitemvalidated', 'uckkarchive');
    }

    /**
     * Return event description.
     *
     * @return string
     */
    public function get_description(): string {
        $archiveid = $this->other['archiveid'] ?? 0;
        $validationstate = $this->other['validationstate'] ?? '';
        $previousstate = $this->other['previousvalidationstate'] ?? '';

        return "The user with id '{$this->userid}' validated the UCKK archive item with id " .
            "'{$this->objectid}' in archive instance id '{$archiveid}' and course module id " .
            "'{$this->contextinstanceid}'. Validation state changed from '{$previousstate}' " .
            "to '{$validationstate}'.";
    }

    /**
     * Return related URL.
     *
     * @return \moodle_url
     */
    public function get_url(): \moodle_url {
        return new \moodle_url('/mod/uckkarchive/item.php', [
            'id' => $this->contextinstanceid,
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
     * Return mappings for ids stored in the other field.
     *
     * @return array
     */
    public static function get_other_mapping(): array {
        return [
            'courseid' => [
                'db' => 'course',
                'restore' => 'course',
            ],
            'cmid' => [
                'db' => 'course_modules',
                'restore' => 'course_module',
            ],
            'archiveid' => [
                'db' => 'uckkarchive',
                'restore' => 'uckkarchive',
            ],
            'validatorid' => [
                'db' => 'user',
                'restore' => 'user',
            ],
            'integritycaseid' => [
                'db' => 'tool_uckki_case',
                'restore' => 'tool_uckkintegrity_case',
            ],
        ];
    }

    /**
     * Validate required event data.
     *
     * Expected creation:
     *
     * $event = \mod_uckkarchive\event\archive_item_validated::create([
     *     'objectid' => $item->id,
     *     'context' => $context,
     *     'other' => [
     *         'courseid' => $course->id,
     *         'cmid' => $cm->id,
     *         'archiveid' => $archive->id,
     *         'validatorid' => $USER->id,
     *         'status' => $item->status,
     *         'visibility' => $item->visibility,
     *         'validationstate' => $item->validationstate,
     *         'previousvalidationstate' => $previousstate,
     *         'versionno' => $item->versionno,
     *         'integritycaseid' => $item->integritycaseid ?? 0,
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
            throw new \coding_exception('The archive_item_validated event must use module context.');
        }

        if (empty($this->objectid)) {
            throw new \coding_exception('The archive_item_validated event requires objectid.');
        }

        if (empty($this->other['courseid'])) {
            throw new \coding_exception('The archive_item_validated event requires courseid in other.');
        }

        if (empty($this->other['cmid'])) {
            throw new \coding_exception('The archive_item_validated event requires cmid in other.');
        }

        if (empty($this->other['archiveid'])) {
            throw new \coding_exception('The archive_item_validated event requires archiveid in other.');
        }

        if (empty($this->other['validatorid'])) {
            throw new \coding_exception('The archive_item_validated event requires validatorid in other.');
        }

        if (!array_key_exists('status', $this->other)) {
            throw new \coding_exception('The archive_item_validated event requires status in other.');
        }

        if (!array_key_exists('visibility', $this->other)) {
            throw new \coding_exception('The archive_item_validated event requires visibility in other.');
        }

        if (!array_key_exists('validationstate', $this->other)) {
            throw new \coding_exception('The archive_item_validated event requires validationstate in other.');
        }

        if (!array_key_exists('previousvalidationstate', $this->other)) {
            throw new \coding_exception('The archive_item_validated event requires previousvalidationstate in other.');
        }
    }
}