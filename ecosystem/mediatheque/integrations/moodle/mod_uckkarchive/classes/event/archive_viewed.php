<?php
// This file is part of Moodle - https://moodle.org/
//
// Moodle is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// any later version.

/**
 * Archive viewed event.
 *
 * @package    mod_uckkarchive
 * @copyright  2026 Univers-Cité King Klown
 * @license    https://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later
 */

declare(strict_types=1);

namespace mod_uckkarchive\event;

defined('MOODLE_INTERNAL') || die();

/**
 * Event fired when a UCKK archive activity is viewed.
 */
final class archive_viewed extends \core\event\base {
    /**
     * Initialise event metadata.
     */
    protected function init(): void {
        $this->data['objecttable'] = 'uckkarchive';
        $this->data['crud'] = 'r';
        $this->data['edulevel'] = self::LEVEL_PARTICIPATING;
    }

    /**
     * Return event name.
     *
     * @return string
     */
    public static function get_name(): string {
        $manager = get_string_manager();

        if ($manager->string_exists('event:archiveviewed', 'uckkarchive')) {
            return get_string('event:archiveviewed', 'uckkarchive');
        }

        if ($manager->string_exists('eventarchiveviewed', 'uckkarchive')) {
            return get_string('eventarchiveviewed', 'uckkarchive');
        }

        return 'Archive viewed';
    }

    /**
     * Return event description.
     *
     * @return string
     */
    public function get_description(): string {
        return "The user with id '{$this->userid}' viewed the UCKK archive with id " .
            "'{$this->objectid}' in course module id '{$this->contextinstanceid}'.";
    }

    /**
     * Return event URL.
     *
     * @return \moodle_url
     */
    public function get_url(): \moodle_url {
        return new \moodle_url('/mod/uckkarchive/view.php', [
            'id' => (int)($this->other['cmid'] ?? $this->contextinstanceid),
        ]);
    }

    /**
     * Return object id mapping.
     *
     * @return array<string, string>
     */
    public static function get_objectid_mapping(): array {
        return [
            'db' => 'uckkarchive',
            'restore' => 'uckkarchive',
        ];
    }

    /**
     * Return other mapping.
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
        ];
    }

    /**
     * Validate event payload.
     */
    protected function validate_data(): void {
        parent::validate_data();

        if ($this->contextlevel !== CONTEXT_MODULE) {
            throw new \coding_exception('The archive_viewed event must use module context.');
        }

        if (empty($this->objectid)) {
            throw new \coding_exception('The archive_viewed event requires objectid.');
        }

        if (empty($this->other['courseid'])) {
            throw new \coding_exception('The archive_viewed event requires courseid in other.');
        }

        if (empty($this->other['cmid'])) {
            throw new \coding_exception('The archive_viewed event requires cmid in other.');
        }
    }
}