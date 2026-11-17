<?php
// This file is part of Moodle - https://moodle.org/
//
// Moodle is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// any later version.

/**
 * Main archive view output object.
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
 * Renderable main view for a UCKK Archive activity.
 *
 * This class prepares already-filtered display data for
 * mod_uckkarchive/archive_view.mustache.
 *
 * It must not validate archive items, revise records, decide provenance,
 * change visibility, export packages, delete evidence, or perform integrity
 * workflow decisions.
 */
final class archive_view implements renderable, templatable {
    /** Status: draft. */
    public const STATUS_DRAFT = 'draft';

    /** Status: active. */
    public const STATUS_ACTIVE = 'active';

    /** Status: hidden. */
    public const STATUS_HIDDEN = 'hidden';

    /** Status: pending review. */
    public const STATUS_PENDING_REVIEW = 'pending_review';

    /** Status: validated. */
    public const STATUS_VALIDATED = 'validated';

    /** Status: rejected. */
    public const STATUS_REJECTED = 'rejected';

    /** Status: correction required. */
    public const STATUS_CORRECTION_REQUIRED = 'correction_required';

    /** Status: contested. */
    public const STATUS_CONTESTED = 'contested';

    /** Status: invalidated. */
    public const STATUS_INVALIDATED = 'invalidated';

    /** Status: closed. */
    public const STATUS_CLOSED = 'closed';

    /** Status: archived. */
    public const STATUS_ARCHIVED = 'archived';

    /** Status: deleted. */
    public const STATUS_DELETED = 'deleted';

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

    /** Visibility: hidden. */
    public const VISIBILITY_HIDDEN = 'hidden';

    /** Visibility: archived. */
    public const VISIBILITY_ARCHIVED = 'archived';

    /** Validation state: unverified. */
    public const VALIDATION_UNVERIFIED = 'unverified';

    /** Validation state: human reviewed. */
    public const VALIDATION_HUMAN_REVIEWED = 'human_reviewed';

    /** Validation state: verified. */
    public const VALIDATION_VERIFIED = 'verified';

    /** Validation state: contested. */
    public const VALIDATION_CONTESTED = 'contested';

    /** Validation state: invalidated. */
    public const VALIDATION_INVALIDATED = 'invalidated';

    /** Validation state: archived. */
    public const VALIDATION_ARCHIVED = 'archived';

    /** Severity: notice. */
    public const SEVERITY_NOTICE = 'notice';

    /** Severity: moderate. */
    public const SEVERITY_MODERATE = 'moderate';

    /** Severity: strong. */
    public const SEVERITY_STRONG = 'strong';

    /** Severity: restricted. */
    public const SEVERITY_RESTRICTED = 'restricted';

    /** @var int Archive instance id. */
    private int $archiveid;

    /** @var int Course module id. */
    private int $cmid;

    /** @var int Course id. */
    private int $courseid;

    /** @var int Context id. */
    private int $contextid;

    /** @var string Archive title. */
    private string $title;

    /** @var string Archive intro HTML. */
    private string $introhtml;

    /** @var array<string, mixed> Prepared archive summary. */
    private array $summary;

    /** @var array<int, array<string, mixed>> Prepared archive item rows. */
    private array $items;

    /** @var array<int, array<string, mixed>> Prepared Kristal rows. */
    private array $kristals;

    /** @var array<int, array<string, mixed>> Prepared proof rows. */
    private array $proofs;

    /** @var array<int, array<string, mixed>> Prepared export rows. */
    private array $exports;

    /** @var array<int, array<string, mixed>> Prepared media rows. */
    private array $media;

    /** @var array<int, array<string, mixed>> Prepared media collection rows. */
    private array $collections;

    /** @var array<int, array<string, mixed>> Prepared external work rows. */
    private array $externalworks;

    /** @var array<int, array<string, mixed>> Prepared content marker rows. */
    private array $contentmarkers;

    /** @var array<int, array<string, mixed>> Prepared action rows. */
    private array $actions;

    /** @var stdClass|null Direct template context supplied by view.php. */
    private ?stdClass $directcontext = null;

    /**
     * Constructor.
     *
     * Direct context mode is preserved for controllers that already prepare the
     * full template payload. Structured mode accepts already-filtered rows.
     *
     * @param int|array<string, mixed>|stdClass $archiveid Archive id or direct template context.
     * @param int|null $cmid Course module id.
     * @param int|null $courseid Course id.
     * @param int|null $contextid Moodle context id.
     * @param string|null $title Archive title.
     * @param string $introhtml Already formatted intro HTML.
     * @param array<string, mixed> $summary Already-filtered summary.
     * @param array<int, array<string, mixed>|stdClass> $items Archive item rows.
     * @param array<int, array<string, mixed>|stdClass> $kristals Kristal rows.
     * @param array<int, array<string, mixed>|stdClass> $proofs Proof rows.
     * @param array<int, array<string, mixed>|stdClass> $exports Export rows.
     * @param array<int, array<string, mixed>|stdClass> $actions Permitted action rows.
     * @param array<int, array<string, mixed>|stdClass> $media Media rows.
     * @param array<int, array<string, mixed>|stdClass> $collections Media collection rows.
     * @param array<int, array<string, mixed>|stdClass> $externalworks External work rows.
     * @param array<int, array<string, mixed>|stdClass> $contentmarkers Content marker rows.
     */
    public function __construct(
        int|array|stdClass $archiveid,
        ?int $cmid = null,
        ?int $courseid = null,
        ?int $contextid = null,
        ?string $title = null,
        string $introhtml = '',
        array $summary = [],
        array $items = [],
        array $kristals = [],
        array $proofs = [],
        array $exports = [],
        array $actions = [],
        array $media = [],
        array $collections = [],
        array $externalworks = [],
        array $contentmarkers = []
    ) {
        if (is_array($archiveid) || $archiveid instanceof stdClass) {
            $this->directcontext = $this->normalise_direct_context((object)$archiveid);

            $this->archiveid = max(0, (int)($this->directcontext->archiveid ?? $this->directcontext->id ?? 0));
            $this->cmid = max(0, (int)($this->directcontext->cmid ?? 0));
            $this->courseid = max(0, (int)($this->directcontext->courseid ?? 0));
            $this->contextid = max(0, (int)($this->directcontext->contextid ?? 0));
            $this->title = format_string((string)($this->directcontext->title ?? ''));
            $this->introhtml = (string)($this->directcontext->introhtml ?? $this->directcontext->intro ?? '');
            $this->summary = (array)$this->directcontext;
            $this->items = [];
            $this->kristals = [];
            $this->proofs = [];
            $this->exports = [];
            $this->media = [];
            $this->collections = [];
            $this->externalworks = [];
            $this->contentmarkers = [];
            $this->actions = [];
            return;
        }

        $this->archiveid = max(0, $archiveid);
        $this->cmid = max(0, (int)($cmid ?? 0));
        $this->courseid = max(0, (int)($courseid ?? 0));
        $this->contextid = max(0, (int)($contextid ?? 0));
        $this->title = format_string((string)($title ?? ''));
        $this->introhtml = $introhtml;
        $this->summary = $summary;
        $this->items = array_map([$this, 'normalise_archive_item'], $items);
        $this->kristals = array_map([$this, 'normalise_kristal'], $kristals);
        $this->proofs = array_map([$this, 'normalise_proof'], $proofs);
        $this->exports = array_map([$this, 'normalise_export'], $exports);
        $this->media = array_map([$this, 'normalise_media'], $media);
        $this->collections = array_map([$this, 'normalise_collection'], $collections);
        $this->externalworks = array_map([$this, 'normalise_external_work'], $externalworks);
        $this->contentmarkers = array_map([$this, 'normalise_content_marker'], $contentmarkers);
        $this->actions = array_map([$this, 'normalise_action'], $actions);
    }

    /**
     * Normalise a direct template context supplied by view.php.
     *
     * @param stdClass $context Direct template context.
     * @return stdClass
     */
    private function normalise_direct_context(stdClass $context): stdClass {
        $data = (object)(array)$context;

        if (!isset($data->archiveid) && isset($data->id)) {
            $data->archiveid = (int)$data->id;
        }

        if (!isset($data->id) && isset($data->archiveid)) {
            $data->id = (int)$data->archiveid;
        }

        $data->cmid = (int)($data->cmid ?? 0);
        $data->courseid = (int)($data->courseid ?? 0);
        $data->contextid = (int)($data->contextid ?? 0);
        $data->title = format_string((string)($data->title ?? ''));

        if (!isset($data->heading)) {
            $data->heading = $this->get_component_string('archiveview', 'Registraire');
        }

        if (!isset($data->introhtml) && isset($data->intro)) {
            $data->introhtml = (string)$data->intro;
        }

        if (!isset($data->intro) && isset($data->introhtml)) {
            $data->intro = (string)$data->introhtml;
        }

        $intro = (string)($data->introhtml ?? $data->intro ?? '');
        if (!isset($data->hasintro)) {
            $data->hasintro = trim(strip_tags($intro)) !== '';
        }

        if (!isset($data->uniqid)) {
            $data->uniqid = 'uckkarchive-view-' . $data->cmid;
        }

        if (!isset($data->viewurl)) {
            $data->viewurl = (new moodle_url('/mod/uckkarchive/view.php', ['id' => $data->cmid]))->out(false);
        }

        if (!isset($data->additemurl)) {
            $data->additemurl = (new moodle_url('/mod/uckkarchive/add.php', ['id' => $data->cmid]))->out(false);
        }

        if (!isset($data->validateurl)) {
            $data->validateurl = (new moodle_url('/mod/uckkarchive/validate.php', ['id' => $data->cmid]))->out(false);
        }

        if (!isset($data->exporturl)) {
            $data->exporturl = (new moodle_url('/mod/uckkarchive/export.php', ['id' => $data->cmid]))->out(false);
        }

        if (!isset($data->mediaurl)) {
            $data->mediaurl = (new moodle_url('/mod/uckkarchive/media.php', ['id' => $data->cmid]))->out(false);
        }

        $listfields = [
            'items',
            'kristals',
            'proofs',
            'actions',
            'statuscounts',
            'warnings',
            'notices',
            'media',
            'collections',
            'externalworks',
            'contentmarkers',
            'advisories',
        ];

        foreach ($listfields as $field) {
            if (!isset($data->{$field}) || !is_array($data->{$field})) {
                $data->{$field} = [];
            }
        }

        $data->hasitems = (bool)($data->hasitems ?? !empty($data->items));
        $data->itemcount = (int)($data->itemcount ?? count($data->items));
        $data->haskristals = (bool)($data->haskristals ?? !empty($data->kristals));
        $data->kristalcount = (int)($data->kristalcount ?? count($data->kristals));
        $data->hasproofs = (bool)($data->hasproofs ?? !empty($data->proofs));
        $data->proofcount = (int)($data->proofcount ?? count($data->proofs));
        $data->hasmedia = (bool)($data->hasmedia ?? !empty($data->media));
        $data->mediacount = (int)($data->mediacount ?? count($data->media));
        $data->hascollections = (bool)($data->hascollections ?? !empty($data->collections));
        $data->collectioncount = (int)($data->collectioncount ?? count($data->collections));
        $data->hasexternalworks = (bool)($data->hasexternalworks ?? !empty($data->externalworks));
        $data->externalworkcount = (int)($data->externalworkcount ?? count($data->externalworks));
        $data->hascontentmarkers = (bool)($data->hascontentmarkers ?? !empty($data->contentmarkers));
        $data->contentmarkercount = (int)($data->contentmarkercount ?? count($data->contentmarkers));
        $data->hasadvisories = (bool)($data->hasadvisories ?? !empty($data->advisories) || $data->hascontentmarkers);
        $data->advisorycount = (int)($data->advisorycount ?? max(count($data->advisories), $data->contentmarkercount));
        $data->hasactions = (bool)($data->hasactions ?? !empty($data->actions));
        $data->hasstatuscounts = (bool)($data->hasstatuscounts ?? !empty($data->statuscounts));
        $data->haswarnings = (bool)($data->haswarnings ?? !empty($data->warnings));
        $data->hasnotices = (bool)($data->hasnotices ?? !empty($data->notices));

        if (!isset($data->exports) || (!is_array($data->exports) && !$data->exports instanceof stdClass)) {
            $data->exports = (object)[
                'canexport' => false,
                'exporturl' => $data->exporturl,
            ];
        }

        if (!isset($data->provenance) || (!is_array($data->provenance) && !$data->provenance instanceof stdClass)) {
            $data->provenance = new stdClass();
        }

        if (!isset($data->validation) || (!is_array($data->validation) && !$data->validation instanceof stdClass)) {
            $data->validation = new stdClass();
        }

        return $data;
    }

    /**
     * Export context for Mustache.
     *
     * @param renderer_base $output Renderer.
     * @return stdClass
     */
    public function export_for_template(renderer_base $output): stdClass {
        if ($this->directcontext !== null) {
            return $this->directcontext;
        }

        $status = $this->normalise_status((string)($this->summary['status'] ?? self::STATUS_ACTIVE));
        $visibility = $this->normalise_visibility((string)($this->summary['visibility'] ?? self::VISIBILITY_COURSE));
        $validationstate = $this->normalise_validation_state(
            (string)($this->summary['validationstate'] ?? self::VALIDATION_UNVERIFIED)
        );

        $data = new stdClass();
        $data->archiveid = $this->archiveid;
        $data->cmid = $this->cmid;
        $data->courseid = $this->courseid;
        $data->contextid = $this->contextid;
        $data->title = $this->title;
        $data->heading = get_string('archiveview', 'uckkarchive');

        $data->viewurl = (new moodle_url('/mod/uckkarchive/view.php', [
            'id' => $this->cmid,
        ]))->out(false);

        $data->additemurl = (new moodle_url('/mod/uckkarchive/add.php', [
            'id' => $this->cmid,
        ]))->out(false);

        $data->validateurl = (new moodle_url('/mod/uckkarchive/validate.php', [
            'id' => $this->cmid,
        ]))->out(false);

        $data->exporturl = (new moodle_url('/mod/uckkarchive/export.php', [
            'id' => $this->cmid,
        ]))->out(false);

        $data->mediaurl = (new moodle_url('/mod/uckkarchive/media.php', [
            'id' => $this->cmid,
        ]))->out(false);

        $data->hasintro = trim($this->introhtml) !== '';
        $data->introhtml = $this->introhtml;

        $data->status = $status;
        $data->statuslabel = $this->get_status_label($status);
        $data->statusclass = 'status-' . str_replace('_', '-', $status);

        $data->visibility = $visibility;
        $data->visibilitylabel = $this->get_visibility_label($visibility);
        $data->visibilityclass = 'visibility-' . str_replace('_', '-', $visibility);

        $data->validationstate = $validationstate;
        $data->validationlabel = $this->get_validation_state_label($validationstate);
        $data->validationclass = 'validation-' . str_replace('_', '-', $validationstate);

        $data->isrestricted = in_array($visibility, [
            self::VISIBILITY_RESTRICTED,
            self::VISIBILITY_RESTRICTED_INTEGRITY,
            self::VISIBILITY_RESTRICTED_CULTURAL,
            self::VISIBILITY_HIDDEN,
        ], true);

        $data->isculturalrestricted = $visibility === self::VISIBILITY_RESTRICTED_CULTURAL
            || !empty($this->summary['culturalprotocol'])
            || !empty($this->summary['hasculturalprotocol']);

        $data->isvalidated = in_array($validationstate, [
            self::VALIDATION_HUMAN_REVIEWED,
            self::VALIDATION_VERIFIED,
            self::VALIDATION_ARCHIVED,
        ], true);

        $data->iscontested = $status === self::STATUS_CONTESTED
            || $validationstate === self::VALIDATION_CONTESTED;

        $data->isinvalidated = $status === self::STATUS_INVALIDATED
            || $validationstate === self::VALIDATION_INVALIDATED;

        $data->timeopen = (int)($this->summary['timeopen'] ?? 0);
        $data->timeclose = (int)($this->summary['timeclose'] ?? 0);
        $data->hastimeopen = $data->timeopen > 0;
        $data->hastimeclose = $data->timeclose > 0;
        $data->timeopenlabel = $data->timeopen > 0 ? userdate($data->timeopen) : '';
        $data->timecloselabel = $data->timeclose > 0 ? userdate($data->timeclose) : '';

        $data->summaryhtml = (string)($this->summary['summaryhtml'] ?? '');
        $data->hassummaryhtml = trim($data->summaryhtml) !== '';

        $data->items = $this->build_archive_item_rows();
        $data->hasitems = !empty($data->items);
        $data->itemcount = count($data->items);

        $data->kristals = $this->build_kristal_rows();
        $data->haskristals = !empty($data->kristals);
        $data->kristalcount = count($data->kristals);

        $data->proofs = $this->build_proof_rows();
        $data->hasproofs = !empty($data->proofs);
        $data->proofcount = count($data->proofs);

        $data->exports = $this->build_export_rows();
        $data->hasexports = !empty($data->exports);
        $data->exportcount = count($data->exports);

        $data->media = $this->build_media_rows();
        $data->hasmedia = !empty($data->media);
        $data->mediacount = count($data->media);

        $data->collections = $this->build_collection_rows();
        $data->hascollections = !empty($data->collections);
        $data->collectioncount = count($data->collections);

        $data->externalworks = $this->build_external_work_rows();
        $data->hasexternalworks = !empty($data->externalworks);
        $data->externalworkcount = count($data->externalworks);

        $data->contentmarkers = $this->build_content_marker_rows();
        $data->hascontentmarkers = !empty($data->contentmarkers);
        $data->contentmarkercount = count($data->contentmarkers);
        $data->hasadvisories = $data->hascontentmarkers;
        $data->advisorycount = $data->contentmarkercount;

        $data->actions = $this->build_action_rows();
        $data->hasactions = !empty($data->actions);

        $data->warnings = $this->normalise_warnings($this->summary['warnings'] ?? []);
        $data->haswarnings = !empty($data->warnings);

        $data->notices = $this->normalise_notices($this->summary['notices'] ?? []);
        $data->hasnotices = !empty($data->notices);

        $data->stats = $this->build_stats($data);
        $data->hasstats = !empty($data->stats);

        $data->emptyitemslabel = get_string('archiveitems:none', 'uckkarchive');
        $data->emptykristalslabel = get_string('kristals:none', 'uckkarchive');
        $data->emptyproofslabel = get_string('proofs:none', 'uckkarchive');
        $data->emptyexportslabel = get_string('exports:none', 'uckkarchive');
        $data->emptymedialabel = $this->get_component_string('media:none', 'No media has been added.');
        $data->emptycollectionslabel = $this->get_component_string('mediacollections:none', 'No media collections have been added.');
        $data->emptyexternalworkslabel = $this->get_component_string('externalworks:none', 'No external works have been added.');
        $data->emptycontentmarkerslabel = $this->get_component_string('contentmarkers:none', 'No content advisories have been added.');
        $data->notice = get_string('archivegovernancenotice', 'uckkarchive');

        return $data;
    }

    /**
     * Normalise archive item row.
     *
     * @param array<string, mixed>|stdClass $item Raw row.
     * @return array<string, mixed>
     */
    private function normalise_archive_item(array|stdClass $item): array {
        $row = (array)$item;
        $status = $this->normalise_status((string)($row['status'] ?? self::STATUS_DRAFT));
        $visibility = $this->normalise_visibility((string)($row['visibility'] ?? self::VISIBILITY_COURSE));
        $validationstate = $this->normalise_validation_state(
            (string)($row['validationstate'] ?? $row['integritystate'] ?? self::VALIDATION_UNVERIFIED)
        );

        return [
            'id' => max(0, (int)($row['id'] ?? 0)),
            'title' => format_string((string)($row['title'] ?? $row['name'] ?? '')),
            'summary' => format_string((string)($row['summary'] ?? '')),
            'summaryhtml' => (string)($row['summaryhtml'] ?? ''),
            'itemtype' => clean_param((string)($row['itemtype'] ?? $row['type'] ?? 'archive_item'), PARAM_ALPHANUMEXT),
            'itemtypelabel' => format_string((string)($row['itemtypelabel'] ?? '')),
            'status' => $status,
            'statuslabel' => format_string((string)($row['statuslabel'] ?? $this->get_status_label($status))),
            'visibility' => $visibility,
            'visibilitylabel' => format_string((string)($row['visibilitylabel'] ?? $this->get_visibility_label($visibility))),
            'validationstate' => $validationstate,
            'validationlabel' => format_string(
                (string)($row['validationlabel'] ?? $this->get_validation_state_label($validationstate))
            ),
            'provenance' => clean_param((string)($row['provenance'] ?? ''), PARAM_ALPHANUMEXT),
            'provenancelabel' => format_string((string)($row['provenancelabel'] ?? '')),
            'url' => $this->normalise_url($row['url'] ?? null),
            'sourcecomponent' => clean_param((string)($row['sourcecomponent'] ?? ''), PARAM_COMPONENT),
            'sourceid' => max(0, (int)($row['sourceid'] ?? 0)),
            'timemodified' => max(0, (int)($row['timemodified'] ?? 0)),
            'timecreated' => max(0, (int)($row['timecreated'] ?? 0)),
            'restricted' => !empty($row['restricted']) || $this->is_restricted_visibility($visibility),
            'culturalprotocol' => !empty($row['culturalprotocol']) || $visibility === self::VISIBILITY_RESTRICTED_CULTURAL,
        ];
    }

    /**
     * Normalise Kristal row.
     *
     * @param array<string, mixed>|stdClass $kristal Raw row.
     * @return array<string, mixed>
     */
    private function normalise_kristal(array|stdClass $kristal): array {
        $row = (array)$kristal;
        $status = $this->normalise_status((string)($row['status'] ?? self::STATUS_DRAFT));
        $validationstate = $this->normalise_validation_state(
            (string)($row['validationstate'] ?? self::VALIDATION_UNVERIFIED)
        );

        return [
            'id' => max(0, (int)($row['id'] ?? 0)),
            'title' => format_string((string)($row['title'] ?? $row['name'] ?? '')),
            'summary' => format_string((string)($row['summary'] ?? '')),
            'content' => (string)($row['content'] ?? ''),
            'kristaltype' => clean_param((string)($row['kristaltype'] ?? $row['type'] ?? 'concept'), PARAM_ALPHANUMEXT),
            'kristaltypelabel' => format_string((string)($row['kristaltypelabel'] ?? '')),
            'status' => $status,
            'statuslabel' => format_string((string)($row['statuslabel'] ?? $this->get_status_label($status))),
            'validationstate' => $validationstate,
            'validationlabel' => format_string(
                (string)($row['validationlabel'] ?? $this->get_validation_state_label($validationstate))
            ),
            'url' => $this->normalise_url($row['url'] ?? null),
            'timecreated' => max(0, (int)($row['timecreated'] ?? 0)),
            'timemodified' => max(0, (int)($row['timemodified'] ?? 0)),
        ];
    }

    /**
     * Normalise proof row.
     *
     * @param array<string, mixed>|stdClass $proof Raw row.
     * @return array<string, mixed>
     */
    private function normalise_proof(array|stdClass $proof): array {
        $row = (array)$proof;
        $status = $this->normalise_status((string)($row['status'] ?? self::STATUS_DRAFT));

        return [
            'id' => max(0, (int)($row['id'] ?? 0)),
            'title' => format_string((string)($row['title'] ?? $row['name'] ?? '')),
            'summary' => format_string((string)($row['summary'] ?? '')),
            'prooftype' => clean_param((string)($row['prooftype'] ?? $row['type'] ?? 'text'), PARAM_ALPHANUMEXT),
            'prooftypelabel' => format_string((string)($row['prooftypelabel'] ?? '')),
            'status' => $status,
            'statuslabel' => format_string((string)($row['statuslabel'] ?? $this->get_status_label($status))),
            'provenance' => clean_param((string)($row['provenance'] ?? ''), PARAM_ALPHANUMEXT),
            'provenancelabel' => format_string((string)($row['provenancelabel'] ?? '')),
            'url' => $this->normalise_url($row['url'] ?? null),
            'hasfiles' => !empty($row['hasfiles']),
            'files' => $this->normalise_files($row['files'] ?? []),
            'timecreated' => max(0, (int)($row['timecreated'] ?? 0)),
            'timemodified' => max(0, (int)($row['timemodified'] ?? 0)),
        ];
    }

    /**
     * Normalise export row.
     *
     * @param array<string, mixed>|stdClass $export Raw row.
     * @return array<string, mixed>
     */
    private function normalise_export(array|stdClass $export): array {
        $row = (array)$export;
        $status = $this->normalise_status((string)($row['status'] ?? self::STATUS_DRAFT));

        return [
            'id' => max(0, (int)($row['id'] ?? 0)),
            'title' => format_string((string)($row['title'] ?? $row['name'] ?? $row['packagename'] ?? '')),
            'exporttype' => clean_param((string)($row['exporttype'] ?? $row['exportscope'] ?? $row['type'] ?? 'package'), PARAM_ALPHANUMEXT),
            'exporttypelabel' => format_string((string)($row['exporttypelabel'] ?? '')),
            'exportformat' => clean_param((string)($row['exportformat'] ?? ''), PARAM_ALPHANUMEXT),
            'status' => $status,
            'statuslabel' => format_string((string)($row['statuslabel'] ?? $this->get_status_label($status))),
            'url' => $this->normalise_url($row['url'] ?? null),
            'downloadurl' => $this->normalise_url($row['downloadurl'] ?? null),
            'timecreated' => max(0, (int)($row['timecreated'] ?? 0)),
            'timemodified' => max(0, (int)($row['timemodified'] ?? 0)),
        ];
    }

    /**
     * Normalise media row.
     *
     * @param array<string, mixed>|stdClass $media Raw row.
     * @return array<string, mixed>
     */
    private function normalise_media(array|stdClass $media): array {
        $row = (array)$media;
        $status = $this->normalise_status((string)($row['status'] ?? self::STATUS_ACTIVE));
        $visibility = $this->normalise_visibility((string)($row['visibility'] ?? self::VISIBILITY_COURSE));

        return [
            'id' => max(0, (int)($row['id'] ?? 0)),
            'uuid' => clean_param((string)($row['uuid'] ?? ''), PARAM_TEXT),
            'title' => format_string((string)($row['title'] ?? $row['name'] ?? '')),
            'summary' => format_string((string)($row['summary'] ?? '')),
            'description' => (string)($row['description'] ?? ''),
            'mediatype' => clean_param((string)($row['mediatype'] ?? $row['type'] ?? 'media'), PARAM_ALPHANUMEXT),
            'mediatypelabel' => format_string((string)($row['mediatypelabel'] ?? '')),
            'mimetype' => clean_param((string)($row['mimetype'] ?? ''), PARAM_TEXT),
            'status' => $status,
            'statuslabel' => format_string((string)($row['statuslabel'] ?? $this->get_status_label($status))),
            'visibility' => $visibility,
            'visibilitylabel' => format_string((string)($row['visibilitylabel'] ?? $this->get_visibility_label($visibility))),
            'url' => $this->normalise_url($row['url'] ?? null),
            'thumbnailurl' => $this->normalise_url($row['thumbnailurl'] ?? $row['thumburl'] ?? null),
            'previewurl' => $this->normalise_url($row['previewurl'] ?? null),
            'downloadurl' => $this->normalise_url($row['downloadurl'] ?? null),
            'versioncount' => max(0, (int)($row['versioncount'] ?? 0)),
            'contentmarkercount' => max(0, (int)($row['contentmarkercount'] ?? $row['advisorycount'] ?? 0)),
            'hasadvisories' => !empty($row['hasadvisories']) || (int)($row['contentmarkercount'] ?? $row['advisorycount'] ?? 0) > 0,
            'restricted' => !empty($row['restricted']) || $this->is_restricted_visibility($visibility),
            'culturalprotocol' => !empty($row['culturalprotocol']) || $visibility === self::VISIBILITY_RESTRICTED_CULTURAL,
            'timecreated' => max(0, (int)($row['timecreated'] ?? 0)),
            'timemodified' => max(0, (int)($row['timemodified'] ?? 0)),
        ];
    }

    /**
     * Normalise media collection row.
     *
     * @param array<string, mixed>|stdClass $collection Raw row.
     * @return array<string, mixed>
     */
    private function normalise_collection(array|stdClass $collection): array {
        $row = (array)$collection;
        $status = $this->normalise_status((string)($row['status'] ?? self::STATUS_ACTIVE));
        $visibility = $this->normalise_visibility((string)($row['visibility'] ?? self::VISIBILITY_COURSE));

        return [
            'id' => max(0, (int)($row['id'] ?? 0)),
            'uuid' => clean_param((string)($row['uuid'] ?? ''), PARAM_TEXT),
            'title' => format_string((string)($row['title'] ?? $row['name'] ?? '')),
            'summary' => format_string((string)($row['summary'] ?? '')),
            'description' => (string)($row['description'] ?? ''),
            'status' => $status,
            'statuslabel' => format_string((string)($row['statuslabel'] ?? $this->get_status_label($status))),
            'visibility' => $visibility,
            'visibilitylabel' => format_string((string)($row['visibilitylabel'] ?? $this->get_visibility_label($visibility))),
            'url' => $this->normalise_url($row['url'] ?? null),
            'media' => is_array($row['media'] ?? null) ? $row['media'] : [],
            'mediacount' => max(0, (int)($row['mediacount'] ?? $row['itemcount'] ?? 0)),
            'restricted' => !empty($row['restricted']) || $this->is_restricted_visibility($visibility),
            'culturalprotocol' => !empty($row['culturalprotocol']) || $visibility === self::VISIBILITY_RESTRICTED_CULTURAL,
            'timecreated' => max(0, (int)($row['timecreated'] ?? 0)),
            'timemodified' => max(0, (int)($row['timemodified'] ?? 0)),
        ];
    }

    /**
     * Normalise external work row.
     *
     * @param array<string, mixed>|stdClass $work Raw row.
     * @return array<string, mixed>
     */
    private function normalise_external_work(array|stdClass $work): array {
        $row = (array)$work;
        $status = $this->normalise_status((string)($row['status'] ?? self::STATUS_ACTIVE));
        $visibility = $this->normalise_visibility((string)($row['visibility'] ?? self::VISIBILITY_COURSE));

        return [
            'id' => max(0, (int)($row['id'] ?? 0)),
            'uuid' => clean_param((string)($row['uuid'] ?? ''), PARAM_TEXT),
            'title' => format_string((string)($row['title'] ?? $row['name'] ?? '')),
            'subtitle' => format_string((string)($row['subtitle'] ?? '')),
            'creator' => format_string((string)($row['creator'] ?? $row['author'] ?? '')),
            'publisher' => format_string((string)($row['publisher'] ?? '')),
            'publicationyear' => max(0, (int)($row['publicationyear'] ?? $row['year'] ?? 0)),
            'language' => clean_param((string)($row['language'] ?? ''), PARAM_TEXT),
            'worktype' => clean_param((string)($row['worktype'] ?? $row['type'] ?? 'other'), PARAM_ALPHANUMEXT),
            'worktypelabel' => format_string((string)($row['worktypelabel'] ?? '')),
            'rightsstatus' => clean_param((string)($row['rightsstatus'] ?? 'unknown'), PARAM_ALPHANUMEXT),
            'rightsstatuslabel' => format_string((string)($row['rightsstatuslabel'] ?? '')),
            'status' => $status,
            'statuslabel' => format_string((string)($row['statuslabel'] ?? $this->get_status_label($status))),
            'visibility' => $visibility,
            'visibilitylabel' => format_string((string)($row['visibilitylabel'] ?? $this->get_visibility_label($visibility))),
            'url' => $this->normalise_url($row['url'] ?? null),
            'sourceurl' => $this->normalise_url($row['sourceurl'] ?? null),
            'media_count' => max(0, (int)($row['media_count'] ?? $row['mediacount'] ?? 0)),
            'contentmarkercount' => max(0, (int)($row['contentmarkercount'] ?? $row['advisorycount'] ?? 0)),
            'hasadvisories' => !empty($row['hasadvisories']) || (int)($row['contentmarkercount'] ?? $row['advisorycount'] ?? 0) > 0,
            'restricted' => !empty($row['restricted']) || $this->is_restricted_visibility($visibility),
            'culturalprotocol' => !empty($row['culturalprotocol']) || $visibility === self::VISIBILITY_RESTRICTED_CULTURAL,
            'timecreated' => max(0, (int)($row['timecreated'] ?? 0)),
            'timemodified' => max(0, (int)($row['timemodified'] ?? 0)),
        ];
    }

    /**
     * Normalise content marker row.
     *
     * @param array<string, mixed>|stdClass $marker Raw row.
     * @return array<string, mixed>
     */
    private function normalise_content_marker(array|stdClass $marker): array {
        $row = (array)$marker;
        $severity = $this->normalise_severity((string)($row['severity'] ?? self::SEVERITY_NOTICE));
        $visibility = $this->normalise_visibility((string)($row['visibility'] ?? self::VISIBILITY_COURSE));
        $reviewstate = $this->normalise_status((string)($row['reviewstate'] ?? $row['status'] ?? self::STATUS_PENDING_REVIEW));

        return [
            'id' => max(0, (int)($row['id'] ?? 0)),
            'uuid' => clean_param((string)($row['uuid'] ?? ''), PARAM_TEXT),
            'mediaid' => max(0, (int)($row['mediaid'] ?? 0)),
            'externalworkid' => max(0, (int)($row['externalworkid'] ?? 0)),
            'targettype' => clean_param((string)($row['targettype'] ?? ''), PARAM_ALPHANUMEXT),
            'targetid' => max(0, (int)($row['targetid'] ?? 0)),
            'tagkey' => clean_param((string)($row['tagkey'] ?? $row['tag'] ?? ''), PARAM_ALPHANUMEXT),
            'taglabel' => format_string((string)($row['taglabel'] ?? $row['label'] ?? '')),
            'severity' => $severity,
            'severitylabel' => format_string((string)($row['severitylabel'] ?? $this->get_severity_label($severity))),
            'reviewstate' => $reviewstate,
            'reviewstatelabel' => format_string((string)($row['reviewstatelabel'] ?? $this->get_status_label($reviewstate))),
            'visibility' => $visibility,
            'visibilitylabel' => format_string((string)($row['visibilitylabel'] ?? $this->get_visibility_label($visibility))),
            'locatortype' => clean_param((string)($row['locatortype'] ?? ''), PARAM_ALPHANUMEXT),
            'locator' => format_string((string)($row['locator'] ?? $row['locatorvalue'] ?? '')),
            'locatorlabel' => format_string((string)($row['locatorlabel'] ?? '')),
            'description' => (string)($row['description'] ?? ''),
            'url' => $this->normalise_url($row['url'] ?? null),
            'restricted' => !empty($row['restricted']) || $severity === self::SEVERITY_RESTRICTED
                || $this->is_restricted_visibility($visibility),
            'culturalprotocol' => !empty($row['culturalprotocol']) || $visibility === self::VISIBILITY_RESTRICTED_CULTURAL,
            'timecreated' => max(0, (int)($row['timecreated'] ?? 0)),
            'timemodified' => max(0, (int)($row['timemodified'] ?? 0)),
        ];
    }

    /**
     * Normalise action row.
     *
     * @param array<string, mixed>|stdClass $action Raw action.
     * @return array<string, mixed>
     */
    private function normalise_action(array|stdClass $action): array {
        $row = (array)$action;
        $key = clean_param((string)($row['key'] ?? $row['action'] ?? ''), PARAM_ALPHANUMEXT);
        $method = strtoupper(clean_param((string)($row['method'] ?? 'get'), PARAM_ALPHA));

        if (!in_array($method, ['GET', 'POST'], true)) {
            $method = 'GET';
        }

        return [
            'key' => $key,
            'label' => format_string((string)($row['label'] ?? $this->get_action_label($key))),
            'url' => $this->normalise_url($row['url'] ?? null),
            'method' => $method,
            'primary' => !empty($row['primary']),
            'danger' => !empty($row['danger']),
            'disabled' => !empty($row['disabled']),
            'disabledreason' => format_string((string)($row['disabledreason'] ?? '')),
            'requiresconfirmation' => !empty($row['requiresconfirmation']),
            'confirmmessage' => format_string((string)($row['confirmmessage'] ?? '')),
        ];
    }

    /**
     * Build archive item rows.
     *
     * @return array<int, stdClass>
     */
    private function build_archive_item_rows(): array {
        $rows = [];

        foreach ($this->items as $item) {
            if ($item['title'] === '') {
                continue;
            }

            $rows[] = (object)[
                'id' => $item['id'],
                'title' => $item['title'],
                'summary' => $item['summary'],
                'hassummary' => $item['summary'] !== '',
                'summaryhtml' => $item['summaryhtml'],
                'hassummaryhtml' => trim($item['summaryhtml']) !== '',
                'itemtype' => $item['itemtype'],
                'itemtypelabel' => $item['itemtypelabel'] !== ''
                    ? $item['itemtypelabel']
                    : $this->get_item_type_label($item['itemtype']),
                'status' => $item['status'],
                'statuslabel' => $item['statuslabel'],
                'statusclass' => 'status-' . str_replace('_', '-', $item['status']),
                'visibility' => $item['visibility'],
                'visibilitylabel' => $item['visibilitylabel'],
                'visibilityclass' => 'visibility-' . str_replace('_', '-', $item['visibility']),
                'validationstate' => $item['validationstate'],
                'validationlabel' => $item['validationlabel'],
                'validationclass' => 'validation-' . str_replace('_', '-', $item['validationstate']),
                'provenance' => $item['provenance'],
                'provenancelabel' => $item['provenancelabel'],
                'hasprovenance' => $item['provenance'] !== '',
                'url' => $item['url'],
                'hasurl' => $item['url'] !== '',
                'sourcecomponent' => $item['sourcecomponent'],
                'sourceid' => $item['sourceid'],
                'hassource' => $item['sourcecomponent'] !== '' || $item['sourceid'] > 0,
                'timecreated' => $item['timecreated'],
                'timecreatedlabel' => $item['timecreated'] > 0 ? userdate($item['timecreated']) : '',
                'hastimecreated' => $item['timecreated'] > 0,
                'timemodified' => $item['timemodified'],
                'timemodifiedlabel' => $item['timemodified'] > 0 ? userdate($item['timemodified']) : '',
                'hastimemodified' => $item['timemodified'] > 0,
                'restricted' => $item['restricted'],
                'culturalprotocol' => $item['culturalprotocol'],
            ];
        }

        return $rows;
    }

    /**
     * Build Kristal rows.
     *
     * @return array<int, stdClass>
     */
    private function build_kristal_rows(): array {
        $rows = [];

        foreach ($this->kristals as $kristal) {
            if ($kristal['title'] === '') {
                continue;
            }

            $rows[] = (object)[
                'id' => $kristal['id'],
                'title' => $kristal['title'],
                'summary' => $kristal['summary'],
                'hassummary' => $kristal['summary'] !== '',
                'content' => $kristal['content'],
                'hascontent' => trim($kristal['content']) !== '',
                'kristaltype' => $kristal['kristaltype'],
                'kristaltypelabel' => $kristal['kristaltypelabel'] !== ''
                    ? $kristal['kristaltypelabel']
                    : $this->get_kristal_type_label($kristal['kristaltype']),
                'status' => $kristal['status'],
                'statuslabel' => $kristal['statuslabel'],
                'statusclass' => 'status-' . str_replace('_', '-', $kristal['status']),
                'validationstate' => $kristal['validationstate'],
                'validationlabel' => $kristal['validationlabel'],
                'validationclass' => 'validation-' . str_replace('_', '-', $kristal['validationstate']),
                'url' => $kristal['url'],
                'hasurl' => $kristal['url'] !== '',
                'timecreated' => $kristal['timecreated'],
                'timecreatedlabel' => $kristal['timecreated'] > 0 ? userdate($kristal['timecreated']) : '',
                'hastimecreated' => $kristal['timecreated'] > 0,
                'timemodified' => $kristal['timemodified'],
                'timemodifiedlabel' => $kristal['timemodified'] > 0 ? userdate($kristal['timemodified']) : '',
                'hastimemodified' => $kristal['timemodified'] > 0,
            ];
        }

        return $rows;
    }

    /**
     * Build proof rows.
     *
     * @return array<int, stdClass>
     */
    private function build_proof_rows(): array {
        $rows = [];

        foreach ($this->proofs as $proof) {
            if ($proof['title'] === '') {
                continue;
            }

            $rows[] = (object)[
                'id' => $proof['id'],
                'title' => $proof['title'],
                'summary' => $proof['summary'],
                'hassummary' => $proof['summary'] !== '',
                'prooftype' => $proof['prooftype'],
                'prooftypelabel' => $proof['prooftypelabel'] !== ''
                    ? $proof['prooftypelabel']
                    : $this->get_proof_type_label($proof['prooftype']),
                'status' => $proof['status'],
                'statuslabel' => $proof['statuslabel'],
                'statusclass' => 'status-' . str_replace('_', '-', $proof['status']),
                'provenance' => $proof['provenance'],
                'provenancelabel' => $proof['provenancelabel'],
                'hasprovenance' => $proof['provenance'] !== '',
                'url' => $proof['url'],
                'hasurl' => $proof['url'] !== '',
                'hasfiles' => $proof['hasfiles'],
                'files' => $proof['files'],
                'timecreated' => $proof['timecreated'],
                'timecreatedlabel' => $proof['timecreated'] > 0 ? userdate($proof['timecreated']) : '',
                'hastimecreated' => $proof['timecreated'] > 0,
                'timemodified' => $proof['timemodified'],
                'timemodifiedlabel' => $proof['timemodified'] > 0 ? userdate($proof['timemodified']) : '',
                'hastimemodified' => $proof['timemodified'] > 0,
            ];
        }

        return $rows;
    }

    /**
     * Build export rows.
     *
     * @return array<int, stdClass>
     */
    private function build_export_rows(): array {
        $rows = [];

        foreach ($this->exports as $export) {
            if ($export['title'] === '') {
                continue;
            }

            $rows[] = (object)[
                'id' => $export['id'],
                'title' => $export['title'],
                'exporttype' => $export['exporttype'],
                'exporttypelabel' => $export['exporttypelabel'] !== ''
                    ? $export['exporttypelabel']
                    : $this->get_export_type_label($export['exporttype']),
                'exportformat' => $export['exportformat'],
                'hasexportformat' => $export['exportformat'] !== '',
                'status' => $export['status'],
                'statuslabel' => $export['statuslabel'],
                'statusclass' => 'status-' . str_replace('_', '-', $export['status']),
                'url' => $export['url'],
                'hasurl' => $export['url'] !== '',
                'downloadurl' => $export['downloadurl'],
                'hasdownloadurl' => $export['downloadurl'] !== '',
                'timecreated' => $export['timecreated'],
                'timecreatedlabel' => $export['timecreated'] > 0 ? userdate($export['timecreated']) : '',
                'hastimecreated' => $export['timecreated'] > 0,
                'timemodified' => $export['timemodified'],
                'timemodifiedlabel' => $export['timemodified'] > 0 ? userdate($export['timemodified']) : '',
                'hastimemodified' => $export['timemodified'] > 0,
            ];
        }

        return $rows;
    }

    /**
     * Build media rows.
     *
     * @return array<int, stdClass>
     */
    private function build_media_rows(): array {
        $rows = [];

        foreach ($this->media as $media) {
            if ($media['title'] === '') {
                continue;
            }

            $rows[] = (object)[
                'id' => $media['id'],
                'uuid' => $media['uuid'],
                'title' => $media['title'],
                'summary' => $media['summary'],
                'hassummary' => $media['summary'] !== '',
                'description' => $media['description'],
                'hasdescription' => trim(strip_tags($media['description'])) !== '',
                'mediatype' => $media['mediatype'],
                'mediatypelabel' => $media['mediatypelabel'] !== ''
                    ? $media['mediatypelabel']
                    : $this->get_media_type_label($media['mediatype']),
                'mimetype' => $media['mimetype'],
                'hasmimetype' => $media['mimetype'] !== '',
                'status' => $media['status'],
                'statuslabel' => $media['statuslabel'],
                'statusclass' => 'status-' . str_replace('_', '-', $media['status']),
                'visibility' => $media['visibility'],
                'visibilitylabel' => $media['visibilitylabel'],
                'visibilityclass' => 'visibility-' . str_replace('_', '-', $media['visibility']),
                'url' => $media['url'],
                'hasurl' => $media['url'] !== '',
                'thumbnailurl' => $media['thumbnailurl'],
                'hasthumbnail' => $media['thumbnailurl'] !== '',
                'previewurl' => $media['previewurl'],
                'haspreview' => $media['previewurl'] !== '',
                'downloadurl' => $media['downloadurl'],
                'hasdownloadurl' => $media['downloadurl'] !== '',
                'versioncount' => $media['versioncount'],
                'hasversions' => $media['versioncount'] > 0,
                'contentmarkercount' => $media['contentmarkercount'],
                'hasadvisories' => $media['hasadvisories'],
                'restricted' => $media['restricted'],
                'culturalprotocol' => $media['culturalprotocol'],
                'timecreated' => $media['timecreated'],
                'timecreatedlabel' => $media['timecreated'] > 0 ? userdate($media['timecreated']) : '',
                'hastimecreated' => $media['timecreated'] > 0,
                'timemodified' => $media['timemodified'],
                'timemodifiedlabel' => $media['timemodified'] > 0 ? userdate($media['timemodified']) : '',
                'hastimemodified' => $media['timemodified'] > 0,
            ];
        }

        return $rows;
    }

    /**
     * Build media collection rows.
     *
     * @return array<int, stdClass>
     */
    private function build_collection_rows(): array {
        $rows = [];

        foreach ($this->collections as $collection) {
            if ($collection['title'] === '') {
                continue;
            }

            $rows[] = (object)[
                'id' => $collection['id'],
                'uuid' => $collection['uuid'],
                'title' => $collection['title'],
                'summary' => $collection['summary'],
                'hassummary' => $collection['summary'] !== '',
                'description' => $collection['description'],
                'hasdescription' => trim(strip_tags($collection['description'])) !== '',
                'status' => $collection['status'],
                'statuslabel' => $collection['statuslabel'],
                'statusclass' => 'status-' . str_replace('_', '-', $collection['status']),
                'visibility' => $collection['visibility'],
                'visibilitylabel' => $collection['visibilitylabel'],
                'visibilityclass' => 'visibility-' . str_replace('_', '-', $collection['visibility']),
                'url' => $collection['url'],
                'hasurl' => $collection['url'] !== '',
                'media' => $collection['media'],
                'hasmedia' => !empty($collection['media']),
                'mediacount' => $collection['mediacount'],
                'restricted' => $collection['restricted'],
                'culturalprotocol' => $collection['culturalprotocol'],
                'timecreated' => $collection['timecreated'],
                'timecreatedlabel' => $collection['timecreated'] > 0 ? userdate($collection['timecreated']) : '',
                'hastimecreated' => $collection['timecreated'] > 0,
                'timemodified' => $collection['timemodified'],
                'timemodifiedlabel' => $collection['timemodified'] > 0 ? userdate($collection['timemodified']) : '',
                'hastimemodified' => $collection['timemodified'] > 0,
            ];
        }

        return $rows;
    }

    /**
     * Build external work rows.
     *
     * @return array<int, stdClass>
     */
    private function build_external_work_rows(): array {
        $rows = [];

        foreach ($this->externalworks as $work) {
            if ($work['title'] === '') {
                continue;
            }

            $rows[] = (object)[
                'id' => $work['id'],
                'uuid' => $work['uuid'],
                'title' => $work['title'],
                'subtitle' => $work['subtitle'],
                'hassubtitle' => $work['subtitle'] !== '',
                'creator' => $work['creator'],
                'hascreator' => $work['creator'] !== '',
                'publisher' => $work['publisher'],
                'haspublisher' => $work['publisher'] !== '',
                'publicationyear' => $work['publicationyear'],
                'haspublicationyear' => $work['publicationyear'] > 0,
                'language' => $work['language'],
                'haslanguage' => $work['language'] !== '',
                'worktype' => $work['worktype'],
                'worktypelabel' => $work['worktypelabel'] !== ''
                    ? $work['worktypelabel']
                    : $this->get_external_work_type_label($work['worktype']),
                'rightsstatus' => $work['rightsstatus'],
                'rightsstatuslabel' => $work['rightsstatuslabel'] !== ''
                    ? $work['rightsstatuslabel']
                    : $this->get_rights_status_label($work['rightsstatus']),
                'status' => $work['status'],
                'statuslabel' => $work['statuslabel'],
                'statusclass' => 'status-' . str_replace('_', '-', $work['status']),
                'visibility' => $work['visibility'],
                'visibilitylabel' => $work['visibilitylabel'],
                'visibilityclass' => 'visibility-' . str_replace('_', '-', $work['visibility']),
                'url' => $work['url'],
                'hasurl' => $work['url'] !== '',
                'sourceurl' => $work['sourceurl'],
                'hassourceurl' => $work['sourceurl'] !== '',
                'mediacount' => $work['media_count'],
                'hasmedia' => $work['media_count'] > 0,
                'contentmarkercount' => $work['contentmarkercount'],
                'hasadvisories' => $work['hasadvisories'],
                'restricted' => $work['restricted'],
                'culturalprotocol' => $work['culturalprotocol'],
                'timecreated' => $work['timecreated'],
                'timecreatedlabel' => $work['timecreated'] > 0 ? userdate($work['timecreated']) : '',
                'hastimecreated' => $work['timecreated'] > 0,
                'timemodified' => $work['timemodified'],
                'timemodifiedlabel' => $work['timemodified'] > 0 ? userdate($work['timemodified']) : '',
                'hastimemodified' => $work['timemodified'] > 0,
            ];
        }

        return $rows;
    }

    /**
     * Build content marker rows.
     *
     * @return array<int, stdClass>
     */
    private function build_content_marker_rows(): array {
        $rows = [];

        foreach ($this->contentmarkers as $marker) {
            $label = $marker['taglabel'] !== ''
                ? $marker['taglabel']
                : $this->get_content_tag_label($marker['tagkey']);

            if ($label === '') {
                continue;
            }

            $rows[] = (object)[
                'id' => $marker['id'],
                'uuid' => $marker['uuid'],
                'mediaid' => $marker['mediaid'],
                'externalworkid' => $marker['externalworkid'],
                'targettype' => $marker['targettype'],
                'targetid' => $marker['targetid'],
                'tagkey' => $marker['tagkey'],
                'taglabel' => $label,
                'severity' => $marker['severity'],
                'severitylabel' => $marker['severitylabel'],
                'severityclass' => 'severity-' . str_replace('_', '-', $marker['severity']),
                'reviewstate' => $marker['reviewstate'],
                'reviewstatelabel' => $marker['reviewstatelabel'],
                'reviewstateclass' => 'reviewstate-' . str_replace('_', '-', $marker['reviewstate']),
                'visibility' => $marker['visibility'],
                'visibilitylabel' => $marker['visibilitylabel'],
                'visibilityclass' => 'visibility-' . str_replace('_', '-', $marker['visibility']),
                'locatortype' => $marker['locatortype'],
                'haslocatortype' => $marker['locatortype'] !== '',
                'locator' => $marker['locator'],
                'haslocator' => $marker['locator'] !== '',
                'locatorlabel' => $marker['locatorlabel'],
                'haslocatorlabel' => $marker['locatorlabel'] !== '',
                'description' => $marker['description'],
                'hasdescription' => trim(strip_tags($marker['description'])) !== '',
                'url' => $marker['url'],
                'hasurl' => $marker['url'] !== '',
                'restricted' => $marker['restricted'],
                'culturalprotocol' => $marker['culturalprotocol'],
                'timecreated' => $marker['timecreated'],
                'timecreatedlabel' => $marker['timecreated'] > 0 ? userdate($marker['timecreated']) : '',
                'hastimecreated' => $marker['timecreated'] > 0,
                'timemodified' => $marker['timemodified'],
                'timemodifiedlabel' => $marker['timemodified'] > 0 ? userdate($marker['timemodified']) : '',
                'hastimemodified' => $marker['timemodified'] > 0,
            ];
        }

        return $rows;
    }

    /**
     * Build action rows.
     *
     * @return array<int, stdClass>
     */
    private function build_action_rows(): array {
        $rows = [];

        foreach ($this->actions as $action) {
            if ($action['key'] === '' || $action['url'] === '') {
                continue;
            }

            $rows[] = (object)[
                'key' => $action['key'],
                'label' => $action['label'],
                'url' => $action['url'],
                'method' => $action['method'],
                'ispost' => $action['method'] === 'POST',
                'isget' => $action['method'] === 'GET',
                'primary' => $action['primary'],
                'danger' => $action['danger'],
                'secondary' => !$action['primary'] && !$action['danger'],
                'disabled' => $action['disabled'],
                'disabledreason' => $action['disabledreason'],
                'hasdisabledreason' => trim($action['disabledreason']) !== '',
                'requiresconfirmation' => $action['requiresconfirmation'],
                'confirmmessage' => $action['confirmmessage'],
                'hasconfirmmessage' => trim($action['confirmmessage']) !== '',
            ];
        }

        return $rows;
    }

    /**
     * Build summary statistics.
     *
     * @param stdClass $data Exported data.
     * @return array<int, stdClass>
     */
    private function build_stats(stdClass $data): array {
        $stats = [
            (object)[
                'key' => 'items',
                'label' => get_string('archiveitems', 'uckkarchive'),
                'value' => (string)$data->itemcount,
                'class' => $data->itemcount > 0 ? 'state-active' : 'state-empty',
            ],
            (object)[
                'key' => 'kristals',
                'label' => get_string('kristals', 'uckkarchive'),
                'value' => (string)$data->kristalcount,
                'class' => $data->kristalcount > 0 ? 'state-active' : 'state-empty',
            ],
            (object)[
                'key' => 'proofs',
                'label' => get_string('proofs', 'uckkarchive'),
                'value' => (string)$data->proofcount,
                'class' => $data->proofcount > 0 ? 'state-active' : 'state-empty',
            ],
            (object)[
                'key' => 'media',
                'label' => $this->get_component_string('media', 'Media'),
                'value' => (string)$data->mediacount,
                'class' => $data->mediacount > 0 ? 'state-active' : 'state-empty',
            ],
            (object)[
                'key' => 'collections',
                'label' => $this->get_component_string('mediacollections', 'Collections'),
                'value' => (string)$data->collectioncount,
                'class' => $data->collectioncount > 0 ? 'state-active' : 'state-empty',
            ],
            (object)[
                'key' => 'externalworks',
                'label' => $this->get_component_string('externalworks', 'External works'),
                'value' => (string)$data->externalworkcount,
                'class' => $data->externalworkcount > 0 ? 'state-active' : 'state-empty',
            ],
            (object)[
                'key' => 'advisories',
                'label' => $this->get_component_string('contentadvisories', 'Content advisories'),
                'value' => (string)$data->advisorycount,
                'class' => $data->advisorycount > 0 ? 'state-active' : 'state-empty',
            ],
            (object)[
                'key' => 'validation',
                'label' => get_string('validationstate', 'uckkarchive'),
                'value' => $data->validationlabel,
                'class' => $data->validationclass,
            ],
        ];

        return $stats;
    }

    /**
     * Normalise file rows.
     *
     * @param mixed $files File rows.
     * @return array<int, stdClass>
     */
    private function normalise_files(mixed $files): array {
        if (!is_array($files)) {
            return [];
        }

        $rows = [];

        foreach ($files as $file) {
            $row = (array)$file;
            $filename = format_string((string)($row['filename'] ?? $row['name'] ?? ''));
            $url = $this->normalise_url($row['url'] ?? null);

            if ($filename === '' || $url === '') {
                continue;
            }

            $rows[] = (object)[
                'filename' => $filename,
                'url' => $url,
                'mimetype' => clean_param((string)($row['mimetype'] ?? ''), PARAM_TEXT),
                'filesize' => max(0, (int)($row['filesize'] ?? 0)),
                'filesizelabel' => !empty($row['filesizelabel'])
                    ? format_string((string)$row['filesizelabel'])
                    : '',
            ];
        }

        return $rows;
    }

    /**
     * Normalise warnings.
     *
     * @param mixed $warnings Warning list.
     * @return array<int, stdClass>
     */
    private function normalise_warnings(mixed $warnings): array {
        return $this->normalise_messages($warnings, 'warning');
    }

    /**
     * Normalise notices.
     *
     * @param mixed $notices Notice list.
     * @return array<int, stdClass>
     */
    private function normalise_notices(mixed $notices): array {
        return $this->normalise_messages($notices, 'info');
    }

    /**
     * Normalise message rows.
     *
     * @param mixed $messages Message list.
     * @param string $defaultseverity Default severity.
     * @return array<int, stdClass>
     */
    private function normalise_messages(mixed $messages, string $defaultseverity): array {
        if (!is_array($messages)) {
            return [];
        }

        $rows = [];

        foreach ($messages as $message) {
            if (is_string($message)) {
                $text = trim($message);
                $severity = $defaultseverity;
            } else {
                $row = (array)$message;
                $text = trim((string)($row['message'] ?? ''));
                $severity = clean_param((string)($row['severity'] ?? $defaultseverity), PARAM_ALPHANUMEXT);
            }

            if ($text === '') {
                continue;
            }

            $rows[] = (object)[
                'message' => format_string($text),
                'severity' => $severity,
                'class' => 'alert-' . $this->get_alert_class($severity),
            ];
        }

        return $rows;
    }

    /**
     * Normalise status.
     *
     * @param string $status Raw status.
     * @return string
     */
    private function normalise_status(string $status): string {
        $status = clean_param($status, PARAM_ALPHANUMEXT);

        $allowed = [
            self::STATUS_DRAFT,
            self::STATUS_ACTIVE,
            self::STATUS_HIDDEN,
            self::STATUS_PENDING_REVIEW,
            self::STATUS_VALIDATED,
            self::STATUS_REJECTED,
            self::STATUS_CORRECTION_REQUIRED,
            self::STATUS_CONTESTED,
            self::STATUS_INVALIDATED,
            self::STATUS_CLOSED,
            self::STATUS_ARCHIVED,
            self::STATUS_DELETED,
        ];

        return in_array($status, $allowed, true) ? $status : self::STATUS_ACTIVE;
    }

    /**
     * Normalise visibility.
     *
     * @param string $visibility Raw visibility.
     * @return string
     */
    private function normalise_visibility(string $visibility): string {
        $visibility = clean_param($visibility, PARAM_ALPHANUMEXT);

        $allowed = [
            self::VISIBILITY_PRIVATE,
            self::VISIBILITY_USER,
            self::VISIBILITY_GROUP,
            self::VISIBILITY_COURSE,
            self::VISIBILITY_COHORT,
            self::VISIBILITY_PROGRAM,
            self::VISIBILITY_INSTITUTION,
            self::VISIBILITY_PUBLIC,
            self::VISIBILITY_RESTRICTED,
            self::VISIBILITY_RESTRICTED_INTEGRITY,
            self::VISIBILITY_RESTRICTED_CULTURAL,
            self::VISIBILITY_HIDDEN,
            self::VISIBILITY_ARCHIVED,
        ];

        return in_array($visibility, $allowed, true) ? $visibility : self::VISIBILITY_COURSE;
    }

    /**
     * Normalise validation state.
     *
     * @param string $state Raw validation state.
     * @return string
     */
    private function normalise_validation_state(string $state): string {
        $state = clean_param($state, PARAM_ALPHANUMEXT);

        $allowed = [
            self::VALIDATION_UNVERIFIED,
            self::VALIDATION_HUMAN_REVIEWED,
            self::VALIDATION_VERIFIED,
            self::VALIDATION_CONTESTED,
            self::VALIDATION_INVALIDATED,
            self::VALIDATION_ARCHIVED,
        ];

        return in_array($state, $allowed, true) ? $state : self::VALIDATION_UNVERIFIED;
    }

    /**
     * Normalise content advisory severity.
     *
     * @param string $severity Raw severity.
     * @return string
     */
    private function normalise_severity(string $severity): string {
        $severity = clean_param($severity, PARAM_ALPHANUMEXT);

        $allowed = [
            self::SEVERITY_NOTICE,
            self::SEVERITY_MODERATE,
            self::SEVERITY_STRONG,
            self::SEVERITY_RESTRICTED,
        ];

        return in_array($severity, $allowed, true) ? $severity : self::SEVERITY_NOTICE;
    }

    /**
     * Whether a visibility is restricted.
     *
     * @param string $visibility Visibility.
     * @return bool
     */
    private function is_restricted_visibility(string $visibility): bool {
        return in_array($visibility, [
            self::VISIBILITY_RESTRICTED,
            self::VISIBILITY_RESTRICTED_INTEGRITY,
            self::VISIBILITY_RESTRICTED_CULTURAL,
            self::VISIBILITY_HIDDEN,
        ], true);
    }

    /**
     * Get status label.
     *
     * Internal status keys may keep legacy archive vocabulary for
     * database/API stability. Public fallbacks must not display "archive".
     *
     * @param string $status Status.
     * @return string
     */
    private function get_status_label(string $status): string {
        return $this->get_component_string(
            'status:' . $status,
            $this->display_fallback_label($status)
        );
    }

    /**
     * Get visibility label.
     *
     * Internal visibility keys may keep legacy archive vocabulary for
     * database/API stability. Public fallbacks must not display "archive".
     *
     * @param string $visibility Visibility.
     * @return string
     */
    private function get_visibility_label(string $visibility): string {
        return $this->get_component_string(
            'visibility:' . $visibility,
            $this->display_fallback_label($visibility)
        );
    }

    /**
     * Get validation state label.
     *
     * Internal validation keys may keep legacy archive vocabulary for
     * database/API stability. Public fallbacks must not display "archive".
     *
     * @param string $state Validation state.
     * @return string
     */
    private function get_validation_state_label(string $state): string {
        return $this->get_component_string(
            'validation:' . $state,
            $this->display_fallback_label($state)
        );
    }

    /**
     * Get registry item type label.
     *
     * Internal item type keys may keep legacy archive vocabulary for
     * database/API stability. Public fallbacks must not display "archive".
     *
     * @param string $type Item type.
     * @return string
     */
    private function get_item_type_label(string $type): string {
        return $this->get_component_string(
            'itemtype:' . $type,
            $this->display_fallback_label($type)
        );
    }

    /**
     * Get Kristal type label.
     *
     * @param string $type Kristal type.
     * @return string
     */
    private function get_kristal_type_label(string $type): string {
        return $this->get_component_string(
            'kristaltype:' . $type,
            $this->display_fallback_label($type)
        );
    }

    /**
     * Get proof type label.
     *
     * @param string $type Proof type.
     * @return string
     */
    private function get_proof_type_label(string $type): string {
        return $this->get_component_string(
            'prooftype:' . $type,
            $this->display_fallback_label($type)
        );
    }

    /**
     * Get export type label.
     *
     * @param string $type Export type.
     * @return string
     */
    private function get_export_type_label(string $type): string {
        return $this->get_component_string(
            'exporttype:' . $type,
            $this->display_fallback_label($type)
        );
    }

    /**
     * Get media type label.
     *
     * @param string $type Media type.
     * @return string
     */
    private function get_media_type_label(string $type): string {
        return $this->get_component_string(
            'mediatype:' . $type,
            $this->display_fallback_label($type)
        );
    }

    /**
     * Get external work type label.
     *
     * @param string $type External work type.
     * @return string
     */
    private function get_external_work_type_label(string $type): string {
        return $this->get_component_string(
            'externalworktype:' . $type,
            $this->display_fallback_label($type)
        );
    }

    /**
     * Get rights status label.
     *
     * @param string $status Rights status.
     * @return string
     */
    private function get_rights_status_label(string $status): string {
        return $this->get_component_string(
            'rightsstatus:' . $status,
            $this->display_fallback_label($status)
        );
    }

    /**
     * Get content tag label.
     *
     * @param string $tagkey Tag key.
     * @return string
     */
    private function get_content_tag_label(string $tagkey): string {
        return $this->get_component_string(
            'contenttag:' . $tagkey,
            $this->display_fallback_label($tagkey)
        );
    }

    /**
     * Get severity label.
     *
     * @param string $severity Severity key.
     * @return string
     */
    private function get_severity_label(string $severity): string {
        return $this->get_component_string(
            'severity:' . $severity,
            $this->display_fallback_label($severity)
        );
    }

    /**
     * Get action label.
     *
     * @param string $key Action key.
     * @return string
     */
    private function get_action_label(string $key): string {
        return $this->get_component_string(
            'action:' . $key,
            $this->display_fallback_label($key)
        );
    }

    /**
     * Build a safe public fallback label from an internal key.
     *
     * Internal keys and constants may keep legacy archive vocabulary for
     * database/API stability. This method prevents those internal names from
     * leaking into the rendered interface when a language string is missing.
     *
     * @param string $key Internal key.
     * @return string Safe display fallback.
     */
    private function display_fallback_label(string $key): string {
        $label = trim(str_replace('_', ' ', $key));

        if ($label === '') {
            return '';
        }

        $replacements = [
            'archived' => 'preserved',
            'archive items' => 'registry items',
            'archive item' => 'registry item',
            'archives' => 'registries',
            'archive' => 'registry',
        ];

        foreach ($replacements as $search => $replace) {
            $label = preg_replace(
                '/\b' . preg_quote($search, '/') . '\b/i',
                $replace,
                $label
            ) ?? $label;
        }

        return ucfirst($label);
    }

    /**
     * Get component string with fallback.
     *
     * @param string $key String key.
     * @param string $fallback Fallback.
     * @return string
     */
    private function get_component_string(string $key, string $fallback): string {
        if (get_string_manager()->string_exists($key, 'uckkarchive')) {
            return get_string($key, 'uckkarchive');
        }

        return $fallback;
    }

    /**
     * Map severity to Bootstrap alert suffix.
     *
     * @param string $severity Severity.
     * @return string
     */
    private function get_alert_class(string $severity): string {
        return match ($severity) {
            'danger', 'error', 'invalidated', 'restricted', 'strong' => 'danger',
            'success', 'validated', 'verified' => 'success',
            'info', 'notice' => 'info',
            default => 'warning',
        };
    }

    /**
     * Normalise a URL.
     *
     * @param mixed $url Raw URL.
     * @return string
     */
    private function normalise_url(mixed $url): string {
        if ($url instanceof moodle_url) {
            return $url->out(false);
        }

        if (is_string($url) && trim($url) !== '') {
            return (new moodle_url($url))->out(false);
        }

        return '';
    }
}