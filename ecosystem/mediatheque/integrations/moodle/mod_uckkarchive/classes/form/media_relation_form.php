<?php
// This file is part of Moodle - https://moodle.org/.
//
// Moodle is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// any later version.

/**
 * Media relation form for mod_uckkarchive.
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
require_once(dirname(__DIR__) . '/local/media_relation.php');

use context_module;
use mod_uckkarchive\local\media_relation;
use moodleform;

/**
 * Form used to create or edit one media relation.
 *
 * A media relation connects archive-owned objects such as media, media
 * versions, archive items, proofs, Kristals, media collections, content
 * advisory markers, and external works.
 *
 * This form only collects relation data. It does not:
 *
 * - create the relation record;
 * - decide access;
 * - bypass media/content policy;
 * - grant access to restricted cultural material;
 * - validate the existence of all target objects across every table.
 *
 * Those checks belong to controllers, external services, and local domain
 * services.
 */
final class media_relation_form extends moodleform {
    /** Default source object type. */
    private const DEFAULT_FROMTYPE = 'media';

    /** Default target object type. */
    private const DEFAULT_TOTYPE = 'media';

    /** Default relation type. */
    private const DEFAULT_RELATIONTYPE = 'references';

    /**
     * Define the form.
     *
     * @return void
     */
    protected function definition(): void {
        $mform = $this->_form;

        $this->add_identity_section($mform);
        $this->add_relation_section($mform);
        $this->add_metadata_section($mform);
        $this->add_hidden_fields($mform);

        $this->add_action_buttons(true, get_string('savemediarelation', 'uckkarchive'));
    }

    /**
     * Add identity fields.
     *
     * @param \MoodleQuickForm $mform Form object.
     * @return void
     */
    private function add_identity_section(\MoodleQuickForm $mform): void {
        $mform->addElement('header', 'identityheader', get_string('mediarelationidentity', 'uckkarchive'));

        $mform->addElement('text', 'fromid', get_string('mediarelationfromid', 'uckkarchive'), [
            'size' => 12,
            'maxlength' => 10,
        ]);
        $mform->setType('fromid', PARAM_INT);
        $mform->addRule('fromid', null, 'required', null, 'client');
        $mform->addRule('fromid', null, 'numeric', null, 'client');

        $mform->addElement('select', 'fromtype', get_string('mediarelationfromtype', 'uckkarchive'),
            $this->get_object_type_options()
        );
        $mform->setDefault('fromtype', self::DEFAULT_FROMTYPE);
        $mform->addRule('fromtype', null, 'required', null, 'client');

        $mform->addElement('text', 'toid', get_string('mediarelationtoid', 'uckkarchive'), [
            'size' => 12,
            'maxlength' => 10,
        ]);
        $mform->setType('toid', PARAM_INT);
        $mform->addRule('toid', null, 'required', null, 'client');
        $mform->addRule('toid', null, 'numeric', null, 'client');

        $mform->addElement('select', 'totype', get_string('mediarelationtotype', 'uckkarchive'),
            $this->get_object_type_options()
        );
        $mform->setDefault('totype', self::DEFAULT_TOTYPE);
        $mform->addRule('totype', null, 'required', null, 'client');
    }

    /**
     * Add relation type and ordering fields.
     *
     * @param \MoodleQuickForm $mform Form object.
     * @return void
     */
    private function add_relation_section(\MoodleQuickForm $mform): void {
        $mform->addElement('header', 'relationheader', get_string('mediarelation', 'uckkarchive'));

        $mform->addElement('select', 'relationtype', get_string('mediarelationtype', 'uckkarchive'),
            $this->get_relation_type_options()
        );
        $mform->setDefault('relationtype', self::DEFAULT_RELATIONTYPE);
        $mform->addRule('relationtype', null, 'required', null, 'client');

        $mform->addElement('text', 'sortorder', get_string('sortorder', 'uckkarchive'), [
            'size' => 8,
            'maxlength' => 10,
        ]);
        $mform->setType('sortorder', PARAM_INT);
        $mform->setDefault('sortorder', 0);
        $mform->addRule('sortorder', null, 'numeric', null, 'client');

        $mform->addElement('textarea', 'relationnote', get_string('mediarelationnote', 'uckkarchive'), [
            'rows' => 3,
            'cols' => 80,
            'maxlength' => 2000,
        ]);
        $mform->setType('relationnote', PARAM_TEXT);
        $mform->addHelpButton('relationnote', 'mediarelationnote', 'uckkarchive');
    }

    /**
     * Add metadata fields.
     *
     * @param \MoodleQuickForm $mform Form object.
     * @return void
     */
    private function add_metadata_section(\MoodleQuickForm $mform): void {
        $mform->addElement('header', 'metadataheader', get_string('metadata', 'uckkarchive'));

        $mform->addElement('textarea', 'metadata', get_string('metadatajson', 'uckkarchive'), [
            'rows' => 6,
            'cols' => 80,
        ]);
        $mform->setType('metadata', PARAM_RAW);
        $mform->addHelpButton('metadata', 'metadatajson', 'uckkarchive');
    }

    /**
     * Add hidden fields expected by controllers.
     *
     * @param \MoodleQuickForm $mform Form object.
     * @return void
     */
    private function add_hidden_fields(\MoodleQuickForm $mform): void {
        foreach ($this->get_default_hidden_values() as $name => $value) {
            $mform->addElement('hidden', $name, $value);
            $mform->setType($name, PARAM_ALPHANUMEXT);
        }

        $mform->setType('id', PARAM_INT);
        $mform->setType('relationid', PARAM_INT);
        $mform->setType('cmid', PARAM_INT);
        $mform->setType('archiveid', PARAM_INT);
        $mform->setType('returnurl', PARAM_LOCALURL);
    }

    /**
     * Validate submitted data.
     *
     * @param array<string, mixed> $data Submitted data.
     * @param array<string, mixed> $files Submitted files.
     * @return array<string, string>
     */
    public function validation($data, $files): array {
        $errors = parent::validation($data, $files);

        $objecttypes = $this->get_object_type_options();
        $relationtypes = $this->get_relation_type_options();

        $this->validate_choice($errors, $data, 'fromtype', $objecttypes);
        $this->validate_choice($errors, $data, 'totype', $objecttypes);
        $this->validate_choice($errors, $data, 'relationtype', $relationtypes);

        $fromid = (int)($data['fromid'] ?? 0);
        $toid = (int)($data['toid'] ?? 0);
        $sortorder = (int)($data['sortorder'] ?? 0);

        if ($fromid <= 0) {
            $errors['fromid'] = get_string('invaliddata', 'error');
        }

        if ($toid <= 0) {
            $errors['toid'] = get_string('invaliddata', 'error');
        }

        if ($sortorder < 0) {
            $errors['sortorder'] = get_string('invaliddata', 'error');
        }

        $fromtype = (string)($data['fromtype'] ?? '');
        $totype = (string)($data['totype'] ?? '');
        $relationtype = (string)($data['relationtype'] ?? '');

        if ($fromid > 0 && $toid > 0 && $fromtype !== '' && $totype !== ''
                && $fromtype === $totype && $fromid === $toid) {
            $errors['toid'] = get_string('mediarelationselfnotallowed', 'uckkarchive');
        }

        $this->validate_relation_shape($errors, $fromtype, $fromid, $relationtype, $totype, $toid);

        $metadata = trim((string)($data['metadata'] ?? ''));
        if ($metadata !== '' && !$this->is_valid_json_object($metadata)) {
            $errors['metadata'] = get_string('invalidjson', 'uckkarchive');
        }

        return $errors;
    }

    /**
     * Validate relation shape.
     *
     * This does not check whether every target object exists. Existence and
     * permission checks belong to the write service/controller.
     *
     * @param array<string, string> $errors Validation errors.
     * @param string $fromtype Source object type.
     * @param int $fromid Source id.
     * @param string $relationtype Relation type.
     * @param string $totype Target object type.
     * @param int $toid Target id.
     * @return void
     */
    private function validate_relation_shape(
        array &$errors,
        string $fromtype,
        int $fromid,
        string $relationtype,
        string $totype,
        int $toid
    ): void {
        if ($fromid <= 0 || $toid <= 0 || $fromtype === '' || $totype === '' || $relationtype === '') {
            return;
        }

        $mediaobject = media_relation::OBJECT_MEDIA;
        $mediaversionobject = media_relation::OBJECT_MEDIA_VERSION;

        if (in_array($relationtype, media_relation::get_media_to_media_relation_types(), true)) {
            $allowed = [$mediaobject, $mediaversionobject];

            if (!in_array($fromtype, $allowed, true) || !in_array($totype, $allowed, true)) {
                $errors['relationtype'] = get_string('mediarelationrequiresmediaobjects', 'uckkarchive');
            }

            return;
        }

        $requiredtargets = [
            media_relation::TYPE_BELONGS_TO_ITEM => media_relation::OBJECT_ARCHIVE_ITEM,
            media_relation::TYPE_BELONGS_TO_KRISTAL => media_relation::OBJECT_KRISTAL,
            media_relation::TYPE_BELONGS_TO_COLLECTION => media_relation::OBJECT_MEDIA_COLLECTION,
            media_relation::TYPE_REFERENCES_EXTERNAL_WORK => media_relation::OBJECT_EXTERNAL_WORK,
            media_relation::TYPE_CONTAINS_CONTENT_MARKER => media_relation::OBJECT_CONTENT_MARKER,
        ];

        if (isset($requiredtargets[$relationtype]) && $totype !== $requiredtargets[$relationtype]) {
            $errors['totype'] = get_string('mediarelationinvalidtargettype', 'uckkarchive');
        }

        if (in_array($relationtype, [
            media_relation::TYPE_BELONGS_TO_ITEM,
            media_relation::TYPE_BELONGS_TO_KRISTAL,
            media_relation::TYPE_BELONGS_TO_COLLECTION,
            media_relation::TYPE_REFERENCES_EXTERNAL_WORK,
            media_relation::TYPE_CONTAINS_CONTENT_MARKER,
        ], true) && !in_array($fromtype, [$mediaobject, $mediaversionobject], true)) {
            $errors['fromtype'] = get_string('mediarelationrequiresmediaobjectsource', 'uckkarchive');
        }
    }

    /**
     * Validate a submitted select value.
     *
     * @param array<string, string> $errors Validation errors.
     * @param array<string, mixed> $data Submitted data.
     * @param string $field Field name.
     * @param array<string, string> $options Allowed options.
     * @return void
     */
    private function validate_choice(array &$errors, array $data, string $field, array $options): void {
        $value = (string)($data[$field] ?? '');

        if ($value === '') {
            $errors[$field] = get_string('required');
            return;
        }

        if (!array_key_exists($value, $options)) {
            $errors[$field] = get_string('invaliddata', 'error');
        }
    }

    /**
     * Return customdata context.
     *
     * @return context_module|null
     */
    private function get_context(): ?context_module {
        if (!empty($this->_customdata['context']) && $this->_customdata['context'] instanceof context_module) {
            return $this->_customdata['context'];
        }

        if (!empty($this->_customdata['cmid'])) {
            return context_module::instance((int)$this->_customdata['cmid'], IGNORE_MISSING) ?: null;
        }

        return null;
    }

    /**
     * Return default hidden values.
     *
     * @return array<string, mixed>
     */
    private function get_default_hidden_values(): array {
        return [
            'id' => $this->_customdata['id'] ?? 0,
            'relationid' => $this->_customdata['relationid'] ?? 0,
            'cmid' => $this->_customdata['cmid'] ?? 0,
            'archiveid' => $this->_customdata['archiveid'] ?? 0,
            'returnurl' => $this->_customdata['returnurl'] ?? '',
        ];
    }

    /**
     * Return object type options.
     *
     * @return array<string, string>
     */
    private function get_object_type_options(): array {
        return [
            media_relation::OBJECT_MEDIA => get_string('mediarelationobject:media', 'uckkarchive'),
            media_relation::OBJECT_MEDIA_VERSION => get_string('mediarelationobject:media_version', 'uckkarchive'),
            media_relation::OBJECT_ARCHIVE_ITEM => get_string('mediarelationobject:archive_item', 'uckkarchive'),
            media_relation::OBJECT_PROOF => get_string('mediarelationobject:proof', 'uckkarchive'),
            media_relation::OBJECT_KRISTAL => get_string('mediarelationobject:kristal', 'uckkarchive'),
            media_relation::OBJECT_MEDIA_COLLECTION => get_string('mediarelationobject:media_collection', 'uckkarchive'),
            media_relation::OBJECT_MEDIA_COLLECTION_ITEM => get_string('mediarelationobject:media_collection_item', 'uckkarchive'),
            media_relation::OBJECT_CONTENT_MARKER => get_string('mediarelationobject:content_marker', 'uckkarchive'),
            media_relation::OBJECT_EXTERNAL_WORK => get_string('mediarelationobject:external_work', 'uckkarchive'),
        ];
    }

    /**
     * Return relation type options.
     *
     * @return array<string, string>
     */
    private function get_relation_type_options(): array {
        return [
            media_relation::TYPE_BELONGS_TO_ITEM => get_string('mediarelationtype:belongs_to_item', 'uckkarchive'),
            media_relation::TYPE_BELONGS_TO_KRISTAL => get_string('mediarelationtype:belongs_to_kristal', 'uckkarchive'),
            media_relation::TYPE_BELONGS_TO_COLLECTION => get_string('mediarelationtype:belongs_to_collection', 'uckkarchive'),
            media_relation::TYPE_IS_DERIVATIVE_OF => get_string('mediarelationtype:is_derivative_of', 'uckkarchive'),
            media_relation::TYPE_IS_TRANSLATION_OF => get_string('mediarelationtype:is_translation_of', 'uckkarchive'),
            media_relation::TYPE_IS_EXCERPT_OF => get_string('mediarelationtype:is_excerpt_of', 'uckkarchive'),
            media_relation::TYPE_IS_PROOF_FOR => get_string('mediarelationtype:is_proof_for', 'uckkarchive'),
            media_relation::TYPE_IS_SOURCE_FOR => get_string('mediarelationtype:is_source_for', 'uckkarchive'),
            media_relation::TYPE_REPLACES => get_string('mediarelationtype:replaces', 'uckkarchive'),
            media_relation::TYPE_REFERENCES => get_string('mediarelationtype:references', 'uckkarchive'),
            media_relation::TYPE_DUPLICATES => get_string('mediarelationtype:duplicates', 'uckkarchive'),
            media_relation::TYPE_REFERENCES_EXTERNAL_WORK => get_string('mediarelationtype:references_external_work', 'uckkarchive'),
            media_relation::TYPE_CONTAINS_CONTENT_MARKER => get_string('mediarelationtype:contains_content_marker', 'uckkarchive'),
        ];
    }

    /**
     * Return whether raw metadata is a JSON object.
     *
     * @param string $value Raw JSON.
     * @return bool
     */
    private function is_valid_json_object(string $value): bool {
        json_decode($value, true);

        if (json_last_error() !== JSON_ERROR_NONE) {
            return false;
        }

        $decoded = json_decode($value, true);

        return is_array($decoded) && array_is_list($decoded) === false;
    }
}

