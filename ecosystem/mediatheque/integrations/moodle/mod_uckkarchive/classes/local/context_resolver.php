<?php
// This file is part of Moodle - https://moodle.org/
//
// Moodle is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// any later version.

namespace mod_uckkarchive\local;

defined('MOODLE_INTERNAL') || die();

use context_module;
use stdClass;

/**
 * Central context resolver for mod_uckkarchive.
 *
 * This class is the single resolution point for:
 * - Moodle course;
 * - Moodle course module;
 * - module context;
 * - uckkarchive activity instance;
 * - archive item;
 * - media object;
 * - media collection;
 * - external work;
 * - content marker.
 *
 * Controllers and external services should call this class instead of
 * reconstructing Moodle context resolution independently.
 *
 * @package    mod_uckkarchive
 * @copyright  2026 Univers-Cité King Klown
 * @license    https://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later
 */
final class context_resolver {
    /** Moodle component name. */
    public const COMPONENT = 'mod_uckkarchive';

    /** Moodle module name. */
    public const MODNAME = 'uckkarchive';

    /**
     * Resolve from flexible input parameters.
     *
     * Supported keys:
     * - cmid
     * - archiveid
     * - courseid + archiveid
     * - itemid
     * - mediaid
     * - mediauuid
     * - collectionid
     * - externalworkid
     * - contentmarkerid
     *
     * @param array $params Resolution parameters.
     * @return stdClass Resolution object.
     */
    public static function resolve(array $params): stdClass {
        $params = array_change_key_case($params, CASE_LOWER);

        if (!empty($params['cmid'])) {
            return self::from_cmid((int)$params['cmid']);
        }

        if (!empty($params['courseid']) && !empty($params['archiveid'])) {
            return self::from_course_and_archive((int)$params['courseid'], (int)$params['archiveid']);
        }

        if (!empty($params['archiveid'])) {
            return self::from_archive((int)$params['archiveid']);
        }

        if (!empty($params['itemid'])) {
            return self::from_item((int)$params['itemid']);
        }

        if (!empty($params['mediaid'])) {
            return self::from_media((int)$params['mediaid']);
        }

        if (!empty($params['mediauuid'])) {
            return self::from_media_uuid((string)$params['mediauuid']);
        }

        if (!empty($params['collectionid'])) {
            return self::from_media_collection((int)$params['collectionid']);
        }

        if (!empty($params['externalworkid'])) {
            return self::from_external_work((int)$params['externalworkid']);
        }

        if (!empty($params['contentmarkerid'])) {
            return self::from_content_marker((int)$params['contentmarkerid']);
        }

        throw new \coding_exception('Unable to resolve mod_uckkarchive context: no supported identifier was provided.');
    }

    /**
     * Resolve from Moodle course module id.
     *
     * @param int $cmid Course module id.
     * @return stdClass Resolution object.
     */
    public static function from_cmid(int $cmid): stdClass {
        global $DB;

        self::require_positive_id($cmid, 'cmid');

        $cm = get_coursemodule_from_id(self::MODNAME, $cmid, 0, false, MUST_EXIST);
        $course = $DB->get_record('course', ['id' => $cm->course], '*', MUST_EXIST);
        $archive = $DB->get_record(self::MODNAME, ['id' => $cm->instance], '*', MUST_EXIST);
        $context = context_module::instance($cm->id, MUST_EXIST);

        return self::build_resolution($course, $cm, $archive, $context);
    }

    /**
     * Resolve from activity instance id.
     *
     * @param int $archiveid uckkarchive instance id.
     * @return stdClass Resolution object.
     */
    public static function from_archive(int $archiveid): stdClass {
        global $DB;

        self::require_positive_id($archiveid, 'archiveid');

        $archive = $DB->get_record(self::MODNAME, ['id' => $archiveid], '*', MUST_EXIST);
        $courseid = self::get_record_int($archive, ['course', 'courseid'], 0);

        if ($courseid <= 0) {
            throw new \coding_exception('Unable to resolve mod_uckkarchive context: archive record has no course reference.');
        }

        return self::from_course_and_archive($courseid, $archiveid);
    }

    /**
     * Resolve from course id and activity instance id.
     *
     * @param int $courseid Course id.
     * @param int $archiveid uckkarchive instance id.
     * @return stdClass Resolution object.
     */
    public static function from_course_and_archive(int $courseid, int $archiveid): stdClass {
        global $DB;

        self::require_positive_id($courseid, 'courseid');
        self::require_positive_id($archiveid, 'archiveid');

        $course = $DB->get_record('course', ['id' => $courseid], '*', MUST_EXIST);
        $archive = $DB->get_record(self::MODNAME, ['id' => $archiveid], '*', MUST_EXIST);
        $cm = get_coursemodule_from_instance(self::MODNAME, $archiveid, $courseid, false, MUST_EXIST);
        $context = context_module::instance($cm->id, MUST_EXIST);

        return self::build_resolution($course, $cm, $archive, $context);
    }

    /**
     * Resolve from archive item id.
     *
     * @param int $itemid Archive item id.
     * @return stdClass Resolution object with ->item.
     */
    public static function from_item(int $itemid): stdClass {
        self::require_positive_id($itemid, 'itemid');

        $item = self::get_required_record('uckkarchive_item', ['id' => $itemid]);
        $resolution = self::from_domain_record($item, 'archive item');
        $resolution->item = $item;
        $resolution->itemid = $itemid;

        return $resolution;
    }

    /**
     * Resolve from media id.
     *
     * @param int $mediaid Media id.
     * @return stdClass Resolution object with ->media.
     */
    public static function from_media(int $mediaid): stdClass {
        self::require_positive_id($mediaid, 'mediaid');

        $media = self::get_required_record('uckkarchive_media', ['id' => $mediaid]);
        $resolution = self::from_domain_record($media, 'media');
        $resolution->media = $media;
        $resolution->mediaid = $mediaid;

        return $resolution;
    }

    /**
     * Resolve from media UUID.
     *
     * @param string $uuid Media UUID.
     * @return stdClass Resolution object with ->media.
     */
    public static function from_media_uuid(string $uuid): stdClass {
        global $DB;

        $uuid = trim($uuid);
        if ($uuid === '') {
            throw new \coding_exception('Unable to resolve mod_uckkarchive context: empty media UUID.');
        }

        if (!self::table_exists('uckkarchive_media') || !self::field_exists('uckkarchive_media', 'uuid')) {
            throw new \coding_exception('Unable to resolve mod_uckkarchive context: media UUID resolution is not available.');
        }

        $media = $DB->get_record('uckkarchive_media', ['uuid' => $uuid], '*', MUST_EXIST);
        $resolution = self::from_domain_record($media, 'media');
        $resolution->media = $media;
        $resolution->mediaid = (int)$media->id;

        return $resolution;
    }

    /**
     * Resolve from media collection id.
     *
     * @param int $collectionid Media collection id.
     * @return stdClass Resolution object with ->collection.
     */
    public static function from_media_collection(int $collectionid): stdClass {
        self::require_positive_id($collectionid, 'collectionid');

        $collection = self::get_required_record('uckkarchive_media_collection', ['id' => $collectionid]);
        $resolution = self::from_domain_record($collection, 'media collection');
        $resolution->collection = $collection;
        $resolution->collectionid = $collectionid;

        return $resolution;
    }

    /**
     * Resolve from external work id.
     *
     * @param int $externalworkid External work id.
     * @return stdClass Resolution object with ->externalwork.
     */
    public static function from_external_work(int $externalworkid): stdClass {
        self::require_positive_id($externalworkid, 'externalworkid');

        $externalwork = self::get_required_record('uckkarchive_external_work', ['id' => $externalworkid]);
        $resolution = self::from_domain_record($externalwork, 'external work');
        $resolution->externalwork = $externalwork;
        $resolution->externalworkid = $externalworkid;

        return $resolution;
    }

    /**
     * Resolve from content marker id.
     *
     * @param int $contentmarkerid Content marker id.
     * @return stdClass Resolution object with ->contentmarker.
     */
    public static function from_content_marker(int $contentmarkerid): stdClass {
        self::require_positive_id($contentmarkerid, 'contentmarkerid');

        $marker = self::get_required_record('uckkarchive_content_marker', ['id' => $contentmarkerid]);
        $resolution = self::from_domain_record($marker, 'content marker');
        $resolution->contentmarker = $marker;
        $resolution->contentmarkerid = $contentmarkerid;

        return $resolution;
    }

    /**
     * Require Moodle login for a resolved context.
     *
     * @param stdClass $resolution Resolution object.
     * @return void
     */
    public static function require_login_for(stdClass $resolution): void {
        self::validate_resolution($resolution);
        require_login($resolution->course, false, $resolution->cm);
    }

    /**
     * Require a capability on a resolved module context.
     *
     * @param string $capability Moodle capability.
     * @param stdClass $resolution Resolution object.
     * @return void
     */
    public static function require_capability_for(string $capability, stdClass $resolution): void {
        self::validate_resolution($resolution);
        require_capability($capability, $resolution->context);
    }

    /**
     * Check a capability on a resolved module context.
     *
     * @param string $capability Moodle capability.
     * @param stdClass $resolution Resolution object.
     * @param int|null $userid User id, or null for current user.
     * @param bool $doanything Whether doanything is respected.
     * @return bool
     */
    public static function has_capability_in(string $capability, stdClass $resolution, ?int $userid = null,
            bool $doanything = true): bool {
        self::validate_resolution($resolution);
        return has_capability($capability, $resolution->context, $userid, $doanything);
    }

    /**
     * Build a canonical resolution object.
     *
     * @param stdClass $course Course record.
     * @param stdClass $cm Course module record.
     * @param stdClass $archive Activity instance record.
     * @param context_module $context Module context.
     * @return stdClass
     */
    private static function build_resolution(stdClass $course, stdClass $cm, stdClass $archive,
            context_module $context): stdClass {
        if (($cm->modname ?? '') !== self::MODNAME) {
            throw new \coding_exception('Unable to resolve mod_uckkarchive context: course module has invalid module type.');
        }

        if ((int)$cm->instance !== (int)$archive->id) {
            throw new \coding_exception('Unable to resolve mod_uckkarchive context: course module and archive instance mismatch.');
        }

        if ((int)$cm->course !== (int)$course->id) {
            throw new \coding_exception('Unable to resolve mod_uckkarchive context: course module and course mismatch.');
        }

        $resolution = new stdClass();
        $resolution->component = self::COMPONENT;
        $resolution->modname = self::MODNAME;

        $resolution->course = $course;
        $resolution->cm = $cm;
        $resolution->archive = $archive;
        $resolution->context = $context;

        $resolution->courseid = (int)$course->id;
        $resolution->cmid = (int)$cm->id;
        $resolution->archiveid = (int)$archive->id;
        $resolution->contextid = (int)$context->id;

        return $resolution;
    }

    /**
     * Resolve from a domain record that points back to the archive instance.
     *
     * @param stdClass $record Domain record.
     * @param string $recordname Human-readable record name.
     * @return stdClass
     */
    private static function from_domain_record(stdClass $record, string $recordname): stdClass {
        $cmid = self::get_record_int($record, ['cmid', 'coursemoduleid'], 0);
        if ($cmid > 0) {
            return self::from_cmid($cmid);
        }

        $archiveid = self::get_record_int($record, [
            'archiveid',
            'uckkarchiveid',
            'uckkarchive',
            'instanceid',
        ], 0);

        if ($archiveid > 0) {
            $courseid = self::get_record_int($record, ['courseid', 'course'], 0);
            if ($courseid > 0) {
                return self::from_course_and_archive($courseid, $archiveid);
            }
            return self::from_archive($archiveid);
        }

        $contextid = self::get_record_int($record, ['contextid'], 0);
        if ($contextid > 0) {
            return self::from_contextid($contextid);
        }

        throw new \coding_exception(
            'Unable to resolve mod_uckkarchive context: ' . $recordname . ' record has no archive, cm, or context reference.'
        );
    }

    /**
     * Resolve from a module context id.
     *
     * @param int $contextid Context id.
     * @return stdClass
     */
    private static function from_contextid(int $contextid): stdClass {
        self::require_positive_id($contextid, 'contextid');

        $context = \context::instance_by_id($contextid, MUST_EXIST);
        if (!$context instanceof context_module) {
            throw new \coding_exception('Unable to resolve mod_uckkarchive context: context is not a module context.');
        }

        return self::from_cmid((int)$context->instanceid);
    }

    /**
     * Validate a resolution object shape.
     *
     * @param stdClass $resolution Resolution object.
     * @return void
     */
    private static function validate_resolution(stdClass $resolution): void {
        foreach (['course', 'cm', 'archive', 'context', 'courseid', 'cmid', 'archiveid', 'contextid'] as $property) {
            if (!property_exists($resolution, $property)) {
                throw new \coding_exception('Invalid mod_uckkarchive resolution object: missing ' . $property . '.');
            }
        }

        if (!$resolution->context instanceof context_module) {
            throw new \coding_exception('Invalid mod_uckkarchive resolution object: context is not context_module.');
        }
    }

    /**
     * Get a required record, with a clear message when a target table does not exist.
     *
     * @param string $table Table name without prefix.
     * @param array $conditions Conditions.
     * @return stdClass
     */
    private static function get_required_record(string $table, array $conditions): stdClass {
        global $DB;

        if (!self::table_exists($table)) {
            throw new \coding_exception('Unable to resolve mod_uckkarchive context: table ' . $table . ' does not exist.');
        }

        return $DB->get_record($table, $conditions, '*', MUST_EXIST);
    }

    /**
     * Return the first integer value found on a record for a list of possible field names.
     *
     * @param stdClass $record Record.
     * @param array $fields Candidate fields.
     * @param int $default Default value.
     * @return int
     */
    private static function get_record_int(stdClass $record, array $fields, int $default = 0): int {
        foreach ($fields as $field) {
            if (property_exists($record, $field) && $record->{$field} !== null && $record->{$field} !== '') {
                return (int)$record->{$field};
            }
        }

        return $default;
    }

    /**
     * Verify an identifier is a positive integer.
     *
     * @param int $id Identifier.
     * @param string $name Identifier name.
     * @return void
     */
    private static function require_positive_id(int $id, string $name): void {
        if ($id <= 0) {
            throw new \coding_exception('Invalid mod_uckkarchive ' . $name . ': expected a positive integer.');
        }
    }

    /**
     * Check whether a table exists.
     *
     * @param string $table Table name without prefix.
     * @return bool
     */
    private static function table_exists(string $table): bool {
        global $DB;

        return $DB->get_manager()->table_exists($table);
    }

    /**
     * Check whether a field exists.
     *
     * @param string $table Table name without prefix.
     * @param string $field Field name.
     * @return bool
     */
    private static function field_exists(string $table, string $field): bool {
        global $DB;

        if (!self::table_exists($table)) {
            return false;
        }

        return array_key_exists($field, $DB->get_columns($table));
    }
}
