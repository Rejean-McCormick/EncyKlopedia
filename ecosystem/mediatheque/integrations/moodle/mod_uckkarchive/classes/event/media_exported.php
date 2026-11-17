<?php
// This file is part of Moodle - https://moodle.org/
//
// Moodle is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// any later version.

/**
 * Event triggered when media is exported from UCKK Archive.
 *
 * @package    mod_uckkarchive
 * @copyright  2026 Univers-Cité King Klown
 * @license    https://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later
 */

declare(strict_types=1);

namespace mod_uckkarchive\event;

defined('MOODLE_INTERNAL') || die();

/**
 * Event triggered when a media object is exported.
 *
 * This event must stay privacy-safe. It records the export action and safe
 * identifiers only. It must not include raw media content, file contents,
 * private notes, full manifest JSON, cultural protocol notes, or redacted data.
 */
class media_exported extends \core\event\base {
    /**
     * Initialise event metadata.
     *
     * @return void
     */
    protected function init(): void {
        $this->data['crud'] = 'r';
        $this->data['edulevel'] = self::LEVEL_OTHER;
        $this->data['objecttable'] = 'uckkarchive_media';
    }

    /**
     * Return localized event name.
     *
     * @return string
     */
    public static function get_name(): string {
        return get_string('eventmediaexported', 'mod_uckkarchive');
    }

    /**
     * Return event description.
     *
     * @return string
     */
    public function get_description(): string {
        $mediaid = (int)$this->objectid;
        $userid = (int)$this->userid;
        $archiveid = (int)($this->other['archiveid'] ?? 0);
        $exportid = (int)($this->other['exportid'] ?? 0);
        $exportformat = (string)($this->other['exportformat'] ?? '');

        $description = "The user with id '{$userid}' exported the media with id '{$mediaid}'";

        if ($archiveid > 0) {
            $description .= " from the UCKK Archive activity with id '{$archiveid}'";
        }

        if ($exportid > 0) {
            $description .= " as part of export package '{$exportid}'";
        }

        if ($exportformat !== '') {
            $description .= " using export format '{$exportformat}'";
        }

        return $description . '.';
    }

    /**
     * Return URL related to the event.
     *
     * @return \moodle_url|null
     */
    public function get_url(): ?\moodle_url {
        $cmid = (int)($this->other['cmid'] ?? 0);
        $exportid = (int)($this->other['exportid'] ?? 0);

        if ($cmid > 0 && $exportid > 0) {
            return new \moodle_url('/mod/uckkarchive/export.php', [
                'id' => $cmid,
                'exportid' => $exportid,
            ]);
        }

        if ($cmid > 0) {
            return new \moodle_url('/mod/uckkarchive/media.php', [
                'id' => $cmid,
                'mediaid' => (int)$this->objectid,
            ]);
        }

        return null;
    }

    /**
     * Validate event data.
     *
     * @return void
     * @throws \coding_exception
     */
    protected function validate_data(): void {
        parent::validate_data();

        if (empty($this->objectid)) {
            throw new \coding_exception('The objectid must be set to the exported media id.');
        }

        if (empty($this->contextid)) {
            throw new \coding_exception('The context must be set for the media_exported event.');
        }

        if (empty($this->other['archiveid'])) {
            throw new \coding_exception('The archiveid must be set in other.');
        }

        if (!array_key_exists('cmid', $this->other)) {
            throw new \coding_exception('The cmid must be set in other.');
        }

        if (!array_key_exists('exportid', $this->other)) {
            throw new \coding_exception('The exportid must be set in other.');
        }

        if (!array_key_exists('exportformat', $this->other)) {
            throw new \coding_exception('The exportformat must be set in other.');
        }
    }

    /**
     * Return object id mapping for backup/restore.
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
     * Return other field mappings for backup/restore.
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
            'exportid' => [
                'db' => 'uckkarchive_export',
                'restore' => 'uckkarchive_export',
            ],
        ];
    }
}