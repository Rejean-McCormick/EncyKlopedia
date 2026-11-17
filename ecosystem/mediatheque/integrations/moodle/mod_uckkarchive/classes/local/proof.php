<?php
// This file is part of Moodle - https://moodle.org/
//
// Moodle is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// any later version.

/**
 * Local domain model for one UCKK archive proof.
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
 * Domain object representing one proof attached to an archive item.
 *
 * This class normalises and validates proof data before service/database layers
 * insert, update, validate, revise, export, or render it.
 *
 * It does not write to the database, decide permissions, validate evidence,
 * open integrity cases, export files, or make AI/human authority decisions.
 */
final class proof {
    /** Proof type: text. */
    public const TYPE_TEXT = 'text';

    /** Proof type: file. */
    public const TYPE_FILE = 'file';

    /** Proof type: URL. */
    public const TYPE_URL = 'url';

    /** Proof type: dataset. */
    public const TYPE_DATASET = 'dataset';

    /** Proof type: image. */
    public const TYPE_IMAGE = 'image';

    /** Proof type: video. */
    public const TYPE_VIDEO = 'video';

    /** Proof type: testimony. */
    public const TYPE_TESTIMONY = 'testimony';

    /** Proof type: observation. */
    public const TYPE_OBSERVATION = 'observation';

    /** Proof type: AI log. */
    public const TYPE_AI_LOG = 'ai_log';

    /** Proof type: decision record. */
    public const TYPE_DECISION_RECORD = 'decision_record';

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

    /** Database id. */
    private int $id = 0;

    /** Parent archive activity instance id. */
    private int $archiveid = 0;

    /** Parent archive item id. */
    private int $archiveitemid = 0;

    /** Moodle course id. */
    private int $courseid = 0;

    /** Moodle course module id. */
    private int $cmid = 0;

    /** Moodle context id. */
    private int $contextid = 0;

    /** Proof owner or submitting user id. */
    private int $userid = 0;

    /** Proof type. */
    private string $prooftype = self::TYPE_TEXT;

    /** Proof title. */
    private string $title = '';

    /** Proof summary. */
    private string $summary = '';

    /** Proof body/text. */
    private string $body = '';

    /** Optional external URL. */
    private string $url = '';

    /** Moodle file item id for this proof. */
    private int $fileitemid = 0;

    /** Optional file name. */
    private string $filename = '';

    /** Optional MIME type. */
    private string $mimetype = '';

    /** Optional file size. */
    private int $filesize = 0;

    /** Optional checksum/hash. */
    private string $checksum = '';

    /** Source component, for cross-plugin evidence. */
    private string $sourcecomponent = '';

    /** Source item id, for cross-plugin evidence. */
    private int $sourceitemid = 0;

    /** Source URL or external identifier. */
    private string $sourceurl = '';

    /** Source author or institution. */
    private string $sourceauthor = '';

    /** Source date timestamp. */
    private int $sourcedate = 0;

    /** Status. */
    private string $status = self::STATUS_DRAFT;

    /** Validation state. */
    private string $validationstate = self::VALIDATION_UNVERIFIED;

    /** Visibility. */
    private string $visibility = self::VISIBILITY_COURSE;

    /** Provenance. */
    private string $provenance = self::PROVENANCE_HUMAN;

    /** Optional provenance hash. */
    private string $provenancehash = '';

    /** Version number. */
    private int $versionno = 1;

    /** Sort order. */
    private int $sortorder = 0;

    /** User who validated this proof. */
    private int $validatedby = 0;

    /** Validation timestamp. */
    private int $timevalidated = 0;

    /** User who created this proof record. */
    private int $createdby = 0;

    /** User who last modified this proof record. */
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
     * @param array<string, mixed>|stdClass|null $data Initial proof data.
     */
    public function __construct(array|stdClass|null $data = null) {
        if ($data !== null) {
            $this->apply_data((array)$data);
        }
    }

    /**
     * Build a proof object from a Moodle database record.
     *
     * @param stdClass $record Record from {uckkarchive_proof}.
     * @return self
     */
    public static function from_record(stdClass $record): self {
        return new self($record);
    }

    /**
     * Build a new proof for an archive item.
     *
     * @param int $archiveid Archive activity instance id.
     * @param int $archiveitemid Archive item id.
     * @param int $userid Owner/submitting user id.
     * @param string $title Proof title.
     * @param string $body Proof body.
     * @param string $prooftype Proof type.
     * @return self
     */
    public static function create(
        int $archiveid,
        int $archiveitemid,
        int $userid,
        string $title,
        string $body,
        string $prooftype = self::TYPE_TEXT
    ): self {
        return new self([
            'archiveid' => $archiveid,
            'archiveitemid' => $archiveitemid,
            'userid' => $userid,
            'title' => $title,
            'body' => $body,
            'prooftype' => $prooftype,
            'status' => self::STATUS_DRAFT,
            'validationstate' => self::VALIDATION_UNVERIFIED,
            'visibility' => self::VISIBILITY_COURSE,
            'provenance' => self::PROVENANCE_HUMAN,
            'versionno' => 1,
        ]);
    }

    /**
     * Apply raw data to this object.
     *
     * @param array<string, mixed> $data Raw input data.
     */
    private function apply_data(array $data): void {
        $this->id = max(0, (int)($data['id'] ?? $this->id));
        $this->archiveid = max(0, (int)($data['archiveid'] ?? $data['uckkarchiveid'] ?? $this->archiveid));
        $this->archiveitemid = max(0, (int)(
            $data['archiveitemid']
            ?? $data['itemid']
            ?? $data['uckkarchiveitemid']
            ?? $this->archiveitemid
        ));

        $this->courseid = max(0, (int)($data['courseid'] ?? $this->courseid));
        $this->cmid = max(0, (int)($data['cmid'] ?? $this->cmid));
        $this->contextid = max(0, (int)($data['contextid'] ?? $this->contextid));
        $this->userid = max(0, (int)($data['userid'] ?? $data['owneruserid'] ?? $this->userid));

        $this->prooftype = self::normalise_proof_type((string)($data['prooftype'] ?? $data['type'] ?? $this->prooftype));
        $this->title = self::normalise_title((string)($data['title'] ?? $data['name'] ?? $this->title));
        $this->summary = trim((string)($data['summary'] ?? $this->summary));
        $this->body = trim((string)($data['body'] ?? $data['content'] ?? $data['prooftext'] ?? $this->body));
        $this->url = self::normalise_url((string)($data['url'] ?? $data['proofurl'] ?? $this->url));

        $this->fileitemid = max(0, (int)($data['fileitemid'] ?? $data['draftitemid'] ?? $this->fileitemid));
        $this->filename = self::normalise_filename((string)($data['filename'] ?? $this->filename));
        $this->mimetype = clean_param((string)($data['mimetype'] ?? $this->mimetype), PARAM_MIMETYPE);
        $this->filesize = max(0, (int)($data['filesize'] ?? $this->filesize));
        $this->checksum = self::normalise_checksum((string)($data['checksum'] ?? $data['contenthash'] ?? $this->checksum));

        $this->sourcecomponent = clean_param((string)($data['sourcecomponent'] ?? $this->sourcecomponent), PARAM_COMPONENT);
        $this->sourceitemid = max(0, (int)($data['sourceitemid'] ?? $this->sourceitemid));
        $this->sourceurl = self::normalise_url((string)($data['sourceurl'] ?? $this->sourceurl));
        $this->sourceauthor = self::normalise_title((string)($data['sourceauthor'] ?? $this->sourceauthor));
        $this->sourcedate = max(0, (int)($data['sourcedate'] ?? $this->sourcedate));

        $this->status = self::normalise_status((string)($data['status'] ?? $this->status));
        $this->validationstate = self::normalise_validation_state(
            (string)($data['validationstate'] ?? $data['validation'] ?? $this->validationstate)
        );
        $this->visibility = self::normalise_visibility((string)($data['visibility'] ?? $this->visibility));
        $this->provenance = self::normalise_provenance((string)($data['provenance'] ?? $this->provenance));
        $this->provenancehash = self::normalise_checksum((string)($data['provenancehash'] ?? $this->provenancehash));

        $this->versionno = max(1, (int)($data['versionno'] ?? $this->versionno));
        $this->sortorder = max(0, (int)($data['sortorder'] ?? $this->sortorder));

        $this->validatedby = max(0, (int)($data['validatedby'] ?? $this->validatedby));
        $this->timevalidated = max(0, (int)($data['timevalidated'] ?? $this->timevalidated));
        $this->createdby = max(0, (int)($data['createdby'] ?? $this->createdby));
        $this->modifiedby = max(0, (int)($data['modifiedby'] ?? $this->modifiedby));
        $this->timecreated = max(0, (int)($data['timecreated'] ?? $this->timecreated));
        $this->timemodified = max(0, (int)($data['timemodified'] ?? $this->timemodified));

        if (array_key_exists('metadata', $data)) {
            $this->metadata = self::normalise_metadata($data['metadata']);
        }
    }

    /**
     * Validate this proof.
     *
     * @throws \coding_exception If the proof is invalid.
     */
    public function validate(): void {
        if ($this->archiveid <= 0) {
            throw new \coding_exception('Archive proof requires a valid archiveid.');
        }

        if ($this->archiveitemid <= 0) {
            throw new \coding_exception('Archive proof requires a valid archiveitemid.');
        }

        if ($this->title === '') {
            throw new \coding_exception('Archive proof requires a title.');
        }

        if (!in_array($this->prooftype, self::get_allowed_proof_types(), true)) {
            throw new \coding_exception('Invalid archive proof type: ' . $this->prooftype);
        }

        if (!in_array($this->status, self::get_allowed_statuses(), true)) {
            throw new \coding_exception('Invalid archive proof status: ' . $this->status);
        }

        if (!in_array($this->validationstate, self::get_allowed_validation_states(), true)) {
            throw new \coding_exception('Invalid archive proof validation state: ' . $this->validationstate);
        }

        if (!in_array($this->visibility, self::get_allowed_visibilities(), true)) {
            throw new \coding_exception('Invalid archive proof visibility: ' . $this->visibility);
        }

        if (!in_array($this->provenance, self::get_allowed_provenance_sources(), true)) {
            throw new \coding_exception('Invalid archive proof provenance: ' . $this->provenance);
        }

        if ($this->requires_body() && $this->body === '' && $this->summary === '') {
            throw new \coding_exception('Archive proof requires body or summary text for this proof type.');
        }

        if ($this->requires_url() && $this->url === '' && $this->sourceurl === '') {
            throw new \coding_exception('Archive proof requires a URL for this proof type.');
        }

        if ($this->requires_file() && $this->fileitemid <= 0 && $this->filename === '') {
            throw new \coding_exception('Archive proof requires a file item id or filename for this proof type.');
        }
    }

    /**
     * Convert to a database record for {uckkarchive_proof}.
     *
     * @param int|null $userid Acting user id.
     * @param int|null $now Current timestamp.
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
        $record->archiveitemid = $this->archiveitemid;
        $record->courseid = $this->courseid;
        $record->cmid = $this->cmid;
        $record->contextid = $this->contextid;
        $record->userid = $this->userid;

        $record->prooftype = $this->prooftype;
        $record->title = $this->title;
        $record->summary = $this->summary;
        $record->body = $this->body;
        $record->url = $this->url !== '' ? $this->url : null;

        $record->fileitemid = $this->fileitemid;
        $record->filename = $this->filename !== '' ? $this->filename : null;
        $record->mimetype = $this->mimetype !== '' ? $this->mimetype : null;
        $record->filesize = $this->filesize;
        $record->checksum = $this->checksum !== '' ? $this->checksum : null;

        $record->sourcecomponent = $this->sourcecomponent !== '' ? $this->sourcecomponent : null;
        $record->sourceitemid = $this->sourceitemid;
        $record->sourceurl = $this->sourceurl !== '' ? $this->sourceurl : null;
        $record->sourceauthor = $this->sourceauthor !== '' ? $this->sourceauthor : null;
        $record->sourcedate = $this->sourcedate;

        $record->status = $this->status;
        $record->validationstate = $this->validationstate;
        $record->visibility = $this->visibility;
        $record->provenance = $this->provenance;
        $record->provenancehash = $this->provenancehash !== '' ? $this->provenancehash : null;
        $record->versionno = $this->versionno;
        $record->sortorder = $this->sortorder;

        $record->validatedby = $this->validatedby;
        $record->timevalidated = $this->timevalidated;
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
        $data->archiveitemid = $this->archiveitemid;
        $data->courseid = $this->courseid;
        $data->cmid = $this->cmid;
        $data->contextid = $this->contextid;
        $data->userid = $this->userid;
        $data->prooftype = $this->prooftype;
        $data->title = $this->title;
        $data->summary = $this->summary;
        $data->body = $this->body;
        $data->url = $this->url;
        $data->fileitemid = $this->fileitemid;
        $data->filename = $this->filename;
        $data->mimetype = $this->mimetype;
        $data->filesize = $this->filesize;
        $data->checksum = $this->checksum;
        $data->sourcecomponent = $this->sourcecomponent;
        $data->sourceitemid = $this->sourceitemid;
        $data->sourceurl = $this->sourceurl;
        $data->sourceauthor = $this->sourceauthor;
        $data->sourcedate = $this->sourcedate;
        $data->status = $this->status;
        $data->validationstate = $this->validationstate;
        $data->visibility = $this->visibility;
        $data->provenance = $this->provenance;
        $data->provenancehash = $this->provenancehash;
        $data->versionno = $this->versionno;
        $data->sortorder = $this->sortorder;
        $data->validatedby = $this->validatedby;
        $data->timevalidated = $this->timevalidated;
        $data->timecreated = $this->timecreated;
        $data->timemodified = $this->timemodified;
        $data->metadata = $this->metadata;

        $data->hasurl = $this->url !== '';
        $data->hasfile = $this->fileitemid > 0 || $this->filename !== '';
        $data->haschecksum = $this->checksum !== '';
        $data->hasprovenancehash = $this->provenancehash !== '';
        $data->isvalidated = $this->is_validated();
        $data->isrestricted = $this->is_restricted();
        $data->isaiassisted = $this->provenance === self::PROVENANCE_AI_ASSISTED || $this->prooftype === self::TYPE_AI_LOG;

        return $data;
    }

    /**
     * Whether this proof requires body/summary text.
     *
     * @return bool
     */
    public function requires_body(): bool {
        return in_array($this->prooftype, [
            self::TYPE_TEXT,
            self::TYPE_TESTIMONY,
            self::TYPE_OBSERVATION,
            self::TYPE_AI_LOG,
            self::TYPE_DECISION_RECORD,
        ], true);
    }

    /**
     * Whether this proof requires a URL.
     *
     * @return bool
     */
    public function requires_url(): bool {
        return $this->prooftype === self::TYPE_URL;
    }

    /**
     * Whether this proof requires a file reference.
     *
     * @return bool
     */
    public function requires_file(): bool {
        return in_array($this->prooftype, [
            self::TYPE_FILE,
            self::TYPE_DATASET,
            self::TYPE_IMAGE,
            self::TYPE_VIDEO,
        ], true);
    }

    /**
     * Whether this proof has been human/authoritatively validated.
     *
     * @return bool
     */
    public function is_validated(): bool {
        return in_array($this->validationstate, [
            self::VALIDATION_HUMAN_REVIEWED,
            self::VALIDATION_VERIFIED,
            self::VALIDATION_ARCHIVED,
        ], true);
    }

    /**
     * Whether this proof is contested.
     *
     * @return bool
     */
    public function is_contested(): bool {
        return $this->status === self::STATUS_CONTESTED
            || $this->validationstate === self::VALIDATION_CONTESTED;
    }

    /**
     * Whether this proof is invalidated.
     *
     * @return bool
     */
    public function is_invalidated(): bool {
        return $this->status === self::STATUS_INVALIDATED
            || $this->validationstate === self::VALIDATION_INVALIDATED;
    }

    /**
     * Whether this proof must be protected from ordinary views/exports.
     *
     * @return bool
     */
    public function is_restricted(): bool {
        return in_array($this->visibility, [
            self::VISIBILITY_PRIVATE,
            self::VISIBILITY_RESTRICTED,
            self::VISIBILITY_RESTRICTED_INTEGRITY,
            self::VISIBILITY_HIDDEN,
        ], true);
    }

    /**
     * Whether this proof is visible at course level without restricted capability.
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
     * Whether this proof is editable by archive services.
     *
     * @return bool
     */
    public function is_editable(): bool {
        return in_array($this->status, [
            self::STATUS_DRAFT,
            self::STATUS_PENDING,
            self::STATUS_CORRECTION_REQUIRED,
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
    public function get_archiveitemid(): int {
        return $this->archiveitemid;
    }

    /**
     * Get proof owner/submitting user id.
     *
     * @return int
     */
    public function get_userid(): int {
        return $this->userid;
    }

    /**
     * Get proof type.
     *
     * @return string
     */
    public function get_prooftype(): string {
        return $this->prooftype;
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
     * Get body.
     *
     * @return string
     */
    public function get_body(): string {
        return $this->body;
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
     * Get validation state.
     *
     * @return string
     */
    public function get_validationstate(): string {
        return $this->validationstate;
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
     * Get provenance.
     *
     * @return string
     */
    public function get_provenance(): string {
        return $this->provenance;
    }

    /**
     * Get file item id.
     *
     * @return int
     */
    public function get_fileitemid(): int {
        return $this->fileitemid;
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
     * Return copy with updated status.
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
     * Return copy with updated validation state.
     *
     * @param string $validationstate New validation state.
     * @return self
     */
    public function with_validationstate(string $validationstate): self {
        $clone = clone $this;
        $clone->validationstate = self::normalise_validation_state($validationstate);
        return $clone;
    }

    /**
     * Return copy with updated visibility.
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
     * Return copy with updated metadata.
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
     * Return copy marked as validated.
     *
     * @param int $userid Validator user id.
     * @param int|null $now Timestamp.
     * @return self
     */
    public function mark_validated(int $userid, ?int $now = null): self {
        $clone = clone $this;
        $clone->status = self::STATUS_VALIDATED;
        $clone->validationstate = self::VALIDATION_VERIFIED;
        $clone->validatedby = max(0, $userid);
        $clone->timevalidated = $now ?? time();
        $clone->modifiedby = max(0, $userid);
        $clone->timemodified = $clone->timevalidated;
        $clone->versionno++;
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
     * Allowed proof types.
     *
     * @return string[]
     */
    public static function get_allowed_proof_types(): array {
        return [
            self::TYPE_TEXT,
            self::TYPE_FILE,
            self::TYPE_URL,
            self::TYPE_DATASET,
            self::TYPE_IMAGE,
            self::TYPE_VIDEO,
            self::TYPE_TESTIMONY,
            self::TYPE_OBSERVATION,
            self::TYPE_AI_LOG,
            self::TYPE_DECISION_RECORD,
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
     * Normalise proof type.
     *
     * @param string $prooftype Raw proof type.
     * @return string
     */
    private static function normalise_proof_type(string $prooftype): string {
        $prooftype = clean_param($prooftype, PARAM_ALPHANUMEXT);

        return in_array($prooftype, self::get_allowed_proof_types(), true)
            ? $prooftype
            : self::TYPE_TEXT;
    }

    /**
     * Normalise title-like text.
     *
     * @param string $title Raw title.
     * @return string
     */
    private static function normalise_title(string $title): string {
        return trim(clean_param($title, PARAM_TEXT));
    }

    /**
     * Normalise filename.
     *
     * @param string $filename Raw filename.
     * @return string
     */
    private static function normalise_filename(string $filename): string {
        return trim(clean_param($filename, PARAM_FILE));
    }

    /**
     * Normalise URL.
     *
     * @param string $url Raw URL.
     * @return string
     */
    private static function normalise_url(string $url): string {
        $url = trim($url);

        if ($url === '') {
            return '';
        }

        return clean_param($url, PARAM_URL);
    }

    /**
     * Normalise checksum/hash.
     *
     * @param string $checksum Raw checksum.
     * @return string
     */
    private static function normalise_checksum(string $checksum): string {
        return clean_param(trim($checksum), PARAM_ALPHANUMEXT);
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

