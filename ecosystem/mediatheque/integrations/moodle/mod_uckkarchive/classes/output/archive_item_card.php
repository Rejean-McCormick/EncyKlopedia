<?php
// This file is part of Moodle - https://moodle.org/
//
// Moodle is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// any later version.

/**
 * Archive item card output object.
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
 * Renderable card for one UCKK archive item.
 *
 * This class prepares display data only. It does not decide permissions,
 * validate archive records, revise archive history, export files, open
 * integrity cases, or make AI/human authority decisions.
 */
final class archive_item_card implements renderable, templatable {
    /** Archive item type: proof. */
    public const TYPE_PROOF = 'proof';

    /** Archive item type: decision. */
    public const TYPE_DECISION = 'decision';

    /** Archive item type: course work. */
    public const TYPE_COURSE_WORK = 'course_work';

    /** Archive item type: challenge result. */
    public const TYPE_CHALLENGE_RESULT = 'challenge_result';

    /** Archive item type: assembly minutes. */
    public const TYPE_ASSEMBLY_MINUTES = 'assembly_minutes';

    /** Archive item type: integrity case summary. */
    public const TYPE_INTEGRITY_CASE_SUMMARY = 'integrity_case_summary';

    /** Archive item type: Kristal. */
    public const TYPE_KRISTAL = 'kristal';

    /** Archive item type: reflection. */
    public const TYPE_REFLECTION = 'reflection';

    /** Archive item type: portfolio item. */
    public const TYPE_PORTFOLIO_ITEM = 'portfolio_item';

    /** Archive item type: version record. */
    public const TYPE_VERSION_RECORD = 'version_record';

    /** Status: draft. */
    public const STATUS_DRAFT = 'draft';

    /** Status: submitted. */
    public const STATUS_SUBMITTED = 'submitted';

    /** Status: under review. */
    public const STATUS_UNDER_REVIEW = 'under_review';

    /** Status: active. */
    public const STATUS_ACTIVE = 'active';

    /** Status: validated. */
    public const STATUS_VALIDATED = 'validated';

    /** Status: published. */
    public const STATUS_PUBLISHED = 'published';

    /** Status: restricted. */
    public const STATUS_RESTRICTED = 'restricted';

    /** Status: contested. */
    public const STATUS_CONTESTED = 'contested';

    /** Status: invalidated. */
    public const STATUS_INVALIDATED = 'invalidated';

    /** Status: superseded. */
    public const STATUS_SUPERSEDED = 'superseded';

    /** Status: archived. */
    public const STATUS_ARCHIVED = 'archived';

    /** Status: hidden. */
    public const STATUS_HIDDEN = 'hidden';

    /** Status: pending. */
    public const STATUS_PENDING = 'pending';

    /** Status: pending review. */
    public const STATUS_PENDING_REVIEW = 'pending_review';

    /** Status: rejected. */
    public const STATUS_REJECTED = 'rejected';

    /** Status: correction required. */
    public const STATUS_CORRECTION_REQUIRED = 'correction_required';

    /** Status: closed. */
    public const STATUS_CLOSED = 'closed';

    /** Status: cancelled. */
    public const STATUS_CANCELLED = 'cancelled';

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

    /** Provenance: human. */
    public const PROVENANCE_HUMAN = 'human';

    /** Provenance: AI-assisted. */
    public const PROVENANCE_AI_ASSISTED = 'ai_assisted';

    /** Provenance: imported. */
    public const PROVENANCE_IMPORTED = 'imported';

    /** Provenance: system. */
    public const PROVENANCE_SYSTEM = 'system';

    /** Provenance: archive. */
    public const PROVENANCE_ARCHIVE = 'archive';

    /** Provenance: assembly. */
    public const PROVENANCE_ASSEMBLY = 'assembly';

    /** Provenance: challenge. */
    public const PROVENANCE_CHALLENGE = 'challenge';

    /** Provenance: integrity. */
    public const PROVENANCE_INTEGRITY = 'integrity';

    /** Provenance: media. */
    public const PROVENANCE_MEDIA = 'media';

    /** Provenance: external work. */
    public const PROVENANCE_EXTERNAL_WORK = 'external_work';

    /** Provenance: content review. */
    public const PROVENANCE_CONTENT_REVIEW = 'content_review';

    /** @var array<string, mixed> Archive item data. */
    private array $item;

    /** @var array<int, array<string, mixed>> Proof rows already filtered for the viewer. */
    private array $proofs;

    /** @var array<int, array<string, mixed>> Media rows already filtered for the viewer. */
    private array $media;

    /** @var array<int, array<string, mixed>> Content marker rows already filtered for the viewer. */
    private array $contentmarkers;

    /** @var array<int, array<string, mixed>> Content review rows already filtered for the viewer. */
    private array $contentreviews;

    /** @var array<int, array<string, mixed>> Revision rows already filtered for the viewer. */
    private array $revisions;

    /** @var array<int, array<string, mixed>> Export rows already filtered for the viewer. */
    private array $exports;

    /** @var array<int, array<string, mixed>> Action rows already filtered for the viewer. */
    private array $actions;

    /** @var array<int, array<string, mixed>> Warning rows already filtered for the viewer. */
    private array $warnings;

    /** @var array<string, mixed> Extra context/options. */
    private array $options;

    /**
     * Constructor.
     *
     * Supports both:
     * - old style: new archive_item_card($item, $proofs, $actions, $warnings)
     * - option style: new archive_item_card($item, ['proofs' => ..., 'actions' => ...])
     *
     * @param array<string, mixed>|stdClass $item Archive item data.
     * @param array<int|string, mixed> $proofs Permission-filtered proof rows or options array.
     * @param array<int, array<string, mixed>|stdClass> $actions Permission-filtered action rows.
     * @param array<int, array<string, mixed>|stdClass|string> $warnings Permission-filtered warnings.
     */
    public function __construct(
        array|stdClass $item,
        array $proofs = [],
        array $actions = [],
        array $warnings = []
    ) {
        $this->item = $this->normalise_item($item);

        if ($this->looks_like_options($proofs)) {
            $this->options = $proofs;
            $this->proofs = array_map([$this, 'normalise_proof'], $this->as_list($proofs['proofs'] ?? []));
            $this->media = array_map([$this, 'normalise_media'], $this->as_list($proofs['media'] ?? []));
            $this->contentmarkers = array_map([$this, 'normalise_content_marker'], $this->as_list($proofs['contentmarkers'] ?? []));
            $this->contentreviews = array_map([$this, 'normalise_content_review'], $this->as_list($proofs['contentreviews'] ?? []));
            $this->revisions = array_map([$this, 'normalise_revision'], $this->as_list($proofs['revisions'] ?? []));
            $this->exports = array_map([$this, 'normalise_export'], $this->as_list($proofs['exports'] ?? []));
            $this->actions = array_map([$this, 'normalise_action'], $this->as_list($proofs['actions'] ?? $actions));
            $this->warnings = $this->normalise_warnings($this->as_list($proofs['warnings'] ?? $warnings));
        } else {
            $this->options = [];
            $this->proofs = array_map([$this, 'normalise_proof'], $proofs);
            $this->media = [];
            $this->contentmarkers = [];
            $this->contentreviews = [];
            $this->revisions = [];
            $this->exports = [];
            $this->actions = array_map([$this, 'normalise_action'], $actions);
            $this->warnings = $this->normalise_warnings($warnings);
        }
    }

    /**
     * Export context for Mustache.
     *
     * @param renderer_base $output Renderer.
     * @return stdClass
     */
    public function export_for_template(renderer_base $output): stdClass {
        $data = new stdClass();

        $data->id = $this->item['id'];
        $data->archiveid = $this->item['archiveid'];
        $data->courseid = $this->item['courseid'];
        $data->cmid = $this->item['cmid'];
        $data->contextid = $this->item['contextid'];

        $data->itemtype = $this->item['itemtype'];
        $data->itemtypelabel = $this->get_item_type_label($this->item['itemtype']);
        $data->itemtypeclass = $this->get_css_class('archive-item-type', $this->item['itemtype']);

        $data->title = $this->item['title'];
        $data->summary = $this->item['summary'];
        $data->hassummary = $data->summary !== '';

        $data->content = $this->item['content'];
        $data->hascontent = $data->content !== '';

        $data->status = $this->item['status'];
        $data->statuslabel = $this->get_status_label($this->item['status']);
        $data->statusclass = $this->get_css_class('status', $this->item['status']);

        $data->validationstate = $this->item['validationstate'];
        $data->validationlabel = $this->get_validation_label($this->item['validationstate']);
        $data->validationclass = $this->get_css_class('validation', $this->item['validationstate']);

        $data->visibility = $this->item['visibility'];
        $data->visibilitylabel = $this->get_visibility_label($this->item['visibility']);
        $data->visibilityclass = $this->get_css_class('visibility', $this->item['visibility']);

        $data->provenance = $this->item['provenance'];
        $data->provenancelabel = $this->get_provenance_label($this->item['provenance']);
        $data->provenanceclass = $this->get_css_class('provenance', $this->item['provenance']);

        $data->sourcecomponent = $this->item['sourcecomponent'];
        $data->hassourcecomponent = $data->sourcecomponent !== '';
        $data->sourceitemid = $this->item['sourceitemid'];
        $data->hassourceitemid = $data->sourceitemid > 0;
        $data->sourceurl = $this->item['sourceurl'];
        $data->hassourceurl = $data->sourceurl !== '';
        $data->sourceauthor = $this->item['sourceauthor'];
        $data->hassourceauthor = $data->sourceauthor !== '';
        $data->sourcedate = $this->item['sourcedate'];
        $data->sourcedatelabel = $this->item['sourcedate'] > 0 ? userdate($this->item['sourcedate']) : '';
        $data->hassourcedate = $data->sourcedatelabel !== '';

        $data->url = $this->item['url'];
        $data->hasurl = $data->url !== '';
        $data->viewurl = $this->build_item_url();
        $data->hasviewurl = $data->viewurl !== '';

        $data->kristalid = $this->item['kristalid'];
        $data->haskristal = $data->kristalid > 0 || $this->item['kristaltitle'] !== '';
        $data->kristaltitle = $this->item['kristaltitle'];
        $data->kristalurl = $this->item['kristalurl'];
        $data->haskristalurl = $data->kristalurl !== '';

        $data->versionno = $this->item['versionno'];
        $data->versionlabel = $this->get_version_label($data->versionno);
        $data->hasversion = $data->versionno > 0;

        $data->timecreated = $this->item['timecreated'];
        $data->timecreatedlabel = $this->item['timecreated'] > 0 ? userdate($this->item['timecreated']) : '';
        $data->hastimecreated = $data->timecreatedlabel !== '';

        $data->timemodified = $this->item['timemodified'];
        $data->timemodifiedlabel = $this->item['timemodified'] > 0 ? userdate($this->item['timemodified']) : '';
        $data->hastimemodified = $data->timemodifiedlabel !== '';

        $data->validatedby = $this->item['validatedby'];
        $data->validatorlabel = $this->item['validatorlabel'];
        $data->hasvalidator = $data->validatorlabel !== '';
        $data->timevalidated = $this->item['timevalidated'];
        $data->timevalidatedlabel = $this->item['timevalidated'] > 0 ? userdate($this->item['timevalidated']) : '';
        $data->hastimevalidated = $data->timevalidatedlabel !== '';

        $data->isvalidated = $this->is_validated();
        $data->iscontested = $this->is_contested();
        $data->isinvalidated = $this->is_invalidated();
        $data->isrestricted = $this->is_restricted();
        $data->isculturalrestricted = $this->is_cultural_restricted();
        $data->isarchived = $this->item['status'] === self::STATUS_ARCHIVED
            || $this->item['validationstate'] === self::VALIDATION_ARCHIVED;
        $data->isaiassisted = $this->item['provenance'] === self::PROVENANCE_AI_ASSISTED;

        $data->proofs = $this->build_proof_rows();
        $data->proofcount = count($data->proofs);
        $data->hasproofs = $data->proofcount > 0;

        $data->media = $this->build_media_rows();
        $data->mediacount = count($data->media);
        $data->hasmedia = $data->mediacount > 0;

        $data->contentmarkers = $this->build_content_marker_rows();
        $data->contentmarkercount = count($data->contentmarkers);
        $data->hascontentmarkers = $data->contentmarkercount > 0;

        $data->contentreviews = $this->build_content_review_rows();
        $data->contentreviewcount = count($data->contentreviews);
        $data->hascontentreviews = $data->contentreviewcount > 0;

        $data->revisions = $this->build_revision_rows();
        $data->revisioncount = count($data->revisions);
        $data->hasrevisions = $data->revisioncount > 0;

        $data->exports = $this->build_export_rows();
        $data->exportcount = count($data->exports);
        $data->hasexports = $data->exportcount > 0;

        $data->warnings = $this->build_warning_rows();
        $data->haswarnings = !empty($data->warnings);

        $data->actions = $this->build_action_rows();
        $data->hasactions = !empty($data->actions);

        $data->badges = $this->build_badge_rows();
        $data->hasbadges = !empty($data->badges);

        $data->notice = $this->get_notice();
        $data->hasnotice = $data->notice !== '';

        $data->canviewrestricted = !empty($this->options['canviewrestricted']);
        $data->canviewmedia = !empty($this->options['canviewmedia']);
        $data->canviewadvisories = !empty($this->options['canviewadvisories']);

        return $data;
    }

    /**
     * Normalise archive item data.
     *
     * @param array<string, mixed>|stdClass $item Raw item data.
     * @return array<string, mixed>
     */
    private function normalise_item(array|stdClass $item): array {
        $row = (array)$item;

        return [
            'id' => max(0, (int)($row['id'] ?? 0)),
            'archiveid' => max(0, (int)($row['archiveid'] ?? $row['uckkarchiveid'] ?? 0)),
            'courseid' => max(0, (int)($row['courseid'] ?? 0)),
            'cmid' => max(0, (int)($row['cmid'] ?? 0)),
            'contextid' => max(0, (int)($row['contextid'] ?? 0)),
            'userid' => max(0, (int)($row['userid'] ?? $row['ownerid'] ?? 0)),

            'itemtype' => $this->normalise_item_type((string)($row['itemtype'] ?? $row['type'] ?? self::TYPE_PROOF)),
            'title' => format_string((string)($row['title'] ?? $row['name'] ?? '')),
            'summary' => $this->format_html((string)($row['summary'] ?? $row['publicsummary'] ?? '')),
            'content' => $this->format_html((string)($row['content'] ?? '')),

            'status' => $this->normalise_status((string)($row['status'] ?? self::STATUS_DRAFT)),
            'validationstate' => $this->normalise_validation_state(
                (string)($row['validationstate'] ?? $row['validation'] ?? self::VALIDATION_UNVERIFIED)
            ),
            'visibility' => $this->normalise_visibility((string)($row['visibility'] ?? self::VISIBILITY_COURSE)),
            'provenance' => $this->normalise_provenance((string)($row['provenance'] ?? self::PROVENANCE_HUMAN)),

            'sourcecomponent' => clean_param((string)($row['sourcecomponent'] ?? ''), PARAM_COMPONENT),
            'sourceitemid' => max(0, (int)($row['sourceitemid'] ?? $row['sourceid'] ?? 0)),
            'sourceurl' => $this->normalise_url($row['sourceurl'] ?? ''),
            'sourceauthor' => format_string((string)($row['sourceauthor'] ?? '')),
            'sourcedate' => max(0, (int)($row['sourcedate'] ?? 0)),

            'url' => $this->normalise_url($row['url'] ?? ''),
            'kristalid' => max(0, (int)($row['kristalid'] ?? 0)),
            'kristaltitle' => format_string((string)($row['kristaltitle'] ?? '')),
            'kristalurl' => $this->normalise_url($row['kristalurl'] ?? ''),

            'versionno' => max(1, (int)($row['versionno'] ?? 1)),
            'validatedby' => max(0, (int)($row['validatedby'] ?? 0)),
            'validatorlabel' => format_string((string)($row['validatorlabel'] ?? '')),
            'timevalidated' => max(0, (int)($row['timevalidated'] ?? 0)),
            'timecreated' => max(0, (int)($row['timecreated'] ?? 0)),
            'timemodified' => max(0, (int)($row['timemodified'] ?? 0)),
        ];
    }

    /**
     * Normalise proof summary row.
     *
     * @param array<string, mixed>|stdClass $proof Raw proof data.
     * @return array<string, mixed>
     */
    private function normalise_proof(array|stdClass $proof): array {
        $row = (array)$proof;

        $prooftype = clean_param((string)($row['prooftype'] ?? $row['type'] ?? 'text'), PARAM_ALPHANUMEXT);
        $validationstate = $this->normalise_validation_state(
            (string)($row['validationstate'] ?? $row['validation'] ?? self::VALIDATION_UNVERIFIED)
        );
        $visibility = $this->normalise_visibility((string)($row['visibility'] ?? self::VISIBILITY_COURSE));

        return [
            'id' => max(0, (int)($row['id'] ?? 0)),
            'prooftype' => $prooftype,
            'prooftypelabel' => $this->get_proof_type_label($prooftype),
            'title' => format_string((string)($row['title'] ?? $row['name'] ?? '')),
            'summary' => $this->format_html((string)($row['summary'] ?? '')),
            'hassummary' => trim(strip_tags((string)($row['summary'] ?? ''))) !== '',
            'validationstate' => $validationstate,
            'validationlabel' => $this->get_validation_label($validationstate),
            'visibility' => $visibility,
            'visibilitylabel' => $this->get_visibility_label($visibility),
            'url' => $this->normalise_url($row['url'] ?? ''),
            'hasurl' => trim((string)($row['url'] ?? '')) !== '',
            'fileurl' => $this->normalise_url($row['fileurl'] ?? ''),
            'hasfileurl' => trim((string)($row['fileurl'] ?? '')) !== '',
            'filename' => format_string((string)($row['filename'] ?? '')),
            'hasfilename' => trim((string)($row['filename'] ?? '')) !== '',
            'restricted' => $this->visibility_is_restricted($visibility),
        ];
    }

    /**
     * Normalise media row.
     *
     * @param array<string, mixed>|stdClass $media Media row.
     * @return array<string, mixed>
     */
    private function normalise_media(array|stdClass $media): array {
        $row = (array)$media;

        $visibility = $this->normalise_visibility((string)($row['visibility'] ?? self::VISIBILITY_COURSE));
        $status = clean_param((string)($row['status'] ?? self::STATUS_ACTIVE), PARAM_ALPHANUMEXT);
        $mediatype = clean_param((string)($row['mediatype'] ?? $row['type'] ?? 'document'), PARAM_ALPHANUMEXT);
        $audience = clean_param((string)($row['audiencesuitability'] ?? 'guided'), PARAM_ALPHANUMEXT);

        return [
            'id' => max(0, (int)($row['id'] ?? 0)),
            'uuid' => (string)($row['uuid'] ?? ''),
            'title' => format_string((string)($row['title'] ?? $row['name'] ?? $row['filename'] ?? '')),
            'description' => $this->format_html((string)($row['description'] ?? $row['summary'] ?? '')),
            'hasdescription' => trim(strip_tags((string)($row['description'] ?? $row['summary'] ?? ''))) !== '',
            'mediatype' => $mediatype,
            'mediatypelabel' => $this->get_component_string('mediatype_' . $mediatype, $this->label_from_key($mediatype)),
            'mimetype' => (string)($row['mimetype'] ?? ''),
            'hasmimetype' => (string)($row['mimetype'] ?? '') !== '',
            'status' => $status,
            'statuslabel' => $this->get_component_string('mediastatus_' . $status, $this->label_from_key($status)),
            'visibility' => $visibility,
            'visibilitylabel' => $this->get_visibility_label($visibility),
            'audiencesuitability' => $audience,
            'audiencesuitabilitylabel' => $this->get_component_string('audiencesuitability_' . $audience, $this->label_from_key($audience)),
            'url' => $this->normalise_url($row['url'] ?? ''),
            'timecreated' => max(0, (int)($row['timecreated'] ?? 0)),
            'timemodified' => max(0, (int)($row['timemodified'] ?? 0)),
            'restricted' => $this->visibility_is_restricted($visibility) || $status === self::STATUS_RESTRICTED,
            'culturalrestricted' => $visibility === self::VISIBILITY_RESTRICTED_CULTURAL || $audience === 'restricted_cultural',
        ];
    }

    /**
     * Normalise content marker row.
     *
     * @param array<string, mixed>|stdClass $marker Marker row.
     * @return array<string, mixed>
     */
    private function normalise_content_marker(array|stdClass $marker): array {
        $row = (array)$marker;

        $severity = clean_param((string)($row['severity'] ?? 'notice'), PARAM_ALPHANUMEXT);
        $reviewstate = clean_param((string)($row['reviewstate'] ?? $row['state'] ?? 'pending_review'), PARAM_ALPHANUMEXT);
        $visibility = $this->normalise_visibility((string)($row['visibility'] ?? self::VISIBILITY_COURSE));
        $tagkey = clean_param((string)($row['tagkey'] ?? $row['tag'] ?? ''), PARAM_ALPHANUMEXT);

        return [
            'id' => max(0, (int)($row['id'] ?? 0)),
            'uuid' => (string)($row['uuid'] ?? ''),
            'tagkey' => $tagkey,
            'taglabel' => format_string((string)($row['taglabel'] ?? $row['label'] ?? $this->label_from_key($tagkey))),
            'severity' => $severity,
            'severitylabel' => $this->get_component_string('severity_' . $severity, $this->label_from_key($severity)),
            'reviewstate' => $reviewstate,
            'reviewstatelabel' => $this->get_component_string('reviewstate_' . $reviewstate, $this->label_from_key($reviewstate)),
            'visibility' => $visibility,
            'visibilitylabel' => $this->get_visibility_label($visibility),
            'description' => $this->format_html((string)($row['description'] ?? $row['summary'] ?? '')),
            'hasdescription' => trim(strip_tags((string)($row['description'] ?? $row['summary'] ?? ''))) !== '',
            'locator' => format_string((string)($row['locator'] ?? $row['locatorlabel'] ?? '')),
            'haslocator' => trim((string)($row['locator'] ?? $row['locatorlabel'] ?? '')) !== '',
            'culturalprotocol' => !empty($row['culturalprotocol']) || $visibility === self::VISIBILITY_RESTRICTED_CULTURAL,
            'restricted' => $this->visibility_is_restricted($visibility) || $severity === 'restricted',
        ];
    }

    /**
     * Normalise content review row.
     *
     * @param array<string, mixed>|stdClass $review Review row.
     * @return array<string, mixed>
     */
    private function normalise_content_review(array|stdClass $review): array {
        $row = (array)$review;

        $state = clean_param((string)($row['state'] ?? $row['reviewstate'] ?? 'pending_review'), PARAM_ALPHANUMEXT);
        $severity = clean_param((string)($row['severity'] ?? 'notice'), PARAM_ALPHANUMEXT);

        return [
            'id' => max(0, (int)($row['id'] ?? 0)),
            'markerid' => max(0, (int)($row['markerid'] ?? $row['contentmarkerid'] ?? 0)),
            'state' => $state,
            'statelabel' => $this->get_component_string('reviewstate_' . $state, $this->label_from_key($state)),
            'severity' => $severity,
            'severitylabel' => $this->get_component_string('severity_' . $severity, $this->label_from_key($severity)),
            'rationale' => $this->format_html((string)($row['rationale'] ?? '')),
            'hasrationale' => trim(strip_tags((string)($row['rationale'] ?? ''))) !== '',
            'reviewnote' => $this->format_html((string)($row['reviewnote'] ?? $row['note'] ?? '')),
            'hasreviewnote' => trim(strip_tags((string)($row['reviewnote'] ?? $row['note'] ?? ''))) !== '',
            'timecreated' => max(0, (int)($row['timecreated'] ?? 0)),
            'timemodified' => max(0, (int)($row['timemodified'] ?? 0)),
        ];
    }

    /**
     * Normalise revision row.
     *
     * @param array<string, mixed>|stdClass $revision Revision row.
     * @return array<string, mixed>
     */
    private function normalise_revision(array|stdClass $revision): array {
        $row = (array)$revision;

        $status = $this->normalise_status((string)($row['status'] ?? self::STATUS_DRAFT));

        return [
            'id' => max(0, (int)($row['id'] ?? 0)),
            'versionno' => max(1, (int)($row['versionno'] ?? 1)),
            'summary' => $this->format_html((string)($row['summary'] ?? '')),
            'hassummary' => trim(strip_tags((string)($row['summary'] ?? ''))) !== '',
            'reason' => $this->format_html((string)($row['reason'] ?? '')),
            'hasreason' => trim(strip_tags((string)($row['reason'] ?? ''))) !== '',
            'status' => $status,
            'statuslabel' => $this->get_status_label($status),
            'timecreated' => max(0, (int)($row['timecreated'] ?? 0)),
            'timemodified' => max(0, (int)($row['timemodified'] ?? 0)),
        ];
    }

    /**
     * Normalise export row.
     *
     * @param array<string, mixed>|stdClass $export Export row.
     * @return array<string, mixed>
     */
    private function normalise_export(array|stdClass $export): array {
        $row = (array)$export;

        $status = clean_param((string)($row['status'] ?? 'pending'), PARAM_ALPHANUMEXT);
        $format = clean_param((string)($row['exportformat'] ?? $row['format'] ?? 'json'), PARAM_ALPHANUMEXT);

        return [
            'id' => max(0, (int)($row['id'] ?? 0)),
            'title' => format_string((string)($row['title'] ?? $row['packagename'] ?? '')),
            'hastitle' => trim((string)($row['title'] ?? $row['packagename'] ?? '')) !== '',
            'status' => $status,
            'statuslabel' => $this->get_component_string('exportstatus_' . $status, $this->label_from_key($status)),
            'exportformat' => $format,
            'exportformatlabel' => strtoupper($format),
            'url' => $this->normalise_url($row['url'] ?? ''),
            'hasurl' => trim((string)($row['url'] ?? '')) !== '',
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
            'url' => $this->normalise_url($row['url'] ?? ''),
            'method' => $method,
            'primary' => !empty($row['primary']),
            'danger' => !empty($row['danger']),
            'disabled' => !empty($row['disabled']),
            'disabledreason' => format_string((string)($row['disabledreason'] ?? '')),
            'requiresummary' => !empty($row['requiresummary']),
            'requiresconfirmation' => !empty($row['requiresconfirmation']),
            'confirmmessage' => format_string((string)($row['confirmmessage'] ?? '')),
            'sesskey' => (string)($row['sesskey'] ?? sesskey()),
        ];
    }

    /**
     * Build proof rows.
     *
     * @return array<int, stdClass>
     */
    private function build_proof_rows(): array {
        $rows = [];

        foreach ($this->proofs as $proof) {
            $rows[] = (object)[
                'id' => $proof['id'],
                'prooftype' => $proof['prooftype'],
                'prooftypelabel' => $proof['prooftypelabel'],
                'title' => $proof['title'],
                'summary' => $proof['summary'],
                'hassummary' => $proof['hassummary'],
                'validationstate' => $proof['validationstate'],
                'validationlabel' => $proof['validationlabel'],
                'validationclass' => $this->get_css_class('validation', $proof['validationstate']),
                'visibility' => $proof['visibility'],
                'visibilitylabel' => $proof['visibilitylabel'],
                'visibilityclass' => $this->get_css_class('visibility', $proof['visibility']),
                'url' => $proof['url'],
                'hasurl' => $proof['hasurl'],
                'fileurl' => $proof['fileurl'],
                'hasfileurl' => $proof['hasfileurl'],
                'filename' => $proof['filename'],
                'hasfilename' => $proof['hasfilename'],
                'restricted' => $proof['restricted'],
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
            $rows[] = (object)[
                'id' => $media['id'],
                'uuid' => $media['uuid'],
                'title' => $media['title'],
                'description' => $media['description'],
                'hasdescription' => $media['hasdescription'],
                'mediatype' => $media['mediatype'],
                'mediatypelabel' => $media['mediatypelabel'],
                'mediatypeclass' => $this->get_css_class('media-type', $media['mediatype']),
                'mimetype' => $media['mimetype'],
                'hasmimetype' => $media['hasmimetype'],
                'status' => $media['status'],
                'statuslabel' => $media['statuslabel'],
                'statusclass' => $this->get_css_class('status', $media['status']),
                'visibility' => $media['visibility'],
                'visibilitylabel' => $media['visibilitylabel'],
                'visibilityclass' => $this->get_css_class('visibility', $media['visibility']),
                'audiencesuitability' => $media['audiencesuitability'],
                'audiencesuitabilitylabel' => $media['audiencesuitabilitylabel'],
                'audiencesuitabilityclass' => $this->get_css_class('audience-suitability', $media['audiencesuitability']),
                'url' => $media['url'],
                'hasurl' => $media['url'] !== '',
                'timecreated' => $media['timecreated'],
                'timecreatedlabel' => $media['timecreated'] > 0 ? userdate($media['timecreated']) : '',
                'timemodified' => $media['timemodified'],
                'timemodifiedlabel' => $media['timemodified'] > 0 ? userdate($media['timemodified']) : '',
                'restricted' => $media['restricted'],
                'culturalrestricted' => $media['culturalrestricted'],
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
            $rows[] = (object)[
                'id' => $marker['id'],
                'uuid' => $marker['uuid'],
                'tagkey' => $marker['tagkey'],
                'taglabel' => $marker['taglabel'],
                'severity' => $marker['severity'],
                'severitylabel' => $marker['severitylabel'],
                'severityclass' => $this->get_css_class('severity', $marker['severity']),
                'reviewstate' => $marker['reviewstate'],
                'reviewstatelabel' => $marker['reviewstatelabel'],
                'reviewstateclass' => $this->get_css_class('review-state', $marker['reviewstate']),
                'visibility' => $marker['visibility'],
                'visibilitylabel' => $marker['visibilitylabel'],
                'visibilityclass' => $this->get_css_class('visibility', $marker['visibility']),
                'description' => $marker['description'],
                'hasdescription' => $marker['hasdescription'],
                'locator' => $marker['locator'],
                'haslocator' => $marker['haslocator'],
                'culturalprotocol' => $marker['culturalprotocol'],
                'restricted' => $marker['restricted'],
            ];
        }

        return $rows;
    }

    /**
     * Build content review rows.
     *
     * @return array<int, stdClass>
     */
    private function build_content_review_rows(): array {
        $rows = [];

        foreach ($this->contentreviews as $review) {
            $rows[] = (object)[
                'id' => $review['id'],
                'markerid' => $review['markerid'],
                'state' => $review['state'],
                'statelabel' => $review['statelabel'],
                'stateclass' => $this->get_css_class('review-state', $review['state']),
                'severity' => $review['severity'],
                'severitylabel' => $review['severitylabel'],
                'severityclass' => $this->get_css_class('severity', $review['severity']),
                'rationale' => $review['rationale'],
                'hasrationale' => $review['hasrationale'],
                'reviewnote' => $review['reviewnote'],
                'hasreviewnote' => $review['hasreviewnote'],
                'timecreated' => $review['timecreated'],
                'timecreatedlabel' => $review['timecreated'] > 0 ? userdate($review['timecreated']) : '',
                'timemodified' => $review['timemodified'],
                'timemodifiedlabel' => $review['timemodified'] > 0 ? userdate($review['timemodified']) : '',
            ];
        }

        return $rows;
    }

    /**
     * Build revision rows.
     *
     * @return array<int, stdClass>
     */
    private function build_revision_rows(): array {
        $rows = [];

        foreach ($this->revisions as $revision) {
            $rows[] = (object)[
                'id' => $revision['id'],
                'versionno' => $revision['versionno'],
                'versionlabel' => $this->get_version_label($revision['versionno']),
                'summary' => $revision['summary'],
                'hassummary' => $revision['hassummary'],
                'reason' => $revision['reason'],
                'hasreason' => $revision['hasreason'],
                'status' => $revision['status'],
                'statuslabel' => $revision['statuslabel'],
                'statusclass' => $this->get_css_class('status', $revision['status']),
                'timecreated' => $revision['timecreated'],
                'timecreatedlabel' => $revision['timecreated'] > 0 ? userdate($revision['timecreated']) : '',
                'timemodified' => $revision['timemodified'],
                'timemodifiedlabel' => $revision['timemodified'] > 0 ? userdate($revision['timemodified']) : '',
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
            $rows[] = (object)[
                'id' => $export['id'],
                'title' => $export['title'],
                'hastitle' => $export['hastitle'],
                'status' => $export['status'],
                'statuslabel' => $export['statuslabel'],
                'statusclass' => $this->get_css_class('status', $export['status']),
                'exportformat' => $export['exportformat'],
                'exportformatlabel' => $export['exportformatlabel'],
                'url' => $export['url'],
                'hasurl' => $export['hasurl'],
                'timecreated' => $export['timecreated'],
                'timecreatedlabel' => $export['timecreated'] > 0 ? userdate($export['timecreated']) : '',
                'timemodified' => $export['timemodified'],
                'timemodifiedlabel' => $export['timemodified'] > 0 ? userdate($export['timemodified']) : '',
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
                'hasdisabledreason' => $action['disabledreason'] !== '',
                'requiresummary' => $action['requiresummary'],
                'requiresconfirmation' => $action['requiresconfirmation'],
                'confirmmessage' => $action['confirmmessage'],
                'hasconfirmmessage' => $action['confirmmessage'] !== '',
                'sesskey' => $action['sesskey'],
                'itemid' => $this->item['id'],
            ];
        }

        return $rows;
    }

    /**
     * Build warning rows.
     *
     * @return array<int, stdClass>
     */
    private function build_warning_rows(): array {
        $rows = [];

        foreach ($this->warnings as $warning) {
            $rows[] = (object)[
                'message' => $warning['message'],
                'severity' => $warning['severity'],
                'class' => 'alert-' . $this->get_warning_class($warning['severity']),
            ];
        }

        return $rows;
    }

    /**
     * Build badge rows.
     *
     * @return array<int, stdClass>
     */
    private function build_badge_rows(): array {
        $badges = [];

        if ($this->is_restricted()) {
            $badges[] = (object)[
                'key' => 'restricted',
                'label' => $this->get_component_string('badge:restricted', 'Restricted'),
                'class' => 'badge-warning',
            ];
        }

        if ($this->is_cultural_restricted()) {
            $badges[] = (object)[
                'key' => 'restricted_cultural',
                'label' => $this->get_component_string('badge:restrictedcultural', 'Cultural protocol'),
                'class' => 'badge-warning',
            ];
        }

        if ($this->is_validated()) {
            $badges[] = (object)[
                'key' => 'validated',
                'label' => $this->get_component_string('badge:validated', 'Validated'),
                'class' => 'badge-success',
            ];
        }

        if ($this->is_contested()) {
            $badges[] = (object)[
                'key' => 'contested',
                'label' => $this->get_component_string('badge:contested', 'Contested'),
                'class' => 'badge-warning',
            ];
        }

        if ($this->is_invalidated()) {
            $badges[] = (object)[
                'key' => 'invalidated',
                'label' => $this->get_component_string('badge:invalidated', 'Invalidated'),
                'class' => 'badge-danger',
            ];
        }

        if ($this->item['provenance'] === self::PROVENANCE_AI_ASSISTED) {
            $badges[] = (object)[
                'key' => 'ai_assisted',
                'label' => $this->get_component_string('badge:aiassisted', 'AI assisted'),
                'class' => 'badge-info',
            ];
        }

        if (!empty($this->media)) {
            $badges[] = (object)[
                'key' => 'has_media',
                'label' => $this->get_component_string('badge:hasmedia', 'Media'),
                'class' => 'badge-secondary',
            ];
        }

        if (!empty($this->contentmarkers)) {
            $badges[] = (object)[
                'key' => 'has_content_advisories',
                'label' => $this->get_component_string('badge:hascontentadvisories', 'Content advisories'),
                'class' => 'badge-warning',
            ];
        }

        return $badges;
    }

    /**
     * Normalise warning rows.
     *
     * @param array<int, array<string, mixed>|stdClass|string> $warnings Warning data.
     * @return array<int, array<string, string>>
     */
    private function normalise_warnings(array $warnings): array {
        $rows = [];

        foreach ($warnings as $warning) {
            if (is_string($warning)) {
                $message = trim($warning);
                $severity = 'warning';
            } else {
                $row = (array)$warning;
                $message = trim((string)($row['message'] ?? ''));
                $severity = clean_param((string)($row['severity'] ?? 'warning'), PARAM_ALPHANUMEXT);
            }

            if ($message === '') {
                continue;
            }

            $rows[] = [
                'message' => format_string($message),
                'severity' => $severity,
            ];
        }

        return $rows;
    }

    /**
     * Build archive item URL.
     *
     * @return string
     */
    private function build_item_url(): string {
        if ($this->item['id'] <= 0) {
            return '';
        }

        if ($this->item['cmid'] > 0) {
            return (new moodle_url('/mod/uckkarchive/item.php', [
                'id' => $this->item['cmid'],
                'itemid' => $this->item['id'],
            ]))->out(false);
        }

        return (new moodle_url('/mod/uckkarchive/item.php', [
            'itemid' => $this->item['id'],
        ]))->out(false);
    }

    /**
     * Return notice text.
     *
     * @return string
     */
    private function get_notice(): string {
        if ($this->item['provenance'] === self::PROVENANCE_AI_ASSISTED) {
            return $this->get_component_string('notice:aiassisted', 'This archive item includes AI-assisted provenance.');
        }

        if ($this->is_cultural_restricted()) {
            return $this->get_component_string(
                'notice:restrictedcultural',
                'This archive item includes cultural protocol restrictions.'
            );
        }

        if ($this->is_restricted()) {
            return $this->get_component_string('notice:restricted', 'This archive item has restricted visibility.');
        }

        return $this->get_component_string('notice:archiveitem', '');
    }

    /**
     * Whether item is validated.
     *
     * @return bool
     */
    private function is_validated(): bool {
        return in_array($this->item['validationstate'], [
            self::VALIDATION_HUMAN_REVIEWED,
            self::VALIDATION_VERIFIED,
            self::VALIDATION_ARCHIVED,
        ], true) || in_array($this->item['status'], [
            self::STATUS_VALIDATED,
            self::STATUS_PUBLISHED,
            self::STATUS_ARCHIVED,
        ], true);
    }

    /**
     * Whether item is contested.
     *
     * @return bool
     */
    private function is_contested(): bool {
        return $this->item['status'] === self::STATUS_CONTESTED
            || $this->item['validationstate'] === self::VALIDATION_CONTESTED;
    }

    /**
     * Whether item is invalidated.
     *
     * @return bool
     */
    private function is_invalidated(): bool {
        return $this->item['status'] === self::STATUS_INVALIDATED
            || $this->item['validationstate'] === self::VALIDATION_INVALIDATED;
    }

    /**
     * Whether item is restricted.
     *
     * @return bool
     */
    private function is_restricted(): bool {
        return $this->item['status'] === self::STATUS_RESTRICTED
            || $this->visibility_is_restricted($this->item['visibility']);
    }

    /**
     * Whether item is culturally restricted.
     *
     * @return bool
     */
    private function is_cultural_restricted(): bool {
        if ($this->item['visibility'] === self::VISIBILITY_RESTRICTED_CULTURAL) {
            return true;
        }

        foreach ($this->contentmarkers as $marker) {
            if (!empty($marker['culturalprotocol'])) {
                return true;
            }
        }

        foreach ($this->media as $media) {
            if (!empty($media['culturalrestricted'])) {
                return true;
            }
        }

        return false;
    }

    /**
     * Get allowed item types.
     *
     * @return string[]
     */
    private function get_allowed_item_types(): array {
        return [
            self::TYPE_PROOF,
            self::TYPE_DECISION,
            self::TYPE_COURSE_WORK,
            self::TYPE_CHALLENGE_RESULT,
            self::TYPE_ASSEMBLY_MINUTES,
            self::TYPE_INTEGRITY_CASE_SUMMARY,
            self::TYPE_KRISTAL,
            self::TYPE_REFLECTION,
            self::TYPE_PORTFOLIO_ITEM,
            self::TYPE_VERSION_RECORD,
        ];
    }

    /**
     * Get allowed statuses.
     *
     * @return string[]
     */
    private function get_allowed_statuses(): array {
        return [
            self::STATUS_DRAFT,
            self::STATUS_SUBMITTED,
            self::STATUS_UNDER_REVIEW,
            self::STATUS_ACTIVE,
            self::STATUS_VALIDATED,
            self::STATUS_PUBLISHED,
            self::STATUS_RESTRICTED,
            self::STATUS_CONTESTED,
            self::STATUS_INVALIDATED,
            self::STATUS_SUPERSEDED,
            self::STATUS_ARCHIVED,
            self::STATUS_HIDDEN,
            self::STATUS_PENDING,
            self::STATUS_PENDING_REVIEW,
            self::STATUS_REJECTED,
            self::STATUS_CORRECTION_REQUIRED,
            self::STATUS_CLOSED,
            self::STATUS_CANCELLED,
        ];
    }

    /**
     * Get allowed validation states.
     *
     * @return string[]
     */
    private function get_allowed_validation_states(): array {
        return [
            self::VALIDATION_UNVERIFIED,
            self::VALIDATION_HUMAN_REVIEWED,
            self::VALIDATION_VERIFIED,
            self::VALIDATION_CONTESTED,
            self::VALIDATION_INVALIDATED,
            self::VALIDATION_ARCHIVED,
        ];
    }

    /**
     * Get allowed visibilities.
     *
     * @return string[]
     */
    private function get_allowed_visibilities(): array {
        return [
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
    }

    /**
     * Get allowed provenance sources.
     *
     * @return string[]
     */
    private function get_allowed_provenance_sources(): array {
        return [
            self::PROVENANCE_HUMAN,
            self::PROVENANCE_AI_ASSISTED,
            self::PROVENANCE_IMPORTED,
            self::PROVENANCE_SYSTEM,
            self::PROVENANCE_ARCHIVE,
            self::PROVENANCE_ASSEMBLY,
            self::PROVENANCE_CHALLENGE,
            self::PROVENANCE_INTEGRITY,
            self::PROVENANCE_MEDIA,
            self::PROVENANCE_EXTERNAL_WORK,
            self::PROVENANCE_CONTENT_REVIEW,
        ];
    }

    /**
     * Normalise item type.
     *
     * @param string $itemtype Raw item type.
     * @return string
     */
    private function normalise_item_type(string $itemtype): string {
        $itemtype = clean_param(strtolower(trim($itemtype)), PARAM_ALPHANUMEXT);

        return in_array($itemtype, $this->get_allowed_item_types(), true)
            ? $itemtype
            : self::TYPE_PROOF;
    }

    /**
     * Normalise status.
     *
     * @param string $status Raw status.
     * @return string
     */
    private function normalise_status(string $status): string {
        $status = clean_param(strtolower(trim($status)), PARAM_ALPHANUMEXT);

        if ($status === self::STATUS_PENDING_REVIEW) {
            return self::STATUS_UNDER_REVIEW;
        }

        return in_array($status, $this->get_allowed_statuses(), true)
            ? $status
            : self::STATUS_DRAFT;
    }

    /**
     * Normalise validation state.
     *
     * @param string $validationstate Raw validation state.
     * @return string
     */
    private function normalise_validation_state(string $validationstate): string {
        $validationstate = clean_param(strtolower(trim($validationstate)), PARAM_ALPHANUMEXT);

        return in_array($validationstate, $this->get_allowed_validation_states(), true)
            ? $validationstate
            : self::VALIDATION_UNVERIFIED;
    }

    /**
     * Normalise visibility.
     *
     * @param string $visibility Raw visibility.
     * @return string
     */
    private function normalise_visibility(string $visibility): string {
        $visibility = clean_param(strtolower(trim($visibility)), PARAM_ALPHANUMEXT);

        if ($visibility === 'institutional') {
            $visibility = self::VISIBILITY_INSTITUTION;
        }

        return in_array($visibility, $this->get_allowed_visibilities(), true)
            ? $visibility
            : self::VISIBILITY_COURSE;
    }

    /**
     * Normalise provenance.
     *
     * @param string $provenance Raw provenance.
     * @return string
     */
    private function normalise_provenance(string $provenance): string {
        $provenance = clean_param(strtolower(trim($provenance)), PARAM_ALPHANUMEXT);

        return in_array($provenance, $this->get_allowed_provenance_sources(), true)
            ? $provenance
            : self::PROVENANCE_HUMAN;
    }

    /**
     * Normalise URL.
     *
     * @param mixed $url Raw URL.
     * @return string
     */
    private function normalise_url(mixed $url): string {
        if ($url instanceof moodle_url) {
            return $url->out(false);
        }

        if (is_string($url) && trim($url) !== '') {
            try {
                return (new moodle_url($url))->out(false);
            } catch (\moodle_exception $exception) {
                return clean_param($url, PARAM_URL);
            }
        }

        return '';
    }

    /**
     * Get item type label.
     *
     * @param string $itemtype Item type.
     * @return string
     */
    private function get_item_type_label(string $itemtype): string {
        return $this->get_component_string('itemtype:' . $itemtype, $this->label_from_key($itemtype));
    }

    /**
     * Get proof type label.
     *
     * @param string $prooftype Proof type.
     * @return string
     */
    private function get_proof_type_label(string $prooftype): string {
        return $this->get_component_string('prooftype:' . $prooftype, $this->label_from_key($prooftype));
    }

    /**
     * Get status label.
     *
     * @param string $status Status.
     * @return string
     */
    private function get_status_label(string $status): string {
        return $this->get_component_string('status:' . $status, $this->label_from_key($status));
    }

    /**
     * Get validation label.
     *
     * @param string $validationstate Validation state.
     * @return string
     */
    private function get_validation_label(string $validationstate): string {
        return $this->get_component_string('validation:' . $validationstate, $this->label_from_key($validationstate));
    }

    /**
     * Get visibility label.
     *
     * @param string $visibility Visibility.
     * @return string
     */
    private function get_visibility_label(string $visibility): string {
        return $this->get_component_string('visibility:' . $visibility, $this->label_from_key($visibility));
    }

    /**
     * Get provenance label.
     *
     * @param string $provenance Provenance.
     * @return string
     */
    private function get_provenance_label(string $provenance): string {
        return $this->get_component_string('provenance:' . $provenance, $this->label_from_key($provenance));
    }

    /**
     * Get action label.
     *
     * @param string $action Action key.
     * @return string
     */
    private function get_action_label(string $action): string {
        return $this->get_component_string('action:' . $action, get_string('view'));
    }

    /**
     * Get version label.
     *
     * @param int $version Version number.
     * @return string
     */
    private function get_version_label(int $version): string {
        if (get_string_manager()->string_exists('versionx', 'uckkarchive')) {
            return get_string('versionx', 'uckkarchive', $version);
        }

        if (get_string_manager()->string_exists('versionnumber', 'uckkarchive')) {
            return get_string('versionnumber', 'uckkarchive', $version);
        }

        return 'Version ' . $version;
    }

    /**
     * Get component string if it exists, otherwise fallback.
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
     * Build CSS class.
     *
     * @param string $prefix Prefix.
     * @param string $value Value.
     * @return string
     */
    private function get_css_class(string $prefix, string $value): string {
        return $prefix . '-' . str_replace('_', '-', clean_param(strtolower(trim($value)), PARAM_ALPHANUMEXT));
    }

    /**
     * Map warning severity to Bootstrap alert class suffix.
     *
     * @param string $severity Severity key.
     * @return string
     */
    private function get_warning_class(string $severity): string {
        return match ($severity) {
            'danger', 'error', 'invalidated' => 'danger',
            'info', 'notice' => 'info',
            'success', 'clear' => 'success',
            default => 'warning',
        };
    }

    /**
     * Format HTML safely.
     *
     * @param string $text Raw text.
     * @return string
     */
    private function format_html(string $text): string {
        $text = trim($text);

        if ($text === '') {
            return '';
        }

        return format_text($text, FORMAT_HTML, ['trusted' => false, 'para' => false]);
    }

    /**
     * Return readable label from a key.
     *
     * @param string $key Key.
     * @return string
     */
    private function label_from_key(string $key): string {
        $key = trim($key);

        if ($key === '') {
            return '';
        }

        return ucfirst(str_replace('_', ' ', $key));
    }

    /**
     * Return whether visibility is restricted.
     *
     * @param string $visibility Visibility.
     * @return bool
     */
    private function visibility_is_restricted(string $visibility): bool {
        return in_array($visibility, [
            self::VISIBILITY_PRIVATE,
            self::VISIBILITY_RESTRICTED,
            self::VISIBILITY_RESTRICTED_INTEGRITY,
            self::VISIBILITY_RESTRICTED_CULTURAL,
            self::VISIBILITY_HIDDEN,
        ], true);
    }

    /**
     * Return whether constructor second argument is an options array.
     *
     * @param array<int|string, mixed> $value Value.
     * @return bool
     */
    private function looks_like_options(array $value): bool {
        foreach ([
            'course',
            'cm',
            'context',
            'proofs',
            'media',
            'contentmarkers',
            'contentreviews',
            'revisions',
            'exports',
            'actions',
            'warnings',
            'canviewrestricted',
            'canviewmedia',
            'canviewadvisories',
        ] as $key) {
            if (array_key_exists($key, $value)) {
                return true;
            }
        }

        return false;
    }

    /**
     * Convert value to list.
     *
     * @param mixed $value Value.
     * @return array<int, mixed>
     */
    private function as_list(mixed $value): array {
        if ($value instanceof stdClass) {
            return [(array)$value];
        }

        if (!is_array($value)) {
            return [];
        }

        if ($value === []) {
            return [];
        }

        if (array_is_list($value)) {
            return $value;
        }

        return array_values($value);
    }
}
