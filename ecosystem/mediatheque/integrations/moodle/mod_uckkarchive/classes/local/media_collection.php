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
 * Media collection domain service for UCKK Archive.
 *
 * @package    mod_uckkarchive
 * @copyright  2026 UCKK
 * @license    http://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later
 */

namespace mod_uckkarchive\local;

defined('MOODLE_INTERNAL') || die();

/**
 * Media collection domain service.
 *
 * This class owns collection-level persistence rules only. It does not replace
 * Moodle capabilities or the media policy layer. External services and page
 * controllers must check context, capabilities, visibility, and policy before
 * calling write methods.
 */
final class media_collection {
    /** @var string Collection table. */
    private const TABLE = 'uckkarchive_media_collection';

    /** @var string Collection membership table. */
    private const ITEM_TABLE = 'uckkarchive_media_collection_item';

    /** @var string Media table. */
    private const MEDIA_TABLE = 'uckkarchive_media';

    /** @var string Draft collection status. */
    public const STATUS_DRAFT = 'draft';

    /** @var string Active collection status. */
    public const STATUS_ACTIVE = 'active';

    /** @var string Restricted collection status. */
    public const STATUS_RESTRICTED = 'restricted';

    /** @var string Archived collection status. */
    public const STATUS_ARCHIVED = 'archived';

    /** @var string Soft-deleted collection status. */
    public const STATUS_DELETED_SOFT = 'deleted_soft';

    /** @var string Private visibility. */
    public const VISIBILITY_PRIVATE = 'private';

    /** @var string Course visibility. */
    public const VISIBILITY_COURSE = 'course';

    /** @var string Restricted visibility. */
    public const VISIBILITY_RESTRICTED = 'restricted';

    /** @var string Restricted cultural visibility. */
    public const VISIBILITY_RESTRICTED_CULTURAL = 'restricted_cultural';

    /** @var string Restricted integrity visibility. */
    public const VISIBILITY_RESTRICTED_INTEGRITY = 'restricted_integrity';

    /**
     * Create a media collection.
     *
     * Expected data keys:
     * - archiveid
     * - courseid
     * - cmid
     * - contextid
     * - title
     * - description
     * - visibility
     * - status
     * - purpose
     * - metadata
     *
     * @param array|\stdClass $data Collection data.
     * @param int $userid Acting user id.
     * @return \stdClass Created collection record.
     */
    public static function create($data, int $userid): \stdClass {
        global $DB;

        $data = (object)$data;
        $now = time();

        $record = new \stdClass();
        $record->uuid = self::generate_uuid();
        $record->archiveid = self::required_int($data, 'archiveid');

        // Collections are owned by one library. Legacy callers fall back to UCKK,
        // while modern callers can pass an explicit libraryid.
        $record->libraryid = self::optional_int($data, 'libraryid');
        if ($record->libraryid <= 0 && media_library_scope::schema_ready()) {
            $libraryscope = new media_library_scope();
            $rootlibrary = $libraryscope->resolve_by_slug(media_library_scope::LIBRARY_UCKK);
            if ($rootlibrary) {
                $record->libraryid = (int)$rootlibrary->id;
            } else {
                unset($record->libraryid);
            }
        }
        $record->courseid = self::optional_int($data, 'courseid');
        $record->cmid = self::optional_int($data, 'cmid');
        $record->contextid = self::optional_int($data, 'contextid');
        $record->title = self::required_text($data, 'title', 255);
        $record->description = self::optional_text($data, 'description');
        $record->purpose = self::optional_text($data, 'purpose', 100);
        $record->visibility = self::normalize_visibility($data->visibility ?? self::VISIBILITY_COURSE);
        $record->status = self::normalize_status($data->status ?? self::STATUS_DRAFT);
        $record->createdby = $userid;
        $record->modifiedby = $userid;
        $record->timecreated = $now;
        $record->timemodified = $now;
        $record->metadata = self::encode_metadata($data->metadata ?? null);

        $record->id = $DB->insert_record(self::TABLE, $record);

        return $DB->get_record(self::TABLE, ['id' => $record->id], '*', MUST_EXIST);
    }

    /**
     * Get a collection by id.
     *
     * @param int $id Collection id.
     * @param int $strictness Moodle strictness constant.
     * @return \stdClass|false Collection record or false.
     */
    public static function get(int $id, int $strictness = MUST_EXIST) {
        global $DB;

        return $DB->get_record(self::TABLE, ['id' => $id], '*', $strictness);
    }

    /**
     * Get a collection by UUID.
     *
     * @param string $uuid Collection UUID.
     * @param int $strictness Moodle strictness constant.
     * @return \stdClass|false Collection record or false.
     */
    public static function get_by_uuid(string $uuid, int $strictness = MUST_EXIST) {
        global $DB;

        return $DB->get_record(self::TABLE, ['uuid' => $uuid], '*', $strictness);
    }

    /**
     * Update a media collection.
     *
     * @param int $id Collection id.
     * @param array|\stdClass $data Data to update.
     * @param int $userid Acting user id.
     * @return \stdClass Updated record.
     */
    public static function update(int $id, $data, int $userid): \stdClass {
        global $DB;

        $current = self::get($id);
        $data = (object)$data;

        $record = new \stdClass();
        $record->id = $current->id;

        if (property_exists($data, 'title')) {
            $record->title = self::required_text($data, 'title', 255);
        }
        if (property_exists($data, 'description')) {
            $record->description = self::optional_text($data, 'description');
        }
        if (property_exists($data, 'purpose')) {
            $record->purpose = self::optional_text($data, 'purpose', 100);
        }
        if (property_exists($data, 'visibility')) {
            $record->visibility = self::normalize_visibility($data->visibility);
        }
        if (property_exists($data, 'status')) {
            $record->status = self::normalize_status($data->status);
        }
        if (property_exists($data, 'metadata')) {
            $record->metadata = self::encode_metadata($data->metadata);
        }

        $record->modifiedby = $userid;
        $record->timemodified = time();

        $DB->update_record(self::TABLE, $record);

        return self::get($id);
    }

    /**
     * Soft-delete a collection.
     *
     * Membership records are preserved so retention, audit, export manifests,
     * and restore workflows can still describe the former collection.
     *
     * @param int $id Collection id.
     * @param int $userid Acting user id.
     * @return \stdClass Updated collection.
     */
    public static function soft_delete(int $id, int $userid): \stdClass {
        return self::update($id, ['status' => self::STATUS_DELETED_SOFT], $userid);
    }

    /**
     * Add media to a collection.
     *
     * @param int $collectionid Collection id.
     * @param int $mediaid Media id.
     * @param int $userid Acting user id.
     * @param int|null $sortorder Optional explicit sort order.
     * @param array|\stdClass|null $metadata Optional membership metadata.
     * @return \stdClass Membership record.
     */
    public static function add_media(
        int $collectionid,
        int $mediaid,
        int $userid,
        ?int $sortorder = null,
        $metadata = null
    ): \stdClass {
        global $DB;

        self::get($collectionid);
        self::require_media_exists($mediaid);

        $existing = $DB->get_record(self::ITEM_TABLE, [
            'collectionid' => $collectionid,
            'mediaid' => $mediaid,
        ]);

        if ($existing) {
            $update = new \stdClass();
            $update->id = $existing->id;
            $update->timemodified = time();
            $update->modifiedby = $userid;

            if ($sortorder !== null) {
                $update->sortorder = $sortorder;
            }
            if ($metadata !== null) {
                $update->metadata = self::encode_metadata($metadata);
            }

            $DB->update_record(self::ITEM_TABLE, $update);

            return $DB->get_record(self::ITEM_TABLE, ['id' => $existing->id], '*', MUST_EXIST);
        }

        $now = time();

        $record = new \stdClass();
        $record->collectionid = $collectionid;
        $record->mediaid = $mediaid;
        $record->sortorder = $sortorder ?? self::next_sortorder($collectionid);
        $record->createdby = $userid;
        $record->modifiedby = $userid;
        $record->timecreated = $now;
        $record->timemodified = $now;
        $record->metadata = self::encode_metadata($metadata);

        $record->id = $DB->insert_record(self::ITEM_TABLE, $record);

        return $DB->get_record(self::ITEM_TABLE, ['id' => $record->id], '*', MUST_EXIST);
    }

    /**
     * Remove media from a collection.
     *
     * @param int $collectionid Collection id.
     * @param int $mediaid Media id.
     * @return bool True when membership existed and was removed.
     */
    public static function remove_media(int $collectionid, int $mediaid): bool {
        global $DB;

        $existing = $DB->get_record(self::ITEM_TABLE, [
            'collectionid' => $collectionid,
            'mediaid' => $mediaid,
        ]);

        if (!$existing) {
            return false;
        }

        $DB->delete_records(self::ITEM_TABLE, ['id' => $existing->id]);

        return true;
    }

    /**
     * Return media records in a collection.
     *
     * @param int $collectionid Collection id.
     * @param int $limitfrom Offset.
     * @param int $limitnum Number of records.
     * @return array Media records keyed by media id.
     */
    public static function get_media(int $collectionid, int $limitfrom = 0, int $limitnum = 0): array {
        global $DB;

        self::get($collectionid);

        $sql = "SELECT m.*, ci.sortorder, ci.metadata AS collectionitemmetadata
                  FROM {" . self::MEDIA_TABLE . "} m
                  JOIN {" . self::ITEM_TABLE . "} ci ON ci.mediaid = m.id
                 WHERE ci.collectionid = :collectionid
              ORDER BY ci.sortorder ASC, ci.id ASC";

        return $DB->get_records_sql($sql, ['collectionid' => $collectionid], $limitfrom, $limitnum);
    }

    /**
     * Count media records in a collection.
     *
     * @param int $collectionid Collection id.
     * @return int Count.
     */
    public static function count_media(int $collectionid): int {
        global $DB;

        return (int)$DB->count_records(self::ITEM_TABLE, ['collectionid' => $collectionid]);
    }

    /**
     * Reorder collection membership.
     *
     * @param int $collectionid Collection id.
     * @param int[] $mediaids Media ids in desired order.
     * @param int $userid Acting user id.
     * @return void
     */
    public static function reorder(int $collectionid, array $mediaids, int $userid): void {
        global $DB;

        self::get($collectionid);

        $transaction = $DB->start_delegated_transaction();
        $sortorder = 0;
        $now = time();

        foreach ($mediaids as $mediaid) {
            $mediaid = (int)$mediaid;
            $membership = $DB->get_record(self::ITEM_TABLE, [
                'collectionid' => $collectionid,
                'mediaid' => $mediaid,
            ]);

            if (!$membership) {
                continue;
            }

            $record = new \stdClass();
            $record->id = $membership->id;
            $record->sortorder = $sortorder++;
            $record->modifiedby = $userid;
            $record->timemodified = $now;
            $DB->update_record(self::ITEM_TABLE, $record);
        }

        $transaction->allow_commit();
    }

    /**
     * Find collections by archive id.
     *
     * @param int $archiveid Archive instance id.
     * @param array $filters Optional filters: status, visibility, search.
     * @param int $limitfrom Offset.
     * @param int $limitnum Number of records.
     * @return array Collection records.
     */
    public static function get_collections_by_archive(
        int $archiveid,
        array $filters = [],
        int $limitfrom = 0,
        int $limitnum = 0
    ): array {
        global $DB;

        $where = ['archiveid = :archiveid'];
        $params = ['archiveid' => $archiveid];

        if (!empty($filters['status'])) {
            $where[] = 'status = :status';
            $params['status'] = self::normalize_status($filters['status']);
        }

        if (!empty($filters['visibility'])) {
            $where[] = 'visibility = :visibility';
            $params['visibility'] = self::normalize_visibility($filters['visibility']);
        }

        if (!empty($filters['search'])) {
            $search = $DB->sql_like('title', ':search', false, false);
            $where[] = $search;
            $params['search'] = '%' . $DB->sql_like_escape($filters['search']) . '%';
        }

        $sql = "SELECT *
                  FROM {" . self::TABLE . "}
                 WHERE " . implode(' AND ', $where) . "
              ORDER BY timemodified DESC, id DESC";

        return $DB->get_records_sql($sql, $params, $limitfrom, $limitnum);
    }

    /**
     * Check whether a media id is already in a collection.
     *
     * @param int $collectionid Collection id.
     * @param int $mediaid Media id.
     * @return bool
     */
    public static function contains_media(int $collectionid, int $mediaid): bool {
        global $DB;

        return $DB->record_exists(self::ITEM_TABLE, [
            'collectionid' => $collectionid,
            'mediaid' => $mediaid,
        ]);
    }

    /**
     * Normalize status.
     *
     * @param string $status Status.
     * @return string
     */
    public static function normalize_status(string $status): string {
        $status = trim($status);

        $allowed = [
            self::STATUS_DRAFT,
            self::STATUS_ACTIVE,
            self::STATUS_RESTRICTED,
            self::STATUS_ARCHIVED,
            self::STATUS_DELETED_SOFT,
        ];

        if (!in_array($status, $allowed, true)) {
            throw new \invalid_parameter_exception('Invalid media collection status.');
        }

        return $status;
    }

    /**
     * Normalize visibility.
     *
     * @param string $visibility Visibility.
     * @return string
     */
    public static function normalize_visibility(string $visibility): string {
        $visibility = trim($visibility);

        if ($visibility === 'institutional') {
            $visibility = 'institution';
        }

        $allowed = [
            self::VISIBILITY_PRIVATE,
            self::VISIBILITY_COURSE,
            self::VISIBILITY_RESTRICTED,
            self::VISIBILITY_RESTRICTED_CULTURAL,
            self::VISIBILITY_RESTRICTED_INTEGRITY,
            'user',
            'group',
            'cohort',
            'program',
            'institution',
            'public',
        ];

        if (!in_array($visibility, $allowed, true)) {
            throw new \invalid_parameter_exception('Invalid media collection visibility.');
        }

        return $visibility;
    }

    /**
     * Get next sort order for a collection.
     *
     * @param int $collectionid Collection id.
     * @return int Sort order.
     */
    private static function next_sortorder(int $collectionid): int {
        global $DB;

        $sql = "SELECT MAX(sortorder)
                  FROM {" . self::ITEM_TABLE . "}
                 WHERE collectionid = :collectionid";

        $max = $DB->get_field_sql($sql, ['collectionid' => $collectionid]);

        return $max === null ? 0 : ((int)$max + 1);
    }

    /**
     * Require media record exists.
     *
     * @param int $mediaid Media id.
     * @return void
     */
    private static function require_media_exists(int $mediaid): void {
        global $DB;

        if (!$DB->record_exists(self::MEDIA_TABLE, ['id' => $mediaid])) {
            throw new \moodle_exception('invalidmediaid', 'mod_uckkarchive');
        }
    }

    /**
     * Get required int field.
     *
     * @param \stdClass $data Data object.
     * @param string $field Field name.
     * @return int
     */
    private static function required_int(\stdClass $data, string $field): int {
        if (!isset($data->{$field}) || (int)$data->{$field} <= 0) {
            throw new \invalid_parameter_exception('Missing required field: ' . $field);
        }

        return (int)$data->{$field};
    }

    /**
     * Get optional int field.
     *
     * @param \stdClass $data Data object.
     * @param string $field Field name.
     * @return int
     */
    private static function optional_int(\stdClass $data, string $field): int {
        if (!isset($data->{$field})) {
            return 0;
        }

        return max(0, (int)$data->{$field});
    }

    /**
     * Get required text field.
     *
     * @param \stdClass $data Data object.
     * @param string $field Field name.
     * @param int $maxlength Max length.
     * @return string
     */
    private static function required_text(\stdClass $data, string $field, int $maxlength): string {
        if (!isset($data->{$field}) || trim((string)$data->{$field}) === '') {
            throw new \invalid_parameter_exception('Missing required field: ' . $field);
        }

        return self::truncate(clean_param((string)$data->{$field}, PARAM_TEXT), $maxlength);
    }

    /**
     * Get optional text field.
     *
     * @param \stdClass $data Data object.
     * @param string $field Field name.
     * @param int|null $maxlength Optional max length.
     * @return string
     */
    private static function optional_text(\stdClass $data, string $field, ?int $maxlength = null): string {
        if (!isset($data->{$field})) {
            return '';
        }

        $value = clean_param((string)$data->{$field}, PARAM_TEXT);

        return $maxlength === null ? $value : self::truncate($value, $maxlength);
    }

    /**
     * Encode metadata as JSON.
     *
     * @param mixed $metadata Metadata value.
     * @return string
     */
    private static function encode_metadata($metadata): string {
        if ($metadata === null || $metadata === '') {
            return '{}';
        }

        if (is_string($metadata)) {
            json_decode($metadata);
            if (json_last_error() === JSON_ERROR_NONE) {
                return $metadata;
            }

            return json_encode(['value' => $metadata], JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
        }

        $json = json_encode($metadata, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);

        if ($json === false) {
            throw new \invalid_parameter_exception('Invalid metadata.');
        }

        return $json;
    }

    /**
     * Generate UUID v4.
     *
     * This method is intentionally local so this class can be generated before
     * classes/local/uuid.php. Once uuid.php is available, callers may replace
     * this with the shared UUID service.
     *
     * @return string UUID.
     */
    private static function generate_uuid(): string {
        $bytes = random_bytes(16);
        $bytes[6] = chr((ord($bytes[6]) & 0x0f) | 0x40);
        $bytes[8] = chr((ord($bytes[8]) & 0x3f) | 0x80);

        return vsprintf('%s%s-%s-%s-%s-%s%s%s', str_split(bin2hex($bytes), 4));
    }

    /**
     * Truncate a string safely.
     *
     * @param string $value Value.
     * @param int $maxlength Max length.
     * @return string
     */
    private static function truncate(string $value, int $maxlength): string {
        if (function_exists('core_text::substr')) {
            return \core_text::substr($value, 0, $maxlength);
        }

        return mb_substr($value, 0, $maxlength);
    }
}
