<?php
// This file is part of Moodle - https://moodle.org/
//
// Moodle is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// any later version.

/**
 * External work card output object.
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
 * Renderable card for one external work reference.
 *
 * This class prepares display data only.
 *
 * It does not:
 * - decide whether the current user may view restricted external work fields;
 * - approve cultural protocol access;
 * - approve content advisories;
 * - validate third-party rights claims;
 * - imply UCKK ownership over external or third-party works;
 * - fetch or copy external content.
 *
 * Authorization, redaction, cultural protocol access, and advisory governance
 * must already have been handled by local/domain classes or external services
 * before this object is rendered.
 */
final class external_work_card implements renderable, templatable {
    /** Work type: film. */
    public const TYPE_FILM = 'film';

    /** Work type: book. */
    public const TYPE_BOOK = 'book';

    /** Work type: article. */
    public const TYPE_ARTICLE = 'article';

    /** Work type: podcast. */
    public const TYPE_PODCAST = 'podcast';

    /** Work type: website. */
    public const TYPE_WEBSITE = 'website';

    /** Work type: external video. */
    public const TYPE_EXTERNAL_VIDEO = 'external_video';

    /** Work type: external image. */
    public const TYPE_EXTERNAL_IMAGE = 'external_image';

    /** Work type: public archive item. */
    public const TYPE_PUBLIC_ARCHIVE_ITEM = 'public_archive_item';

    /** Work type: third-party PDF. */
    public const TYPE_THIRD_PARTY_PDF = 'third_party_pdf';

    /** Work type: other. */
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

    /** Visibility: private. */
    public const VISIBILITY_PRIVATE = 'private';

    /** Visibility: user. */
    public const VISIBILITY_USER = 'user';

    /** Visibility: group. */
    public const VISIBILITY_GROUP = 'group';

    /** Visibility: course. */
    public const VISIBILITY_COURSE = 'course';

    /** Visibility: institution. */
    public const VISIBILITY_INSTITUTION = 'institution';

    /** Visibility: public. */
    public const VISIBILITY_PUBLIC = 'public';

    /** Visibility: restricted. */
    public const VISIBILITY_RESTRICTED = 'restricted';

    /** Visibility: restricted cultural. */
    public const VISIBILITY_RESTRICTED_CULTURAL = 'restricted_cultural';

    /** Visibility: restricted integrity. */
    public const VISIBILITY_RESTRICTED_INTEGRITY = 'restricted_integrity';

    /** Rights status: unknown. */
    public const RIGHTS_UNKNOWN = 'unknown';

    /** Rights status: public domain. */
    public const RIGHTS_PUBLIC_DOMAIN = 'public_domain';

    /** Rights status: open license. */
    public const RIGHTS_OPEN_LICENSE = 'open_license';

    /** Rights status: licensed. */
    public const RIGHTS_LICENSED = 'licensed';

    /** Rights status: permission required. */
    public const RIGHTS_PERMISSION_REQUIRED = 'permission_required';

    /** Rights status: fair use reference. */
    public const RIGHTS_FAIR_USE_REFERENCE = 'fair_use_reference';

    /** Rights status: restricted reference. */
    public const RIGHTS_RESTRICTED_REFERENCE = 'restricted_reference';

    /** @var stdClass External work record. */
    private stdClass $work;

    /** @var array<string, mixed> Display options. */
    private array $options;

    /**
     * Constructor.
     *
     * Expected $options keys:
     *
     * ```text
     * cmid
     * archiveid
     * courseid
     * canview
     * canupdate
     * candelete
     * canmanageadvisories
     * canviewrestricted
     * showactions
     * showurl
     * showrights
     * showadvisorycount
     * contentadvisorycount
     * contentmarkerurl
     * editurl
     * deleteurl
     * viewurl
     * ```
     *
     * @param stdClass $work Already-authorized external work record.
     * @param array<string, mixed> $options Display options and permission flags.
     */
    public function __construct(stdClass $work, array $options = []) {
        $this->work = $work;
        $this->options = array_merge($this->default_options(), $options);
    }

    /**
     * Export data for Mustache template.
     *
     * @param renderer_base $output Renderer.
     * @return stdClass
     */
    public function export_for_template(renderer_base $output): stdClass {
        $work = $this->work;

        $id = $this->int_field($work, ['id']);
        $uuid = $this->text_field($work, ['uuid']);
        $archiveid = $this->int_field($work, ['archiveid']);
        $courseid = $this->int_field($work, ['courseid']);
        $cmid = $this->int_option('cmid') ?: $this->int_field($work, ['cmid']);
        $contextid = $this->int_field($work, ['contextid']);

        $worktype = $this->normalise_key($this->text_field($work, ['worktype', 'type'], self::TYPE_OTHER));
        $status = $this->normalise_key($this->text_field($work, ['status'], self::STATUS_ACTIVE));
        $visibility = $this->normalise_key($this->text_field($work, ['visibility'], self::VISIBILITY_PRIVATE));
        $audiencesuitability = $this->normalise_key($this->text_field($work, ['audiencesuitability'], 'guided'));
        $rightsstatus = $this->normalise_key($this->text_field($work, ['rightsstatus'], self::RIGHTS_UNKNOWN));

        $title = $this->text_field($work, ['title', 'name'], get_string('externalwork', 'uckkarchive'));
        $subtitle = $this->text_field($work, ['subtitle']);
        $creator = $this->text_field($work, ['creator', 'author', 'director']);
        $publisher = $this->text_field($work, ['publisher', 'distributor']);
        $publicationyear = $this->int_field($work, ['publicationyear', 'year']);
        $language = $this->text_field($work, ['language']);
        $sourceurl = $this->text_field($work, ['sourceurl', 'url']);
        $identifier = $this->text_field($work, ['identifier']);
        $identifiertype = $this->normalise_key($this->text_field($work, ['identifiertype']));
        $citation = $this->raw_field($work, ['citation']);
        $rightsstatement = $this->raw_field($work, ['rightsstatement']);
        $licensekey = $this->text_field($work, ['licensekey']);
        $sourcenote = $this->raw_field($work, ['sourcenote']);
        $teachingnote = $this->raw_field($work, ['teachingnote']);
        $culturalprotocolnote = $this->raw_field($work, ['culturalprotocolnote']);
        $description = $this->raw_field($work, ['description', 'summary']);

        $timecreated = $this->int_field($work, ['timecreated']);
        $timemodified = $this->int_field($work, ['timemodified']);

        $canview = $this->bool_option('canview', true);
        $canupdate = $this->bool_option('canupdate');
        $candelete = $this->bool_option('candelete');
        $canmanageadvisories = $this->bool_option('canmanageadvisories');
        $canviewrestricted = $this->bool_option('canviewrestricted');
        $showactions = $this->bool_option('showactions', true);
        $showurl = $this->bool_option('showurl', true) && $sourceurl !== '';
        $showrights = $this->bool_option('showrights', true);
        $showadvisorycount = $this->bool_option('showadvisorycount', true);

        $isrestricted = $this->is_restricted($status, $visibility, $audiencesuitability);
        $isculturalrestricted = $visibility === self::VISIBILITY_RESTRICTED_CULTURAL ||
            $this->has_content($culturalprotocolnote) ||
            $this->bool_field($work, ['culturalprotocol']);

        $isredacted = $this->bool_option('redacted') || ($isrestricted && !$canviewrestricted);

        if ($isredacted) {
            $subtitle = '';
            $description = '';
            $citation = '';
            $rightsstatement = '';
            $sourcenote = '';
            $teachingnote = '';
            $culturalprotocolnote = '';
            $sourceurl = '';
            $identifier = '';
            $showurl = false;
        }

        $contentadvisorycount = $this->int_option('contentadvisorycount');
        if ($contentadvisorycount === 0) {
            $contentadvisorycount = $this->int_field($work, [
                'contentadvisorycount',
                'contentmarker_count',
                'contentmarkercount',
                'advisorycount',
            ]);
        }

        $viewurl = $this->url_option('viewurl') ?: $this->build_view_url($cmid, $id);
        $editurl = $this->url_option('editurl');
        $deleteurl = $this->url_option('deleteurl');
        $contentmarkerurl = $this->url_option('contentmarkerurl');

        $data = (object)[
            'id' => $id,
            'uuid' => $uuid,
            'archiveid' => $archiveid,
            'courseid' => $courseid,
            'cmid' => $cmid,
            'contextid' => $contextid,

            'worktype' => $worktype,
            'worktypelabel' => $this->label('externalworktype_' . $worktype, $worktype),
            'worktypeclass' => $this->css_class('uckkarchive-external-work-card--type-', $worktype),

            'status' => $status,
            'statuslabel' => $this->label('status_' . $status, $status),
            'statusclass' => $this->status_class($status),

            'visibility' => $visibility,
            'visibilitylabel' => $this->label('visibility_' . $visibility, $visibility),
            'visibilityclass' => $this->visibility_class($visibility),

            'audiencesuitability' => $audiencesuitability,
            'audiencesuitabilitylabel' => $this->label('audiencesuitability_' . $audiencesuitability, $audiencesuitability),

            'rightsstatus' => $rightsstatus,
            'rightsstatuslabel' => $this->label('rightsstatus_' . $rightsstatus, $rightsstatus),
            'rightsstatusclass' => $this->rights_class($rightsstatus),

            'title' => format_string($title),
            'subtitle' => format_string($subtitle),
            'creator' => format_string($creator),
            'publisher' => format_string($publisher),
            'publicationyear' => $publicationyear,
            'language' => $language,
            'languagelabel' => $this->language_label($language),

            'sourceurl' => $sourceurl,
            'sourceurllabel' => $this->source_url_label($sourceurl),
            'identifier' => format_string($identifier),
            'identifiertype' => $identifiertype,
            'identifiertypelabel' => $this->label('identifiertype_' . $identifiertype, $identifiertype),

            'citation' => $this->format_raw($citation),
            'rightsstatement' => $this->format_raw($rightsstatement),
            'licensekey' => format_string($licensekey),
            'sourcenote' => $this->format_raw($sourcenote),
            'teachingnote' => $this->format_raw($teachingnote),
            'culturalprotocolnote' => $this->format_raw($culturalprotocolnote),
            'description' => $this->format_raw($description),

            'ownerid' => $this->int_field($work, ['ownerid', 'userid']),
            'createdby' => $this->int_field($work, ['createdby']),
            'modifiedby' => $this->int_field($work, ['modifiedby']),
            'provenanceid' => $this->int_field($work, ['provenanceid']),
            'timecreated' => $timecreated,
            'timemodified' => $timemodified,
            'timecreatedlabel' => $this->date_label($timecreated),
            'timemodifiedlabel' => $this->date_label($timemodified),

            'contentadvisorycount' => $contentadvisorycount,
            'contentadvisorycountlabel' => $this->count_label($contentadvisorycount),

            'isrestricted' => $isrestricted,
            'isculturalrestricted' => $isculturalrestricted,
            'isredacted' => $isredacted,
            'isexternalreference' => true,
            'isthirdparty' => true,

            'hasuuid' => $uuid !== '',
            'hassubtitle' => $this->has_content($subtitle),
            'hascreator' => $this->has_content($creator),
            'haspublisher' => $this->has_content($publisher),
            'haspublicationyear' => $publicationyear > 0,
            'haslanguage' => $this->has_content($language),
            'hassourceurl' => $showurl,
            'hasidentifier' => $this->has_content($identifier),
            'hasidentifiertype' => $this->has_content($identifiertype),
            'hascitation' => $this->has_content($citation),
            'hasrightsstatement' => $this->has_content($rightsstatement),
            'haslicensekey' => $this->has_content($licensekey),
            'hassourcenote' => $this->has_content($sourcenote),
            'hasteachingnote' => $this->has_content($teachingnote),
            'hasculturalprotocolnote' => $this->has_content($culturalprotocolnote),
            'hasdescription' => $this->has_content($description),
            'hastimecreated' => $timecreated > 0,
            'hastimemodified' => $timemodified > 0,
            'hascontentadvisories' => $contentadvisorycount > 0,

            'canview' => $canview,
            'canupdate' => $canupdate,
            'candelete' => $candelete,
            'canmanageadvisories' => $canmanageadvisories,
            'canviewrestricted' => $canviewrestricted,

            'showactions' => $showactions,
            'showrights' => $showrights,
            'showadvisorycount' => $showadvisorycount,
            'showrestrictednotice' => $isrestricted,
            'showculturalnotice' => $isculturalrestricted,
            'showredactednotice' => $isredacted,

            'viewurl' => $viewurl,
            'editurl' => $editurl,
            'deleteurl' => $deleteurl,
            'contentmarkerurl' => $contentmarkerurl,

            'hasviewurl' => $viewurl !== '',
            'hasediturl' => $editurl !== '' && $canupdate,
            'hasdeleteurl' => $deleteurl !== '' && $candelete,
            'hascontentmarkerurl' => $contentmarkerurl !== '' && $canmanageadvisories,

            'actions' => $this->build_actions($viewurl, $editurl, $deleteurl, $contentmarkerurl),
            'metadata' => $this->metadata_array($work),
            'notice' => $this->build_notice($isrestricted, $isculturalrestricted, $isredacted),
        ];

        return $data;
    }

    /**
     * Return default options.
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
            'canmanageadvisories' => false,
            'canviewrestricted' => false,
            'showactions' => true,
            'showurl' => true,
            'showrights' => true,
            'showadvisorycount' => true,
            'contentadvisorycount' => 0,
            'viewurl' => '',
            'editurl' => '',
            'deleteurl' => '',
            'contentmarkerurl' => '',
            'redacted' => false,
        ];
    }

    /**
     * Build card actions.
     *
     * @param string $viewurl View URL.
     * @param string $editurl Edit URL.
     * @param string $deleteurl Delete URL.
     * @param string $contentmarkerurl Content marker URL.
     * @return array<int, array<string, mixed>>
     */
    private function build_actions(
        string $viewurl,
        string $editurl,
        string $deleteurl,
        string $contentmarkerurl
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

        if ($contentmarkerurl !== '' && $this->bool_option('canmanageadvisories')) {
            $actions[] = [
                'key' => 'advisories',
                'label' => $this->string_or_fallback('contentadvisories', 'Content advisories'),
                'url' => $contentmarkerurl,
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
     * Build restricted/cultural/redacted notice data.
     *
     * @param bool $isrestricted Restricted.
     * @param bool $isculturalrestricted Culturally restricted.
     * @param bool $isredacted Redacted.
     * @return array<string, mixed>
     */
    private function build_notice(bool $isrestricted, bool $isculturalrestricted, bool $isredacted): array {
        if ($isredacted) {
            return [
                'type' => 'redacted',
                'class' => 'alert alert-warning',
                'message' => $this->string_or_fallback(
                    'externalworkredactednotice',
                    'Some external work details are restricted.'
                ),
            ];
        }

        if ($isculturalrestricted) {
            return [
                'type' => 'cultural',
                'class' => 'alert alert-warning',
                'message' => $this->string_or_fallback(
                    'externalworkculturalnotice',
                    'This external work reference includes cultural protocol information.'
                ),
            ];
        }

        if ($isrestricted) {
            return [
                'type' => 'restricted',
                'class' => 'alert alert-info',
                'message' => $this->string_or_fallback(
                    'externalworkrestrictednotice',
                    'This external work reference has restricted visibility.'
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
     * @param int $externalworkid External work id.
     * @return string
     */
    private function build_view_url(int $cmid, int $externalworkid): string {
        if ($cmid <= 0 || $externalworkid <= 0) {
            return '';
        }

        return (new moodle_url('/mod/uckkarchive/media.php', [
            'id' => $cmid,
            'externalworkid' => $externalworkid,
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
     * Get integer option.
     *
     * @param string $key Option key.
     * @return int
     */
    private function int_option(string $key): int {
        return (int)($this->options[$key] ?? 0);
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
     * Normalize machine key.
     *
     * @param string $value Raw key.
     * @return string
     */
    private function normalise_key(string $value): string {
        return clean_param(trim($value), PARAM_ALPHANUMEXT);
    }

    /**
     * Format raw HTML text safely.
     *
     * @param string $text Raw text.
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
     * Return whether content is non-empty.
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
     * Return content advisory count label.
     *
     * @param int $count Count.
     * @return string
     */
    private function count_label(int $count): string {
        if ($count === 1) {
            return $this->string_or_fallback('onecontentadvisory', '1 content advisory');
        }

        $template = $this->string_or_fallback('contentadvisorycount', '{$a} content advisories');

        return str_replace('{$a}', (string)$count, $template);
    }

    /**
     * Return language display label.
     *
     * @param string $language Language code.
     * @return string
     */
    private function language_label(string $language): string {
        if ($language === '') {
            return '';
        }

        $languages = get_string_manager()->get_list_of_languages();

        return $languages[$language] ?? strtoupper($language);
    }

    /**
     * Return short source URL label.
     *
     * @param string $url URL.
     * @return string
     */
    private function source_url_label(string $url): string {
        if ($url === '') {
            return '';
        }

        $host = parse_url($url, PHP_URL_HOST);

        return $host ? (string)$host : $url;
    }

    /**
     * Return label from string key with fallback.
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
        if (get_string_manager()->string_exists($identifier, 'uckkarchive')) {
            return get_string($identifier, 'uckkarchive');
        }

        if (get_string_manager()->string_exists($identifier, 'mod_uckkarchive')) {
            return get_string($identifier, 'mod_uckkarchive');
        }

        if (get_string_manager()->string_exists($identifier, 'moodle')) {
            return get_string($identifier, 'moodle');
        }

        return $fallback;
    }

    /**
     * Return CSS class suffix.
     *
     * @param string $prefix Prefix.
     * @param string $value Value.
     * @return string
     */
    private function css_class(string $prefix, string $value): string {
        return $prefix . preg_replace('/[^a-z0-9_-]+/', '-', strtolower($value));
    }

    /**
     * Return status class.
     *
     * @param string $status Status.
     * @return string
     */
    private function status_class(string $status): string {
        return match ($status) {
            self::STATUS_ACTIVE,
            self::STATUS_REVIEWED => 'badge badge-success',
            self::STATUS_PENDING_REVIEW,
            self::STATUS_DRAFT => 'badge badge-warning',
            self::STATUS_RESTRICTED => 'badge badge-danger',
            self::STATUS_RETIRED,
            self::STATUS_ARCHIVED => 'badge badge-secondary',
            default => 'badge badge-light',
        };
    }

    /**
     * Return visibility class.
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
            self::VISIBILITY_INSTITUTION => 'badge badge-info',
            self::VISIBILITY_RESTRICTED,
            self::VISIBILITY_RESTRICTED_CULTURAL,
            self::VISIBILITY_RESTRICTED_INTEGRITY => 'badge badge-danger',
            self::VISIBILITY_PRIVATE => 'badge badge-secondary',
            default => 'badge badge-light',
        };
    }

    /**
     * Return rights class.
     *
     * @param string $rightsstatus Rights status.
     * @return string
     */
    private function rights_class(string $rightsstatus): string {
        return match ($rightsstatus) {
            self::RIGHTS_PUBLIC_DOMAIN,
            self::RIGHTS_OPEN_LICENSE,
            self::RIGHTS_LICENSED => 'badge badge-success',
            self::RIGHTS_FAIR_USE_REFERENCE,
            self::RIGHTS_PERMISSION_REQUIRED => 'badge badge-warning',
            self::RIGHTS_RESTRICTED_REFERENCE,
            self::RIGHTS_UNKNOWN => 'badge badge-secondary',
            default => 'badge badge-light',
        };
    }

    /**
     * Return whether the work should be treated as restricted.
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
                self::VISIBILITY_RESTRICTED_CULTURAL,
                self::VISIBILITY_RESTRICTED_INTEGRITY,
            ], true) ||
            in_array($audiencesuitability, [
                'restricted',
                'restricted_cultural',
                'restricted_integrity',
                'staff_only',
            ], true);
    }

    /**
     * Return metadata as Mustache-friendly array.
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