<?php
// This file is part of Moodle - https://moodle.org/.
//
// Moodle is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// any later version.

/**
 * Media library renderable for UCKK Archive.
 *
 * @package    mod_uckkarchive
 * @copyright  2026 UCKK
 * @license    http://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later
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
 * Media library renderable.
 *
 * This class prepares display data only. It does not decide access policy,
 * modify media, expose files directly, or bypass Moodle capability checks.
 */
final class media_library implements renderable, templatable {
    /** @var context_module Module context. */
    private context_module $context;

    /** @var stdClass Course record. */
    private stdClass $course;

    /** @var stdClass Course module record. */
    private stdClass $cm;

    /** @var stdClass Archive instance record. */
    private stdClass $archive;

    /** @var array<int, mixed> Media records or preformatted media card data. */
    private array $media;

    /** @var array<int, mixed> Collection records or preformatted collection card data. */
    private array $collections;

    /** @var array<string, mixed> Active filters. */
    private array $filters;

    /** @var int Total matching media count. */
    private int $totalcount;

    /** @var int Current page number. */
    private int $page;

    /** @var int Items per page. */
    private int $perpage;

    /** @var string Optional notification message. */
    private string $notification;

    /** @var string Optional notification type. */
    private string $notificationtype;

    /** @var array<string, mixed> Additional rendering options. */
    private array $options;

    /**
     * Constructor.
     *
     * @param context_module $context Module context.
     * @param stdClass $course Course record.
     * @param stdClass $cm Course module record.
     * @param stdClass $archive Archive instance record.
     * @param array<int, mixed> $media Media records or preformatted media cards.
     * @param array<int, mixed> $collections Collection records or preformatted collection cards.
     * @param array<string, mixed> $filters Active filters.
     * @param int $totalcount Total media count.
     * @param int $page Current page.
     * @param int $perpage Per page.
     * @param string $notification Optional notification message.
     * @param string $notificationtype Optional notification type.
     * @param array<string, mixed> $options Additional rendering options.
     */
    public function __construct(
        context_module $context,
        stdClass $course,
        stdClass $cm,
        stdClass $archive,
        array $media = [],
        array $collections = [],
        array $filters = [],
        int $totalcount = 0,
        int $page = 0,
        int $perpage = 24,
        string $notification = '',
        string $notificationtype = 'info',
        array $options = []
    ) {
        $this->context = $context;
        $this->course = $course;
        $this->cm = $cm;
        $this->archive = $archive;
        $this->media = $media;
        $this->collections = $collections;
        $this->filters = $filters;
        $this->totalcount = max(0, $totalcount);
        $this->page = max(0, $page);
        $this->perpage = max(1, $perpage);
        $this->notification = $notification;
        $this->notificationtype = $this->normalise_notification_type($notificationtype);
        $this->options = $options;
    }

    /**
     * Export data for Mustache template.
     *
     * @param renderer_base $output Renderer.
     * @return stdClass Template data.
     */
    public function export_for_template(renderer_base $output): stdClass {
        $data = new stdClass();

        $data->archive = $this->export_archive();
        $data->course = $this->export_course();
        $data->cmid = (int)$this->cm->id;
        $data->archiveid = (int)$this->archive->id;
        $data->contextid = (int)$this->context->id;

        $data->media = array_values(array_map([$this, 'export_media_item'], $this->media));
        $data->collections = array_values(array_map([$this, 'export_collection_item'], $this->collections));

        $data->hasmedia = !empty($data->media);
        $data->hascollections = !empty($data->collections);
        $data->mediahasresults = $data->hasmedia;
        $data->collectionshasresults = $data->hascollections;

        $data->mediacount = count($data->media);
        $data->collectioncount = count($data->collections);
        $data->totalcount = $this->totalcount;

        $data->emptymessage = $this->get_component_string('nomediafound', 'No media found');
        $data->emptycollectionmessage = $this->get_component_string('nomediacollectionsfound', 'No media collections found');

        $data->filters = $this->export_filters();
        $data->filteroptions = $this->export_filter_options();

        $data->paging = $this->export_paging();
        $data->capabilities = $this->export_capabilities();
        $data->urls = $this->export_urls();

        $data->notification = $this->notification;
        $data->notificationtype = $this->notificationtype;
        $data->hasnotification = trim($this->notification) !== '';

        $data->strings = $this->export_strings();
        $data->actions = $this->export_actions();
        $data->hasactions = !empty($data->actions);

        $data->showcollections = !empty($this->options['showcollections']) || $data->hascollections;
        $data->showfilters = !array_key_exists('showfilters', $this->options) || !empty($this->options['showfilters']);
        $data->showpaging = !array_key_exists('showpaging', $this->options) || !empty($this->options['showpaging']);
        $data->showintro = !array_key_exists('showintro', $this->options) || !empty($this->options['showintro']);

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
        $archive->intro = format_module_intro('uckkarchive', $this->archive, $this->cm->id);
        $archive->hasintro = trim(strip_tags($archive->intro)) !== '';
        $archive->status = (string)($this->archive->status ?? 'active');
        $archive->visibility = (string)($this->archive->visibility ?? 'course');

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
     * Export one media item.
     *
     * @param mixed $item Media record or array.
     * @return stdClass
     */
    private function export_media_item($item): stdClass {
        $item = (object)$item;
        $metadata = $this->extract_metadata($item);

        $media = new stdClass();
        $media->id = (int)($item->id ?? $item->mediaid ?? 0);
        $media->uuid = (string)($item->uuid ?? '');
        $media->archiveid = (int)($item->archiveid ?? $this->archive->id);
        $media->cmid = (int)$this->cm->id;
        $media->contextid = (int)$this->context->id;

        $title = (string)($item->title ?? $item->name ?? '');
        $media->title = format_string($title !== '' ? $title : $this->get_component_string('untitledmedia', 'Untitled media'), true, [
            'context' => $this->context,
        ]);

        $media->description = format_text(
            (string)($item->description ?? $item->summary ?? ''),
            FORMAT_HTML,
            ['context' => $this->context, 'para' => false]
        );
        $media->hasdescription = trim(strip_tags($media->description)) !== '';

        $media->mediatype = $this->normalise_key((string)($item->mediatype ?? $item->type ?? 'other'));
        $media->mediatypelabel = $this->get_media_type_label($media->mediatype);
        $media->mediatypeclass = $this->css_class('media-type', $media->mediatype);

        $media->sourcetype = $this->normalise_key($this->first_value($item, $metadata, [
            'sourcetype',
            'source',
            'source_type',
        ], ''));
        $media->sourcetypelabel = $media->sourcetype !== ''
            ? $this->get_source_type_label($media->sourcetype)
            : '';
        $media->hassourcetype = $media->sourcetype !== '';
        $media->sourcetypeclass = $media->sourcetype !== ''
            ? $this->css_class('source-type', $media->sourcetype)
            : '';

        $media->sourceownership = $this->normalise_key($this->first_value($item, $metadata, [
            'sourceownership',
            'source_ownership',
            'ownership',
        ], ''));
        $media->sourceownershiplabel = $media->sourceownership !== ''
            ? $this->get_source_ownership_label($media->sourceownership)
            : '';
        $media->hassourceownership = $media->sourceownership !== '';

        $media->sourceurl = $this->clean_external_url($this->extract_source_url($item, $metadata));
        $media->externalurl = $media->sourceurl;
        $media->hasexternalurl = $media->externalurl !== '';
        $media->isexternalreference = $this->is_external_source_type($media->sourcetype)
            || in_array($media->mediatype, ['external', 'external_reference'], true)
            || $media->hasexternalurl;
        $media->externalreferencelabel = $this->get_component_string('externalreference', 'External reference');
        $media->openexternallabel = $this->get_component_string('openexternal', 'Open external reference');

        $media->status = $this->normalise_key((string)($item->status ?? 'draft'));
        $media->statuslabel = $this->get_status_label($media->status);
        $media->statusclass = $this->css_class('status', $media->status);

        $media->visibility = $this->normalise_key((string)($item->visibility ?? 'restricted'));
        $media->visibilitylabel = $this->get_visibility_label($media->visibility);
        $media->visibilityclass = $this->css_class('visibility', $media->visibility);

        $media->audiencesuitability = $this->normalise_key(
            (string)($item->audiencesuitability ?? $item->audience ?? 'guided')
        );
        $media->audiencesuitabilitylabel = $this->get_audience_suitability_label($media->audiencesuitability);
        $media->audiencesuitabilityclass = $this->css_class('audience-suitability', $media->audiencesuitability);

        $media->mimetype = (string)($item->mimetype ?? '');
        $media->hasmimetype = $media->mimetype !== '';

        $media->filename = (string)($item->filename ?? '');
        $media->hasfilename = $media->filename !== '';

        $media->filesize = (int)($item->filesize ?? 0);
        $media->filesizeformatted = $media->filesize > 0 ? display_size($media->filesize) : '';
        $media->hasfilesize = $media->filesize > 0;

        $media->haslocalfile = $media->hasfilename
            || $media->hasfilesize
            || $media->hasmimetype
            || !empty($item->fileid)
            || !empty($item->storedfileid);

        $media->isrestricted = $this->is_restricted_visibility($media->visibility)
            || $media->status === 'restricted'
            || $media->audiencesuitability === 'restricted'
            || $media->audiencesuitability === 'staff_only'
            || !empty($item->restricted)
            || !empty($item->isrestricted);

        $media->isculturallyrestricted = $media->visibility === 'restricted_cultural'
            || $media->audiencesuitability === 'restricted_cultural'
            || !empty($item->culturalprotocol)
            || !empty($item->isculturallyrestricted);

        $media->isintegrityrestricted = $media->visibility === 'restricted_integrity'
            || $media->audiencesuitability === 'restricted_integrity'
            || !empty($item->integrityrestricted)
            || !empty($item->isintegrityrestricted);

        $media->timecreated = (int)($item->timecreated ?? 0);
        $media->timemodified = (int)($item->timemodified ?? 0);
        $media->timecreatedformatted = $media->timecreated > 0 ? userdate($media->timecreated) : '';
        $media->timemodifiedformatted = $media->timemodified > 0 ? userdate($media->timemodified) : '';

        $media->thumbnailurl = (string)($item->thumbnailurl ?? $item->thumburl ?? '');
        $media->hasthumbnail = $media->thumbnailurl !== '';

        $media->previewurl = (string)($item->previewurl ?? '');
        $media->haspreview = $media->previewurl !== '';

        $media->contentadvisorycount = (int)($item->contentadvisorycount ?? $item->contentmarkercount ?? 0);
        $media->hascontentadvisories = $media->contentadvisorycount > 0;

        $media->collectioncount = (int)($item->collectioncount ?? $item->mediacollectioncount ?? 0);
        $media->hascollections = $media->collectioncount > 0;

        $media->versioncount = (int)($item->versioncount ?? 0);
        $media->hasversions = $media->versioncount > 0;

        $media->relationcount = (int)($item->relationcount ?? 0);
        $media->hasrelations = $media->relationcount > 0;

        $media->tagcount = (int)($item->tagcount ?? 0);
        $media->hastags = $media->tagcount > 0;

        $media->url = $this->url('/mod/uckkarchive/media.php', [
            'id' => $this->cm->id,
            'mediaid' => $media->id,
            'action' => 'view',
        ]);

        $media->editurl = $this->url('/mod/uckkarchive/media.php', [
            'id' => $this->cm->id,
            'mediaid' => $media->id,
            'action' => 'edit',
        ]);

        $media->deleteurl = $this->url('/mod/uckkarchive/media.php', [
            'id' => $this->cm->id,
            'mediaid' => $media->id,
            'action' => 'delete',
        ]);

        $media->downloadurl = $this->url('/mod/uckkarchive/media.php', [
            'id' => $this->cm->id,
            'mediaid' => $media->id,
            'action' => 'download',
        ]);

        $media->versionurl = $this->url('/mod/uckkarchive/media.php', [
            'id' => $this->cm->id,
            'mediaid' => $media->id,
            'action' => 'versions',
        ]);

        $media->advisoryurl = $this->url('/mod/uckkarchive/media.php', [
            'id' => $this->cm->id,
            'mediaid' => $media->id,
            'action' => 'advisories',
        ]);

        $media->exporturl = $this->url('/mod/uckkarchive/export.php', [
            'id' => $this->cm->id,
            'scope' => 'media',
            'mediaid' => $media->id,
        ]);

        $media->canview = $this->has_capability('mod/uckkarchive:viewmedia', 'mod/uckkarchive:view');
        $media->canedit = $this->has_capability('mod/uckkarchive:editmedia', 'mod/uckkarchive:manage');
        $media->candelete = $this->has_capability('mod/uckkarchive:deletemedia', 'mod/uckkarchive:manage');
        $media->candownload = $media->haslocalfile
            && $this->has_capability('mod/uckkarchive:downloadmedia', 'mod/uckkarchive:viewmedia');
        $media->canversion = $this->has_capability('mod/uckkarchive:versionmedia', 'mod/uckkarchive:manage');
        $media->canexport = $this->has_capability('mod/uckkarchive:exportmedia', 'mod/uckkarchive:export');
        $media->canmanageadvisories = $this->has_capability('mod/uckkarchive:manageadvisories', 'mod/uckkarchive:manage');
        $media->canopenexternal = $media->canview && $media->hasexternalurl;

        $media->actions = $this->export_media_actions($media);
        $media->hasactions = !empty($media->actions);

        return $media;
    }

    /**
     * Export one collection item.
     *
     * @param mixed $item Collection record or array.
     * @return stdClass
     */
    private function export_collection_item($item): stdClass {
        $item = (object)$item;

        $collection = new stdClass();
        $collection->id = (int)($item->id ?? $item->collectionid ?? 0);
        $collection->uuid = (string)($item->uuid ?? '');
        $collection->archiveid = (int)($item->archiveid ?? $this->archive->id);
        $collection->cmid = (int)$this->cm->id;
        $collection->contextid = (int)$this->context->id;

        $title = (string)($item->title ?? $item->name ?? '');
        $collection->title = format_string($title !== '' ? $title : $this->get_component_string('untitledcollection', 'Untitled collection'), true, [
            'context' => $this->context,
        ]);

        $collection->description = format_text(
            (string)($item->description ?? $item->summary ?? ''),
            FORMAT_HTML,
            ['context' => $this->context, 'para' => false]
        );
        $collection->hasdescription = trim(strip_tags($collection->description)) !== '';

        $collection->purpose = (string)($item->purpose ?? '');
        $collection->haspurpose = $collection->purpose !== '';

        $collection->status = $this->normalise_key((string)($item->status ?? 'draft'));
        $collection->statuslabel = $this->get_status_label($collection->status);
        $collection->statusclass = $this->css_class('status', $collection->status);

        $collection->visibility = $this->normalise_key((string)($item->visibility ?? 'restricted'));
        $collection->visibilitylabel = $this->get_visibility_label($collection->visibility);
        $collection->visibilityclass = $this->css_class('visibility', $collection->visibility);

        $collection->isrestricted = $this->is_restricted_visibility($collection->visibility)
            || $collection->status === 'restricted'
            || !empty($item->restricted)
            || !empty($item->isrestricted);

        $collection->mediacount = (int)($item->mediacount ?? $item->countmedia ?? $item->itemcount ?? 0);
        $collection->hasmedia = $collection->mediacount > 0;

        $collection->timecreated = (int)($item->timecreated ?? 0);
        $collection->timemodified = (int)($item->timemodified ?? 0);
        $collection->timecreatedformatted = $collection->timecreated > 0 ? userdate($collection->timecreated) : '';
        $collection->timemodifiedformatted = $collection->timemodified > 0 ? userdate($collection->timemodified) : '';

        $collection->url = $this->url('/mod/uckkarchive/media.php', [
            'id' => $this->cm->id,
            'collectionid' => $collection->id,
        ]);

        $collection->editurl = $this->url('/mod/uckkarchive/media.php', [
            'id' => $this->cm->id,
            'collectionid' => $collection->id,
            'action' => 'editcollection',
        ]);

        $collection->deleteurl = $this->url('/mod/uckkarchive/media.php', [
            'id' => $this->cm->id,
            'collectionid' => $collection->id,
            'action' => 'deletecollection',
        ]);

        $collection->exporturl = $this->url('/mod/uckkarchive/export.php', [
            'id' => $this->cm->id,
            'scope' => 'collection',
            'collectionid' => $collection->id,
        ]);

        $collection->canview = $this->has_capability('mod/uckkarchive:viewmedia', 'mod/uckkarchive:view');
        $collection->canmanage = $this->has_capability('mod/uckkarchive:managemediacollections', 'mod/uckkarchive:manage');
        $collection->canedit = $collection->canmanage;
        $collection->candelete = $collection->canmanage;
        $collection->canexport = $this->has_capability('mod/uckkarchive:exportmedia', 'mod/uckkarchive:export');

        $collection->actions = $this->export_collection_actions($collection);
        $collection->hasactions = !empty($collection->actions);

        return $collection;
    }

    /**
     * Export active filters.
     *
     * @return stdClass
     */
    private function export_filters(): stdClass {
        $filters = new stdClass();
        $filters->search = clean_param((string)($this->filters['search'] ?? $this->filters['q'] ?? ''), PARAM_TEXT);
        $filters->mediatype = $this->normalise_key((string)($this->filters['mediatype'] ?? ''));
        $filters->sourcetype = $this->normalise_key((string)($this->filters['sourcetype'] ?? ''));
        $filters->sourceownership = $this->normalise_key((string)($this->filters['sourceownership'] ?? ''));
        $filters->status = $this->normalise_key((string)($this->filters['status'] ?? ''));
        $filters->visibility = $this->normalise_key((string)($this->filters['visibility'] ?? ''));
        $filters->audiencesuitability = $this->normalise_key((string)($this->filters['audiencesuitability'] ?? ''));
        $filters->collectionid = (int)($this->filters['collectionid'] ?? 0);
        $filters->tag = $this->normalise_key((string)($this->filters['tag'] ?? ''));
        $filters->hasadvisories = !empty($this->filters['hasadvisories']);
        $filters->hasactivefilters = $filters->search !== ''
            || $filters->mediatype !== ''
            || $filters->sourcetype !== ''
            || $filters->sourceownership !== ''
            || $filters->status !== ''
            || $filters->visibility !== ''
            || $filters->audiencesuitability !== ''
            || $filters->collectionid > 0
            || $filters->tag !== ''
            || $filters->hasadvisories;

        return $filters;
    }

    /**
     * Export filter option lists.
     *
     * @return stdClass
     */
    private function export_filter_options(): stdClass {
        $options = new stdClass();
        $filters = $this->export_filters();

        $options->mediatypes = $this->build_options([
            'image',
            'video',
            'audio',
            'document',
            'text',
            'dataset',
            'external_reference',
            'external',
            'other',
        ], $filters->mediatype, 'get_media_type_label');

        $options->sourcetypes = $this->build_options([
            'produced_by_uckk',
            'submitted_to_uckk',
            'imported',
            'external_reference_only',
            'licensed_external',
            'public_domain',
            'fair_use_reference',
            'restricted_reference',
        ], $filters->sourcetype, 'get_source_type_label');

        $options->sourceownerships = $this->build_options([
            'uckk',
            'student',
            'teacher',
            'partner',
            'external',
            'unknown',
        ], $filters->sourceownership, 'get_source_ownership_label');

        $options->statuses = $this->build_options([
            'draft',
            'submitted',
            'active',
            'restricted',
            'superseded',
            'archived',
            'deleted_soft',
        ], $filters->status, 'get_status_label');

        $options->visibilities = $this->build_options([
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
        ], $filters->visibility, 'get_visibility_label');

        $options->audiencesuitabilities = $this->build_options([
            'general',
            'guided',
            'mature',
            'restricted',
            'restricted_cultural',
            'restricted_integrity',
            'staff_only',
            'not_for_children',
            'review_required',
            'unknown',
        ], $filters->audiencesuitability, 'get_audience_suitability_label');

        return $options;
    }

    /**
     * Export paging data.
     *
     * @return stdClass
     */
    private function export_paging(): stdClass {
        $paging = new stdClass();
        $paging->totalcount = $this->totalcount;
        $paging->page = $this->page;
        $paging->displaypage = $this->page + 1;
        $paging->perpage = $this->perpage;
        $paging->pagecount = $this->totalcount > 0 ? (int)ceil($this->totalcount / $this->perpage) : 1;
        $paging->haspaging = $paging->pagecount > 1;
        $paging->hasprevious = $this->page > 0;
        $paging->hasnext = ($this->page + 1) < $paging->pagecount;
        $paging->previouspage = max(0, $this->page - 1);
        $paging->nextpage = $this->page + 1;

        $params = [
            'id' => $this->cm->id,
        ];

        foreach ($this->filters as $key => $value) {
            if ($value !== '' && $value !== null && $value !== 0 && $value !== false) {
                $params[clean_param((string)$key, PARAM_ALPHANUMEXT)] = $value;
            }
        }

        $previousparams = $params + ['page' => $paging->previouspage, 'perpage' => $this->perpage];
        $nextparams = $params + ['page' => $paging->nextpage, 'perpage' => $this->perpage];

        $paging->previousurl = $this->url('/mod/uckkarchive/media.php', $previousparams);
        $paging->nexturl = $this->url('/mod/uckkarchive/media.php', $nextparams);

        return $paging;
    }

    /**
     * Export current user capabilities.
     *
     * @return stdClass
     */
    private function export_capabilities(): stdClass {
        $capabilities = new stdClass();

        $capabilities->viewmedia = $this->has_capability('mod/uckkarchive:viewmedia', 'mod/uckkarchive:view');
        $capabilities->addmedia = $this->has_capability('mod/uckkarchive:addmedia', 'mod/uckkarchive:manage');
        $capabilities->editmedia = $this->has_capability('mod/uckkarchive:editmedia', 'mod/uckkarchive:manage');
        $capabilities->deletemedia = $this->has_capability('mod/uckkarchive:deletemedia', 'mod/uckkarchive:manage');
        $capabilities->downloadmedia = $this->has_capability('mod/uckkarchive:downloadmedia', 'mod/uckkarchive:viewmedia');
        $capabilities->versionmedia = $this->has_capability('mod/uckkarchive:versionmedia', 'mod/uckkarchive:manage');
        $capabilities->managemediacollections = $this->has_capability(
            'mod/uckkarchive:managemediacollections',
            'mod/uckkarchive:manage'
        );
        $capabilities->exportmedia = $this->has_capability('mod/uckkarchive:exportmedia', 'mod/uckkarchive:export');
        $capabilities->viewrestrictedmedia = $this->has_capability(
            'mod/uckkarchive:viewrestrictedmedia',
            'mod/uckkarchive:viewrestricted'
        );
        $capabilities->viewadvisories = $this->has_capability('mod/uckkarchive:viewadvisories', 'mod/uckkarchive:view');
        $capabilities->manageadvisories = $this->has_capability('mod/uckkarchive:manageadvisories', 'mod/uckkarchive:manage');
        $capabilities->reviewadvisories = $this->has_capability('mod/uckkarchive:reviewadvisories', 'mod/uckkarchive:manage');
        $capabilities->viewculturallyrestricted = $this->has_capability(
            'mod/uckkarchive:viewculturallyrestricted',
            'mod/uckkarchive:viewrestricted'
        );
        $capabilities->manageexternalworks = $this->has_capability(
            'mod/uckkarchive:manageexternalworks',
            'mod/uckkarchive:manage'
        );

        return $capabilities;
    }

    /**
     * Export useful URLs.
     *
     * @return stdClass
     */
    private function export_urls(): stdClass {
        $urls = new stdClass();

        $urls->view = $this->url('/mod/uckkarchive/view.php', [
            'id' => $this->cm->id,
        ]);

        $urls->media = $this->url('/mod/uckkarchive/media.php', [
            'id' => $this->cm->id,
        ]);

        $urls->addmedia = $this->url('/mod/uckkarchive/media.php', [
            'id' => $this->cm->id,
            'action' => 'add',
        ]);

        $urls->addcollection = $this->url('/mod/uckkarchive/media.php', [
            'id' => $this->cm->id,
            'action' => 'addcollection',
        ]);

        $urls->externalworks = $this->url('/mod/uckkarchive/media.php', [
            'id' => $this->cm->id,
            'tab' => 'externalworks',
        ]);

        $urls->contentadvisories = $this->url('/mod/uckkarchive/media.php', [
            'id' => $this->cm->id,
            'tab' => 'advisories',
        ]);

        $urls->exportmedia = $this->url('/mod/uckkarchive/export.php', [
            'id' => $this->cm->id,
            'scope' => 'media',
        ]);

        $urls->clearfilters = $this->url('/mod/uckkarchive/media.php', [
            'id' => $this->cm->id,
        ]);

        return $urls;
    }

    /**
     * Export page-level action list.
     *
     * @return array<int, stdClass>
     */
    private function export_actions(): array {
        $actions = [];

        if ($this->has_capability('mod/uckkarchive:addmedia', 'mod/uckkarchive:manage')) {
            $actions[] = $this->action(
                'addmedia',
                $this->get_component_string('addmedia', 'Add media'),
                $this->url('/mod/uckkarchive/media.php', ['id' => $this->cm->id, 'action' => 'add']),
                true
            );
        }

        if ($this->has_capability('mod/uckkarchive:managemediacollections', 'mod/uckkarchive:manage')) {
            $actions[] = $this->action(
                'addcollection',
                $this->get_component_string('addcollection', 'Add collection'),
                $this->url('/mod/uckkarchive/media.php', ['id' => $this->cm->id, 'action' => 'addcollection'])
            );
        }

        if ($this->has_capability('mod/uckkarchive:exportmedia', 'mod/uckkarchive:export')) {
            $actions[] = $this->action(
                'exportmedia',
                $this->get_component_string('exportmedia', 'Export media'),
                $this->url('/mod/uckkarchive/export.php', ['id' => $this->cm->id, 'scope' => 'media'])
            );
        }

        return $actions;
    }

    /**
     * Export media action list.
     *
     * @param stdClass $media Media data.
     * @return array<int, stdClass>
     */
    private function export_media_actions(stdClass $media): array {
        $actions = [];

        if ($media->canview) {
            $actions[] = $this->action('view', $this->get_component_string('view', 'View'), $media->url);
        }

        if ($media->canopenexternal) {
            $actions[] = $this->action(
                'openexternal',
                $media->openexternallabel,
                $media->externalurl,
                false,
                true
            );
        }

        if ($media->canedit) {
            $actions[] = $this->action('edit', $this->get_component_string('edit', 'Edit'), $media->editurl);
        }

        if ($media->candownload) {
            $actions[] = $this->action('download', $this->get_component_string('download', 'Download'), $media->downloadurl);
        }

        if ($media->canversion) {
            $actions[] = $this->action('versions', $this->get_component_string('versions', 'Versions'), $media->versionurl);
        }

        if ($media->canexport) {
            $actions[] = $this->action('export', $this->get_component_string('export', 'Export'), $media->exporturl);
        }

        return $actions;
    }

    /**
     * Export collection action list.
     *
     * @param stdClass $collection Collection data.
     * @return array<int, stdClass>
     */
    private function export_collection_actions(stdClass $collection): array {
        $actions = [];

        if ($collection->canview) {
            $actions[] = $this->action('view', $this->get_component_string('view', 'View'), $collection->url);
        }

        if ($collection->canmanage) {
            $actions[] = $this->action('edit', $this->get_component_string('edit', 'Edit'), $collection->editurl);
        }

        if ($collection->canexport) {
            $actions[] = $this->action('export', $this->get_component_string('export', 'Export'), $collection->exporturl);
        }

        return $actions;
    }

    /**
     * Build action object.
     *
     * @param string $key Action key.
     * @param string $label Label.
     * @param string $url URL.
     * @param bool $primary Primary action.
     * @param bool $external External action.
     * @return stdClass
     */
    private function action(string $key, string $label, string $url, bool $primary = false, bool $external = false): stdClass {
        $action = new stdClass();
        $action->key = $key;
        $action->label = $label;
        $action->url = $url;
        $action->primary = $primary;
        $action->external = $external;
        $action->class = $this->css_class('action', $key);
        $action->disabled = false;
        $action->target = $external ? '_blank' : '';
        $action->rel = $external ? 'noopener noreferrer' : '';

        return $action;
    }

    /**
     * Export strings used by the template.
     *
     * @return stdClass
     */
    private function export_strings(): stdClass {
        $strings = new stdClass();

        $stringkeys = [
            'medialibrary',
            'media',
            'addmedia',
            'addcollection',
            'exportmedia',
            'search',
            'filter',
            'clearfilters',
            'mediatype',
            'sourcetype',
            'sourceownership',
            'externalreference',
            'externalurl',
            'openexternal',
            'status',
            'visibility',
            'audiencesuitability',
            'collections',
            'contentadvisories',
            'restricted',
            'culturallyrestricted',
            'integrityrestricted',
            'edit',
            'delete',
            'download',
            'view',
            'versions',
            'export',
            'previous',
            'next',
            'results',
            'nomediafound',
            'nomediacollectionsfound',
        ];

        foreach ($stringkeys as $key) {
            $strings->{$key} = $this->get_component_string($key, ucfirst(str_replace('_', ' ', $key)));
        }

        return $strings;
    }

    /**
     * Build Mustache option list.
     *
     * @param string[] $values Option values.
     * @param string $selected Current value.
     * @param string $labelmethod Label method.
     * @return array<int, stdClass>
     */
    private function build_options(array $values, string $selected, string $labelmethod): array {
        $options = [];

        foreach ($values as $value) {
            $option = new stdClass();
            $option->value = $value;
            $option->label = $this->{$labelmethod}($value);
            $option->selected = $value === $selected;
            $options[] = $option;
        }

        return $options;
    }

    /**
     * Get media type label.
     *
     * @param string $type Media type.
     * @return string
     */
    private function get_media_type_label(string $type): string {
        return $this->get_component_string('mediatype_' . $type, $type);
    }

    /**
     * Get source type label.
     *
     * @param string $type Source type.
     * @return string
     */
    private function get_source_type_label(string $type): string {
        return $this->get_component_string('sourcetype_' . $type, $type);
    }

    /**
     * Get source ownership label.
     *
     * @param string $ownership Source ownership.
     * @return string
     */
    private function get_source_ownership_label(string $ownership): string {
        return $this->get_component_string('sourceownership_' . $ownership, $ownership);
    }

    /**
     * Get status label.
     *
     * @param string $status Status.
     * @return string
     */
    private function get_status_label(string $status): string {
        return $this->get_component_string('status_' . $status, $status);
    }

    /**
     * Get visibility label.
     *
     * @param string $visibility Visibility.
     * @return string
     */
    private function get_visibility_label(string $visibility): string {
        return $this->get_component_string('visibility_' . $visibility, $visibility);
    }

    /**
     * Get audience suitability label.
     *
     * @param string $suitability Audience suitability.
     * @return string
     */
    private function get_audience_suitability_label(string $suitability): string {
        return $this->get_component_string('audiencesuitability_' . $suitability, $suitability);
    }

    /**
     * Return component string or readable fallback.
     *
     * @param string $identifier String identifier.
     * @param string $fallback Fallback value.
     * @return string
     */
    private function get_component_string(string $identifier, string $fallback): string {
        $components = [
            'mod_uckkarchive',
            'uckkarchive',
        ];

        foreach ($components as $component) {
            if (get_string_manager()->string_exists($identifier, $component)) {
                return get_string($identifier, $component);
            }
        }

        return ucfirst(str_replace('_', ' ', $fallback));
    }

    /**
     * Return whether current user has a capability.
     *
     * If the new capability has not yet been installed, an optional fallback is
     * used so this renderable can still run during staged development.
     *
     * @param string $capability Capability.
     * @param string|null $fallback Fallback capability.
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
     * Return whether a capability exists.
     *
     * @param string $capability Capability.
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
     * Build URL string.
     *
     * @param string $path Moodle path.
     * @param array<string, mixed> $params Params.
     * @return string
     */
    private function url(string $path, array $params = []): string {
        return (new moodle_url($path, $params))->out(false);
    }

    /**
     * Return CSS class.
     *
     * @param string $prefix Prefix.
     * @param string $value Value.
     * @return string
     */
    private function css_class(string $prefix, string $value): string {
        $value = str_replace('_', '-', $this->normalise_key($value));

        return $prefix . '-' . $value;
    }

    /**
     * Normalise machine key.
     *
     * @param string $value Value.
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
        $type = clean_param($type, PARAM_ALPHANUMEXT);

        if (!in_array($type, ['info', 'success', 'warning', 'danger'], true)) {
            return 'info';
        }

        return $type;
    }

    /**
     * Check restricted visibility.
     *
     * @param string $visibility Visibility.
     * @return bool
     */
    private function is_restricted_visibility(string $visibility): bool {
        return in_array($visibility, [
            'private',
            'restricted',
            'restricted_integrity',
            'restricted_cultural',
        ], true);
    }

    /**
     * Return whether a source type points to an external reference.
     *
     * @param string $sourcetype Source type.
     * @return bool
     */
    private function is_external_source_type(string $sourcetype): bool {
        return in_array($this->normalise_key($sourcetype), [
            'external',
            'external_reference',
            'external_reference_only',
            'licensed_external',
            'public_domain',
            'fair_use_reference',
            'restricted_reference',
        ], true);
    }

    /**
     * Extract source URL from known fields and metadata.
     *
     * @param stdClass $item Media record.
     * @param array<string,mixed> $metadata Decoded metadata.
     * @return string
     */
    private function extract_source_url(stdClass $item, array $metadata): string {
        $url = $this->first_value($item, $metadata, [
            'sourceurl',
            'externalurl',
            'referenceurl',
            'source_url',
            'external_url',
            'reference_url',
            'urlsource',
            'citationurl',
            'citation_url',
        ], '');

        if ($url !== '') {
            return $url;
        }

        foreach (['citation', 'rightsnote', 'externalworkidentifier', 'externalworknote'] as $field) {
            $text = $this->first_value($item, $metadata, [$field], '');
            $found = $this->first_url_from_text($text);

            if ($found !== '') {
                return $found;
            }
        }

        return '';
    }

    /**
     * Return the first non-empty value from record fields or metadata keys.
     *
     * @param stdClass $item Record.
     * @param array<string,mixed> $metadata Metadata.
     * @param string[] $keys Candidate keys.
     * @param string $default Default value.
     * @return string
     */
    private function first_value(stdClass $item, array $metadata, array $keys, string $default = ''): string {
        foreach ($keys as $key) {
            if (property_exists($item, $key) && trim((string)$item->{$key}) !== '') {
                return trim((string)$item->{$key});
            }
        }

        foreach ($keys as $key) {
            if (array_key_exists($key, $metadata) && trim((string)$metadata[$key]) !== '') {
                return trim((string)$metadata[$key]);
            }
        }

        return $default;
    }

    /**
     * Decode metadata from a media record.
     *
     * @param stdClass $item Media record.
     * @return array<string,mixed>
     */
    private function extract_metadata(stdClass $item): array {
        if (!property_exists($item, 'metadata')) {
            return [];
        }

        if (is_array($item->metadata)) {
            return $item->metadata;
        }

        if (is_object($item->metadata)) {
            return (array)$item->metadata;
        }

        if (!is_string($item->metadata) || trim($item->metadata) === '') {
            return [];
        }

        $decoded = json_decode($item->metadata, true);

        if (json_last_error() !== JSON_ERROR_NONE || !is_array($decoded)) {
            return [];
        }

        return $decoded;
    }

    /**
     * Clean an external URL for display.
     *
     * Only absolute HTTP(S) URLs are exposed as external references.
     *
     * @param string $url Raw URL.
     * @return string
     */
    private function clean_external_url(string $url): string {
        $url = trim($url);

        if ($url === '') {
            return '';
        }

        $url = clean_param($url, PARAM_URL);

        if (!preg_match('/^https?:\/\//i', $url)) {
            return '';
        }

        return $url;
    }

    /**
     * Extract the first HTTP(S) URL from free text.
     *
     * @param string $text Source text.
     * @return string
     */
    private function first_url_from_text(string $text): string {
        if ($text === '') {
            return '';
        }

        if (!preg_match('/https?:\/\/[^\s<>"\']+/i', $text, $matches)) {
            return '';
        }

        return rtrim((string)$matches[0], ".,;:)]}");
    }
}

