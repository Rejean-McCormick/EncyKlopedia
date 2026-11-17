<?php
// This file is part of Moodle - https://moodle.org/
//
// Moodle is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// any later version.

/**
 * Content advisory tag create/edit form for mod_uckkarchive.
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

use mod_uckkarchive\local\content_tag;
use mod_uckkarchive\local\content_tag_set;
use moodleform;
use stdClass;

/**
 * Form used to create or edit a content advisory tag.
 *
 * Content tags are controlled vocabulary records used by content markers,
 * advisory panels, cultural protocol warnings, audience suitability rules,
 * and external work/media references.
 *
 * This form only collects and validates tag data. It does not approve a tag,
 * decide final marker visibility, grant cultural access, or apply restrictions
 * to media. Those decisions belong to capability-checked controllers and
 * classes/local policy services.
 */
final class content_tag_form extends moodleform {
    /** Default category. */
    private const DEFAULT_CATEGORY = 'general_advisory';

    /** Default severity. */
    private const DEFAULT_SEVERITY = 'notice';

    /** Default audience. */
    private const DEFAULT_AUDIENCE = 'guided';

    /** Default review state. */
    private const DEFAULT_REVIEW_STATE = 'draft';

    /**
     * Define form.
     */
    protected function definition(): void {
        $mform = $this->_form;

        $this->add_identity_section($mform);
        $this->add_tag_section($mform);
        $this->add_advisory_section($mform);
        $this->add_review_section($mform);
        $this->add_metadata_section($mform);

        $this->add_action_buttons(true);

        $this->set_defaults_from_customdata();
    }

    /**
     * Add identity fields.
     *
     * @param \MoodleQuickForm $mform Form object.
     */
    private function add_identity_section(\MoodleQuickForm $mform): void {
        $mform->addElement('header', 'identityhdr', get_string('contenttag:identity', 'uckkarchive', null, true));

        $mform->addElement('hidden', 'id');
        $mform->setType('id', PARAM_INT);

        $mform->addElement('hidden', 'cmid');
        $mform->setType('cmid', PARAM_INT);

        $mform->addElement('hidden', 'tagid');
        $mform->setType('tagid', PARAM_INT);

        $mform->addElement('hidden', 'uuid');
        $mform->setType('uuid', PARAM_ALPHANUMEXT);

        $tagsetoptions = $this->get_tag_set_options();
        if (!empty($tagsetoptions)) {
            $mform->addElement('select', 'tagsetid', get_string('contenttag:tagset', 'uckkarchive', null, true), $tagsetoptions);
            $mform->setType('tagsetid', PARAM_INT);
            $mform->setDefault('tagsetid', 0);
        } else {
            $mform->addElement('hidden', 'tagsetid', 0);
            $mform->setType('tagsetid', PARAM_INT);
        }
    }

    /**
     * Add core tag fields.
     *
     * @param \MoodleQuickForm $mform Form object.
     */
    private function add_tag_section(\MoodleQuickForm $mform): void {
        $mform->addElement('header', 'taghdr', get_string('contenttag:tag', 'uckkarchive', null, true));

        $mform->addElement(
            'text',
            'tagkey',
            get_string('contenttag:tagkey', 'uckkarchive', null, true),
            ['size' => 48, 'maxlength' => 128]
        );
        $mform->setType('tagkey', PARAM_ALPHANUMEXT);
        $mform->addRule('tagkey', get_string('required'), 'required', null, 'client');
        $mform->addHelpButton('tagkey', 'contenttag:tagkey', 'uckkarchive');

        $mform->addElement(
            'text',
            'label',
            get_string('contenttag:label', 'uckkarchive', null, true),
            ['size' => 64, 'maxlength' => 255]
        );
        $mform->setType('label', PARAM_TEXT);
        $mform->addRule('label', get_string('required'), 'required', null, 'client');

        $mform->addElement(
            'textarea',
            'description',
            get_string('contenttag:description', 'uckkarchive', null, true),
            ['rows' => 5, 'cols' => 80]
        );
        $mform->setType('description', PARAM_TEXT);

        $mform->addElement(
            'select',
            'category',
            get_string('contenttag:category', 'uckkarchive', null, true),
            $this->get_category_options()
        );
        $mform->setType('category', PARAM_ALPHANUMEXT);
        $mform->setDefault('category', self::DEFAULT_CATEGORY);
    }

    /**
     * Add advisory behaviour fields.
     *
     * @param \MoodleQuickForm $mform Form object.
     */
    private function add_advisory_section(\MoodleQuickForm $mform): void {
        $mform->addElement('header', 'advisoryhdr', get_string('contenttag:advisory', 'uckkarchive', null, true));

        $mform->addElement(
            'select',
            'severity',
            get_string('contenttag:severity', 'uckkarchive', null, true),
            $this->get_severity_options()
        );
        $mform->setType('severity', PARAM_ALPHANUMEXT);
        $mform->setDefault('severity', self::DEFAULT_SEVERITY);

        $mform->addElement(
            'select',
            'defaultaudience',
            get_string('contenttag:defaultaudience', 'uckkarchive', null, true),
            $this->get_audience_options()
        );
        $mform->setType('defaultaudience', PARAM_ALPHANUMEXT);
        $mform->setDefault('defaultaudience', self::DEFAULT_AUDIENCE);

        $mform->addElement(
            'advcheckbox',
            'iscultural',
            get_string('contenttag:iscultural', 'uckkarchive', null, true),
            get_string('contenttag:iscultural_desc', 'uckkarchive', null, true)
        );
        $mform->setType('iscultural', PARAM_BOOL);
        $mform->setDefault('iscultural', 0);

        $mform->addElement(
            'advcheckbox',
            'restrictsdefault',
            get_string('contenttag:restrictsdefault', 'uckkarchive', null, true),
            get_string('contenttag:restrictsdefault_desc', 'uckkarchive', null, true)
        );
        $mform->setType('restrictsdefault', PARAM_BOOL);
        $mform->setDefault('restrictsdefault', 0);
    }

    /**
     * Add review/state fields.
     *
     * @param \MoodleQuickForm $mform Form object.
     */
    private function add_review_section(\MoodleQuickForm $mform): void {
        $mform->addElement('header', 'reviewhdr', get_string('contenttag:review', 'uckkarchive', null, true));

        $mform->addElement(
            'select',
            'reviewstate',
            get_string('contenttag:reviewstate', 'uckkarchive', null, true),
            $this->get_review_state_options()
        );
        $mform->setType('reviewstate', PARAM_ALPHANUMEXT);
        $mform->setDefault('reviewstate', self::DEFAULT_REVIEW_STATE);

        $mform->addElement(
            'advcheckbox',
            'active',
            get_string('contenttag:active', 'uckkarchive', null, true),
            get_string('contenttag:active_desc', 'uckkarchive', null, true)
        );
        $mform->setType('active', PARAM_BOOL);
        $mform->setDefault('active', 1);

        $mform->addElement(
            'text',
            'sortorder',
            get_string('contenttag:sortorder', 'uckkarchive', null, true),
            ['size' => 8, 'maxlength' => 10]
        );
        $mform->setType('sortorder', PARAM_INT);
        $mform->setDefault('sortorder', 0);
    }

    /**
     * Add metadata fields.
     *
     * @param \MoodleQuickForm $mform Form object.
     */
    private function add_metadata_section(\MoodleQuickForm $mform): void {
        $mform->addElement('header', 'metadatahdr', get_string('contenttag:metadata', 'uckkarchive', null, true));

        $mform->addElement(
            'textarea',
            'metadata',
            get_string('contenttag:metadatajson', 'uckkarchive', null, true),
            ['rows' => 8, 'cols' => 80]
        );
        $mform->setType('metadata', PARAM_RAW);
        $mform->setDefault('metadata', '{}');
        $mform->addHelpButton('metadata', 'contenttag:metadatajson', 'uckkarchive');
    }

    /**
     * Validate form data.
     *
     * @param array<string, mixed> $data Submitted data.
     * @param array<string, mixed> $files Submitted files.
     * @return array<string, string>
     */
    public function validation($data, $files): array {
        $errors = parent::validation($data, $files);

        $tagkey = trim((string)($data['tagkey'] ?? ''));
        if ($tagkey === '') {
            $errors['tagkey'] = get_string('required');
        } else if (!$this->is_valid_machine_key($tagkey)) {
            $errors['tagkey'] = get_string('contenttag:error:invalidtagkey', 'uckkarchive', null, true);
        }

        $label = trim((string)($data['label'] ?? ''));
        if ($label === '') {
            $errors['label'] = get_string('required');
        }

        $category = (string)($data['category'] ?? '');
        if (!array_key_exists($category, $this->get_category_options())) {
            $errors['category'] = get_string('contenttag:error:invalidcategory', 'uckkarchive', null, true);
        }

        $severity = (string)($data['severity'] ?? '');
        if (!array_key_exists($severity, $this->get_severity_options())) {
            $errors['severity'] = get_string('contenttag:error:invalidseverity', 'uckkarchive', null, true);
        }

        $audience = (string)($data['defaultaudience'] ?? '');
        if (!array_key_exists($audience, $this->get_audience_options())) {
            $errors['defaultaudience'] = get_string('contenttag:error:invalidaudience', 'uckkarchive', null, true);
        }

        $reviewstate = (string)($data['reviewstate'] ?? '');
        if (!array_key_exists($reviewstate, $this->get_review_state_options())) {
            $errors['reviewstate'] = get_string('contenttag:error:invalidreviewstate', 'uckkarchive', null, true);
        }

        if (!empty($data['metadata'])) {
            $decoded = json_decode((string)$data['metadata'], true);
            if (!is_array($decoded)) {
                $errors['metadata'] = get_string('contenttag:error:invalidmetadata', 'uckkarchive', null, true);
            }
        }

        if (!empty($data['iscultural']) && empty($data['restrictsdefault'])) {
            $category = (string)($data['category'] ?? '');
            if ($category === 'cultural_protocol') {
                // Cultural protocol tags may remain informational, but make the
                // distinction explicit for the editor.
                // No error is returned here intentionally.
            }
        }

        return $errors;
    }

    /**
     * Return cleaned tag data suitable for local\content_tag::create/update.
     *
     * @return array<string, mixed>
     */
    public function get_tag_data(): array {
        $data = (array)$this->get_data();

        $metadata = [];
        if (!empty($data['metadata'])) {
            $decoded = json_decode((string)$data['metadata'], true);
            if (is_array($decoded)) {
                $metadata = $decoded;
            }
        }

        return [
            'id' => (int)($data['id'] ?? $data['tagid'] ?? 0),
            'uuid' => trim((string)($data['uuid'] ?? '')),
            'tagsetid' => (int)($data['tagsetid'] ?? 0),
            'tagkey' => trim((string)($data['tagkey'] ?? '')),
            'label' => trim((string)($data['label'] ?? '')),
            'description' => trim((string)($data['description'] ?? '')),
            'category' => trim((string)($data['category'] ?? self::DEFAULT_CATEGORY)),
            'severity' => trim((string)($data['severity'] ?? self::DEFAULT_SEVERITY)),
            'defaultaudience' => trim((string)($data['defaultaudience'] ?? self::DEFAULT_AUDIENCE)),
            'iscultural' => !empty($data['iscultural']) ? 1 : 0,
            'restrictsdefault' => !empty($data['restrictsdefault']) ? 1 : 0,
            'reviewstate' => trim((string)($data['reviewstate'] ?? self::DEFAULT_REVIEW_STATE)),
            'active' => !empty($data['active']) ? 1 : 0,
            'sortorder' => (int)($data['sortorder'] ?? 0),
            'metadata' => $metadata,
        ];
    }

    /**
     * Set defaults from customdata.
     */
    private function set_defaults_from_customdata(): void {
        $defaults = [];

        if (!empty($this->_customdata['cmid'])) {
            $defaults['cmid'] = (int)$this->_customdata['cmid'];
        }

        if (!empty($this->_customdata['tagid'])) {
            $defaults['tagid'] = (int)$this->_customdata['tagid'];
            $defaults['id'] = (int)$this->_customdata['tagid'];
        }

        if (!empty($this->_customdata['tagsetid'])) {
            $defaults['tagsetid'] = (int)$this->_customdata['tagsetid'];
        }

        if (!empty($this->_customdata['tag'])) {
            $tag = $this->_customdata['tag'];
            if (is_array($tag)) {
                $tag = (object)$tag;
            }

            if ($tag instanceof stdClass) {
                $defaults = array_merge($defaults, $this->defaults_from_record($tag));
            }
        }

        $this->set_data($defaults);
    }

    /**
     * Convert an existing tag record to form defaults.
     *
     * @param stdClass $tag Existing tag record.
     * @return array<string, mixed>
     */
    private function defaults_from_record(stdClass $tag): array {
        $metadata = $tag->metadata ?? '{}';
        if (is_array($metadata)) {
            $metadata = json_encode($metadata, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
        } else if ($metadata instanceof stdClass) {
            $metadata = json_encode((array)$metadata, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
        }

        if (!is_string($metadata) || trim($metadata) === '') {
            $metadata = '{}';
        }

        return [
            'id' => (int)($tag->id ?? 0),
            'tagid' => (int)($tag->id ?? 0),
            'uuid' => (string)($tag->uuid ?? ''),
            'tagsetid' => (int)($tag->tagsetid ?? 0),
            'tagkey' => (string)($tag->tagkey ?? ''),
            'label' => (string)($tag->label ?? ''),
            'description' => (string)($tag->description ?? ''),
            'category' => (string)($tag->category ?? self::DEFAULT_CATEGORY),
            'severity' => (string)($tag->severity ?? self::DEFAULT_SEVERITY),
            'defaultaudience' => (string)($tag->defaultaudience ?? self::DEFAULT_AUDIENCE),
            'iscultural' => !empty($tag->iscultural) ? 1 : 0,
            'restrictsdefault' => !empty($tag->restrictsdefault) ? 1 : 0,
            'reviewstate' => (string)($tag->reviewstate ?? self::DEFAULT_REVIEW_STATE),
            'active' => !empty($tag->active) ? 1 : 0,
            'sortorder' => (int)($tag->sortorder ?? 0),
            'metadata' => $metadata,
        ];
    }

    /**
     * Return tag set options.
     *
     * @return array<int, string>
     */
    private function get_tag_set_options(): array {
        global $DB;

        $options = [0 => get_string('none')];

        if (!$DB->get_manager()->table_exists(new \xmldb_table('uckkarchive_content_tag_set'))) {
            return $options;
        }

        $records = $DB->get_records('uckkarchive_content_tag_set', null, 'sortorder ASC, name ASC, id ASC');

        foreach ($records as $record) {
            $label = $record->name ?? $record->label ?? $record->setkey ?? ('#' . $record->id);
            $options[(int)$record->id] = format_string((string)$label);
        }

        return $options;
    }

    /**
     * Return category options.
     *
     * @return array<string, string>
     */
    private function get_category_options(): array {
        $categories = class_exists(content_tag::class) ? content_tag::get_categories() : [
            'general_advisory',
            'cultural_protocol',
            'classroom_suitability',
            'integrity_sensitive',
            'youth_access',
            'source_rights',
        ];

        return $this->string_options('contenttag:category:', $categories);
    }

    /**
     * Return severity options.
     *
     * @return array<string, string>
     */
    private function get_severity_options(): array {
        $severities = class_exists(content_tag::class) ? content_tag::get_severities() : [
            'notice',
            'moderate',
            'strong',
            'restricted',
        ];

        return $this->string_options('contenttag:severity:', $severities);
    }

    /**
     * Return audience options.
     *
     * @return array<string, string>
     */
    private function get_audience_options(): array {
        $audiences = class_exists(content_tag::class) ? content_tag::get_audience_values() : [
            'general',
            'guided',
            'mature',
            'restricted',
            'restricted_cultural',
            'restricted_integrity',
            'staff_only',
        ];

        return $this->string_options('contenttag:audience:', $audiences);
    }

    /**
     * Return review state options.
     *
     * @return array<string, string>
     */
    private function get_review_state_options(): array {
        $states = class_exists(content_tag::class) ? content_tag::get_review_states() : [
            'draft',
            'pending_review',
            'reviewed',
            'approved',
            'contested',
            'retired',
        ];

        return $this->string_options('contenttag:reviewstate:', $states);
    }

    /**
     * Convert machine keys to translated option labels.
     *
     * @param string $prefix Language string prefix.
     * @param string[] $values Values.
     * @return array<string, string>
     */
    private function string_options(string $prefix, array $values): array {
        $manager = get_string_manager();
        $options = [];

        foreach ($values as $value) {
            $key = $prefix . $value;
            $options[$value] = $manager->string_exists($key, 'uckkarchive')
                ? get_string($key, 'uckkarchive')
                : ucfirst(str_replace('_', ' ', $value));
        }

        return $options;
    }

    /**
     * Validate a machine key.
     *
     * @param string $key Key.
     * @return bool
     */
    private function is_valid_machine_key(string $key): bool {
        return (bool)preg_match('/^[a-z0-9][a-z0-9_-]*$/', $key);
    }
}