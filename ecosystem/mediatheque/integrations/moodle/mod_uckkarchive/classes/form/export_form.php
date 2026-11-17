<?php
// This file is part of Moodle - https://moodle.org/
//
// Moodle is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// any later version.

/**
 * Export form for UCKK archive packages.
 *
 * @package    mod_uckkarchive
 * @copyright  2026 Univers-Cité King Klown
 * @license    https://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later
 */

declare(strict_types=1);

namespace mod_uckkarchive\form;

defined('MOODLE_INTERNAL') || die();

global $CFG;
require_once($CFG->libdir . '/formslib.php');
require_once($CFG->dirroot . '/mod/uckkarchive/locallib.php');

use context_module;
use moodleform;
use stdClass;

/**
 * Form used to request or configure an archive export package.
 *
 * This form collects export intent and packaging options only. It does not:
 * - bypass archive visibility rules;
 * - expose restricted integrity records;
 * - validate archive items;
 * - revise archive history;
 * - create files directly;
 * - run long export generation work.
 *
 * Export creation, redaction, provenance packaging, event emission, and file
 * generation belong in service classes and scheduled/ad-hoc tasks.
 */
final class export_form extends moodleform {
    /** Export scope: whole visible archive. */
    private const SCOPE_ARCHIVE = 'archive';

    /** Export scope: selected item ids. */
    private const SCOPE_SELECTED_ITEMS = 'selected_items';

    /** Export scope: validated visible items. */
    private const SCOPE_VALIDATED_ITEMS = 'validated_items';

    /** Export scope: public visible items. */
    private const SCOPE_PUBLIC_ITEMS = 'public_items';

    /** Export scope: restricted integrity material. */
    private const SCOPE_RESTRICTED_INTEGRITY = 'restricted_integrity';

    /** Export format: JSON. */
    private const FORMAT_JSON = 'json';

    /** Export format: CSV. */
    private const FORMAT_CSV = 'csv';

    /** Export format: HTML. */
    private const FORMAT_HTML = 'html';

    /** Export format: ZIP package. */
    private const FORMAT_ZIP = 'zip';

    /** Export mode: generate immediately. */
    private const MODE_IMMEDIATE = 'immediate';

    /** Export mode: queue generation. */
    private const MODE_QUEUED = 'queued';

    /**
     * Define the form.
     */
    protected function definition(): void {
        $mform = $this->_form;

        $archive = $this->get_custom_record('archive');
        $context = $this->get_context();

        $mform->addElement('header', 'exportheader', get_string('archiveexport', 'uckkarchive'));

        if (!empty($archive->name)) {
            $mform->addElement(
                'static',
                'archivename',
                get_string('archive', 'uckkarchive'),
                format_string($archive->name)
            );
        }

        $this->add_scope_section($mform);
        $this->add_package_section($mform);
        $this->add_provenance_section($mform);
        $this->add_privacy_section($mform);
        $this->add_governance_section($mform, $context);
        $this->add_hidden_fields($mform);

        $buttonarray = [];
        $buttonarray[] = $mform->createElement('submit', 'submitbutton', get_string('requestexport', 'uckkarchive'));
        $buttonarray[] = $mform->createElement('cancel');

        $mform->addGroup($buttonarray, 'buttonar', '', [' '], false);
    }

    /**
     * Add export scope fields.
     *
     * @param \MoodleQuickForm $mform Form object.
     */
    private function add_scope_section(\MoodleQuickForm $mform): void {
        $mform->addElement('header', 'scopeheader', get_string('exportscope', 'uckkarchive'));

        $mform->addElement('select', 'scope', get_string('exportscope', 'uckkarchive'), $this->get_scope_options());
        $mform->setDefault('scope', self::SCOPE_VALIDATED_ITEMS);
        $mform->addRule('scope', null, 'required', null, 'client');
        $mform->addHelpButton('scope', 'exportscope', 'uckkarchive');

        $mform->addElement('textarea', 'itemids', get_string('exportitemids', 'uckkarchive'), [
            'rows' => 4,
            'cols' => 80,
        ]);
        $mform->setType('itemids', PARAM_RAW_TRIMMED);
        $mform->hideIf('itemids', 'scope', 'neq', self::SCOPE_SELECTED_ITEMS);
        $mform->addHelpButton('itemids', 'exportitemids', 'uckkarchive');

        $mform->addElement('select', 'statusfilter', get_string('exportstatusfilter', 'uckkarchive'), $this->get_status_filter_options());
        $mform->setDefault('statusfilter', '');

        $mform->addElement('select', 'typefilter', get_string('exporttypefilter', 'uckkarchive'), $this->get_type_filter_options());
        $mform->setDefault('typefilter', '');

        $mform->addElement('date_time_selector', 'timefrom', get_string('exporttimefrom', 'uckkarchive'), [
            'optional' => true,
        ]);
        $mform->setDefault('timefrom', 0);

        $mform->addElement('date_time_selector', 'timeto', get_string('exporttimeto', 'uckkarchive'), [
            'optional' => true,
        ]);
        $mform->setDefault('timeto', 0);
    }

    /**
     * Add package output fields.
     *
     * @param \MoodleQuickForm $mform Form object.
     */
    private function add_package_section(\MoodleQuickForm $mform): void {
        $mform->addElement('header', 'packageheader', get_string('exportpackage', 'uckkarchive'));

        $mform->addElement('select', 'format', get_string('exportformat', 'uckkarchive'), $this->get_format_options());
        $mform->setDefault('format', self::FORMAT_ZIP);
        $mform->addRule('format', null, 'required', null, 'client');

        $mform->addElement('select', 'mode', get_string('exportmode', 'uckkarchive'), $this->get_mode_options());
        $mform->setDefault('mode', self::MODE_QUEUED);
        $mform->addRule('mode', null, 'required', null, 'client');

        $mform->addElement('text', 'packagename', get_string('exportpackagename', 'uckkarchive'), [
            'size' => 64,
            'maxlength' => 255,
        ]);
        $mform->setType('packagename', PARAM_TEXT);
        $mform->addHelpButton('packagename', 'exportpackagename', 'uckkarchive');

        $mform->addElement('textarea', 'description', get_string('exportdescription', 'uckkarchive'), [
            'rows' => 4,
            'cols' => 80,
        ]);
        $mform->setType('description', PARAM_RAW);

        $mform->addElement('advcheckbox', 'includefiles', get_string('exportincludefiles', 'uckkarchive'));
        $mform->setDefault('includefiles', 1);

        $mform->addElement('advcheckbox', 'includeproofs', get_string('exportincludeproofs', 'uckkarchive'));
        $mform->setDefault('includeproofs', 1);

        $mform->addElement('advcheckbox', 'includekristals', get_string('exportincludekristals', 'uckkarchive'));
        $mform->setDefault('includekristals', 1);
    }

    /**
     * Add provenance and version fields.
     *
     * @param \MoodleQuickForm $mform Form object.
     */
    private function add_provenance_section(\MoodleQuickForm $mform): void {
        $mform->addElement('header', 'provenanceheader', get_string('exportprovenance', 'uckkarchive'));

        $mform->addElement('advcheckbox', 'includeprovenance', get_string('exportincludeprovenance', 'uckkarchive'));
        $mform->setDefault('includeprovenance', 1);

        $mform->addElement('advcheckbox', 'includeversions', get_string('exportincludeversions', 'uckkarchive'));
        $mform->setDefault('includeversions', 1);

        $mform->addElement('advcheckbox', 'includemetadata', get_string('exportincludemetadata', 'uckkarchive'));
        $mform->setDefault('includemetadata', 1);

        $mform->addElement('advcheckbox', 'includehashes', get_string('exportincludehashes', 'uckkarchive'));
        $mform->setDefault('includehashes', 1);

        $mform->addElement('advcheckbox', 'includeintegritysummary', get_string('exportincludeintegritysummary', 'uckkarchive'));
        $mform->setDefault('includeintegritysummary', 1);
        $mform->addHelpButton('includeintegritysummary', 'exportincludeintegritysummary', 'uckkarchive');
    }

    /**
     * Add privacy and redaction fields.
     *
     * @param \MoodleQuickForm $mform Form object.
     */
    private function add_privacy_section(\MoodleQuickForm $mform): void {
        $mform->addElement('header', 'privacyheader', get_string('exportprivacy', 'uckkarchive'));

        $mform->addElement('select', 'visibility', get_string('exportvisibility', 'uckkarchive'), $this->get_visibility_options());
        $mform->setDefault('visibility', UCKKARCHIVE_VISIBILITY_COURSE);
        $mform->addRule('visibility', null, 'required', null, 'client');

        $mform->addElement('advcheckbox', 'redactpersonaldata', get_string('exportredactpersonaldata', 'uckkarchive'));
        $mform->setDefault('redactpersonaldata', 1);

        $mform->addElement('advcheckbox', 'redactrestricted', get_string('exportredactrestricted', 'uckkarchive'));
        $mform->setDefault('redactrestricted', 1);

        $mform->addElement('advcheckbox', 'includeprivatefields', get_string('exportincludeprivatefields', 'uckkarchive'));
        $mform->setDefault('includeprivatefields', 0);
        $mform->addHelpButton('includeprivatefields', 'exportincludeprivatefields', 'uckkarchive');

        if (!$this->can_export_restricted()) {
            $mform->freeze('includeprivatefields');
        }
    }

    /**
     * Add governance fields.
     *
     * @param \MoodleQuickForm $mform Form object.
     * @param context_module $context Module context.
     */
    private function add_governance_section(\MoodleQuickForm $mform, context_module $context): void {
        $mform->addElement('header', 'governanceheader', get_string('exportgovernance', 'uckkarchive'));

        $mform->addElement('textarea', 'reason', get_string('exportreason', 'uckkarchive'), [
            'rows' => 5,
            'cols' => 80,
        ]);
        $mform->setType('reason', PARAM_RAW_TRIMMED);
        $mform->addRule('reason', null, 'required', null, 'client');
        $mform->addHelpButton('reason', 'exportreason', 'uckkarchive');

        $mform->addElement('textarea', 'auditnote', get_string('exportauditnote', 'uckkarchive'), [
            'rows' => 4,
            'cols' => 80,
        ]);
        $mform->setType('auditnote', PARAM_RAW_TRIMMED);

        $mform->addElement('static', 'exportnotice', get_string('exportnotice', 'uckkarchive'), get_string('exportnotice_desc', 'uckkarchive'));

        $mform->addElement('advcheckbox', 'confirmpolicy', get_string('exportconfirmpolicy', 'uckkarchive'));
        $mform->setDefault('confirmpolicy', 0);
        $mform->addRule('confirmpolicy', get_string('exportconfirmpolicyrequired', 'uckkarchive'), 'required', null, 'client');

        $mform->addElement('hidden', 'contextid', $context->id);
        $mform->setType('contextid', PARAM_INT);
    }

    /**
     * Add hidden identifiers.
     *
     * @param \MoodleQuickForm $mform Form object.
     */
    private function add_hidden_fields(\MoodleQuickForm $mform): void {
        foreach ([
            'id',
            'archiveid',
            'exportid',
            'returnurl',
        ] as $field) {
            $mform->addElement('hidden', $field);
        }

        $mform->setType('id', PARAM_INT);
        $mform->setType('archiveid', PARAM_INT);
        $mform->setType('exportid', PARAM_INT);
        $mform->setType('returnurl', PARAM_LOCALURL);
    }

    /**
     * Validate form data.
     *
     * @param array $data Submitted data.
     * @param array $files Submitted files.
     * @return array<string, string>
     */
    public function validation($data, $files): array {
        $errors = parent::validation($data, $files);

        $scope = (string)($data['scope'] ?? '');
        $format = (string)($data['format'] ?? '');
        $mode = (string)($data['mode'] ?? '');
        $visibility = (string)($data['visibility'] ?? '');

        if (!array_key_exists($scope, $this->get_scope_options())) {
            $errors['scope'] = get_string('invalidexportscope', 'uckkarchive');
        }

        if (!array_key_exists($format, $this->get_format_options())) {
            $errors['format'] = get_string('invalidexportformat', 'uckkarchive');
        }

        if (!array_key_exists($mode, $this->get_mode_options())) {
            $errors['mode'] = get_string('invalidexportmode', 'uckkarchive');
        }

        if (!array_key_exists($visibility, $this->get_visibility_options())) {
            $errors['visibility'] = get_string('invalidexportvisibility', 'uckkarchive');
        }

        if ($scope === self::SCOPE_SELECTED_ITEMS && empty($this->parse_item_ids((string)($data['itemids'] ?? '')))) {
            $errors['itemids'] = get_string('exportitemidsrequired', 'uckkarchive');
        }

        if (!empty($data['timefrom']) && !empty($data['timeto']) && (int)$data['timeto'] <= (int)$data['timefrom']) {
            $errors['timeto'] = get_string('exporttimetomustbeafterfrom', 'uckkarchive');
        }

        $restrictedexportrequested = $scope === self::SCOPE_RESTRICTED_INTEGRITY
            || $visibility === UCKKARCHIVE_VISIBILITY_RESTRICTED_INTEGRITY
            || !empty($data['includeprivatefields']);

        if ($restrictedexportrequested && !$this->can_export_restricted()) {
            if ($scope === self::SCOPE_RESTRICTED_INTEGRITY) {
                $errors['scope'] = get_string('exportrestrictednotallowed', 'uckkarchive');
            }

            if ($visibility === UCKKARCHIVE_VISIBILITY_RESTRICTED_INTEGRITY) {
                $errors['visibility'] = get_string('exportrestrictednotallowed', 'uckkarchive');
            }

            if (!empty($data['includeprivatefields'])) {
                $errors['includeprivatefields'] = get_string('exportrestrictednotallowed', 'uckkarchive');
            }
        }

        if ($restrictedexportrequested && empty($data['redactrestricted']) && !$this->can_export_unredacted()) {
            $errors['redactrestricted'] = get_string('exportunredactednotallowed', 'uckkarchive');
        }

        if (empty(trim((string)($data['reason'] ?? '')))) {
            $errors['reason'] = get_string('required');
        }

        if (empty($data['confirmpolicy'])) {
            $errors['confirmpolicy'] = get_string('exportconfirmpolicyrequired', 'uckkarchive');
        }

        return $errors;
    }

    /**
     * Convert submitted values into a service-friendly options object.
     *
     * @param stdClass $data Submitted form data.
     * @return stdClass
     */
    public function export_options_from_data(stdClass $data): stdClass {
        $options = new stdClass();

        $options->cmid = (int)($data->id ?? 0);
        $options->archiveid = (int)($data->archiveid ?? 0);
        $options->exportid = (int)($data->exportid ?? 0);
        $options->contextid = (int)($data->contextid ?? 0);

        $options->scope = (string)$data->scope;
        $options->itemids = $this->parse_item_ids((string)($data->itemids ?? ''));
        $options->statusfilter = clean_param((string)($data->statusfilter ?? ''), PARAM_ALPHANUMEXT);
        $options->typefilter = clean_param((string)($data->typefilter ?? ''), PARAM_ALPHANUMEXT);
        $options->timefrom = (int)($data->timefrom ?? 0);
        $options->timeto = (int)($data->timeto ?? 0);

        $options->format = (string)$data->format;
        $options->mode = (string)$data->mode;
        $options->packagename = trim((string)($data->packagename ?? ''));
        $options->description = trim((string)($data->description ?? ''));

        $options->includefiles = !empty($data->includefiles);
        $options->includeproofs = !empty($data->includeproofs);
        $options->includekristals = !empty($data->includekristals);
        $options->includeprovenance = !empty($data->includeprovenance);
        $options->includeversions = !empty($data->includeversions);
        $options->includemetadata = !empty($data->includemetadata);
        $options->includehashes = !empty($data->includehashes);
        $options->includeintegritysummary = !empty($data->includeintegritysummary);

        $options->visibility = (string)$data->visibility;
        $options->redactpersonaldata = !empty($data->redactpersonaldata);
        $options->redactrestricted = !empty($data->redactrestricted);
        $options->includeprivatefields = !empty($data->includeprivatefields);

        $options->reason = trim((string)($data->reason ?? ''));
        $options->auditnote = trim((string)($data->auditnote ?? ''));
        $options->returnurl = (string)($data->returnurl ?? '');

        return $options;
    }

    /**
     * Get module context from custom data.
     *
     * @return context_module
     */
    private function get_context(): context_module {
        if (!empty($this->_customdata['context']) && $this->_customdata['context'] instanceof context_module) {
            return $this->_customdata['context'];
        }

        throw new \coding_exception('export_form requires a module context in customdata.');
    }

    /**
     * Get a custom data record.
     *
     * @param string $key Custom data key.
     * @return stdClass
     */
    private function get_custom_record(string $key): stdClass {
        if (empty($this->_customdata[$key])) {
            return new stdClass();
        }

        return (object)$this->_customdata[$key];
    }

    /**
     * Whether this user/session can request restricted export data.
     *
     * @return bool
     */
    private function can_export_restricted(): bool {
        return !empty($this->_customdata['canexportrestricted']);
    }

    /**
     * Whether this user/session can request unredacted restricted export data.
     *
     * @return bool
     */
    private function can_export_unredacted(): bool {
        return !empty($this->_customdata['canexportunredacted']);
    }

    /**
     * Parse comma/newline/space separated item ids.
     *
     * @param string $raw Raw item ids.
     * @return int[]
     */
    private function parse_item_ids(string $raw): array {
        $raw = trim($raw);

        if ($raw === '') {
            return [];
        }

        $parts = preg_split('/[\s,;]+/', $raw) ?: [];
        $ids = [];

        foreach ($parts as $part) {
            $id = (int)$part;

            if ($id > 0) {
                $ids[$id] = $id;
            }
        }

        return array_values($ids);
    }

    /**
     * Export scope options.
     *
     * @return array<string, string>
     */
    private function get_scope_options(): array {
        $options = [
            self::SCOPE_ARCHIVE => get_string('exportscope:archive', 'uckkarchive'),
            self::SCOPE_SELECTED_ITEMS => get_string('exportscope:selecteditems', 'uckkarchive'),
            self::SCOPE_VALIDATED_ITEMS => get_string('exportscope:validateditems', 'uckkarchive'),
            self::SCOPE_PUBLIC_ITEMS => get_string('exportscope:publicitems', 'uckkarchive'),
        ];

        if ($this->can_export_restricted()) {
            $options[self::SCOPE_RESTRICTED_INTEGRITY] = get_string('exportscope:restrictedintegrity', 'uckkarchive');
        }

        return $options;
    }

    /**
     * Export format options.
     *
     * @return array<string, string>
     */
    private function get_format_options(): array {
        return [
            self::FORMAT_ZIP => get_string('exportformat:zip', 'uckkarchive'),
            self::FORMAT_JSON => get_string('exportformat:json', 'uckkarchive'),
            self::FORMAT_CSV => get_string('exportformat:csv', 'uckkarchive'),
            self::FORMAT_HTML => get_string('exportformat:html', 'uckkarchive'),
        ];
    }

    /**
     * Export generation mode options.
     *
     * @return array<string, string>
     */
    private function get_mode_options(): array {
        return [
            self::MODE_QUEUED => get_string('exportmode:queued', 'uckkarchive'),
            self::MODE_IMMEDIATE => get_string('exportmode:immediate', 'uckkarchive'),
        ];
    }

    /**
     * Status filter options.
     *
     * @return array<string, string>
     */
    private function get_status_filter_options(): array {
        return ['' => get_string('all')] + uckkarchive_get_status_options();
    }

    /**
     * Type filter options.
     *
     * @return array<string, string>
     */
    private function get_type_filter_options(): array {
        return ['' => get_string('all')] + uckkarchive_get_item_type_options();
    }

    /**
     * Visibility options.
     *
     * @return array<string, string>
     */
    private function get_visibility_options(): array {
        $options = uckkarchive_get_visibility_options();

        if (!$this->can_export_restricted()) {
            unset($options[UCKKARCHIVE_VISIBILITY_RESTRICTED_INTEGRITY]);
        }

        return $options;
    }
}
