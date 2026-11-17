<?php
// This file is part of Moodle - https://moodle.org/.
//
// Moodle is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// any later version.

/**
 * Scheduled task for rebuilding the media search index.
 *
 * @package    mod_uckkarchive
 * @copyright  2026 Univers-Cité King Klown
 * @license    https://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later
 */

declare(strict_types=1);

namespace mod_uckkarchive\task;

defined('MOODLE_INTERNAL') || die();

use core\lock\lock_config;
use core\task\scheduled_task;
use stdClass;

/**
 * Rebuild the denormalised media search index.
 *
 * This task is deliberately mechanical. It may rebuild search text and
 * denormalised index rows, but it must not:
 *
 * - change media ownership;
 * - change media visibility;
 * - approve or reject content advisories;
 * - expose restricted cultural material;
 * - validate archive truth claims;
 * - generate files or derivatives;
 * - modify grades, assemblies, challenges, or integrity cases.
 *
 * The search index is an optimisation only. Permission checks remain in
 * `media_policy`, `content_policy`, pluginfile callbacks, external services,
 * and controllers.
 */
final class rebuild_media_search extends scheduled_task {
    /** Plugin component. */
    private const COMPONENT = 'mod_uckkarchive';

    /** Lock name. */
    private const LOCK_NAME = 'rebuild_media_search';

    /** Lock timeout in seconds. */
    private const LOCK_TIMEOUT = 5;

    /** Default batch size. */
    private const DEFAULT_BATCH_SIZE = 250;

    /** Maximum batch size. */
    private const MAX_BATCH_SIZE = 1000;

    /** Media table. */
    private const TABLE_MEDIA = 'uckkarchive_media';

    /** Optional denormalised search index table. */
    private const TABLE_MEDIA_SEARCH = 'uckkarchive_media_search';

    /** Media tag table. */
    private const TABLE_MEDIA_TAG = 'uckkarchive_media_tag';

    /** Content marker table. */
    private const TABLE_CONTENT_MARKER = 'uckkarchive_content_marker';

    /** Content tag table. */
    private const TABLE_CONTENT_TAG = 'uckkarchive_content_tag';

    /** Media relation table. */
    private const TABLE_MEDIA_RELATION = 'uckkarchive_media_relation';

    /** External work table. */
    private const TABLE_EXTERNAL_WORK = 'uckkarchive_external_work';

    /** Media collection item table. */
    private const TABLE_COLLECTION_ITEM = 'uckkarchive_media_collection_item';

    /** Media collection table. */
    private const TABLE_COLLECTION = 'uckkarchive_media_collection';

    /**
     * Return task name.
     *
     * @return string
     */
    public function get_name(): string {
        return get_string('task_rebuild_media_search', 'uckkarchive');
    }

    /**
     * Execute task.
     *
     * @return void
     */
    public function execute(): void {
        global $DB;

        if (!$this->table_exists(self::TABLE_MEDIA)) {
            mtrace('mod_uckkarchive: table {' . self::TABLE_MEDIA . '} does not exist; media search rebuild skipped.');
            return;
        }

        $target = $this->detect_index_target();
        if ($target === null) {
            mtrace('mod_uckkarchive: no media search index target found; media search rebuild skipped.');
            return;
        }

        $lockfactory = lock_config::get_lock_factory(self::COMPONENT);
        $lock = $lockfactory->get_lock(self::LOCK_NAME, self::LOCK_TIMEOUT);

        if (!$lock) {
            mtrace('mod_uckkarchive: media search rebuild already running; skipped.');
            return;
        }

        try {
            $batchsize = $this->get_batch_size();
            $processed = 0;
            $indexed = 0;
            $offset = 0;

            mtrace('mod_uckkarchive: rebuilding media search index.');

            if ($target === self::TABLE_MEDIA_SEARCH) {
                $DB->delete_records(self::TABLE_MEDIA_SEARCH);
            }

            while (true) {
                $records = $this->get_media_batch($offset, $batchsize);
                if (empty($records)) {
                    break;
                }

                foreach ($records as $media) {
                    $processed++;
                    $this->rebuild_one_media_record($media, $target);
                    $indexed++;
                }

                $offset += $batchsize;
            }

            mtrace('mod_uckkarchive: media search rebuild complete. Processed ' . $processed . ' media records; indexed ' . $indexed . '.');
        } finally {
            $lock->release();
        }
    }

    /**
     * Detect where search data should be written.
     *
     * Preferred target:
     *
     * - `{uckkarchive_media_search}` if present.
     *
     * Fallback target:
     *
     * - `{uckkarchive_media}` if it contains a writable search column.
     *
     * @return string|null
     */
    private function detect_index_target(): ?string {
        if ($this->table_exists(self::TABLE_MEDIA_SEARCH)) {
            return self::TABLE_MEDIA_SEARCH;
        }

        $mediacolumns = $this->columns(self::TABLE_MEDIA);
        foreach ($this->media_search_columns() as $column) {
            if (array_key_exists($column, $mediacolumns)) {
                return self::TABLE_MEDIA;
            }
        }

        return null;
    }

    /**
     * Rebuild one media record search entry.
     *
     * @param stdClass $media Media record.
     * @param string $target Target table.
     * @return void
     */
    private function rebuild_one_media_record(stdClass $media, string $target): void {
        if ($target === self::TABLE_MEDIA_SEARCH) {
            $this->write_search_index_row($media);
            return;
        }

        $this->update_media_search_columns($media);
    }

    /**
     * Insert one row into the optional media search table.
     *
     * @param stdClass $media Media record.
     * @return void
     */
    private function write_search_index_row(stdClass $media): void {
        global $DB;

        $columns = $this->columns(self::TABLE_MEDIA_SEARCH);
        $entry = $this->build_index_entry($media);
        $record = new stdClass();

        foreach ($entry as $field => $value) {
            if (array_key_exists($field, $columns)) {
                $record->{$field} = $value;
            }
        }

        if (array_key_exists('timecreated', $columns) && empty($record->timecreated)) {
            $record->timecreated = time();
        }

        if (array_key_exists('timemodified', $columns) && empty($record->timemodified)) {
            $record->timemodified = time();
        }

        if (count((array)$record) === 0) {
            return;
        }

        $DB->insert_record(self::TABLE_MEDIA_SEARCH, $record);
    }

    /**
     * Update search columns directly on the media table.
     *
     * @param stdClass $media Media record.
     * @return void
     */
    private function update_media_search_columns(stdClass $media): void {
        global $DB;

        $columns = $this->columns(self::TABLE_MEDIA);
        $entry = $this->build_index_entry($media);
        $record = new stdClass();
        $record->id = (int)$media->id;

        foreach ($this->media_search_columns() as $field) {
            if (array_key_exists($field, $columns) && array_key_exists($field, $entry)) {
                $record->{$field} = $entry[$field];
            }
        }

        if (array_key_exists('searchtext', $columns)) {
            $record->searchtext = $entry['searchtext'];
        }

        if (array_key_exists('searchindex', $columns)) {
            $record->searchindex = $entry['searchtext'];
        }

        if (array_key_exists('normalizedsearch', $columns)) {
            $record->normalizedsearch = $entry['normalizedtext'];
        }

        if (array_key_exists('searchhash', $columns)) {
            $record->searchhash = $entry['searchhash'];
        }

        if (array_key_exists('timeindexed', $columns)) {
            $record->timeindexed = time();
        }

        if (array_key_exists('timemodified', $columns)) {
            $record->timemodified = time();
        }

        if (count((array)$record) > 1) {
            $DB->update_record(self::TABLE_MEDIA, $record);
        }
    }

    /**
     * Build a denormalised index entry for one media record.
     *
     * @param stdClass $media Media record.
     * @return array<string, mixed>
     */
    private function build_index_entry(stdClass $media): array {
        $mediaid = (int)$media->id;

        $title = $this->field($media, ['title', 'name'], '');
        $summary = $this->field($media, ['summary', 'publicsummary'], '');
        $description = $this->field($media, ['description', 'body', 'notes'], '');
        $caption = $this->field($media, ['caption'], '');
        $alttext = $this->field($media, ['alttext', 'alt'], '');
        $language = $this->field($media, ['language', 'lang'], '');
        $mimetype = $this->field($media, ['mimetype', 'mime'], '');
        $mediatype = $this->field($media, ['mediatype', 'type'], '');
        $status = $this->field($media, ['status'], '');
        $visibility = $this->field($media, ['visibility'], '');
        $audiencesuitability = $this->field($media, ['audiencesuitability'], '');
        $source = $this->field($media, ['source', 'sourcetype'], '');

        $tagtext = $this->load_media_tag_text($mediaid);
        $contenttagtext = $this->load_content_marker_text($mediaid);
        $externalworktext = $this->load_external_work_text($mediaid);
        $collectiontext = $this->load_collection_text($mediaid);

        $rawtext = implode(' ', array_filter([
            $title,
            $summary,
            $description,
            $caption,
            $alttext,
            $language,
            $mimetype,
            $mediatype,
            $status,
            $visibility,
            $audiencesuitability,
            $source,
            $tagtext,
            $contenttagtext,
            $externalworktext,
            $collectiontext,
            $this->decode_metadata_text($this->field($media, ['metadata'], '')),
        ]));

        $searchtext = $this->normalise_search_text($rawtext);
        $normalizedtext = $this->normalise_machine_text($searchtext);
        $now = time();

        return [
            'mediaid' => $mediaid,
            'archiveid' => (int)$this->field($media, ['archiveid', 'uckkarchiveid'], 0),
            'courseid' => (int)$this->field($media, ['courseid'], 0),
            'cmid' => (int)$this->field($media, ['cmid'], 0),
            'contextid' => (int)$this->field($media, ['contextid'], 0),
            'uuid' => (string)$this->field($media, ['uuid'], ''),
            'title' => (string)$title,
            'mediatype' => (string)$mediatype,
            'mimetype' => (string)$mimetype,
            'status' => (string)$status,
            'visibility' => (string)$visibility,
            'audiencesuitability' => (string)$audiencesuitability,
            'source' => (string)$source,
            'tagtext' => $tagtext,
            'contenttagtext' => $contenttagtext,
            'externalworktext' => $externalworktext,
            'collectiontext' => $collectiontext,
            'searchtext' => $searchtext,
            'normalizedtext' => $normalizedtext,
            'normalizedsearch' => $normalizedtext,
            'searchindex' => $searchtext,
            'searchhash' => hash('sha256', $normalizedtext),
            'timeindexed' => $now,
            'timecreated' => $now,
            'timemodified' => $now,
        ];
    }

    /**
     * Return media batch.
     *
     * @param int $offset Offset.
     * @param int $limit Limit.
     * @return stdClass[]
     */
    private function get_media_batch(int $offset, int $limit): array {
        global $DB;

        return array_values($DB->get_records(
            self::TABLE_MEDIA,
            null,
            'id ASC',
            '*',
            $offset,
            $limit
        ));
    }

    /**
     * Load media tag text.
     *
     * @param int $mediaid Media id.
     * @return string
     */
    private function load_media_tag_text(int $mediaid): string {
        global $DB;

        if (!$this->table_exists(self::TABLE_MEDIA_TAG)) {
            return '';
        }

        $columns = $this->columns(self::TABLE_MEDIA_TAG);
        $mediafield = $this->first_column($columns, ['mediaid', 'itemid']);
        if ($mediafield === null) {
            return '';
        }

        $fields = array_values(array_filter([
            $this->first_column($columns, ['tag']),
            $this->first_column($columns, ['tagkey']),
            $this->first_column($columns, ['name']),
            $this->first_column($columns, ['rawname']),
            $this->first_column($columns, ['description']),
        ]));

        return $this->load_text_from_table(self::TABLE_MEDIA_TAG, $mediafield, $mediaid, $fields);
    }

    /**
     * Load content marker/advisory text.
     *
     * @param int $mediaid Media id.
     * @return string
     */
    private function load_content_marker_text(int $mediaid): string {
        global $DB;

        if (!$this->table_exists(self::TABLE_CONTENT_MARKER)) {
            return '';
        }

        $columns = $this->columns(self::TABLE_CONTENT_MARKER);
        $mediafield = $this->first_column($columns, ['mediaid']);
        if ($mediafield === null) {
            return '';
        }

        $fields = array_values(array_filter([
            $this->first_column($columns, ['tag']),
            $this->first_column($columns, ['tagkey']),
            $this->first_column($columns, ['contenttag']),
            $this->first_column($columns, ['advisorytag']),
            $this->first_column($columns, ['severity']),
            $this->first_column($columns, ['audiencesuitability']),
            $this->first_column($columns, ['locatortype']),
            $this->first_column($columns, ['locator']),
            $this->first_column($columns, ['note']),
            $this->first_column($columns, ['description']),
        ]));

        $text = $this->load_text_from_table(self::TABLE_CONTENT_MARKER, $mediafield, $mediaid, $fields);

        if ($this->table_exists(self::TABLE_CONTENT_TAG)) {
            $text .= ' ' . $this->load_content_tag_lookup_text($mediaid);
        }

        return trim($text);
    }

    /**
     * Load content tag lookup text where marker tag ids are used.
     *
     * @param int $mediaid Media id.
     * @return string
     */
    private function load_content_tag_lookup_text(int $mediaid): string {
        global $DB;

        $markercolumns = $this->columns(self::TABLE_CONTENT_MARKER);
        $tagcolumns = $this->columns(self::TABLE_CONTENT_TAG);

        $mediafield = $this->first_column($markercolumns, ['mediaid']);
        $tagidfield = $this->first_column($markercolumns, ['tagid', 'contenttagid']);
        if ($mediafield === null || $tagidfield === null) {
            return '';
        }

        $tagprimary = $this->first_column($tagcolumns, ['id']);
        if ($tagprimary === null) {
            return '';
        }

        $fields = array_values(array_filter([
            $this->first_column($tagcolumns, ['tag']),
            $this->first_column($tagcolumns, ['tagkey']),
            $this->first_column($tagcolumns, ['name']),
            $this->first_column($tagcolumns, ['label']),
            $this->first_column($tagcolumns, ['description']),
        ]));

        if (empty($fields)) {
            return '';
        }

        $selects = [];
        foreach ($fields as $field) {
            $selects[] = 'ct.' . $field;
        }

        $sql = 'SELECT ' . implode(', ', $selects) . '
                  FROM {' . self::TABLE_CONTENT_MARKER . '} cm
                  JOIN {' . self::TABLE_CONTENT_TAG . '} ct ON ct.' . $tagprimary . ' = cm.' . $tagidfield . '
                 WHERE cm.' . $mediafield . ' = :mediaid';

        $records = $DB->get_records_sql($sql, ['mediaid' => $mediaid]);

        return $this->records_to_text($records, $fields);
    }

    /**
     * Load external work text through media relation records.
     *
     * @param int $mediaid Media id.
     * @return string
     */
    private function load_external_work_text(int $mediaid): string {
        global $DB;

        if (!$this->table_exists(self::TABLE_MEDIA_RELATION) || !$this->table_exists(self::TABLE_EXTERNAL_WORK)) {
            return '';
        }

        $relationcolumns = $this->columns(self::TABLE_MEDIA_RELATION);
        $workcolumns = $this->columns(self::TABLE_EXTERNAL_WORK);

        $sourcefield = $this->first_column($relationcolumns, ['mediaid', 'fromid', 'sourceid', 'sourcemediaid']);
        $targetfield = $this->first_column($relationcolumns, ['externalworkid', 'toid', 'targetid', 'targetworkid']);
        if ($sourcefield === null || $targetfield === null) {
            return '';
        }

        $workidfield = $this->first_column($workcolumns, ['id']);
        if ($workidfield === null) {
            return '';
        }

        $fields = array_values(array_filter([
            $this->first_column($workcolumns, ['title']),
            $this->first_column($workcolumns, ['subtitle']),
            $this->first_column($workcolumns, ['creator']),
            $this->first_column($workcolumns, ['publisher']),
            $this->first_column($workcolumns, ['identifier']),
            $this->first_column($workcolumns, ['citation']),
            $this->first_column($workcolumns, ['description']),
            $this->first_column($workcolumns, ['teachingnote']),
        ]));

        if (empty($fields)) {
            return '';
        }

        $selects = [];
        foreach ($fields as $field) {
            $selects[] = 'ew.' . $field;
        }

        $sql = 'SELECT ' . implode(', ', $selects) . '
                  FROM {' . self::TABLE_MEDIA_RELATION . '} mr
                  JOIN {' . self::TABLE_EXTERNAL_WORK . '} ew ON ew.' . $workidfield . ' = mr.' . $targetfield . '
                 WHERE mr.' . $sourcefield . ' = :mediaid';

        $records = $DB->get_records_sql($sql, ['mediaid' => $mediaid]);

        return $this->records_to_text($records, $fields);
    }

    /**
     * Load collection text for media memberships.
     *
     * @param int $mediaid Media id.
     * @return string
     */
    private function load_collection_text(int $mediaid): string {
        global $DB;

        if (!$this->table_exists(self::TABLE_COLLECTION_ITEM) || !$this->table_exists(self::TABLE_COLLECTION)) {
            return '';
        }

        $itemcolumns = $this->columns(self::TABLE_COLLECTION_ITEM);
        $collectioncolumns = $this->columns(self::TABLE_COLLECTION);

        $mediafield = $this->first_column($itemcolumns, ['mediaid', 'itemid']);
        $collectionfield = $this->first_column($itemcolumns, ['collectionid', 'mediacollectionid']);

        if ($mediafield === null || $collectionfield === null) {
            return '';
        }

        $collectionidfield = $this->first_column($collectioncolumns, ['id']);
        if ($collectionidfield === null) {
            return '';
        }

        $fields = array_values(array_filter([
            $this->first_column($collectioncolumns, ['title']),
            $this->first_column($collectioncolumns, ['name']),
            $this->first_column($collectioncolumns, ['summary']),
            $this->first_column($collectioncolumns, ['description']),
        ]));

        if (empty($fields)) {
            return '';
        }

        $selects = [];
        foreach ($fields as $field) {
            $selects[] = 'mc.' . $field;
        }

        $sql = 'SELECT ' . implode(', ', $selects) . '
                  FROM {' . self::TABLE_COLLECTION_ITEM . '} mci
                  JOIN {' . self::TABLE_COLLECTION . '} mc ON mc.' . $collectionidfield . ' = mci.' . $collectionfield . '
                 WHERE mci.' . $mediafield . ' = :mediaid';

        $records = $DB->get_records_sql($sql, ['mediaid' => $mediaid]);

        return $this->records_to_text($records, $fields);
    }

    /**
     * Load text from a table where a media id field matches.
     *
     * @param string $table Table.
     * @param string $mediafield Media id field.
     * @param int $mediaid Media id.
     * @param string[] $fields Text fields.
     * @return string
     */
    private function load_text_from_table(string $table, string $mediafield, int $mediaid, array $fields): string {
        global $DB;

        if (empty($fields)) {
            return '';
        }

        $selects = [];
        foreach ($fields as $field) {
            $selects[] = $field;
        }

        $sql = 'SELECT id, ' . implode(', ', $selects) . '
                  FROM {' . $table . '}
                 WHERE ' . $mediafield . ' = :mediaid';

        $records = $DB->get_records_sql($sql, ['mediaid' => $mediaid]);

        return $this->records_to_text($records, $fields);
    }

    /**
     * Convert records to text.
     *
     * @param stdClass[] $records Records.
     * @param string[] $fields Fields.
     * @return string
     */
    private function records_to_text(array $records, array $fields): string {
        $parts = [];

        foreach ($records as $record) {
            foreach ($fields as $field) {
                if (isset($record->{$field}) && trim((string)$record->{$field}) !== '') {
                    $parts[] = (string)$record->{$field};
                }
            }
        }

        return trim(implode(' ', $parts));
    }

    /**
     * Decode metadata JSON into searchable text.
     *
     * @param mixed $metadata Metadata value.
     * @return string
     */
    private function decode_metadata_text($metadata): string {
        if ($metadata === null || $metadata === '') {
            return '';
        }

        if (is_array($metadata)) {
            return $this->flatten_metadata($metadata);
        }

        if ($metadata instanceof stdClass) {
            return $this->flatten_metadata((array)$metadata);
        }

        $decoded = json_decode((string)$metadata, true);
        if (!is_array($decoded)) {
            return '';
        }

        return $this->flatten_metadata($decoded);
    }

    /**
     * Flatten metadata values into text.
     *
     * @param array<mixed> $metadata Metadata.
     * @return string
     */
    private function flatten_metadata(array $metadata): string {
        $parts = [];

        foreach ($metadata as $key => $value) {
            if (is_array($value)) {
                $parts[] = $this->flatten_metadata($value);
                continue;
            }

            if ($value instanceof stdClass) {
                $parts[] = $this->flatten_metadata((array)$value);
                continue;
            }

            if (is_scalar($value)) {
                $parts[] = (string)$key;
                $parts[] = (string)$value;
            }
        }

        return trim(implode(' ', $parts));
    }

    /**
     * Normalize display search text.
     *
     * @param string $text Text.
     * @return string
     */
    private function normalise_search_text(string $text): string {
        $text = html_to_text($text, 0, false);
        $text = preg_replace('/\s+/u', ' ', $text) ?? $text;
        $text = trim($text);

        if (\core_text::strlen($text) > 20000) {
            $text = \core_text::substr($text, 0, 20000);
        }

        return $text;
    }

    /**
     * Normalize machine search text.
     *
     * @param string $text Text.
     * @return string
     */
    private function normalise_machine_text(string $text): string {
        $text = \core_text::strtolower($text);
        $text = preg_replace('/[^\p{L}\p{N}_-]+/u', ' ', $text) ?? $text;
        $text = preg_replace('/\s+/u', ' ', $text) ?? $text;

        return trim($text);
    }

    /**
     * Return known possible search columns on media table.
     *
     * @return string[]
     */
    private function media_search_columns(): array {
        return [
            'searchtext',
            'searchindex',
            'normalizedsearch',
            'normalizedtext',
            'searchhash',
            'timeindexed',
        ];
    }

    /**
     * Return first existing column from candidates.
     *
     * @param array<string, object> $columns Table columns.
     * @param string[] $candidates Candidate column names.
     * @return string|null
     */
    private function first_column(array $columns, array $candidates): ?string {
        foreach ($candidates as $candidate) {
            if (array_key_exists($candidate, $columns)) {
                return $candidate;
            }
        }

        return null;
    }

    /**
     * Return field value from record.
     *
     * @param stdClass $record Record.
     * @param string[] $fields Candidate fields.
     * @param mixed $default Default value.
     * @return mixed
     */
    private function field(stdClass $record, array $fields, $default = null) {
        foreach ($fields as $field) {
            if (property_exists($record, $field) && $record->{$field} !== null && $record->{$field} !== '') {
                return $record->{$field};
            }
        }

        return $default;
    }

    /**
     * Return table columns.
     *
     * @param string $table Table name.
     * @return array<string, object>
     */
    private function columns(string $table): array {
        global $DB;

        return $DB->get_columns($table);
    }

    /**
     * Return whether a table exists.
     *
     * @param string $table Table name.
     * @return bool
     */
    private function table_exists(string $table): bool {
        global $DB;

        return $DB->get_manager()->table_exists(new \xmldb_table($table));
    }

    /**
     * Return batch size from config.
     *
     * @return int
     */
    private function get_batch_size(): int {
        $configured = (int)get_config(self::COMPONENT, 'media_search_rebuild_batchsize');

        if ($configured <= 0) {
            return self::DEFAULT_BATCH_SIZE;
        }

        return min(self::MAX_BATCH_SIZE, max(1, $configured));
    }
}

