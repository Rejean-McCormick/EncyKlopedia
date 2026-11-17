<?php
// This file is part of Moodle - https://moodle.org/
//
// Moodle is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// any later version.

/**
 * Local domain model for a UCKK archive revision.
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
 * Domain object representing one archive item revision.
 *
 * This class normalises and validates revision data before service/database
 * layers insert, update, render, export, or archive it.
 *
 * It does not decide permissions, validate evidence, alter archive items,
 * publish public records, or delete history.
 */
final class revision {
    /** Revision type: item created. */
    public const TYPE_CREATED = 'created';

    /** Revision type: item updated. */
    public const TYPE_UPDATED = 'updated';

    /** Revision type: item revised. */
    public const TYPE_REVISED = 'revised';

    /** Revision type: item validated. */
    public const TYPE_VALIDATED = 'validated';

    /** Revision type: correction issued. */
    public const TYPE_CORRECTION = 'correction';

    /** Revision type: status changed. */
    public const TYPE_STATUS_CHANGED = 'status_changed';

    /** Revision type: visibility changed. */
    public const TYPE_VISIBILITY_CHANGED = 'visibility_changed';

    /** Revision type: validation state changed. */
    public const TYPE_VALIDATION_CHANGED = 'validation_changed';

    /** Revision type: item invalidated. */
    public const TYPE_INVALIDATED = 'invalidated';

    /** Revision type: item archived. */
    public const TYPE_ARCHIVED = 'archived';

    /** Revision type: item exported. */
    public const TYPE_EXPORTED = 'exported';

    /** Revision type: item restored. */
    public const TYPE_RESTORED = 'restored';

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

    /** Compatibility visibility used by earlier archive code. */
    public const VISIBILITY_INSTITUTIONAL = 'institutional';

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

    /** Archive item id. */
    private int $itemid = 0;

    /** Moodle course id. */
    private int $courseid = 0;

    /** Moodle course module id. */
    private int $cmid = 0;

    /** Moodle context id. */
    private int $contextid = 0;

    /** User affected by or responsible for the revision. */
    private int $userid = 0;

    /** Revision type. */
    private string $revisiontype = self::TYPE_UPDATED;

    /** Previous item status. */
    private ?string $previousstatus = null;

    /** New item status. */
    private ?string $newstatus = null;

    /** Previous item visibility. */
    private ?string $previousvisibility = null;

    /** New item visibility. */
    private ?string $newvisibility = null;

    /** Previous validation state. */
    private ?string $previousvalidationstate = null;

    /** New validation state. */
    private ?string $newvalidationstate = null;

    /** Human-readable reason for the revision. */
    private string $reason = '';

    /** Revision record status. */
    private string $status = self::STATUS_ACTIVE;

    /** Revision record visibility. */
    private string $visibility = self::VISIBILITY_COURSE;

    /** Revision provenance. */
    private string $provenance = self::PROVENANCE_HUMAN;

    /** Optional provenance hash. */
    private string $provenancehash = '';

    /** Version number after this revision. */
    private int $versionno = 1;

    /** User who created the revision record. */
    private int $createdby = 0;

    /** User who last modified the revision record. */
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
     * @param array<string, mixed>|stdClass|null $data Initial revision data.
     */
    public function __construct(array|stdClass|null $data = null) {
        if ($data !== null) {
            $this->apply_data((array)$data);
        }
    }

    /**
     * Build a revision object from a Moodle database record.
     *
     * @param stdClass $record Record from {uckkarchive_rev}.
     * @return self
     */
    public static function from_record(stdClass $record): self {
        return new self($record);
    }

    /**
     * Build an item-created revision.
     *
     * @param int $archiveid Archive instance id.
     * @param int $itemid Archive item id.
     * @param int $userid Acting user id.
     * @param string $newstatus New item status.
     * @param string $newvisibility New item visibility.
     * @param string $reason Reason text.
     * @return self
     */
    public static function item_created(
        int $archiveid,
        int $itemid,
        int $userid,
        string $newstatus = self::STATUS_DRAFT,
        string $newvisibility = self::VISIBILITY_COURSE,
        string $reason = ''
    ): self {
        return new self([
            'archiveid' => $archiveid,
            'itemid' => $itemid,
            'userid' => $userid,
            'revisiontype' => self::TYPE_CREATED,
            'previousstatus' => null,
            'newstatus' => $newstatus,
            'previousvisibility' => null,
            'newvisibility' => $newvisibility,
            'reason' => $reason,
            'status' => self::STATUS_ACTIVE,
            'visibility' => $newvisibility,
            'provenance' => self::PROVENANCE_HUMAN,
            'versionno' => 1,
        ]);
    }

    /**
     * Build a status-change revision.
     *
     * @param int $archiveid Archive instance id.
     * @param int $itemid Archive item id.
     * @param int $userid Acting user id.
     * @param string|null $previousstatus Previous status.
     * @param string $newstatus New status.
     * @param string $visibility Revision visibility.
     * @param string $reason Reason text.
     * @return self
     */
    public static function status_changed(
        int $archiveid,
        int $itemid,
        int $userid,
        ?string $previousstatus,
        string $newstatus,
        string $visibility = self::VISIBILITY_COURSE,
        string $reason = ''
    ): self {
        return new self([
            'archiveid' => $archiveid,
            'itemid' => $itemid,
            'userid' => $userid,
            'revisiontype' => self::TYPE_STATUS_CHANGED,
            'previousstatus' => $previousstatus,
            'newstatus' => $newstatus,
            'reason' => $reason,
            'status' => self::STATUS_ACTIVE,
            'visibility' => $visibility,
            'provenance' => self::PROVENANCE_ARCHIVE,
        ]);
    }

    /**
     * Build a visibility-change revision.
     *
     * @param int $archiveid Archive instance id.
     * @param int $itemid Archive item id.
     * @param int $userid Acting user id.
     * @param string|null $previousvisibility Previous visibility.
     * @param string $newvisibility New visibility.
     * @param string $reason Reason text.
     * @return self
     */
    public static function visibility_changed(
        int $archiveid,
        int $itemid,
        int $userid,
        ?string $previousvisibility,
        string $newvisibility,
        string $reason = ''
    ): self {
        return new self([
            'archiveid' => $archiveid,
            'itemid' => $itemid,
            'userid' => $userid,
            'revisiontype' => self::TYPE_VISIBILITY_CHANGED,
            'previousvisibility' => $previousvisibility,
            'newvisibility' => $newvisibility,
            'reason' => $reason,
            'status' => self::STATUS_ACTIVE,
            'visibility' => $newvisibility,
            'provenance' => self::PROVENANCE_ARCHIVE,
        ]);
    }

    /**
     * Apply raw data to this object.
     *
     * @param array<string, mixed> $data Input data.
     */
    private function apply_data(array $data): void {
        $this->id = max(0, (int)($data['id'] ?? $this->id));
        $this->archiveid = max(0, (int)($data['archiveid'] ?? $data['uckkarchiveid'] ?? $this->archiveid));
        $this->itemid = max(0, (int)($data['itemid'] ?? $data['archiveitemid'] ?? $this->itemid));
        $this->courseid = max(0, (int)($data['courseid'] ?? $this->courseid));
        $this->cmid = max(0, (int)($data['cmid'] ?? $this->cmid));
        $this->contextid = max(0, (int)($data['contextid'] ?? $this->contextid));
        $this->userid = max(0, (int)($data['userid'] ?? $this->userid));

        $this->revisiontype = self::normalise_revision_type(
            (string)($data['revisiontype'] ?? $data['type'] ?? $this->revisiontype)
        );

        $this->previousstatus = self::normalise_optional_status($data['previousstatus'] ?? $this->previousstatus);
        $this->newstatus = self::normalise_optional_status($data['newstatus'] ?? $this->newstatus);

        $this->previousvisibility = self::normalise_optional_visibility(
            $data['previousvisibility'] ?? $this->previousvisibility
        );
        $this->newvisibility = self::normalise_optional_visibility($data['newvisibility'] ?? $this->newvisibility);

        $this->previousvalidationstate = self::normalise_optional_validation_state(
            $data['previousvalidationstate'] ?? $data['previousvalidation'] ?? $this->previousvalidationstate
        );
        $this->newvalidationstate = self::normalise_optional_validation_state(
            $data['newvalidationstate'] ?? $data['newvalidation'] ?? $this->newvalidationstate
        );

        $this->reason = trim(clean_param((string)($data['reason'] ?? $this->reason), PARAM_TEXT));
        $this->status = self::normalise_status((string)($data['status'] ?? $this->status));
        $this->visibility = self::normalise_visibility((string)($data['visibility'] ?? $this->visibility));
        $this->provenance = self::normalise_provenance((string)($data['provenance'] ?? $this->provenance));
        $this->provenancehash = clean_param((string)($data['provenancehash'] ?? $this->provenancehash), PARAM_ALPHANUMEXT);

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
     * Validate this revision.
     *
     * @throws \coding_exception If the revision is invalid.
     */
    public function validate(): void {
        if ($this->archiveid <= 0) {
            throw new \coding_exception('Archive revision requires a valid archiveid.');
        }

        if ($this->itemid <= 0) {
            throw new \coding_exception('Archive revision requires a valid itemid.');
        }

        if ($this->userid <= 0) {
            throw new \coding_exception('Archive revision requires a valid userid.');
        }

        if (!in_array($this->revisiontype, self::get_allowed_revision_types(), true)) {
            throw new \coding_exception('Invalid archive revision type: ' . $this->revisiontype);
        }

        if (!in_array($this->status, self::get_allowed_statuses(), true)) {
            throw new \coding_exception('Invalid archive revision status: ' . $this->status);
        }

        if (!in_array($this->visibility, self::get_allowed_visibilities(), true)) {
            throw new \coding_exception('Invalid archive revision visibility: ' . $this->visibility);
        }

        if (!in_array($this->provenance, self::get_allowed_provenance_sources(), true)) {
            throw new \coding_exception('Invalid archive revision provenance: ' . $this->provenance);
        }

        if ($this->is_state_change() && $this->previousstatus === $this->newstatus) {
            throw new \coding_exception('Archive status revision must change status.');
        }

        if ($this->is_visibility_change() && $this->previousvisibility === $this->newvisibility) {
            throw new \coding_exception('Archive visibility revision must change visibility.');
        }

        if ($this->is_validation_change() && $this->previousvalidationstate === $this->newvalidationstate) {
            throw new \coding_exception('Archive validation revision must change validation state.');
        }
    }

    /**
     * Convert to a database record for {uckkarchive_rev}.
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
        $record->itemid = $this->itemid;
        $record->courseid = $this->courseid;
        $record->cmid = $this->cmid;
        $record->contextid = $this->contextid;
        $record->userid = $this->userid;
        $record->revisiontype = $this->revisiontype;
        $record->previousstatus = $this->previousstatus;
        $record->newstatus = $this->newstatus;
        $record->previousvisibility = $this->previousvisibility;
        $record->newvisibility = $this->newvisibility;
        $record->previousvalidationstate = $this->previousvalidationstate;
        $record->newvalidationstate = $this->newvalidationstate;
        $record->reason = $this->reason;
        $record->status = $this->status;
        $record->visibility = $this->visibility;
        $record->provenance = $this->provenance;
        $record->provenancehash = $this->provenancehash !== '' ? $this->provenancehash : null;
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
        $data->courseid = $this->courseid;
        $data->cmid = $this->cmid;
        $data->contextid = $this->contextid;
        $data->userid = $this->userid;
        $data->revisiontype = $this->revisiontype;
        $data->previousstatus = $this->previousstatus;
        $data->newstatus = $this->newstatus;
        $data->previousvisibility = $this->previousvisibility;
        $data->newvisibility = $this->newvisibility;
        $data->previousvalidationstate = $this->previousvalidationstate;
        $data->newvalidationstate = $this->newvalidationstate;
        $data->reason = $this->reason;
        $data->status = $this->status;
        $data->visibility = $this->visibility;
        $data->provenance = $this->provenance;
        $data->provenancehash = $this->provenancehash;
        $data->versionno = $this->versionno;
        $data->createdby = $this->createdby;
        $data->modifiedby = $this->modifiedby;
        $data->timecreated = $this->timecreated;
        $data->timemodified = $this->timemodified;
        $data->metadata = $this->metadata;
        return $data;
    }

    /**
     * Whether this revision records a status change.
     *
     * @return bool
     */
    public function is_state_change(): bool {
        return $this->revisiontype === self::TYPE_STATUS_CHANGED
            || $this->previousstatus !== null
            || $this->newstatus !== null;
    }

    /**
     * Whether this revision records a visibility change.
     *
     * @return bool
     */
    public function is_visibility_change(): bool {
        return $this->revisiontype === self::TYPE_VISIBILITY_CHANGED
            || $this->previousvisibility !== null
            || $this->newvisibility !== null;
    }

    /**
     * Whether this revision records a validation change.
     *
     * @return bool
     */
    public function is_validation_change(): bool {
        return $this->revisiontype === self::TYPE_VALIDATION_CHANGED
            || $this->previousvalidationstate !== null
            || $this->newvalidationstate !== null;
    }

    /**
     * Whether this revision is integrity-restricted.
     *
     * @return bool
     */
    public function is_integrity_restricted(): bool {
        return $this->visibility === self::VISIBILITY_RESTRICTED_INTEGRITY;
    }

    /**
     * Whether this revision is visible at course level.
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
            self::VISIBILITY_INSTITUTIONAL,
            self::VISIBILITY_PUBLIC,
        ], true);
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
        return $clone;
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
     * Get item id.
     *
     * @return int
     */
    public function get_itemid(): int {
        return $this->itemid;
    }

    /**
     * Get revision type.
     *
     * @return string
     */
    public function get_revisiontype(): string {
        return $this->revisiontype;
    }

    /**
     * Get reason.
     *
     * @return string
     */
    public function get_reason(): string {
        return $this->reason;
    }

    /**
     * Get version number.
     *
     * @return int
     */
    public function get_versionno(): int {
        return $this->versionno;
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
     * Allowed revision types.
     *
     * @return string[]
     */
    public static function get_allowed_revision_types(): array {
        return [
            self::TYPE_CREATED,
            self::TYPE_UPDATED,
            self::TYPE_REVISED,
            self::TYPE_VALIDATED,
            self::TYPE_CORRECTION,
            self::TYPE_STATUS_CHANGED,
            self::TYPE_VISIBILITY_CHANGED,
            self::TYPE_VALIDATION_CHANGED,
            self::TYPE_INVALIDATED,
            self::TYPE_ARCHIVED,
            self::TYPE_EXPORTED,
            self::TYPE_RESTORED,
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
            self::VISIBILITY_INSTITUTIONAL,
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
            'unverified',
            'human_reviewed',
            'verified',
            'contested',
            'invalidated',
            'archived',
        ];
    }

    /**
     * Normalise revision type.
     *
     * @param string $type Raw type.
     * @return string
     */
    private static function normalise_revision_type(string $type): string {
        $type = clean_param($type, PARAM_ALPHANUMEXT);

        return in_array($type, self::get_allowed_revision_types(), true)
            ? $type
            : self::TYPE_UPDATED;
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
            : self::STATUS_ACTIVE;
    }

    /**
     * Normalise optional status.
     *
     * @param mixed $status Raw status.
     * @return string|null
     */
    private static function normalise_optional_status(mixed $status): ?string {
        if ($status === null || $status === '') {
            return null;
        }

        $status = clean_param((string)$status, PARAM_ALPHANUMEXT);

        return in_array($status, self::get_allowed_statuses(), true) ? $status : null;
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
     * Normalise optional visibility.
     *
     * @param mixed $visibility Raw visibility.
     * @return string|null
     */
    private static function normalise_optional_visibility(mixed $visibility): ?string {
        if ($visibility === null || $visibility === '') {
            return null;
        }

        $visibility = clean_param((string)$visibility, PARAM_ALPHANUMEXT);

        return in_array($visibility, self::get_allowed_visibilities(), true) ? $visibility : null;
    }

    /**
     * Normalise optional validation state.
     *
     * @param mixed $state Raw state.
     * @return string|null
     */
    private static function normalise_optional_validation_state(mixed $state): ?string {
        if ($state === null || $state === '') {
            return null;
        }

        $state = clean_param((string)$state, PARAM_ALPHANUMEXT);

        return in_array($state, self::get_allowed_validation_states(), true) ? $state : null;
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

