<?php
// This file is part of Moodle - https://moodle.org/.
//
// Moodle is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// any later version.
//
// Moodle is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with Moodle. If not, see <https://www.gnu.org/licenses/>.

/**
 * External service for updating a content advisory marker.
 *
 * @package    mod_uckkarchive
 * @copyright  2026 UCKK
 * @license    https://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later
 */

declare(strict_types=1);

namespace mod_uckkarchive\external;

defined('MOODLE_INTERNAL') || die();

global $CFG;
require_once($CFG->libdir . '/externallib.php');

use context;
use context_module;
use core_external\external_api;
use core_external\external_function_parameters;
use core_external\external_multiple_structure;
use core_external\external_single_structure;
use core_external\external_value;
use invalid_parameter_exception;
use mod_uckkarchive\local\content_marker;
use mod_uckkarchive\local\content_policy;
use stdClass;

/**
 * Update an existing content marker.
 *
 * Content markers are advisory/cultural protocol locators. Updating them is a
 * server-side authority operation: the service resolves context, checks Moodle
 * capabilities, applies content policy, normalises marker input through the
 * local domain class, and returns a redaction-aware payload.
 */
final class update_content_marker extends external_api {
    /**
     * Marker table.
     */
    private const TABLE = 'uckkarchive_content_marker';

    /**
     * Text fields accepted by this service.
     */
    private const TEXT_FIELDS = [
        'targetuuid',
        'tagkey',
        'locatorvalue',
        'locatorstart',
        'locatorend',
        'note',
        'teachingcontext',
        'culturalprotocolnote',
        'reviewrationale',
    ];

    /**
     * Integer fields accepted by this service.
     */
    private const INT_FIELDS = [
        'targetid',
        'tagid',
        'tagsetid',
        'locatorsort',
    ];

    /**
     * Enum fields accepted by this service.
     */
    private const ENUM_FIELDS = [
        'targettype',
        'locatortype',
        'severity',
        'visibility',
        'audiencesuitability',
        'reviewstate',
    ];

    /**
     * Return service parameters.
     *
     * Empty scalar values mean "do not change", unless the field name appears
     * in `clearfields`.
     *
     * @return external_function_parameters
     */
    public static function execute_parameters(): external_function_parameters {
        return new external_function_parameters([
            'cmid' => new external_value(PARAM_INT, 'Course module id. Optional when marker already stores cmid/contextid.', VALUE_DEFAULT, 0),
            'markerid' => new external_value(PARAM_INT, 'Content marker id.', VALUE_DEFAULT, 0),
            'markeruuid' => new external_value(PARAM_RAW, 'Content marker UUID.', VALUE_DEFAULT, ''),

            'targettype' => new external_value(PARAM_ALPHANUMEXT, 'Target type.', VALUE_DEFAULT, ''),
            'targetid' => new external_value(PARAM_INT, 'Target id.', VALUE_DEFAULT, 0),
            'targetuuid' => new external_value(PARAM_RAW, 'Target UUID.', VALUE_DEFAULT, ''),
            'tagid' => new external_value(PARAM_INT, 'Content tag id.', VALUE_DEFAULT, 0),
            'tagsetid' => new external_value(PARAM_INT, 'Content tag set id.', VALUE_DEFAULT, 0),
            'tagkey' => new external_value(PARAM_ALPHANUMEXT, 'Content tag key.', VALUE_DEFAULT, ''),

            'locatortype' => new external_value(PARAM_ALPHANUMEXT, 'Locator type.', VALUE_DEFAULT, ''),
            'locatorvalue' => new external_value(PARAM_RAW, 'Locator value.', VALUE_DEFAULT, ''),
            'locatorstart' => new external_value(PARAM_RAW, 'Locator start.', VALUE_DEFAULT, ''),
            'locatorend' => new external_value(PARAM_RAW, 'Locator end.', VALUE_DEFAULT, ''),
            'locatorsort' => new external_value(PARAM_INT, 'Locator sort value.', VALUE_DEFAULT, 0),

            'severity' => new external_value(PARAM_ALPHANUMEXT, 'Advisory severity.', VALUE_DEFAULT, ''),
            'visibility' => new external_value(PARAM_ALPHANUMEXT, 'Marker visibility.', VALUE_DEFAULT, ''),
            'audiencesuitability' => new external_value(PARAM_ALPHANUMEXT, 'Audience suitability.', VALUE_DEFAULT, ''),
            'reviewstate' => new external_value(PARAM_ALPHANUMEXT, 'Review state. Reviewed/approved/contested/retired requires review capability.', VALUE_DEFAULT, ''),

            'note' => new external_value(PARAM_RAW, 'Advisory note.', VALUE_DEFAULT, ''),
            'teachingcontext' => new external_value(PARAM_RAW, 'Teaching context.', VALUE_DEFAULT, ''),
            'culturalprotocolnote' => new external_value(PARAM_RAW, 'Cultural protocol note.', VALUE_DEFAULT, ''),
            'reviewrationale' => new external_value(PARAM_RAW, 'Review rationale.', VALUE_DEFAULT, ''),
            'metadata' => new external_value(PARAM_RAW, 'JSON object metadata. Empty means no change.', VALUE_DEFAULT, ''),
            'clearfields' => new external_multiple_structure(
                new external_value(PARAM_ALPHANUMEXT, 'Field to clear.'),
                'Fields to clear intentionally.',
                VALUE_DEFAULT,
                []
            ),
        ]);
    }

    /**
     * Execute marker update.
     *
     * @param int $cmid Course module id.
     * @param int $markerid Marker id.
     * @param string $markeruuid Marker UUID.
     * @param string $targettype Target type.
     * @param int $targetid Target id.
     * @param string $targetuuid Target UUID.
     * @param int $tagid Tag id.
     * @param int $tagsetid Tag set id.
     * @param string $tagkey Tag key.
     * @param string $locatortype Locator type.
     * @param string $locatorvalue Locator value.
     * @param string $locatorstart Locator start.
     * @param string $locatorend Locator end.
     * @param int $locatorsort Locator sort.
     * @param string $severity Severity.
     * @param string $visibility Visibility.
     * @param string $audiencesuitability Audience suitability.
     * @param string $reviewstate Review state.
     * @param string $note Advisory note.
     * @param string $teachingcontext Teaching context.
     * @param string $culturalprotocolnote Cultural protocol note.
     * @param string $reviewrationale Review rationale.
     * @param string $metadata JSON metadata.
     * @param array $clearfields Fields to clear.
     * @return array
     */
    public static function execute(
        int $cmid = 0,
        int $markerid = 0,
        string $markeruuid = '',
        string $targettype = '',
        int $targetid = 0,
        string $targetuuid = '',
        int $tagid = 0,
        int $tagsetid = 0,
        string $tagkey = '',
        string $locatortype = '',
        string $locatorvalue = '',
        string $locatorstart = '',
        string $locatorend = '',
        int $locatorsort = 0,
        string $severity = '',
        string $visibility = '',
        string $audiencesuitability = '',
        string $reviewstate = '',
        string $note = '',
        string $teachingcontext = '',
        string $culturalprotocolnote = '',
        string $reviewrationale = '',
        string $metadata = '',
        array $clearfields = []
    ): array {
        global $DB, $USER;

        $params = self::validate_parameters(self::execute_parameters(), [
            'cmid' => $cmid,
            'markerid' => $markerid,
            'markeruuid' => $markeruuid,
            'targettype' => $targettype,
            'targetid' => $targetid,
            'targetuuid' => $targetuuid,
            'tagid' => $tagid,
            'tagsetid' => $tagsetid,
            'tagkey' => $tagkey,
            'locatortype' => $locatortype,
            'locatorvalue' => $locatorvalue,
            'locatorstart' => $locatorstart,
            'locatorend' => $locatorend,
            'locatorsort' => $locatorsort,
            'severity' => $severity,
            'visibility' => $visibility,
            'audiencesuitability' => $audiencesuitability,
            'reviewstate' => $reviewstate,
            'note' => $note,
            'teachingcontext' => $teachingcontext,
            'culturalprotocolnote' => $culturalprotocolnote,
            'reviewrationale' => $reviewrationale,
            'metadata' => $metadata,
            'clearfields' => $clearfields,
        ]);

        self::require_marker_table();

        $marker = self::load_marker((int)$params['markerid'], (string)$params['markeruuid']);
        $resolution = self::resolve_marker_context($marker, (int)$params['cmid']);

        self::validate_context($resolution->context);
        require_login($resolution->course, false, $resolution->cm);

        self::require_edit_permission($resolution->context, $marker);

        $updates = self::build_update_data($params);
        if (empty($updates)) {
            return self::response($marker, $resolution, [], 'unchanged');
        }

        self::require_review_permission_if_needed($resolution->context, $marker, $updates);

        if (class_exists(content_policy::class) && method_exists(content_policy::class, 'normalize_marker_input')) {
            $updates = content_policy::normalize_marker_input($updates);
        }

        $transaction = $DB->start_delegated_transaction();

        $updated = content_marker::update((int)$marker->id, $updates, (int)$USER->id);

        self::trigger_updated_event($updated, $resolution->context, array_keys($updates));

        $transaction->allow_commit();

        return self::response($updated, $resolution, array_keys($updates), 'updated');
    }

    /**
     * Return service response structure.
     *
     * @return external_single_structure
     */
    public static function execute_returns(): external_single_structure {
        return new external_single_structure([
            'status' => new external_value(PARAM_ALPHANUMEXT, 'Operation status.'),
            'markerid' => new external_value(PARAM_INT, 'Content marker id.'),
            'markeruuid' => new external_value(PARAM_RAW, 'Content marker UUID.'),
            'archiveid' => new external_value(PARAM_INT, 'Archive instance id.'),
            'courseid' => new external_value(PARAM_INT, 'Course id.'),
            'cmid' => new external_value(PARAM_INT, 'Course module id.'),
            'record' => self::marker_record_returns(),
            'summary' => self::marker_summary_returns(),
            'permissions' => self::permissions_returns(),
            'changedfields' => new external_multiple_structure(
                new external_value(PARAM_ALPHANUMEXT, 'Changed field.')
            ),
            'warnings' => self::warnings_returns(),
        ]);
    }

    /**
     * Marker record return structure.
     *
     * @return external_single_structure
     */
    private static function marker_record_returns(): external_single_structure {
        return new external_single_structure([
            'id' => new external_value(PARAM_INT, 'Marker id.'),
            'uuid' => new external_value(PARAM_RAW, 'Marker UUID.'),
            'archiveid' => new external_value(PARAM_INT, 'Archive instance id.'),
            'courseid' => new external_value(PARAM_INT, 'Course id.'),
            'cmid' => new external_value(PARAM_INT, 'Course module id.'),
            'contextid' => new external_value(PARAM_INT, 'Context id.'),
            'targettype' => new external_value(PARAM_ALPHANUMEXT, 'Target type.'),
            'targetid' => new external_value(PARAM_INT, 'Target id.'),
            'targetuuid' => new external_value(PARAM_RAW, 'Target UUID.'),
            'tagid' => new external_value(PARAM_INT, 'Tag id.'),
            'tagsetid' => new external_value(PARAM_INT, 'Tag set id.'),
            'tagkey' => new external_value(PARAM_ALPHANUMEXT, 'Tag key.'),
            'locatortype' => new external_value(PARAM_ALPHANUMEXT, 'Locator type.'),
            'locatorvalue' => new external_value(PARAM_RAW, 'Locator value.'),
            'locatorstart' => new external_value(PARAM_RAW, 'Locator start.'),
            'locatorend' => new external_value(PARAM_RAW, 'Locator end.'),
            'locatorsort' => new external_value(PARAM_INT, 'Locator sort.'),
            'severity' => new external_value(PARAM_ALPHANUMEXT, 'Severity.'),
            'visibility' => new external_value(PARAM_ALPHANUMEXT, 'Visibility.'),
            'audiencesuitability' => new external_value(PARAM_ALPHANUMEXT, 'Audience suitability.'),
            'reviewstate' => new external_value(PARAM_ALPHANUMEXT, 'Review state.'),
            'reviewedby' => new external_value(PARAM_INT, 'Reviewer user id.'),
            'timereviewed' => new external_value(PARAM_INT, 'Review timestamp.'),
            'note' => new external_value(PARAM_RAW, 'Advisory note.'),
            'teachingcontext' => new external_value(PARAM_RAW, 'Teaching context.'),
            'culturalprotocolnote' => new external_value(PARAM_RAW, 'Cultural protocol note.'),
            'reviewrationale' => new external_value(PARAM_RAW, 'Review rationale.'),
            'createdby' => new external_value(PARAM_INT, 'Creator user id.'),
            'modifiedby' => new external_value(PARAM_INT, 'Modifier user id.'),
            'metadatajson' => new external_value(PARAM_RAW, 'Metadata JSON.'),
            'timecreated' => new external_value(PARAM_INT, 'Created timestamp.'),
            'timemodified' => new external_value(PARAM_INT, 'Modified timestamp.'),
        ]);
    }

    /**
     * Marker safe summary return structure.
     *
     * @return external_single_structure
     */
    private static function marker_summary_returns(): external_single_structure {
        return new external_single_structure([
            'id' => new external_value(PARAM_INT, 'Marker id.'),
            'uuid' => new external_value(PARAM_RAW, 'Marker UUID.'),
            'tagkey' => new external_value(PARAM_ALPHANUMEXT, 'Tag key.'),
            'label' => new external_value(PARAM_TEXT, 'Label.'),
            'severity' => new external_value(PARAM_ALPHANUMEXT, 'Severity.'),
            'visibility' => new external_value(PARAM_ALPHANUMEXT, 'Visibility.'),
            'audiencesuitability' => new external_value(PARAM_ALPHANUMEXT, 'Audience suitability.'),
            'reviewstate' => new external_value(PARAM_ALPHANUMEXT, 'Review state.'),
            'redacted' => new external_value(PARAM_BOOL, 'Whether marker data is redacted.'),
            'redactionmode' => new external_value(PARAM_ALPHANUMEXT, 'Redaction mode.'),
            'requirescontext' => new external_value(PARAM_BOOL, 'Whether context warning is required.'),
            'cultural' => new external_value(PARAM_BOOL, 'Whether this is culturally restricted.'),
            'restricted' => new external_value(PARAM_BOOL, 'Whether this is restricted.'),
            'showlocator' => new external_value(PARAM_BOOL, 'Whether locator may be displayed.'),
        ]);
    }

    /**
     * Permissions return structure.
     *
     * @return external_single_structure
     */
    private static function permissions_returns(): external_single_structure {
        return new external_single_structure([
            'canview' => new external_value(PARAM_BOOL, 'Can view advisories.'),
            'canmanage' => new external_value(PARAM_BOOL, 'Can manage advisories.'),
            'canreview' => new external_value(PARAM_BOOL, 'Can review advisories.'),
            'candelete' => new external_value(PARAM_BOOL, 'Can delete this marker.'),
            'canviewculturallyrestricted' => new external_value(PARAM_BOOL, 'Can view culturally restricted advisory data.'),
        ]);
    }

    /**
     * Warnings return structure.
     *
     * @return external_multiple_structure
     */
    private static function warnings_returns(): external_multiple_structure {
        return new external_multiple_structure(
            new external_single_structure([
                'item' => new external_value(PARAM_TEXT, 'Warning item.'),
                'itemid' => new external_value(PARAM_INT, 'Warning item id.'),
                'warningcode' => new external_value(PARAM_ALPHANUMEXT, 'Warning code.'),
                'message' => new external_value(PARAM_TEXT, 'Warning message.'),
            ])
        );
    }

    /**
     * Load marker by id or UUID.
     *
     * @param int $markerid Marker id.
     * @param string $markeruuid Marker UUID.
     * @return stdClass
     */
    private static function load_marker(int $markerid, string $markeruuid): stdClass {
        if ($markerid > 0) {
            return content_marker::get_record($markerid, MUST_EXIST);
        }

        $markeruuid = trim($markeruuid);
        if ($markeruuid !== '') {
            return content_marker::get_record_by_uuid($markeruuid, MUST_EXIST);
        }

        throw new invalid_parameter_exception('Either markerid or markeruuid is required.');
    }

    /**
     * Resolve marker context.
     *
     * @param stdClass $marker Marker record.
     * @param int $cmid Optional cmid.
     * @return stdClass Resolution with course, cm, archive, context.
     */
    private static function resolve_marker_context(stdClass $marker, int $cmid = 0): stdClass {
        global $DB;

        if ($cmid <= 0 && !empty($marker->cmid)) {
            $cmid = (int)$marker->cmid;
        }

        if ($cmid > 0) {
            $cm = get_coursemodule_from_id('uckkarchive', $cmid, 0, false, MUST_EXIST);
            $course = $DB->get_record('course', ['id' => $cm->course], '*', MUST_EXIST);
            $archive = $DB->get_record('uckkarchive', ['id' => $cm->instance], '*', MUST_EXIST);
            $context = context_module::instance($cm->id);

            self::assert_marker_matches_context($marker, $archive, $cm, $course, $context);

            return self::resolution($course, $cm, $archive, $context);
        }

        if (!empty($marker->contextid)) {
            $context = context::instance_by_id((int)$marker->contextid, MUST_EXIST);
            if ($context instanceof context_module) {
                $cm = get_coursemodule_from_id('uckkarchive', (int)$context->instanceid, 0, false, MUST_EXIST);
                $course = $DB->get_record('course', ['id' => $cm->course], '*', MUST_EXIST);
                $archive = $DB->get_record('uckkarchive', ['id' => $cm->instance], '*', MUST_EXIST);

                self::assert_marker_matches_context($marker, $archive, $cm, $course, $context);

                return self::resolution($course, $cm, $archive, $context);
            }
        }

        if (!empty($marker->archiveid)) {
            $archive = $DB->get_record('uckkarchive', ['id' => (int)$marker->archiveid], '*', MUST_EXIST);
            $courseid = !empty($marker->courseid) ? (int)$marker->courseid : (int)$archive->course;
            $cm = get_coursemodule_from_instance('uckkarchive', (int)$archive->id, $courseid, false, MUST_EXIST);
            $course = $DB->get_record('course', ['id' => $courseid], '*', MUST_EXIST);
            $context = context_module::instance($cm->id);

            self::assert_marker_matches_context($marker, $archive, $cm, $course, $context);

            return self::resolution($course, $cm, $archive, $context);
        }

        throw new invalid_parameter_exception('Could not resolve content marker context.');
    }

    /**
     * Return resolution object.
     *
     * @param stdClass $course Course.
     * @param stdClass $cm Course module.
     * @param stdClass $archive Archive instance.
     * @param context_module $context Context.
     * @return stdClass
     */
    private static function resolution(stdClass $course, stdClass $cm, stdClass $archive, context_module $context): stdClass {
        return (object)[
            'course' => $course,
            'cm' => $cm,
            'archive' => $archive,
            'context' => $context,
        ];
    }

    /**
     * Validate marker belongs to resolved context.
     *
     * @param stdClass $marker Marker.
     * @param stdClass $archive Archive.
     * @param stdClass $cm Course module.
     * @param stdClass $course Course.
     * @param context_module $context Context.
     * @return void
     */
    private static function assert_marker_matches_context(
        stdClass $marker,
        stdClass $archive,
        stdClass $cm,
        stdClass $course,
        context_module $context
    ): void {
        if (!empty($marker->archiveid) && (int)$marker->archiveid !== (int)$archive->id) {
            throw new invalid_parameter_exception('Marker does not belong to the resolved archive.');
        }

        if (!empty($marker->courseid) && (int)$marker->courseid !== (int)$course->id) {
            throw new invalid_parameter_exception('Marker does not belong to the resolved course.');
        }

        if (!empty($marker->cmid) && (int)$marker->cmid !== (int)$cm->id) {
            throw new invalid_parameter_exception('Marker does not belong to the resolved course module.');
        }

        if (!empty($marker->contextid) && (int)$marker->contextid !== (int)$context->id) {
            throw new invalid_parameter_exception('Marker does not belong to the resolved context.');
        }
    }

    /**
     * Require permission to edit marker.
     *
     * @param context_module $context Context.
     * @param stdClass $marker Marker.
     * @return void
     */
    private static function require_edit_permission(context_module $context, stdClass $marker): void {
        if (class_exists(content_policy::class)) {
            content_policy::require_manage_advisories($context);

            if (!content_policy::can_edit_marker($context, $marker)) {
                throw new \required_capability_exception($context, 'mod/uckkarchive:manageadvisories', 'nopermissions', '');
            }

            return;
        }

        require_capability('mod/uckkarchive:manageadvisories', $context);
    }

    /**
     * Require review capability when update changes review-authority fields.
     *
     * @param context_module $context Context.
     * @param stdClass $marker Current marker.
     * @param array $updates Update data.
     * @return void
     */
    private static function require_review_permission_if_needed(context_module $context, stdClass $marker, array $updates): void {
        if (!array_key_exists('reviewstate', $updates)) {
            return;
        }

        $reviewstate = (string)$updates['reviewstate'];
        $reviewstates = ['reviewed', 'approved', 'contested', 'retired'];

        if (!in_array($reviewstate, $reviewstates, true)) {
            return;
        }

        if (class_exists(content_policy::class)) {
            if (!content_policy::can_review_marker($context, $marker)) {
                throw new \required_capability_exception($context, 'mod/uckkarchive:reviewadvisories', 'nopermissions', '');
            }

            return;
        }

        require_capability('mod/uckkarchive:reviewadvisories', $context);
    }

    /**
     * Build update data.
     *
     * @param array $params Validated parameters.
     * @return array
     */
    private static function build_update_data(array $params): array {
        $updates = [];
        $clearfields = self::normalise_clearfields((array)$params['clearfields']);

        foreach (self::TEXT_FIELDS as $field) {
            if (in_array($field, $clearfields, true)) {
                $updates[$field] = '';
                continue;
            }

            if (array_key_exists($field, $params) && trim((string)$params[$field]) !== '') {
                $updates[$field] = (string)$params[$field];
            }
        }

        foreach (self::INT_FIELDS as $field) {
            if (in_array($field, $clearfields, true)) {
                $updates[$field] = 0;
                continue;
            }

            if (array_key_exists($field, $params) && (int)$params[$field] > 0) {
                $updates[$field] = (int)$params[$field];
            }
        }

        foreach (self::ENUM_FIELDS as $field) {
            if (array_key_exists($field, $params) && trim((string)$params[$field]) !== '') {
                $updates[$field] = clean_param(strtolower(trim((string)$params[$field])), PARAM_ALPHANUMEXT);
            }
        }

        if (trim((string)$params['metadata']) !== '') {
            $metadata = json_decode((string)$params['metadata'], true);
            if (!is_array($metadata)) {
                throw new invalid_parameter_exception('metadata must be a JSON object.');
            }
            $updates['metadata'] = $metadata;
        }

        return $updates;
    }

    /**
     * Normalize clearfields.
     *
     * @param array $clearfields Raw fields.
     * @return string[]
     */
    private static function normalise_clearfields(array $clearfields): array {
        $allowed = array_merge(self::TEXT_FIELDS, self::INT_FIELDS);
        $normalised = [];

        foreach ($clearfields as $field) {
            $field = clean_param((string)$field, PARAM_ALPHANUMEXT);
            if (in_array($field, $allowed, true)) {
                $normalised[] = $field;
            }
        }

        return array_values(array_unique($normalised));
    }

    /**
     * Build response.
     *
     * @param stdClass $marker Marker.
     * @param stdClass $resolution Resolution.
     * @param string[] $changedfields Changed fields.
     * @param string $status Operation status.
     * @return array
     */
    private static function response(stdClass $marker, stdClass $resolution, array $changedfields, string $status): array {
        $record = content_marker::export_record($marker);

        if (class_exists(content_policy::class) && method_exists(content_policy::class, 'marker_display_summary')) {
            $summary = content_policy::marker_display_summary($resolution->context, $marker);
        } else {
            $summary = self::fallback_summary($record);
        }

        return [
            'status' => $status,
            'markerid' => (int)$record['id'],
            'markeruuid' => (string)$record['uuid'],
            'archiveid' => (int)$record['archiveid'],
            'courseid' => (int)$record['courseid'],
            'cmid' => (int)$record['cmid'],
            'record' => self::format_record($record),
            'summary' => self::format_summary($summary),
            'permissions' => self::permissions($resolution->context, $marker),
            'changedfields' => array_values(array_unique(array_map(static function(string $field): string {
                return clean_param($field, PARAM_ALPHANUMEXT);
            }, $changedfields))),
            'warnings' => [],
        ];
    }

    /**
     * Format full marker record.
     *
     * @param array $record Export record.
     * @return array
     */
    private static function format_record(array $record): array {
        return [
            'id' => (int)($record['id'] ?? 0),
            'uuid' => (string)($record['uuid'] ?? ''),
            'archiveid' => (int)($record['archiveid'] ?? 0),
            'courseid' => (int)($record['courseid'] ?? 0),
            'cmid' => (int)($record['cmid'] ?? 0),
            'contextid' => (int)($record['contextid'] ?? 0),
            'targettype' => (string)($record['targettype'] ?? ''),
            'targetid' => (int)($record['targetid'] ?? 0),
            'targetuuid' => (string)($record['targetuuid'] ?? ''),
            'tagid' => (int)($record['tagid'] ?? 0),
            'tagsetid' => (int)($record['tagsetid'] ?? 0),
            'tagkey' => (string)($record['tagkey'] ?? ''),
            'locatortype' => (string)($record['locatortype'] ?? ''),
            'locatorvalue' => (string)($record['locatorvalue'] ?? ''),
            'locatorstart' => (string)($record['locatorstart'] ?? ''),
            'locatorend' => (string)($record['locatorend'] ?? ''),
            'locatorsort' => (int)($record['locatorsort'] ?? 0),
            'severity' => (string)($record['severity'] ?? 'notice'),
            'visibility' => (string)($record['visibility'] ?? 'course'),
            'audiencesuitability' => (string)($record['audiencesuitability'] ?? 'guided'),
            'reviewstate' => (string)($record['reviewstate'] ?? 'draft'),
            'reviewedby' => (int)($record['reviewedby'] ?? 0),
            'timereviewed' => (int)($record['timereviewed'] ?? 0),
            'note' => (string)($record['note'] ?? ''),
            'teachingcontext' => (string)($record['teachingcontext'] ?? ''),
            'culturalprotocolnote' => (string)($record['culturalprotocolnote'] ?? ''),
            'reviewrationale' => (string)($record['reviewrationale'] ?? ''),
            'createdby' => (int)($record['createdby'] ?? 0),
            'modifiedby' => (int)($record['modifiedby'] ?? 0),
            'metadatajson' => self::json(is_array($record['metadata'] ?? null) ? $record['metadata'] : []),
            'timecreated' => (int)($record['timecreated'] ?? 0),
            'timemodified' => (int)($record['timemodified'] ?? 0),
        ];
    }

    /**
     * Format summary.
     *
     * @param array $summary Summary.
     * @return array
     */
    private static function format_summary(array $summary): array {
        return [
            'id' => (int)($summary['id'] ?? 0),
            'uuid' => (string)($summary['uuid'] ?? ''),
            'tagkey' => (string)($summary['tagkey'] ?? ''),
            'label' => (string)($summary['label'] ?? ($summary['tagkey'] ?? '')),
            'severity' => (string)($summary['severity'] ?? 'notice'),
            'visibility' => (string)($summary['visibility'] ?? 'course'),
            'audiencesuitability' => (string)($summary['audiencesuitability'] ?? 'guided'),
            'reviewstate' => (string)($summary['reviewstate'] ?? 'draft'),
            'redacted' => !empty($summary['redacted']),
            'redactionmode' => (string)($summary['redactionmode'] ?? 'none'),
            'requirescontext' => !empty($summary['requirescontext']),
            'cultural' => !empty($summary['cultural']),
            'restricted' => !empty($summary['restricted']),
            'showlocator' => !empty($summary['showlocator']),
        ];
    }

    /**
     * Fallback summary.
     *
     * @param array $record Marker export.
     * @return array
     */
    private static function fallback_summary(array $record): array {
        return [
            'id' => (int)($record['id'] ?? 0),
            'uuid' => (string)($record['uuid'] ?? ''),
            'tagkey' => (string)($record['tagkey'] ?? ''),
            'label' => (string)($record['tagkey'] ?? ''),
            'severity' => (string)($record['severity'] ?? 'notice'),
            'visibility' => (string)($record['visibility'] ?? 'course'),
            'audiencesuitability' => (string)($record['audiencesuitability'] ?? 'guided'),
            'reviewstate' => (string)($record['reviewstate'] ?? 'draft'),
            'redacted' => false,
            'redactionmode' => 'none',
            'requirescontext' => false,
            'cultural' => in_array((string)($record['visibility'] ?? ''), ['restricted_cultural'], true),
            'restricted' => in_array((string)($record['visibility'] ?? ''), ['restricted', 'restricted_integrity', 'restricted_cultural'], true),
            'showlocator' => true,
        ];
    }

    /**
     * Permissions payload.
     *
     * @param context_module $context Context.
     * @param stdClass $marker Marker.
     * @return array
     */
    private static function permissions(context_module $context, stdClass $marker): array {
        if (class_exists(content_policy::class)) {
            return [
                'canview' => content_policy::can_view_advisories($context),
                'canmanage' => content_policy::can_manage_advisories($context),
                'canreview' => content_policy::can_review_marker($context, $marker),
                'candelete' => content_policy::can_delete_marker($context, $marker),
                'canviewculturallyrestricted' => content_policy::can_view_culturally_restricted($context),
            ];
        }

        return [
            'canview' => has_capability('mod/uckkarchive:viewadvisories', $context),
            'canmanage' => has_capability('mod/uckkarchive:manageadvisories', $context),
            'canreview' => has_capability('mod/uckkarchive:reviewadvisories', $context),
            'candelete' => has_capability('mod/uckkarchive:manageadvisories', $context),
            'canviewculturallyrestricted' => has_capability('mod/uckkarchive:viewculturallyrestricted', $context),
        ];
    }

    /**
     * Trigger content marker reviewed event when update changes review state.
     *
     * @param stdClass $marker Marker.
     * @param context_module $context Context.
     * @param string[] $changedfields Changed fields.
     * @return void
     */
    private static function trigger_updated_event(stdClass $marker, context_module $context, array $changedfields): void {
        if (!in_array('reviewstate', $changedfields, true)) {
            return;
        }

        $eventclass = '\\mod_uckkarchive\\event\\content_marker_reviewed';
        if (!class_exists($eventclass)) {
            return;
        }

        try {
            $event = $eventclass::create([
                'objectid' => (int)$marker->id,
                'context' => $context,
                'relateduserid' => !empty($marker->reviewedby) ? (int)$marker->reviewedby : null,
                'other' => [
                    'uuid' => (string)($marker->uuid ?? ''),
                    'tagkey' => (string)($marker->tagkey ?? ''),
                    'reviewstate' => (string)($marker->reviewstate ?? ''),
                ],
            ]);
            $event->add_record_snapshot(self::TABLE, $marker);
            $event->trigger();
        } catch (\Throwable $ignored) {
            // Event availability must not break marker persistence while files are generated incrementally.
        }
    }

    /**
     * Ensure marker table exists.
     *
     * @return void
     */
    private static function require_marker_table(): void {
        global $DB;

        if (!$DB->get_manager()->table_exists(new \xmldb_table(self::TABLE))) {
            throw new \moodle_exception('missingtable', 'error', '', self::TABLE);
        }
    }

    /**
     * JSON encode.
     *
     * @param array $data Data.
     * @return string
     */
    private static function json(array $data): string {
        return json_encode($data, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES) ?: '{}';
    }
}
