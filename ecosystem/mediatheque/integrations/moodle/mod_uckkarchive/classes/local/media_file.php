<?php
// This file is part of Moodle - https://moodle.org/
//
// Moodle is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// any later version.

/**
 * Media File API coordination for UCKK Archive media objects.
 *
 * @package    mod_uckkarchive
 * @copyright  2026 Univers-Cité King Klown
 * @license    https://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later
 */

declare(strict_types=1);

namespace mod_uckkarchive\local;

use context;
use context_module;
use core_files\stored_file;
use file_exception;
use file_storage;
use invalid_parameter_exception;
use moodle_exception;
use moodle_url;
use stdClass;

defined('MOODLE_INTERNAL') || die();

global $CFG;
require_once($CFG->dirroot . '/repository/lib.php');

/**
 * Coordinates Moodle File API work for media-owned file areas.
 *
 * This class is intentionally not an authorization layer.
 *
 * Responsibilities:
 * - validate media file areas;
 * - define safe File API options for media files;
 * - save files from Moodle draft areas into canonical media file areas;
 * - read stored files and file metadata;
 * - generate pluginfile URLs;
 * - delete area files when policy has already approved deletion.
 *
 * Non-responsibilities:
 * - deciding whether the current user may view/download a file;
 * - deciding whether media is public, restricted, cultural, or integrity-bound;
 * - validating media lifecycle transitions;
 * - validating content advisories or cultural protocol access;
 * - serving files directly.
 *
 * Access control belongs in:
 *
 * ```text
 * classes/local/media_policy.php
 * classes/local/content_policy.php
 * lib.php pluginfile handling
 * ```
 */
final class media_file {
    /** Moodle File API component. */
    public const COMPONENT = 'mod_uckkarchive';

    /** Original uploaded or preserved media file. */
    public const AREA_ORIGINAL = 'media_original';

    /** Preview-optimized media file. */
    public const AREA_PREVIEW = 'media_preview';

    /** Thumbnail file. */
    public const AREA_THUMBNAIL = 'media_thumbnail';

    /** Generated derivative. */
    public const AREA_DERIVATIVE = 'media_derivative';

    /** Caption file such as VTT/SRT. */
    public const AREA_CAPTION = 'media_caption';

    /** Transcript file. */
    public const AREA_TRANSCRIPT = 'media_transcript';

    /** Supporting attachment. */
    public const AREA_ATTACHMENT = 'media_attachment';

    /** Default maximum bytes for media area saves when no setting exists. */
    private const DEFAULT_MAXBYTES = 0;

    /**
     * Return canonical media file areas.
     *
     * The canonical source of truth is intended to be
     * {@see \mod_uckkarchive\local\file_area_registry}. This method mirrors
     * the media subset so this class remains usable during initial module
     * construction and upgrade tasks.
     *
     * @return string[]
     */
    public static function get_media_fileareas(): array {
        if (class_exists(file_area_registry::class) &&
                method_exists(file_area_registry::class, 'get_media_fileareas')) {
            $areas = file_area_registry::get_media_fileareas();
            if (is_array($areas) && !empty($areas)) {
                return array_values(array_map('strval', $areas));
            }
        }

        return [
            self::AREA_ORIGINAL,
            self::AREA_PREVIEW,
            self::AREA_THUMBNAIL,
            self::AREA_DERIVATIVE,
            self::AREA_CAPTION,
            self::AREA_TRANSCRIPT,
            self::AREA_ATTACHMENT,
        ];
    }

    /**
     * Return media file area labels.
     *
     * @return array<string, string>
     */
    public static function get_media_filearea_labels(): array {
        return [
            self::AREA_ORIGINAL => get_string('filearea:media_original', 'uckkarchive'),
            self::AREA_PREVIEW => get_string('filearea:media_preview', 'uckkarchive'),
            self::AREA_THUMBNAIL => get_string('filearea:media_thumbnail', 'uckkarchive'),
            self::AREA_DERIVATIVE => get_string('filearea:media_derivative', 'uckkarchive'),
            self::AREA_CAPTION => get_string('filearea:media_caption', 'uckkarchive'),
            self::AREA_TRANSCRIPT => get_string('filearea:media_transcript', 'uckkarchive'),
            self::AREA_ATTACHMENT => get_string('filearea:media_attachment', 'uckkarchive'),
        ];
    }

    /**
     * Return whether a file area is a canonical media file area.
     *
     * @param string $filearea File area.
     * @return bool
     */
    public static function is_media_filearea(string $filearea): bool {
        $filearea = self::normalise_filearea($filearea);

        return in_array($filearea, self::get_media_fileareas(), true);
    }

    /**
     * Validate and normalize a media file area.
     *
     * @param string $filearea File area.
     * @return string Normalized file area.
     * @throws invalid_parameter_exception
     */
    public static function require_media_filearea(string $filearea): string {
        $filearea = self::normalise_filearea($filearea);

        if (!self::is_media_filearea($filearea)) {
            throw new invalid_parameter_exception('Invalid UCKK Archive media file area: ' . $filearea);
        }

        return $filearea;
    }

    /**
     * Return whether the file area normally stores generated files.
     *
     * @param string $filearea File area.
     * @return bool
     */
    public static function is_generated_area(string $filearea): bool {
        $filearea = self::require_media_filearea($filearea);

        return in_array($filearea, [
            self::AREA_PREVIEW,
            self::AREA_THUMBNAIL,
            self::AREA_DERIVATIVE,
        ], true);
    }

    /**
     * Return whether the file area normally stores text/support files.
     *
     * @param string $filearea File area.
     * @return bool
     */
    public static function is_textual_support_area(string $filearea): bool {
        $filearea = self::require_media_filearea($filearea);

        return in_array($filearea, [
            self::AREA_CAPTION,
            self::AREA_TRANSCRIPT,
        ], true);
    }

    /**
     * Return safe File API save options for a media file area.
     *
     * @param string $filearea File area.
     * @param array<string, mixed> $overrides Override options.
     * @return array<string, mixed>
     */
    public static function get_file_options(string $filearea, array $overrides = []): array {
        $filearea = self::require_media_filearea($filearea);

        $options = [
            'subdirs' => false,
            'maxbytes' => self::DEFAULT_MAXBYTES,
            'maxfiles' => self::get_default_maxfiles($filearea),
            'accepted_types' => self::get_default_accepted_types($filearea),
            'return_types' => \FILE_INTERNAL,
        ];

        return array_merge($options, $overrides);
    }

    /**
     * Save files from a Moodle draft area into a canonical media file area.
     *
     * Permission checks must already have happened in the caller.
     *
     * @param int $draftitemid Draft item id.
     * @param context|int $context Context or context id.
     * @param string $filearea Canonical media file area.
     * @param int $itemid File item id, usually media version id or media id.
     * @param array<string, mixed> $options File API options.
     * @return void
     * @throws moodle_exception
     */
    public static function save_draft_area_files(
        int $draftitemid,
        context|int $context,
        string $filearea,
        int $itemid,
        array $options = []
    ): void {
        global $CFG;

        require_once($CFG->libdir . '/filelib.php');

        $contextid = self::get_contextid($context);
        $filearea = self::require_media_filearea($filearea);
        $itemid = self::require_positive_itemid($itemid);
        $draftitemid = self::require_non_negative_int($draftitemid, 'draftitemid');

        file_save_draft_area_files(
            $draftitemid,
            $contextid,
            self::COMPONENT,
            $filearea,
            $itemid,
            self::get_file_options($filearea, $options)
        );
    }

    /**
     * Create a file in a media file area from a string.
     *
     * Permission checks must already have happened in the caller.
     *
     * @param context|int $context Context or context id.
     * @param string $filearea Canonical media file area.
     * @param int $itemid File item id.
     * @param string $filename File name.
     * @param string $content File content.
     * @param string $filepath File path.
     * @param int|null $userid Optional user id.
     * @return stored_file
     * @throws file_exception
     * @throws moodle_exception
     */
    public static function create_file_from_string(
        context|int $context,
        string $filearea,
        int $itemid,
        string $filename,
        string $content,
        string $filepath = '/',
        ?int $userid = null
    ): stored_file {
        $contextid = self::get_contextid($context);
        $filearea = self::require_media_filearea($filearea);
        $itemid = self::require_positive_itemid($itemid);
        $filename = self::normalise_filename($filename);
        $filepath = self::normalise_filepath($filepath);

        $record = [
            'contextid' => $contextid,
            'component' => self::COMPONENT,
            'filearea' => $filearea,
            'itemid' => $itemid,
            'filepath' => $filepath,
            'filename' => $filename,
            'userid' => $userid,
        ];

        return self::get_file_storage()->create_file_from_string($record, $content);
    }

    /**
     * Create a file in a media file area from a local path.
     *
     * Permission checks must already have happened in the caller.
     *
     * @param context|int $context Context or context id.
     * @param string $filearea Canonical media file area.
     * @param int $itemid File item id.
     * @param string $filename File name.
     * @param string $sourcepath Local source path.
     * @param string $filepath File path.
     * @param int|null $userid Optional user id.
     * @return stored_file
     * @throws file_exception
     * @throws moodle_exception
     */
    public static function create_file_from_pathname(
        context|int $context,
        string $filearea,
        int $itemid,
        string $filename,
        string $sourcepath,
        string $filepath = '/',
        ?int $userid = null
    ): stored_file {
        $contextid = self::get_contextid($context);
        $filearea = self::require_media_filearea($filearea);
        $itemid = self::require_positive_itemid($itemid);
        $filename = self::normalise_filename($filename);
        $filepath = self::normalise_filepath($filepath);

        if ($sourcepath === '' || !is_readable($sourcepath)) {
            throw new invalid_parameter_exception('Source file is not readable.');
        }

        $record = [
            'contextid' => $contextid,
            'component' => self::COMPONENT,
            'filearea' => $filearea,
            'itemid' => $itemid,
            'filepath' => $filepath,
            'filename' => $filename,
            'userid' => $userid,
        ];

        return self::get_file_storage()->create_file_from_pathname($record, $sourcepath);
    }

    /**
     * Return all real files in a media file area.
     *
     * Directory placeholder files are excluded.
     *
     * @param context|int $context Context or context id.
     * @param string $filearea Canonical media file area.
     * @param int $itemid File item id.
     * @param string $sort Sort expression.
     * @param bool $includedirs Include directories.
     * @return stored_file[]
     */
    public static function get_files(
        context|int $context,
        string $filearea,
        int $itemid,
        string $sort = 'filename',
        bool $includedirs = false
    ): array {
        $files = self::get_file_storage()->get_area_files(
            self::get_contextid($context),
            self::COMPONENT,
            self::require_media_filearea($filearea),
            self::require_positive_itemid($itemid),
            $sort,
            $includedirs
        );

        return array_values(array_filter($files, static function(stored_file $file): bool {
            return !$file->is_directory();
        }));
    }

    /**
     * Return the first file in a media file area.
     *
     * @param context|int $context Context or context id.
     * @param string $filearea Canonical media file area.
     * @param int $itemid File item id.
     * @return stored_file|null
     */
    public static function get_first_file(context|int $context, string $filearea, int $itemid): ?stored_file {
        $files = self::get_files($context, $filearea, $itemid, 'sortorder, filename', false);

        return $files[0] ?? null;
    }

    /**
     * Return one stored file by path/name.
     *
     * @param context|int $context Context or context id.
     * @param string $filearea Canonical media file area.
     * @param int $itemid File item id.
     * @param string $filename File name.
     * @param string $filepath File path.
     * @return stored_file|null
     */
    public static function get_file(
        context|int $context,
        string $filearea,
        int $itemid,
        string $filename,
        string $filepath = '/'
    ): ?stored_file {
        return self::get_file_storage()->get_file(
            self::get_contextid($context),
            self::COMPONENT,
            self::require_media_filearea($filearea),
            self::require_positive_itemid($itemid),
            self::normalise_filepath($filepath),
            self::normalise_filename($filename)
        ) ?: null;
    }

    /**
     * Return whether a media file area has at least one file.
     *
     * @param context|int $context Context or context id.
     * @param string $filearea Canonical media file area.
     * @param int $itemid File item id.
     * @return bool
     */
    public static function has_files(context|int $context, string $filearea, int $itemid): bool {
        return self::get_first_file($context, $filearea, $itemid) !== null;
    }

    /**
     * Count real files in a media file area.
     *
     * @param context|int $context Context or context id.
     * @param string $filearea Canonical media file area.
     * @param int $itemid File item id.
     * @return int
     */
    public static function count_files(context|int $context, string $filearea, int $itemid): int {
        return count(self::get_files($context, $filearea, $itemid));
    }

    /**
     * Return a Moodle pluginfile URL for a stored file.
     *
     * Access is still enforced in lib.php pluginfile handling.
     *
     * @param stored_file $file Stored file.
     * @param bool $forcedownload Force download.
     * @return moodle_url
     */
    public static function get_file_url(stored_file $file, bool $forcedownload = false): moodle_url {
        return moodle_url::make_pluginfile_url(
            $file->get_contextid(),
            $file->get_component(),
            $file->get_filearea(),
            $file->get_itemid(),
            $file->get_filepath(),
            $file->get_filename(),
            $forcedownload
        );
    }

    /**
     * Return pluginfile URL for the first file in a media area.
     *
     * @param context|int $context Context or context id.
     * @param string $filearea Canonical media file area.
     * @param int $itemid File item id.
     * @param bool $forcedownload Force download.
     * @return moodle_url|null
     */
    public static function get_first_file_url(
        context|int $context,
        string $filearea,
        int $itemid,
        bool $forcedownload = false
    ): ?moodle_url {
        $file = self::get_first_file($context, $filearea, $itemid);

        return $file ? self::get_file_url($file, $forcedownload) : null;
    }

    /**
     * Return metadata for a stored file.
     *
     * @param stored_file $file Stored file.
     * @param bool $includeurl Include pluginfile URL.
     * @return array<string, mixed>
     */
    public static function get_file_metadata(stored_file $file, bool $includeurl = true): array {
        $metadata = [
            'contextid' => $file->get_contextid(),
            'component' => $file->get_component(),
            'filearea' => $file->get_filearea(),
            'itemid' => $file->get_itemid(),
            'filepath' => $file->get_filepath(),
            'filename' => $file->get_filename(),
            'filesize' => $file->get_filesize(),
            'mimetype' => $file->get_mimetype(),
            'contenthash' => $file->get_contenthash(),
            'pathnamehash' => $file->get_pathnamehash(),
            'userid' => $file->get_userid(),
            'timecreated' => $file->get_timecreated(),
            'timemodified' => $file->get_timemodified(),
            'sortorder' => $file->get_sortorder(),
            'isimage' => $file->is_valid_image(),
            'isgenerated' => self::is_generated_area($file->get_filearea()),
        ];

        if ($includeurl) {
            $metadata['url'] = self::get_file_url($file)->out(false);
            $metadata['downloadurl'] = self::get_file_url($file, true)->out(false);
        }

        return $metadata;
    }

    /**
     * Return metadata for all files in an area.
     *
     * @param context|int $context Context or context id.
     * @param string $filearea Canonical media file area.
     * @param int $itemid File item id.
     * @param bool $includeurls Include pluginfile URLs.
     * @return array<int, array<string, mixed>>
     */
    public static function get_area_metadata(
        context|int $context,
        string $filearea,
        int $itemid,
        bool $includeurls = true
    ): array {
        return array_map(
            static fn(stored_file $file): array => self::get_file_metadata($file, $includeurls),
            self::get_files($context, $filearea, $itemid)
        );
    }

    /**
     * Delete all files in one media file area.
     *
     * Policy checks must already have approved deletion.
     *
     * @param context|int $context Context or context id.
     * @param string $filearea Canonical media file area.
     * @param int $itemid File item id.
     * @return void
     */
    public static function delete_area_files(context|int $context, string $filearea, int $itemid): void {
        self::get_file_storage()->delete_area_files(
            self::get_contextid($context),
            self::COMPONENT,
            self::require_media_filearea($filearea),
            self::require_positive_itemid($itemid)
        );
    }

    /**
     * Delete all media file areas for one item id.
     *
     * Policy checks must already have approved deletion.
     *
     * @param context|int $context Context or context id.
     * @param int $itemid File item id.
     * @return void
     */
    public static function delete_all_media_area_files(context|int $context, int $itemid): void {
        foreach (self::get_media_fileareas() as $filearea) {
            self::delete_area_files($context, $filearea, $itemid);
        }
    }

    /**
     * Copy all files from one media area/item to another media area/item.
     *
     * Permission and policy checks must already have happened in the caller.
     *
     * @param context|int $sourcecontext Source context or context id.
     * @param string $sourcefilearea Source file area.
     * @param int $sourceitemid Source item id.
     * @param context|int $targetcontext Target context or context id.
     * @param string $targetfilearea Target file area.
     * @param int $targetitemid Target item id.
     * @param int|null $userid Optional new user id.
     * @return stored_file[]
     */
    public static function copy_area_files(
        context|int $sourcecontext,
        string $sourcefilearea,
        int $sourceitemid,
        context|int $targetcontext,
        string $targetfilearea,
        int $targetitemid,
        ?int $userid = null
    ): array {
        $fs = self::get_file_storage();
        $created = [];

        foreach (self::get_files($sourcecontext, $sourcefilearea, $sourceitemid) as $sourcefile) {
            $record = [
                'contextid' => self::get_contextid($targetcontext),
                'component' => self::COMPONENT,
                'filearea' => self::require_media_filearea($targetfilearea),
                'itemid' => self::require_positive_itemid($targetitemid),
                'filepath' => $sourcefile->get_filepath(),
                'filename' => $sourcefile->get_filename(),
                'userid' => $userid ?? $sourcefile->get_userid(),
                'sortorder' => $sourcefile->get_sortorder(),
            ];

            $created[] = $fs->create_file_from_storedfile($record, $sourcefile);
        }

        return $created;
    }

    /**
     * Prepare a draft area from an existing media file area.
     *
     * This is used by forms before editing files.
     *
     * @param int $draftitemid Draft item id.
     * @param context|int $context Context or context id.
     * @param string $filearea Canonical media file area.
     * @param int $itemid File item id.
     * @param array<string, mixed> $options File manager/editor options.
     * @return int Draft item id.
     */
    public static function prepare_draft_area(
        int $draftitemid,
        context|int $context,
        string $filearea,
        int $itemid,
        array $options = []
    ): int {
        global $CFG;

        require_once($CFG->libdir . '/filelib.php');

        $draftitemid = self::require_non_negative_int($draftitemid, 'draftitemid');
        $filearea = self::require_media_filearea($filearea);
        $itemid = self::require_positive_itemid($itemid);
        $contextid = self::get_contextid($context);
        $options = self::get_file_options($filearea, $options);

        file_prepare_draft_area(
            $draftitemid,
            $contextid,
            self::COMPONENT,
            $filearea,
            $itemid,
            $options
        );

        return $draftitemid;
    }

    /**
     * Return default max files for one media file area.
     *
     * @param string $filearea File area.
     * @return int
     */
    private static function get_default_maxfiles(string $filearea): int {
        $filearea = self::require_media_filearea($filearea);

        return match ($filearea) {
            self::AREA_ORIGINAL,
            self::AREA_PREVIEW,
            self::AREA_THUMBNAIL => 1,
            default => -1,
        };
    }

    /**
     * Return default accepted file types for one media file area.
     *
     * @param string $filearea File area.
     * @return string[]|string
     */
    private static function get_default_accepted_types(string $filearea): array|string {
        $filearea = self::require_media_filearea($filearea);

        return match ($filearea) {
            self::AREA_THUMBNAIL => ['image'],
            self::AREA_CAPTION => ['.vtt', '.srt', '.sbv', '.sub', '.ttml', '.dfxp'],
            self::AREA_TRANSCRIPT => ['.txt', '.md', '.pdf', '.doc', '.docx', '.odt'],
            default => '*',
        };
    }

    /**
     * Return Moodle file storage instance.
     *
     * @return file_storage
     */
    private static function get_file_storage(): file_storage {
        return get_file_storage();
    }

    /**
     * Return context id from context object or id.
     *
     * @param context|int $context Context or context id.
     * @return int
     */
    private static function get_contextid(context|int $context): int {
        $contextid = $context instanceof context ? (int)$context->id : (int)$context;

        if ($contextid <= 0) {
            throw new invalid_parameter_exception('Invalid context id.');
        }

        return $contextid;
    }

    /**
     * Return module context id from course module id.
     *
     * @param int $cmid Course module id.
     * @return int
     */
    public static function get_contextid_from_cmid(int $cmid): int {
        $cmid = self::require_positive_itemid($cmid);

        return (int)context_module::instance($cmid)->id;
    }

    /**
     * Normalise file area.
     *
     * @param string $filearea Raw file area.
     * @return string
     */
    private static function normalise_filearea(string $filearea): string {
        return clean_param($filearea, PARAM_ALPHANUMEXT);
    }

    /**
     * Normalise filename.
     *
     * @param string $filename Raw filename.
     * @return string
     */
    private static function normalise_filename(string $filename): string {
        $filename = trim($filename);

        if ($filename === '' || $filename === '.' || $filename === '..') {
            throw new invalid_parameter_exception('Invalid filename.');
        }

        return clean_param($filename, PARAM_FILE);
    }

    /**
     * Normalise File API filepath.
     *
     * @param string $filepath Raw filepath.
     * @return string
     */
    private static function normalise_filepath(string $filepath): string {
        $filepath = trim($filepath);
        if ($filepath === '') {
            $filepath = '/';
        }

        if ($filepath[0] !== '/') {
            $filepath = '/' . $filepath;
        }

        if (substr($filepath, -1) !== '/') {
            $filepath .= '/';
        }

        return clean_param($filepath, PARAM_PATH);
    }

    /**
     * Require a positive File API item id.
     *
     * @param int $itemid Item id.
     * @return int
     */
    private static function require_positive_itemid(int $itemid): int {
        if ($itemid <= 0) {
            throw new invalid_parameter_exception('Invalid media file item id.');
        }

        return $itemid;
    }

    /**
     * Require a non-negative integer.
     *
     * @param int $value Value.
     * @param string $name Parameter name.
     * @return int
     */
    private static function require_non_negative_int(int $value, string $name): int {
        if ($value < 0) {
            throw new invalid_parameter_exception('Invalid ' . $name . '.');
        }

        return $value;
    }
}
