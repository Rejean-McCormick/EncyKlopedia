<?php
// This file is part of Moodle - https://moodle.org/
//
// Moodle is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// any later version.

/**
 * Scheduled task that rebuilds the content marker locator/index metadata.
 *
 * @package    mod_uckkarchive
 * @copyright  2026 Univers-Cité King Klown
 * @license    https://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later
 */

declare(strict_types=1);

namespace mod_uckkarchive\task;

defined('MOODLE_INTERNAL') || die();

use core\task\scheduled_task;
use stdClass;

/**
 * Rebuild content marker and advisory locator index data.
 *
 * The task maintains derived search/locator metadata for content advisory
 * markers. It does not publish markers, does not relax visibility, does not
 * approve reviews, and does not bypass content advisory, cultural protocol, or
 * restricted integrity policy.
 *
 * If a dedicated index table or index columns are added later, this task will
 * write to them when present. In the current schema it safely stores a compact
 * internal index payload under the marker metadata key:
 *
 * ```text
 * metadata.content_marker_index
 * ```
 *
 * The payload deliberately avoids copying sensitive review rationale,
 * cultural protocol notes, or free-form advisory notes into uncontrolled
 * search text.
 */
final class rebuild_content_marker_index extends scheduled_task {
    /** Content marker table. */
    private const TABLE_MARKER = 'uckkarchive_content_marker';

    /** Content advisory tag table. */
    private const TABLE_TAG = 'uckkarchive_content_tag';

    /** Content review table. */
    private const TABLE_REVIEW = 'uckkarchive_content_review';

    /** Media table. */
    private const TABLE_MEDIA = 'uckkarchive_media';

    /** External work table. */
    private const TABLE_EXTERNAL_WORK = 'uckkarchive_external_work';

    /** Optional dedicated marker index table. */
    private const TABLE_INDEX = 'uckkarchive_content_marker_idx';

    /** Metadata key used when no dedicated index table exists. */
    private const METADATA_INDEX_KEY = 'content_marker_index';

    /** Default batch size. */
    private const BATCH_SIZE = 200;

    /**
     * Return scheduled task name.
     *
     * @return string
     */
    public function get_name(): string {
        $manager = get_string_manager();

        if ($manager->string_exists('task:rebuildcontentmarkerindex', 'uckkarchive')) {
            return get_string('task:rebuildcontentmarkerindex', 'uckkarchive');
        }

        if ($manager->string_exists('rebuildcontentmarkerindex', 'uckkarchive')) {
            return get_string('rebuildcontentmarkerindex', 'uckkarchive');
        }

        return 'Rebuild content marker index';
    }

    /**
     * Execute task.
     *
     * @return void
     */
    public function execute(): void {
        global $DB;

        if (!self::table_exists(self::TABLE_MARKER)) {
            mtrace('mod_uckkarchive: content marker table not found; skipping content marker index rebuild.');
            return;
        }

        $markercolumns = $DB->get_columns(self::TABLE_MARKER);

        if (!array_key_exists('metadata', $markercolumns) &&
                !self::has_marker_index_columns($markercolumns) &&
                !self::table_exists(self::TABLE_INDEX)) {
            mtrace('mod_uckkarchive: no marker index storage available; skipping content marker index rebuild.');
            return;
        }

        $processed = 0;
        $updated = 0;
        $skipped = 0;
        $failed = 0;
        $lastid = 0;

        do {
            $records = $DB->get_records_select(
                self::TABLE_MARKER,
                'id > :lastid',
                ['lastid' => $lastid],
                'id ASC',
                '*',
                0,
                self::BATCH_SIZE
            );

            foreach ($records as $marker) {
                $processed++;
                $lastid = (int)$marker->id;

                try {
                    $index = self::build_index_payload($marker);
                    $changed = false;

                    if (self::table_exists(self::TABLE_INDEX)) {
                        $changed = self::upsert_index_record($marker, $index) || $changed;
                    }

                    if (self::has_marker_index_columns($markercolumns)) {
                        $changed = self::update_marker_index_columns($marker, $index, $markercolumns) || $changed;
                    }

                    if (array_key_exists('metadata', $markercolumns)) {
                        $changed = self::update_marker_metadata_index($marker, $index) || $changed;
                    }

                    if ($changed) {
                        $updated++;
                    } else {
                        $skipped++;
                    }
                } catch (\Throwable $exception) {
                    $failed++;
                    mtrace(
                        'mod_uckkarchive: failed to rebuild content marker index for marker ' .
                        (int)$marker->id . ': ' . $exception->getMessage()
                    );
                }
            }
        } while (!empty($records));

        mtrace(
            'mod_uckkarchive: content marker index rebuild complete. ' .
            'processed=' . $processed . ', updated=' . $updated .
            ', unchanged=' . $skipped . ', failed=' . $failed . '.'
        );
    }

    /**
     * Build derived index payload for one content marker.
     *
     * @param stdClass $marker Marker record.
     * @return array<string, mixed>
     */
    private static function build_index_payload(stdClass $marker): array {
        $targettype = (string)self::field($marker, ['targettype'], 'manual_reference');
        $targetid = (int)self::field($marker, ['targetid'], 0);
        $tagkey = (string)self::field($marker, ['tagkey'], '');
        $tag = self::load_tag_summary((int)self::field($marker, ['tagid'], 0), $tagkey);
        $review = self::load_latest_review_summary((int)$marker->id);

        $visibility = (string)self::field($marker, ['visibility'], 'course');
        $audience = (string)self::field($marker, ['audiencesuitability'], 'guided');
        $severity = (string)self::field($marker, ['severity'], 'notice');
        $reviewstate = (string)self::field($marker, ['reviewstate'], 'draft');

        $restricted = self::is_restricted($visibility, $audience, $severity);
        $cultural = self::is_cultural_restricted($visibility, $audience, $tag);

        $locator = [
            'type' => (string)self::field($marker, ['locatortype'], 'manual_reference'),
            'value' => (string)self::field($marker, ['locatorvalue'], ''),
            'start' => (string)self::field($marker, ['locatorstart'], ''),
            'end' => (string)self::field($marker, ['locatorend'], ''),
            'sort' => (int)self::field($marker, ['locatorsort'], 0),
        ];

        $target = self::load_target_summary($targettype, $targetid, $restricted || $cultural);

        $searchtokens = self::normalise_search_tokens([
            $targettype,
            $tagkey,
            $tag['name'] ?? '',
            $tag['category'] ?? '',
            $locator['type'],
            $locator['value'],
            $locator['start'],
            $locator['end'],
            $severity,
            $visibility,
            $audience,
            $reviewstate,
            $restricted ? 'restricted' : '',
            $cultural ? 'cultural_protocol' : '',
        ]);

        $payload = [
            'markerid' => (int)$marker->id,
            'markeruuid' => (string)self::field($marker, ['uuid'], ''),
            'archiveid' => (int)self::field($marker, ['archiveid'], 0),
            'courseid' => (int)self::field($marker, ['courseid'], 0),
            'cmid' => (int)self::field($marker, ['cmid'], 0),
            'contextid' => (int)self::field($marker, ['contextid'], 0),
            'target' => [
                'type' => $targettype,
                'id' => $targetid,
                'uuid' => (string)self::field($marker, ['targetuuid'], ''),
                'summary' => $target,
            ],
            'tag' => $tag,
            'locator' => $locator,
            'severity' => $severity,
            'visibility' => $visibility,
            'audiencesuitability' => $audience,
            'review' => [
                'state' => $review['state'] ?? $reviewstate,
                'latestreviewid' => $review['id'] ?? 0,
                'reviewedby' => (int)self::field($marker, ['reviewedby'], 0),
                'timereviewed' => (int)self::field($marker, ['timereviewed'], 0),
            ],
            'restriction' => [
                'restricted' => $restricted,
                'culturalprotocol' => $cultural,
                'integrityrestricted' => self::is_integrity_restricted($visibility, $audience),
                'redactionrequired' => $restricted || $cultural,
            ],
            'searchtokens' => $searchtokens,
            'searchtext' => implode(' ', $searchtokens),
            'hash' => '',
            'timeindexed' => time(),
        ];

        $payload['hash'] = self::hash_payload($payload);

        return $payload;
    }

    /**
     * Update optional index columns on marker table.
     *
     * @param stdClass $marker Marker record.
     * @param array<string, mixed> $index Index payload.
     * @param array<string, object> $columns Marker columns.
     * @return bool
     */
    private static function update_marker_index_columns(stdClass $marker, array $index, array $columns): bool {
        global $DB;

        $update = new stdClass();
        $update->id = (int)$marker->id;

        $changed = false;

        foreach ([
            'indextext' => $index['searchtext'],
            'searchtext' => $index['searchtext'],
            'indexjson' => self::encode_json($index),
            'indexhash' => $index['hash'],
            'contentindexhash' => $index['hash'],
            'timeindexed' => $index['timeindexed'],
            'indexedtime' => $index['timeindexed'],
        ] as $field => $value) {
            if (!array_key_exists($field, $columns)) {
                continue;
            }

            $current = $marker->{$field} ?? null;
            if ((string)$current !== (string)$value) {
                $update->{$field} = $value;
                $changed = true;
            }
        }

        if (array_key_exists('indexdirty', $columns)) {
            $update->indexdirty = 0;
            $changed = true;
        }

        if (array_key_exists('timemodified', $columns)) {
            $update->timemodified = time();
        }

        if (!$changed) {
            return false;
        }

        $DB->update_record(self::TABLE_MARKER, $update);

        return true;
    }

    /**
     * Update marker metadata with compact internal index payload.
     *
     * @param stdClass $marker Marker record.
     * @param array<string, mixed> $index Index payload.
     * @return bool
     */
    private static function update_marker_metadata_index(stdClass $marker, array $index): bool {
        global $DB;

        $metadata = self::decode_metadata($marker->metadata ?? null);
        $oldhash = $metadata[self::METADATA_INDEX_KEY]['hash'] ?? '';

        if ($oldhash === $index['hash']) {
            return false;
        }

        $metadata[self::METADATA_INDEX_KEY] = $index;

        $update = new stdClass();
        $update->id = (int)$marker->id;
        $update->metadata = self::encode_json($metadata);

        $columns = $DB->get_columns(self::TABLE_MARKER);
        if (array_key_exists('timemodified', $columns)) {
            $update->timemodified = time();
        }

        $DB->update_record(self::TABLE_MARKER, $update);

        return true;
    }

    /**
     * Upsert optional dedicated content marker index table record.
     *
     * @param stdClass $marker Marker record.
     * @param array<string, mixed> $index Index payload.
     * @return bool
     */
    private static function upsert_index_record(stdClass $marker, array $index): bool {
        global $DB;

        if (!self::table_exists(self::TABLE_INDEX)) {
            return false;
        }

        $columns = $DB->get_columns(self::TABLE_INDEX);
        $existing = null;

        if (array_key_exists('markerid', $columns)) {
            $existing = $DB->get_record(self::TABLE_INDEX, ['markerid' => (int)$marker->id], '*', IGNORE_MISSING);
        }

        $record = new stdClass();

        if ($existing) {
            $record->id = (int)$existing->id;
        }

        $values = [
            'markerid' => (int)$marker->id,
            'archiveid' => (int)$index['archiveid'],
            'courseid' => (int)$index['courseid'],
            'cmid' => (int)$index['cmid'],
            'contextid' => (int)$index['contextid'],
            'targettype' => (string)$index['target']['type'],
            'targetid' => (int)$index['target']['id'],
            'targetuuid' => (string)$index['target']['uuid'],
            'tagkey' => (string)($index['tag']['key'] ?? ''),
            'locatortype' => (string)$index['locator']['type'],
            'locatorvalue' => (string)$index['locator']['value'],
            'locatorstart' => (string)$index['locator']['start'],
            'locatorend' => (string)$index['locator']['end'],
            'locatorsort' => (int)$index['locator']['sort'],
            'severity' => (string)$index['severity'],
            'visibility' => (string)$index['visibility'],
            'audiencesuitability' => (string)$index['audiencesuitability'],
            'reviewstate' => (string)($index['review']['state'] ?? ''),
            'restricted' => !empty($index['restriction']['restricted']) ? 1 : 0,
            'culturalprotocol' => !empty($index['restriction']['culturalprotocol']) ? 1 : 0,
            'searchtext' => (string)$index['searchtext'],
            'indexjson' => self::encode_json($index),
            'indexhash' => (string)$index['hash'],
            'timeindexed' => (int)$index['timeindexed'],
            'timemodified' => time(),
        ];

        $changed = !$existing;

        foreach ($values as $field => $value) {
            if (!array_key_exists($field, $columns)) {
                continue;
            }

            if (!$existing || (string)($existing->{$field} ?? '') !== (string)$value) {
                $record->{$field} = $value;
                $changed = true;
            }
        }

        if (!$changed) {
            return false;
        }

        if ($existing) {
            $DB->update_record(self::TABLE_INDEX, $record);
        } else {
            if (array_key_exists('timecreated', $columns)) {
                $record->timecreated = time();
            }
            $DB->insert_record(self::TABLE_INDEX, $record);
        }

        return true;
    }

    /**
     * Return whether marker table has any explicit index columns.
     *
     * @param array<string, object> $columns Marker table columns.
     * @return bool
     */
    private static function has_marker_index_columns(array $columns): bool {
        foreach ([
            'indextext',
            'searchtext',
            'indexjson',
            'indexhash',
            'contentindexhash',
            'timeindexed',
            'indexedtime',
            'indexdirty',
        ] as $field) {
            if (array_key_exists($field, $columns)) {
                return true;
            }
        }

        return false;
    }

    /**
     * Load advisory tag summary.
     *
     * @param int $tagid Tag id.
     * @param string $fallbackkey Fallback tag key.
     * @return array<string, mixed>
     */
    private static function load_tag_summary(int $tagid, string $fallbackkey): array {
        global $DB;

        $summary = [
            'id' => $tagid,
            'key' => $fallbackkey,
            'name' => '',
            'category' => '',
            'severity' => '',
            'audiencesuitability' => '',
            'restricteddefault' => false,
            'culturalprotocol' => false,
        ];

        if ($tagid <= 0 || !self::table_exists(self::TABLE_TAG)) {
            return $summary;
        }

        $tag = $DB->get_record(self::TABLE_TAG, ['id' => $tagid], '*', IGNORE_MISSING);
        if (!$tag) {
            return $summary;
        }

        $summary['key'] = (string)self::field($tag, ['tagkey', 'key', 'shortname'], $fallbackkey);
        $summary['name'] = (string)self::field($tag, ['name', 'title', 'label'], '');
        $summary['category'] = (string)self::field($tag, ['category'], '');
        $summary['severity'] = (string)self::field($tag, ['severity'], '');
        $summary['audiencesuitability'] = (string)self::field($tag, ['audiencesuitability'], '');
        $summary['restricteddefault'] = !empty($tag->restricteddefault) || !empty($tag->restrictsbydefault);
        $summary['culturalprotocol'] = (string)$summary['category'] === 'cultural_protocol' ||
            !empty($tag->culturalprotocol);

        return $summary;
    }

    /**
     * Load latest review summary.
     *
     * @param int $markerid Marker id.
     * @return array<string, mixed>
     */
    private static function load_latest_review_summary(int $markerid): array {
        global $DB;

        if ($markerid <= 0 || !self::table_exists(self::TABLE_REVIEW)) {
            return [];
        }

        $columns = $DB->get_columns(self::TABLE_REVIEW);
        if (!array_key_exists('markerid', $columns)) {
            return [];
        }

        $records = $DB->get_records(
            self::TABLE_REVIEW,
            ['markerid' => $markerid],
            self::review_sort_sql($columns),
            '*',
            0,
            1
        );

        $review = reset($records);
        if (!$review) {
            return [];
        }

        return [
            'id' => (int)$review->id,
            'state' => (string)self::field($review, ['state', 'reviewstate'], ''),
            'reviewerid' => (int)self::field($review, ['reviewerid', 'reviewedby'], 0),
            'timemodified' => (int)self::field($review, ['timemodified', 'timecreated'], 0),
        ];
    }

    /**
     * Build a safe target summary.
     *
     * @param string $targettype Target type.
     * @param int $targetid Target id.
     * @param bool $restricted Whether target details should be minimized.
     * @return array<string, mixed>
     */
    private static function load_target_summary(string $targettype, int $targetid, bool $restricted): array {
        if ($targetid <= 0) {
            return [
                'available' => false,
                'restricted' => $restricted,
            ];
        }

        if ($targettype === 'media') {
            return self::load_target_from_table(self::TABLE_MEDIA, $targetid, $restricted);
        }

        if ($targettype === 'external_work') {
            return self::load_target_from_table(self::TABLE_EXTERNAL_WORK, $targetid, $restricted);
        }

        return [
            'available' => true,
            'restricted' => $restricted,
        ];
    }

    /**
     * Build a safe target summary from a table.
     *
     * @param string $table Table name.
     * @param int $id Record id.
     * @param bool $restricted Whether details should be minimized.
     * @return array<string, mixed>
     */
    private static function load_target_from_table(string $table, int $id, bool $restricted): array {
        global $DB;

        if (!self::table_exists($table)) {
            return [
                'available' => false,
                'restricted' => $restricted,
            ];
        }

        $record = $DB->get_record($table, ['id' => $id], '*', IGNORE_MISSING);
        if (!$record) {
            return [
                'available' => false,
                'restricted' => $restricted,
            ];
        }

        $summary = [
            'available' => true,
            'id' => (int)$record->id,
            'uuid' => (string)self::field($record, ['uuid'], ''),
            'restricted' => $restricted,
            'visibility' => (string)self::field($record, ['visibility'], ''),
            'status' => (string)self::field($record, ['status'], ''),
        ];

        if (!$restricted) {
            $summary['title'] = (string)self::field($record, ['title', 'name'], '');
            $summary['type'] = (string)self::field($record, ['mediatype', 'worktype', 'type'], '');
        }

        return $summary;
    }

    /**
     * Return review sorting clause.
     *
     * @param array<string, object> $columns Review table columns.
     * @return string
     */
    private static function review_sort_sql(array $columns): string {
        if (array_key_exists('timemodified', $columns)) {
            return 'timemodified DESC, id DESC';
        }

        if (array_key_exists('timecreated', $columns)) {
            return 'timecreated DESC, id DESC';
        }

        return 'id DESC';
    }

    /**
     * Return whether marker/target should be treated as restricted.
     *
     * @param string $visibility Visibility.
     * @param string $audience Audience suitability.
     * @param string $severity Severity.
     * @return bool
     */
    private static function is_restricted(string $visibility, string $audience, string $severity): bool {
        return in_array($visibility, ['restricted', 'restricted_integrity', 'restricted_cultural'], true) ||
            in_array($audience, ['restricted', 'restricted_integrity', 'restricted_cultural', 'staff_only'], true) ||
            $severity === 'restricted';
    }

    /**
     * Return whether marker is cultural-protocol restricted.
     *
     * @param string $visibility Visibility.
     * @param string $audience Audience suitability.
     * @param array<string, mixed> $tag Tag summary.
     * @return bool
     */
    private static function is_cultural_restricted(string $visibility, string $audience, array $tag): bool {
        return $visibility === 'restricted_cultural' ||
            $audience === 'restricted_cultural' ||
            !empty($tag['culturalprotocol']);
    }

    /**
     * Return whether marker is integrity restricted.
     *
     * @param string $visibility Visibility.
     * @param string $audience Audience suitability.
     * @return bool
     */
    private static function is_integrity_restricted(string $visibility, string $audience): bool {
        return $visibility === 'restricted_integrity' || $audience === 'restricted_integrity';
    }

    /**
     * Normalize search tokens.
     *
     * @param array<int, mixed> $values Values.
     * @return string[]
     */
    private static function normalise_search_tokens(array $values): array {
        $tokens = [];

        foreach ($values as $value) {
            $value = trim((string)$value);
            if ($value === '') {
                continue;
            }

            $value = \core_text::strtolower($value);
            $value = preg_replace('/[^\pL\pN:_\-.]+/u', ' ', $value);
            $value = trim((string)$value);

            if ($value === '') {
                continue;
            }

            foreach (preg_split('/\s+/', $value, -1, PREG_SPLIT_NO_EMPTY) as $token) {
                $tokens[] = $token;
            }
        }

        return array_values(array_unique($tokens));
    }

    /**
     * Hash payload without the volatile hash field.
     *
     * @param array<string, mixed> $payload Payload.
     * @return string
     */
    private static function hash_payload(array $payload): string {
        unset($payload['hash']);
        return hash('sha256', self::encode_json($payload));
    }

    /**
     * Return one field from record.
     *
     * @param stdClass $record Record.
     * @param string[] $fields Candidate fields.
     * @param mixed $default Default value.
     * @return mixed
     */
    private static function field(stdClass $record, array $fields, mixed $default = null): mixed {
        foreach ($fields as $field) {
            if (property_exists($record, $field) && $record->{$field} !== null && $record->{$field} !== '') {
                return $record->{$field};
            }
        }

        return $default;
    }

    /**
     * Decode metadata safely.
     *
     * @param mixed $metadata Raw metadata.
     * @return array<string, mixed>
     */
    private static function decode_metadata(mixed $metadata): array {
        if (is_array($metadata)) {
            return $metadata;
        }

        if ($metadata instanceof stdClass) {
            return (array)$metadata;
        }

        if (is_string($metadata) && trim($metadata) !== '') {
            $decoded = json_decode($metadata, true);
            return is_array($decoded) ? $decoded : [];
        }

        return [];
    }

    /**
     * Encode JSON safely.
     *
     * @param mixed $data Data.
     * @return string
     */
    private static function encode_json(mixed $data): string {
        $json = json_encode($data, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
        return $json === false ? '{}' : $json;
    }

    /**
     * Return whether table exists.
     *
     * @param string $table Table name.
     * @return bool
     */
    private static function table_exists(string $table): bool {
        global $DB;

        return $DB->get_manager()->table_exists(new \xmldb_table($table));
    }
}

