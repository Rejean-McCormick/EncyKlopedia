<?php
// This file is part of Moodle - https://moodle.org/
//
// Moodle is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// any later version.

/**
 * Scheduled task that generates missing media thumbnails.
 *
 * @package    mod_uckkarchive
 * @copyright  2026 Univers-Cité King Klown
 * @license    https://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later
 */

declare(strict_types=1);

namespace mod_uckkarchive\task;

defined('MOODLE_INTERNAL') || die();

use core\task\scheduled_task;
use dml_exception;
use moodle_exception;
use stored_file;
use stdClass;

/**
 * Generate thumbnails for media records that do not yet have thumbnails.
 *
 * This task is intentionally conservative:
 *
 * - it only generates thumbnails for image media;
 * - it never changes the original media file;
 * - it stores generated thumbnails in the Moodle File API;
 * - it skips restricted/cultural/integrity media unless generation is explicitly safe;
 * - it processes a small batch per run to avoid long cron execution;
 * - it degrades safely when GD, WebP support, or the media tables are unavailable.
 */
final class generate_media_thumbnails extends scheduled_task {
    /** Plugin component. */
    private const COMPONENT = 'mod_uckkarchive';

    /** Media table. */
    private const TABLE_MEDIA = 'uckkarchive_media';

    /** Original media file area. */
    private const AREA_ORIGINAL = 'media_original';

    /** Thumbnail media file area. */
    private const AREA_THUMBNAIL = 'media_thumbnail';

    /** Default maximum records processed per cron run. */
    private const DEFAULT_BATCH_SIZE = 25;

    /** Maximum generated thumbnail width. */
    private const MAX_WIDTH = 480;

    /** Maximum generated thumbnail height. */
    private const MAX_HEIGHT = 480;

    /** Generated thumbnail MIME type. */
    private const THUMBNAIL_MIMETYPE = 'image/jpeg';

    /** Generated thumbnail filename. */
    private const THUMBNAIL_FILENAME = 'thumbnail.jpg';

    /**
     * Return task name.
     *
     * @return string
     */
    public function get_name(): string {
        $manager = get_string_manager();

        if ($manager->string_exists('task:generatemediathumbnails', 'uckkarchive')) {
            return get_string('task:generatemediathumbnails', 'uckkarchive');
        }

        if ($manager->string_exists('taskgeneratemediathumbnails', 'uckkarchive')) {
            return get_string('taskgeneratemediathumbnails', 'uckkarchive');
        }

        return 'Generate UCKK Archive media thumbnails';
    }

    /**
     * Execute task.
     *
     * @return void
     */
    public function execute(): void {
        if (!extension_loaded('gd')) {
            mtrace('UCKK Archive media thumbnails: GD extension is not available; skipping.');
            return;
        }

        if (!self::table_exists(self::TABLE_MEDIA)) {
            mtrace('UCKK Archive media thumbnails: media table does not exist; skipping.');
            return;
        }

        $records = $this->load_candidate_media(self::DEFAULT_BATCH_SIZE);

        if (empty($records)) {
            mtrace('UCKK Archive media thumbnails: no candidate media found.');
            return;
        }

        $created = 0;
        $skipped = 0;
        $failed = 0;

        foreach ($records as $media) {
            try {
                $result = $this->process_media($media);

                if ($result === true) {
                    $created++;
                } else {
                    $skipped++;
                }
            } catch (\Throwable $exception) {
                $failed++;
                mtrace('UCKK Archive media thumbnails: failed for media id ' . (int)$media->id . ': ' . $exception->getMessage());
            }
        }

        mtrace(
            'UCKK Archive media thumbnails: created=' . $created .
            ', skipped=' . $skipped .
            ', failed=' . $failed . '.'
        );
    }

    /**
     * Load media records that may need thumbnails.
     *
     * @param int $limit Maximum records.
     * @return stdClass[]
     * @throws dml_exception
     */
    private function load_candidate_media(int $limit): array {
        global $DB;

        $columns = $DB->get_columns(self::TABLE_MEDIA);
        $where = [];
        $params = [];

        if (array_key_exists('status', $columns)) {
            $where[] = 'status <> :deletedsoft';
            $params['deletedsoft'] = 'deleted_soft';
        }

        if (array_key_exists('mediatype', $columns) && array_key_exists('mimetype', $columns)) {
            $where[] = '(mediatype = :mediatypeimage OR ' . $DB->sql_like('mimetype', ':mimetypeimage', false, false) . ')';
            $params['mediatypeimage'] = 'image';
            $params['mimetypeimage'] = 'image/%';
        } else if (array_key_exists('type', $columns) && array_key_exists('mimetype', $columns)) {
            $where[] = '(type = :mediatypeimage OR ' . $DB->sql_like('mimetype', ':mimetypeimage', false, false) . ')';
            $params['mediatypeimage'] = 'image';
            $params['mimetypeimage'] = 'image/%';
        } else if (array_key_exists('mediatype', $columns)) {
            $where[] = 'mediatype = :mediatypeimage';
            $params['mediatypeimage'] = 'image';
        } else if (array_key_exists('type', $columns)) {
            $where[] = 'type = :mediatypeimage';
            $params['mediatypeimage'] = 'image';
        } else if (array_key_exists('mimetype', $columns)) {
            $where[] = $DB->sql_like('mimetype', ':mimetypeimage', false, false);
            $params['mimetypeimage'] = 'image/%';
        }

        if (array_key_exists('visibility', $columns)) {
            $where[] = 'visibility NOT IN (:restricted, :restrictedintegrity, :restrictedcultural)';
            $params['restricted'] = 'restricted';
            $params['restrictedintegrity'] = 'restricted_integrity';
            $params['restrictedcultural'] = 'restricted_cultural';
        }

        if (array_key_exists('restricted', $columns)) {
            $where[] = '(restricted = 0 OR restricted IS NULL)';
        }

        if (array_key_exists('culturalprotocol', $columns)) {
            $where[] = '(culturalprotocol = 0 OR culturalprotocol IS NULL)';
        }

        $wheresql = empty($where) ? '1 = 1' : implode(' AND ', $where);
        $sort = array_key_exists('timemodified', $columns) ? 'timemodified ASC, id ASC' : 'id ASC';

        $sql = "SELECT *
                  FROM {" . self::TABLE_MEDIA . "}
                 WHERE {$wheresql}
              ORDER BY {$sort}";

        return array_values($DB->get_records_sql($sql, $params, 0, max(1, $limit)));
    }

    /**
     * Process one media record.
     *
     * @param stdClass $media Media record.
     * @return bool True when thumbnail was created.
     */
    private function process_media(stdClass $media): bool {
        $contextid = $this->resolve_contextid($media);
        if ($contextid <= 0) {
            mtrace('UCKK Archive media thumbnails: media id ' . (int)$media->id . ' has no resolvable context.');
            return false;
        }

        if ($this->has_thumbnail($contextid, (int)$media->id)) {
            return false;
        }

        $original = $this->get_original_file($contextid, (int)$media->id);
        if (!$original) {
            return false;
        }

        if (!$this->is_supported_image($original)) {
            return false;
        }

        $thumbnailpath = $this->create_thumbnail_file($original);
        if ($thumbnailpath === '') {
            return false;
        }

        try {
            $this->store_thumbnail($contextid, (int)$media->id, $thumbnailpath, (int)($media->createdby ?? 0));
        } finally {
            if (is_file($thumbnailpath)) {
                @unlink($thumbnailpath);
            }
        }

        $this->mark_media_updated($media);

        return true;
    }

    /**
     * Resolve context id for a media record.
     *
     * @param stdClass $media Media record.
     * @return int
     */
    private function resolve_contextid(stdClass $media): int {
        if (!empty($media->contextid)) {
            return (int)$media->contextid;
        }

        if (!empty($media->cmid)) {
            $context = \context_module::instance((int)$media->cmid, IGNORE_MISSING);
            return $context ? (int)$context->id : 0;
        }

        return 0;
    }

    /**
     * Return whether media already has a thumbnail.
     *
     * @param int $contextid Context id.
     * @param int $mediaid Media id.
     * @return bool
     */
    private function has_thumbnail(int $contextid, int $mediaid): bool {
        $fs = get_file_storage();

        $files = $fs->get_area_files(
            $contextid,
            self::COMPONENT,
            self::AREA_THUMBNAIL,
            $mediaid,
            'filename',
            false
        );

        foreach ($files as $file) {
            if (!$file->is_directory()) {
                return true;
            }
        }

        return false;
    }

    /**
     * Return original stored file for a media record.
     *
     * @param int $contextid Context id.
     * @param int $mediaid Media id.
     * @return stored_file|null
     */
    private function get_original_file(int $contextid, int $mediaid): ?stored_file {
        $fs = get_file_storage();

        $files = $fs->get_area_files(
            $contextid,
            self::COMPONENT,
            self::AREA_ORIGINAL,
            $mediaid,
            'filename',
            false
        );

        foreach ($files as $file) {
            if (!$file->is_directory()) {
                return $file;
            }
        }

        return null;
    }

    /**
     * Return whether the file is a supported image.
     *
     * @param stored_file $file Stored file.
     * @return bool
     */
    private function is_supported_image(stored_file $file): bool {
        $mimetype = strtolower((string)$file->get_mimetype());

        if (in_array($mimetype, ['image/jpeg', 'image/jpg', 'image/png', 'image/gif'], true)) {
            return true;
        }

        if ($mimetype === 'image/webp') {
            return function_exists('imagecreatefromwebp');
        }

        return false;
    }

    /**
     * Create temporary thumbnail file from stored file.
     *
     * @param stored_file $file Original file.
     * @return string Temporary path, or empty string when skipped.
     */
    private function create_thumbnail_file(stored_file $file): string {
        $sourcepath = make_request_directory() . '/uckkarchive-thumbnail-source-' . uniqid('', true);
        $targetpath = make_request_directory() . '/uckkarchive-thumbnail-' . uniqid('', true) . '.jpg';

        $file->copy_content_to($sourcepath);

        try {
            $source = $this->create_image_resource($sourcepath, (string)$file->get_mimetype());
            if (!$source) {
                return '';
            }

            $sourcewidth = imagesx($source);
            $sourceheight = imagesy($source);

            if ($sourcewidth <= 0 || $sourceheight <= 0) {
                imagedestroy($source);
                return '';
            }

            [$targetwidth, $targetheight] = $this->calculate_dimensions($sourcewidth, $sourceheight);

            $target = imagecreatetruecolor($targetwidth, $targetheight);
            if (!$target) {
                imagedestroy($source);
                return '';
            }

            $background = imagecolorallocate($target, 255, 255, 255);
            if ($background !== false) {
                imagefill($target, 0, 0, $background);
            }

            imagecopyresampled(
                $target,
                $source,
                0,
                0,
                0,
                0,
                $targetwidth,
                $targetheight,
                $sourcewidth,
                $sourceheight
            );

            $saved = imagejpeg($target, $targetpath, 85);

            imagedestroy($source);
            imagedestroy($target);

            return $saved && is_file($targetpath) ? $targetpath : '';
        } finally {
            if (is_file($sourcepath)) {
                @unlink($sourcepath);
            }
        }
    }

    /**
     * Create GD image resource from file.
     *
     * @param string $path Path.
     * @param string $mimetype MIME type.
     * @return \GdImage|resource|false
     */
    private function create_image_resource(string $path, string $mimetype) {
        $mimetype = strtolower($mimetype);

        if ($mimetype === 'image/jpeg' || $mimetype === 'image/jpg') {
            return @imagecreatefromjpeg($path);
        }

        if ($mimetype === 'image/png') {
            return @imagecreatefrompng($path);
        }

        if ($mimetype === 'image/gif') {
            return @imagecreatefromgif($path);
        }

        if ($mimetype === 'image/webp' && function_exists('imagecreatefromwebp')) {
            return @imagecreatefromwebp($path);
        }

        return false;
    }

    /**
     * Calculate thumbnail dimensions.
     *
     * @param int $width Source width.
     * @param int $height Source height.
     * @return int[]
     */
    private function calculate_dimensions(int $width, int $height): array {
        $ratio = min(self::MAX_WIDTH / $width, self::MAX_HEIGHT / $height, 1);

        return [
            max(1, (int)round($width * $ratio)),
            max(1, (int)round($height * $ratio)),
        ];
    }

    /**
     * Store thumbnail in Moodle File API.
     *
     * @param int $contextid Context id.
     * @param int $mediaid Media id.
     * @param string $thumbnailpath Thumbnail temp path.
     * @param int $userid User id.
     * @return void
     */
    private function store_thumbnail(int $contextid, int $mediaid, string $thumbnailpath, int $userid): void {
        $fs = get_file_storage();

        $fs->delete_area_files($contextid, self::COMPONENT, self::AREA_THUMBNAIL, $mediaid);

        $filerecord = [
            'contextid' => $contextid,
            'component' => self::COMPONENT,
            'filearea' => self::AREA_THUMBNAIL,
            'itemid' => $mediaid,
            'filepath' => '/',
            'filename' => self::THUMBNAIL_FILENAME,
            'userid' => $userid > 0 ? $userid : null,
        ];

        $fs->create_file_from_pathname($filerecord, $thumbnailpath);
    }

    /**
     * Update media bookkeeping fields when available.
     *
     * @param stdClass $media Media record.
     * @return void
     */
    private function mark_media_updated(stdClass $media): void {
        global $DB;

        $columns = $DB->get_columns(self::TABLE_MEDIA);
        $update = new stdClass();
        $update->id = (int)$media->id;

        if (array_key_exists('hasthumbnail', $columns)) {
            $update->hasthumbnail = 1;
        }

        if (array_key_exists('thumbnailgenerated', $columns)) {
            $update->thumbnailgenerated = 1;
        }

        if (array_key_exists('thumbnailtimecreated', $columns)) {
            $update->thumbnailtimecreated = time();
        }

        if (array_key_exists('timemodified', $columns)) {
            $update->timemodified = time();
        }

        if (count(get_object_vars($update)) > 1) {
            $DB->update_record(self::TABLE_MEDIA, $update);
        }
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

