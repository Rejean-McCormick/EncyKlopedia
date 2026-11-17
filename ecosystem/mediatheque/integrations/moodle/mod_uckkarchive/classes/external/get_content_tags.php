<?php
// This file is part of Moodle - https://moodle.org/.
//
// Moodle is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// any later version.
//
// Moodle is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with Moodle. If not, see <https://www.gnu.org/licenses/>.

/**
 * External service for reading content advisory tags.
 *
 * @package    mod_uckkarchive
 * @copyright  2026 UCKK
 * @license    https://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later
 */

namespace mod_uckkarchive\external;

use context_module;
use external_api;
use external_function_parameters;
use external_multiple_structure;
use external_single_structure;
use external_value;
use invalid_parameter_exception;
use mod_uckkarchive\local\content_tag;
use mod_uckkarchive\local\content_tag_set;

defined('MOODLE_INTERNAL') || die();

require_once($CFG->libdir . '/externallib.php');

/**
 * Get content advisory tags.
 *
 * This service returns the content advisory / cultural protocol vocabulary used
 * by media, external works, content markers, reviews, teaching workflows, and
 * export manifests.
 *
 * It is read-only. It does not approve advisories, create markers, or grant
 * access to restricted media. It returns vocabulary records only.
 */
final class get_content_tags extends external_api {
    /**
     * Content tag table.
     */
    private const CONTENT_TAG_TABLE = 'uckkarchive_content_tag';

    /**
     * Content tag set table.
     */
    private const CONTENT_TAG_SET_TABLE = 'uckkarchive_content_tag_set';

    /**
     * Describe service parameters.
     *
     * @return external_function_parameters
     */
    public static function execute_parameters(): external_function_parameters {
        return new external_function_parameters([
            'cmid' => new external_value(PARAM_INT, 'Course module id for the UCKK Archive instance.'),
            'filters' => new external_single_structure([
                'category' => new external_value(PARAM_ALPHANUMEXT, 'Tag category.', VALUE_DEFAULT, ''),
                'severity' => new external_value(PARAM_ALPHANUMEXT, 'Advisory severity.', VALUE_DEFAULT, ''),
                'defaultaudience' => new external_value(PARAM_ALPHANUMEXT, 'Default audience suitability.', VALUE_DEFAULT, ''),
                'reviewstate' => new external_value(PARAM_ALPHANUMEXT, 'Review state.', VALUE_DEFAULT, ''),
                'tagsetid' => new external_value(PARAM_INT, 'Content tag set id.', VALUE_DEFAULT, 0),
                'tagsetkey' => new external_value(PARAM_ALPHANUMEXT, 'Content tag set key.', VALUE_DEFAULT, ''),
                'search' => new external_value(PARAM_TEXT, 'Search in key, label, or description.', VALUE_DEFAULT, ''),
                'active' => new external_value(PARAM_BOOL, 'Only active tags.', VALUE_DEFAULT, true),
                'includeinactive' => new external_value(PARAM_BOOL, 'Include inactive/retired tags.', VALUE_DEFAULT, false),
                'iscultural' => new external_value(PARAM_BOOL, 'Only cultural protocol tags.', VALUE_DEFAULT, false),
                'restrictsdefault' => new external_value(PARAM_BOOL, 'Only tags that restrict by default.', VALUE_DEFAULT, false),
            ], 'Tag filters.', VALUE_DEFAULT, []),
            'include' => new external_single_structure([
                'metadata' => new external_value(PARAM_BOOL, 'Include JSON metadata.', VALUE_DEFAULT, false),
                'tagsets' => new external_value(PARAM_BOOL, 'Include tag set summaries.', VALUE_DEFAULT, true),
                'seedfallback' => new external_value(PARAM_BOOL, 'Return seed vocabulary if the table is not installed or empty.', VALUE_DEFAULT, true),
            ], 'Include options.', VALUE_DEFAULT, []),
            'page' => new external_value(PARAM_INT, 'Zero-based page number.', VALUE_DEFAULT, 0),
            'perpage' => new external_value(PARAM_INT, 'Items per page. Use 0 to return all.', VALUE_DEFAULT, 0),
        ]);
    }

    /**
     * Execute service.
     *
     * @param int $cmid Course module id.
     * @param array $filters Filters.
     * @param array $include Include options.
     * @param int $page Zero-based page.
     * @param int $perpage Items per page.
     * @return array
     */
    public static function execute(
        int $cmid,
        array $filters = [],
        array $include = [],
        int $page = 0,
        int $perpage = 0
    ): array {
        global $DB;

        [
            'cmid' => $cmid,
            'filters' => $filters,
            'include' => $include,
            'page' => $page,
            'perpage' => $perpage,
        ] = self::validate_parameters(self::execute_parameters(), [
            'cmid' => $cmid,
            'filters' => $filters,
            'include' => $include,
            'page' => $page,
            'perpage' => $perpage,
        ]);

        $cm = get_coursemodule_from_id('uckkarchive', $cmid, 0, false, MUST_EXIST);
        $course = $DB->get_record('course', ['id' => $cm->course], '*', MUST_EXIST);
        $archive = $DB->get_record('uckkarchive', ['id' => $cm->instance], '*', MUST_EXIST);
        $context = context_module::instance($cm->id);

        self::validate_context($context);
        require_login($course, false, $cm);
        self::require_view_advisories($context);

        $filters = self::normalize_filters($filters);
        $include = self::normalize_include($include);
        $page = max(0, (int)$page);
        $perpage = max(0, min(250, (int)$perpage));

        $warnings = [];
        $source = 'database';

        if (!self::table_exists(self::CONTENT_TAG_TABLE)) {
            $warnings[] = self::warning('content_tag', 0, 'contenttagtablenotfound', 'Content tag table is not installed.');
            $tags = $include['seedfallback'] ? self::seed_tags($filters, $include['metadata']) : [];
            $source = 'seed';
        } else {
            $tags = self::load_tags($filters, $include['metadata']);

            if (empty($tags) && $include['seedfallback']) {
                $tags = self::seed_tags($filters, $include['metadata']);
                $source = 'seed';
            }
        }

        $total = count($tags);
        if ($perpage > 0) {
            $tags = array_slice($tags, $page * $perpage, $perpage);
        }

        $tagsets = [];
        if ($include['tagsets']) {
            $tagsets = self::load_tagsets($include['metadata']);
        }

        return [
            'tags' => array_values($tags),
            'tagsets' => $tagsets,
            'categories' => content_tag::get_categories(),
            'severities' => content_tag::get_severities(),
            'audiencevalues' => content_tag::get_audience_values(),
            'reviewstates' => content_tag::get_review_states(),
            'pagination' => [
                'page' => $page,
                'perpage' => $perpage,
                'total' => $total,
                'returned' => count($tags),
                'hasmore' => $perpage > 0 ? (($page + 1) * $perpage < $total) : false,
            ],
            'source' => $source,
            'permissions' => [
                'viewadvisories' => has_capability('mod/uckkarchive:viewadvisories', $context),
                'manageadvisories' => has_capability('mod/uckkarchive:manageadvisories', $context),
                'reviewadvisories' => has_capability('mod/uckkarchive:reviewadvisories', $context),
                'viewculturallyrestricted' => has_capability('mod/uckkarchive:viewculturallyrestricted', $context),
            ],
            'warnings' => $warnings,
        ];
    }

    /**
     * Describe service return structure.
     *
     * @return external_single_structure
     */
    public static function execute_returns(): external_single_structure {
        return new external_single_structure([
            'tags' => new external_multiple_structure(self::tag_structure(), 'Content advisory tags.'),
            'tagsets' => new external_multiple_structure(self::tagset_structure(), 'Content tag set summaries.'),
            'categories' => new external_multiple_structure(
                new external_value(PARAM_ALPHANUMEXT, 'Tag category.'),
                'Supported categories.'
            ),
            'severities' => new external_multiple_structure(
                new external_value(PARAM_ALPHANUMEXT, 'Advisory severity.'),
                'Supported severities.'
            ),
            'audiencevalues' => new external_multiple_structure(
                new external_value(PARAM_ALPHANUMEXT, 'Audience suitability value.'),
                'Supported audience values.'
            ),
            'reviewstates' => new external_multiple_structure(
                new external_value(PARAM_ALPHANUMEXT, 'Review state.'),
                'Supported review states.'
            ),
            'pagination' => new external_single_structure([
                'page' => new external_value(PARAM_INT, 'Current zero-based page.'),
                'perpage' => new external_value(PARAM_INT, 'Items per page, or 0 when unpaged.'),
                'total' => new external_value(PARAM_INT, 'Total matching records.'),
                'returned' => new external_value(PARAM_INT, 'Returned records.'),
                'hasmore' => new external_value(PARAM_BOOL, 'Whether more records exist.'),
            ]),
            'source' => new external_value(PARAM_ALPHANUMEXT, 'Vocabulary source: database or seed.'),
            'permissions' => new external_single_structure([
                'viewadvisories' => new external_value(PARAM_BOOL, 'Can view advisories.'),
                'manageadvisories' => new external_value(PARAM_BOOL, 'Can manage advisories.'),
                'reviewadvisories' => new external_value(PARAM_BOOL, 'Can review advisories.'),
                'viewculturallyrestricted' => new external_value(PARAM_BOOL, 'Can view culturally restricted material.'),
            ]),
            'warnings' => new external_multiple_structure(
                new external_single_structure([
                    'item' => new external_value(PARAM_TEXT, 'Warning item.'),
                    'itemid' => new external_value(PARAM_INT, 'Warning item id.'),
                    'warningcode' => new external_value(PARAM_ALPHANUMEXT, 'Warning code.'),
                    'message' => new external_value(PARAM_TEXT, 'Warning message.'),
                ]),
                'Warnings.'
            ),
        ]);
    }

    /**
     * Tag return structure.
     *
     * @return external_single_structure
     */
    private static function tag_structure(): external_single_structure {
        return new external_single_structure([
            'id' => new external_value(PARAM_INT, 'Tag id.'),
            'uuid' => new external_value(PARAM_RAW, 'Tag UUID.'),
            'tagkey' => new external_value(PARAM_ALPHANUMEXT, 'Tag key.'),
            'label' => new external_value(PARAM_TEXT, 'Tag label.'),
            'description' => new external_value(PARAM_RAW, 'Tag description.'),
            'category' => new external_value(PARAM_ALPHANUMEXT, 'Tag category.'),
            'severity' => new external_value(PARAM_ALPHANUMEXT, 'Advisory severity.'),
            'defaultaudience' => new external_value(PARAM_ALPHANUMEXT, 'Default audience suitability.'),
            'iscultural' => new external_value(PARAM_BOOL, 'Whether this is a cultural protocol tag.'),
            'restrictsdefault' => new external_value(PARAM_BOOL, 'Whether this restricts by default.'),
            'reviewstate' => new external_value(PARAM_ALPHANUMEXT, 'Review state.'),
            'active' => new external_value(PARAM_BOOL, 'Whether the tag is active.'),
            'tagsetid' => new external_value(PARAM_INT, 'Tag set id.'),
            'tagsetkey' => new external_value(PARAM_ALPHANUMEXT, 'Tag set key.'),
            'sortorder' => new external_value(PARAM_INT, 'Sort order.'),
            'metadatajson' => new external_value(PARAM_RAW, 'Metadata as JSON string.'),
        ]);
    }

    /**
     * Tag set return structure.
     *
     * @return external_single_structure
     */
    private static function tagset_structure(): external_single_structure {
        return new external_single_structure([
            'id' => new external_value(PARAM_INT, 'Tag set id.'),
            'uuid' => new external_value(PARAM_RAW, 'Tag set UUID.'),
            'tagsetkey' => new external_value(PARAM_ALPHANUMEXT, 'Tag set key.'),
            'name' => new external_value(PARAM_TEXT, 'Name.'),
            'description' => new external_value(PARAM_RAW, 'Description.'),
            'purpose' => new external_value(PARAM_ALPHANUMEXT, 'Purpose.'),
            'visibility' => new external_value(PARAM_ALPHANUMEXT, 'Visibility.'),
            'audiencesuitability' => new external_value(PARAM_ALPHANUMEXT, 'Audience suitability.'),
            'status' => new external_value(PARAM_ALPHANUMEXT, 'Status.'),
            'visible' => new external_value(PARAM_BOOL, 'Visible.'),
            'locked' => new external_value(PARAM_BOOL, 'Locked.'),
            'sortorder' => new external_value(PARAM_INT, 'Sort order.'),
            'metadatajson' => new external_value(PARAM_RAW, 'Metadata as JSON string.'),
        ]);
    }

    /**
     * Load content tags from database/domain helper.
     *
     * @param array $filters Filters.
     * @param bool $includemetadata Include metadata.
     * @return array
     */
    private static function load_tags(array $filters, bool $includemetadata): array {
        $domainfilters = [];

        if (!$filters['includeinactive']) {
            $domainfilters['active'] = $filters['active'] ? 1 : 0;
        }

        foreach (['category', 'severity', 'iscultural', 'restrictsdefault'] as $key) {
            if ($filters[$key] !== '' && $filters[$key] !== false) {
                $domainfilters[$key] = $filters[$key];
            }
        }

        if ($filters['tagsetid'] > 0 || $filters['tagsetkey'] !== '') {
            $tagset = $filters['tagsetid'] > 0 ? $filters['tagsetid'] : $filters['tagsetkey'];
            $records = content_tag_set::get_tags($tagset, !$filters['includeinactive']);
        } else {
            $records = content_tag::get_all($domainfilters);
        }

        $tags = [];
        foreach ($records as $record) {
            $tag = self::format_tag(content_tag::to_export_array($record, $includemetadata), $includemetadata);
            if (self::matches_post_filters($tag, $filters)) {
                $tags[] = $tag;
            }
        }

        return $tags;
    }

    /**
     * Load tag set summaries.
     *
     * @param bool $includemetadata Include metadata.
     * @return array
     */
    private static function load_tagsets(bool $includemetadata): array {
        if (!self::table_exists(self::CONTENT_TAG_SET_TABLE)) {
            return [];
        }

        $sets = [];
        foreach (content_tag_set::get_all(null, true) as $record) {
            $summary = content_tag_set::export_summary($record, false);
            $sets[] = [
                'id' => (int)($summary['id'] ?? 0),
                'uuid' => (string)($summary['uuid'] ?? ''),
                'tagsetkey' => (string)($summary['tagsetkey'] ?? ''),
                'name' => (string)($summary['name'] ?? ''),
                'description' => (string)($summary['description'] ?? ''),
                'purpose' => (string)($summary['purpose'] ?? ''),
                'visibility' => (string)($summary['visibility'] ?? ''),
                'audiencesuitability' => (string)($summary['audiencesuitability'] ?? ''),
                'status' => (string)($summary['status'] ?? ''),
                'visible' => !empty($summary['visible']),
                'locked' => !empty($summary['locked']),
                'sortorder' => (int)($summary['sortorder'] ?? 0),
                'metadatajson' => $includemetadata ? self::json($summary['metadata'] ?? []) : '{}',
            ];
        }

        return $sets;
    }

    /**
     * Return seed tags from domain constants.
     *
     * @param array $filters Filters.
     * @param bool $includemetadata Include metadata.
     * @return array
     */
    private static function seed_tags(array $filters, bool $includemetadata): array {
        $tags = [];
        $sort = 10;

        foreach (content_tag::get_seed_tags() as $tagkey => $record) {
            $tag = self::format_tag([
                'id' => 0,
                'uuid' => '',
                'tagkey' => $tagkey,
                'label' => $record['label'] ?? $tagkey,
                'description' => $record['description'] ?? '',
                'category' => $record['category'] ?? 'general_advisory',
                'severity' => $record['severity'] ?? 'notice',
                'defaultaudience' => $record['defaultaudience'] ?? 'guided',
                'iscultural' => !empty($record['iscultural']),
                'restrictsdefault' => !empty($record['restrictsdefault']),
                'reviewstate' => $record['reviewstate'] ?? 'approved',
                'active' => 1,
                'tagsetid' => 0,
                'tagsetkey' => $record['tagsetkey'] ?? '',
                'sortorder' => $record['sortorder'] ?? $sort,
                'metadata' => $record['metadata'] ?? [],
            ], $includemetadata);

            if (self::matches_post_filters($tag, $filters)) {
                $tags[] = $tag;
            }

            $sort += 10;
        }

        return $tags;
    }

    /**
     * Format one tag payload.
     *
     * @param array $tag Tag data.
     * @param bool $includemetadata Include metadata.
     * @return array
     */
    private static function format_tag(array $tag, bool $includemetadata): array {
        $metadata = $tag['metadata'] ?? [];

        return [
            'id' => (int)($tag['id'] ?? 0),
            'uuid' => (string)($tag['uuid'] ?? ''),
            'tagkey' => (string)($tag['tagkey'] ?? ''),
            'label' => (string)($tag['label'] ?? ''),
            'description' => (string)($tag['description'] ?? ''),
            'category' => (string)($tag['category'] ?? ''),
            'severity' => (string)($tag['severity'] ?? ''),
            'defaultaudience' => (string)($tag['defaultaudience'] ?? ''),
            'iscultural' => !empty($tag['iscultural']),
            'restrictsdefault' => !empty($tag['restrictsdefault']),
            'reviewstate' => (string)($tag['reviewstate'] ?? ''),
            'active' => !array_key_exists('active', $tag) || !empty($tag['active']),
            'tagsetid' => (int)($tag['tagsetid'] ?? 0),
            'tagsetkey' => (string)($tag['tagsetkey'] ?? ''),
            'sortorder' => (int)($tag['sortorder'] ?? 0),
            'metadatajson' => $includemetadata ? self::json(is_array($metadata) ? $metadata : []) : '{}',
        ];
    }

    /**
     * Match post filters that are not fully supported by the domain helper.
     *
     * @param array $tag Formatted tag.
     * @param array $filters Filters.
     * @return bool
     */
    private static function matches_post_filters(array $tag, array $filters): bool {
        foreach (['category', 'severity', 'defaultaudience', 'reviewstate', 'tagsetkey'] as $key) {
            if ($filters[$key] !== '' && (string)$tag[$key] !== (string)$filters[$key]) {
                return false;
            }
        }

        if (!$filters['includeinactive'] && !$tag['active']) {
            return false;
        }

        if ($filters['iscultural'] && !$tag['iscultural']) {
            return false;
        }

        if ($filters['restrictsdefault'] && !$tag['restrictsdefault']) {
            return false;
        }

        if ($filters['search'] !== '') {
            $haystack = strtolower($tag['tagkey'] . ' ' . $tag['label'] . ' ' . $tag['description']);
            if (!str_contains($haystack, strtolower($filters['search']))) {
                return false;
            }
        }

        return true;
    }

    /**
     * Normalize filters.
     *
     * @param array $filters Raw filters.
     * @return array
     */
    private static function normalize_filters(array $filters): array {
        $defaults = [
            'category' => '',
            'severity' => '',
            'defaultaudience' => '',
            'reviewstate' => '',
            'tagsetid' => 0,
            'tagsetkey' => '',
            'search' => '',
            'active' => true,
            'includeinactive' => false,
            'iscultural' => false,
            'restrictsdefault' => false,
        ];

        $filters = array_merge($defaults, $filters);

        foreach (['category', 'severity', 'defaultaudience', 'reviewstate', 'tagsetkey'] as $key) {
            $filters[$key] = clean_param(strtolower(trim((string)$filters[$key])), PARAM_ALPHANUMEXT);
        }

        $filters['search'] = clean_param(trim((string)$filters['search']), PARAM_TEXT);
        $filters['tagsetid'] = max(0, (int)$filters['tagsetid']);
        $filters['active'] = !empty($filters['active']);
        $filters['includeinactive'] = !empty($filters['includeinactive']);
        $filters['iscultural'] = !empty($filters['iscultural']);
        $filters['restrictsdefault'] = !empty($filters['restrictsdefault']);

        return $filters;
    }

    /**
     * Normalize include options.
     *
     * @param array $include Include options.
     * @return array
     */
    private static function normalize_include(array $include): array {
        $defaults = [
            'metadata' => false,
            'tagsets' => true,
            'seedfallback' => true,
        ];

        $include = array_merge($defaults, $include);

        return [
            'metadata' => !empty($include['metadata']),
            'tagsets' => !empty($include['tagsets']),
            'seedfallback' => !empty($include['seedfallback']),
        ];
    }

    /**
     * Require view-advisories capability through domain helper when available.
     *
     * @param \context_module $context Context.
     * @return void
     */
    private static function require_view_advisories(context_module $context): void {
        if (class_exists(content_tag::class) && method_exists(content_tag::class, 'require_view')) {
            content_tag::require_view($context);
            return;
        }

        require_capability('mod/uckkarchive:viewadvisories', $context);
    }

    /**
     * Return whether table exists.
     *
     * @param string $table Table name.
     * @return bool
     */
    private static function table_exists(string $table): bool {
        global $DB;

        return $DB->get_manager()->table_exists(new \xmldb_table($table));
    }

    /**
     * Warning payload.
     *
     * @param string $item Warning item.
     * @param int $itemid Item id.
     * @param string $code Warning code.
     * @param string $message Message.
     * @return array
     */
    private static function warning(string $item, int $itemid, string $code, string $message): array {
        return [
            'item' => $item,
            'itemid' => $itemid,
            'warningcode' => clean_param($code, PARAM_ALPHANUMEXT),
            'message' => $message,
        ];
    }

    /**
     * JSON encode data.
     *
     * @param array $data Data.
     * @return string
     */
    private static function json(array $data): string {
        return json_encode($data, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES) ?: '{}';
    }
}
