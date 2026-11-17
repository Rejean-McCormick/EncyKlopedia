<?php
// This file is part of Moodle - https://moodle.org/
//
// Moodle is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// any later version.

/**
 * Content marker form for UCKK Archive.
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
 * Form used to create or edit a content advisory marker.
 *
 * A content marker links a content advisory or cultural protocol tag to a
 * precise locator in a media object, media version, archive item, proof,
 * Kristal, external work, collection, or manual reference.
 *
 * This form only collects and validates input. It does not decide final access,
 * content review approval, cultural protocol authority, redaction, export
 * visibility, or restricted media access. Those rules belong to local policy
 * and service/controller code.
 */
final class content_marker_form extends moodleform {
    /** Target type: media. */
    private const TARGET_MEDIA = 'media';

    /** Target type: media version. */
    private const TARGET_MEDIA_VERSION = 'media_version';

    /** Target type: archive item. */
    private const TARGET_ARCHIVE_ITEM = 'archive_item';

    /** Target type: proof. */
    private const TARGET_PROOF = 'proof';

    /** Target type: Kristal. */
    private const TARGET_KRISTAL = 'kristal';

    /** Target type: external work. */
    private const TARGET_EXTERNAL_WORK = 'external_work';

    /** Target type: collection. */
    private const TARGET_COLLECTION = 'collection';

    /** Target type: manual reference. */
    private const TARGET_MANUAL_REFERENCE = 'manual_reference';

    /** Review state: draft. */
    private const REVIEW_DRAFT = 'draft';

    /** Review state: pending review. */
    private const REVIEW_PENDING = 'pending_review';

    /** Review state: reviewed. */
    private const REVIEW_REVIEWED = 'reviewed';

    /** Review state: approved. */
    private const REVIEW_APPROVED = 'approved';

    /** Review state: contested. */
    private const REVIEW_CONTESTED = 'contested';

    /** Review state: retired. */
    private const REVIEW_RETIRED = 'retired';

    /** Severity: notice. */
    private const SEVERITY_NOTICE = 'notice';

    /** Severity: moderate. */
    private const SEVERITY_MODERATE = 'moderate';

    /** Severity: strong. */
    private const SEVERITY_STRONG = 'strong';

    /** Severity: restricted. */
    private const SEVERITY_RESTRICTED = 'restricted';

    /** Visibility: private. */
    private const VISIBILITY_PRIVATE = 'private';

    /** Visibility: user. */
    private const VISIBILITY_USER = 'user';

    /** Visibility: course. */
    private const VISIBILITY_COURSE = 'course';

    /** Visibility: restricted. */
    private const VISIBILITY_RESTRICTED = 'restricted';

    /** Visibility: restricted integrity. */
    private const VISIBILITY_RESTRICTED_INTEGRITY = 'restricted_integrity';

    /** Visibility: restricted cultural. */
    private const VISIBILITY_RESTRICTED_CULTURAL = 'restricted_cultural';

    /** Audience suitability: general. */
    private const SUITABILITY_GENERAL = 'general';

    /** Audience suitability: guided. */
    private const SUITABILITY_GUIDED = 'guided';

    /** Audience suitability: mature. */
    private const SUITABILITY_MATURE = 'mature';

    /** Audience suitability: restricted. */
    private const SUITABILITY_RESTRICTED = 'restricted';

    /** Audience suitability: restricted cultural. */
    private const SUITABILITY_RESTRICTED_CULTURAL = 'restricted_cultural';

    /** Audience suitability: restricted integrity. */
    private const SUITABILITY_RESTRICTED_INTEGRITY = 'restricted_integrity';

    /** Audience suitability: staff only. */
    private const SUITABILITY_STAFF_ONLY = 'staff_only';

    /**
     * Define form.
     */
    protected function definition(): void {
        $mform = $this->_form;

        $mform->addElement('header', 'contentmarkerhdr', $this->str('contentmarker', 'Content marker'));

        $this->add_identity_fields();
        $this->add_tag_fields();
        $this->add_target_fields();
        $this->add_locator_fields();
        $this->add_advisory_fields();
        $this->add_protocol_fields();
        $this->add_metadata_fields();

        $this->set_initial_data();

        $this->add_action_buttons(true, $this->str('savecontentmarker', 'Save content marker'));
    }

    /**
     * Add hidden identity fields.
     */
    private function add_identity_fields(): void {
        $mform = $this->_form;

        foreach ([
            'id',
            'archiveid',
            'courseid',
            'cmid',
            'contextid',
            'createdby',
            'modifiedby',
        ] as $field) {
            $mform->addElement('hidden', $field, $this->custom_int($field));
            $mform->setType($field, PARAM_INT);
        }

        $mform->addElement('hidden', 'uuid', $this->custom_string('uuid'));
        $mform->setType('uuid', PARAM_TEXT);
    }

    /**
     * Add content tag fields.
     */
    private function add_tag_fields(): void {
        $mform = $this->_form;

        $mform->addElement('header', 'taghdr', $this->str('contenttag', 'Content tag'));

        $tagoptions = $this->custom_array('contenttagoptions');
        if (!empty($tagoptions)) {
            $mform->addElement('select', 'tagid', $this->str('contenttag', 'Content tag'), [0 => get_string('choose')] + $tagoptions);
            $mform->setType('tagid', PARAM_INT);
        } else {
            $mform->addElement('hidden', 'tagid', 0);
            $mform->setType('tagid', PARAM_INT);
        }

        $mform->addElement('text', 'tagkey', $this->str('tagkey', 'Tag key'), ['size' => 48]);
        $mform->setType('tagkey', PARAM_ALPHANUMEXT);
        $mform->addRule('tagkey', get_string('required'), 'required', null, 'client');
        $mform->addHelpButton('tagkey', 'tagkey', 'uckkarchive');

        $tagsetoptions = $this->custom_array('contenttagsetoptions');
        if (!empty($tagsetoptions)) {
            $mform->addElement('select', 'tagsetkey', $this->str('contenttagset', 'Content tag set'), ['' => get_string('none')] + $tagsetoptions);
        } else {
            $mform->addElement('text', 'tagsetkey', $this->str('contenttagsetkey', 'Content tag set key'), ['size' => 48]);
        }
        $mform->setType('tagsetkey', PARAM_ALPHANUMEXT);
    }

    /**
     * Add target fields.
     */
    private function add_target_fields(): void {
        $mform = $this->_form;

        $mform->addElement('header', 'targethdr', $this->str('markertarget', 'Marker target'));

        $mform->addElement('select', 'targettype', $this->str('targettype', 'Target type'), $this->get_target_type_options());
        $mform->setType('targettype', PARAM_ALPHANUMEXT);
        $mform->addRule('targettype', get_string('required'), 'required', null, 'client');

        $mform->addElement('text', 'targetid', $this->str('targetid', 'Target id'), ['size' => 12]);
        $mform->setType('targetid', PARAM_INT);

        $mform->addElement('text', 'targetuuid', $this->str('targetuuid', 'Target UUID'), ['size' => 48]);
        $mform->setType('targetuuid', PARAM_TEXT);

        $mform->addElement('text', 'externalworkid', $this->str('externalworkid', 'External work id'), ['size' => 12]);
        $mform->setType('externalworkid', PARAM_INT);

        $mform->addElement('text', 'externalworkuuid', $this->str('externalworkuuid', 'External work UUID'), ['size' => 48]);
        $mform->setType('externalworkuuid', PARAM_TEXT);

        $mform->addElement('static', 'targetguidance', '', $this->str(
            'contentmarkertargetguidance',
            'For internal targets, provide a target id or target UUID. For manual references, describe the target in the locator and notes.'
        ));
    }

    /**
     * Add locator fields.
     */
    private function add_locator_fields(): void {
        $mform = $this->_form;

        $mform->addElement('header', 'locatorhdr', $this->str('locator', 'Locator'));

        $mform->addElement('select', 'locatortype', $this->str('locatortype', 'Locator type'), $this->get_locator_type_options());
        $mform->setType('locatortype', PARAM_ALPHANUMEXT);
        $mform->addRule('locatortype', get_string('required'), 'required', null, 'client');

        $mform->addElement('text', 'locatorvalue', $this->str('locatorvalue', 'Locator value'), ['size' => 64]);
        $mform->setType('locatorvalue', PARAM_TEXT);

        $mform->addElement('text', 'locatorstart', $this->str('locatorstart', 'Locator start'), ['size' => 32]);
        $mform->setType('locatorstart', PARAM_TEXT);

        $mform->addElement('text', 'locatorend', $this->str('locatorend', 'Locator end'), ['size' => 32]);
        $mform->setType('locatorend', PARAM_TEXT);

        $mform->addElement('text', 'locatorlabel', $this->str('locatorlabel', 'Locator label'), ['size' => 64]);
        $mform->setType('locatorlabel', PARAM_TEXT);

        $mform->addElement('static', 'locatorguidance', '', $this->str(
            'contentmarkerlocatorguidance',
            'Examples: 01:12:30-01:15:10, page 42-45, chapter 3, #section-3, scene 4.'
        ));
    }

    /**
     * Add advisory fields.
     */
    private function add_advisory_fields(): void {
        $mform = $this->_form;

        $mform->addElement('header', 'advisoryhdr', $this->str('contentadvisory', 'Content advisory'));

        $mform->addElement('select', 'severity', $this->str('severity', 'Severity'), $this->get_severity_options());
        $mform->setType('severity', PARAM_ALPHANUMEXT);

        $mform->addElement('select', 'audiencesuitability', $this->str('audiencesuitability', 'Audience suitability'), $this->get_audience_options());
        $mform->setType('audiencesuitability', PARAM_ALPHANUMEXT);

        $mform->addElement('select', 'reviewstate', $this->str('reviewstate', 'Review state'), $this->get_review_state_options());
        $mform->setType('reviewstate', PARAM_ALPHANUMEXT);

        $mform->addElement('select', 'visibility', $this->str('visibility', 'Visibility'), $this->get_visibility_options());
        $mform->setType('visibility', PARAM_ALPHANUMEXT);

        $mform->addElement('textarea', 'note', $this->str('advisorynote', 'Advisory note'), [
            'rows' => 5,
            'cols' => 80,
        ]);
        $mform->setType('note', PARAM_RAW);

        $mform->addElement('textarea', 'teachingnote', $this->str('teachingnote', 'Teaching note'), [
            'rows' => 5,
            'cols' => 80,
        ]);
        $mform->setType('teachingnote', PARAM_RAW);
    }

    /**
     * Add cultural protocol and restriction fields.
     */
    private function add_protocol_fields(): void {
        $mform = $this->_form;

        $mform->addElement('header', 'protocolhdr', $this->str('culturalprotocol', 'Cultural protocol'));

        $mform->addElement('advcheckbox', 'iscultural', $this->str('iscultural', 'Cultural protocol marker'));
        $mform->setType('iscultural', PARAM_BOOL);

        $mform->addElement('advcheckbox', 'isrestricted', $this->str('isrestricted', 'Restricted advisory marker'));
        $mform->setType('isrestricted', PARAM_BOOL);

        $mform->addElement('advcheckbox', 'requiresreview', $this->str('requiresreview', 'Requires human review'));
        $mform->setType('requiresreview', PARAM_BOOL);

        $mform->addElement('advcheckbox', 'requirescontext', $this->str('requirescontext', 'Requires context note'));
        $mform->setType('requirescontext', PARAM_BOOL);

        $mform->addElement('advcheckbox', 'requirespermission', $this->str('requirespermission', 'Requires permission before use'));
        $mform->setType('requirespermission', PARAM_BOOL);

        $mform->addElement('textarea', 'culturalprotocolnote', $this->str('culturalprotocolnote', 'Cultural protocol note'), [
            'rows' => 5,
            'cols' => 80,
        ]);
        $mform->setType('culturalprotocolnote', PARAM_RAW);

        $mform->addElement('static', 'protocolnotice', '', $this->str(
            'culturalprotocolnotice',
            'Cultural protocol notes may contain sensitive access rules and must remain permission-filtered.'
        ));
    }

    /**
     * Add metadata fields.
     */
    private function add_metadata_fields(): void {
        $mform = $this->_form;

        $mform->addElement('header', 'metadatahdr', $this->str('metadata', 'Metadata'));

        $mform->addElement('advcheckbox', 'aiassisted', $this->str('aiassisted', 'AI-assisted suggestion'));
        $mform->setType('aiassisted', PARAM_BOOL);

        $mform->addElement('textarea', 'metadata', $this->str('metadatajson', 'Metadata JSON'), [
            'rows' => 8,
            'cols' => 80,
        ]);
        $mform->setType('metadata', PARAM_RAW);
        $mform->addHelpButton('metadata', 'metadata', 'uckkarchive');
    }

    /**
     * Apply initial data from customdata marker.
     */
    private function set_initial_data(): void {
        $marker = $this->custom_record('marker');

        if ($marker === null) {
            $defaults = [
                'severity' => self::SEVERITY_NOTICE,
                'audiencesuitability' => self::SUITABILITY_GUIDED,
                'reviewstate' => self::REVIEW_DRAFT,
                'visibility' => self::VISIBILITY_COURSE,
            ];

            foreach (['archiveid', 'courseid', 'cmid', 'contextid'] as $field) {
                $value = $this->custom_int($field);
                if ($value > 0) {
                    $defaults[$field] = $value;
                }
            }

            $this->set_data((object)$defaults);
            return;
        }

        $data = clone $marker;

        if (isset($data->metadata) && is_array($data->metadata)) {
            $data->metadata = json_encode($data->metadata, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
        }

        if (isset($data->locator) && is_array($data->locator)) {
            $data->locatortype = $data->locator['type'] ?? ($data->locatortype ?? '');
            $data->locatorvalue = $data->locator['value'] ?? ($data->locatorvalue ?? '');
            $data->locatorstart = $data->locator['start'] ?? ($data->locatorstart ?? '');
            $data->locatorend = $data->locator['end'] ?? ($data->locatorend ?? '');
            $data->locatorlabel = $data->locator['label'] ?? ($data->locatorlabel ?? '');
        }

        $this->set_data($data);
    }

    /**
     * Validate form data.
     *
     * @param array<string, mixed> $data Form data.
     * @param array<string, mixed> $files Files.
     * @return array<string, string>
     */
    public function validation($data, $files): array {
        $errors = parent::validation($data, $files);

        $tagid = (int)($data['tagid'] ?? 0);
        $tagkey = trim((string)($data['tagkey'] ?? ''));

        if ($tagid <= 0 && $tagkey === '') {
            $errors['tagkey'] = $this->str('contentmarkerrequirestag', 'A content marker requires a content tag.');
        }

        if ($tagkey !== '' && !preg_match('/^[a-z][a-z0-9_]*$/', $tagkey)) {
            $errors['tagkey'] = $this->str(
                'contentmarkertagkeyinvalid',
                'Tag key must start with a lowercase letter and contain only lowercase letters, numbers, and underscores.'
            );
        }

        $targettype = (string)($data['targettype'] ?? '');
        $targetid = (int)($data['targetid'] ?? 0);
        $targetuuid = trim((string)($data['targetuuid'] ?? ''));

        if ($targettype === '') {
            $errors['targettype'] = get_string('required');
        }

        if ($targettype !== self::TARGET_MANUAL_REFERENCE && $targetid <= 0 && $targetuuid === '') {
            $errors['targetid'] = $this->str(
                'contentmarkertargetrequired',
                'A non-manual content marker requires a target id or target UUID.'
            );
        }

        if ($targetuuid !== '' && !$this->looks_like_uuid($targetuuid)) {
            $errors['targetuuid'] = $this->str('uuidinvalid', 'Invalid UUID.');
        }

        $externalworkuuid = trim((string)($data['externalworkuuid'] ?? ''));
        if ($externalworkuuid !== '' && !$this->looks_like_uuid($externalworkuuid)) {
            $errors['externalworkuuid'] = $this->str('uuidinvalid', 'Invalid UUID.');
        }

        $locatortype = (string)($data['locatortype'] ?? '');
        if ($locatortype === '') {
            $errors['locatortype'] = get_string('required');
        }

        if (!$this->has_locator_value($data)) {
            $errors['locatorvalue'] = $this->str(
                'contentmarkerlocatorrequired',
                'A content marker requires locator value, locator start, or locator end.'
            );
        }

        if (!empty($data['metadata']) && !$this->is_valid_json_object((string)$data['metadata'])) {
            $errors['metadata'] = $this->str('metadatajsoninvalid', 'Metadata must be a valid JSON object.');
        }

        if (!empty($data['iscultural']) && empty($data['culturalprotocolnote'])) {
            $errors['culturalprotocolnote'] = $this->str(
                'culturalprotocolnoterequired',
                'A cultural protocol marker requires a cultural protocol note.'
            );
        }

        if (!empty($data['isrestricted'])
                && !in_array((string)($data['severity'] ?? ''), [self::SEVERITY_STRONG, self::SEVERITY_RESTRICTED], true)) {
            $errors['severity'] = $this->str(
                'restrictedmarkerseverityrequired',
                'Restricted markers should use strong or restricted severity.'
            );
        }

        return $errors;
    }

    /**
     * Return target type options.
     *
     * @return array<string, string>
     */
    private function get_target_type_options(): array {
        return [
            '' => get_string('choose'),
            self::TARGET_MEDIA => $this->str('targettype:media', 'Media'),
            self::TARGET_MEDIA_VERSION => $this->str('targettype:media_version', 'Media version'),
            self::TARGET_ARCHIVE_ITEM => $this->str('targettype:archive_item', 'Archive item'),
            self::TARGET_PROOF => $this->str('targettype:proof', 'Proof'),
            self::TARGET_KRISTAL => $this->str('targettype:kristal', 'Kristal'),
            self::TARGET_EXTERNAL_WORK => $this->str('targettype:external_work', 'External work'),
            self::TARGET_COLLECTION => $this->str('targettype:collection', 'Collection'),
            self::TARGET_MANUAL_REFERENCE => $this->str('targettype:manual_reference', 'Manual reference'),
        ];
    }

    /**
     * Return locator type options.
     *
     * @return array<string, string>
     */
    private function get_locator_type_options(): array {
        return [
            '' => get_string('choose'),
            'timecode' => $this->str('locatortype:timecode', 'Timecode'),
            'timecode_range' => $this->str('locatortype:timecode_range', 'Timecode range'),
            'page' => $this->str('locatortype:page', 'Page'),
            'page_range' => $this->str('locatortype:page_range', 'Page range'),
            'chapter' => $this->str('locatortype:chapter', 'Chapter'),
            'chapter_range' => $this->str('locatortype:chapter_range', 'Chapter range'),
            'section' => $this->str('locatortype:section', 'Section'),
            'section_range' => $this->str('locatortype:section_range', 'Section range'),
            'paragraph' => $this->str('locatortype:paragraph', 'Paragraph'),
            'paragraph_range' => $this->str('locatortype:paragraph_range', 'Paragraph range'),
            'scene' => $this->str('locatortype:scene', 'Scene'),
            'track' => $this->str('locatortype:track', 'Track'),
            'timestamp' => $this->str('locatortype:timestamp', 'Timestamp'),
            'url_fragment' => $this->str('locatortype:url_fragment', 'URL fragment'),
            'manual_reference' => $this->str('locatortype:manual_reference', 'Manual reference'),
        ];
    }

    /**
     * Return severity options.
     *
     * @return array<string, string>
     */
    private function get_severity_options(): array {
        return [
            self::SEVERITY_NOTICE => $this->str('advisoryseverity:notice', 'Notice'),
            self::SEVERITY_MODERATE => $this->str('advisoryseverity:moderate', 'Moderate'),
            self::SEVERITY_STRONG => $this->str('advisoryseverity:strong', 'Strong'),
            self::SEVERITY_RESTRICTED => $this->str('advisoryseverity:restricted', 'Restricted'),
        ];
    }

    /**
     * Return audience suitability options.
     *
     * @return array<string, string>
     */
    private function get_audience_options(): array {
        return [
            self::SUITABILITY_GENERAL => $this->str('audience:general', 'General'),
            self::SUITABILITY_GUIDED => $this->str('audience:guided', 'Guided'),
            self::SUITABILITY_MATURE => $this->str('audience:mature', 'Mature'),
            self::SUITABILITY_RESTRICTED => $this->str('audience:restricted', 'Restricted'),
            self::SUITABILITY_RESTRICTED_CULTURAL => $this->str('audience:restricted_cultural', 'Restricted cultural'),
            self::SUITABILITY_RESTRICTED_INTEGRITY => $this->str('audience:restricted_integrity', 'Restricted integrity'),
            self::SUITABILITY_STAFF_ONLY => $this->str('audience:staff_only', 'Staff only'),
        ];
    }

    /**
     * Return review state options.
     *
     * @return array<string, string>
     */
    private function get_review_state_options(): array {
        return [
            self::REVIEW_DRAFT => $this->str('reviewstate:draft', 'Draft'),
            self::REVIEW_PENDING => $this->str('reviewstate:pending_review', 'Pending review'),
            self::REVIEW_REVIEWED => $this->str('reviewstate:reviewed', 'Reviewed'),
            self::REVIEW_APPROVED => $this->str('reviewstate:approved', 'Approved'),
            self::REVIEW_CONTESTED => $this->str('reviewstate:contested', 'Contested'),
            self::REVIEW_RETIRED => $this->str('reviewstate:retired', 'Retired'),
        ];
    }

    /**
     * Return visibility options.
     *
     * @return array<string, string>
     */
    private function get_visibility_options(): array {
        return [
            self::VISIBILITY_PRIVATE => $this->str('visibility:private', 'Private'),
            self::VISIBILITY_USER => $this->str('visibility:user', 'User'),
            self::VISIBILITY_COURSE => $this->str('visibility:course', 'Course'),
            self::VISIBILITY_RESTRICTED => $this->str('visibility:restricted', 'Restricted'),
            self::VISIBILITY_RESTRICTED_INTEGRITY => $this->str('visibility:restricted_integrity', 'Restricted integrity'),
            self::VISIBILITY_RESTRICTED_CULTURAL => $this->str('visibility:restricted_cultural', 'Restricted cultural'),
        ];
    }

    /**
     * Return whether locator data is present.
     *
     * @param array<string, mixed> $data Form data.
     * @return bool
     */
    private function has_locator_value(array $data): bool {
        foreach (['locatorvalue', 'locatorstart', 'locatorend'] as $field) {
            if (trim((string)($data[$field] ?? '')) !== '') {
                return true;
            }
        }

        return false;
    }

    /**
     * Return whether value is a JSON object.
     *
     * @param string $value JSON string.
     * @return bool
     */
    private function is_valid_json_object(string $value): bool {
        $value = trim($value);
        if ($value === '') {
            return true;
        }

        $decoded = json_decode($value, true);

        return json_last_error() === JSON_ERROR_NONE && is_array($decoded);
    }

    /**
     * Return whether a value looks like a UUID.
     *
     * @param string $uuid UUID.
     * @return bool
     */
    private function looks_like_uuid(string $uuid): bool {
        return (bool)preg_match(
            '/^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i',
            trim($uuid)
        );
    }

    /**
     * Return int from custom data.
     *
     * @param string $key Key.
     * @return int
     */
    private function custom_int(string $key): int {
        if (!isset($this->_customdata[$key])) {
            return 0;
        }

        return (int)$this->_customdata[$key];
    }

    /**
     * Return string from custom data.
     *
     * @param string $key Key.
     * @return string
     */
    private function custom_string(string $key): string {
        if (!isset($this->_customdata[$key])) {
            return '';
        }

        return (string)$this->_customdata[$key];
    }

    /**
     * Return array from custom data.
     *
     * @param string $key Key.
     * @return array<mixed>
     */
    private function custom_array(string $key): array {
        if (!isset($this->_customdata[$key]) || !is_array($this->_customdata[$key])) {
            return [];
        }

        return $this->_customdata[$key];
    }

    /**
     * Return record from custom data.
     *
     * @param string $key Key.
     * @return stdClass|null
     */
    private function custom_record(string $key): ?stdClass {
        if (empty($this->_customdata[$key])) {
            return null;
        }

        if ($this->_customdata[$key] instanceof stdClass) {
            return $this->_customdata[$key];
        }

        if (is_array($this->_customdata[$key])) {
            return (object)$this->_customdata[$key];
        }

        return null;
    }

    /**
     * Safe component string lookup.
     *
     * @param string $identifier String identifier.
     * @param string $fallback Fallback.
     * @return string
     */
    private function str(string $identifier, string $fallback): string {
        $manager = get_string_manager();

        if ($manager->string_exists($identifier, 'uckkarchive')) {
            return get_string($identifier, 'uckkarchive');
        }

        return $fallback;
    }
}
