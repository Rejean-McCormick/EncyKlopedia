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

namespace mod_uckkarchive\local;

defined('MOODLE_INTERNAL') || die();

use coding_exception;
use dml_exception;
use invalid_parameter_exception;
use moodle_exception;
use stdClass;

/**
 * Domain service for media source records.
 *
 * A media source describes where a media object came from and what kind of
 * ownership or rights relationship applies. It supports UCKK-produced media,
 * submitted media, imported media, external references, licensed external
 * material, public-domain material, fair-use references, and restricted
 * references.
 *
 * This class owns validation and database access for the
 * uckkarchive_media_source table. It does not decide final access by itself;
 * media_policy and content_policy remain responsible for runtime access,
 * download, export, and restriction decisions.
 *
 * @package    mod_uckkarchive
 * @copyright  2026 UCKK
 * @license    https://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later
 */
final class media_source {

    /** @var string Database table name. */
    public const TABLE = 'uckkarchive_media_source';

    /** @var string Media was produced directly by UCKK. */
    public const SOURCE_PRODUCED_BY_UCKK = 'produced_by_uckk';

    /** @var string Media was submitted to UCKK by a member, learner, partner, or other contributor. */
    public const SOURCE_SUBMITTED_TO_UCKK = 'submitted_to_uckk';

    /** @var string Media was imported into the archive/media library. */
    public const SOURCE_IMPORTED = 'imported';

    /** @var string Media is represented as an external reference only. */
    public const SOURCE_EXTERNAL_REFERENCE_ONLY = 'external_reference_only';

    /** @var string Media is licensed external material. */
    public const SOURCE_LICENSED_EXTERNAL = 'licensed_external';

    /** @var string Media is identified as public domain. */
    public const SOURCE_PUBLIC_DOMAIN = 'public_domain';

    /** @var string Media is recorded as a fair-use reference. */
    public const SOURCE_FAIR_USE_REFERENCE = 'fair_use_reference';

    /** @var string Media is an external or internal reference that must remain restricted. */
    public const SOURCE_RESTRICTED_REFERENCE = 'restricted_reference';

    /** @var string UCKK created the media. */
    public const OWNERSHIP_UCKK_CREATED = 'uckk_created';

    /** @var string UCKK commissioned the media. */
    public const OWNERSHIP_UCKK_COMMISSIONED = 'uckk_commissioned';

    /** @var string A member submitted the media. */
    public const OWNERSHIP_MEMBER_SUBMITTED = 'member_submitted';

    /** @var string A partner submitted the media. */
    public const OWNERSHIP_PARTNER_SUBMITTED = 'partner_submitted';

    /** @var string The media is only an external reference. */
    public const OWNERSHIP_EXTERNAL_REFERENCE = 'external_reference';

    /** @var string A third party owns copyright or other rights. */
    public const OWNERSHIP_THIRD_PARTY_COPYRIGHT = 'third_party_copyright';

    /** @var string The media is public domain. */
    public const OWNERSHIP_PUBLIC_DOMAIN = 'public_domain';

    /** @var string The media is under an open license. */
    public const OWNERSHIP_OPEN_LICENSE = 'open_license';

    /** @var string Source ownership is unknown or unresolved. */
    public const OWNERSHIP_UNKNOWN_SOURCE = 'unknown_source';

    /**
     * Return canonical source types.
     *
     * @return string[]
     */
    public static function get_source_types(): array {
        return [
            self::SOURCE_PRODUCED_BY_UCKK,
            self::SOURCE_SUBMITTED_TO_UCKK,
            self::SOURCE_IMPORTED,
            self::SOURCE_EXTERNAL_REFERENCE_ONLY,
            self::SOURCE_LICENSED_EXTERNAL,
            self::SOURCE_PUBLIC_DOMAIN,
            self::SOURCE_FAIR_USE_REFERENCE,
            self::SOURCE_RESTRICTED_REFERENCE,
        ];
    }

    /**
     * Return canonical ownership values.
     *
     * @return string[]
     */
    public static function get_ownership_values(): array {
        return [
            self::OWNERSHIP_UCKK_CREATED,
            self::OWNERSHIP_UCKK_COMMISSIONED,
            self::OWNERSHIP_MEMBER_SUBMITTED,
            self::OWNERSHIP_PARTNER_SUBMITTED,
            self::OWNERSHIP_EXTERNAL_REFERENCE,
            self::OWNERSHIP_THIRD_PARTY_COPYRIGHT,
            self::OWNERSHIP_PUBLIC_DOMAIN,
            self::OWNERSHIP_OPEN_LICENSE,
            self::OWNERSHIP_UNKNOWN_SOURCE,
        ];
    }

    /**
     * Return whether a source type is valid.
     *
     * @param string $sourcetype Source type.
     * @return bool
     */
    public static function is_valid_source_type(string $sourcetype): bool {
        return in_array($sourcetype, self::get_source_types(), true);
    }

    /**
     * Return whether an ownership value is valid.
     *
     * @param string $ownership Ownership value.
     * @return bool
     */
    public static function is_valid_ownership(string $ownership): bool {
        return in_array($ownership, self::get_ownership_values(), true);
    }

    /**
     * Return default source type.
     *
     * Unknown media should not be assumed to be public or unrestricted.
     *
     * @return string
     */
    public static function get_default_source_type(): string {
        return self::SOURCE_RESTRICTED_REFERENCE;
    }

    /**
     * Return default ownership value.
     *
     * Unknown source must not be treated as public domain.
     *
     * @return string
     */
    public static function get_default_ownership(): string {
        return self::OWNERSHIP_UNKNOWN_SOURCE;
    }

    /**
     * Create a media source record.
     *
     * Required fields:
     * - contextid
     * - sourcetype
     * - ownership
     *
     * Common optional fields:
     * - mediaid
     * - archiveid
     * - externalworkid
     * - title
     * - creator
     * - publisher
     * - sourceyear
     * - sourceurl
     * - identifier
     * - licence
     * - rightsnote
     * - citation
     * - metadata
     *
     * @param stdClass|array $data Media source data.
     * @return stdClass Created record.
     * @throws coding_exception
     * @throws dml_exception
     * @throws invalid_parameter_exception
     */
    public static function create($data): stdClass {
        global $DB, $USER;

        $record = self::filter_to_table_fields(self::prepare_record($data, true));

        $now = time();
        $record->timecreated = $record->timecreated ?? $now;
        $record->timemodified = $record->timemodified ?? $now;
        $record->createdby = $record->createdby ?? (int)$USER->id;
        $record->modifiedby = $record->modifiedby ?? (int)$USER->id;

        if (empty($record->uuid)) {
            $record->uuid = self::generate_uuid();
        }

        $record->id = $DB->insert_record(self::TABLE, $record);

        return $DB->get_record(self::TABLE, ['id' => $record->id], '*', MUST_EXIST);
    }

    /**
     * Update an existing media source record.
     *
     * @param int $id Record id.
     * @param stdClass|array $data New data.
     * @return stdClass Updated record.
     * @throws dml_exception
     * @throws invalid_parameter_exception
     */
    public static function update(int $id, $data): stdClass {
        global $DB, $USER;

        $existing = self::get_by_id($id);
        $incoming = (object)$data;

        foreach ((array)$incoming as $field => $value) {
            if ($field === 'id') {
                continue;
            }
            $existing->{$field} = $value;
        }

        $record = self::filter_to_table_fields(self::prepare_record($existing, false));
        $record->id = $id;
        $record->timemodified = time();
        $record->modifiedby = (int)$USER->id;

        $DB->update_record(self::TABLE, $record);

        return $DB->get_record(self::TABLE, ['id' => $id], '*', MUST_EXIST);
    }

    /**
     * Get a media source by id.
     *
     * @param int $id Record id.
     * @return stdClass
     * @throws dml_exception
     */
    public static function get_by_id(int $id): stdClass {
        global $DB;

        return $DB->get_record(self::TABLE, ['id' => $id], '*', MUST_EXIST);
    }

    /**
     * Get a media source by UUID.
     *
     * @param string $uuid Stable UUID.
     * @return stdClass|null
     * @throws dml_exception
     */
    public static function get_by_uuid(string $uuid): ?stdClass {
        global $DB;

        return $DB->get_record(self::TABLE, ['uuid' => $uuid], '*') ?: null;
    }

    /**
     * Get all source records linked to a media object.
     *
     * @param int $mediaid Media id.
     * @return stdClass[]
     * @throws dml_exception
     */
    public static function get_for_media(int $mediaid): array {
        global $DB;

        return $DB->get_records(self::TABLE, ['mediaid' => $mediaid], 'timecreated ASC, id ASC');
    }

    /**
     * Get source records linked to an external work.
     *
     * @param int $externalworkid External work id.
     * @return stdClass[]
     * @throws dml_exception
     */
    public static function get_for_external_work(int $externalworkid): array {
        global $DB;

        return $DB->get_records(self::TABLE, ['externalworkid' => $externalworkid], 'timecreated ASC, id ASC');
    }

    /**
     * Soft-delete a media source when a deleted flag exists, otherwise delete.
     *
     * The target schema should prefer soft-deletion where audit and provenance
     * retention are required. This method supports both table variants so early
     * implementation can proceed safely.
     *
     * @param int $id Record id.
     * @return bool
     * @throws dml_exception
     */
    public static function delete(int $id): bool {
        global $DB, $USER;

        $record = self::get_by_id($id);

        if (property_exists($record, 'deleted')) {
            $record->deleted = 1;
            $record->timemodified = time();
            $record->modifiedby = (int)$USER->id;
            $DB->update_record(self::TABLE, $record);
            return true;
        }

        return $DB->delete_records(self::TABLE, ['id' => $id]);
    }

    /**
     * Return true if the source is UCKK-owned or UCKK-commissioned.
     *
     * @param stdClass $record Source record.
     * @return bool
     */
    public static function is_uckk_controlled(stdClass $record): bool {
        return in_array(self::ownership_value($record), [
            self::OWNERSHIP_UCKK_CREATED,
            self::OWNERSHIP_UCKK_COMMISSIONED,
        ], true);
    }

    /**
     * Return true if the source is external or third-party.
     *
     * @param stdClass $record Source record.
     * @return bool
     */
    public static function is_external(stdClass $record): bool {
        return in_array($record->sourcetype ?? '', [
            self::SOURCE_EXTERNAL_REFERENCE_ONLY,
            self::SOURCE_LICENSED_EXTERNAL,
            self::SOURCE_FAIR_USE_REFERENCE,
            self::SOURCE_RESTRICTED_REFERENCE,
        ], true) || in_array($record->ownership ?? '', [
            self::OWNERSHIP_EXTERNAL_REFERENCE,
            self::OWNERSHIP_THIRD_PARTY_COPYRIGHT,
            self::OWNERSHIP_UNKNOWN_SOURCE,
        ], true);
    }

    /**
     * Return true if the media source is only a reference and should not imply
     * local ownership or local file custody.
     *
     * @param stdClass $record Source record.
     * @return bool
     */
    public static function is_reference_only(stdClass $record): bool {
        return ($record->sourcetype ?? '') === self::SOURCE_EXTERNAL_REFERENCE_ONLY;
    }

    /**
     * Return true when this source should default to restricted handling.
     *
     * @param stdClass $record Source record.
     * @return bool
     */
    public static function requires_restricted_handling(stdClass $record): bool {
        if (($record->sourcetype ?? '') === self::SOURCE_RESTRICTED_REFERENCE) {
            return true;
        }

        if (self::ownership_value($record) === self::OWNERSHIP_UNKNOWN_SOURCE) {
            return true;
        }

        if (self::ownership_value($record) === self::OWNERSHIP_THIRD_PARTY_COPYRIGHT
                && empty($record->licence) && empty($record->license) && empty($record->rightsnote)) {
            return true;
        }

        return false;
    }

    /**
     * Decode metadata JSON from a record.
     *
     * @param stdClass $record Source record.
     * @return array
     */
    public static function get_metadata(stdClass $record): array {
        if (empty($record->metadata)) {
            return [];
        }

        $decoded = json_decode($record->metadata, true);

        return is_array($decoded) ? $decoded : [];
    }

    /**
     * Set one metadata value on a source record and save it.
     *
     * @param int $id Source id.
     * @param string $key Metadata key.
     * @param mixed $value Metadata value.
     * @return stdClass Updated record.
     * @throws dml_exception
     * @throws invalid_parameter_exception
     */
    public static function set_metadata_value(int $id, string $key, $value): stdClass {
        $record = self::get_by_id($id);
        $metadata = self::get_metadata($record);
        $metadata[$key] = $value;

        return self::update($id, ['metadata' => $metadata]);
    }

    /**
     * Prepare a record for insert/update.
     *
     * @param stdClass|array $data Input data.
     * @param bool $creating Whether this is a create operation.
     * @return stdClass
     * @throws invalid_parameter_exception
     */
    private static function prepare_record($data, bool $creating): stdClass {
        $record = (object)$data;

        if ($creating && empty($record->contextid)) {
            throw new invalid_parameter_exception('Missing required field: contextid');
        }

        $record->contextid = isset($record->contextid) ? (int)$record->contextid : null;
        $record->mediaid = isset($record->mediaid) ? (int)$record->mediaid : null;
        $record->archiveid = isset($record->archiveid) ? (int)$record->archiveid : null;
        $record->externalworkid = isset($record->externalworkid) ? (int)$record->externalworkid : null;

        $record->sourcetype = self::normalize_source_type($record->sourcetype ?? self::get_default_source_type());
        $ownership = self::normalize_ownership($record->ownership ?? self::get_default_ownership());

        // The released Moodle schema uses sourceauthor/license plus generic JSON
        // metadata, while older service callers used creator/licence/ownership and
        // richer bibliographic aliases. Preserve the public API and translate it
        // to whichever columns are actually installed.
        if (empty($record->sourceauthor) && !empty($record->creator)) {
            $record->sourceauthor = $record->creator;
        }
        if (empty($record->license) && !empty($record->licence)) {
            $record->license = $record->licence;
        }
        if (empty($record->sourceobjectid) && !empty($record->sourceitemid)) {
            $record->sourceobjectid = $record->sourceitemid;
        }

        $metadata = [];
        if (property_exists($record, 'metadata')) {
            if (is_string($record->metadata)) {
                $decoded = json_decode($record->metadata, true);
                $metadata = is_array($decoded) ? $decoded : [];
            } else if ($record->metadata instanceof stdClass) {
                $metadata = (array)$record->metadata;
            } else if (is_array($record->metadata)) {
                $metadata = $record->metadata;
            }
        }
        $metadata['ownership'] = $ownership;
        foreach ([
            'title', 'publisher', 'sourceyear', 'identifier', 'rightsnote',
        ] as $alias) {
            if (property_exists($record, $alias) && $record->{$alias} !== null && $record->{$alias} !== '') {
                $metadata[$alias] = $record->{$alias};
            }
        }
        $record->metadata = self::encode_metadata($metadata);

        foreach ([
            'sourceurl', 'sourceauthor', 'license', 'citation', 'rightsstatus',
            'sourcecomponent', 'status', 'visibility', 'provenancehash',
        ] as $field) {
            if (property_exists($record, $field) && $record->{$field} !== null) {
                $record->{$field} = trim((string)$record->{$field});
            }
        }

        return $record;
    }

    /**
     * Keep only fields that exist in the installed Moodle table.
     *
     * This makes the service compatible with both historical deployments and
     * the current install.xml schema without silently dropping provenance.
     *
     * @param stdClass $record Prepared source record.
     * @return stdClass
     */
    private static function filter_to_table_fields(stdClass $record): stdClass {
        global $DB;

        $columns = $DB->get_columns(self::TABLE);
        if (!$columns) {
            return $record;
        }

        $filtered = new stdClass();
        foreach (get_object_vars($record) as $field => $value) {
            if (isset($columns[$field]) || $field === 'id') {
                $filtered->{$field} = $value;
            }
        }
        return $filtered;
    }

    /**
     * Read ownership from a native field or the compatibility metadata envelope.
     *
     * @param stdClass $record Source record.
     * @return string
     */
    private static function ownership_value(stdClass $record): string {
        if (!empty($record->ownership)) {
            return (string)$record->ownership;
        }
        $metadata = self::get_metadata($record);
        return (string)($metadata['ownership'] ?? self::get_default_ownership());
    }

    /**
     * Normalize and validate a source type.
     *
     * @param string $sourcetype Source type.
     * @return string
     * @throws invalid_parameter_exception
     */
    private static function normalize_source_type(string $sourcetype): string {
        $sourcetype = trim($sourcetype);

        if (!self::is_valid_source_type($sourcetype)) {
            throw new invalid_parameter_exception('Invalid media source type: ' . $sourcetype);
        }

        return $sourcetype;
    }

    /**
     * Normalize and validate an ownership value.
     *
     * @param string $ownership Ownership value.
     * @return string
     * @throws invalid_parameter_exception
     */
    private static function normalize_ownership(string $ownership): string {
        $ownership = trim($ownership);

        if (!self::is_valid_ownership($ownership)) {
            throw new invalid_parameter_exception('Invalid media source ownership: ' . $ownership);
        }

        return $ownership;
    }

    /**
     * Encode metadata as JSON.
     *
     * @param mixed $metadata Metadata.
     * @return string
     */
    private static function encode_metadata($metadata): string {
        if (is_string($metadata)) {
            $decoded = json_decode($metadata, true);
            if (is_array($decoded)) {
                $metadata = $decoded;
            } else {
                $metadata = ['raw' => $metadata];
            }
        }

        if ($metadata instanceof stdClass) {
            $metadata = (array)$metadata;
        }

        if (!is_array($metadata)) {
            $metadata = [];
        }

        return json_encode($metadata, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
    }

    /**
     * Generate a stable UUID.
     *
     * @return string
     */
    private static function generate_uuid(): string {
        if (class_exists(uuid::class)) {
            return uuid::generate();
        }

        if (class_exists('\\core\\uuid')) {
            return \core\uuid::generate();
        }

        return self::fallback_uuid_v4();
    }

    /**
     * Fallback UUID v4 generator for early implementation/bootstrap.
     *
     * @return string
     */
    private static function fallback_uuid_v4(): string {
        $data = random_bytes(16);
        $data[6] = chr((ord($data[6]) & 0x0f) | 0x40);
        $data[8] = chr((ord($data[8]) & 0x3f) | 0x80);

        return vsprintf('%s%s-%s-%s-%s-%s%s%s', str_split(bin2hex($data), 4));
    }
}
