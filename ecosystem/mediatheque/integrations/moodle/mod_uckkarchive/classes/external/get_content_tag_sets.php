<?php
// This file is part of Moodle - https://moodle.org/.
//
// Moodle is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// any later version.

/**
 * External service for listing content advisory tag sets.
 *
 * @package    mod_uckkarchive
 * @copyright  2026 Univers-Cité King Klown
 * @license    https://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later
 */

declare(strict_types=1);

namespace mod_uckkarchive\external;

defined('MOODLE_INTERNAL') || die();

global $CFG;
require_once($CFG->libdir . '/externallib.php');
require_once(dirname(__DIR__, 2) . '/locallib.php');
require_once(dirname(__DIR__) . '/local/content_policy.php');
require_once(dirname(__DIR__) . '/local/content_tag_set.php');

use context_module;
use core_external\external_api;
use core_external\external_function_parameters;
use core_external\external_multiple_structure;
use core_external\external_single_structure;
use core_external\external_value;
use invalid_parameter_exception;
use mod_uckkarchive\local\content_policy;
use mod_uckkarchive\local\content_tag_set;
use stdClass;

/**
 * Return permission-filtered content advisory tag sets.
 *
 * Target service name:
 *
 * ```text
 * mod_uckkarchive_get_content_tag_sets
 * ```
 *
 * This is a read service. It exposes the controlled advisory vocabularies used
 * by content markers, reviews, media cards, external works, and advisory panels.
 *
 * It must not expose hidden/retired vocabularies unless the caller has advisory
 * management authority.
 */
final class get_content_tag_sets extends external_api {
    /** Content tag set table. */
    private const TAG_SET_TABLE = 'uckkarchive_content_tag_set';

    /** Content tag table. */
    private const TAG_TABLE = 'uckkarchive_content_tag';

    /**
     * Define service parameters.
     *
     * @return external_function_parameters
     */
    public static function execute_parameters(): external_function_parameters {
        return new external_function_parameters([
            'cmid' => new external_value(PARAM_INT, 'Course module id for the UCKK Archive instance.'),
            'status' => new external_value(
                PARAM_ALPHANUMEXT,
                'Status filter: active, draft, archived, retired, or all.',
                VALUE_DEFAULT,
                content_tag_set::STATUS_ACTIVE
            ),
            'includehidden' => new external_value(
                PARAM_BOOL,
                'Include hidden tag sets. Requires manageadvisories.',
                VALUE_DEFAULT,
                false
            ),
            'includetags' => new external_value(
                PARAM_BOOL,
                'Include tags belonging to each tag set.',
                VALUE_DEFAULT,
                true
            ),
            'activeonlytags' => new external_value(
                PARAM_BOOL,
                'When includetags is true, include only active/visible tags.',
                VALUE_DEFAULT,
                true
            ),
            'ensurebaseline' => new external_value(
                PARAM_BOOL,
                'Ensure baseline tag sets exist before reading. Requires manageadvisories.',
                VALUE_DEFAULT,
                false
            ),
        ]);
    }

    /**
     * Execute service.
     *
     * @param int $cmid Course module id.
     * @param string $status Status filter.
     * @param bool $includehidden Include hidden sets.
     * @param bool $includetags Include tags.
     * @param bool $activeonlytags Active-only tags.
     * @param bool $ensurebaseline Ensure baseline records.
     * @return array<string, mixed>
     */
    public static function execute(
        int $cmid,
        string $status = content_tag_set::STATUS_ACTIVE,
        bool $includehidden = false,
        bool $includetags = true,
        bool $activeonlytags = true,
        bool $ensurebaseline = false
    ): array {
        $params = self::validate_parameters(self::execute_parameters(), [
            'cmid' => $cmid,
            'status' => $status,
            'includehidden' => $includehidden,
            'includetags' => $includetags,
            'activeonlytags' => $activeonlytags,
            'ensurebaseline' => $ensurebaseline,
        ]);

        [$course, $cm, $archive, $context] = self::load_page((int)$params['cmid']);

        self::validate_context($context);
        require_login($course, false, $cm);
        content_policy::require_view_advisories($context);

        $includehidden = !empty($params['includehidden']);
        $ensurebaseline = !empty($params['ensurebaseline']);

        if (($includehidden || $ensurebaseline) && !content_policy::can_manage_advisories($context)) {
            throw new \required_capability_exception(
                $context,
                content_policy::CAP_MANAGE_ADVISORIES,
                'nopermissions',
                ''
            );
        }

        if (!self::table_exists(self::TAG_SET_TABLE)) {
            return [
                'tagsets' => [],
                'total' => 0,
                'permissions' => self::permissions($context),
                'warnings' => [[
                    'item' => 'content_tag_set',
                    'itemid' => 0,
                    'warningcode' => 'tagsettablenotfound',
                    'message' => 'Content advisory tag set table is not installed yet.',
                ]],
            ];
        }

        if ($ensurebaseline && method_exists(content_tag_set::class, 'ensure_baseline_sets')) {
            content_tag_set::ensure_baseline_sets();
        }

        $status = self::normalise_status((string)$params['status']);
        $statusfilter = $status === 'all' ? null : $status;

        $records = content_tag_set::get_all($statusfilter, $includehidden);
        $tagsets = [];

        foreach ($records as $record) {
            if (!self::can_view_tag_set($record, $context)) {
                continue;
            }

            $tagsets[] = self::export_tag_set($record, $context, !empty($params['includetags']), !empty($params['activeonlytags']));
        }

        return [
            'tagsets' => $tagsets,
            'total' => count($tagsets),
            'permissions' => self::permissions($context),
            'warnings' => [],
        ];
    }

    /**
     * Define service return structure.
     *
     * @return external_single_structure
     */
    public static function execute_returns(): external_single_structure {
        return new external_single_structure([
            'tagsets' => new external_multiple_structure(self::tag_set_structure(), 'Content advisory tag sets.'),
            'total' => new external_value(PARAM_INT, 'Total returned tag sets.'),
            'permissions' => self::permissions_structure(),
            'warnings' => self::warnings_structure(),
        ]);
    }

    /**
     * Return tag set structure.
     *
     * @return external_single_structure
     */
    private static function tag_set_structure(): external_single_structure {
        return new external_single_structure([
            'id' => new external_value(PARAM_INT, 'Tag set id.'),
            'uuid' => new external_value(PARAM_RAW, 'Tag set UUID.'),
            'tagsetkey' => new external_value(PARAM_ALPHANUMEXT, 'Tag set machine key.'),
            'name' => new external_value(PARAM_TEXT, 'Display name.'),
            'description' => new external_value(PARAM_RAW, 'Description.'),
            'purpose' => new external_value(PARAM_ALPHANUMEXT, 'Purpose/category of the tag set.'),
            'visibility' => new external_value(PARAM_ALPHANUMEXT, 'Visibility.'),
            'audiencesuitability' => new external_value(PARAM_ALPHANUMEXT, 'Audience suitability.'),
            'status' => new external_value(PARAM_ALPHANUMEXT, 'Status.'),
            'visible' => new external_value(PARAM_BOOL, 'Visible flag.'),
            'locked' => new external_value(PARAM_BOOL, 'Locked/system flag.'),
            'sortorder' => new external_value(PARAM_INT, 'Sort order.'),
            'tagcount' => new external_value(PARAM_INT, 'Number of included tags.'),
            'metadatajson' => new external_value(PARAM_RAW, 'JSON-encoded metadata.'),
            'timecreated' => new external_value(PARAM_INT, 'Created timestamp.'),
            'timemodified' => new external_value(PARAM_INT, 'Modified timestamp.'),
            'tags' => new external_multiple_structure(self::tag_structure(), 'Tags in this tag set.'),
        ]);
    }

    /**
     * Return tag structure.
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
            'severity' => new external_value(PARAM_ALPHANUMEXT, 'Default severity.'),
            'audiencesuitability' => new external_value(PARAM_ALPHANUMEXT, 'Default audience suitability.'),
            'reviewstate' => new external_value(PARAM_ALPHANUMEXT, 'Default review state.'),
            'status' => new external_value(PARAM_ALPHANUMEXT, 'Tag status.'),
            'visible' => new external_value(PARAM_BOOL, 'Visible flag.'),
            'culturalprotocol' => new external_value(PARAM_BOOL, 'Cultural protocol tag.'),
            'restrictsbydefault' => new external_value(PARAM_BOOL, 'Restricts by default.'),
            'requiresreview' => new external_value(PARAM_BOOL, 'Requires review.'),
            'sortorder' => new external_value(PARAM_INT, 'Sort order.'),
        ]);
    }

    /**
     * Return permission structure.
     *
     * @return external_single_structure
     */
    private static function permissions_structure(): external_single_structure {
        return new external_single_structure([
            'viewadvisories' => new external_value(PARAM_BOOL, 'Can view advisories.'),
            'manageadvisories' => new external_value(PARAM_BOOL, 'Can manage advisories.'),
            'reviewadvisories' => new external_value(PARAM_BOOL, 'Can review advisories.'),
            'viewculturallyrestricted' => new external_value(PARAM_BOOL, 'Can view culturally restricted material.'),
        ]);
    }

    /**
     * Return warnings structure.
     *
     * @return external_multiple_structure
     */
    private static function warnings_structure(): external_multiple_structure {
        return new external_multiple_structure(new external_single_structure([
            'item' => new external_value(PARAM_TEXT, 'Warning item.'),
            'itemid' => new external_value(PARAM_INT, 'Warning item id.'),
            'warningcode' => new external_value(PARAM_ALPHANUMEXT, 'Warning code.'),
            'message' => new external_value(PARAM_TEXT, 'Warning message.'),
        ]));
    }

    /**
     * Load Moodle activity context.
     *
     * @param int $cmid Course module id.
     * @return array{0:stdClass,1:stdClass,2:stdClass,3:context_module}
     */
    private static function load_page(int $cmid): array {
        global $DB;

        if (function_exists('uckkarchive_require_page')) {
            [$course, $cm, $archive, $context] = \uckkarchive_require_page($cmid, 0);
            return [$course, $cm, $archive, $context];
        }

        $cm = get_coursemodule_from_id('uckkarchive', $cmid, 0, false, MUST_EXIST);
        $course = $DB->get_record('course', ['id' => $cm->course], '*', MUST_EXIST);
        $archive = $DB->get_record('uckkarchive', ['id' => $cm->instance], '*', MUST_EXIST);
        $context = context_module::instance($cm->id);

        return [$course, $cm, $archive, $context];
    }

    /**
     * Normalize status.
     *
     * @param string $status Status.
     * @return string
     */
    private static function normalise_status(string $status): string {
        $status = clean_param($status, PARAM_ALPHANUMEXT);

        if ($status === '') {
            return content_tag_set::STATUS_ACTIVE;
        }

        $allowed = array_merge(['all'], content_tag_set::statuses());

        if (!in_array($status, $allowed, true)) {
            throw new invalid_parameter_exception('Invalid content tag set status.');
        }

        return $status;
    }

    /**
     * Return whether the user may view the tag set.
     *
     * @param stdClass $record Tag set.
     * @param context_module $context Context.
     * @return bool
     */
    private static function can_view_tag_set(stdClass $record, context_module $context): bool {
        if (!content_policy::can_view_advisories($context)) {
            return false;
        }

        $visible = !property_exists($record, 'visible') || !empty($record->visible);
        $status = (string)($record->status ?? content_tag_set::STATUS_ACTIVE);

        if (!$visible || in_array($status, [content_tag_set::STATUS_DRAFT, content_tag_set::STATUS_RETIRED], true)) {
            return content_policy::can_manage_advisories($context);
        }

        if ((string)($record->visibility ?? '') === 'restricted_cultural') {
            return content_policy::can_view_culturally_restricted($context);
        }

        return true;
    }

    /**
     * Export one tag set.
     *
     * @param stdClass $record Tag set record.
     * @param context_module $context Context.
     * @param bool $includetags Include tags.
     * @param bool $activeonlytags Active-only tags.
     * @return array<string, mixed>
     */
    private static function export_tag_set(
        stdClass $record,
        context_module $context,
        bool $includetags,
        bool $activeonlytags
    ): array {
        $summary = content_tag_set::export_summary($record, false);
        $tags = [];

        if ($includetags && self::table_exists(self::TAG_TABLE)) {
            foreach (content_tag_set::get_tags($record, $activeonlytags) as $tag) {
                if (!self::can_view_tag($tag, $context)) {
                    continue;
                }
                $tags[] = self::export_tag($tag);
            }
        }

        return [
            'id' => (int)($summary['id'] ?? 0),
            'uuid' => (string)($summary['uuid'] ?? ''),
            'tagsetkey' => (string)($summary['tagsetkey'] ?? ''),
            'name' => format_string((string)($summary['name'] ?? '')),
            'description' => format_text((string)($summary['description'] ?? ''), FORMAT_HTML, ['para' => false]),
            'purpose' => (string)($summary['purpose'] ?? ''),
            'visibility' => (string)($summary['visibility'] ?? ''),
            'audiencesuitability' => (string)($summary['audiencesuitability'] ?? ''),
            'status' => (string)($summary['status'] ?? ''),
            'visible' => !empty($summary['visible']),
            'locked' => !empty($summary['locked']),
            'sortorder' => (int)($summary['sortorder'] ?? 0),
            'tagcount' => count($tags),
            'metadatajson' => self::encode_json((array)($summary['metadata'] ?? [])),
            'timecreated' => (int)($summary['timecreated'] ?? 0),
            'timemodified' => (int)($summary['timemodified'] ?? 0),
            'tags' => $tags,
        ];
    }

    /**
     * Return whether user may view a tag.
     *
     * @param stdClass $tag Tag record.
     * @param context_module $context Context.
     * @return bool
     */
    private static function can_view_tag(stdClass $tag, context_module $context): bool {
        $visible = !property_exists($tag, 'visible') || !empty($tag->visible);
        $status = (string)($tag->status ?? 'active');

        if (!$visible || in_array($status, ['draft', 'retired', 'archived'], true)) {
            return content_policy::can_manage_advisories($context);
        }

        $iscultural = !empty($tag->culturalprotocol) ||
            in_array((string)($tag->category ?? ''), ['cultural_protocol', 'cultural_protocols'], true) ||
            !empty($tag->iscultural);

        if ($iscultural) {
            return content_policy::can_view_culturally_restricted($context);
        }

        return true;
    }

    /**
     * Export one tag.
     *
     * @param stdClass $tag Tag record.
     * @return array<string, mixed>
     */
    private static function export_tag(stdClass $tag): array {
        return [
            'id' => (int)($tag->id ?? 0),
            'uuid' => (string)($tag->uuid ?? ''),
            'tagkey' => (string)($tag->tagkey ?? $tag->key ?? ''),
            'label' => format_string((string)($tag->label ?? $tag->name ?? '')),
            'description' => format_text((string)($tag->description ?? ''), FORMAT_HTML, ['para' => false]),
            'category' => (string)($tag->category ?? ''),
            'severity' => (string)($tag->severity ?? ''),
            'audiencesuitability' => (string)($tag->audiencesuitability ?? $tag->audience ?? ''),
            'reviewstate' => (string)($tag->reviewstate ?? ''),
            'status' => (string)($tag->status ?? ''),
            'visible' => !isset($tag->visible) || !empty($tag->visible),
            'culturalprotocol' => !empty($tag->culturalprotocol) || !empty($tag->iscultural),
            'restrictsbydefault' => !empty($tag->restrictsbydefault) || !empty($tag->restrictedbydefault),
            'requiresreview' => !empty($tag->requiresreview),
            'sortorder' => (int)($tag->sortorder ?? 0),
        ];
    }

    /**
     * Return permissions payload.
     *
     * @param context_module $context Context.
     * @return array<string, bool>
     */
    private static function permissions(context_module $context): array {
        return [
            'viewadvisories' => content_policy::can_view_advisories($context),
            'manageadvisories' => content_policy::can_manage_advisories($context),
            'reviewadvisories' => content_policy::can_review_advisories($context),
            'viewculturallyrestricted' => content_policy::can_view_culturally_restricted($context),
        ];
    }

    /**
     * Return whether a table exists.
     *
     * @param string $table Table name.
     * @return bool
     */
    private static function table_exists(string $table): bool {
        global $DB;

        return $DB->get_manager()->table_exists(new \xmldb_table($table));
    }

    /**
     * Encode metadata JSON safely.
     *
     * @param array<string, mixed> $data Data.
     * @return string
     */
    private static function encode_json(array $data): string {
        $json = json_encode($data, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);

        return $json === false ? '{}' : $json;
    }
}
