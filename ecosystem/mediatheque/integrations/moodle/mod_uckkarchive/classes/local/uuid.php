<?php
// This file is part of Moodle - https://moodle.org/.
//
// Moodle is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
//
// Moodle is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with Moodle. If not, see <https://www.gnu.org/licenses/>.

/**
 * Stable UUID helper for UCKK Archive.
 *
 * UUIDs are portable object identifiers used across archive records, media
 * records, versions, collections, content markers, external works, exports,
 * backup, restore, and manifest generation.
 *
 * @package    mod_uckkarchive
 * @copyright  2026 UCKK
 * @license    https://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later
 */

namespace mod_uckkarchive\local;

defined('MOODLE_INTERNAL') || die();

/**
 * UUID helper.
 *
 * Database integer IDs are local Moodle identifiers. UUIDs are stable portable
 * identifiers used when records need to survive export, restore, duplication,
 * and cross-site movement.
 */
final class uuid {

    /**
     * RFC 4122 UUID pattern.
     */
    private const UUID_PATTERN = '/^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i';

    /**
     * Private constructor.
     */
    private function __construct() {
    }

    /**
     * Generate a random UUID v4.
     *
     * @return string Lowercase UUID v4.
     */
    public static function generate(): string {
        $bytes = random_bytes(16);

        // Version 4.
        $bytes[6] = chr((ord($bytes[6]) & 0x0f) | 0x40);

        // RFC 4122 variant.
        $bytes[8] = chr((ord($bytes[8]) & 0x3f) | 0x80);

        $hex = bin2hex($bytes);

        return sprintf(
            '%s-%s-%s-%s-%s',
            substr($hex, 0, 8),
            substr($hex, 8, 4),
            substr($hex, 12, 4),
            substr($hex, 16, 4),
            substr($hex, 20, 12)
        );
    }

    /**
     * Normalise a UUID-like value.
     *
     * This method trims whitespace and lowercases the value. It does not invent
     * missing hyphens or repair malformed UUIDs.
     *
     * @param mixed $value Raw value.
     * @return string Normalised value, or empty string for null/empty input.
     */
    public static function normalise($value): string {
        if ($value === null) {
            return '';
        }

        $value = trim((string) $value);

        if ($value === '') {
            return '';
        }

        return strtolower($value);
    }

    /**
     * Alias using US spelling.
     *
     * @param mixed $value Raw value.
     * @return string Normalised value, or empty string for null/empty input.
     */
    public static function normalize($value): string {
        return self::normalise($value);
    }

    /**
     * Check whether a value is a valid RFC 4122 UUID.
     *
     * @param mixed $value Raw value.
     * @return bool
     */
    public static function is_valid($value): bool {
        $value = self::normalise($value);

        if ($value === '') {
            return false;
        }

        return preg_match(self::UUID_PATTERN, $value) === 1;
    }

    /**
     * Require a valid UUID and return its normalised value.
     *
     * @param mixed $value Raw value.
     * @param string $fieldname Field name used in exception messages.
     * @return string Normalised UUID.
     * @throws \invalid_parameter_exception
     */
    public static function require_valid($value, string $fieldname = 'uuid'): string {
        $value = self::normalise($value);

        if (!self::is_valid($value)) {
            throw new \invalid_parameter_exception('Invalid ' . $fieldname . '.');
        }

        return $value;
    }

    /**
     * Return an existing valid UUID or generate a new one.
     *
     * This is used by create/upgrade paths where a record must always end with a
     * stable portable identifier.
     *
     * @param mixed $value Existing UUID value.
     * @return string Existing normalised UUID or new UUID v4.
     */
    public static function ensure($value = null): string {
        $value = self::normalise($value);

        if ($value !== '') {
            return self::require_valid($value);
        }

        return self::generate();
    }

    /**
     * Ensure a record has a UUID property.
     *
     * The input record is modified in place and also returned for convenience.
     *
     * @param \stdClass $record Record object.
     * @param string $fieldname UUID field name.
     * @return \stdClass The same record with a valid UUID field.
     */
    public static function ensure_record(\stdClass $record, string $fieldname = 'uuid'): \stdClass {
        $record->{$fieldname} = self::ensure($record->{$fieldname} ?? null);

        return $record;
    }

    /**
     * Compare two UUID values after normalisation.
     *
     * @param mixed $left First UUID.
     * @param mixed $right Second UUID.
     * @return bool True when both are valid and equal.
     */
    public static function equals($left, $right): bool {
        $left = self::normalise($left);
        $right = self::normalise($right);

        if (!self::is_valid($left) || !self::is_valid($right)) {
            return false;
        }

        return $left === $right;
    }

    /**
     * Build a safe SQL condition for selecting records by UUID.
     *
     * @param string $fieldname Database field name.
     * @param mixed $uuid UUID value.
     * @param string $paramname SQL parameter name.
     * @return array Tuple of SQL fragment and params.
     * @throws \invalid_parameter_exception
     */
    public static function sql_equals(string $fieldname, $uuid, string $paramname = 'uuid'): array {
        $uuid = self::require_valid($uuid, $paramname);

        return [
            $fieldname . ' = :' . $paramname,
            [$paramname => $uuid],
        ];
    }
}
