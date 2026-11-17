<?php
// This file is part of Moodle - https://moodle.org/
//
// Moodle is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// any later version.

/**
 * Create an export request for a media collection.
 *
 * @package    mod_uckkarchive
 * @copyright  2026 Univers-Cité King Klown
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
use invalid_parameter_exception;
use mod_uckkarchive\local\manifest_builder;
use mod_uckkarchive\local\media_collection;
use mod_uckkarchive\local\media_policy;
use moodle_exception;
use moodle_url;
use stdClass;

/**
 * External service that creates an export request for a media collection.
 *
 * Service contract:
 *
 * ```text
 * cmid
 * collectionid
 * collectionuuid
 * format
 * options
 * reason
 * ```
 *
 * Returns:
 *
 * ```text
 * exportid
 * exportuuid
 * state
 * manifest
 * downloadurl
 * warnings
 * ```
 *
 * Collection export rule:
 *
 * ```text
 * Collection export checks every included media object individually.
 * Collection membership does not grant export authority.
 * ```
 */
final class export_collection extends external_api {
    /** Export table. */
    private const EXPORT_TABLE = 'uckkarchive_export';

    /** Export scope. */
    private const EXPORT_SCOPE = 'media_collection';

    /** Default export format. */
    private const DEFAULT_FORMAT = 'zip';

    /** Export state queued. */
    private const STATE_QUEUED = 'queued';

    /** Export state blocked. */
    private const STATE_BLOCKED = 'blocked';

    /**
     * Load the page context.
     *
     * @param int $cmid Course module id.
     * @return array{0:stdClass,1:stdClass,2:stdClass,3:context_module}
     */
    protected static function load_page(int $cmid): array {
        [$course, $cm, $archive, $context] = \uckkarchive_require_page($cmid, 0);

        return [$course, $cm, $archive, $context];
    }

    /**
     * Define service parameters.
     *
     * @return external_function_parameters
     */
    public static function execute_parameters(): external_function_parameters {
        return new external_function_parameters([
            'cmid' => new external_value(PARAM_INT, 'Course module id'),
            'collectionid' => new external_value(PARAM_INT, 'Media collection id', VALUE_DEFAULT, 0),
            'collectionuuid' => new external_value(PARAM_TEXT, 'Media collection UUID', VALUE_DEFAULT, ''),
            'format' => new external_value(PARAM_ALPHANUMEXT, 'Export format', VALUE_DEFAULT, self::DEFAULT_FORMAT),
            'options' => new external_single_structure([
                'includefiles' => new external_value(PARAM_BOOL, 'Include media files', VALUE_DEFAULT, true),
                'includethumbnails' => new external_value(PARAM_BOOL, 'Include thumbnails', VALUE_DEFAULT, true),
                'includepreviews' => new external_value(PARAM_BOOL, 'Include previews', VALUE_DEFAULT, true),
                'includederivatives' => new external_value(PARAM_BOOL, 'Include derivatives', VALUE_DEFAULT, true),
                'includeversions' => new external_value(PARAM_BOOL, 'Include media version metadata', VALUE_DEFAULT, true),
                'includeadvisories' => new external_value(PARAM_BOOL, 'Include content advisory metadata', VALUE_DEFAULT, true),
                'includeexternalworks' => new external_value(PARAM_BOOL, 'Include external work metadata', VALUE_DEFAULT, true),
                'redactionlevel' => new external_value(PARAM_ALPHANUMEXT, 'Redaction level', VALUE_DEFAULT, 'standard'),
                'visibility' => new external_value(PARAM_ALPHANUMEXT, 'Export visibility', VALUE_DEFAULT, 'course'),
            ], 'Export options', VALUE_DEFAULT, []),
            'reason' => new external_value(PARAM_RAW, 'Export reason', VALUE_DEFAULT, ''),
        ]);
    }

    /**
     * Execute the service.
     *
     * @param int $cmid Course module id.
     * @param int $collectionid Collection id.
     * @param string $collectionuuid Collection UUID.
     * @param string $format Export format.
     * @param array<string, mixed> $options Export options.
     * @param string $reason Export reason.
     * @return array<string, mixed>
     */
    public static function execute(
        int $cmid,
        int $collectionid = 0,
        string $collectionuuid = '',
        string $format = self::DEFAULT_FORMAT,
        array $options = [],
        string $reason = ''
    ): array {
        global $DB, $USER;

        $params = self::validate_parameters(self::execute_parameters(), [
            'cmid' => $cmid,
            'collectionid' => $collectionid,
            'collectionuuid' => $collectionuuid,
            'format' => $format,
            'options' => $options,
            'reason' => $reason,
        ]);

        [$course, $cm, $archive, $context] = self::load_page((int)$params['cmid']);
        self::validate_context($context);

        require_capability('mod/uckkarchive:exportmedia', $context);

        if (!self::table_exists(self::EXPORT_TABLE)) {
            throw new moodle_exception('missingtable', 'error', '', self::EXPORT_TABLE);
        }

        if (!class_exists(media_collection::class)) {
            throw new moodle_exception('missingclass', 'error', '', media_collection::class);
        }

        $format = self::normalise_format((string)$params['format']);
        $options = self::normalise_options((array)$params['options']);
        $reason = self::normalise_text((string)$params['reason']);

        $collection = self::load_collection((int)$params['collectionid'], (string)$params['collectionuuid']);
        self::require_collection_belongs_to_archive($collection, (int)$archive->id);

        if (class_exists(media_policy::class) && !media_policy::can_view_collection($context, $collection)) {
            throw new moodle_exception('nopermissions', 'error', '', 'Cannot view this media collection.');
        }

        $collectionmedia = media_collection::get_media((int)$collection->id);
        $allowedmedia = [];
        $excluded = [];
        $warnings = [];

        foreach ($collectionmedia as $media) {
            if (self::can_export_media($context, $media)) {
                $allowedmedia[] = $media;
                continue;
            }

            $excluded[] = (int)$media->id;
            $warnings[] = self::warning(
                'media',
                (int)$media->id,
                'mediaexcluded',
                'A media object was excluded because the current user cannot export it.'
            );
        }

        if (empty($allowedmedia)) {
            $manifest = self::build_blocked_manifest($archive, $collection, $excluded, $reason, $options);

            return [
                'exportid' => 0,
                'exportuuid' => '',
                'state' => self::STATE_BLOCKED,
                'manifest' => self::encode_manifest($manifest),
                'downloadurl' => '',
                'warnings' => array_merge($warnings, [
                    self::warning(
                        'collection',
                        (int)$collection->id,
                        'noexportablemedia',
                        'The collection contains no media that the current user may export.'
                    ),
                ]),
            ];
        }

        $now = time();
        $exportuuid = self::generate_uuid();

        $exportrecord = self::build_export_record(
            $archive,
            $course,
            $cm,
            $context,
            $collection,
            $allowedmedia,
            $excluded,
            $exportuuid,
            $format,
            $options,
            $reason,
            (int)$USER->id,
            $now
        );

        $exportid = self::insert_export_record($exportrecord);
        $exportrecord->id = $exportid;

        $manifest = self::build_manifest(
            $archive,
            $collection,
            $allowedmedia,
            $excluded,
            $exportrecord,
            $context,
            (int)$USER->id,
            $reason,
            $options,
            $warnings
        );

        self::update_export_manifest($exportid, $exportuuid, $manifest, $allowedmedia, $excluded, $options, $reason);

        self::trigger_media_exported_events($allowedmedia, $collection, $archive, $course, $cm, $context, $exportid, $format);

        return [
            'exportid' => $exportid,
            'exportuuid' => $exportuuid,
            'state' => self::STATE_QUEUED,
            'manifest' => self::encode_manifest($manifest),
            'downloadurl' => self::get_download_url($context, $exportid),
            'warnings' => $warnings,
        ];
    }

    /**
     * Define service return structure.
     *
     * @return external_single_structure
     */
    public static function execute_returns(): external_single_structure {
        return new external_single_structure([
            'exportid' => new external_value(PARAM_INT, 'Export id, or 0 if blocked'),
            'exportuuid' => new external_value(PARAM_TEXT, 'Stable export UUID'),
            'state' => new external_value(PARAM_ALPHANUMEXT, 'Export state'),
            'manifest' => new external_value(PARAM_RAW, 'Manifest JSON'),
            'downloadurl' => new external_value(PARAM_RAW, 'Download URL when a generated package exists'),
            'warnings' => new external_multiple_structure(
                new external_single_structure([
                    'item' => new external_value(PARAM_TEXT, 'Warning item'),
                    'itemid' => new external_value(PARAM_INT, 'Warning item id'),
                    'warningcode' => new external_value(PARAM_ALPHANUMEXT, 'Warning code'),
                    'message' => new external_value(PARAM_TEXT, 'Warning message'),
                ])
            ),
        ]);
    }

    /**
     * Load collection by id or UUID.
     *
     * @param int $collectionid Collection id.
     * @param string $collectionuuid Collection UUID.
     * @return stdClass
     */
    protected static function load_collection(int $collectionid, string $collectionuuid): stdClass {
        $collectionuuid = trim($collectionuuid);

        if ($collectionid > 0) {
            return media_collection::get($collectionid, MUST_EXIST);
        }

        if ($collectionuuid !== '') {
            $collection = media_collection::get_by_uuid($collectionuuid, MUST_EXIST);
            if ($collection) {
                return $collection;
            }
        }

        throw new invalid_parameter_exception('A collection id or collection UUID is required.');
    }

    /**
     * Ensure collection belongs to the current archive.
     *
     * @param stdClass $collection Collection record.
     * @param int $archiveid Archive id.
     * @return void
     */
    protected static function require_collection_belongs_to_archive(stdClass $collection, int $archiveid): void {
        if (!property_exists($collection, 'archiveid')) {
            return;
        }

        if ((int)$collection->archiveid !== $archiveid) {
            throw new moodle_exception('invalidcollection', 'mod_uckkarchive');
        }
    }

    /**
     * Check media export authority.
     *
     * @param context_module $context Module context.
     * @param stdClass $media Media record.
     * @return bool
     */
    protected static function can_export_media(context_module $context, stdClass $media): bool {
        if (class_exists(media_policy::class)) {
            return media_policy::can_export_media($context, $media);
        }

        if (!has_capability('mod/uckkarchive:exportmedia', $context)) {
            return false;
        }

        $visibility = (string)($media->visibility ?? '');
        if (in_array($visibility, ['restricted', 'restricted_integrity'], true)) {
            return has_capability('mod/uckkarchive:viewrestrictedmedia', $context);
        }

        if ($visibility === 'restricted_cultural') {
            return has_capability('mod/uckkarchive:viewculturallyrestricted', $context);
        }

        return has_capability('mod/uckkarchive:viewmedia', $context);
    }

    /**
     * Build export record.
     *
     * @param stdClass $archive Archive record.
     * @param stdClass $course Course record.
     * @param stdClass $cm Course module record.
     * @param context_module $context Module context.
     * @param stdClass $collection Collection record.
     * @param stdClass[] $allowedmedia Allowed media.
     * @param int[] $excluded Excluded media ids.
     * @param string $exportuuid Export UUID.
     * @param string $format Export format.
     * @param array<string, mixed> $options Options.
     * @param string $reason Reason.
     * @param int $userid User id.
     * @param int $now Timestamp.
     * @return stdClass
     */
    protected static function build_export_record(
        stdClass $archive,
        stdClass $course,
        stdClass $cm,
        context_module $context,
        stdClass $collection,
        array $allowedmedia,
        array $excluded,
        string $exportuuid,
        string $format,
        array $options,
        string $reason,
        int $userid,
        int $now
    ): stdClass {
        $record = new stdClass();
        $record->uuid = $exportuuid;
        $record->archiveid = (int)$archive->id;
        $record->courseid = (int)$course->id;
        $record->cmid = (int)$cm->id;
        $record->contextid = (int)$context->id;
        $record->userid = $userid;
        $record->exportscope = self::EXPORT_SCOPE;
        $record->exportformat = $format;
        $record->packagename = 'uckkarchive-collection-' . (int)$collection->id . '-' . $now;
        $record->description = 'Media collection export: ' . clean_param((string)($collection->title ?? ''), PARAM_TEXT);
        $record->itemids = json_encode(array_values(array_map(static fn(stdClass $media): int => (int)$media->id, $allowedmedia)));
        $record->reason = $reason;
        $record->auditnote = 'Created by external export_collection service';
        $record->redactionlevel = (string)$options['redactionlevel'];
        $record->redacted = $options['redactionlevel'] !== 'none' ? 1 : 0;
        $record->includefiles = !empty($options['includefiles']) ? 1 : 0;
        $record->includeproofs = 0;
        $record->includeprovenance = 1;
        $record->includeversions = !empty($options['includeversions']) ? 1 : 0;
        $record->fileitemid = 0;
        $record->downloadcount = 0;
        $record->timequeued = $now;
        $record->timestarted = 0;
        $record->timecompleted = 0;
        $record->status = self::STATE_QUEUED;
        $record->visibility = (string)$options['visibility'];
        $record->versionno = 1;
        $record->createdby = $userid;
        $record->modifiedby = $userid;
        $record->timecreated = $now;
        $record->timemodified = $now;
        $record->metadata = self::encode_metadata([
            'service' => 'mod_uckkarchive_export_collection',
            'exportuuid' => $exportuuid,
            'collectionid' => (int)$collection->id,
            'collectionuuid' => (string)($collection->uuid ?? ''),
            'mediacount' => count($allowedmedia),
            'excludedmediaids' => array_values($excluded),
            'options' => $options,
        ]);

        return $record;
    }

    /**
     * Insert export record, filtering to installed schema columns.
     *
     * @param stdClass $record Export record.
     * @return int
     */
    protected static function insert_export_record(stdClass $record): int {
        global $DB;

        return (int)$DB->insert_record(self::EXPORT_TABLE, self::filter_record_for_table($record));
    }

    /**
     * Update export metadata with final manifest.
     *
     * @param int $exportid Export id.
     * @param string $exportuuid Export UUID.
     * @param array<string, mixed> $manifest Manifest.
     * @param stdClass[] $allowedmedia Allowed media.
     * @param int[] $excluded Excluded media ids.
     * @param array<string, mixed> $options Options.
     * @param string $reason Reason.
     * @return void
     */
    protected static function update_export_manifest(
        int $exportid,
        string $exportuuid,
        array $manifest,
        array $allowedmedia,
        array $excluded,
        array $options,
        string $reason
    ): void {
        global $DB;

        $record = new stdClass();
        $record->id = $exportid;
        $record->timemodified = time();
        $record->metadata = self::encode_metadata([
            'service' => 'mod_uckkarchive_export_collection',
            'exportuuid' => $exportuuid,
            'manifest' => $manifest,
            'mediacount' => count($allowedmedia),
            'mediaids' => array_values(array_map(static fn(stdClass $media): int => (int)$media->id, $allowedmedia)),
            'excludedmediaids' => array_values($excluded),
            'options' => $options,
            'reason' => $reason,
        ]);

        $DB->update_record(self::EXPORT_TABLE, self::filter_record_for_table($record));
    }

    /**
     * Build manifest.
     *
     * @param stdClass $archive Archive record.
     * @param stdClass $collection Collection record.
     * @param stdClass[] $allowedmedia Allowed media.
     * @param int[] $excluded Excluded media ids.
     * @param stdClass $exportrecord Export record.
     * @param context_module $context Module context.
     * @param int $userid User id.
     * @param string $reason Reason.
     * @param array<string, mixed> $options Options.
     * @param array<int, array<string, mixed>> $warnings Warnings.
     * @return array<string, mixed>
     */
    protected static function build_manifest(
        stdClass $archive,
        stdClass $collection,
        array $allowedmedia,
        array $excluded,
        stdClass $exportrecord,
        context_module $context,
        int $userid,
        string $reason,
        array $options,
        array $warnings
    ): array {
        if (class_exists(manifest_builder::class)) {
            $builder = new manifest_builder();
            $manifest = $builder->create($archive, $exportrecord, $context, $userid, 'media_collection_export', $reason, $options);
            $builder->add_collection($manifest, $collection, $options);

            foreach ($allowedmedia as $media) {
                $builder->add_media($manifest, $media, $options);
            }

            foreach ($excluded as $mediaid) {
                $builder->add_warning($manifest, 'mediaexcluded', 'A media object was excluded from collection export.', [
                    'mediaid' => $mediaid,
                ]);
            }

            foreach ($warnings as $warning) {
                $builder->add_warning($manifest, (string)$warning['warningcode'], (string)$warning['message'], [
                    'item' => $warning['item'],
                    'itemid' => $warning['itemid'],
                ]);
            }

            return $builder->finalise($manifest);
        }

        return [
            'schema' => [
                'name' => 'manifest.json',
                'version' => '1.0',
                'component' => 'mod_uckkarchive',
                'generatedat' => time(),
            ],
            'package' => [
                'exportid' => (int)$exportrecord->id,
                'exportuuid' => (string)$exportrecord->uuid,
                'exporttype' => 'media_collection_export',
                'exportactor' => $userid,
                'exportreason' => $reason,
                'redactionlevel' => (string)$options['redactionlevel'],
            ],
            'collection' => [
                'id' => (int)$collection->id,
                'uuid' => (string)($collection->uuid ?? ''),
                'title' => (string)($collection->title ?? ''),
                'visibility' => (string)($collection->visibility ?? ''),
            ],
            'media' => array_values(array_map([self::class, 'export_media_summary'], $allowedmedia)),
            'excludedmediaids' => array_values($excluded),
            'warnings' => $warnings,
            'counts' => [
                'media' => count($allowedmedia),
                'excluded' => count($excluded),
                'warnings' => count($warnings),
            ],
        ];
    }

    /**
     * Build a blocked manifest.
     *
     * @param stdClass $archive Archive record.
     * @param stdClass $collection Collection record.
     * @param int[] $excluded Excluded media ids.
     * @param string $reason Reason.
     * @param array<string, mixed> $options Options.
     * @return array<string, mixed>
     */
    protected static function build_blocked_manifest(
        stdClass $archive,
        stdClass $collection,
        array $excluded,
        string $reason,
        array $options
    ): array {
        return [
            'schema' => [
                'name' => 'manifest.json',
                'version' => '1.0',
                'component' => 'mod_uckkarchive',
                'generatedat' => time(),
            ],
            'package' => [
                'exportid' => 0,
                'exportuuid' => '',
                'exporttype' => 'media_collection_export',
                'exportreason' => $reason,
                'state' => self::STATE_BLOCKED,
                'redactionlevel' => (string)$options['redactionlevel'],
            ],
            'archive' => [
                'id' => (int)$archive->id,
                'name' => (string)($archive->name ?? ''),
            ],
            'collection' => [
                'id' => (int)$collection->id,
                'uuid' => (string)($collection->uuid ?? ''),
                'title' => (string)($collection->title ?? ''),
            ],
            'media' => [],
            'excludedmediaids' => array_values($excluded),
            'warnings' => [[
                'code' => 'noexportablemedia',
                'message' => 'No media in this collection can be exported by the current user.',
            ]],
            'counts' => [
                'media' => 0,
                'excluded' => count($excluded),
                'warnings' => 1,
            ],
        ];
    }

    /**
     * Export media summary for fallback manifest.
     *
     * @param stdClass $media Media record.
     * @return array<string, mixed>
     */
    protected static function export_media_summary(stdClass $media): array {
        return [
            'id' => (int)$media->id,
            'uuid' => (string)($media->uuid ?? ''),
            'title' => (string)($media->title ?? ''),
            'mediatype' => (string)($media->mediatype ?? ''),
            'mimetype' => (string)($media->mimetype ?? ''),
            'status' => (string)($media->status ?? ''),
            'visibility' => (string)($media->visibility ?? ''),
            'currentversionid' => (int)($media->currentversionid ?? 0),
        ];
    }

    /**
     * Return possible download URL.
     *
     * The actual package is normally generated by a scheduled task. If no file
     * exists yet, the service returns an empty string and status can be checked
     * through get_export_status.
     *
     * @param context_module $context Module context.
     * @param int $exportid Export id.
     * @return string
     */
    protected static function get_download_url(context_module $context, int $exportid): string {
        $fs = get_file_storage();
        $files = $fs->get_area_files((int)$context->id, 'mod_uckkarchive', 'export_package', $exportid, 'filename', false);

        foreach ($files as $file) {
            if ($file->is_directory()) {
                continue;
            }

            return moodle_url::make_pluginfile_url(
                $file->get_contextid(),
                $file->get_component(),
                $file->get_filearea(),
                $file->get_itemid(),
                $file->get_filepath(),
                $file->get_filename(),
                true
            )->out(false);
        }

        return '';
    }

    /**
     * Trigger media exported events when event class exists.
     *
     * @param stdClass[] $mediarecords Media records.
     * @param stdClass $collection Collection.
     * @param stdClass $archive Archive.
     * @param stdClass $course Course.
     * @param stdClass $cm Course module.
     * @param context_module $context Context.
     * @param int $exportid Export id.
     * @param string $format Format.
     * @return void
     */
    protected static function trigger_media_exported_events(
        array $mediarecords,
        stdClass $collection,
        stdClass $archive,
        stdClass $course,
        stdClass $cm,
        context_module $context,
        int $exportid,
        string $format
    ): void {
        $eventclass = '\\mod_uckkarchive\\event\\media_exported';

        if (!class_exists($eventclass)) {
            return;
        }

        foreach ($mediarecords as $media) {
            try {
                $event = $eventclass::create([
                    'objectid' => (int)$media->id,
                    'context' => $context,
                    'other' => [
                        'archiveid' => (int)$archive->id,
                        'courseid' => (int)$course->id,
                        'cmid' => (int)$cm->id,
                        'collectionid' => (int)$collection->id,
                        'collectionuuid' => (string)($collection->uuid ?? ''),
                        'exportid' => $exportid,
                        'exporttype' => $format,
                    ],
                ]);
                $event->trigger();
            } catch (\Throwable $ignored) {
                // Export record creation must not fail because event code is absent or incomplete.
            }
        }
    }

    /**
     * Normalize format.
     *
     * @param string $format Format.
     * @return string
     */
    protected static function normalise_format(string $format): string {
        $format = clean_param($format, PARAM_ALPHANUMEXT);
        $allowed = ['json', 'zip', 'html', 'csv', 'pdf', 'moodle'];

        return in_array($format, $allowed, true) ? $format : self::DEFAULT_FORMAT;
    }

    /**
     * Normalize options.
     *
     * @param array<string, mixed> $options Options.
     * @return array<string, mixed>
     */
    protected static function normalise_options(array $options): array {
        $defaults = [
            'includefiles' => true,
            'includethumbnails' => true,
            'includepreviews' => true,
            'includederivatives' => true,
            'includeversions' => true,
            'includeadvisories' => true,
            'includeexternalworks' => true,
            'redactionlevel' => 'standard',
            'visibility' => 'course',
        ];

        $options = array_merge($defaults, $options);

        foreach ([
            'includefiles',
            'includethumbnails',
            'includepreviews',
            'includederivatives',
            'includeversions',
            'includeadvisories',
            'includeexternalworks',
        ] as $key) {
            $options[$key] = !empty($options[$key]);
        }

        $options['redactionlevel'] = clean_param((string)$options['redactionlevel'], PARAM_ALPHANUMEXT);
        $options['visibility'] = self::normalise_visibility((string)$options['visibility']);

        return $options;
    }

    /**
     * Normalize export visibility.
     *
     * @param string $visibility Visibility.
     * @return string
     */
    protected static function normalise_visibility(string $visibility): string {
        $visibility = clean_param(trim($visibility), PARAM_ALPHANUMEXT);

        if ($visibility === 'institutional') {
            $visibility = 'institution';
        }

        $allowed = [
            'private',
            'user',
            'group',
            'course',
            'cohort',
            'program',
            'institution',
            'public',
            'restricted',
            'restricted_integrity',
            'restricted_cultural',
        ];

        return in_array($visibility, $allowed, true) ? $visibility : 'course';
    }

    /**
     * Normalize text.
     *
     * @param string $text Text.
     * @return string
     */
    protected static function normalise_text(string $text): string {
        return clean_param(trim($text), PARAM_TEXT);
    }

    /**
     * Return warning payload.
     *
     * @param string $item Item.
     * @param int $itemid Item id.
     * @param string $code Warning code.
     * @param string $message Message.
     * @return array<string, mixed>
     */
    protected static function warning(string $item, int $itemid, string $code, string $message): array {
        return [
            'item' => $item,
            'itemid' => $itemid,
            'warningcode' => clean_param($code, PARAM_ALPHANUMEXT),
            'message' => $message,
        ];
    }

    /**
     * Return whether table exists.
     *
     * @param string $tablename Table name.
     * @return bool
     */
    protected static function table_exists(string $tablename): bool {
        global $DB;

        return $DB->get_manager()->table_exists(new \xmldb_table($tablename));
    }

    /**
     * Filter record properties to installed schema.
     *
     * @param stdClass $record Record.
     * @return stdClass
     */
    protected static function filter_record_for_table(stdClass $record): stdClass {
        global $DB;

        $columns = $DB->get_columns(self::EXPORT_TABLE);
        $filtered = new stdClass();

        foreach ($columns as $name => $definition) {
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
    protected static function generate_uuid(): string {
        if (class_exists('\\mod_uckkarchive\\local\\uuid') && method_exists('\\mod_uckkarchive\\local\\uuid', 'generate')) {
            return \mod_uckkarchive\local\uuid::generate();
        }

        if (class_exists('\\core\\uuid')) {
            return \core\uuid::generate();
        }

        $bytes = random_bytes(16);
        $bytes[6] = chr((ord($bytes[6]) & 0x0f) | 0x40);
        $bytes[8] = chr((ord($bytes[8]) & 0x3f) | 0x80);

        return vsprintf('%s%s-%s-%s-%s-%s%s%s', str_split(bin2hex($bytes), 4));
    }

    /**
     * Encode metadata as JSON.
     *
     * @param array<string, mixed> $metadata Metadata.
     * @return string
     */
    protected static function encode_metadata(array $metadata): string {
        return json_encode($metadata, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES) ?: '{}';
    }

    /**
     * Encode manifest as JSON.
     *
     * @param array<string, mixed> $manifest Manifest.
     * @return string
     */
    protected static function encode_manifest(array $manifest): string {
        return json_encode($manifest, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES | JSON_PRETTY_PRINT) ?: '{}';
    }
}
