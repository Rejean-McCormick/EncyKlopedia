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
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with Moodle.  If not, see <http://www.gnu.org/licenses/>.

/**
 * External service for adding media to a media collection.
 *
 * @package    mod_uckkarchive
 * @copyright  2026 UCKK
 * @license    http://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later
 */

namespace mod_uckkarchive\external;

defined('MOODLE_INTERNAL') || die();

global $CFG;
require_once($CFG->libdir . '/externallib.php');

use external_api;
use external_function_parameters;
use external_multiple_structure;
use external_single_structure;
use external_value;
use invalid_parameter_exception;
use mod_uckkarchive\local\context_resolver;
use mod_uckkarchive\local\media_collection;
use mod_uckkarchive\local\media_policy;
use stdClass;

/**
 * Add media to collection external service.
 *
 * Collections group media objects without duplicating files.
 * Collection membership does not override media-level restrictions.
 *
 * Target service name:
 *
 * ```text
 * mod_uckkarchive_add_media_to_collection
 * ```
 */
final class add_media_to_collection extends external_api {
    /** Media table. */
    private const MEDIA_TABLE = 'uckkarchive_media';

    /** Collection table. */
    private const COLLECTION_TABLE = 'uckkarchive_media_collection';

    /** Collection membership table. */
    private const ITEM_TABLE = 'uckkarchive_media_collection_item';

    /**
     * Describe service parameters.
     *
     * @return external_function_parameters
     */
    public static function execute_parameters(): external_function_parameters {
        return new external_function_parameters([
            'cmid' => new external_value(PARAM_INT, 'Course module id for the UCKK Archive instance.'),
            'collectionid' => new external_value(PARAM_INT, 'Media collection id.'),
            'mediaid' => new external_value(PARAM_INT, 'Media id to add to the collection.'),
            'sortorder' => new external_value(PARAM_INT, 'Optional explicit sort order. Use -1 for append.', VALUE_DEFAULT, -1),
            'metadata' => new external_single_structure([
                'role' => new external_value(PARAM_ALPHANUMEXT, 'Membership role or grouping key.', VALUE_DEFAULT, ''),
                'note' => new external_value(PARAM_TEXT, 'Membership note.', VALUE_DEFAULT, ''),
                'purpose' => new external_value(PARAM_TEXT, 'Reason this media belongs to the collection.', VALUE_DEFAULT, ''),
            ], 'Optional membership metadata.', VALUE_DEFAULT, []),
        ]);
    }

    /**
     * Execute service.
     *
     * @param int $cmid Course module id.
     * @param int $collectionid Collection id.
     * @param int $mediaid Media id.
     * @param int $sortorder Sort order, or -1 to append.
     * @param array $metadata Membership metadata.
     * @return array Result.
     */
    public static function execute(
        int $cmid,
        int $collectionid,
        int $mediaid,
        int $sortorder = -1,
        array $metadata = []
    ): array {
        global $DB, $USER;

        [
            'cmid' => $cmid,
            'collectionid' => $collectionid,
            'mediaid' => $mediaid,
            'sortorder' => $sortorder,
            'metadata' => $metadata,
        ] = self::validate_parameters(self::execute_parameters(), [
            'cmid' => $cmid,
            'collectionid' => $collectionid,
            'mediaid' => $mediaid,
            'sortorder' => $sortorder,
            'metadata' => $metadata,
        ]);

        self::require_positive($cmid, 'cmid');
        self::require_positive($collectionid, 'collectionid');
        self::require_positive($mediaid, 'mediaid');

        $resolution = context_resolver::from_cmid($cmid);
        context_resolver::require_login_for($resolution);
        self::validate_context($resolution->context);

        require_capability('mod/uckkarchive:viewmedia', $resolution->context);
        require_capability('mod/uckkarchive:managemediacollections', $resolution->context);

        self::require_domain_service();

        $collection = media_collection::get($collectionid, MUST_EXIST);
        $media = $DB->get_record(self::MEDIA_TABLE, ['id' => $mediaid], '*', MUST_EXIST);

        self::require_same_archive($resolution, $collection, 'collection');
        self::require_same_archive($resolution, $media, 'media');
        self::require_viewable_collection($resolution, $collection);
        self::require_viewable_media($resolution, $media);

        $alreadyexists = media_collection::contains_media($collectionid, $mediaid);
        $normalizedmetadata = self::normalize_metadata($metadata);

        $membership = media_collection::add_media(
            $collectionid,
            $mediaid,
            (int)$USER->id,
            $sortorder >= 0 ? $sortorder : null,
            $normalizedmetadata
        );

        $membership = $DB->get_record(self::ITEM_TABLE, ['id' => $membership->id], '*', MUST_EXIST);

        return [
            'status' => true,
            'created' => !$alreadyexists,
            'membership' => self::format_membership($membership),
            'collection' => self::format_collection($collection),
            'media' => self::format_media($media),
            'permissions' => self::format_permissions($resolution->context),
            'warnings' => $alreadyexists ? [
                self::warning('membership', (int)$membership->id, 'alreadyexists',
                    'The media record was already in the collection; membership metadata or sort order was updated.')
            ] : [],
        ];
    }

    /**
     * Describe service return structure.
     *
     * @return external_single_structure
     */
    public static function execute_returns(): external_single_structure {
        return new external_single_structure([
            'status' => new external_value(PARAM_BOOL, 'Whether the operation completed.'),
            'created' => new external_value(PARAM_BOOL, 'Whether a new collection membership was created.'),
            'membership' => new external_single_structure([
                'id' => new external_value(PARAM_INT, 'Collection membership id.'),
                'collectionid' => new external_value(PARAM_INT, 'Collection id.'),
                'mediaid' => new external_value(PARAM_INT, 'Media id.'),
                'sortorder' => new external_value(PARAM_INT, 'Sort order.'),
                'metadata' => new external_value(PARAM_RAW, 'Membership metadata JSON.'),
                'createdby' => new external_value(PARAM_INT, 'Creator user id.'),
                'modifiedby' => new external_value(PARAM_INT, 'Modifier user id.'),
                'timecreated' => new external_value(PARAM_INT, 'Created timestamp.'),
                'timemodified' => new external_value(PARAM_INT, 'Modified timestamp.'),
            ]),
            'collection' => new external_single_structure([
                'id' => new external_value(PARAM_INT, 'Collection id.'),
                'uuid' => new external_value(PARAM_RAW, 'Collection UUID.'),
                'title' => new external_value(PARAM_TEXT, 'Collection title.'),
                'visibility' => new external_value(PARAM_ALPHANUMEXT, 'Collection visibility.'),
                'status' => new external_value(PARAM_ALPHANUMEXT, 'Collection status.'),
                'media_count' => new external_value(PARAM_INT, 'Number of media records in the collection.'),
            ]),
            'media' => new external_single_structure([
                'id' => new external_value(PARAM_INT, 'Media id.'),
                'uuid' => new external_value(PARAM_RAW, 'Media UUID.'),
                'title' => new external_value(PARAM_TEXT, 'Media title.'),
                'mediatype' => new external_value(PARAM_ALPHANUMEXT, 'Media type.'),
                'visibility' => new external_value(PARAM_ALPHANUMEXT, 'Media visibility.'),
                'status' => new external_value(PARAM_ALPHANUMEXT, 'Media status.'),
            ]),
            'permissions' => new external_single_structure([
                'canviewmedia' => new external_value(PARAM_BOOL, 'Can view media.'),
                'canaddmedia' => new external_value(PARAM_BOOL, 'Can add media.'),
                'caneditmedia' => new external_value(PARAM_BOOL, 'Can edit media.'),
                'canmanagemediacollections' => new external_value(PARAM_BOOL, 'Can manage media collections.'),
                'canviewrestrictedmedia' => new external_value(PARAM_BOOL, 'Can view restricted media.'),
                'canviewculturallyrestricted' => new external_value(PARAM_BOOL, 'Can view culturally restricted material.'),
            ]),
            'warnings' => new external_multiple_structure(
                new external_single_structure([
                    'item' => new external_value(PARAM_TEXT, 'Warning item.'),
                    'itemid' => new external_value(PARAM_INT, 'Warning item id.'),
                    'warningcode' => new external_value(PARAM_ALPHANUMEXT, 'Warning code.'),
                    'message' => new external_value(PARAM_TEXT, 'Warning message.'),
                ]),
                'Warnings.'
            ),
        ]);
    }

    /**
     * Require media collection domain service.
     *
     * @return void
     */
    private static function require_domain_service(): void {
        if (!class_exists(media_collection::class) ||
                !method_exists(media_collection::class, 'add_media') ||
                !method_exists(media_collection::class, 'contains_media')) {
            throw new \coding_exception('The media collection domain service must implement add_media() and contains_media().');
        }
    }

    /**
     * Ensure a domain record belongs to the resolved archive instance.
     *
     * @param stdClass $resolution Resolved Moodle context.
     * @param stdClass $record Domain record.
     * @param string $name Record name.
     * @return void
     */
    private static function require_same_archive(stdClass $resolution, stdClass $record, string $name): void {
        $archiveid = self::field_int($record, ['archiveid', 'uckkarchiveid', 'instanceid'], 0);

        if ($archiveid <= 0) {
            throw new invalid_parameter_exception('The ' . $name . ' record does not include an archive id.');
        }

        if ($archiveid !== (int)$resolution->archiveid) {
            throw new invalid_parameter_exception('The ' . $name . ' record does not belong to this UCKK Archive activity.');
        }
    }

    /**
     * Require collection view/manage policy.
     *
     * @param stdClass $resolution Resolution.
     * @param stdClass $collection Collection record.
     * @return void
     */
    private static function require_viewable_collection(stdClass $resolution, stdClass $collection): void {
        if (class_exists(media_policy::class) &&
                method_exists(media_policy::class, 'can_manage_collections') &&
                !media_policy::can_manage_collections($resolution->context)) {
            throw new \required_capability_exception(
                $resolution->context,
                'mod/uckkarchive:managemediacollections',
                'nopermissions',
                ''
            );
        }

        if (class_exists(media_policy::class) &&
                method_exists(media_policy::class, 'can_view_collection') &&
                !media_policy::can_view_collection($resolution->context, $collection)) {
            throw new \required_capability_exception(
                $resolution->context,
                'mod/uckkarchive:viewmedia',
                'nopermissions',
                ''
            );
        }
    }

    /**
     * Require media view policy.
     *
     * @param stdClass $resolution Resolution.
     * @param stdClass $media Media record.
     * @return void
     */
    private static function require_viewable_media(stdClass $resolution, stdClass $media): void {
        if (class_exists(media_policy::class) &&
                method_exists(media_policy::class, 'can_view_media') &&
                !media_policy::can_view_media($resolution->context, $media)) {
            throw new \required_capability_exception(
                $resolution->context,
                'mod/uckkarchive:viewmedia',
                'nopermissions',
                ''
            );
        }

        $visibility = (string)($media->visibility ?? '');
        $status = (string)($media->status ?? '');

        if (($visibility === 'restricted' || $visibility === 'restricted_integrity' || $status === 'restricted') &&
                !has_capability('mod/uckkarchive:viewrestrictedmedia', $resolution->context) &&
                !has_capability('mod/uckkarchive:viewrestricted', $resolution->context)) {
            throw new \required_capability_exception(
                $resolution->context,
                'mod/uckkarchive:viewrestrictedmedia',
                'nopermissions',
                ''
            );
        }

        if ($visibility === 'restricted_cultural' &&
                !has_capability('mod/uckkarchive:viewculturallyrestricted', $resolution->context)) {
            throw new \required_capability_exception(
                $resolution->context,
                'mod/uckkarchive:viewculturallyrestricted',
                'nopermissions',
                ''
            );
        }
    }

    /**
     * Format membership record.
     *
     * @param stdClass $membership Membership record.
     * @return array
     */
    private static function format_membership(stdClass $membership): array {
        return [
            'id' => (int)$membership->id,
            'collectionid' => (int)$membership->collectionid,
            'mediaid' => (int)$membership->mediaid,
            'sortorder' => (int)($membership->sortorder ?? 0),
            'metadata' => (string)($membership->metadata ?? '{}'),
            'createdby' => (int)($membership->createdby ?? 0),
            'modifiedby' => (int)($membership->modifiedby ?? 0),
            'timecreated' => (int)($membership->timecreated ?? 0),
            'timemodified' => (int)($membership->timemodified ?? 0),
        ];
    }

    /**
     * Format collection record.
     *
     * @param stdClass $collection Collection record.
     * @return array
     */
    private static function format_collection(stdClass $collection): array {
        return [
            'id' => (int)$collection->id,
            'uuid' => (string)($collection->uuid ?? ''),
            'title' => (string)($collection->title ?? ''),
            'visibility' => (string)($collection->visibility ?? 'course'),
            'status' => (string)($collection->status ?? 'draft'),
            'media_count' => class_exists(media_collection::class) && method_exists(media_collection::class, 'count_media')
                ? media_collection::count_media((int)$collection->id)
                : 0,
        ];
    }

    /**
     * Format media record.
     *
     * @param stdClass $media Media record.
     * @return array
     */
    private static function format_media(stdClass $media): array {
        return [
            'id' => (int)$media->id,
            'uuid' => (string)($media->uuid ?? ''),
            'title' => (string)($media->title ?? ''),
            'mediatype' => (string)($media->mediatype ?? 'other'),
            'visibility' => (string)($media->visibility ?? 'restricted'),
            'status' => (string)($media->status ?? 'draft'),
        ];
    }

    /**
     * Format permissions.
     *
     * @param \context_module $context Module context.
     * @return array
     */
    private static function format_permissions(\context_module $context): array {
        return [
            'canviewmedia' => has_capability('mod/uckkarchive:viewmedia', $context),
            'canaddmedia' => has_capability('mod/uckkarchive:addmedia', $context),
            'caneditmedia' => has_capability('mod/uckkarchive:editmedia', $context),
            'canmanagemediacollections' => has_capability('mod/uckkarchive:managemediacollections', $context),
            'canviewrestrictedmedia' => has_capability('mod/uckkarchive:viewrestrictedmedia', $context),
            'canviewculturallyrestricted' => has_capability('mod/uckkarchive:viewculturallyrestricted', $context),
        ];
    }

    /**
     * Normalize membership metadata.
     *
     * @param array $metadata Metadata.
     * @return array
     */
    private static function normalize_metadata(array $metadata): array {
        return [
            'role' => clean_param((string)($metadata['role'] ?? ''), PARAM_ALPHANUMEXT),
            'note' => clean_param((string)($metadata['note'] ?? ''), PARAM_TEXT),
            'purpose' => clean_param((string)($metadata['purpose'] ?? ''), PARAM_TEXT),
        ];
    }

    /**
     * Return warning payload.
     *
     * @param string $item Item.
     * @param int $itemid Item id.
     * @param string $code Code.
     * @param string $message Message.
     * @return array
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
     * Require positive int.
     *
     * @param int $value Value.
     * @param string $name Name.
     * @return void
     */
    private static function require_positive(int $value, string $name): void {
        if ($value <= 0) {
            throw new invalid_parameter_exception('Invalid ' . $name . '.');
        }
    }

    /**
     * Return first integer field from a record.
     *
     * @param stdClass $record Record.
     * @param string[] $fields Candidate fields.
     * @param int $default Default value.
     * @return int
     */
    private static function field_int(stdClass $record, array $fields, int $default = 0): int {
        foreach ($fields as $field) {
            if (isset($record->{$field}) && (int)$record->{$field} > 0) {
                return (int)$record->{$field};
            }
        }

        return $default;
    }
}
