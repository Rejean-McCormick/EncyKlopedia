<?php
// This file is part of Moodle - https://moodle.org/
//
// Moodle is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// any later version.

/**
 * Local domain model for UCKK archive provenance records.
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
 * Domain object representing one provenance record.
 *
 * This class normalises and validates provenance data before service/database
 * layers insert, update, render, export, revise, or archive it.
 *
 * It does not decide permissions, validate evidence, open integrity cases,
 * revise archive items, or write directly to the database.
 */
final class provenance {
    /** Owning Moodle component. */
    public const COMPONENT = 'mod_uckkarchive';

    /** Default subject type. */
    public const SUBJECT_ARCHIVE_ITEM = 'archive_item';

    /** Subject type: proof. */
    public const SUBJECT_PROOF = 'proof';

    /** Subject type: Kristal. */
    public const SUBJECT_KRISTAL = 'kristal';

    /** Subject type: revision. */
    public const SUBJECT_REVISION = 'revision';

    /** Subject type: export package. */
    public const SUBJECT_EXPORT = 'export';

    /** Provenance source: human. */
    public const PROVENANCE_HUMAN = 'human';

    /** Provenance source: AI-assisted. */
    public const PROVENANCE_AI_ASSISTED = 'ai_assisted';

    /** Provenance source: imported. */
    public const PROVENANCE_IMPORTED = 'imported';

    /** Provenance source: system. */
    public const PROVENANCE_SYSTEM = 'system';

    /** Provenance source: archive. */
    public const PROVENANCE_ARCHIVE = 'archive';

    /** Provenance source: assembly. */
    public const PROVENANCE_ASSEMBLY = 'assembly';

    /** Provenance source: challenge. */
    public const PROVENANCE_CHALLENGE = 'challenge';

    /** Provenance source: integrity. */
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

    /** Status: draft. */
    public const STATUS_DRAFT = 'draft';

    /** Status: active. */
    public const STATUS_ACTIVE = 'active';

    /** Status: pending review. */
    public const STATUS_PENDING_REVIEW = 'pending_review';

    /** Status: validated. */
    public const STATUS_VALIDATED = 'validated';

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

    /** Database id. */
    private int $id = 0;

    /** Parent archive activity instance id. */
    private int $archiveid = 0;

    /** Related archive item id. */
    private int $itemid = 0;

    /** Related proof id. */
    private int $proofid = 0;

    /** Related Kristal id. */
    private int $kristalid = 0;

    /** Related revision id. */
    private int $revisionid = 0;

    /** Moodle course id. */
    private int $courseid = 0;

    /** Moodle course module id. */
    private int $cmid = 0;

    /** Moodle context id. */
    private int $contextid = 0;

    /** User associated with the provenance subject. */
    private int $userid = 0;

    /** Component owning the subject record. */
    private string $component = self::COMPONENT;

    /** Subject type inside the owning component. */
    private string $subjecttype = self::SUBJECT_ARCHIVE_ITEM;

    /** Subject id inside the owning component. */
    private int $subjectid = 0;

    /** Component where the source originated. */
    private string $sourcecomponent = '';

    /** Source object type. */
    private string $sourcetype = '';

    /** Source object id. */
    private int $sourceid = 0;

    /** Source context id. */
    private int $sourcecontextid = 0;

    /** Optional source URL. */
    private string $sourceurl = '';

    /** Optional source title. */
    private string $sourcetitle = '';

    /** Optional source author label. */
    private string $sourceauthor = '';

    /** Optional source timestamp/date. */
    private int $sourcedate = 0;

    /** Human-readable provenance statement. */
    private string $statement = '';

    /** Provenance source category. */
    private string $provenance = self::PROVENANCE_HUMAN;

    /** Validation state. */
    private string $validationstate = self::VALIDATION_UNVERIFIED;

    /** Record status. */
    private string $status = self::STATUS_ACTIVE;

    /** Record visibility. */
    private string $visibility = self::VISIBILITY_COURSE;

    /** Stable provenance hash. */
    private string $provenancehash = '';

    /** Compatibility alias for systems using hash instead of provenancehash. */
    private string $hash = '';

    /** Version number. */
    private int $versionno = 1;

    /** User who created this record. */
    private int $createdby = 0;

    /** User who last modified this record. */
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
     * @param array<string, mixed>|stdClass|null $data Initial data.
     */
    public function __construct(array|stdClass|null $data = null) {
        if ($data !== null) {
            $this->apply_data((array)$data);
        }
    }

    /**
     * Build provenance from a database record.
     *
     * @param stdClass $record Record from {uckkarchive_prov}.
     * @return self
     */
    public static function from_record(stdClass $record): self {
        return new self($record);
    }

    /**
     * Build provenance for an archive item.
     *
     * @param int $archiveid Archive activity instance id.
     * @param int $itemid Archive item id.
     * @param int $contextid Moodle context id.
     * @param string $sourcecomponent Source component.
     * @param string $sourcetype Source type.
     * @param int $sourceid Source id.
     * @param string $statement Human-readable provenance statement.
     * @return self
     */
    public static function for_archive_item(
        int $archiveid,
        int $itemid,
        int $contextid,
        string $sourcecomponent,
        string $sourcetype,
        int $sourceid,
        string $statement
    ): self {
        return new self([
            'archiveid' => $archiveid,
            'itemid' => $itemid,
            'contextid' => $contextid,
            'component' => self::COMPONENT,
            'subjecttype' => self::SUBJECT_ARCHIVE_ITEM,
            'subjectid' => $itemid,
            'sourcecomponent' => $sourcecomponent,
            'sourcetype' => $sourcetype,
            'sourceid' => $sourceid,
            'statement' => $statement,
            'provenance' => self::PROVENANCE_HUMAN,
            'validationstate' => self::VALIDATION_UNVERIFIED,
            'status' => self::STATUS_ACTIVE,
            'visibility' => self::VISIBILITY_COURSE,
        ]);
    }

    /**
     * Build provenance for an imported record.
     *
     * @param int $archiveid Archive activity instance id.
     * @param int $contextid Moodle context id.
     * @param string $sourcecomponent Source component.
     * @param string $sourcetitle Source title.
     * @param string $statement Provenance statement.
     * @param array<string, mixed> $metadata Metadata.
     * @return self
     */
    public static function imported(
        int $archiveid,
        int $contextid,
        string $sourcecomponent,
        string $sourcetitle,
        string $statement,
        array $metadata = []
    ): self {
        return new self([
            'archiveid' => $archiveid,
            'contextid' => $contextid,
            'sourcecomponent' => $sourcecomponent,
            'sourcetitle' => $sourcetitle,
            'statement' => $statement,
            'provenance' => self::PROVENANCE_IMPORTED,
            'validationstate' => self::VALIDATION_UNVERIFIED,
            'status' => self::STATUS_PENDING_REVIEW,
            'visibility' => self::VISIBILITY_COURSE,
            'metadata' => $metadata,
        ]);
    }

    /**
     * Apply raw data.
     *
     * @param array<string, mixed> $data Raw data.
     */
    private function apply_data(array $data): void {
        $this->id = max(0, (int)($data['id'] ?? $this->id));
        $this->archiveid = max(0, (int)($data['archiveid'] ?? $data['uckkarchiveid'] ?? $this->archiveid));
        $this->itemid = max(0, (int)($data['itemid'] ?? $data['archiveitemid'] ?? $this->itemid));
        $this->proofid = max(0, (int)($data['proofid'] ?? $this->proofid));
        $this->kristalid = max(0, (int)($data['kristalid'] ?? $this->kristalid));
        $this->revisionid = max(0, (int)($data['revisionid'] ?? $data['revid'] ?? $this->revisionid));
        $this->courseid = max(0, (int)($data['courseid'] ?? $this->courseid));
        $this->cmid = max(0, (int)($data['cmid'] ?? $this->cmid));
        $this->contextid = max(0, (int)($data['contextid'] ?? $this->contextid));
        $this->userid = max(0, (int)($data['userid'] ?? $this->userid));

        $this->component = self::normalise_component((string)($data['component'] ?? $this->component));
        $this->subjecttype = self::normalise_subject_type((string)($data['subjecttype'] ?? $data['itemtype'] ?? $this->subjecttype));
        $this->subjectid = max(0, (int)($data['subjectid'] ?? $data['subjectitemid'] ?? $this->subjectid));

        if ($this->subjectid <= 0 && $this->subjecttype === self::SUBJECT_ARCHIVE_ITEM) {
            $this->subjectid = $this->itemid;
        }

        $this->sourcecomponent = self::normalise_component((string)($data['sourcecomponent'] ?? $this->sourcecomponent), true);
        $this->sourcetype = self::normalise_identifier((string)($data['sourcetype'] ?? $data['sourcetypeid'] ?? $this->sourcetype));
        $this->sourceid = max(0, (int)($data['sourceid'] ?? $data['sourceitemid'] ?? $this->sourceid));
        $this->sourcecontextid = max(0, (int)($data['sourcecontextid'] ?? $this->sourcecontextid));

        $this->sourceurl = clean_param((string)($data['sourceurl'] ?? $data['url'] ?? $this->sourceurl), PARAM_URL);
        $this->sourcetitle = self::normalise_text((string)($data['sourcetitle'] ?? $data['title'] ?? $this->sourcetitle));
        $this->sourceauthor = self::normalise_text((string)($data['sourceauthor'] ?? $data['author'] ?? $this->sourceauthor));
        $this->sourcedate = max(0, (int)($data['sourcedate'] ?? $data['sourcetime'] ?? $this->sourcedate));

        $this->statement = trim((string)($data['statement'] ?? $data['provenancestatement'] ?? $data['description'] ?? $this->statement));
        $this->provenance = self::normalise_provenance((string)($data['provenance'] ?? $this->provenance));
        $this->validationstate = self::normalise_validation_state((string)($data['validationstate'] ?? $this->validationstate));
        $this->status = self::normalise_status((string)($data['status'] ?? $this->status));
        $this->visibility = self::normalise_visibility((string)($data['visibility'] ?? $this->visibility));

        $this->provenancehash = clean_param((string)($data['provenancehash'] ?? $this->provenancehash), PARAM_ALPHANUMEXT);
        $this->hash = clean_param((string)($data['hash'] ?? $this->hash), PARAM_ALPHANUMEXT);

        if ($this->provenancehash === '' && $this->hash !== '') {
            $this->provenancehash = $this->hash;
        }

        if ($this->hash === '' && $this->provenancehash !== '') {
            $this->hash = $this->provenancehash;
        }

        $this->versionno = max(1, (int)($data['versionno'] ?? $this->versionno));
        $this->createdby = max(0, (int)($data['createdby'] ?? $this->createdby));
        $this->modifiedby = max(0, (int)($data['modifiedby'] ?? $this->modifiedby));
        $this->timecreated = max(0, (int)($data['timecreated'] ?? $this->timecreated));
        $this->timemodified = max(0, (int)($data['timemodified'] ?? $this->timemodified));

        if (array_key_exists('metadata', $data)) {
            $this->metadata = self::normalise_metadata($data['metadata']);
        }
    }

    /**
     * Validate this object.
     *
     * @throws \coding_exception If required provenance fields are missing.
     */
    public function validate(): void {
        if ($this->archiveid <= 0) {
            throw new \coding_exception('Archive provenance requires a valid archiveid.');
        }

        if ($this->contextid <= 0) {
            throw new \coding_exception('Archive provenance requires a valid contextid.');
        }

        if ($this->component === '') {
            throw new \coding_exception('Archive provenance requires a component.');
        }

        if ($this->subjecttype === '') {
            throw new \coding_exception('Archive provenance requires a subjecttype.');
        }

        if ($this->statement === '') {
            throw new \coding_exception('Archive provenance requires a statement.');
        }

        if (!in_array($this->provenance, self::get_allowed_provenance_sources(), true)) {
            throw new \coding_exception('Invalid archive provenance source: ' . $this->provenance);
        }

        if (!in_array($this->validationstate, self::get_allowed_validation_states(), true)) {
            throw new \coding_exception('Invalid archive provenance validation state: ' . $this->validationstate);
        }

        if (!in_array($this->status, self::get_allowed_statuses(), true)) {
            throw new \coding_exception('Invalid archive provenance status: ' . $this->status);
        }

        if (!in_array($this->visibility, self::get_allowed_visibilities(), true)) {
            throw new \coding_exception('Invalid archive provenance visibility: ' . $this->visibility);
        }
    }

    /**
     * Convert to a DB record for {uckkarchive_prov}.
     *
     * Service/database layers may filter this object to actual schema columns
     * before inserting, if the initial install.xml uses a reduced field set.
     *
     * @param int|null $userid Acting user id.
     * @param int|null $now Current timestamp.
     * @return stdClass
     */
    public function to_record(?int $userid = null, ?int $now = null): stdClass {
        $this->validate();

        $now ??= time();
        $userid ??= 0;

        if ($this->provenancehash === '') {
            $this->provenancehash = $this->calculate_hash();
            $this->hash = $this->provenancehash;
        }

        $record = new stdClass();

        if ($this->id > 0) {
            $record->id = $this->id;
        }

        $record->archiveid = $this->archiveid;
        $record->uckkarchiveid = $this->archiveid;
        $record->itemid = $this->itemid;
        $record->archiveitemid = $this->itemid;
        $record->proofid = $this->proofid;
        $record->kristalid = $this->kristalid;
        $record->revisionid = $this->revisionid;

        $record->courseid = $this->courseid;
        $record->cmid = $this->cmid;
        $record->contextid = $this->contextid;
        $record->userid = $this->userid;

        $record->component = $this->component;
        $record->subjecttype = $this->subjecttype;
        $record->itemtype = $this->subjecttype;
        $record->subjectid = $this->subjectid;
        $record->sourcecomponent = $this->sourcecomponent;
        $record->sourcetype = $this->sourcetype;
        $record->sourceid = $this->sourceid;
        $record->sourcecontextid = $this->sourcecontextid;
        $record->sourceurl = $this->sourceurl !== '' ? $this->sourceurl : null;
        $record->sourcetitle = $this->sourcetitle !== '' ? $this->sourcetitle : null;
        $record->sourceauthor = $this->sourceauthor !== '' ? $this->sourceauthor : null;
        $record->sourcedate = $this->sourcedate;

        $record->statement = $this->statement;
        $record->provenancestatement = $this->statement;
        $record->provenance = $this->provenance;
        $record->validationstate = $this->validationstate;
        $record->status = $this->status;
        $record->visibility = $this->visibility;

        $record->provenancehash = $this->provenancehash;
        $record->hash = $this->hash !== '' ? $this->hash : $this->provenancehash;
        $record->versionno = $this->versionno;

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
        $data->kristalid = $this->kristalid;
        $data->revisionid = $this->revisionid;
        $data->courseid = $this->courseid;
        $data->cmid = $this->cmid;
        $data->contextid = $this->contextid;
        $data->userid = $this->userid;
        $data->component = $this->component;
        $data->subjecttype = $this->subjecttype;
        $data->subjectid = $this->subjectid;
        $data->sourcecomponent = $this->sourcecomponent;
        $data->sourcetype = $this->sourcetype;
        $data->sourceid = $this->sourceid;
        $data->sourcecontextid = $this->sourcecontextid;
        $data->sourceurl = $this->sourceurl;
        $data->sourcetitle = $this->sourcetitle;
        $data->sourceauthor = $this->sourceauthor;
        $data->sourcedate = $this->sourcedate;
        $data->statement = $this->statement;
        $data->provenance = $this->provenance;
        $data->validationstate = $this->validationstate;
        $data->status = $this->status;
        $data->visibility = $this->visibility;
        $data->provenancehash = $this->provenancehash !== '' ? $this->provenancehash : $this->calculate_hash();
        $data->versionno = $this->versionno;
        $data->metadata = $this->metadata;

        return $data;
    }

    /**
     * Calculate a stable hash of the provenance claim.
     *
     * @return string
     */
    public function calculate_hash(): string {
        $payload = [
            'archiveid' => $this->archiveid,
            'itemid' => $this->itemid,
            'proofid' => $this->proofid,
            'kristalid' => $this->kristalid,
            'revisionid' => $this->revisionid,
            'component' => $this->component,
            'subjecttype' => $this->subjecttype,
            'subjectid' => $this->subjectid,
            'sourcecomponent' => $this->sourcecomponent,
            'sourcetype' => $this->sourcetype,
            'sourceid' => $this->sourceid,
            'sourcecontextid' => $this->sourcecontextid,
            'sourceurl' => $this->sourceurl,
            'sourcetitle' => $this->sourcetitle,
            'sourceauthor' => $this->sourceauthor,
            'sourcedate' => $this->sourcedate,
            'statement' => $this->statement,
            'provenance' => $this->provenance,
            'metadata' => $this->metadata,
        ];

        return hash('sha256', json_encode($payload, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES));
    }

    /**
     * Whether the provenance was AI-assisted.
     *
     * @return bool
     */
    public function is_ai_assisted(): bool {
        return $this->provenance === self::PROVENANCE_AI_ASSISTED;
    }

    /**
     * Whether the provenance has been human reviewed or verified.
     *
     * @return bool
     */
    public function is_human_validated(): bool {
        return in_array($this->validationstate, [
            self::VALIDATION_HUMAN_REVIEWED,
            self::VALIDATION_VERIFIED,
            self::VALIDATION_ARCHIVED,
        ], true);
    }

    /**
     * Whether the provenance is contested.
     *
     * @return bool
     */
    public function is_contested(): bool {
        return $this->validationstate === self::VALIDATION_CONTESTED
            || $this->status === self::STATUS_CONTESTED;
    }

    /**
     * Whether the provenance is invalidated.
     *
     * @return bool
     */
    public function is_invalidated(): bool {
        return $this->validationstate === self::VALIDATION_INVALIDATED
            || $this->status === self::STATUS_INVALIDATED;
    }

    /**
     * Whether the provenance is restricted.
     *
     * @return bool
     */
    public function is_restricted(): bool {
        return in_array($this->visibility, [
            self::VISIBILITY_RESTRICTED,
            self::VISIBILITY_RESTRICTED_INTEGRITY,
            self::VISIBILITY_HIDDEN,
        ], true);
    }

    /**
     * Whether this provenance has a source reference.
     *
     * @return bool
     */
    public function has_source(): bool {
        return $this->sourcecomponent !== ''
            || $this->sourcetype !== ''
            || $this->sourceid > 0
            || $this->sourceurl !== ''
            || $this->sourcetitle !== '';
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
     * Get subject type.
     *
     * @return string
     */
    public function get_subjecttype(): string {
        return $this->subjecttype;
    }

    /**
     * Get subject id.
     *
     * @return int
     */
    public function get_subjectid(): int {
        return $this->subjectid;
    }

    /**
     * Get source component.
     *
     * @return string
     */
    public function get_sourcecomponent(): string {
        return $this->sourcecomponent;
    }

    /**
     * Get source type.
     *
     * @return string
     */
    public function get_sourcetype(): string {
        return $this->sourcetype;
    }

    /**
     * Get source id.
     *
     * @return int
     */
    public function get_sourceid(): int {
        return $this->sourceid;
    }

    /**
     * Get statement.
     *
     * @return string
     */
    public function get_statement(): string {
        return $this->statement;
    }

    /**
     * Get provenance source.
     *
     * @return string
     */
    public function get_provenance(): string {
        return $this->provenance;
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
     * Get provenance hash.
     *
     * @return string
     */
    public function get_provenancehash(): string {
        return $this->provenancehash !== '' ? $this->provenancehash : $this->calculate_hash();
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
     * Get a metadata value.
     *
     * @param string $key Metadata key.
     * @param mixed $default Default.
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
     * Return copy linked to an archive item.
     *
     * @param int $itemid Archive item id.
     * @return self
     */
    public function with_itemid(int $itemid): self {
        $clone = clone $this;
        $clone->itemid = max(0, $itemid);

        if ($clone->subjecttype === self::SUBJECT_ARCHIVE_ITEM) {
            $clone->subjectid = $clone->itemid;
        }

        return $clone;
    }

    /**
     * Return copy with source reference.
     *
     * @param string $component Source component.
     * @param string $type Source type.
     * @param int $id Source id.
     * @param int $contextid Source context id.
     * @return self
     */
    public function with_source(string $component, string $type, int $id = 0, int $contextid = 0): self {
        $clone = clone $this;
        $clone->sourcecomponent = self::normalise_component($component, true);
        $clone->sourcetype = self::normalise_identifier($type);
        $clone->sourceid = max(0, $id);
        $clone->sourcecontextid = max(0, $contextid);
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
        $clone->provenancehash = '';
        $clone->hash = '';
        return $clone;
    }

    /**
     * Return allowed subject types.
     *
     * @return string[]
     */
    public static function get_allowed_subject_types(): array {
        return [
            self::SUBJECT_ARCHIVE_ITEM,
            self::SUBJECT_PROOF,
            self::SUBJECT_KRISTAL,
            self::SUBJECT_REVISION,
            self::SUBJECT_EXPORT,
        ];
    }

    /**
     * Return allowed provenance sources.
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
     * Return allowed validation states.
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
     * Return allowed statuses.
     *
     * @return string[]
     */
    public static function get_allowed_statuses(): array {
        return [
            self::STATUS_DRAFT,
            self::STATUS_ACTIVE,
            self::STATUS_PENDING_REVIEW,
            self::STATUS_VALIDATED,
            self::STATUS_CONTESTED,
            self::STATUS_INVALIDATED,
            self::STATUS_ARCHIVED,
        ];
    }

    /**
     * Return allowed visibilities.
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
     * Normalise component names.
     *
     * @param string $component Raw component.
     * @param bool $allowempty Whether empty is allowed.
     * @return string
     */
    private static function normalise_component(string $component, bool $allowempty = false): string {
        $component = clean_param($component, PARAM_COMPONENT);

        if ($component === '' && !$allowempty) {
            return self::COMPONENT;
        }

        return $component;
    }

    /**
     * Normalise subject type.
     *
     * @param string $subjecttype Raw subject type.
     * @return string
     */
    private static function normalise_subject_type(string $subjecttype): string {
        $subjecttype = self::normalise_identifier($subjecttype);

        return in_array($subjecttype, self::get_allowed_subject_types(), true)
            ? $subjecttype
            : self::SUBJECT_ARCHIVE_ITEM;
    }

    /**
     * Normalise provenance source.
     *
     * @param string $provenance Raw provenance.
     * @return string
     */
    private static function normalise_provenance(string $provenance): string {
        $provenance = self::normalise_identifier($provenance);

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
        $validationstate = self::normalise_identifier($validationstate);

        return in_array($validationstate, self::get_allowed_validation_states(), true)
            ? $validationstate
            : self::VALIDATION_UNVERIFIED;
    }

    /**
     * Normalise status.
     *
     * @param string $status Raw status.
     * @return string
     */
    private static function normalise_status(string $status): string {
        $status = self::normalise_identifier($status);

        return in_array($status, self::get_allowed_statuses(), true)
            ? $status
            : self::STATUS_ACTIVE;
    }

    /**
     * Normalise visibility.
     *
     * @param string $visibility Raw visibility.
     * @return string
     */
    private static function normalise_visibility(string $visibility): string {
        $visibility = self::normalise_identifier($visibility);

        return in_array($visibility, self::get_allowed_visibilities(), true)
            ? $visibility
            : self::VISIBILITY_COURSE;
    }

    /**
     * Normalise identifier values.
     *
     * @param string $identifier Raw identifier.
     * @return string
     */
    private static function normalise_identifier(string $identifier): string {
        return clean_param(trim($identifier), PARAM_ALPHANUMEXT);
    }

    /**
     * Normalise display text.
     *
     * @param string $text Raw text.
     * @return string
     */
    private static function normalise_text(string $text): string {
        return trim(clean_param($text, PARAM_TEXT));
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

