<?php
// This file is part of Moodle - https://moodle.org/
//
// Moodle is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// any later version.

/**
 * Event fired when a UCKK archive item is exported.
 *
 * @package    mod_uckkarchive
 * @copyright  2026 Univers-Cité King Klown
 * @license    https://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later
 */

declare(strict_types=1);

namespace mod_uckkarchive\event;

defined('MOODLE_INTERNAL') || die();

/**
 * Event fired when an archive item is exported.
 *
 * This event records an export action for an archive item. It does not itself
 * decide visibility, validation, archive policy, privacy retention, or whether
 * the export package is safe to release. Those decisions must remain in
 * capability-checked archive services/controllers.
 */
final class archive_item_exported extends \core\event\base {
    /**
     * Initialise event metadata.
     */
    protected function init(): void {
        $this->data['crud'] = 'r';
        $this->data['edulevel'] = self::LEVEL_PARTICIPATING;
        $this->data['objecttable'] = 'uckkarchive_item';
    }

    /**
     * Return localised event name.
     *
     * @return string
     */
    public static function get_name(): string {
        return get_string('eventarchiveitemexported', 'uckkarchive');
    }

    /**
     * Return event description.
     *
     * @return string
     */
    public function get_description(): string {
        $exportid = $this->other['exportid'] ?? 0;
        $exporttype = $this->other['exporttype'] ?? 'unknown';

        return "The user with id '{$this->userid}' exported the UCKK archive item with id " .
            "'{$this->objectid}' using export record id '{$exportid}' and export type '{$exporttype}'.";
    }

    /**
     * Return related URL.
     *
     * @return \moodle_url
     */
    public function get_url(): \moodle_url {
        $params = [
            'itemid' => $this->objectid,
        ];

        if (!empty($this->other['cmid'])) {
            $params['id'] = $this->other['cmid'];
        }

        if (!empty($this->other['exportid'])) {
            $params['exportid'] = $this->other['exportid'];
        }

        return new \moodle_url('/mod/uckkarchive/export.php', $params);
    }

    /**
     * Object id mapping used by backup and restore.
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
     * Other field mappings used by backup and restore.
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
            'exportid' => [
                'db' => 'uckkarchive_export',
                'restore' => 'uckkarchive_export',
            ],
        ];
    }

    /**
     * Validate event data.
     */
    protected function validate_data(): void {
        parent::validate_data();

        $allowedcontexts = [
            CONTEXT_MODULE,
            CONTEXT_COURSE,
            CONTEXT_USER,
            CONTEXT_SYSTEM,
        ];

        if (!in_array($this->contextlevel, $allowedcontexts, true)) {
            throw new \coding_exception(
                'The archive_item_exported event must use module, course, user, or system context.'
            );
        }

        if (empty($this->objectid)) {
            throw new \coding_exception('The archive_item_exported event requires objectid.');
        }

        if (empty($this->other['courseid'])) {
            throw new \coding_exception('The archive_item_exported event requires courseid in other.');
        }

        if (empty($this->other['exportid'])) {
            throw new \coding_exception('The archive_item_exported event requires exportid in other.');
        }

        if (empty($this->other['exporttype'])) {
            throw new \coding_exception('The archive_item_exported event requires exporttype in other.');
        }

        if ($this->contextlevel === CONTEXT_MODULE && empty($this->other['cmid'])) {
            throw new \coding_exception('The archive_item_exported event requires cmid in module context.');
        }
    }
}