<?php
// This file is part of Moodle - https://moodle.org/
//
// Moodle is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// any later version.

/**
 * Local domain model for a UCKK archive Kristal.
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
 * Domain object representing one Kristal pédagogique.
 *
 * A Kristal is a structured knowledge item preserved by the archive. It may
 * summarize a concept, decision, method, proof pattern, lesson, glossary item,
 * or validated learning trace.
 *
 * This class normalises and validates one Kristal record before service or
 * database layers insert, update, validate, revise, export, or render it.
 * It does not perform permission checks, workflow transitions, file handling,
 * integrity decisions, or database writes.
 */
final class kristal {
    /** Kristal type: concept. */
    public const TYPE_CONCEPT = 'concept';

    /** Kristal type: formula. */
    public const TYPE_FORMULA = 'formula';

    /** Kristal type: method. */
    public const TYPE_METHOD = 'method';

    /** Kristal type: decision. */
    public const TYPE_DECISION = 'decision';

    /** Kristal type: lesson. */
    public const TYPE_LESSON = 'lesson';

    /** Kristal type: question. */
    public const TYPE_QUESTION = 'question';

    /** Kristal type: map. */
    public const TYPE_MAP = 'map';

    /** Kristal type: reference. */
    public const TYPE_REFERENCE = 'reference';

    /** Kristal type: glossary entry. */
    public const TYPE_GLOSSARY_ENTRY = 'glossary_entry';

    /** Kristal type: proof pattern. */
    public const TYPE_PROOF_PATTERN = 'proof_pattern';

    /** Kristal type: portfolio insight. */
    public const TYPE_PORTFOLIO_INSIGHT = 'portfolio_insight';

    /** Status: draft. */
    public const STATUS_DRAFT = 'draft';

    /** Status: active. */
    public const STATUS_ACTIVE = 'active';

    /** Status: hidden. */
    public const STATUS_HIDDEN = 'hidden';

    /** Status: pending review. */
    public const STATUS_PENDING_REVIEW = 'pending_review';

    /** Status: validated. */
    public const STATUS_VALIDATED = 'validated';

    /** Status: rejected. */
    public const STATUS_REJECTED = 'rejected';

    /** Status: correction required. */
    public const STATUS_CORRECTION_REQUIRED = 'correction_required';

    /** Status: contested. */
    public const STATUS_CONTESTED = 'contested';

    /** Status: invalidated. */
    public const STATUS_INVALIDATED = 'invalidated';

    /** Status: archived. */
    public const STATUS_ARCHIVED = 'archived';

    /** Visibility: private. */
    public const VISIBILITY_PRIVATE = 'private';

    /** Visibility: user. */
    public const VISIBILITY_USER = 'user';

    /** Visibility: group. */
    public const VISIBILITY_GROUP = 'group';

    /** Visibility: course. */
    public const VISIBILITY_COURSE = 'course';

    /** Visibility: cohort. */
    public const VISIBILITY_COHORT = 'cohort';

    /** Visibility: program. */
    public const VISIBILITY_PROGRAM = 'program';

    /** Visibility: institution. */
    public const VISIBILITY_INSTITUTION = 'institution';

    /** Visibility: public. */
    public const VISIBILITY_PUBLIC = 'public';

    /** Visibility: restricted. */
    public const VISIBILITY_RESTRICTED = 'restricted';

    /** Visibility: restricted integrity. */
    public const VISIBILITY_RESTRICTED_INTEGRITY = 'restricted_integrity';

    /** Visibility: hidden. */
    public const VISIBILITY_HIDDEN = 'hidden';

    /** Visibility: archived. */
    public const VISIBILITY_ARCHIVED = 'archived';

    /** Provenance: human. */
    public const PROVENANCE_HUMAN = 'human';

    /** Provenance: AI-assisted. */
    public const PROVENANCE_AI_ASSISTED = 'ai_assisted';

    /** Provenance: imported. */
    public const PROVENANCE_IMPORTED = 'imported';

    /** Provenance: system. */
    public const PROVENANCE_SYSTEM = 'system';

    /** Provenance: archive. */
    public const PROVENANCE_ARCHIVE = 'archive';

    /** Provenance: assembly. */
    public const PROVENANCE_ASSEMBLY = 'assembly';

    /** Provenance: challenge. */
    public const PROVENANCE_CHALLENGE = 'challenge';

    /** Provenance: integrity. */
    public const PROVENANCE_INTEGRITY = 'integrity';

    /** Validation state: unverified. */
    public const VALIDATION_UNVERIFIED = 'unverified';

    /** Validation state: human reviewed. */
    public const VALIDATION_HUMAN_REVIEWED = 'human_reviewed';

    /** Validation state: verified. */
    public const VALIDATION_VERIFIED = 'verified';

    /** Validation state: contested. */
    public const VALIDATION_CONTESTED = 'contested';

    /** Validation state: invalidated. */
    public const VALIDATION_INVALIDATED = 'invalidated';

    /** Validation state: archived. */
    public const VALIDATION_ARCHIVED = 'archived';

    /** Database id. */
    private int $id = 0;

    /** Parent archive activity id. */
    private int $archiveid = 0;

    /** Optional parent archive item id. */
    private int $itemid = 0;

    /** Optional proof id related to this Kristal. */
    private int $proofid = 0;

    /** Moodle course id. */
    private int $courseid = 0;

    /** Moodle course module id. */
    private int $cmid = 0;

    /** Moodle context id. */
    private int $contextid = 0;

    /** User id primarily associated with this Kristal. */
    private int $userid = 0;

    /** Kristal type. */
    private string $kristaltype = self::TYPE_CONCEPT;

    /** Stable title. */
    private string $title = '';

    /** Optional short summary. */
    private string $summary = '';

    /** Main content/body. */
    private string $content = '';

    /** Optional source component, for cross-plugin origin tracking. */
    private string $sourcecomponent = '';

    /** Optional source record id. */
    private int $sourceid = 0;

    /** Optional source URL or reference. */
    private string $sourceref = '';

    /** Status. */
    private string $status = self::STATUS_DRAFT;

    /** Visibility. */
    private string $visibility = self::VISIBILITY_COURSE;

    /** Provenance source. */
    private string $provenance = self::PROVENANCE_HUMAN;

    /** Validation state. */
    private string $validationstate = self::VALIDATION_UNVERIFIED;

    /** Optional provenance hash. */
    private string $provenancehash = '';

    /** Version number. */
    private int $versionno = 1;

    /** Sort order. */
    private int $sortorder = 0;

    /** Creator user id. */
    private int $createdby = 0;

    /** Modifier user id. */
    private int $modifiedby = 0;

    /** Creation timestamp. */
    private int $timecreated = 0;

    /** Modification timestamp. */
    private int $timemodified = 0;

    /** Variable JSON metadata. */
    private array $metadata = [];

    /**
     * Constructor.
     *
     * @param array<string, mixed>|stdClass|null $data Initial data.
     */
    public function __construct(array|stdClass|null $data = null) {
        if ($data !== null) {
            $this->apply_data((array)$data);
        }
    }

    /**
     * Build from a Moodle database record.
     *
     * @param stdClass $record Record from {uckkarchive_kristal}.
     * @return self
     */
    public static function from_record(stdClass $record): self {
        return new self($record);
    }

    /**
     * Build a new Kristal.
     *
     * @param int $archiveid Archive instance id.
     * @param string $title Kristal title.
     * @param string $content Kristal content.
     * @param string $kristaltype Kristal type.
     * @param array<string, mixed> $metadata Optional metadata.
     * @return self
     */
    public static function create(
        int $archiveid,
        string $title,
        string $content,
        string $kristaltype = self::TYPE_CONCEPT,
        array $metadata = []
    ): self {
        return new self([
            'archiveid' => $archiveid,
            'title' => $title,
            'content' => $content,
            'kristaltype' => $kristaltype,
            'metadata' => $metadata,
            'status' => self::STATUS_DRAFT,
            'visibility' => self::VISIBILITY_COURSE,
            'provenance' => self::PROVENANCE_HUMAN,
            'validationstate' => self::VALIDATION_UNVERIFIED,
        ]);
    }

    /**
     * Apply raw data to this object.
     *
     * @param array<string, mixed> $data Raw data.
     */
    private function apply_data(array $data): void {
        $this->id = max(0, (int)($data['id'] ?? $this->id));
        $this->archiveid = max(0, (int)($data['archiveid'] ?? $data['uckkarchiveid'] ?? $this->archiveid));
        $this->itemid = max(0, (int)($data['itemid'] ?? $data['archiveitemid'] ?? $this->itemid));
        $this->proofid = max(0, (int)($data['proofid'] ?? $this->proofid));
        $this->courseid = max(0, (int)($data['courseid'] ?? $this->courseid));
        $this->cmid = max(0, (int)($data['cmid'] ?? $this->cmid));
        $this->contextid = max(0, (int)($data['contextid'] ?? $this->contextid));
        $this->userid = max(0, (int)($data['userid'] ?? $this->userid));

        $this->kristaltype = self::normalise_kristal_type(
            (string)($data['kristaltype'] ?? $data['type'] ?? $this->kristaltype)
        );

        $this->title = self::normalise_title((string)($data['title'] ?? $data['name'] ?? $this->title));
        $this->summary = trim((string)($data['summary'] ?? $this->summary));
        $this->content = trim((string)($data['content'] ?? $data['body'] ?? $this->content));

        $this->sourcecomponent = self::normalise_source_component(
            (string)($data['sourcecomponent'] ?? $this->sourcecomponent)
        );
        $this->sourceid = max(0, (int)($data['sourceid'] ?? $this->sourceid));
        $this->sourceref = trim(clean_param((string)($data['sourceref'] ?? $data['sourceurl'] ?? $this->sourceref), PARAM_TEXT));

        $this->status = self::normalise_status((string)($data['status'] ?? $this->status));
        $this->visibility = self::normalise_visibility((string)($data['visibility'] ?? $this->visibility));
        $this->provenance = self::normalise_provenance((string)($data['provenance'] ?? $this->provenance));
        $this->validationstate = self::normalise_validation_state(
            (string)($data['validationstate'] ?? $data['integritystate'] ?? $this->validationstate)
        );

        $this->provenancehash = clean_param((string)($data['provenancehash'] ?? $this->provenancehash), PARAM_ALPHANUMEXT);
        $this->versionno = max(1, (int)($data['versionno'] ?? $this->versionno));
        $this->sortorder = max(0, (int)($data['sortorder'] ?? $this->sortorder));

        $this->createdby = max(0, (int)($data['createdby'] ?? $this->createdby));
        $this->modifiedby = max(0, (int)($data['modifiedby'] ?? $this->modifiedby));
        $this->timecreated = max(0, (int)($data['timecreated'] ?? $this->timecreated));
        $this->timemodified = max(0, (int)($data['timemodified'] ?? $this->timemodified));

        if (array_key_exists('metadata', $data)) {
            $this->metadata = self::normalise_metadata($data['metadata']);
        }
    }

    /**
     * Validate the Kristal.
     *
     * @throws \coding_exception If invalid.
     */
    public function validate(): void {
        if ($this->archiveid <= 0) {
            throw new \coding_exception('Kristal requires a valid archiveid.');
        }

        if ($this->title === '') {
            throw new \coding_exception('Kristal requires a title.');
        }

        if ($this->content === '') {
            throw new \coding_exception('Kristal requires content.');
        }

        if (!in_array($this->kristaltype, self::get_allowed_kristal_types(), true)) {
            throw new \coding_exception('Invalid Kristal type: ' . $this->kristaltype);
        }

        if (!in_array($this->status, self::get_allowed_statuses(), true)) {
            throw new \coding_exception('Invalid Kristal status: ' . $this->status);
        }

        if (!in_array($this->visibility, self::get_allowed_visibilities(), true)) {
            throw new \coding_exception('Invalid Kristal visibility: ' . $this->visibility);
        }

        if (!in_array($this->provenance, self::get_allowed_provenance_sources(), true)) {
            throw new \coding_exception('Invalid Kristal provenance: ' . $this->provenance);
        }

        if (!in_array($this->validationstate, self::get_allowed_validation_states(), true)) {
            throw new \coding_exception('Invalid Kristal validation state: ' . $this->validationstate);
        }
    }

    /**
     * Convert to a database record for {uckkarchive_kristal}.
     *
     * @param int|null $userid Acting user id.
     * @param int|null $now Timestamp.
     * @return stdClass
     */
    public function to_record(?int $userid = null, ?int $now = null): stdClass {
        $this->validate();

        $now ??= time();
        $userid ??= 0;

        $record = new stdClass();

        if ($this->id > 0) {
            $record->id = $this->id;
        }

        $record->archiveid = $this->archiveid;
        $record->itemid = $this->itemid;
        $record->proofid = $this->proofid;
        $record->courseid = $this->courseid;
        $record->cmid = $this->cmid;
        $record->contextid = $this->contextid;
        $record->userid = $this->userid;
        $record->kristaltype = $this->kristaltype;
        $record->title = $this->title;
        $record->summary = $this->summary;
        $record->content = $this->content;
        $record->sourcecomponent = $this->sourcecomponent !== '' ? $this->sourcecomponent : null;
        $record->sourceid = $this->sourceid;
        $record->sourceref = $this->sourceref !== '' ? $this->sourceref : null;
        $record->status = $this->status;
        $record->visibility = $this->visibility;
        $record->provenance = $this->provenance;
        $record->validationstate = $this->validationstate;
        $record->provenancehash = $this->provenancehash !== '' ? $this->provenancehash : null;
        $record->versionno = $this->versionno;
        $record->sortorder = $this->sortorder;

        $record->createdby = $this->createdby > 0 ? $this->createdby : $userid;
        $record->modifiedby = $userid > 0 ? $userid : $this->modifiedby;
        $record->timecreated = $this->timecreated > 0 ? $this->timecreated : $now;
        $record->timemodified = $now;
        $record->metadata = $this->metadata === []
            ? null
            : json_encode($this->metadata, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);

        return $record;
    }

    /**
     * Convert to export-safe data.
     *
     * @return stdClass
     */
    public function to_export(): stdClass {
        $data = new stdClass();
        $data->id = $this->id;
        $data->archiveid = $this->archiveid;
        $data->itemid = $this->itemid;
        $data->proofid = $this->proofid;
        $data->courseid = $this->courseid;
        $data->cmid = $this->cmid;
        $data->contextid = $this->contextid;
        $data->userid = $this->userid;
        $data->kristaltype = $this->kristaltype;
        $data->title = $this->title;
        $data->summary = $this->summary;
        $data->content = $this->content;
        $data->sourcecomponent = $this->sourcecomponent;
        $data->sourceid = $this->sourceid;
        $data->sourceref = $this->sourceref;
        $data->status = $this->status;
        $data->visibility = $this->visibility;
        $data->provenance = $this->provenance;
        $data->validationstate = $this->validationstate;
        $data->provenancehash = $this->provenancehash;
        $data->versionno = $this->versionno;
        $data->sortorder = $this->sortorder;
        $data->metadata = $this->metadata;
        return $data;
    }

    /**
     * Whether this Kristal is editable by service workflows.
     *
     * @return bool
     */
    public function is_editable(): bool {
        return in_array($this->status, [
            self::STATUS_DRAFT,
            self::STATUS_PENDING_REVIEW,
            self::STATUS_CORRECTION_REQUIRED,
        ], true);
    }

    /**
     * Whether this Kristal is validated.
     *
     * @return bool
     */
    public function is_validated(): bool {
        return $this->status === self::STATUS_VALIDATED
            || $this->validationstate === self::VALIDATION_VERIFIED;
    }

    /**
     * Whether this Kristal is contested.
     *
     * @return bool
     */
    public function is_contested(): bool {
        return $this->status === self::STATUS_CONTESTED
            || $this->validationstate === self::VALIDATION_CONTESTED;
    }

    /**
     * Whether this Kristal requires restricted integrity handling.
     *
     * @return bool
     */
    public function is_integrity_restricted(): bool {
        return $this->visibility === self::VISIBILITY_RESTRICTED_INTEGRITY
            || $this->validationstate === self::VALIDATION_CONTESTED
            || $this->validationstate === self::VALIDATION_INVALIDATED;
    }

    /**
     * Whether this Kristal is visible to normal course participants.
     *
     * @return bool
     */
    public function is_course_visible(): bool {
        return in_array($this->visibility, [
            self::VISIBILITY_COURSE,
            self::VISIBILITY_GROUP,
            self::VISIBILITY_COHORT,
            self::VISIBILITY_PROGRAM,
            self::VISIBILITY_INSTITUTION,
            self::VISIBILITY_PUBLIC,
        ], true);
    }

    /**
     * Get id.
     *
     * @return int
     */
    public function get_id(): int {
        return $this->id;
    }

    /**
     * Get archive id.
     *
     * @return int
     */
    public function get_archiveid(): int {
        return $this->archiveid;
    }

    /**
     * Get archive item id.
     *
     * @return int
     */
    public function get_itemid(): int {
        return $this->itemid;
    }

    /**
     * Get proof id.
     *
     * @return int
     */
    public function get_proofid(): int {
        return $this->proofid;
    }

    /**
     * Get Kristal type.
     *
     * @return string
     */
    public function get_kristaltype(): string {
        return $this->kristaltype;
    }

    /**
     * Get title.
     *
     * @return string
     */
    public function get_title(): string {
        return $this->title;
    }

    /**
     * Get summary.
     *
     * @return string
     */
    public function get_summary(): string {
        return $this->summary;
    }

    /**
     * Get content.
     *
     * @return string
     */
    public function get_content(): string {
        return $this->content;
    }

    /**
     * Get status.
     *
     * @return string
     */
    public function get_status(): string {
        return $this->status;
    }

    /**
     * Get visibility.
     *
     * @return string
     */
    public function get_visibility(): string {
        return $this->visibility;
    }

    /**
     * Get validation state.
     *
     * @return string
     */
    public function get_validationstate(): string {
        return $this->validationstate;
    }

    /**
     * Get provenance.
     *
     * @return string
     */
    public function get_provenance(): string {
        return $this->provenance;
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
     * Get metadata value.
     *
     * @param string $key Metadata key.
     * @param mixed $default Default value.
     * @return mixed
     */
    public function get_metadata_value(string $key, mixed $default = null): mixed {
        return $this->metadata[$key] ?? $default;
    }

    /**
     * Return copy with database id.
     *
     * @param int $id Record id.
     * @return self
     */
    public function with_id(int $id): self {
        $clone = clone $this;
        $clone->id = max(0, $id);
        return $clone;
    }

    /**
     * Return copy linked to an archive item.
     *
     * @param int $itemid Archive item id.
     * @return self
     */
    public function with_itemid(int $itemid): self {
        $clone = clone $this;
        $clone->itemid = max(0, $itemid);
        return $clone;
    }

    /**
     * Return copy linked to a proof.
     *
     * @param int $proofid Proof id.
     * @return self
     */
    public function with_proofid(int $proofid): self {
        $clone = clone $this;
        $clone->proofid = max(0, $proofid);
        return $clone;
    }

    /**
     * Return copy with context references.
     *
     * @param int $courseid Course id.
     * @param int $cmid Course module id.
     * @param int $contextid Context id.
     * @return self
     */
    public function with_context(int $courseid, int $cmid, int $contextid): self {
        $clone = clone $this;
        $clone->courseid = max(0, $courseid);
        $clone->cmid = max(0, $cmid);
        $clone->contextid = max(0, $contextid);
        return $clone;
    }

    /**
     * Return copy with source reference.
     *
     * @param string $sourcecomponent Source component.
     * @param int $sourceid Source id.
     * @param string $sourceref Source reference.
     * @return self
     */
    public function with_source(string $sourcecomponent, int $sourceid = 0, string $sourceref = ''): self {
        $clone = clone $this;
        $clone->sourcecomponent = self::normalise_source_component($sourcecomponent);
        $clone->sourceid = max(0, $sourceid);
        $clone->sourceref = trim(clean_param($sourceref, PARAM_TEXT));
        return $clone;
    }

    /**
     * Return copy with status.
     *
     * @param string $status New status.
     * @return self
     */
    public function with_status(string $status): self {
        $clone = clone $this;
        $clone->status = self::normalise_status($status);
        return $clone;
    }

    /**
     * Return copy with visibility.
     *
     * @param string $visibility New visibility.
     * @return self
     */
    public function with_visibility(string $visibility): self {
        $clone = clone $this;
        $clone->visibility = self::normalise_visibility($visibility);
        return $clone;
    }

    /**
     * Return copy with validation state.
     *
     * @param string $validationstate Validation state.
     * @return self
     */
    public function with_validationstate(string $validationstate): self {
        $clone = clone $this;
        $clone->validationstate = self::normalise_validation_state($validationstate);
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
     * Return copy marked modified by a user.
     *
     * @param int $userid User id.
     * @param int|null $now Timestamp.
     * @return self
     */
    public function mark_modified(int $userid, ?int $now = null): self {
        $clone = clone $this;
        $clone->modifiedby = max(0, $userid);
        $clone->timemodified = $now ?? time();
        $clone->versionno++;
        return $clone;
    }

    /**
     * Allowed Kristal types.
     *
     * @return string[]
     */
    public static function get_allowed_kristal_types(): array {
        return [
            self::TYPE_CONCEPT,
            self::TYPE_FORMULA,
            self::TYPE_METHOD,
            self::TYPE_DECISION,
            self::TYPE_LESSON,
            self::TYPE_QUESTION,
            self::TYPE_MAP,
            self::TYPE_REFERENCE,
            self::TYPE_GLOSSARY_ENTRY,
            self::TYPE_PROOF_PATTERN,
            self::TYPE_PORTFOLIO_INSIGHT,
        ];
    }

    /**
     * Allowed statuses.
     *
     * @return string[]
     */
    public static function get_allowed_statuses(): array {
        return [
            self::STATUS_DRAFT,
            self::STATUS_ACTIVE,
            self::STATUS_HIDDEN,
            self::STATUS_PENDING_REVIEW,
            self::STATUS_VALIDATED,
            self::STATUS_REJECTED,
            self::STATUS_CORRECTION_REQUIRED,
            self::STATUS_CONTESTED,
            self::STATUS_INVALIDATED,
            self::STATUS_ARCHIVED,
        ];
    }

    /**
     * Allowed visibilities.
     *
     * @return string[]
     */
    public static function get_allowed_visibilities(): array {
        return [
            self::VISIBILITY_PRIVATE,
            self::VISIBILITY_USER,
            self::VISIBILITY_GROUP,
            self::VISIBILITY_COURSE,
            self::VISIBILITY_COHORT,
            self::VISIBILITY_PROGRAM,
            self::VISIBILITY_INSTITUTION,
            self::VISIBILITY_PUBLIC,
            self::VISIBILITY_RESTRICTED,
            self::VISIBILITY_RESTRICTED_INTEGRITY,
            self::VISIBILITY_HIDDEN,
            self::VISIBILITY_ARCHIVED,
        ];
    }

    /**
     * Allowed provenance sources.
     *
     * @return string[]
     */
    public static function get_allowed_provenance_sources(): array {
        return [
            self::PROVENANCE_HUMAN,
            self::PROVENANCE_AI_ASSISTED,
            self::PROVENANCE_IMPORTED,
            self::PROVENANCE_SYSTEM,
            self::PROVENANCE_ARCHIVE,
            self::PROVENANCE_ASSEMBLY,
            self::PROVENANCE_CHALLENGE,
            self::PROVENANCE_INTEGRITY,
        ];
    }

    /**
     * Allowed validation states.
     *
     * @return string[]
     */
    public static function get_allowed_validation_states(): array {
        return [
            self::VALIDATION_UNVERIFIED,
            self::VALIDATION_HUMAN_REVIEWED,
            self::VALIDATION_VERIFIED,
            self::VALIDATION_CONTESTED,
            self::VALIDATION_INVALIDATED,
            self::VALIDATION_ARCHIVED,
        ];
    }

    /**
     * Normalise Kristal type.
     *
     * @param string $type Raw type.
     * @return string
     */
    private static function normalise_kristal_type(string $type): string {
        $type = clean_param($type, PARAM_ALPHANUMEXT);

        return in_array($type, self::get_allowed_kristal_types(), true)
            ? $type
            : self::TYPE_CONCEPT;
    }

    /**
     * Normalise title.
     *
     * @param string $title Raw title.
     * @return string
     */
    private static function normalise_title(string $title): string {
        return trim(clean_param($title, PARAM_TEXT));
    }

    /**
     * Normalise source component.
     *
     * @param string $component Raw source component.
     * @return string
     */
    private static function normalise_source_component(string $component): string {
        $component = trim($component);

        if ($component === '') {
            return '';
        }

        $cleaned = clean_param($component, PARAM_COMPONENT);

        return $cleaned === $component ? $cleaned : '';
    }

    /**
     * Normalise status.
     *
     * @param string $status Raw status.
     * @return string
     */
    private static function normalise_status(string $status): string {
        $status = clean_param($status, PARAM_ALPHANUMEXT);

        return in_array($status, self::get_allowed_statuses(), true)
            ? $status
            : self::STATUS_DRAFT;
    }

    /**
     * Normalise visibility.
     *
     * @param string $visibility Raw visibility.
     * @return string
     */
    private static function normalise_visibility(string $visibility): string {
        $visibility = clean_param($visibility, PARAM_ALPHANUMEXT);

        return in_array($visibility, self::get_allowed_visibilities(), true)
            ? $visibility
            : self::VISIBILITY_COURSE;
    }

    /**
     * Normalise provenance.
     *
     * @param string $provenance Raw provenance.
     * @return string
     */
    private static function normalise_provenance(string $provenance): string {
        $provenance = clean_param($provenance, PARAM_ALPHANUMEXT);

        return in_array($provenance, self::get_allowed_provenance_sources(), true)
            ? $provenance
            : self::PROVENANCE_HUMAN;
    }

    /**
     * Normalise validation state.
     *
     * @param string $validationstate Raw validation state.
     * @return string
     */
    private static function normalise_validation_state(string $validationstate): string {
        $validationstate = clean_param($validationstate, PARAM_ALPHANUMEXT);

        return in_array($validationstate, self::get_allowed_validation_states(), true)
            ? $validationstate
            : self::VALIDATION_UNVERIFIED;
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

        if (is_string($metadata)) {
            $decoded = json_decode($metadata, true);

            if (json_last_error() !== JSON_ERROR_NONE || !is_array($decoded)) {
                return [];
            }

            return $decoded;
        }

        if ($metadata instanceof stdClass) {
            return (array)$metadata;
        }

        if (is_array($metadata)) {
            return $metadata;
        }

        return [];
    }
}

