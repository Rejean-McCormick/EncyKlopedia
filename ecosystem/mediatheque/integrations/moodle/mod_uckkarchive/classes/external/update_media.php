<?php
// This file is part of Moodle - https://moodle.org/
//
// Moodle is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// any later version.

/**
 * Update an existing media record.
 *
 * @package    mod_uckkarchive
 * @copyright  2026 Univers-Cité King Klown
 * @license    https://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later
 */

namespace mod_uckkarchive\external;

defined('MOODLE_INTERNAL') || die();

global $CFG;
require_once($CFG->libdir . '/externallib.php');
require_once(dirname(__DIR__) . '/local/context_resolver.php');

use core_external\external_api;
use core_external\external_function_parameters;
use core_external\external_multiple_structure;
use core_external\external_single_structure;
use core_external\external_value;
use mod_uckkarchive\local\context_resolver;
use stdClass;

/**
 * External service: update an existing media record.
 */
class update_media extends external_api {
    /** Target media table. */
    private const TABLE_MEDIA = 'uckkarchive_media';

    /** Allowed media lifecycle states. */
    private const STATUSES = [
        'draft',
        'submitted',
        'active',
        'restricted',
        'superseded',
        'archived',
        'deleted_soft',
    ];

    /** Allowed visibility states. */
    private const VISIBILITIES = [
        'private',
        'user',
        'group',
        'course',
        'cohort',
        'program',
        'institution',
        'public',
        'restricted',
        'restricted_integrity',
        'restricted_cultural',
    ];

    /** Allowed audience suitability values. */
    private const AUDIENCES = [
        'general',
        'guided',
        'mature',
        'restricted',
        'restricted_cultural',
        'restricted_integrity',
        'staff_only',
    ];

    /** Text fields accepted by the update service. */
    private const TEXT_FIELDS = [
        'title' => PARAM_TEXT,
        'description' => PARAM_RAW,
        'alttext' => PARAM_TEXT,
        'caption' => PARAM_RAW,
        'license' => PARAM_TEXT,
        'rightsnote' => PARAM_RAW,
        'language' => PARAM_LANG,
    ];

    /** Enum fields accepted by the update service. */
    private const ENUM_FIELDS = [
        'status' => self::STATUSES,
        'visibility' => self::VISIBILITIES,
        'audiencesuitability' => self::AUDIENCES,
    ];

    /**
     * Return service parameters.
     *
     * Empty string means "do not change" for scalar text/enum fields.
     * Metadata is a JSON object string merged as replacement metadata.
     *
     * @return external_function_parameters
     */
    public static function execute_parameters(): external_function_parameters {
        return new external_function_parameters([
            'cmid' => new external_value(PARAM_INT, 'Course module id', VALUE_DEFAULT, 0),
            'archiveid' => new external_value(PARAM_INT, 'Archive instance id', VALUE_DEFAULT, 0),
            'mediaid' => new external_value(PARAM_INT, 'Media id', VALUE_DEFAULT, 0),
            'mediauuid' => new external_value(PARAM_TEXT, 'Media UUID', VALUE_DEFAULT, ''),
            'title' => new external_value(PARAM_TEXT, 'Media title', VALUE_DEFAULT, ''),
            'description' => new external_value(PARAM_RAW, 'Media description', VALUE_DEFAULT, ''),
            'alttext' => new external_value(PARAM_TEXT, 'Alternative text', VALUE_DEFAULT, ''),
            'caption' => new external_value(PARAM_RAW, 'Caption', VALUE_DEFAULT, ''),
            'status' => new external_value(PARAM_ALPHANUMEXT, 'Media lifecycle status', VALUE_DEFAULT, ''),
            'visibility' => new external_value(PARAM_ALPHANUMEXT, 'Visibility', VALUE_DEFAULT, ''),
            'audiencesuitability' => new external_value(PARAM_ALPHANUMEXT, 'Audience suitability', VALUE_DEFAULT, ''),
            'license' => new external_value(PARAM_TEXT, 'License', VALUE_DEFAULT, ''),
            'rightsnote' => new external_value(PARAM_RAW, 'Rights note', VALUE_DEFAULT, ''),
            'language' => new external_value(PARAM_LANG, 'Language code', VALUE_DEFAULT, ''),
            'sourceid' => new external_value(PARAM_INT, 'Media source id', VALUE_DEFAULT, 0),
            'metadata' => new external_value(PARAM_RAW, 'JSON metadata object', VALUE_DEFAULT, ''),
            'reason' => new external_value(PARAM_RAW, 'Reason for update', VALUE_DEFAULT, ''),
        ]);
    }

    /**
     * Execute media update.
     *
     * @param int $cmid Course module id.
     * @param int $archiveid Archive instance id.
     * @param int $mediaid Media id.
     * @param string $mediauuid Media UUID.
     * @param string $title Title.
     * @param string $description Description.
     * @param string $alttext Alternative text.
     * @param string $caption Caption.
     * @param string $status Lifecycle status.
     * @param string $visibility Visibility.
     * @param string $audiencesuitability Audience suitability.
     * @param string $license License.
     * @param string $rightsnote Rights note.
     * @param string $language Language.
     * @param int $sourceid Source id.
     * @param string $metadata JSON metadata.
     * @param string $reason Update reason.
     * @return array
     */
    public static function execute(int $cmid = 0, int $archiveid = 0, int $mediaid = 0, string $mediauuid = '',
            string $title = '', string $description = '', string $alttext = '', string $caption = '',
            string $status = '', string $visibility = '', string $audiencesuitability = '', string $license = '',
            string $rightsnote = '', string $language = '', int $sourceid = 0, string $metadata = '',
            string $reason = ''): array {
        global $DB, $USER;

        $params = self::validate_parameters(self::execute_parameters(), [
            'cmid' => $cmid,
            'archiveid' => $archiveid,
            'mediaid' => $mediaid,
            'mediauuid' => $mediauuid,
            'title' => $title,
            'description' => $description,
            'alttext' => $alttext,
            'caption' => $caption,
            'status' => $status,
            'visibility' => $visibility,
            'audiencesuitability' => $audiencesuitability,
            'license' => $license,
            'rightsnote' => $rightsnote,
            'language' => $language,
            'sourceid' => $sourceid,
            'metadata' => $metadata,
            'reason' => $reason,
        ]);

        self::require_media_table();

        $media = self::load_media($params['mediaid'], $params['mediauuid']);
        $resolution = self::resolve_media_context($media, $params);
        self::validate_context($resolution->context);
        require_login($resolution->course, false, $resolution->cm);

        self::require_edit_permission($resolution, $media);
        self::require_policy_permission($resolution, $media, $params);

        $changes = self::build_update_record($media, $params);
        if (count((array)$changes) === 1) {
            return self::response($media, $resolution, [], 'unchanged');
        }

        $changes->id = (int)$media->id;
        if (self::field_exists(self::TABLE_MEDIA, 'usermodified')) {
            $changes->usermodified = (int)$USER->id;
        }
        if (self::field_exists(self::TABLE_MEDIA, 'timemodified')) {
            $changes->timemodified = time();
        }

        $transaction = $DB->start_delegated_transaction();

        $DB->update_record(self::TABLE_MEDIA, $changes);
        $updated = $DB->get_record(self::TABLE_MEDIA, ['id' => (int)$media->id], '*', MUST_EXIST);

        self::write_revision_if_available($media, $updated, $resolution, $params['reason']);
        self::write_provenance_if_available($updated, $resolution, $params['reason']);
        self::trigger_media_updated_event($updated, $resolution, array_keys((array)$changes));

        $transaction->allow_commit();

        return self::response($updated, $resolution, array_keys((array)$changes), 'updated');
    }

    /**
     * Return service response structure.
     *
     * @return external_single_structure
     */
    public static function execute_returns(): external_single_structure {
        return new external_single_structure([
            'status' => new external_value(PARAM_ALPHANUMEXT, 'Operation status'),
            'mediaid' => new external_value(PARAM_INT, 'Media id'),
            'mediauuid' => new external_value(PARAM_TEXT, 'Media UUID'),
            'archiveid' => new external_value(PARAM_INT, 'Archive instance id'),
            'cmid' => new external_value(PARAM_INT, 'Course module id'),
            'record' => self::media_record_returns(),
            'permissions' => self::permissions_returns(),
            'changedfields' => new external_multiple_structure(
                new external_value(PARAM_ALPHANUMEXT, 'Changed field')
            ),
            'warnings' => self::warnings_returns(),
        ]);
    }

    /**
     * Return media record external structure.
     *
     * @return external_single_structure
     */
    private static function media_record_returns(): external_single_structure {
        return new external_single_structure([
            'id' => new external_value(PARAM_INT, 'Media id'),
            'uuid' => new external_value(PARAM_TEXT, 'Media UUID'),
            'archiveid' => new external_value(PARAM_INT, 'Archive instance id'),
            'courseid' => new external_value(PARAM_INT, 'Course id'),
            'cmid' => new external_value(PARAM_INT, 'Course module id'),
            'contextid' => new external_value(PARAM_INT, 'Context id'),
            'title' => new external_value(PARAM_TEXT, 'Title'),
            'description' => new external_value(PARAM_RAW, 'Description'),
            'mediatype' => new external_value(PARAM_ALPHANUMEXT, 'Media type'),
            'mimetype' => new external_value(PARAM_TEXT, 'MIME type'),
            'status' => new external_value(PARAM_ALPHANUMEXT, 'Status'),
            'visibility' => new external_value(PARAM_ALPHANUMEXT, 'Visibility'),
            'audiencesuitability' => new external_value(PARAM_ALPHANUMEXT, 'Audience suitability'),
            'sourceid' => new external_value(PARAM_INT, 'Source id'),
            'language' => new external_value(PARAM_LANG, 'Language'),
            'timecreated' => new external_value(PARAM_INT, 'Created time'),
            'timemodified' => new external_value(PARAM_INT, 'Modified time'),
        ]);
    }

    /**
     * Return permissions structure.
     *
     * @return external_single_structure
     */
    private static function permissions_returns(): external_single_structure {
        return new external_single_structure([
            'canview' => new external_value(PARAM_BOOL, 'Can view media'),
            'canedit' => new external_value(PARAM_BOOL, 'Can edit media'),
            'candelete' => new external_value(PARAM_BOOL, 'Can delete media'),
            'canversion' => new external_value(PARAM_BOOL, 'Can version media'),
            'candownload' => new external_value(PARAM_BOOL, 'Can download media'),
            'canviewrestricted' => new external_value(PARAM_BOOL, 'Can view restricted media'),
            'canviewculturallyrestricted' => new external_value(PARAM_BOOL, 'Can view culturally restricted material'),
        ]);
    }

    /**
     * Return warnings structure.
     *
     * @return external_multiple_structure
     */
    private static function warnings_returns(): external_multiple_structure {
        return new external_multiple_structure(
            new external_single_structure([
                'item' => new external_value(PARAM_TEXT, 'Warning item'),
                'itemid' => new external_value(PARAM_INT, 'Warning item id'),
                'warningcode' => new external_value(PARAM_ALPHANUMEXT, 'Warning code'),
                'message' => new external_value(PARAM_TEXT, 'Warning message'),
            ])
        );
    }

    /**
     * Load media by id or UUID.
     *
     * @param int $mediaid Media id.
     * @param string $mediauuid Media UUID.
     * @return stdClass
     */
    private static function load_media(int $mediaid, string $mediauuid): stdClass {
        global $DB;

        if ($mediaid > 0) {
            return $DB->get_record(self::TABLE_MEDIA, ['id' => $mediaid], '*', MUST_EXIST);
        }

        $mediauuid = trim($mediauuid);
        if ($mediauuid !== '' && self::field_exists(self::TABLE_MEDIA, 'uuid')) {
            return $DB->get_record(self::TABLE_MEDIA, ['uuid' => $mediauuid], '*', MUST_EXIST);
        }

        throw new \invalid_parameter_exception('Either mediaid or mediauuid is required.');
    }

    /**
     * Resolve media context.
     *
     * @param stdClass $media Media record.
     * @param array $params Parameters.
     * @return stdClass
     */
    private static function resolve_media_context(stdClass $media, array $params): stdClass {
        if (!empty($params['cmid'])) {
            $resolution = context_resolver::from_cmid((int)$params['cmid']);
        } else {
            $resolution = context_resolver::from_media((int)$media->id);
        }

        $mediaarchiveid = self::record_int($media, ['archiveid', 'uckkarchiveid', 'uckkarchive'], 0);
        if ($mediaarchiveid > 0 && (int)$resolution->archiveid !== $mediaarchiveid) {
            throw new \invalid_parameter_exception('Media record does not belong to the resolved archive instance.');
        }

        if (!empty($params['archiveid']) && (int)$params['archiveid'] !== (int)$resolution->archiveid) {
            throw new \invalid_parameter_exception('archiveid does not match resolved archive instance.');
        }

        return $resolution;
    }

    /**
     * Require edit capability and restricted access if needed.
     *
     * @param stdClass $resolution Resolution object.
     * @param stdClass $media Media record.
     * @return void
     */
    private static function require_edit_permission(stdClass $resolution, stdClass $media): void {
        require_capability('mod/uckkarchive:editmedia', $resolution->context);

        if (self::is_restricted_media($media)) {
            if (!has_capability('mod/uckkarchive:viewrestrictedmedia', $resolution->context)
                    && !has_capability('mod/uckkarchive:viewrestricted', $resolution->context)) {
                throw new \required_capability_exception(
                    $resolution->context,
                    'mod/uckkarchive:viewrestrictedmedia',
                    'nopermissions',
                    ''
                );
            }
        }

        if (self::is_culturally_restricted_media($media)
                && !has_capability('mod/uckkarchive:viewculturallyrestricted', $resolution->context)) {
            throw new \required_capability_exception(
                $resolution->context,
                'mod/uckkarchive:viewculturallyrestricted',
                'nopermissions',
                ''
            );
        }
    }

    /**
     * Call media_policy if available.
     *
     * @param stdClass $resolution Resolution object.
     * @param stdClass $media Media record.
     * @param array $params Parameters.
     * @return void
     */
    private static function require_policy_permission(stdClass $resolution, stdClass $media, array $params): void {
        $policyclass = '\\mod_uckkarchive\\local\\media_policy';

        if (!class_exists($policyclass)) {
            return;
        }

        if (method_exists($policyclass, 'require_can_edit')) {
            $policyclass::require_can_edit($media, $resolution->context);
            return;
        }

        if (method_exists($policyclass, 'can_edit')
                && !$policyclass::can_edit($media, $resolution->context)) {
            throw new \required_capability_exception(
                $resolution->context,
                'mod/uckkarchive:editmedia',
                'nopermissions',
                ''
            );
        }
    }

    /**
     * Build DB update object from parameters.
     *
     * @param stdClass $media Existing media.
     * @param array $params Parameters.
     * @return stdClass
     */
    private static function build_update_record(stdClass $media, array $params): stdClass {
        $update = new stdClass();
        $update->id = (int)$media->id;

        foreach (self::TEXT_FIELDS as $field => $paramtype) {
            if (!self::field_exists(self::TABLE_MEDIA, $field)) {
                continue;
            }

            if (!array_key_exists($field, $params) || $params[$field] === '') {
                continue;
            }

            $value = clean_param($params[$field], $paramtype);
            if (!property_exists($media, $field) || (string)$media->{$field} !== (string)$value) {
                $update->{$field} = $value;
            }
        }

        foreach (self::ENUM_FIELDS as $field => $allowed) {
            if (!self::field_exists(self::TABLE_MEDIA, $field)) {
                continue;
            }

            if (!array_key_exists($field, $params) || $params[$field] === '') {
                continue;
            }

            $value = clean_param($params[$field], PARAM_ALPHANUMEXT);
            self::require_allowed_value($field, $value, $allowed);

            if ($field === 'visibility' && $value === 'institutional') {
                $value = 'institution';
            }

            if (!property_exists($media, $field) || (string)$media->{$field} !== $value) {
                $update->{$field} = $value;
            }
        }

        if (!empty($params['sourceid']) && self::field_exists(self::TABLE_MEDIA, 'sourceid')) {
            $sourceid = (int)$params['sourceid'];
            self::require_valid_source($sourceid);
            if (!property_exists($media, 'sourceid') || (int)$media->sourceid !== $sourceid) {
                $update->sourceid = $sourceid;
            }
        }

        if ($params['metadata'] !== '' && self::field_exists(self::TABLE_MEDIA, 'metadata')) {
            $metadata = self::normalize_metadata($params['metadata']);
            if (!property_exists($media, 'metadata') || (string)$media->metadata !== $metadata) {
                $update->metadata = $metadata;
            }
        }

        return $update;
    }

    /**
     * Validate an allowed enum value.
     *
     * @param string $field Field name.
     * @param string $value Value.
     * @param array $allowed Allowed values.
     * @return void
     */
    private static function require_allowed_value(string $field, string $value, array $allowed): void {
        if (!in_array($value, $allowed, true)) {
            throw new \invalid_parameter_exception('Invalid media ' . $field . ': ' . $value);
        }
    }

    /**
     * Validate source id if source table exists.
     *
     * @param int $sourceid Source id.
     * @return void
     */
    private static function require_valid_source(int $sourceid): void {
        global $DB;

        if ($sourceid <= 0) {
            throw new \invalid_parameter_exception('Invalid source id.');
        }

        if (self::table_exists('uckkarchive_media_source')
                && !$DB->record_exists('uckkarchive_media_source', ['id' => $sourceid])) {
            throw new \invalid_parameter_exception('Media source does not exist.');
        }
    }

    /**
     * Normalize metadata JSON.
     *
     * @param string $metadata JSON metadata object.
     * @return string
     */
    private static function normalize_metadata(string $metadata): string {
        $decoded = json_decode($metadata, true);

        if (!is_array($decoded) || array_is_list($decoded)) {
            throw new \invalid_parameter_exception('metadata must be a JSON object.');
        }

        return json_encode($decoded, JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE);
    }

    /**
     * Write revision if local class exists.
     *
     * @param stdClass $before Previous media record.
     * @param stdClass $after Updated media record.
     * @param stdClass $resolution Resolution object.
     * @param string $reason Reason.
     * @return void
     */
    private static function write_revision_if_available(stdClass $before, stdClass $after, stdClass $resolution,
            string $reason): void {
        $class = '\\mod_uckkarchive\\local\\media_version';
        if (!class_exists($class)) {
            return;
        }

        if (method_exists($class, 'record_metadata_update')) {
            $class::record_metadata_update($before, $after, $resolution, $reason);
        }
    }

    /**
     * Write provenance if local class exists.
     *
     * @param stdClass $media Updated media record.
     * @param stdClass $resolution Resolution object.
     * @param string $reason Reason.
     * @return void
     */
    private static function write_provenance_if_available(stdClass $media, stdClass $resolution, string $reason): void {
        $class = '\\mod_uckkarchive\\local\\provenance';
        if (!class_exists($class)) {
            return;
        }

        if (method_exists($class, 'record_media_update')) {
            $class::record_media_update($media, $resolution, $reason);
        }
    }

    /**
     * Trigger media updated event if event class exists.
     *
     * @param stdClass $media Updated media record.
     * @param stdClass $resolution Resolution object.
     * @param array $changedfields Changed field names.
     * @return void
     */
    private static function trigger_media_updated_event(stdClass $media, stdClass $resolution,
            array $changedfields): void {
        $eventclass = '\\mod_uckkarchive\\event\\media_updated';
        if (!class_exists($eventclass)) {
            return;
        }

        $event = $eventclass::create([
            'objectid' => (int)$media->id,
            'context' => $resolution->context,
            'other' => [
                'archiveid' => (int)$resolution->archiveid,
                'courseid' => (int)$resolution->courseid,
                'cmid' => (int)$resolution->cmid,
                'mediauuid' => (string)($media->uuid ?? ''),
                'changedfields' => array_values(array_diff($changedfields, ['id'])),
            ],
        ]);
        $event->add_record_snapshot(self::TABLE_MEDIA, $media);
        $event->trigger();
    }

    /**
     * Build response.
     *
     * @param stdClass $media Media record.
     * @param stdClass $resolution Resolution object.
     * @param array $changedfields Changed fields.
     * @param string $status Status.
     * @return array
     */
    private static function response(stdClass $media, stdClass $resolution, array $changedfields,
            string $status): array {
        return [
            'status' => $status,
            'mediaid' => (int)$media->id,
            'mediauuid' => (string)($media->uuid ?? ''),
            'archiveid' => (int)$resolution->archiveid,
            'cmid' => (int)$resolution->cmid,
            'record' => self::export_media_record($media, $resolution),
            'permissions' => self::export_permissions($resolution),
            'changedfields' => array_values(array_diff($changedfields, ['id'])),
            'warnings' => [],
        ];
    }

    /**
     * Export media record safely.
     *
     * @param stdClass $media Media record.
     * @param stdClass $resolution Resolution object.
     * @return array
     */
    private static function export_media_record(stdClass $media, stdClass $resolution): array {
        return [
            'id' => (int)$media->id,
            'uuid' => (string)($media->uuid ?? ''),
            'archiveid' => self::record_int($media, ['archiveid', 'uckkarchiveid', 'uckkarchive'], (int)$resolution->archiveid),
            'courseid' => self::record_int($media, ['courseid', 'course'], (int)$resolution->courseid),
            'cmid' => self::record_int($media, ['cmid', 'coursemoduleid'], (int)$resolution->cmid),
            'contextid' => self::record_int($media, ['contextid'], (int)$resolution->contextid),
            'title' => (string)($media->title ?? ''),
            'description' => (string)($media->description ?? ''),
            'mediatype' => (string)($media->mediatype ?? ''),
            'mimetype' => (string)($media->mimetype ?? ''),
            'status' => (string)($media->status ?? ''),
            'visibility' => (string)($media->visibility ?? ''),
            'audiencesuitability' => (string)($media->audiencesuitability ?? ''),
            'sourceid' => (int)($media->sourceid ?? 0),
            'language' => (string)($media->language ?? ''),
            'timecreated' => (int)($media->timecreated ?? 0),
            'timemodified' => (int)($media->timemodified ?? 0),
        ];
    }

    /**
     * Export permission summary.
     *
     * @param stdClass $resolution Resolution object.
     * @return array
     */
    private static function export_permissions(stdClass $resolution): array {
        return [
            'canview' => has_capability('mod/uckkarchive:viewmedia', $resolution->context),
            'canedit' => has_capability('mod/uckkarchive:editmedia', $resolution->context),
            'candelete' => has_capability('mod/uckkarchive:deletemedia', $resolution->context),
            'canversion' => has_capability('mod/uckkarchive:versionmedia', $resolution->context),
            'candownload' => has_capability('mod/uckkarchive:downloadmedia', $resolution->context),
            'canviewrestricted' => has_capability('mod/uckkarchive:viewrestrictedmedia', $resolution->context)
                || has_capability('mod/uckkarchive:viewrestricted', $resolution->context),
            'canviewculturallyrestricted' => has_capability('mod/uckkarchive:viewculturallyrestricted', $resolution->context),
        ];
    }

    /**
     * Check whether media is restricted.
     *
     * @param stdClass $media Media record.
     * @return bool
     */
    private static function is_restricted_media(stdClass $media): bool {
        $visibility = (string)($media->visibility ?? '');
        $status = (string)($media->status ?? '');
        $audience = (string)($media->audiencesuitability ?? '');

        return in_array($visibility, ['restricted', 'restricted_integrity', 'restricted_cultural'], true)
            || in_array($status, ['restricted'], true)
            || in_array($audience, ['restricted', 'restricted_integrity', 'restricted_cultural', 'staff_only'], true);
    }

    /**
     * Check whether media is culturally restricted.
     *
     * @param stdClass $media Media record.
     * @return bool
     */
    private static function is_culturally_restricted_media(stdClass $media): bool {
        return (string)($media->visibility ?? '') === 'restricted_cultural'
            || (string)($media->audiencesuitability ?? '') === 'restricted_cultural';
    }

    /**
     * Return first integer field found on a record.
     *
     * @param stdClass $record Record.
     * @param array $fields Candidate fields.
     * @param int $default Default.
     * @return int
     */
    private static function record_int(stdClass $record, array $fields, int $default = 0): int {
        foreach ($fields as $field) {
            if (property_exists($record, $field) && $record->{$field} !== null && $record->{$field} !== '') {
                return (int)$record->{$field};
            }
        }

        return $default;
    }

    /**
     * Require media table to exist.
     *
     * @return void
     */
    private static function require_media_table(): void {
        if (!self::table_exists(self::TABLE_MEDIA)) {
            throw new \moodle_exception('missingtable', 'error', '', self::TABLE_MEDIA);
        }
    }

    /**
     * Check table existence.
     *
     * @param string $table Table name without prefix.
     * @return bool
     */
    private static function table_exists(string $table): bool {
        global $DB;

        return $DB->get_manager()->table_exists($table);
    }

    /**
     * Check field existence.
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
