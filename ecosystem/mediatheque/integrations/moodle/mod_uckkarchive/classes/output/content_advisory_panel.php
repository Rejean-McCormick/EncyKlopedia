<?php
// This file is part of Moodle - https://moodle.org/
//
// Moodle is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// any later version.

/**
 * Content advisory panel output object.
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
 * Renderable content advisory panel.
 *
 * This class prepares already-authorized content advisory data for Mustache.
 * It does not decide access, grant permissions, approve reviews, change
 * cultural protocol state, update markers, or expose restricted locator data
 * that has not already been filtered by the caller.
 */
final class content_advisory_panel implements renderable, templatable {
    /** Target type: media. */
    public const TARGET_MEDIA = 'media';

    /** Target type: external work. */
    public const TARGET_EXTERNAL_WORK = 'external_work';

    /** Target type: archive item. */
    public const TARGET_ARCHIVE_ITEM = 'archive_item';

    /** Review state: draft. */
    public const REVIEW_DRAFT = 'draft';

    /** Review state: pending review. */
    public const REVIEW_PENDING = 'pending_review';

    /** Review state: reviewed. */
    public const REVIEW_REVIEWED = 'reviewed';

    /** Review state: approved. */
    public const REVIEW_APPROVED = 'approved';

    /** Review state: contested. */
    public const REVIEW_CONTESTED = 'contested';

    /** Review state: retired. */
    public const REVIEW_RETIRED = 'retired';

    /** Severity: notice. */
    public const SEVERITY_NOTICE = 'notice';

    /** Severity: moderate. */
    public const SEVERITY_MODERATE = 'moderate';

    /** Severity: strong. */
    public const SEVERITY_STRONG = 'strong';

    /** Severity: restricted. */
    public const SEVERITY_RESTRICTED = 'restricted';

    /** Audience suitability: general. */
    public const SUITABILITY_GENERAL = 'general';

    /** Audience suitability: guided. */
    public const SUITABILITY_GUIDED = 'guided';

    /** Audience suitability: mature. */
    public const SUITABILITY_MATURE = 'mature';

    /** Audience suitability: restricted. */
    public const SUITABILITY_RESTRICTED = 'restricted';

    /** Audience suitability: restricted cultural. */
    public const SUITABILITY_RESTRICTED_CULTURAL = 'restricted_cultural';

    /** Audience suitability: restricted integrity. */
    public const SUITABILITY_RESTRICTED_INTEGRITY = 'restricted_integrity';

    /** Audience suitability: staff only. */
    public const SUITABILITY_STAFF_ONLY = 'staff_only';

    /** Visibility: private. */
    public const VISIBILITY_PRIVATE = 'private';

    /** Visibility: course. */
    public const VISIBILITY_COURSE = 'course';

    /** Visibility: public. */
    public const VISIBILITY_PUBLIC = 'public';

    /** Visibility: restricted. */
    public const VISIBILITY_RESTRICTED = 'restricted';

    /** Visibility: restricted cultural. */
    public const VISIBILITY_RESTRICTED_CULTURAL = 'restricted_cultural';

    /** Visibility: restricted integrity. */
    public const VISIBILITY_RESTRICTED_INTEGRITY = 'restricted_integrity';

    /** @var int Archive instance id. */
    private int $archiveid;

    /** @var int Course module id. */
    private int $cmid;

    /** @var int Context id. */
    private int $contextid;

    /** @var string Target type. */
    private string $targettype;

    /** @var int Target id. */
    private int $targetid;

    /** @var string Target display title. */
    private string $targettitle;

    /** @var array<int, array<string, mixed>> Content marker records. */
    private array $markers;

    /** @var array<int, array<string, mixed>> Content review records. */
    private array $reviews;

    /** @var array<int, array<string, mixed>> Content tag records. */
    private array $tags;

    /** @var array<int, array<string, mixed>> Content tag-set records. */
    private array $tagsets;

    /** @var array<int, array<string, mixed>> External work records. */
    private array $externalworks;

    /** @var array<string, bool> Permission flags already determined by service/policy layer. */
    private array $permissions;

    /** @var array<int, array<string, mixed>> UI actions. */
    private array $actions;

    /** @var array<string, mixed> Summary data. */
    private array $summary;

    /**
     * Constructor.
     *
     * @param int $archiveid Archive instance id.
     * @param int $cmid Course module id.
     * @param int $contextid Context id.
     * @param string $targettype Target type.
     * @param int $targetid Target id.
     * @param string $targettitle Target title.
     * @param array<int, mixed> $markers Content markers.
     * @param array<int, mixed> $reviews Content reviews.
     * @param array<int, mixed> $tags Content tags.
     * @param array<int, mixed> $tagsets Content tag sets.
     * @param array<int, mixed> $externalworks External work references.
     * @param array<string, mixed> $permissions Permission flags.
     * @param array<int, mixed> $actions UI actions.
     * @param array<string, mixed> $summary Summary overrides.
     */
    public function __construct(
        int $archiveid,
        int $cmid,
        int $contextid,
        string $targettype = '',
        int $targetid = 0,
        string $targettitle = '',
        array $markers = [],
        array $reviews = [],
        array $tags = [],
        array $tagsets = [],
        array $externalworks = [],
        array $permissions = [],
        array $actions = [],
        array $summary = []
    ) {
        $this->archiveid = max(0, $archiveid);
        $this->cmid = max(0, $cmid);
        $this->contextid = max(0, $contextid);
        $this->targettype = $this->normalise_target_type($targettype);
        $this->targetid = max(0, $targetid);
        $this->targettitle = format_string($targettitle);

        $this->markers = array_values(array_map([$this, 'normalise_marker'], $markers));
        $this->reviews = array_values(array_map([$this, 'normalise_review'], $reviews));
        $this->tags = array_values(array_map([$this, 'normalise_tag'], $tags));
        $this->tagsets = array_values(array_map([$this, 'normalise_tag_set'], $tagsets));
        $this->externalworks = array_values(array_map([$this, 'normalise_external_work'], $externalworks));
        $this->permissions = $this->normalise_permissions($permissions);
        $this->actions = array_values(array_map([$this, 'normalise_action'], $actions));
        $this->summary = $summary;
    }

    /**
     * Export context for Mustache.
     *
     * @param renderer_base $output Renderer.
     * @return stdClass
     */
    public function export_for_template(renderer_base $output): stdClass {
        $markerlist = $this->build_marker_list();
        $severitysummary = $this->build_severity_summary($markerlist);
        $reviewsummary = $this->build_review_summary($markerlist);

        $manageurl = new moodle_url('/mod/uckkarchive/media.php', [
            'id' => $this->cmid,
            'targettype' => $this->targettype,
            'targetid' => $this->targetid,
            'panel' => 'contentadvisory',
        ]);

        $data = new stdClass();
        $data->archiveid = $this->archiveid;
        $data->cmid = $this->cmid;
        $data->contextid = $this->contextid;

        $data->targettype = $this->targettype;
        $data->targettypelabel = $this->get_target_type_label($this->targettype);
        $data->targettypeclass = $this->css_class('target-type', $this->targettype);
        $data->targetid = $this->targetid;
        $data->targettitle = $this->targettitle;
        $data->hastargettitle = $this->targettitle !== '';

        $data->heading = $this->get_component_string('contentadvisorypanel', 'Content advisory');
        $data->description = $this->get_component_string(
            'contentadvisorypanel_desc',
            'Content advisories, cultural protocol notes, and audience suitability information.'
        );

        $data->manageurl = $manageurl->out(false);

        $data->markers = $markerlist;
        $data->hasmarkers = !empty($markerlist);
        $data->markercount = count($markerlist);

        $data->reviews = $this->build_review_list();
        $data->hasreviews = !empty($data->reviews);
        $data->reviewcount = count($data->reviews);

        $data->tags = $this->build_tag_list();
        $data->hastags = !empty($data->tags);
        $data->tagcount = count($data->tags);

        $data->tagsets = $this->build_tag_set_list();
        $data->hastagsets = !empty($data->tagsets);
        $data->tagsetcount = count($data->tagsets);

        $data->externalworks = $this->build_external_work_list();
        $data->hasexternalworks = !empty($data->externalworks);
        $data->externalworkcount = count($data->externalworks);

        $data->severitysummary = $severitysummary;
        $data->hasseveritysummary = !empty($severitysummary);

        $data->reviewsummary = $reviewsummary;
        $data->hasreviewsummary = !empty($reviewsummary);

        $data->highestseverity = $this->highest_severity($markerlist);
        $data->highestseveritylabel = $this->get_severity_label($data->highestseverity);
        $data->highestseverityclass = $this->css_class('severity', $data->highestseverity);

        $data->hassensitivecontent = $this->has_sensitive_content($markerlist);
        $data->hasrestrictedcontent = $this->has_restricted_content($markerlist);
        $data->hasculturalprotocol = $this->has_cultural_protocol($markerlist);
        $data->haspendingreview = $this->has_review_state($markerlist, self::REVIEW_PENDING);
        $data->hascontestedreview = $this->has_review_state($markerlist, self::REVIEW_CONTESTED);
        $data->hasapprovedreview = $this->has_review_state($markerlist, self::REVIEW_APPROVED);

        $data->emptytitle = $this->get_component_string('nocontentadvisories', 'No content advisories');
        $data->emptydescription = $this->get_component_string(
            'nocontentadvisories_desc',
            'No advisory markers are available for this record.'
        );

        $data->canview = $this->permissions['canview'];
        $data->canmanage = $this->permissions['canmanage'];
        $data->canreview = $this->permissions['canreview'];
        $data->canedit = $this->permissions['canedit'];
        $data->candelete = $this->permissions['candelete'];
        $data->canexport = $this->permissions['canexport'];
        $data->canviewrestricted = $this->permissions['canviewrestricted'];
        $data->canviewcultural = $this->permissions['canviewcultural'];

        $data->actions = $this->actions;
        $data->hasactions = !empty($this->actions);

        $data->summary = $this->build_summary($markerlist);
        $data->warnings = $this->build_warnings($markerlist);
        $data->haswarnings = !empty($data->warnings);

        return $data;
    }

    /**
     * Build marker list.
     *
     * @return array<int, array<string, mixed>>
     */
    private function build_marker_list(): array {
        $items = [];

        foreach ($this->markers as $marker) {
            $severity = $this->normalise_severity((string)$marker['severity']);
            $reviewstate = $this->normalise_review_state((string)$marker['reviewstate']);
            $suitability = $this->normalise_suitability((string)$marker['audiencesuitability']);
            $visibility = $this->normalise_visibility((string)$marker['visibility']);

            $marker['severity'] = $severity;
            $marker['severitylabel'] = $this->get_severity_label($severity);
            $marker['severityclass'] = $this->css_class('severity', $severity);

            $marker['reviewstate'] = $reviewstate;
            $marker['reviewstatelabel'] = $this->get_review_state_label($reviewstate);
            $marker['reviewstateclass'] = $this->css_class('review-state', $reviewstate);

            $marker['audiencesuitability'] = $suitability;
            $marker['audiencesuitabilitylabel'] = $this->get_suitability_label($suitability);
            $marker['audiencesuitabilityclass'] = $this->css_class('audience-suitability', $suitability);

            $marker['visibility'] = $visibility;
            $marker['visibilitylabel'] = $this->get_visibility_label($visibility);
            $marker['visibilityclass'] = $this->css_class('visibility', $visibility);

            $marker['targettypelabel'] = $this->get_target_type_label((string)$marker['targettype']);
            $marker['locatortypelabel'] = $this->get_locator_type_label((string)$marker['locatortype']);
            $marker['haslocator'] = $marker['locatorlabel'] !== '' ||
                $marker['locatorstart'] !== '' ||
                $marker['locatorend'] !== '';

            $marker['hasdescription'] = $marker['description'] !== '';
            $marker['hasnote'] = $marker['note'] !== '';
            $marker['hastaglabel'] = $marker['taglabel'] !== '';
            $marker['hastagcategory'] = $marker['tagcategory'] !== '';

            $marker['isnotice'] = $severity === self::SEVERITY_NOTICE;
            $marker['ismoderate'] = $severity === self::SEVERITY_MODERATE;
            $marker['isstrong'] = $severity === self::SEVERITY_STRONG;
            $marker['isrestrictedseverity'] = $severity === self::SEVERITY_RESTRICTED;

            $marker['isapproved'] = $reviewstate === self::REVIEW_APPROVED;
            $marker['ispending'] = $reviewstate === self::REVIEW_PENDING;
            $marker['iscontested'] = $reviewstate === self::REVIEW_CONTESTED;
            $marker['isretired'] = $reviewstate === self::REVIEW_RETIRED;

            $marker['isrestricted'] = $this->is_restricted_visibility($visibility) ||
                $severity === self::SEVERITY_RESTRICTED ||
                !empty($marker['restricted']);

            $marker['isculturalprotocol'] = !empty($marker['culturalprotocol']) ||
                $visibility === self::VISIBILITY_RESTRICTED_CULTURAL ||
                $suitability === self::SUITABILITY_RESTRICTED_CULTURAL;

            $marker['requirescontext'] = !empty($marker['requirescontext']);
            $marker['isredacted'] = !empty($marker['redacted']);

            $items[] = $marker;
        }

        return $items;
    }

    /**
     * Build review list.
     *
     * @return array<int, array<string, mixed>>
     */
    private function build_review_list(): array {
        $items = [];

        foreach ($this->reviews as $review) {
            $state = $this->normalise_review_state((string)$review['state']);
            $severity = $this->normalise_severity((string)$review['severity']);
            $suitability = $this->normalise_suitability((string)$review['audiencesuitability']);

            $review['state'] = $state;
            $review['statelabel'] = $this->get_review_state_label($state);
            $review['stateclass'] = $this->css_class('review-state', $state);

            $review['severity'] = $severity;
            $review['severitylabel'] = $this->get_severity_label($severity);
            $review['severityclass'] = $this->css_class('severity', $severity);

            $review['audiencesuitability'] = $suitability;
            $review['audiencesuitabilitylabel'] = $this->get_suitability_label($suitability);
            $review['audiencesuitabilityclass'] = $this->css_class('audience-suitability', $suitability);

            $review['timecreatedlabel'] = $review['timecreated'] > 0 ? userdate($review['timecreated']) : '';
            $review['timemodifiedlabel'] = $review['timemodified'] > 0 ? userdate($review['timemodified']) : '';

            $review['hasrationale'] = $review['rationale'] !== '';
            $review['hasreviewnote'] = $review['reviewnote'] !== '';
            $review['hasmetadata'] = $review['metadatajson'] !== '{}';

            $items[] = $review;
        }

        return $items;
    }

    /**
     * Build tag list.
     *
     * @return array<int, array<string, mixed>>
     */
    private function build_tag_list(): array {
        $items = [];

        foreach ($this->tags as $tag) {
            $severity = $this->normalise_severity((string)$tag['defaultseverity']);
            $suitability = $this->normalise_suitability((string)$tag['defaultaudiencesuitability']);

            $tag['defaultseverity'] = $severity;
            $tag['defaultseveritylabel'] = $this->get_severity_label($severity);
            $tag['defaultseverityclass'] = $this->css_class('severity', $severity);

            $tag['defaultaudiencesuitability'] = $suitability;
            $tag['defaultaudiencesuitabilitylabel'] = $this->get_suitability_label($suitability);
            $tag['defaultaudiencesuitabilityclass'] = $this->css_class('audience-suitability', $suitability);

            $tag['hasdescription'] = $tag['description'] !== '';
            $tag['iscultural'] = !empty($tag['iscultural']);
            $tag['restrictsbydefault'] = !empty($tag['restrictsbydefault']);
            $tag['requiresreview'] = !empty($tag['requiresreview']);

            $items[] = $tag;
        }

        return $items;
    }

    /**
     * Build tag-set list.
     *
     * @return array<int, array<string, mixed>>
     */
    private function build_tag_set_list(): array {
        $items = [];

        foreach ($this->tagsets as $tagset) {
            $tagset['hasdescription'] = $tagset['description'] !== '';
            $tagset['hasversion'] = $tagset['version'] !== '';
            $tagset['tagcountlabel'] = (string)$tagset['tagcount'];
            $tagset['statusclass'] = $this->css_class('tag-set-status', (string)$tagset['status']);

            $items[] = $tagset;
        }

        return $items;
    }

    /**
     * Build external work list.
     *
     * @return array<int, array<string, mixed>>
     */
    private function build_external_work_list(): array {
        $items = [];

        foreach ($this->externalworks as $work) {
            $work['worktypelabel'] = $this->get_component_string(
                'externalworktype_' . $work['worktype'],
                $work['worktype']
            );
            $work['worktypeclass'] = $this->css_class('external-work-type', $work['worktype']);
            $work['hascreator'] = $work['creator'] !== '';
            $work['haspublicationyear'] = $work['publicationyear'] > 0;
            $work['hassourceurl'] = $work['sourceurl'] !== '';
            $work['hascitation'] = $work['citation'] !== '';

            $items[] = $work;
        }

        return $items;
    }

    /**
     * Build summary data.
     *
     * @param array<int, array<string, mixed>> $markers Marker list.
     * @return array<string, mixed>
     */
    private function build_summary(array $markers): array {
        $summary = [
            'markercount' => count($markers),
            'reviewcount' => count($this->reviews),
            'tagcount' => count($this->tags),
            'externalworkcount' => count($this->externalworks),
            'highestseverity' => $this->highest_severity($markers),
            'hasrestrictedcontent' => $this->has_restricted_content($markers),
            'hasculturalprotocol' => $this->has_cultural_protocol($markers),
            'haspendingreview' => $this->has_review_state($markers, self::REVIEW_PENDING),
            'hascontestedreview' => $this->has_review_state($markers, self::REVIEW_CONTESTED),
            'hasapprovedreview' => $this->has_review_state($markers, self::REVIEW_APPROVED),
        ];

        foreach ($this->summary as $key => $value) {
            $summary[clean_param((string)$key, PARAM_ALPHANUMEXT)] = $value;
        }

        $summary['highestseveritylabel'] = $this->get_severity_label((string)$summary['highestseverity']);
        $summary['highestseverityclass'] = $this->css_class('severity', (string)$summary['highestseverity']);

        return $summary;
    }

    /**
     * Build warning badges for the panel header.
     *
     * @param array<int, array<string, mixed>> $markers Marker list.
     * @return array<int, array<string, mixed>>
     */
    private function build_warnings(array $markers): array {
        $warnings = [];

        if ($this->has_restricted_content($markers)) {
            $warnings[] = [
                'type' => 'restricted',
                'label' => $this->get_component_string('restrictedcontent', 'Restricted content'),
                'class' => 'warning-restricted',
            ];
        }

        if ($this->has_cultural_protocol($markers)) {
            $warnings[] = [
                'type' => 'cultural_protocol',
                'label' => $this->get_component_string('culturalprotocol', 'Cultural protocol'),
                'class' => 'warning-cultural-protocol',
            ];
        }

        if ($this->has_review_state($markers, self::REVIEW_PENDING)) {
            $warnings[] = [
                'type' => 'pending_review',
                'label' => $this->get_component_string('pendingreview', 'Pending review'),
                'class' => 'warning-pending-review',
            ];
        }

        if ($this->has_review_state($markers, self::REVIEW_CONTESTED)) {
            $warnings[] = [
                'type' => 'contested',
                'label' => $this->get_component_string('contestedreview', 'Contested review'),
                'class' => 'warning-contested',
            ];
        }

        return $warnings;
    }

    /**
     * Build severity summary.
     *
     * @param array<int, array<string, mixed>> $markers Marker list.
     * @return array<int, array<string, mixed>>
     */
    private function build_severity_summary(array $markers): array {
        $counts = [
            self::SEVERITY_NOTICE => 0,
            self::SEVERITY_MODERATE => 0,
            self::SEVERITY_STRONG => 0,
            self::SEVERITY_RESTRICTED => 0,
        ];

        foreach ($markers as $marker) {
            $severity = $this->normalise_severity((string)$marker['severity']);
            $counts[$severity]++;
        }

        $summary = [];
        foreach ($counts as $severity => $count) {
            if ($count <= 0) {
                continue;
            }

            $summary[] = [
                'severity' => $severity,
                'label' => $this->get_severity_label($severity),
                'class' => $this->css_class('severity', $severity),
                'count' => $count,
            ];
        }

        return $summary;
    }

    /**
     * Build review-state summary.
     *
     * @param array<int, array<string, mixed>> $markers Marker list.
     * @return array<int, array<string, mixed>>
     */
    private function build_review_summary(array $markers): array {
        $counts = [
            self::REVIEW_DRAFT => 0,
            self::REVIEW_PENDING => 0,
            self::REVIEW_REVIEWED => 0,
            self::REVIEW_APPROVED => 0,
            self::REVIEW_CONTESTED => 0,
            self::REVIEW_RETIRED => 0,
        ];

        foreach ($markers as $marker) {
            $state = $this->normalise_review_state((string)$marker['reviewstate']);
            $counts[$state]++;
        }

        $summary = [];
        foreach ($counts as $state => $count) {
            if ($count <= 0) {
                continue;
            }

            $summary[] = [
                'state' => $state,
                'label' => $this->get_review_state_label($state),
                'class' => $this->css_class('review-state', $state),
                'count' => $count,
            ];
        }

        return $summary;
    }

    /**
     * Normalize a marker record.
     *
     * @param mixed $marker Marker.
     * @return array<string, mixed>
     */
    private function normalise_marker(mixed $marker): array {
        $marker = $this->as_array($marker);

        $targettype = $this->normalise_target_type((string)$this->field($marker, ['targettype'], $this->targettype));
        $tagkey = $this->clean_key((string)$this->field($marker, ['tagkey', 'tag', 'contenttag', 'advisorytag'], ''));

        return [
            'id' => $this->int_field($marker, ['id']),
            'uuid' => $this->text_field($marker, ['uuid']),
            'archiveid' => $this->int_field($marker, ['archiveid'], $this->archiveid),
            'mediaid' => $this->int_field($marker, ['mediaid']),
            'externalworkid' => $this->int_field($marker, ['externalworkid', 'workid']),
            'targettype' => $targettype,
            'targetid' => $this->int_field($marker, ['targetid'], $this->targetid),
            'tagkey' => $tagkey,
            'taglabel' => $this->text_field($marker, ['taglabel', 'label', 'name'], $this->label_from_key($tagkey)),
            'tagcategory' => $this->clean_key((string)$this->field($marker, ['tagcategory', 'category'], '')),
            'severity' => $this->normalise_severity((string)$this->field($marker, ['severity'], self::SEVERITY_NOTICE)),
            'audiencesuitability' => $this->normalise_suitability(
                (string)$this->field($marker, ['audiencesuitability', 'audience_suitability'], self::SUITABILITY_GUIDED)
            ),
            'reviewstate' => $this->normalise_review_state(
                (string)$this->field($marker, ['reviewstate', 'review_state', 'state'], self::REVIEW_PENDING)
            ),
            'visibility' => $this->normalise_visibility(
                (string)$this->field($marker, ['visibility'], self::VISIBILITY_COURSE)
            ),
            'locatortype' => $this->clean_key((string)$this->field($marker, ['locatortype', 'locator_type'], '')),
            'locatorstart' => $this->text_field($marker, ['locatorstart', 'locator_start', 'start', 'from']),
            'locatorend' => $this->text_field($marker, ['locatorend', 'locator_end', 'end', 'to']),
            'locatorlabel' => $this->text_field($marker, ['locatorlabel', 'locator', 'locatorvalue']),
            'description' => $this->format_raw($this->field($marker, ['description', 'summary'], '')),
            'note' => $this->format_raw($this->field($marker, ['note', 'advisorynote', 'teachingnote'], '')),
            'culturalprotocol' => $this->bool_field($marker, ['culturalprotocol', 'iscultural', 'cultural']),
            'restricted' => $this->bool_field($marker, ['restricted', 'isrestricted']),
            'requirescontext' => $this->bool_field($marker, ['requirescontext', 'requires_context']),
            'redacted' => $this->bool_field($marker, ['redacted', 'isredacted']),
            'timecreated' => $this->int_field($marker, ['timecreated']),
            'timemodified' => $this->int_field($marker, ['timemodified']),
        ];
    }

    /**
     * Normalize a review record.
     *
     * @param mixed $review Review.
     * @return array<string, mixed>
     */
    private function normalise_review(mixed $review): array {
        $review = $this->as_array($review);

        return [
            'id' => $this->int_field($review, ['id']),
            'uuid' => $this->text_field($review, ['uuid']),
            'markerid' => $this->int_field($review, ['markerid', 'contentmarkerid']),
            'reviewerid' => $this->int_field($review, ['reviewerid', 'userid']),
            'state' => $this->normalise_review_state(
                (string)$this->field($review, ['state', 'reviewstate'], self::REVIEW_PENDING)
            ),
            'severity' => $this->normalise_severity(
                (string)$this->field($review, ['severity'], self::SEVERITY_NOTICE)
            ),
            'audiencesuitability' => $this->normalise_suitability(
                (string)$this->field($review, ['audiencesuitability'], self::SUITABILITY_GUIDED)
            ),
            'rationale' => $this->format_raw($this->field($review, ['rationale'], '')),
            'reviewnote' => $this->format_raw($this->field($review, ['reviewnote', 'note'], '')),
            'culturalprotocol' => $this->bool_field($review, ['culturalprotocol']),
            'restricted' => $this->bool_field($review, ['restricted']),
            'metadatajson' => $this->metadata_json($this->field($review, ['metadata'], [])),
            'timecreated' => $this->int_field($review, ['timecreated']),
            'timemodified' => $this->int_field($review, ['timemodified']),
        ];
    }

    /**
     * Normalize content tag.
     *
     * @param mixed $tag Tag.
     * @return array<string, mixed>
     */
    private function normalise_tag(mixed $tag): array {
        $tag = $this->as_array($tag);

        $tagkey = $this->clean_key((string)$this->field($tag, ['tagkey', 'key', 'tag'], ''));

        return [
            'id' => $this->int_field($tag, ['id']),
            'uuid' => $this->text_field($tag, ['uuid']),
            'tagkey' => $tagkey,
            'label' => $this->text_field($tag, ['label', 'name'], $this->label_from_key($tagkey)),
            'category' => $this->clean_key((string)$this->field($tag, ['category'], '')),
            'description' => $this->format_raw($this->field($tag, ['description'], '')),
            'defaultseverity' => $this->normalise_severity(
                (string)$this->field($tag, ['defaultseverity', 'severity'], self::SEVERITY_NOTICE)
            ),
            'defaultaudiencesuitability' => $this->normalise_suitability(
                (string)$this->field($tag, ['defaultaudiencesuitability', 'audiencesuitability'], self::SUITABILITY_GUIDED)
            ),
            'iscultural' => $this->bool_field($tag, ['iscultural', 'culturalprotocol']),
            'restrictsbydefault' => $this->bool_field($tag, ['restrictsbydefault', 'restricted']),
            'requiresreview' => $this->bool_field($tag, ['requiresreview']),
        ];
    }

    /**
     * Normalize content tag set.
     *
     * @param mixed $tagset Tag set.
     * @return array<string, mixed>
     */
    private function normalise_tag_set(mixed $tagset): array {
        $tagset = $this->as_array($tagset);

        $key = $this->clean_key((string)$this->field($tagset, ['tagsetkey', 'setkey', 'key'], ''));

        return [
            'id' => $this->int_field($tagset, ['id']),
            'uuid' => $this->text_field($tagset, ['uuid']),
            'key' => $key,
            'label' => $this->text_field($tagset, ['label', 'name'], $this->label_from_key($key)),
            'description' => $this->format_raw($this->field($tagset, ['description'], '')),
            'status' => $this->clean_key((string)$this->field($tagset, ['status'], 'active')),
            'version' => $this->text_field($tagset, ['version', 'versionno']),
            'tagcount' => $this->int_field($tagset, ['tagcount']),
        ];
    }

    /**
     * Normalize external work reference.
     *
     * @param mixed $work External work.
     * @return array<string, mixed>
     */
    private function normalise_external_work(mixed $work): array {
        $work = $this->as_array($work);

        return [
            'id' => $this->int_field($work, ['id']),
            'uuid' => $this->text_field($work, ['uuid']),
            'worktype' => $this->clean_key((string)$this->field($work, ['worktype'], 'other')),
            'title' => $this->text_field($work, ['title']),
            'creator' => $this->text_field($work, ['creator']),
            'publisher' => $this->text_field($work, ['publisher']),
            'publicationyear' => $this->int_field($work, ['publicationyear']),
            'sourceurl' => $this->normalise_url($this->field($work, ['sourceurl'], '')),
            'citation' => $this->format_raw($this->field($work, ['citation'], '')),
        ];
    }

    /**
     * Normalize UI action.
     *
     * @param mixed $action Action.
     * @return array<string, mixed>
     */
    private function normalise_action(mixed $action): array {
        $action = $this->as_array($action);

        $key = $this->clean_key((string)$this->field($action, ['key', 'name'], ''));

        return [
            'key' => $key,
            'label' => $this->text_field($action, ['label'], $this->label_from_key($key)),
            'url' => $this->normalise_url($this->field($action, ['url'], '')),
            'class' => $this->text_field($action, ['class'], $this->css_class('action', $key)),
            'disabled' => $this->bool_field($action, ['disabled']),
            'primary' => $this->bool_field($action, ['primary']),
        ];
    }

    /**
     * Normalize permission flags.
     *
     * @param array<string, mixed> $permissions Permission flags.
     * @return array<string, bool>
     */
    private function normalise_permissions(array $permissions): array {
        $defaults = [
            'canview' => true,
            'canmanage' => false,
            'canreview' => false,
            'canedit' => false,
            'candelete' => false,
            'canexport' => false,
            'canviewrestricted' => false,
            'canviewcultural' => false,
        ];

        foreach ($defaults as $key => $default) {
            $defaults[$key] = array_key_exists($key, $permissions) ? !empty($permissions[$key]) : $default;
        }

        return $defaults;
    }

    /**
     * Return highest severity.
     *
     * @param array<int, array<string, mixed>> $markers Marker list.
     * @return string
     */
    private function highest_severity(array $markers): string {
        $rank = [
            self::SEVERITY_NOTICE => 1,
            self::SEVERITY_MODERATE => 2,
            self::SEVERITY_STRONG => 3,
            self::SEVERITY_RESTRICTED => 4,
        ];

        $highest = self::SEVERITY_NOTICE;
        foreach ($markers as $marker) {
            $severity = $this->normalise_severity((string)$marker['severity']);
            if ($rank[$severity] > $rank[$highest]) {
                $highest = $severity;
            }
        }

        return $highest;
    }

    /**
     * Return whether markers contain sensitive content.
     *
     * @param array<int, array<string, mixed>> $markers Marker list.
     * @return bool
     */
    private function has_sensitive_content(array $markers): bool {
        return !empty($markers);
    }

    /**
     * Return whether markers include restricted content.
     *
     * @param array<int, array<string, mixed>> $markers Marker list.
     * @return bool
     */
    private function has_restricted_content(array $markers): bool {
        foreach ($markers as $marker) {
            if (!empty($marker['isrestricted']) || !empty($marker['restricted']) ||
                    $this->normalise_severity((string)$marker['severity']) === self::SEVERITY_RESTRICTED ||
                    $this->is_restricted_visibility((string)$marker['visibility'])) {
                return true;
            }
        }

        return false;
    }

    /**
     * Return whether markers include cultural protocol.
     *
     * @param array<int, array<string, mixed>> $markers Marker list.
     * @return bool
     */
    private function has_cultural_protocol(array $markers): bool {
        foreach ($markers as $marker) {
            if (!empty($marker['isculturalprotocol']) || !empty($marker['culturalprotocol'])) {
                return true;
            }
        }

        return false;
    }

    /**
     * Return whether marker list contains a review state.
     *
     * @param array<int, array<string, mixed>> $markers Marker list.
     * @param string $state Review state.
     * @return bool
     */
    private function has_review_state(array $markers, string $state): bool {
        foreach ($markers as $marker) {
            if ($this->normalise_review_state((string)$marker['reviewstate']) === $state) {
                return true;
            }
        }

        return false;
    }

    /**
     * Normalize target type.
     *
     * @param string $targettype Target type.
     * @return string
     */
    private function normalise_target_type(string $targettype): string {
        $targettype = $this->clean_key($targettype);

        if (!in_array($targettype, [
            self::TARGET_MEDIA,
            self::TARGET_EXTERNAL_WORK,
            self::TARGET_ARCHIVE_ITEM,
            '',
        ], true)) {
            return '';
        }

        return $targettype;
    }

    /**
     * Normalize review state.
     *
     * @param string $state State.
     * @return string
     */
    private function normalise_review_state(string $state): string {
        $state = $this->clean_key($state);

        if (!in_array($state, [
            self::REVIEW_DRAFT,
            self::REVIEW_PENDING,
            self::REVIEW_REVIEWED,
            self::REVIEW_APPROVED,
            self::REVIEW_CONTESTED,
            self::REVIEW_RETIRED,
        ], true)) {
            return self::REVIEW_PENDING;
        }

        return $state;
    }

    /**
     * Normalize severity.
     *
     * @param string $severity Severity.
     * @return string
     */
    private function normalise_severity(string $severity): string {
        $severity = $this->clean_key($severity);

        if (!in_array($severity, [
            self::SEVERITY_NOTICE,
            self::SEVERITY_MODERATE,
            self::SEVERITY_STRONG,
            self::SEVERITY_RESTRICTED,
        ], true)) {
            return self::SEVERITY_NOTICE;
        }

        return $severity;
    }

    /**
     * Normalize audience suitability.
     *
     * @param string $suitability Suitability.
     * @return string
     */
    private function normalise_suitability(string $suitability): string {
        $suitability = $this->clean_key($suitability);

        if (!in_array($suitability, [
            self::SUITABILITY_GENERAL,
            self::SUITABILITY_GUIDED,
            self::SUITABILITY_MATURE,
            self::SUITABILITY_RESTRICTED,
            self::SUITABILITY_RESTRICTED_CULTURAL,
            self::SUITABILITY_RESTRICTED_INTEGRITY,
            self::SUITABILITY_STAFF_ONLY,
        ], true)) {
            return self::SUITABILITY_GUIDED;
        }

        return $suitability;
    }

    /**
     * Normalize visibility.
     *
     * @param string $visibility Visibility.
     * @return string
     */
    private function normalise_visibility(string $visibility): string {
        $visibility = $this->clean_key($visibility);

        if (!in_array($visibility, [
            self::VISIBILITY_PRIVATE,
            self::VISIBILITY_COURSE,
            self::VISIBILITY_PUBLIC,
            self::VISIBILITY_RESTRICTED,
            self::VISIBILITY_RESTRICTED_CULTURAL,
            self::VISIBILITY_RESTRICTED_INTEGRITY,
        ], true)) {
            return self::VISIBILITY_COURSE;
        }

        return $visibility;
    }

    /**
     * Get target type label.
     *
     * @param string $targettype Target type.
     * @return string
     */
    private function get_target_type_label(string $targettype): string {
        return $this->get_component_string('targettype_' . $targettype, $this->label_from_key($targettype));
    }

    /**
     * Get severity label.
     *
     * @param string $severity Severity.
     * @return string
     */
    private function get_severity_label(string $severity): string {
        return $this->get_component_string('severity_' . $severity, $this->label_from_key($severity));
    }

    /**
     * Get review-state label.
     *
     * @param string $state State.
     * @return string
     */
    private function get_review_state_label(string $state): string {
        return $this->get_component_string('reviewstate_' . $state, $this->label_from_key($state));
    }

    /**
     * Get suitability label.
     *
     * @param string $suitability Suitability.
     * @return string
     */
    private function get_suitability_label(string $suitability): string {
        return $this->get_component_string('audiencesuitability_' . $suitability, $this->label_from_key($suitability));
    }

    /**
     * Get visibility label.
     *
     * @param string $visibility Visibility.
     * @return string
     */
    private function get_visibility_label(string $visibility): string {
        return $this->get_component_string('visibility_' . $visibility, $this->label_from_key($visibility));
    }

    /**
     * Get locator type label.
     *
     * @param string $locatortype Locator type.
     * @return string
     */
    private function get_locator_type_label(string $locatortype): string {
        if ($locatortype === '') {
            return '';
        }

        return $this->get_component_string('locatortype_' . $locatortype, $this->label_from_key($locatortype));
    }

    /**
     * Get component string or fallback.
     *
     * @param string $identifier Identifier.
     * @param string $fallback Fallback.
     * @return string
     */
    private function get_component_string(string $identifier, string $fallback): string {
        if (get_string_manager()->string_exists($identifier, 'uckkarchive')) {
            return get_string($identifier, 'uckkarchive');
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
        $value = $this->clean_key($value);
        $value = str_replace('_', '-', $value);

        return $prefix . '-' . $value;
    }

    /**
     * Return whether visibility is restricted.
     *
     * @param string $visibility Visibility.
     * @return bool
     */
    private function is_restricted_visibility(string $visibility): bool {
        return in_array($visibility, [
            self::VISIBILITY_RESTRICTED,
            self::VISIBILITY_RESTRICTED_CULTURAL,
            self::VISIBILITY_RESTRICTED_INTEGRITY,
        ], true);
    }

    /**
     * Convert object/array to array.
     *
     * @param mixed $value Value.
     * @return array<string, mixed>
     */
    private function as_array(mixed $value): array {
        if ($value instanceof stdClass) {
            return (array)$value;
        }

        if (is_array($value)) {
            return $value;
        }

        return [];
    }

    /**
     * Get first available field.
     *
     * @param array<string, mixed> $record Record.
     * @param string[] $fields Candidate fields.
     * @param mixed $default Default.
     * @return mixed
     */
    private function field(array $record, array $fields, mixed $default = null): mixed {
        foreach ($fields as $field) {
            if (array_key_exists($field, $record) && $record[$field] !== null) {
                return $record[$field];
            }
        }

        return $default;
    }

    /**
     * Get int field.
     *
     * @param array<string, mixed> $record Record.
     * @param string[] $fields Candidate fields.
     * @param int $default Default.
     * @return int
     */
    private function int_field(array $record, array $fields, int $default = 0): int {
        return (int)$this->field($record, $fields, $default);
    }

    /**
     * Get bool field.
     *
     * @param array<string, mixed> $record Record.
     * @param string[] $fields Candidate fields.
     * @param bool $default Default.
     * @return bool
     */
    private function bool_field(array $record, array $fields, bool $default = false): bool {
        return !empty($this->field($record, $fields, $default));
    }

    /**
     * Get formatted text field.
     *
     * @param array<string, mixed> $record Record.
     * @param string[] $fields Candidate fields.
     * @param string $default Default.
     * @return string
     */
    private function text_field(array $record, array $fields, string $default = ''): string {
        return format_string((string)$this->field($record, $fields, $default));
    }

    /**
     * Format raw text for template output.
     *
     * @param mixed $value Value.
     * @return string
     */
    private function format_raw(mixed $value): string {
        $value = trim((string)$value);

        if ($value === '') {
            return '';
        }

        return format_text($value, FORMAT_HTML, ['trusted' => false, 'para' => false]);
    }

    /**
     * Normalize URL.
     *
     * @param mixed $url URL.
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

    /**
     * Clean machine key.
     *
     * @param string $key Key.
     * @return string
     */
    private function clean_key(string $key): string {
        return clean_param(strtolower(trim($key)), PARAM_ALPHANUMEXT);
    }

    /**
     * Convert key to readable label.
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
     * Encode metadata as JSON.
     *
     * @param mixed $metadata Metadata.
     * @return string
     */
    private function metadata_json(mixed $metadata): string {
        if (is_string($metadata)) {
            $decoded = json_decode($metadata, true);
            if (is_array($decoded)) {
                $metadata = $decoded;
            } else {
                $metadata = [];
            }
        }

        if ($metadata instanceof stdClass) {
            $metadata = (array)$metadata;
        }

        if (!is_array($metadata)) {
            $metadata = [];
        }

        $json = json_encode($metadata, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);

        return $json === false ? '{}' : $json;
    }
}
