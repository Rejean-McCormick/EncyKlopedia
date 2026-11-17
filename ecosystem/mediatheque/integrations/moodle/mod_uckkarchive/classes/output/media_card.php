<?php
// This file is part of Moodle - https://moodle.org/
//
// Moodle is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// any later version.

/**
 * Media card output object.
 *
 * @package    mod_uckkarchive
 * @copyright  2026 Univers-Cité King Klown
 * @license    https://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later
 */

declare(strict_types=1);

namespace mod_uckkarchive\output;

use moodle_url;
use renderable;
use renderer_base;
use stdClass;
use templatable;

defined('MOODLE_INTERNAL') || die();

/**
 * Renderable card for one media record.
 *
 * This class prepares display data only.
 *
 * It does not:
 * - decide whether the current user may view restricted media;
 * - decide whether the current user may download files;
 * - decide cultural protocol access;
 * - approve content advisories;
 * - approve validation state;
 * - serve files directly.
 *
 * Authorization, restriction filtering, advisory filtering, and File API
 * access must already have been handled by local/domain classes, external
 * services, or pluginfile handling before this object is rendered.
 */
final class media_card implements renderable, templatable {
    /** Media type: image. */
    public const TYPE_IMAGE = 'image';

    /** Media type: video. */
    public const TYPE_VIDEO = 'video';

    /** Media type: audio. */
    public const TYPE_AUDIO = 'audio';

    /** Media type: document. */
    public const TYPE_DOCUMENT = 'document';

    /** Media type: text. */
    public const TYPE_TEXT = 'text';

    /** Media type: dataset. */
    public const TYPE_DATASET = 'dataset';

    /** Media type: archive bundle. */
    public const TYPE_ARCHIVE = 'archive';

    /** Media type: link/external. */
    public const TYPE_LINK = 'link';

    /** Media type: other. */
    public const TYPE_OTHER = 'other';

    /** Status: draft. */
    public const STATUS_DRAFT = 'draft';

    /** Status: active. */
    public const STATUS_ACTIVE = 'active';

    /** Status: pending review. */
    public const STATUS_PENDING_REVIEW = 'pending_review';

    /** Status: reviewed. */
    public const STATUS_REVIEWED = 'reviewed';

    /** Status: archived. */
    public const STATUS_ARCHIVED = 'archived';

    /** Status: retired. */
    public const STATUS_RETIRED = 'retired';

    /** Status: restricted. */
    public const STATUS_RESTRICTED = 'restricted';

    /** Status: soft-deleted. */
    public const STATUS_DELETED_SOFT = 'deleted_soft';

    /** Visibility: private. */
    public const VISIBILITY_PRIVATE = 'private';

    /** Visibility: user. */
    public const VISIBILITY_USER = 'user';

    /** Visibility: group. */
    public const VISIBILITY_GROUP = 'group';

    /** Visibility: course. */
    public const VISIBILITY_COURSE = 'course';

    /** Visibility: cohort. */
    public const VISIBILITY_COHORT = 'cohort';

    /** Visibility: program. */
    public const VISIBILITY_PROGRAM = 'program';

    /** Visibility: institution. */
    public const VISIBILITY_INSTITUTION = 'institution';

    /** Visibility: public. */
    public const VISIBILITY_PUBLIC = 'public';

    /** Visibility: restricted. */
    public const VISIBILITY_RESTRICTED = 'restricted';

    /** Visibility: restricted integrity. */
    public const VISIBILITY_RESTRICTED_INTEGRITY = 'restricted_integrity';

    /** Visibility: restricted cultural. */
    public const VISIBILITY_RESTRICTED_CULTURAL = 'restricted_cultural';

    /** @var stdClass Media record. */
    private stdClass $media;

    /** @var array<string, mixed> Display options. */
    private array $options;

    /**
     * Constructor.
     *
     * Expected option keys:
     *
     * ```text
     * cmid
     * archiveid
     * courseid
     * canview
     * canupdate
     * candelete
     * candownload
     * canversion
     * canexport
     * canmanageadvisories
     * canviewrestricted
     * showactions
     * showfiles
     * showadvisories
     * showversions
     * showmetadata
     * redacted
     * thumbnailurl
     * previewurl
     * downloadurl
     * viewurl
     * editurl
     * deleteurl
     * versionurl
     * exporturl
     * advisoryurl
     * files
     * tags
     * contentmarkers
     * versions
     * ```
     *
     * @param stdClass $media Already-authorized media record.
     * @param array<string, mixed> $options Display options and permission flags.
     */
    public function __construct(stdClass $media, array $options = []) {
        $this->media = $media;
        $this->options = array_merge($this->default_options(), $options);
    }

    /**
     * Export data for Mustache template.
     *
     * @param renderer_base $output Renderer.
     * @return stdClass
     */
    public function export_for_template(renderer_base $output): stdClass {
        $media = $this->media;

        $id = $this->int_field($media, ['id']);
        $uuid = $this->text_field($media, ['uuid']);
        $archiveid = $this->int_option('archiveid') ?: $this->int_field($media, ['archiveid', 'uckkarchiveid']);
        $courseid = $this->int_option('courseid') ?: $this->int_field($media, ['courseid']);
        $cmid = $this->int_option('cmid') ?: $this->int_field($media, ['cmid']);
        $contextid = $this->int_field($media, ['contextid']);

        $title = $this->text_field($media, ['title', 'name'], get_string('media', 'uckkarchive'));
        $summary = $this->raw_field($media, ['summary', 'publicsummary']);
        $description = $this->raw_field($media, ['description', 'body', 'notes']);

        $mediatype = $this->normalise_key($this->text_field($media, ['mediatype', 'type'], self::TYPE_OTHER));
        $mimetype = $this->text_field($media, ['mimetype', 'mime']);
        $status = $this->normalise_key($this->text_field($media, ['status'], self::STATUS_DRAFT));
        $visibility = $this->normalise_key($this->text_field($media, ['visibility'], self::VISIBILITY_PRIVATE));
        $audiencesuitability = $this->normalise_key($this->text_field($media, ['audiencesuitability'], 'guided'));
        $source = $this->normalise_key($this->text_field($media, ['source', 'sourcetype']));

        $ownerid = $this->int_field($media, ['ownerid', 'userid']);
        $createdby = $this->int_field($media, ['createdby', 'userid', 'ownerid']);
        $modifiedby = $this->int_field($media, ['modifiedby']);
        $timecreated = $this->int_field($media, ['timecreated']);
        $timemodified = $this->int_field($media, ['timemodified']);

        $filesize = $this->int_field($media, ['filesize', 'sizebytes']);
        $duration = $this->int_field($media, ['duration', 'durationseconds']);
        $width = $this->int_field($media, ['width']);
        $height = $this->int_field($media, ['height']);

        $currentversionid = $this->int_field($media, ['currentversionid', 'versionid']);
        $versioncount = $this->count_from_options_or_record('versioncount', ['versioncount', 'versionscount']);
        $contentadvisorycount = $this->count_from_options_or_record('contentadvisorycount', [
            'contentadvisorycount',
            'contentmarkercount',
            'contentmarker_count',
            'advisorycount',
        ]);
        $tagcount = $this->count_from_options_or_record('tagcount', ['tagcount', 'tags_count']);

        $canview = $this->bool_option('canview', true);
        $canupdate = $this->bool_option('canupdate');
        $candelete = $this->bool_option('candelete');
        $candownload = $this->bool_option('candownload');
        $canversion = $this->bool_option('canversion');
        $canexport = $this->bool_option('canexport');
        $canmanageadvisories = $this->bool_option('canmanageadvisories');
        $canviewrestricted = $this->bool_option('canviewrestricted');

        $isrestricted = $this->is_restricted($status, $visibility, $audiencesuitability);
        $isculturalrestricted = $visibility === self::VISIBILITY_RESTRICTED_CULTURAL ||
            $this->bool_field($media, ['culturalprotocol', 'isculturalrestricted']);
        $isintegrityrestricted = $visibility === self::VISIBILITY_RESTRICTED_INTEGRITY ||
            $this->bool_field($media, ['integrityrestricted', 'isintegrityrestricted']);
        $isdeleted = $status === self::STATUS_DELETED_SOFT;
        $isredacted = $this->bool_option('redacted') || ($isrestricted && !$canviewrestricted);

        if ($isredacted) {
            $summary = '';
            $description = '';
        }

        $thumbnailurl = $this->url_option('thumbnailurl') ?: $this->text_field($media, ['thumbnailurl']);
        $previewurl = $this->url_option('previewurl') ?: $this->text_field($media, ['previewurl']);
        $downloadurl = $this->url_option('downloadurl') ?: $this->text_field($media, ['downloadurl']);
        $externalurl = $this->url_option('externalurl') ?: $this->text_field($media, ['externalurl', 'sourceurl', 'url']);
        $isgithub = str_starts_with(strtolower($externalurl), 'https://github.com/');

        if (!$candownload) {
            $downloadurl = '';
        }

        $viewurl = $this->url_option('viewurl') ?: $this->build_view_url($cmid, $id);
        $editurl = $this->url_option('editurl');
        $deleteurl = $this->url_option('deleteurl');
        $versionurl = $this->url_option('versionurl');
        $exporturl = $this->url_option('exporturl');
        $advisoryurl = $this->url_option('advisoryurl');

        $files = $this->files_array();
        $tags = $this->tags_array();
        $contentmarkers = $this->content_markers_array();
        $versions = $this->versions_array();

        $data = (object)[
            'id' => $id,
            'uuid' => $uuid,
            'archiveid' => $archiveid,
            'courseid' => $courseid,
            'cmid' => $cmid,
            'contextid' => $contextid,

            'title' => format_string($title),
            'summary' => $this->format_raw($summary),
            'description' => $this->format_raw($description),

            'mediatype' => $mediatype,
            'mediatypelabel' => $this->label('mediatype_' . $mediatype, $mediatype),
            'mediatypeclass' => $this->css_class('uckkarchive-media-card--type-', $mediatype),
            'mimetype' => $mimetype,

            'status' => $status,
            'statuslabel' => $this->label('status_' . $status, $status),
            'statusclass' => $this->status_class($status),

            'visibility' => $visibility,
            'visibilitylabel' => $this->label('visibility_' . $visibility, $visibility),
            'visibilityclass' => $this->visibility_class($visibility),

            'audiencesuitability' => $audiencesuitability,
            'audiencesuitabilitylabel' => $this->label('audiencesuitability_' . $audiencesuitability, $audiencesuitability),

            'source' => $source,
            'sourcelabel' => $this->label('mediasource_' . $source, $source),

            'ownerid' => $ownerid,
            'createdby' => $createdby,
            'modifiedby' => $modifiedby,
            'timecreated' => $timecreated,
            'timemodified' => $timemodified,
            'timecreatedlabel' => $this->date_label($timecreated),
            'timemodifiedlabel' => $this->date_label($timemodified),

            'filesize' => $filesize,
            'filesizelabel' => $this->filesize_label($filesize),
            'duration' => $duration,
            'durationlabel' => $this->duration_label($duration),
            'width' => $width,
            'height' => $height,
            'dimensionslabel' => $this->dimensions_label($width, $height),

            'currentversionid' => $currentversionid,
            'versioncount' => $versioncount,
            'versioncountlabel' => $this->count_label($versioncount, 'version'),
            'contentadvisorycount' => $contentadvisorycount,
            'contentadvisorycountlabel' => $this->count_label($contentadvisorycount, 'content advisory'),
            'tagcount' => $tagcount,
            'tagcountlabel' => $this->count_label($tagcount, 'tag'),

            'thumbnailurl' => $thumbnailurl,
            'previewurl' => $previewurl,
            'downloadurl' => $downloadurl,
            'externalurl' => $externalurl,
            'viewurl' => $viewurl,
            'editurl' => $editurl,
            'deleteurl' => $deleteurl,
            'versionurl' => $versionurl,
            'exporturl' => $exporturl,
            'advisoryurl' => $advisoryurl,

            'hasuuid' => $uuid !== '',
            'hassummary' => $this->has_content($summary),
            'hasdescription' => $this->has_content($description),
            'hasmimetype' => $mimetype !== '',
            'hassource' => $source !== '',
            'hasthumbnail' => $thumbnailurl !== '',
            'haspreview' => $previewurl !== '',
            'hasdownload' => $downloadurl !== '' && $candownload,
            'hasexternalurl' => $externalurl !== '',
            'hasviewurl' => $viewurl !== '',
            'hasediturl' => $editurl !== '' && $canupdate,
            'hasdeleteurl' => $deleteurl !== '' && $candelete,
            'hasversionurl' => $versionurl !== '' && $canversion,
            'hasexporturl' => $exporturl !== '' && $canexport,
            'hasadvisoryurl' => $advisoryurl !== '' && $canmanageadvisories,
            'hasfilesize' => $filesize > 0,
            'hasduration' => $duration > 0,
            'hasdimensions' => $width > 0 && $height > 0,
            'hasversions' => $versioncount > 0 || !empty($versions),
            'hascontentadvisories' => $contentadvisorycount > 0 || !empty($contentmarkers),
            'hastags' => $tagcount > 0 || !empty($tags),
            'hasfiles' => !empty($files),

            'isimage' => $mediatype === self::TYPE_IMAGE || str_starts_with($mimetype, 'image/'),
            'isvideo' => $mediatype === self::TYPE_VIDEO || str_starts_with($mimetype, 'video/'),
            'isaudio' => $mediatype === self::TYPE_AUDIO || str_starts_with($mimetype, 'audio/'),
            'isdocument' => $mediatype === self::TYPE_DOCUMENT,
            'isexternal' => in_array($mediatype, [self::TYPE_LINK, 'external_reference'], true) || $source === 'external' || $externalurl !== '',
            'isgithub' => $isgithub,
            'isrestricted' => $isrestricted,
            'isculturalrestricted' => $isculturalrestricted,
            'isintegrityrestricted' => $isintegrityrestricted,
            'isdeleted' => $isdeleted,
            'isredacted' => $isredacted,

            'canview' => $canview,
            'canupdate' => $canupdate,
            'candelete' => $candelete,
            'candownload' => $candownload,
            'canversion' => $canversion,
            'canexport' => $canexport,
            'canmanageadvisories' => $canmanageadvisories,
            'canviewrestricted' => $canviewrestricted,

            'showactions' => $this->bool_option('showactions', true),
            'showfiles' => $this->bool_option('showfiles', true) && !empty($files),
            'showadvisories' => $this->bool_option('showadvisories', true),
            'showversions' => $this->bool_option('showversions', true),
            'showmetadata' => $this->bool_option('showmetadata', false),
            'showrestrictednotice' => $isrestricted,
            'showculturalnotice' => $isculturalrestricted,
            'showintegritynotice' => $isintegrityrestricted,
            'showredactednotice' => $isredacted,

            'files' => $files,
            'tags' => $tags,
            'contentmarkers' => $contentmarkers,
            'versions' => $versions,
            'metadata' => $this->metadata_array($media),
            'actions' => $this->build_actions($viewurl, $editurl, $deleteurl, $versionurl, $exporturl, $advisoryurl),
            'notice' => $this->build_notice($isrestricted, $isculturalrestricted, $isintegrityrestricted, $isredacted),
        ];

        return $data;
    }

    /**
     * Return default display options.
     *
     * @return array<string, mixed>
     */
    private function default_options(): array {
        return [
            'cmid' => 0,
            'archiveid' => 0,
            'courseid' => 0,
            'canview' => true,
            'canupdate' => false,
            'candelete' => false,
            'candownload' => false,
            'canversion' => false,
            'canexport' => false,
            'canmanageadvisories' => false,
            'canviewrestricted' => false,
            'showactions' => true,
            'showfiles' => true,
            'showadvisories' => true,
            'showversions' => true,
            'showmetadata' => false,
            'redacted' => false,
            'thumbnailurl' => '',
            'previewurl' => '',
            'downloadurl' => '',
            'viewurl' => '',
            'editurl' => '',
            'deleteurl' => '',
            'versionurl' => '',
            'exporturl' => '',
            'advisoryurl' => '',
            'files' => [],
            'tags' => [],
            'contentmarkers' => [],
            'versions' => [],
            'contentadvisorycount' => 0,
            'versioncount' => 0,
            'tagcount' => 0,
        ];
    }

    /**
     * Build action array.
     *
     * @param string $viewurl View URL.
     * @param string $editurl Edit URL.
     * @param string $deleteurl Delete URL.
     * @param string $versionurl Version URL.
     * @param string $exporturl Export URL.
     * @param string $advisoryurl Advisory URL.
     * @return array<int, array<string, mixed>>
     */
    private function build_actions(
        string $viewurl,
        string $editurl,
        string $deleteurl,
        string $versionurl,
        string $exporturl,
        string $advisoryurl
    ): array {
        if (!$this->bool_option('showactions', true)) {
            return [];
        }

        $actions = [];

        if ($viewurl !== '' && $this->bool_option('canview', true)) {
            $actions[] = [
                'key' => 'view',
                'label' => $this->string_or_fallback('view', 'View'),
                'url' => $viewurl,
                'class' => 'btn btn-secondary btn-sm',
                'primary' => false,
                'danger' => false,
            ];
        }

        if ($editurl !== '' && $this->bool_option('canupdate')) {
            $actions[] = [
                'key' => 'edit',
                'label' => $this->string_or_fallback('edit', 'Edit'),
                'url' => $editurl,
                'class' => 'btn btn-primary btn-sm',
                'primary' => true,
                'danger' => false,
            ];
        }

        if ($versionurl !== '' && $this->bool_option('canversion')) {
            $actions[] = [
                'key' => 'version',
                'label' => $this->string_or_fallback('versionmedia', 'Version'),
                'url' => $versionurl,
                'class' => 'btn btn-secondary btn-sm',
                'primary' => false,
                'danger' => false,
            ];
        }

        if ($advisoryurl !== '' && $this->bool_option('canmanageadvisories')) {
            $actions[] = [
                'key' => 'advisories',
                'label' => $this->string_or_fallback('contentadvisories', 'Content advisories'),
                'url' => $advisoryurl,
                'class' => 'btn btn-secondary btn-sm',
                'primary' => false,
                'danger' => false,
            ];
        }

        if ($exporturl !== '' && $this->bool_option('canexport')) {
            $actions[] = [
                'key' => 'export',
                'label' => $this->string_or_fallback('export', 'Export'),
                'url' => $exporturl,
                'class' => 'btn btn-secondary btn-sm',
                'primary' => false,
                'danger' => false,
            ];
        }

        if ($deleteurl !== '' && $this->bool_option('candelete')) {
            $actions[] = [
                'key' => 'delete',
                'label' => $this->string_or_fallback('delete', 'Delete'),
                'url' => $deleteurl,
                'class' => 'btn btn-danger btn-sm',
                'primary' => false,
                'danger' => true,
            ];
        }

        return $actions;
    }

    /**
     * Build notice array.
     *
     * @param bool $isrestricted Restricted.
     * @param bool $isculturalrestricted Cultural restriction.
     * @param bool $isintegrityrestricted Integrity restriction.
     * @param bool $isredacted Redacted.
     * @return array<string, mixed>
     */
    private function build_notice(
        bool $isrestricted,
        bool $isculturalrestricted,
        bool $isintegrityrestricted,
        bool $isredacted
    ): array {
        if ($isredacted) {
            return [
                'type' => 'redacted',
                'class' => 'alert alert-warning',
                'message' => $this->string_or_fallback(
                    'mediaredactednotice',
                    'Some media details are restricted.'
                ),
            ];
        }

        if ($isculturalrestricted) {
            return [
                'type' => 'cultural',
                'class' => 'alert alert-warning',
                'message' => $this->string_or_fallback(
                    'mediaculturalnotice',
                    'This media includes cultural protocol restrictions.'
                ),
            ];
        }

        if ($isintegrityrestricted) {
            return [
                'type' => 'integrity',
                'class' => 'alert alert-warning',
                'message' => $this->string_or_fallback(
                    'mediaintegritynotice',
                    'This media includes integrity-related restrictions.'
                ),
            ];
        }

        if ($isrestricted) {
            return [
                'type' => 'restricted',
                'class' => 'alert alert-info',
                'message' => $this->string_or_fallback(
                    'mediarestrictednotice',
                    'This media has restricted visibility.'
                ),
            ];
        }

        return [
            'type' => '',
            'class' => '',
            'message' => '',
        ];
    }

    /**
     * Build fallback view URL.
     *
     * @param int $cmid Course module id.
     * @param int $mediaid Media id.
     * @return string
     */
    private function build_view_url(int $cmid, int $mediaid): string {
        if ($cmid <= 0 || $mediaid <= 0) {
            return '';
        }

        return (new moodle_url('/mod/uckkarchive/media.php', [
            'id' => $cmid,
            'mediaid' => $mediaid,
        ]))->out(false);
    }

    /**
     * Get URL option.
     *
     * @param string $key Option key.
     * @return string
     */
    private function url_option(string $key): string {
        $value = $this->options[$key] ?? '';

        if ($value instanceof moodle_url) {
            return $value->out(false);
        }

        return trim((string)$value);
    }

    /**
     * Get boolean option.
     *
     * @param string $key Option key.
     * @param bool $default Default.
     * @return bool
     */
    private function bool_option(string $key, bool $default = false): bool {
        if (!array_key_exists($key, $this->options)) {
            return $default;
        }

        return (bool)$this->options[$key];
    }

    /**
     * Get integer option.
     *
     * @param string $key Option key.
     * @return int
     */
    private function int_option(string $key): int {
        return (int)($this->options[$key] ?? 0);
    }

    /**
     * Return count from options or media record.
     *
     * @param string $optionkey Option key.
     * @param string[] $recordfields Candidate record fields.
     * @return int
     */
    private function count_from_options_or_record(string $optionkey, array $recordfields): int {
        $optionvalue = $this->int_option($optionkey);
        if ($optionvalue > 0) {
            return $optionvalue;
        }

        return $this->int_field($this->media, $recordfields);
    }

    /**
     * Get string field.
     *
     * @param stdClass $record Record.
     * @param string[] $fields Candidate fields.
     * @param string $default Default.
     * @return string
     */
    private function text_field(stdClass $record, array $fields, string $default = ''): string {
        foreach ($fields as $field) {
            if (property_exists($record, $field) && $record->{$field} !== null && $record->{$field} !== '') {
                return trim((string)$record->{$field});
            }
        }

        return $default;
    }

    /**
     * Get raw field.
     *
     * @param stdClass $record Record.
     * @param string[] $fields Candidate fields.
     * @param string $default Default.
     * @return string
     */
    private function raw_field(stdClass $record, array $fields, string $default = ''): string {
        return $this->text_field($record, $fields, $default);
    }

    /**
     * Get integer field.
     *
     * @param stdClass $record Record.
     * @param string[] $fields Candidate fields.
     * @param int $default Default.
     * @return int
     */
    private function int_field(stdClass $record, array $fields, int $default = 0): int {
        foreach ($fields as $field) {
            if (property_exists($record, $field) && $record->{$field} !== null && $record->{$field} !== '') {
                return (int)$record->{$field};
            }
        }

        return $default;
    }

    /**
     * Get boolean field.
     *
     * @param stdClass $record Record.
     * @param string[] $fields Candidate fields.
     * @param bool $default Default.
     * @return bool
     */
    private function bool_field(stdClass $record, array $fields, bool $default = false): bool {
        foreach ($fields as $field) {
            if (property_exists($record, $field)) {
                return !empty($record->{$field});
            }
        }

        return $default;
    }

    /**
     * Return option list.
     *
     * @param string $key Option key.
     * @return array<int, mixed>
     */
    private function list_option(string $key): array {
        $value = $this->options[$key] ?? [];

        return is_array($value) ? array_values($value) : [];
    }

    /**
     * Normalize machine key.
     *
     * @param string $value Raw value.
     * @return string
     */
    private function normalise_key(string $value): string {
        return clean_param(trim($value), PARAM_ALPHANUMEXT);
    }

    /**
     * Format raw text safely.
     *
     * @param string $text Text.
     * @return string
     */
    private function format_raw(string $text): string {
        if ($text === '') {
            return '';
        }

        return format_text($text, FORMAT_HTML, [
            'trusted' => false,
            'noclean' => false,
            'para' => false,
        ]);
    }

    /**
     * Return whether content exists.
     *
     * @param string $content Content.
     * @return bool
     */
    private function has_content(string $content): bool {
        return trim(strip_tags($content)) !== '';
    }

    /**
     * Return date label.
     *
     * @param int $timestamp Timestamp.
     * @return string
     */
    private function date_label(int $timestamp): string {
        return $timestamp > 0 ? userdate($timestamp) : '';
    }

    /**
     * Return file size label.
     *
     * @param int $bytes File size in bytes.
     * @return string
     */
    private function filesize_label(int $bytes): string {
        if ($bytes <= 0) {
            return '';
        }

        return display_size($bytes);
    }

    /**
     * Return duration label.
     *
     * @param int $seconds Duration in seconds.
     * @return string
     */
    private function duration_label(int $seconds): string {
        if ($seconds <= 0) {
            return '';
        }

        $hours = intdiv($seconds, 3600);
        $minutes = intdiv($seconds % 3600, 60);
        $remaining = $seconds % 60;

        if ($hours > 0) {
            return sprintf('%d:%02d:%02d', $hours, $minutes, $remaining);
        }

        return sprintf('%d:%02d', $minutes, $remaining);
    }

    /**
     * Return dimensions label.
     *
     * @param int $width Width.
     * @param int $height Height.
     * @return string
     */
    private function dimensions_label(int $width, int $height): string {
        if ($width <= 0 || $height <= 0) {
            return '';
        }

        return $width . ' × ' . $height;
    }

    /**
     * Return count label.
     *
     * @param int $count Count.
     * @param string $noun Noun.
     * @return string
     */
    private function count_label(int $count, string $noun): string {
        if ($count === 1) {
            return '1 ' . $noun;
        }

        return $count . ' ' . $noun . 's';
    }

    /**
     * Return label from language string or fallback.
     *
     * @param string $identifier String identifier.
     * @param string $fallback Fallback.
     * @return string
     */
    private function label(string $identifier, string $fallback): string {
        if ($fallback === '') {
            return '';
        }

        return $this->string_or_fallback($identifier, ucfirst(str_replace('_', ' ', $fallback)));
    }

    /**
     * Return component string or fallback.
     *
     * @param string $identifier String identifier.
     * @param string $fallback Fallback.
     * @return string
     */
    private function string_or_fallback(string $identifier, string $fallback): string {
        $manager = get_string_manager();

        if ($manager->string_exists($identifier, 'uckkarchive')) {
            return get_string($identifier, 'uckkarchive');
        }

        if ($manager->string_exists($identifier, 'mod_uckkarchive')) {
            return get_string($identifier, 'mod_uckkarchive');
        }

        if ($manager->string_exists($identifier, 'moodle')) {
            return get_string($identifier, 'moodle');
        }

        return $fallback;
    }

    /**
     * Return CSS class.
     *
     * @param string $prefix Prefix.
     * @param string $value Value.
     * @return string
     */
    private function css_class(string $prefix, string $value): string {
        return $prefix . preg_replace('/[^a-z0-9_-]+/', '-', strtolower($value));
    }

    /**
     * Return status badge class.
     *
     * @param string $status Status.
     * @return string
     */
    private function status_class(string $status): string {
        return match ($status) {
            self::STATUS_ACTIVE,
            self::STATUS_REVIEWED => 'badge badge-success',
            self::STATUS_DRAFT,
            self::STATUS_PENDING_REVIEW => 'badge badge-warning',
            self::STATUS_RESTRICTED => 'badge badge-danger',
            self::STATUS_ARCHIVED,
            self::STATUS_RETIRED,
            self::STATUS_DELETED_SOFT => 'badge badge-secondary',
            default => 'badge badge-light',
        };
    }

    /**
     * Return visibility badge class.
     *
     * @param string $visibility Visibility.
     * @return string
     */
    private function visibility_class(string $visibility): string {
        return match ($visibility) {
            self::VISIBILITY_PUBLIC => 'badge badge-success',
            self::VISIBILITY_COURSE,
            self::VISIBILITY_GROUP,
            self::VISIBILITY_USER,
            self::VISIBILITY_COHORT,
            self::VISIBILITY_PROGRAM,
            self::VISIBILITY_INSTITUTION => 'badge badge-info',
            self::VISIBILITY_RESTRICTED,
            self::VISIBILITY_RESTRICTED_CULTURAL,
            self::VISIBILITY_RESTRICTED_INTEGRITY => 'badge badge-danger',
            self::VISIBILITY_PRIVATE => 'badge badge-secondary',
            default => 'badge badge-light',
        };
    }

    /**
     * Return restricted flag.
     *
     * @param string $status Status.
     * @param string $visibility Visibility.
     * @param string $audiencesuitability Audience suitability.
     * @return bool
     */
    private function is_restricted(string $status, string $visibility, string $audiencesuitability): bool {
        return $status === self::STATUS_RESTRICTED ||
            in_array($visibility, [
                self::VISIBILITY_RESTRICTED,
                self::VISIBILITY_RESTRICTED_INTEGRITY,
                self::VISIBILITY_RESTRICTED_CULTURAL,
            ], true) ||
            in_array($audiencesuitability, [
                'restricted',
                'restricted_integrity',
                'restricted_cultural',
                'staff_only',
            ], true);
    }

    /**
     * Return file rows.
     *
     * @return array<int, array<string, mixed>>
     */
    private function files_array(): array {
        $files = [];

        foreach ($this->list_option('files') as $file) {
            $file = (object)$file;

            $files[] = [
                'filearea' => $this->text_field($file, ['filearea']),
                'filearealabel' => $this->label('filearea_' . $this->text_field($file, ['filearea']), $this->text_field($file, ['filearea'])),
                'filename' => $this->text_field($file, ['filename']),
                'filepath' => $this->text_field($file, ['filepath'], '/'),
                'filesize' => $this->int_field($file, ['filesize']),
                'filesizelabel' => $this->filesize_label($this->int_field($file, ['filesize'])),
                'mimetype' => $this->text_field($file, ['mimetype']),
                'url' => $this->text_field($file, ['url']),
                'downloadurl' => $this->text_field($file, ['downloadurl']),
                'hasurl' => $this->text_field($file, ['url']) !== '',
                'hasdownloadurl' => $this->text_field($file, ['downloadurl']) !== '',
            ];
        }

        return $files;
    }

    /**
     * Return tag rows.
     *
     * @return array<int, array<string, mixed>>
     */
    private function tags_array(): array {
        $tags = [];

        foreach ($this->list_option('tags') as $tag) {
            if (is_scalar($tag)) {
                $tags[] = [
                    'key' => clean_param((string)$tag, PARAM_TEXT),
                    'label' => format_string((string)$tag),
                    'type' => '',
                ];
                continue;
            }

            $tag = (object)$tag;
            $key = $this->text_field($tag, ['key', 'tag', 'tagkey', 'name']);

            $tags[] = [
                'key' => clean_param($key, PARAM_TEXT),
                'label' => format_string($this->text_field($tag, ['label', 'name', 'tag', 'tagkey'], $key)),
                'type' => $this->text_field($tag, ['type', 'tagtype']),
            ];
        }

        return $tags;
    }

    /**
     * Return content marker rows.
     *
     * @return array<int, array<string, mixed>>
     */
    private function content_markers_array(): array {
        $markers = [];

        foreach ($this->list_option('contentmarkers') as $marker) {
            $marker = (object)$marker;
            $tag = $this->text_field($marker, ['tagkey', 'tag', 'contenttag']);

            $markers[] = [
                'id' => $this->int_field($marker, ['id', 'markerid']),
                'uuid' => $this->text_field($marker, ['uuid']),
                'tagkey' => $tag,
                'taglabel' => format_string($this->text_field($marker, ['taglabel', 'label', 'tag'], $tag)),
                'severity' => $this->normalise_key($this->text_field($marker, ['severity'])),
                'severitylabel' => $this->label('severity_' . $this->text_field($marker, ['severity']), $this->text_field($marker, ['severity'])),
                'audiencesuitability' => $this->normalise_key($this->text_field($marker, ['audiencesuitability'])),
                'reviewstate' => $this->normalise_key($this->text_field($marker, ['reviewstate', 'state'])),
                'locatortype' => $this->normalise_key($this->text_field($marker, ['locatortype'])),
                'locator' => $this->text_field($marker, ['locator', 'locatorvalue']),
                'restricted' => $this->bool_field($marker, ['restricted']),
                'culturalprotocol' => $this->bool_field($marker, ['culturalprotocol']),
            ];
        }

        return $markers;
    }

    /**
     * Return version rows.
     *
     * @return array<int, array<string, mixed>>
     */
    private function versions_array(): array {
        $versions = [];

        foreach ($this->list_option('versions') as $version) {
            $version = (object)$version;
            $versionnumber = $this->int_field($version, ['versionnumber', 'versionno', 'number']);

            $versions[] = [
                'id' => $this->int_field($version, ['id', 'versionid']),
                'uuid' => $this->text_field($version, ['uuid']),
                'versionnumber' => $versionnumber,
                'label' => format_string($this->text_field($version, ['label', 'title'], $versionnumber ? 'v' . $versionnumber : '')),
                'status' => $this->normalise_key($this->text_field($version, ['status'])),
                'iscurrent' => $this->bool_field($version, ['iscurrent']),
                'timecreated' => $this->int_field($version, ['timecreated']),
                'timecreatedlabel' => $this->date_label($this->int_field($version, ['timecreated'])),
            ];
        }

        return $versions;
    }

    /**
     * Return metadata rows.
     *
     * @param stdClass $record Record.
     * @return array<int, array<string, string>>
     */
    private function metadata_array(stdClass $record): array {
        if (!property_exists($record, 'metadata') || empty($record->metadata)) {
            return [];
        }

        $metadata = $record->metadata;

        if (is_string($metadata)) {
            $decoded = json_decode($metadata, true);
            $metadata = is_array($decoded) ? $decoded : [];
        }

        if ($metadata instanceof stdClass) {
            $metadata = (array)$metadata;
        }

        if (!is_array($metadata)) {
            return [];
        }

        $items = [];

        foreach ($metadata as $key => $value) {
            if (is_array($value) || $value instanceof stdClass) {
                $value = json_encode($value, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
            }

            $items[] = [
                'key' => clean_param((string)$key, PARAM_TEXT),
                'value' => clean_param((string)$value, PARAM_TEXT),
            ];
        }

        return $items;
    }
}