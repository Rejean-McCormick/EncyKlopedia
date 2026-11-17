<?php
// This file is part of Moodle - https://moodle.org/
//
// Moodle is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// any later version.

/**
 * Provenance panel output object for UCKK archive items.
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
 * Renderable provenance panel for one archive item.
 *
 * This class prepares display data only. It does not validate provenance,
 * modify archive history, open integrity cases, export records, delete
 * evidence, or decide visibility.
 */
final class provenance_panel implements renderable, templatable {
    /** Provenance source: human. */
    public const PROVENANCE_HUMAN = 'human';

    /** Provenance source: AI-assisted. */
    public const PROVENANCE_AI_ASSISTED = 'ai_assisted';

    /** Provenance source: imported. */
    public const PROVENANCE_IMPORTED = 'imported';

    /** Provenance source: system. */
    public const PROVENANCE_SYSTEM = 'system';

    /** Provenance source: archive. */
    public const PROVENANCE_ARCHIVE = 'archive';

    /** Provenance source: assembly. */
    public const PROVENANCE_ASSEMBLY = 'assembly';

    /** Provenance source: challenge. */
    public const PROVENANCE_CHALLENGE = 'challenge';

    /** Provenance source: integrity. */
    public const PROVENANCE_INTEGRITY = 'integrity';

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

    /**
     * Archive instance id.
     *
     * @var int
     */
    private int $archiveid;

    /**
     * Archive item id.
     *
     * @var int
     */
    private int $itemid;

    /**
     * Course module id.
     *
     * @var int
     */
    private int $cmid;

    /**
     * Context id.
     *
     * @var int
     */
    private int $contextid;

    /**
     * Archive item title.
     *
     * @var string
     */
    private string $itemtitle;

    /**
     * Permission-filtered provenance summary.
     *
     * @var array<string, mixed>
     */
    private array $summary;

    /**
     * Permission-filtered provenance records.
     *
     * @var array<int, array<string, mixed>>
     */
    private array $records;

    /**
     * Permission-filtered action records.
     *
     * @var array<int, array<string, mixed>>
     */
    private array $actions;

    /**
     * Constructor.
     *
     * @param int $archiveid Archive instance id.
     * @param int $itemid Archive item id.
     * @param int $cmid Course module id.
     * @param int $contextid Moodle context id.
     * @param string $itemtitle Archive item title.
     * @param array<string, mixed> $summary Permission-filtered provenance summary.
     * @param array<int, array<string, mixed>|stdClass> $records Permission-filtered provenance records.
     * @param array<int, array<string, mixed>|stdClass> $actions Permission-filtered action rows.
     */
    public function __construct(
        int $archiveid,
        int $itemid,
        int $cmid,
        int $contextid,
        string $itemtitle,
        array $summary = [],
        array $records = [],
        array $actions = []
    ) {
        $this->archiveid = max(0, $archiveid);
        $this->itemid = max(0, $itemid);
        $this->cmid = max(0, $cmid);
        $this->contextid = max(0, $contextid);
        $this->itemtitle = format_string($itemtitle);
        $this->summary = $summary;
        $this->records = array_map([$this, 'normalise_record'], $records);
        $this->actions = array_map([$this, 'normalise_action'], $actions);
    }

    /**
     * Export context for Mustache.
     *
     * @param renderer_base $output Renderer.
     * @return stdClass
     */
    public function export_for_template(renderer_base $output): stdClass {
        $provenance = $this->normalise_provenance((string)($this->summary['provenance'] ?? self::PROVENANCE_HUMAN));
        $validationstate = $this->normalise_validation_state(
            (string)($this->summary['validationstate'] ?? self::VALIDATION_UNVERIFIED)
        );
        $visibility = $this->normalise_visibility((string)($this->summary['visibility'] ?? self::VISIBILITY_COURSE));

        $itemurl = new moodle_url('/mod/uckkarchive/item.php', [
            'id' => $this->cmid,
            'itemid' => $this->itemid,
        ]);

        $validateurl = new moodle_url('/mod/uckkarchive/validate.php', [
            'id' => $this->cmid,
            'itemid' => $this->itemid,
        ]);

        $data = new stdClass();
        $data->archiveid = $this->archiveid;
        $data->itemid = $this->itemid;
        $data->cmid = $this->cmid;
        $data->contextid = $this->contextid;
        $data->itemtitle = $this->itemtitle;
        $data->heading = get_string('provenancepanel', 'uckkarchive');

        $data->itemurl = $itemurl->out(false);
        $data->validateurl = $validateurl->out(false);

        $data->provenance = $provenance;
        $data->provenancelabel = $this->get_provenance_label($provenance);
        $data->provenanceclass = 'provenance-' . str_replace('_', '-', $provenance);

        $data->validationstate = $validationstate;
        $data->validationstatelabel = $this->get_validation_state_label($validationstate);
        $data->validationstateclass = 'validation-state-' . str_replace('_', '-', $validationstate);

        $data->visibility = $visibility;
        $data->visibilitylabel = $this->get_visibility_label($visibility);
        $data->visibilityclass = 'visibility-' . str_replace('_', '-', $visibility);

        $data->provenanceverified = !empty($this->summary['provenanceverified']);
        $data->sourceverified = !empty($this->summary['sourceverified']);
        $data->contextverified = !empty($this->summary['contextverified']);
        $data->evidencerelationverified = !empty($this->summary['evidencerelationverified']);

        $data->aiassisted = $provenance === self::PROVENANCE_AI_ASSISTED || !empty($this->summary['aiassisted']);
        $data->hasrestricteddata = $this->is_restricted_visibility($visibility) || !empty($this->summary['hasrestricteddata']);
        $data->hascontestation = $validationstate === self::VALIDATION_CONTESTED || !empty($this->summary['hascontestation']);
        $data->hasinvalidation = $validationstate === self::VALIDATION_INVALIDATED || !empty($this->summary['hasinvalidation']);

        $data->provenancehash = clean_param((string)($this->summary['provenancehash'] ?? ''), PARAM_ALPHANUMEXT);
        $data->hasprovenancehash = $data->provenancehash !== '';

        $data->uncertaintylabel = format_string((string)($this->summary['uncertaintylabel'] ?? ''));
        $data->hasuncertainty = $data->uncertaintylabel !== '';

        $data->sourceauthor = format_string((string)($this->summary['sourceauthor'] ?? ''));
        $data->hassourceauthor = $data->sourceauthor !== '';

        $data->sourcedatelabel = format_string((string)($this->summary['sourcedatelabel'] ?? ''));
        $data->hassourcedate = $data->sourcedatelabel !== '';

        $data->recordcount = count($this->records);
        $data->records = $this->build_record_rows();
        $data->hasrecords = !empty($data->records);

        $data->checks = $this->build_check_rows($data);
        $data->summaryitems = $this->build_summary_items($data);

        $data->warnings = $this->normalise_warnings($this->summary['warnings'] ?? []);
        $data->haswarnings = !empty($data->warnings);

        $data->actions = $this->build_action_rows();
        $data->hasactions = !empty($data->actions);

        $data->notice = get_string('provenancegovernancenotice', 'uckkarchive');
        $data->emptyrecordslabel = get_string('provenancerecords:none', 'uckkarchive');

        return $data;
    }

    /**
     * Normalise one provenance record.
     *
     * @param array<string, mixed>|stdClass $record Raw record.
     * @return array<string, mixed>
     */
    private function normalise_record(array|stdClass $record): array {
        $row = (array)$record;

        $provenance = $this->normalise_provenance((string)($row['provenance'] ?? $row['source'] ?? self::PROVENANCE_HUMAN));
        $validationstate = $this->normalise_validation_state(
            (string)($row['validationstate'] ?? self::VALIDATION_UNVERIFIED)
        );
        $visibility = $this->normalise_visibility((string)($row['visibility'] ?? self::VISIBILITY_COURSE));

        return [
            'id' => max(0, (int)($row['id'] ?? 0)),
            'itemid' => max(0, (int)($row['itemid'] ?? $this->itemid)),
            'provenance' => $provenance,
            'provenancelabel' => $this->get_provenance_label($provenance),
            'validationstate' => $validationstate,
            'validationstatelabel' => $this->get_validation_state_label($validationstate),
            'visibility' => $visibility,
            'visibilitylabel' => $this->get_visibility_label($visibility),
            'sourcecomponent' => clean_param((string)($row['sourcecomponent'] ?? ''), PARAM_COMPONENT),
            'sourceid' => max(0, (int)($row['sourceid'] ?? 0)),
            'sourcetype' => clean_param((string)($row['sourcetype'] ?? ''), PARAM_ALPHANUMEXT),
            'sourcelabel' => format_string((string)($row['sourcelabel'] ?? '')),
            'summary' => format_string((string)($row['summary'] ?? '')),
            'hassummary' => trim((string)($row['summary'] ?? '')) !== '',
            'evidenceurl' => $this->normalise_url($row['evidenceurl'] ?? $row['url'] ?? null),
            'actorlabel' => format_string((string)($row['actorlabel'] ?? '')),
            'hasactorlabel' => trim((string)($row['actorlabel'] ?? '')) !== '',
            'provenancehash' => clean_param((string)($row['provenancehash'] ?? ''), PARAM_ALPHANUMEXT),
            'verified' => !empty($row['verified']),
            'aiassisted' => $provenance === self::PROVENANCE_AI_ASSISTED || !empty($row['aiassisted']),
            'restricted' => $this->is_restricted_visibility($visibility) || !empty($row['restricted']),
            'timecreated' => max(0, (int)($row['timecreated'] ?? 0)),
            'timemodified' => max(0, (int)($row['timemodified'] ?? 0)),
        ];
    }

    /**
     * Normalise one action row.
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
            'description' => format_string((string)($row['description'] ?? '')),
            'hasdescription' => trim((string)($row['description'] ?? '')) !== '',
            'url' => $this->normalise_url($row['url'] ?? null),
            'method' => $method,
            'primary' => !empty($row['primary']),
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
     * Build provenance record rows.
     *
     * @return array<int, stdClass>
     */
    private function build_record_rows(): array {
        $rows = [];

        foreach ($this->records as $record) {
            $rows[] = (object)[
                'id' => $record['id'],
                'itemid' => $record['itemid'],
                'provenance' => $record['provenance'],
                'provenancelabel' => $record['provenancelabel'],
                'provenanceclass' => 'provenance-' . str_replace('_', '-', $record['provenance']),
                'validationstate' => $record['validationstate'],
                'validationstatelabel' => $record['validationstatelabel'],
                'validationstateclass' => 'validation-state-' . str_replace('_', '-', $record['validationstate']),
                'visibility' => $record['visibility'],
                'visibilitylabel' => $record['visibilitylabel'],
                'visibilityclass' => 'visibility-' . str_replace('_', '-', $record['visibility']),
                'sourcecomponent' => $record['sourcecomponent'],
                'hassourcecomponent' => $record['sourcecomponent'] !== '',
                'sourceid' => $record['sourceid'],
                'hassourceid' => $record['sourceid'] > 0,
                'sourcetype' => $record['sourcetype'],
                'hassourcetype' => $record['sourcetype'] !== '',
                'sourcelabel' => $record['sourcelabel'],
                'hassourcelabel' => $record['sourcelabel'] !== '',
                'summary' => $record['summary'],
                'hassummary' => $record['hassummary'],
                'evidenceurl' => $record['evidenceurl'],
                'hasevidenceurl' => $record['evidenceurl'] !== '',
                'actorlabel' => $record['actorlabel'],
                'hasactorlabel' => $record['hasactorlabel'],
                'provenancehash' => $record['provenancehash'],
                'hasprovenancehash' => $record['provenancehash'] !== '',
                'verified' => $record['verified'],
                'aiassisted' => $record['aiassisted'],
                'restricted' => $record['restricted'],
                'timecreated' => $record['timecreated'],
                'timecreatedlabel' => $record['timecreated'] > 0 ? userdate($record['timecreated']) : '',
                'hastimecreated' => $record['timecreated'] > 0,
                'timemodified' => $record['timemodified'],
                'timemodifiedlabel' => $record['timemodified'] > 0 ? userdate($record['timemodified']) : '',
                'hastimemodified' => $record['timemodified'] > 0,
            ];
        }

        return $rows;
    }

    /**
     * Build verification check rows.
     *
     * @param stdClass $data Exported base data.
     * @return array<int, stdClass>
     */
    private function build_check_rows(stdClass $data): array {
        return [
            (object)[
                'key' => 'provenanceverified',
                'label' => get_string('provenanceverified', 'uckkarchive'),
                'checked' => $data->provenanceverified,
                'class' => $data->provenanceverified ? 'check-ok' : 'check-missing',
            ],
            (object)[
                'key' => 'sourceverified',
                'label' => get_string('sourceverified', 'uckkarchive'),
                'checked' => $data->sourceverified,
                'class' => $data->sourceverified ? 'check-ok' : 'check-missing',
            ],
            (object)[
                'key' => 'contextverified',
                'label' => get_string('contextverified', 'uckkarchive'),
                'checked' => $data->contextverified,
                'class' => $data->contextverified ? 'check-ok' : 'check-missing',
            ],
            (object)[
                'key' => 'evidencerelationverified',
                'label' => get_string('evidencerelationverified', 'uckkarchive'),
                'checked' => $data->evidencerelationverified,
                'class' => $data->evidencerelationverified ? 'check-ok' : 'check-missing',
            ],
        ];
    }

    /**
     * Build summary rows.
     *
     * @param stdClass $data Exported base data.
     * @return array<int, stdClass>
     */
    private function build_summary_items(stdClass $data): array {
        return [
            (object)[
                'key' => 'provenance',
                'label' => get_string('provenance', 'uckkarchive'),
                'value' => $data->provenancelabel,
                'class' => $data->provenanceclass,
            ],
            (object)[
                'key' => 'validationstate',
                'label' => get_string('validationstate', 'uckkarchive'),
                'value' => $data->validationstatelabel,
                'class' => $data->validationstateclass,
            ],
            (object)[
                'key' => 'visibility',
                'label' => get_string('visibility', 'uckkarchive'),
                'value' => $data->visibilitylabel,
                'class' => $data->visibilityclass,
            ],
            (object)[
                'key' => 'recordcount',
                'label' => get_string('provenancerecordcount', 'uckkarchive'),
                'value' => (string)$data->recordcount,
                'class' => $data->recordcount > 0 ? 'state-has-records' : 'state-empty',
            ],
        ];
    }

    /**
     * Build permitted action rows.
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
                'description' => $action['description'],
                'hasdescription' => $action['hasdescription'],
                'url' => $action['url'],
                'method' => $action['method'],
                'ispost' => $action['method'] === 'POST',
                'isget' => $action['method'] === 'GET',
                'primary' => $action['primary'],
                'danger' => $action['danger'],
                'secondary' => !$action['primary'] && !$action['danger'],
                'disabled' => $action['disabled'],
                'disabledreason' => $action['disabledreason'],
                'hasdisabledreason' => $action['hasdisabledreason'],
                'requiresconfirmation' => $action['requiresconfirmation'],
                'confirmmessage' => $action['confirmmessage'],
                'hasconfirmmessage' => $action['hasconfirmmessage'],
            ];
        }

        return $rows;
    }

    /**
     * Normalise warning rows.
     *
     * @param mixed $warnings Warning list.
     * @return array<int, stdClass>
     */
    private function normalise_warnings(mixed $warnings): array {
        if (!is_array($warnings)) {
            return [];
        }

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

            $rows[] = (object)[
                'message' => format_string($message),
                'severity' => $severity,
                'class' => 'alert-' . $this->get_warning_class($severity),
            ];
        }

        return $rows;
    }

    /**
     * Normalise provenance value.
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
        ];

        return in_array($visibility, $allowed, true) ? $visibility : self::VISIBILITY_COURSE;
    }

    /**
     * Return whether a visibility level is restricted.
     *
     * @param string $visibility Visibility key.
     * @return bool
     */
    private function is_restricted_visibility(string $visibility): bool {
        return in_array($visibility, [
            self::VISIBILITY_PRIVATE,
            self::VISIBILITY_RESTRICTED,
            self::VISIBILITY_RESTRICTED_INTEGRITY,
        ], true);
    }

    /**
     * Get provenance label.
     *
     * @param string $provenance Provenance key.
     * @return string
     */
    private function get_provenance_label(string $provenance): string {
        $key = 'provenance:' . $provenance;

        if (get_string_manager()->string_exists($key, 'uckkarchive')) {
            return get_string($key, 'uckkarchive');
        }

        return ucfirst(str_replace('_', ' ', $provenance));
    }

    /**
     * Get validation state label.
     *
     * @param string $state Validation state.
     * @return string
     */
    private function get_validation_state_label(string $state): string {
        $key = 'validationstate:' . $state;

        if (get_string_manager()->string_exists($key, 'uckkarchive')) {
            return get_string($key, 'uckkarchive');
        }

        return ucfirst(str_replace('_', ' ', $state));
    }

    /**
     * Get visibility label.
     *
     * @param string $visibility Visibility key.
     * @return string
     */
    private function get_visibility_label(string $visibility): string {
        $key = 'visibility:' . $visibility;

        if (get_string_manager()->string_exists($key, 'uckkarchive')) {
            return get_string($key, 'uckkarchive');
        }

        return ucfirst(str_replace('_', ' ', $visibility));
    }

    /**
     * Get action label.
     *
     * @param string $key Action key.
     * @return string
     */
    private function get_action_label(string $key): string {
        $stringkey = 'provenanceaction:' . str_replace('_', '', $key);

        if ($key !== '' && get_string_manager()->string_exists($stringkey, 'uckkarchive')) {
            return get_string($stringkey, 'uckkarchive');
        }

        return get_string('view');
    }

    /**
     * Map warning severity to Bootstrap alert class suffix.
     *
     * @param string $severity Severity.
     * @return string
     */
    private function get_warning_class(string $severity): string {
        return match ($severity) {
            'danger', 'error', 'invalidated', 'restricted' => 'danger',
            'info', 'notice' => 'info',
            'success', 'verified' => 'success',
            default => 'warning',
        };
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
            return (new moodle_url($url))->out(false);
        }

        return '';
    }
}
