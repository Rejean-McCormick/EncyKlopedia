<?php
// This file is part of Moodle - https://moodle.org/.
//
// Moodle is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// any later version.

/**
 * External service for reading one external work reference.
 *
 * @package    mod_uckkarchive
 * @copyright  2026 Univers-Cité King Klown
 * @license    https://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later
 */

declare(strict_types=1);

namespace mod_uckkarchive\external;

defined('MOODLE_INTERNAL') || die();

global $CFG;

require_once($CFG->libdir . '/externallib.php');
require_once(dirname(__DIR__, 2) . '/locallib.php');
require_once(dirname(__DIR__) . '/local/external_work.php');

use context_module;
use core_external\external_api;
use core_external\external_function_parameters;
use core_external\external_multiple_structure;
use core_external\external_single_structure;
use core_external\external_value;
use invalid_parameter_exception;
use mod_uckkarchive\local\external_work;
use moodle_exception;
use stdClass;

/**
 * Reads one external work reference for the self-contained media library.
 *
 * External works are third-party or foreign works referenced by the archive.
 * This service does not imply ownership over the work and does not expose
 * restricted fields unless the current user has the required archive/media
 * capabilities.
 */
final class get_external_work extends external_api {
    /** Capability for ordinary media/library visibility. */
    private const CAP_VIEW_MEDIA = 'mod/uckkarchive:viewmedia';

    /** Capability for managing external works. */
    private const CAP_MANAGE_EXTERNAL_WORKS = 'mod/uckkarchive:manageexternalworks';

    /** Capability for restricted media visibility. */
    private const CAP_VIEW_RESTRICTED_MEDIA = 'mod/uckkarchive:viewrestrictedmedia';

    /** Capability for restricted archive visibility. */
    private const CAP_VIEW_RESTRICTED_ARCHIVE = 'mod/uckkarchive:viewrestricted';

    /** Capability for culturally restricted material. */
    private const CAP_VIEW_CULTURALLY_RESTRICTED = 'mod/uckkarchive:viewculturallyrestricted';

    /** External work table. */
    private const TABLE_EXTERNAL_WORK = 'uckkarchive_external_work';

    /**
     * Return service parameters.
     *
     * Either `externalworkid` or `externalworkuuid` must be provided.
     *
     * @return external_function_parameters
     */
    public static function execute_parameters(): external_function_parameters {
        return new external_function_parameters([
            'cmid' => new external_value(PARAM_INT, 'Course module id'),
            'externalworkid' => new external_value(PARAM_INT, 'External work id', VALUE_DEFAULT, 0),
            'externalworkuuid' => new external_value(PARAM_TEXT, 'External work UUID', VALUE_DEFAULT, ''),
            'include' => new external_multiple_structure(
                new external_value(PARAM_ALPHANUMEXT, 'Include value'),
                'Optional include values: permissions',
                VALUE_DEFAULT,
                []
            ),
        ]);
    }

    /**
     * Execute the service.
     *
     * @param int $cmid Course module id.
     * @param int $externalworkid External work id.
     * @param string $externalworkuuid External work UUID.
     * @param string[] $include Include values.
     * @return array<string, mixed>
     */
    public static function execute(
        int $cmid,
        int $externalworkid = 0,
        string $externalworkuuid = '',
        array $include = []
    ): array {
        $params = self::validate_parameters(self::execute_parameters(), [
            'cmid' => $cmid,
            'externalworkid' => $externalworkid,
            'externalworkuuid' => $externalworkuuid,
            'include' => $include,
        ]);

        [$course, $cm, $archive, $context] = self::load_page((int)$params['cmid']);
        self::validate_context($context);

        self::require_base_capability($context);

        $include = self::normalise_include((array)$params['include']);
        $externalworkid = (int)$params['externalworkid'];
        $externalworkuuid = trim((string)$params['externalworkuuid']);

        if ($externalworkid <= 0 && $externalworkuuid === '') {
            throw new invalid_parameter_exception('Either externalworkid or externalworkuuid is required.');
        }

        if (!self::table_exists(self::TABLE_EXTERNAL_WORK)) {
            return self::not_found_response(
                self::get_permissions($context),
                self::warning('external_work', 0, 'externalworktablenotfound', 'External work table is not installed yet.')
            );
        }

        $work = self::load_external_work($externalworkid, $externalworkuuid);

        if (!$work) {
            return self::not_found_response(
                self::get_permissions($context),
                self::warning('external_work', max(0, $externalworkid), 'externalworknotfound', 'External work was not found.')
            );
        }

        if (!self::belongs_to_archive($work, (int)$archive->id)) {
            return self::not_found_response(
                self::get_permissions($context),
                self::warning('external_work', (int)$work->id, 'externalworknotfound', 'External work was not found.')
            );
        }

        if (!self::can_view_external_work($work, $context)) {
            throw new moodle_exception('nopermissions', 'error', '', self::CAP_VIEW_MEDIA);
        }

        $response = [
            'found' => true,
            'externalwork' => self::export_external_work($work, $context),
            'permissions' => self::get_permissions($context),
            'warnings' => [],
        ];

        if (!in_array('permissions', $include, true)) {
            // Preserve the return shape but keep it minimal when not explicitly requested.
            $response['permissions'] = self::get_permissions($context);
        }

        return $response;
    }

    /**
     * Return service response structure.
     *
     * @return external_single_structure
     */
    public static function execute_returns(): external_single_structure {
        return new external_single_structure([
            'found' => new external_value(PARAM_BOOL, 'Whether the external work was found and visible'),
            'externalwork' => self::external_work_structure(),
            'permissions' => self::permissions_structure(),
            'warnings' => self::warnings_structure(),
        ]);
    }

    /**
     * Return external work structure.
     *
     * @return external_single_structure
     */
    private static function external_work_structure(): external_single_structure {
        return new external_single_structure([
            'id' => new external_value(PARAM_INT, 'External work id'),
            'uuid' => new external_value(PARAM_TEXT, 'Stable external work UUID'),
            'archiveid' => new external_value(PARAM_INT, 'Archive instance id'),
            'courseid' => new external_value(PARAM_INT, 'Course id'),
            'cmid' => new external_value(PARAM_INT, 'Course module id'),
            'contextid' => new external_value(PARAM_INT, 'Context id'),
            'ownerid' => new external_value(PARAM_INT, 'Owner user id'),
            'createdby' => new external_value(PARAM_INT, 'Creator user id'),
            'modifiedby' => new external_value(PARAM_INT, 'Modifier user id'),
            'worktype' => new external_value(PARAM_ALPHANUMEXT, 'External work type'),
            'status' => new external_value(PARAM_ALPHANUMEXT, 'External work status'),
            'visibility' => new external_value(PARAM_ALPHANUMEXT, 'External work visibility'),
            'audiencesuitability' => new external_value(PARAM_ALPHANUMEXT, 'Audience suitability'),
            'rightsstatus' => new external_value(PARAM_ALPHANUMEXT, 'Rights status'),
            'title' => new external_value(PARAM_TEXT, 'Title'),
            'subtitle' => new external_value(PARAM_TEXT, 'Subtitle'),
            'creator' => new external_value(PARAM_TEXT, 'Creator'),
            'publisher' => new external_value(PARAM_TEXT, 'Publisher'),
            'publicationyear' => new external_value(PARAM_INT, 'Publication year'),
            'language' => new external_value(PARAM_ALPHANUMEXT, 'Language code'),
            'sourceurl' => new external_value(PARAM_URL, 'Source URL', VALUE_OPTIONAL),
            'identifier' => new external_value(PARAM_TEXT, 'Identifier'),
            'identifiertype' => new external_value(PARAM_ALPHANUMEXT, 'Identifier type'),
            'citation' => new external_value(PARAM_RAW, 'Citation'),
            'rightsstatement' => new external_value(PARAM_RAW, 'Rights statement'),
            'licensekey' => new external_value(PARAM_ALPHANUMEXT, 'License key'),
            'sourcenote' => new external_value(PARAM_RAW, 'Source note'),
            'teachingnote' => new external_value(PARAM_RAW, 'Teaching note'),
            'culturalprotocolnote' => new external_value(PARAM_RAW, 'Cultural protocol note'),
            'description' => new external_value(PARAM_RAW, 'Description'),
            'provenanceid' => new external_value(PARAM_INT, 'Provenance id'),
            'metadatajson' => new external_value(PARAM_RAW, 'Metadata JSON'),
            'timecreated' => new external_value(PARAM_INT, 'Created timestamp'),
            'timemodified' => new external_value(PARAM_INT, 'Modified timestamp'),
            'isrestricted' => new external_value(PARAM_BOOL, 'Whether the work is restricted'),
            'isculturallyrestricted' => new external_value(PARAM_BOOL, 'Whether the work is culturally restricted'),
            'canviewfull' => new external_value(PARAM_BOOL, 'Whether full details are visible to the current user'),
        ]);
    }

    /**
     * Return permissions response structure.
     *
     * @return external_single_structure
     */
    private static function permissions_structure(): external_single_structure {
        return new external_single_structure([
            'viewmedia' => new external_value(PARAM_BOOL, 'Can view media/library records'),
            'manageexternalworks' => new external_value(PARAM_BOOL, 'Can manage external works'),
            'viewrestrictedmedia' => new external_value(PARAM_BOOL, 'Can view restricted media'),
            'viewrestricted' => new external_value(PARAM_BOOL, 'Can view restricted archive material'),
            'viewculturallyrestricted' => new external_value(PARAM_BOOL, 'Can view culturally restricted material'),
        ]);
    }

    /**
     * Return warnings response structure.
     *
     * @return external_multiple_structure
     */
    private static function warnings_structure(): external_multiple_structure {
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
     * Load Moodle page context.
     *
     * @param int $cmid Course module id.
     * @return array{0:stdClass,1:stdClass,2:stdClass,3:context_module}
     */
    private static function load_page(int $cmid): array {
        [$course, $cm, $archive, $context] = \uckkarchive_require_page($cmid, 0);
        return [$course, $cm, $archive, $context];
    }

    /**
     * Require ordinary base capability.
     *
     * @param context_module $context Module context.
     * @return void
     */
    private static function require_base_capability(context_module $context): void {
        if (has_capability(self::CAP_VIEW_MEDIA, $context) ||
                has_capability(self::CAP_MANAGE_EXTERNAL_WORKS, $context)) {
            return;
        }

        require_capability(self::CAP_VIEW_MEDIA, $context);
    }

    /**
     * Load external work by id or UUID.
     *
     * @param int $id External work id.
     * @param string $uuid External work UUID.
     * @return stdClass|null
     */
    private static function load_external_work(int $id, string $uuid): ?stdClass {
        if ($id > 0) {
            return external_work::get($id, IGNORE_MISSING);
        }

        return external_work::get_by_uuid($uuid, IGNORE_MISSING);
    }

    /**
     * Return whether the external work belongs to the active archive instance.
     *
     * @param stdClass $work External work record.
     * @param int $archiveid Archive id.
     * @return bool
     */
    private static function belongs_to_archive(stdClass $work, int $archiveid): bool {
        $workarchiveid = (int)self::field($work, ['archiveid', 'uckkarchiveid'], 0);

        return $workarchiveid === 0 || $archiveid === 0 || $workarchiveid === $archiveid;
    }

    /**
     * Return whether current user may view this external work.
     *
     * @param stdClass $work External work record.
     * @param context_module $context Module context.
     * @return bool
     */
    private static function can_view_external_work(stdClass $work, context_module $context): bool {
        global $USER;

        if (has_capability(self::CAP_MANAGE_EXTERNAL_WORKS, $context)) {
            return true;
        }

        $status = (string)self::field($work, ['status'], '');
        if ($status === 'deleted_soft') {
            return false;
        }

        $visibility = (string)self::field($work, ['visibility'], 'restricted');

        if ($visibility === 'private') {
            $ownerid = (int)self::field($work, ['ownerid', 'createdby'], 0);
            return $ownerid > 0 && $ownerid === (int)$USER->id;
        }

        if (self::is_restricted($work)) {
            return self::can_view_restricted($work, $context);
        }

        return has_capability(self::CAP_VIEW_MEDIA, $context);
    }

    /**
     * Return whether full sensitive details can be shown.
     *
     * @param stdClass $work External work record.
     * @param context_module $context Module context.
     * @return bool
     */
    private static function can_view_full(stdClass $work, context_module $context): bool {
        if (has_capability(self::CAP_MANAGE_EXTERNAL_WORKS, $context)) {
            return true;
        }

        if (!self::is_restricted($work)) {
            return has_capability(self::CAP_VIEW_MEDIA, $context);
        }

        return self::can_view_restricted($work, $context);
    }

    /**
     * Return whether restricted access is granted.
     *
     * @param stdClass $work External work record.
     * @param context_module $context Module context.
     * @return bool
     */
    private static function can_view_restricted(stdClass $work, context_module $context): bool {
        if (self::is_culturally_restricted($work)) {
            return has_capability(self::CAP_VIEW_CULTURALLY_RESTRICTED, $context);
        }

        return has_capability(self::CAP_VIEW_RESTRICTED_MEDIA, $context) ||
            has_capability(self::CAP_VIEW_RESTRICTED_ARCHIVE, $context);
    }

    /**
     * Export external work record for service response.
     *
     * @param stdClass $work External work record.
     * @param context_module $context Module context.
     * @return array<string, mixed>
     */
    private static function export_external_work(stdClass $work, context_module $context): array {
        $export = external_work::export_record($work);
        $canviewfull = self::can_view_full($work, $context);

        if (!$canviewfull) {
            $export['sourcenote'] = '';
            $export['teachingnote'] = '';
            $export['culturalprotocolnote'] = '';
            $export['rightsstatement'] = '';
            $export['description'] = '';
            $export['metadata'] = [];
        }

        $sourceurl = clean_param((string)($export['sourceurl'] ?? ''), PARAM_URL);

        $response = [
            'id' => (int)($export['id'] ?? 0),
            'uuid' => (string)($export['uuid'] ?? ''),
            'archiveid' => (int)($export['archiveid'] ?? 0),
            'courseid' => (int)($export['courseid'] ?? 0),
            'cmid' => (int)($export['cmid'] ?? 0),
            'contextid' => (int)($export['contextid'] ?? 0),
            'ownerid' => (int)($export['ownerid'] ?? 0),
            'createdby' => (int)($export['createdby'] ?? 0),
            'modifiedby' => (int)($export['modifiedby'] ?? 0),
            'worktype' => (string)($export['worktype'] ?? ''),
            'status' => (string)($export['status'] ?? ''),
            'visibility' => (string)($export['visibility'] ?? ''),
            'audiencesuitability' => (string)($export['audiencesuitability'] ?? ''),
            'rightsstatus' => (string)($export['rightsstatus'] ?? ''),
            'title' => format_string((string)($export['title'] ?? '')),
            'subtitle' => format_string((string)($export['subtitle'] ?? '')),
            'creator' => format_string((string)($export['creator'] ?? '')),
            'publisher' => format_string((string)($export['publisher'] ?? '')),
            'publicationyear' => (int)($export['publicationyear'] ?? 0),
            'language' => clean_param((string)($export['language'] ?? ''), PARAM_ALPHANUMEXT),
            'identifier' => (string)($export['identifier'] ?? ''),
            'identifiertype' => (string)($export['identifiertype'] ?? ''),
            'citation' => self::format_raw((string)($export['citation'] ?? '')),
            'rightsstatement' => self::format_raw((string)($export['rightsstatement'] ?? '')),
            'licensekey' => (string)($export['licensekey'] ?? ''),
            'sourcenote' => self::format_raw((string)($export['sourcenote'] ?? '')),
            'teachingnote' => self::format_raw((string)($export['teachingnote'] ?? '')),
            'culturalprotocolnote' => self::format_raw((string)($export['culturalprotocolnote'] ?? '')),
            'description' => self::format_raw((string)($export['description'] ?? '')),
            'provenanceid' => (int)($export['provenanceid'] ?? 0),
            'metadatajson' => self::encode_json($export['metadata'] ?? []),
            'timecreated' => (int)($export['timecreated'] ?? 0),
            'timemodified' => (int)($export['timemodified'] ?? 0),
            'isrestricted' => self::is_restricted($work),
            'isculturallyrestricted' => self::is_culturally_restricted($work),
            'canviewfull' => $canviewfull,
        ];

        if ($sourceurl !== '') {
            $response['sourceurl'] = $sourceurl;
        }

        return $response;
    }

    /**
     * Return an empty external work response.
     *
     * @return array<string, mixed>
     */
    private static function empty_external_work(): array {
        return [
            'id' => 0,
            'uuid' => '',
            'archiveid' => 0,
            'courseid' => 0,
            'cmid' => 0,
            'contextid' => 0,
            'ownerid' => 0,
            'createdby' => 0,
            'modifiedby' => 0,
            'worktype' => '',
            'status' => '',
            'visibility' => '',
            'audiencesuitability' => '',
            'rightsstatus' => '',
            'title' => '',
            'subtitle' => '',
            'creator' => '',
            'publisher' => '',
            'publicationyear' => 0,
            'language' => '',
            'identifier' => '',
            'identifiertype' => '',
            'citation' => '',
            'rightsstatement' => '',
            'licensekey' => '',
            'sourcenote' => '',
            'teachingnote' => '',
            'culturalprotocolnote' => '',
            'description' => '',
            'provenanceid' => 0,
            'metadatajson' => '{}',
            'timecreated' => 0,
            'timemodified' => 0,
            'isrestricted' => false,
            'isculturallyrestricted' => false,
            'canviewfull' => false,
        ];
    }

    /**
     * Return not found response.
     *
     * @param array<string, bool> $permissions Permissions.
     * @param array<string, mixed> $warning Warning.
     * @return array<string, mixed>
     */
    private static function not_found_response(array $permissions, array $warning): array {
        return [
            'found' => false,
            'externalwork' => self::empty_external_work(),
            'permissions' => $permissions,
            'warnings' => [$warning],
        ];
    }

    /**
     * Return permissions payload.
     *
     * @param context_module $context Module context.
     * @return array<string, bool>
     */
    private static function get_permissions(context_module $context): array {
        return [
            'viewmedia' => has_capability(self::CAP_VIEW_MEDIA, $context),
            'manageexternalworks' => has_capability(self::CAP_MANAGE_EXTERNAL_WORKS, $context),
            'viewrestrictedmedia' => has_capability(self::CAP_VIEW_RESTRICTED_MEDIA, $context),
            'viewrestricted' => has_capability(self::CAP_VIEW_RESTRICTED_ARCHIVE, $context),
            'viewculturallyrestricted' => has_capability(self::CAP_VIEW_CULTURALLY_RESTRICTED, $context),
        ];
    }

    /**
     * Build warning payload.
     *
     * @param string $item Warning item.
     * @param int $itemid Warning item id.
     * @param string $code Warning code.
     * @param string $message Warning message.
     * @return array<string, mixed>
     */
    private static function warning(string $item, int $itemid, string $code, string $message): array {
        return [
            'item' => $item,
            'itemid' => $itemid,
            'warningcode' => clean_param($code, PARAM_ALPHANUMEXT),
            'message' => $message,
        ];
    }

    /**
     * Return whether external work is restricted.
     *
     * @param stdClass $work External work.
     * @return bool
     */
    private static function is_restricted(stdClass $work): bool {
        $status = (string)self::field($work, ['status'], '');
        $visibility = (string)self::field($work, ['visibility'], '');

        return in_array($status, ['restricted'], true) ||
            in_array($visibility, ['restricted', 'restricted_integrity', 'restricted_cultural'], true);
    }

    /**
     * Return whether external work is culturally restricted.
     *
     * @param stdClass $work External work.
     * @return bool
     */
    private static function is_culturally_restricted(stdClass $work): bool {
        $visibility = (string)self::field($work, ['visibility'], '');

        return $visibility === 'restricted_cultural' || !empty($work->culturalprotocol);
    }

    /**
     * Return field value from record.
     *
     * @param stdClass $record Record.
     * @param string[] $fields Candidate fields.
     * @param mixed $default Default value.
     * @return mixed
     */
    private static function field(stdClass $record, array $fields, mixed $default = null): mixed {
        foreach ($fields as $field) {
            if (property_exists($record, $field) && $record->{$field} !== null && $record->{$field} !== '') {
                return $record->{$field};
            }
        }

        return $default;
    }

    /**
     * Normalize include values.
     *
     * @param string[] $include Include values.
     * @return string[]
     */
    private static function normalise_include(array $include): array {
        $allowed = ['permissions'];
        $clean = [];

        foreach ($include as $value) {
            $value = clean_param((string)$value, PARAM_ALPHANUMEXT);
            if (in_array($value, $allowed, true)) {
                $clean[] = $value;
            }
        }

        return array_values(array_unique($clean));
    }

    /**
     * Return whether table exists.
     *
     * @param string $tablename Table name.
     * @return bool
     */
    private static function table_exists(string $tablename): bool {
        global $DB;

        return $DB->get_manager()->table_exists(new \xmldb_table($tablename));
    }

    /**
     * Encode JSON safely for external return.
     *
     * @param mixed $data Data.
     * @return string
     */
    private static function encode_json(mixed $data): string {
        if (!is_array($data)) {
            $data = [];
        }

        $json = json_encode($data, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);

        return $json === false ? '{}' : $json;
    }

    /**
     * Format raw long text as HTML-safe Moodle text.
     *
     * @param string $text Text.
     * @return string
     */
    private static function format_raw(string $text): string {
        return format_text($text, FORMAT_HTML, ['para' => false, 'trusted' => false]);
    }
}
