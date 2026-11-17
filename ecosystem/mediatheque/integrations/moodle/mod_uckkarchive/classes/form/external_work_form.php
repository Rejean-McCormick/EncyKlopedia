<?php
// This file is part of Moodle - https://moodle.org/
//
// Moodle is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// any later version.

/**
 * External work create/edit form for mod_uckkarchive.
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

use context_module;
use moodleform;

/**
 * Form used to create or edit an external work reference.
 *
 * External works are archive-owned references to third-party or outside
 * material. They support media source records, content advisories, teaching
 * notes, cultural protocol notes, rights statements, and export manifests.
 *
 * This form collects metadata only. It does not decide whether the work may be
 * shown, exported, used in teaching, or attached to media. Those decisions
 * belong to capability-checked controllers, local policy classes, and service
 * classes.
 */
final class external_work_form extends moodleform {
    /** Default work type. */
    private const DEFAULT_WORKTYPE = 'other';

    /** Default status. */
    private const DEFAULT_STATUS = 'draft';

    /** Default visibility. */
    private const DEFAULT_VISIBILITY = 'course';

    /** Default audience suitability. */
    private const DEFAULT_AUDIENCE = 'guided';

    /** Default rights status. */
    private const DEFAULT_RIGHTS = 'unknown';

    /**
     * Define form.
     */
    protected function definition(): void {
        $mform = $this->_form;

        $this->add_identity_section($mform);
        $this->add_source_section($mform);
        $this->add_rights_section($mform);
        $this->add_governance_section($mform);
        $this->add_teaching_and_protocol_section($mform);
        $this->add_metadata_section($mform);
        $this->add_hidden_fields($mform);

        $this->add_action_buttons(true, get_string('saveexternalwork', 'uckkarchive'));
    }

    /**
     * Add external work identity fields.
     *
     * @param \MoodleQuickForm $mform Form object.
     * @return void
     */
    private function add_identity_section(\MoodleQuickForm $mform): void {
        $mform->addElement('header', 'identityheader', get_string('externalworkidentity', 'uckkarchive'));

        $mform->addElement('text', 'title', get_string('externalworktitle', 'uckkarchive'), [
            'size' => 80,
            'maxlength' => 255,
        ]);
        $mform->setType('title', PARAM_TEXT);
        $mform->addRule('title', null, 'required', null, 'client');

        $mform->addElement('text', 'subtitle', get_string('externalworksubtitle', 'uckkarchive'), [
            'size' => 80,
            'maxlength' => 255,
        ]);
        $mform->setType('subtitle', PARAM_TEXT);

        $mform->addElement('select', 'worktype', get_string('externalworktype', 'uckkarchive'),
            $this->get_work_type_options()
        );
        $mform->setDefault('worktype', self::DEFAULT_WORKTYPE);
        $mform->addRule('worktype', null, 'required', null, 'client');

        $mform->addElement('text', 'creator', get_string('externalworkcreator', 'uckkarchive'), [
            'size' => 80,
            'maxlength' => 255,
        ]);
        $mform->setType('creator', PARAM_TEXT);

        $mform->addElement('text', 'publisher', get_string('externalworkpublisher', 'uckkarchive'), [
            'size' => 80,
            'maxlength' => 255,
        ]);
        $mform->setType('publisher', PARAM_TEXT);

        $mform->addElement('text', 'publicationyear', get_string('externalworkpublicationyear', 'uckkarchive'), [
            'size' => 12,
            'maxlength' => 4,
        ]);
        $mform->setType('publicationyear', PARAM_INT);
        $mform->addHelpButton('publicationyear', 'externalworkpublicationyear', 'uckkarchive');

        $mform->addElement('text', 'language', get_string('externalworklanguage', 'uckkarchive'), [
            'size' => 16,
            'maxlength' => 32,
        ]);
        $mform->setType('language', PARAM_ALPHANUMEXT);
        $mform->addHelpButton('language', 'externalworklanguage', 'uckkarchive');
    }

    /**
     * Add source and identifier fields.
     *
     * @param \MoodleQuickForm $mform Form object.
     * @return void
     */
    private function add_source_section(\MoodleQuickForm $mform): void {
        $mform->addElement('header', 'sourceheader', get_string('externalworksource', 'uckkarchive'));

        $mform->addElement('text', 'sourceurl', get_string('externalworksourceurl', 'uckkarchive'), [
            'size' => 96,
            'maxlength' => 2048,
        ]);
        $mform->setType('sourceurl', PARAM_URL);
        $mform->addHelpButton('sourceurl', 'externalworksourceurl', 'uckkarchive');

        $mform->addElement('text', 'identifier', get_string('externalworkidentifier', 'uckkarchive'), [
            'size' => 80,
            'maxlength' => 255,
        ]);
        $mform->setType('identifier', PARAM_TEXT);

        $mform->addElement('select', 'identifiertype', get_string('externalworkidentifiertype', 'uckkarchive'),
            $this->get_identifier_type_options()
        );
        $mform->setDefault('identifiertype', '');

        $mform->addElement('textarea', 'citation', get_string('externalworkcitation', 'uckkarchive'), [
            'rows' => 4,
            'cols' => 96,
            'maxlength' => 4000,
        ]);
        $mform->setType('citation', PARAM_TEXT);
        $mform->addHelpButton('citation', 'externalworkcitation', 'uckkarchive');

        $mform->addElement('textarea', 'sourcenote', get_string('externalworksourcenote', 'uckkarchive'), [
            'rows' => 3,
            'cols' => 96,
            'maxlength' => 4000,
        ]);
        $mform->setType('sourcenote', PARAM_TEXT);
    }

    /**
     * Add rights and license fields.
     *
     * @param \MoodleQuickForm $mform Form object.
     * @return void
     */
    private function add_rights_section(\MoodleQuickForm $mform): void {
        $mform->addElement('header', 'rightsheader', get_string('externalworkrights', 'uckkarchive'));

        $mform->addElement('select', 'rightsstatus', get_string('externalworkrightsstatus', 'uckkarchive'),
            $this->get_rights_status_options()
        );
        $mform->setDefault('rightsstatus', self::DEFAULT_RIGHTS);
        $mform->addRule('rightsstatus', null, 'required', null, 'client');

        $mform->addElement('text', 'licensekey', get_string('externalworklicensekey', 'uckkarchive'), [
            'size' => 64,
            'maxlength' => 255,
        ]);
        $mform->setType('licensekey', PARAM_TEXT);
        $mform->hideIf('licensekey', 'rightsstatus', 'neq', 'open_license');
        $mform->hideIf('licensekey', 'rightsstatus', 'neq', 'licensed_external');

        $mform->addElement('textarea', 'rightsstatement', get_string('externalworkrightsstatement', 'uckkarchive'), [
            'rows' => 4,
            'cols' => 96,
            'maxlength' => 4000,
        ]);
        $mform->setType('rightsstatement', PARAM_TEXT);
        $mform->addHelpButton('rightsstatement', 'externalworkrightsstatement', 'uckkarchive');
    }

    /**
     * Add status, visibility and audience fields.
     *
     * @param \MoodleQuickForm $mform Form object.
     * @return void
     */
    private function add_governance_section(\MoodleQuickForm $mform): void {
        $mform->addElement('header', 'governanceheader', get_string('externalworkgovernance', 'uckkarchive'));

        $mform->addElement('select', 'status', get_string('status', 'uckkarchive'), $this->get_status_options());
        $mform->setDefault('status', self::DEFAULT_STATUS);
        $mform->addRule('status', null, 'required', null, 'client');

        $mform->addElement('select', 'visibility', get_string('visibility', 'uckkarchive'), $this->get_visibility_options());
        $mform->setDefault('visibility', self::DEFAULT_VISIBILITY);
        $mform->addRule('visibility', null, 'required', null, 'client');

        $mform->addElement('select', 'audiencesuitability', get_string('audiencesuitability', 'uckkarchive'),
            $this->get_audience_options()
        );
        $mform->setDefault('audiencesuitability', self::DEFAULT_AUDIENCE);
        $mform->addRule('audiencesuitability', null, 'required', null, 'client');
    }

    /**
     * Add teaching, description and cultural protocol fields.
     *
     * @param \MoodleQuickForm $mform Form object.
     * @return void
     */
    private function add_teaching_and_protocol_section(\MoodleQuickForm $mform): void {
        $mform->addElement('header', 'teachingheader', get_string('externalworkteachingandprotocol', 'uckkarchive'));

        $mform->addElement('textarea', 'description', get_string('externalworkdescription', 'uckkarchive'), [
            'rows' => 5,
            'cols' => 96,
            'maxlength' => 8000,
        ]);
        $mform->setType('description', PARAM_TEXT);

        $mform->addElement('textarea', 'teachingnote', get_string('externalworkteachingnote', 'uckkarchive'), [
            'rows' => 5,
            'cols' => 96,
            'maxlength' => 8000,
        ]);
        $mform->setType('teachingnote', PARAM_TEXT);
        $mform->addHelpButton('teachingnote', 'externalworkteachingnote', 'uckkarchive');

        $mform->addElement('textarea', 'culturalprotocolnote', get_string('externalworkculturalprotocolnote', 'uckkarchive'), [
            'rows' => 5,
            'cols' => 96,
            'maxlength' => 8000,
        ]);
        $mform->setType('culturalprotocolnote', PARAM_TEXT);
        $mform->addHelpButton('culturalprotocolnote', 'externalworkculturalprotocolnote', 'uckkarchive');
    }

    /**
     * Add metadata fields.
     *
     * @param \MoodleQuickForm $mform Form object.
     * @return void
     */
    private function add_metadata_section(\MoodleQuickForm $mform): void {
        $mform->addElement('header', 'metadataheader', get_string('metadata', 'uckkarchive'));

        $mform->addElement('textarea', 'metadata', get_string('metadatakeyvalues', 'uckkarchive'), [
            'rows' => 6,
            'cols' => 96,
            'maxlength' => 12000,
        ]);
        $mform->setType('metadata', PARAM_RAW);
        $mform->addHelpButton('metadata', 'metadatakeyvalues', 'uckkarchive');
    }

    /**
     * Add hidden context and identity fields.
     *
     * @param \MoodleQuickForm $mform Form object.
     * @return void
     */
    private function add_hidden_fields(\MoodleQuickForm $mform): void {
        $hiddenfields = [
            'id' => PARAM_INT,
            'externalworkid' => PARAM_INT,
            'archiveid' => PARAM_INT,
            'courseid' => PARAM_INT,
            'cmid' => PARAM_INT,
            'contextid' => PARAM_INT,
            'ownerid' => PARAM_INT,
            'provenanceid' => PARAM_INT,
            'returnurl' => PARAM_LOCALURL,
        ];

        foreach ($hiddenfields as $field => $type) {
            $mform->addElement('hidden', $field);
            $mform->setType($field, $type);
        }

        foreach ($this->get_default_hidden_values() as $field => $value) {
            if ($mform->elementExists($field)) {
                $mform->setDefault($field, $value);
            }
        }
    }

    /**
     * Validate submitted form data.
     *
     * @param array<string,mixed> $data Submitted data.
     * @param array<string,mixed> $files Submitted files.
     * @return array<string,string>
     */
    public function validation($data, $files): array {
        $errors = parent::validation($data, $files);

        $this->validate_choice($errors, $data, 'worktype', $this->get_work_type_options());
        $this->validate_choice($errors, $data, 'status', $this->get_status_options());
        $this->validate_choice($errors, $data, 'visibility', $this->get_visibility_options());
        $this->validate_choice($errors, $data, 'audiencesuitability', $this->get_audience_options());
        $this->validate_choice($errors, $data, 'rightsstatus', $this->get_rights_status_options());
        $this->validate_choice($errors, $data, 'identifiertype', $this->get_identifier_type_options(), false);

        if (empty(trim((string)($data['title'] ?? '')))) {
            $errors['title'] = get_string('required');
        }

        if (!empty($data['sourceurl']) && clean_param((string)$data['sourceurl'], PARAM_URL) === '') {
            $errors['sourceurl'] = get_string('invalidurl', 'error');
        }

        if (!empty($data['publicationyear'])) {
            $year = (int)$data['publicationyear'];
            if ($year < 1 || $year > 9999) {
                $errors['publicationyear'] = get_string('invalidexternalworkyear', 'uckkarchive');
            }
        }

        $requiresreference = in_array((string)($data['worktype'] ?? ''), [
            'website',
            'external_video',
            'external_image',
            'public_archive_item',
            'third_party_pdf',
        ], true);

        if ($requiresreference
                && empty(trim((string)($data['sourceurl'] ?? '')))
                && empty(trim((string)($data['identifier'] ?? '')))
                && empty(trim((string)($data['citation'] ?? '')))) {
            $errors['sourceurl'] = get_string('externalworkreferencerequired', 'uckkarchive');
        }

        if (!empty($data['identifier']) && empty($data['identifiertype'])) {
            $errors['identifiertype'] = get_string('required');
        }

        if ((string)($data['rightsstatus'] ?? '') === 'open_license'
                && empty(trim((string)($data['licensekey'] ?? '')))
                && empty(trim((string)($data['rightsstatement'] ?? '')))) {
            $errors['licensekey'] = get_string('externalworklicenserequired', 'uckkarchive');
        }

        if ((string)($data['rightsstatus'] ?? '') === 'restricted_reference'
                && empty(trim((string)($data['rightsstatement'] ?? '')))) {
            $errors['rightsstatement'] = get_string('externalworkrightsstatementrequired', 'uckkarchive');
        }

        $restrictedvisibility = in_array((string)($data['visibility'] ?? ''), [
            'restricted',
            'restricted_integrity',
            'restricted_cultural',
        ], true);

        $restrictedaudience = in_array((string)($data['audiencesuitability'] ?? ''), [
            'restricted',
            'restricted_integrity',
            'restricted_cultural',
            'staff_only',
        ], true);

        if (($restrictedvisibility || $restrictedaudience)
                && empty(trim((string)($data['teachingnote'] ?? '')))
                && empty(trim((string)($data['culturalprotocolnote'] ?? '')))) {
            $errors['teachingnote'] = get_string('externalworkrestrictionnoterequired', 'uckkarchive');
        }

        if (((string)($data['visibility'] ?? '') === 'restricted_cultural'
                || (string)($data['audiencesuitability'] ?? '') === 'restricted_cultural')
                && empty(trim((string)($data['culturalprotocolnote'] ?? '')))) {
            $errors['culturalprotocolnote'] = get_string('culturalprotocolnoterequired', 'uckkarchive');
        }

        if (!$this->is_valid_json_object(trim((string)($data['metadata'] ?? '')))) {
            $errors['metadata'] = get_string('invalidmetadata', 'uckkarchive');
        }

        return $errors;
    }

    /**
     * Return context from custom data.
     *
     * @return context_module
     */
    private function get_context(): context_module {
        if (!empty($this->_customdata['context']) && $this->_customdata['context'] instanceof context_module) {
            return $this->_customdata['context'];
        }

        if (!empty($this->_customdata['cmid'])) {
            return context_module::instance((int)$this->_customdata['cmid']);
        }

        if (!empty($this->_customdata['cm']) && !empty($this->_customdata['cm']->id)) {
            return context_module::instance((int)$this->_customdata['cm']->id);
        }

        throw new \coding_exception('external_work_form requires a module context or cmid in customdata.');
    }

    /**
     * Return default hidden values from custom data.
     *
     * @return array<string,mixed>
     */
    private function get_default_hidden_values(): array {
        $context = $this->get_context();

        $cmid = (int)($this->_customdata['cmid'] ?? 0);
        if ($cmid <= 0 && !empty($this->_customdata['cm']->id)) {
            $cmid = (int)$this->_customdata['cm']->id;
        }

        $courseid = (int)($this->_customdata['courseid'] ?? 0);
        if ($courseid <= 0 && !empty($this->_customdata['course']->id)) {
            $courseid = (int)$this->_customdata['course']->id;
        }

        $archiveid = (int)($this->_customdata['archiveid'] ?? 0);
        if ($archiveid <= 0 && !empty($this->_customdata['archive']->id)) {
            $archiveid = (int)$this->_customdata['archive']->id;
        }

        $externalworkid = (int)($this->_customdata['externalworkid'] ?? 0);
        if ($externalworkid <= 0 && !empty($this->_customdata['externalwork']->id)) {
            $externalworkid = (int)$this->_customdata['externalwork']->id;
        }

        $ownerid = (int)($this->_customdata['ownerid'] ?? 0);
        if ($ownerid <= 0 && !empty($this->_customdata['externalwork']->ownerid)) {
            $ownerid = (int)$this->_customdata['externalwork']->ownerid;
        }

        $provenanceid = (int)($this->_customdata['provenanceid'] ?? 0);
        if ($provenanceid <= 0 && !empty($this->_customdata['externalwork']->provenanceid)) {
            $provenanceid = (int)$this->_customdata['externalwork']->provenanceid;
        }

        return [
            'id' => $cmid,
            'externalworkid' => $externalworkid,
            'archiveid' => $archiveid,
            'courseid' => $courseid,
            'cmid' => $cmid,
            'contextid' => (int)$context->id,
            'ownerid' => $ownerid,
            'provenanceid' => $provenanceid,
            'returnurl' => (string)($this->_customdata['returnurl'] ?? ''),
        ];
    }

    /**
     * Validate selected value against option keys.
     *
     * @param array<string,string> $errors Error map.
     * @param array<string,mixed> $data Submitted data.
     * @param string $field Field name.
     * @param array<string,string> $options Allowed options.
     * @param bool $required Whether value is required.
     * @return void
     */
    private function validate_choice(array &$errors, array $data, string $field, array $options, bool $required = true): void {
        $value = (string)($data[$field] ?? '');

        if ($value === '' && !$required) {
            return;
        }

        if ($value === '' && $required) {
            $errors[$field] = get_string('required');
            return;
        }

        if (!array_key_exists($value, $options)) {
            $errors[$field] = get_string('invaliddata', 'error');
        }
    }

    /**
     * Return work type options.
     *
     * @return array<string,string>
     */
    private function get_work_type_options(): array {
        return [
            'film' => get_string('externalworktype:film', 'uckkarchive'),
            'book' => get_string('externalworktype:book', 'uckkarchive'),
            'article' => get_string('externalworktype:article', 'uckkarchive'),
            'podcast' => get_string('externalworktype:podcast', 'uckkarchive'),
            'website' => get_string('externalworktype:website', 'uckkarchive'),
            'external_video' => get_string('externalworktype:external_video', 'uckkarchive'),
            'external_image' => get_string('externalworktype:external_image', 'uckkarchive'),
            'public_archive_item' => get_string('externalworktype:public_archive_item', 'uckkarchive'),
            'third_party_pdf' => get_string('externalworktype:third_party_pdf', 'uckkarchive'),
            'other' => get_string('externalworktype:other', 'uckkarchive'),
        ];
    }

    /**
     * Return status options.
     *
     * @return array<string,string>
     */
    private function get_status_options(): array {
        return [
            'draft' => get_string('status:draft', 'uckkarchive'),
            'active' => get_string('status:active', 'uckkarchive'),
            'restricted' => get_string('status:restricted', 'uckkarchive'),
            'archived' => get_string('status:archived', 'uckkarchive'),
            'deleted_soft' => get_string('status:deleted_soft', 'uckkarchive'),
        ];
    }

    /**
     * Return rights status options.
     *
     * @return array<string,string>
     */
    private function get_rights_status_options(): array {
        return [
            'unknown' => get_string('rightsstatus:unknown', 'uckkarchive'),
            'third_party_copyright' => get_string('rightsstatus:third_party_copyright', 'uckkarchive'),
            'licensed_external' => get_string('rightsstatus:licensed_external', 'uckkarchive'),
            'public_domain' => get_string('rightsstatus:public_domain', 'uckkarchive'),
            'open_license' => get_string('rightsstatus:open_license', 'uckkarchive'),
            'fair_use_reference' => get_string('rightsstatus:fair_use_reference', 'uckkarchive'),
            'restricted_reference' => get_string('rightsstatus:restricted_reference', 'uckkarchive'),
        ];
    }

    /**
     * Return visibility options.
     *
     * @return array<string,string>
     */
    private function get_visibility_options(): array {
        return [
            'private' => get_string('visibility:private', 'uckkarchive'),
            'user' => get_string('visibility:user', 'uckkarchive'),
            'group' => get_string('visibility:group', 'uckkarchive'),
            'course' => get_string('visibility:course', 'uckkarchive'),
            'cohort' => get_string('visibility:cohort', 'uckkarchive'),
            'program' => get_string('visibility:program', 'uckkarchive'),
            'institution' => get_string('visibility:institution', 'uckkarchive'),
            'public' => get_string('visibility:public', 'uckkarchive'),
            'restricted' => get_string('visibility:restricted', 'uckkarchive'),
            'restricted_integrity' => get_string('visibility:restricted_integrity', 'uckkarchive'),
            'restricted_cultural' => get_string('visibility:restricted_cultural', 'uckkarchive'),
        ];
    }

    /**
     * Return audience suitability options.
     *
     * @return array<string,string>
     */
    private function get_audience_options(): array {
        return [
            'general' => get_string('audience:general', 'uckkarchive'),
            'guided' => get_string('audience:guided', 'uckkarchive'),
            'mature' => get_string('audience:mature', 'uckkarchive'),
            'restricted' => get_string('audience:restricted', 'uckkarchive'),
            'restricted_cultural' => get_string('audience:restricted_cultural', 'uckkarchive'),
            'restricted_integrity' => get_string('audience:restricted_integrity', 'uckkarchive'),
            'staff_only' => get_string('audience:staff_only', 'uckkarchive'),
        ];
    }

    /**
     * Return identifier type options.
     *
     * @return array<string,string>
     */
    private function get_identifier_type_options(): array {
        return [
            '' => get_string('none'),
            'isbn' => get_string('identifiertype:isbn', 'uckkarchive'),
            'issn' => get_string('identifiertype:issn', 'uckkarchive'),
            'doi' => get_string('identifiertype:doi', 'uckkarchive'),
            'url' => get_string('identifiertype:url', 'uckkarchive'),
            'uri' => get_string('identifiertype:uri', 'uckkarchive'),
            'accession_number' => get_string('identifiertype:accession_number', 'uckkarchive'),
            'catalogue_number' => get_string('identifiertype:catalogue_number', 'uckkarchive'),
            'archive_identifier' => get_string('identifiertype:archive_identifier', 'uckkarchive'),
            'local_identifier' => get_string('identifiertype:local_identifier', 'uckkarchive'),
            'other' => get_string('identifiertype:other', 'uckkarchive'),
        ];
    }

    /**
     * Return whether a metadata field is empty or a valid JSON object.
     *
     * @param string $value Raw metadata value.
     * @return bool
     */
    private function is_valid_json_object(string $value): bool {
        if ($value === '') {
            return true;
        }

        $decoded = json_decode($value, true);

        return is_array($decoded) && json_last_error() === JSON_ERROR_NONE;
    }
}
