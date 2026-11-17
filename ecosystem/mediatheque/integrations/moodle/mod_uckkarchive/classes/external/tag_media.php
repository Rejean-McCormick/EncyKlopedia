<?php
// This file is part of Moodle - https://moodle.org/
//
// Moodle is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// any later version.
//
// Moodle is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with Moodle. If not, see <https://www.gnu.org/licenses/>.

/**
 * Add ordinary media tags to a media record.
 *
 * @package    mod_uckkarchive
 * @copyright  2026 UCKK
 * @license    https://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later
 */

declare(strict_types=1);

namespace mod_uckkarchive\external;

defined('MOODLE_INTERNAL') || die();

global $CFG;
require_once($CFG->libdir . '/externallib.php');
require_once(dirname(__DIR__, 2) . '/locallib.php');

use context_module;
use core_external\external_api;
use core_external\external_function_parameters;
use core_external\external_multiple_structure;
use core_external\external_single_structure;
use core_external\external_value;
use dml_exception;
use invalid_parameter_exception;
use mod_uckkarchive\event\media_updated;
use mod_uckkarchive\local\media;
use mod_uckkarchive\local\media_policy;
use mod_uckkarchive\local\media_tag;
use moodle_exception;
use required_capability_exception;
use stdClass;

/**
 * External service for adding ordinary media-library tags.
 *
 * Target service name:
 *
 * ```text
 * mod_uckkarchive_tag_media
 * ```
 *
 * This service is for normal media classification only: topic, format,
 * language, region, course use, pedagogical theme, source category, and
 * review-state labels.
 *
 * Content advisories, cultural protocol tags, trigger/content warnings, and
 * sensitive access markers do not belong here. They must use the content
 * advisory subsystem instead.
 */
class tag_media extends external_api {

    /** @var string Media table. */
    private const MEDIA_TABLE = 'uckkarchive_media';

    /** @var string Media tag table. */
    private const TAG_TABLE = 'uckkarchive_media_tag';

    /** @var string Default tag type. */
    private const DEFAULT_TAGTYPE = 'topic';

    /** @var string Default tag source. */
    private const DEFAULT_SOURCE = 'human';

    /** @var int Maximum tags accepted in one request. */
    private const MAX_TAGS_PER_REQUEST = 100;

    /** @var string Restricted visibility. */
    private const VISIBILITY_RESTRICTED = 'restricted';

    /** @var string Restricted integrity visibility. */
    private const VISIBILITY_RESTRICTED_INTEGRITY = 'restricted_integrity';

    /** @var string Restricted cultural visibility. */
    private const VISIBILITY_RESTRICTED_CULTURAL = 'restricted_cultural';

    /**
     * Define service parameters.
     *
     * @return external_function_parameters
     */
    public static function execute_parameters(): external_function_parameters {
        return new external_function_parameters([
            'cmid' => new external_value(
                PARAM_INT,
                'Course module id for the uckkarchive activity.'
            ),
            'mediaid' => new external_value(
                PARAM_INT,
                'Media id to tag.'
            ),
            'tags' => new external_multiple_structure(
                new external_single_structure([
                    'tagkey' => new external_value(
                        PARAM_TEXT,
                        'Tag key or raw tag label. It will be normalized.'
                    ),
                    'label' => new external_value(
                        PARAM_TEXT,
                        'Human-readable label. Defaults to tagkey.',
                        VALUE_DEFAULT,
                        ''
                    ),
                    'tagtype' => new external_value(
                        PARAM_ALPHANUMEXT,
                        'Tag type: topic, format, course_use, language, region, pedagogical_theme, source_category, review_state.',
                        VALUE_DEFAULT,
                        self::DEFAULT_TAGTYPE
                    ),
                    'source' => new external_value(
                        PARAM_ALPHANUMEXT,
                        'Tag source: human, imported, system, ai_suggested.',
                        VALUE_DEFAULT,
                        self::DEFAULT_SOURCE
                    ),
                    'weight' => new external_value(
                        PARAM_INT,
                        'Tag weight or ordering hint.',
                        VALUE_DEFAULT,
                        0
                    ),
                    'metadata' => new external_single_structure([
                        'note' => new external_value(
                            PARAM_RAW,
                            'Optional note about why this tag was applied.',
                            VALUE_DEFAULT,
                            ''
                        ),
                        'context' => new external_value(
                            PARAM_TEXT,
                            'Optional tagging context.',
                            VALUE_DEFAULT,
                            ''
                        ),
                        'confidence' => new external_value(
                            PARAM_RAW,
                            'Optional confidence value, especially for imported or suggested tags.',
                            VALUE_DEFAULT,
                            ''
                        ),
                    ], 'Optional metadata.', VALUE_DEFAULT, []),
                ]),
                'Tags to add or update.'
            ),
            'upsert' => new external_value(
                PARAM_BOOL,
                'When true, existing matching tags are updated instead of causing a duplicate error.',
                VALUE_DEFAULT,
                true
            ),
        ]);
    }

    /**
     * Add or update media tags.
     *
     * @param int $cmid Course module id.
     * @param int $mediaid Media id.
     * @param array<int, array<string, mixed>> $tags Tags.
     * @param bool $upsert Whether to update existing tags.
     * @return array<string, mixed>
     * @throws dml_exception
     * @throws invalid_parameter_exception
     * @throws moodle_exception
     * @throws required_capability_exception
     */
    public static function execute(
        int $cmid,
        int $mediaid,
        array $tags,
        bool $upsert = true
    ): array {
        global $DB, $USER;

        $params = self::validate_parameters(self::execute_parameters(), [
            'cmid' => $cmid,
            'mediaid' => $mediaid,
            'tags' => $tags,
            'upsert' => $upsert,
        ]);

        [$course, $cm, $archive, $context] = self::load_page((int)$params['cmid']);
        self::validate_context($context);

        $media = self::get_media_record((int)$params['mediaid']);
        self::assert_media_belongs_to_activity($media, $course, $cm, $archive, $context);
        self::require_can_tag_media($context, $media);

        if (empty($params['tags'])) {
            throw new invalid_parameter_exception('At least one tag is required.');
        }

        if (count($params['tags']) > self::MAX_TAGS_PER_REQUEST) {
            throw new invalid_parameter_exception('Too many tags in one request.');
        }

        if (!self::table_exists(self::TAG_TABLE)) {
            throw new moodle_exception('missingmediatagtable', 'mod_uckkarchive');
        }

        $created = [];
        $updated = [];
        $warnings = [];

        $transaction = $DB->start_delegated_transaction();

        foreach ((array)$params['tags'] as $tagdata) {
            $tagdata = self::normalise_tag_input((array)$tagdata);

            if ($tagdata['tagkey'] === '') {
                $warnings[] = self::warning(
                    'media_tag',
                    0,
                    'emptytagignored',
                    'An empty tag was ignored.'
                );
                continue;
            }

            if (self::is_content_advisory_tag($tagdata['tagkey'])) {
                throw new invalid_parameter_exception(
                    'Content advisory or cultural protocol tags must be created with content advisory services.'
                );
            }

            $existing = self::get_existing_tag(
                (int)$media->id,
                $tagdata['tagkey'],
                $tagdata['tagtype']
            );

            if ($existing && empty($params['upsert'])) {
                throw new invalid_parameter_exception(
                    'Duplicate media tag for media object: ' . $tagdata['tagkey']
                );
            }

            $record = self::save_tag((int)$media->id, $tagdata, !empty($params['upsert']), (int)$USER->id);

            if ($existing) {
                $updated[] = $record;
            } else {
                $created[] = $record;
            }
        }

        self::touch_media($media, (int)$USER->id);
        self::trigger_media_tagged_event($context, $media, count($created), count($updated));

        $transaction->allow_commit();

        $alltags = array_merge($created, $updated);

        return [
            'success' => true,
            'mediaid' => (int)$media->id,
            'createdcount' => count($created),
            'updatedcount' => count($updated),
            'tags' => self::export_tags($alltags, true),
            'warnings' => $warnings,
        ];
    }

    /**
     * Define service returns.
     *
     * @return external_single_structure
     */
    public static function execute_returns(): external_single_structure {
        return new external_single_structure([
            'success' => new external_value(PARAM_BOOL, 'Whether the operation succeeded.'),
            'mediaid' => new external_value(PARAM_INT, 'Media id.'),
            'createdcount' => new external_value(PARAM_INT, 'Number of created tags.'),
            'updatedcount' => new external_value(PARAM_INT, 'Number of updated tags.'),
            'tags' => new external_multiple_structure(
                self::tag_structure(),
                'Created or updated tag records.'
            ),
            'warnings' => self::warnings_structure(),
        ]);
    }

    /**
     * Return external tag structure.
     *
     * @return external_single_structure
     */
    private static function tag_structure(): external_single_structure {
        return new external_single_structure([
            'id' => new external_value(PARAM_INT, 'Tag id.'),
            'uuid' => new external_value(PARAM_RAW, 'Tag UUID.'),
            'mediaid' => new external_value(PARAM_INT, 'Media id.'),
            'tagkey' => new external_value(PARAM_ALPHANUMEXT, 'Normalized tag key.'),
            'label' => new external_value(PARAM_TEXT, 'Human-readable tag label.'),
            'tagtype' => new external_value(PARAM_ALPHANUMEXT, 'Tag type.'),
            'source' => new external_value(PARAM_ALPHANUMEXT, 'Tag source.'),
            'weight' => new external_value(PARAM_INT, 'Tag weight.'),
            'userid' => new external_value(PARAM_INT, 'User id that last applied the tag.'),
            'timecreated' => new external_value(PARAM_INT, 'Time created.'),
            'timemodified' => new external_value(PARAM_INT, 'Time modified.'),
            'metadata' => new external_single_structure([
                'note' => new external_value(PARAM_RAW, 'Tag note.', VALUE_DEFAULT, ''),
                'context' => new external_value(PARAM_TEXT, 'Tag context.', VALUE_DEFAULT, ''),
                'confidence' => new external_value(PARAM_RAW, 'Tag confidence.', VALUE_DEFAULT, ''),
            ], 'Tag metadata.', VALUE_DEFAULT, []),
        ]);
    }

    /**
     * Return warnings structure.
     *
     * @return external_multiple_structure
     */
    private static function warnings_structure(): external_multiple_structure {
        return new external_multiple_structure(
            new external_single_structure([
                'item' => new external_value(PARAM_TEXT, 'Warning item type.'),
                'itemid' => new external_value(PARAM_INT, 'Warning item id.'),
                'warningcode' => new external_value(PARAM_ALPHANUMEXT, 'Warning code.'),
                'message' => new external_value(PARAM_TEXT, 'Warning message.'),
            ]),
            'Warnings.',
            VALUE_DEFAULT,
            []
        );
    }

    /**
     * Load Moodle page objects.
     *
     * @param int $cmid Course module id.
     * @return array{0:stdClass,1:stdClass,2:stdClass,3:context_module}
     */
    private static function load_page(int $cmid): array {
        [$course, $cm, $archive, $context] = \uckkarchive_require_page($cmid, 0);
        return [$course, $cm, $archive, $context];
    }

    /**
     * Get a media record.
     *
     * @param int $mediaid Media id.
     * @return stdClass
     * @throws dml_exception
     * @throws invalid_parameter_exception
     * @throws moodle_exception
     */
    private static function get_media_record(int $mediaid): stdClass {
        global $DB;

        if ($mediaid <= 0) {
            throw new invalid_parameter_exception('Invalid media id.');
        }

        if (!$DB->get_manager()->table_exists(self::MEDIA_TABLE)) {
            throw new moodle_exception('missingmediatable', 'mod_uckkarchive');
        }

        if (class_exists(media::class) && method_exists(media::class, 'get_record')) {
            $record = media::get_record($mediaid, MUST_EXIST);
            if ($record) {
                return $record;
            }
        }

        return $DB->get_record(self::MEDIA_TABLE, ['id' => $mediaid], '*', MUST_EXIST);
    }

    /**
     * Ensure media belongs to the resolved archive activity.
     *
     * @param stdClass $media Media record.
     * @param stdClass $course Course record.
     * @param stdClass $cm Course module record.
     * @param stdClass $archive Archive record.
     * @param context_module $context Module context.
     * @return void
     * @throws moodle_exception
     */
    private static function assert_media_belongs_to_activity(
        stdClass $media,
        stdClass $course,
        stdClass $cm,
        stdClass $archive,
        context_module $context
    ): void {
        if (isset($media->archiveid) && (int)$media->archiveid !== (int)$archive->id) {
            throw new moodle_exception('invalidmediaarchive', 'mod_uckkarchive');
        }

        if (isset($media->uckkarchiveid) && (int)$media->uckkarchiveid !== (int)$archive->id) {
            throw new moodle_exception('invalidmediaarchive', 'mod_uckkarchive');
        }

        if (isset($media->courseid) && (int)$media->courseid !== (int)$course->id) {
            throw new moodle_exception('invalidmediacourse', 'mod_uckkarchive');
        }

        if (isset($media->cmid) && (int)$media->cmid !== (int)$cm->id) {
            throw new moodle_exception('invalidmediacm', 'mod_uckkarchive');
        }

        if (isset($media->contextid) && (int)$media->contextid !== (int)$context->id) {
            throw new moodle_exception('invalidmediacontext', 'mod_uckkarchive');
        }
    }

    /**
     * Require permission to tag a media record.
     *
     * @param context_module $context Module context.
     * @param stdClass $media Media record.
     * @return void
     * @throws required_capability_exception
     * @throws moodle_exception
     */
    private static function require_can_tag_media(context_module $context, stdClass $media): void {
        if (class_exists(media_policy::class) && method_exists(media_policy::class, 'require_edit_media')) {
            media_policy::require_edit_media($context, $media);
        } else {
            require_capability('mod/uckkarchive:editmedia', $context);
        }

        if (self::is_culturally_restricted_media($media)) {
            require_capability('mod/uckkarchive:viewculturallyrestricted', $context);
            return;
        }

        if (self::is_restricted_media($media)) {
            require_capability('mod/uckkarchive:viewrestrictedmedia', $context);
        }
    }

    /**
     * Normalize one tag input row.
     *
     * @param array<string, mixed> $tagdata Tag data.
     * @return array<string, mixed>
     */
    private static function normalise_tag_input(array $tagdata): array {
        $tagkey = trim((string)($tagdata['tagkey'] ?? ''));
        $label = trim((string)($tagdata['label'] ?? ''));

        if (class_exists(media_tag::class) && method_exists(media_tag::class, 'normalise_key')) {
            $tagkey = media_tag::normalise_key($tagkey);
        } else {
            $tagkey = self::normalise_key_fallback($tagkey);
        }

        $tagtype = self::normalise_tagtype((string)($tagdata['tagtype'] ?? self::DEFAULT_TAGTYPE));
        $source = self::normalise_source((string)($tagdata['source'] ?? self::DEFAULT_SOURCE));

        $metadata = (array)($tagdata['metadata'] ?? []);

        return [
            'tagkey' => $tagkey,
            'label' => $label !== '' ? clean_param($label, PARAM_TEXT) : $tagkey,
            'tagtype' => $tagtype,
            'source' => $source,
            'weight' => (int)($tagdata['weight'] ?? 0),
            'metadata' => [
                'note' => clean_param((string)($metadata['note'] ?? ''), PARAM_RAW),
                'context' => clean_param((string)($metadata['context'] ?? ''), PARAM_TEXT),
                'confidence' => clean_param((string)($metadata['confidence'] ?? ''), PARAM_RAW),
            ],
        ];
    }

    /**
     * Save a tag through the local domain class when possible.
     *
     * @param int $mediaid Media id.
     * @param array<string, mixed> $tagdata Normalized tag data.
     * @param bool $upsert Whether to upsert.
     * @param int $userid User id.
     * @return stdClass
     */
    private static function save_tag(int $mediaid, array $tagdata, bool $upsert, int $userid): stdClass {
        if (class_exists(media_tag::class)) {
            $options = [
                'label' => $tagdata['label'],
                'tagtype' => $tagdata['tagtype'],
                'source' => $tagdata['source'],
                'weight' => $tagdata['weight'],
                'metadata' => $tagdata['metadata'],
                'userid' => $userid,
            ];

            if ($upsert && method_exists(media_tag::class, 'add_or_update')) {
                return media_tag::add_or_update($mediaid, $tagdata['tagkey'], $options);
            }

            if (method_exists(media_tag::class, 'create')) {
                return media_tag::create($mediaid, $tagdata['tagkey'], $options);
            }
        }

        return self::save_tag_fallback($mediaid, $tagdata, $upsert, $userid);
    }

    /**
     * Fallback tag persistence for early construction stages.
     *
     * @param int $mediaid Media id.
     * @param array<string, mixed> $tagdata Tag data.
     * @param bool $upsert Whether to update existing tag.
     * @param int $userid User id.
     * @return stdClass
     * @throws dml_exception
     */
    private static function save_tag_fallback(int $mediaid, array $tagdata, bool $upsert, int $userid): stdClass {
        global $DB;

        $existing = self::get_existing_tag($mediaid, $tagdata['tagkey'], $tagdata['tagtype']);
        $now = time();

        if ($existing && $upsert) {
            $existing->label = $tagdata['label'];
            $existing->source = $tagdata['source'];
            $existing->weight = $tagdata['weight'];
            $existing->metadata = json_encode($tagdata['metadata'], JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
            $existing->userid = $userid;
            $existing->timemodified = $now;
            $DB->update_record(self::TAG_TABLE, self::filter_record_for_table(self::TAG_TABLE, $existing));

            return $DB->get_record(self::TAG_TABLE, ['id' => (int)$existing->id], '*', MUST_EXIST);
        }

        $record = (object)[
            'uuid' => self::generate_uuid(),
            'mediaid' => $mediaid,
            'tagkey' => $tagdata['tagkey'],
            'label' => $tagdata['label'],
            'tagtype' => $tagdata['tagtype'],
            'source' => $tagdata['source'],
            'userid' => $userid,
            'weight' => $tagdata['weight'],
            'metadata' => json_encode($tagdata['metadata'], JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES),
            'timecreated' => $now,
            'timemodified' => $now,
        ];

        $record->id = $DB->insert_record(self::TAG_TABLE, self::filter_record_for_table(self::TAG_TABLE, $record));

        return $DB->get_record(self::TAG_TABLE, ['id' => (int)$record->id], '*', MUST_EXIST);
    }

    /**
     * Get an existing tag for media/key/type.
     *
     * @param int $mediaid Media id.
     * @param string $tagkey Tag key.
     * @param string $tagtype Tag type.
     * @return stdClass|null
     */
    private static function get_existing_tag(int $mediaid, string $tagkey, string $tagtype): ?stdClass {
        global $DB;

        if (!self::table_exists(self::TAG_TABLE)) {
            return null;
        }

        return $DB->get_record(self::TAG_TABLE, [
            'mediaid' => $mediaid,
            'tagkey' => $tagkey,
            'tagtype' => $tagtype,
        ]) ?: null;
    }

    /**
     * Export tag records.
     *
     * @param stdClass[] $tags Tags.
     * @param bool $includemetadata Include metadata.
     * @return array<int, array<string, mixed>>
     */
    private static function export_tags(array $tags, bool $includemetadata): array {
        if (class_exists(media_tag::class) && method_exists(media_tag::class, 'export_list')) {
            $export = media_tag::export_list($tags, $includemetadata);

            foreach ($export as &$row) {
                $row['metadata'] = self::normalise_export_metadata((array)($row['metadata'] ?? []));
            }

            return $export;
        }

        $export = [];
        foreach ($tags as $tag) {
            $export[] = [
                'id' => (int)$tag->id,
                'uuid' => (string)($tag->uuid ?? ''),
                'mediaid' => (int)$tag->mediaid,
                'tagkey' => (string)$tag->tagkey,
                'label' => (string)$tag->label,
                'tagtype' => (string)$tag->tagtype,
                'source' => (string)$tag->source,
                'weight' => (int)($tag->weight ?? 0),
                'userid' => (int)($tag->userid ?? 0),
                'timecreated' => (int)($tag->timecreated ?? 0),
                'timemodified' => (int)($tag->timemodified ?? 0),
                'metadata' => self::decode_metadata((string)($tag->metadata ?? '')),
            ];
        }

        return $export;
    }

    /**
     * Normalize exported metadata shape.
     *
     * @param array<string, mixed> $metadata Metadata.
     * @return array<string, mixed>
     */
    private static function normalise_export_metadata(array $metadata): array {
        return [
            'note' => (string)($metadata['note'] ?? ''),
            'context' => (string)($metadata['context'] ?? ''),
            'confidence' => (string)($metadata['confidence'] ?? ''),
        ];
    }

    /**
     * Decode metadata.
     *
     * @param string $metadata JSON metadata.
     * @return array<string, mixed>
     */
    private static function decode_metadata(string $metadata): array {
        $decoded = json_decode($metadata, true);
        if (!is_array($decoded)) {
            return self::normalise_export_metadata([]);
        }

        return self::normalise_export_metadata($decoded);
    }

    /**
     * Touch media modified fields.
     *
     * @param stdClass $media Media record.
     * @param int $userid User id.
     * @return void
     */
    private static function touch_media(stdClass $media, int $userid): void {
        global $DB;

        $update = new stdClass();
        $update->id = (int)$media->id;
        $update->timemodified = time();

        if (self::table_has_column(self::MEDIA_TABLE, 'modifiedby')) {
            $update->modifiedby = $userid;
        }

        $DB->update_record(self::MEDIA_TABLE, self::filter_record_for_table(self::MEDIA_TABLE, $update));
    }

    /**
     * Trigger media updated event when available.
     *
     * @param context_module $context Module context.
     * @param stdClass $media Media record.
     * @param int $createdcount Created count.
     * @param int $updatedcount Updated count.
     * @return void
     */
    private static function trigger_media_tagged_event(
        context_module $context,
        stdClass $media,
        int $createdcount,
        int $updatedcount
    ): void {
        if (!class_exists(media_updated::class)) {
            return;
        }

        $event = media_updated::create([
            'context' => $context,
            'objectid' => (int)$media->id,
            'other' => [
                'action' => 'tag_media',
                'createdcount' => $createdcount,
                'updatedcount' => $updatedcount,
                'uuid' => (string)($media->uuid ?? ''),
            ],
        ]);

        $event->add_record_snapshot(self::MEDIA_TABLE, $media);
        $event->trigger();
    }

    /**
     * Return whether a tag key looks like a content advisory tag.
     *
     * @param string $tagkey Tag key.
     * @return bool
     */
    private static function is_content_advisory_tag(string $tagkey): bool {
        if (class_exists(media_tag::class) && method_exists(media_tag::class, 'is_content_advisory_key')) {
            return media_tag::is_content_advisory_key($tagkey);
        }

        return in_array($tagkey, [
            'sexual_violence',
            'violence',
            'racism',
            'colonial_violence',
            'death',
            'self_harm',
            'substance_use',
            'nudity',
            'explicit_language',
            'culturally_sensitive',
            'sacred_content',
            'ceremonial_content',
            'restricted_knowledge',
            'grief_or_mourning',
            'requires_context',
            'not_for_children',
        ], true);
    }

    /**
     * Normalize tag type.
     *
     * @param string $tagtype Tag type.
     * @return string
     */
    private static function normalise_tagtype(string $tagtype): string {
        if (class_exists(media_tag::class) && method_exists(media_tag::class, 'normalise_type')) {
            return media_tag::normalise_type($tagtype);
        }

        $tagtype = clean_param($tagtype, PARAM_ALPHANUMEXT);
        $allowed = [
            'topic',
            'format',
            'course_use',
            'language',
            'region',
            'pedagogical_theme',
            'source_category',
            'review_state',
        ];

        if (!in_array($tagtype, $allowed, true)) {
            throw new invalid_parameter_exception('Invalid media tag type.');
        }

        return $tagtype;
    }

    /**
     * Normalize source.
     *
     * @param string $source Source.
     * @return string
     */
    private static function normalise_source(string $source): string {
        if (class_exists(media_tag::class) && method_exists(media_tag::class, 'normalise_source')) {
            return media_tag::normalise_source($source);
        }

        $source = clean_param($source, PARAM_ALPHANUMEXT);
        $allowed = ['human', 'imported', 'system', 'ai_suggested'];

        if (!in_array($source, $allowed, true)) {
            throw new invalid_parameter_exception('Invalid media tag source.');
        }

        return $source;
    }

    /**
     * Fallback key normalizer.
     *
     * @param string $value Raw value.
     * @return string
     */
    private static function normalise_key_fallback(string $value): string {
        $value = trim(\core_text::strtolower($value));
        $value = preg_replace('/[^\p{L}\p{N}_-]+/u', '_', $value) ?? '';
        $value = preg_replace('/_+/', '_', $value) ?? '';
        $value = trim($value, '_-');

        if ($value === '') {
            throw new invalid_parameter_exception('Media tag key cannot be empty.');
        }

        return substr($value, 0, 100);
    }

    /**
     * Return whether media is restricted.
     *
     * @param stdClass $media Media record.
     * @return bool
     */
    private static function is_restricted_media(stdClass $media): bool {
        if (class_exists(media_policy::class) && method_exists(media_policy::class, 'is_restricted_media')) {
            return media_policy::is_restricted_media($media);
        }

        $visibility = (string)($media->visibility ?? '');
        return in_array($visibility, [
            self::VISIBILITY_RESTRICTED,
            self::VISIBILITY_RESTRICTED_INTEGRITY,
            self::VISIBILITY_RESTRICTED_CULTURAL,
        ], true) || !empty($media->restricted);
    }

    /**
     * Return whether media is culturally restricted.
     *
     * @param stdClass $media Media record.
     * @return bool
     */
    private static function is_culturally_restricted_media(stdClass $media): bool {
        if (class_exists(media_policy::class) && method_exists(media_policy::class, 'is_culturally_restricted')) {
            return media_policy::is_culturally_restricted($media);
        }

        return (string)($media->visibility ?? '') === self::VISIBILITY_RESTRICTED_CULTURAL ||
            !empty($media->culturalprotocol);
    }

    /**
     * Return whether a table exists.
     *
     * @param string $tablename Table name.
     * @return bool
     */
    private static function table_exists(string $tablename): bool {
        global $DB;

        return $DB->get_manager()->table_exists(new \xmldb_table($tablename));
    }

    /**
     * Return whether a table has one column.
     *
     * @param string $tablename Table name.
     * @param string $column Column name.
     * @return bool
     */
    private static function table_has_column(string $tablename, string $column): bool {
        global $DB;

        if (!self::table_exists($tablename)) {
            return false;
        }

        return array_key_exists($column, $DB->get_columns($tablename));
    }

    /**
     * Filter a record to existing table fields.
     *
     * @param string $tablename Table name.
     * @param stdClass $record Record.
     * @return stdClass
     */
    private static function filter_record_for_table(string $tablename, stdClass $record): stdClass {
        global $DB;

        $columns = $DB->get_columns($tablename);
        $filtered = new stdClass();

        foreach ($columns as $name => $unused) {
            if (property_exists($record, $name)) {
                $filtered->{$name} = $record->{$name};
            }
        }

        return $filtered;
    }

    /**
     * Generate UUID.
     *
     * @return string
     */
    private static function generate_uuid(): string {
        if (class_exists('\\mod_uckkarchive\\local\\uuid') &&
                method_exists('\\mod_uckkarchive\\local\\uuid', 'generate')) {
            return \mod_uckkarchive\local\uuid::generate();
        }

        return \core\uuid::generate();
    }

    /**
     * Build warning.
     *
     * @param string $item Item.
     * @param int $itemid Item id.
     * @param string $warningcode Warning code.
     * @param string $message Message.
     * @return array<string, mixed>
     */
    private static function warning(string $item, int $itemid, string $warningcode, string $message): array {
        return [
            'item' => $item,
            'itemid' => $itemid,
            'warningcode' => clean_param($warningcode, PARAM_ALPHANUMEXT),
            'message' => $message,
        ];
    }
}
