<?php
// This file is part of Moodle - https://moodle.org/.
//
// Moodle is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// any later version.

/**
 * External service for reading one media collection.
 *
 * @package    mod_uckkarchive
 * @copyright  2026 UCKK
 * @license    http://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later
 */

declare(strict_types=1);

namespace mod_uckkarchive\external;

defined('MOODLE_INTERNAL') || die();

global $CFG;
require_once($CFG->libdir . '/externallib.php');
require_once(dirname(__DIR__, 2) . '/locallib.php');
require_once(dirname(__DIR__) . '/local/media_collection.php');
require_once(dirname(__DIR__) . '/local/media_policy.php');

use context_module;
use core_external\external_api;
use core_external\external_function_parameters;
use core_external\external_multiple_structure;
use core_external\external_single_structure;
use core_external\external_value;
use invalid_parameter_exception;
use mod_uckkarchive\local\media_collection;
use mod_uckkarchive\local\media_policy;
use moodle_exception;
use stdClass;

/**
 * Return one permission-filtered media collection.
 *
 * Target service name:
 *
 * ```text
 * mod_uckkarchive_get_media_collection
 * ```
 *
 * This service reads a collection and its member media. It does not expose
 * unrestricted files, raw restricted notes, or unfiltered advisory data.
 */
final class get_media_collection extends external_api {
    /** Collection table. */
    private const TABLE_COLLECTION = 'uckkarchive_media_collection';

    /** Collection membership table. */
    private const TABLE_ITEM = 'uckkarchive_media_collection_item';

    /** Media table. */
    private const TABLE_MEDIA = 'uckkarchive_media';

    /** Default page size. */
    private const DEFAULT_PERPAGE = 50;

    /** Maximum page size. */
    private const MAX_PERPAGE = 100;

    /**
     * Define service parameters.
     *
     * @return external_function_parameters
     */
    public static function execute_parameters(): external_function_parameters {
        return new external_function_parameters([
            'cmid' => new external_value(PARAM_INT, 'Course module id'),
            'collectionid' => new external_value(PARAM_INT, 'Media collection id'),
            'page' => new external_value(PARAM_INT, 'Zero-based page number', VALUE_DEFAULT, 0),
            'perpage' => new external_value(PARAM_INT, 'Items per page', VALUE_DEFAULT, self::DEFAULT_PERPAGE),
            'include' => new external_multiple_structure(
                new external_value(PARAM_ALPHANUMEXT, 'Include value'),
                'Optional include values: media, permissions, counts',
                VALUE_DEFAULT,
                ['media', 'permissions', 'counts']
            ),
        ]);
    }

    /**
     * Execute service.
     *
     * @param int $cmid Course module id.
     * @param int $collectionid Collection id.
     * @param int $page Zero-based page number.
     * @param int $perpage Items per page.
     * @param string[] $include Include values.
     * @return array<string, mixed>
     */
    public static function execute(
        int $cmid,
        int $collectionid,
        int $page = 0,
        int $perpage = self::DEFAULT_PERPAGE,
        array $include = ['media', 'permissions', 'counts']
    ): array {
        global $DB;

        $params = self::validate_parameters(self::execute_parameters(), [
            'cmid' => $cmid,
            'collectionid' => $collectionid,
            'page' => $page,
            'perpage' => $perpage,
            'include' => $include,
        ]);

        [$course, $cm, $archive, $context] = self::load_page((int)$params['cmid']);
        self::validate_context($context);

        require_capability('mod/uckkarchive:viewmedia', $context);

        $collectionid = self::require_positive_int((int)$params['collectionid'], 'collectionid');
        $page = max(0, (int)$params['page']);
        $perpage = min(self::MAX_PERPAGE, max(1, (int)$params['perpage']));
        $include = self::normalise_include((array)$params['include']);

        if (!self::table_exists(self::TABLE_COLLECTION)) {
            throw new moodle_exception('invalidmediacollection', 'mod_uckkarchive');
        }

        $collection = media_collection::get($collectionid, MUST_EXIST);
        self::require_collection_belongs_to_archive($collection, (int)$archive->id);

        if (!media_policy::can_view_collection($context, $collection)) {
            throw new moodle_exception('nopermissiontoviewmediacollection', 'mod_uckkarchive');
        }

        if (self::is_deleted_collection($collection) &&
                !has_capability('mod/uckkarchive:managemediacollections', $context)) {
            throw new moodle_exception('nopermissiontoviewmediacollection', 'mod_uckkarchive');
        }

        $warnings = [];
        $allmedia = [];
        $visiblemedia = [];

        if (in_array('media', $include, true) && self::table_exists(self::TABLE_ITEM) &&
                self::table_exists(self::TABLE_MEDIA)) {
            $allmedia = array_values(media_collection::get_media($collectionid, 0, 0));

            foreach ($allmedia as $media) {
                if (!media_policy::can_view_media($context, $media)) {
                    continue;
                }

                $visiblemedia[] = self::export_media_summary($media, $context);
            }
        }

        $total = count($visiblemedia);
        $pagedmedia = array_slice($visiblemedia, $page * $perpage, $perpage);

        return [
            'collection' => self::export_collection($collection, $context, count($visiblemedia)),
            'media' => $pagedmedia,
            'pagination' => [
                'page' => $page,
                'perpage' => $perpage,
                'total' => $total,
                'returned' => count($pagedmedia),
                'hasmore' => (($page + 1) * $perpage) < $total,
            ],
            'permissions' => self::get_permissions($context, $collection),
            'warnings' => $warnings,
        ];
    }

    /**
     * Define service return structure.
     *
     * @return external_single_structure
     */
    public static function execute_returns(): external_single_structure {
        return new external_single_structure([
            'collection' => self::collection_structure(),
            'media' => new external_multiple_structure(self::media_structure(), 'Permission-filtered collection media'),
            'pagination' => new external_single_structure([
                'page' => new external_value(PARAM_INT, 'Current zero-based page'),
                'perpage' => new external_value(PARAM_INT, 'Items per page'),
                'total' => new external_value(PARAM_INT, 'Visible media count'),
                'returned' => new external_value(PARAM_INT, 'Returned media count'),
                'hasmore' => new external_value(PARAM_BOOL, 'Whether more visible media exists'),
            ]),
            'permissions' => self::permissions_structure(),
            'warnings' => self::warnings_structure(),
        ]);
    }

    /**
     * Return collection structure.
     *
     * @return external_single_structure
     */
    private static function collection_structure(): external_single_structure {
        return new external_single_structure([
            'id' => new external_value(PARAM_INT, 'Collection id'),
            'uuid' => new external_value(PARAM_TEXT, 'Collection UUID'),
            'archiveid' => new external_value(PARAM_INT, 'Archive instance id'),
            'title' => new external_value(PARAM_TEXT, 'Collection title'),
            'description' => new external_value(PARAM_RAW, 'Permission-filtered description'),
            'purpose' => new external_value(PARAM_ALPHANUMEXT, 'Collection purpose'),
            'status' => new external_value(PARAM_ALPHANUMEXT, 'Collection status'),
            'visibility' => new external_value(PARAM_ALPHANUMEXT, 'Collection visibility'),
            'ownerid' => new external_value(PARAM_INT, 'Owner user id'),
            'createdby' => new external_value(PARAM_INT, 'Creator user id'),
            'modifiedby' => new external_value(PARAM_INT, 'Modifier user id'),
            'timecreated' => new external_value(PARAM_INT, 'Time created'),
            'timemodified' => new external_value(PARAM_INT, 'Time modified'),
            'isrestricted' => new external_value(PARAM_BOOL, 'Restricted collection'),
            'isculturalrestricted' => new external_value(PARAM_BOOL, 'Culturally restricted collection'),
            'mediacount' => new external_value(PARAM_INT, 'Visible media count'),
        ]);
    }

    /**
     * Return media summary structure.
     *
     * @return external_single_structure
     */
    private static function media_structure(): external_single_structure {
        return new external_single_structure([
            'id' => new external_value(PARAM_INT, 'Media id'),
            'uuid' => new external_value(PARAM_TEXT, 'Media UUID'),
            'title' => new external_value(PARAM_TEXT, 'Media title'),
            'mediatype' => new external_value(PARAM_ALPHANUMEXT, 'Media type'),
            'mimetype' => new external_value(PARAM_TEXT, 'MIME type'),
            'status' => new external_value(PARAM_ALPHANUMEXT, 'Media status'),
            'visibility' => new external_value(PARAM_ALPHANUMEXT, 'Media visibility'),
            'source' => new external_value(PARAM_ALPHANUMEXT, 'Source type'),
            'sortorder' => new external_value(PARAM_INT, 'Collection sort order'),
            'timecreated' => new external_value(PARAM_INT, 'Time created'),
            'timemodified' => new external_value(PARAM_INT, 'Time modified'),
            'isrestricted' => new external_value(PARAM_BOOL, 'Restricted media'),
            'isculturalrestricted' => new external_value(PARAM_BOOL, 'Culturally restricted media'),
        ]);
    }

    /**
     * Return permissions structure.
     *
     * @return external_single_structure
     */
    private static function permissions_structure(): external_single_structure {
        return new external_single_structure([
            'viewmedia' => new external_value(PARAM_BOOL, 'Can view media'),
            'addmedia' => new external_value(PARAM_BOOL, 'Can add media'),
            'editmedia' => new external_value(PARAM_BOOL, 'Can edit media'),
            'downloadmedia' => new external_value(PARAM_BOOL, 'Can download media'),
            'managemediacollections' => new external_value(PARAM_BOOL, 'Can manage media collections'),
            'exportmedia' => new external_value(PARAM_BOOL, 'Can export media'),
            'viewrestrictedmedia' => new external_value(PARAM_BOOL, 'Can view restricted media'),
            'viewculturallyrestricted' => new external_value(PARAM_BOOL, 'Can view culturally restricted material'),
        ]);
    }

    /**
     * Return warnings structure.
     *
     * @return external_multiple_structure
     */
    private static function warnings_structure(): external_multiple_structure {
        return new external_multiple_structure(new external_single_structure([
            'item' => new external_value(PARAM_TEXT, 'Warning item'),
            'itemid' => new external_value(PARAM_INT, 'Warning item id'),
            'warningcode' => new external_value(PARAM_ALPHANUMEXT, 'Warning code'),
            'message' => new external_value(PARAM_TEXT, 'Warning message'),
        ]));
    }

    /**
     * Load Moodle page records.
     *
     * @param int $cmid Course module id.
     * @return array{0:stdClass,1:stdClass,2:stdClass,3:context_module}
     */
    private static function load_page(int $cmid): array {
        [$course, $cm, $archive, $context] = \uckkarchive_require_page($cmid, 0);

        return [$course, $cm, $archive, $context];
    }

    /**
     * Export a collection record.
     *
     * @param stdClass $collection Collection record.
     * @param context_module $context Context.
     * @param int $visiblecount Visible media count.
     * @return array<string, mixed>
     */
    private static function export_collection(stdClass $collection, context_module $context, int $visiblecount): array {
        $description = (string)self::field($collection, ['description', 'summary'], '');

        if (self::is_restricted_collection($collection) && !self::can_view_restricted_collection($context, $collection)) {
            $description = '';
        }

        return [
            'id' => (int)$collection->id,
            'uuid' => (string)self::field($collection, ['uuid'], ''),
            'archiveid' => (int)self::field($collection, ['archiveid', 'uckkarchiveid'], 0),
            'title' => format_string((string)self::field($collection, ['title', 'name'], '')),
            'description' => format_text($description, FORMAT_HTML, ['para' => false]),
            'purpose' => (string)self::field($collection, ['purpose', 'collectiontype'], ''),
            'status' => (string)self::field($collection, ['status'], 'draft'),
            'visibility' => (string)self::field($collection, ['visibility'], 'restricted'),
            'ownerid' => (int)self::field($collection, ['ownerid', 'userid', 'createdby'], 0),
            'createdby' => (int)self::field($collection, ['createdby', 'userid', 'ownerid'], 0),
            'modifiedby' => (int)self::field($collection, ['modifiedby'], 0),
            'timecreated' => (int)self::field($collection, ['timecreated'], 0),
            'timemodified' => (int)self::field($collection, ['timemodified'], 0),
            'isrestricted' => self::is_restricted_collection($collection),
            'isculturalrestricted' => self::is_culturally_restricted_collection($collection),
            'mediacount' => $visiblecount,
        ];
    }

    /**
     * Export media summary.
     *
     * @param stdClass $media Media record with collection membership fields.
     * @param context_module $context Context.
     * @return array<string, mixed>
     */
    private static function export_media_summary(stdClass $media, context_module $context): array {
        return [
            'id' => (int)$media->id,
            'uuid' => (string)self::field($media, ['uuid'], ''),
            'title' => format_string((string)self::field($media, ['title', 'name'], '')),
            'mediatype' => (string)self::field($media, ['mediatype', 'type'], ''),
            'mimetype' => (string)self::field($media, ['mimetype', 'mime'], ''),
            'status' => (string)self::field($media, ['status'], 'draft'),
            'visibility' => (string)self::field($media, ['visibility'], 'restricted'),
            'source' => (string)self::field($media, ['source', 'sourcetype'], ''),
            'sortorder' => (int)self::field($media, ['sortorder'], 0),
            'timecreated' => (int)self::field($media, ['timecreated'], 0),
            'timemodified' => (int)self::field($media, ['timemodified'], 0),
            'isrestricted' => media_policy::is_restricted_media($media),
            'isculturalrestricted' => media_policy::is_culturally_restricted($media),
        ];
    }

    /**
     * Get permission summary.
     *
     * @param context_module $context Context.
     * @param stdClass $collection Collection record.
     * @return array<string, bool>
     */
    private static function get_permissions(context_module $context, stdClass $collection): array {
        return [
            'viewmedia' => has_capability('mod/uckkarchive:viewmedia', $context),
            'addmedia' => has_capability('mod/uckkarchive:addmedia', $context),
            'editmedia' => has_capability('mod/uckkarchive:editmedia', $context),
            'downloadmedia' => has_capability('mod/uckkarchive:downloadmedia', $context),
            'managemediacollections' => has_capability('mod/uckkarchive:managemediacollections', $context),
            'exportmedia' => has_capability('mod/uckkarchive:exportmedia', $context),
            'viewrestrictedmedia' => has_capability('mod/uckkarchive:viewrestrictedmedia', $context),
            'viewculturallyrestricted' => has_capability('mod/uckkarchive:viewculturallyrestricted', $context),
        ];
    }

    /**
     * Require collection belongs to the current archive instance.
     *
     * @param stdClass $collection Collection record.
     * @param int $archiveid Archive id.
     * @return void
     */
    private static function require_collection_belongs_to_archive(stdClass $collection, int $archiveid): void {
        $collectionarchiveid = (int)self::field($collection, ['archiveid', 'uckkarchiveid'], 0);

        if ($collectionarchiveid !== $archiveid) {
            throw new moodle_exception('invalidmediacollection', 'mod_uckkarchive');
        }
    }

    /**
     * Return whether collection is deleted.
     *
     * @param stdClass $collection Collection record.
     * @return bool
     */
    private static function is_deleted_collection(stdClass $collection): bool {
        return (string)self::field($collection, ['status'], '') === 'deleted_soft';
    }

    /**
     * Return whether collection is restricted.
     *
     * @param stdClass $collection Collection record.
     * @return bool
     */
    private static function is_restricted_collection(stdClass $collection): bool {
        $status = (string)self::field($collection, ['status'], '');
        $visibility = (string)self::field($collection, ['visibility'], '');

        return $status === 'restricted' ||
            in_array($visibility, ['restricted', 'restricted_integrity', 'restricted_cultural'], true) ||
            !empty($collection->restricted);
    }

    /**
     * Return whether collection is culturally restricted.
     *
     * @param stdClass $collection Collection record.
     * @return bool
     */
    private static function is_culturally_restricted_collection(stdClass $collection): bool {
        $visibility = (string)self::field($collection, ['visibility'], '');

        return $visibility === 'restricted_cultural' || !empty($collection->culturalprotocol);
    }

    /**
     * Return whether user can see restricted collection details.
     *
     * @param context_module $context Context.
     * @param stdClass $collection Collection.
     * @return bool
     */
    private static function can_view_restricted_collection(context_module $context, stdClass $collection): bool {
        if (has_capability('mod/uckkarchive:viewrestrictedmedia', $context) ||
                has_capability('mod/uckkarchive:viewrestricted', $context)) {
            return true;
        }

        if (self::is_culturally_restricted_collection($collection)) {
            return has_capability('mod/uckkarchive:viewculturallyrestricted', $context);
        }

        return false;
    }

    /**
     * Normalize include values.
     *
     * @param string[] $include Include values.
     * @return string[]
     */
    private static function normalise_include(array $include): array {
        $allowed = ['media', 'permissions', 'counts'];
        $clean = [];

        foreach ($include as $value) {
            $value = clean_param((string)$value, PARAM_ALPHANUMEXT);
            if (in_array($value, $allowed, true)) {
                $clean[] = $value;
            }
        }

        if (empty($clean)) {
            $clean = ['media', 'permissions', 'counts'];
        }

        return array_values(array_unique($clean));
    }

    /**
     * Return whether a table exists.
     *
     * @param string $tablename Table name.
     * @return bool
     */
    private static function table_exists(string $tablename): bool {
        global $DB;

        return $DB->get_manager()->table_exists(new \xmldb_table($tablename));
    }

    /**
     * Return the first available field value.
     *
     * @param stdClass $record Record.
     * @param string[] $fields Candidate field names.
     * @param mixed $default Default value.
     * @return mixed
     */
    private static function field(stdClass $record, array $fields, mixed $default = null): mixed {
        foreach ($fields as $field) {
            if (property_exists($record, $field) && $record->{$field} !== null && $record->{$field} !== '') {
                return $record->{$field};
            }
        }

        return $default;
    }

    /**
     * Require positive integer.
     *
     * @param int $value Value.
     * @param string $name Parameter name.
     * @return int
     */
    private static function require_positive_int(int $value, string $name): int {
        if ($value <= 0) {
            throw new invalid_parameter_exception('Invalid ' . $name . '.');
        }

        return $value;
    }
}
