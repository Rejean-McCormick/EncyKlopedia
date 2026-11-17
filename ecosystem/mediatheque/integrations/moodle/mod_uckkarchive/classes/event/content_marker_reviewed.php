<?php
// This file is part of Moodle - https://moodle.org/
//
// Moodle is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// any later version.

/**
 * Event fired when a content marker receives human review.
 *
 * @package    mod_uckkarchive
 * @copyright  2026 Univers-Cité King Klown
 * @license    https://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later
 */

declare(strict_types=1);

namespace mod_uckkarchive\event;

use moodle_url;

defined('MOODLE_INTERNAL') || die();

/**
 * Event fired when a content marker advisory review is recorded.
 *
 * This event audits that a content advisory marker was reviewed, approved,
 * contested, retired, or otherwise reviewed by an authorised human actor.
 *
 * It must not carry private review notes, cultural protocol notes, raw media
 * content, restricted advisory text, or unredacted personal data.
 *
 * Expected creation:
 *
 * ```php
 * $event = \mod_uckkarchive\event\content_marker_reviewed::create([
 *     'objectid' => $review->id,
 *     'context' => $context,
 *     'relateduserid' => $reviewerid,
 *     'other' => [
 *         'archiveid' => $archive->id,
 *         'courseid' => $course->id,
 *         'cmid' => $cm->id,
 *         'markerid' => $marker->id,
 *         'markeruuid' => $marker->uuid,
 *         'reviewuuid' => $review->uuid,
 *         'reviewstate' => $review->state,
 *         'previousreviewstate' => $previousstate,
 *         'tagkey' => $tagkey,
 *         'severity' => $severity,
 *         'audiencesuitability' => $audiencesuitability,
 *         'visibility' => $visibility,
 *         'action' => 'reviewed',
 *     ],
 * ]);
 * $event->add_record_snapshot('course', $course);
 * $event->add_record_snapshot('course_modules', $cm);
 * $event->add_record_snapshot('uckkarchive', $archive);
 * $event->add_record_snapshot('uckkarchive_content_marker', $marker);
 * $event->add_record_snapshot('uckkarchive_content_review', $review);
 * $event->trigger();
 * ```
 */
final class content_marker_reviewed extends \core\event\base {
    /**
     * Initialise event data.
     */
    protected function init(): void {
        $this->data['crud'] = 'u';
        $this->data['edulevel'] = self::LEVEL_TEACHING;
        $this->data['objecttable'] = 'uckkarchive_content_review';
    }

    /**
     * Return localised event name.
     *
     * @return string
     */
    public static function get_name(): string {
        $manager = get_string_manager();

        if ($manager->string_exists('eventcontentmarkerreviewed', 'uckkarchive')) {
            return get_string('eventcontentmarkerreviewed', 'uckkarchive');
        }

        if ($manager->string_exists('event:contentmarkerreviewed', 'uckkarchive')) {
            return get_string('event:contentmarkerreviewed', 'uckkarchive');
        }

        return 'Content marker reviewed';
    }

    /**
     * Return event description.
     *
     * @return string
     */
    public function get_description(): string {
        $archiveid = $this->other['archiveid'] ?? 0;
        $cmid = $this->other['cmid'] ?? $this->contextinstanceid;
        $markerid = $this->other['markerid'] ?? 0;
        $reviewstate = $this->other['reviewstate'] ?? 'unknown';
        $previousstate = $this->other['previousreviewstate'] ?? '';
        $action = $this->other['action'] ?? 'reviewed';

        $description = "The user with id '{$this->userid}' {$action} content marker with id " .
            "'{$markerid}' using content review record id '{$this->objectid}' in archive id " .
            "'{$archiveid}' and course module id '{$cmid}'. The review state is '{$reviewstate}'";

        if ($previousstate !== '') {
            $description .= " and the previous review state was '{$previousstate}'";
        }

        return $description . '.';
    }

    /**
     * Return related URL.
     *
     * @return moodle_url
     */
    public function get_url(): moodle_url {
        $cmid = $this->other['cmid'] ?? $this->contextinstanceid;
        $markerid = $this->other['markerid'] ?? 0;

        if (!empty($cmid) && !empty($markerid)) {
            return new moodle_url('/mod/uckkarchive/media.php', [
                'id' => $cmid,
                'contentmarkerid' => $markerid,
            ]);
        }

        if (!empty($cmid)) {
            return new moodle_url('/mod/uckkarchive/media.php', [
                'id' => $cmid,
            ]);
        }

        return new moodle_url('/mod/uckkarchive/index.php');
    }

    /**
     * Return object id mapping for backup/restore.
     *
     * @return array
     */
    public static function get_objectid_mapping(): array {
        return [
            'db' => 'uckkarchive_content_review',
            'restore' => 'uckkarchive_content_review',
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
            'markerid' => [
                'db' => 'uckkarchive_content_marker',
                'restore' => 'uckkarchive_content_marker',
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
            throw new \coding_exception('The content_marker_reviewed event must use module context.');
        }

        if (empty($this->objectid)) {
            throw new \coding_exception('The content_marker_reviewed event requires objectid.');
        }

        if (empty($this->other['archiveid'])) {
            throw new \coding_exception('The content_marker_reviewed event requires archiveid in other.');
        }

        if (empty($this->other['courseid'])) {
            throw new \coding_exception('The content_marker_reviewed event requires courseid in other.');
        }

        if (empty($this->other['cmid'])) {
            throw new \coding_exception('The content_marker_reviewed event requires cmid in other.');
        }

        if (empty($this->other['markerid'])) {
            throw new \coding_exception('The content_marker_reviewed event requires markerid in other.');
        }

        if (!array_key_exists('reviewstate', $this->other)) {
            throw new \coding_exception('The content_marker_reviewed event requires reviewstate in other.');
        }

        if (!array_key_exists('action', $this->other)) {
            throw new \coding_exception('The content_marker_reviewed event requires action in other.');
        }

        if (!$this->is_safe_key((string)$this->other['reviewstate'])) {
            throw new \coding_exception('The content_marker_reviewed event reviewstate must be a safe key.');
        }

        if (!$this->is_safe_key((string)$this->other['action'])) {
            throw new \coding_exception('The content_marker_reviewed event action must be a safe key.');
        }

        foreach (['tagkey', 'severity', 'audiencesuitability', 'visibility', 'previousreviewstate'] as $key) {
            if (array_key_exists($key, $this->other) && !$this->is_safe_optional_key((string)$this->other[$key])) {
                throw new \coding_exception("The content_marker_reviewed event {$key} must be a safe key.");
            }
        }
    }

    /**
     * Return whether value is a required safe machine key.
     *
     * @param string $value Value.
     * @return bool
     */
    private function is_safe_key(string $value): bool {
        return $value !== '' && preg_match('/^[a-z0-9_:-]+$/', $value) === 1;
    }

    /**
     * Return whether value is an optional safe machine key.
     *
     * @param string $value Value.
     * @return bool
     */
    private function is_safe_optional_key(string $value): bool {
        return $value === '' || preg_match('/^[a-z0-9_:-]+$/', $value) === 1;
    }
}