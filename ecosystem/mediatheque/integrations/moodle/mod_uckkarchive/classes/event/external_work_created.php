<?php
// This file is part of Moodle - https://moodle.org/
//
// Moodle is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// any later version.

/**
 * Event fired when an external work reference is created.
 *
 * @package    mod_uckkarchive
 * @copyright  2026 Univers-Cité King Klown
 * @license    https://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later
 */

declare(strict_types=1);

namespace mod_uckkarchive\event;

defined('MOODLE_INTERNAL') || die();

/**
 * Event fired when an external work reference is created.
 *
 * External works represent non-UCKK material referenced by the archive/media
 * library, such as films, books, articles, podcasts, websites, external videos,
 * external images, public archive records, or third-party PDFs.
 *
 * This event records that an external work reference was created. It does not
 * grant rights, validate ownership, approve cultural protocol access, approve
 * content advisories, copy third-party works, or expose restricted notes.
 *
 * Expected creation:
 *
 * $event = \mod_uckkarchive\event\external_work_created::create([
 *     'objectid' => $externalwork->id,
 *     'context' => $context,
 *     'other' => [
 *         'archiveid' => $archive->id,
 *         'courseid' => $course->id,
 *         'cmid' => $cm->id,
 *         'uuid' => $externalwork->uuid,
 *         'worktype' => $externalwork->worktype,
 *         'status' => $externalwork->status,
 *         'visibility' => $externalwork->visibility,
 *         'rightsstatus' => $externalwork->rightsstatus,
 *         'audiencesuitability' => $externalwork->audiencesuitability,
 *     ],
 * ]);
 * $event->add_record_snapshot('course', $course);
 * $event->add_record_snapshot('course_modules', $cm);
 * $event->add_record_snapshot('uckkarchive', $archive);
 * $event->add_record_snapshot('uckkarchive_external_work', $externalwork);
 * $event->trigger();
 */
final class external_work_created extends \core\event\base {
    /**
     * Initialise event metadata.
     */
    protected function init(): void {
        $this->data['crud'] = 'c';
        $this->data['edulevel'] = self::LEVEL_OTHER;
        $this->data['objecttable'] = 'uckkarchive_external_work';
    }

    /**
     * Return localised event name.
     *
     * @return string
     */
    public static function get_name(): string {
        $manager = get_string_manager();

        if ($manager->string_exists('eventexternalworkcreated', 'uckkarchive')) {
            return get_string('eventexternalworkcreated', 'uckkarchive');
        }

        if ($manager->string_exists('event:externalworkcreated', 'uckkarchive')) {
            return get_string('event:externalworkcreated', 'uckkarchive');
        }

        return 'External work reference created';
    }

    /**
     * Return event description.
     *
     * @return string
     */
    public function get_description(): string {
        $archiveid = $this->other['archiveid'] ?? 0;
        $cmid = $this->other['cmid'] ?? 0;
        $worktype = $this->other['worktype'] ?? 'unknown';
        $status = $this->other['status'] ?? 'unknown';
        $visibility = $this->other['visibility'] ?? 'unknown';
        $rightsstatus = $this->other['rightsstatus'] ?? 'unknown';

        return "The user with id '{$this->userid}' created the external work reference with id " .
            "'{$this->objectid}' in UCKK archive id '{$archiveid}', course module id '{$cmid}', " .
            "work type '{$worktype}', status '{$status}', visibility '{$visibility}', and rights status " .
            "'{$rightsstatus}'.";
    }

    /**
     * Return related URL.
     *
     * @return \moodle_url
     */
    public function get_url(): \moodle_url {
        $params = [
            'externalworkid' => $this->objectid,
        ];

        if (!empty($this->other['cmid'])) {
            $params['id'] = $this->other['cmid'];
        }

        return new \moodle_url('/mod/uckkarchive/media.php', $params);
    }

    /**
     * Object id mapping used by backup and restore.
     *
     * @return array
     */
    public static function get_objectid_mapping(): array {
        return [
            'db' => 'uckkarchive_external_work',
            'restore' => 'uckkarchive_external_work',
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
     * @return void
     */
    protected function validate_data(): void {
        parent::validate_data();

        if ($this->contextlevel !== CONTEXT_MODULE) {
            throw new \coding_exception('The external_work_created event must use module context.');
        }

        if (empty($this->objectid)) {
            throw new \coding_exception('The external_work_created event requires objectid.');
        }

        if (empty($this->other['archiveid'])) {
            throw new \coding_exception('The external_work_created event requires archiveid in other.');
        }

        if (empty($this->other['courseid'])) {
            throw new \coding_exception('The external_work_created event requires courseid in other.');
        }

        if (empty($this->other['cmid'])) {
            throw new \coding_exception('The external_work_created event requires cmid in other.');
        }

        if (!array_key_exists('worktype', $this->other)) {
            throw new \coding_exception('The external_work_created event requires worktype in other.');
        }

        if (!array_key_exists('status', $this->other)) {
            throw new \coding_exception('The external_work_created event requires status in other.');
        }

        if (!array_key_exists('visibility', $this->other)) {
            throw new \coding_exception('The external_work_created event requires visibility in other.');
        }

        if (!array_key_exists('rightsstatus', $this->other)) {
            throw new \coding_exception('The external_work_created event requires rightsstatus in other.');
        }
    }
}