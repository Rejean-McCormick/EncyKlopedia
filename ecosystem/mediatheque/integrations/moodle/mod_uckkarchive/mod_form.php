<?php
// This file is part of Moodle - https://moodle.org/
//
// Moodle is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// any later version.

/**
 * Activity instance form for UCKK Archives.
 *
 * @package    mod_uckkarchive
 * @copyright  2026 Univers-Cité King Klown
 * @license    https://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later
 */

defined('MOODLE_INTERNAL') || die();

require_once($CFG->dirroot . '/course/moodleform_mod.php');

/**
 * UCKK Archive activity form.
 *
 * This form configures one Archive activity instance. It does not validate
 * archive items, revise item history, export packages, decide integrity cases,
 * or publish restricted evidence. Those actions must remain in service classes
 * and capability-checked controllers.
 */
class mod_uckkarchive_mod_form extends moodleform_mod {
    /**
     * Define the activity settings form.
     */
    public function definition(): void {
        $mform = $this->_form;

        $this->add_general_section($mform);
        $this->add_scope_section($mform);
        $this->add_item_policy_section($mform);
        $this->add_validation_section($mform);
        $this->add_revision_section($mform);
        $this->add_export_section($mform);
        $this->add_integrity_section($mform);

        $this->standard_coursemodule_elements();
        $this->add_action_buttons();
    }

    /**
     * Add general Archive settings.
     *
     * @param MoodleQuickForm $mform Form object.
     */
    private function add_general_section(MoodleQuickForm $mform): void {
        $mform->addElement('header', 'general', get_string('general', 'form'));

        $mform->addElement('text', 'name', get_string('archivename', 'uckkarchive'), [
            'size' => 64,
            'maxlength' => 255,
        ]);
        $mform->setType('name', PARAM_TEXT);
        $mform->addRule('name', null, 'required', null, 'client');
        $mform->addHelpButton('name', 'archivename', 'uckkarchive');

        $this->standard_intro_elements(get_string('archiveintro', 'uckkarchive'));

        $mform->addElement('text', 'archivecode', get_string('archivecode', 'uckkarchive'), [
            'size' => 32,
            'maxlength' => 100,
        ]);
        $mform->setType('archivecode', PARAM_ALPHANUMEXT);
        $mform->addHelpButton('archivecode', 'archivecode', 'uckkarchive');

        $mform->addElement('select', 'archivetype', get_string('archivetype', 'uckkarchive'), $this->get_archive_type_options());
        $mform->setDefault('archivetype', 'course_memory');
        $mform->addRule('archivetype', null, 'required', null, 'client');

        $mform->addElement('select', 'status', get_string('archivestatus', 'uckkarchive'), $this->get_status_options());
        $mform->setDefault('status', 'draft');
        $mform->addRule('status', null, 'required', null, 'client');

        $mform->addElement('select', 'visibility', get_string('visibility', 'uckkarchive'), $this->get_visibility_options());
        $mform->setDefault('visibility', 'course');
        $mform->addRule('visibility', null, 'required', null, 'client');
        $mform->addHelpButton('visibility', 'visibility', 'uckkarchive');
    }

    /**
     * Add archive scope and purpose fields.
     *
     * @param MoodleQuickForm $mform Form object.
     */
    private function add_scope_section(MoodleQuickForm $mform): void {
        $mform->addElement('header', 'archivescopeheader', get_string('archivescope', 'uckkarchive'));

        $mform->addElement('textarea', 'purpose', get_string('archivepurpose', 'uckkarchive'), [
            'rows' => 6,
            'cols' => 80,
        ]);
        $mform->setType('purpose', PARAM_RAW);
        $mform->addRule('purpose', null, 'required', null, 'client');
        $mform->addHelpButton('purpose', 'archivepurpose', 'uckkarchive');

        $mform->addElement('textarea', 'scope', get_string('archivescopefield', 'uckkarchive'), [
            'rows' => 6,
            'cols' => 80,
        ]);
        $mform->setType('scope', PARAM_RAW);
        $mform->addHelpButton('scope', 'archivescopefield', 'uckkarchive');

        $mform->addElement('textarea', 'publicsummary', get_string('publicsummary', 'uckkarchive'), [
            'rows' => 5,
            'cols' => 80,
        ]);
        $mform->setType('publicsummary', PARAM_RAW);
        $mform->addHelpButton('publicsummary', 'publicsummary', 'uckkarchive');
    }

    /**
     * Add archive item policy fields.
     *
     * @param MoodleQuickForm $mform Form object.
     */
    private function add_item_policy_section(MoodleQuickForm $mform): void {
        $mform->addElement('header', 'itempolicyheader', get_string('archiveitempolicy', 'uckkarchive'));

        $mform->addElement('advcheckbox', 'allowitems', get_string('allowarchiveitems', 'uckkarchive'));
        $mform->setDefault('allowitems', 1);

        $mform->addElement('advcheckbox', 'allowproofs', get_string('allowproofs', 'uckkarchive'));
        $mform->setDefault('allowproofs', 1);

        $mform->addElement('advcheckbox', 'allowkristals', get_string('allowkristals', 'uckkarchive'));
        $mform->setDefault('allowkristals', 1);

        $mform->addElement('advcheckbox', 'allowportfolioitems', get_string('allowportfolioitems', 'uckkarchive'));
        $mform->setDefault('allowportfolioitems', 1);

        $mform->addElement('select', 'defaultitemtype', get_string('defaultitemtype', 'uckkarchive'), $this->get_item_type_options());
        $mform->setDefault('defaultitemtype', 'proof');

        $mform->addElement('select', 'defaultprovenance', get_string('defaultprovenance', 'uckkarchive'), $this->get_provenance_options());
        $mform->setDefault('defaultprovenance', 'human');

        $mform->addElement('textarea', 'provenancepolicy', get_string('provenancepolicy', 'uckkarchive'), [
            'rows' => 6,
            'cols' => 80,
        ]);
        $mform->setType('provenancepolicy', PARAM_RAW);
        $mform->addRule('provenancepolicy', null, 'required', null, 'client');
        $mform->addHelpButton('provenancepolicy', 'provenancepolicy', 'uckkarchive');

        $mform->addElement('textarea', 'evidencepolicy', get_string('evidencepolicy', 'uckkarchive'), [
            'rows' => 6,
            'cols' => 80,
        ]);
        $mform->setType('evidencepolicy', PARAM_RAW);
        $mform->addHelpButton('evidencepolicy', 'uckkarchive');
    }

    /**
     * Add validation settings.
     *
     * @param MoodleQuickForm $mform Form object.
     */
    private function add_validation_section(MoodleQuickForm $mform): void {
        $mform->addElement('header', 'validationheader', get_string('archivevalidation', 'uckkarchive'));

        $mform->addElement('advcheckbox', 'requirevalidation', get_string('requirevalidation', 'uckkarchive'));
        $mform->setDefault('requirevalidation', 1);
        $mform->addHelpButton('requirevalidation', 'requirevalidation', 'uckkarchive');

        $mform->addElement('select', 'defaultvalidationstate', get_string('defaultvalidationstate', 'uckkarchive'), $this->get_validation_state_options());
        $mform->setDefault('defaultvalidationstate', 'unverified');

        $mform->addElement('select', 'validationworkflow', get_string('validationworkflow', 'uckkarchive'), $this->get_validation_workflow_options());
        $mform->setDefault('validationworkflow', 'human_review');

        $mform->addElement('textarea', 'validationcriteria', get_string('validationcriteria', 'uckkarchive'), [
            'rows' => 7,
            'cols' => 80,
        ]);
        $mform->setType('validationcriteria', PARAM_RAW);
        $mform->addHelpButton('validationcriteria', 'validationcriteria', 'uckkarchive');

        $mform->addElement('advcheckbox', 'allowcontestation', get_string('allowcontestation', 'uckkarchive'));
        $mform->setDefault('allowcontestation', 1);

        $mform->addElement('text', 'contestabilitydays', get_string('contestabilitydays', 'uckkarchive'), [
            'size' => 6,
            'maxlength' => 5,
        ]);
        $mform->setType('contestabilitydays', PARAM_INT);
        $mform->setDefault('contestabilitydays', 30);
    }

    /**
     * Add revision and retention settings.
     *
     * @param MoodleQuickForm $mform Form object.
     */
    private function add_revision_section(MoodleQuickForm $mform): void {
        $mform->addElement('header', 'revisionheader', get_string('revisionandretention', 'uckkarchive'));

        $mform->addElement('advcheckbox', 'forcerevisions', get_string('forcerevisions', 'uckkarchive'));
        $mform->setDefault('forcerevisions', 1);
        $mform->addHelpButton('forcerevisions', 'forcerevisions', 'uckkarchive');

        $mform->addElement('select', 'revisionpolicy', get_string('revisionpolicy', 'uckkarchive'), $this->get_revision_policy_options());
        $mform->setDefault('revisionpolicy', 'version_on_change');

        $mform->addElement('select', 'retentionpolicy', get_string('retentionpolicy', 'uckkarchive'), $this->get_retention_policy_options());
        $mform->setDefault('retentionpolicy', 'institutional_memory');

        $mform->addElement('textarea', 'retentionnotes', get_string('retentionnotes', 'uckkarchive'), [
            'rows' => 5,
            'cols' => 80,
        ]);
        $mform->setType('retentionnotes', PARAM_RAW);
        $mform->addHelpButton('retentionnotes', 'retentionnotes', 'uckkarchive');
    }

    /**
     * Add export settings.
     *
     * @param MoodleQuickForm $mform Form object.
     */
    private function add_export_section(MoodleQuickForm $mform): void {
        $mform->addElement('header', 'exportheader', get_string('archiveexport', 'uckkarchive'));

        $mform->addElement('select', 'exportpolicy', get_string('exportpolicy', 'uckkarchive'), $this->get_export_policy_options());
        $mform->setDefault('exportpolicy', 'validated_only');
        $mform->addHelpButton('exportpolicy', 'exportpolicy', 'uckkarchive');

        $mform->addElement('advcheckbox', 'allowexports', get_string('allowexports', 'uckkarchive'));
        $mform->setDefault('allowexports', 1);

        $mform->addElement('advcheckbox', 'includefilesinexports', get_string('includefilesinexports', 'uckkarchive'));
        $mform->setDefault('includefilesinexports', 1);

        $mform->addElement('advcheckbox', 'includerevisionsinexports', get_string('includerevisionsinexports', 'uckkarchive'));
        $mform->setDefault('includerevisionsinexports', 1);

        $mform->addElement('advcheckbox', 'redactrestrictedexports', get_string('redactrestrictedexports', 'uckkarchive'));
        $mform->setDefault('redactrestrictedexports', 1);
    }

    /**
     * Add integrity and AI governance settings.
     *
     * @param MoodleQuickForm $mform Form object.
     */
    private function add_integrity_section(MoodleQuickForm $mform): void {
        $mform->addElement('header', 'integrityheader', get_string('integrityandai', 'uckkarchive'));

        $mform->addElement('advcheckbox', 'integrityrequired', get_string('integrityrequired', 'uckkarchive'));
        $mform->setDefault('integrityrequired', 1);
        $mform->addHelpButton('integrityrequired', 'integrityrequired', 'uckkarchive');

        $mform->addElement('advcheckbox', 'allowailogs', get_string('allowailogs', 'uckkarchive'));
        $mform->setDefault('allowailogs', 1);

        $mform->addElement('textarea', 'aipolicy', get_string('aipolicy', 'uckkarchive'), [
            'rows' => 5,
            'cols' => 80,
        ]);
        $mform->setType('aipolicy', PARAM_RAW);
        $mform->setDefault('aipolicy', get_string('defaultaipolicy', 'uckkarchive'));
        $mform->addHelpButton('aipolicy', 'aipolicy', 'uckkarchive');

        $mform->addElement('textarea', 'integritynotes', get_string('integritynotes', 'uckkarchive'), [
            'rows' => 5,
            'cols' => 80,
        ]);
        $mform->setType('integritynotes', PARAM_RAW);
        $mform->addHelpButton('integritynotes', 'integritynotes', 'uckkarchive');
    }

    /**
     * Validate submitted form data.
     *
     * @param array $data Submitted data.
     * @param array $files Submitted files.
     * @return array<string, string> Fieldname => error message.
     */
    public function validation($data, $files): array {
        $errors = parent::validation($data, $files);

        if (!empty($data['archivecode']) && !preg_match('/^[A-Za-z0-9_-]+$/', (string)$data['archivecode'])) {
            $errors['archivecode'] = get_string('invalidarchivecode', 'uckkarchive');
        }

        foreach (['purpose', 'provenancepolicy'] as $requiredfield) {
            if (trim((string)($data[$requiredfield] ?? '')) === '') {
                $errors[$requiredfield] = get_string('required');
            }
        }

        if (isset($data['contestabilitydays']) && (int)$data['contestabilitydays'] < 0) {
            $errors['contestabilitydays'] = get_string('contestabilitydaysinvalid', 'uckkarchive');
        }

        if (empty($data['allowitems']) && empty($data['allowproofs']) && empty($data['allowkristals']) && empty($data['allowportfolioitems'])) {
            $errors['allowitems'] = get_string('atleastonearchivetypeenabled', 'uckkarchive');
        }

        return $errors;
    }

    /**
     * Preprocess defaults when editing an existing Archive instance.
     *
     * @param array $defaultvalues Default form values.
     */
    public function data_preprocessing(&$defaultvalues): void {
        $defaults = [
            'archivecode' => '',
            'archivetype' => 'course_memory',
            'status' => 'draft',
            'visibility' => 'course',
            'purpose' => '',
            'scope' => '',
            'publicsummary' => '',
            'allowitems' => 1,
            'allowproofs' => 1,
            'allowkristals' => 1,
            'allowportfolioitems' => 1,
            'defaultitemtype' => 'proof',
            'defaultprovenance' => 'human',
            'provenancepolicy' => '',
            'evidencepolicy' => '',
            'requirevalidation' => 1,
            'defaultvalidationstate' => 'unverified',
            'validationworkflow' => 'human_review',
            'validationcriteria' => '',
            'allowcontestation' => 1,
            'contestabilitydays' => 30,
            'forcerevisions' => 1,
            'revisionpolicy' => 'version_on_change',
            'retentionpolicy' => 'institutional_memory',
            'retentionnotes' => '',
            'exportpolicy' => 'validated_only',
            'allowexports' => 1,
            'includefilesinexports' => 1,
            'includerevisionsinexports' => 1,
            'redactrestrictedexports' => 1,
            'integrityrequired' => 1,
            'allowailogs' => 1,
            'aipolicy' => get_string('defaultaipolicy', 'uckkarchive'),
            'integritynotes' => '',
        ];

        foreach ($defaults as $field => $value) {
            if (!isset($defaultvalues[$field])) {
                $defaultvalues[$field] = $value;
            }
        }
    }

    /**
     * Add custom completion rules.
     *
     * @return array<int, string>
     */
    public function add_completion_rules(): array {
        $mform = $this->_form;

        $mform->addElement('advcheckbox', 'completionrequireitem', '', get_string('completionrequireitem', 'uckkarchive'));
        $mform->setDefault('completionrequireitem', 0);

        $mform->addElement('advcheckbox', 'completionrequirevalidateditem', '', get_string('completionrequirevalidateditem', 'uckkarchive'));
        $mform->setDefault('completionrequirevalidateditem', 0);

        return [
            'completionrequireitem',
            'completionrequirevalidateditem',
        ];
    }

    /**
     * Whether custom completion rules are enabled.
     *
     * @param array $data Submitted form data.
     * @return bool
     */
    public function completion_rule_enabled($data): bool {
        return !empty($data['completionrequireitem']) || !empty($data['completionrequirevalidateditem']);
    }

    /**
     * Archive type options.
     *
     * @return array<string, string>
     */
    private function get_archive_type_options(): array {
        return [
            'course_memory' => get_string('archivetype:course_memory', 'uckkarchive'),
            'proof_repository' => get_string('archivetype:proof_repository', 'uckkarchive'),
            'portfolio_archive' => get_string('archivetype:portfolio_archive', 'uckkarchive'),
            'assembly_memory' => get_string('archivetype:assembly_memory', 'uckkarchive'),
            'challenge_output' => get_string('archivetype:challenge_output', 'uckkarchive'),
            'kristal_library' => get_string('archivetype:kristal_library', 'uckkarchive'),
            'integrity_memory' => get_string('archivetype:integrity_memory', 'uckkarchive'),
        ];
    }

    /**
     * Archive status options.
     *
     * @return array<string, string>
     */
    private function get_status_options(): array {
        return [
            'draft' => get_string('status:draft', 'uckkarchive'),
            'active' => get_string('status:active', 'uckkarchive'),
            'hidden' => get_string('status:hidden', 'uckkarchive'),
            'pending_review' => get_string('status:pendingreview', 'uckkarchive'),
            'validated' => get_string('status:validated', 'uckkarchive'),
            'contested' => get_string('status:contested', 'uckkarchive'),
            'archived' => get_string('status:archived', 'uckkarchive'),
        ];
    }

    /**
     * Visibility options.
     *
     * @return array<string, string>
     */
    private function get_visibility_options(): array {
        return [
            'private' => get_string('visibility:private', 'uckkarchive'),
            'course' => get_string('visibility:course', 'uckkarchive'),
            'cohort' => get_string('visibility:cohort', 'uckkarchive'),
            'program' => get_string('visibility:program', 'uckkarchive'),
            'institution' => get_string('visibility:institution', 'uckkarchive'),
            'public' => get_string('visibility:public', 'uckkarchive'),
            'restricted_integrity' => get_string('visibility:restricted_integrity', 'uckkarchive'),
        ];
    }

    /**
     * Archive item type options.
     *
     * @return array<string, string>
     */
    private function get_item_type_options(): array {
        return [
            'proof' => get_string('itemtype:proof', 'uckkarchive'),
            'decision' => get_string('itemtype:decision', 'uckkarchive'),
            'minutes' => get_string('itemtype:minutes', 'uckkarchive'),
            'challenge_result' => get_string('itemtype:challenge_result', 'uckkarchive'),
            'course_work' => get_string('itemtype:course_work', 'uckkarchive'),
            'portfolio_item' => get_string('itemtype:portfolio_item', 'uckkarchive'),
            'kristal' => get_string('itemtype:kristal', 'uckkarchive'),
            'integrity_summary' => get_string('itemtype:integrity_summary', 'uckkarchive'),
            'public_summary' => get_string('itemtype:public_summary', 'uckkarchive'),
        ];
    }

    /**
     * Provenance options.
     *
     * @return array<string, string>
     */
    private function get_provenance_options(): array {
        return [
            'human' => get_string('provenance:human', 'uckkarchive'),
            'ai_assisted' => get_string('provenance:ai_assisted', 'uckkarchive'),
            'imported' => get_string('provenance:imported', 'uckkarchive'),
            'system' => get_string('provenance:system', 'uckkarchive'),
            'archive' => get_string('provenance:archive', 'uckkarchive'),
            'assembly' => get_string('provenance:assembly', 'uckkarchive'),
            'challenge' => get_string('provenance:challenge', 'uckkarchive'),
            'integrity' => get_string('provenance:integrity', 'uckkarchive'),
        ];
    }

    /**
     * Validation state options.
     *
     * @return array<string, string>
     */
    private function get_validation_state_options(): array {
        return [
            'unverified' => get_string('validation:unverified', 'uckkarchive'),
            'human_reviewed' => get_string('validation:human_reviewed', 'uckkarchive'),
            'verified' => get_string('validation:verified', 'uckkarchive'),
            'contested' => get_string('validation:contested', 'uckkarchive'),
            'invalidated' => get_string('validation:invalidated', 'uckkarchive'),
            'archived' => get_string('validation:archived', 'uckkarchive'),
        ];
    }

    /**
     * Validation workflow options.
     *
     * @return array<string, string>
     */
    private function get_validation_workflow_options(): array {
        return [
            'none' => get_string('validationworkflow:none', 'uckkarchive'),
            'human_review' => get_string('validationworkflow:human_review', 'uckkarchive'),
            'archivist_review' => get_string('validationworkflow:archivist_review', 'uckkarchive'),
            'integrity_review' => get_string('validationworkflow:integrity_review', 'uckkarchive'),
        ];
    }

    /**
     * Revision policy options.
     *
     * @return array<string, string>
     */
    private function get_revision_policy_options(): array {
        return [
            'none' => get_string('revisionpolicy:none', 'uckkarchive'),
            'version_on_change' => get_string('revisionpolicy:version_on_change', 'uckkarchive'),
            'version_on_validation' => get_string('revisionpolicy:version_on_validation', 'uckkarchive'),
            'version_every_edit' => get_string('revisionpolicy:version_every_edit', 'uckkarchive'),
        ];
    }

    /**
     * Retention policy options.
     *
     * @return array<string, string>
     */
    private function get_retention_policy_options(): array {
        return [
            'course_lifetime' => get_string('retentionpolicy:course_lifetime', 'uckkarchive'),
            'program_lifetime' => get_string('retentionpolicy:program_lifetime', 'uckkarchive'),
            'institutional_memory' => get_string('retentionpolicy:institutional_memory', 'uckkarchive'),
            'restricted_integrity' => get_string('retentionpolicy:restricted_integrity', 'uckkarchive'),
        ];
    }

    /**
     * Export policy options.
     *
     * @return array<string, string>
     */
    private function get_export_policy_options(): array {
        return [
            'none' => get_string('exportpolicy:none', 'uckkarchive'),
            'validated_only' => get_string('exportpolicy:validated_only', 'uckkarchive'),
            'public_only' => get_string('exportpolicy:public_only', 'uckkarchive'),
            'full_with_revisions' => get_string('exportpolicy:full_with_revisions', 'uckkarchive'),
            'restricted_redacted' => get_string('exportpolicy:restricted_redacted', 'uckkarchive'),
        ];
    }
}