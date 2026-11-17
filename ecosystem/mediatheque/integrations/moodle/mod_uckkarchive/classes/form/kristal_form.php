<?php
// This file is part of Moodle - https://moodle.org/
//
// Moodle is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// any later version.

/**
 * Kristal form for the UCKK archive activity.
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
use stdClass;

/**
 * Form used to create or edit a Kristal pédagogique.
 *
 * A Kristal is a structured knowledge/memory object. This form collects the
 * author-supplied content, provenance, visibility, uncertainty, and optional
 * AI disclosure. It does not validate, certify, archive-finalise, publish
 * institutional recognition, or replace Archiviste/Inquisiteur review.
 */
final class kristal_form extends moodleform {
    /** Kristal type: concept. */
    private const TYPE_CONCEPT = 'concept';

    /** Kristal type: method. */
    private const TYPE_METHOD = 'method';

    /** Kristal type: principle. */
    private const TYPE_PRINCIPLE = 'principle';

    /** Kristal type: definition. */
    private const TYPE_DEFINITION = 'definition';

    /** Kristal type: synthesis. */
    private const TYPE_SYNTHESIS = 'synthesis';

    /** Kristal type: decision memory. */
    private const TYPE_DECISION_MEMORY = 'decision_memory';

    /** Kristal type: proof synthesis. */
    private const TYPE_PROOF_SYNTHESIS = 'proof_synthesis';

    /** Kristal type: reflection. */
    private const TYPE_REFLECTION = 'reflection';

    /** Kristal type: canon link. */
    private const TYPE_CANON_LINK = 'canon_link';

    /** Status: draft. */
    private const STATUS_DRAFT = 'draft';

    /** Status: pending review. */
    private const STATUS_PENDING_REVIEW = 'pending_review';

    /** Status: hidden. */
    private const STATUS_HIDDEN = 'hidden';

    /** Status: archived. */
    private const STATUS_ARCHIVED = 'archived';

    /** Validation state: unverified. */
    private const VALIDATION_UNVERIFIED = 'unverified';

    /** Validation state: human reviewed. */
    private const VALIDATION_HUMAN_REVIEWED = 'human_reviewed';

    /** Provenance: human. */
    private const PROVENANCE_HUMAN = 'human';

    /** Provenance: AI-assisted. */
    private const PROVENANCE_AI_ASSISTED = 'ai_assisted';

    /** Provenance: imported. */
    private const PROVENANCE_IMPORTED = 'imported';

    /** Provenance: system. */
    private const PROVENANCE_SYSTEM = 'system';

    /** Provenance: archive. */
    private const PROVENANCE_ARCHIVE = 'archive';

    /** Provenance: assembly. */
    private const PROVENANCE_ASSEMBLY = 'assembly';

    /** Provenance: challenge. */
    private const PROVENANCE_CHALLENGE = 'challenge';

    /** Visibility: private. */
    private const VISIBILITY_PRIVATE = 'private';

    /** Visibility: user. */
    private const VISIBILITY_USER = 'user';

    /** Visibility: group. */
    private const VISIBILITY_GROUP = 'group';

    /** Visibility: course. */
    private const VISIBILITY_COURSE = 'course';

    /** Visibility: cohort. */
    private const VISIBILITY_COHORT = 'cohort';

    /** Visibility: program. */
    private const VISIBILITY_PROGRAM = 'program';

    /** Visibility: institution. */
    private const VISIBILITY_INSTITUTION = 'institution';

    /** Visibility: public. */
    private const VISIBILITY_PUBLIC = 'public';

    /** Visibility: restricted. */
    private const VISIBILITY_RESTRICTED = 'restricted';

    /** Visibility: restricted integrity. */
    private const VISIBILITY_RESTRICTED_INTEGRITY = 'restricted_integrity';

    /**
     * Define the form.
     */
    protected function definition(): void {
        $mform = $this->_form;
        $context = $this->get_context();
        $archive = $this->get_custom_record('archive');
        $item = $this->get_custom_record('item');
        $kristal = $this->get_custom_record('kristal');

        $this->add_identity_section($mform, $archive, $item, $kristal);
        $this->add_content_section($mform, $context);
        $this->add_provenance_section($mform);
        $this->add_alignment_section($mform);
        $this->add_visibility_section($mform);
        $this->add_ai_section($mform);
        $this->add_hidden_fields($mform);

        $buttonarray = [];
        $buttonarray[] = $mform->createElement('submit', 'savedraft', get_string('savekristaldraft', 'uckkarchive'));
        $buttonarray[] = $mform->createElement('submit', 'submitbutton', get_string('submitkristal', 'uckkarchive'));
        $buttonarray[] = $mform->createElement('cancel');

        $mform->addGroup($buttonarray, 'buttonar', '', [' '], false);
    }

    /**
     * Add identity fields.
     *
     * @param \MoodleQuickForm $mform Form object.
     * @param stdClass $archive Archive instance.
     * @param stdClass $item Optional archive item.
     * @param stdClass $kristal Optional Kristal record.
     */
    private function add_identity_section(
        \MoodleQuickForm $mform,
        stdClass $archive,
        stdClass $item,
        stdClass $kristal
    ): void {
        $mform->addElement('header', 'identityheader', get_string('kristalidentity', 'uckkarchive'));

        if (!empty($archive->name)) {
            $mform->addElement(
                'static',
                'archivename',
                get_string('archive', 'uckkarchive'),
                format_string($archive->name)
            );
        }

        if (!empty($item->title)) {
            $mform->addElement(
                'static',
                'archiveitemtitle',
                get_string('archiveitem', 'uckkarchive'),
                format_string($item->title)
            );
        }

        if (!empty($kristal->id)) {
            $mform->addElement(
                'static',
                'kristalrecordid',
                get_string('recordid', 'uckkarchive'),
                (string)$kristal->id
            );
        }

        $mform->addElement('text', 'title', get_string('kristaltitle', 'uckkarchive'), [
            'size' => 80,
            'maxlength' => 255,
        ]);
        $mform->setType('title', PARAM_TEXT);
        $mform->addRule('title', null, 'required', null, 'client');

        $mform->addElement('text', 'shortname', get_string('kristalshortname', 'uckkarchive'), [
            'size' => 40,
            'maxlength' => 100,
        ]);
        $mform->setType('shortname', PARAM_ALPHANUMEXT);
        $mform->addHelpButton('shortname', 'kristalshortname', 'uckkarchive');

        $mform->addElement('select', 'kristaltype', get_string('kristaltype', 'uckkarchive'), $this->get_kristal_type_options());
        $mform->setDefault('kristaltype', self::TYPE_CONCEPT);
        $mform->addRule('kristaltype', null, 'required', null, 'client');

        $mform->addElement('textarea', 'summary', get_string('kristalsummary', 'uckkarchive'), [
            'rows' => 4,
            'cols' => 80,
            'maxlength' => 2000,
        ]);
        $mform->setType('summary', PARAM_RAW);
        $mform->addRule('summary', null, 'required', null, 'client');
    }

    /**
     * Add content fields.
     *
     * @param \MoodleQuickForm $mform Form object.
     * @param context_module $context Module context.
     */
    private function add_content_section(\MoodleQuickForm $mform, context_module $context): void {
        $mform->addElement('header', 'contentheader', get_string('kristalcontent', 'uckkarchive'));

        $mform->addElement(
            'editor',
            'content_editor',
            get_string('kristalbody', 'uckkarchive'),
            null,
            $this->get_editor_options($context)
        );
        $mform->setType('content_editor', PARAM_RAW);
        $mform->addRule('content_editor', null, 'required', null, 'client');
        $mform->addHelpButton('content_editor', 'kristalbody', 'uckkarchive');

        $mform->addElement('textarea', 'uncertaintynotes', get_string('uncertaintynotes', 'uckkarchive'), [
            'rows' => 4,
            'cols' => 80,
            'maxlength' => 4000,
        ]);
        $mform->setType('uncertaintynotes', PARAM_RAW);
        $mform->addHelpButton('uncertaintynotes', 'uncertaintynotes', 'uckkarchive');

        $mform->addElement('textarea', 'ethicalnotes', get_string('ethicalnotes', 'uckkarchive'), [
            'rows' => 4,
            'cols' => 80,
            'maxlength' => 4000,
        ]);
        $mform->setType('ethicalnotes', PARAM_RAW);
        $mform->addHelpButton('ethicalnotes', 'ethicalnotes', 'uckkarchive');
    }

    /**
     * Add provenance fields.
     *
     * @param \MoodleQuickForm $mform Form object.
     */
    private function add_provenance_section(\MoodleQuickForm $mform): void {
        $mform->addElement('header', 'provenanceheader', get_string('provenance', 'uckkarchive'));

        $mform->addElement('select', 'provenance', get_string('provenance', 'uckkarchive'), $this->get_provenance_options());
        $mform->setDefault('provenance', self::PROVENANCE_HUMAN);
        $mform->addRule('provenance', null, 'required', null, 'client');

        $mform->addElement('textarea', 'provenancestatement', get_string('provenancestatement', 'uckkarchive'), [
            'rows' => 5,
            'cols' => 80,
            'maxlength' => 4000,
        ]);
        $mform->setType('provenancestatement', PARAM_RAW);
        $mform->addRule('provenancestatement', null, 'required', null, 'client');
        $mform->addHelpButton('provenancestatement', 'provenancestatement', 'uckkarchive');

        $mform->addElement('text', 'sourceauthor', get_string('sourceauthor', 'uckkarchive'), [
            'size' => 80,
            'maxlength' => 255,
        ]);
        $mform->setType('sourceauthor', PARAM_TEXT);

        $mform->addElement('text', 'sourcetitle', get_string('sourcetitle', 'uckkarchive'), [
            'size' => 80,
            'maxlength' => 255,
        ]);
        $mform->setType('sourcetitle', PARAM_TEXT);

        $mform->addElement('url', 'sourceurl', get_string('sourceurl', 'uckkarchive'), [
            'size' => 80,
        ]);
        $mform->setType('sourceurl', PARAM_URL);
        $mform->addHelpButton('sourceurl', 'sourceurl', 'uckkarchive');

        $mform->addElement('date_time_selector', 'sourcedate', get_string('sourcedate', 'uckkarchive'), [
            'optional' => true,
        ]);
        $mform->setDefault('sourcedate', 0);

        $mform->addElement('text', 'provenancehash', get_string('provenancehash', 'uckkarchive'), [
            'size' => 80,
            'maxlength' => 128,
        ]);
        $mform->setType('provenancehash', PARAM_ALPHANUMEXT);
        $mform->addHelpButton('provenancehash', 'provenancehash', 'uckkarchive');
    }

    /**
     * Add alignment fields.
     *
     * @param \MoodleQuickForm $mform Form object.
     */
    private function add_alignment_section(\MoodleQuickForm $mform): void {
        $mform->addElement('header', 'alignmentheader', get_string('kristalalignment', 'uckkarchive'));

        $mform->addElement('text', 'canonref', get_string('canonreference', 'uckkarchive'), [
            'size' => 80,
            'maxlength' => 255,
        ]);
        $mform->setType('canonref', PARAM_TEXT);
        $mform->addHelpButton('canonref', 'canonreference', 'uckkarchive');

        $mform->addElement('textarea', 'competencycodes', get_string('competencycodes', 'uckkarchive'), [
            'rows' => 3,
            'cols' => 80,
        ]);
        $mform->setType('competencycodes', PARAM_RAW);
        $mform->addHelpButton('competencycodes', 'competencycodes', 'uckkarchive');

        $mform->addElement('textarea', 'badgekeys', get_string('badgekeys', 'uckkarchive'), [
            'rows' => 3,
            'cols' => 80,
        ]);
        $mform->setType('badgekeys', PARAM_RAW);
        $mform->addHelpButton('badgekeys', 'badgekeys', 'uckkarchive');

        $mform->addElement('textarea', 'tags', get_string('tags', 'uckkarchive'), [
            'rows' => 3,
            'cols' => 80,
        ]);
        $mform->setType('tags', PARAM_RAW);
        $mform->addHelpButton('tags', 'tags', 'uckkarchive');

        $mform->addElement('text', 'sourcecomponent', get_string('sourcecomponent', 'uckkarchive'), [
            'size' => 40,
            'maxlength' => 100,
        ]);
        $mform->setType('sourcecomponent', PARAM_COMPONENT);

        $mform->addElement('text', 'sourceid', get_string('sourceid', 'uckkarchive'), [
            'size' => 20,
            'maxlength' => 20,
        ]);
        $mform->setType('sourceid', PARAM_INT);
    }

    /**
     * Add visibility/status fields.
     *
     * @param \MoodleQuickForm $mform Form object.
     */
    private function add_visibility_section(\MoodleQuickForm $mform): void {
        $mform->addElement('header', 'visibilityheader', get_string('visibilityandreview', 'uckkarchive'));

        $mform->addElement('select', 'visibility', get_string('visibility', 'uckkarchive'), $this->get_visibility_options());
        $mform->setDefault('visibility', self::VISIBILITY_COURSE);
        $mform->addRule('visibility', null, 'required', null, 'client');

        $mform->addElement('select', 'status', get_string('status'), $this->get_status_options());
        $mform->setDefault('status', self::STATUS_DRAFT);
        $mform->addRule('status', null, 'required', null, 'client');

        $mform->addElement('select', 'validationstate', get_string('validationstate', 'uckkarchive'), $this->get_validation_state_options());
        $mform->setDefault('validationstate', self::VALIDATION_UNVERIFIED);
        $mform->freeze('validationstate');
        $mform->addHelpButton('validationstate', 'validationstate', 'uckkarchive');

        $mform->addElement('textarea', 'publicsummary', get_string('publicsummary', 'uckkarchive'), [
            'rows' => 4,
            'cols' => 80,
            'maxlength' => 2000,
        ]);
        $mform->setType('publicsummary', PARAM_RAW);
        $mform->addHelpButton('publicsummary', 'publicsummary', 'uckkarchive');

        $mform->addElement('textarea', 'restrictednotes', get_string('restrictednotes', 'uckkarchive'), [
            'rows' => 4,
            'cols' => 80,
            'maxlength' => 4000,
        ]);
        $mform->setType('restrictednotes', PARAM_RAW);
        $mform->hideIf('restrictednotes', 'visibility', 'neq', self::VISIBILITY_RESTRICTED_INTEGRITY);
        $mform->addHelpButton('restrictednotes', 'restrictednotes', 'uckkarchive');
    }

    /**
     * Add AI disclosure fields.
     *
     * @param \MoodleQuickForm $mform Form object.
     */
    private function add_ai_section(\MoodleQuickForm $mform): void {
        $mform->addElement('header', 'aiheader', get_string('aigovernance', 'uckkarchive'));

        $mform->addElement('advcheckbox', 'aiassisted', get_string('aiassisted', 'uckkarchive'));
        $mform->setDefault('aiassisted', 0);
        $mform->addHelpButton('aiassisted', 'aiassisted', 'uckkarchive');

        $mform->addElement('textarea', 'ailog', get_string('ailog', 'uckkarchive'), [
            'rows' => 5,
            'cols' => 80,
            'maxlength' => 8000,
        ]);
        $mform->setType('ailog', PARAM_RAW);
        $mform->hideIf('ailog', 'aiassisted', 'notchecked');
        $mform->addHelpButton('ailog', 'ailog', 'uckkarchive');

        $mform->addElement(
            'static',
            'ainonsovereignnotice',
            '',
            get_string('ainonsovereignnotice', 'uckkarchive')
        );
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
            'itemid',
            'kristalid',
            'userid',
            'returnurl',
        ] as $field) {
            $mform->addElement('hidden', $field);
        }

        $mform->setType('id', PARAM_INT);
        $mform->setType('archiveid', PARAM_INT);
        $mform->setType('itemid', PARAM_INT);
        $mform->setType('kristalid', PARAM_INT);
        $mform->setType('userid', PARAM_INT);
        $mform->setType('returnurl', PARAM_LOCALURL);
    }

    /**
     * Validate submitted data.
     *
     * @param array $data Submitted data.
     * @param array $files Submitted files.
     * @return array<string, string>
     */
    public function validation($data, $files): array {
        $errors = parent::validation($data, $files);

        $isfinalsubmit = !empty($data['submitbutton']);
        $content = trim((string)($data['content_editor']['text'] ?? ''));

        if (trim((string)($data['title'] ?? '')) === '') {
            $errors['title'] = get_string('required');
        }

        if (trim((string)($data['summary'] ?? '')) === '') {
            $errors['summary'] = get_string('required');
        }

        if ($isfinalsubmit && $content === '') {
            $errors['content_editor'] = get_string('kristalbodyrequired', 'uckkarchive');
        }

        if (trim((string)($data['provenancestatement'] ?? '')) === '') {
            $errors['provenancestatement'] = get_string('provenancestatementrequired', 'uckkarchive');
        }

        if (!empty($data['shortname']) && !preg_match('/^[A-Za-z0-9_-]+$/', (string)$data['shortname'])) {
            $errors['shortname'] = get_string('invalidshortname', 'uckkarchive');
        }

        if (!empty($data['sourcecomponent']) && !preg_match('/^[a-z]+_[a-z0-9_]+$/', (string)$data['sourcecomponent'])) {
            $errors['sourcecomponent'] = get_string('invalidsourcecomponent', 'uckkarchive');
        }

        if (!empty($data['aiassisted']) && trim((string)($data['ailog'] ?? '')) === '') {
            $errors['ailog'] = get_string('ailogrequired', 'uckkarchive');
        }

        if (
            ($data['provenance'] ?? '') === self::PROVENANCE_AI_ASSISTED
            && empty($data['aiassisted'])
        ) {
            $errors['aiassisted'] = get_string('aiassistancemustbedisclosed', 'uckkarchive');
        }

        if (
            ($data['visibility'] ?? '') === self::VISIBILITY_PUBLIC
            && trim((string)($data['publicsummary'] ?? '')) === ''
        ) {
            $errors['publicsummary'] = get_string('publicsummaryrequired', 'uckkarchive');
        }

        if (
            ($data['visibility'] ?? '') === self::VISIBILITY_RESTRICTED_INTEGRITY
            && trim((string)($data['restrictednotes'] ?? '')) === ''
        ) {
            $errors['restrictednotes'] = get_string('restrictednotesrequired', 'uckkarchive');
        }

        foreach (['competencycodes', 'badgekeys', 'tags'] as $listfield) {
            $value = trim((string)($data[$listfield] ?? ''));

            if ($value !== '' && !$this->is_valid_json_or_plain_list($value)) {
                $errors[$listfield] = get_string('invalidjsonorlist', 'uckkarchive');
            }
        }

        return $errors;
    }

    /**
     * Return whether this submission is a draft save.
     *
     * @return bool
     */
    public function is_draft_save(): bool {
        $data = $this->get_data();

        return $data !== null && !empty($data->savedraft) && empty($data->submitbutton);
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

        throw new \coding_exception('kristal_form requires a module context in customdata.');
    }

    /**
     * Get custom data as record.
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
     * Editor options.
     *
     * @param context_module $context Module context.
     * @return array<string, mixed>
     */
    private function get_editor_options(context_module $context): array {
        return [
            'context' => $context,
            'maxfiles' => EDITOR_UNLIMITED_FILES,
            'maxbytes' => get_max_upload_file_size(),
            'trusttext' => false,
            'noclean' => false,
            'subdirs' => false,
        ];
    }

    /**
     * Kristal type options.
     *
     * @return array<string, string>
     */
    private function get_kristal_type_options(): array {
        return [
            self::TYPE_CONCEPT => get_string('kristaltype:concept', 'uckkarchive'),
            self::TYPE_METHOD => get_string('kristaltype:method', 'uckkarchive'),
            self::TYPE_PRINCIPLE => get_string('kristaltype:principle', 'uckkarchive'),
            self::TYPE_DEFINITION => get_string('kristaltype:definition', 'uckkarchive'),
            self::TYPE_SYNTHESIS => get_string('kristaltype:synthesis', 'uckkarchive'),
            self::TYPE_DECISION_MEMORY => get_string('kristaltype:decisionmemory', 'uckkarchive'),
            self::TYPE_PROOF_SYNTHESIS => get_string('kristaltype:proofsynthesis', 'uckkarchive'),
            self::TYPE_REFLECTION => get_string('kristaltype:reflection', 'uckkarchive'),
            self::TYPE_CANON_LINK => get_string('kristaltype:canonlink', 'uckkarchive'),
        ];
    }

    /**
     * Provenance options.
     *
     * @return array<string, string>
     */
    private function get_provenance_options(): array {
        return [
            self::PROVENANCE_HUMAN => get_string('provenance:human', 'uckkarchive'),
            self::PROVENANCE_AI_ASSISTED => get_string('provenance:ai_assisted', 'uckkarchive'),
            self::PROVENANCE_IMPORTED => get_string('provenance:imported', 'uckkarchive'),
            self::PROVENANCE_SYSTEM => get_string('provenance:system', 'uckkarchive'),
            self::PROVENANCE_ARCHIVE => get_string('provenance:archive', 'uckkarchive'),
            self::PROVENANCE_ASSEMBLY => get_string('provenance:assembly', 'uckkarchive'),
            self::PROVENANCE_CHALLENGE => get_string('provenance:challenge', 'uckkarchive'),
        ];
    }

    /**
     * Visibility options.
     *
     * @return array<string, string>
     */
    private function get_visibility_options(): array {
        return [
            self::VISIBILITY_PRIVATE => get_string('visibility:private', 'uckkarchive'),
            self::VISIBILITY_USER => get_string('visibility:user', 'uckkarchive'),
            self::VISIBILITY_GROUP => get_string('visibility:group', 'uckkarchive'),
            self::VISIBILITY_COURSE => get_string('visibility:course', 'uckkarchive'),
            self::VISIBILITY_COHORT => get_string('visibility:cohort', 'uckkarchive'),
            self::VISIBILITY_PROGRAM => get_string('visibility:program', 'uckkarchive'),
            self::VISIBILITY_INSTITUTION => get_string('visibility:institution', 'uckkarchive'),
            self::VISIBILITY_PUBLIC => get_string('visibility:public', 'uckkarchive'),
            self::VISIBILITY_RESTRICTED => get_string('visibility:restricted', 'uckkarchive'),
            self::VISIBILITY_RESTRICTED_INTEGRITY => get_string('visibility:restricted_integrity', 'uckkarchive'),
        ];
    }

    /**
     * Status options available from this form.
     *
     * Validation/final archive states remain service-controlled.
     *
     * @return array<string, string>
     */
    private function get_status_options(): array {
        return [
            self::STATUS_DRAFT => get_string('status:draft', 'uckkarchive'),
            self::STATUS_PENDING_REVIEW => get_string('status:pending_review', 'uckkarchive'),
            self::STATUS_HIDDEN => get_string('status:hidden', 'uckkarchive'),
            self::STATUS_ARCHIVED => get_string('status:archived', 'uckkarchive'),
        ];
    }

    /**
     * Validation states visible in this form.
     *
     * The field is frozen because Kristal validation belongs to validation
     * services, not ordinary content editing.
     *
     * @return array<string, string>
     */
    private function get_validation_state_options(): array {
        return [
            self::VALIDATION_UNVERIFIED => get_string('validation:unverified', 'uckkarchive'),
            self::VALIDATION_HUMAN_REVIEWED => get_string('validation:human_reviewed', 'uckkarchive'),
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
