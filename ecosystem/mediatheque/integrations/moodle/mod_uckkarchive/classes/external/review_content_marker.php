<?php
// This file is part of Moodle - https://moodle.org/.
//
// Moodle is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// any later version.

/**
 * External service for human review of content advisory markers.
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
require_once(dirname(__DIR__) . '/local/content_review.php');

use context_module;
use core_external\external_api;
use core_external\external_function_parameters;
use core_external\external_multiple_structure;
use core_external\external_single_structure;
use core_external\external_value;
use invalid_parameter_exception;
use mod_uckkarchive\local\content_marker;
use mod_uckkarchive\local\content_policy;
use mod_uckkarchive\local\content_review;
use stdClass;

/**
 * Human review endpoint for a content advisory marker.
 *
 * Target service name:
 *
 * ```text
 * mod_uckkarchive_review_content_marker
 * ```
 *
 * This endpoint is human-authority only. It must not be used by AI automation
 * to approve, retire, contest, or remove cultural protocol restrictions.
 */
final class review_content_marker extends external_api {
    /** Content marker table. */
    private const MARKER_TABLE = 'uckkarchive_content_marker';

    /**
     * Define service parameters.
     *
     * @return external_function_parameters
     */
    public static function execute_parameters(): external_function_parameters {
        return new external_function_parameters([
            'cmid' => new external_value(PARAM_INT, 'Course module id for the UCKK Archive instance.'),
            'markerid' => new external_value(PARAM_INT, 'Content marker id.', VALUE_DEFAULT, 0),
            'markeruuid' => new external_value(PARAM_RAW_TRIMMED, 'Content marker UUID.', VALUE_DEFAULT, ''),
            'decision' => new external_value(
                PARAM_ALPHANUMEXT,
                'Review decision: reviewed, approved, contested, retired, pending_review.',
                VALUE_DEFAULT,
                content_review::STATE_REVIEWED
            ),
            'rationale' => new external_value(PARAM_RAW, 'Human review rationale.', VALUE_DEFAULT, ''),
            'reviewnote' => new external_value(PARAM_RAW, 'Private or internal review note.', VALUE_DEFAULT, ''),
            'severity' => new external_value(PARAM_ALPHANUMEXT, 'Reviewed advisory severity.', VALUE_DEFAULT, ''),
            'audiencesuitability' => new external_value(PARAM_ALPHANUMEXT, 'Reviewed audience suitability.', VALUE_DEFAULT, ''),
            'restricted' => new external_value(PARAM_BOOL, 'Whether the review requires restricted handling.', VALUE_DEFAULT, false),
            'culturalprotocol' => new external_value(PARAM_BOOL, 'Whether the review confirms cultural protocol handling.', VALUE_DEFAULT, false),
            'updatemarker' => new external_value(
                PARAM_BOOL,
                'Synchronise review state and selected fields back to the marker record.',
                VALUE_DEFAULT,
                true
            ),
            'metadata' => new external_single_structure([
                'source' => new external_value(PARAM_ALPHANUMEXT, 'Review metadata source.', VALUE_DEFAULT, ''),
                'reason' => new external_value(PARAM_TEXT, 'Review metadata reason.', VALUE_DEFAULT, ''),
                'notes' => new external_value(PARAM_RAW, 'Additional metadata notes.', VALUE_DEFAULT, ''),
            ], 'Optional review metadata.', VALUE_DEFAULT, []),
        ]);
    }

    /**
     * Execute service.
     *
     * @param int $cmid Course module id.
     * @param int $markerid Marker id.
     * @param string $markeruuid Marker UUID.
     * @param string $decision Review decision.
     * @param string $rationale Review rationale.
     * @param string $reviewnote Review note.
     * @param string $severity Severity.
     * @param string $audiencesuitability Audience suitability.
     * @param bool $restricted Restricted flag.
     * @param bool $culturalprotocol Cultural protocol flag.
     * @param bool $updatemarker Whether to sync marker.
     * @param array $metadata Metadata.
     * @return array<string, mixed>
     */
    public static function execute(
        int $cmid,
        int $markerid = 0,
        string $markeruuid = '',
        string $decision = content_review::STATE_REVIEWED,
        string $rationale = '',
        string $reviewnote = '',
        string $severity = '',
        string $audiencesuitability = '',
        bool $restricted = false,
        bool $culturalprotocol = false,
        bool $updatemarker = true,
        array $metadata = []
    ): array {
        global $DB, $USER;

        $params = self::validate_parameters(self::execute_parameters(), [
            'cmid' => $cmid,
            'markerid' => $markerid,
            'markeruuid' => $markeruuid,
            'decision' => $decision,
            'rationale' => $rationale,
            'reviewnote' => $reviewnote,
            'severity' => $severity,
            'audiencesuitability' => $audiencesuitability,
            'restricted' => $restricted,
            'culturalprotocol' => $culturalprotocol,
            'updatemarker' => $updatemarker,
            'metadata' => $metadata,
        ]);

        [$course, $cm, $archive, $context] = self::load_page((int)$params['cmid']);

        self::validate_context($context);
        require_login($course, false, $cm);
        self::require_review_capability($context);

        $decision = self::normalise_decision((string)$params['decision']);
        $marker = self::get_marker((int)$params['markerid'], (string)$params['markeruuid']);
        self::require_marker_in_archive($marker, (int)$archive->id);

        if (!self::can_review_marker($context, $marker)) {
            throw new \required_capability_exception(
                $context,
                content_policy::CAP_REVIEW_ADVISORIES,
                'nopermissions',
                ''
            );
        }

        if (!empty($params['culturalprotocol']) && !has_capability(content_policy::CAP_VIEW_CULTURALLY_RESTRICTED, $context)) {
            throw new \required_capability_exception(
                $context,
                content_policy::CAP_VIEW_CULTURALLY_RESTRICTED,
                'nopermissions',
                ''
            );
        }

        $reviewdata = self::build_review_data($decision, $params, $marker);
        $transaction = $DB->start_delegated_transaction();

        $review = self::create_or_update_review((int)$marker->id, (int)$USER->id, $decision, $reviewdata);

        if (!empty($params['updatemarker'])) {
            $marker = self::sync_marker_review_state($marker, $decision, $reviewdata, (int)$USER->id);
        }

        self::trigger_review_event($review, $marker, $context, $course, $cm, $archive, $decision);

        $transaction->allow_commit();

        return [
            'review' => self::export_review($review),
            'marker' => self::export_marker($marker, $context),
            'permissions' => self::permissions($context),
            'warnings' => [],
        ];
    }

    /**
     * Define service return structure.
     *
     * @return external_single_structure
     */
    public static function execute_returns(): external_single_structure {
        return new external_single_structure([
            'review' => self::review_structure(),
            'marker' => self::marker_structure(),
            'permissions' => self::permissions_structure(),
            'warnings' => self::warnings_structure(),
        ]);
    }

    /**
     * Return review response structure.
     *
     * @return external_single_structure
     */
    private static function review_structure(): external_single_structure {
        return new external_single_structure([
            'id' => new external_value(PARAM_INT, 'Review id.'),
            'uuid' => new external_value(PARAM_RAW, 'Review UUID.'),
            'markerid' => new external_value(PARAM_INT, 'Marker id.'),
            'reviewerid' => new external_value(PARAM_INT, 'Reviewer user id.'),
            'state' => new external_value(PARAM_ALPHANUMEXT, 'Review state.'),
            'severity' => new external_value(PARAM_ALPHANUMEXT, 'Reviewed severity.'),
            'audiencesuitability' => new external_value(PARAM_ALPHANUMEXT, 'Reviewed audience suitability.'),
            'rationale' => new external_value(PARAM_RAW, 'Safe rationale.'),
            'reviewnote' => new external_value(PARAM_RAW, 'Safe review note.'),
            'culturalprotocol' => new external_value(PARAM_BOOL, 'Cultural protocol flag.'),
            'restricted' => new external_value(PARAM_BOOL, 'Restricted flag.'),
            'metadatajson' => new external_value(PARAM_RAW, 'JSON metadata.'),
            'timecreated' => new external_value(PARAM_INT, 'Created timestamp.'),
            'timemodified' => new external_value(PARAM_INT, 'Modified timestamp.'),
        ]);
    }

    /**
     * Return marker response structure.
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
            'locatortype' => new external_value(PARAM_ALPHANUMEXT, 'Locator type.'),
            'locatorvalue' => new external_value(PARAM_RAW, 'Locator value.'),
            'locatorstart' => new external_value(PARAM_RAW, 'Locator start.'),
            'locatorend' => new external_value(PARAM_RAW, 'Locator end.'),
            'locatorlabel' => new external_value(PARAM_TEXT, 'Locator label.'),
            'severity' => new external_value(PARAM_ALPHANUMEXT, 'Severity.'),
            'visibility' => new external_value(PARAM_ALPHANUMEXT, 'Visibility.'),
            'audiencesuitability' => new external_value(PARAM_ALPHANUMEXT, 'Audience suitability.'),
            'reviewstate' => new external_value(PARAM_ALPHANUMEXT, 'Marker review state.'),
            'reviewrationale' => new external_value(PARAM_RAW, 'Safe marker review rationale.'),
            'note' => new external_value(PARAM_RAW, 'Safe marker note.'),
            'teachingcontext' => new external_value(PARAM_RAW, 'Safe teaching context.'),
            'culturalprotocolnote' => new external_value(PARAM_RAW, 'Safe cultural protocol note.'),
            'culturalprotocol' => new external_value(PARAM_BOOL, 'Cultural protocol flag.'),
            'reviewedby' => new external_value(PARAM_INT, 'Reviewed by user id.'),
            'timereviewed' => new external_value(PARAM_INT, 'Review timestamp.'),
            'timecreated' => new external_value(PARAM_INT, 'Created timestamp.'),
            'timemodified' => new external_value(PARAM_INT, 'Modified timestamp.'),
            'redacted' => new external_value(PARAM_BOOL, 'Whether details were redacted.'),
        ]);
    }

    /**
     * Return permissions response structure.
     *
     * @return external_single_structure
     */
    private static function permissions_structure(): external_single_structure {
        return new external_single_structure([
            'viewadvisories' => new external_value(PARAM_BOOL, 'Can view advisories.'),
            'manageadvisories' => new external_value(PARAM_BOOL, 'Can manage advisories.'),
            'reviewadvisories' => new external_value(PARAM_BOOL, 'Can review advisories.'),
            'viewculturallyrestricted' => new external_value(PARAM_BOOL, 'Can view culturally restricted details.'),
        ]);
    }

    /**
     * Return warnings response structure.
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
     * Require review capability.
     *
     * @param context_module $context Context.
     * @return void
     */
    private static function require_review_capability(context_module $context): void {
        require_capability(content_policy::CAP_REVIEW_ADVISORIES, $context);
    }

    /**
     * Return marker record by id or uuid.
     *
     * @param int $markerid Marker id.
     * @param string $markeruuid Marker uuid.
     * @return stdClass
     */
    private static function get_marker(int $markerid, string $markeruuid): stdClass {
        global $DB;

        if (!self::table_exists(self::MARKER_TABLE)) {
            throw new invalid_parameter_exception('Content marker table is not installed yet.');
        }

        $markerid = max(0, $markerid);
        $markeruuid = trim($markeruuid);

        if ($markerid <= 0 && $markeruuid === '') {
            throw new invalid_parameter_exception('markerid or markeruuid is required.');
        }

        if ($markerid > 0 && method_exists(content_marker::class, 'get_record')) {
            return content_marker::get_record($markerid, MUST_EXIST);
        }

        if ($markeruuid !== '' && method_exists(content_marker::class, 'get_record_by_uuid')) {
            return content_marker::get_record_by_uuid($markeruuid, MUST_EXIST);
        }

        if ($markerid > 0) {
            return $DB->get_record(self::MARKER_TABLE, ['id' => $markerid], '*', MUST_EXIST);
        }

        return $DB->get_record(self::MARKER_TABLE, ['uuid' => $markeruuid], '*', MUST_EXIST);
    }

    /**
     * Ensure marker belongs to the current archive instance.
     *
     * @param stdClass $marker Marker record.
     * @param int $archiveid Archive id.
     * @return void
     */
    private static function require_marker_in_archive(stdClass $marker, int $archiveid): void {
        foreach (['archiveid', 'uckkarchiveid'] as $field) {
            if (isset($marker->{$field}) && (int)$marker->{$field} > 0 && (int)$marker->{$field} !== $archiveid) {
                throw new invalid_parameter_exception('Content marker does not belong to this archive.');
            }
        }
    }

    /**
     * Return whether current user may review this marker.
     *
     * @param context_module $context Context.
     * @param stdClass $marker Marker.
     * @return bool
     */
    private static function can_review_marker(context_module $context, stdClass $marker): bool {
        if (!has_capability(content_policy::CAP_REVIEW_ADVISORIES, $context)) {
            return false;
        }

        $iscultural = !empty($marker->culturalprotocol) ||
            (string)($marker->visibility ?? '') === 'restricted_cultural' ||
            (string)($marker->audiencesuitability ?? '') === 'restricted_cultural';

        if ($iscultural && !has_capability(content_policy::CAP_VIEW_CULTURALLY_RESTRICTED, $context)) {
            return false;
        }

        return true;
    }

    /**
     * Normalize decision.
     *
     * @param string $decision Decision.
     * @return string
     */
    private static function normalise_decision(string $decision): string {
        $decision = clean_param($decision, PARAM_ALPHANUMEXT);

        $aliases = [
            'approve' => content_review::STATE_APPROVED,
            'approved' => content_review::STATE_APPROVED,
            'review' => content_review::STATE_REVIEWED,
            'reviewed' => content_review::STATE_REVIEWED,
            'contest' => content_review::STATE_CONTESTED,
            'contested' => content_review::STATE_CONTESTED,
            'retire' => content_review::STATE_RETIRED,
            'retired' => content_review::STATE_RETIRED,
            'pending' => content_review::STATE_PENDING,
            'pending_review' => content_review::STATE_PENDING,
        ];

        $decision = $aliases[$decision] ?? $decision;

        if (!in_array($decision, [
            content_review::STATE_PENDING,
            content_review::STATE_REVIEWED,
            content_review::STATE_APPROVED,
            content_review::STATE_CONTESTED,
            content_review::STATE_RETIRED,
        ], true)) {
            throw new invalid_parameter_exception('Invalid content marker review decision.');
        }

        return $decision;
    }

    /**
     * Build review data for content_review.
     *
     * @param string $decision Decision.
     * @param array<string, mixed> $params Params.
     * @param stdClass $marker Marker.
     * @return array<string, mixed>
     */
    private static function build_review_data(string $decision, array $params, stdClass $marker): array {
        $severity = trim((string)$params['severity']);
        if ($severity === '') {
            $severity = (string)($marker->severity ?? content_review::SEVERITY_NOTICE);
        }

        $suitability = trim((string)$params['audiencesuitability']);
        if ($suitability === '') {
            $suitability = (string)($marker->audiencesuitability ?? content_review::SUITABILITY_GUIDED);
        }

        $metadata = [
            'source' => clean_param((string)($params['metadata']['source'] ?? ''), PARAM_ALPHANUMEXT),
            'reason' => clean_param((string)($params['metadata']['reason'] ?? ''), PARAM_TEXT),
            'notes' => clean_param((string)($params['metadata']['notes'] ?? ''), PARAM_RAW),
            'createdbyservice' => 'review_content_marker',
            'targetmarkeruuid' => (string)($marker->uuid ?? ''),
        ];

        return [
            'state' => $decision,
            'severity' => clean_param($severity, PARAM_ALPHANUMEXT),
            'audiencesuitability' => clean_param($suitability, PARAM_ALPHANUMEXT),
            'rationale' => clean_param((string)$params['rationale'], PARAM_RAW),
            'reviewnote' => clean_param((string)$params['reviewnote'], PARAM_RAW),
            'culturalprotocol' => !empty($params['culturalprotocol']) || !empty($marker->culturalprotocol),
            'restricted' => !empty($params['restricted']) || self::decision_is_restricting($decision),
            'metadata' => $metadata,
        ];
    }

    /**
     * Return whether a decision should imply restricted handling.
     *
     * @param string $decision Decision.
     * @return bool
     */
    private static function decision_is_restricting(string $decision): bool {
        return in_array($decision, [
            content_review::STATE_CONTESTED,
        ], true);
    }

    /**
     * Create or update review through domain class.
     *
     * @param int $markerid Marker id.
     * @param int $reviewerid Reviewer id.
     * @param string $decision Decision.
     * @param array<string, mixed> $data Review data.
     * @return stdClass
     */
    private static function create_or_update_review(
        int $markerid,
        int $reviewerid,
        string $decision,
        array $data
    ): stdClass {
        return match ($decision) {
            content_review::STATE_APPROVED => content_review::approve(
                $markerid,
                $reviewerid,
                (string)$data['rationale'],
                $data
            ),
            content_review::STATE_REVIEWED => content_review::mark_reviewed(
                $markerid,
                $reviewerid,
                (string)$data['rationale'],
                $data
            ),
            content_review::STATE_CONTESTED => content_review::contest(
                $markerid,
                $reviewerid,
                (string)$data['rationale'],
                $data
            ),
            content_review::STATE_RETIRED => content_review::retire(
                $markerid,
                $reviewerid,
                (string)$data['rationale'],
                $data
            ),
            default => content_review::review_marker($markerid, $reviewerid, $decision, $data),
        };
    }

    /**
     * Sync marker review state and safe review fields.
     *
     * @param stdClass $marker Marker.
     * @param string $decision Decision.
     * @param array<string, mixed> $reviewdata Review data.
     * @param int $userid User id.
     * @return stdClass Updated marker.
     */
    private static function sync_marker_review_state(
        stdClass $marker,
        string $decision,
        array $reviewdata,
        int $userid
    ): stdClass {
        global $DB;

        $columns = $DB->get_columns(self::MARKER_TABLE);
        $update = new stdClass();
        $update->id = (int)$marker->id;

        $map = [
            'reviewstate' => $decision,
            'reviewrationale' => (string)$reviewdata['rationale'],
            'severity' => (string)$reviewdata['severity'],
            'audiencesuitability' => (string)$reviewdata['audiencesuitability'],
            'reviewedby' => $userid,
            'timereviewed' => time(),
            'modifiedby' => $userid,
            'timemodified' => time(),
        ];

        if (!empty($reviewdata['culturalprotocol'])) {
            $map['culturalprotocol'] = 1;
        }

        if (!empty($reviewdata['restricted']) && array_key_exists('visibility', $columns)) {
            $map['visibility'] = self::restricted_visibility_for_marker($marker);
        }

        foreach ($map as $field => $value) {
            if (array_key_exists($field, $columns)) {
                $update->{$field} = $value;
                $marker->{$field} = $value;
            }
        }

        $DB->update_record(self::MARKER_TABLE, $update);

        return $DB->get_record(self::MARKER_TABLE, ['id' => (int)$marker->id], '*', MUST_EXIST);
    }

    /**
     * Return restricted visibility suitable for a marker.
     *
     * @param stdClass $marker Marker.
     * @return string
     */
    private static function restricted_visibility_for_marker(stdClass $marker): string {
        if (!empty($marker->culturalprotocol) || (string)($marker->visibility ?? '') === 'restricted_cultural') {
            return 'restricted_cultural';
        }

        return 'restricted';
    }

    /**
     * Export review.
     *
     * @param stdClass $review Review.
     * @return array<string, mixed>
     */
    private static function export_review(stdClass $review): array {
        $review = content_review::hydrate_record($review);
        $metadata = is_array($review->metadata ?? null) ? $review->metadata : [];

        return [
            'id' => (int)($review->id ?? 0),
            'uuid' => (string)($review->uuid ?? ''),
            'markerid' => (int)($review->markerid ?? 0),
            'reviewerid' => (int)($review->reviewerid ?? 0),
            'state' => (string)($review->state ?? ''),
            'severity' => (string)($review->severity ?? ''),
            'audiencesuitability' => (string)($review->audiencesuitability ?? ''),
            'rationale' => (string)($review->rationale ?? ''),
            'reviewnote' => (string)($review->reviewnote ?? ''),
            'culturalprotocol' => !empty($review->culturalprotocol),
            'restricted' => !empty($review->restricted),
            'metadatajson' => self::encode_json($metadata),
            'timecreated' => (int)($review->timecreated ?? 0),
            'timemodified' => (int)($review->timemodified ?? 0),
        ];
    }

    /**
     * Export marker through policy redaction.
     *
     * @param stdClass $marker Marker.
     * @param context_module $context Context.
     * @return array<string, mixed>
     */
    private static function export_marker(stdClass $marker, context_module $context): array {
        if (method_exists(content_policy::class, 'can_view_marker') &&
                !content_policy::can_view_marker($context, $marker)) {
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
            'locatortype' => (string)($marker->locatortype ?? $marker->locator_type ?? ''),
            'locatorvalue' => (string)($marker->locatorvalue ?? $marker->locator_value ?? ''),
            'locatorstart' => (string)($marker->locatorstart ?? $marker->locator_start ?? ''),
            'locatorend' => (string)($marker->locatorend ?? $marker->locator_end ?? ''),
            'locatorlabel' => (string)($marker->locatorlabel ?? $marker->locator_label ?? ''),
            'severity' => (string)($marker->severity ?? ''),
            'visibility' => (string)($marker->visibility ?? ''),
            'audiencesuitability' => (string)($marker->audiencesuitability ?? ''),
            'reviewstate' => (string)($marker->reviewstate ?? ''),
            'reviewrationale' => (string)($marker->reviewrationale ?? ''),
            'note' => (string)($marker->note ?? ''),
            'teachingcontext' => (string)($marker->teachingcontext ?? ''),
            'culturalprotocolnote' => (string)($marker->culturalprotocolnote ?? ''),
            'culturalprotocol' => !empty($marker->culturalprotocol),
            'reviewedby' => (int)($marker->reviewedby ?? 0),
            'timereviewed' => (int)($marker->timereviewed ?? 0),
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
            'viewadvisories' => has_capability(content_policy::CAP_VIEW_ADVISORIES, $context),
            'manageadvisories' => has_capability(content_policy::CAP_MANAGE_ADVISORIES, $context),
            'reviewadvisories' => has_capability(content_policy::CAP_REVIEW_ADVISORIES, $context),
            'viewculturallyrestricted' => has_capability(content_policy::CAP_VIEW_CULTURALLY_RESTRICTED, $context),
        ];
    }

    /**
     * Trigger review event when event class exists.
     *
     * @param stdClass $review Review.
     * @param stdClass $marker Marker.
     * @param context_module $context Context.
     * @param stdClass $course Course.
     * @param stdClass $cm Course module.
     * @param stdClass $archive Archive.
     * @param string $decision Decision.
     * @return void
     */
    private static function trigger_review_event(
        stdClass $review,
        stdClass $marker,
        context_module $context,
        stdClass $course,
        stdClass $cm,
        stdClass $archive,
        string $decision
    ): void {
        $eventclass = '\\mod_uckkarchive\\event\\content_marker_reviewed';
        if (!class_exists($eventclass)) {
            return;
        }

        $event = $eventclass::create([
            'context' => $context,
            'objectid' => (int)($marker->id ?? 0),
            'relateduserid' => (int)($review->reviewerid ?? 0),
            'other' => [
                'archiveid' => (int)$archive->id,
                'courseid' => (int)$course->id,
                'cmid' => (int)$cm->id,
                'markeruuid' => (string)($marker->uuid ?? ''),
                'reviewid' => (int)($review->id ?? 0),
                'reviewuuid' => (string)($review->uuid ?? ''),
                'decision' => $decision,
                'reviewstate' => (string)($marker->reviewstate ?? $decision),
                'tagkey' => (string)($marker->tagkey ?? ''),
            ],
        ]);
        $event->trigger();
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
     * Encode JSON safely.
     *
     * @param array<string, mixed> $data Data.
     * @return string
     */
    private static function encode_json(array $data): string {
        $json = json_encode($data, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);

        return $json === false ? '{}' : $json;
    }
}
