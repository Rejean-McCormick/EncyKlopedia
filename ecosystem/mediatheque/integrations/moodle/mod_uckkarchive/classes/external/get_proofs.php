<?php
// This file is part of Moodle - https://moodle.org/
//
// Moodle is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// any later version.

/**
 * Return proofs linked to an archive item.
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
 * Return proofs linked to an archive item.
 */
class get_proofs extends external_api {

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
            'itemid' => new external_value(PARAM_INT, 'Item id'),
        ]);
    }

    public static function execute(int $cmid, int $itemid): array {
        $params = self::validate_parameters(self::execute_parameters(), compact('cmid', 'itemid'));
        [$course, $cm, $archive, $context] = self::load_page($params['cmid']);
        self::validate_context($context);

        $item = \uckkarchive_get_item($params['itemid'], (int)$archive->id);
        if (!\uckkarchive_can_view_item($archive, $item, $cm, $context)) {
            throw new \required_capability_exception($context, 'mod/uckkarchive:view', 'nopermissions', '');
        }

        $proofs = [];
        foreach (self::load_proofs((int)$item->id) as $proof) {
            $visibility = \uckkarchive_normalise_visibility($proof->visibility ?? null);
            if ($visibility === UCKKARCHIVE_VISIBILITY_RESTRICTED_INTEGRITY && !has_capability('mod/uckkarchive:viewrestricted', $context)) {
                continue;
            }
            $proofs[] = [
                'id' => (int)$proof->id,
                'itemid' => (int)$proof->itemid,
                'title' => format_string((string)$proof->title),
                'prooftype' => (string)$proof->prooftype,
                'description' => format_text((string)($proof->description ?? ''), (int)($proof->descriptionformat ?? FORMAT_HTML), ['para' => false]),
                'sourceurl' => (string)($proof->sourceurl ?? ''),
                'status' => (string)$proof->status,
                'visibility' => (string)$proof->visibility,
                'validationstate' => (string)$proof->validationstate,
                'provenance' => (string)$proof->provenance,
                'fileitemid' => (int)($proof->fileitemid ?? 0),
                'timemodified' => (int)($proof->timemodified ?? 0),
            ];
        }

        return ['proofs' => $proofs, 'warnings' => []];
    }

    public static function execute_returns(): external_single_structure {
        return new external_single_structure([
            'proofs' => new external_multiple_structure(
                new external_single_structure([
                    'id' => new external_value(PARAM_INT, 'Proof id'),
                    'itemid' => new external_value(PARAM_INT, 'Item id'),
                    'title' => new external_value(PARAM_TEXT, 'Title'),
                    'prooftype' => new external_value(PARAM_ALPHANUMEXT, 'Proof type'),
                    'description' => new external_value(PARAM_RAW, 'Description HTML'),
                    'sourceurl' => new external_value(PARAM_RAW, 'Source URL'),
                    'status' => new external_value(PARAM_ALPHANUMEXT, 'Status'),
                    'visibility' => new external_value(PARAM_ALPHANUMEXT, 'Visibility'),
                    'validationstate' => new external_value(PARAM_ALPHANUMEXT, 'Validation state'),
                    'provenance' => new external_value(PARAM_ALPHANUMEXT, 'Provenance'),
                    'fileitemid' => new external_value(PARAM_INT, 'File item id'),
                    'timemodified' => new external_value(PARAM_INT, 'Time modified'),
                ])
            ),
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
