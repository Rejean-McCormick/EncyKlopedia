<?php
// This file is part of Moodle - https://moodle.org/
//
// Moodle is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// any later version.

/**
 * Local domain model for UCKK archive media relations.
 *
 * @package    mod_uckkarchive
 * @copyright  2026 Univers-Cité King Klown
 * @license    https://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later
 */

declare(strict_types=1);

namespace mod_uckkarchive\local;

use stdClass;

defined('MOODLE_INTERNAL') || die();

/**
 * Domain object representing one media graph relation.
 *
 * Relations connect media objects, archive items, Kristals, media collections,
 * external works, content markers, proofs, and media versions.
 *
 * This class normalises and validates relation data before service/database
 * layers insert, update, render, export, backup, or restore it.
 *
 * It does not write to the database, copy files, decide permissions, transfer
 * external authority, or bypass content advisory/cultural protocol policy.
 */
final class media_relation {
    /** Object type: media object. */
    public const OBJECT_MEDIA = 'media';

    /** Object type: media version. */
    public const OBJECT_MEDIA_VERSION = 'media_version';

    /** Object type: archive item. */
    public const OBJECT_ARCHIVE_ITEM = 'archive_item';

    /** Object type: proof. */
    public const OBJECT_PROOF = 'proof';

    /** Object type: Kristal. */
    public const OBJECT_KRISTAL = 'kristal';

    /** Object type: media collection. */
    public const OBJECT_MEDIA_COLLECTION = 'media_collection';

    /** Object type: media collection membership row. */
    public const OBJECT_MEDIA_COLLECTION_ITEM = 'media_collection_item';

    /** Object type: content advisory marker. */
    public const OBJECT_CONTENT_MARKER = 'content_marker';

    /** Object type: external work reference. */
    public const OBJECT_EXTERNAL_WORK = 'external_work';

    /** Relation type: media belongs to archive item. */
    public const TYPE_BELONGS_TO_ITEM = 'belongs_to_item';

    /** Relation type: media belongs to Kristal. */
    public const TYPE_BELONGS_TO_KRISTAL = 'belongs_to_kristal';

    /** Relation type: media belongs to collection. */
    public const TYPE_BELONGS_TO_COLLECTION = 'belongs_to_collection';

    /** Relation type: media is derivative of another media/version. */
    public const TYPE_IS_DERIVATIVE_OF = 'is_derivative_of';

    /** Relation type: media is translation of another media/version. */
    public const TYPE_IS_TRANSLATION_OF = 'is_translation_of';

    /** Relation type: media is excerpt of another media/version. */
    public const TYPE_IS_EXCERPT_OF = 'is_excerpt_of';

    /** Relation type: media is proof for another object. */
    public const TYPE_IS_PROOF_FOR = 'is_proof_for';

    /** Relation type: media is source for another object. */
    public const TYPE_IS_SOURCE_FOR = 'is_source_for';

    /** Relation type: media replaces another object. */
    public const TYPE_REPLACES = 'replaces';

    /** Relation type: generic reference. */
    public const TYPE_REFERENCES = 'references';

    /** Relation type: duplicate relation. */
    public const TYPE_DUPLICATES = 'duplicates';

    /** Relation type: relation references an external work. */
    public const TYPE_REFERENCES_EXTERNAL_WORK = 'references_external_work';

    /** Relation type: object contains a content marker. */
    public const TYPE_CONTAINS_CONTENT_MARKER = 'contains_content_marker';

    /** Database id. */
    private int $id = 0;

    /** Portable relation UUID. */
    private string $uuid = '';

    /** Parent archive activity instance id. */
    private int $archiveid = 0;

    /** Source object type. */
    private string $fromtype = self::OBJECT_MEDIA;

    /** Source object id. */
    private int $fromid = 0;

    /** Target object type. */
    private string $totype = self::OBJECT_MEDIA;

    /** Target object id. */
    private int $toid = 0;

    /** Relation type. */
    private string $relationtype = self::TYPE_REFERENCES;

    /** Sort order. */
    private int $sortorder = 0;

    /** Creator user id. */
    private int $createdby = 0;

    /** Creation timestamp. */
    private int $timecreated = 0;

    /** Variable metadata. */
    private array $metadata = [];

    /**
     * Constructor.
     *
     * @param array<string, mixed>|stdClass|null $data Initial relation data.
     */
    public function __construct(array|stdClass|null $data = null) {
        if ($data !== null) {
            $this->apply_data((array)$data);
        }
    }

    /**
     * Build from a Moodle DB record.
     *
     * @param stdClass $record Record from {uckkarchive_media_relation}.
     * @return self
     */
    public static function from_record(stdClass $record): self {
        return new self($record);
    }

    /**
     * Build a generic relation.
     *
     * @param int $archiveid Parent archive id.
     * @param string $fromtype Source object type.
     * @param int $fromid Source object id.
     * @param string $totype Target object type.
     * @param int $toid Target object id.
     * @param string $relationtype Relation type.
     * @return self
     */
    public static function create(
        int $archiveid,
        string $fromtype,
        int $fromid,
        string $totype,
        int $toid,
        string $relationtype = self::TYPE_REFERENCES
    ): self {
        return new self([
            'archiveid' => $archiveid,
            'fromtype' => $fromtype,
            'fromid' => $fromid,
            'totype' => $totype,
            'toid' => $toid,
            'relationtype' => $relationtype,
        ]);
    }

    /**
     * Build a relation between media and an archive item.
     *
     * @param int $archiveid Parent archive id.
     * @param int $mediaid Media object id.
     * @param int $itemid Archive item id.
     * @return self
     */
    public static function belongs_to_item(int $archiveid, int $mediaid, int $itemid): self {
        return self::create(
            $archiveid,
            self::OBJECT_MEDIA,
            $mediaid,
            self::OBJECT_ARCHIVE_ITEM,
            $itemid,
            self::TYPE_BELONGS_TO_ITEM
        );
    }

    /**
     * Build a relation between media and a Kristal.
     *
     * @param int $archiveid Parent archive id.
     * @param int $mediaid Media object id.
     * @param int $kristalid Kristal id.
     * @return self
     */
    public static function belongs_to_kristal(int $archiveid, int $mediaid, int $kristalid): self {
        return self::create(
            $archiveid,
            self::OBJECT_MEDIA,
            $mediaid,
            self::OBJECT_KRISTAL,
            $kristalid,
            self::TYPE_BELONGS_TO_KRISTAL
        );
    }

    /**
     * Build a relation between media and a media collection.
     *
     * @param int $archiveid Parent archive id.
     * @param int $mediaid Media object id.
     * @param int $collectionid Media collection id.
     * @return self
     */
    public static function belongs_to_collection(int $archiveid, int $mediaid, int $collectionid): self {
        return self::create(
            $archiveid,
            self::OBJECT_MEDIA,
            $mediaid,
            self::OBJECT_MEDIA_COLLECTION,
            $collectionid,
            self::TYPE_BELONGS_TO_COLLECTION
        );
    }

    /**
     * Build a media-to-media derivative relation.
     *
     * @param int $archiveid Parent archive id.
     * @param int $mediaid Derived media id.
     * @param int $sourcemediaid Source media id.
     * @return self
     */
    public static function derivative_of(int $archiveid, int $mediaid, int $sourcemediaid): self {
        return self::create(
            $archiveid,
            self::OBJECT_MEDIA,
            $mediaid,
            self::OBJECT_MEDIA,
            $sourcemediaid,
            self::TYPE_IS_DERIVATIVE_OF
        );
    }

    /**
     * Build a relation from media to an external work.
     *
     * @param int $archiveid Parent archive id.
     * @param int $mediaid Media object id.
     * @param int $externalworkid External work id.
     * @return self
     */
    public static function references_external_work(int $archiveid, int $mediaid, int $externalworkid): self {
        return self::create(
            $archiveid,
            self::OBJECT_MEDIA,
            $mediaid,
            self::OBJECT_EXTERNAL_WORK,
            $externalworkid,
            self::TYPE_REFERENCES_EXTERNAL_WORK
        );
    }

    /**
     * Build a relation between media and a content marker.
     *
     * @param int $archiveid Parent archive id.
     * @param int $mediaid Media object id.
     * @param int $markerid Content marker id.
     * @return self
     */
    public static function contains_content_marker(int $archiveid, int $mediaid, int $markerid): self {
        return self::create(
            $archiveid,
            self::OBJECT_MEDIA,
            $mediaid,
            self::OBJECT_CONTENT_MARKER,
            $markerid,
            self::TYPE_CONTAINS_CONTENT_MARKER
        );
    }

    /**
     * Apply raw data to this object.
     *
     * @param array<string, mixed> $data Raw data.
     */
    private function apply_data(array $data): void {
        $this->id = max(0, (int)($data['id'] ?? $this->id));
        $this->uuid = uuid::normalise($data['uuid'] ?? $this->uuid);
        $this->archiveid = max(0, (int)($data['archiveid'] ?? $data['uckkarchiveid'] ?? $this->archiveid));

        $this->fromtype = self::normalise_object_type((string)($data['fromtype'] ?? $this->fromtype));
        $this->fromid = max(0, (int)($data['fromid'] ?? $data['sourceid'] ?? $this->fromid));

        $this->totype = self::normalise_object_type((string)($data['totype'] ?? $this->totype));
        $this->toid = max(0, (int)($data['toid'] ?? $data['targetid'] ?? $this->toid));

        $this->relationtype = self::normalise_relation_type(
            (string)($data['relationtype'] ?? $data['type'] ?? $this->relationtype)
        );

        $this->sortorder = max(0, (int)($data['sortorder'] ?? $this->sortorder));
        $this->createdby = max(0, (int)($data['createdby'] ?? $data['userid'] ?? $this->createdby));
        $this->timecreated = max(0, (int)($data['timecreated'] ?? $this->timecreated));

        if (array_key_exists('metadata', $data)) {
            $this->metadata = self::normalise_metadata($data['metadata']);
        }
    }

    /**
     * Validate this relation.
     *
     * @throws \coding_exception If invalid.
     */
    public function validate(): void {
        if ($this->archiveid <= 0) {
            throw new \coding_exception('Media relation requires a valid archiveid.');
        }

        if ($this->uuid !== '' && !uuid::is_valid($this->uuid)) {
            throw new \coding_exception('Media relation has an invalid UUID.');
        }

        if (!in_array($this->fromtype, self::get_allowed_object_types(), true)) {
            throw new \coding_exception('Invalid media relation source type: ' . $this->fromtype);
        }

        if (!in_array($this->totype, self::get_allowed_object_types(), true)) {
            throw new \coding_exception('Invalid media relation target type: ' . $this->totype);
        }

        if ($this->fromid <= 0) {
            throw new \coding_exception('Media relation requires a valid source object id.');
        }

        if ($this->toid <= 0) {
            throw new \coding_exception('Media relation requires a valid target object id.');
        }

        if ($this->fromtype === $this->totype && $this->fromid === $this->toid) {
            throw new \coding_exception('Media relation cannot link an object to itself.');
        }

        if (!in_array($this->relationtype, self::get_allowed_relation_types(), true)) {
            throw new \coding_exception('Invalid media relation type: ' . $this->relationtype);
        }

        $this->validate_relation_shape();
    }

    /**
     * Validate canonical source/target shapes for relation types with strict meaning.
     *
     * @throws \coding_exception If invalid.
     */
    private function validate_relation_shape(): void {
        if ($this->relationtype === self::TYPE_BELONGS_TO_ITEM &&
                ($this->fromtype !== self::OBJECT_MEDIA || $this->totype !== self::OBJECT_ARCHIVE_ITEM)) {
            throw new \coding_exception('belongs_to_item requires media -> archive_item.');
        }

        if ($this->relationtype === self::TYPE_BELONGS_TO_KRISTAL &&
                ($this->fromtype !== self::OBJECT_MEDIA || $this->totype !== self::OBJECT_KRISTAL)) {
            throw new \coding_exception('belongs_to_kristal requires media -> kristal.');
        }

        if ($this->relationtype === self::TYPE_BELONGS_TO_COLLECTION &&
                ($this->fromtype !== self::OBJECT_MEDIA || $this->totype !== self::OBJECT_MEDIA_COLLECTION)) {
            throw new \coding_exception('belongs_to_collection requires media -> media_collection.');
        }

        if ($this->relationtype === self::TYPE_REFERENCES_EXTERNAL_WORK &&
                $this->totype !== self::OBJECT_EXTERNAL_WORK) {
            throw new \coding_exception('references_external_work requires target external_work.');
        }

        if ($this->relationtype === self::TYPE_CONTAINS_CONTENT_MARKER &&
                $this->totype !== self::OBJECT_CONTENT_MARKER) {
            throw new \coding_exception('contains_content_marker requires target content_marker.');
        }

        if (in_array($this->relationtype, self::get_media_to_media_relation_types(), true)) {
            if (!self::is_media_like_object_type($this->fromtype) || !self::is_media_like_object_type($this->totype)) {
                throw new \coding_exception($this->relationtype . ' requires media/media_version endpoints.');
            }
        }
    }

    /**
     * Convert to database record for {uckkarchive_media_relation}.
     *
     * @param int|null $userid Acting user id.
     * @param int|null $now Timestamp.
     * @return stdClass
     */
    public function to_record(?int $userid = null, ?int $now = null): stdClass {
        $userid ??= 0;
        $now ??= time();

        $this->uuid = uuid::ensure($this->uuid);
        $this->validate();

        $record = new stdClass();

        if ($this->id > 0) {
            $record->id = $this->id;
        }

        $record->uuid = $this->uuid;
        $record->archiveid = $this->archiveid;
        $record->fromtype = $this->fromtype;
        $record->fromid = $this->fromid;
        $record->totype = $this->totype;
        $record->toid = $this->toid;
        $record->relationtype = $this->relationtype;
        $record->sortorder = $this->sortorder;
        $record->createdby = $this->createdby ?: $userid;
        $record->metadata = self::encode_metadata($this->metadata);
        $record->timecreated = $this->timecreated ?: $now;

        return $record;
    }

    /**
     * Convert to export/manifest-safe data.
     *
     * @return stdClass
     */
    public function to_export(): stdClass {
        $this->uuid = uuid::ensure($this->uuid);
        $this->validate();

        $export = new stdClass();
        $export->id = $this->id;
        $export->uuid = $this->uuid;
        $export->archiveid = $this->archiveid;
        $export->fromtype = $this->fromtype;
        $export->fromid = $this->fromid;
        $export->totype = $this->totype;
        $export->toid = $this->toid;
        $export->relationtype = $this->relationtype;
        $export->sortorder = $this->sortorder;
        $export->metadata = $this->metadata;
        $export->timecreated = $this->timecreated;

        return $export;
    }

    /**
     * Whether this relation touches a media object or media version.
     *
     * @return bool
     */
    public function touches_media(): bool {
        return self::is_media_like_object_type($this->fromtype) || self::is_media_like_object_type($this->totype);
    }

    /**
     * Whether this relation targets an external work.
     *
     * @return bool
     */
    public function targets_external_work(): bool {
        return $this->totype === self::OBJECT_EXTERNAL_WORK ||
            $this->relationtype === self::TYPE_REFERENCES_EXTERNAL_WORK;
    }

    /**
     * Whether this relation targets a content advisory marker.
     *
     * @return bool
     */
    public function targets_content_marker(): bool {
        return $this->totype === self::OBJECT_CONTENT_MARKER ||
            $this->relationtype === self::TYPE_CONTAINS_CONTENT_MARKER;
    }

    /**
     * Whether this relation describes generated/derived media.
     *
     * @return bool
     */
    public function is_derivative_relation(): bool {
        return in_array($this->relationtype, [
            self::TYPE_IS_DERIVATIVE_OF,
            self::TYPE_IS_TRANSLATION_OF,
            self::TYPE_IS_EXCERPT_OF,
        ], true);
    }

    /**
     * Get database id.
     *
     * @return int
     */
    public function get_id(): int {
        return $this->id;
    }

    /**
     * Get portable UUID.
     *
     * @return string
     */
    public function get_uuid(): string {
        return $this->uuid;
    }

    /**
     * Get parent archive id.
     *
     * @return int
     */
    public function get_archiveid(): int {
        return $this->archiveid;
    }

    /**
     * Get source object type.
     *
     * @return string
     */
    public function get_fromtype(): string {
        return $this->fromtype;
    }

    /**
     * Get source object id.
     *
     * @return int
     */
    public function get_fromid(): int {
        return $this->fromid;
    }

    /**
     * Get target object type.
     *
     * @return string
     */
    public function get_totype(): string {
        return $this->totype;
    }

    /**
     * Get target object id.
     *
     * @return int
     */
    public function get_toid(): int {
        return $this->toid;
    }

    /**
     * Get relation type.
     *
     * @return string
     */
    public function get_relationtype(): string {
        return $this->relationtype;
    }

    /**
     * Get sort order.
     *
     * @return int
     */
    public function get_sortorder(): int {
        return $this->sortorder;
    }

    /**
     * Get creator id.
     *
     * @return int
     */
    public function get_createdby(): int {
        return $this->createdby;
    }

    /**
     * Get creation timestamp.
     *
     * @return int
     */
    public function get_timecreated(): int {
        return $this->timecreated;
    }

    /**
     * Get metadata.
     *
     * @return array<string, mixed>
     */
    public function get_metadata(): array {
        return $this->metadata;
    }

    /**
     * Get one metadata value.
     *
     * @param string $key Metadata key.
     * @param mixed $default Default value.
     * @return mixed
     */
    public function get_metadata_value(string $key, mixed $default = null): mixed {
        return $this->metadata[$key] ?? $default;
    }

    /**
     * Return copy with id.
     *
     * @param int $id Database id.
     * @return self
     */
    public function with_id(int $id): self {
        $clone = clone $this;
        $clone->id = max(0, $id);
        return $clone;
    }

    /**
     * Return copy with UUID.
     *
     * @param string $uuid Portable UUID.
     * @return self
     */
    public function with_uuid(string $uuid): self {
        $clone = clone $this;
        $clone->uuid = uuid::require_valid($uuid);
        return $clone;
    }

    /**
     * Return copy with source endpoint.
     *
     * @param string $type Source object type.
     * @param int $id Source object id.
     * @return self
     */
    public function with_from(string $type, int $id): self {
        $clone = clone $this;
        $clone->fromtype = self::normalise_object_type($type);
        $clone->fromid = max(0, $id);
        return $clone;
    }

    /**
     * Return copy with target endpoint.
     *
     * @param string $type Target object type.
     * @param int $id Target object id.
     * @return self
     */
    public function with_to(string $type, int $id): self {
        $clone = clone $this;
        $clone->totype = self::normalise_object_type($type);
        $clone->toid = max(0, $id);
        return $clone;
    }

    /**
     * Return copy with relation type.
     *
     * @param string $relationtype Relation type.
     * @return self
     */
    public function with_relationtype(string $relationtype): self {
        $clone = clone $this;
        $clone->relationtype = self::normalise_relation_type($relationtype);
        return $clone;
    }

    /**
     * Return copy with sort order.
     *
     * @param int $sortorder Sort order.
     * @return self
     */
    public function with_sortorder(int $sortorder): self {
        $clone = clone $this;
        $clone->sortorder = max(0, $sortorder);
        return $clone;
    }

    /**
     * Return copy with creator/timestamp.
     *
     * @param int $userid Creator user id.
     * @param int|null $now Timestamp.
     * @return self
     */
    public function with_creation(int $userid, ?int $now = null): self {
        $clone = clone $this;
        $clone->createdby = max(0, $userid);
        $clone->timecreated = max(0, $now ?? time());
        return $clone;
    }

    /**
     * Return copy with metadata.
     *
     * @param array<string, mixed> $metadata Metadata.
     * @return self
     */
    public function with_metadata(array $metadata): self {
        $clone = clone $this;
        $clone->metadata = self::normalise_metadata($metadata);
        return $clone;
    }

    /**
     * Return copy with one metadata value.
     *
     * @param string $key Metadata key.
     * @param mixed $value Metadata value.
     * @return self
     */
    public function with_metadata_value(string $key, mixed $value): self {
        $key = clean_param($key, PARAM_ALPHANUMEXT);

        if ($key === '') {
            throw new \coding_exception('Metadata key cannot be empty.');
        }

        $clone = clone $this;
        $clone->metadata[$key] = $value;
        return $clone;
    }

    /**
     * Get allowed object types.
     *
     * @return string[]
     */
    public static function get_allowed_object_types(): array {
        return [
            self::OBJECT_MEDIA,
            self::OBJECT_MEDIA_VERSION,
            self::OBJECT_ARCHIVE_ITEM,
            self::OBJECT_PROOF,
            self::OBJECT_KRISTAL,
            self::OBJECT_MEDIA_COLLECTION,
            self::OBJECT_MEDIA_COLLECTION_ITEM,
            self::OBJECT_CONTENT_MARKER,
            self::OBJECT_EXTERNAL_WORK,
        ];
    }

    /**
     * Get allowed relation types.
     *
     * @return string[]
     */
    public static function get_allowed_relation_types(): array {
        return [
            self::TYPE_BELONGS_TO_ITEM,
            self::TYPE_BELONGS_TO_KRISTAL,
            self::TYPE_BELONGS_TO_COLLECTION,
            self::TYPE_IS_DERIVATIVE_OF,
            self::TYPE_IS_TRANSLATION_OF,
            self::TYPE_IS_EXCERPT_OF,
            self::TYPE_IS_PROOF_FOR,
            self::TYPE_IS_SOURCE_FOR,
            self::TYPE_REPLACES,
            self::TYPE_REFERENCES,
            self::TYPE_DUPLICATES,
            self::TYPE_REFERENCES_EXTERNAL_WORK,
            self::TYPE_CONTAINS_CONTENT_MARKER,
        ];
    }

    /**
     * Get relation types requiring media-like endpoints.
     *
     * @return string[]
     */
    public static function get_media_to_media_relation_types(): array {
        return [
            self::TYPE_IS_DERIVATIVE_OF,
            self::TYPE_IS_TRANSLATION_OF,
            self::TYPE_IS_EXCERPT_OF,
            self::TYPE_REPLACES,
            self::TYPE_DUPLICATES,
        ];
    }

    /**
     * Whether an object type is media-like.
     *
     * @param string $type Object type.
     * @return bool
     */
    public static function is_media_like_object_type(string $type): bool {
        $type = self::normalise_object_type($type);

        return in_array($type, [
            self::OBJECT_MEDIA,
            self::OBJECT_MEDIA_VERSION,
        ], true);
    }

    /**
     * Normalise object type.
     *
     * @param string $type Raw object type.
     * @return string
     */
    private static function normalise_object_type(string $type): string {
        $type = clean_param(strtolower(trim($type)), PARAM_ALPHANUMEXT);

        return match ($type) {
            'item', 'archiveitem', 'archive_item' => self::OBJECT_ARCHIVE_ITEM,
            'media', 'media_item', 'media_object' => self::OBJECT_MEDIA,
            'version', 'media_version' => self::OBJECT_MEDIA_VERSION,
            'collection', 'mediacollection', 'media_collection' => self::OBJECT_MEDIA_COLLECTION,
            'collection_item', 'collectionitem', 'media_collection_item' => self::OBJECT_MEDIA_COLLECTION_ITEM,
            'marker', 'contentmarker', 'content_marker' => self::OBJECT_CONTENT_MARKER,
            'externalwork', 'external_work', 'work' => self::OBJECT_EXTERNAL_WORK,
            'kristal' => self::OBJECT_KRISTAL,
            'proof' => self::OBJECT_PROOF,
            default => $type,
        };
    }

    /**
     * Normalise relation type.
     *
     * @param string $relationtype Raw relation type.
     * @return string
     */
    private static function normalise_relation_type(string $relationtype): string {
        $relationtype = clean_param(strtolower(trim($relationtype)), PARAM_ALPHANUMEXT);

        return match ($relationtype) {
            'item', 'belongs_item', 'belongs_to_archive_item' => self::TYPE_BELONGS_TO_ITEM,
            'kristal', 'belongs_kristal' => self::TYPE_BELONGS_TO_KRISTAL,
            'collection', 'belongs_collection', 'belongs_to_media_collection' => self::TYPE_BELONGS_TO_COLLECTION,
            'derivative', 'derived_from' => self::TYPE_IS_DERIVATIVE_OF,
            'translation', 'translated_from' => self::TYPE_IS_TRANSLATION_OF,
            'excerpt', 'excerpt_from' => self::TYPE_IS_EXCERPT_OF,
            'proof_for' => self::TYPE_IS_PROOF_FOR,
            'source_for' => self::TYPE_IS_SOURCE_FOR,
            'replace', 'replacement_for' => self::TYPE_REPLACES,
            'reference', 'refers_to' => self::TYPE_REFERENCES,
            'duplicate', 'duplicate_of' => self::TYPE_DUPLICATES,
            'external_work', 'references_work' => self::TYPE_REFERENCES_EXTERNAL_WORK,
            'content_marker', 'has_content_marker' => self::TYPE_CONTAINS_CONTENT_MARKER,
            default => $relationtype,
        };
    }

    /**
     * Normalise metadata.
     *
     * @param mixed $metadata Raw metadata.
     * @return array<string, mixed>
     */
    private static function normalise_metadata(mixed $metadata): array {
        if ($metadata === null || $metadata === '') {
            return [];
        }

        if (is_array($metadata)) {
            return $metadata;
        }

        if ($metadata instanceof stdClass) {
            return (array)$metadata;
        }

        if (is_string($metadata)) {
            $decoded = json_decode($metadata, true);

            if (is_array($decoded)) {
                return $decoded;
            }

            return ['raw' => $metadata];
        }

        return ['value' => $metadata];
    }

    /**
     * Encode metadata for DB storage.
     *
     * @param array<string, mixed> $metadata Metadata.
     * @return string
     */
    private static function encode_metadata(array $metadata): string {
        if ($metadata === []) {
            return '{}';
        }

        $json = json_encode($metadata, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);

        if ($json === false) {
            throw new \coding_exception('Unable to encode media relation metadata.');
        }

        return $json;
    }
}
