<?php
// This file is part of Moodle - https://moodle.org/
//
// Moodle is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// any later version.

/**
 * Scheduled task to generate media derivative files.
 *
 * @package    mod_uckkarchive
 * @copyright  2026 Univers-Cité King Klown
 * @license    https://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later
 */

declare(strict_types=1);

namespace mod_uckkarchive\task;

defined('MOODLE_INTERNAL') || die();

/**
 * Generate media derivatives for archive media files.
 *
 * This task is deliberately conservative:
 *
 * - it only uses Moodle File API;
 * - it never writes to unmanaged public folders;
 * - it is idempotent;
 * - it does not bypass pluginfile access control;
 * - it generates image derivatives only when PHP GD can safely process them;
 * - it leaves video/audio/PDF derivatives to future specialist workers.
 *
 * Generated derivatives are stored in:
 *
 * ```text
 * component = mod_uckkarchive
 * filearea  = media_derivative
 * itemid    = media id, falling back to version id when source file does
 * ```
 */
final class generate_media_derivatives extends \core\task\scheduled_task {
    /** Component name. */
    private const COMPONENT = 'mod_uckkarchive';

    /** Media table. */
    private const TABLE_MEDIA = 'uckkarchive_media';

    /** Media version table. */
    private const TABLE_VERSION = 'uckkarchive_media_version';

    /** Original file area. */
    private const AREA_ORIGINAL = 'media_original';

    /** Derivative file area. */
    private const AREA_DERIVATIVE = 'media_derivative';

    /** Preview file area. */
    private const AREA_PREVIEW = 'media_preview';

    /** Default batch limit. */
    private const DEFAULT_BATCH_LIMIT = 50;

    /** Default maximum derivative width. */
    private const DEFAULT_MAX_WIDTH = 1920;

    /** Default maximum derivative height. */
    private const DEFAULT_MAX_HEIGHT = 1920;

    /** Default preview maximum width. */
    private const DEFAULT_PREVIEW_MAX_WIDTH = 1280;

    /** Default preview maximum height. */
    private const DEFAULT_PREVIEW_MAX_HEIGHT = 1280;

    /**
     * Return task name.
     *
     * @return string
     */
    public function get_name(): string {
        return get_string('task:generatemediaderivatives', 'uckkarchive');
    }

    /**
     * Execute task.
     *
     * @return void
     */
    public function execute(): void {
        global $DB;

        if (!self::table_exists(self::TABLE_MEDIA)) {
            mtrace('mod_uckkarchive: media table does not exist; derivative generation skipped.');
            return;
        }

        if (!extension_loaded('gd')) {
            mtrace('mod_uckkarchive: PHP GD extension is not loaded; derivative generation skipped.');
            return;
        }

        $limit = self::get_batch_limit();
        $records = self::get_candidate_media($limit);

        if (empty($records)) {
            mtrace('mod_uckkarchive: no media records need derivative processing.');
            return;
        }

        $processed = 0;
        $generated = 0;
        $skipped = 0;
        $failed = 0;

        foreach ($records as $media) {
            $processed++;

            try {
                $result = self::process_media($media);
                $generated += $result['generated'];
                $skipped += $result['skipped'];
            } catch (\Throwable $exception) {
                $failed++;
                mtrace('mod_uckkarchive: derivative generation failed for media ' . (int)$media->id .
                    ': ' . $exception->getMessage());
            }
        }

        mtrace('mod_uckkarchive: derivative task complete. ' .
            'processed=' . $processed . ', ' .
            'generated=' . $generated . ', ' .
            'skipped=' . $skipped . ', ' .
            'failed=' . $failed . '.');
    }

    /**
     * Process one media record.
     *
     * @param \stdClass $media Media record.
     * @return array{generated:int,skipped:int}
     */
    private static function process_media(\stdClass $media): array {
        $contextid = self::resolve_contextid($media);
        if ($contextid <= 0) {
            mtrace('mod_uckkarchive: media ' . (int)$media->id . ' has no resolvable context; skipped.');
            return ['generated' => 0, 'skipped' => 1];
        }

        $sourcefiles = self::get_original_files($contextid, $media);

        if (empty($sourcefiles)) {
            return ['generated' => 0, 'skipped' => 1];
        }

        $generated = 0;
        $skipped = 0;

        foreach ($sourcefiles as $sourcefile) {
            if (!self::is_supported_image($sourcefile)) {
                $skipped++;
                continue;
            }

            if (self::generate_derivative($sourcefile, self::AREA_DERIVATIVE, self::DEFAULT_MAX_WIDTH, self::DEFAULT_MAX_HEIGHT)) {
                $generated++;
            } else {
                $skipped++;
            }

            if (self::generate_derivative(
                $sourcefile,
                self::AREA_PREVIEW,
                self::DEFAULT_PREVIEW_MAX_WIDTH,
                self::DEFAULT_PREVIEW_MAX_HEIGHT
            )) {
                $generated++;
            }
        }

        self::mark_media_processed($media, $generated, $skipped);

        return [
            'generated' => $generated,
            'skipped' => $skipped,
        ];
    }

    /**
     * Generate one derivative file.
     *
     * @param \stored_file $sourcefile Source file.
     * @param string $targetarea Target file area.
     * @param int $maxwidth Maximum width.
     * @param int $maxheight Maximum height.
     * @return bool True when a file was generated, false when skipped.
     */
    private static function generate_derivative(
        \stored_file $sourcefile,
        string $targetarea,
        int $maxwidth,
        int $maxheight
    ): bool {
        $targetfilename = self::target_filename($sourcefile, $targetarea);
        $fs = get_file_storage();

        if ($fs->file_exists(
            $sourcefile->get_contextid(),
            self::COMPONENT,
            $targetarea,
            $sourcefile->get_itemid(),
            '/',
            $targetfilename
        )) {
            return false;
        }

        $sourcecontent = $sourcefile->get_content();
        $image = @imagecreatefromstring($sourcecontent);

        if (!$image) {
            return false;
        }

        $sourcewidth = imagesx($image);
        $sourceheight = imagesy($image);

        if ($sourcewidth <= 0 || $sourceheight <= 0) {
            imagedestroy($image);
            return false;
        }

        [$targetwidth, $targetheight] = self::target_dimensions($sourcewidth, $sourceheight, $maxwidth, $maxheight);

        if ($targetwidth <= 0 || $targetheight <= 0) {
            imagedestroy($image);
            return false;
        }

        $target = imagecreatetruecolor($targetwidth, $targetheight);

        if (!$target) {
            imagedestroy($image);
            return false;
        }

        self::preserve_transparency($image, $target, $sourcefile->get_mimetype());

        $resampled = imagecopyresampled(
            $target,
            $image,
            0,
            0,
            0,
            0,
            $targetwidth,
            $targetheight,
            $sourcewidth,
            $sourceheight
        );

        if (!$resampled) {
            imagedestroy($image);
            imagedestroy($target);
            return false;
        }

        $tempfile = make_request_directory() . '/' . uniqid('uckkarchive_derivative_', true);
        $written = self::write_image($target, $tempfile, $sourcefile->get_mimetype());

        imagedestroy($image);
        imagedestroy($target);

        if (!$written || !is_readable($tempfile)) {
            @unlink($tempfile);
            return false;
        }

        $filerecord = [
            'contextid' => $sourcefile->get_contextid(),
            'component' => self::COMPONENT,
            'filearea' => $targetarea,
            'itemid' => $sourcefile->get_itemid(),
            'filepath' => '/',
            'filename' => $targetfilename,
            'userid' => self::get_system_userid(),
            'author' => get_string('pluginname', 'uckkarchive'),
            'license' => $sourcefile->get_license(),
            'source' => 'generated-from:' . $sourcefile->get_contenthash(),
        ];

        $fs->create_file_from_pathname($filerecord, $tempfile);
        @unlink($tempfile);

        mtrace('mod_uckkarchive: generated ' . $targetarea . ' file ' . $targetfilename .
            ' for source ' . $sourcefile->get_filename() . '.');

        return true;
    }

    /**
     * Return candidate media records.
     *
     * @param int $limit Limit.
     * @return \stdClass[]
     */
    private static function get_candidate_media(int $limit): array {
        global $DB;

        $columns = $DB->get_columns(self::TABLE_MEDIA);
        $where = [];
        $params = [];

        if (array_key_exists('status', $columns)) {
            [$insql, $inparams] = $DB->get_in_or_equal([
                'draft',
                'submitted',
                'active',
                'restricted',
            ], SQL_PARAMS_NAMED, 'status');
            $where[] = 'status ' . $insql;
            $params += $inparams;
        }

        if (array_key_exists('mediatype', $columns)) {
            [$insql, $inparams] = $DB->get_in_or_equal([
                'image',
                'thumbnail',
                'preview',
                'derivative',
            ], SQL_PARAMS_NAMED, 'type');
            $where[] = 'mediatype ' . $insql;
            $params += $inparams;
        }

        $wheresql = empty($where) ? '1 = 1' : implode(' AND ', $where);

        $sort = 'id ASC';
        if (array_key_exists('timemodified', $columns)) {
            $sort = 'timemodified ASC, id ASC';
        }

        return array_values($DB->get_records_select(self::TABLE_MEDIA, $wheresql, $params, $sort, '*', 0, $limit));
    }

    /**
     * Return original files for a media record.
     *
     * @param int $contextid Context id.
     * @param \stdClass $media Media record.
     * @return \stored_file[]
     */
    private static function get_original_files(int $contextid, \stdClass $media): array {
        $fs = get_file_storage();

        $itemids = [
            (int)$media->id,
        ];

        if (!empty($media->currentversionid)) {
            $itemids[] = (int)$media->currentversionid;
        }

        if (self::table_exists(self::TABLE_VERSION)) {
            $currentversionid = self::get_current_versionid((int)$media->id);
            if ($currentversionid > 0) {
                $itemids[] = $currentversionid;
            }
        }

        $itemids = array_values(array_unique(array_filter($itemids)));
        $files = [];

        foreach ($itemids as $itemid) {
            $storedfiles = $fs->get_area_files(
                $contextid,
                self::COMPONENT,
                self::AREA_ORIGINAL,
                $itemid,
                'filename',
                false
            );

            foreach ($storedfiles as $file) {
                if ($file->is_directory()) {
                    continue;
                }

                $files[$file->get_contenthash() . ':' . $file->get_filename()] = $file;
            }
        }

        return array_values($files);
    }

    /**
     * Return current version id for media.
     *
     * @param int $mediaid Media id.
     * @return int
     */
    private static function get_current_versionid(int $mediaid): int {
        global $DB;

        if (!self::table_exists(self::TABLE_VERSION)) {
            return 0;
        }

        $columns = $DB->get_columns(self::TABLE_VERSION);

        if (array_key_exists('iscurrent', $columns)) {
            $record = $DB->get_record(self::TABLE_VERSION, ['mediaid' => $mediaid, 'iscurrent' => 1], 'id', IGNORE_MULTIPLE);
            return $record ? (int)$record->id : 0;
        }

        if (array_key_exists('versionno', $columns)) {
            $record = $DB->get_record_sql(
                'SELECT id
                   FROM {' . self::TABLE_VERSION . '}
                  WHERE mediaid = :mediaid
               ORDER BY versionno DESC, id DESC',
                ['mediaid' => $mediaid],
                IGNORE_MULTIPLE
            );
            return $record ? (int)$record->id : 0;
        }

        $record = $DB->get_record_sql(
            'SELECT id
               FROM {' . self::TABLE_VERSION . '}
              WHERE mediaid = :mediaid
           ORDER BY id DESC',
            ['mediaid' => $mediaid],
            IGNORE_MULTIPLE
        );

        return $record ? (int)$record->id : 0;
    }

    /**
     * Mark media as processed when metadata columns are present.
     *
     * @param \stdClass $media Media.
     * @param int $generated Generated count.
     * @param int $skipped Skipped count.
     * @return void
     */
    private static function mark_media_processed(\stdClass $media, int $generated, int $skipped): void {
        global $DB;

        $columns = $DB->get_columns(self::TABLE_MEDIA);
        $update = new \stdClass();
        $update->id = (int)$media->id;
        $changed = false;

        if (array_key_exists('timemodified', $columns)) {
            $update->timemodified = time();
            $changed = true;
        }

        if (array_key_exists('metadata', $columns)) {
            $metadata = self::decode_metadata($media->metadata ?? null);
            $metadata['derivative_task'] = [
                'lastprocessed' => time(),
                'generated' => $generated,
                'skipped' => $skipped,
            ];
            $update->metadata = self::encode_metadata($metadata);
            $changed = true;
        }

        if ($changed) {
            $DB->update_record(self::TABLE_MEDIA, $update);
        }
    }

    /**
     * Resolve context id for media.
     *
     * @param \stdClass $media Media.
     * @return int
     */
    private static function resolve_contextid(\stdClass $media): int {
        if (!empty($media->contextid)) {
            return (int)$media->contextid;
        }

        if (!empty($media->cmid)) {
            try {
                return \context_module::instance((int)$media->cmid)->id;
            } catch (\Throwable $exception) {
                return 0;
            }
        }

        return 0;
    }

    /**
     * Return target derivative filename.
     *
     * @param \stored_file $sourcefile Source file.
     * @param string $targetarea Target file area.
     * @return string
     */
    private static function target_filename(\stored_file $sourcefile, string $targetarea): string {
        $filename = $sourcefile->get_filename();
        $extension = strtolower(pathinfo($filename, PATHINFO_EXTENSION));
        $basename = pathinfo($filename, PATHINFO_FILENAME);

        if ($extension === '') {
            $extension = self::extension_from_mimetype($sourcefile->get_mimetype());
        }

        $suffix = $targetarea === self::AREA_PREVIEW ? 'preview' : 'derivative';
        $hash = substr($sourcefile->get_contenthash(), 0, 12);

        $basename = clean_filename($basename);
        if ($basename === '') {
            $basename = 'media';
        }

        return $basename . '-' . $suffix . '-' . $hash . '.' . $extension;
    }

    /**
     * Return target image dimensions.
     *
     * @param int $width Source width.
     * @param int $height Source height.
     * @param int $maxwidth Max width.
     * @param int $maxheight Max height.
     * @return int[]
     */
    private static function target_dimensions(int $width, int $height, int $maxwidth, int $maxheight): array {
        if ($width <= $maxwidth && $height <= $maxheight) {
            return [$width, $height];
        }

        $ratio = min($maxwidth / $width, $maxheight / $height);

        return [
            max(1, (int)floor($width * $ratio)),
            max(1, (int)floor($height * $ratio)),
        ];
    }

    /**
     * Preserve alpha transparency when possible.
     *
     * @param resource|\GdImage $source Source image.
     * @param resource|\GdImage $target Target image.
     * @param string $mimetype MIME type.
     * @return void
     */
    private static function preserve_transparency($source, $target, string $mimetype): void {
        if (!in_array($mimetype, ['image/png', 'image/gif', 'image/webp'], true)) {
            return;
        }

        imagealphablending($target, false);
        imagesavealpha($target, true);

        $transparent = imagecolorallocatealpha($target, 0, 0, 0, 127);
        imagefilledrectangle($target, 0, 0, imagesx($target), imagesy($target), $transparent);

        if ($mimetype === 'image/gif') {
            $transparentindex = imagecolortransparent($source);

            if ($transparentindex >= 0) {
                $color = imagecolorsforindex($source, $transparentindex);
                $transparentcolor = imagecolorallocate(
                    $target,
                    (int)$color['red'],
                    (int)$color['green'],
                    (int)$color['blue']
                );
                imagefill($target, 0, 0, $transparentcolor);
                imagecolortransparent($target, $transparentcolor);
            }
        }
    }

    /**
     * Write image to path.
     *
     * @param resource|\GdImage $image Image.
     * @param string $pathname Path.
     * @param string $mimetype MIME type.
     * @return bool
     */
    private static function write_image($image, string $pathname, string $mimetype): bool {
        switch ($mimetype) {
            case 'image/jpeg':
            case 'image/jpg':
                return imagejpeg($image, $pathname, 85);

            case 'image/png':
                return imagepng($image, $pathname, 6);

            case 'image/gif':
                return imagegif($image, $pathname);

            case 'image/webp':
                if (function_exists('imagewebp')) {
                    return imagewebp($image, $pathname, 85);
                }
                return false;

            default:
                return false;
        }
    }

    /**
     * Return whether file is a supported image.
     *
     * @param \stored_file $file File.
     * @return bool
     */
    private static function is_supported_image(\stored_file $file): bool {
        $mimetype = $file->get_mimetype();

        if (!in_array($mimetype, ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp'], true)) {
            return false;
        }

        if ($mimetype === 'image/webp' && !function_exists('imagewebp')) {
            return false;
        }

        return true;
    }

    /**
     * Return extension for MIME type.
     *
     * @param string $mimetype MIME type.
     * @return string
     */
    private static function extension_from_mimetype(string $mimetype): string {
        switch ($mimetype) {
            case 'image/jpeg':
            case 'image/jpg':
                return 'jpg';

            case 'image/png':
                return 'png';

            case 'image/gif':
                return 'gif';

            case 'image/webp':
                return 'webp';

            default:
                return 'bin';
        }
    }

    /**
     * Decode metadata safely.
     *
     * @param mixed $metadata Raw metadata.
     * @return array<string, mixed>
     */
    private static function decode_metadata($metadata): array {
        if (is_array($metadata)) {
            return $metadata;
        }

        if ($metadata instanceof \stdClass) {
            return (array)$metadata;
        }

        if (is_string($metadata) && trim($metadata) !== '') {
            $decoded = json_decode($metadata, true);
            return is_array($decoded) ? $decoded : [];
        }

        return [];
    }

    /**
     * Encode metadata safely.
     *
     * @param mixed $metadata Metadata.
     * @return string
     */
    private static function encode_metadata($metadata): string {
        $json = json_encode($metadata, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
        return $json === false ? '{}' : $json;
    }

    /**
     * Return configured batch limit.
     *
     * @return int
     */
    private static function get_batch_limit(): int {
        $configured = get_config(self::COMPONENT, 'mediaderivativebatchlimit');
        $limit = (int)$configured;

        if ($limit <= 0) {
            return self::DEFAULT_BATCH_LIMIT;
        }

        return min($limit, 500);
    }

    /**
     * Return system user id fallback.
     *
     * @return int
     */
    private static function get_system_userid(): int {
        global $USER;

        if (!empty($USER->id)) {
            return (int)$USER->id;
        }

        return 0;
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

