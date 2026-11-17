<?php
// This file is part of Moodle - https://moodle.org/
//
// Moodle is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// any later version.

/**
 * Media version form for UCKK Archive.
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

use mod_uckkarchive\local\media_file;
use mod_uckkarchive\local\media_version;
use stdClass;

/**
 * Form used to create or edit a media version.
 *
 * Media versions represent controlled changes to a media record:
 *
 * - original replacement;
 * - preview replacement;
 * - derivative generation;
 * - caption upload;
 * - transcript upload;
 * - attachment upload;
 * - metadata-only correction;
 * - accessibility correction;
 * - rights/provenance correction.
 *
 * This form does not decide authority. Capability checks belong to the page,
 * external service, or policy layer before the form is shown or processed.
 */
final class media_version_form extends \moodleform {
    /** Draft file area field. */
    public const FIELD_FILES = 'files';

    /** Metadata field. */
    public const FIELD_METADATA = 'metadata';

    /** Default max bytes fallback. */
    private const DEFAULT_MAXBYTES = 0;

    /**
     * Define form.
     *
     * @return void
     */
    protected function definition(): void {
        $mform = $this->_form;
        $data = $this->get_custom_data();

        $cmid = (int)($data['cmid'] ?? 0);
        $mediaid = (int)($data['mediaid'] ?? 0);
        $versionid = (int)($data['versionid'] ?? 0);
        $draftitemid = (int)($data['draftitemid'] ?? 0);
        $currentfilearea = (string)($data['filearea'] ?? media_file::AREA_ORIGINAL);

        $mform->addElement('hidden', 'cmid', $cmid);
        $mform->setType('cmid', PARAM_INT);

        $mform->addElement('hidden', 'mediaid', $mediaid);
        $mform->setType('mediaid', PARAM_INT);

        $mform->addElement('hidden', 'versionid', $versionid);
        $mform->setType('versionid', PARAM_INT);

        $mform->addElement('hidden', 'draftitemid', $draftitemid);
        $mform->setType('draftitemid', PARAM_INT);

        $mform->addElement('header', 'versiondetails', self::string('mediaversiondetails', 'Version details'));

        $mform->addElement(
            'select',
            'versiontype',
            self::string('mediaversiontype', 'Version type'),
            self::version_type_options()
        );
        $mform->setType('versiontype', PARAM_ALPHANUMEXT);
        $mform->setDefault('versiontype', (string)($data['versiontype'] ?? 'replacement'));
        $mform->addRule('versiontype', null, 'required', null, 'client');

        $mform->addElement(
            'select',
            'filearea',
            self::string('filearea', 'File area'),
            self::filearea_options()
        );
        $mform->setType('filearea', PARAM_ALPHANUMEXT);
        $mform->setDefault('filearea', $currentfilearea);
        $mform->addRule('filearea', null, 'required', null, 'client');

        $mform->addElement(
            'select',
            'status',
            self::string('status', 'Status'),
            self::status_options()
        );
        $mform->setType('status', PARAM_ALPHANUMEXT);
        $mform->setDefault('status', (string)($data['status'] ?? 'draft'));
        $mform->addRule('status', null, 'required', null, 'client');

        $mform->addElement(
            'text',
            'label',
            self::string('mediaversionlabel', 'Version label'),
            ['size' => 64, 'maxlength' => 255]
        );
        $mform->setType('label', PARAM_TEXT);
        $mform->setDefault('label', (string)($data['label'] ?? ''));

        $mform->addElement(
            'textarea',
            'summary',
            self::string('summary', 'Summary'),
            ['rows' => 4, 'cols' => 80]
        );
        $mform->setType('summary', PARAM_TEXT);
        $mform->setDefault('summary', (string)($data['summary'] ?? ''));

        $mform->addElement(
            'textarea',
            'reason',
            self::string('reason', 'Reason'),
            ['rows' => 4, 'cols' => 80]
        );
        $mform->setType('reason', PARAM_TEXT);
        $mform->setDefault('reason', (string)($data['reason'] ?? ''));

        $mform->addElement(
            'advcheckbox',
            'makecurrent',
            self::string('makemediaversioncurrent', 'Make this the current version'),
            self::string('makemediaversioncurrent_helptext', 'Use this version as the active media version.')
        );
        $mform->setType('makecurrent', PARAM_BOOL);
        $mform->setDefault('makecurrent', !empty($data['makecurrent']) ? 1 : 0);

        $mform->addElement('header', 'versionfile', self::string('mediaversionfile', 'Version file'));

        $mform->addElement(
            'filemanager',
            self::FIELD_FILES,
            self::string('files', 'Files'),
            null,
            self::filemanager_options($data)
        );
        $mform->addHelpButton(self::FIELD_FILES, 'files', 'moodle');
        $mform->setDefault(self::FIELD_FILES, $draftitemid);

        $mform->addElement(
            'static',
            'fileguidance',
            '',
            self::string(
                'mediaversionfileguidance',
                'Upload the replacement or support file for this version. Metadata-only versions may leave this empty.'
            )
        );

        $mform->addElement('header', 'versionmetadata', self::string('metadata', 'Metadata'));

        $mform->addElement(
            'textarea',
            self::FIELD_METADATA,
            self::string('metadatajson', 'Metadata JSON'),
            ['rows' => 8, 'cols' => 80]
        );
        $mform->setType(self::FIELD_METADATA, PARAM_RAW);
        $mform->setDefault(self::FIELD_METADATA, self::default_metadata($data));

        $mform->addElement(
            'textarea',
            'auditnote',
            self::string('auditnote', 'Audit note'),
            ['rows' => 3, 'cols' => 80]
        );
        $mform->setType('auditnote', PARAM_TEXT);
        $mform->setDefault('auditnote', (string)($data['auditnote'] ?? ''));

        $this->add_action_buttons(true, $versionid > 0
            ? self::string('savechanges', 'Save changes')
            : self::string('addmediaversion', 'Add media version')
        );
    }

    /**
     * Validate form.
     *
     * @param array $data Submitted data.
     * @param array $files Submitted files.
     * @return array
     */
    public function validation($data, $files): array {
        $errors = parent::validation($data, $files);

        $mediaid = (int)($data['mediaid'] ?? 0);
        if ($mediaid <= 0) {
            $errors['mediaid'] = self::string('required');
        }

        $filearea = (string)($data['filearea'] ?? '');
        if (!array_key_exists($filearea, self::filearea_options())) {
            $errors['filearea'] = self::string('invalidfilearea', 'Invalid file area.');
        }

        $versiontype = (string)($data['versiontype'] ?? '');
        if (!array_key_exists($versiontype, self::version_type_options())) {
            $errors['versiontype'] = self::string('invalidversiontype', 'Invalid version type.');
        }

        $status = (string)($data['status'] ?? '');
        if (!array_key_exists($status, self::status_options())) {
            $errors['status'] = self::string('invalidstatus', 'Invalid status.');
        }

        $metadata = trim((string)($data[self::FIELD_METADATA] ?? ''));
        if ($metadata !== '') {
            $decoded = json_decode($metadata, true);
            if (!is_array($decoded)) {
                $errors[self::FIELD_METADATA] = self::string('invalidjson', 'Invalid JSON.');
            }
        }

        if ($versiontype !== 'metadata_correction') {
            $reason = trim((string)($data['reason'] ?? ''));
            if ($reason === '') {
                $errors['reason'] = self::string('required');
            }
        }

        return $errors;
    }

    /**
     * Return submitted data normalised for the domain layer.
     *
     * @return stdClass|null
     */
    public function get_data(): ?stdClass {
        $data = parent::get_data();

        if (!$data) {
            return null;
        }

        $data->cmid = (int)($data->cmid ?? 0);
        $data->mediaid = (int)($data->mediaid ?? 0);
        $data->versionid = (int)($data->versionid ?? 0);
        $data->draftitemid = (int)($data->draftitemid ?? 0);
        $data->makecurrent = !empty($data->makecurrent) ? 1 : 0;

        $data->versiontype = clean_param((string)($data->versiontype ?? ''), PARAM_ALPHANUMEXT);
        $data->filearea = clean_param((string)($data->filearea ?? ''), PARAM_ALPHANUMEXT);
        $data->status = clean_param((string)($data->status ?? ''), PARAM_ALPHANUMEXT);
        $data->label = clean_param((string)($data->label ?? ''), PARAM_TEXT);
        $data->summary = clean_param((string)($data->summary ?? ''), PARAM_TEXT);
        $data->reason = clean_param((string)($data->reason ?? ''), PARAM_TEXT);
        $data->auditnote = clean_param((string)($data->auditnote ?? ''), PARAM_TEXT);

        $metadata = trim((string)($data->{self::FIELD_METADATA} ?? ''));
        $data->metadata = $metadata === '' ? [] : json_decode($metadata, true);

        if (!is_array($data->metadata)) {
            $data->metadata = [];
        }

        return $data;
    }

    /**
     * Return custom data.
     *
     * @return array<string, mixed>
     */
    private function get_custom_data(): array {
        return is_array($this->_customdata) ? $this->_customdata : [];
    }

    /**
     * Return version type options.
     *
     * @return array<string, string>
     */
    private static function version_type_options(): array {
        return [
            'replacement' => self::string('mediaversiontype_replacement', 'Replacement'),
            'correction' => self::string('mediaversiontype_correction', 'Correction'),
            'derivative' => self::string('mediaversiontype_derivative', 'Derivative'),
            'preview' => self::string('mediaversiontype_preview', 'Preview'),
            'thumbnail' => self::string('mediaversiontype_thumbnail', 'Thumbnail'),
            'caption' => self::string('mediaversiontype_caption', 'Caption'),
            'transcript' => self::string('mediaversiontype_transcript', 'Transcript'),
            'attachment' => self::string('mediaversiontype_attachment', 'Attachment'),
            'accessibility_correction' => self::string(
                'mediaversiontype_accessibility_correction',
                'Accessibility correction'
            ),
            'rights_correction' => self::string('mediaversiontype_rights_correction', 'Rights correction'),
            'metadata_correction' => self::string('mediaversiontype_metadata_correction', 'Metadata correction'),
        ];
    }

    /**
     * Return media version status options.
     *
     * @return array<string, string>
     */
    private static function status_options(): array {
        $statuses = [];

        if (class_exists(media_version::class) && method_exists(media_version::class, 'statuses')) {
            foreach (media_version::statuses() as $status) {
                $statuses[$status] = self::string('mediaversionstatus_' . $status, ucfirst(str_replace('_', ' ', $status)));
            }

            return $statuses;
        }

        foreach ([
            'draft',
            'active',
            'superseded',
            'archived',
            'restricted',
            'deleted_soft',
        ] as $status) {
            $statuses[$status] = self::string('mediaversionstatus_' . $status, ucfirst(str_replace('_', ' ', $status)));
        }

        return $statuses;
    }

    /**
     * Return file area options.
     *
     * @return array<string, string>
     */
    private static function filearea_options(): array {
        if (class_exists(media_file::class) && method_exists(media_file::class, 'get_media_filearea_labels')) {
            return media_file::get_media_filearea_labels();
        }

        return [
            'media_original' => self::string('filearea_media_original', 'Original'),
            'media_preview' => self::string('filearea_media_preview', 'Preview'),
            'media_thumbnail' => self::string('filearea_media_thumbnail', 'Thumbnail'),
            'media_derivative' => self::string('filearea_media_derivative', 'Derivative'),
            'media_caption' => self::string('filearea_media_caption', 'Caption'),
            'media_transcript' => self::string('filearea_media_transcript', 'Transcript'),
            'media_attachment' => self::string('filearea_media_attachment', 'Attachment'),
        ];
    }

    /**
     * Return filemanager options.
     *
     * @param array<string, mixed> $data Custom data.
     * @return array<string, mixed>
     */
    private static function filemanager_options(array $data): array {
        $course = $data['course'] ?? null;

        $maxbytes = self::DEFAULT_MAXBYTES;
        if ($course && isset($course->maxbytes)) {
            $maxbytes = (int)$course->maxbytes;
        } else if (isset($data['maxbytes'])) {
            $maxbytes = (int)$data['maxbytes'];
        }

        return [
            'subdirs' => 0,
            'maxbytes' => $maxbytes,
            'maxfiles' => 1,
            'accepted_types' => '*',
            'return_types' => \FILE_INTERNAL,
        ];
    }

    /**
     * Return default metadata JSON.
     *
     * @param array<string, mixed> $data Custom data.
     * @return string
     */
    private static function default_metadata(array $data): string {
        $metadata = $data['metadata'] ?? [];

        if (is_string($metadata)) {
            $decoded = json_decode($metadata, true);
            $metadata = is_array($decoded) ? $decoded : [];
        }

        if ($metadata instanceof stdClass) {
            $metadata = (array)$metadata;
        }

        if (!is_array($metadata)) {
            $metadata = [];
        }

        if (empty($metadata)) {
            return '';
        }

        $json = json_encode($metadata, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);

        return $json === false ? '' : $json;
    }

    /**
     * Return plugin string with fallback.
     *
     * @param string $identifier String identifier.
     * @param string|null $fallback Fallback text.
     * @return string
     */
    private static function string(string $identifier, ?string $fallback = null): string {
        $manager = get_string_manager();

        if ($manager->string_exists($identifier, 'uckkarchive')) {
            return get_string($identifier, 'uckkarchive');
        }

        if ($manager->string_exists($identifier, 'moodle')) {
            return get_string($identifier);
        }

        return $fallback ?? $identifier;
    }
}
