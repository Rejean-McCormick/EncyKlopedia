<?php
// This file is part of Moodle - https://moodle.org/.
//
// Moodle is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// any later version.

/**
 * Media-library ownership and bridge registry.
 *
 * @package    mod_uckkarchive
 * @copyright  2026 Univers-Cité King Klown
 * @license    https://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later
 */

declare(strict_types=1);

namespace mod_uckkarchive\local;

use coding_exception;
use stdClass;
use xmldb_table;

defined('MOODLE_INTERNAL') || die();

/**
 * Resolve autonomous media libraries and explicit cross-library bridges.
 *
 * Design rules:
 * - every media object has one home library;
 * - one library may be the primary library of several public sites;
 * - libraries are isolated by default;
 * - bridges are directional and explicit;
 * - a bridge can expose a whole source library, one collection, or one media;
 * - bridges never duplicate the underlying media row or UUID.
 *
 * Write methods in this class intentionally do not perform capability checks.
 * Callers that expose them through UI or external services must authorise the
 * action before invoking the method.
 */
final class media_library_scope {
    public const TABLE_LIBRARY = 'uckkarchive_library';
    public const TABLE_LIBRARY_SITE = 'uckkarchive_library_site';
    public const TABLE_LIBRARY_BRIDGE = 'uckkarchive_library_bridge';
    public const TABLE_MEDIA = 'uckkarchive_media';
    public const TABLE_COLLECTION = 'uckkarchive_media_collection';
    public const TABLE_COLLECTION_ITEM = 'uckkarchive_media_collection_item';

    public const STATUS_ACTIVE = 'active';
    public const STATUS_INACTIVE = 'inactive';

    public const SITE_ROLE_PRIMARY = 'primary';
    public const SITE_ROLE_SHARED = 'shared';

    public const SCOPE_LIBRARY = 'library';
    public const SCOPE_COLLECTION = 'collection';
    public const SCOPE_MEDIA = 'media';

    public const SITE_UCKK = 'uckk';
    public const SITE_UCC = 'ucc';
    public const SITE_MATH = 'math';

    public const LIBRARY_UCKK = 'uckk';
    public const LIBRARY_UCC = 'ucc';
    public const LIBRARY_MATH = 'math';

    /** @return array<string,array{slug:string,name:string}> */
    public static function default_libraries(): array {
        return [
            self::SITE_UCKK => [
                'slug' => self::LIBRARY_UCKK,
                'name' => 'Médiathèque UCKK',
            ],
            self::SITE_UCC => [
                'slug' => self::LIBRARY_UCC,
                'name' => 'Médiathèque chrétienne',
            ],
            self::SITE_MATH => [
                'slug' => self::LIBRARY_MATH,
                'name' => 'Bibliothèque mathématique',
            ],
        ];
    }

    public static function schema_ready(): bool {
        global $DB;

        $dbman = $DB->get_manager();
        foreach ([self::TABLE_LIBRARY, self::TABLE_LIBRARY_SITE, self::TABLE_LIBRARY_BRIDGE] as $tablename) {
            if (!$dbman->table_exists(new xmldb_table($tablename))) {
                return false;
            }
        }

        $mediacolumns = $DB->get_columns(self::TABLE_MEDIA);
        $collectioncolumns = $DB->get_columns(self::TABLE_COLLECTION);

        return isset($mediacolumns['libraryid']) && isset($collectioncolumns['libraryid']);
    }

    /** Resolve the primary library used by a public site key. */
    public function resolve_primary_for_site(string $sitekey): ?stdClass {
        global $DB;

        if (!self::schema_ready()) {
            return null;
        }

        $sitekey = self::clean_site_key($sitekey);
        if ($sitekey === '') {
            $sitekey = self::SITE_UCKK;
        }

        $sql = 'SELECT l.*, ls.role AS siterole, ls.sitekey
                  FROM {' . self::TABLE_LIBRARY_SITE . '} ls
                  JOIN {' . self::TABLE_LIBRARY . '} l ON l.id = ls.libraryid
                 WHERE ls.sitekey = :sitekey
                   AND ls.status = :sitestatus
                   AND l.status = :librarystatus
              ORDER BY CASE WHEN ls.role = :primaryrole THEN 0 ELSE 1 END,
                       ls.sortorder ASC,
                       l.id ASC';

        $records = $DB->get_records_sql($sql, [
            'sitekey' => $sitekey,
            'sitestatus' => self::STATUS_ACTIVE,
            'librarystatus' => self::STATUS_ACTIVE,
            'primaryrole' => self::SITE_ROLE_PRIMARY,
        ], 0, 1);

        if (!$records) {
            return null;
        }

        return reset($records) ?: null;
    }

    /** Resolve an active library by slug. */
    public function resolve_by_slug(string $slug): ?stdClass {
        global $DB;

        if (!self::schema_ready()) {
            return null;
        }

        $slug = self::clean_slug($slug);
        if ($slug === '') {
            return null;
        }

        return $DB->get_record(
            self::TABLE_LIBRARY,
            ['slug' => $slug, 'status' => self::STATUS_ACTIVE],
            '*',
            IGNORE_MISSING
        ) ?: null;
    }

    /** Resolve a library by id. */
    public function resolve_by_id(int $libraryid): ?stdClass {
        global $DB;

        if (!self::schema_ready() || $libraryid <= 0) {
            return null;
        }

        return $DB->get_record(self::TABLE_LIBRARY, ['id' => $libraryid], '*', IGNORE_MISSING) ?: null;
    }

    /** Return all active libraries attached to a public site. */
    public function get_site_libraries(string $sitekey): array {
        global $DB;

        if (!self::schema_ready()) {
            return [];
        }

        $sitekey = self::clean_site_key($sitekey);
        if ($sitekey === '') {
            return [];
        }

        $sql = 'SELECT l.*, ls.role AS siterole, ls.sitekey, ls.sortorder AS sitesortorder
                  FROM {' . self::TABLE_LIBRARY_SITE . '} ls
                  JOIN {' . self::TABLE_LIBRARY . '} l ON l.id = ls.libraryid
                 WHERE ls.sitekey = :sitekey
                   AND ls.status = :sitestatus
                   AND l.status = :librarystatus
              ORDER BY CASE WHEN ls.role = :primaryrole THEN 0 ELSE 1 END,
                       ls.sortorder ASC,
                       l.name ASC';

        return array_values($DB->get_records_sql($sql, [
            'sitekey' => $sitekey,
            'sitestatus' => self::STATUS_ACTIVE,
            'librarystatus' => self::STATUS_ACTIVE,
            'primaryrole' => self::SITE_ROLE_PRIMARY,
        ]));
    }

    /** Create a new autonomous media library or return the existing slug. */
    public function create_library(string $slug, string $name, string $description = ''): stdClass {
        global $DB;

        if (!self::schema_ready()) {
            throw new coding_exception('Media library schema is not installed.');
        }

        $slug = self::clean_slug($slug);
        $name = trim($name);
        if ($slug === '' || $name === '') {
            throw new coding_exception('Library slug and name are required.');
        }

        $existing = $DB->get_record(self::TABLE_LIBRARY, ['slug' => $slug], '*', IGNORE_MISSING);
        if ($existing) {
            return $existing;
        }

        $now = time();
        $record = (object)[
            'uuid' => uuid::generate(),
            'slug' => $slug,
            'name' => $name,
            'description' => trim($description),
            'status' => self::STATUS_ACTIVE,
            'timecreated' => $now,
            'timemodified' => $now,
            'metadata' => null,
        ];
        $record->id = (int)$DB->insert_record(self::TABLE_LIBRARY, $record);

        return $record;
    }

    /** Return all libraries for management UIs. */
    public function get_all_libraries(bool $activeonly = false): array {
        global $DB;

        if (!self::schema_ready()) {
            return [];
        }

        $conditions = $activeonly ? ['status' => self::STATUS_ACTIVE] : [];
        return array_values($DB->get_records(self::TABLE_LIBRARY, $conditions, 'name ASC, id ASC'));
    }

    /** Return all site-to-library mappings enriched with library names. */
    public function get_all_site_mappings(bool $activeonly = false): array {
        global $DB;

        if (!self::schema_ready()) {
            return [];
        }

        $where = $activeonly ? 'WHERE ls.status = :status' : '';
        $params = $activeonly ? ['status' => self::STATUS_ACTIVE] : [];
        $sql = 'SELECT ls.*, l.slug AS libraryslug, l.name AS libraryname
                  FROM {' . self::TABLE_LIBRARY_SITE . '} ls
                  JOIN {' . self::TABLE_LIBRARY . '} l ON l.id = ls.libraryid
                  ' . $where . '
              ORDER BY ls.sitekey ASC,
                       CASE WHEN ls.role = :primaryrole THEN 0 ELSE 1 END,
                       ls.sortorder ASC, l.name ASC';
        $params['primaryrole'] = self::SITE_ROLE_PRIMARY;

        return array_values($DB->get_records_sql($sql, $params));
    }

    /** Return bridge records enriched with source/target names. */
    public function get_all_bridges(bool $activeonly = false): array {
        global $DB;

        if (!self::schema_ready()) {
            return [];
        }

        $where = $activeonly ? 'WHERE b.status = :status' : '';
        $params = $activeonly ? ['status' => self::STATUS_ACTIVE] : [];
        $sql = 'SELECT b.*, source.slug AS sourceslug, source.name AS sourcename,
                       target.slug AS targetslug, target.name AS targetname
                  FROM {' . self::TABLE_LIBRARY_BRIDGE . '} b
                  JOIN {' . self::TABLE_LIBRARY . '} source ON source.id = b.sourcelibraryid
                  JOIN {' . self::TABLE_LIBRARY . '} target ON target.id = b.targetlibraryid
                  ' . $where . '
              ORDER BY b.status ASC, source.name ASC, target.name ASC, b.scopetype ASC, b.id ASC';

        return array_values($DB->get_records_sql($sql, $params));
    }

    /** Assign media by portable UUID. */
    public function assign_media_uuid_to_library(string $mediauuid, string $libraryslug): void {
        global $DB;
        $mediauuid = uuid::require_valid($mediauuid, 'mediauuid');
        $media = $DB->get_record(self::TABLE_MEDIA, ['uuid' => $mediauuid], 'id', MUST_EXIST);
        $this->assign_media_to_library((int)$media->id, $libraryslug);
    }

    /** Assign collection by portable UUID. */
    public function assign_collection_uuid_to_library(string $collectionuuid, string $libraryslug): void {
        global $DB;
        $collectionuuid = uuid::require_valid($collectionuuid, 'collectionuuid');
        $collection = $DB->get_record(self::TABLE_COLLECTION, ['uuid' => $collectionuuid], 'id', MUST_EXIST);
        $this->assign_collection_to_library((int)$collection->id, $libraryslug);
    }

    /** Resolve a collection/media UUID to the local id expected by create_bridge(). */
    public function resolve_scope_uuid(string $scopetype, string $scopeuuid): int {
        global $DB;

        $scopetype = self::clean_scope_type($scopetype);
        if ($scopetype === self::SCOPE_LIBRARY) {
            return 0;
        }

        $scopeuuid = uuid::require_valid($scopeuuid, 'scopeuuid');
        $table = $scopetype === self::SCOPE_COLLECTION ? self::TABLE_COLLECTION : self::TABLE_MEDIA;
        $record = $DB->get_record($table, ['uuid' => $scopeuuid], 'id', MUST_EXIST);
        return (int)$record->id;
    }

    /** Assign a media row to exactly one home library. */
    public function assign_media_to_library(int $mediaid, string $libraryslug): void {
        global $DB;

        $library = $this->require_library($libraryslug);
        if (!$DB->record_exists(self::TABLE_MEDIA, ['id' => $mediaid])) {
            throw new coding_exception('Unknown media id: ' . $mediaid);
        }

        $DB->set_field(self::TABLE_MEDIA, 'libraryid', (int)$library->id, ['id' => $mediaid]);
    }

    /** Assign a collection to one home library. */
    public function assign_collection_to_library(int $collectionid, string $libraryslug): void {
        global $DB;

        $library = $this->require_library($libraryslug);
        if (!$DB->record_exists(self::TABLE_COLLECTION, ['id' => $collectionid])) {
            throw new coding_exception('Unknown media collection id: ' . $collectionid);
        }

        $DB->set_field(self::TABLE_COLLECTION, 'libraryid', (int)$library->id, ['id' => $collectionid]);
    }

    /**
     * Attach an existing library to a public site.
     *
     * Two sites can therefore use the exact same library by attaching the same
     * library slug to both sites with role=primary.
     */
    public function attach_library_to_site(
        string $libraryslug,
        string $sitekey,
        string $role = self::SITE_ROLE_PRIMARY,
        int $sortorder = 0
    ): int {
        global $DB;

        $library = $this->require_library($libraryslug);
        $sitekey = self::clean_site_key($sitekey);
        $role = self::clean_site_role($role);

        if ($sitekey === '') {
            throw new coding_exception('Site key cannot be empty.');
        }

        $existing = $DB->get_record(self::TABLE_LIBRARY_SITE, [
            'libraryid' => (int)$library->id,
            'sitekey' => $sitekey,
        ], '*', IGNORE_MISSING);

        $now = time();

        // A public site has exactly one primary library. When an existing library
        // becomes primary, retain older attachments as shared rather than deleting
        // them. This makes switching two sites onto the same exact fund reversible.
        if ($role === self::SITE_ROLE_PRIMARY) {
            $sql = 'UPDATE {' . self::TABLE_LIBRARY_SITE . '}
                       SET role = :sharedrole, timemodified = :timemodified
                     WHERE sitekey = :sitekey
                       AND libraryid <> :libraryid
                       AND role = :primaryrole';
            $DB->execute($sql, [
                'sharedrole' => self::SITE_ROLE_SHARED,
                'timemodified' => $now,
                'sitekey' => $sitekey,
                'libraryid' => (int)$library->id,
                'primaryrole' => self::SITE_ROLE_PRIMARY,
            ]);
        }

        if ($existing) {
            $existing->role = $role;
            $existing->sortorder = $sortorder;
            $existing->status = self::STATUS_ACTIVE;
            $existing->timemodified = $now;
            $DB->update_record(self::TABLE_LIBRARY_SITE, $existing);
            return (int)$existing->id;
        }

        return (int)$DB->insert_record(self::TABLE_LIBRARY_SITE, (object)[
            'libraryid' => (int)$library->id,
            'sitekey' => $sitekey,
            'role' => $role,
            'sortorder' => $sortorder,
            'status' => self::STATUS_ACTIVE,
            'timecreated' => $now,
            'timemodified' => $now,
        ]);
    }

    /**
     * Create or reactivate a directional bridge.
     *
     * For collection/media scopes, $scopeid is the local database id. Callers
     * may resolve portable UUIDs before invoking this low-level method.
     */
    public function create_bridge(
        string $sourcelibraryslug,
        string $targetlibraryslug,
        string $scopetype = self::SCOPE_LIBRARY,
        int $scopeid = 0,
        string $label = ''
    ): stdClass {
        global $DB;

        $source = $this->require_library($sourcelibraryslug);
        $target = $this->require_library($targetlibraryslug);
        $scopetype = self::clean_scope_type($scopetype);

        if ((int)$source->id === (int)$target->id) {
            throw new coding_exception('A library cannot bridge to itself.');
        }

        if ($scopetype === self::SCOPE_LIBRARY) {
            $scopeid = 0;
        } else if ($scopeid <= 0) {
            throw new coding_exception('Collection and media bridges require a positive scope id.');
        }

        $this->validate_scope_owner((int)$source->id, $scopetype, $scopeid);

        $conditions = [
            'sourcelibraryid' => (int)$source->id,
            'targetlibraryid' => (int)$target->id,
            'scopetype' => $scopetype,
            'scopeid' => $scopeid,
        ];

        $existing = $DB->get_record(self::TABLE_LIBRARY_BRIDGE, $conditions, '*', IGNORE_MISSING);
        $now = time();

        if ($existing) {
            $existing->status = self::STATUS_ACTIVE;
            $existing->label = trim($label);
            $existing->timemodified = $now;
            $DB->update_record(self::TABLE_LIBRARY_BRIDGE, $existing);
            return $existing;
        }

        $record = (object)($conditions + [
            'uuid' => uuid::generate(),
            'label' => trim($label),
            'status' => self::STATUS_ACTIVE,
            'timecreated' => $now,
            'timemodified' => $now,
        ]);
        $record->id = (int)$DB->insert_record(self::TABLE_LIBRARY_BRIDGE, $record);

        return $record;
    }

    /** Deactivate a bridge without deleting its audit identity. */
    public function deactivate_bridge(int $bridgeid): void {
        global $DB;

        if ($bridgeid <= 0) {
            return;
        }

        $DB->set_field(self::TABLE_LIBRARY_BRIDGE, 'status', self::STATUS_INACTIVE, ['id' => $bridgeid]);
        $DB->set_field(self::TABLE_LIBRARY_BRIDGE, 'timemodified', time(), ['id' => $bridgeid]);
    }

    /**
     * Return the bridge that exposes a media object to a target library.
     *
     * Specific media bridges outrank collection bridges, which outrank a whole
     * library bridge. This is only presentation metadata; visibility is still
     * enforced by the repository SQL.
     */
    public function get_bridge_for_media(int $targetlibraryid, int $mediaid, int $sourcelibraryid): ?stdClass {
        global $DB;

        if (!self::schema_ready() || $targetlibraryid <= 0 || $mediaid <= 0 || $sourcelibraryid <= 0) {
            return null;
        }

        if ($targetlibraryid === $sourcelibraryid) {
            return null;
        }

        $sql = 'SELECT b.*
                  FROM {' . self::TABLE_LIBRARY_BRIDGE . '} b
                 WHERE b.targetlibraryid = :targetlibraryid
                   AND b.sourcelibraryid = :sourcelibraryid
                   AND b.status = :status
                   AND (
                        (b.scopetype = :scopemedia AND b.scopeid = :mediaid)
                     OR (b.scopetype = :scopecollection AND EXISTS (
                            SELECT 1
                              FROM {' . self::TABLE_COLLECTION_ITEM . '} ci
                             WHERE ci.collectionid = b.scopeid
                               AND ci.mediaid = :collectionmediaid
                        ))
                     OR (b.scopetype = :scopelibrary AND b.scopeid = 0)
                   )
              ORDER BY CASE b.scopetype
                           WHEN :ordermedia THEN 0
                           WHEN :ordercollection THEN 1
                           ELSE 2
                       END,
                       b.id ASC';

        $records = $DB->get_records_sql($sql, [
            'targetlibraryid' => $targetlibraryid,
            'sourcelibraryid' => $sourcelibraryid,
            'status' => self::STATUS_ACTIVE,
            'scopemedia' => self::SCOPE_MEDIA,
            'mediaid' => $mediaid,
            'scopecollection' => self::SCOPE_COLLECTION,
            'collectionmediaid' => $mediaid,
            'scopelibrary' => self::SCOPE_LIBRARY,
            'ordermedia' => self::SCOPE_MEDIA,
            'ordercollection' => self::SCOPE_COLLECTION,
        ], 0, 1);

        return $records ? (reset($records) ?: null) : null;
    }

    private function require_library(string $slug): stdClass {
        $library = $this->resolve_by_slug($slug);
        if (!$library) {
            throw new coding_exception('Unknown active media library: ' . $slug);
        }
        return $library;
    }

    private function validate_scope_owner(int $sourcelibraryid, string $scopetype, int $scopeid): void {
        global $DB;

        if ($scopetype === self::SCOPE_LIBRARY) {
            return;
        }

        $table = $scopetype === self::SCOPE_COLLECTION ? self::TABLE_COLLECTION : self::TABLE_MEDIA;
        $record = $DB->get_record($table, ['id' => $scopeid], 'id, libraryid', IGNORE_MISSING);
        if (!$record) {
            throw new coding_exception('Unknown bridge scope object: ' . $scopeid);
        }

        if ((int)($record->libraryid ?? 0) !== $sourcelibraryid) {
            throw new coding_exception('Bridge scope object does not belong to the source library.');
        }
    }

    public static function clean_site_key(string $sitekey): string {
        return clean_param(strtolower(trim($sitekey)), PARAM_ALPHANUMEXT);
    }

    public static function clean_slug(string $slug): string {
        return clean_param(strtolower(trim($slug)), PARAM_ALPHANUMEXT);
    }

    private static function clean_site_role(string $role): string {
        $role = clean_param(strtolower(trim($role)), PARAM_ALPHANUMEXT);
        return in_array($role, [self::SITE_ROLE_PRIMARY, self::SITE_ROLE_SHARED], true)
            ? $role
            : self::SITE_ROLE_SHARED;
    }

    private static function clean_scope_type(string $scopetype): string {
        $scopetype = clean_param(strtolower(trim($scopetype)), PARAM_ALPHANUMEXT);
        if (!in_array($scopetype, [self::SCOPE_LIBRARY, self::SCOPE_COLLECTION, self::SCOPE_MEDIA], true)) {
            throw new coding_exception('Unsupported media-library bridge scope: ' . $scopetype);
        }
        return $scopetype;
    }
}
