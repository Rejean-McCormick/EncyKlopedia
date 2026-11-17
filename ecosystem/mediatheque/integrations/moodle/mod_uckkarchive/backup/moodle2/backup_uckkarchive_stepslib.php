<?php
// This file is part of Moodle - https://moodle.org/
//
// Moodle is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// any later version.

/**
 * Backup structure step for UCKK Archive.
 *
 * @package    mod_uckkarchive
 * @copyright  2026 Univers-Cité King Klown
 * @license    https://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later
 */

defined('MOODLE_INTERNAL') || die();

/**
 * Defines the complete backup structure for one UCKK Archive activity.
 *
 * The structure keeps archive memory, media, didactic material, provenance,
 * proof records, Kristals, revisions, content advisories, external works,
 * media collections, media versions, media relations, and export records
 * together under the restored activity instance.
 *
 * User-created evidence, media, advisory markers, review decisions, source
 * metadata, and audit records are included only when Moodle's standard
 * activity user-data setting is enabled.
 */
class backup_uckkarchive_activity_structure_step extends backup_activity_structure_step {
    /**
     * Define the backup structure.
     *
     * @return backup_nested_element
     */
    protected function define_structure() {
        $userinfo = $this->get_setting_value('userinfo');

        $archive = $this->make_element('uckkarchive', 'uckkarchive', [
            'course',
            'courseid',
            'cmid',
            'contextid',
            'name',
            'intro',
            'introformat',
            'archivecode',
            'archivetype',
            'archivepolicy',
            'defaultvisibility',
            'allowpublicitems',
            'allowstudentitems',
            'requirevalidation',
            'enablekristals',
            'enableexports',
            'allowexports',
            'completionrequireitem',
            'completionrequirevalidation',
            'status',
            'visibility',
            'provenance',
            'versionno',
            'createdby',
            'modifiedby',
            'timecreated',
            'timemodified',
            'metadata',
        ]);

        $archive->set_source_table('uckkarchive', [
            'id' => backup::VAR_ACTIVITYID,
        ]);

        $archive->annotate_ids('course', 'course');
        $archive->annotate_ids('course', 'courseid');
        $archive->annotate_ids('context', 'contextid');
        $archive->annotate_ids('user', 'createdby');
        $archive->annotate_ids('user', 'modifiedby');
        $archive->annotate_files('mod_uckkarchive', 'intro', null);

        if ($userinfo) {
            $this->add_archive_items($archive);
            $this->add_kristals($archive);
            $this->add_archive_level_proofs($archive);
            $this->add_archive_level_provenance($archive);
            $this->add_archive_level_revisions($archive);
            $this->add_exports($archive);
            $this->add_external_works($archive);
            $this->add_media($archive);
            $this->add_media_collections($archive);
            $this->add_content_tag_sets($archive);
            $this->add_content_markers($archive);
        }

        return $this->prepare_activity_structure($archive);
    }

    /**
     * Add archive item subtree.
     *
     * @param backup_nested_element $archive Archive element.
     * @return void
     */
    protected function add_archive_items($archive) {
        if (!$this->table_exists('uckkarchive_item')) {
            return;
        }

        $items = new backup_nested_element('items');

        $item = $this->make_element('item', 'uckkarchive_item', [
            'archiveid',
            'courseid',
            'cmid',
            'contextid',
            'userid',
            'parentitemid',
            'itemtype',
            'title',
            'summary',
            'content',
            'contentformat',
            'publicsummary',
            'publicsummaryformat',
            'sourceurl',
            'sourcetitle',
            'sourceauthor',
            'sourcedate',
            'sourcecomponent',
            'sourceobjectid',
            'origincomponent',
            'originarea',
            'originid',
            'originobjectid',
            'license',
            'tags',
            'status',
            'visibility',
            'validationstate',
            'provenance',
            'provenancehash',
            'integritycaseid',
            'versionno',
            'createdby',
            'modifiedby',
            'timecreated',
            'timemodified',
            'metadata',
        ]);

        $archive->add_child($items);
        $items->add_child($item);

        $item->set_source_table('uckkarchive_item', [
            'archiveid' => backup::VAR_PARENTID,
        ]);

        $item->annotate_ids('course', 'courseid');
        $item->annotate_ids('context', 'contextid');
        $item->annotate_ids('user', 'userid');
        $item->annotate_ids('user', 'createdby');
        $item->annotate_ids('user', 'modifiedby');

        $item->annotate_files('mod_uckkarchive', 'item_content', 'id');
        $item->annotate_files('mod_uckkarchive', 'public_summary', 'id');
        $item->annotate_files('mod_uckkarchive', 'item_files', 'id');
        $item->annotate_files('mod_uckkarchive', 'proof_files', 'id');

        $this->add_item_proofs($item);
        $this->add_item_provenance($item);
        $this->add_item_revisions($item);
    }

    /**
     * Add Kristal records.
     *
     * @param backup_nested_element $archive Archive element.
     * @return void
     */
    protected function add_kristals($archive) {
        if (!$this->table_exists('uckkarchive_kristal')) {
            return;
        }

        $kristals = new backup_nested_element('kristals');

        $kristal = $this->make_element('kristal', 'uckkarchive_kristal', [
            'archiveid',
            'itemid',
            'sourceitemid',
            'courseid',
            'cmid',
            'contextid',
            'userid',
            'shortname',
            'kristaltype',
            'title',
            'claim',
            'body',
            'bodyformat',
            'content',
            'contentformat',
            'summary',
            'summaryformat',
            'evidence',
            'concepts',
            'relations',
            'sourceurl',
            'sourcetitle',
            'sourceauthor',
            'sourcedate',
            'confidence',
            'status',
            'visibility',
            'validationstate',
            'provenance',
            'provenancehash',
            'integritycaseid',
            'versionno',
            'createdby',
            'modifiedby',
            'timecreated',
            'timemodified',
            'metadata',
        ]);

        $archive->add_child($kristals);
        $kristals->add_child($kristal);

        $kristal->set_source_table('uckkarchive_kristal', [
            'archiveid' => backup::VAR_PARENTID,
        ]);

        $kristal->annotate_ids('course', 'courseid');
        $kristal->annotate_ids('context', 'contextid');
        $kristal->annotate_ids('user', 'userid');
        $kristal->annotate_ids('user', 'createdby');
        $kristal->annotate_ids('user', 'modifiedby');

        $kristal->annotate_files('mod_uckkarchive', 'kristal_content', 'id');
        $kristal->annotate_files('mod_uckkarchive', 'kristal_summary', 'id');
        $kristal->annotate_files('mod_uckkarchive', 'kristal_files', 'id');
    }

    /**
     * Add proof records directly under archive when schema uses archiveid only.
     *
     * @param backup_nested_element $archive Archive element.
     * @return void
     */
    protected function add_archive_level_proofs($archive) {
        if (!$this->table_exists('uckkarchive_proof')) {
            return;
        }

        $proofs = new backup_nested_element('archiveproofs');

        $proof = $this->make_element('archiveproof', 'uckkarchive_proof', [
            'archiveid',
            'itemid',
            'courseid',
            'cmid',
            'contextid',
            'userid',
            'prooftype',
            'title',
            'description',
            'descriptionformat',
            'sourceurl',
            'sourcetitle',
            'sourceauthor',
            'sourcedate',
            'fileitemid',
            'sourcecomponent',
            'sourceobjectid',
            'status',
            'visibility',
            'validationstate',
            'provenance',
            'provenancehash',
            'integritycaseid',
            'versionno',
            'createdby',
            'modifiedby',
            'timecreated',
            'timemodified',
            'metadata',
        ]);

        $archive->add_child($proofs);
        $proofs->add_child($proof);

        $proof->set_source_table('uckkarchive_proof', [
            'archiveid' => backup::VAR_PARENTID,
        ]);

        $proof->annotate_ids('course', 'courseid');
        $proof->annotate_ids('context', 'contextid');
        $proof->annotate_ids('user', 'userid');
        $proof->annotate_ids('user', 'createdby');
        $proof->annotate_ids('user', 'modifiedby');

        $proof->annotate_files('mod_uckkarchive', 'proof_description', 'id');
        $proof->annotate_files('mod_uckkarchive', 'proof_files', 'id');
    }

    /**
     * Add proof records nested under archive items.
     *
     * @param backup_nested_element $item Item element.
     * @return void
     */
    protected function add_item_proofs($item) {
        if (!$this->table_exists('uckkarchive_proof')) {
            return;
        }

        $proofs = new backup_nested_element('proofs');

        $proof = $this->make_element('proof', 'uckkarchive_proof', [
            'archiveid',
            'itemid',
            'courseid',
            'cmid',
            'contextid',
            'userid',
            'prooftype',
            'title',
            'description',
            'descriptionformat',
            'sourceurl',
            'sourcetitle',
            'sourceauthor',
            'sourcedate',
            'fileitemid',
            'sourcecomponent',
            'sourceobjectid',
            'status',
            'visibility',
            'validationstate',
            'provenance',
            'provenancehash',
            'integritycaseid',
            'versionno',
            'createdby',
            'modifiedby',
            'timecreated',
            'timemodified',
            'metadata',
        ]);

        $item->add_child($proofs);
        $proofs->add_child($proof);

        $proof->set_source_table('uckkarchive_proof', [
            'itemid' => backup::VAR_PARENTID,
        ]);

        $proof->annotate_ids('course', 'courseid');
        $proof->annotate_ids('context', 'contextid');
        $proof->annotate_ids('user', 'userid');
        $proof->annotate_ids('user', 'createdby');
        $proof->annotate_ids('user', 'modifiedby');

        $proof->annotate_files('mod_uckkarchive', 'proof_description', 'id');
        $proof->annotate_files('mod_uckkarchive', 'proof_files', 'id');
    }

    /**
     * Add provenance records directly under archive.
     *
     * @param backup_nested_element $archive Archive element.
     * @return void
     */
    protected function add_archive_level_provenance($archive) {
        if (!$this->table_exists('uckkarchive_prov')) {
            return;
        }

        $provenances = new backup_nested_element('archiveprovenances');

        $provenance = $this->make_element('archiveprovenance', 'uckkarchive_prov', [
            'archiveid',
            'itemid',
            'proofid',
            'kristalid',
            'courseid',
            'cmid',
            'contextid',
            'userid',
            'authorid',
            'origincomponent',
            'originobjectid',
            'sourcecomponent',
            'sourcearea',
            'sourceid',
            'sourcetype',
            'sourcetitle',
            'sourceurl',
            'sourceauthor',
            'sourcedate',
            'source',
            'statement',
            'statementformat',
            'evidence',
            'status',
            'visibility',
            'validationstate',
            'provenance',
            'provenancehash',
            'integritycaseid',
            'versionno',
            'createdby',
            'modifiedby',
            'timecreated',
            'timemodified',
            'metadata',
        ]);

        $archive->add_child($provenances);
        $provenances->add_child($provenance);

        $provenance->set_source_table('uckkarchive_prov', [
            'archiveid' => backup::VAR_PARENTID,
        ]);

        $provenance->annotate_ids('course', 'courseid');
        $provenance->annotate_ids('context', 'contextid');
        $provenance->annotate_ids('user', 'userid');
        $provenance->annotate_ids('user', 'authorid');
        $provenance->annotate_ids('user', 'createdby');
        $provenance->annotate_ids('user', 'modifiedby');

        $provenance->annotate_files('mod_uckkarchive', 'provenance_statement', 'id');
    }

    /**
     * Add provenance records nested under archive items.
     *
     * @param backup_nested_element $item Item element.
     * @return void
     */
    protected function add_item_provenance($item) {
        if (!$this->table_exists('uckkarchive_prov')) {
            return;
        }

        $provenances = new backup_nested_element('provenances');

        $provenance = $this->make_element('provenance', 'uckkarchive_prov', [
            'archiveid',
            'itemid',
            'proofid',
            'kristalid',
            'courseid',
            'cmid',
            'contextid',
            'userid',
            'authorid',
            'origincomponent',
            'originobjectid',
            'sourcecomponent',
            'sourcearea',
            'sourceid',
            'sourcetype',
            'sourcetitle',
            'sourceurl',
            'sourceauthor',
            'sourcedate',
            'source',
            'statement',
            'statementformat',
            'evidence',
            'status',
            'visibility',
            'validationstate',
            'provenance',
            'provenancehash',
            'integritycaseid',
            'versionno',
            'createdby',
            'modifiedby',
            'timecreated',
            'timemodified',
            'metadata',
        ]);

        $item->add_child($provenances);
        $provenances->add_child($provenance);

        $provenance->set_source_table('uckkarchive_prov', [
            'itemid' => backup::VAR_PARENTID,
        ]);

        $provenance->annotate_ids('course', 'courseid');
        $provenance->annotate_ids('context', 'contextid');
        $provenance->annotate_ids('user', 'userid');
        $provenance->annotate_ids('user', 'authorid');
        $provenance->annotate_ids('user', 'createdby');
        $provenance->annotate_ids('user', 'modifiedby');

        $provenance->annotate_files('mod_uckkarchive', 'provenance_statement', 'id');
    }

    /**
     * Add revision records directly under archive.
     *
     * @param backup_nested_element $archive Archive element.
     * @return void
     */
    protected function add_archive_level_revisions($archive) {
        if (!$this->table_exists('uckkarchive_rev')) {
            return;
        }

        $revisions = new backup_nested_element('archiverevisions');

        $revision = $this->make_element('archiverevision', 'uckkarchive_rev', [
            'archiveid',
            'itemid',
            'courseid',
            'cmid',
            'contextid',
            'userid',
            'revisiontype',
            'previousstatus',
            'newstatus',
            'previousvisibility',
            'newvisibility',
            'previousvalidationstate',
            'newvalidationstate',
            'previousstate',
            'newstate',
            'reason',
            'changereason',
            'status',
            'visibility',
            'provenance',
            'provenancehash',
            'integritycaseid',
            'versionno',
            'createdby',
            'modifiedby',
            'timecreated',
            'timemodified',
            'metadata',
        ]);

        $archive->add_child($revisions);
        $revisions->add_child($revision);

        $revision->set_source_table('uckkarchive_rev', [
            'archiveid' => backup::VAR_PARENTID,
        ]);

        $revision->annotate_ids('course', 'courseid');
        $revision->annotate_ids('context', 'contextid');
        $revision->annotate_ids('user', 'userid');
        $revision->annotate_ids('user', 'createdby');
        $revision->annotate_ids('user', 'modifiedby');
    }

    /**
     * Add item revision records.
     *
     * @param backup_nested_element $item Item element.
     * @return void
     */
    protected function add_item_revisions($item) {
        if (!$this->table_exists('uckkarchive_rev')) {
            return;
        }

        $revisions = new backup_nested_element('revisions');

        $revision = $this->make_element('revision', 'uckkarchive_rev', [
            'archiveid',
            'itemid',
            'courseid',
            'cmid',
            'contextid',
            'userid',
            'revisiontype',
            'previousstatus',
            'newstatus',
            'previousvisibility',
            'newvisibility',
            'previousvalidationstate',
            'newvalidationstate',
            'previousstate',
            'newstate',
            'reason',
            'changereason',
            'status',
            'visibility',
            'provenance',
            'provenancehash',
            'integritycaseid',
            'versionno',
            'createdby',
            'modifiedby',
            'timecreated',
            'timemodified',
            'metadata',
        ]);

        $item->add_child($revisions);
        $revisions->add_child($revision);

        $revision->set_source_table('uckkarchive_rev', [
            'itemid' => backup::VAR_PARENTID,
        ]);

        $revision->annotate_ids('course', 'courseid');
        $revision->annotate_ids('context', 'contextid');
        $revision->annotate_ids('user', 'userid');
        $revision->annotate_ids('user', 'createdby');
        $revision->annotate_ids('user', 'modifiedby');
    }

    /**
     * Add export records.
     *
     * @param backup_nested_element $archive Archive element.
     * @return void
     */
    protected function add_exports($archive) {
        if (!$this->table_exists('uckkarchive_export')) {
            return;
        }

        $exports = new backup_nested_element('exports');

        $export = $this->make_element('export', 'uckkarchive_export', [
            'archiveid',
            'itemid',
            'courseid',
            'cmid',
            'contextid',
            'userid',
            'exporttype',
            'exportscope',
            'exportformat',
            'title',
            'summary',
            'summaryformat',
            'packagename',
            'description',
            'itemids',
            'reason',
            'auditnote',
            'redactionlevel',
            'redacted',
            'includefiles',
            'includeproofs',
            'includeprovenance',
            'includeversions',
            'fileitemid',
            'downloadcount',
            'lastdownloaded',
            'timequeued',
            'timestarted',
            'timecompleted',
            'error',
            'status',
            'visibility',
            'validationstate',
            'provenance',
            'provenancehash',
            'integritycaseid',
            'versionno',
            'createdby',
            'modifiedby',
            'timecreated',
            'timemodified',
            'metadata',
        ]);

        $archive->add_child($exports);
        $exports->add_child($export);

        $export->set_source_table('uckkarchive_export', [
            'archiveid' => backup::VAR_PARENTID,
        ]);

        $export->annotate_ids('course', 'courseid');
        $export->annotate_ids('context', 'contextid');
        $export->annotate_ids('user', 'userid');
        $export->annotate_ids('user', 'createdby');
        $export->annotate_ids('user', 'modifiedby');

        $export->annotate_files('mod_uckkarchive', 'export_files', 'id');
        $export->annotate_files('mod_uckkarchive', 'export_manifest', 'id');
        $export->annotate_files('mod_uckkarchive', 'export_package', 'id');
    }

    /**
     * Add external work records.
     *
     * @param backup_nested_element $archive Archive element.
     * @return void
     */
    protected function add_external_works($archive) {
        if (!$this->table_exists('uckkarchive_external_work')) {
            return;
        }

        $externalworks = new backup_nested_element('external_works');

        $externalwork = $this->make_element('external_work', 'uckkarchive_external_work', [
            'uuid',
            'archiveid',
            'courseid',
            'cmid',
            'contextid',
            'ownerid',
            'userid',
            'worktype',
            'status',
            'visibility',
            'audiencesuitability',
            'rightsstatus',
            'title',
            'subtitle',
            'creator',
            'publisher',
            'publicationyear',
            'language',
            'sourceurl',
            'identifier',
            'identifiertype',
            'citation',
            'rightsstatement',
            'licensekey',
            'sourcenote',
            'teachingnote',
            'culturalprotocolnote',
            'description',
            'provenanceid',
            'createdby',
            'modifiedby',
            'timecreated',
            'timemodified',
            'metadata',
        ]);

        $archive->add_child($externalworks);
        $externalworks->add_child($externalwork);

        $externalwork->set_source_table('uckkarchive_external_work', [
            'archiveid' => backup::VAR_PARENTID,
        ]);

        $externalwork->annotate_ids('course', 'courseid');
        $externalwork->annotate_ids('context', 'contextid');
        $externalwork->annotate_ids('user', 'ownerid');
        $externalwork->annotate_ids('user', 'userid');
        $externalwork->annotate_ids('user', 'createdby');
        $externalwork->annotate_ids('user', 'modifiedby');

        $externalwork->annotate_files('mod_uckkarchive', 'external_work_reference_files', 'id');
        $externalwork->annotate_files('mod_uckkarchive', 'cultural_protocol_files', 'id');
    }

    /**
     * Add media library records.
     *
     * @param backup_nested_element $archive Archive element.
     * @return void
     */
    protected function add_media($archive) {
        if (!$this->table_exists('uckkarchive_media')) {
            return;
        }

        $mediarecords = new backup_nested_element('media_records');

        $media = $this->make_element('media', 'uckkarchive_media', [
            'uuid',
            'archiveid',
            'courseid',
            'cmid',
            'contextid',
            'userid',
            'ownerid',
            'externalworkid',
            'currentversionid',
            'title',
            'summary',
            'description',
            'mediatype',
            'mimetype',
            'source',
            'sourcetype',
            'sourceurl',
            'sourcecomponent',
            'sourceobjectid',
            'license',
            'rightsstatus',
            'status',
            'visibility',
            'audiencesuitability',
            'provenance',
            'provenancehash',
            'integritycaseid',
            'culturalprotocol',
            'restricted',
            'searchable',
            'versionno',
            'createdby',
            'modifiedby',
            'timecreated',
            'timemodified',
            'metadata',
        ]);

        $archive->add_child($mediarecords);
        $mediarecords->add_child($media);

        $media->set_source_table('uckkarchive_media', [
            'archiveid' => backup::VAR_PARENTID,
        ]);

        $media->annotate_ids('course', 'courseid');
        $media->annotate_ids('context', 'contextid');
        $media->annotate_ids('user', 'userid');
        $media->annotate_ids('user', 'ownerid');
        $media->annotate_ids('user', 'createdby');
        $media->annotate_ids('user', 'modifiedby');

        $media->annotate_files('mod_uckkarchive', 'media_original', 'id');
        $media->annotate_files('mod_uckkarchive', 'media_preview', 'id');
        $media->annotate_files('mod_uckkarchive', 'media_thumbnail', 'id');
        $media->annotate_files('mod_uckkarchive', 'media_derivative', 'id');
        $media->annotate_files('mod_uckkarchive', 'media_caption', 'id');
        $media->annotate_files('mod_uckkarchive', 'media_transcript', 'id');
        $media->annotate_files('mod_uckkarchive', 'media_attachment', 'id');

        $this->add_media_versions($media);
        $this->add_media_sources($media);
        $this->add_media_tags($media);
        $this->add_media_relations($media);
    }

    /**
     * Add media version records.
     *
     * @param backup_nested_element $media Media element.
     * @return void
     */
    protected function add_media_versions($media) {
        if (!$this->table_exists('uckkarchive_media_version')) {
            return;
        }

        $versions = new backup_nested_element('media_versions');

        $version = $this->make_element('media_version', 'uckkarchive_media_version', [
            'uuid',
            'mediaid',
            'archiveid',
            'courseid',
            'cmid',
            'contextid',
            'userid',
            'versionnumber',
            'versionno',
            'label',
            'changereason',
            'filearea',
            'filename',
            'filepath',
            'filesize',
            'mimetype',
            'contenthash',
            'iscurrent',
            'status',
            'visibility',
            'provenancehash',
            'createdby',
            'modifiedby',
            'timecreated',
            'timemodified',
            'metadata',
        ]);

        $media->add_child($versions);
        $versions->add_child($version);

        $version->set_source_table('uckkarchive_media_version', [
            'mediaid' => backup::VAR_PARENTID,
        ]);

        $version->annotate_ids('course', 'courseid');
        $version->annotate_ids('context', 'contextid');
        $version->annotate_ids('user', 'userid');
        $version->annotate_ids('user', 'createdby');
        $version->annotate_ids('user', 'modifiedby');

        $version->annotate_files('mod_uckkarchive', 'media_original', 'id');
        $version->annotate_files('mod_uckkarchive', 'media_preview', 'id');
        $version->annotate_files('mod_uckkarchive', 'media_derivative', 'id');
        $version->annotate_files('mod_uckkarchive', 'media_caption', 'id');
        $version->annotate_files('mod_uckkarchive', 'media_transcript', 'id');
        $version->annotate_files('mod_uckkarchive', 'media_attachment', 'id');
    }

    /**
     * Add media source records.
     *
     * @param backup_nested_element $media Media element.
     * @return void
     */
    protected function add_media_sources($media) {
        if (!$this->table_exists('uckkarchive_media_source')) {
            return;
        }

        $sources = new backup_nested_element('media_sources');

        $source = $this->make_element('media_source', 'uckkarchive_media_source', [
            'uuid',
            'mediaid',
            'archiveid',
            'courseid',
            'cmid',
            'contextid',
            'userid',
            'sourcetype',
            'sourcecomponent',
            'sourceobjectid',
            'sourceurl',
            'sourceauthor',
            'sourcedate',
            'citation',
            'rightsstatus',
            'license',
            'status',
            'visibility',
            'provenancehash',
            'createdby',
            'modifiedby',
            'timecreated',
            'timemodified',
            'metadata',
        ]);

        $media->add_child($sources);
        $sources->add_child($source);

        $source->set_source_table('uckkarchive_media_source', [
            'mediaid' => backup::VAR_PARENTID,
        ]);

        $source->annotate_ids('course', 'courseid');
        $source->annotate_ids('context', 'contextid');
        $source->annotate_ids('user', 'userid');
        $source->annotate_ids('user', 'createdby');
        $source->annotate_ids('user', 'modifiedby');
    }

    /**
     * Add media tag records.
     *
     * @param backup_nested_element $media Media element.
     * @return void
     */
    protected function add_media_tags($media) {
        if (!$this->table_exists('uckkarchive_media_tag')) {
            return;
        }

        $tags = new backup_nested_element('media_tags');

        $tag = $this->make_element('media_tag', 'uckkarchive_media_tag', [
            'uuid',
            'archiveid',
            'courseid',
            'cmid',
            'contextid',
            'mediaid',
            'userid',
            'tag',
            'tagkey',
            'tagtype',
            'rawname',
            'source',
            'status',
            'visibility',
            'createdby',
            'modifiedby',
            'timecreated',
            'timemodified',
            'metadata',
        ]);

        $media->add_child($tags);
        $tags->add_child($tag);

        $tag->set_source_table('uckkarchive_media_tag', [
            'mediaid' => backup::VAR_PARENTID,
        ]);

        $tag->annotate_ids('course', 'courseid');
        $tag->annotate_ids('context', 'contextid');
        $tag->annotate_ids('user', 'userid');
        $tag->annotate_ids('user', 'createdby');
        $tag->annotate_ids('user', 'modifiedby');
    }

    /**
     * Add media relation records.
     *
     * @param backup_nested_element $media Media element.
     * @return void
     */
    protected function add_media_relations($media) {
        if (!$this->table_exists('uckkarchive_media_relation')) {
            return;
        }

        $relations = new backup_nested_element('media_relations');

        $relation = $this->make_element('media_relation', 'uckkarchive_media_relation', [
            'uuid',
            'archiveid',
            'courseid',
            'cmid',
            'contextid',
            'mediaid',
            'sourcemediaid',
            'targetmediaid',
            'targettype',
            'targetid',
            'relationtype',
            'description',
            'status',
            'visibility',
            'createdby',
            'modifiedby',
            'timecreated',
            'timemodified',
            'metadata',
        ]);

        $media->add_child($relations);
        $relations->add_child($relation);

        $relation->set_source_table('uckkarchive_media_relation', [
            'mediaid' => backup::VAR_PARENTID,
        ]);

        $relation->annotate_ids('course', 'courseid');
        $relation->annotate_ids('context', 'contextid');
        $relation->annotate_ids('user', 'createdby');
        $relation->annotate_ids('user', 'modifiedby');
    }

    /**
     * Add media collections.
     *
     * @param backup_nested_element $archive Archive element.
     * @return void
     */
    protected function add_media_collections($archive) {
        if (!$this->table_exists('uckkarchive_media_collection')) {
            return;
        }

        $collections = new backup_nested_element('media_collections');

        $collection = $this->make_element('media_collection', 'uckkarchive_media_collection', [
            'uuid',
            'archiveid',
            'courseid',
            'cmid',
            'contextid',
            'userid',
            'ownerid',
            'title',
            'description',
            'collectiontype',
            'status',
            'visibility',
            'audiencesuitability',
            'sortorder',
            'createdby',
            'modifiedby',
            'timecreated',
            'timemodified',
            'metadata',
        ]);

        $archive->add_child($collections);
        $collections->add_child($collection);

        $collection->set_source_table('uckkarchive_media_collection', [
            'archiveid' => backup::VAR_PARENTID,
        ]);

        $collection->annotate_ids('course', 'courseid');
        $collection->annotate_ids('context', 'contextid');
        $collection->annotate_ids('user', 'userid');
        $collection->annotate_ids('user', 'ownerid');
        $collection->annotate_ids('user', 'createdby');
        $collection->annotate_ids('user', 'modifiedby');

        $this->add_media_collection_items($collection);
    }

    /**
     * Add media collection membership records.
     *
     * @param backup_nested_element $collection Collection element.
     * @return void
     */
    protected function add_media_collection_items($collection) {
        if (!$this->table_exists('uckkarchive_media_collection_item')) {
            return;
        }

        $items = new backup_nested_element('media_collection_items');

        $item = $this->make_element('media_collection_item', 'uckkarchive_media_collection_item', [
            'collectionid',
            'mediaid',
            'archiveid',
            'courseid',
            'cmid',
            'contextid',
            'sortorder',
            'role',
            'status',
            'createdby',
            'modifiedby',
            'timecreated',
            'timemodified',
            'metadata',
        ]);

        $collection->add_child($items);
        $items->add_child($item);

        $item->set_source_table('uckkarchive_media_collection_item', [
            'collectionid' => backup::VAR_PARENTID,
        ]);

        $item->annotate_ids('course', 'courseid');
        $item->annotate_ids('context', 'contextid');
        $item->annotate_ids('user', 'createdby');
        $item->annotate_ids('user', 'modifiedby');
    }

    /**
     * Add content advisory tag sets and tags.
     *
     * @param backup_nested_element $archive Archive element.
     * @return void
     */
    protected function add_content_tag_sets($archive) {
        if (!$this->table_exists('uckkarchive_content_tag_set')) {
            return;
        }

        $tagsets = new backup_nested_element('content_tag_sets');

        $tagset = $this->make_element('content_tag_set', 'uckkarchive_content_tag_set', [
            'uuid',
            'tagsetkey',
            'setkey',
            'name',
            'label',
            'description',
            'status',
            'visibility',
            'version',
            'sortorder',
            'createdby',
            'modifiedby',
            'timecreated',
            'timemodified',
            'metadata',
        ]);

        $archive->add_child($tagsets);
        $tagsets->add_child($tagset);

        $tagset->set_source_table('uckkarchive_content_tag_set', []);

        $tagset->annotate_ids('user', 'createdby');
        $tagset->annotate_ids('user', 'modifiedby');

        $this->add_content_tags($tagset);
        $this->add_content_tag_set_items($tagset);
    }

    /**
     * Add content tag definitions.
     *
     * @param backup_nested_element $tagset Tag set element.
     * @return void
     */
    protected function add_content_tags($tagset) {
        if (!$this->table_exists('uckkarchive_content_tag')) {
            return;
        }

        $tags = new backup_nested_element('content_tags');

        $tag = $this->make_element('content_tag', 'uckkarchive_content_tag', [
            'uuid',
            'tagsetid',
            'tagkey',
            'key',
            'name',
            'label',
            'category',
            'description',
            'defaultseverity',
            'defaultaudiencesuitability',
            'defaultreviewstate',
            'iscultural',
            'restrictsbydefault',
            'requiresreview',
            'status',
            'visibility',
            'sortorder',
            'createdby',
            'modifiedby',
            'timecreated',
            'timemodified',
            'metadata',
        ]);

        $tagset->add_child($tags);
        $tags->add_child($tag);

        $tag->set_source_table('uckkarchive_content_tag', [
            'tagsetid' => backup::VAR_PARENTID,
        ]);

        $tag->annotate_ids('user', 'createdby');
        $tag->annotate_ids('user', 'modifiedby');
    }

    /**
     * Add content tag set membership records.
     *
     * @param backup_nested_element $tagset Tag set element.
     * @return void
     */
    protected function add_content_tag_set_items($tagset) {
        if (!$this->table_exists('uckkarchive_content_tag_set_item')) {
            return;
        }

        $items = new backup_nested_element('content_tag_set_items');

        $item = $this->make_element('content_tag_set_item', 'uckkarchive_content_tag_set_item', [
            'tagsetid',
            'tagid',
            'sortorder',
            'status',
            'timecreated',
            'timemodified',
        ]);

        $tagset->add_child($items);
        $items->add_child($item);

        $item->set_source_table('uckkarchive_content_tag_set_item', [
            'tagsetid' => backup::VAR_PARENTID,
        ]);
    }

    /**
     * Add content advisory markers.
     *
     * @param backup_nested_element $archive Archive element.
     * @return void
     */
    protected function add_content_markers($archive) {
        if (!$this->table_exists('uckkarchive_content_marker')) {
            return;
        }

        $markers = new backup_nested_element('content_markers');

        $marker = $this->make_element('content_marker', 'uckkarchive_content_marker', [
            'uuid',
            'archiveid',
            'courseid',
            'cmid',
            'contextid',
            'mediaid',
            'externalworkid',
            'itemid',
            'targettype',
            'targetid',
            'userid',
            'tagid',
            'tagkey',
            'tag',
            'category',
            'severity',
            'audiencesuitability',
            'reviewstate',
            'visibility',
            'locatortype',
            'locator',
            'locatorstart',
            'locatorend',
            'locatorlabel',
            'description',
            'note',
            'culturalprotocol',
            'restricted',
            'requirescontext',
            'redacted',
            'provenanceid',
            'reviewedby',
            'createdby',
            'modifiedby',
            'timecreated',
            'timemodified',
            'timereviewed',
            'metadata',
        ]);

        $archive->add_child($markers);
        $markers->add_child($marker);

        $marker->set_source_table('uckkarchive_content_marker', [
            'archiveid' => backup::VAR_PARENTID,
        ]);

        $marker->annotate_ids('course', 'courseid');
        $marker->annotate_ids('context', 'contextid');
        $marker->annotate_ids('user', 'userid');
        $marker->annotate_ids('user', 'reviewedby');
        $marker->annotate_ids('user', 'createdby');
        $marker->annotate_ids('user', 'modifiedby');

        $this->add_content_reviews($marker);
    }

    /**
     * Add human review decisions for content markers.
     *
     * @param backup_nested_element $marker Marker element.
     * @return void
     */
    protected function add_content_reviews($marker) {
        if (!$this->table_exists('uckkarchive_content_review')) {
            return;
        }

        $reviews = new backup_nested_element('content_reviews');

        $review = $this->make_element('content_review', 'uckkarchive_content_review', [
            'uuid',
            'archiveid',
            'courseid',
            'cmid',
            'contextid',
            'markerid',
            'reviewerid',
            'userid',
            'state',
            'severity',
            'audiencesuitability',
            'rationale',
            'reviewnote',
            'culturalprotocol',
            'restricted',
            'createdby',
            'modifiedby',
            'timecreated',
            'timemodified',
            'metadata',
        ]);

        $marker->add_child($reviews);
        $reviews->add_child($review);

        $review->set_source_table('uckkarchive_content_review', [
            'markerid' => backup::VAR_PARENTID,
        ]);

        $review->annotate_ids('course', 'courseid');
        $review->annotate_ids('context', 'contextid');
        $review->annotate_ids('user', 'reviewerid');
        $review->annotate_ids('user', 'userid');
        $review->annotate_ids('user', 'createdby');
        $review->annotate_ids('user', 'modifiedby');

        $review->annotate_files('mod_uckkarchive', 'content_review_files', 'id');
    }

    /**
     * Create a backup nested element using only fields that exist in the table.
     *
     * This keeps the backup step tolerant while the plugin is evolving across
     * installations that may have been upgraded through different intermediate
     * versions.
     *
     * @param string $name Element name.
     * @param string $table Table name.
     * @param array $candidatefields Candidate fields.
     * @return backup_nested_element
     */
    protected function make_element($name, $table, array $candidatefields) {
        return new backup_nested_element($name, ['id'], $this->existing_fields($table, $candidatefields));
    }

    /**
     * Return only candidate fields that exist in the table.
     *
     * @param string $table Table name.
     * @param array $candidatefields Candidate fields.
     * @return array
     */
    protected function existing_fields($table, array $candidatefields) {
        global $DB;

        if (!$this->table_exists($table)) {
            return $candidatefields;
        }

        $columns = $DB->get_columns($table);
        $fields = [];

        foreach ($candidatefields as $field) {
            if ($field === 'id') {
                continue;
            }

            if (array_key_exists($field, $columns)) {
                $fields[] = $field;
            }
        }

        return $fields;
    }

    /**
     * Return whether a table exists.
     *
     * @param string $table Table name without prefix.
     * @return bool
     */
    protected function table_exists($table) {
        global $DB;

        return $DB->get_manager()->table_exists(new xmldb_table($table));
    }
}

