<?php
// This file is part of Moodle - https://moodle.org/
//
// Moodle is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// any later version.

/**
 * Content advisory review form.
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

use mod_uckkarchive\local\content_review;
use stdClass;

/**
 * Moodle form for reviewing a content advisory marker.
 *
 * This form is intentionally human-review oriented. It may record advisory
 * state, severity, audience suitability, cultural protocol flags, restriction
 * flags, rationale, review notes, review files, and structured metadata.
 *
 * It does not decide whether a user may review the marker. Capability checks
 * belong in controllers, external services, and content_policy.
 */
final class content_review_form extends \moodleform {
    /** Draft state. */
    private const STATE_DRAFT = 'draft';

    /** Pending review state. */
    private const STATE_PENDING = 'pending_review';

    /** Reviewed state. */
    private const STATE_REVIEWED = 'reviewed';

    /** Approved state. */
    private const STATE_APPROVED = 'approved';

    /** Contested state. */
    private const STATE_CONTESTED = 'contested';

    /** Retired state. */
    private const STATE_RETIRED = 'retired';

    /** Default file manager options. */
    private const DEFAULT_FILE_OPTIONS = [
        'subdirs' => 0,
        'maxfiles' => -1,
        'maxbytes' => 0,
        'accepted_types' => '*',
        'return_types' => \FILE_INTERNAL,
    ];

    /**
     * Define form.
     *
     * @return void
     */
    protected function definition(): void {
        $mform = $this->_form;

        $customdata = $this->_customdata ?? [];

        $cmid = (int)($customdata['cmid'] ?? 0);
        $markerid = (int)($customdata['markerid'] ?? 0);
        $reviewid = (int)($customdata['reviewid'] ?? 0);
        $draftitemid = (int)($customdata['draftitemid'] ?? 0);
        $readonly = !empty($customdata['readonly']);

        $mform->addElement('hidden', 'cmid', $cmid);
        $mform->setType('cmid', PARAM_INT);

        $mform->addElement('hidden', 'markerid', $markerid);
        $mform->setType('markerid', PARAM_INT);

        $mform->addElement('hidden', 'reviewid', $reviewid);
        $mform->setType('reviewid', PARAM_INT);

        $mform->addElement('hidden', 'draftitemid', $draftitemid);
        $mform->setType('draftitemid', PARAM_INT);

        $mform->addElement('header', 'contentreviewheader', get_string('contentreview', 'uckkarchive'));

        $mform->addElement(
            'select',
            'state',
            get_string('contentreviewstate', 'uckkarchive'),
            self::state_options()
        );
        $mform->setType('state', PARAM_ALPHANUMEXT);
        $mform->setDefault('state', self::STATE_PENDING);
        $mform->addRule('state', get_string('required'), 'required', null, 'client');

        $mform->addElement(
            'select',
            'severity',
            get_string('contentadvisoryseverity', 'uckkarchive'),
            self::severity_options()
        );
        $mform->setType('severity', PARAM_ALPHANUMEXT);
        $mform->setDefault('severity', 'notice');
        $mform->addRule('severity', get_string('required'), 'required', null, 'client');

        $mform->addElement(
            'select',
            'audiencesuitability',
            get_string('audiencesuitability', 'uckkarchive'),
            self::audience_suitability_options()
        );
        $mform->setType('audiencesuitability', PARAM_ALPHANUMEXT);
        $mform->setDefault('audiencesuitability', 'guided');
        $mform->addRule('audiencesuitability', get_string('required'), 'required', null, 'client');

        $mform->addElement(
            'advcheckbox',
            'culturalprotocol',
            get_string('culturalprotocol', 'uckkarchive'),
            get_string('contentreview:culturalprotocol_help', 'uckkarchive')
        );
        $mform->setType('culturalprotocol', PARAM_BOOL);
        $mform->setDefault('culturalprotocol', 0);

        $mform->addElement(
            'advcheckbox',
            'restricted',
            get_string('restricted', 'uckkarchive'),
            get_string('contentreview:restricted_help', 'uckkarchive')
        );
        $mform->setType('restricted', PARAM_BOOL);
        $mform->setDefault('restricted', 0);

        $mform->addElement(
            'textarea',
            'rationale',
            get_string('contentreviewrationale', 'uckkarchive'),
            [
                'rows' => 7,
                'cols' => 80,
                'maxlength' => 20000,
            ]
        );
        $mform->setType('rationale', PARAM_RAW);
        $mform->addHelpButton('rationale', 'contentreviewrationale', 'uckkarchive');

        $mform->addElement(
            'textarea',
            'reviewnote',
            get_string('contentreviewnote', 'uckkarchive'),
            [
                'rows' => 6,
                'cols' => 80,
                'maxlength' => 20000,
            ]
        );
        $mform->setType('reviewnote', PARAM_RAW);
        $mform->addHelpButton('reviewnote', 'contentreviewnote', 'uckkarchive');

        $mform->addElement(
            'filemanager',
            'reviewfiles',
            get_string('contentreviewfiles', 'uckkarchive'),
            null,
            self::file_options($customdata)
        );
        $mform->addHelpButton('reviewfiles', 'contentreviewfiles', 'uckkarchive');

        $mform->addElement(
            'textarea',
            'metadatajson',
            get_string('metadata', 'uckkarchive'),
            [
                'rows' => 8,
                'cols' => 80,
                'maxlength' => 20000,
            ]
        );
        $mform->setType('metadatajson', PARAM_RAW);
        $mform->setDefault('metadatajson', '{}');
        $mform->addHelpButton('metadatajson', 'metadata', 'uckkarchive');

        if ($readonly) {
            $this->freeze();
        } else {
            $this->add_action_buttons(true, get_string('savechanges'));
        }
    }

    /**
     * Validate form.
     *
     * @param array<string, mixed> $data Submitted data.
     * @param array<string, mixed> $files Submitted files.
     * @return array<string, string>
     */
    public function validation($data, $files): array {
        $errors = parent::validation($data, $files);

        $markerid = (int)($data['markerid'] ?? 0);
        $reviewid = (int)($data['reviewid'] ?? 0);
        $state = self::clean_key((string)($data['state'] ?? ''));
        $severity = self::clean_key((string)($data['severity'] ?? ''));
        $audiencesuitability = self::clean_key((string)($data['audiencesuitability'] ?? ''));
        $rationale = trim((string)($data['rationale'] ?? ''));
        $metadatajson = trim((string)($data['metadatajson'] ?? ''));

        if ($markerid <= 0 && $reviewid <= 0) {
            $errors['markerid'] = get_string('contentmarkerrequired', 'uckkarchive');
        }

        if (!array_key_exists($state, self::state_options())) {
            $errors['state'] = get_string('invalidstate', 'uckkarchive');
        }

        if (!array_key_exists($severity, self::severity_options())) {
            $errors['severity'] = get_string('invalidseverity', 'uckkarchive');
        }

        if (!array_key_exists($audiencesuitability, self::audience_suitability_options())) {
            $errors['audiencesuitability'] = get_string('invalidaudiencesuitability', 'uckkarchive');
        }

        if (in_array($state, [self::STATE_REVIEWED, self::STATE_APPROVED, self::STATE_CONTESTED, self::STATE_RETIRED], true)
                && $rationale === '') {
            $errors['rationale'] = get_string('contentreviewrationalerequired', 'uckkarchive');
        }

        if ((!empty($data['restricted']) || !empty($data['culturalprotocol'])) && $rationale === '') {
            $errors['rationale'] = get_string('contentreviewrestrictedrationalerequired', 'uckkarchive');
        }

        if ($metadatajson !== '') {
            $decoded = json_decode($metadatajson, true);

            if (!is_array($decoded) || json_last_error() !== JSON_ERROR_NONE) {
                $errors['metadatajson'] = get_string('invalidjson', 'uckkarchive');
            }
        }

        return $errors;
    }

    /**
     * Return normalized data object for service/domain layer.
     *
     * @return stdClass|null
     */
    public function get_normalized_data(): ?stdClass {
        $data = $this->get_data();

        if (!$data) {
            return null;
        }

        $record = new stdClass();
        $record->cmid = (int)($data->cmid ?? 0);
        $record->markerid = (int)($data->markerid ?? 0);
        $record->reviewid = (int)($data->reviewid ?? 0);
        $record->draftitemid = (int)($data->draftitemid ?? 0);
        $record->state = self::clean_key((string)($data->state ?? self::STATE_PENDING));
        $record->severity = self::clean_key((string)($data->severity ?? 'notice'));
        $record->audiencesuitability = self::clean_key((string)($data->audiencesuitability ?? 'guided'));
        $record->culturalprotocol = !empty($data->culturalprotocol) ? 1 : 0;
        $record->restricted = !empty($data->restricted) ? 1 : 0;
        $record->rationale = trim((string)($data->rationale ?? ''));
        $record->reviewnote = trim((string)($data->reviewnote ?? ''));
        $record->reviewfiles = $data->reviewfiles ?? 0;
        $record->metadata = self::decode_metadata((string)($data->metadatajson ?? '{}'));

        return $record;
    }

    /**
     * Set initial form data from a review record.
     *
     * @param stdClass|array<string, mixed> $defaultvalues Default values.
     * @return void
     */
    public function set_review_data($defaultvalues): void {
        $data = (object)$defaultvalues;

        if (isset($data->id) && empty($data->reviewid)) {
            $data->reviewid = (int)$data->id;
        }

        if (isset($data->metadata) && !isset($data->metadatajson)) {
            $data->metadatajson = self::encode_metadata($data->metadata);
        }

        if (!isset($data->metadatajson)) {
            $data->metadatajson = '{}';
        }

        $this->set_data($data);
    }

    /**
     * Return filemanager options.
     *
     * @param array<string, mixed> $customdata Form custom data.
     * @return array<string, mixed>
     */
    private static function file_options(array $customdata): array {
        $options = self::DEFAULT_FILE_OPTIONS;

        if (!empty($customdata['fileoptions']) && is_array($customdata['fileoptions'])) {
            $options = array_merge($options, $customdata['fileoptions']);
        }

        if (!empty($customdata['maxbytes'])) {
            $options['maxbytes'] = (int)$customdata['maxbytes'];
        }

        return $options;
    }

    /**
     * Return review state options.
     *
     * @return array<string, string>
     */
    private static function state_options(): array {
        if (class_exists(content_review::class) && method_exists(content_review::class, 'get_states')) {
            return self::option_labels(content_review::get_states(), 'contentreviewstate');
        }

        return self::option_labels([
            self::STATE_DRAFT,
            self::STATE_PENDING,
            self::STATE_REVIEWED,
            self::STATE_APPROVED,
            self::STATE_CONTESTED,
            self::STATE_RETIRED,
        ], 'contentreviewstate');
    }

    /**
     * Return severity options.
     *
     * @return array<string, string>
     */
    private static function severity_options(): array {
        if (class_exists(content_review::class) && method_exists(content_review::class, 'get_severity_values')) {
            return self::option_labels(content_review::get_severity_values(), 'contentadvisoryseverity');
        }

        return self::option_labels([
            'notice',
            'moderate',
            'strong',
            'restricted',
        ], 'contentadvisoryseverity');
    }

    /**
     * Return audience suitability options.
     *
     * @return array<string, string>
     */
    private static function audience_suitability_options(): array {
        if (class_exists(content_review::class) && method_exists(content_review::class, 'get_suitability_values')) {
            return self::option_labels(content_review::get_suitability_values(), 'audiencesuitability');
        }

        return self::option_labels([
            'general',
            'guided',
            'mature',
            'restricted',
            'restricted_cultural',
            'restricted_integrity',
            'staff_only',
        ], 'audiencesuitability');
    }

    /**
     * Return labels for machine options.
     *
     * @param string[] $values Values.
     * @param string $prefix Language key prefix.
     * @return array<string, string>
     */
    private static function option_labels(array $values, string $prefix): array {
        $options = [];

        foreach ($values as $value) {
            $value = self::clean_key((string)$value);
            $options[$value] = get_string($prefix . ':' . $value, 'uckkarchive');
        }

        return $options;
    }

    /**
     * Clean machine key.
     *
     * @param string $key Raw key.
     * @return string
     */
    private static function clean_key(string $key): string {
        return clean_param(\core_text::strtolower(trim($key)), PARAM_ALPHANUMEXT);
    }

    /**
     * Decode metadata JSON.
     *
     * @param string $json JSON.
     * @return array<string, mixed>
     */
    private static function decode_metadata(string $json): array {
        $json = trim($json);

        if ($json === '') {
            return [];
        }

        $decoded = json_decode($json, true);

        if (!is_array($decoded)) {
            return [];
        }

        return $decoded;
    }

    /**
     * Encode metadata to JSON.
     *
     * @param mixed $metadata Metadata.
     * @return string
     */
    private static function encode_metadata($metadata): string {
        if (is_string($metadata)) {
            $decoded = json_decode($metadata, true);

            if (is_array($decoded)) {
                $metadata = $decoded;
            } else {
                return '{}';
            }
        }

        if ($metadata instanceof stdClass) {
            $metadata = (array)$metadata;
        }

        if (!is_array($metadata)) {
            return '{}';
        }

        $json = json_encode($metadata, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);

        return $json === false ? '{}' : $json;
    }
}
