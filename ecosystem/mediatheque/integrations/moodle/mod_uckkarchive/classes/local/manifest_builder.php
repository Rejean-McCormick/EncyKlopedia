<?php
// This file is part of Moodle - https://moodle.org/
//
// Moodle is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// any later version.

/**
 * Export manifest builder for the UCKK Archive activity module.
 *
 * @package    mod_uckkarchive
 * @copyright  2026 Univers-Cité King Klown
 * @license    https://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later
 */

namespace mod_uckkarchive\local;

use context;
use core\uuid;
use JsonException;
use moodle_exception;
use stdClass;
use stored_file;

defined('MOODLE_INTERNAL') || die();

/**
 * Builds portable, redaction-aware export manifests.
 *
 * This class does not decide whether a record may be exported. Export policy is
 * owned by archive_policy, media_policy, and content_policy. The builder only
 * receives already-authorised records and produces a stable manifest structure.
 *
 * The manifest is intended to describe archive, media, content advisory,
 * external work, file, relation, provenance, revision, and validation state
 * enough for audit, restore, duplication, and cross-site portability.
 */
class manifest_builder {
    /** @var string Manifest filename used inside export packages. */
    public const MANIFEST_FILENAME = 'manifest.json';

    /** @var string Current manifest schema version. */
    public const SCHEMA_VERSION = '1.0';

    /** @var string Default component name. */
    public const COMPONENT = 'mod_uckkarchive';

    /** @var string Entry content is included. */
    public const FIELD_INCLUDED = 'included';

    /** @var string Entry content is summarized. */
    public const FIELD_SUMMARIZED = 'summarized';

    /** @var string Entry content is redacted. */
    public const FIELD_REDACTED = 'redacted';

    /** @var string Entry content is omitted. */
    public const FIELD_OMITTED = 'omitted';

    /** @var string Entry is a reference only. */
    public const FIELD_REFERENCE_ONLY = 'reference_only';

    /** @var string Archive item entry type. */
    public const ENTRY_ARCHIVE_ITEM = 'archive_item';

    /** @var string Media entry type. */
    public const ENTRY_MEDIA = 'media';

    /** @var string Media version entry type. */
    public const ENTRY_MEDIA_VERSION = 'media_version';

    /** @var string Media collection entry type. */
    public const ENTRY_MEDIA_COLLECTION = 'media_collection';

    /** @var string Media relation entry type. */
    public const ENTRY_MEDIA_RELATION = 'media_relation';

    /** @var string Content marker entry type. */
    public const ENTRY_CONTENT_MARKER = 'content_marker';

    /** @var string Content tag entry type. */
    public const ENTRY_CONTENT_TAG = 'content_tag';

    /** @var string Content tag set entry type. */
    public const ENTRY_CONTENT_TAG_SET = 'content_tag_set';

    /** @var string Content review entry type. */
    public const ENTRY_CONTENT_REVIEW = 'content_review';

    /** @var string External work entry type. */
    public const ENTRY_EXTERNAL_WORK = 'external_work';

    /** @var string Provenance entry type. */
    public const ENTRY_PROVENANCE = 'provenance';

    /** @var string Revision entry type. */
    public const ENTRY_REVISION = 'revision';

    /** @var string File entry type. */
    public const ENTRY_FILE = 'file';

    /** @var string Export package entry type. */
    public const ENTRY_EXPORT = 'export';

    /** @var string Moodle component name. */
    protected string $component;

    /** @var string|null Plugin version string. */
    protected ?string $pluginversion;

    /**
     * Constructor.
     *
     * @param string $component Moodle component.
     * @param string|null $pluginversion Optional plugin version.
     */
    public function __construct(string $component = self::COMPONENT, ?string $pluginversion = null) {
        $this->component = $component;
        $this->pluginversion = $pluginversion;
    }

    /**
     * Return the canonical manifest filename.
     *
     * @return string
     */
    public static function filename(): string {
        return self::MANIFEST_FILENAME;
    }

    /**
     * Create a new manifest array.
     *
     * @param stdClass $archive Archive activity record.
     * @param stdClass|null $export Export record, if already created.
     * @param context $context Moodle context.
     * @param int $actorid User creating the export.
     * @param string $exporttype Export type.
     * @param string $reason Export reason.
     * @param array $options Additional options.
     * @return array
     */
    public function create(
        stdClass $archive,
        ?stdClass $export,
        context $context,
        int $actorid,
        string $exporttype = 'archive_media_export',
        string $reason = '',
        array $options = []
    ): array {
        $now = time();

        return [
            'schema' => [
                'name' => self::MANIFEST_FILENAME,
                'version' => self::SCHEMA_VERSION,
                'component' => $this->component,
                'pluginversion' => $this->pluginversion,
                'generatedat' => $now,
            ],
            'package' => [
                'exportid' => $this->property_int($export, 'id'),
                'exportuuid' => $this->property_string($export, 'uuid', $this->generate_uuid()),
                'exporttype' => $exporttype,
                'exporttimestamp' => $now,
                'exportactor' => $actorid,
                'exportreason' => $reason,
                'redactionlevel' => $this->option_string($options, 'redactionlevel', 'none'),
                'visibility' => $this->option_string($options, 'visibility', ''),
                'restrictionstate' => $this->option_string($options, 'restrictionstate', ''),
            ],
            'context' => [
                'contextid' => $context->id,
                'contextlevel' => $context->contextlevel,
                'instanceid' => $context->instanceid,
                'courseid' => $this->property_int($archive, 'course'),
                'coursemoduleid' => $this->option_int($options, 'cmid', 0),
                'archiveid' => $this->property_int($archive, 'id'),
                'archiveuuid' => $this->property_string($archive, 'uuid'),
                'archivename' => $this->property_string($archive, 'name'),
            ],
            'entries' => [
                self::ENTRY_ARCHIVE_ITEM => [],
                self::ENTRY_MEDIA => [],
                self::ENTRY_MEDIA_VERSION => [],
                self::ENTRY_MEDIA_COLLECTION => [],
                self::ENTRY_MEDIA_RELATION => [],
                self::ENTRY_CONTENT_MARKER => [],
                self::ENTRY_CONTENT_TAG => [],
                self::ENTRY_CONTENT_TAG_SET => [],
                self::ENTRY_CONTENT_REVIEW => [],
                self::ENTRY_EXTERNAL_WORK => [],
                self::ENTRY_PROVENANCE => [],
                self::ENTRY_REVISION => [],
                self::ENTRY_FILE => [],
                self::ENTRY_EXPORT => [],
            ],
            'counts' => [],
            'redactions' => [],
            'warnings' => [],
            'metadata' => $this->normalise_metadata($options['metadata'] ?? []),
        ];
    }

    /**
     * Add an archive item entry.
     *
     * @param array $manifest Manifest array.
     * @param stdClass $item Archive item record.
     * @param array $options Entry options.
     */
    public function add_archive_item(array &$manifest, stdClass $item, array $options = []): void {
        $this->add_entry($manifest, self::ENTRY_ARCHIVE_ITEM, [
            'id' => $this->property_int($item, 'id'),
            'uuid' => $this->property_string($item, 'uuid'),
            'type' => $this->property_string($item, 'itemtype', $this->property_string($item, 'type')),
            'title' => $this->field_value($item, 'title', $options),
            'status' => $this->property_string($item, 'status'),
            'visibility' => $this->property_string($item, 'visibility'),
            'validationstate' => $this->property_string($item, 'validationstate'),
            'provenance' => $this->property_string($item, 'provenance'),
            'timecreated' => $this->property_int($item, 'timecreated'),
            'timemodified' => $this->property_int($item, 'timemodified'),
            'createdby' => $this->property_int($item, 'createdby'),
            'modifiedby' => $this->property_int($item, 'modifiedby'),
            'metadata' => $this->field_value($item, 'metadata', $options, true),
        ]);
    }

    /**
     * Add a media object entry.
     *
     * @param array $manifest Manifest array.
     * @param stdClass $media Media record.
     * @param array $options Entry options.
     */
    public function add_media(array &$manifest, stdClass $media, array $options = []): void {
        $this->add_entry($manifest, self::ENTRY_MEDIA, [
            'id' => $this->property_int($media, 'id'),
            'uuid' => $this->property_string($media, 'uuid'),
            'title' => $this->field_value($media, 'title', $options),
            'description' => $this->field_value($media, 'description', $options),
            'mediatype' => $this->property_string($media, 'mediatype'),
            'mimetype' => $this->property_string($media, 'mimetype'),
            'status' => $this->property_string($media, 'status'),
            'visibility' => $this->property_string($media, 'visibility'),
            'audiencesuitability' => $this->property_string($media, 'audiencesuitability'),
            'sourceid' => $this->property_int($media, 'sourceid'),
            'currentversionid' => $this->property_int($media, 'currentversionid'),
            'timecreated' => $this->property_int($media, 'timecreated'),
            'timemodified' => $this->property_int($media, 'timemodified'),
            'createdby' => $this->property_int($media, 'createdby'),
            'modifiedby' => $this->property_int($media, 'modifiedby'),
            'metadata' => $this->field_value($media, 'metadata', $options, true),
        ]);
    }

    /**
     * Add a media version entry.
     *
     * @param array $manifest Manifest array.
     * @param stdClass $version Media version record.
     * @param array $options Entry options.
     */
    public function add_media_version(array &$manifest, stdClass $version, array $options = []): void {
        $this->add_entry($manifest, self::ENTRY_MEDIA_VERSION, [
            'id' => $this->property_int($version, 'id'),
            'uuid' => $this->property_string($version, 'uuid'),
            'mediaid' => $this->property_int($version, 'mediaid'),
            'mediauuid' => $this->property_string($version, 'mediauuid'),
            'versionno' => $this->property_int($version, 'versionno'),
            'status' => $this->property_string($version, 'status'),
            'filename' => $this->field_value($version, 'filename', $options),
            'mimetype' => $this->property_string($version, 'mimetype'),
            'filesize' => $this->property_int($version, 'filesize'),
            'filehash' => $this->property_string($version, 'filehash'),
            'timecreated' => $this->property_int($version, 'timecreated'),
            'createdby' => $this->property_int($version, 'createdby'),
            'metadata' => $this->field_value($version, 'metadata', $options, true),
        ]);
    }

    /**
     * Add a media collection entry.
     *
     * @param array $manifest Manifest array.
     * @param stdClass $collection Collection record.
     * @param array $options Entry options.
     */
    public function add_collection(array &$manifest, stdClass $collection, array $options = []): void {
        $this->add_entry($manifest, self::ENTRY_MEDIA_COLLECTION, [
            'id' => $this->property_int($collection, 'id'),
            'uuid' => $this->property_string($collection, 'uuid'),
            'title' => $this->field_value($collection, 'title', $options),
            'description' => $this->field_value($collection, 'description', $options),
            'visibility' => $this->property_string($collection, 'visibility'),
            'audiencesuitability' => $this->property_string($collection, 'audiencesuitability'),
            'timecreated' => $this->property_int($collection, 'timecreated'),
            'timemodified' => $this->property_int($collection, 'timemodified'),
            'metadata' => $this->field_value($collection, 'metadata', $options, true),
        ]);
    }

    /**
     * Add a relation entry.
     *
     * @param array $manifest Manifest array.
     * @param stdClass $relation Relation record.
     * @param array $options Entry options.
     */
    public function add_relation(array &$manifest, stdClass $relation, array $options = []): void {
        $this->add_entry($manifest, self::ENTRY_MEDIA_RELATION, [
            'id' => $this->property_int($relation, 'id'),
            'uuid' => $this->property_string($relation, 'uuid'),
            'relationtype' => $this->property_string($relation, 'relationtype'),
            'sourceobjecttype' => $this->property_string($relation, 'sourceobjecttype'),
            'sourceid' => $this->property_int($relation, 'sourceid'),
            'sourceuuid' => $this->property_string($relation, 'sourceuuid'),
            'targetobjecttype' => $this->property_string($relation, 'targetobjecttype'),
            'targetid' => $this->property_int($relation, 'targetid'),
            'targetuuid' => $this->property_string($relation, 'targetuuid'),
            'metadata' => $this->field_value($relation, 'metadata', $options, true),
        ]);
    }

    /**
     * Add a content marker entry.
     *
     * @param array $manifest Manifest array.
     * @param stdClass $marker Marker record.
     * @param array $options Entry options.
     */
    public function add_content_marker(array &$manifest, stdClass $marker, array $options = []): void {
        $this->add_entry($manifest, self::ENTRY_CONTENT_MARKER, [
            'id' => $this->property_int($marker, 'id'),
            'uuid' => $this->property_string($marker, 'uuid'),
            'tagkey' => $this->property_string($marker, 'tagkey'),
            'targettype' => $this->property_string($marker, 'targettype'),
            'targetid' => $this->property_int($marker, 'targetid'),
            'targetuuid' => $this->property_string($marker, 'targetuuid'),
            'locatortype' => $this->property_string($marker, 'locatortype'),
            'locatorstart' => $this->field_value($marker, 'locatorstart', $options),
            'locatorend' => $this->field_value($marker, 'locatorend', $options),
            'severity' => $this->property_string($marker, 'severity'),
            'audiencesuitability' => $this->property_string($marker, 'audiencesuitability'),
            'reviewstate' => $this->property_string($marker, 'reviewstate'),
            'visibility' => $this->property_string($marker, 'visibility'),
            'note' => $this->field_value($marker, 'note', $options),
            'metadata' => $this->field_value($marker, 'metadata', $options, true),
        ]);
    }

    /**
     * Add a content tag entry.
     *
     * @param array $manifest Manifest array.
     * @param stdClass $tag Tag record.
     * @param array $options Entry options.
     */
    public function add_content_tag(array &$manifest, stdClass $tag, array $options = []): void {
        $this->add_entry($manifest, self::ENTRY_CONTENT_TAG, [
            'id' => $this->property_int($tag, 'id'),
            'key' => $this->property_string($tag, 'tagkey', $this->property_string($tag, 'key')),
            'label' => $this->field_value($tag, 'label', $options),
            'description' => $this->field_value($tag, 'description', $options),
            'category' => $this->property_string($tag, 'category'),
            'severity' => $this->property_string($tag, 'severity'),
            'culturalprotocol' => $this->property_bool($tag, 'culturalprotocol'),
        ]);
    }

    /**
     * Add a content tag set entry.
     *
     * @param array $manifest Manifest array.
     * @param stdClass $tagset Tag set record.
     * @param array $options Entry options.
     */
    public function add_content_tag_set(array &$manifest, stdClass $tagset, array $options = []): void {
        $this->add_entry($manifest, self::ENTRY_CONTENT_TAG_SET, [
            'id' => $this->property_int($tagset, 'id'),
            'key' => $this->property_string($tagset, 'setkey', $this->property_string($tagset, 'key')),
            'label' => $this->field_value($tagset, 'label', $options),
            'description' => $this->field_value($tagset, 'description', $options),
            'visibility' => $this->property_string($tagset, 'visibility'),
            'metadata' => $this->field_value($tagset, 'metadata', $options, true),
        ]);
    }

    /**
     * Add a content review entry.
     *
     * @param array $manifest Manifest array.
     * @param stdClass $review Review record.
     * @param array $options Entry options.
     */
    public function add_content_review(array &$manifest, stdClass $review, array $options = []): void {
        $this->add_entry($manifest, self::ENTRY_CONTENT_REVIEW, [
            'id' => $this->property_int($review, 'id'),
            'uuid' => $this->property_string($review, 'uuid'),
            'markerid' => $this->property_int($review, 'markerid'),
            'markeruuid' => $this->property_string($review, 'markeruuid'),
            'reviewstate' => $this->property_string($review, 'reviewstate'),
            'reviewedby' => $this->property_int($review, 'reviewedby'),
            'timereviewed' => $this->property_int($review, 'timereviewed'),
            'rationale' => $this->field_value($review, 'rationale', $options),
            'metadata' => $this->field_value($review, 'metadata', $options, true),
        ]);
    }

    /**
     * Add an external work entry.
     *
     * @param array $manifest Manifest array.
     * @param stdClass $work External work record.
     * @param array $options Entry options.
     */
    public function add_external_work(array &$manifest, stdClass $work, array $options = []): void {
        $this->add_entry($manifest, self::ENTRY_EXTERNAL_WORK, [
            'id' => $this->property_int($work, 'id'),
            'uuid' => $this->property_string($work, 'uuid'),
            'worktype' => $this->property_string($work, 'worktype'),
            'title' => $this->field_value($work, 'title', $options),
            'creator' => $this->field_value($work, 'creator', $options),
            'year' => $this->property_string($work, 'year'),
            'sourceurl' => $this->field_value($work, 'sourceurl', $options),
            'identifier' => $this->field_value($work, 'identifier', $options),
            'rightsnote' => $this->field_value($work, 'rightsnote', $options),
            'citation' => $this->field_value($work, 'citation', $options),
            'visibility' => $this->property_string($work, 'visibility'),
            'audiencesuitability' => $this->property_string($work, 'audiencesuitability'),
            'metadata' => $this->field_value($work, 'metadata', $options, true),
        ]);
    }

    /**
     * Add a provenance entry.
     *
     * @param array $manifest Manifest array.
     * @param stdClass $provenance Provenance record.
     * @param array $options Entry options.
     */
    public function add_provenance(array &$manifest, stdClass $provenance, array $options = []): void {
        $this->add_entry($manifest, self::ENTRY_PROVENANCE, [
            'id' => $this->property_int($provenance, 'id'),
            'uuid' => $this->property_string($provenance, 'uuid'),
            'sourcecomponent' => $this->property_string($provenance, 'sourcecomponent'),
            'sourcearea' => $this->property_string($provenance, 'sourcearea'),
            'sourceid' => $this->property_string($provenance, 'sourceid'),
            'sourceuuid' => $this->property_string($provenance, 'sourceuuid'),
            'provenance' => $this->property_string($provenance, 'provenance'),
            'hash' => $this->property_string($provenance, 'hash'),
            'metadata' => $this->field_value($provenance, 'metadata', $options, true),
        ]);
    }

    /**
     * Add a revision entry.
     *
     * @param array $manifest Manifest array.
     * @param stdClass $revision Revision record.
     * @param array $options Entry options.
     */
    public function add_revision(array &$manifest, stdClass $revision, array $options = []): void {
        $this->add_entry($manifest, self::ENTRY_REVISION, [
            'id' => $this->property_int($revision, 'id'),
            'uuid' => $this->property_string($revision, 'uuid'),
            'objecttype' => $this->property_string($revision, 'objecttype'),
            'objectid' => $this->property_int($revision, 'objectid'),
            'objectuuid' => $this->property_string($revision, 'objectuuid'),
            'revisionno' => $this->property_int($revision, 'revisionno'),
            'reason' => $this->field_value($revision, 'reason', $options),
            'createdby' => $this->property_int($revision, 'createdby'),
            'timecreated' => $this->property_int($revision, 'timecreated'),
            'metadata' => $this->field_value($revision, 'metadata', $options, true),
        ]);
    }

    /**
     * Add a stored_file entry.
     *
     * @param array $manifest Manifest array.
     * @param stored_file $file Moodle stored file.
     * @param string $sourceuuid UUID of the source object.
     * @param string $sourceversionuuid UUID of the source version, if any.
     * @param array $options Entry options.
     */
    public function add_file(
        array &$manifest,
        stored_file $file,
        string $sourceuuid = '',
        string $sourceversionuuid = '',
        array $options = []
    ): void {
        $this->add_entry($manifest, self::ENTRY_FILE, [
            'component' => $file->get_component(),
            'filearea' => $file->get_filearea(),
            'itemid' => $file->get_itemid(),
            'filepath' => $file->get_filepath(),
            'filename' => $this->option_bool($options, 'redactfilename', false) ? self::FIELD_REDACTED : $file->get_filename(),
            'contenthash' => $file->get_contenthash(),
            'sha256' => $this->option_string($options, 'sha256', ''),
            'mimetype' => $file->get_mimetype(),
            'filesize' => $file->get_filesize(),
            'timecreated' => $file->get_timecreated(),
            'timemodified' => $file->get_timemodified(),
            'sourceuuid' => $sourceuuid,
            'sourceversionuuid' => $sourceversionuuid,
            'redactionstate' => $this->option_string($options, 'redactionstate', self::FIELD_INCLUDED),
            'restrictionstate' => $this->option_string($options, 'restrictionstate', ''),
        ]);
    }

    /**
     * Add an export record entry.
     *
     * @param array $manifest Manifest array.
     * @param stdClass $export Export record.
     * @param array $options Entry options.
     */
    public function add_export(array &$manifest, stdClass $export, array $options = []): void {
        $this->add_entry($manifest, self::ENTRY_EXPORT, [
            'id' => $this->property_int($export, 'id'),
            'uuid' => $this->property_string($export, 'uuid'),
            'exporttype' => $this->property_string($export, 'exporttype'),
            'status' => $this->property_string($export, 'status'),
            'visibility' => $this->property_string($export, 'visibility'),
            'redactionlevel' => $this->property_string($export, 'redactionlevel'),
            'createdby' => $this->property_int($export, 'createdby', $this->property_int($export, 'userid')),
            'timecreated' => $this->property_int($export, 'timecreated'),
            'metadata' => $this->field_value($export, 'metadata', $options, true),
        ]);
    }

    /**
     * Add a warning to the manifest.
     *
     * @param array $manifest Manifest array.
     * @param string $code Warning code.
     * @param string $message Warning message.
     * @param array $details Optional details.
     */
    public function add_warning(array &$manifest, string $code, string $message, array $details = []): void {
        $manifest['warnings'][] = [
            'code' => $code,
            'message' => $message,
            'details' => $details,
        ];
    }

    /**
     * Add a redaction marker to the manifest.
     *
     * @param array $manifest Manifest array.
     * @param string $objecttype Object type.
     * @param string $objectuuid Object UUID.
     * @param string $field Field name.
     * @param string $reason Redaction reason.
     * @param string $mode Redaction mode.
     */
    public function add_redaction(
        array &$manifest,
        string $objecttype,
        string $objectuuid,
        string $field,
        string $reason,
        string $mode = self::FIELD_REDACTED
    ): void {
        $manifest['redactions'][] = [
            'objecttype' => $objecttype,
            'objectuuid' => $objectuuid,
            'field' => $field,
            'reason' => $reason,
            'mode' => $mode,
        ];
    }

    /**
     * Finalise a manifest by adding counts and ordering entries.
     *
     * @param array $manifest Manifest array.
     * @return array Final manifest.
     */
    public function finalise(array $manifest): array {
        foreach ($manifest['entries'] as $type => $entries) {
            $manifest['counts'][$type] = count($entries);
        }

        $manifest['counts']['warnings'] = count($manifest['warnings']);
        $manifest['counts']['redactions'] = count($manifest['redactions']);
        $manifest['schema']['finalisedat'] = time();

        return $manifest;
    }

    /**
     * Encode a manifest as pretty JSON.
     *
     * @param array $manifest Manifest array.
     * @return string JSON manifest.
     * @throws moodle_exception
     */
    public function encode(array $manifest): string {
        try {
            return json_encode(
                $this->finalise($manifest),
                JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE | JSON_THROW_ON_ERROR
            );
        } catch (JsonException $exception) {
            throw new moodle_exception('errormanifestjson', 'uckkarchive', '', null, $exception->getMessage());
        }
    }

    /**
     * Decode a manifest JSON string.
     *
     * @param string $json JSON manifest.
     * @return array
     * @throws moodle_exception
     */
    public function decode(string $json): array {
        try {
            $decoded = json_decode($json, true, 512, JSON_THROW_ON_ERROR);
        } catch (JsonException $exception) {
            throw new moodle_exception('errormanifestjson', 'uckkarchive', '', null, $exception->getMessage());
        }

        if (!is_array($decoded)) {
            throw new moodle_exception('errormanifestjson', 'uckkarchive');
        }

        return $decoded;
    }

    /**
     * Add an entry to the manifest.
     *
     * @param array $manifest Manifest array.
     * @param string $type Entry type.
     * @param array $entry Entry data.
     */
    protected function add_entry(array &$manifest, string $type, array $entry): void {
        if (!isset($manifest['entries'][$type])) {
            $manifest['entries'][$type] = [];
        }

        $manifest['entries'][$type][] = $this->normalise_entry($entry);
    }

    /**
     * Normalise an entry recursively.
     *
     * @param array $entry Entry data.
     * @return array
     */
    protected function normalise_entry(array $entry): array {
        $normalised = [];

        foreach ($entry as $key => $value) {
            if (is_array($value)) {
                $normalised[$key] = $this->normalise_entry($value);
                continue;
            }

            if ($value instanceof stdClass) {
                $normalised[$key] = $this->normalise_metadata($value);
                continue;
            }

            $normalised[$key] = $value;
        }

        return $normalised;
    }

    /**
     * Return a field value, applying redaction options.
     *
     * Options:
     * - redactfields: string[] field names to mark as redacted.
     * - omitfields: string[] field names to omit.
     * - summarizefields: string[] field names to mark as summarized.
     * - referenceonlyfields: string[] field names to mark as reference_only.
     *
     * @param stdClass $record Record.
     * @param string $field Field name.
     * @param array $options Options.
     * @param bool $metadata Whether field is metadata.
     * @return mixed
     */
    protected function field_value(stdClass $record, string $field, array $options, bool $metadata = false) {
        if ($this->field_in_option($field, $options, 'omitfields')) {
            return self::FIELD_OMITTED;
        }

        if ($this->field_in_option($field, $options, 'redactfields')) {
            return self::FIELD_REDACTED;
        }

        if ($this->field_in_option($field, $options, 'summarizefields')) {
            return self::FIELD_SUMMARIZED;
        }

        if ($this->field_in_option($field, $options, 'referenceonlyfields')) {
            return self::FIELD_REFERENCE_ONLY;
        }

        if (!property_exists($record, $field)) {
            return $metadata ? [] : '';
        }

        $value = $record->{$field};

        if ($metadata) {
            return $this->normalise_metadata($value);
        }

        return $value;
    }

    /**
     * Check if field appears in an option list.
     *
     * @param string $field Field name.
     * @param array $options Options.
     * @param string $option Option key.
     * @return bool
     */
    protected function field_in_option(string $field, array $options, string $option): bool {
        if (empty($options[$option]) || !is_array($options[$option])) {
            return false;
        }

        return in_array($field, $options[$option], true);
    }

    /**
     * Normalise metadata from JSON, arrays, objects, or scalar values.
     *
     * @param mixed $metadata Metadata value.
     * @return array
     */
    protected function normalise_metadata($metadata): array {
        if ($metadata === null || $metadata === '') {
            return [];
        }

        if (is_array($metadata)) {
            return $metadata;
        }

        if ($metadata instanceof stdClass) {
            return (array)$metadata;
        }

        if (is_string($metadata)) {
            try {
                $decoded = json_decode($metadata, true, 512, JSON_THROW_ON_ERROR);
                return is_array($decoded) ? $decoded : ['value' => $metadata];
            } catch (JsonException $exception) {
                return ['value' => $metadata];
            }
        }

        if (is_scalar($metadata)) {
            return ['value' => $metadata];
        }

        return [];
    }

    /**
     * Generate a UUID.
     *
     * @return string
     */
    protected function generate_uuid(): string {
        if (class_exists(uuid::class)) {
            return uuid::generate();
        }

        if (function_exists('random_bytes')) {
            $bytes = random_bytes(16);
            $bytes[6] = chr((ord($bytes[6]) & 0x0f) | 0x40);
            $bytes[8] = chr((ord($bytes[8]) & 0x3f) | 0x80);

            return vsprintf('%s%s-%s-%s-%s-%s%s%s', str_split(bin2hex($bytes), 4));
        }

        return uniqid('uckkarchive-', true);
    }

    /**
     * Get a string property.
     *
     * @param stdClass|null $record Record.
     * @param string $property Property name.
     * @param string $default Default value.
     * @return string
     */
    protected function property_string(?stdClass $record, string $property, string $default = ''): string {
        if ($record === null || !property_exists($record, $property) || $record->{$property} === null) {
            return $default;
        }

        return (string)$record->{$property};
    }

    /**
     * Get an integer property.
     *
     * @param stdClass|null $record Record.
     * @param string $property Property name.
     * @param int $default Default value.
     * @return int
     */
    protected function property_int(?stdClass $record, string $property, int $default = 0): int {
        if ($record === null || !property_exists($record, $property) || $record->{$property} === null) {
            return $default;
        }

        return (int)$record->{$property};
    }

    /**
     * Get a boolean property.
     *
     * @param stdClass|null $record Record.
     * @param string $property Property name.
     * @param bool $default Default value.
     * @return bool
     */
    protected function property_bool(?stdClass $record, string $property, bool $default = false): bool {
        if ($record === null || !property_exists($record, $property) || $record->{$property} === null) {
            return $default;
        }

        return (bool)$record->{$property};
    }

    /**
     * Return a string option.
     *
     * @param array $options Options.
     * @param string $key Option key.
     * @param string $default Default value.
     * @return string
     */
    protected function option_string(array $options, string $key, string $default = ''): string {
        if (!array_key_exists($key, $options) || $options[$key] === null) {
            return $default;
        }

        return (string)$options[$key];
    }

    /**
     * Return an integer option.
     *
     * @param array $options Options.
     * @param string $key Option key.
     * @param int $default Default value.
     * @return int
     */
    protected function option_int(array $options, string $key, int $default = 0): int {
        if (!array_key_exists($key, $options) || $options[$key] === null) {
            return $default;
        }

        return (int)$options[$key];
    }

    /**
     * Return a boolean option.
     *
     * @param array $options Options.
     * @param string $key Option key.
     * @param bool $default Default value.
     * @return bool
     */
    protected function option_bool(array $options, string $key, bool $default = false): bool {
        if (!array_key_exists($key, $options) || $options[$key] === null) {
            return $default;
        }

        return (bool)$options[$key];
    }
}
