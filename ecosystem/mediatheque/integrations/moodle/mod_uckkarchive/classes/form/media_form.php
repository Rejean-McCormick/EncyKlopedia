<?php
// This file is part of Moodle - https://moodle.org/
//
// Moodle is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// any later version.

/**
 * Media create/edit/upload form for mod_uckkarchive.
 *
 * This form collects media metadata, source data, visibility, audience
 * suitability, optional external work references, and file upload data. It does
 * not authorize access, decide cultural protocol access, approve content
 * advisories, publish restricted records, create derivatives, or export files.
 * Those actions belong to capability-checked controllers and classes/local.
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
require_once($CFG->libdir . '/filelib.php');
require_once($CFG->dirroot . '/repository/lib.php');

use context_module;
use moodleform;
use stdClass;

/**
 * Form used to create or edit a media object.
 */
final class media_form extends moodleform {
    /** Default media type. */
    private const DEFAULT_MEDIATYPE = 'document';

    /** Default media status. */
    private const DEFAULT_STATUS = 'draft';

    /** Default visibility. */
    private const DEFAULT_VISIBILITY = 'course';

    /** Default audience suitability. */
    private const DEFAULT_AUDIENCE = 'guided';

    /** Default source type. */
    private const DEFAULT_SOURCE = 'submitted_to_uckk';

    /** Default source ownership. */
    private const DEFAULT_SOURCE_OWNERSHIP = 'member_submitted';

    /** Default file area for primary uploads. */
    private const DEFAULT_FILEAREA = 'media_original';

    /**
     * Define form fields.
     */
    protected function definition(): void {
        $mform = $this->_form;
        $context = $this->get_context();

        $this->add_identity_section($mform);
        $this->add_file_section($mform, $context);
        $this->add_source_section($mform);
        $this->add_external_reference_section($mform);
        $this->add_governance_section($mform);
        $this->add_advisory_hint_section($mform);
        $this->add_metadata_section($mform);
        $this->add_hidden_fields($mform);

        $this->add_action_buttons(true, get_string('savemedia', 'uckkarchive'));
    }

    /**
     * Add media identity fields.
     *
     * @param \MoodleQuickForm $mform Form object.
     * @return void
     */
    private function add_identity_section(\MoodleQuickForm $mform): void {
        $mform->addElement('header', 'identityheader', get_string('mediaidentity', 'uckkarchive'));

        $mform->addElement('text', 'title', get_string('mediatitle', 'uckkarchive'), [
            'size' => 64,
            'maxlength' => 255,
        ]);
        $mform->setType('title', PARAM_TEXT);
        $mform->addRule('title', null, 'required', null, 'client');

        $mform->addElement('textarea', 'description', get_string('mediadescription', 'uckkarchive'), [
            'rows' => 5,
            'cols' => 80,
            'maxlength' => 4000,
        ]);
        $mform->setType('description', PARAM_TEXT);

        $mform->addElement('select', 'mediatype', get_string('mediatype', 'uckkarchive'), $this->get_media_type_options());
        $mform->setDefault('mediatype', self::DEFAULT_MEDIATYPE);
        $mform->addRule('mediatype', null, 'required', null, 'client');

        $mform->addElement('text', 'language', get_string('medialanguage', 'uckkarchive'), [
            'size' => 16,
            'maxlength' => 32,
        ]);
        $mform->setType('language', PARAM_LANG);
        $mform->addHelpButton('language', 'medialanguage', 'uckkarchive');

        $mform->addElement('text', 'creator', get_string('mediacreator', 'uckkarchive'), [
            'size' => 64,
            'maxlength' => 255,
        ]);
        $mform->setType('creator', PARAM_TEXT);

        $mform->addElement('text', 'datecreated', get_string('mediadatecreated', 'uckkarchive'), [
            'size' => 32,
            'maxlength' => 64,
        ]);
        $mform->setType('datecreated', PARAM_TEXT);
        $mform->addHelpButton('datecreated', 'mediadatecreated', 'uckkarchive');
    }

    /**
     * Add media upload fields.
     *
     * @param \MoodleQuickForm $mform Form object.
     * @param context_module $context Module context.
     * @return void
     */
    private function add_file_section(\MoodleQuickForm $mform, context_module $context): void {
        $mform->addElement('header', 'fileheader', get_string('mediafile', 'uckkarchive'));

        $mform->addElement('select', 'filearea', get_string('mediafilearea', 'uckkarchive'), $this->get_filearea_options());
        $mform->setDefault('filearea', self::DEFAULT_FILEAREA);
        $mform->addRule('filearea', null, 'required', null, 'client');

        $mform->addElement('filemanager', 'mediafiles', get_string('mediafiles', 'uckkarchive'), null,
            $this->get_filemanager_options($context)
        );
        $mform->addHelpButton('mediafiles', 'mediafiles', 'uckkarchive');

        $mform->addElement('text', 'alttext', get_string('mediaalttext', 'uckkarchive'), [
            'size' => 64,
            'maxlength' => 255,
        ]);
        $mform->setType('alttext', PARAM_TEXT);

        $mform->addElement('textarea', 'transcriptsummary', get_string('mediatranscriptsummary', 'uckkarchive'), [
            'rows' => 3,
            'cols' => 80,
            'maxlength' => 2000,
        ]);
        $mform->setType('transcriptsummary', PARAM_TEXT);
    }

    /**
     * Add source classification fields.
     *
     * @param \MoodleQuickForm $mform Form object.
     * @return void
     */
    private function add_source_section(\MoodleQuickForm $mform): void {
        $mform->addElement('header', 'sourceheader', get_string('mediasource', 'uckkarchive'));

        $mform->addElement('select', 'sourcetype', get_string('mediasourcetype', 'uckkarchive'), $this->get_source_type_options());
        $mform->setDefault('sourcetype', self::DEFAULT_SOURCE);
        $mform->addRule('sourcetype', null, 'required', null, 'client');

        $mform->addElement('select', 'sourceownership', get_string('mediasourceownership', 'uckkarchive'),
            $this->get_source_ownership_options()
        );
        $mform->setDefault('sourceownership', self::DEFAULT_SOURCE_OWNERSHIP);
        $mform->addRule('sourceownership', null, 'required', null, 'client');

        $mform->addElement('text', 'license', get_string('medialicense', 'uckkarchive'), [
            'size' => 64,
            'maxlength' => 255,
        ]);
        $mform->setType('license', PARAM_TEXT);

        $mform->addElement('textarea', 'rightsnote', get_string('mediarightsnote', 'uckkarchive'), [
            'rows' => 3,
            'cols' => 80,
            'maxlength' => 2000,
        ]);
        $mform->setType('rightsnote', PARAM_TEXT);

        $mform->addElement('text', 'sourceurl', get_string('mediasourceurl', 'uckkarchive'), [
            'size' => 80,
            'maxlength' => 2048,
        ]);
        $mform->setType('sourceurl', PARAM_URL);
        $mform->hideIf('sourceurl', 'sourcetype', 'eq', 'produced_by_uckk');
        $mform->hideIf('sourceurl', 'sourcetype', 'eq', 'submitted_to_uckk');

        $mform->addElement('textarea', 'citation', get_string('mediacitation', 'uckkarchive'), [
            'rows' => 3,
            'cols' => 80,
            'maxlength' => 2000,
        ]);
        $mform->setType('citation', PARAM_TEXT);
    }

    /**
     * Add external work reference fields.
     *
     * @param \MoodleQuickForm $mform Form object.
     * @return void
     */
    private function add_external_reference_section(\MoodleQuickForm $mform): void {
        $mform->addElement('header', 'externalheader', get_string('externalworkreference', 'uckkarchive'));

        $mform->addElement('text', 'externalworktitle', get_string('externalworktitle', 'uckkarchive'), [
            'size' => 64,
            'maxlength' => 255,
        ]);
        $mform->setType('externalworktitle', PARAM_TEXT);

        $mform->addElement('select', 'externalworktype', get_string('externalworktype', 'uckkarchive'),
            $this->get_external_work_type_options()
        );

        $mform->addElement('text', 'externalworkcreator', get_string('externalworkcreator', 'uckkarchive'), [
            'size' => 64,
            'maxlength' => 255,
        ]);
        $mform->setType('externalworkcreator', PARAM_TEXT);

        $mform->addElement('text', 'externalworkyear', get_string('externalworkyear', 'uckkarchive'), [
            'size' => 12,
            'maxlength' => 16,
        ]);
        $mform->setType('externalworkyear', PARAM_ALPHANUMEXT);

        $mform->addElement('text', 'externalworkidentifier', get_string('externalworkidentifier', 'uckkarchive'), [
            'size' => 64,
            'maxlength' => 255,
        ]);
        $mform->setType('externalworkidentifier', PARAM_TEXT);

        $mform->addElement('textarea', 'externalworknote', get_string('externalworknote', 'uckkarchive'), [
            'rows' => 3,
            'cols' => 80,
            'maxlength' => 2000,
        ]);
        $mform->setType('externalworknote', PARAM_TEXT);

        $mform->hideIf('externalheader', 'sourcetype', 'neq', 'external_reference_only');
        $mform->hideIf('externalworktitle', 'sourcetype', 'neq', 'external_reference_only');
        $mform->hideIf('externalworktype', 'sourcetype', 'neq', 'external_reference_only');
        $mform->hideIf('externalworkcreator', 'sourcetype', 'neq', 'external_reference_only');
        $mform->hideIf('externalworkyear', 'sourcetype', 'neq', 'external_reference_only');
        $mform->hideIf('externalworkidentifier', 'sourcetype', 'neq', 'external_reference_only');
        $mform->hideIf('externalworknote', 'sourcetype', 'neq', 'external_reference_only');
    }

    /**
     * Add status, visibility, suitability and collection hint fields.
     *
     * @param \MoodleQuickForm $mform Form object.
     * @return void
     */
    private function add_governance_section(\MoodleQuickForm $mform): void {
        $mform->addElement('header', 'governanceheader', get_string('mediagovernance', 'uckkarchive'));

        $mform->addElement('select', 'status', get_string('mediastatus', 'uckkarchive'), $this->get_status_options());
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

        $mform->addElement('text', 'collectionhint', get_string('mediacollectionhint', 'uckkarchive'), [
            'size' => 64,
            'maxlength' => 255,
        ]);
        $mform->setType('collectionhint', PARAM_TEXT);
        $mform->addHelpButton('collectionhint', 'mediacollectionhint', 'uckkarchive');

        $mform->addElement('advcheckbox', 'requestreview', get_string('requestmediareview', 'uckkarchive'));
        $mform->setDefault('requestreview', 0);
    }

    /**
     * Add advisory hint fields.
     *
     * These fields are not a substitute for content marker review. They help the
     * controller/service decide whether to open the content advisory workflow.
     *
     * @param \MoodleQuickForm $mform Form object.
     * @return void
     */
    private function add_advisory_hint_section(\MoodleQuickForm $mform): void {
        $mform->addElement('header', 'advisoryheader', get_string('contentadvisoryhints', 'uckkarchive'));

        $mform->addElement('advcheckbox', 'hasadvisory', get_string('mediahascontentadvisory', 'uckkarchive'));
        $mform->setDefault('hasadvisory', 0);

        $mform->addElement('textarea', 'advisoryhint', get_string('mediaadvisoryhint', 'uckkarchive'), [
            'rows' => 4,
            'cols' => 80,
            'maxlength' => 4000,
        ]);
        $mform->setType('advisoryhint', PARAM_TEXT);
        $mform->hideIf('advisoryhint', 'hasadvisory', 'notchecked');

        $mform->addElement('select', 'advisoryseverity', get_string('advisoryseverity', 'uckkarchive'),
            $this->get_advisory_severity_options()
        );
        $mform->hideIf('advisoryseverity', 'hasadvisory', 'notchecked');

        $mform->addElement('advcheckbox', 'culturalprotocolrequired', get_string('culturalprotocolrequired', 'uckkarchive'));
        $mform->setDefault('culturalprotocolrequired', 0);

        $mform->addElement('textarea', 'culturalprotocolnote', get_string('culturalprotocolnote', 'uckkarchive'), [
            'rows' => 4,
            'cols' => 80,
            'maxlength' => 4000,
        ]);
        $mform->setType('culturalprotocolnote', PARAM_TEXT);
        $mform->hideIf('culturalprotocolnote', 'culturalprotocolrequired', 'notchecked');
    }

    /**
     * Add metadata fields.
     *
     * @param \MoodleQuickForm $mform Form object.
     * @return void
     */
    private function add_metadata_section(\MoodleQuickForm $mform): void {
        $mform->addElement('header', 'metadataheader', get_string('metadata', 'uckkarchive'));

        $mform->addElement('textarea', 'tags', get_string('mediatags', 'uckkarchive'), [
            'rows' => 3,
            'cols' => 80,
            'maxlength' => 2000,
        ]);
        $mform->setType('tags', PARAM_TEXT);
        $mform->addHelpButton('tags', 'mediatags', 'uckkarchive');

        $mform->addElement('textarea', 'metadata', get_string('metadatakeyvalues', 'uckkarchive'), [
            'rows' => 5,
            'cols' => 80,
            'maxlength' => 8000,
        ]);
        $mform->setType('metadata', PARAM_RAW);
        $mform->addHelpButton('metadata', 'metadatakeyvalues', 'uckkarchive');

        $mform->addElement('textarea', 'internalnote', get_string('internalnote', 'uckkarchive'), [
            'rows' => 3,
            'cols' => 80,
            'maxlength' => 4000,
        ]);
        $mform->setType('internalnote', PARAM_TEXT);
    }

    /**
     * Add hidden identity/context fields.
     *
     * @param \MoodleQuickForm $mform Form object.
     * @return void
     */
    private function add_hidden_fields(\MoodleQuickForm $mform): void {
        $hiddenfields = [
            'id' => PARAM_INT,
            'mediaid' => PARAM_INT,
            'archiveid' => PARAM_INT,
            'courseid' => PARAM_INT,
            'cmid' => PARAM_INT,
            'contextid' => PARAM_INT,
            'sourceid' => PARAM_INT,
            'externalworkid' => PARAM_INT,
            'currentversionid' => PARAM_INT,
            'returnurl' => PARAM_LOCALURL,
        ];

        foreach ($hiddenfields as $field => $type) {
            $mform->addElement('hidden', $field);
            $mform->setType($field, $type);
        }

        $defaults = $this->get_default_hidden_values();
        foreach ($defaults as $field => $value) {
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

        $this->validate_choice($errors, $data, 'mediatype', $this->get_media_type_options());
        $this->validate_choice($errors, $data, 'filearea', $this->get_filearea_options());
        $this->validate_choice($errors, $data, 'sourcetype', $this->get_source_type_options());
        $this->validate_choice($errors, $data, 'sourceownership', $this->get_source_ownership_options());
        $this->validate_choice($errors, $data, 'status', $this->get_status_options());
        $this->validate_choice($errors, $data, 'visibility', $this->get_visibility_options());
        $this->validate_choice($errors, $data, 'audiencesuitability', $this->get_audience_options());
        $this->validate_choice($errors, $data, 'advisoryseverity', $this->get_advisory_severity_options(), false);

        if (!empty($data['sourceurl']) && clean_param((string)$data['sourceurl'], PARAM_URL) === '') {
            $errors['sourceurl'] = get_string('invalidurl', 'error');
        }

        $externaltypes = [
            'external_reference_only',
            'licensed_external',
            'public_domain',
            'fair_use_reference',
            'restricted_reference',
        ];

        if (in_array((string)($data['sourcetype'] ?? ''), $externaltypes, true)
                && empty(trim((string)($data['sourceurl'] ?? '')))
                && empty(trim((string)($data['citation'] ?? '')))
                && empty(trim((string)($data['externalworktitle'] ?? '')))) {
            $errors['sourcetype'] = get_string('externalworkreferencerequired', 'uckkarchive');
        }

        if (!empty($data['externalworkyear']) && !preg_match('/^[0-9]{4}|[0-9]{4}[-\/][0-9]{4}|unknown$/',
                trim((string)$data['externalworkyear']))) {
            $errors['externalworkyear'] = get_string('invalidexternalworkyear', 'uckkarchive');
        }

        if (!empty($data['hasadvisory']) && empty(trim((string)($data['advisoryhint'] ?? '')))) {
            $errors['advisoryhint'] = get_string('advisoryhintrequired', 'uckkarchive');
        }

        if (!empty($data['culturalprotocolrequired']) && empty(trim((string)($data['culturalprotocolnote'] ?? '')))) {
            $errors['culturalprotocolnote'] = get_string('culturalprotocolnoterequired', 'uckkarchive');
        }

        if (!$this->is_valid_json_or_plain_list(trim((string)($data['tags'] ?? '')))) {
            $errors['tags'] = get_string('invalidtaglist', 'uckkarchive');
        }

        if (!$this->is_valid_json_or_plain_list(trim((string)($data['metadata'] ?? '')))) {
            $errors['metadata'] = get_string('invalidmetadata', 'uckkarchive');
        }

        return $errors;
    }

    /**
     * Return filemanager options.
     *
     * @param context_module $context Module context.
     * @return array<string,mixed>
     */
    public function get_filemanager_options(context_module $context): array {
        $maxbytes = (int)($this->_customdata['maxbytes'] ?? get_max_upload_file_size());
        $subdirs = !empty($this->_customdata['subdirs']);

        return [
            'subdirs' => $subdirs,
            'maxbytes' => $maxbytes,
            'maxfiles' => (int)($this->_customdata['maxfiles'] ?? 10),
            'accepted_types' => $this->_customdata['accepted_types'] ?? '*',
            'return_types' => \FILE_INTERNAL,
            'context' => $context,
        ];
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

        throw new \coding_exception('media_form requires a module context or cmid in customdata.');
    }

    /**
     * Get default hidden values from custom data.
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

        return [
            'id' => $cmid,
            'archiveid' => $archiveid,
            'courseid' => $courseid,
            'cmid' => $cmid,
            'contextid' => (int)$context->id,
            'returnurl' => (string)($this->_customdata['returnurl'] ?? ''),
        ];
    }

    /**
     * Validate a selected value against option keys.
     *
     * @param array<string,string> $errors Error map.
     * @param array<string,mixed> $data Submitted data.
     * @param string $field Field name.
     * @param array<string,string> $options Allowed options.
     * @param bool $required Whether empty value is invalid.
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
     * Media type options.
     *
     * @return array<string,string>
     */
    private function get_media_type_options(): array {
        return [
            'image' => get_string('mediatype:image', 'uckkarchive'),
            'video' => get_string('mediatype:video', 'uckkarchive'),
            'audio' => get_string('mediatype:audio', 'uckkarchive'),
            'document' => get_string('mediatype:document', 'uckkarchive'),
            'pdf' => get_string('mediatype:pdf', 'uckkarchive'),
            'transcript' => get_string('mediatype:transcript', 'uckkarchive'),
            'caption' => get_string('mediatype:caption', 'uckkarchive'),
            'thumbnail' => get_string('mediatype:thumbnail', 'uckkarchive'),
            'preview' => get_string('mediatype:preview', 'uckkarchive'),
            'derivative' => get_string('mediatype:derivative', 'uckkarchive'),
            'attachment' => get_string('mediatype:attachment', 'uckkarchive'),
            'external' => get_string('mediatype:external', 'uckkarchive'),
            'other' => get_string('mediatype:other', 'uckkarchive'),
        ];
    }

    /**
     * File area options.
     *
     * @return array<string,string>
     */
    private function get_filearea_options(): array {
        return [
            'media_original' => get_string('filearea:media_original', 'uckkarchive'),
            'media_preview' => get_string('filearea:media_preview', 'uckkarchive'),
            'media_thumbnail' => get_string('filearea:media_thumbnail', 'uckkarchive'),
            'media_derivative' => get_string('filearea:media_derivative', 'uckkarchive'),
            'media_caption' => get_string('filearea:media_caption', 'uckkarchive'),
            'media_transcript' => get_string('filearea:media_transcript', 'uckkarchive'),
            'media_attachment' => get_string('filearea:media_attachment', 'uckkarchive'),
        ];
    }

    /**
     * Source type options.
     *
     * @return array<string,string>
     */
    private function get_source_type_options(): array {
        return [
            'produced_by_uckk' => get_string('mediasource:produced_by_uckk', 'uckkarchive'),
            'submitted_to_uckk' => get_string('mediasource:submitted_to_uckk', 'uckkarchive'),
            'imported' => get_string('mediasource:imported', 'uckkarchive'),
            'external_reference_only' => get_string('mediasource:external_reference_only', 'uckkarchive'),
            'licensed_external' => get_string('mediasource:licensed_external', 'uckkarchive'),
            'public_domain' => get_string('mediasource:public_domain', 'uckkarchive'),
            'fair_use_reference' => get_string('mediasource:fair_use_reference', 'uckkarchive'),
            'restricted_reference' => get_string('mediasource:restricted_reference', 'uckkarchive'),
        ];
    }

    /**
     * Source ownership options.
     *
     * @return array<string,string>
     */
    private function get_source_ownership_options(): array {
        return [
            'uckk_created' => get_string('sourceownership:uckk_created', 'uckkarchive'),
            'uckk_commissioned' => get_string('sourceownership:uckk_commissioned', 'uckkarchive'),
            'member_submitted' => get_string('sourceownership:member_submitted', 'uckkarchive'),
            'partner_submitted' => get_string('sourceownership:partner_submitted', 'uckkarchive'),
            'external_reference' => get_string('sourceownership:external_reference', 'uckkarchive'),
            'third_party_copyright' => get_string('sourceownership:third_party_copyright', 'uckkarchive'),
            'public_domain' => get_string('sourceownership:public_domain', 'uckkarchive'),
            'open_license' => get_string('sourceownership:open_license', 'uckkarchive'),
            'unknown_source' => get_string('sourceownership:unknown_source', 'uckkarchive'),
        ];
    }

    /**
     * External work type options.
     *
     * @return array<string,string>
     */
    private function get_external_work_type_options(): array {
        return [
            '' => get_string('none'),
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
     * Media status options.
     *
     * @return array<string,string>
     */
    private function get_status_options(): array {
        return [
            'draft' => get_string('status:draft', 'uckkarchive'),
            'submitted' => get_string('status:submitted', 'uckkarchive'),
            'active' => get_string('status:active', 'uckkarchive'),
            'restricted' => get_string('status:restricted', 'uckkarchive'),
            'superseded' => get_string('status:superseded', 'uckkarchive'),
            'archived' => get_string('status:archived', 'uckkarchive'),
            'deleted_soft' => get_string('status:deleted_soft', 'uckkarchive'),
        ];
    }

    /**
     * Visibility options.
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
     * Audience suitability options.
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
     * Advisory severity options.
     *
     * @return array<string,string>
     */
    private function get_advisory_severity_options(): array {
        return [
            '' => get_string('none'),
            'notice' => get_string('advisoryseverity:notice', 'uckkarchive'),
            'moderate' => get_string('advisoryseverity:moderate', 'uckkarchive'),
            'strong' => get_string('advisoryseverity:strong', 'uckkarchive'),
            'restricted' => get_string('advisoryseverity:restricted', 'uckkarchive'),
        ];
    }

    /**
     * Accept JSON or a plain newline/comma-separated list.
     *
     * @param string $value Raw value.
     * @return bool
     */
    private function is_valid_json_or_plain_list(string $value): bool {
        if ($value === '') {
            return true;
        }

        json_decode($value);
        if (json_last_error() === JSON_ERROR_NONE) {
            return true;
        }

        return str_contains($value, "\n")
            || str_contains($value, ',')
            || (!str_contains($value, '{') && !str_contains($value, '['));
    }
}
