<?php
// This file is part of Moodle - https://moodle.org/.
//
// Moodle is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// any later version.

/**
 * External service for adding content advisory markers.
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
require_once(dirname(__DIR__) . '/local/content_marker.php');
require_once(dirname(__DIR__) . '/local/content_policy.php');

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
 * Add a content advisory marker to media, archive item, media version,
 * external work, collection, proof, Kristal, or manual reference.
 *
 * Target service name:
 *
 * ```text
 * mod_uckkarchive_add_content_marker
 * ```
 *
 * This endpoint is an authority gate. It resolves Moodle context, checks
 * advisory management capability, normalises advisory metadata, creates marker
 * records through the domain class, and returns permission-filtered data.
 */
final class add_content_marker extends external_api {
    /** Media table. */
    private const TABLE_MEDIA = 'uckkarchive_media';

    /** Media version table. */
    private const TABLE_MEDIA_VERSION = 'uckkarchive_media_version';

    /** Archive item table. */
    private const TABLE_ITEM = 'uckkarchive_item';

    /** External work table. */
    private const TABLE_EXTERNAL_WORK = 'uckkarchive_external_work';

    /** Media collection table. */
    private const TABLE_COLLECTION = 'uckkarchive_media_collection';

    /** Proof table. */
    private const TABLE_PROOF = 'uckkarchive_proof';

    /** Kristal table. */
    private const TABLE_KRISTAL = 'uckkarchive_kristal';

    /**
     * Describe service parameters.
     *
     * @return external_function_parameters
     */
    public static function execute_parameters(): external_function_parameters {
        return new external_function_parameters([
            'cmid' => new external_value(PARAM_INT, 'Course module id for the UCKK Archive instance.'),
            'targettype' => new external_value(
                PARAM_ALPHANUMEXT,
                'Target type: media, media_version, archive_item, proof, kristal, external_work, collection, manual_reference.'
            ),
            'targetid' => new external_value(PARAM_INT, 'Target record id. Optional when targetuuid is provided.', VALUE_DEFAULT, 0),
            'targetuuid' => new external_value(PARAM_RAW_TRIMMED, 'Target UUID. Optional when targetid is provided.', VALUE_DEFAULT, ''),
            'tagkey' => new external_value(PARAM_ALPHANUMEXT, 'Single advisory tag key.', VALUE_DEFAULT, ''),
            'tagkeys' => new external_multiple_structure(
                new external_value(PARAM_ALPHANUMEXT, 'Advisory tag key.'),
                'One or more advisory tag keys.',
                VALUE_DEFAULT,
                []
            ),
            'tagid' => new external_value(PARAM_INT, 'Optional content tag id.', VALUE_DEFAULT, 0),
            'tagsetid' => new external_value(PARAM_INT, 'Optional content tag set id.', VALUE_DEFAULT, 0),
            'tagsetkey' => new external_value(PARAM_ALPHANUMEXT, 'Optional content tag set key.', VALUE_DEFAULT, ''),
            'locatortype' => new external_value(PARAM_ALPHANUMEXT, 'Locator type.', VALUE_DEFAULT, 'manual_reference'),
            'locatorvalue' => new external_value(PARAM_RAW_TRIMMED, 'Locator value.', VALUE_DEFAULT, ''),
            'locatorstart' => new external_value(PARAM_RAW_TRIMMED, 'Locator start.', VALUE_DEFAULT, ''),
            'locatorend' => new external_value(PARAM_RAW_TRIMMED, 'Locator end.', VALUE_DEFAULT, ''),
            'locatorlabel' => new external_value(PARAM_TEXT, 'Human-readable locator label.', VALUE_DEFAULT, ''),
            'description' => new external_value(PARAM_RAW, 'Advisory description or note.', VALUE_DEFAULT, ''),
            'teachingcontext' => new external_value(PARAM_RAW, 'Teaching/context note.', VALUE_DEFAULT, ''),
            'culturalprotocolnote' => new external_value(PARAM_RAW, 'Cultural protocol note.', VALUE_DEFAULT, ''),
            'severity' => new external_value(PARAM_ALPHANUMEXT, 'Severity: notice, moderate, strong, restricted.', VALUE_DEFAULT, 'notice'),
            'audiencesuitability' => new external_value(PARAM_ALPHANUMEXT, 'Audience suitability.', VALUE_DEFAULT, ''),
            'visibility' => new external_value(PARAM_ALPHANUMEXT, 'Marker visibility.', VALUE_DEFAULT, ''),
            'reviewrequired' => new external_value(PARAM_BOOL, 'Whether human review is required.', VALUE_DEFAULT, true),
            'culturalprotocol' => new external_value(PARAM_BOOL, 'Whether this marker carries cultural protocol meaning.', VALUE_DEFAULT, false),
            'suggestedbyai' => new external_value(PARAM_BOOL, 'Whether this marker began as an AI-assisted suggestion.', VALUE_DEFAULT, false),
            'metadata' => new external_single_structure([
                'source' => new external_value(PARAM_ALPHANUMEXT, 'Metadata source.', VALUE_DEFAULT, ''),
                'reason' => new external_value(PARAM_TEXT, 'Reason for marker creation.', VALUE_DEFAULT, ''),
                'confidence' => new external_value(PARAM_FLOAT, 'Optional suggestion confidence.', VALUE_DEFAULT, 0.0),
                'notes' => new external_value(PARAM_RAW, 'Additional metadata notes.', VALUE_DEFAULT, ''),
            ], 'Optional marker metadata.', VALUE_DEFAULT, []),
        ]);
    }

    /**
     * Execute service.
     *
     * @param int $cmid Course module id.
     * @param string $targettype Target type.
     * @param int $targetid Target id.
     * @param string $targetuuid Target UUID.
     * @param string $tagkey Single tag key.
     * @param array $tagkeys Multiple tag keys.
     * @param int $tagid Tag id.
     * @param int $tagsetid Tag set id.
     * @param string $tagsetkey Tag set key.
     * @param string $locatortype Locator type.
     * @param string $locatorvalue Locator value.
     * @param string $locatorstart Locator start.
     * @param string $locatorend Locator end.
     * @param string $locatorlabel Locator label.
     * @param string $description Description.
     * @param string $teachingcontext Teaching context note.
     * @param string $culturalprotocolnote Cultural protocol note.
     * @param string $severity Severity.
     * @param string $audiencesuitability Audience suitability.
     * @param string $visibility Visibility.
     * @param bool $reviewrequired Review required flag.
     * @param bool $culturalprotocol Cultural protocol flag.
     * @param bool $suggestedbyai AI suggestion flag.
     * @param array $metadata Metadata.
     * @return array<string, mixed>
     */
    public static function execute(
        int $cmid,
        string $targettype,
        int $targetid = 0,
        string $targetuuid = '',
        string $tagkey = '',
        array $tagkeys = [],
        int $tagid = 0,
        int $tagsetid = 0,
        string $tagsetkey = '',
        string $locatortype = 'manual_reference',
        string $locatorvalue = '',
        string $locatorstart = '',
        string $locatorend = '',
        string $locatorlabel = '',
        string $description = '',
        string $teachingcontext = '',
        string $culturalprotocolnote = '',
        string $severity = 'notice',
        string $audiencesuitability = '',
        string $visibility = '',
        bool $reviewrequired = true,
        bool $culturalprotocol = false,
        bool $suggestedbyai = false,
        array $metadata = []
    ): array {
        global $DB, $USER;

        $params = self::validate_parameters(self::execute_parameters(), [
            'cmid' => $cmid,
            'targettype' => $targettype,
            'targetid' => $targetid,
            'targetuuid' => $targetuuid,
            'tagkey' => $tagkey,
            'tagkeys' => $tagkeys,
            'tagid' => $tagid,
            'tagsetid' => $tagsetid,
            'tagsetkey' => $tagsetkey,
            'locatortype' => $locatortype,
            'locatorvalue' => $locatorvalue,
            'locatorstart' => $locatorstart,
            'locatorend' => $locatorend,
            'locatorlabel' => $locatorlabel,
            'description' => $description,
            'teachingcontext' => $teachingcontext,
            'culturalprotocolnote' => $culturalprotocolnote,
            'severity' => $severity,
            'audiencesuitability' => $audiencesuitability,
            'visibility' => $visibility,
            'reviewrequired' => $reviewrequired,
            'culturalprotocol' => $culturalprotocol,
            'suggestedbyai' => $suggestedbyai,
            'metadata' => $metadata,
        ]);

        [$course, $cm, $archive, $context] = self::load_page((int)$params['cmid']);

        self::validate_context($context);
        require_login($course, false, $cm);
        content_policy::require_manage_advisories($context);

        if (!class_exists(content_marker::class) || !method_exists(content_marker::class, 'create')) {
            throw new \coding_exception('The content marker domain service must implement content_marker::create().');
        }

        $targettype = self::normalise_target_type((string)$params['targettype']);
        $targetid = max(0, (int)$params['targetid']);
        $targetuuid = trim((string)$params['targetuuid']);
        $tagkeys = self::normalise_tagkeys((string)$params['tagkey'], (array)$params['tagkeys'], (int)$params['tagid']);

        $severity = self::normalise_value(
            (string)$params['severity'],
            content_marker::severities(),
            'Invalid advisory severity.'
        );

        $locatortype = self::normalise_value(
            (string)$params['locatortype'],
            content_marker::locator_types(),
            'Invalid locator type.'
        );

        $visibility = trim((string)$params['visibility']);
        if ($visibility === '') {
            $visibility = content_policy::default_marker_visibility($tagkeys[0] ?? '', $severity);
        }
        $visibility = self::normalise_value($visibility, content_marker::visibilities(), 'Invalid marker visibility.');

        $audiencesuitability = trim((string)$params['audiencesuitability']);
        if ($audiencesuitability === '') {
            $audiencesuitability = content_policy::default_audience_suitability($tagkeys[0] ?? '', $severity);
        }
        $audiencesuitability = self::normalise_value(
            $audiencesuitability,
            content_marker::audience_suitabilities(),
            'Invalid audience suitability.'
        );

        $reviewstate = !empty($params['reviewrequired'])
            ? content_marker::REVIEW_PENDING
            : content_policy::default_review_state($tagkeys[0] ?? '', $severity);
        $reviewstate = self::normalise_value($reviewstate, content_marker::review_states(), 'Invalid review state.');

        if (!empty($params['culturalprotocol']) && !content_policy::can_view_culturally_restricted($context)) {
            throw new \required_capability_exception(
                $context,
                content_policy::CAP_VIEW_CULTURALLY_RESTRICTED,
                'nopermissions',
                ''
            );
        }

        self::validate_target((int)$archive->id, $targettype, $targetid, $targetuuid);

        $metadata = self::normalise_metadata((array)$params['metadata']);
        $metadata['suggestedbyai'] = !empty($params['suggestedbyai']);
        $metadata['createdbyservice'] = 'add_content_marker';

        $base = [
            'archiveid' => (int)$archive->id,
            'courseid' => (int)$course->id,
            'cmid' => (int)$cm->id,
            'contextid' => (int)$context->id,
            'targettype' => $targettype,
            'targetid' => $targetid,
            'targetuuid' => $targetuuid,
            'tagid' => max(0, (int)$params['tagid']),
            'tagsetid' => max(0, (int)$params['tagsetid']),
            'tagsetkey' => clean_param((string)$params['tagsetkey'], PARAM_ALPHANUMEXT),
            'locatortype' => $locatortype,
            'locatorvalue' => trim((string)$params['locatorvalue']),
            'locatorstart' => trim((string)$params['locatorstart']),
            'locatorend' => trim((string)$params['locatorend']),
            'locatorlabel' => clean_param((string)$params['locatorlabel'], PARAM_TEXT),
            'locatorsort' => 0,
            'severity' => $severity,
            'visibility' => $visibility,
            'audiencesuitability' => $audiencesuitability,
            'reviewstate' => $reviewstate,
            'note' => clean_param((string)$params['description'], PARAM_RAW),
            'teachingcontext' => clean_param((string)$params['teachingcontext'], PARAM_RAW),
            'culturalprotocolnote' => clean_param((string)$params['culturalprotocolnote'], PARAM_RAW),
            'culturalprotocol' => !empty($params['culturalprotocol']) ? 1 : 0,
            'createdby' => (int)$USER->id,
            'modifiedby' => (int)$USER->id,
            'metadata' => $metadata,
        ];

        if ($targettype !== content_marker::TARGET_MANUAL_REFERENCE && $targetid <= 0 && $targetuuid === '') {
            throw new invalid_parameter_exception('A non-manual content marker requires targetid or targetuuid.');
        }

        if ($base['locatorvalue'] === '' && $base['locatorstart'] === '' && $base['locatorend'] === '') {
            throw new invalid_parameter_exception('A content marker requires locatorvalue, locatorstart, or locatorend.');
        }

        $transaction = $DB->start_delegated_transaction();

        $markers = [];
        foreach ($tagkeys as $key) {
            $record = $base;
            $record['tagkey'] = $key;
            $marker = content_marker::create($record, (int)$USER->id);
            self::trigger_created_event($marker, $context, $course, $cm, $archive);
            $markers[] = self::export_marker($marker, $context);
        }

        $transaction->allow_commit();

        return [
            'marker' => $markers[0],
            'markers' => $markers,
            'permissions' => self::permissions($context),
            'warnings' => [],
        ];
    }

    /**
     * Describe service return structure.
     *
     * @return external_single_structure
     */
    public static function execute_returns(): external_single_structure {
        return new external_single_structure([
            'marker' => self::marker_structure(),
            'markers' => new external_multiple_structure(self::marker_structure(), 'Created marker records.'),
            'permissions' => self::permissions_structure(),
            'warnings' => self::warnings_structure(),
        ]);
    }

    /**
     * Return marker structure.
     *
     * @return external_single_structure
     */
    private static function marker_structure(): external_single_structure {
        return new external_single_structure([
            'id' => new external_value(PARAM_INT, 'Marker id.'),
            'uuid' => new external_value(PARAM_RAW, 'Marker UUID.'),
            'archiveid' => new external_value(PARAM_INT, 'Archive id.'),
            'courseid' => new external_value(PARAM_INT, 'Course id.'),
            'cmid' => new external_value(PARAM_INT, 'Course module id.'),
            'contextid' => new external_value(PARAM_INT, 'Context id.'),
            'targettype' => new external_value(PARAM_ALPHANUMEXT, 'Target type.'),
            'targetid' => new external_value(PARAM_INT, 'Target id.'),
            'targetuuid' => new external_value(PARAM_RAW, 'Target UUID.'),
            'tagid' => new external_value(PARAM_INT, 'Tag id.'),
            'tagkey' => new external_value(PARAM_ALPHANUMEXT, 'Tag key.'),
            'tagsetid' => new external_value(PARAM_INT, 'Tag set id.'),
            'tagsetkey' => new external_value(PARAM_ALPHANUMEXT, 'Tag set key.'),
            'locatortype' => new external_value(PARAM_ALPHANUMEXT, 'Locator type.'),
            'locatorvalue' => new external_value(PARAM_RAW, 'Locator value.'),
            'locatorstart' => new external_value(PARAM_RAW, 'Locator start.'),
            'locatorend' => new external_value(PARAM_RAW, 'Locator end.'),
            'locatorlabel' => new external_value(PARAM_TEXT, 'Locator label.'),
            'severity' => new external_value(PARAM_ALPHANUMEXT, 'Severity.'),
            'visibility' => new external_value(PARAM_ALPHANUMEXT, 'Visibility.'),
            'audiencesuitability' => new external_value(PARAM_ALPHANUMEXT, 'Audience suitability.'),
            'reviewstate' => new external_value(PARAM_ALPHANUMEXT, 'Review state.'),
            'note' => new external_value(PARAM_RAW, 'Safe note.'),
            'teachingcontext' => new external_value(PARAM_RAW, 'Safe teaching context.'),
            'culturalprotocolnote' => new external_value(PARAM_RAW, 'Safe cultural protocol note.'),
            'culturalprotocol' => new external_value(PARAM_BOOL, 'Cultural protocol flag.'),
            'createdby' => new external_value(PARAM_INT, 'Created by user id.'),
            'modifiedby' => new external_value(PARAM_INT, 'Modified by user id.'),
            'timecreated' => new external_value(PARAM_INT, 'Creation timestamp.'),
            'timemodified' => new external_value(PARAM_INT, 'Modified timestamp.'),
            'redacted' => new external_value(PARAM_BOOL, 'Whether fields were redacted.'),
        ]);
    }

    /**
     * Return permission structure.
     *
     * @return external_single_structure
     */
    private static function permissions_structure(): external_single_structure {
        return new external_single_structure([
            'viewadvisories' => new external_value(PARAM_BOOL, 'Can view advisories.'),
            'manageadvisories' => new external_value(PARAM_BOOL, 'Can manage advisories.'),
            'reviewadvisories' => new external_value(PARAM_BOOL, 'Can review advisories.'),
            'viewculturallyrestricted' => new external_value(PARAM_BOOL, 'Can view culturally restricted advisories.'),
        ]);
    }

    /**
     * Return warnings structure.
     *
     * @return external_multiple_structure
     */
    private static function warnings_structure(): external_multiple_structure {
        return new external_multiple_structure(new external_single_structure([
            'item' => new external_value(PARAM_TEXT, 'Warning item.'),
            'itemid' => new external_value(PARAM_INT, 'Warning item id.'),
            'warningcode' => new external_value(PARAM_ALPHANUMEXT, 'Warning code.'),
            'message' => new external_value(PARAM_TEXT, 'Warning message.'),
        ]));
    }

    /**
     * Load Moodle activity context.
     *
     * @param int $cmid Course module id.
     * @return array{0:stdClass,1:stdClass,2:stdClass,3:context_module}
     */
    private static function load_page(int $cmid): array {
        global $DB;

        if (function_exists('uckkarchive_require_page')) {
            [$course, $cm, $archive, $context] = \uckkarchive_require_page($cmid, 0);
            return [$course, $cm, $archive, $context];
        }

        $cm = get_coursemodule_from_id('uckkarchive', $cmid, 0, false, MUST_EXIST);
        $course = $DB->get_record('course', ['id' => $cm->course], '*', MUST_EXIST);
        $archive = $DB->get_record('uckkarchive', ['id' => $cm->instance], '*', MUST_EXIST);
        $context = context_module::instance($cm->id);

        return [$course, $cm, $archive, $context];
    }

    /**
     * Normalise target type.
     *
     * @param string $targettype Target type.
     * @return string
     */
    private static function normalise_target_type(string $targettype): string {
        $targettype = clean_param($targettype, PARAM_ALPHANUMEXT);

        return self::normalise_value($targettype, content_marker::target_types(), 'Invalid content marker target type.');
    }

    /**
     * Normalise one value against allowed values.
     *
     * @param string $value Value.
     * @param string[] $allowed Allowed values.
     * @param string $message Error message.
     * @return string
     */
    private static function normalise_value(string $value, array $allowed, string $message): string {
        $value = clean_param($value, PARAM_ALPHANUMEXT);

        if (!in_array($value, $allowed, true)) {
            throw new invalid_parameter_exception($message);
        }

        return $value;
    }

    /**
     * Normalise tag keys.
     *
     * @param string $tagkey Single tag key.
     * @param array $tagkeys Multiple tag keys.
     * @param int $tagid Tag id.
     * @return string[]
     */
    private static function normalise_tagkeys(string $tagkey, array $tagkeys, int $tagid): array {
        $keys = [];

        if (trim($tagkey) !== '') {
            $keys[] = clean_param($tagkey, PARAM_ALPHANUMEXT);
        }

        foreach ($tagkeys as $key) {
            $key = clean_param((string)$key, PARAM_ALPHANUMEXT);
            if ($key !== '') {
                $keys[] = $key;
            }
        }

        $keys = array_values(array_unique($keys));

        if (empty($keys) && $tagid <= 0) {
            throw new invalid_parameter_exception('A content marker requires tagkey, tagkeys, or tagid.');
        }

        if (empty($keys) && $tagid > 0) {
            $keys[] = 'tag_' . $tagid;
        }

        return $keys;
    }

    /**
     * Normalise metadata.
     *
     * @param array $metadata Metadata.
     * @return array<string, mixed>
     */
    private static function normalise_metadata(array $metadata): array {
        return [
            'source' => clean_param((string)($metadata['source'] ?? ''), PARAM_ALPHANUMEXT),
            'reason' => clean_param((string)($metadata['reason'] ?? ''), PARAM_TEXT),
            'confidence' => (float)($metadata['confidence'] ?? 0.0),
            'notes' => clean_param((string)($metadata['notes'] ?? ''), PARAM_RAW),
        ];
    }

    /**
     * Validate that target belongs to this archive when target table exists.
     *
     * @param int $archiveid Archive id.
     * @param string $targettype Target type.
     * @param int $targetid Target id.
     * @param string $targetuuid Target UUID.
     * @return void
     */
    private static function validate_target(int $archiveid, string $targettype, int $targetid, string $targetuuid): void {
        $target = self::target_table_and_fields($targettype);
        if ($target === null) {
            return;
        }

        [$table, $archivefields] = $target;

        if (!self::table_exists($table)) {
            return;
        }

        if ($targetid <= 0 && $targetuuid === '') {
            return;
        }

        $record = self::get_target_record($table, $targetid, $targetuuid);
        if (!$record) {
            throw new invalid_parameter_exception('Content marker target was not found.');
        }

        foreach ($archivefields as $field) {
            if (property_exists($record, $field) && (int)$record->{$field} > 0 && (int)$record->{$field} !== $archiveid) {
                throw new invalid_parameter_exception('Content marker target does not belong to this archive.');
            }
        }
    }

    /**
     * Return target table and archive id fields.
     *
     * @param string $targettype Target type.
     * @return array{0:string,1:string[]}|null
     */
    private static function target_table_and_fields(string $targettype): ?array {
        return match ($targettype) {
            content_marker::TARGET_MEDIA => [self::TABLE_MEDIA, ['archiveid', 'uckkarchiveid']],
            content_marker::TARGET_MEDIA_VERSION => [self::TABLE_MEDIA_VERSION, ['archiveid', 'uckkarchiveid']],
            content_marker::TARGET_ARCHIVE_ITEM => [self::TABLE_ITEM, ['archiveid', 'uckkarchiveid']],
            content_marker::TARGET_EXTERNAL_WORK => [self::TABLE_EXTERNAL_WORK, ['archiveid', 'uckkarchiveid']],
            content_marker::TARGET_COLLECTION => [self::TABLE_COLLECTION, ['archiveid', 'uckkarchiveid']],
            content_marker::TARGET_PROOF => [self::TABLE_PROOF, ['archiveid', 'uckkarchiveid']],
            content_marker::TARGET_KRISTAL => [self::TABLE_KRISTAL, ['archiveid', 'uckkarchiveid']],
            default => null,
        };
    }

    /**
     * Return target record by id or uuid.
     *
     * @param string $table Table.
     * @param int $targetid Target id.
     * @param string $targetuuid Target UUID.
     * @return stdClass|null
     */
    private static function get_target_record(string $table, int $targetid, string $targetuuid): ?stdClass {
        global $DB;

        if ($targetid > 0 && $DB->record_exists($table, ['id' => $targetid])) {
            return $DB->get_record($table, ['id' => $targetid], '*', MUST_EXIST);
        }

        $columns = $DB->get_columns($table);
        if ($targetuuid !== '' && array_key_exists('uuid', $columns) && $DB->record_exists($table, ['uuid' => $targetuuid])) {
            return $DB->get_record($table, ['uuid' => $targetuuid], '*', MUST_EXIST);
        }

        return null;
    }

    /**
     * Return whether a table exists.
     *
     * @param string $table Table.
     * @return bool
     */
    private static function table_exists(string $table): bool {
        global $DB;

        return $DB->get_manager()->table_exists(new \xmldb_table($table));
    }

    /**
     * Export marker safely.
     *
     * @param stdClass $marker Marker record.
     * @param context_module $context Context.
     * @return array<string, mixed>
     */
    private static function export_marker(stdClass $marker, context_module $context): array {
        if (method_exists(content_policy::class, 'can_view_marker') && !content_policy::can_view_marker($context, $marker)) {
            $marker = content_policy::redact_marker($marker, content_policy::REDACT_PLACEHOLDER);
        }

        return [
            'id' => (int)($marker->id ?? 0),
            'uuid' => (string)($marker->uuid ?? ''),
            'archiveid' => (int)($marker->archiveid ?? $marker->uckkarchiveid ?? 0),
            'courseid' => (int)($marker->courseid ?? 0),
            'cmid' => (int)($marker->cmid ?? 0),
            'contextid' => (int)($marker->contextid ?? 0),
            'targettype' => (string)($marker->targettype ?? ''),
            'targetid' => (int)($marker->targetid ?? 0),
            'targetuuid' => (string)($marker->targetuuid ?? ''),
            'tagid' => (int)($marker->tagid ?? 0),
            'tagkey' => (string)($marker->tagkey ?? ''),
            'tagsetid' => (int)($marker->tagsetid ?? 0),
            'tagsetkey' => (string)($marker->tagsetkey ?? ''),
            'locatortype' => (string)($marker->locatortype ?? $marker->locator_type ?? ''),
            'locatorvalue' => (string)($marker->locatorvalue ?? $marker->locator_value ?? ''),
            'locatorstart' => (string)($marker->locatorstart ?? $marker->locator_start ?? ''),
            'locatorend' => (string)($marker->locatorend ?? $marker->locator_end ?? ''),
            'locatorlabel' => (string)($marker->locatorlabel ?? $marker->locator_label ?? ''),
            'severity' => (string)($marker->severity ?? ''),
            'visibility' => (string)($marker->visibility ?? ''),
            'audiencesuitability' => (string)($marker->audiencesuitability ?? ''),
            'reviewstate' => (string)($marker->reviewstate ?? ''),
            'note' => (string)($marker->note ?? ''),
            'teachingcontext' => (string)($marker->teachingcontext ?? ''),
            'culturalprotocolnote' => (string)($marker->culturalprotocolnote ?? ''),
            'culturalprotocol' => !empty($marker->culturalprotocol),
            'createdby' => (int)($marker->createdby ?? 0),
            'modifiedby' => (int)($marker->modifiedby ?? 0),
            'timecreated' => (int)($marker->timecreated ?? 0),
            'timemodified' => (int)($marker->timemodified ?? 0),
            'redacted' => !empty($marker->redacted),
        ];
    }

    /**
     * Return permissions payload.
     *
     * @param context_module $context Context.
     * @return array<string, bool>
     */
    private static function permissions(context_module $context): array {
        return [
            'viewadvisories' => content_policy::can_view_advisories($context),
            'manageadvisories' => content_policy::can_manage_advisories($context),
            'reviewadvisories' => content_policy::can_review_advisories($context),
            'viewculturallyrestricted' => content_policy::can_view_culturally_restricted($context),
        ];
    }

    /**
     * Trigger marker created event when the event class exists.
     *
     * @param stdClass $marker Marker.
     * @param context_module $context Context.
     * @param stdClass $course Course.
     * @param stdClass $cm Course module.
     * @param stdClass $archive Archive.
     * @return void
     */
    private static function trigger_created_event(
        stdClass $marker,
        context_module $context,
        stdClass $course,
        stdClass $cm,
        stdClass $archive
    ): void {
        $eventclass = '\\mod_uckkarchive\\event\\content_marker_created';
        if (!class_exists($eventclass)) {
            return;
        }

        $event = $eventclass::create([
            'context' => $context,
            'objectid' => (int)$marker->id,
            'other' => [
                'archiveid' => (int)$archive->id,
                'courseid' => (int)$course->id,
                'cmid' => (int)$cm->id,
                'uuid' => (string)($marker->uuid ?? ''),
                'targettype' => (string)($marker->targettype ?? ''),
                'targetid' => (int)($marker->targetid ?? 0),
                'tagkey' => (string)($marker->tagkey ?? ''),
                'reviewstate' => (string)($marker->reviewstate ?? ''),
            ],
        ]);
        $event->trigger();
    }
}
