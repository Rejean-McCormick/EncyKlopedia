<?php
// This file is part of Moodle - https://moodle.org/
//
// Moodle is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// any later version.

/**
 * Event fired when a content advisory marker is created.
 *
 * @package    mod_uckkarchive
 * @copyright  2026 Univers-Cité King Klown
 * @license    https://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later
 */

declare(strict_types=1);

namespace mod_uckkarchive\event;

defined('MOODLE_INTERNAL') || die();

/**
 * Event fired when a content advisory marker is created.
 *
 * Content markers are audit-relevant because they may identify warnings,
 * cultural protocol restrictions, audience suitability, or responsible access
 * conditions for media, archive items, or external works.
 *
 * This event must not expose restricted content, private cultural protocol
 * notes, trauma descriptions, confidential review notes, or redacted metadata.
 *
 * Expected creation:
 *
 * $event = \mod_uckkarchive\event\content_marker_created::create([
 *     'objectid' => $marker->id,
 *     'context' => $context,
 *     'relateduserid' => $USER->id,
 *     'other' => [
 *         'archiveid' => $archive->id,
 *         'courseid' => $course->id,
 *         'cmid' => $cm->id,
 *         'markeruuid' => $marker->uuid,
 *         'mediaid' => $marker->mediaid ?? 0,
 *         'itemid' => $marker->itemid ?? 0,
 *         'externalworkid' => $marker->externalworkid ?? 0,
 *         'tagid' => $marker->tagid ?? 0,
 *         'tagkey' => $marker->tagkey,
 *         'locator_type' => $marker->locatortype,
 *         'reviewstate' => $marker->reviewstate,
 *         'visibility' => $marker->visibility,
 *         'audiencesuitability' => $marker->audiencesuitability,
 *         'restricted' => !empty($marker->restricted),
 *         'restrictedtype' => $marker->restrictedtype ?? '',
 *     ],
 * ]);
 * $event->add_record_snapshot('course', $course);
 * $event->add_record_snapshot('course_modules', $cm);
 * $event->add_record_snapshot('uckkarchive', $archive);
 * $event->add_record_snapshot('uckkarchive_content_marker', $marker);
 * $event->trigger();
 */
final class content_marker_created extends \core\event\base {
    /**
     * Initialise event data.
     */
    protected function init(): void {
        $this->data['crud'] = 'c';
        $this->data['edulevel'] = self::LEVEL_OTHER;
        $this->data['objecttable'] = 'uckkarchive_content_marker';
    }

    /**
     * Return localised event name.
     *
     * @return string
     */
    public static function get_name(): string {
        $manager = get_string_manager();

        if ($manager->string_exists('eventcontentmarkercreated', 'uckkarchive')) {
            return get_string('eventcontentmarkercreated', 'uckkarchive');
        }

        if ($manager->string_exists('event:contentmarkercreated', 'uckkarchive')) {
            return get_string('event:contentmarkercreated', 'uckkarchive');
        }

        return 'Content marker created';
    }

    /**
     * Return event description.
     *
     * @return string
     */
    public function get_description(): string {
        $archiveid = $this->other['archiveid'] ?? 0;
        $cmid = $this->other['cmid'] ?? $this->contextinstanceid;
        $tagkey = $this->other['tagkey'] ?? '';
        $locatortype = $this->other['locator_type'] ?? '';
        $visibility = $this->other['visibility'] ?? '';
        $reviewstate = $this->other['reviewstate'] ?? '';

        return "The user with id '{$this->userid}' created the content advisory marker with id " .
            "'{$this->objectid}' in archive instance id '{$archiveid}' and course module id " .
            "'{$cmid}'. The safe advisory tag key is '{$tagkey}', locator type is " .
            "'{$locatortype}', visibility is '{$visibility}', and review state is " .
            "'{$reviewstate}'.";
    }

    /**
     * Return related URL.
     *
     * @return \moodle_url
     */
    public function get_url(): \moodle_url {
        $cmid = (int)($this->other['cmid'] ?? $this->contextinstanceid);

        if (!empty($this->other['mediaid'])) {
            return new \moodle_url('/mod/uckkarchive/media.php', [
                'id' => $cmid,
                'mediaid' => (int)$this->other['mediaid'],
                'markerid' => $this->objectid,
            ]);
        }

        if (!empty($this->other['itemid'])) {
            return new \moodle_url('/mod/uckkarchive/item.php', [
                'id' => $cmid,
                'itemid' => (int)$this->other['itemid'],
                'markerid' => $this->objectid,
            ]);
        }

        if (!empty($this->other['externalworkid'])) {
            return new \moodle_url('/mod/uckkarchive/media.php', [
                'id' => $cmid,
                'externalworkid' => (int)$this->other['externalworkid'],
                'markerid' => $this->objectid,
            ]);
        }

        return new \moodle_url('/mod/uckkarchive/media.php', [
            'id' => $cmid,
            'markerid' => $this->objectid,
        ]);
    }

    /**
     * Return object id mapping for backup and restore.
     *
     * @return array
     */
    public static function get_objectid_mapping(): array {
        return [
            'db' => 'uckkarchive_content_marker',
            'restore' => 'uckkarchive_content_marker',
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
            'mediaid' => [
                'db' => 'uckkarchive_media',
                'restore' => 'uckkarchive_media',
            ],
            'itemid' => [
                'db' => 'uckkarchive_item',
                'restore' => 'uckkarchive_item',
            ],
            'externalworkid' => [
                'db' => 'uckkarchive_external_work',
                'restore' => 'uckkarchive_external_work',
            ],
            'tagid' => [
                'db' => 'uckkarchive_content_tag',
                'restore' => 'uckkarchive_content_tag',
            ],
            'tagsetid' => [
                'db' => 'uckkarchive_content_tag_set',
                'restore' => 'uckkarchive_content_tag_set',
            ],
            'createdby' => [
                'db' => 'user',
                'restore' => 'user',
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
            throw new \coding_exception('The content_marker_created event must use module context.');
        }

        if (empty($this->objectid)) {
            throw new \coding_exception('The content_marker_created event requires objectid.');
        }

        if (empty($this->other['archiveid'])) {
            throw new \coding_exception('The content_marker_created event requires archiveid in other.');
        }

        if (empty($this->other['courseid'])) {
            throw new \coding_exception('The content_marker_created event requires courseid in other.');
        }

        if (empty($this->other['cmid'])) {
            throw new \coding_exception('The content_marker_created event requires cmid in other.');
        }

        if (!array_key_exists('markeruuid', $this->other)) {
            throw new \coding_exception('The content_marker_created event requires markeruuid in other.');
        }

        if (!array_key_exists('tagkey', $this->other)) {
            throw new \coding_exception('The content_marker_created event requires tagkey in other.');
        }

        if (!array_key_exists('locator_type', $this->other)) {
            throw new \coding_exception('The content_marker_created event requires locator_type in other.');
        }

        if (!array_key_exists('reviewstate', $this->other)) {
            throw new \coding_exception('The content_marker_created event requires reviewstate in other.');
        }

        if (!array_key_exists('visibility', $this->other)) {
            throw new \coding_exception('The content_marker_created event requires visibility in other.');
        }

        if (!array_key_exists('audiencesuitability', $this->other)) {
            throw new \coding_exception('The content_marker_created event requires audiencesuitability in other.');
        }

        if (empty($this->other['mediaid']) &&
                empty($this->other['itemid']) &&
                empty($this->other['externalworkid']) &&
                empty($this->other['manualreference'])) {
            throw new \coding_exception(
                'The content_marker_created event requires mediaid, itemid, externalworkid, or manualreference in other.'
            );
        }

        foreach (['note', 'reviewnote', 'culturalprotocolnote', 'privatecomment', 'rawcontent'] as $unsafe) {
            if (array_key_exists($unsafe, $this->other)) {
                throw new \coding_exception(
                    'The content_marker_created event must not include unsafe restricted detail in other: ' . $unsafe
                );
            }
        }
    }
}