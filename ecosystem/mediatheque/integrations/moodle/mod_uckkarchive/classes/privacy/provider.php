<?php
// This file is part of Moodle - https://moodle.org/
//
// Moodle is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// any later version.

/**
 * Privacy provider for the UCKK Archive activity.
 *
 * @package    mod_uckkarchive
 * @copyright  2026 Univers-Cité King Klown
 * @license    https://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later
 */

declare(strict_types=1);

namespace mod_uckkarchive\privacy;

use context;
use core_privacy\local\metadata\collection;
use core_privacy\local\request\approved_contextlist;
use core_privacy\local\request\approved_userlist;
use core_privacy\local\request\contextlist;
use core_privacy\local\request\userlist;
use core_privacy\local\request\writer;
use stdClass;
use xmldb_field;
use xmldb_table;

defined('MOODLE_INTERNAL') || die();

/**
 * Privacy provider for mod_uckkarchive.
 *
 * UCKK Archive is an institutional memory module. Some records are institutional
 * and must remain historically coherent, but many archive records can contain
 * personal data: user-authored archive items, media records, evidence, proofs,
 * Kristals, provenance statements, revision notes, validation records, content
 * advisories, cultural protocol reviews, external work references, media source
 * notes, and export logs.
 *
 * User deletion therefore avoids silent destruction of institutional memory
 * where possible. It anonymises user references and redacts user-authored text.
 * Full context deletion removes child records and plugin-owned files in that
 * Moodle context.
 */
final class provider implements
    \core_privacy\local\metadata\provider,
    \core_privacy\local\request\plugin\provider,
    \core_privacy\local\request\core_userlist_provider {

    /**
     * Plugin component name.
     */
    private const COMPONENT = 'mod_uckkarchive';

    /**
     * Tables owned by the plugin and potentially containing personal data.
     *
     * userfields:
     * - user id fields that can identify a person.
     *
     * textfields:
     * - text/json fields that can contain personal data and should be redacted
     *   when a user is erased.
     *
     * metadata:
     * - language string identifier used by get_metadata().
     *
     * Keep child tables before parent tables so full-context deletion does not
     * trip over database foreign keys.
     */
    private const TABLES = [
        'uckkarchive_content_review' => [
            'userfields' => ['userid', 'reviewerid', 'createdby', 'modifiedby'],
            'textfields' => [
                'rationale',
                'reviewnote',
                'note',
                'metadata',
            ],
            'metadata' => 'privacy:metadata:uckkarchive_content_review',
        ],
        'uckkarchive_content_marker' => [
            'userfields' => ['userid', 'createdby', 'modifiedby', 'reviewedby'],
            'textfields' => [
                'description',
                'note',
                'advisorynote',
                'teachingnote',
                'locator',
                'locatorlabel',
                'metadata',
            ],
            'metadata' => 'privacy:metadata:uckkarchive_content_marker',
        ],
        'uckkarchive_content_tag' => [
            'userfields' => ['userid', 'createdby', 'modifiedby'],
            'textfields' => [
                'tagkey',
                'label',
                'name',
                'description',
                'metadata',
            ],
            'metadata' => 'privacy:metadata:uckkarchive_content_tag',
        ],
        'uckkarchive_content_tag_set' => [
            'userfields' => ['userid', 'createdby', 'modifiedby'],
            'textfields' => [
                'tagsetkey',
                'setkey',
                'label',
                'name',
                'description',
                'metadata',
            ],
            'metadata' => 'privacy:metadata:uckkarchive_content_tag_set',
        ],
        'uckkarchive_media_collection_item' => [
            'userfields' => ['userid', 'createdby', 'modifiedby'],
            'textfields' => [
                'note',
                'metadata',
            ],
            'metadata' => 'privacy:metadata:uckkarchive_media_collection_item',
        ],
        'uckkarchive_media_relation' => [
            'userfields' => ['userid', 'createdby', 'modifiedby'],
            'textfields' => [
                'relationtype',
                'description',
                'note',
                'metadata',
            ],
            'metadata' => 'privacy:metadata:uckkarchive_media_relation',
        ],
        'uckkarchive_media_tag' => [
            'userfields' => ['userid', 'createdby', 'modifiedby'],
            'textfields' => [
                'tag',
                'tagkey',
                'name',
                'rawname',
                'note',
                'metadata',
            ],
            'metadata' => 'privacy:metadata:uckkarchive_media_tag',
        ],
        'uckkarchive_media_source' => [
            'userfields' => ['userid', 'createdby', 'modifiedby'],
            'textfields' => [
                'source',
                'sourcetype',
                'sourceurl',
                'sourceauthor',
                'citation',
                'rightsstatement',
                'sourcenote',
                'metadata',
                'provenancehash',
            ],
            'metadata' => 'privacy:metadata:uckkarchive_media_source',
        ],
        'uckkarchive_media_version' => [
            'userfields' => ['userid', 'createdby', 'modifiedby'],
            'textfields' => [
                'label',
                'title',
                'filename',
                'mimetype',
                'contenthash',
                'filehash',
                'changecomment',
                'reason',
                'metadata',
                'provenancehash',
            ],
            'metadata' => 'privacy:metadata:uckkarchive_media_version',
        ],
        'uckkarchive_media_collection' => [
            'userfields' => ['userid', 'ownerid', 'createdby', 'modifiedby'],
            'textfields' => [
                'title',
                'name',
                'summary',
                'description',
                'purpose',
                'metadata',
                'provenancehash',
            ],
            'metadata' => 'privacy:metadata:uckkarchive_media_collection',
        ],
        'uckkarchive_media' => [
            'userfields' => ['userid', 'ownerid', 'createdby', 'modifiedby', 'validatedby'],
            'textfields' => [
                'title',
                'name',
                'summary',
                'description',
                'caption',
                'transcript',
                'source',
                'sourcetype',
                'sourceurl',
                'sourceauthor',
                'license',
                'rightsstatement',
                'sourcenote',
                'teachingnote',
                'culturalprotocolnote',
                'metadata',
                'provenancehash',
            ],
            'metadata' => 'privacy:metadata:uckkarchive_media',
        ],
        'uckkarchive_external_work' => [
            'userfields' => ['userid', 'ownerid', 'createdby', 'modifiedby'],
            'textfields' => [
                'title',
                'subtitle',
                'creator',
                'publisher',
                'sourceurl',
                'identifier',
                'citation',
                'rightsstatement',
                'licensekey',
                'sourcenote',
                'teachingnote',
                'culturalprotocolnote',
                'description',
                'metadata',
                'provenancehash',
            ],
            'metadata' => 'privacy:metadata:uckkarchive_external_work',
        ],
        'uckkarchive_export' => [
            'userfields' => ['userid', 'createdby', 'modifiedby', 'exportedby'],
            'textfields' => [
                'title',
                'summary',
                'description',
                'reason',
                'auditnote',
                'notes',
                'exportpath',
                'packagename',
                'metadata',
                'provenancehash',
            ],
            'metadata' => 'privacy:metadata:uckkarchive_export',
        ],
        'uckkarchive_rev' => [
            'userfields' => ['userid', 'createdby', 'modifiedby'],
            'textfields' => [
                'reason',
                'notes',
                'summary',
                'contentbefore',
                'contentafter',
                'metadata',
                'provenancehash',
            ],
            'metadata' => 'privacy:metadata:uckkarchive_rev',
        ],
        'uckkarchive_prov' => [
            'userfields' => ['userid', 'createdby', 'modifiedby', 'validatedby'],
            'textfields' => [
                'statement',
                'source',
                'sourceauthor',
                'sourceurl',
                'notes',
                'metadata',
                'provenancehash',
            ],
            'metadata' => 'privacy:metadata:uckkarchive_prov',
        ],
        'uckkarchive_proof' => [
            'userfields' => ['userid', 'createdby', 'modifiedby', 'validatedby'],
            'textfields' => [
                'title',
                'summary',
                'content',
                'description',
                'sourceauthor',
                'sourceurl',
                'notes',
                'metadata',
                'provenancehash',
            ],
            'metadata' => 'privacy:metadata:uckkarchive_proof',
        ],
        'uckkarchive_kristal' => [
            'userfields' => ['userid', 'createdby', 'modifiedby', 'validatedby'],
            'textfields' => [
                'title',
                'summary',
                'statement',
                'content',
                'contexttext',
                'proof',
                'notes',
                'metadata',
                'provenancehash',
            ],
            'metadata' => 'privacy:metadata:uckkarchive_kristal',
        ],
        'uckkarchive_item' => [
            'userfields' => ['userid', 'createdby', 'modifiedby', 'validatedby'],
            'textfields' => [
                'title',
                'summary',
                'content',
                'description',
                'notes',
                'sourceauthor',
                'sourceurl',
                'license',
                'tags',
                'metadata',
                'provenancehash',
            ],
            'metadata' => 'privacy:metadata:uckkarchive_item',
        ],
        'uckkarchive' => [
            'userfields' => ['userid', 'createdby', 'modifiedby'],
            'textfields' => [
                'name',
                'intro',
                'archivecontext',
                'archivepurpose',
                'metadata',
            ],
            'metadata' => 'privacy:metadata:uckkarchive',
        ],
    ];

    /**
     * Plugin file areas that can contain personal data.
     */
    private const FILE_AREAS = [
        'item_content',
        'proof_files',
        'decision_attachments',
        'minutes_files',
        'kristal_files',
        'portfolio_files',
        'integrity_exports',
        'export_packages',

        'media_original',
        'media_preview',
        'media_thumbnail',
        'media_derivative',
        'media_caption',
        'media_transcript',
        'media_attachment',

        'content_review_files',
        'external_work_reference_files',
        'cultural_protocol_files',

        'export_manifest',
        'export_package',
    ];

    /**
     * File areas associated with table records.
     */
    private const TABLE_FILE_AREAS = [
        'uckkarchive_item' => [
            'item_content',
            'proof_files',
            'decision_attachments',
            'minutes_files',
            'portfolio_files',
        ],
        'uckkarchive_kristal' => [
            'kristal_files',
        ],
        'uckkarchive_proof' => [
            'proof_files',
        ],
        'uckkarchive_export' => [
            'export_packages',
            'integrity_exports',
            'export_manifest',
            'export_package',
        ],
        'uckkarchive_media' => [
            'media_original',
            'media_preview',
            'media_thumbnail',
            'media_derivative',
            'media_caption',
            'media_transcript',
            'media_attachment',
        ],
        'uckkarchive_media_version' => [
            'media_original',
            'media_preview',
            'media_derivative',
            'media_caption',
            'media_transcript',
            'media_attachment',
        ],
        'uckkarchive_content_review' => [
            'content_review_files',
        ],
        'uckkarchive_content_marker' => [
            'cultural_protocol_files',
        ],
        'uckkarchive_external_work' => [
            'external_work_reference_files',
        ],
    ];

    /**
     * Describe personal data stored by this plugin.
     *
     * @param collection $collection Metadata collection.
     * @return collection
     */
    public static function get_metadata(collection $collection): collection {
        $commonfields = [
            'uuid' => 'privacy:metadata:common:uuid',
            'archiveid' => 'privacy:metadata:common:archiveid',
            'courseid' => 'privacy:metadata:common:courseid',
            'cmid' => 'privacy:metadata:common:cmid',
            'contextid' => 'privacy:metadata:common:contextid',
            'userid' => 'privacy:metadata:common:userid',
            'ownerid' => 'privacy:metadata:common:ownerid',
            'createdby' => 'privacy:metadata:common:createdby',
            'modifiedby' => 'privacy:metadata:common:modifiedby',
            'validatedby' => 'privacy:metadata:common:validatedby',
            'reviewerid' => 'privacy:metadata:common:reviewerid',
            'exportedby' => 'privacy:metadata:common:exportedby',
            'timecreated' => 'privacy:metadata:common:timecreated',
            'timemodified' => 'privacy:metadata:common:timemodified',
            'timevalidated' => 'privacy:metadata:common:timevalidated',
            'status' => 'privacy:metadata:common:status',
            'visibility' => 'privacy:metadata:common:visibility',
            'metadata' => 'privacy:metadata:common:metadata',
            'provenancehash' => 'privacy:metadata:common:provenancehash',
        ];

        $tablefields = [
            'uckkarchive' => [
                'name' => 'privacy:metadata:uckkarchive:name',
                'intro' => 'privacy:metadata:uckkarchive:intro',
                'archivecontext' => 'privacy:metadata:uckkarchive:archivecontext',
                'archivepurpose' => 'privacy:metadata:uckkarchive:archivepurpose',
            ],
            'uckkarchive_item' => [
                'title' => 'privacy:metadata:uckkarchive_item:title',
                'summary' => 'privacy:metadata:uckkarchive_item:summary',
                'content' => 'privacy:metadata:uckkarchive_item:content',
                'itemtype' => 'privacy:metadata:uckkarchive_item:itemtype',
                'sourcecomponent' => 'privacy:metadata:uckkarchive_item:sourcecomponent',
                'sourceid' => 'privacy:metadata:uckkarchive_item:sourceid',
                'sourceurl' => 'privacy:metadata:uckkarchive_item:sourceurl',
                'sourceauthor' => 'privacy:metadata:uckkarchive_item:sourceauthor',
                'sourcedate' => 'privacy:metadata:uckkarchive_item:sourcedate',
            ],
            'uckkarchive_kristal' => [
                'title' => 'privacy:metadata:uckkarchive_kristal:title',
                'statement' => 'privacy:metadata:uckkarchive_kristal:statement',
                'content' => 'privacy:metadata:uckkarchive_kristal:content',
                'contexttext' => 'privacy:metadata:uckkarchive_kristal:contexttext',
                'proof' => 'privacy:metadata:uckkarchive_kristal:proof',
            ],
            'uckkarchive_proof' => [
                'title' => 'privacy:metadata:uckkarchive_proof:title',
                'summary' => 'privacy:metadata:uckkarchive_proof:summary',
                'content' => 'privacy:metadata:uckkarchive_proof:content',
                'description' => 'privacy:metadata:uckkarchive_proof:description',
                'sourceurl' => 'privacy:metadata:uckkarchive_proof:sourceurl',
            ],
            'uckkarchive_prov' => [
                'statement' => 'privacy:metadata:uckkarchive_prov:statement',
                'source' => 'privacy:metadata:uckkarchive_prov:source',
                'sourceurl' => 'privacy:metadata:uckkarchive_prov:sourceurl',
            ],
            'uckkarchive_rev' => [
                'reason' => 'privacy:metadata:uckkarchive_rev:reason',
                'contentbefore' => 'privacy:metadata:uckkarchive_rev:contentbefore',
                'contentafter' => 'privacy:metadata:uckkarchive_rev:contentafter',
            ],
            'uckkarchive_export' => [
                'exportformat' => 'privacy:metadata:uckkarchive_export:exportformat',
                'exportscope' => 'privacy:metadata:uckkarchive_export:exportscope',
                'reason' => 'privacy:metadata:uckkarchive_export:reason',
                'exportpath' => 'privacy:metadata:uckkarchive_export:exportpath',
                'packagename' => 'privacy:metadata:uckkarchive_export:packagename',
            ],
            'uckkarchive_media' => [
                'title' => 'privacy:metadata:uckkarchive_media:title',
                'summary' => 'privacy:metadata:uckkarchive_media:summary',
                'description' => 'privacy:metadata:uckkarchive_media:description',
                'mediatype' => 'privacy:metadata:uckkarchive_media:mediatype',
                'mimetype' => 'privacy:metadata:uckkarchive_media:mimetype',
                'sourceurl' => 'privacy:metadata:uckkarchive_media:sourceurl',
                'caption' => 'privacy:metadata:uckkarchive_media:caption',
                'transcript' => 'privacy:metadata:uckkarchive_media:transcript',
            ],
            'uckkarchive_media_version' => [
                'label' => 'privacy:metadata:uckkarchive_media_version:label',
                'filename' => 'privacy:metadata:uckkarchive_media_version:filename',
                'contenthash' => 'privacy:metadata:uckkarchive_media_version:contenthash',
                'changecomment' => 'privacy:metadata:uckkarchive_media_version:changecomment',
            ],
            'uckkarchive_media_source' => [
                'source' => 'privacy:metadata:uckkarchive_media_source:source',
                'sourceurl' => 'privacy:metadata:uckkarchive_media_source:sourceurl',
                'citation' => 'privacy:metadata:uckkarchive_media_source:citation',
                'rightsstatement' => 'privacy:metadata:uckkarchive_media_source:rightsstatement',
            ],
            'uckkarchive_media_collection' => [
                'title' => 'privacy:metadata:uckkarchive_media_collection:title',
                'summary' => 'privacy:metadata:uckkarchive_media_collection:summary',
                'description' => 'privacy:metadata:uckkarchive_media_collection:description',
            ],
            'uckkarchive_media_collection_item' => [
                'note' => 'privacy:metadata:uckkarchive_media_collection_item:note',
            ],
            'uckkarchive_media_relation' => [
                'relationtype' => 'privacy:metadata:uckkarchive_media_relation:relationtype',
                'description' => 'privacy:metadata:uckkarchive_media_relation:description',
            ],
            'uckkarchive_media_tag' => [
                'tag' => 'privacy:metadata:uckkarchive_media_tag:tag',
                'tagkey' => 'privacy:metadata:uckkarchive_media_tag:tagkey',
            ],
            'uckkarchive_content_tag' => [
                'tagkey' => 'privacy:metadata:uckkarchive_content_tag:tagkey',
                'label' => 'privacy:metadata:uckkarchive_content_tag:label',
                'description' => 'privacy:metadata:uckkarchive_content_tag:description',
            ],
            'uckkarchive_content_tag_set' => [
                'tagsetkey' => 'privacy:metadata:uckkarchive_content_tag_set:tagsetkey',
                'label' => 'privacy:metadata:uckkarchive_content_tag_set:label',
                'description' => 'privacy:metadata:uckkarchive_content_tag_set:description',
            ],
            'uckkarchive_content_marker' => [
                'tagkey' => 'privacy:metadata:uckkarchive_content_marker:tagkey',
                'severity' => 'privacy:metadata:uckkarchive_content_marker:severity',
                'audiencesuitability' => 'privacy:metadata:uckkarchive_content_marker:audiencesuitability',
                'locator' => 'privacy:metadata:uckkarchive_content_marker:locator',
                'description' => 'privacy:metadata:uckkarchive_content_marker:description',
                'note' => 'privacy:metadata:uckkarchive_content_marker:note',
            ],
            'uckkarchive_content_review' => [
                'state' => 'privacy:metadata:uckkarchive_content_review:state',
                'severity' => 'privacy:metadata:uckkarchive_content_review:severity',
                'audiencesuitability' => 'privacy:metadata:uckkarchive_content_review:audiencesuitability',
                'rationale' => 'privacy:metadata:uckkarchive_content_review:rationale',
                'reviewnote' => 'privacy:metadata:uckkarchive_content_review:reviewnote',
            ],
            'uckkarchive_external_work' => [
                'title' => 'privacy:metadata:uckkarchive_external_work:title',
                'subtitle' => 'privacy:metadata:uckkarchive_external_work:subtitle',
                'creator' => 'privacy:metadata:uckkarchive_external_work:creator',
                'publisher' => 'privacy:metadata:uckkarchive_external_work:publisher',
                'sourceurl' => 'privacy:metadata:uckkarchive_external_work:sourceurl',
                'identifier' => 'privacy:metadata:uckkarchive_external_work:identifier',
                'citation' => 'privacy:metadata:uckkarchive_external_work:citation',
                'rightsstatement' => 'privacy:metadata:uckkarchive_external_work:rightsstatement',
                'description' => 'privacy:metadata:uckkarchive_external_work:description',
            ],
        ];

        foreach (self::TABLES as $table => $config) {
            $fields = $commonfields + ($tablefields[$table] ?? []);

            $collection->add_database_table(
                $table,
                $fields,
                $config['metadata']
            );
        }

        $collection->add_subsystem_link('core_files', [], 'privacy:metadata:files');

        return $collection;
    }

    /**
     * Get contexts containing personal data for a user.
     *
     * @param int $userid User id.
     * @return contextlist
     */
    public static function get_contexts_for_userid(int $userid): contextlist {
        $contextlist = new contextlist();

        foreach (self::TABLES as $table => $config) {
            if (!self::table_exists($table)) {
                continue;
            }

            $conditions = [];
            $params = [];

            foreach ($config['userfields'] as $field) {
                if (!self::field_exists($table, $field)) {
                    continue;
                }

                $param = $table . '_' . $field;
                $conditions[] = "t.{$field} = :{$param}";
                $params[$param] = $userid;
            }

            if (!$conditions) {
                continue;
            }

            $sql = self::get_contexts_sql_for_table($table, implode(' OR ', $conditions));

            if ($sql === '') {
                continue;
            }

            $contextlist->add_from_sql($sql, $params);
        }

        return $contextlist;
    }

    /**
     * Export personal data for approved contexts.
     *
     * @param approved_contextlist $contextlist Approved context list.
     */
    public static function export_user_data(approved_contextlist $contextlist): void {
        $user = $contextlist->get_user();

        foreach ($contextlist->get_contexts() as $context) {
            $export = new stdClass();

            foreach (array_keys(self::TABLES) as $table) {
                $records = self::get_user_records_in_context($table, (int)$user->id, $context);

                if (!$records) {
                    continue;
                }

                $export->{$table} = array_map([self::class, 'prepare_record_for_export'], $records);
            }

            $subcontext = [get_string('privacy:path:archives', 'uckkarchive')];

            writer::with_context($context)->export_data($subcontext, $export);
            self::export_user_files($context, (int)$user->id, $subcontext);
        }
    }

    /**
     * Delete all personal archive data in a context.
     *
     * This is used when the context itself is being expired/deleted. It removes
     * plugin child records and file areas in the context. The activity instance
     * shell is not deleted here because Moodle owns that lifecycle.
     *
     * @param context $context Context.
     */
    public static function delete_data_for_all_users_in_context(context $context): void {
        global $DB;

        self::delete_all_archive_files_in_context($context);

        foreach (array_keys(self::TABLES) as $table) {
            if (!self::table_exists($table)) {
                continue;
            }

            [$select, $params] = self::get_context_select_for_table($table, $context);

            if ($select === '') {
                continue;
            }

            if ($table === 'uckkarchive') {
                self::anonymise_all_user_references_in_context($table, $select, $params);
                continue;
            }

            $DB->delete_records_select($table, $select, $params);
        }
    }

    /**
     * Delete personal data for one user in approved contexts.
     *
     * @param approved_contextlist $contextlist Approved context list.
     */
    public static function delete_data_for_user(approved_contextlist $contextlist): void {
        $user = $contextlist->get_user();

        foreach ($contextlist->get_contexts() as $context) {
            self::delete_user_data_in_context((int)$user->id, $context);
        }
    }

    /**
     * Add users with archive personal data in a context.
     *
     * @param userlist $userlist Userlist.
     */
    public static function get_users_in_context(userlist $userlist): void {
        $context = $userlist->get_context();

        foreach (self::TABLES as $table => $config) {
            if (!self::table_exists($table)) {
                continue;
            }

            [$contextselect, $contextparams] = self::get_context_select_for_table($table, $context);

            if ($contextselect === '') {
                continue;
            }

            foreach ($config['userfields'] as $field) {
                if (!self::field_exists($table, $field)) {
                    continue;
                }

                $sql = "SELECT {$field}
                          FROM {{$table}}
                         WHERE {$contextselect}
                           AND {$field} <> 0";

                $userlist->add_from_sql($field, $sql, $contextparams);
            }
        }
    }

    /**
     * Delete personal data for multiple users in a context.
     *
     * @param approved_userlist $userlist Approved userlist.
     */
    public static function delete_data_for_users(approved_userlist $userlist): void {
        $context = $userlist->get_context();

        foreach ($userlist->get_userids() as $userid) {
            self::delete_user_data_in_context((int)$userid, $context);
        }
    }

    /**
     * Export files attached to user-owned records.
     *
     * @param context $context Context.
     * @param int $userid User id.
     * @param array<int, string> $subcontext Subcontext.
     */
    private static function export_user_files(context $context, int $userid, array $subcontext): void {
        foreach (array_keys(self::TABLE_FILE_AREAS) as $table) {
            $records = self::get_user_records_in_context($table, $userid, $context);

            foreach ($records as $record) {
                if (empty($record->id)) {
                    continue;
                }

                foreach (self::get_file_areas_for_table($table) as $filearea) {
                    writer::with_context($context)->export_area_files(
                        array_merge($subcontext, [$table, (string)$record->id, $filearea]),
                        self::COMPONENT,
                        $filearea,
                        (int)$record->id
                    );
                }
            }
        }
    }

    /**
     * Delete or anonymise one user's archive data in a context.
     *
     * @param int $userid User id.
     * @param context $context Context.
     */
    private static function delete_user_data_in_context(int $userid, context $context): void {
        global $DB;

        foreach (self::TABLES as $table => $config) {
            if (!self::table_exists($table)) {
                continue;
            }

            [$select, $params] = self::get_user_select_for_context($table, $config['userfields'], $userid, $context);

            if ($select === '') {
                continue;
            }

            $records = $DB->get_records_select($table, $select, $params);

            if (!$records) {
                continue;
            }

            self::delete_files_for_records($context, $table, $records);
            self::anonymise_records($table, $config, $select, $params);
        }
    }

    /**
     * Build SQL selection for one user in one context.
     *
     * @param string $table Table name.
     * @param array<int, string> $userfields User id fields.
     * @param int $userid User id.
     * @param context $context Context.
     * @return array{0:string,1:array<string,mixed>}
     */
    private static function get_user_select_for_context(
        string $table,
        array $userfields,
        int $userid,
        context $context
    ): array {
        [$contextselect, $params] = self::get_context_select_for_table($table, $context);

        if ($contextselect === '') {
            return ['', []];
        }

        $conditions = [];

        foreach ($userfields as $field) {
            if (!self::field_exists($table, $field)) {
                continue;
            }

            $param = 'userid_' . $field;
            $conditions[] = "{$field} = :{$param}";
            $params[$param] = $userid;
        }

        if (!$conditions) {
            return ['', []];
        }

        return [
            $contextselect . ' AND (' . implode(' OR ', $conditions) . ')',
            $params,
        ];
    }

    /**
     * Get user-owned records in a context.
     *
     * @param string $table Table name.
     * @param int $userid User id.
     * @param context $context Context.
     * @return array<int, stdClass>
     */
    private static function get_user_records_in_context(string $table, int $userid, context $context): array {
        global $DB;

        if (!self::table_exists($table)) {
            return [];
        }

        $config = self::TABLES[$table] ?? null;

        if ($config === null) {
            return [];
        }

        [$select, $params] = self::get_user_select_for_context($table, $config['userfields'], $userid, $context);

        if ($select === '') {
            return [];
        }

        return $DB->get_records_select($table, $select, $params, 'id ASC');
    }

    /**
     * Prepare a record for privacy export.
     *
     * @param stdClass $record Record.
     * @return stdClass
     */
    private static function prepare_record_for_export(stdClass $record): stdClass {
        $data = clone $record;

        foreach ([
            'timecreated',
            'timemodified',
            'timevalidated',
            'sourcedate',
            'timequeued',
            'timestarted',
            'timecompleted',
            'lastdownloaded',
        ] as $field) {
            if (!empty($data->{$field})) {
                $data->{$field . 'readable'} = userdate((int)$data->{$field});
            }
        }

        return $data;
    }

    /**
     * Anonymise records matched by a select statement.
     *
     * @param string $table Table name.
     * @param array<string, mixed> $config Table config.
     * @param string $select SQL select.
     * @param array<string, mixed> $params SQL params.
     */
    private static function anonymise_records(string $table, array $config, string $select, array $params): void {
        global $DB;

        foreach ($config['userfields'] as $field) {
            if (self::field_exists($table, $field)) {
                $DB->set_field_select($table, $field, 0, $select, $params);
            }
        }

        foreach ($config['textfields'] as $field) {
            if (!self::field_exists($table, $field)) {
                continue;
            }

            $value = self::redacted_value_for_field($field);
            $DB->set_field_select($table, $field, $value, $select, $params);
        }

        if (self::field_exists($table, 'timemodified')) {
            $DB->set_field_select($table, 'timemodified', time(), $select, $params);
        }
    }

    /**
     * Anonymise all user references in records matching a context selection.
     *
     * Used for the activity instance table during context deletion. Moodle owns
     * the module instance lifecycle, so this privacy provider must not delete
     * the instance record itself.
     *
     * @param string $table Table name.
     * @param string $select SQL select.
     * @param array<string, mixed> $params SQL params.
     */
    private static function anonymise_all_user_references_in_context(string $table, string $select, array $params): void {
        global $DB;

        if (!isset(self::TABLES[$table])) {
            return;
        }

        foreach (self::TABLES[$table]['userfields'] as $field) {
            if (self::field_exists($table, $field)) {
                $DB->set_field_select($table, $field, 0, $select, $params);
            }
        }

        foreach (self::TABLES[$table]['textfields'] as $field) {
            if (!self::field_exists($table, $field)) {
                continue;
            }

            if ($field === 'metadata') {
                $DB->set_field_select($table, $field, '{}', $select, $params);
            }
        }

        if (self::field_exists($table, 'timemodified')) {
            $DB->set_field_select($table, 'timemodified', time(), $select, $params);
        }
    }

    /**
     * Delete files for matching records.
     *
     * @param context $context Context.
     * @param string $table Table name.
     * @param array<int, stdClass> $records Records.
     */
    private static function delete_files_for_records(context $context, string $table, array $records): void {
        $fs = get_file_storage();

        foreach ($records as $record) {
            if (empty($record->id)) {
                continue;
            }

            foreach (self::get_file_areas_for_table($table) as $filearea) {
                $fs->delete_area_files($context->id, self::COMPONENT, $filearea, (int)$record->id);
            }
        }
    }

    /**
     * Delete all archive files in a context.
     *
     * @param context $context Context.
     */
    private static function delete_all_archive_files_in_context(context $context): void {
        $fs = get_file_storage();

        foreach (self::FILE_AREAS as $filearea) {
            $fs->delete_area_files($context->id, self::COMPONENT, $filearea);
        }
    }

    /**
     * Get file areas associated with a table.
     *
     * @param string $table Table name.
     * @return array<int, string>
     */
    private static function get_file_areas_for_table(string $table): array {
        return self::TABLE_FILE_AREAS[$table] ?? [];
    }

    /**
     * Build SQL that returns context ids for a table/user condition.
     *
     * @param string $table Table name.
     * @param string $usercondition User condition using alias t.
     * @return string SQL.
     */
    private static function get_contexts_sql_for_table(string $table, string $usercondition): string {
        if (self::field_exists($table, 'contextid')) {
            return "SELECT DISTINCT ctx.id
                      FROM {context} ctx
                      JOIN {{$table}} t ON t.contextid = ctx.id
                     WHERE {$usercondition}";
        }

        if (self::field_exists($table, 'archiveid') &&
                self::table_exists('uckkarchive') &&
                self::field_exists('uckkarchive', 'contextid')) {
            return "SELECT DISTINCT ctx.id
                      FROM {context} ctx
                      JOIN {uckkarchive} a ON a.contextid = ctx.id
                      JOIN {{$table}} t ON t.archiveid = a.id
                     WHERE {$usercondition}";
        }

        return '';
    }

    /**
     * Build a context filter for a table.
     *
     * @param string $table Table name.
     * @param context $context Context.
     * @return array{0:string,1:array<string,mixed>}
     */
    private static function get_context_select_for_table(string $table, context $context): array {
        if (self::field_exists($table, 'contextid')) {
            return [
                'contextid = :contextid',
                ['contextid' => $context->id],
            ];
        }

        if (self::field_exists($table, 'archiveid') &&
                self::table_exists('uckkarchive') &&
                self::field_exists('uckkarchive', 'contextid')) {
            return [
                'archiveid IN (SELECT id FROM {uckkarchive} WHERE contextid = :contextid)',
                ['contextid' => $context->id],
            ];
        }

        return ['', []];
    }

    /**
     * Get redacted value for a field.
     *
     * @param string $field Field name.
     * @return string
     */
    private static function redacted_value_for_field(string $field): string {
        if ($field === 'metadata') {
            return '{}';
        }

        if ($field === 'provenancehash') {
            return '';
        }

        return get_string('privacy:deleted', 'uckkarchive');
    }

    /**
     * Check whether a database table exists.
     *
     * @param string $table Table name without prefix.
     * @return bool
     */
    private static function table_exists(string $table): bool {
        global $DB;

        return $DB->get_manager()->table_exists(new xmldb_table($table));
    }

    /**
     * Check whether a database field exists.
     *
     * @param string $table Table name without prefix.
     * @param string $field Field name.
     * @return bool
     */
    private static function field_exists(string $table, string $field): bool {
        global $DB;

        if (!self::table_exists($table)) {
            return false;
        }

        return $DB->get_manager()->field_exists(new xmldb_table($table), new xmldb_field($field));
    }
}