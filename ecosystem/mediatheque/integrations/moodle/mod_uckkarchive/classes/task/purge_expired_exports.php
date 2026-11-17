<?php
// This file is part of Moodle - https://moodle.org/
//
// Moodle is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// any later version.

/**
 * Scheduled task for purging expired UCKK Archive export packages.
 *
 * @package    mod_uckkarchive
 * @copyright  2026 Univers-Cité King Klown
 * @license    https://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later
 */

declare(strict_types=1);

namespace mod_uckkarchive\task;

defined('MOODLE_INTERNAL') || die();

/**
 * Purge expired export package files and stale export records.
 *
 * This task only handles archive-owned export artefacts. It does not delete
 * source archive items, media records, proofs, Kristals, provenance, revision
 * records, validation records, content markers, external works, or Moodle
 * course data.
 *
 * Purged file areas:
 *
 * - export_package
 * - export_manifest
 * - integrity_exports
 *
 * Selection policy:
 *
 * - exports with explicit `timeexpires` in the past are purgeable when that
 *   column exists;
 * - otherwise completed, failed, cancelled, or archived exports older than the
 *   configured retention period are purgeable;
 * - pending/processing exports are not deleted, but very stale processing
 *   exports may be marked failed.
 */
final class purge_expired_exports extends \core\task\scheduled_task {
    /** Export table. */
    private const TABLE_EXPORT = 'uckkarchive_export';

    /** Component name. */
    private const COMPONENT = 'mod_uckkarchive';

    /** Export package file area. */
    private const FILEAREA_EXPORT_PACKAGE = 'export_package';

    /** Export manifest file area. */
    private const FILEAREA_EXPORT_MANIFEST = 'export_manifest';

    /** Optional integrity export file area. */
    private const FILEAREA_INTEGRITY_EXPORTS = 'integrity_exports';

    /** Default export retention in days. */
    private const DEFAULT_RETENTION_DAYS = 30;

    /** Default stale processing threshold in hours. */
    private const DEFAULT_STALE_PROCESSING_HOURS = 24;

    /** Default batch size. */
    private const DEFAULT_BATCH_LIMIT = 100;

    /**
     * Return task name.
     *
     * @return string
     */
    public function get_name(): string {
        $manager = get_string_manager();

        if ($manager->string_exists('task:purgeexpiredexports', 'uckkarchive')) {
            return get_string('task:purgeexpiredexports', 'uckkarchive');
        }

        if ($manager->string_exists('purgeexpiredexports', 'uckkarchive')) {
            return get_string('purgeexpiredexports', 'uckkarchive');
        }

        return 'Purge expired UCKK Archive exports';
    }

    /**
     * Execute task.
     *
     * @return void
     */
    public function execute(): void {
        global $DB;

        if (!$this->table_exists(self::TABLE_EXPORT)) {
            mtrace('UCKK Archive export table is not installed. Nothing to purge.');
            return;
        }

        $columns = $DB->get_columns(self::TABLE_EXPORT);

        $this->mark_stale_processing_exports_failed($columns);

        $records = $this->get_expired_exports($columns);

        if (empty($records)) {
            mtrace('No expired UCKK Archive exports found.');
            return;
        }

        $purged = 0;
        $failed = 0;

        foreach ($records as $record) {
            try {
                $this->purge_export($record, $columns);
                $purged++;
            } catch (\Throwable $exception) {
                $failed++;
                mtrace(
                    'Failed to purge UCKK Archive export id ' .
                    (int)$record->id .
                    ': ' .
                    $exception->getMessage()
                );
            }
        }

        mtrace('Purged ' . $purged . ' expired UCKK Archive export(s).');

        if ($failed > 0) {
            mtrace('Failed to purge ' . $failed . ' expired UCKK Archive export(s).');
        }
    }

    /**
     * Mark abandoned processing exports as failed.
     *
     * @param array<string,object> $columns Export table columns.
     * @return void
     */
    private function mark_stale_processing_exports_failed(array $columns): void {
        global $DB;

        if (!$this->has_column($columns, 'status') || !$this->has_column($columns, 'timemodified')) {
            return;
        }

        $hours = $this->get_positive_config_int(
            'exportstaleprocessinghours',
            self::DEFAULT_STALE_PROCESSING_HOURS
        );

        $cutoff = time() - ($hours * HOURSECS);

        $params = [
            'processing' => 'processing',
            'pending' => 'pending',
            'failed' => 'failed',
            'cutoff' => $cutoff,
            'now' => time(),
        ];

        $set = 'status = :failed';

        if ($this->has_column($columns, 'error')) {
            $set .= ', error = :error';
            $params['error'] = 'Export marked failed by purge_expired_exports after exceeding stale processing threshold.';
        }

        if ($this->has_column($columns, 'modifiedby')) {
            $set .= ', modifiedby = :modifiedby';
            $params['modifiedby'] = 0;
        }

        if ($this->has_column($columns, 'timemodified')) {
            $set .= ', timemodified = :now';
        }

        $sql = "UPDATE {" . self::TABLE_EXPORT . "}
                   SET {$set}
                 WHERE status IN (:processing, :pending)
                   AND timemodified > 0
                   AND timemodified < :cutoff";

        $DB->execute($sql, $params);
    }

    /**
     * Return expired export records.
     *
     * @param array<string,object> $columns Export table columns.
     * @return \stdClass[]
     */
    private function get_expired_exports(array $columns): array {
        global $DB;

        $params = [];
        $where = [];

        if ($this->has_column($columns, 'timeexpires')) {
            $where[] = '(timeexpires IS NOT NULL AND timeexpires > 0 AND timeexpires < :now)';
            $params['now'] = time();
        }

        if ($this->has_column($columns, 'status')) {
            $statuses = [
                'completed',
                'failed',
                'cancelled',
                'archived',
            ];

            [$statussql, $statusparams] = $DB->get_in_or_equal($statuses, SQL_PARAMS_NAMED, 'status');
            $params = array_merge($params, $statusparams);

            $timefield = $this->get_retention_time_field($columns);
            if ($timefield !== null) {
                $retentiondays = $this->get_positive_config_int('exportretentiondays', self::DEFAULT_RETENTION_DAYS);
                $cutoff = time() - ($retentiondays * DAYSECS);

                $where[] = "(status {$statussql} AND {$timefield} > 0 AND {$timefield} < :retentioncutoff)";
                $params['retentioncutoff'] = $cutoff;
            }
        }

        if (empty($where)) {
            return [];
        }

        $sql = "SELECT *
                  FROM {" . self::TABLE_EXPORT . "}
                 WHERE (" . implode(' OR ', $where) . ")
              ORDER BY timecreated ASC, id ASC";

        $limit = $this->get_positive_config_int('exportpurgebatchlimit', self::DEFAULT_BATCH_LIMIT);

        return array_values($DB->get_records_sql($sql, $params, 0, $limit));
    }

    /**
     * Purge one export record and related files.
     *
     * @param \stdClass $record Export record.
     * @param array<string,object> $columns Export table columns.
     * @return void
     */
    private function purge_export(\stdClass $record, array $columns): void {
        global $DB;

        $exportid = (int)$record->id;
        $contextid = (int)($record->contextid ?? 0);

        if ($contextid > 0) {
            $this->delete_export_files($contextid, $exportid);
        }

        $this->delete_export_fileitem_files($record, $columns);

        $DB->delete_records(self::TABLE_EXPORT, ['id' => $exportid]);

        mtrace('Purged UCKK Archive export id ' . $exportid . '.');
    }

    /**
     * Delete standard export file areas for one export.
     *
     * @param int $contextid Context id.
     * @param int $exportid Export id.
     * @return void
     */
    private function delete_export_files(int $contextid, int $exportid): void {
        $fs = get_file_storage();

        foreach ($this->get_export_fileareas() as $filearea) {
            $fs->delete_area_files($contextid, self::COMPONENT, $filearea, $exportid);
        }
    }

    /**
     * Delete package files referenced by fileitemid when present.
     *
     * Some generated packages may use `fileitemid` instead of export id as the
     * File API item id.
     *
     * @param \stdClass $record Export record.
     * @param array<string,object> $columns Export table columns.
     * @return void
     */
    private function delete_export_fileitem_files(\stdClass $record, array $columns): void {
        if (!$this->has_column($columns, 'fileitemid')) {
            return;
        }

        $contextid = (int)($record->contextid ?? 0);
        $fileitemid = (int)($record->fileitemid ?? 0);
        $exportid = (int)($record->id ?? 0);

        if ($contextid <= 0 || $fileitemid <= 0 || $fileitemid === $exportid) {
            return;
        }

        $fs = get_file_storage();

        foreach ($this->get_export_fileareas() as $filearea) {
            $fs->delete_area_files($contextid, self::COMPONENT, $filearea, $fileitemid);
        }
    }

    /**
     * Return export file areas managed by this task.
     *
     * @return string[]
     */
    private function get_export_fileareas(): array {
        return [
            self::FILEAREA_EXPORT_PACKAGE,
            self::FILEAREA_EXPORT_MANIFEST,
            self::FILEAREA_INTEGRITY_EXPORTS,
        ];
    }

    /**
     * Return the timestamp field used for retention cutoff.
     *
     * @param array<string,object> $columns Export table columns.
     * @return string|null
     */
    private function get_retention_time_field(array $columns): ?string {
        foreach (['timecompleted', 'timemodified', 'timecreated'] as $field) {
            if ($this->has_column($columns, $field)) {
                return $field;
            }
        }

        return null;
    }

    /**
     * Return positive integer plugin config.
     *
     * @param string $name Config name.
     * @param int $default Default value.
     * @return int
     */
    private function get_positive_config_int(string $name, int $default): int {
        $value = get_config(self::COMPONENT, $name);

        if ($value === false || $value === null || $value === '') {
            return $default;
        }

        $value = (int)$value;

        return $value > 0 ? $value : $default;
    }

    /**
     * Return whether table exists.
     *
     * @param string $table Table name without braces.
     * @return bool
     */
    private function table_exists(string $table): bool {
        global $DB;

        return $DB->get_manager()->table_exists(new \xmldb_table($table));
    }

    /**
     * Return whether a column exists.
     *
     * @param array<string,object> $columns Column map.
     * @param string $field Field name.
     * @return bool
     */
    private function has_column(array $columns, string $field): bool {
        return array_key_exists($field, $columns);
    }
}