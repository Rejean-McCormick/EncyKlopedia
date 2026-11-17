<?php
// This file is part of Moodle - https://moodle.org/
//
// Moodle is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// any later version.

/**
 * Update an external work reference.
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
require_once(dirname(__DIR__) . '/local/context_resolver.php');
require_once(dirname(__DIR__) . '/local/external_work.php');

use context_module;
use core_external\external_api;
use core_external\external_function_parameters;
use core_external\external_single_structure;
use core_external\external_multiple_structure;
use core_external\external_value;
use invalid_parameter_exception;
use mod_uckkarchive\local\context_resolver;
use mod_uckkarchive\local\external_work;
use moodle_exception;
use stdClass;

/**
 * External service: update an existing external work reference.
 *
 * Target service:
 *
 * ```text
 * mod_uckkarchive_update_external_work
 * ```
 *
 * External works are archive-owned references to outside material such as
 * books, films, articles, public web resources, external videos, external
 * images, or third-party PDFs. They are used by content advisory markers and
 * media source/provenance records.
 */
final class update_external_work extends external_api {
    /** External work table. */
    private const TABLE = 'uckkarchive_external_work';

    /**
     * Service parameters.
     *
     * @return external_function_parameters
     */
    public static function execute_parameters(): external_function_parameters {
        return new external_function_parameters([
            'cmid' => new external_value(PARAM_INT, 'Course module id', VALUE_DEFAULT, 0),
            'externalworkid' => new external_value(PARAM_INT, 'External work id', VALUE_DEFAULT, 0),
            'externalworkuuid' => new external_value(PARAM_TEXT, 'External work UUID', VALUE_DEFAULT, ''),
            'updates' => new external_single_structure([
                'worktype' => new external_value(PARAM_ALPHANUMEXT, 'External work type', VALUE_OPTIONAL),
                'status' => new external_value(PARAM_ALPHANUMEXT, 'External work lifecycle status', VALUE_OPTIONAL),
                'visibility' => new external_value(PARAM_ALPHANUMEXT, 'Visibility', VALUE_OPTIONAL),
                'audiencesuitability' => new external_value(PARAM_ALPHANUMEXT, 'Audience suitability', VALUE_OPTIONAL),
                'rightsstatus' => new external_value(PARAM_ALPHANUMEXT, 'Rights status', VALUE_OPTIONAL),
                'title' => new external_value(PARAM_TEXT, 'Title', VALUE_OPTIONAL),
                'subtitle' => new external_value(PARAM_TEXT, 'Subtitle', VALUE_OPTIONAL),
                'creator' => new external_value(PARAM_TEXT, 'Creator/author/director', VALUE_OPTIONAL),
                'publisher' => new external_value(PARAM_TEXT, 'Publisher/distributor', VALUE_OPTIONAL),
                'publicationyear' => new external_value(PARAM_INT, 'Publication year', VALUE_OPTIONAL),
                'language' => new external_value(PARAM_ALPHANUMEXT, 'Language code', VALUE_OPTIONAL),
                'sourceurl' => new external_value(PARAM_URL, 'Source URL', VALUE_OPTIONAL),
                'identifier' => new external_value(PARAM_TEXT, 'External identifier', VALUE_OPTIONAL),
                'identifiertype' => new external_value(PARAM_ALPHANUMEXT, 'Identifier type', VALUE_OPTIONAL),
                'citation' => new external_value(PARAM_RAW, 'Citation', VALUE_OPTIONAL),
                'rightsstatement' => new external_value(PARAM_RAW, 'Rights statement', VALUE_OPTIONAL),
                'licensekey' => new external_value(PARAM_TEXT, 'License key', VALUE_OPTIONAL),
                'sourcenote' => new external_value(PARAM_RAW, 'Source note', VALUE_OPTIONAL),
                'teachingnote' => new external_value(PARAM_RAW, 'Teaching note', VALUE_OPTIONAL),
                'culturalprotocolnote' => new external_value(PARAM_RAW, 'Cultural protocol note', VALUE_OPTIONAL),
                'description' => new external_value(PARAM_RAW, 'Description', VALUE_OPTIONAL),
                'provenanceid' => new external_value(PARAM_INT, 'Provenance id', VALUE_OPTIONAL),
                'metadata' => new external_value(PARAM_RAW, 'Metadata JSON object', VALUE_OPTIONAL),
            ], 'Fields to update', VALUE_DEFAULT, []),
            'reason' => new external_value(PARAM_RAW, 'Reason for update', VALUE_DEFAULT, ''),
        ]);
    }

    /**
     * Execute update.
     *
     * @param int $cmid Course module id.
     * @param int $externalworkid External work id.
     * @param string $externalworkuuid External work UUID.
     * @param array<string, mixed> $updates Update fields.
     * @param string $reason Update reason.
     * @return array<string, mixed>
     */
    public static function execute(
        int $cmid = 0,
        int $externalworkid = 0,
        string $externalworkuuid = '',
        array $updates = [],
        string $reason = ''
    ): array {
        global $USER;

        $params = self::validate_parameters(self::execute_parameters(), [
            'cmid' => $cmid,
            'externalworkid' => $externalworkid,
            'externalworkuuid' => $externalworkuuid,
            'updates' => $updates,
            'reason' => $reason,
        ]);

        self::require_table();

        $work = self::load_external_work((int)$params['externalworkid'], (string)$params['externalworkuuid']);
        $resolution = self::resolve_context((int)$params['cmid'], $work);

        self::validate_context($resolution->context);
        context_resolver::require_login_for($resolution);

        self::require_update_permission($resolution, $work);

        $update = self::build_update_payload($params['updates'], (string)$params['reason']);
        if (empty($update)) {
            return self::response($work, $resolution, [], 'unchanged');
        }

        self::require_restricted_permission_for_update($resolution, $work, $update);

        $changedfields = self::changed_fields($work, $update);

        if (empty($changedfields)) {
            return self::response($work, $resolution, [], 'unchanged');
        }

        $updated = external_work::update((int)$work->id, $update, (int)$USER->id);

        self::trigger_updated_event($updated, $resolution, $changedfields, (string)$params['reason']);

        return self::response($updated, $resolution, $changedfields, 'updated');
    }

    /**
     * Return service structure.
     *
     * @return external_single_structure
     */
    public static function execute_returns(): external_single_structure {
        return new external_single_structure([
            'status' => new external_value(PARAM_ALPHANUMEXT, 'Operation status'),
            'externalworkid' => new external_value(PARAM_INT, 'External work id'),
            'externalworkuuid' => new external_value(PARAM_TEXT, 'External work UUID'),
            'archiveid' => new external_value(PARAM_INT, 'Archive instance id'),
            'cmid' => new external_value(PARAM_INT, 'Course module id'),
            'record' => self::external_work_record_returns(),
            'permissions' => self::permissions_returns(),
            'changedfields' => new external_multiple_structure(
                new external_value(PARAM_ALPHANUMEXT, 'Changed field')
            ),
            'warnings' => self::warnings_returns(),
        ]);
    }

    /**
     * External work return structure.
     *
     * @return external_single_structure
     */
    private static function external_work_record_returns(): external_single_structure {
        return new external_single_structure([
            'id' => new external_value(PARAM_INT, 'External work id'),
            'uuid' => new external_value(PARAM_TEXT, 'External work UUID'),
            'archiveid' => new external_value(PARAM_INT, 'Archive instance id'),
            'courseid' => new external_value(PARAM_INT, 'Course id'),
            'cmid' => new external_value(PARAM_INT, 'Course module id'),
            'contextid' => new external_value(PARAM_INT, 'Context id'),
            'ownerid' => new external_value(PARAM_INT, 'Owner user id'),
            'createdby' => new external_value(PARAM_INT, 'Creator user id'),
            'modifiedby' => new external_value(PARAM_INT, 'Modifier user id'),
            'worktype' => new external_value(PARAM_ALPHANUMEXT, 'Work type'),
            'status' => new external_value(PARAM_ALPHANUMEXT, 'Status'),
            'visibility' => new external_value(PARAM_ALPHANUMEXT, 'Visibility'),
            'audiencesuitability' => new external_value(PARAM_ALPHANUMEXT, 'Audience suitability'),
            'rightsstatus' => new external_value(PARAM_ALPHANUMEXT, 'Rights status'),
            'title' => new external_value(PARAM_TEXT, 'Title'),
            'subtitle' => new external_value(PARAM_TEXT, 'Subtitle'),
            'creator' => new external_value(PARAM_TEXT, 'Creator'),
            'publisher' => new external_value(PARAM_TEXT, 'Publisher'),
            'publicationyear' => new external_value(PARAM_INT, 'Publication year'),
            'language' => new external_value(PARAM_ALPHANUMEXT, 'Language'),
            'sourceurl' => new external_value(PARAM_URL, 'Source URL'),
            'identifier' => new external_value(PARAM_TEXT, 'Identifier'),
            'identifiertype' => new external_value(PARAM_ALPHANUMEXT, 'Identifier type'),
            'citation' => new external_value(PARAM_RAW, 'Citation'),
            'rightsstatement' => new external_value(PARAM_RAW, 'Rights statement'),
            'licensekey' => new external_value(PARAM_TEXT, 'License key'),
            'sourcenote' => new external_value(PARAM_RAW, 'Source note'),
            'teachingnote' => new external_value(PARAM_RAW, 'Teaching note'),
            'culturalprotocolnote' => new external_value(PARAM_RAW, 'Cultural protocol note'),
            'description' => new external_value(PARAM_RAW, 'Description'),
            'provenanceid' => new external_value(PARAM_INT, 'Provenance id'),
            'metadata' => new external_value(PARAM_RAW, 'Metadata JSON'),
            'timecreated' => new external_value(PARAM_INT, 'Created time'),
            'timemodified' => new external_value(PARAM_INT, 'Modified time'),
        ]);
    }

    /**
     * Permissions return structure.
     *
     * @return external_single_structure
     */
    private static function permissions_returns(): external_single_structure {
        return new external_single_structure([
            'canview' => new external_value(PARAM_BOOL, 'Can view external work'),
            'canupdate' => new external_value(PARAM_BOOL, 'Can update external work'),
            'canmanageadvisories' => new external_value(PARAM_BOOL, 'Can manage content advisories'),
            'canviewrestricted' => new external_value(PARAM_BOOL, 'Can view restricted archive data'),
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
                'item' => new external_value(PARAM_TEXT, 'Warning item'),
                'itemid' => new external_value(PARAM_INT, 'Warning item id'),
                'warningcode' => new external_value(PARAM_ALPHANUMEXT, 'Warning code'),
                'message' => new external_value(PARAM_TEXT, 'Warning message'),
            ])
        );
    }

    /**
     * Load external work by id or UUID.
     *
     * @param int $externalworkid External work id.
     * @param string $externalworkuuid External work UUID.
     * @return stdClass
     */
    private static function load_external_work(int $externalworkid, string $externalworkuuid): stdClass {
        $externalworkid = max(0, $externalworkid);
        $externalworkuuid = trim($externalworkuuid);

        if ($externalworkid > 0) {
            return external_work::get_record($externalworkid, MUST_EXIST);
        }

        if ($externalworkuuid !== '') {
            return external_work::get_record_by_uuid($externalworkuuid, MUST_EXIST);
        }

        throw new invalid_parameter_exception('Either externalworkid or externalworkuuid is required.');
    }

    /**
     * Resolve context from cmid or existing external work.
     *
     * @param int $cmid Course module id.
     * @param stdClass $work External work record.
     * @return stdClass
     */
    private static function resolve_context(int $cmid, stdClass $work): stdClass {
        if ($cmid > 0) {
            $resolution = context_resolver::from_cmid($cmid);

            $archiveid = (int)($work->archiveid ?? 0);
            if ($archiveid > 0 && (int)$resolution->archive->id !== $archiveid) {
                throw new invalid_parameter_exception('External work does not belong to the supplied course module.');
            }

            return $resolution;
        }

        return context_resolver::from_external_work((int)$work->id);
    }

    /**
     * Build update payload from validated params.
     *
     * @param array<string, mixed> $updates Raw update fields.
     * @param string $reason Update reason.
     * @return array<string, mixed>
     */
    private static function build_update_payload(array $updates, string $reason): array {
        $payload = [];

        foreach (self::updatable_fields() as $field => $type) {
            if (!array_key_exists($field, $updates)) {
                continue;
            }

            $value = $updates[$field];

            switch ($type) {
                case 'int':
                    $payload[$field] = (int)$value;
                    break;

                case 'year':
                    $payload[$field] = self::normalise_year((int)$value);
                    break;

                case 'url':
                    $payload[$field] = self::normalise_url((string)$value);
                    break;

                case 'json':
                    $payload[$field] = self::decode_json_metadata((string)$value);
                    break;

                case 'raw':
                    $payload[$field] = self::normalise_raw((string)$value);
                    break;

                case 'text':
                default:
                    $payload[$field] = self::normalise_text((string)$value);
                    break;
            }
        }

        $reason = self::normalise_raw($reason);
        if ($reason !== '') {
            $metadata = [];
            if (isset($payload['metadata']) && is_array($payload['metadata'])) {
                $metadata = $payload['metadata'];
            }

            $metadata['last_update_reason'] = $reason;
            $payload['metadata'] = $metadata;
        }

        return $payload;
    }

    /**
     * Return updatable fields and their normalization type.
     *
     * @return array<string, string>
     */
    private static function updatable_fields(): array {
        return [
            'worktype' => 'text',
            'status' => 'text',
            'visibility' => 'text',
            'audiencesuitability' => 'text',
            'rightsstatus' => 'text',
            'title' => 'text',
            'subtitle' => 'text',
            'creator' => 'text',
            'publisher' => 'text',
            'publicationyear' => 'year',
            'language' => 'text',
            'sourceurl' => 'url',
            'identifier' => 'text',
            'identifiertype' => 'text',
            'citation' => 'raw',
            'rightsstatement' => 'raw',
            'licensekey' => 'text',
            'sourcenote' => 'raw',
            'teachingnote' => 'raw',
            'culturalprotocolnote' => 'raw',
            'description' => 'raw',
            'provenanceid' => 'int',
            'metadata' => 'json',
        ];
    }

    /**
     * Require permission to update external work.
     *
     * @param stdClass $resolution Context resolution.
     * @param stdClass $work External work.
     * @return void
     */
    private static function require_update_permission(stdClass $resolution, stdClass $work): void {
        if (self::can_update($resolution, $work)) {
            return;
        }

        throw new moodle_exception('nopermissions', 'error', '', 'update external work');
    }

    /**
     * Require restricted authority if update creates/keeps restricted state.
     *
     * @param stdClass $resolution Context resolution.
     * @param stdClass $work Existing work.
     * @param array<string, mixed> $update Update payload.
     * @return void
     */
    private static function require_restricted_permission_for_update(stdClass $resolution, stdClass $work, array $update): void {
        $visibility = (string)($update['visibility'] ?? ($work->visibility ?? ''));
        $status = (string)($update['status'] ?? ($work->status ?? ''));
        $suitability = (string)($update['audiencesuitability'] ?? ($work->audiencesuitability ?? ''));

        $restricted = in_array($visibility, ['restricted', 'restricted_integrity', 'restricted_cultural'], true) ||
            $status === 'restricted' ||
            in_array($suitability, ['restricted', 'restricted_integrity', 'restricted_cultural', 'staff_only'], true);

        if (!$restricted) {
            return;
        }

        if (self::has_any_capability($resolution->context, [
            'mod/uckkarchive:viewrestricted',
            'mod/uckkarchive:viewrestrictedmedia',
            'mod/uckkarchive:manageadvisories',
            'mod/uckkarchive:managecontentadvisories',
        ])) {
            return;
        }

        throw new moodle_exception('nopermissions', 'error', '', 'restricted external work update');
    }

    /**
     * Return whether current user can update this work.
     *
     * @param stdClass $resolution Context resolution.
     * @param stdClass $work External work.
     * @return bool
     */
    private static function can_update(stdClass $resolution, stdClass $work): bool {
        if (self::has_any_capability($resolution->context, [
            'mod/uckkarchive:manageadvisories',
            'mod/uckkarchive:managecontentadvisories',
            'mod/uckkarchive:editmedia',
            'mod/uckkarchive:addmedia',
            'mod/uckkarchive:validateitem',
        ])) {
            return true;
        }

        return false;
    }

    /**
     * Return response.
     *
     * @param stdClass $work External work.
     * @param stdClass $resolution Context resolution.
     * @param string[] $changedfields Changed fields.
     * @param string $status Operation status.
     * @return array<string, mixed>
     */
    private static function response(stdClass $work, stdClass $resolution, array $changedfields, string $status): array {
        return [
            'status' => $status,
            'externalworkid' => (int)$work->id,
            'externalworkuuid' => (string)($work->uuid ?? ''),
            'archiveid' => (int)$resolution->archive->id,
            'cmid' => (int)$resolution->cm->id,
            'record' => self::export_record($work),
            'permissions' => [
                'canview' => self::can_view($resolution, $work),
                'canupdate' => self::can_update($resolution, $work),
                'canmanageadvisories' => self::has_any_capability($resolution->context, [
                    'mod/uckkarchive:manageadvisories',
                    'mod/uckkarchive:managecontentadvisories',
                ]),
                'canviewrestricted' => self::has_any_capability($resolution->context, [
                    'mod/uckkarchive:viewrestricted',
                    'mod/uckkarchive:viewrestrictedmedia',
                ]),
            ],
            'changedfields' => array_values($changedfields),
            'warnings' => [],
        ];
    }

    /**
     * Export work record to external response.
     *
     * @param stdClass $work External work.
     * @return array<string, mixed>
     */
    private static function export_record(stdClass $work): array {
        $record = external_work::export_record($work);

        $record['metadata'] = self::encode_json($record['metadata'] ?? []);

        foreach ([
            'id',
            'archiveid',
            'courseid',
            'cmid',
            'contextid',
            'ownerid',
            'createdby',
            'modifiedby',
            'publicationyear',
            'provenanceid',
            'timecreated',
            'timemodified',
        ] as $field) {
            $record[$field] = (int)($record[$field] ?? 0);
        }

        foreach ([
            'uuid',
            'worktype',
            'status',
            'visibility',
            'audiencesuitability',
            'rightsstatus',
            'title',
            'subtitle',
            'creator',
            'publisher',
            'language',
            'sourceurl',
            'identifier',
            'identifiertype',
            'citation',
            'rightsstatement',
            'licensekey',
            'sourcenote',
            'teachingnote',
            'culturalprotocolnote',
            'description',
            'metadata',
        ] as $field) {
            $record[$field] = (string)($record[$field] ?? '');
        }

        return $record;
    }

    /**
     * Return changed fields.
     *
     * @param stdClass $current Current record.
     * @param array<string, mixed> $update Update payload.
     * @return string[]
     */
    private static function changed_fields(stdClass $current, array $update): array {
        $changed = [];

        foreach ($update as $field => $value) {
            $old = $current->{$field} ?? null;

            if ($field === 'metadata') {
                $old = self::decode_existing_metadata($old);
                if (self::encode_json($old) !== self::encode_json($value)) {
                    $changed[] = $field;
                }
                continue;
            }

            if ((string)$old !== (string)$value) {
                $changed[] = $field;
            }
        }

        return $changed;
    }

    /**
     * Return whether current user can view the work.
     *
     * @param stdClass $resolution Context resolution.
     * @param stdClass $work External work.
     * @return bool
     */
    private static function can_view(stdClass $resolution, stdClass $work): bool {
        $visibility = (string)($work->visibility ?? '');
        $status = (string)($work->status ?? '');

        if ($status === 'deleted_soft') {
            return self::can_update($resolution, $work);
        }

        if (in_array($visibility, ['restricted', 'restricted_integrity', 'restricted_cultural'], true) ||
                $status === 'restricted') {
            return self::has_any_capability($resolution->context, [
                'mod/uckkarchive:viewrestricted',
                'mod/uckkarchive:viewrestrictedmedia',
                'mod/uckkarchive:viewculturallyrestricted',
                'mod/uckkarchive:manageadvisories',
                'mod/uckkarchive:managecontentadvisories',
            ]);
        }

        return self::has_any_capability($resolution->context, [
            'mod/uckkarchive:view',
            'mod/uckkarchive:viewmedia',
        ]);
    }

    /**
     * Trigger updated event when available.
     *
     * @param stdClass $work Updated work.
     * @param stdClass $resolution Context resolution.
     * @param string[] $changedfields Changed fields.
     * @param string $reason Update reason.
     * @return void
     */
    private static function trigger_updated_event(
        stdClass $work,
        stdClass $resolution,
        array $changedfields,
        string $reason
    ): void {
        $eventclass = '\\mod_uckkarchive\\event\\external_work_created';

        if (!class_exists($eventclass)) {
            return;
        }

        try {
            $event = $eventclass::create([
                'objectid' => (int)$work->id,
                'context' => $resolution->context,
                'other' => [
                    'archiveid' => (int)$resolution->archive->id,
                    'courseid' => (int)$resolution->course->id,
                    'cmid' => (int)$resolution->cm->id,
                    'uuid' => (string)($work->uuid ?? ''),
                    'action' => 'updated',
                    'changedfields' => implode(',', $changedfields),
                    'reason' => self::normalise_raw($reason),
                ],
            ]);
            $event->trigger();
        } catch (\Throwable $ignored) {
            // External work persistence must not fail because event code is not ready.
        }
    }

    /**
     * Return whether user has any known capability.
     *
     * Unknown capabilities are ignored so the service remains installable while
     * db/access.php is being expanded.
     *
     * @param context_module $context Context.
     * @param string[] $capabilities Capabilities.
     * @return bool
     */
    private static function has_any_capability(context_module $context, array $capabilities): bool {
        foreach ($capabilities as $capability) {
            if (function_exists('get_capability_info') && !get_capability_info($capability)) {
                continue;
            }

            if (has_capability($capability, $context)) {
                return true;
            }
        }

        return false;
    }

    /**
     * Decode raw metadata.
     *
     * @param string $metadata Metadata JSON.
     * @return array<string, mixed>
     */
    private static function decode_json_metadata(string $metadata): array {
        $metadata = trim($metadata);
        if ($metadata === '') {
            return [];
        }

        $decoded = json_decode($metadata, true);
        if (!is_array($decoded)) {
            throw new invalid_parameter_exception('metadata must be a valid JSON object.');
        }

        return $decoded;
    }

    /**
     * Decode existing metadata from db/domain form.
     *
     * @param mixed $metadata Metadata.
     * @return array<string, mixed>
     */
    private static function decode_existing_metadata(mixed $metadata): array {
        if (is_array($metadata)) {
            return $metadata;
        }

        if ($metadata instanceof stdClass) {
            return (array)$metadata;
        }

        if (is_string($metadata) && trim($metadata) !== '') {
            $decoded = json_decode($metadata, true);
            return is_array($decoded) ? $decoded : [];
        }

        return [];
    }

    /**
     * Encode JSON.
     *
     * @param mixed $data Data.
     * @return string
     */
    private static function encode_json(mixed $data): string {
        $json = json_encode($data, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
        return $json === false ? '{}' : $json;
    }

    /**
     * Normalize text.
     *
     * @param string $text Text.
     * @return string
     */
    private static function normalise_text(string $text): string {
        return clean_param(trim($text), PARAM_TEXT);
    }

    /**
     * Normalize raw text.
     *
     * @param string $text Text.
     * @return string
     */
    private static function normalise_raw(string $text): string {
        return trim(clean_text($text, FORMAT_HTML));
    }

    /**
     * Normalize URL.
     *
     * @param string $url URL.
     * @return string
     */
    private static function normalise_url(string $url): string {
        $url = trim($url);

        if ($url === '') {
            return '';
        }

        return clean_param($url, PARAM_URL);
    }

    /**
     * Normalize publication year.
     *
     * @param int $year Year.
     * @return int
     */
    private static function normalise_year(int $year): int {
        if ($year === 0) {
            return 0;
        }

        if ($year < 0 || $year > 9999) {
            throw new invalid_parameter_exception('publicationyear must be between 0 and 9999.');
        }

        return $year;
    }

    /**
     * Require table.
     *
     * @return void
     * @throws moodle_exception
     */
    private static function require_table(): void {
        global $DB;

        if (!$DB->get_manager()->table_exists(new \xmldb_table(self::TABLE))) {
            throw new moodle_exception('missingtable', 'error', '', self::TABLE);
        }
    }
}
