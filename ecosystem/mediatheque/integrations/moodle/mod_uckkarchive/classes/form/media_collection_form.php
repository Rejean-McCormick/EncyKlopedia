<?php
// This file is part of Moodle - https://moodle.org/
//
// Moodle is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// any later version.

/**
 * Media collection form for mod_uckkarchive.
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
 * Form used to create or edit one media collection.
 *
 * A media collection is a curated grouping of media records. This form collects
 * collection identity, description, visibility, suitability, ordering, curation
 * notes, optional initial media ids, tags, and JSON metadata.
 *
 * It does not decide final policy, restricted access, collection membership
 * authority, export authority, content advisory review, or media file access.
 * Those checks belong to local policy classes, controllers, and external
 * services.
 */
final class media_collection_form extends moodleform {
    /** Collection type: general collection. */
    private const TYPE_GENERAL = 'general';

    /** Collection type: lesson/teaching collection. */
    private const TYPE_LESSON = 'lesson';

    /** Collection type: gallery. */
    private const TYPE_GALLERY = 'gallery';

    /** Collection type: playlist. */
    private const TYPE_PLAYLIST = 'playlist';

    /** Collection type: exhibit. */
    private const TYPE_EXHIBIT = 'exhibit';

    /** Collection type: archive set. */
    private const TYPE_ARCHIVE_SET = 'archive_set';

    /** Collection type: content advisory set. */
    private const TYPE_CONTENT_ADVISORY = 'content_advisory';

    /** Collection type: restricted protocol set. */
    private const TYPE_RESTRICTED_PROTOCOL = 'restricted_protocol';

    /** Status: draft. */
    private const STATUS_DRAFT = 'draft';

    /** Status: active. */
    private const STATUS_ACTIVE = 'active';

    /** Status: hidden. */
    private const STATUS_HIDDEN = 'hidden';

    /** Status: archived. */
    private const STATUS_ARCHIVED = 'archived';

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
     * Define form fields.
     *
     * @return void
     */
    protected function definition(): void {
        $mform = $this->_form;

        $this->add_identity_section($mform);
        $this->add_curation_section($mform);
        $this->add_governance_section($mform);
        $this->add_membership_section($mform);
        $this->add_metadata_section($mform);
        $this->add_hidden_fields($mform);

        $this->add_action_buttons(true, $this->str('savemediacollection', 'Save media collection'));
    }

    /**
     * Add identity fields.
     *
     * @param \MoodleQuickForm $mform Form object.
     * @return void
     */
    private function add_identity_section(\MoodleQuickForm $mform): void {
        $mform->addElement('header', 'identityheader', $this->str('mediacollectionidentity', 'Collection identity'));

        $mform->addElement('text', 'title', $this->str('mediacollectiontitle', 'Collection title'), [
            'size' => 64,
            'maxlength' => 255,
        ]);
        $mform->setType('title', PARAM_TEXT);
        $mform->addRule('title', null, 'required', null, 'client');

        $mform->addElement(
            'select',
            'collectiontype',
            $this->str('mediacollectiontype', 'Collection type'),
            $this->get_collection_type_options()
        );
        $mform->setDefault('collectiontype', self::TYPE_GENERAL);
        $mform->addRule('collectiontype', null, 'required', null, 'client');

        $mform->addElement('textarea', 'description', $this->str('description', 'Description'), [
            'rows' => 8,
            'cols' => 80,
        ]);
        $mform->setType('description', PARAM_RAW);
    }

    /**
     * Add curation fields.
     *
     * @param \MoodleQuickForm $mform Form object.
     * @return void
     */
    private function add_curation_section(\MoodleQuickForm $mform): void {
        $mform->addElement('header', 'curationheader', $this->str('mediacollectioncuration', 'Collection curation'));

        $mform->addElement('textarea', 'curationnote', $this->str('curationnote', 'Curation note'), [
            'rows' => 5,
            'cols' => 80,
        ]);
        $mform->setType('curationnote', PARAM_RAW);

        $mform->addElement('textarea', 'teachingnote', $this->str('teachingnote', 'Teaching note'), [
            'rows' => 5,
            'cols' => 80,
        ]);
        $mform->setType('teachingnote', PARAM_RAW);

        $mform->addElement('textarea', 'culturalprotocolnote', $this->str('culturalprotocolnote', 'Cultural protocol note'), [
            'rows' => 5,
            'cols' => 80,
        ]);
        $mform->setType('culturalprotocolnote', PARAM_RAW);

        $mform->addElement('text', 'sortorder', $this->str('sortorder', 'Sort order'), [
            'size' => 8,
            'maxlength' => 10,
        ]);
        $mform->setType('sortorder', PARAM_INT);
        $mform->setDefault('sortorder', 0);

        $mform->addElement('selectyesno', 'featured', $this->str('featuredcollection', 'Featured collection'));
        $mform->setDefault('featured', 0);
    }

    /**
     * Add governance fields.
     *
     * @param \MoodleQuickForm $mform Form object.
     * @return void
     */
    private function add_governance_section(\MoodleQuickForm $mform): void {
        $mform->addElement('header', 'governanceheader', $this->str('governance', 'Governance'));

        $mform->addElement('select', 'status', $this->str('status', 'Status'), $this->get_status_options());
        $mform->setDefault('status', self::STATUS_DRAFT);
        $mform->addRule('status', null, 'required', null, 'client');

        $mform->addElement('select', 'visibility', $this->str('visibility', 'Visibility'), $this->get_visibility_options());
        $mform->setDefault('visibility', self::VISIBILITY_COURSE);
        $mform->addRule('visibility', null, 'required', null, 'client');

        $mform->addElement(
            'select',
            'audiencesuitability',
            $this->str('audiencesuitability', 'Audience suitability'),
            $this->get_audience_options()
        );
        $mform->setDefault('audiencesuitability', self::SUITABILITY_GUIDED);
        $mform->addRule('audiencesuitability', null, 'required', null, 'client');

        if (!$this->can_manage_restricted()) {
            $mform->hardFreeze(['visibility', 'audiencesuitability']);
        }
    }

    /**
     * Add initial membership fields.
     *
     * @param \MoodleQuickForm $mform Form object.
     * @return void
     */
    private function add_membership_section(\MoodleQuickForm $mform): void {
        $mform->addElement('header', 'membershipheader', $this->str('mediacollectionmembership', 'Collection membership'));

        $mform->addElement('textarea', 'mediaids', $this->str('initialmediaids', 'Initial media ids'), [
            'rows' => 4,
            'cols' => 80,
        ]);
        $mform->setType('mediaids', PARAM_RAW);
        $mform->addHelpButton('mediaids', 'initialmediaids', 'uckkarchive');

        $mform->addElement('textarea', 'tags', $this->str('tags', 'Tags'), [
            'rows' => 4,
            'cols' => 80,
        ]);
        $mform->setType('tags', PARAM_RAW);
        $mform->addHelpButton('tags', 'tags', 'uckkarchive');
    }

    /**
     * Add metadata fields.
     *
     * @param \MoodleQuickForm $mform Form object.
     * @return void
     */
    private function add_metadata_section(\MoodleQuickForm $mform): void {
        $mform->addElement('header', 'metadataheader', $this->str('metadata', 'Metadata'));

        $mform->addElement('textarea', 'metadata', $this->str('metadatajson', 'Metadata JSON'), [
            'rows' => 8,
            'cols' => 80,
        ]);
        $mform->setType('metadata', PARAM_RAW);
        $mform->addHelpButton('metadata', 'metadatajson', 'uckkarchive');
    }

    /**
     * Add hidden fields.
     *
     * @param \MoodleQuickForm $mform Form object.
     * @return void
     */
    private function add_hidden_fields(\MoodleQuickForm $mform): void {
        foreach ([
            'cmid' => PARAM_INT,
            'archiveid' => PARAM_INT,
            'collectionid' => PARAM_INT,
            'returnurl' => PARAM_LOCALURL,
        ] as $field => $type) {
            $mform->addElement('hidden', $field);
            $mform->setType($field, $type);
        }

        $mform->setDefault('cmid', $this->get_custom_int('cmid'));
        $mform->setDefault('archiveid', $this->get_custom_int('archiveid'));
        $mform->setDefault('collectionid', $this->get_custom_int('collectionid'));
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

        $title = trim((string)($data['title'] ?? ''));
        if ($title === '') {
            $errors['title'] = get_string('required');
        }

        if (!array_key_exists((string)($data['collectiontype'] ?? ''), $this->get_collection_type_options())) {
            $errors['collectiontype'] = $this->str('invalidcollectiontype', 'Invalid collection type.');
        }

        if (!array_key_exists((string)($data['status'] ?? ''), $this->get_status_options())) {
            $errors['status'] = $this->str('invalidstatus', 'Invalid status.');
        }

        if (!array_key_exists((string)($data['visibility'] ?? ''), $this->get_visibility_options())) {
            $errors['visibility'] = $this->str('invalidvisibility', 'Invalid visibility.');
        }

        if (!array_key_exists((string)($data['audiencesuitability'] ?? ''), $this->get_audience_options())) {
            $errors['audiencesuitability'] = $this->str('invalidaudiencesuitability', 'Invalid audience suitability.');
        }

        if ((int)($data['sortorder'] ?? 0) < 0) {
            $errors['sortorder'] = $this->str('sortordernonnegative', 'Sort order must be zero or greater.');
        }

        $visibility = (string)($data['visibility'] ?? '');
        $audience = (string)($data['audiencesuitability'] ?? '');

        if (in_array($visibility, [self::VISIBILITY_RESTRICTED, self::VISIBILITY_RESTRICTED_INTEGRITY,
                self::VISIBILITY_RESTRICTED_CULTURAL], true) && !$this->can_manage_restricted()) {
            $errors['visibility'] = $this->str('restrictedvisibilitynotallowed', 'You cannot set restricted visibility.');
        }

        if (in_array($audience, [self::SUITABILITY_RESTRICTED, self::SUITABILITY_RESTRICTED_INTEGRITY,
                self::SUITABILITY_RESTRICTED_CULTURAL, self::SUITABILITY_STAFF_ONLY], true) &&
                !$this->can_manage_restricted()) {
            $errors['audiencesuitability'] = $this->str(
                'restrictedaudiencenotallowed',
                'You cannot set restricted audience suitability.'
            );
        }

        if (($visibility === self::VISIBILITY_RESTRICTED_CULTURAL ||
                $audience === self::SUITABILITY_RESTRICTED_CULTURAL) &&
                trim((string)($data['culturalprotocolnote'] ?? '')) === '') {
            $errors['culturalprotocolnote'] = $this->str(
                'culturalprotocolnoterequired',
                'A cultural protocol note is required.'
            );
        }

        if (!$this->is_valid_id_list((string)($data['mediaids'] ?? ''))) {
            $errors['mediaids'] = $this->str('invalidmediaids', 'Media ids must be a comma, space, or newline-separated list of positive integers.');
        }

        if (!$this->is_valid_tag_list((string)($data['tags'] ?? ''))) {
            $errors['tags'] = $this->str('invalidtags', 'Tags must be plain text values separated by commas or new lines.');
        }

        if (!$this->is_valid_json_object((string)($data['metadata'] ?? ''))) {
            $errors['metadata'] = $this->str('invalidmetadatajson', 'Metadata must be a valid JSON object.');
        }

        return $errors;
    }

    /**
     * Prepare current collection data for the form.
     *
     * @param stdClass $collection Collection record.
     * @return stdClass
     */
    public static function prepare_data(stdClass $collection): stdClass {
        if (isset($collection->metadata) && is_array($collection->metadata)) {
            $collection->metadata = json_encode($collection->metadata, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE);
        }

        if (isset($collection->mediaids) && is_array($collection->mediaids)) {
            $collection->mediaids = implode("\n", array_map('intval', $collection->mediaids));
        }

        if (isset($collection->tags) && is_array($collection->tags)) {
            $collection->tags = implode("\n", array_map('strval', $collection->tags));
        }

        if (!empty($collection->id) && empty($collection->collectionid)) {
            $collection->collectionid = (int)$collection->id;
        }

        return $collection;
    }

    /**
     * Return collection type options.
     *
     * @return array<string, string>
     */
    private function get_collection_type_options(): array {
        return [
            self::TYPE_GENERAL => $this->str('collectiontype:general', 'General collection'),
            self::TYPE_LESSON => $this->str('collectiontype:lesson', 'Lesson collection'),
            self::TYPE_GALLERY => $this->str('collectiontype:gallery', 'Gallery'),
            self::TYPE_PLAYLIST => $this->str('collectiontype:playlist', 'Playlist'),
            self::TYPE_EXHIBIT => $this->str('collectiontype:exhibit', 'Exhibit'),
            self::TYPE_ARCHIVE_SET => $this->str('collectiontype:archive_set', 'Archive set'),
            self::TYPE_CONTENT_ADVISORY => $this->str('collectiontype:content_advisory', 'Content advisory set'),
            self::TYPE_RESTRICTED_PROTOCOL => $this->str('collectiontype:restricted_protocol', 'Restricted protocol set'),
        ];
    }

    /**
     * Return status options.
     *
     * @return array<string, string>
     */
    private function get_status_options(): array {
        return [
            self::STATUS_DRAFT => $this->str('status:draft', 'Draft'),
            self::STATUS_ACTIVE => $this->str('status:active', 'Active'),
            self::STATUS_HIDDEN => $this->str('status:hidden', 'Hidden'),
            self::STATUS_ARCHIVED => $this->str('status:archived', 'Archived'),
        ];
    }

    /**
     * Return visibility options.
     *
     * @return array<string, string>
     */
    private function get_visibility_options(): array {
        $options = [
            self::VISIBILITY_PRIVATE => $this->str('visibility:private', 'Private'),
            self::VISIBILITY_USER => $this->str('visibility:user', 'User'),
            self::VISIBILITY_GROUP => $this->str('visibility:group', 'Group'),
            self::VISIBILITY_COURSE => $this->str('visibility:course', 'Course'),
            self::VISIBILITY_COHORT => $this->str('visibility:cohort', 'Cohort'),
            self::VISIBILITY_PROGRAM => $this->str('visibility:program', 'Program'),
            self::VISIBILITY_INSTITUTION => $this->str('visibility:institution', 'Institution'),
            self::VISIBILITY_PUBLIC => $this->str('visibility:public', 'Public'),
            self::VISIBILITY_RESTRICTED => $this->str('visibility:restricted', 'Restricted'),
            self::VISIBILITY_RESTRICTED_INTEGRITY => $this->str('visibility:restricted_integrity', 'Restricted integrity'),
            self::VISIBILITY_RESTRICTED_CULTURAL => $this->str('visibility:restricted_cultural', 'Restricted cultural'),
        ];

        if (!$this->can_manage_restricted()) {
            unset(
                $options[self::VISIBILITY_RESTRICTED],
                $options[self::VISIBILITY_RESTRICTED_INTEGRITY],
                $options[self::VISIBILITY_RESTRICTED_CULTURAL]
            );
        }

        return $options;
    }

    /**
     * Return audience suitability options.
     *
     * @return array<string, string>
     */
    private function get_audience_options(): array {
        $options = [
            self::SUITABILITY_GENERAL => $this->str('audience:general', 'General'),
            self::SUITABILITY_GUIDED => $this->str('audience:guided', 'Guided'),
            self::SUITABILITY_MATURE => $this->str('audience:mature', 'Mature'),
            self::SUITABILITY_RESTRICTED => $this->str('audience:restricted', 'Restricted'),
            self::SUITABILITY_RESTRICTED_CULTURAL => $this->str('audience:restricted_cultural', 'Restricted cultural'),
            self::SUITABILITY_RESTRICTED_INTEGRITY => $this->str('audience:restricted_integrity', 'Restricted integrity'),
            self::SUITABILITY_STAFF_ONLY => $this->str('audience:staff_only', 'Staff only'),
        ];

        if (!$this->can_manage_restricted()) {
            unset(
                $options[self::SUITABILITY_RESTRICTED],
                $options[self::SUITABILITY_RESTRICTED_CULTURAL],
                $options[self::SUITABILITY_RESTRICTED_INTEGRITY],
                $options[self::SUITABILITY_STAFF_ONLY]
            );
        }

        return $options;
    }

    /**
     * Return whether current user can set restricted collection metadata.
     *
     * @return bool
     */
    private function can_manage_restricted(): bool {
        $context = $this->get_context();

        if (!$context) {
            return false;
        }

        foreach ([
            'mod/uckkarchive:manageadvisories',
            'mod/uckkarchive:managecontentadvisories',
            'mod/uckkarchive:viewrestrictedmedia',
            'mod/uckkarchive:viewrestricted',
        ] as $capability) {
            if (function_exists('get_capability_info') && !get_capability_info($capability)) {
                continue;
            }

            if (has_capability($capability, $context)) {
                return true;
            }
        }

        return false;
    }

    /**
     * Get module context from custom data.
     *
     * @return context_module|null
     */
    private function get_context(): ?context_module {
        $context = $this->_customdata['context'] ?? null;

        if ($context instanceof context_module) {
            return $context;
        }

        return null;
    }

    /**
     * Get integer custom data.
     *
     * @param string $key Custom data key.
     * @return int
     */
    private function get_custom_int(string $key): int {
        return (int)($this->_customdata[$key] ?? 0);
    }

    /**
     * Validate JSON object.
     *
     * @param string $value Raw value.
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
     * Validate positive id list.
     *
     * @param string $value Raw value.
     * @return bool
     */
    private function is_valid_id_list(string $value): bool {
        $value = trim($value);

        if ($value === '') {
            return true;
        }

        $parts = preg_split('/[\s,;]+/', $value, -1, PREG_SPLIT_NO_EMPTY);

        if ($parts === false) {
            return false;
        }

        foreach ($parts as $part) {
            if (!preg_match('/^[1-9][0-9]*$/', $part)) {
                return false;
            }
        }

        return true;
    }

    /**
     * Validate simple tag list.
     *
     * @param string $value Raw value.
     * @return bool
     */
    private function is_valid_tag_list(string $value): bool {
        $value = trim($value);

        if ($value === '') {
            return true;
        }

        return strpos($value, '<') === false && strpos($value, '>') === false;
    }

    /**
     * Safe string helper with fallback for files generated before lang strings exist.
     *
     * @param string $identifier String identifier.
     * @param string $fallback Fallback text.
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
