<?php
// This file is part of Moodle - https://moodle.org/
//
// Moodle is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// any later version.

/**
 * Scheduled task for generating queued UCKK archive exports.
 *
 * @package    mod_uckkarchive
 * @copyright  2026 Univers-Cité King Klown
 * @license    https://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later
 */

declare(strict_types=1);

namespace mod_uckkarchive\task;

use core\lock\lock_config;
use core\task\scheduled_task;
use moodle_exception;
use stdClass;

defined('MOODLE_INTERNAL') || die();

/**
 * Generate queued archive exports.
 *
 * This task is intentionally narrow:
 * - it finds pending export records;
 * - it marks one export as being processed;
 * - it delegates package creation to the archive export package layer;
 * - it records success or failure.
 *
 * It must not validate archive items, revise public archive records, decide
 * integrity outcomes, change evidence visibility, or delete source data.
 */
final class generate_archive_exports extends scheduled_task {
    /** Component name. */
    private const COMPONENT = 'mod_uckkarchive';

    /** Export table. */
    private const TABLE_EXPORT = 'uckkarchive_export';

    /** Archive table. */
    private const TABLE_ARCHIVE = 'uckkarchive';

    /** Pending export status. */
    private const STATUS_PENDING = 'pending';

    /** Processing export status. */
    private const STATUS_ACTIVE = 'active';

    /** Completed/generated export status. */
    private const STATUS_VALIDATED = 'validated';

    /** Failed export status. */
    private const STATUS_REJECTED = 'rejected';

    /** Archived export status. */
    private const STATUS_ARCHIVED = 'archived';

    /** Default batch size. */
    private const DEFAULT_BATCH_SIZE = 25;

    /** Maximum batch size. */
    private const MAX_BATCH_SIZE = 100;

    /** Lock timeout in seconds. */
    private const LOCK_TIMEOUT = 5;

    /**
     * Return task name.
     *
     * @return string
     */
    public function get_name(): string {
        return get_string('task_generate_archive_exports', 'uckkarchive');
    }

    /**
     * Execute the scheduled task.
     */
    public function execute(): void {
        global $DB;

        $lockfactory = lock_config::get_lock_factory(self::COMPONENT);
        $lock = $lockfactory->get_lock('generate_archive_exports', self::LOCK_TIMEOUT);

        if (!$lock) {
            mtrace('[mod_uckkarchive] Export generation skipped: another task run holds the lock.');
            return;
        }

        try {
            if (!$DB->get_manager()->table_exists(self::TABLE_EXPORT)) {
                mtrace('[mod_uckkarchive] Export generation skipped: export table does not exist.');
                return;
            }

            $batchsize = $this->get_batch_size();
            $exports = $this->get_pending_exports($batchsize);

            if (empty($exports)) {
                mtrace('[mod_uckkarchive] No pending archive exports.');
                return;
            }

            mtrace('[mod_uckkarchive] Processing ' . count($exports) . ' pending archive export(s).');

            foreach ($exports as $export) {
                $this->process_export($export);
            }
        } finally {
            $lock->release();
        }
    }

    /**
     * Return task batch size.
     *
     * @return int
     */
    private function get_batch_size(): int {
        $configured = (int)get_config('mod_uckkarchive', 'exportbatchsize');

        if ($configured <= 0) {
            return self::DEFAULT_BATCH_SIZE;
        }

        return min($configured, self::MAX_BATCH_SIZE);
    }

    /**
     * Get pending export records.
     *
     * @param int $batchsize Batch size.
     * @return stdClass[]
     */
    private function get_pending_exports(int $batchsize): array {
        global $DB;

        return $DB->get_records_select(
            self::TABLE_EXPORT,
            'status = :status',
            ['status' => self::STATUS_PENDING],
            'timecreated ASC, id ASC',
            '*',
            0,
            $batchsize
        );
    }

    /**
     * Process one export record.
     *
     * @param stdClass $export Export record.
     */
    private function process_export(stdClass $export): void {
        global $DB;

        $exportid = (int)$export->id;

        $exportlock = lock_config::get_lock_factory(self::COMPONENT)
            ->get_lock('generate_archive_export_' . $exportid, self::LOCK_TIMEOUT);

        if (!$exportlock) {
            mtrace('[mod_uckkarchive] Export ' . $exportid . ' skipped: record lock unavailable.');
            return;
        }

        try {
            $fresh = $DB->get_record(self::TABLE_EXPORT, ['id' => $exportid], '*', IGNORE_MISSING);

            if (!$fresh) {
                mtrace('[mod_uckkarchive] Export ' . $exportid . ' skipped: record no longer exists.');
                return;
            }

            if (($fresh->status ?? '') !== self::STATUS_PENDING) {
                mtrace('[mod_uckkarchive] Export ' . $exportid . ' skipped: status is no longer pending.');
                return;
            }

            $this->mark_export_processing($fresh);

            $archive = $this->get_archive_record($fresh);

            if (!$archive) {
                $this->mark_export_failed($fresh, get_string('exporterror:missingarchive', 'uckkarchive'));
                mtrace('[mod_uckkarchive] Export ' . $exportid . ' failed: archive record missing.');
                return;
            }

            $result = $this->generate_export_package($fresh, $archive);

            $this->mark_export_complete($fresh, $result);

            mtrace('[mod_uckkarchive] Export ' . $exportid . ' generated.');
        } catch (\Throwable $exception) {
            $this->mark_export_failed($export, $exception->getMessage());
            mtrace('[mod_uckkarchive] Export ' . $exportid . ' failed: ' . $exception->getMessage());
        } finally {
            $exportlock->release();
        }
    }

    /**
     * Get the archive instance for an export.
     *
     * @param stdClass $export Export record.
     * @return stdClass|null
     */
    private function get_archive_record(stdClass $export): ?stdClass {
        global $DB;

        $archiveid = (int)($export->archiveid ?? 0);

        if ($archiveid <= 0) {
            return null;
        }

        return $DB->get_record(self::TABLE_ARCHIVE, ['id' => $archiveid], '*', IGNORE_MISSING) ?: null;
    }

    /**
     * Mark an export as processing.
     *
     * @param stdClass $export Export record.
     */
    private function mark_export_processing(stdClass $export): void {
        global $DB, $USER;

        $record = new stdClass();
        $record->id = (int)$export->id;
        $record->status = self::STATUS_ACTIVE;
        $record->timemodified = time();
        $record->modifiedby = (int)($USER->id ?? 0);
        $record->metadata = $this->merge_metadata($export, [
            'task' => self::class,
            'processingstarted' => time(),
        ]);

        $DB->update_record(self::TABLE_EXPORT, $record);
    }

    /**
     * Mark an export as completed.
     *
     * @param stdClass $export Export record.
     * @param stdClass $result Export result.
     */
    private function mark_export_complete(stdClass $export, stdClass $result): void {
        global $DB, $USER;

        $record = new stdClass();
        $record->id = (int)$export->id;
        $record->status = self::STATUS_VALIDATED;
        $record->timemodified = time();
        $record->modifiedby = (int)($USER->id ?? 0);

        if (property_exists($result, 'filepath')) {
            $record->filepath = $result->filepath;
        }

        if (property_exists($result, 'filename')) {
            $record->filename = $result->filename;
        }

        if (property_exists($result, 'filesize')) {
            $record->filesize = max(0, (int)$result->filesize);
        }

        if (property_exists($result, 'contenthash')) {
            $record->contenthash = clean_param((string)$result->contenthash, PARAM_ALPHANUMEXT);
        }

        $record->metadata = $this->merge_metadata($export, [
            'task' => self::class,
            'completed' => time(),
            'result' => $this->normalise_result_metadata($result),
        ]);

        $DB->update_record(self::TABLE_EXPORT, $record);

        $this->trigger_export_generated_event((int)$export->id);
    }

    /**
     * Mark an export as failed.
     *
     * @param stdClass $export Export record.
     * @param string $message Failure message.
     */
    private function mark_export_failed(stdClass $export, string $message): void {
        global $DB, $USER;

        if (empty($export->id) || !$DB->record_exists(self::TABLE_EXPORT, ['id' => (int)$export->id])) {
            return;
        }

        $record = new stdClass();
        $record->id = (int)$export->id;
        $record->status = self::STATUS_REJECTED;
        $record->timemodified = time();
        $record->modifiedby = (int)($USER->id ?? 0);
        $record->metadata = $this->merge_metadata($export, [
            'task' => self::class,
            'failed' => time(),
            'error' => core_text::substr($message, 0, 1000),
        ]);

        $DB->update_record(self::TABLE_EXPORT, $record);
    }

    /**
     * Generate an export package.
     *
     * The preferred implementation is mod_uckkarchive\local\export_package.
     * This task supports a conservative fallback so the queue state remains
     * coherent during early plugin build-out.
     *
     * Expected export_package method contract for later implementation:
     *
     * export_package::generate(stdClass $export, stdClass $archive): stdClass
     *
     * The returned object may include:
     * - filepath
     * - filename
     * - filesize
     * - contenthash
     * - metadata
     *
     * @param stdClass $export Export record.
     * @param stdClass $archive Archive instance.
     * @return stdClass
     */
    private function generate_export_package(stdClass $export, stdClass $archive): stdClass {
        $class = '\\mod_uckkarchive\\local\\export_package';

        if (class_exists($class) && method_exists($class, 'generate')) {
            $result = $class::generate($export, $archive);

            if ($result instanceof stdClass) {
                return $result;
            }

            throw new moodle_exception('exporterror:invalidresult', 'uckkarchive');
        }

        return $this->generate_placeholder_result($export, $archive);
    }

    /**
     * Build a safe placeholder result while export_package is not implemented.
     *
     * This does not create a downloadable file. It only records that the export
     * queue was processed. Replace by export_package::generate() when the export
     * package class is generated.
     *
     * @param stdClass $export Export record.
     * @param stdClass $archive Archive instance.
     * @return stdClass
     */
    private function generate_placeholder_result(stdClass $export, stdClass $archive): stdClass {
        $result = new stdClass();
        $result->filename = 'uckkarchive-export-' . (int)$archive->id . '-' . (int)$export->id . '.json';
        $result->filepath = null;
        $result->filesize = 0;
        $result->contenthash = null;
        $result->metadata = [
            'placeholder' => true,
            'archiveid' => (int)$archive->id,
            'exportid' => (int)$export->id,
            'generatedby' => self::class,
            'note' => 'No file was generated because export_package::generate() is not available yet.',
        ];

        return $result;
    }

    /**
     * Normalise result metadata for JSON storage.
     *
     * @param stdClass $result Export result.
     * @return array<string, mixed>
     */
    private function normalise_result_metadata(stdClass $result): array {
        $metadata = [];

        foreach (['filepath', 'filename', 'filesize', 'contenthash'] as $field) {
            if (property_exists($result, $field)) {
                $metadata[$field] = $result->{$field};
            }
        }

        if (property_exists($result, 'metadata')) {
            if (is_array($result->metadata)) {
                $metadata['metadata'] = $result->metadata;
            } else if ($result->metadata instanceof stdClass) {
                $metadata['metadata'] = (array)$result->metadata;
            }
        }

        return $metadata;
    }

    /**
     * Merge existing export metadata with task metadata.
     *
     * @param stdClass $export Export record.
     * @param array<string, mixed> $append Metadata to append.
     * @return string|null
     */
    private function merge_metadata(stdClass $export, array $append): ?string {
        $metadata = [];

        if (!empty($export->metadata)) {
            $decoded = json_decode((string)$export->metadata, true);

            if (json_last_error() === JSON_ERROR_NONE && is_array($decoded)) {
                $metadata = $decoded;
            }
        }

        $metadata['generate_archive_exports'] = $append;

        return json_encode($metadata, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
    }

    /**
     * Trigger the archive exported event if the event class exists.
     *
     * @param int $exportid Export record id.
     */
    private function trigger_export_generated_event(int $exportid): void {
        global $DB;

        $eventclass = '\\mod_uckkarchive\\event\\archive_item_exported';

        if (!class_exists($eventclass)) {
            return;
        }

        $export = $DB->get_record(self::TABLE_EXPORT, ['id' => $exportid], '*', IGNORE_MISSING);

        if (!$export || empty($export->archiveid)) {
            return;
        }

        $archive = $DB->get_record(self::TABLE_ARCHIVE, ['id' => (int)$export->archiveid], '*', IGNORE_MISSING);

        if (!$archive || empty($archive->course)) {
            return;
        }

        $cm = get_coursemodule_from_instance('uckkarchive', (int)$archive->id, (int)$archive->course, false, IGNORE_MISSING);

        if (!$cm) {
            return;
        }

        $context = \context_module::instance((int)$cm->id);

        $event = $eventclass::create([
            'objectid' => $exportid,
            'context' => $context,
            'other' => [
                'archiveid' => (int)$archive->id,
                'courseid' => (int)$archive->course,
                'cmid' => (int)$cm->id,
                'status' => $export->status ?? self::STATUS_VALIDATED,
                'visibility' => $export->visibility ?? 'restricted',
            ],
        ]);

        $event->add_record_snapshot(self::TABLE_ARCHIVE, $archive);
        $event->add_record_snapshot(self::TABLE_EXPORT, $export);
        $event->trigger();
    }
}