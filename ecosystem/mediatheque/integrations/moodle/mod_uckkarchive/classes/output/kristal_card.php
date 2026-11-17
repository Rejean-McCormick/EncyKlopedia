<?php
// This file is part of Moodle - https://moodle.org/
//
// Moodle is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// any later version.

/**
 * Kristal card output object for the UCKK archive activity.
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
 * Renderable Kristal card.
 *
 * This object exports already permission-filtered Kristal data for Mustache.
 * It does not validate, certify, revise, archive-finalise, expose restricted
 * information, or make integrity decisions.
 */
final class kristal_card implements renderable, templatable {
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

    /** Status: contested. */
    public const STATUS_CONTESTED = 'contested';

    /** Status: invalidated. */
    public const STATUS_INVALIDATED = 'invalidated';

    /** Status: archived. */
    public const STATUS_ARCHIVED = 'archived';

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

    /**
     * Raw Kristal data.
     *
     * @var array<string, mixed>
     */
    private array $kristal;

    /**
     * Already-filtered actions.
     *
     * @var array<int, array<string, mixed>>
     */
    private array $actions;

    /**
     * Already-filtered links.
     *
     * @var array<int, array<string, mixed>>
     */
    private array $links;

    /**
     * Already-filtered warnings.
     *
     * @var array<int, array<string, mixed>>
     */
    private array $warnings;

    /**
     * Constructor.
     *
     * @param array<string, mixed>|stdClass $kristal Kristal data.
     * @param array<int, array<string, mixed>|stdClass> $actions Permitted actions.
     * @param array<int, array<string, mixed>|stdClass> $links Related links.
     * @param array<int, array<string, mixed>|stdClass|string> $warnings Warning rows.
     */
    public function __construct(
        array|stdClass $kristal,
        array $actions = [],
        array $links = [],
        array $warnings = []
    ) {
        $this->kristal = (array)$kristal;
        $this->actions = array_map([$this, 'normalise_action'], $actions);
        $this->links = array_map([$this, 'normalise_link'], $links);
        $this->warnings = $this->normalise_warnings($warnings);
    }

    /**
     * Export the template context.
     *
     * @param renderer_base $output Renderer.
     * @return stdClass
     */
    public function export_for_template(renderer_base $output): stdClass {
        $data = new stdClass();

        $data->kristalid = $this->get_int('id');
        $data->archiveid = $this->get_int('archiveid');
        $data->itemid = $this->get_int('itemid');
        $data->courseid = $this->get_int('courseid');
        $data->cmid = $this->get_int('cmid');
        $data->contextid = $this->get_int('contextid');
        $data->userid = $this->get_int('userid');

        $data->title = format_string($this->get_string('title', get_string('kristal', 'uckkarchive')));
        $data->shortname = clean_param($this->get_string('shortname'), PARAM_ALPHANUMEXT);
        $data->hasshortname = $data->shortname !== '';

        $data->summary = format_text($this->get_string('summary'), FORMAT_HTML);
        $data->hassummary = trim(strip_tags($data->summary)) !== '';

        $data->content = format_text($this->get_string('content'), FORMAT_HTML);
        $data->hascontent = trim(strip_tags($data->content)) !== '';

        $data->kristaltype = clean_param($this->get_string('kristaltype', 'concept'), PARAM_ALPHANUMEXT);
        $data->kristaltypelabel = $this->get_label('kristaltype', $data->kristaltype);
        $data->kristaltypeclass = 'kristal-type-' . str_replace('_', '-', $data->kristaltype);

        $data->status = $this->normalise_status($this->get_string('status', self::STATUS_DRAFT));
        $data->statuslabel = $this->get_label('status', $data->status);
        $data->statusclass = 'status-' . str_replace('_', '-', $data->status);

        $data->validationstate = $this->normalise_validation_state(
            $this->get_string('validationstate', self::VALIDATION_UNVERIFIED)
        );
        $data->validationlabel = $this->get_label('validation', $data->validationstate);
        $data->validationclass = 'validation-' . str_replace('_', '-', $data->validationstate);

        $data->visibility = clean_param($this->get_string('visibility', 'course'), PARAM_ALPHANUMEXT);
        $data->visibilitylabel = $this->get_label('visibility', $data->visibility);
        $data->visibilityclass = 'visibility-' . str_replace('_', '-', $data->visibility);

        $data->provenance = $this->normalise_provenance($this->get_string('provenance', self::PROVENANCE_HUMAN));
        $data->provenancelabel = $this->get_label('provenance', $data->provenance);
        $data->provenanceclass = 'provenance-' . str_replace('_', '-', $data->provenance);

        $data->provenancestatement = format_text($this->get_string('provenancestatement'), FORMAT_HTML);
        $data->hasprovenancestatement = trim(strip_tags($data->provenancestatement)) !== '';

        $data->sourceauthor = format_string($this->get_string('sourceauthor'));
        $data->hassourceauthor = $data->sourceauthor !== '';

        $data->sourcetitle = format_string($this->get_string('sourcetitle'));
        $data->hassourcetitle = $data->sourcetitle !== '';

        $data->sourceurl = $this->normalise_url($this->get_string('sourceurl'));
        $data->hassourceurl = $data->sourceurl !== '';

        $data->sourcedate = $this->get_int('sourcedate');
        $data->sourcedatelabel = $data->sourcedate > 0 ? userdate($data->sourcedate) : '';
        $data->hassourcedate = $data->sourcedate > 0;

        $data->provenancehash = clean_param($this->get_string('provenancehash'), PARAM_ALPHANUMEXT);
        $data->hasprovenancehash = $data->provenancehash !== '';

        $data->canonref = format_string($this->get_string('canonref'));
        $data->hascanonref = $data->canonref !== '';

        $data->publicsummary = format_text($this->get_string('publicsummary'), FORMAT_HTML);
        $data->haspublicsummary = trim(strip_tags($data->publicsummary)) !== '';

        $data->restrictednotes = format_text($this->get_string('restrictednotes'), FORMAT_HTML);
        $data->hasrestrictednotes = trim(strip_tags($data->restrictednotes)) !== '';

        $data->uncertaintynotes = format_text($this->get_string('uncertaintynotes'), FORMAT_HTML);
        $data->hasuncertaintynotes = trim(strip_tags($data->uncertaintynotes)) !== '';

        $data->ethicalnotes = format_text($this->get_string('ethicalnotes'), FORMAT_HTML);
        $data->hasethicalnotes = trim(strip_tags($data->ethicalnotes)) !== '';

        $data->aiassisted = !empty($this->kristal['aiassisted'])
            || $data->provenance === self::PROVENANCE_AI_ASSISTED;
        $data->ailog = format_text($this->get_string('ailog'), FORMAT_HTML);
        $data->hasailog = trim(strip_tags($data->ailog)) !== '';
        $data->ainotice = $data->aiassisted ? get_string('ainonsovereignnotice', 'uckkarchive') : '';

        $data->sourcecomponent = clean_param($this->get_string('sourcecomponent'), PARAM_COMPONENT);
        $data->sourceid = $this->get_int('sourceid');
        $data->hassourcerecord = $data->sourcecomponent !== '' && $data->sourceid > 0;

        $data->versionno = max(1, $this->get_int('versionno', 1));
        $data->versionlabel = get_string('version', 'uckkarchive') . ' ' . $data->versionno;

        $data->timecreated = $this->get_int('timecreated');
        $data->timecreatedlabel = $data->timecreated > 0 ? userdate($data->timecreated) : '';
        $data->hastimecreated = $data->timecreated > 0;

        $data->timemodified = $this->get_int('timemodified');
        $data->timemodifiedlabel = $data->timemodified > 0 ? userdate($data->timemodified) : '';
        $data->hastimemodified = $data->timemodified > 0;

        $data->url = $this->get_primary_url();
        $data->hasurl = $data->url !== '';

        $data->itemurl = $this->get_item_url();
        $data->hasitemurl = $data->itemurl !== '';

        $data->tags = $this->normalise_list($this->kristal['tags'] ?? []);
        $data->hastags = !empty($data->tags);

        $data->competencies = $this->normalise_list($this->kristal['competencycodes'] ?? []);
        $data->hascompetencies = !empty($data->competencies);

        $data->badges = $this->normalise_list($this->kristal['badgekeys'] ?? []);
        $data->hasbadges = !empty($data->badges);

        $data->links = array_map(static fn(array $link): stdClass => (object)$link, $this->links);
        $data->haslinks = !empty($data->links);

        $data->warnings = array_map(static fn(array $warning): stdClass => (object)$warning, $this->warnings);
        $data->haswarnings = !empty($data->warnings);

        $data->actions = array_map(static fn(array $action): stdClass => (object)$action, $this->actions);
        $data->hasactions = !empty($data->actions);

        $data->isvalidated = in_array($data->validationstate, [
            self::VALIDATION_HUMAN_REVIEWED,
            self::VALIDATION_VERIFIED,
            self::VALIDATION_ARCHIVED,
        ], true);
        $data->iscontested = $data->validationstate === self::VALIDATION_CONTESTED
            || $data->status === self::STATUS_CONTESTED;
        $data->isinvalidated = $data->validationstate === self::VALIDATION_INVALIDATED
            || $data->status === self::STATUS_INVALIDATED;
        $data->isrestricted = in_array($data->visibility, [
            'restricted',
            'restricted_integrity',
        ], true);

        $data->notice = get_string('kristalgovernancenotice', 'uckkarchive');

        return $data;
    }

    /**
     * Get an integer field.
     *
     * @param string $key Field key.
     * @param int $default Default value.
     * @return int
     */
    private function get_int(string $key, int $default = 0): int {
        return max(0, (int)($this->kristal[$key] ?? $default));
    }

    /**
     * Get a string field.
     *
     * @param string $key Field key.
     * @param string $default Default value.
     * @return string
     */
    private function get_string(string $key, string $default = ''): string {
        return trim((string)($this->kristal[$key] ?? $default));
    }

    /**
     * Get primary Kristal URL.
     *
     * @return string
     */
    private function get_primary_url(): string {
        if (!empty($this->kristal['url'])) {
            return $this->normalise_url($this->kristal['url']);
        }

        $cmid = $this->get_int('cmid');
        $kristalid = $this->get_int('id');

        if ($cmid <= 0 || $kristalid <= 0) {
            return '';
        }

        return (new moodle_url('/mod/uckkarchive/item.php', [
            'id' => $cmid,
            'kristalid' => $kristalid,
        ]))->out(false);
    }

    /**
     * Get parent archive item URL.
     *
     * @return string
     */
    private function get_item_url(): string {
        if (!empty($this->kristal['itemurl'])) {
            return $this->normalise_url($this->kristal['itemurl']);
        }

        $cmid = $this->get_int('cmid');
        $itemid = $this->get_int('itemid');

        if ($cmid <= 0 || $itemid <= 0) {
            return '';
        }

        return (new moodle_url('/mod/uckkarchive/item.php', [
            'id' => $cmid,
            'itemid' => $itemid,
        ]))->out(false);
    }

    /**
     * Normalise an action row.
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
            'isget' => $method === 'GET',
            'ispost' => $method === 'POST',
            'primary' => !empty($row['primary']),
            'secondary' => empty($row['primary']) && empty($row['danger']),
            'danger' => !empty($row['danger']),
            'disabled' => !empty($row['disabled']),
            'disabledreason' => format_string((string)($row['disabledreason'] ?? '')),
            'hasdisabledreason' => trim((string)($row['disabledreason'] ?? '')) !== '',
            'requiresconfirmation' => !empty($row['requiresconfirmation']),
            'confirmmessage' => format_string((string)($row['confirmmessage'] ?? '')),
            'hasconfirmmessage' => trim((string)($row['confirmmessage'] ?? '')) !== '',
        ];
    }

    /**
     * Normalise a related link.
     *
     * @param array<string, mixed>|stdClass $link Raw link.
     * @return array<string, mixed>
     */
    private function normalise_link(array|stdClass $link): array {
        $row = (array)$link;
        $type = clean_param((string)($row['type'] ?? 'related'), PARAM_ALPHANUMEXT);

        return [
            'type' => $type,
            'typelabel' => format_string((string)($row['typelabel'] ?? $this->get_label('linktype', $type))),
            'title' => format_string((string)($row['title'] ?? '')),
            'summary' => format_string((string)($row['summary'] ?? '')),
            'hassummary' => trim((string)($row['summary'] ?? '')) !== '',
            'url' => $this->normalise_url($row['url'] ?? ''),
            'hasurl' => trim((string)($row['url'] ?? '')) !== '',
        ];
    }

    /**
     * Normalise warning rows.
     *
     * @param array<int, array<string, mixed>|stdClass|string> $warnings Raw warnings.
     * @return array<int, array<string, mixed>>
     */
    private function normalise_warnings(array $warnings): array {
        $normalised = [];

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

            $normalised[] = [
                'message' => format_string($message),
                'severity' => $severity,
                'class' => 'alert-' . $this->get_warning_class($severity),
            ];
        }

        return $normalised;
    }

    /**
     * Normalise list-like data.
     *
     * @param mixed $value Raw list value.
     * @return array<int, stdClass>
     */
    private function normalise_list(mixed $value): array {
        if (is_string($value)) {
            $decoded = json_decode($value, true);

            if (json_last_error() === JSON_ERROR_NONE && is_array($decoded)) {
                $value = $decoded;
            } else {
                $value = preg_split('/[\r\n,]+/', $value) ?: [];
            }
        }

        if ($value instanceof stdClass) {
            $value = (array)$value;
        }

        if (!is_array($value)) {
            return [];
        }

        $items = [];

        foreach ($value as $key => $item) {
            if ($item instanceof stdClass) {
                $item = (array)$item;
            }

            if (is_array($item)) {
                $label = trim((string)($item['label'] ?? $item['name'] ?? $item['code'] ?? $item['key'] ?? ''));
                $code = trim((string)($item['code'] ?? $item['key'] ?? $key));
                $url = $this->normalise_url($item['url'] ?? '');
            } else {
                $label = trim((string)$item);
                $code = trim((string)$item);
                $url = '';
            }

            if ($label === '') {
                continue;
            }

            $items[] = (object)[
                'label' => format_string($label),
                'code' => format_string($code),
                'hascode' => $code !== '' && $code !== $label,
                'url' => $url,
                'hasurl' => $url !== '',
            ];
        }

        return $items;
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
            self::STATUS_CONTESTED,
            self::STATUS_INVALIDATED,
            self::STATUS_ARCHIVED,
        ];

        return in_array($status, $allowed, true) ? $status : self::STATUS_DRAFT;
    }

    /**
     * Normalise validation state.
     *
     * @param string $state Raw state.
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
     * Normalise provenance.
     *
     * @param string $provenance Raw provenance.
     * @return string
     */
    private function normalise_provenance(string $provenance): string {
        $provenance = clean_param($provenance, PARAM_ALPHANUMEXT);

        $allowed = [
            self::PROVENANCE_HUMAN,
            self::PROVENANCE_AI_ASSISTED,
            self::PROVENANCE_IMPORTED,
            self::PROVENANCE_SYSTEM,
            self::PROVENANCE_ARCHIVE,
            self::PROVENANCE_ASSEMBLY,
            self::PROVENANCE_CHALLENGE,
            self::PROVENANCE_INTEGRITY,
        ];

        return in_array($provenance, $allowed, true) ? $provenance : self::PROVENANCE_HUMAN;
    }

    /**
     * Get a localised label for a canonical value.
     *
     * @param string $prefix String key prefix.
     * @param string $value Canonical value.
     * @return string
     */
    private function get_label(string $prefix, string $value): string {
        $key = $prefix . ':' . str_replace('_', '', $value);
        $altkey = $prefix . ':' . $value;

        if (get_string_manager()->string_exists($key, 'uckkarchive')) {
            return get_string($key, 'uckkarchive');
        }

        if (get_string_manager()->string_exists($altkey, 'uckkarchive')) {
            return get_string($altkey, 'uckkarchive');
        }

        return ucfirst(str_replace('_', ' ', $value));
    }

    /**
     * Get default action label.
     *
     * @param string $key Action key.
     * @return string
     */
    private function get_action_label(string $key): string {
        $stringkey = 'kristalaction:' . str_replace('_', '', $key);

        if ($key !== '' && get_string_manager()->string_exists($stringkey, 'uckkarchive')) {
            return get_string($stringkey, 'uckkarchive');
        }

        return get_string('view');
    }

    /**
     * Convert warning severity to Bootstrap alert suffix.
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
     * Normalise URL input.
     *
     * @param mixed $url URL input.
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
