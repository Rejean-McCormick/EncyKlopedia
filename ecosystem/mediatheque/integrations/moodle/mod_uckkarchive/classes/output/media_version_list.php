<?php
// This file is part of Moodle - https://moodle.org/.
//
// Moodle is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// any later version.

/**
 * Media version list renderable for UCKK Archive.
 *
 * @package    mod_uckkarchive
 * @copyright  2026 Univers-Cité King Klown
 * @license    https://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later
 */

declare(strict_types=1);

namespace mod_uckkarchive\output;

use context_module;
use moodle_url;
use renderable;
use renderer_base;
use stdClass;
use templatable;

defined('MOODLE_INTERNAL') || die();

/**
 * Renderable media version list.
 *
 * This class prepares already-authorized media version data for Mustache.
 *
 * It does not:
 * - decide whether a user may view a media record;
 * - decide whether a user may download a file;
 * - create versions;
 * - delete versions;
 * - promote versions;
 * - expose restricted files;
 * - validate cultural protocol access.
 *
 * Those decisions belong in local policy classes, external services, page
 * controllers, and the pluginfile callback.
 */
final class media_version_list implements renderable, templatable {
    /** Version status: draft. */
    public const STATUS_DRAFT = 'draft';

    /** Version status: active. */
    public const STATUS_ACTIVE = 'active';

    /** Version status: current. */
    public const STATUS_CURRENT = 'current';

    /** Version status: superseded. */
    public const STATUS_SUPERSEDED = 'superseded';

    /** Version status: archived. */
    public const STATUS_ARCHIVED = 'archived';

    /** Version status: restricted. */
    public const STATUS_RESTRICTED = 'restricted';

    /** Version status: soft-deleted. */
    public const STATUS_DELETED_SOFT = 'deleted_soft';

    /** @var context_module Module context. */
    private context_module $context;

    /** @var stdClass Media record or preformatted media object. */
    private stdClass $media;

    /** @var array<int, stdClass|array> Version rows. */
    private array $versions;

    /** @var array<string, mixed> Permission flags prepared by controller/service. */
    private array $permissions;

    /** @var array<string, mixed> Display options. */
    private array $options;

    /**
     * Constructor.
     *
     * @param context_module $context Module context.
     * @param stdClass|array $media Media record or exported media data.
     * @param array<int, stdClass|array> $versions Version records or exported version data.
     * @param array<string, mixed> $permissions Permission flags already computed by caller.
     * @param array<string, mixed> $options Display options.
     */
    public function __construct(
        context_module $context,
        $media,
        array $versions = [],
        array $permissions = [],
        array $options = []
    ) {
        $this->context = $context;
        $this->media = $this->to_object($media);
        $this->versions = array_values($versions);
        $this->permissions = $permissions;
        $this->options = $options;
    }

    /**
     * Export data for Mustache.
     *
     * @param renderer_base $output Renderer.
     * @return stdClass
     */
    public function export_for_template(renderer_base $output): stdClass {
        $versions = [];
        $currentversionid = $this->current_version_id();

        foreach ($this->versions as $index => $version) {
            $versions[] = $this->export_version($this->to_object($version), $index, $currentversionid);
        }

        $hasversions = !empty($versions);

        return (object)[
            'mediaid' => (int)$this->field($this->media, ['id', 'mediaid'], 0),
            'mediauuid' => (string)$this->field($this->media, ['uuid', 'mediauuid'], ''),
            'mediatitle' => $this->format_plain((string)$this->field($this->media, ['title', 'name'], '')),
            'currentversionid' => $currentversionid,
            'versions' => $versions,
            'hasversions' => $hasversions,
            'versioncount' => count($versions),
            'emptytitle' => $this->str('media_version_list_empty_title', 'No versions yet'),
            'emptymessage' => $this->str(
                'media_version_list_empty_message',
                'No media versions are available for this item.'
            ),
            'permissions' => (object)[
                'canviewmedia' => $this->permission('canviewmedia', 'viewmedia'),
                'candownloadmedia' => $this->permission('candownloadmedia', 'downloadmedia'),
                'canversionmedia' => $this->permission('canversionmedia', 'versionmedia'),
                'caneditmedia' => $this->permission('caneditmedia', 'editmedia'),
                'candeletemedia' => $this->permission('candeletemedia', 'deletemedia'),
                'canviewrestrictedmedia' => $this->permission('canviewrestrictedmedia', 'viewrestrictedmedia'),
            ],
            'actions' => (object)[
                'showaddversion' => $this->bool_option('showaddversion', true) && $this->permission('canversionmedia', 'versionmedia'),
                'showdownloads' => $this->bool_option('showdownloads', true) && $this->permission('candownloadmedia', 'downloadmedia'),
                'showhashes' => $this->bool_option('showhashes', false),
                'showmetadata' => $this->bool_option('showmetadata', false),
            ],
            'notification' => $this->notification(),
            'classes' => $this->classes(),
            'attributes' => $this->attributes(),
        ];
    }

    /**
     * Export one version row.
     *
     * @param stdClass $version Version record or exported version.
     * @param int $index Zero-based row index.
     * @param int $currentversionid Current media version id.
     * @return stdClass
     */
    private function export_version(stdClass $version, int $index, int $currentversionid): stdClass {
        $id = (int)$this->field($version, ['id', 'versionid'], 0);
        $versionnumber = (int)$this->field($version, ['versionnumber', 'versionno', 'number'], $index + 1);
        $status = $this->normalise_status((string)$this->field($version, ['status'], self::STATUS_DRAFT));
        $iscurrent = $this->is_current($version, $id, $currentversionid, $status);
        $files = $this->export_files($version);
        $metadatajson = $this->normalise_metadata_json($this->field($version, ['metadata'], '{}'));

        return (object)[
            'id' => $id,
            'uuid' => (string)$this->field($version, ['uuid'], ''),
            'mediaid' => (int)$this->field($version, ['mediaid'], (int)$this->field($this->media, ['id', 'mediaid'], 0)),
            'versionnumber' => $versionnumber,
            'versionlabel' => $this->version_label($version, $versionnumber, $iscurrent),
            'label' => $this->format_plain((string)$this->field($version, ['label', 'title', 'name'], '')),
            'haslabel' => trim((string)$this->field($version, ['label', 'title', 'name'], '')) !== '',
            'summary' => $this->format_html((string)$this->field($version, ['summary', 'description', 'note'], '')),
            'hassummary' => trim(strip_tags((string)$this->field($version, ['summary', 'description', 'note'], ''))) !== '',
            'status' => $status,
            'statuslabel' => $this->status_label($status),
            'statusclass' => $this->status_class($status, $iscurrent),
            'iscurrent' => $iscurrent,
            'isactive' => $status === self::STATUS_ACTIVE || $status === self::STATUS_CURRENT,
            'isdraft' => $status === self::STATUS_DRAFT,
            'issuperseded' => $status === self::STATUS_SUPERSEDED,
            'isarchived' => $status === self::STATUS_ARCHIVED,
            'isrestricted' => $status === self::STATUS_RESTRICTED,
            'isdeleted' => $status === self::STATUS_DELETED_SOFT,
            'filearea' => (string)$this->field($version, ['filearea'], ''),
            'filearealabel' => $this->filearea_label((string)$this->field($version, ['filearea'], '')),
            'filename' => (string)$this->field($version, ['filename'], ''),
            'hasfilename' => trim((string)$this->field($version, ['filename'], '')) !== '',
            'filesize' => (int)$this->field($version, ['filesize'], 0),
            'filesizelabel' => display_size((int)$this->field($version, ['filesize'], 0)),
            'mimetype' => (string)$this->field($version, ['mimetype', 'mime'], ''),
            'hasmimetype' => trim((string)$this->field($version, ['mimetype', 'mime'], '')) !== '',
            'contenthash' => (string)$this->field($version, ['contenthash', 'filehash'], ''),
            'hascontenthash' => trim((string)$this->field($version, ['contenthash', 'filehash'], '')) !== '',
            'createdby' => (int)$this->field($version, ['createdby', 'userid'], 0),
            'modifiedby' => (int)$this->field($version, ['modifiedby'], 0),
            'timecreated' => (int)$this->field($version, ['timecreated'], 0),
            'timemodified' => (int)$this->field($version, ['timemodified'], 0),
            'timecreatedlabel' => $this->time_label((int)$this->field($version, ['timecreated'], 0)),
            'timemodifiedlabel' => $this->time_label((int)$this->field($version, ['timemodified'], 0)),
            'metadata' => $metadatajson,
            'hasmetadata' => $metadatajson !== '{}',
            'files' => $files,
            'hasfiles' => !empty($files),
            'filecount' => count($files),
            'url' => $this->version_url($id),
            'hasurl' => $id > 0,
            'actions' => (object)[
                'candownload' => $this->permission('candownloadmedia', 'downloadmedia') && !empty($files),
                'canmakecurrent' => $this->permission('canversionmedia', 'versionmedia') && !$iscurrent && $id > 0,
                'canedit' => $this->permission('caneditmedia', 'editmedia') && $id > 0,
                'candelete' => $this->permission('candeletemedia', 'deletemedia') && $id > 0 && !$iscurrent,
            ],
            'classes' => implode(' ', array_filter([
                'uckkarchive-media-version',
                'uckkarchive-media-version--' . $status,
                $iscurrent ? 'uckkarchive-media-version--current' : '',
            ])),
        ];
    }

    /**
     * Export files attached to a version.
     *
     * @param stdClass $version Version data.
     * @return stdClass[]
     */
    private function export_files(stdClass $version): array {
        if (!$this->permission('candownloadmedia', 'downloadmedia')) {
            return [];
        }

        $files = $this->field($version, ['files'], []);

        if ($files instanceof stdClass) {
            $files = [$files];
        }

        if (!is_array($files)) {
            return [];
        }

        $exported = [];

        foreach ($files as $file) {
            $file = $this->to_object($file);

            $filename = (string)$this->field($file, ['filename'], '');
            if ($filename === '') {
                continue;
            }

            $filesize = (int)$this->field($file, ['filesize', 'size'], 0);
            $filearea = (string)$this->field($file, ['filearea'], '');

            $exported[] = (object)[
                'filearea' => $filearea,
                'filearealabel' => $this->filearea_label($filearea),
                'filename' => $filename,
                'filepath' => (string)$this->field($file, ['filepath'], '/'),
                'filesize' => $filesize,
                'filesizelabel' => display_size($filesize),
                'mimetype' => (string)$this->field($file, ['mimetype', 'mime'], ''),
                'contenthash' => (string)$this->field($file, ['contenthash', 'hash'], ''),
                'hascontenthash' => trim((string)$this->field($file, ['contenthash', 'hash'], '')) !== '',
                'url' => (string)$this->field($file, ['url'], ''),
                'hasurl' => trim((string)$this->field($file, ['url'], '')) !== '',
                'downloadurl' => (string)$this->field($file, ['downloadurl'], (string)$this->field($file, ['url'], '')),
                'hasdownloadurl' => trim((string)$this->field($file, ['downloadurl', 'url'], '')) !== '',
                'icon' => $this->file_icon($filename),
            ];
        }

        return $exported;
    }

    /**
     * Return current version id.
     *
     * @return int
     */
    private function current_version_id(): int {
        $fromoptions = (int)($this->options['currentversionid'] ?? 0);
        if ($fromoptions > 0) {
            return $fromoptions;
        }

        return (int)$this->field($this->media, ['currentversionid', 'current_version_id'], 0);
    }

    /**
     * Return whether the version is current.
     *
     * @param stdClass $version Version record.
     * @param int $versionid Version id.
     * @param int $currentversionid Current version id.
     * @param string $status Normalized status.
     * @return bool
     */
    private function is_current(stdClass $version, int $versionid, int $currentversionid, string $status): bool {
        if ((bool)$this->field($version, ['iscurrent', 'current'], false)) {
            return true;
        }

        if ($currentversionid > 0 && $versionid === $currentversionid) {
            return true;
        }

        return $status === self::STATUS_CURRENT;
    }

    /**
     * Return version display label.
     *
     * @param stdClass $version Version record.
     * @param int $versionnumber Version number.
     * @param bool $iscurrent Current flag.
     * @return string
     */
    private function version_label(stdClass $version, int $versionnumber, bool $iscurrent): string {
        $label = trim((string)$this->field($version, ['label', 'title', 'name'], ''));

        if ($label !== '') {
            return $this->format_plain($label);
        }

        $base = $this->str('media_version_label', 'Version {$a}', $versionnumber);

        if ($iscurrent) {
            return $base . ' — ' . $this->str('media_version_current', 'Current');
        }

        return $base;
    }

    /**
     * Return status label.
     *
     * @param string $status Status.
     * @return string
     */
    private function status_label(string $status): string {
        $key = 'media_version_status:' . $status;

        return $this->str($key, ucfirst(str_replace('_', ' ', $status)));
    }

    /**
     * Return CSS class for status.
     *
     * @param string $status Status.
     * @param bool $iscurrent Current flag.
     * @return string
     */
    private function status_class(string $status, bool $iscurrent): string {
        if ($iscurrent) {
            return 'badge badge-success';
        }

        return match ($status) {
            self::STATUS_DRAFT => 'badge badge-secondary',
            self::STATUS_ACTIVE => 'badge badge-success',
            self::STATUS_CURRENT => 'badge badge-success',
            self::STATUS_SUPERSEDED => 'badge badge-info',
            self::STATUS_ARCHIVED => 'badge badge-light',
            self::STATUS_RESTRICTED => 'badge badge-warning',
            self::STATUS_DELETED_SOFT => 'badge badge-danger',
            default => 'badge badge-secondary',
        };
    }

    /**
     * Normalize version status.
     *
     * @param string $status Raw status.
     * @return string
     */
    private function normalise_status(string $status): string {
        $status = clean_param(trim($status), PARAM_ALPHANUMEXT);

        if ($status === '') {
            return self::STATUS_DRAFT;
        }

        return $status;
    }

    /**
     * Return file area label.
     *
     * @param string $filearea File area.
     * @return string
     */
    private function filearea_label(string $filearea): string {
        if ($filearea === '') {
            return '';
        }

        $key = 'filearea:' . $filearea;

        return $this->str($key, ucfirst(str_replace('_', ' ', $filearea)));
    }

    /**
     * Return file icon key.
     *
     * @param string $filename Filename.
     * @return string
     */
    private function file_icon(string $filename): string {
        $extension = strtolower(pathinfo($filename, PATHINFO_EXTENSION));

        return match ($extension) {
            'jpg', 'jpeg', 'png', 'gif', 'webp', 'svg' => 'image',
            'mp4', 'mov', 'm4v', 'webm', 'avi' => 'video',
            'mp3', 'wav', 'm4a', 'ogg', 'flac' => 'audio',
            'pdf' => 'pdf',
            'vtt', 'srt' => 'caption',
            'txt', 'md', 'rtf' => 'text',
            'doc', 'docx', 'odt' => 'document',
            'xls', 'xlsx', 'ods', 'csv' => 'spreadsheet',
            'zip', 'tar', 'gz', '7z' => 'archive',
            default => 'file',
        };
    }

    /**
     * Return a URL to the media page focused on one version.
     *
     * @param int $versionid Version id.
     * @return string
     */
    private function version_url(int $versionid): string {
        if ($versionid <= 0) {
            return '';
        }

        if (!empty($this->options['versionurlbase'])) {
            $base = $this->options['versionurlbase'];
            if ($base instanceof moodle_url) {
                $url = new moodle_url($base);
            } else {
                $url = new moodle_url((string)$base);
            }

            $url->param('versionid', $versionid);
            return $url->out(false);
        }

        $cmid = (int)$this->field($this->media, ['cmid'], 0);
        $mediaid = (int)$this->field($this->media, ['id', 'mediaid'], 0);

        if ($cmid <= 0 && !empty($this->options['cmid'])) {
            $cmid = (int)$this->options['cmid'];
        }

        if ($cmid <= 0) {
            return '';
        }

        return (new moodle_url('/mod/uckkarchive/media.php', [
            'id' => $cmid,
            'mediaid' => $mediaid,
            'versionid' => $versionid,
        ]))->out(false);
    }

    /**
     * Return a formatted time label.
     *
     * @param int $timestamp Unix timestamp.
     * @return string
     */
    private function time_label(int $timestamp): string {
        if ($timestamp <= 0) {
            return '';
        }

        return userdate($timestamp);
    }

    /**
     * Return notification object.
     *
     * @return stdClass
     */
    private function notification(): stdClass {
        $message = trim((string)($this->options['notification'] ?? ''));

        return (object)[
            'message' => $message,
            'type' => clean_param((string)($this->options['notificationtype'] ?? 'info'), PARAM_ALPHANUMEXT),
            'hasmessage' => $message !== '',
        ];
    }

    /**
     * Return wrapper CSS classes.
     *
     * @return string
     */
    private function classes(): string {
        $classes = [
            'uckkarchive-media-version-list',
        ];

        if (empty($this->versions)) {
            $classes[] = 'uckkarchive-media-version-list--empty';
        }

        if ($this->permission('canversionmedia', 'versionmedia')) {
            $classes[] = 'uckkarchive-media-version-list--can-version';
        }

        return implode(' ', $classes);
    }

    /**
     * Return HTML/data attributes for template.
     *
     * @return stdClass
     */
    private function attributes(): stdClass {
        return (object)[
            'region' => 'uckkarchive-media-versions',
            'mediaid' => (int)$this->field($this->media, ['id', 'mediaid'], 0),
            'mediauuid' => (string)$this->field($this->media, ['uuid', 'mediauuid'], ''),
        ];
    }

    /**
     * Return a permission flag.
     *
     * @param string $primary Primary key.
     * @param string|null $fallback Fallback key.
     * @return bool
     */
    private function permission(string $primary, ?string $fallback = null): bool {
        if (array_key_exists($primary, $this->permissions)) {
            return (bool)$this->permissions[$primary];
        }

        if ($fallback !== null && array_key_exists($fallback, $this->permissions)) {
            return (bool)$this->permissions[$fallback];
        }

        return false;
    }

    /**
     * Return boolean display option.
     *
     * @param string $key Option key.
     * @param bool $default Default.
     * @return bool
     */
    private function bool_option(string $key, bool $default = false): bool {
        if (!array_key_exists($key, $this->options)) {
            return $default;
        }

        return !empty($this->options[$key]);
    }

    /**
     * Return metadata as safe JSON object string.
     *
     * @param mixed $metadata Metadata input.
     * @return string
     */
    private function normalise_metadata_json(mixed $metadata): string {
        if (is_string($metadata)) {
            $metadata = trim($metadata);
            if ($metadata === '') {
                return '{}';
            }

            $decoded = json_decode($metadata, true);
            if (!is_array($decoded)) {
                return '{}';
            }

            $metadata = $decoded;
        }

        if ($metadata instanceof stdClass) {
            $metadata = (array)$metadata;
        }

        if (!is_array($metadata)) {
            return '{}';
        }

        $json = json_encode($metadata, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);

        return $json === false ? '{}' : $json;
    }

    /**
     * Format plain display text.
     *
     * @param string $text Text.
     * @return string
     */
    private function format_plain(string $text): string {
        $text = trim($text);

        if ($text === '') {
            return '';
        }

        return format_string($text, true, ['context' => $this->context]);
    }

    /**
     * Format HTML text.
     *
     * @param string $text Text.
     * @return string
     */
    private function format_html(string $text): string {
        $text = trim($text);

        if ($text === '') {
            return '';
        }

        return format_text($text, FORMAT_HTML, [
            'context' => $this->context,
            'para' => false,
            'trusted' => false,
        ]);
    }

    /**
     * Safe component string lookup.
     *
     * @param string $identifier String identifier.
     * @param string $fallback Fallback string.
     * @param mixed $a Optional placeholder.
     * @return string
     */
    private function str(string $identifier, string $fallback, mixed $a = null): string {
        $manager = get_string_manager();

        if ($manager->string_exists($identifier, 'uckkarchive')) {
            return get_string($identifier, 'uckkarchive', $a);
        }

        if ($a !== null && is_scalar($a)) {
            return str_replace('{$a}', (string)$a, $fallback);
        }

        return $fallback;
    }

    /**
     * Return field value from record.
     *
     * @param stdClass $record Record.
     * @param string[] $fields Candidate fields.
     * @param mixed $default Default value.
     * @return mixed
     */
    private function field(stdClass $record, array $fields, mixed $default = null): mixed {
        foreach ($fields as $field) {
            if (property_exists($record, $field) && $record->{$field} !== null && $record->{$field} !== '') {
                return $record->{$field};
            }
        }

        return $default;
    }

    /**
     * Convert array/object to stdClass.
     *
     * @param mixed $value Value.
     * @return stdClass
     */
    private function to_object(mixed $value): stdClass {
        if ($value instanceof stdClass) {
            return $value;
        }

        if (is_array($value)) {
            $object = new stdClass();

            foreach ($value as $key => $item) {
                $object->{$key} = $item;
            }

            return $object;
        }

        return new stdClass();
    }
}
