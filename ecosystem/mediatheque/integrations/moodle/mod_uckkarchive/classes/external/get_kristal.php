<?php
// This file is part of Moodle - https://moodle.org/
//
// Moodle is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// any later version.

/**
 * Return a Kristal linked to an archive item.
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
 * Return a Kristal linked to an archive item.
 */
class get_kristal extends external_api {

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
            'itemid' => new external_value(PARAM_INT, 'Item id', VALUE_DEFAULT, 0),
            'kristalid' => new external_value(PARAM_INT, 'Kristal id', VALUE_DEFAULT, 0),
        ]);
    }

    public static function execute(int $cmid, int $itemid = 0, int $kristalid = 0): array {
        global $DB;
        $params = self::validate_parameters(self::execute_parameters(), compact('cmid', 'itemid', 'kristalid'));
        [$course, $cm, $archive, $context] = self::load_page($params['cmid']);
        self::validate_context($context);
        require_capability('mod/uckkarchive:view', $context);

        if (!$DB->get_manager()->table_exists('uckkarchive_kristal')) {
            return ['kristal' => null, 'warnings' => self::warning('kristal', 0, 'Kristal table is not available in this build.')];
        }

        $kristal = null;
        if ($params['kristalid'] > 0) {
            $kristal = $DB->get_record('uckkarchive_kristal', ['id' => $params['kristalid'], 'archiveid' => $archive->id], '*');
        } else if ($params['itemid'] > 0) {
            $kristal = $DB->get_record('uckkarchive_kristal', ['itemid' => $params['itemid'], 'archiveid' => $archive->id], '*');
        }

        if (!$kristal) {
            return ['kristal' => null, 'warnings' => self::warning('kristal', 0, 'No Kristal record was found.')];
        }

        $visibility = \uckkarchive_normalise_visibility($kristal->visibility ?? null);
        if ($visibility === UCKKARCHIVE_VISIBILITY_RESTRICTED_INTEGRITY && !has_capability('mod/uckkarchive:viewrestricted', $context)) {
            throw new \required_capability_exception($context, 'mod/uckkarchive:viewrestricted', 'nopermissions', '');
        }

        $metadata = \uckkarchive_decode_metadata($kristal->metadata ?? null);

        return [
            'kristal' => [
                'id' => (int)$kristal->id,
                'itemid' => (int)($kristal->itemid ?? 0),
                'title' => format_string((string)$kristal->title),
                'kristaltype' => (string)$kristal->kristaltype,
                'claim' => format_text((string)($kristal->claim ?? ''), FORMAT_HTML, ['para' => false]),
                'body' => format_text((string)($kristal->body ?? ''), (int)($kristal->bodyformat ?? FORMAT_HTML), ['para' => false]),
                'evidence' => format_text((string)($kristal->evidence ?? ''), FORMAT_HTML, ['para' => false]),
                'confidence' => (int)($kristal->confidence ?? 0),
                'status' => (string)$kristal->status,
                'visibility' => (string)$kristal->visibility,
                'validationstate' => (string)$kristal->validationstate,
                'provenance' => (string)$kristal->provenance,
                'metadata' => json_encode($metadata, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES),
            ],
            'warnings' => [],
        ];
    }

    public static function execute_returns(): external_single_structure {
        return new external_single_structure([
            'kristal' => new external_single_structure([
                'id' => new external_value(PARAM_INT, 'Kristal id'),
                'itemid' => new external_value(PARAM_INT, 'Item id'),
                'title' => new external_value(PARAM_TEXT, 'Title'),
                'kristaltype' => new external_value(PARAM_ALPHANUMEXT, 'Kristal type'),
                'claim' => new external_value(PARAM_RAW, 'Claim HTML'),
                'body' => new external_value(PARAM_RAW, 'Body HTML'),
                'evidence' => new external_value(PARAM_RAW, 'Evidence HTML'),
                'confidence' => new external_value(PARAM_INT, 'Confidence'),
                'status' => new external_value(PARAM_ALPHANUMEXT, 'Status'),
                'visibility' => new external_value(PARAM_ALPHANUMEXT, 'Visibility'),
                'validationstate' => new external_value(PARAM_ALPHANUMEXT, 'Validation state'),
                'provenance' => new external_value(PARAM_ALPHANUMEXT, 'Provenance'),
                'metadata' => new external_value(PARAM_RAW, 'JSON metadata'),
            ], 'Kristal record', VALUE_OPTIONAL),
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
