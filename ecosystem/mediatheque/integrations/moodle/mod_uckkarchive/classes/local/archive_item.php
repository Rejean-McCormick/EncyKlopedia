<?php
// This file is part of Moodle - https://moodle.org/
//
// Moodle is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// any later version.

/**
 * Local domain model for one UCKK archive item.
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
 * Domain object for an archive item.
 *
 * This class normalises and validates one archive item before service/database
 * layers insert, update, revise, validate, export, or render it.
 *
 * It does not decide permissions, validate evidence, export packages, resolve
 * integrity cases, redact restricted data, or write to the database directly.
 */
final class archive_item {
    /** Item type: proof. */
    public const TYPE_PROOF = 'proof';

    /** Item type: decision. */
    public const TYPE_DECISION = 'decision';

    /** Item type: minutes. */
    public const TYPE_MINUTES = 'minutes';

    /** Item type: challenge result. */
    public const TYPE_CHALLENGE_RESULT = 'challenge_result';

    /** Item type: course work. */
    public const TYPE_COURSE_WORK = 'course_work';

    /** Item type: portfolio item. */
    public const TYPE_PORTFOLIO_ITEM = 'portfolio_item';

    /** Item type: Kristal. */
    public const TYPE_KRISTAL = 'kristal';

    /** Item type: integrity summary. */
    public const TYPE_INTEGRITY_SUMMARY = 'integrity_summary';

    /** Item type: public summary. */
    public const TYPE_PUBLIC_SUMMARY = 'public_summary';

    /** Status: draft. */
    public const STATUS_DRAFT = 'draft';

    /** Status: active. */
    public const STATUS_ACTIVE = 'active';

    /** Status: hidden. */
    public const STATUS_HIDDEN = 'hidden';

    /** Status: pending. */
    public const STATUS_PENDING = 'pending';

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

    /** Status: closed. */
    public const STATUS_CLOSED = 'closed';

    /** Status: archived. */
    public const STATUS_ARCHIVED = 'archived';

    /** Status: cancelled. */
    public const STATUS_CANCELLED = 'cancelled';

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

    /** Parent archive activity instance id. */
    private int $archiveid = 0;

    /** Moodle course id. */
    private int $courseid = 0;

    /** Moodle course module id. */
    private int $cmid = 0;

    /** Moodle context id. */
    private int $contextid = 0;

    /** Owner or subject user id, when applicable. */
    private int $userid = 0;

    /** Item type. */
    private string $itemtype = self::TYPE_PROOF;

    /** Item title. */
    private string $title = '';

    /** Main archive item content. */
    private string $content = '';

    /** Safe public summary, if any. */
    private string $publicsummary = '';

    /** Source component, for example mod_uckkchallenge. */
    private string $sourcecomponent = '';

    /** Source area, for example submission, decision, minutes. */
    private string $sourcearea = '';

    /** Source id in the originating component. */
    private int $sourceid = 0;

    /** Source URL, if relevant and safe. */
    private string $sourceurl = '';

    /** Status. */
    private string $status = self::STATUS_DRAFT;

    /** Visibility. */
    private string $visibility = self::VISIBILITY_COURSE;

    /** Validation state. */
    private string $validationstate = self::VALIDATION_UNVERIFIED;

    /** Provenance source. */
    private string $provenance = self::PROVENANCE_HUMAN;

    /** Optional provenance hash. */
    private string $provenancehash = '';

    /** Whether restricted data is present. */
    private bool $hasrestricteddata = false;

    /** Whether an integrity review is required. */
    private bool $integrityrequired = false;

    /** Whether AI assistance was disclosed. */
    private bool $aiassisted = false;

    /** Version number. */
    private int $versionno = 1;

    /** Sort order. */
    private int $sortorder = 0;

    /** Creator user id. */
    private int $createdby = 0;

    /** Last modifier user id. */
    private int $modifiedby = 0;

    /** Creation timestamp. */
    private int $timecreated = 0;

    /** Modification timestamp. */
    private int $timemodified = 0;

    /** Variable metadata. */
    private array $metadata = [];

    /**
     * Constructor.
     *
     * @param array<string, mixed>|stdClass|null $data Initial item data.
     */
    public function __construct(array|stdClass|null $data = null) {
        if ($data !== null) {
            $this->apply_data((array)$data);
        }
    }

    /**
     * Build from a Moodle DB record.
     *
     * @param stdClass $record Record from {uckkarchive_item}.
     * @return self
     */
    public static function from_record(stdClass $record): self {
        return new self($record);
    }

    /**
     * Build a new item for an archive.
     *
     * @param int $archiveid Parent archive id.
     * @param int $contextid Context id.
     * @param string $title Item title.
     * @param string $content Item content.
     * @param string $itemtype Item type.
     * @return self
     */
    public static function create(
        int $archiveid,
        int $contextid,
        string $title,
        string $content,
        string $itemtype = self::TYPE_PROOF
    ): self {
        return new self([
            'archiveid' => $archiveid,
            'contextid' => $contextid,
            'title' => $title,
            'content' => $content,
            'itemtype' => $itemtype,
            'status' => self::STATUS_DRAFT,
            'visibility' => self::VISIBILITY_COURSE,
            'validationstate' => self::VALIDATION_UNVERIFIED,
            'provenance' => self::PROVENANCE_HUMAN,
            'versionno' => 1,
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
        $this->courseid = max(0, (int)($data['courseid'] ?? $this->courseid));
        $this->cmid = max(0, (int)($data['cmid'] ?? $this->cmid));
        $this->contextid = max(0, (int)($data['contextid'] ?? $this->contextid));
        $this->userid = max(0, (int)($data['userid'] ?? $this->userid));

        $this->itemtype = self::normalise_item_type((string)($data['itemtype'] ?? $data['type'] ?? $this->itemtype));
        $this->title = self::normalise_title((string)($data['title'] ?? $data['name'] ?? $this->title));
        $this->content = trim((string)($data['content'] ?? $data['body'] ?? $data['description'] ?? $this->content));
        $this->publicsummary = trim((string)($data['publicsummary'] ?? $data['summary'] ?? $this->publicsummary));

        $this->sourcecomponent = clean_param((string)($data['sourcecomponent'] ?? $this->sourcecomponent), PARAM_COMPONENT);
        $this->sourcearea = clean_param((string)($data['sourcearea'] ?? $this->sourcearea), PARAM_ALPHANUMEXT);
        $this->sourceid = max(0, (int)($data['sourceid'] ?? $this->sourceid));
        $this->sourceurl = clean_param((string)($data['sourceurl'] ?? $this->sourceurl), PARAM_URL);

        $this->status = self::normalise_status((string)($data['status'] ?? $this->status));
        $this->visibility = self::normalise_visibility((string)($data['visibility'] ?? $this->visibility));
        $this->validationstate = self::normalise_validation_state(
            (string)($data['validationstate'] ?? $data['validation'] ?? $this->validationstate)
        );
        $this->provenance = self::normalise_provenance((string)($data['provenance'] ?? $this->provenance));
        $this->provenancehash = clean_param((string)($data['provenancehash'] ?? $this->provenancehash), PARAM_ALPHANUMEXT);

        $this->hasrestricteddata = self::normalise_bool($data['hasrestricteddata'] ?? $this->hasrestricteddata);
        $this->integrityrequired = self::normalise_bool($data['integrityrequired'] ?? $this->integrityrequired);
        $this->aiassisted = self::normalise_bool($data['aiassisted'] ?? $this->aiassisted);

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
     * Validate this item.
     *
     * @throws \coding_exception If invalid.
     */
    public function validate(): void {
        if ($this->archiveid <= 0) {
            throw new \coding_exception('Archive item requires a valid archiveid.');
        }

        if ($this->contextid <= 0) {
            throw new \coding_exception('Archive item requires a valid contextid.');
        }

        if ($this->title === '') {
            throw new \coding_exception('Archive item requires a title.');
        }

        if ($this->content === '' && $this->publicsummary === '') {
            throw new \coding_exception('Archive item requires content or a public summary.');
        }

        if (!in_array($this->itemtype, self::get_allowed_item_types(), true)) {
            throw new \coding_exception('Invalid archive item type: ' . $this->itemtype);
        }

        if (!in_array($this->status, self::get_allowed_statuses(), true)) {
            throw new \coding_exception('Invalid archive item status: ' . $this->status);
        }

        if (!in_array($this->visibility, self::get_allowed_visibilities(), true)) {
            throw new \coding_exception('Invalid archive item visibility: ' . $this->visibility);
        }

        if (!in_array($this->validationstate, self::get_allowed_validation_states(), true)) {
            throw new \coding_exception('Invalid archive item validation state: ' . $this->validationstate);
        }

        if (!in_array($this->provenance, self::get_allowed_provenance_sources(), true)) {
            throw new \coding_exception('Invalid archive item provenance: ' . $this->provenance);
        }

        if ($this->visibility === self::VISIBILITY_PUBLIC && $this->hasrestricteddata) {
            throw new \coding_exception('Archive item with restricted data cannot be public.');
        }

        if ($this->visibility === self::VISIBILITY_PUBLIC && $this->validationstate === self::VALIDATION_UNVERIFIED) {
            throw new \coding_exception('Unverified archive item cannot be public.');
        }
    }

    /**
     * Convert to database record for {uckkarchive_item}.
     *
     * @param int|null $userid Acting user id.
     * @param int|null $now Timestamp.
     * @return stdClass
     */
    public function to_record(?int $userid = null, ?int $now = null): stdClass {
        $this->validate();

        $userid ??= 0;
        $now ??= time();

        $record = new stdClass();

        if ($this->id > 0) {
            $record->id = $this->id;
        }

        $record->archiveid = $this->archiveid;
        $record->courseid = $this->courseid;
        $record->cmid = $this->cmid;
        $record->contextid = $this->contextid;
        $record->userid = $this->userid;
        $record->itemtype = $this->itemtype;
        $record->title = $this->title;
        $record->content = $this->content;
        $record->publicsummary = $this->publicsummary;
        $record->sourcecomponent = $this->sourcecomponent;
        $record->sourcearea = $this->sourcearea;
        $record->sourceid = $this->sourceid;
        $record->sourceurl = $this->sourceurl;
        $record->status = $this->status;
        $record->visibility = $this->visibility;
        $record->validationstate = $this->validationstate;
        $record->provenance = $this->provenance;
        $record->provenancehash = $this->provenancehash !== '' ? $this->provenancehash : null;
        $record->hasrestricteddata = $this->hasrestricteddata ? 1 : 0;
        $record->integrityrequired = $this->integrityrequired ? 1 : 0;
        $record->aiassisted = $this->aiassisted ? 1 : 0;
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
     * @param bool $includerestricted Whether restricted details may be included.
     * @return stdClass
     */
    public function to_export(bool $includerestricted = false): stdClass {
        $data = new stdClass();
        $data->id = $this->id;
        $data->archiveid = $this->archiveid;
        $data->courseid = $this->courseid;
        $data->cmid = $this->cmid;
        $data->contextid = $this->contextid;
        $data->userid = $this->userid;
        $data->itemtype = $this->itemtype;
        $data->title = $this->title;
        $data->publicsummary = $this->publicsummary;
        $data->status = $this->status;
        $data->visibility = $this->visibility;
        $data->validationstate = $this->validationstate;
        $data->provenance = $this->provenance;
        $data->provenancehash = $this->provenancehash;
        $data->sourcecomponent = $this->sourcecomponent;
        $data->sourcearea = $this->sourcearea;
        $data->sourceid = $this->sourceid;
        $data->sourceurl = $this->sourceurl;
        $data->hasrestricteddata = $this->hasrestricteddata;
        $data->integrityrequired = $this->integrityrequired;
        $data->aiassisted = $this->aiassisted;
        $data->versionno = $this->versionno;
        $data->sortorder = $this->sortorder;
        $data->timecreated = $this->timecreated;
        $data->timemodified = $this->timemodified;

        if ($includerestricted || !$this->requires_restricted_handling()) {
            $data->content = $this->content;
            $data->metadata = $this->metadata;
        } else {
            $data->content = '';
            $data->metadata = [];
            $data->redacted = true;
        }

        return $data;
    }

    /**
     * Whether item can be edited by workflow services.
     *
     * @return bool
     */
    public function is_editable(): bool {
        return in_array($this->status, [
            self::STATUS_DRAFT,
            self::STATUS_PENDING,
            self::STATUS_PENDING_REVIEW,
            self::STATUS_CORRECTION_REQUIRED,
        ], true);
    }

    /**
     * Whether item is validated.
     *
     * @return bool
     */
    public function is_validated(): bool {
        return $this->status === self::STATUS_VALIDATED
            || $this->validationstate === self::VALIDATION_VERIFIED
            || $this->validationstate === self::VALIDATION_HUMAN_REVIEWED;
    }

    /**
     * Whether item is contested.
     *
     * @return bool
     */
    public function is_contested(): bool {
        return $this->status === self::STATUS_CONTESTED
            || $this->validationstate === self::VALIDATION_CONTESTED;
    }

    /**
     * Whether item is invalidated.
     *
     * @return bool
     */
    public function is_invalidated(): bool {
        return $this->status === self::STATUS_INVALIDATED
            || $this->validationstate === self::VALIDATION_INVALIDATED;
    }

    /**
     * Whether item can be shown to ordinary course viewers.
     *
     * @return bool
     */
    public function is_course_visible(): bool {
        return !$this->requires_restricted_handling()
            && in_array($this->visibility, [
                self::VISIBILITY_COURSE,
                self::VISIBILITY_GROUP,
                self::VISIBILITY_COHORT,
                self::VISIBILITY_PROGRAM,
                self::VISIBILITY_INSTITUTION,
                self::VISIBILITY_PUBLIC,
            ], true);
    }

    /**
     * Whether item requires restricted handling.
     *
     * @return bool
     */
    public function requires_restricted_handling(): bool {
        return $this->hasrestricteddata
            || $this->integrityrequired
            || $this->visibility === self::VISIBILITY_RESTRICTED
            || $this->visibility === self::VISIBILITY_RESTRICTED_INTEGRITY
            || $this->itemtype === self::TYPE_INTEGRITY_SUMMARY;
    }

    /**
     * Whether item can be exported without redaction.
     *
     * @return bool
     */
    public function can_export_unrestricted(): bool {
        return !$this->requires_restricted_handling()
            && $this->is_validated()
            && !$this->is_invalidated();
    }

    /**
     * Return id.
     *
     * @return int
     */
    public function get_id(): int {
        return $this->id;
    }

    /**
     * Return archive id.
     *
     * @return int
     */
    public function get_archiveid(): int {
        return $this->archiveid;
    }

    /**
     * Return context id.
     *
     * @return int
     */
    public function get_contextid(): int {
        return $this->contextid;
    }

    /**
     * Return item type.
     *
     * @return string
     */
    public function get_itemtype(): string {
        return $this->itemtype;
    }

    /**
     * Return title.
     *
     * @return string
     */
    public function get_title(): string {
        return $this->title;
    }

    /**
     * Return content.
     *
     * @return string
     */
    public function get_content(): string {
        return $this->content;
    }

    /**
     * Return public summary.
     *
     * @return string
     */
    public function get_publicsummary(): string {
        return $this->publicsummary;
    }

    /**
     * Return status.
     *
     * @return string
     */
    public function get_status(): string {
        return $this->status;
    }

    /**
     * Return visibility.
     *
     * @return string
     */
    public function get_visibility(): string {
        return $this->visibility;
    }

    /**
     * Return validation state.
     *
     * @return string
     */
    public function get_validationstate(): string {
        return $this->validationstate;
    }

    /**
     * Return provenance.
     *
     * @return string
     */
    public function get_provenance(): string {
        return $this->provenance;
    }

    /**
     * Return version number.
     *
     * @return int
     */
    public function get_versionno(): int {
        return $this->versionno;
    }

    /**
     * Return metadata.
     *
     * @return array<string, mixed>
     */
    public function get_metadata(): array {
        return $this->metadata;
    }

    /**
     * Return metadata value.
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
     * Return copy with Moodle context references.
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
     * @param string $component Source component.
     * @param string $area Source area.
     * @param int $sourceid Source id.
     * @param string $sourceurl Source URL.
     * @return self
     */
    public function with_source(string $component, string $area, int $sourceid, string $sourceurl = ''): self {
        $clone = clone $this;
        $clone->sourcecomponent = clean_param($component, PARAM_COMPONENT);
        $clone->sourcearea = clean_param($area, PARAM_ALPHANUMEXT);
        $clone->sourceid = max(0, $sourceid);
        $clone->sourceurl = clean_param($sourceurl, PARAM_URL);
        return $clone;
    }

    /**
     * Return copy with status.
     *
     * @param string $status Status.
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
     * @param string $visibility Visibility.
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
     * Return copy marked as revised.
     *
     * @param int $userid Acting user id.
     * @param int|null $now Timestamp.
     * @return self
     */
    public function mark_revised(int $userid, ?int $now = null): self {
        $clone = clone $this;
        $clone->modifiedby = max(0, $userid);
        $clone->timemodified = $now ?? time();
        $clone->versionno++;
        return $clone;
    }

    /**
     * Allowed item types.
     *
     * @return string[]
     */
    public static function get_allowed_item_types(): array {
        return [
            self::TYPE_PROOF,
            self::TYPE_DECISION,
            self::TYPE_MINUTES,
            self::TYPE_CHALLENGE_RESULT,
            self::TYPE_COURSE_WORK,
            self::TYPE_PORTFOLIO_ITEM,
            self::TYPE_KRISTAL,
            self::TYPE_INTEGRITY_SUMMARY,
            self::TYPE_PUBLIC_SUMMARY,
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
            self::STATUS_PENDING,
            self::STATUS_PENDING_REVIEW,
            self::STATUS_VALIDATED,
            self::STATUS_REJECTED,
            self::STATUS_CORRECTION_REQUIRED,
            self::STATUS_CONTESTED,
            self::STATUS_INVALIDATED,
            self::STATUS_CLOSED,
            self::STATUS_ARCHIVED,
            self::STATUS_CANCELLED,
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
     * Normalise item type.
     *
     * @param string $itemtype Raw item type.
     * @return string
     */
    private static function normalise_item_type(string $itemtype): string {
        $itemtype = clean_param($itemtype, PARAM_ALPHANUMEXT);

        return in_array($itemtype, self::get_allowed_item_types(), true)
            ? $itemtype
            : self::TYPE_PROOF;
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
     * Normalise a bool-ish value.
     *
     * @param mixed $value Raw value.
     * @return bool
     */
    private static function normalise_bool(mixed $value): bool {
        if (is_bool($value)) {
            return $value;
        }

        if (is_numeric($value)) {
            return (int)$value === 1;
        }

        if (is_string($value)) {
            return in_array(strtolower($value), ['1', 'true', 'yes', 'on'], true);
        }

        return !empty($value);
    }

    /**
     * Normalise metadata.
     *
     * @param mixed $metadata Raw metadata array, object, or JSON string.
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

