<?php
// This file is part of Moodle - https://moodle.org/
//
// Moodle is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// any later version.

/**
 * Archive policy helper for UCKK Archives.
 *
 * @package    mod_uckkarchive
 * @copyright  2026 Univers-Cité King Klown
 * @license    https://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later
 */

declare(strict_types=1);

namespace mod_uckkarchive\local;

use context;
use stdClass;

defined('MOODLE_INTERNAL') || die();

/**
 * Central archive policy object.
 *
 * This class does not write to the database. It centralises policy decisions
 * used by controllers, forms, services, renderables, scheduled tasks, and
 * tests:
 *
 * - status transitions;
 * - visibility restrictions;
 * - provenance requirements;
 * - validation requirements;
 * - revision permissions;
 * - export eligibility;
 * - retention classification.
 */
final class archive_policy {
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

    /** Archive item type: archive item. */
    public const TYPE_ARCHIVE_ITEM = 'archive_item';

    /** Archive item type: Kristal. */
    public const TYPE_KRISTAL = 'kristal';

    /** Archive item type: proof. */
    public const TYPE_PROOF = 'proof';

    /** Archive item type: decision. */
    public const TYPE_DECISION = 'decision';

    /** Archive item type: reflection. */
    public const TYPE_REFLECTION = 'reflection';

    /** Archive item type: portfolio item. */
    public const TYPE_PORTFOLIO_ITEM = 'portfolio_item';

    /** Archive item type: badge evidence. */
    public const TYPE_BADGE = 'badge';

    /** Archive item type: competency evidence. */
    public const TYPE_COMPETENCY = 'competency';

    /** Archive policy: no automatic archive. */
    public const POLICY_NONE = 'none';

    /** Archive policy: summary only. */
    public const POLICY_SUMMARY = 'summary';

    /** Archive policy: full archive. */
    public const POLICY_FULL = 'full';

    /** Archive policy: restricted integrity archive. */
    public const POLICY_RESTRICTED_INTEGRITY = 'restricted_integrity';

    /** Export type: item summary. */
    public const EXPORT_ITEM_SUMMARY = 'item_summary';

    /** Export type: evidence package. */
    public const EXPORT_EVIDENCE_PACKAGE = 'evidence_package';

    /** Export type: public package. */
    public const EXPORT_PUBLIC_PACKAGE = 'public_package';

    /** Export type: restricted package. */
    public const EXPORT_RESTRICTED_PACKAGE = 'restricted_package';

    /** Retention class: normal. */
    public const RETENTION_NORMAL = 'normal';

    /** Retention class: permanent memory. */
    public const RETENTION_PERMANENT = 'permanent';

    /** Retention class: restricted review. */
    public const RETENTION_RESTRICTED_REVIEW = 'restricted_review';

    /** Retention class: legal hold. */
    public const RETENTION_LEGAL_HOLD = 'legal_hold';

    /**
     * Whether archive exports require validation.
     *
     * @var bool
     */
    private bool $exportrequiresvalidation;

    /**
     * Whether public visibility requires verified validation.
     *
     * @var bool
     */
    private bool $publicrequiresverified;

    /**
     * Whether AI-assisted records require explicit provenance.
     *
     * @var bool
     */
    private bool $aiprovenancerequired;

    /**
     * Constructor.
     *
     * @param array<string, mixed> $config Optional policy configuration.
     */
    public function __construct(array $config = []) {
        $this->exportrequiresvalidation = (bool)($config['exportrequiresvalidation'] ?? true);
        $this->publicrequiresverified = (bool)($config['publicrequiresverified'] ?? true);
        $this->aiprovenancerequired = (bool)($config['aiprovenancerequired'] ?? true);
    }

    /**
     * Create policy from plugin configuration.
     *
     * @return self
     */
    public static function from_config(): self {
        return new self([
            'exportrequiresvalidation' => (bool)get_config('uckkarchive', 'exportrequiresvalidation'),
            'publicrequiresverified' => (bool)get_config('uckkarchive', 'publicrequiresverified'),
            'aiprovenancerequired' => true,
        ]);
    }

    /**
     * Whether the current user can view the item.
     *
     * @param array<string, mixed>|stdClass $item Archive item.
     * @param context $context Moodle context.
     * @param stdClass|null $user User record.
     * @return bool
     */
    public function can_view_item(array|stdClass $item, context $context, ?stdClass $user = null): bool {
        global $USER;

        $user ??= $USER;

        if (!has_capability('mod/uckkarchive:view', $context, $user)) {
            return false;
        }

        $item = (object)$item;
        $visibility = self::normalise_visibility((string)($item->visibility ?? self::VISIBILITY_COURSE));

        if ($this->is_restricted_visibility($visibility)) {
            return has_capability('mod/uckkarchive:viewrestricted', $context, $user);
        }

        if ($visibility === self::VISIBILITY_PRIVATE || $visibility === self::VISIBILITY_USER) {
            return $this->is_item_owner($item, $user)
                || has_capability('mod/uckkarchive:viewrestricted', $context, $user);
        }

        if ($visibility === self::VISIBILITY_HIDDEN) {
            return has_capability('mod/uckkarchive:viewrestricted', $context, $user);
        }

        return true;
    }

    /**
     * Whether the current user can revise the item.
     *
     * @param array<string, mixed>|stdClass $item Archive item.
     * @param context $context Moodle context.
     * @param stdClass|null $user User record.
     * @return bool
     */
    public function can_revise_item(array|stdClass $item, context $context, ?stdClass $user = null): bool {
        global $USER;

        $user ??= $USER;

        if (!has_capability('mod/uckkarchive:reviseitem', $context, $user)) {
            return false;
        }

        $item = (object)$item;
        $status = self::normalise_status((string)($item->status ?? self::STATUS_DRAFT));

        return in_array($status, [
            self::STATUS_DRAFT,
            self::STATUS_ACTIVE,
            self::STATUS_PENDING,
            self::STATUS_PENDING_REVIEW,
            self::STATUS_VALIDATED,
            self::STATUS_CORRECTION_REQUIRED,
            self::STATUS_CONTESTED,
        ], true);
    }

    /**
     * Whether the current user can validate the item.
     *
     * @param array<string, mixed>|stdClass $item Archive item.
     * @param context $context Moodle context.
     * @param stdClass|null $user User record.
     * @return bool
     */
    public function can_validate_item(array|stdClass $item, context $context, ?stdClass $user = null): bool {
        global $USER;

        $user ??= $USER;

        if (!has_capability('mod/uckkarchive:validateitem', $context, $user)) {
            return false;
        }

        $item = (object)$item;
        $status = self::normalise_status((string)($item->status ?? self::STATUS_DRAFT));
        $visibility = self::normalise_visibility((string)($item->visibility ?? self::VISIBILITY_COURSE));

        if ($visibility === self::VISIBILITY_RESTRICTED_INTEGRITY
            && !has_capability('mod/uckkarchive:viewrestricted', $context, $user)) {
            return false;
        }

        return in_array($status, [
            self::STATUS_PENDING,
            self::STATUS_PENDING_REVIEW,
            self::STATUS_CORRECTION_REQUIRED,
            self::STATUS_CONTESTED,
            self::STATUS_ACTIVE,
        ], true);
    }

    /**
     * Whether the current user can export the item.
     *
     * @param array<string, mixed>|stdClass $item Archive item.
     * @param context $context Moodle context.
     * @param string $exporttype Export type.
     * @param stdClass|null $user User record.
     * @return bool
     */
    public function can_export_item(
        array|stdClass $item,
        context $context,
        string $exporttype = self::EXPORT_ITEM_SUMMARY,
        ?stdClass $user = null
    ): bool {
        global $USER;

        $user ??= $USER;

        if (!has_capability('mod/uckkarchive:export', $context, $user)) {
            return false;
        }

        $item = (object)$item;
        $visibility = self::normalise_visibility((string)($item->visibility ?? self::VISIBILITY_COURSE));
        $validationstate = self::normalise_validation_state(
            (string)($item->validationstate ?? self::VALIDATION_UNVERIFIED)
        );

        if ($this->is_restricted_visibility($visibility)
            && !has_capability('mod/uckkarchive:viewrestricted', $context, $user)) {
            return false;
        }

        if ($exporttype === self::EXPORT_PUBLIC_PACKAGE && $visibility !== self::VISIBILITY_PUBLIC) {
            return false;
        }

        if ($this->exportrequiresvalidation
            && !in_array($validationstate, [
                self::VALIDATION_HUMAN_REVIEWED,
                self::VALIDATION_VERIFIED,
                self::VALIDATION_ARCHIVED,
            ], true)) {
            return false;
        }

        return true;
    }

    /**
     * Whether a status transition is allowed by archive policy.
     *
     * Services must still check capabilities and record events.
     *
     * @param string $from Current status.
     * @param string $to New status.
     * @return bool
     */
    public function can_transition_status(string $from, string $to): bool {
        $from = self::normalise_status($from);
        $to = self::normalise_status($to);

        if ($from === $to) {
            return true;
        }

        $map = [
            self::STATUS_DRAFT => [
                self::STATUS_ACTIVE,
                self::STATUS_PENDING,
                self::STATUS_PENDING_REVIEW,
                self::STATUS_CANCELLED,
            ],
            self::STATUS_ACTIVE => [
                self::STATUS_PENDING_REVIEW,
                self::STATUS_VALIDATED,
                self::STATUS_CONTESTED,
                self::STATUS_HIDDEN,
                self::STATUS_ARCHIVED,
                self::STATUS_CLOSED,
            ],
            self::STATUS_PENDING => [
                self::STATUS_PENDING_REVIEW,
                self::STATUS_VALIDATED,
                self::STATUS_REJECTED,
                self::STATUS_CORRECTION_REQUIRED,
                self::STATUS_CANCELLED,
            ],
            self::STATUS_PENDING_REVIEW => [
                self::STATUS_VALIDATED,
                self::STATUS_REJECTED,
                self::STATUS_CORRECTION_REQUIRED,
                self::STATUS_CONTESTED,
                self::STATUS_INVALIDATED,
            ],
            self::STATUS_VALIDATED => [
                self::STATUS_ARCHIVED,
                self::STATUS_CONTESTED,
                self::STATUS_INVALIDATED,
                self::STATUS_CLOSED,
            ],
            self::STATUS_REJECTED => [
                self::STATUS_CORRECTION_REQUIRED,
                self::STATUS_ARCHIVED,
                self::STATUS_CLOSED,
            ],
            self::STATUS_CORRECTION_REQUIRED => [
                self::STATUS_PENDING_REVIEW,
                self::STATUS_VALIDATED,
                self::STATUS_REJECTED,
                self::STATUS_CANCELLED,
            ],
            self::STATUS_CONTESTED => [
                self::STATUS_PENDING_REVIEW,
                self::STATUS_VALIDATED,
                self::STATUS_INVALIDATED,
                self::STATUS_ARCHIVED,
                self::STATUS_CLOSED,
            ],
            self::STATUS_INVALIDATED => [
                self::STATUS_ARCHIVED,
                self::STATUS_CLOSED,
            ],
            self::STATUS_HIDDEN => [
                self::STATUS_ACTIVE,
                self::STATUS_ARCHIVED,
                self::STATUS_CLOSED,
            ],
            self::STATUS_ARCHIVED => [
                self::STATUS_CONTESTED,
            ],
            self::STATUS_CLOSED => [],
            self::STATUS_CANCELLED => [],
        ];

        return in_array($to, $map[$from] ?? [], true);
    }

    /**
     * Whether a validation transition is allowed by policy.
     *
     * @param string $from Current validation state.
     * @param string $to New validation state.
     * @return bool
     */
    public function can_transition_validation(string $from, string $to): bool {
        $from = self::normalise_validation_state($from);
        $to = self::normalise_validation_state($to);

        if ($from === $to) {
            return true;
        }

        $map = [
            self::VALIDATION_UNVERIFIED => [
                self::VALIDATION_HUMAN_REVIEWED,
                self::VALIDATION_VERIFIED,
                self::VALIDATION_CONTESTED,
                self::VALIDATION_INVALIDATED,
            ],
            self::VALIDATION_HUMAN_REVIEWED => [
                self::VALIDATION_VERIFIED,
                self::VALIDATION_CONTESTED,
                self::VALIDATION_INVALIDATED,
                self::VALIDATION_ARCHIVED,
            ],
            self::VALIDATION_VERIFIED => [
                self::VALIDATION_CONTESTED,
                self::VALIDATION_INVALIDATED,
                self::VALIDATION_ARCHIVED,
            ],
            self::VALIDATION_CONTESTED => [
                self::VALIDATION_HUMAN_REVIEWED,
                self::VALIDATION_VERIFIED,
                self::VALIDATION_INVALIDATED,
                self::VALIDATION_ARCHIVED,
            ],
            self::VALIDATION_INVALIDATED => [
                self::VALIDATION_ARCHIVED,
            ],
            self::VALIDATION_ARCHIVED => [
                self::VALIDATION_CONTESTED,
            ],
        ];

        return in_array($to, $map[$from] ?? [], true);
    }

    /**
     * Validate archive item fields against policy.
     *
     * @param array<string, mixed>|stdClass $item Archive item.
     * @return array<string, string> Field => error key.
     */
    public function validate_item_policy(array|stdClass $item): array {
        $item = (object)$item;
        $errors = [];

        if (trim((string)($item->title ?? $item->name ?? '')) === '') {
            $errors['title'] = 'missingtitle';
        }

        $status = self::normalise_status((string)($item->status ?? ''));
        if (!in_array($status, self::get_allowed_statuses(), true)) {
            $errors['status'] = 'invalidstatus';
        }

        $visibility = self::normalise_visibility((string)($item->visibility ?? ''));
        if (!in_array($visibility, self::get_allowed_visibilities(), true)) {
            $errors['visibility'] = 'invalidvisibility';
        }

        $provenance = self::normalise_provenance((string)($item->provenance ?? ''));
        if (!in_array($provenance, self::get_allowed_provenance_sources(), true)) {
            $errors['provenance'] = 'invalidprovenance';
        }

        $validationstate = self::normalise_validation_state((string)($item->validationstate ?? self::VALIDATION_UNVERIFIED));
        if (!in_array($validationstate, self::get_allowed_validation_states(), true)) {
            $errors['validationstate'] = 'invalidvalidationstate';
        }

        if ($this->requires_provenance_statement($item)
            && trim((string)($item->provenancestatement ?? $item->source ?? '')) === '') {
            $errors['provenancestatement'] = 'missingprovenance';
        }

        if ($this->aiprovenancerequired
            && $provenance === self::PROVENANCE_AI_ASSISTED
            && trim((string)($item->ailog ?? $item->metadata ?? '')) === '') {
            $errors['ailog'] = 'missingaiprovenance';
        }

        if ($this->publicrequiresverified
            && $visibility === self::VISIBILITY_PUBLIC
            && !in_array($validationstate, [
                self::VALIDATION_HUMAN_REVIEWED,
                self::VALIDATION_VERIFIED,
                self::VALIDATION_ARCHIVED,
            ], true)) {
            $errors['validationstate'] = 'publicrequiresvalidation';
        }

        if ($visibility === self::VISIBILITY_RESTRICTED_INTEGRITY
            && !in_array($provenance, [
                self::PROVENANCE_INTEGRITY,
                self::PROVENANCE_ARCHIVE,
                self::PROVENANCE_SYSTEM,
            ], true)) {
            $errors['provenance'] = 'restrictedintegrityrequiresintegrityprovenance';
        }

        return $errors;
    }

    /**
     * Return default values for a new archive item.
     *
     * @param int $userid Acting user id.
     * @param int|null $now Timestamp.
     * @return array<string, mixed>
     */
    public function get_default_item_values(int $userid, ?int $now = null): array {
        $now ??= time();

        return [
            'status' => self::STATUS_DRAFT,
            'visibility' => self::VISIBILITY_COURSE,
            'validationstate' => self::VALIDATION_UNVERIFIED,
            'provenance' => self::PROVENANCE_HUMAN,
            'versionno' => 1,
            'createdby' => $userid,
            'modifiedby' => $userid,
            'timecreated' => $now,
            'timemodified' => $now,
            'metadata' => null,
        ];
    }

    /**
     * Apply policy defaults to a record before insert.
     *
     * @param array<string, mixed>|stdClass $record Raw record.
     * @param int $userid Acting user id.
     * @param int|null $now Timestamp.
     * @return stdClass
     */
    public function prepare_insert_record(array|stdClass $record, int $userid, ?int $now = null): stdClass {
        $now ??= time();

        $record = (object)array_merge($this->get_default_item_values($userid, $now), (array)$record);

        $record->status = self::normalise_status((string)$record->status);
        $record->visibility = self::normalise_visibility((string)$record->visibility);
        $record->validationstate = self::normalise_validation_state((string)$record->validationstate);
        $record->provenance = self::normalise_provenance((string)$record->provenance);
        $record->versionno = max(1, (int)($record->versionno ?? 1));
        $record->createdby = !empty($record->createdby) ? (int)$record->createdby : $userid;
        $record->modifiedby = $userid;
        $record->timecreated = !empty($record->timecreated) ? (int)$record->timecreated : $now;
        $record->timemodified = $now;

        return $record;
    }

    /**
     * Apply policy defaults to a record before update.
     *
     * @param array<string, mixed>|stdClass $record Raw record.
     * @param int $userid Acting user id.
     * @param int|null $now Timestamp.
     * @return stdClass
     */
    public function prepare_update_record(array|stdClass $record, int $userid, ?int $now = null): stdClass {
        $now ??= time();

        $record = (object)$record;

        if (isset($record->status)) {
            $record->status = self::normalise_status((string)$record->status);
        }

        if (isset($record->visibility)) {
            $record->visibility = self::normalise_visibility((string)$record->visibility);
        }

        if (isset($record->validationstate)) {
            $record->validationstate = self::normalise_validation_state((string)$record->validationstate);
        }

        if (isset($record->provenance)) {
            $record->provenance = self::normalise_provenance((string)$record->provenance);
        }

        if (isset($record->versionno)) {
            $record->versionno = max(1, (int)$record->versionno);
        }

        $record->modifiedby = $userid;
        $record->timemodified = $now;

        return $record;
    }

    /**
     * Whether visibility is restricted.
     *
     * @param string $visibility Visibility key.
     * @return bool
     */
    public function is_restricted_visibility(string $visibility): bool {
        $visibility = self::normalise_visibility($visibility);

        return in_array($visibility, [
            self::VISIBILITY_PRIVATE,
            self::VISIBILITY_RESTRICTED,
            self::VISIBILITY_RESTRICTED_INTEGRITY,
            self::VISIBILITY_HIDDEN,
        ], true);
    }

    /**
     * Whether visibility is public.
     *
     * @param string $visibility Visibility key.
     * @return bool
     */
    public function is_public_visibility(string $visibility): bool {
        return self::normalise_visibility($visibility) === self::VISIBILITY_PUBLIC;
    }

    /**
     * Whether a record requires a provenance statement.
     *
     * @param array<string, mixed>|stdClass $item Archive item.
     * @return bool
     */
    public function requires_provenance_statement(array|stdClass $item): bool {
        $item = (object)$item;

        $provenance = self::normalise_provenance((string)($item->provenance ?? self::PROVENANCE_HUMAN));
        $visibility = self::normalise_visibility((string)($item->visibility ?? self::VISIBILITY_COURSE));
        $type = self::normalise_item_type((string)($item->itemtype ?? $item->type ?? self::TYPE_ARCHIVE_ITEM));

        if ($provenance !== self::PROVENANCE_HUMAN) {
            return true;
        }

        if ($this->is_restricted_visibility($visibility) || $visibility === self::VISIBILITY_PUBLIC) {
            return true;
        }

        return in_array($type, [
            self::TYPE_PROOF,
            self::TYPE_DECISION,
            self::TYPE_COMPETENCY,
            self::TYPE_BADGE,
        ], true);
    }

    /**
     * Whether the item requires human validation.
     *
     * @param array<string, mixed>|stdClass $item Archive item.
     * @return bool
     */
    public function requires_human_validation(array|stdClass $item): bool {
        $item = (object)$item;

        $visibility = self::normalise_visibility((string)($item->visibility ?? self::VISIBILITY_COURSE));
        $provenance = self::normalise_provenance((string)($item->provenance ?? self::PROVENANCE_HUMAN));
        $type = self::normalise_item_type((string)($item->itemtype ?? $item->type ?? self::TYPE_ARCHIVE_ITEM));

        if ($visibility === self::VISIBILITY_PUBLIC || $this->is_restricted_visibility($visibility)) {
            return true;
        }

        if ($provenance === self::PROVENANCE_AI_ASSISTED || $provenance === self::PROVENANCE_IMPORTED) {
            return true;
        }

        return in_array($type, [
            self::TYPE_PROOF,
            self::TYPE_DECISION,
            self::TYPE_COMPETENCY,
            self::TYPE_BADGE,
        ], true);
    }

    /**
     * Return retention class for an item.
     *
     * @param array<string, mixed>|stdClass $item Archive item.
     * @return string
     */
    public function get_retention_class(array|stdClass $item): string {
        $item = (object)$item;

        $visibility = self::normalise_visibility((string)($item->visibility ?? self::VISIBILITY_COURSE));
        $validationstate = self::normalise_validation_state(
            (string)($item->validationstate ?? self::VALIDATION_UNVERIFIED)
        );
        $status = self::normalise_status((string)($item->status ?? self::STATUS_DRAFT));

        if ($visibility === self::VISIBILITY_RESTRICTED_INTEGRITY
            || $validationstate === self::VALIDATION_CONTESTED
            || $status === self::STATUS_CONTESTED) {
            return self::RETENTION_RESTRICTED_REVIEW;
        }

        if ($validationstate === self::VALIDATION_INVALIDATED
            || $status === self::STATUS_INVALIDATED) {
            return self::RETENTION_LEGAL_HOLD;
        }

        if ($status === self::STATUS_ARCHIVED
            || $validationstate === self::VALIDATION_ARCHIVED
            || $visibility === self::VISIBILITY_ARCHIVED) {
            return self::RETENTION_PERMANENT;
        }

        return self::RETENTION_NORMAL;
    }

    /**
     * Whether an archive item is owned by the user.
     *
     * @param stdClass $item Archive item.
     * @param stdClass $user User record.
     * @return bool
     */
    private function is_item_owner(stdClass $item, stdClass $user): bool {
        $userid = (int)($user->id ?? 0);

        if ($userid <= 0) {
            return false;
        }

        return (int)($item->userid ?? 0) === $userid
            || (int)($item->createdby ?? 0) === $userid
            || (int)($item->authorid ?? 0) === $userid;
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
     * Return allowed archive item types.
     *
     * @return string[]
     */
    public static function get_allowed_item_types(): array {
        return [
            self::TYPE_ARCHIVE_ITEM,
            self::TYPE_KRISTAL,
            self::TYPE_PROOF,
            self::TYPE_DECISION,
            self::TYPE_REFLECTION,
            self::TYPE_PORTFOLIO_ITEM,
            self::TYPE_BADGE,
            self::TYPE_COMPETENCY,
        ];
    }

    /**
     * Return allowed archive policies.
     *
     * @return string[]
     */
    public static function get_allowed_archive_policies(): array {
        return [
            self::POLICY_NONE,
            self::POLICY_SUMMARY,
            self::POLICY_FULL,
            self::POLICY_RESTRICTED_INTEGRITY,
        ];
    }

    /**
     * Return allowed export types.
     *
     * @return string[]
     */
    public static function get_allowed_export_types(): array {
        return [
            self::EXPORT_ITEM_SUMMARY,
            self::EXPORT_EVIDENCE_PACKAGE,
            self::EXPORT_PUBLIC_PACKAGE,
            self::EXPORT_RESTRICTED_PACKAGE,
        ];
    }

    /**
     * Normalise status.
     *
     * @param string $status Raw status.
     * @return string
     */
    public static function normalise_status(string $status): string {
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
    public static function normalise_visibility(string $visibility): string {
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
    public static function normalise_provenance(string $provenance): string {
        $provenance = clean_param($provenance, PARAM_ALPHANUMEXT);

        return in_array($provenance, self::get_allowed_provenance_sources(), true)
            ? $provenance
            : self::PROVENANCE_HUMAN;
    }

    /**
     * Normalise validation state.
     *
     * @param string $state Raw validation state.
     * @return string
     */
    public static function normalise_validation_state(string $state): string {
        $state = clean_param($state, PARAM_ALPHANUMEXT);

        return in_array($state, self::get_allowed_validation_states(), true)
            ? $state
            : self::VALIDATION_UNVERIFIED;
    }

    /**
     * Normalise archive item type.
     *
     * @param string $type Raw type.
     * @return string
     */
    public static function normalise_item_type(string $type): string {
        $type = clean_param($type, PARAM_ALPHANUMEXT);

        return in_array($type, self::get_allowed_item_types(), true)
            ? $type
            : self::TYPE_ARCHIVE_ITEM;
    }

    /**
     * Normalise archive policy.
     *
     * @param string $policy Raw policy.
     * @return string
     */
    public static function normalise_archive_policy(string $policy): string {
        $policy = clean_param($policy, PARAM_ALPHANUMEXT);

        return in_array($policy, self::get_allowed_archive_policies(), true)
            ? $policy
            : self::POLICY_SUMMARY;
    }

    /**
     * Normalise export type.
     *
     * @param string $exporttype Raw export type.
     * @return string
     */
    public static function normalise_export_type(string $exporttype): string {
        $exporttype = clean_param($exporttype, PARAM_ALPHANUMEXT);

        return in_array($exporttype, self::get_allowed_export_types(), true)
            ? $exporttype
            : self::EXPORT_ITEM_SUMMARY;
    }
}

