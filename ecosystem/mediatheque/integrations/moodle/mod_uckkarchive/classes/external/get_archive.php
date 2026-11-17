<?php
// This file is part of Moodle - https://moodle.org/
//
// Moodle is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// any later version.

/**
 * Return a permission-filtered archive view model.
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
 * Return a permission-filtered archive view model.
 */
class get_archive extends external_api {

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
            'tab' => new external_value(PARAM_ALPHAEXT, 'Active tab', VALUE_DEFAULT, 'items'),
        ]);
    }

    public static function execute(int $cmid, string $tab = 'items'): array {
        global $DB;
        $params = self::validate_parameters(self::execute_parameters(), ['cmid' => $cmid, 'tab' => $tab]);
        [$course, $cm, $archive, $context] = self::load_page($params['cmid']);
        self::validate_context($context);
        require_capability('mod/uckkarchive:view', $context);

        $items = [];
        foreach (\uckkarchive_get_visible_items($archive, $context, null, [], 0, 0) as $item) {
            $items[] = self::export_item($item);
        }

        $summary = \uckkarchive_get_summary($archive, $context);
        return [
            'archiveid' => (int)$archive->id,
            'cmid' => (int)$cm->id,
            'courseid' => (int)$course->id,
            'contextid' => (int)$context->id,
            'title' => format_string((string)$archive->name),
            'tab' => $params['tab'],
            'canadditem' => has_capability('mod/uckkarchive:additem', $context),
            'canvalidate' => has_capability('mod/uckkarchive:validateitem', $context),
            'canrevise' => has_capability('mod/uckkarchive:reviseitem', $context),
            'canviewrestricted' => has_capability('mod/uckkarchive:viewrestricted', $context),
            'canexport' => has_capability('mod/uckkarchive:export', $context),
            'itemcount' => count($items),
            'items' => $items,
            'summary_totalitems' => (int)$summary->totalitems,
            'summary_validateditems' => (int)$summary->validateditems,
            'summary_publisheditems' => (int)$summary->publisheditems,
            'summary_contesteditems' => (int)$summary->contesteditems,
            'warnings' => [],
        ];
    }

    public static function execute_returns(): external_single_structure {
        return new external_single_structure([
            'archiveid' => new external_value(PARAM_INT, 'Archive id'),
            'cmid' => new external_value(PARAM_INT, 'Course module id'),
            'courseid' => new external_value(PARAM_INT, 'Course id'),
            'contextid' => new external_value(PARAM_INT, 'Context id'),
            'title' => new external_value(PARAM_TEXT, 'Archive title'),
            'tab' => new external_value(PARAM_ALPHAEXT, 'Active tab'),
            'canadditem' => new external_value(PARAM_BOOL, 'Can add items'),
            'canvalidate' => new external_value(PARAM_BOOL, 'Can validate items'),
            'canrevise' => new external_value(PARAM_BOOL, 'Can revise items'),
            'canviewrestricted' => new external_value(PARAM_BOOL, 'Can view restricted items'),
            'canexport' => new external_value(PARAM_BOOL, 'Can export'),
            'itemcount' => new external_value(PARAM_INT, 'Number of visible items'),
            'items' => new external_multiple_structure(new external_single_structure([
            'id' => new external_value(PARAM_INT, 'Item id'),
            'archiveid' => new external_value(PARAM_INT, 'Archive id'),
            'courseid' => new external_value(PARAM_INT, 'Course id'),
            'cmid' => new external_value(PARAM_INT, 'Course module id'),
            'contextid' => new external_value(PARAM_INT, 'Context id'),
            'itemtype' => new external_value(PARAM_ALPHANUMEXT, 'Item type'),
            'itemtypelabel' => new external_value(PARAM_TEXT, 'Item type label'),
            'status' => new external_value(PARAM_ALPHANUMEXT, 'Status'),
            'statuslabel' => new external_value(PARAM_TEXT, 'Status label'),
            'visibility' => new external_value(PARAM_ALPHANUMEXT, 'Visibility'),
            'visibilitylabel' => new external_value(PARAM_TEXT, 'Visibility label'),
            'validationstate' => new external_value(PARAM_ALPHANUMEXT, 'Validation state'),
            'validationstatelabel' => new external_value(PARAM_TEXT, 'Validation label'),
            'provenance' => new external_value(PARAM_ALPHANUMEXT, 'Provenance'),
            'provenancelabel' => new external_value(PARAM_TEXT, 'Provenance label'),
            'title' => new external_value(PARAM_TEXT, 'Title'),
            'summaryhtml' => new external_value(PARAM_RAW, 'Summary HTML'),
            'hassummary' => new external_value(PARAM_BOOL, 'Has summary'),
            'contenthtml' => new external_value(PARAM_RAW, 'Content HTML'),
            'hascontent' => new external_value(PARAM_BOOL, 'Has content'),
            'sourcecomponent' => new external_value(PARAM_TEXT, 'Source component'),
            'sourceid' => new external_value(PARAM_INT, 'Source object id'),
            'sourceauthor' => new external_value(PARAM_TEXT, 'Source author'),
            'hasauthor' => new external_value(PARAM_BOOL, 'Has author'),
            'authorlabel' => new external_value(PARAM_TEXT, 'Author label'),
            'sourceurl' => new external_value(PARAM_RAW, 'Source URL'),
            'sourcetitle' => new external_value(PARAM_TEXT, 'Source title'),
            'sourcedatelabel' => new external_value(PARAM_TEXT, 'Source date label'),
            'timecreatedlabel' => new external_value(PARAM_TEXT, 'Created date label'),
            'timemodifiedlabel' => new external_value(PARAM_TEXT, 'Modified date label'),
            'versionno' => new external_value(PARAM_INT, 'Version number'),
            'hasversion' => new external_value(PARAM_BOOL, 'Has version'),
            'provenancehash' => new external_value(PARAM_TEXT, 'Provenance hash'),
            'hasprovenancehash' => new external_value(PARAM_BOOL, 'Has provenance hash'),
            'originlabel' => new external_value(PARAM_TEXT, 'Origin label'),
            'originurl' => new external_value(PARAM_RAW, 'Origin URL'),
            'hasorigin' => new external_value(PARAM_BOOL, 'Has origin'),
            'url' => new external_value(PARAM_RAW, 'Item URL'),
        ])),
            'summary_totalitems' => new external_value(PARAM_INT, 'Total visible items'),
            'summary_validateditems' => new external_value(PARAM_INT, 'Validated items'),
            'summary_publisheditems' => new external_value(PARAM_INT, 'Published items'),
            'summary_contesteditems' => new external_value(PARAM_INT, 'Contested items'),
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
