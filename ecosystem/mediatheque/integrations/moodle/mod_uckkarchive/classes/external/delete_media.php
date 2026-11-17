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
 * Delete or soft-delete a media record.
 *
 * @package    mod_uckkarchive
 * @copyright  2026 UCKK
 * @license    https://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later
 */

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
use mod_uckkarchive\event\media_updated;
use mod_uckkarchive\local\file_area_registry;
use moodle_exception;
use required_capability_exception;
use stdClass;

/**
 * External service for deleting media records.
 *
 * The default operation is a soft delete. It marks the media object as
 * deleted_soft while preserving provenance, versions, relations, advisory
 * markers, audit data, and Moodle File API files.
 *
 * Physical file purge is intentionally optional and disabled by default.
 * Runtime policy must remain fail-closed for restricted, cultural, or
 * integrity-linked media.
 */
class delete_media extends external_api {

    /** @var string Media table. */
    private const MEDIA_TABLE = 'uckkarchive_media';

    /** @var string Media version table. */
    private const VERSION_TABLE = 'uckkarchive_media_version';

    /** @var string Deleted media status. */
    private const STATUS_DELETED_SOFT = 'deleted_soft';

    /** @var string Archived media status. */
    private const STATUS_ARCHIVED = 'archived';

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
            'mediaid' => new external_value(
                PARAM_INT,
                'Media record id to delete.'
            ),
            'reason' => new external_value(
                PARAM_TEXT,
                'Reason for deletion. Stored in metadata when metadata exists.',
                VALUE_DEFAULT,
                ''
            ),
            'purgefiles' => new external_value(
                PARAM_BOOL,
                'Whether to physically purge Moodle File API files. Defaults to false and should normally remain false.',
                VALUE_DEFAULT,
                false
            ),
        ]);
    }

    /**
     * Delete or soft-delete a media record.
     *
     * @param int $cmid Course module id.
     * @param int $mediaid Media id.
     * @param string $reason Deletion reason.
     * @param bool $purgefiles Whether to purge files.
     * @return array<string, mixed>
     * @throws dml_exception
     * @throws invalid_parameter_exception
     * @throws moodle_exception
     * @throws required_capability_exception
     */
    public static function execute(
        int $cmid,
        int $mediaid,
        string $reason = '',
        bool $purgefiles = false
    ): array {
        global $DB, $USER;

        $params = self::validate_parameters(self::execute_parameters(), [
            'cmid' => $cmid,
            'mediaid' => $mediaid,
            'reason' => $reason,
            'purgefiles' => $purgefiles,
        ]);

        [$course, $cm, $archive, $context] = self::load_page((int)$params['cmid']);
        self::validate_context($context);

        require_capability('mod/uckkarchive:deletemedia', $context);

        $media = self::get_media_record((int)$params['mediaid']);
        self::assert_media_belongs_to_activity($media, $archive, $cm, $context);
        self::assert_restricted_access_for_delete($media, $context);
        self::assert_media_can_be_deleted($media, $context);

        $warnings = [];
        $alreadydeleted = (($media->status ?? '') === self::STATUS_DELETED_SOFT);
        $filespurged = false;

        if ($alreadydeleted) {
            $warnings[] = self::warning(
                'media',
                (int)$media->id,
                'Media is already soft-deleted.'
            );

            return [
                'success' => true,
                'mediaid' => (int)$media->id,
                'uuid' => (string)($media->uuid ?? ''),
                'status' => self::STATUS_DELETED_SOFT,
                'alreadydeleted' => true,
                'filespurged' => false,
                'warnings' => $warnings,
            ];
        }

        $transaction = $DB->start_delegated_transaction();

        $oldstatus = (string)($media->status ?? '');
        $oldmetadata = self::decode_metadata($media->metadata ?? '');

        $media->status = self::STATUS_DELETED_SOFT;
        $media->timemodified = time();
        $media->modifiedby = (int)$USER->id;

        if (property_exists($media, 'deleted')) {
            $media->deleted = 1;
        }

        if (property_exists($media, 'metadata')) {
            $media->metadata = self::encode_metadata(array_merge($oldmetadata, [
                'deleted' => true,
                'deletedby' => (int)$USER->id,
                'deletedat' => time(),
                'deletereason' => trim($params['reason']),
                'previousstatus' => $oldstatus,
            ]));
        }

        $DB->update_record(self::MEDIA_TABLE, $media);

        self::archive_current_versions((int)$media->id);

        if (!empty($params['purgefiles'])) {
            require_capability('mod/uckkarchive:downloadmedia', $context);
            $filespurged = self::purge_media_files($context, (int)$media->id);
        }

        $updated = $DB->get_record(self::MEDIA_TABLE, ['id' => (int)$media->id], '*', MUST_EXIST);

        self::trigger_media_updated_event($context, $updated, $oldstatus, self::STATUS_DELETED_SOFT, $filespurged);

        $transaction->allow_commit();

        return [
            'success' => true,
            'mediaid' => (int)$updated->id,
            'uuid' => (string)($updated->uuid ?? ''),
            'status' => (string)$updated->status,
            'alreadydeleted' => false,
            'filespurged' => $filespurged,
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
            'success' => new external_value(PARAM_BOOL, 'Whether the delete operation succeeded.'),
            'mediaid' => new external_value(PARAM_INT, 'Deleted media id.'),
            'uuid' => new external_value(PARAM_RAW, 'Deleted media UUID.'),
            'status' => new external_value(PARAM_ALPHANUMEXT, 'Resulting media status.'),
            'alreadydeleted' => new external_value(PARAM_BOOL, 'Whether the media was already soft-deleted.'),
            'filespurged' => new external_value(PARAM_BOOL, 'Whether Moodle File API files were physically purged.'),
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
     * Get a media record.
     *
     * @param int $mediaid Media id.
     * @return stdClass
     * @throws dml_exception
     */
    private static function get_media_record(int $mediaid): stdClass {
        global $DB;

        return $DB->get_record(self::MEDIA_TABLE, ['id' => $mediaid], '*', MUST_EXIST);
    }

    /**
     * Ensure the media record belongs to this activity instance.
     *
     * @param stdClass $media Media record.
     * @param stdClass $archive Archive instance.
     * @param stdClass $cm Course module.
     * @param context_module $context Module context.
     * @return void
     * @throws moodle_exception
     */
    private static function assert_media_belongs_to_activity(
        stdClass $media,
        stdClass $archive,
        stdClass $cm,
        context_module $context
    ): void {
        if (isset($media->archiveid) && (int)$media->archiveid !== (int)$archive->id) {
            throw new moodle_exception('invalidmediaarchive', 'mod_uckkarchive');
        }

        if (isset($media->cmid) && (int)$media->cmid !== (int)$cm->id) {
            throw new moodle_exception('invalidmediacm', 'mod_uckkarchive');
        }

        if (isset($media->contextid) && (int)$media->contextid !== (int)$context->id) {
            throw new moodle_exception('invalidmediacontext', 'mod_uckkarchive');
        }
    }

    /**
     * Require additional access for restricted media.
     *
     * @param stdClass $media Media record.
     * @param context_module $context Module context.
     * @return void
     */
    private static function assert_restricted_access_for_delete(stdClass $media, context_module $context): void {
        $visibility = (string)($media->visibility ?? '');

        if (in_array($visibility, [
            self::VISIBILITY_RESTRICTED,
            self::VISIBILITY_RESTRICTED_INTEGRITY,
            self::VISIBILITY_RESTRICTED_CULTURAL,
        ], true)) {
            require_capability('mod/uckkarchive:viewrestrictedmedia', $context);
        }

        if ($visibility === self::VISIBILITY_RESTRICTED_CULTURAL) {
            require_capability('mod/uckkarchive:viewculturallyrestricted', $context);
        }
    }

    /**
     * Allow a future media_policy implementation to veto deletion.
     *
     * The local media policy class is the authority layer. This method avoids
     * binding to one exact signature while still using the policy if present.
     *
     * @param stdClass $media Media record.
     * @param context_module $context Module context.
     * @return void
     * @throws moodle_exception
     */
    private static function assert_media_can_be_deleted(stdClass $media, context_module $context): void {
        $policyclass = '\\mod_uckkarchive\\local\\media_policy';

        if (!class_exists($policyclass) || !method_exists($policyclass, 'can_delete')) {
            return;
        }

        $allowed = null;

        try {
            $allowed = $policyclass::can_delete($media, $context);
        } catch (\ArgumentCountError $exception) {
            $allowed = $policyclass::can_delete($media);
        }

        if ($allowed === false) {
            throw new moodle_exception('cannotdeletemedia', 'mod_uckkarchive');
        }
    }

    /**
     * Archive current media version records after a media soft delete.
     *
     * This does not delete version records and does not overwrite file history.
     *
     * @param int $mediaid Media id.
     * @return void
     * @throws dml_exception
     */
    private static function archive_current_versions(int $mediaid): void {
        global $DB;

        if (!$DB->get_manager()->table_exists(self::VERSION_TABLE)) {
            return;
        }

        $records = $DB->get_records(self::VERSION_TABLE, ['mediaid' => $mediaid]);

        foreach ($records as $record) {
            $changed = false;

            if (property_exists($record, 'iscurrent') && (int)$record->iscurrent === 1) {
                $record->iscurrent = 0;
                $changed = true;
            }

            if (property_exists($record, 'status')
                    && !in_array((string)$record->status, [self::STATUS_ARCHIVED, self::STATUS_DELETED_SOFT], true)) {
                $record->status = self::STATUS_ARCHIVED;
                $changed = true;
            }

            if ($changed) {
                $DB->update_record(self::VERSION_TABLE, $record);
            }
        }
    }

    /**
     * Purge media files from Moodle File API.
     *
     * This is intentionally not the default operation. Most archive use cases
     * should preserve files under soft-delete and retention policy.
     *
     * @param context_module $context Module context.
     * @param int $mediaid Media id.
     * @return bool
     * @throws dml_exception
     */
    private static function purge_media_files(context_module $context, int $mediaid): bool {
        global $DB;

        $fs = get_file_storage();

        $fileareas = class_exists(file_area_registry::class)
            ? file_area_registry::get_media_fileareas()
            : [
                'media_original',
                'media_preview',
                'media_thumbnail',
                'media_derivative',
                'media_caption',
                'media_transcript',
                'media_attachment',
            ];

        foreach ($fileareas as $filearea) {
            $fs->delete_area_files($context->id, 'mod_uckkarchive', $filearea, $mediaid);
        }

        if ($DB->get_manager()->table_exists(self::VERSION_TABLE)) {
            $versions = $DB->get_records(self::VERSION_TABLE, ['mediaid' => $mediaid], '', 'id');

            foreach ($versions as $version) {
                foreach ($fileareas as $filearea) {
                    $fs->delete_area_files($context->id, 'mod_uckkarchive', $filearea, (int)$version->id);
                }
            }
        }

        return true;
    }

    /**
     * Trigger media_updated event when the event class exists.
     *
     * @param context_module $context Module context.
     * @param stdClass $media Media record.
     * @param string $oldstatus Previous status.
     * @param string $newstatus New status.
     * @param bool $filespurged Whether files were purged.
     * @return void
     */
    private static function trigger_media_updated_event(
        context_module $context,
        stdClass $media,
        string $oldstatus,
        string $newstatus,
        bool $filespurged
    ): void {
        if (!class_exists(media_updated::class)) {
            return;
        }

        $event = media_updated::create([
            'context' => $context,
            'objectid' => (int)$media->id,
            'other' => [
                'action' => 'delete_media',
                'oldstatus' => $oldstatus,
                'newstatus' => $newstatus,
                'filespurged' => $filespurged,
            ],
        ]);

        $event->add_record_snapshot(self::MEDIA_TABLE, $media);
        $event->trigger();
    }

    /**
     * Decode JSON metadata.
     *
     * @param string|null $metadata Metadata JSON.
     * @return array<string, mixed>
     */
    private static function decode_metadata(?string $metadata): array {
        if (empty($metadata)) {
            return [];
        }

        $decoded = json_decode($metadata, true);

        return is_array($decoded) ? $decoded : [];
    }

    /**
     * Encode metadata as JSON.
     *
     * @param array<string, mixed> $metadata Metadata.
     * @return string
     */
    private static function encode_metadata(array $metadata): string {
        return json_encode($metadata, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
    }

    /**
     * Build a standard external warning.
     *
     * @param string $item Warning item.
     * @param int $itemid Item id.
     * @param string $message Message.
     * @param string $warningcode Warning code.
     * @return array<string, mixed>
     */
    private static function warning(
        string $item,
        int $itemid,
        string $message,
        string $warningcode = 'notice'
    ): array {
        return [
            'item' => $item,
            'itemid' => $itemid,
            'warningcode' => $warningcode,
            'message' => $message,
        ];
    }
}
