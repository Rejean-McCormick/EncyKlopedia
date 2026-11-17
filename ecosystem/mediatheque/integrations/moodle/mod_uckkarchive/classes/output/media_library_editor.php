<?php
// This file is part of Moodle - https://moodle.org/.
//
// Moodle is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// any later version.

/**
 * Unified media-library editor renderable for mod_uckkarchive.
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
 * Unified media-library editor renderable.
 *
 * This output object composes the existing media form, marker/advisory entry
 * points, relation/version links, provenance summary, and validation state into
 * one workflow screen. It does not create, update, validate, restrict, publish,
 * export, or authorize media records. Those responsibilities remain in the
 * controller and local policy/service classes.
 */
final class media_library_editor implements renderable, templatable {
    /** @var context_module Module context. */
    private context_module $context;

    /** @var stdClass Course record. */
    private stdClass $course;

    /** @var stdClass Course module record. */
    private stdClass $cm;

    /** @var stdClass Archive instance record. */
    private stdClass $archive;

    /** @var stdClass|null Media record being edited. */
    private ?stdClass $media;

    /** @var string Already-rendered Moodle form HTML. */
    private string $formhtml;

    /** @var string Current editor action. */
    private string $action;

    /** @var string Optional notification message. */
    private string $notification;

    /** @var string Optional notification type. */
    private string $notificationtype;

    /** @var array<string,mixed> Additional display options. */
    private array $options;

    /**
     * Constructor.
     *
     * @param context_module $context Module context.
     * @param stdClass $course Course record.
     * @param stdClass $cm Course module record.
     * @param stdClass $archive Archive instance record.
     * @param stdClass|null $media Media record, null when creating.
     * @param string $formhtml Rendered Moodle form HTML.
     * @param string $action Current action.
     * @param string $notification Optional notification.
     * @param string $notificationtype Notification type.
     * @param array<string,mixed> $options Additional display options.
     */
    public function __construct(
        context_module $context,
        stdClass $course,
        stdClass $cm,
        stdClass $archive,
        ?stdClass $media,
        string $formhtml,
        string $action = 'edit',
        string $notification = '',
        string $notificationtype = 'info',
        array $options = []
    ) {
        $this->context = $context;
        $this->course = $course;
        $this->cm = $cm;
        $this->archive = $archive;
        $this->media = $media;
        $this->formhtml = $formhtml;
        $this->action = $this->normalise_key($action);
        $this->notification = $notification;
        $this->notificationtype = $this->normalise_notification_type($notificationtype);
        $this->options = $options;
    }

    /**
     * Export data for Mustache.
     *
     * @param renderer_base $output Renderer.
     * @return stdClass
     */
    public function export_for_template(renderer_base $output): stdClass {
        $data = new stdClass();

        $data->cmid = (int)$this->cm->id;
        $data->archiveid = (int)$this->archive->id;
        $data->contextid = (int)$this->context->id;
        $data->action = $this->action;
        $data->isnew = $this->media === null;
        $data->isedit = !$data->isnew;

        $data->archive = $this->export_archive();
        $data->course = $this->export_course();
        $data->media = $this->export_media();
        $data->hasmedia = $this->media !== null;

        $data->formhtml = $this->formhtml;
        $data->hasform = trim($this->formhtml) !== '';

        $data->notification = $this->notification;
        $data->notificationtype = $this->notificationtype;
        $data->hasnotification = trim($this->notification) !== '';

        $data->urls = $this->export_urls();
        $data->capabilities = $this->export_capabilities();
        $data->strings = $this->export_strings();

        $data->workflow = $this->export_workflow_steps();
        $data->governanceitems = $this->export_governance_items();
        $data->hasgovernanceitems = !empty($data->governanceitems);
        $data->markersummary = $this->export_marker_summary();
        $data->relationsummary = $this->export_relation_summary();
        $data->versionsummary = $this->export_version_summary();

        $data->showmarkerentry = $data->hasmedia && $data->capabilities->manageadvisories;
        $data->showversionentry = $data->hasmedia && $data->capabilities->versionmedia;
        $data->showrelationentry = $data->hasmedia && $data->capabilities->editmedia;
        $data->showexportentry = $data->hasmedia && $data->capabilities->exportmedia;

        return $data;
    }

    /**
     * Export archive summary.
     *
     * @return stdClass
     */
    private function export_archive(): stdClass {
        $archive = new stdClass();
        $archive->id = (int)$this->archive->id;
        $archive->name = format_string((string)($this->archive->name ?? ''), true, ['context' => $this->context]);

        return $archive;
    }

    /**
     * Export course summary.
     *
     * @return stdClass
     */
    private function export_course(): stdClass {
        $course = new stdClass();
        $course->id = (int)$this->course->id;
        $course->fullname = format_string((string)($this->course->fullname ?? ''), true, ['context' => $this->context]);
        $course->shortname = format_string((string)($this->course->shortname ?? ''), true, ['context' => $this->context]);

        return $course;
    }

    /**
     * Export selected media summary.
     *
     * @return stdClass
     */
    private function export_media(): stdClass {
        $item = $this->media ?? new stdClass();

        $media = new stdClass();
        $media->id = (int)($item->id ?? 0);
        $media->uuid = (string)($item->uuid ?? '');
        $media->title = format_string(
            (string)($item->title ?? $this->string('newmediarecord', 'New media record')),
            true,
            ['context' => $this->context]
        );
        $media->description = format_text((string)($item->description ?? $item->summary ?? ''), FORMAT_HTML, [
            'context' => $this->context,
            'para' => false,
        ]);
        $media->hasdescription = trim(strip_tags($media->description)) !== '';

        $media->mediatype = $this->normalise_key((string)($item->mediatype ?? 'document'));
        $media->mediatypelabel = $this->string('mediatype:' . $media->mediatype, $media->mediatype);
        $media->mediatypeclass = $this->css_class('media-type', $media->mediatype);

        $media->status = $this->normalise_key((string)($item->status ?? 'draft'));
        $media->statuslabel = $this->status_label($media->status);
        $media->statusclass = $this->css_class('status', $media->status);

        $media->visibility = $this->normalise_key((string)($item->visibility ?? 'course'));
        $media->visibilitylabel = $this->visibility_label($media->visibility);
        $media->visibilityclass = $this->css_class('visibility', $media->visibility);

        $media->audiencesuitability = $this->normalise_key((string)($item->audiencesuitability ?? 'guided'));
        $media->audiencesuitabilitylabel = $this->audience_label($media->audiencesuitability);
        $media->audiencesuitabilityclass = $this->css_class('audience-suitability', $media->audiencesuitability);

        $media->language = (string)($item->language ?? '');
        $media->haslanguage = $media->language !== '';
        $media->license = (string)($item->license ?? $item->licensekey ?? '');
        $media->haslicense = $media->license !== '';
        $media->source = (string)($item->source ?? $item->sourcetype ?? '');
        $media->hassource = $media->source !== '';
        $media->versionno = (int)($item->versionno ?? 1);
        $media->hasversion = $media->id > 0;

        $media->isrestricted = $this->is_restricted($media->visibility, $media->status, $media->audiencesuitability, $item);
        $media->isculturallyrestricted = $media->visibility === 'restricted_cultural'
            || $media->audiencesuitability === 'restricted_cultural'
            || !empty($item->culturalprotocol);
        $media->isintegrityrestricted = $media->visibility === 'restricted_integrity'
            || $media->audiencesuitability === 'restricted_integrity'
            || !empty($item->integritycaseid);

        $media->timecreated = (int)($item->timecreated ?? 0);
        $media->timemodified = (int)($item->timemodified ?? 0);
        $media->timecreatedformatted = $media->timecreated > 0 ? userdate($media->timecreated) : '';
        $media->timemodifiedformatted = $media->timemodified > 0 ? userdate($media->timemodified) : '';

        return $media;
    }

    /**
     * Export editor workflow steps.
     *
     * @return array<int,stdClass>
     */
    private function export_workflow_steps(): array {
        $steps = [
            'reception' => 'mediaeditorstep_reception',
            'identification' => 'mediaeditorstep_identification',
            'qualification' => 'mediaeditorstep_qualification',
            'markers' => 'mediaeditorstep_markers',
            'advisories' => 'mediaeditorstep_advisories',
            'relations' => 'mediaeditorstep_relations',
            'validation' => 'mediaeditorstep_validation',
        ];

        $items = [];
        $position = 1;

        foreach ($steps as $key => $stringkey) {
            $item = new stdClass();
            $item->key = $key;
            $item->number = $position;
            $item->label = $this->string($stringkey, ucfirst($key));
            $item->target = 'uckkarchive-media-editor-panel-' . $key;
            $item->active = ($position === 1);
            $item->available = $this->media !== null || in_array($key, ['reception', 'identification', 'qualification'], true);
            $item->class = $item->active ? 'is-active' : '';
            $items[] = $item;
            $position++;
        }

        return $items;
    }

    /**
     * Export governance key/value items.
     *
     * @return array<int,stdClass>
     */
    private function export_governance_items(): array {
        $media = $this->export_media();

        return [
            $this->governance_item('mediastatus', 'Status', $media->statuslabel, $media->statusclass),
            $this->governance_item('visibility', 'Visibility', $media->visibilitylabel, $media->visibilityclass),
            $this->governance_item(
                'audiencesuitability',
                'Audience suitability',
                $media->audiencesuitabilitylabel,
                $media->audiencesuitabilityclass
            ),
        ];
    }

    /**
     * Build one governance item.
     *
     * @param string $key String key.
     * @param string $fallback Fallback label.
     * @param string $value Display value.
     * @param string $class CSS class.
     * @return stdClass
     */
    private function governance_item(string $key, string $fallback, string $value, string $class): stdClass {
        $item = new stdClass();
        $item->label = $this->string($key, $fallback);
        $item->value = $value;
        $item->class = $class;

        return $item;
    }

    /**
     * Marker summary.
     *
     * @return stdClass
     */
    private function export_marker_summary(): stdClass {
        $summary = new stdClass();
        $summary->label = $this->string('passagemarkers', 'Passage markers');
        $summary->count = (int)($this->options['contentmarkercount'] ?? 0);
        $summary->hasitems = $summary->count > 0;

        return $summary;
    }

    /**
     * Relation summary.
     *
     * @return stdClass
     */
    private function export_relation_summary(): stdClass {
        $summary = new stdClass();
        $summary->label = $this->string('mediarelations', 'Relations');
        $summary->count = (int)($this->options['relationcount'] ?? 0);
        $summary->hasitems = $summary->count > 0;

        return $summary;
    }

    /**
     * Version summary.
     *
     * @return stdClass
     */
    private function export_version_summary(): stdClass {
        $summary = new stdClass();
        $summary->label = $this->string('versions', 'Versions');
        $summary->count = (int)($this->options['versioncount'] ?? 0);
        $summary->hasitems = $summary->count > 0;

        return $summary;
    }

    /**
     * Export URLs.
     *
     * @return stdClass
     */
    private function export_urls(): stdClass {
        $urls = new stdClass();
        $mediaid = $this->media !== null ? (int)$this->media->id : 0;

        $urls->library = $this->url('/mod/uckkarchive/media.php', ['id' => $this->cm->id]);
        $urls->view = $this->url('/mod/uckkarchive/view.php', ['id' => $this->cm->id]);
        $urls->add = $this->url('/mod/uckkarchive/media.php', ['id' => $this->cm->id, 'action' => 'add']);

        if ($mediaid > 0) {
            $urls->edit = $this->url('/mod/uckkarchive/media.php', [
                'id' => $this->cm->id,
                'mediaid' => $mediaid,
                'action' => 'edit',
            ]);
            $urls->markers = $this->url('/mod/uckkarchive/media.php', [
                'id' => $this->cm->id,
                'mediaid' => $mediaid,
                'action' => 'advisories',
            ]);
            $urls->versions = $this->url('/mod/uckkarchive/media.php', [
                'id' => $this->cm->id,
                'mediaid' => $mediaid,
                'action' => 'versions',
            ]);
            $urls->export = $this->url('/mod/uckkarchive/export.php', [
                'id' => $this->cm->id,
                'scope' => 'media',
                'mediaid' => $mediaid,
            ]);
        }

        return $urls;
    }

    /**
     * Export capability flags already available to display.
     *
     * @return stdClass
     */
    private function export_capabilities(): stdClass {
        $capabilities = new stdClass();
        $capabilities->viewmedia = $this->has_capability('mod/uckkarchive:viewmedia', 'mod/uckkarchive:view');
        $capabilities->addmedia = $this->has_capability('mod/uckkarchive:addmedia', 'mod/uckkarchive:manage');
        $capabilities->editmedia = $this->has_capability('mod/uckkarchive:editmedia', 'mod/uckkarchive:manage');
        $capabilities->versionmedia = $this->has_capability('mod/uckkarchive:versionmedia', 'mod/uckkarchive:manage');
        $capabilities->exportmedia = $this->has_capability('mod/uckkarchive:exportmedia', 'mod/uckkarchive:export');
        $capabilities->manageadvisories = $this->has_capability('mod/uckkarchive:manageadvisories', 'mod/uckkarchive:manage');
        $capabilities->viewadvisories = $this->has_capability('mod/uckkarchive:viewadvisories', 'mod/uckkarchive:view');

        return $capabilities;
    }

    /**
     * Export template strings.
     *
     * @return stdClass
     */
    private function export_strings(): stdClass {
        $strings = new stdClass();

        foreach ([
            'medialibraryeditor',
            'medialibraryeditor_desc',
            'medialibrary',
            'backtomedialibrary',
            'mediaeditorpreview',
            'mediaeditorworkflow',
            'mediaeditorgovernance',
            'mediaeditoractions',
            'mediaeditorform',
            'passagemarkers',
            'contentadvisories',
            'mediarelations',
            'versions',
            'provenance',
            'validation',
            'export',
            'addmedia',
            'edit',
            'view',
        ] as $key) {
            $strings->{$key} = $this->string($key, ucfirst(str_replace('_', ' ', $key)));
        }

        return $strings;
    }

    /**
     * Find a component string with fallback.
     *
     * @param string $identifier String identifier.
     * @param string $fallback Fallback.
     * @return string
     */
    private function string(string $identifier, string $fallback): string {
        foreach (['mod_uckkarchive', 'uckkarchive'] as $component) {
            if (get_string_manager()->string_exists($identifier, $component)) {
                return get_string($identifier, $component);
            }
        }

        return $fallback;
    }

    /**
     * Status label.
     *
     * @param string $status Status key.
     * @return string
     */
    private function status_label(string $status): string {
        if (get_string_manager()->string_exists('status:' . $status, 'uckkarchive')) {
            return get_string('status:' . $status, 'uckkarchive');
        }

        return $this->string('status_' . $status, $status);
    }

    /**
     * Visibility label.
     *
     * @param string $visibility Visibility key.
     * @return string
     */
    private function visibility_label(string $visibility): string {
        if (get_string_manager()->string_exists('visibility:' . $visibility, 'uckkarchive')) {
            return get_string('visibility:' . $visibility, 'uckkarchive');
        }

        return $this->string('visibility_' . $visibility, $visibility);
    }

    /**
     * Audience suitability label.
     *
     * @param string $audience Audience key.
     * @return string
     */
    private function audience_label(string $audience): string {
        if (get_string_manager()->string_exists('audience:' . $audience, 'uckkarchive')) {
            return get_string('audience:' . $audience, 'uckkarchive');
        }

        if (get_string_manager()->string_exists('audiencesuitability:' . $audience, 'uckkarchive')) {
            return get_string('audiencesuitability:' . $audience, 'uckkarchive');
        }

        return $this->string('audiencesuitability_' . $audience, $audience);
    }

    /**
     * Capability check with optional fallback.
     *
     * @param string $capability Main capability.
     * @param string|null $fallback Optional fallback capability.
     * @return bool
     */
    private function has_capability(string $capability, ?string $fallback = null): bool {
        if ($this->capability_exists($capability)) {
            return has_capability($capability, $this->context);
        }

        if ($fallback !== null && $this->capability_exists($fallback)) {
            return has_capability($fallback, $this->context);
        }

        return false;
    }

    /**
     * Check whether a capability is installed.
     *
     * @param string $capability Capability name.
     * @return bool
     */
    private function capability_exists(string $capability): bool {
        global $DB;

        static $cache = [];

        if (array_key_exists($capability, $cache)) {
            return $cache[$capability];
        }

        if (function_exists('get_capability_info')) {
            $cache[$capability] = (bool)get_capability_info($capability);
            return $cache[$capability];
        }

        $cache[$capability] = $DB->record_exists('capabilities', ['name' => $capability]);

        return $cache[$capability];
    }

    /**
     * URL helper.
     *
     * @param string $path Moodle path.
     * @param array<string,mixed> $params Parameters.
     * @return string
     */
    private function url(string $path, array $params = []): string {
        return (new moodle_url($path, $params))->out(false);
    }

    /**
     * CSS helper.
     *
     * @param string $prefix Prefix.
     * @param string $value Value.
     * @return string
     */
    private function css_class(string $prefix, string $value): string {
        return $prefix . '-' . str_replace('_', '-', $this->normalise_key($value));
    }

    /**
     * Normalise machine key.
     *
     * @param string $value Raw value.
     * @return string
     */
    private function normalise_key(string $value): string {
        return clean_param(strtolower(trim($value)), PARAM_ALPHANUMEXT);
    }

    /**
     * Normalise notification type.
     *
     * @param string $type Notification type.
     * @return string
     */
    private function normalise_notification_type(string $type): string {
        $type = $this->normalise_key($type);

        return in_array($type, ['info', 'success', 'warning', 'danger'], true) ? $type : 'info';
    }

    /**
     * Restricted summary.
     *
     * @param string $visibility Visibility.
     * @param string $status Status.
     * @param string $audience Audience suitability.
     * @param stdClass $item Raw media record.
     * @return bool
     */
    private function is_restricted(string $visibility, string $status, string $audience, stdClass $item): bool {
        return in_array($visibility, ['private', 'restricted', 'restricted_integrity', 'restricted_cultural'], true)
            || in_array($audience, ['restricted', 'restricted_integrity', 'restricted_cultural', 'staff_only'], true)
            || $status === 'restricted'
            || !empty($item->restricted);
    }
}
