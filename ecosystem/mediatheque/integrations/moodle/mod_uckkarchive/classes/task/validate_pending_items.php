<?php
// This file is part of Moodle - https://moodle.org/
//
// Moodle is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// any later version.

/**
 * Scheduled task that pre-validates pending UCKK archive items.
 *
 * @package    mod_uckkarchive
 * @copyright  2026 Univers-Cité King Klown
 * @license    https://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later
 */

declare(strict_types=1);

namespace mod_uckkarchive\task;

use context;
use core\task\scheduled_task;
use mod_uckkarchive\local\revision;
use stdClass;

defined('MOODLE_INTERNAL') || die();

/**
 * Scheduled task that performs non-sovereign validation checks on pending items.
 *
 * This task does mechanical archive-readiness checks only. It must not replace
 * Archiviste/Inquisiteur review, publish archive items, certify evidence, or
 * convert unverified evidence into final institutional truth.
 */
final class validate_pending_items extends scheduled_task {
    /** Task lock namespace. */
    private const LOCK_TYPE = 'mod_uckkarchive_validate_pending_items';

    /** Lock key. */
    private const LOCK_KEY = 'global';

    /** Maximum lock wait in seconds. */
    private const LOCK_TIMEOUT = 5;

    /** Default processing limit per cron run. */
    private const DEFAULT_LIMIT = 100;

    /** Status: submitted. */
    private const STATUS_SUBMITTED = 'submitted';

    /** Status: pending. */
    private const STATUS_PENDING = 'pending';

    /** Status: pending review. */
    private const STATUS_PENDING_REVIEW = 'pending_review';

    /** Status: correction required. */
    private const STATUS_CORRECTION_REQUIRED = 'correction_required';

    /** Status: invalidated. */
    private const STATUS_INVALIDATED = 'invalidated';

    /** Validation state: unverified. */
    private const VALIDATION_UNVERIFIED = 'unverified';

    /** Validation state: human reviewed. */
    private const VALIDATION_HUMAN_REVIEWED = 'human_reviewed';

    /**
     * Return task name.
     *
     * @return string
     */
    public function get_name(): string {
        return get_string('task:validate_pending_items', 'uckkarchive');
    }

    /**
     * Execute task.
     */
    public function execute(): void {
        global $DB;

        if (!$DB->get_manager()->table_exists('uckkarchive_item')) {
            mtrace('mod_uckkarchive: table {uckkarchive_item} does not exist; skipping pending item validation.');
            return;
        }

        $lockfactory = \core\lock\lock_config::get_lock_factory(self::LOCK_TYPE);
        $lock = $lockfactory->get_lock(self::LOCK_KEY, self::LOCK_TIMEOUT);

        if (!$lock) {
            mtrace('mod_uckkarchive: validate_pending_items already running; skipping this run.');
            return;
        }

        try {
            $limit = $this->get_processing_limit();
            $items = $this->get_pending_items($limit);
            $count = count($items);

            if ($count === 0) {
                mtrace('mod_uckkarchive: no pending archive items to validate.');
                return;
            }

            mtrace('mod_uckkarchive: validating pending archive items: ' . $count);

            $processed = 0;
            $ready = 0;
            $correction = 0;
            $skipped = 0;

            foreach ($items as $item) {
                try {
                    $result = $this->process_item($item);
                    $processed++;

                    if ($result === self::STATUS_PENDING_REVIEW) {
                        $ready++;
                    } else if ($result === self::STATUS_CORRECTION_REQUIRED) {
                        $correction++;
                    } else {
                        $skipped++;
                    }
                } catch (\Throwable $exception) {
                    $skipped++;
                    mtrace('mod_uckkarchive: failed to validate archive item ' . $item->id . ': ' . $exception->getMessage());
                }
            }

            mtrace(
                'mod_uckkarchive: pending item validation completed. ' .
                'processed=' . $processed .
                ', ready=' . $ready .
                ', correction_required=' . $correction .
                ', skipped=' . $skipped
            );
        } finally {
            $lock->release();
        }
    }

    /**
     * Get processing limit.
     *
     * @return int
     */
    private function get_processing_limit(): int {
        $configured = (int)get_config('uckkarchive', 'pendingvalidationlimit');

        if ($configured <= 0) {
            return self::DEFAULT_LIMIT;
        }

        return min($configured, 1000);
    }

    /**
     * Fetch pending archive items.
     *
     * @param int $limit Maximum records to process.
     * @return stdClass[]
     */
    private function get_pending_items(int $limit): array {
        global $DB;

        [$statussql, $statusparams] = $DB->get_in_or_equal([
            self::STATUS_SUBMITTED,
            self::STATUS_PENDING,
            self::STATUS_PENDING_REVIEW,
        ], SQL_PARAMS_NAMED, 'status');

        [$validationsql, $validationparams] = $DB->get_in_or_equal([
            self::VALIDATION_UNVERIFIED,
            self::VALIDATION_HUMAN_REVIEWED,
        ], SQL_PARAMS_NAMED, 'validation');

        $sql = "
            SELECT *
              FROM {uckkarchive_item}
             WHERE status {$statussql}
               AND validationstate {$validationsql}
          ORDER BY timemodified ASC, id ASC
        ";

        return $DB->get_records_sql($sql, $statusparams + $validationparams, 0, $limit);
    }

    /**
     * Process one item.
     *
     * @param stdClass $item Archive item record.
     * @return string Resulting status.
     */
    private function process_item(stdClass $item): string {
        global $DB, $USER;

        if (!$this->can_process_item($item)) {
            return 'skipped';
        }

        $checks = $this->validate_item_readiness($item);
        $now = time();

        if ($checks['passed']) {
            $newstatus = self::STATUS_PENDING_REVIEW;
            $reason = get_string('task:validation_ready_reason', 'uckkarchive');
        } else {
            $newstatus = self::STATUS_CORRECTION_REQUIRED;
            $reason = get_string('task:validation_correction_reason', 'uckkarchive');
        }

        $metadata = $this->merge_metadata($item, [
            'system_validation' => [
                'checked_at' => $now,
                'checked_by_task' => self::class,
                'passed' => $checks['passed'],
                'errors' => $checks['errors'],
                'warnings' => $checks['warnings'],
                'non_sovereign' => true,
                'requires_human_validation' => true,
            ],
        ]);

        $transaction = $DB->start_delegated_transaction();

        $update = new stdClass();
        $update->id = (int)$item->id;
        $update->status = $newstatus;
        $update->timemodified = $now;
        $update->modifiedby = $this->get_actor_id();
        $update->metadata = json_encode($metadata, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);

        // The scheduled task can route the item toward human review, but must not
        // assert final validation. Human-reviewed items keep their validation state.
        if ((string)$item->validationstate !== self::VALIDATION_HUMAN_REVIEWED) {
            $update->validationstate = self::VALIDATION_UNVERIFIED;
        }

        $DB->update_record('uckkarchive_item', $update);

        $this->create_revision($item, $newstatus, $reason, $metadata);

        $transaction->allow_commit();

        return $newstatus;
    }

    /**
     * Whether the item can be processed by this task.
     *
     * @param stdClass $item Archive item.
     * @return bool
     */
    private function can_process_item(stdClass $item): bool {
        if (empty($item->id) || empty($item->archiveid) || empty($item->contextid)) {
            return false;
        }

        if ((string)($item->status ?? '') === self::STATUS_INVALIDATED) {
            return false;
        }

        if ((string)($item->validationstate ?? '') === 'verified') {
            return false;
        }

        return true;
    }

    /**
     * Perform mechanical readiness checks for an archive item.
     *
     * @param stdClass $item Archive item record.
     * @return array{passed: bool, errors: string[], warnings: string[]}
     */
    private function validate_item_readiness(stdClass $item): array {
        $errors = [];
        $warnings = [];

        if (trim((string)($item->title ?? '')) === '') {
            $errors[] = 'missing_title';
        }

        if (trim((string)($item->itemtype ?? '')) === '') {
            $errors[] = 'missing_itemtype';
        }

        if (!in_array((string)($item->visibility ?? ''), $this->get_allowed_visibilities(), true)) {
            $errors[] = 'invalid_visibility';
        }

        if (!in_array((string)($item->provenance ?? ''), $this->get_allowed_provenance_sources(), true)) {
            $errors[] = 'invalid_provenance';
        }

        if (!in_array((string)($item->validationstate ?? ''), $this->get_allowed_validation_states(), true)) {
            $errors[] = 'invalid_validation_state';
        }

        $hascontent = trim((string)($item->content ?? '')) !== '';
        $hassource = trim((string)($item->sourceurl ?? '')) !== '';
        $hasfiles = $this->item_has_files((int)$item->contextid, (int)$item->id);

        if (!$hascontent && !$hassource && !$hasfiles) {
            $errors[] = 'missing_content_source_or_files';
        }

        if ((string)($item->visibility ?? '') === 'public' && trim((string)($item->publicsummary ?? '')) === '') {
            $errors[] = 'missing_public_summary';
        }

        if ((string)($item->provenance ?? '') === 'ai_assisted' && !$this->has_ai_metadata($item)) {
            $errors[] = 'missing_ai_metadata';
        }

        if (empty($item->provenancehash) && ($hascontent || $hassource)) {
            $warnings[] = 'missing_provenance_hash';
        }

        if (empty($item->createdby)) {
            $warnings[] = 'missing_createdby';
        }

        if (empty($item->versionno)) {
            $warnings[] = 'missing_versionno';
        }

        return [
            'passed' => empty($errors),
            'errors' => $errors,
            'warnings' => $warnings,
        ];
    }

    /**
     * Check whether an archive item has files in known archive file areas.
     *
     * @param int $contextid Context id.
     * @param int $itemid Item id.
     * @return bool
     */
    private function item_has_files(int $contextid, int $itemid): bool {
        if ($contextid <= 0 || $itemid <= 0) {
            return false;
        }

        $fs = get_file_storage();

        foreach ($this->get_item_file_areas() as $filearea) {
            $files = $fs->get_area_files($contextid, 'mod_uckkarchive', $filearea, $itemid, 'id', false);

            if (!empty($files)) {
                return true;
            }
        }

        return false;
    }

    /**
     * Known item file areas.
     *
     * @return string[]
     */
    private function get_item_file_areas(): array {
        return [
            'item_files',
            'proof_files',
            'decision_attachments',
            'minutes_files',
            'kristal_files',
            'portfolio_files',
            'integrity_exports',
            'item_content',
            'public_summary',
        ];
    }

    /**
     * Whether an AI-assisted record has AI provenance metadata.
     *
     * @param stdClass $item Archive item.
     * @return bool
     */
    private function has_ai_metadata(stdClass $item): bool {
        $metadata = $this->decode_metadata($item->metadata ?? null);

        return !empty($metadata['ai']) || !empty($metadata['ai_policy']);
    }

    /**
     * Merge metadata into an item metadata payload.
     *
     * @param stdClass $item Archive item.
     * @param array<string, mixed> $append Appended metadata.
     * @return array<string, mixed>
     */
    private function merge_metadata(stdClass $item, array $append): array {
        $metadata = $this->decode_metadata($item->metadata ?? null);

        return array_replace_recursive($metadata, $append);
    }

    /**
     * Decode metadata.
     *
     * @param mixed $metadata Metadata JSON, array or object.
     * @return array<string, mixed>
     */
    private function decode_metadata(mixed $metadata): array {
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

            if (json_last_error() === JSON_ERROR_NONE && is_array($decoded)) {
                return $decoded;
            }
        }

        return [];
    }

    /**
     * Create a revision record for the task outcome.
     *
     * @param stdClass $item Original item record.
     * @param string $newstatus New status.
     * @param string $reason Revision reason.
     * @param array<string, mixed> $metadata Revision metadata.
     */
    private function create_revision(stdClass $item, string $newstatus, string $reason, array $metadata): void {
        global $DB;

        if (!$DB->get_manager()->table_exists('uckkarchive_rev')) {
            return;
        }

        $userid = $this->get_actor_id();
        $now = time();

        if (class_exists(revision::class)) {
            $revision = revision::status_changed(
                (int)$item->archiveid,
                (int)$item->id,
                $userid,
                (string)($item->status ?? ''),
                $newstatus,
                (string)($item->visibility ?? 'course'),
                $reason
            )
                ->with_context(
                    (int)($item->courseid ?? 0),
                    (int)($item->cmid ?? 0),
                    (int)($item->contextid ?? 0)
                )
                ->with_metadata([
                    'task' => self::class,
                    'system_validation' => $metadata['system_validation'] ?? [],
                ]);

            $DB->insert_record('uckkarchive_rev', $revision->to_record($userid, $now));
            return;
        }

        $record = new stdClass();
        $record->archiveid = (int)$item->archiveid;
        $record->itemid = (int)$item->id;
        $record->courseid = (int)($item->courseid ?? 0);
        $record->cmid = (int)($item->cmid ?? 0);
        $record->contextid = (int)($item->contextid ?? 0);
        $record->userid = $userid;
        $record->revisiontype = 'status_changed';
        $record->previousstatus = (string)($item->status ?? '');
        $record->newstatus = $newstatus;
        $record->previousvisibility = (string)($item->visibility ?? '');
        $record->newvisibility = (string)($item->visibility ?? '');
        $record->previousvalidationstate = (string)($item->validationstate ?? '');
        $record->newvalidationstate = (string)($item->validationstate ?? '');
        $record->reason = $reason;
        $record->status = 'active';
        $record->visibility = (string)($item->visibility ?? 'course');
        $record->provenance = 'system';
        $record->provenancehash = null;
        $record->versionno = max(1, (int)($item->versionno ?? 1));
        $record->createdby = $userid;
        $record->modifiedby = $userid;
        $record->timecreated = $now;
        $record->timemodified = $now;
        $record->metadata = json_encode([
            'task' => self::class,
            'system_validation' => $metadata['system_validation'] ?? [],
        ], JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);

        $DB->insert_record('uckkarchive_rev', $record);
    }

    /**
     * Return task actor id.
     *
     * @return int
     */
    private function get_actor_id(): int {
        $admin = get_admin();

        return $admin ? (int)$admin->id : 0;
    }

    /**
     * Allowed visibility states.
     *
     * @return string[]
     */
    private function get_allowed_visibilities(): array {
        if (function_exists('local_uckk_get_visibilities')) {
            return array_merge(local_uckk_get_visibilities(), ['program', 'institutional', 'restricted', 'hidden', 'archived']);
        }

        return [
            'private',
            'user',
            'group',
            'course',
            'cohort',
            'program',
            'institution',
            'institutional',
            'public',
            'restricted',
            'restricted_integrity',
            'hidden',
            'archived',
        ];
    }

    /**
     * Allowed provenance sources.
     *
     * @return string[]
     */
    private function get_allowed_provenance_sources(): array {
        if (function_exists('local_uckk_get_provenance_sources')) {
            return local_uckk_get_provenance_sources();
        }

        return [
            'human',
            'ai_assisted',
            'imported',
            'system',
            'archive',
            'assembly',
            'challenge',
            'integrity',
        ];
    }

    /**
     * Allowed validation states.
     *
     * @return string[]
     */
    private function get_allowed_validation_states(): array {
        if (function_exists('local_uckk_get_validation_states')) {
            return local_uckk_get_validation_states();
        }

        return [
            'unverified',
            'human_reviewed',
            'verified',
            'contested',
            'invalidated',
            'archived',
        ];
    }
}
