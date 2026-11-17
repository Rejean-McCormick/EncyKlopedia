<?php
// This file is part of Moodle - https://moodle.org/
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
 * Delete or retire a content advisory marker.
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
require_once(dirname(__DIR__, 2) . '/locallib.php');

use context_module;
use core_external\external_api;
use core_external\external_function_parameters;
use core_external\external_multiple_structure;
use core_external\external_single_structure;
use core_external\external_value;
use dml_exception;
use invalid_parameter_exception;
use mod_uckkarchive\local\content_marker;
use mod_uckkarchive\local\content_policy;
use moodle_exception;
use required_capability_exception;
use stdClass;

/**
 * External service for deleting or retiring content advisory markers.
 *
 * Default behaviour is preservation-safe:
 *
 * - ordinary delete = retire marker;
 * - hard delete = allowed only for non-approved markers;
 * - approved, contested, cultural, or restricted markers are retired rather
 *   than physically deleted unless future retention policy explicitly allows
 *   otherwise.
 *
 * Content advisories are part of archive memory and may affect responsible
 * access, cultural protocol, teaching context, and export/redaction behavior.
 * They must not disappear silently once reviewed or approved.
 */
class delete_content_marker extends external_api {

    /** @var string Content marker table. */
    private const MARKER_TABLE = 'uckkarchive_content_marker';

    /** @var string Review table. */
    private const REVIEW_TABLE = 'uckkarchive_content_review';

    /** @var string Retired review state. */
    private const REVIEW_RETIRED = 'retired';

    /** @var string Draft review state. */
    private const REVIEW_DRAFT = 'draft';

    /** @var string Pending review state. */
    private const REVIEW_PENDING = 'pending_review';

    /** @var string Reviewed state. */
    private const REVIEW_REVIEWED = 'reviewed';

    /** @var string Approved review state. */
    private const REVIEW_APPROVED = 'approved';

    /** @var string Contested review state. */
    private const REVIEW_CONTESTED = 'contested';

    /** @var string Restricted visibility. */
    private const VISIBILITY_RESTRICTED = 'restricted';

    /** @var string Restricted integrity visibility. */
    private const VISIBILITY_RESTRICTED_INTEGRITY = 'restricted_integrity';

    /** @var string Restricted cultural visibility. */
    private const VISIBILITY_RESTRICTED_CULTURAL = 'restricted_cultural';

    /**
     * Define service parameters.
     *
     * @return external_function_parameters
     */
    public static function execute_parameters(): external_function_parameters {
        return new external_function_parameters([
            'cmid' => new external_value(
                PARAM_INT,
                'Course module id for the uckkarchive activity.'
            ),
            'markerid' => new external_value(
                PARAM_INT,
                'Content advisory marker id to delete or retire.'
            ),
            'reason' => new external_value(
                PARAM_TEXT,
                'Deletion or retirement reason.',
                VALUE_DEFAULT,
                ''
            ),
            'harddelete' => new external_value(
                PARAM_BOOL,
                'Physically delete the marker only when safe. Defaults to false.',
                VALUE_DEFAULT,
                false
            ),
        ]);
    }

    /**
     * Delete or retire a content advisory marker.
     *
     * @param int $cmid Course module id.
     * @param int $markerid Content marker id.
     * @param string $reason Deletion or retirement reason.
     * @param bool $harddelete Whether to physically delete when safe.
     * @return array<string, mixed>
     * @throws dml_exception
     * @throws invalid_parameter_exception
     * @throws moodle_exception
     * @throws required_capability_exception
     */
    public static function execute(
        int $cmid,
        int $markerid,
        string $reason = '',
        bool $harddelete = false
    ): array {
        global $DB, $USER;

        $params = self::validate_parameters(self::execute_parameters(), [
            'cmid' => $cmid,
            'markerid' => $markerid,
            'reason' => $reason,
            'harddelete' => $harddelete,
        ]);

        [$course, $cm, $archive, $context] = self::load_page((int)$params['cmid']);
        self::validate_context($context);

        require_capability('mod/uckkarchive:manageadvisories', $context);

        $marker = self::get_marker_record((int)$params['markerid']);
        self::assert_marker_belongs_to_activity($marker, $course, $cm, $archive, $context);
        self::assert_restricted_access_for_delete($marker, $context);
        self::assert_policy_allows_delete($marker, $context);

        $warnings = [];
        $oldstate = (string)($marker->reviewstate ?? self::REVIEW_DRAFT);
        $alreadyretired = ($oldstate === self::REVIEW_RETIRED);
        $harddeleted = false;
        $retired = false;

        if ($alreadyretired && empty($params['harddelete'])) {
            $warnings[] = self::warning(
                'content_marker',
                (int)$marker->id,
                'alreadyretired',
                'Content marker is already retired.'
            );

            return [
                'success' => true,
                'markerid' => (int)$marker->id,
                'uuid' => (string)($marker->uuid ?? ''),
                'reviewstate' => self::REVIEW_RETIRED,
                'retired' => false,
                'harddeleted' => false,
                'alreadyretired' => true,
                'warnings' => $warnings,
            ];
        }

        $transaction = $DB->start_delegated_transaction();

        if (!empty($params['harddelete']) && self::can_hard_delete_marker($marker)) {
            self::delete_marker_records((int)$marker->id);
            $harddeleted = true;
        } else {
            if (!empty($params['harddelete'])) {
                $warnings[] = self::warning(
                    'content_marker',
                    (int)$marker->id,
                    'harddeleteblocked',
                    'Hard delete was blocked by preservation policy; marker was retired instead.'
                );
            }

            $marker = self::retire_marker(
                $marker,
                trim((string)$params['reason']),
                (int)$USER->id
            );
            $retired = true;
        }

        self::trigger_marker_event($context, $marker, $oldstate, $harddeleted ? 'harddelete' : 'retire');

        $transaction->allow_commit();

        return [
            'success' => true,
            'markerid' => (int)$marker->id,
            'uuid' => (string)($marker->uuid ?? ''),
            'reviewstate' => $harddeleted ? 'deleted' : (string)($marker->reviewstate ?? self::REVIEW_RETIRED),
            'retired' => $retired,
            'harddeleted' => $harddeleted,
            'alreadyretired' => $alreadyretired,
            'warnings' => $warnings,
        ];
    }

    /**
     * Define service return structure.
     *
     * @return external_single_structure
     */
    public static function execute_returns(): external_single_structure {
        return new external_single_structure([
            'success' => new external_value(PARAM_BOOL, 'Whether the operation succeeded.'),
            'markerid' => new external_value(PARAM_INT, 'Content marker id.'),
            'uuid' => new external_value(PARAM_RAW, 'Content marker UUID.'),
            'reviewstate' => new external_value(PARAM_ALPHANUMEXT, 'Resulting review state.'),
            'retired' => new external_value(PARAM_BOOL, 'Whether the marker was retired.'),
            'harddeleted' => new external_value(PARAM_BOOL, 'Whether the marker was physically deleted.'),
            'alreadyretired' => new external_value(PARAM_BOOL, 'Whether the marker was already retired.'),
            'warnings' => new external_multiple_structure(
                new external_single_structure([
                    'item' => new external_value(PARAM_TEXT, 'Warning item type.'),
                    'itemid' => new external_value(PARAM_INT, 'Warning item id.'),
                    'warningcode' => new external_value(PARAM_ALPHANUMEXT, 'Warning code.'),
                    'message' => new external_value(PARAM_TEXT, 'Warning message.'),
                ]),
                'Warnings.',
                VALUE_DEFAULT,
                []
            ),
        ]);
    }

    /**
     * Load Moodle page objects for the activity.
     *
     * @param int $cmid Course module id.
     * @return array{0:stdClass,1:stdClass,2:stdClass,3:context_module}
     */
    private static function load_page(int $cmid): array {
        [$course, $cm, $archive, $context] = \uckkarchive_require_page($cmid, 0);
        return [$course, $cm, $archive, $context];
    }

    /**
     * Get a content marker record.
     *
     * @param int $markerid Marker id.
     * @return stdClass
     * @throws dml_exception
     * @throws moodle_exception
     */
    private static function get_marker_record(int $markerid): stdClass {
        global $DB;

        if ($markerid <= 0) {
            throw new invalid_parameter_exception('Invalid content marker id.');
        }

        if (!$DB->get_manager()->table_exists(self::MARKER_TABLE)) {
            throw new moodle_exception('missingcontentmarkertable', 'mod_uckkarchive');
        }

        if (class_exists(content_marker::class) && method_exists(content_marker::class, 'get_record')) {
            return content_marker::get_record($markerid, MUST_EXIST);
        }

        return $DB->get_record(self::MARKER_TABLE, ['id' => $markerid], '*', MUST_EXIST);
    }

    /**
     * Ensure marker belongs to the resolved archive activity.
     *
     * @param stdClass $marker Marker record.
     * @param stdClass $course Course record.
     * @param stdClass $cm Course module record.
     * @param stdClass $archive Archive instance record.
     * @param context_module $context Module context.
     * @return void
     * @throws moodle_exception
     */
    private static function assert_marker_belongs_to_activity(
        stdClass $marker,
        stdClass $course,
        stdClass $cm,
        stdClass $archive,
        context_module $context
    ): void {
        if (isset($marker->archiveid) && (int)$marker->archiveid !== (int)$archive->id) {
            throw new moodle_exception('invalidcontentmarkerarchive', 'mod_uckkarchive');
        }

        if (isset($marker->courseid) && (int)$marker->courseid !== (int)$course->id) {
            throw new moodle_exception('invalidcontentmarkercourse', 'mod_uckkarchive');
        }

        if (isset($marker->cmid) && (int)$marker->cmid !== (int)$cm->id) {
            throw new moodle_exception('invalidcontentmarkercm', 'mod_uckkarchive');
        }

        if (isset($marker->contextid) && (int)$marker->contextid !== (int)$context->id) {
            throw new moodle_exception('invalidcontentmarkercontext', 'mod_uckkarchive');
        }
    }

    /**
     * Require additional capability for restricted/cultural markers.
     *
     * @param stdClass $marker Marker record.
     * @param context_module $context Module context.
     * @return void
     */
    private static function assert_restricted_access_for_delete(stdClass $marker, context_module $context): void {
        $visibility = (string)($marker->visibility ?? '');

        if (in_array($visibility, [
            self::VISIBILITY_RESTRICTED,
            self::VISIBILITY_RESTRICTED_INTEGRITY,
            self::VISIBILITY_RESTRICTED_CULTURAL,
        ], true)) {
            require_capability('mod/uckkarchive:viewadvisories', $context);
        }

        if ($visibility === self::VISIBILITY_RESTRICTED_CULTURAL) {
            require_capability('mod/uckkarchive:viewculturallyrestricted', $context);
        }
    }

    /**
     * Allow content_policy to veto deletion.
     *
     * @param stdClass $marker Marker record.
     * @param context_module $context Module context.
     * @return void
     * @throws moodle_exception
     */
    private static function assert_policy_allows_delete(stdClass $marker, context_module $context): void {
        if (!class_exists(content_policy::class) || !method_exists(content_policy::class, 'can_delete_marker')) {
            return;
        }

        $allowed = null;

        try {
            $allowed = content_policy::can_delete_marker($context, $marker);
        } catch (\ArgumentCountError $exception) {
            try {
                $allowed = content_policy::can_delete_marker($marker, $context);
            } catch (\ArgumentCountError $innerexception) {
                $allowed = content_policy::can_delete_marker($context, $marker, null);
            }
        }

        if ($allowed === false) {
            throw new moodle_exception('cannotdeletecontentmarker', 'mod_uckkarchive');
        }
    }

    /**
     * Return whether hard delete is allowed for this marker.
     *
     * @param stdClass $marker Marker record.
     * @return bool
     */
    private static function can_hard_delete_marker(stdClass $marker): bool {
        $state = (string)($marker->reviewstate ?? self::REVIEW_DRAFT);
        $visibility = (string)($marker->visibility ?? '');

        if (in_array($visibility, [
            self::VISIBILITY_RESTRICTED,
            self::VISIBILITY_RESTRICTED_INTEGRITY,
            self::VISIBILITY_RESTRICTED_CULTURAL,
        ], true)) {
            return false;
        }

        if (in_array($state, [
            self::REVIEW_APPROVED,
            self::REVIEW_CONTESTED,
            self::REVIEW_RETIRED,
        ], true)) {
            return false;
        }

        return in_array($state, [
            self::REVIEW_DRAFT,
            self::REVIEW_PENDING,
            self::REVIEW_REVIEWED,
        ], true);
    }

    /**
     * Retire a marker.
     *
     * @param stdClass $marker Marker record.
     * @param string $reason Retirement reason.
     * @param int $userid Acting user id.
     * @return stdClass Updated marker.
     * @throws dml_exception
     * @throws moodle_exception
     */
    private static function retire_marker(stdClass $marker, string $reason, int $userid): stdClass {
        global $DB;

        if (class_exists(content_marker::class) && method_exists(content_marker::class, 'retire')) {
            return content_marker::retire((int)$marker->id, $reason, $userid);
        }

        $marker->reviewstate = self::REVIEW_RETIRED;
        $marker->reviewrationale = $reason;
        $marker->reviewedby = $userid;
        $marker->timereviewed = time();
        $marker->modifiedby = $userid;
        $marker->timemodified = time();

        $DB->update_record(self::MARKER_TABLE, $marker);

        return $DB->get_record(self::MARKER_TABLE, ['id' => (int)$marker->id], '*', MUST_EXIST);
    }

    /**
     * Physically delete marker-related records.
     *
     * @param int $markerid Marker id.
     * @return void
     * @throws dml_exception
     */
    private static function delete_marker_records(int $markerid): void {
        global $DB;

        if ($DB->get_manager()->table_exists(self::REVIEW_TABLE)) {
            $DB->delete_records(self::REVIEW_TABLE, ['markerid' => $markerid]);
        }

        $DB->delete_records(self::MARKER_TABLE, ['id' => $markerid]);
    }

    /**
     * Trigger marker event when the class exists.
     *
     * @param context_module $context Module context.
     * @param stdClass $marker Marker record.
     * @param string $oldstate Previous state.
     * @param string $action Event action.
     * @return void
     */
    private static function trigger_marker_event(
        context_module $context,
        stdClass $marker,
        string $oldstate,
        string $action
    ): void {
        $eventclass = '\\mod_uckkarchive\\event\\content_marker_reviewed';

        if (!class_exists($eventclass)) {
            return;
        }

        $event = $eventclass::create([
            'context' => $context,
            'objectid' => (int)$marker->id,
            'other' => [
                'action' => $action,
                'oldstate' => $oldstate,
                'newstate' => (string)($marker->reviewstate ?? ''),
                'uuid' => (string)($marker->uuid ?? ''),
            ],
        ]);

        if (!empty($marker->id)) {
            $event->add_record_snapshot(self::MARKER_TABLE, $marker);
        }

        $event->trigger();
    }

    /**
     * Build a standard external warning.
     *
     * @param string $item Warning item.
     * @param int $itemid Item id.
     * @param string $warningcode Warning code.
     * @param string $message Message.
     * @return array<string, mixed>
     */
    private static function warning(
        string $item,
        int $itemid,
        string $warningcode,
        string $message
    ): array {
        return [
            'item' => $item,
            'itemid' => $itemid,
            'warningcode' => $warningcode,
            'message' => $message,
        ];
    }
}
