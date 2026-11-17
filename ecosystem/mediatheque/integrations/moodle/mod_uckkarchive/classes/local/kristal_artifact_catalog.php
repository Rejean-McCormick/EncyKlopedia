<?php
// This file is part of Moodle - https://moodle.org/
//
// Moodle is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// any later version.

/**
 * Stable Kristal artifact catalog for the UCKK Médiathèque.
 *
 * @package    mod_uckkarchive
 * @copyright  2026 Univers-Cité King Klown
 * @license    https://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later
 */

declare(strict_types=1);

namespace mod_uckkarchive\local;

use invalid_parameter_exception;
use moodle_exception;
use stdClass;

/**
 * Stores Kristal artifact identities and immutable version bindings.
 *
 * This catalog does not own Kristal semantic identity. ``kristalref`` is an
 * external semantic identifier owned by Kristal/Kristall. Moodle/Médiathèque
 * owns only catalog rows, media rows, stored bytes, integrity facts, and
 * version locators.
 *
 * The legacy {uckkarchive_kristal} table remains a separate archive/insight
 * concept and must not be used as the canonical artifact catalog.
 */
final class kristal_artifact_catalog {
    public const TABLE_ARTIFACT = 'uckkarchive_kartifact';
    public const TABLE_VERSION = 'uckkarchive_kversion';

    public const KIND_UNIVERSITY = 'university';
    public const KIND_VOIE = 'voie';
    public const KIND_COURSE = 'course';
    public const KIND_GENERIC = 'generic';

    public const PORTABLE_CONTRACT = 'kristal_state/6.0';
    public const KRISTALL_BASELINE = '7.0.0-draft.3.2';

    /** @return string[] */
    public static function kinds(): array {
        return [
            self::KIND_UNIVERSITY,
            self::KIND_VOIE,
            self::KIND_COURSE,
            self::KIND_GENERIC,
        ];
    }

    public static function schema_ready(): bool {
        global $DB;
        $dbman = $DB->get_manager();
        return $dbman->table_exists(self::TABLE_ARTIFACT)
            && $dbman->table_exists(self::TABLE_VERSION);
    }

    public static function get_by_ref(int $libraryid, string $kristalref, int $strictness = IGNORE_MISSING): stdClass|false {
        global $DB;
        self::require_schema();
        $kristalref = self::normalise_ref($kristalref);
        return $DB->get_record(self::TABLE_ARTIFACT, [
            'libraryid' => self::positive_id($libraryid, 'libraryid'),
            'kristalref' => $kristalref,
        ], '*', $strictness);
    }

    /**
     * Insert or update an artifact identity row.
     *
     * Expected keys: libraryid, kristalref, kind, title. Optional catalog-only
     * keys include uuid, parentid, voiecode, coursecode, status, mediaid,
     * currentversionid, sortorder and metadata.
     */
    public static function upsert_artifact(array $data): stdClass {
        global $DB;
        self::require_schema();

        $libraryid = self::positive_id((int)($data['libraryid'] ?? 0), 'libraryid');
        $kristalref = self::normalise_ref((string)($data['kristalref'] ?? ''));
        $kind = self::normalise_kind((string)($data['kind'] ?? self::KIND_GENERIC));
        $title = trim((string)($data['title'] ?? ''));
        if ($title === '') {
            throw new invalid_parameter_exception('Kristal artifact title is required.');
        }

        $now = time();
        $existing = self::get_by_ref($libraryid, $kristalref, IGNORE_MISSING);
        $record = $existing ? clone $existing : new stdClass();
        $record->libraryid = $libraryid;
        $record->kristalref = $kristalref;
        $record->kind = $kind;
        $record->parentid = self::nullable_positive_id($data['parentid'] ?? ($record->parentid ?? null));
        $record->voiecode = self::nullable_text($data['voiecode'] ?? ($record->voiecode ?? null));
        $record->coursecode = self::nullable_text($data['coursecode'] ?? ($record->coursecode ?? null));
        $record->title = $title;
        $record->status = self::clean_token((string)($data['status'] ?? ($record->status ?? 'stub')), 'stub');
        $record->portablecontract = self::nullable_text($data['portablecontract'] ?? self::PORTABLE_CONTRACT)
            ?? self::PORTABLE_CONTRACT;
        $record->kristallbaseline = self::nullable_text($data['kristallbaseline'] ?? self::KRISTALL_BASELINE)
            ?? self::KRISTALL_BASELINE;
        $record->mediaid = self::nullable_positive_id($data['mediaid'] ?? ($record->mediaid ?? null));
        $record->currentversionid = self::nullable_positive_id(
            $data['currentversionid'] ?? ($record->currentversionid ?? null)
        );
        $record->sortorder = max(0, (int)($data['sortorder'] ?? ($record->sortorder ?? 0)));
        $record->metadata = self::encode_metadata($data['metadata'] ?? self::decode_metadata($record->metadata ?? null));
        $record->timemodified = $now;

        if ($existing) {
            $DB->update_record(self::TABLE_ARTIFACT, $record);
        } else {
            $record->uuid = self::normalise_uuid((string)($data['uuid'] ?? ''));
            if ($record->uuid === '') {
                $record->uuid = self::generate_uuid();
            }
            $record->timecreated = $now;
            $record->id = $DB->insert_record(self::TABLE_ARTIFACT, $record);
        }

        return $DB->get_record(self::TABLE_ARTIFACT, ['id' => (int)$record->id], '*', MUST_EXIST);
    }

    /**
     * Resolve one parent reference after all hierarchy identities are present.
     */
    public static function set_parent_ref(int $artifactid, ?string $parentref): stdClass {
        global $DB;
        self::require_schema();
        $artifact = $DB->get_record(self::TABLE_ARTIFACT, ['id' => self::positive_id($artifactid, 'artifactid')], '*', MUST_EXIST);
        $parentid = null;
        if ($parentref !== null && trim($parentref) !== '') {
            $parent = self::get_by_ref((int)$artifact->libraryid, $parentref, MUST_EXIST);
            if ((int)$parent->id === (int)$artifact->id) {
                throw new invalid_parameter_exception('Kristal artifact cannot parent itself.');
            }
            $parentid = (int)$parent->id;
        }
        $artifact->parentid = $parentid;
        $artifact->timemodified = time();
        $DB->update_record(self::TABLE_ARTIFACT, $artifact);
        return $DB->get_record(self::TABLE_ARTIFACT, ['id' => (int)$artifact->id], '*', MUST_EXIST);
    }

    /**
     * Record an immutable stored version for a Kristal artifact.
     */
    public static function record_version(int $artifactid, array $data): stdClass {
        global $DB;
        self::require_schema();
        $artifact = $DB->get_record(self::TABLE_ARTIFACT, [
            'id' => self::positive_id($artifactid, 'artifactid'),
        ], '*', MUST_EXIST);

        $sha256 = strtolower(trim((string)($data['sha256'] ?? '')));
        if (!preg_match('/^[0-9a-f]{64}$/', $sha256)) {
            throw new invalid_parameter_exception('Kristal artifact version requires a SHA-256 digest.');
        }
        $existing = $DB->get_record(self::TABLE_VERSION, [
            'artifactid' => (int)$artifact->id,
            'sha256' => $sha256,
        ]);
        if ($existing) {
            return $existing;
        }

        $now = time();
        $record = (object)[
            'uuid' => self::normalise_uuid((string)($data['uuid'] ?? '')) ?: self::generate_uuid(),
            'artifactid' => (int)$artifact->id,
            'mediaid' => self::positive_id((int)($data['mediaid'] ?? 0), 'mediaid'),
            'mediaversionid' => self::positive_id((int)($data['mediaversionid'] ?? 0), 'mediaversionid'),
            'versionlabel' => trim((string)($data['versionlabel'] ?? 'stub')) ?: 'stub',
            'stateid' => self::nullable_text($data['stateid'] ?? null),
            'releaseid' => self::nullable_text($data['releaseid'] ?? null),
            'sha256' => $sha256,
            'status' => self::clean_token((string)($data['status'] ?? 'stub'), 'stub'),
            'portablecontract' => self::nullable_text($data['portablecontract'] ?? self::PORTABLE_CONTRACT)
                ?? self::PORTABLE_CONTRACT,
            'kristallbaseline' => self::nullable_text($data['kristallbaseline'] ?? self::KRISTALL_BASELINE)
                ?? self::KRISTALL_BASELINE,
            'observedat' => max(1, (int)($data['observedat'] ?? $now)),
            'metadata' => self::encode_metadata($data['metadata'] ?? []),
            'timecreated' => $now,
            'timemodified' => $now,
        ];
        $record->id = $DB->insert_record(self::TABLE_VERSION, $record);

        $artifact->mediaid = (int)$record->mediaid;
        $artifact->currentversionid = (int)$record->id;
        $artifact->status = $record->status;
        $artifact->timemodified = $now;
        $DB->update_record(self::TABLE_ARTIFACT, $artifact);

        return $DB->get_record(self::TABLE_VERSION, ['id' => (int)$record->id], '*', MUST_EXIST);
    }

    /** @return stdClass[] */
    public static function list_children(int $artifactid): array {
        global $DB;
        self::require_schema();
        return $DB->get_records(self::TABLE_ARTIFACT, [
            'parentid' => self::positive_id($artifactid, 'artifactid'),
        ], 'sortorder ASC, id ASC');
    }

    /** @return array<string,mixed> */
    public static function decode_metadata(mixed $metadata): array {
        if (is_array($metadata)) {
            return $metadata;
        }
        if (is_object($metadata)) {
            return (array)$metadata;
        }
        if (!is_string($metadata) || trim($metadata) === '') {
            return [];
        }
        $decoded = json_decode($metadata, true);
        return is_array($decoded) ? $decoded : [];
    }

    public static function encode_metadata(mixed $metadata): ?string {
        $array = self::decode_metadata($metadata);
        if ($array === []) {
            return null;
        }
        return json_encode($array, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
    }

    private static function require_schema(): void {
        if (!self::schema_ready()) {
            throw new moodle_exception('missingtable', 'error', '', self::TABLE_ARTIFACT . '/' . self::TABLE_VERSION);
        }
    }

    private static function positive_id(int $value, string $name): int {
        if ($value <= 0) {
            throw new invalid_parameter_exception('Invalid ' . $name . '.');
        }
        return $value;
    }

    private static function nullable_positive_id(mixed $value): ?int {
        if ($value === null || $value === '' || (int)$value <= 0) {
            return null;
        }
        return (int)$value;
    }

    private static function normalise_ref(string $value): string {
        $value = trim($value);
        if ($value === '' || strlen($value) > 255) {
            throw new invalid_parameter_exception('Invalid kristalref.');
        }
        return $value;
    }

    private static function normalise_kind(string $value): string {
        $value = self::clean_token($value, self::KIND_GENERIC);
        if (!in_array($value, self::kinds(), true)) {
            throw new invalid_parameter_exception('Invalid Kristal artifact kind: ' . $value);
        }
        return $value;
    }

    private static function clean_token(string $value, string $default): string {
        $value = strtolower(trim($value));
        if ($value === '') {
            return $default;
        }
        $value = preg_replace('/[^a-z0-9_.-]+/', '_', $value) ?? '';
        return $value !== '' ? $value : $default;
    }

    private static function nullable_text(mixed $value): ?string {
        if ($value === null) {
            return null;
        }
        $value = trim((string)$value);
        return $value === '' ? null : $value;
    }

    private static function normalise_uuid(string $uuid): string {
        $uuid = strtolower(trim($uuid));
        return preg_match('/^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/', $uuid)
            ? $uuid
            : '';
    }

    private static function generate_uuid(): string {
        $data = random_bytes(16);
        $data[6] = chr((ord($data[6]) & 0x0f) | 0x40);
        $data[8] = chr((ord($data[8]) & 0x3f) | 0x80);
        $hex = bin2hex($data);
        return substr($hex, 0, 8) . '-' . substr($hex, 8, 4) . '-' . substr($hex, 12, 4) . '-'
            . substr($hex, 16, 4) . '-' . substr($hex, 20, 12);
    }
}
