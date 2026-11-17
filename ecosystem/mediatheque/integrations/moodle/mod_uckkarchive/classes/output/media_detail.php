<?php
// This file is part of Moodle - https://moodle.org/.
//
// Moodle is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// any later version.

/**
 * Media detail renderable for mod_uckkarchive.
 *
 * This renderable prepares a single media record for the internal
 * Médiathèque detail view.
 *
 * It does not decide media access, bypass content advisories, expose private
 * files, mutate Moodle data, or validate publication policy. The controller
 * and media policy services must resolve permissions before this object is
 * rendered.
 *
 * @package    mod_uckkarchive
 * @copyright  2026 Univers-Cité King Klown
 * @license    https://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later
 */

declare(strict_types=1);

namespace mod_uckkarchive\output;

use context_module;
use core\output\notification;
use moodle_url;
use renderable;
use renderer_base;
use stdClass;
use templatable;

defined('MOODLE_INTERNAL') || die();

/**
 * Media detail renderable.
 *
 * Expected template:
 *
 *     mod_uckkarchive/media_detail
 *
 * @package mod_uckkarchive
 */
final class media_detail implements renderable, templatable {
    /**
     * String components accepted while language files are being consolidated.
     */
    private const STRING_COMPONENTS = [
        'uckkarchive',
        'mod_uckkarchive',
    ];

    /**
     * Source types that represent external references.
     */
    private const EXTERNAL_SOURCE_TYPES = [
        'external_reference_only',
        'licensed_external',
        'public_domain',
        'fair_use_reference',
        'restricted_reference',
    ];

    /**
     * Media types that commonly represent auxiliary internal files.
     */
    private const AUXILIARY_MEDIA_TYPES = [
        'thumbnail',
        'preview',
        'derivative',
        'caption',
        'transcript',
        'attachment',
    ];

    /** @var context_module Module context. */
    private context_module $context;

    /** @var stdClass Course record. */
    private stdClass $course;

    /** @var stdClass Course module record. */
    private stdClass $cm;

    /** @var stdClass Archive instance record. */
    private stdClass $archive;

    /** @var stdClass Media record. */
    private stdClass $media;

    /** @var string Optional notification message. */
    private string $notificationmessage;

    /** @var string Moodle notification type. */
    private string $notificationtype;

    /**
     * Constructor.
     *
     * @param context_module $context Module context.
     * @param stdClass $course Course record.
     * @param stdClass $cm Course module record.
     * @param stdClass $archive Archive instance record.
     * @param stdClass $media Already-authorized media record.
     * @param string $notificationmessage Optional notification message.
     * @param string $notificationtype Notification type.
     */
    public function __construct(
        context_module $context,
        stdClass $course,
        stdClass $cm,
        stdClass $archive,
        stdClass $media,
        string $notificationmessage = '',
        string $notificationtype = notification::NOTIFY_INFO
    ) {
        $this->context = $context;
        $this->course = $course;
        $this->cm = $cm;
        $this->archive = $archive;
        $this->media = $media;
        $this->notificationmessage = $notificationmessage;
        $this->notificationtype = $notificationtype;
    }

    /**
     * Return Mustache template name.
     *
     * @param renderer_base $renderer Renderer.
     * @return string Template name.
     */
    public function get_template_name(renderer_base $renderer): string {
        return 'mod_uckkarchive/media_detail';
    }

    /**
     * Export data for Mustache.
     *
     * @param renderer_base $output Renderer.
     * @return stdClass Template data.
     */
    public function export_for_template(renderer_base $output): stdClass {
        $media = $this->media;

        $mediaid = self::int_field($media, ['id']);
        $cmid = (int)$this->cm->id;
        $archiveid = (int)$this->archive->id;
        $courseid = (int)$this->course->id;
        $contextid = (int)$this->context->id;

        $title = self::text_field($media, ['title', 'name'], self::string('media', 'Media'));
        $summary = self::raw_field($media, ['summary']);
        $description = self::raw_field($media, ['description']);
        $mediatype = self::normalise_key(self::text_field($media, ['mediatype', 'type'], 'document'));
        $mimetype = self::text_field($media, ['mimetype']);
        $status = self::normalise_key(self::text_field($media, ['status'], 'draft'));
        $visibility = self::normalise_key(self::text_field($media, ['visibility'], 'course'));
        $audience = self::normalise_key(self::text_field($media, ['audiencesuitability'], 'guided'));
        $sourcetype = self::normalise_key(self::text_field($media, ['sourcetype', 'source']));
        $sourceownership = self::normalise_key(self::text_field($media, ['sourceownership']));
        $sourceurl = self::url_field($media, ['sourceurl', 'url', 'externalurl', 'referenceurl']);
        $license = self::text_field($media, ['license', 'licensekey']);
        $rightsnote = self::raw_field($media, ['rightsstatement', 'rightsnote', 'rightsstatus']);
        $citation = self::raw_field($media, ['citation']);
        $language = self::text_field($media, ['language', 'lang']);
        $externalworkid = self::int_field($media, ['externalworkid']);
        $restricted = self::bool_field($media, ['restricted', 'isrestricted']);
        $culturalprotocol = self::bool_field($media, ['culturalprotocol', 'culturalprotocolrequired']);
        $metadata = self::decode_metadata(self::raw_field($media, ['metadata', 'metadatajson']));

        $creator = self::metadata_or_field($metadata, $media, 'creator', ['creator', 'author']);
        $datecreated = self::metadata_or_field($metadata, $media, 'datecreated', ['datecreated', 'createddate']);
        $alttext = self::metadata_or_field($metadata, $media, 'alttext', ['alttext']);
        $transcriptsummary = self::metadata_or_field($metadata, $media, 'transcriptsummary', ['transcriptsummary']);
        $collectionhint = self::metadata_or_field($metadata, $media, 'collectionhint', ['collectionhint']);
        $advisoryhint = self::metadata_or_field($metadata, $media, 'advisoryhint', ['advisoryhint']);
        $culturalprotocolnote = self::metadata_or_field(
            $metadata,
            $media,
            'culturalprotocolnote',
            ['culturalprotocolnote']
        );

        $hasexternalurl = self::is_external_reference($sourcetype, $mediatype, $sourceurl);
        $canedit = has_capability('mod/uckkarchive:editmedia', $this->context);
        $canversion = has_capability('mod/uckkarchive:versionmedia', $this->context);
        $candownload = has_capability('mod/uckkarchive:downloadmedia', $this->context);
        $canexport = has_capability('mod/uckkarchive:exportmedia', $this->context)
            || has_capability('mod/uckkarchive:export', $this->context);
        $canmanageadvisories = has_capability('mod/uckkarchive:manageadvisories', $this->context);

        $libraryurl = new moodle_url('/mod/uckkarchive/media.php', [
            'id' => $cmid,
        ]);

        $viewurl = new moodle_url('/mod/uckkarchive/media.php', [
            'id' => $cmid,
            'mediaid' => $mediaid,
            'action' => 'view',
        ]);

        $editurl = new moodle_url('/mod/uckkarchive/media.php', [
            'id' => $cmid,
            'mediaid' => $mediaid,
            'action' => 'edit',
        ]);

        $versionurl = new moodle_url('/mod/uckkarchive/media.php', [
            'id' => $cmid,
            'mediaid' => $mediaid,
            'action' => 'versions',
        ]);

        $downloadurl = new moodle_url('/mod/uckkarchive/download.php', [
            'id' => $cmid,
            'mediaid' => $mediaid,
        ]);

        $exporturl = new moodle_url('/mod/uckkarchive/export.php', [
            'id' => $cmid,
            'mediaid' => $mediaid,
            'area' => 'media',
        ]);

        $data = new stdClass();

        $data->id = $mediaid;
        $data->mediaid = $mediaid;
        $data->cmid = $cmid;
        $data->archiveid = $archiveid;
        $data->courseid = $courseid;
        $data->contextid = $contextid;

        $data->component = 'mod_uckkarchive';
        $data->pagetype = 'media_detail';
        $data->classes = self::join_classes([
            'uckkarchive-media-detail',
            'uckkarchive-media-detail--' . $mediatype,
            $restricted ? 'uckkarchive-media-detail--restricted' : null,
            $culturalprotocol ? 'uckkarchive-media-detail--cultural-protocol' : null,
            $hasexternalurl ? 'uckkarchive-media-detail--external-reference' : null,
        ]);

        $data->course = self::export_course($this->course);
        $data->archive = self::export_archive($this->archive);
        $data->cm = self::export_cm($this->cm);

        $data->title = format_string($title, true, ['context' => $this->context]);
        $data->summary = self::format_rich_text($summary, $output, $this->context);
        $data->description = self::format_rich_text($description, $output, $this->context);
        $data->hassummary = trim($summary) !== '';
        $data->hasdescription = trim($description) !== '';

        $data->mediatype = $mediatype;
        $data->mediatypelabel = self::media_type_label($mediatype);
        $data->mimetype = $mimetype;
        $data->hasmimetype = $mimetype !== '';

        $data->status = $status;
        $data->statuslabel = self::status_label($status);
        $data->visibility = $visibility;
        $data->visibilitylabel = self::visibility_label($visibility);
        $data->audiencesuitability = $audience;
        $data->audiencesuitabilitylabel = self::audience_label($audience);

        $data->sourcetype = $sourcetype;
        $data->sourcetypelabel = self::source_type_label($sourcetype);
        $data->sourceownership = $sourceownership;
        $data->sourceownershiplabel = self::humanise_key($sourceownership);
        $data->hassourcetype = $sourcetype !== '';
        $data->hassourceownership = $sourceownership !== '';

        $data->sourceurl = $sourceurl;
        $data->externalurl = $sourceurl;
        $data->hasexternalurl = $hasexternalurl;
        $data->isexternalreference = $hasexternalurl;
        $data->canopenexternal = $hasexternalurl;
        $data->openexternallabel = self::string('openexternal', 'Ouvrir la référence externe');

        $data->license = $license;
        $data->haslicense = $license !== '';
        $data->rightsnote = self::format_rich_text($rightsnote, $output, $this->context);
        $data->hasrightsnote = trim($rightsnote) !== '';
        $data->citation = self::format_rich_text($citation, $output, $this->context);
        $data->hascitation = trim($citation) !== '';

        $data->language = $language;
        $data->haslanguage = $language !== '';
        $data->externalworkid = $externalworkid;
        $data->hasexternalwork = $externalworkid > 0;

        $data->creator = $creator;
        $data->hascreator = $creator !== '';
        $data->datecreated = $datecreated;
        $data->hasdatecreated = $datecreated !== '';
        $data->alttext = $alttext;
        $data->hasalttext = $alttext !== '';
        $data->transcriptsummary = $transcriptsummary;
        $data->hastranscriptsummary = $transcriptsummary !== '';
        $data->collectionhint = $collectionhint;
        $data->hascollectionhint = $collectionhint !== '';
        $data->advisoryhint = $advisoryhint;
        $data->hasadvisoryhint = $advisoryhint !== '';
        $data->culturalprotocolnote = $culturalprotocolnote;
        $data->hasculturalprotocolnote = $culturalprotocolnote !== '';

        $data->isrestricted = $restricted;
        $data->isculturallyrestricted = $culturalprotocol;
        $data->isauxiliarytype = in_array($mediatype, self::AUXILIARY_MEDIA_TYPES, true);

        $data->timecreated = self::int_field($media, ['timecreated']);
        $data->timemodified = self::int_field($media, ['timemodified']);
        $data->timecreatedformatted = self::format_time($data->timecreated);
        $data->timemodifiedformatted = self::format_time($data->timemodified);
        $data->hastimecreated = $data->timecreated > 0;
        $data->hastimemodified = $data->timemodified > 0;

        $data->metadata = self::export_metadata($metadata);
        $data->hasmetadata = !empty($data->metadata);
        $data->metadatajson = json_encode($metadata, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES) ?: '{}';

        $data->libraryurl = $libraryurl->out(false);
        $data->viewurl = $viewurl->out(false);
        $data->editurl = $editurl->out(false);
        $data->versionurl = $versionurl->out(false);
        $data->downloadurl = $downloadurl->out(false);
        $data->exporturl = $exporturl->out(false);

        $data->canedit = $canedit;
        $data->canversion = $canversion;
        $data->candownload = $candownload;
        $data->canexport = $canexport;
        $data->canmanageadvisories = $canmanageadvisories;

        $data->actions = [
            'view' => true,
            'openexternal' => $data->canopenexternal,
            'edit' => $canedit,
            'version' => $canversion,
            'download' => $candownload,
            'export' => $canexport,
            'manageadvisories' => $canmanageadvisories,
        ];

        $data->strings = [
            'backtolibrary' => self::string('backtomediatheque', 'Retour à la Médiathèque'),
            'mediaidentity' => self::string('mediaidentity', 'Identité du média'),
            'mediasource' => self::string('mediasource', 'Source du média'),
            'mediagovernance' => self::string('mediagovernance', 'Gouvernance du média'),
            'metadata' => self::string('metadata', 'Métadonnées'),
            'rights' => self::string('rights', 'Droits'),
            'citation' => self::string('citation', 'Citation'),
            'openexternal' => self::string('openexternal', 'Ouvrir la référence externe'),
            'edit' => self::string('edit', 'Modifier'),
            'versions' => self::string('versions', 'Versions'),
            'download' => self::string('download', 'Télécharger'),
            'export' => self::string('export', 'Exporter'),
            'manageadvisories' => self::string('manageadvisories', 'Gérer les avis de contenu'),
        ];

        $data->notificationmessage = $this->notificationmessage;
        $data->notificationtype = $this->notificationtype;
        $data->hasnotification = $this->notificationmessage !== '';

        return $data;
    }

    /**
     * Export course data.
     *
     * @param stdClass $course Course record.
     * @return stdClass
     */
    private static function export_course(stdClass $course): stdClass {
        $data = new stdClass();
        $data->id = (int)($course->id ?? 0);
        $data->fullname = format_string((string)($course->fullname ?? ''), true);
        $data->shortname = format_string((string)($course->shortname ?? ''), true);

        return $data;
    }

    /**
     * Export archive data.
     *
     * @param stdClass $archive Archive instance record.
     * @return stdClass
     */
    private static function export_archive(stdClass $archive): stdClass {
        $data = new stdClass();
        $data->id = (int)($archive->id ?? 0);
        $data->name = format_string((string)($archive->name ?? ''), true);
        $data->intro = (string)($archive->intro ?? '');
        $data->hasintro = trim($data->intro) !== '';

        return $data;
    }

    /**
     * Export course module data.
     *
     * @param stdClass $cm Course module record.
     * @return stdClass
     */
    private static function export_cm(stdClass $cm): stdClass {
        $data = new stdClass();
        $data->id = (int)($cm->id ?? 0);
        $data->name = format_string((string)($cm->name ?? ''), true);

        return $data;
    }

    /**
     * Return whether a media record is an external reference.
     *
     * @param string $sourcetype Source type.
     * @param string $mediatype Media type.
     * @param string $sourceurl Source URL.
     * @return bool
     */
    private static function is_external_reference(string $sourcetype, string $mediatype, string $sourceurl): bool {
        if ($sourceurl === '') {
            return false;
        }

        if (in_array($sourcetype, self::EXTERNAL_SOURCE_TYPES, true)) {
            return true;
        }

        return in_array($mediatype, ['external', 'external_reference', 'other'], true);
    }

    /**
     * Export metadata as label/value rows.
     *
     * @param array<string, mixed> $metadata Metadata.
     * @return array<int, stdClass>
     */
    private static function export_metadata(array $metadata): array {
        $out = [];

        foreach ($metadata as $key => $value) {
            if (is_array($value) || is_object($value)) {
                $value = json_encode($value, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
            }

            if ($value === null || trim((string)$value) === '') {
                continue;
            }

            $row = new stdClass();
            $row->key = self::normalise_key((string)$key);
            $row->label = self::humanise_key((string)$key);
            $row->value = trim((string)$value);

            $out[] = $row;
        }

        return $out;
    }

    /**
     * Decode metadata JSON safely.
     *
     * @param string $raw Raw metadata JSON.
     * @return array<string, mixed>
     */
    private static function decode_metadata(string $raw): array {
        $raw = trim($raw);

        if ($raw === '') {
            return [];
        }

        $decoded = json_decode($raw, true);

        if (json_last_error() !== JSON_ERROR_NONE || !is_array($decoded)) {
            return [
                'raw' => $raw,
            ];
        }

        return $decoded;
    }

    /**
     * Return a metadata value or a fallback record field.
     *
     * @param array<string, mixed> $metadata Metadata.
     * @param stdClass $record Record.
     * @param string $metakey Metadata key.
     * @param array<int, string> $fields Fallback fields.
     * @return string
     */
    private static function metadata_or_field(array $metadata, stdClass $record, string $metakey, array $fields): string {
        if (array_key_exists($metakey, $metadata) && is_scalar($metadata[$metakey])) {
            return trim((string)$metadata[$metakey]);
        }

        return self::text_field($record, $fields);
    }

    /**
     * Format rich text safely for Moodle output.
     *
     * @param string $text Raw text.
     * @param renderer_base $output Renderer.
     * @param context_module $context Module context.
     * @return string
     */
    private static function format_rich_text(string $text, renderer_base $output, context_module $context): string {
        $text = trim($text);

        if ($text === '') {
            return '';
        }

        return format_text($text, FORMAT_HTML, [
            'context' => $context,
            'trusted' => false,
            'filter' => true,
        ]);
    }

    /**
     * Return a text field from a record.
     *
     * @param stdClass $record Record.
     * @param array<int, string> $fields Candidate fields.
     * @param string $default Default value.
     * @return string
     */
    private static function text_field(stdClass $record, array $fields, string $default = ''): string {
        foreach ($fields as $field) {
            if (property_exists($record, $field) && is_scalar($record->{$field})) {
                $value = trim((string)$record->{$field});

                if ($value !== '') {
                    return $value;
                }
            }
        }

        return $default;
    }

    /**
     * Return a raw string field from a record.
     *
     * @param stdClass $record Record.
     * @param array<int, string> $fields Candidate fields.
     * @param string $default Default value.
     * @return string
     */
    private static function raw_field(stdClass $record, array $fields, string $default = ''): string {
        return self::text_field($record, $fields, $default);
    }

    /**
     * Return an integer field from a record.
     *
     * @param stdClass $record Record.
     * @param array<int, string> $fields Candidate fields.
     * @param int $default Default value.
     * @return int
     */
    private static function int_field(stdClass $record, array $fields, int $default = 0): int {
        foreach ($fields as $field) {
            if (property_exists($record, $field) && is_numeric($record->{$field})) {
                return (int)$record->{$field};
            }
        }

        return $default;
    }

    /**
     * Return a boolean field from a record.
     *
     * @param stdClass $record Record.
     * @param array<int, string> $fields Candidate fields.
     * @param bool $default Default value.
     * @return bool
     */
    private static function bool_field(stdClass $record, array $fields, bool $default = false): bool {
        foreach ($fields as $field) {
            if (!property_exists($record, $field)) {
                continue;
            }

            $value = $record->{$field};

            if (is_bool($value)) {
                return $value;
            }

            if (is_numeric($value)) {
                return (int)$value !== 0;
            }

            if (is_string($value)) {
                return in_array(strtolower(trim($value)), ['1', 'true', 'yes', 'y'], true);
            }
        }

        return $default;
    }

    /**
     * Return a clean URL field from a record.
     *
     * @param stdClass $record Record.
     * @param array<int, string> $fields Candidate fields.
     * @return string
     */
    private static function url_field(stdClass $record, array $fields): string {
        foreach ($fields as $field) {
            if (!property_exists($record, $field) || !is_scalar($record->{$field})) {
                continue;
            }

            $url = trim((string)$record->{$field});

            if ($url === '') {
                continue;
            }

            $clean = clean_param($url, PARAM_URL);

            if ($clean !== '') {
                return $clean;
            }
        }

        return '';
    }

    /**
     * Get a component string with fallback.
     *
     * @param string $identifier String identifier.
     * @param string $fallback Fallback string.
     * @return string
     */
    private static function string(string $identifier, string $fallback): string {
        $manager = get_string_manager();

        foreach (self::STRING_COMPONENTS as $component) {
            if ($manager->string_exists($identifier, $component)) {
                return get_string($identifier, $component);
            }
        }

        return $fallback;
    }

    /**
     * Return a media type label.
     *
     * @param string $type Media type.
     * @return string
     */
    private static function media_type_label(string $type): string {
        if ($type === '') {
            return '';
        }

        return self::string('mediatype:' . $type, self::humanise_key($type));
    }

    /**
     * Return a status label.
     *
     * @param string $status Status.
     * @return string
     */
    private static function status_label(string $status): string {
        if ($status === '') {
            return '';
        }

        return self::string('status:' . $status, self::humanise_key($status));
    }

    /**
     * Return a visibility label.
     *
     * @param string $visibility Visibility.
     * @return string
     */
    private static function visibility_label(string $visibility): string {
        if ($visibility === '') {
            return '';
        }

        return self::string('visibility:' . $visibility, self::humanise_key($visibility));
    }

    /**
     * Return an audience suitability label.
     *
     * @param string $audience Audience suitability.
     * @return string
     */
    private static function audience_label(string $audience): string {
        if ($audience === '') {
            return '';
        }

        return self::string('audiencesuitability:' . $audience, self::humanise_key($audience));
    }

    /**
     * Return a source type label.
     *
     * @param string $sourcetype Source type.
     * @return string
     */
    private static function source_type_label(string $sourcetype): string {
        if ($sourcetype === '') {
            return '';
        }

        return self::string('sourcetype:' . $sourcetype, self::humanise_key($sourcetype));
    }

    /**
     * Normalise a key for CSS/data use.
     *
     * @param string $key Raw key.
     * @return string
     */
    private static function normalise_key(string $key): string {
        $key = strtolower(trim($key));
        $key = preg_replace('/[^a-z0-9_-]+/', '_', $key) ?? '';
        $key = trim($key, '_-');

        return $key;
    }

    /**
     * Humanise a machine key.
     *
     * @param string $key Raw key.
     * @return string
     */
    private static function humanise_key(string $key): string {
        $key = trim($key);

        if ($key === '') {
            return '';
        }

        $key = str_replace(['_', '-'], ' ', $key);
        $key = preg_replace('/\s+/', ' ', $key) ?? $key;

        return ucfirst(trim($key));
    }

    /**
     * Format a timestamp.
     *
     * @param int $timestamp Unix timestamp.
     * @return string
     */
    private static function format_time(int $timestamp): string {
        if ($timestamp <= 0) {
            return '';
        }

        return userdate($timestamp);
    }

    /**
     * Join CSS classes.
     *
     * @param array<int, string|null|false> $classes CSS classes.
     * @return string
     */
    private static function join_classes(array $classes): string {
        $out = [];

        foreach ($classes as $class) {
            if (!is_string($class)) {
                continue;
            }

            $class = trim($class);

            if ($class !== '') {
                $out[] = $class;
            }
        }

        return implode(' ', $out);
    }
}