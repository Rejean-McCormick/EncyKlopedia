<?php
// This file is part of Moodle - https://moodle.org/
//
// Moodle is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// any later version.

/**
 * Create an archive export request.
 *
 * @package    mod_uckkarchive
 * @copyright  2026 Univers-Cité King Klown
 * @license    https://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later
 */

namespace mod_uckkarchive\external;

defined('MOODLE_INTERNAL') || die();

global $CFG;
require_once($CFG->libdir . '/externallib.php');
require_once(dirname(__DIR__, 2) . '/locallib.php');
require_once(dirname(__DIR__) . '/local/archive_item.php');
require_once(dirname(__DIR__) . '/output/archive_item_card.php');
require_once(dirname(__DIR__) . '/output/provenance_panel.php');

use core_external\external_api;
use core_external\external_function_parameters;
use core_external\external_multiple_structure;
use core_external\external_single_structure;
use core_external\external_value;
use mod_uckkarchive\event\archive_item_created;
use mod_uckkarchive\event\archive_item_exported;
use mod_uckkarchive\event\archive_item_revised;
use mod_uckkarchive\event\archive_item_validated;
use mod_uckkarchive\output\archive_item_card;
use mod_uckkarchive\output\provenance_panel;

/**
 * Create an archive export request.
 */
class export_items extends external_api {

    /**
     * Load the page context.
     *
     * @param int $cmid Course module id.
     * @return array{0:\stdClass,1:\stdClass,2:\stdClass,3:\context_module}
     */
    protected static function load_page(int $cmid): array {
        [$course, $cm, $archive, $context] = \uckkarchive_require_page($cmid, 0);
        return [$course, $cm, $archive, $context];
    }

    /**
     * Export one item record.
     *
     * @param \stdClass $item Item.
     * @return array<string, mixed>
     */
    protected static function export_item(\stdClass $item): array {
        return \mod_uckkarchive\local\archive_item::from_record($item)->to_export();
    }

    /**
     * Return warnings in standard external format.
     *
     * @param string $item Warning item type.
     * @param int $itemid Warning item id.
     * @param string $message Warning message.
     * @return array<int, array<string, mixed>>
     */
    protected static function warning(string $item, int $itemid, string $message): array {
        return [[
            'item' => $item,
            'itemid' => $itemid,
            'warningcode' => 'archivewarning',
            'message' => $message,
        ]];
    }

    /**
     * Fetch proofs for one item.
     *
     * @param int $itemid Item id.
     * @return array<int, \stdClass>
     */
    protected static function load_proofs(int $itemid): array {
        global $DB;
        if (!$DB->get_manager()->table_exists('uckkarchive_proof')) {
            return [];
        }
        return array_values($DB->get_records('uckkarchive_proof', ['itemid' => $itemid], 'timemodified DESC, id DESC'));
    }

    /**
     * Fetch provenance records for one item.
     *
     * @param int $itemid Item id.
     * @return array<int, \stdClass>
     */
    protected static function load_provenance(int $itemid): array {
        global $DB;
        if (!$DB->get_manager()->table_exists('uckkarchive_prov')) {
            return [];
        }
        return array_values($DB->get_records('uckkarchive_prov', ['itemid' => $itemid], 'timemodified DESC, id DESC'));
    }

    /**
     * Fetch revisions for one item.
     *
     * @param int $itemid Item id.
     * @return array<int, \stdClass>
     */
    protected static function load_revisions(int $itemid): array {
        global $DB;
        if (!$DB->get_manager()->table_exists('uckkarchive_rev')) {
            return [];
        }
        return array_values($DB->get_records('uckkarchive_rev', ['itemid' => $itemid], 'timecreated DESC, id DESC'));
    }

    /**
     * Fetch latest kristal for one item.
     *
     * @param int $itemid Item id.
     * @return \stdClass|null
     */
    protected static function load_kristal(int $itemid): ?\stdClass {
        global $DB;
        if (!$DB->get_manager()->table_exists('uckkarchive_kristal')) {
            return null;
        }
        return $DB->get_record('uckkarchive_kristal', ['itemid' => $itemid], '*');
    }

    /**
     * Fetch export records for one item.
     *
     * @param int $itemid Item id.
     * @return array<int, \stdClass>
     */
    protected static function load_exports(int $itemid): array {
        global $DB;
        if (!$DB->get_manager()->table_exists('uckkarchive_export')) {
            return [];
        }

        $all = $DB->get_records('uckkarchive_export', [], 'timemodified DESC, id DESC');
        $matches = [];
        foreach ($all as $record) {
            $itemids = [];
            if (!empty($record->itemids)) {
                $decoded = json_decode((string)$record->itemids, true);
                if (is_array($decoded)) {
                    $itemids = array_map('intval', $decoded);
                }
            }
            if (in_array($itemid, $itemids, true)) {
                $matches[] = $record;
            }
        }
        return $matches;
    }


    public static function execute_parameters(): external_function_parameters {
        return new external_function_parameters([
            'cmid' => new external_value(PARAM_INT, 'Course module id'),
            'itemids' => new external_multiple_structure(new external_value(PARAM_INT, 'Item id')),
            'exportformat' => new external_value(PARAM_ALPHANUMEXT, 'Export format', VALUE_DEFAULT, 'json'),
            'description' => new external_value(PARAM_RAW, 'Description', VALUE_DEFAULT, ''),
            'reason' => new external_value(PARAM_RAW, 'Reason', VALUE_DEFAULT, ''),
            'redactionlevel' => new external_value(PARAM_ALPHANUMEXT, 'Redaction level', VALUE_DEFAULT, 'standard'),
            'includeproofs' => new external_value(PARAM_BOOL, 'Include proofs', VALUE_DEFAULT, true),
            'includeprovenance' => new external_value(PARAM_BOOL, 'Include provenance', VALUE_DEFAULT, true),
            'includeversions' => new external_value(PARAM_BOOL, 'Include versions', VALUE_DEFAULT, true),
        ]);
    }

    public static function execute(int $cmid, array $itemids, string $exportformat = 'json', string $description = '', string $reason = '', string $redactionlevel = 'standard', bool $includeproofs = true, bool $includeprovenance = true, bool $includeversions = true): array {
        global $DB, $USER;
        $params = self::validate_parameters(self::execute_parameters(), compact('cmid', 'itemids', 'exportformat', 'description', 'reason', 'redactionlevel', 'includeproofs', 'includeprovenance', 'includeversions'));
        [$course, $cm, $archive, $context] = self::load_page($params['cmid']);
        self::validate_context($context);
        require_capability('mod/uckkarchive:export', $context);

        if (!$DB->get_manager()->table_exists('uckkarchive_export')) {
            throw new \moodle_exception('missingtable', 'error', '', 'uckkarchive_export');
        }

        $allowed = [];
        foreach ($params['itemids'] as $itemid) {
            $item = \uckkarchive_get_item((int)$itemid, (int)$archive->id);
            if (\uckkarchive_can_view_item($archive, $item, $cm, $context) && \uckkarchive_item_can_export($item)) {
                $allowed[] = (int)$item->id;
            }
        }

        $now = time();
        $record = (object)[
            'archiveid' => (int)$archive->id,
            'courseid' => (int)$course->id,
            'cmid' => (int)$cm->id,
            'contextid' => (int)$context->id,
            'userid' => (int)$USER->id,
            'exportscope' => 'selected',
            'exportformat' => clean_param($params['exportformat'], PARAM_ALPHANUMEXT),
            'packagename' => 'uckkarchive-' . $archive->id . '-' . $now,
            'description' => $params['description'],
            'itemids' => json_encode(array_values($allowed)),
            'reason' => $params['reason'],
            'auditnote' => 'Created by external export_items service',
            'redactionlevel' => clean_param($params['redactionlevel'], PARAM_ALPHANUMEXT),
            'redacted' => $params['redactionlevel'] !== 'none' ? 1 : 0,
            'includefiles' => 1,
            'includeproofs' => $params['includeproofs'] ? 1 : 0,
            'includeprovenance' => $params['includeprovenance'] ? 1 : 0,
            'includeversions' => $params['includeversions'] ? 1 : 0,
            'status' => 'completed',
            'visibility' => 'course',
            'versionno' => 1,
            'createdby' => (int)$USER->id,
            'modifiedby' => (int)$USER->id,
            'timequeued' => $now,
            'timestarted' => $now,
            'timecompleted' => $now,
            'timemodified' => $now,
            'timecreated' => $now,
            'metadata' => \uckkarchive_encode_metadata([
                'service' => 'mod_uckkarchive_export_items',
                'itemcount' => count($allowed),
            ]),
        ];
        $exportid = (int)$DB->insert_record('uckkarchive_export', $record);

        foreach ($allowed as $itemid) {
            if (class_exists(archive_item_exported::class)) {
                $event = archive_item_exported::create([
                    'objectid' => (int)$itemid,
                    'context' => $context,
                    'other' => [
                        'archiveid' => (int)$archive->id,
                        'courseid' => (int)$course->id,
                        'cmid' => (int)$cm->id,
                        'exportid' => $exportid,
                        'exporttype' => clean_param($params['exportformat'], PARAM_ALPHANUMEXT),
                    ],
                ]);
                $event->trigger();
            }
        }

        return ['exportid' => $exportid, 'itemcount' => count($allowed), 'warnings' => []];
    }

    public static function execute_returns(): external_single_structure {
        return new external_single_structure([
            'exportid' => new external_value(PARAM_INT, 'Export id'),
            'itemcount' => new external_value(PARAM_INT, 'Exported item count'),
            'warnings' => new external_multiple_structure(
            new external_single_structure([
                'item' => new external_value(PARAM_TEXT, 'Warning item'),
                'itemid' => new external_value(PARAM_INT, 'Warning item id'),
                'warningcode' => new external_value(PARAM_ALPHANUMEXT, 'Warning code'),
                'message' => new external_value(PARAM_TEXT, 'Warning message'),
            ])
        ),
        ]);
    }
}
