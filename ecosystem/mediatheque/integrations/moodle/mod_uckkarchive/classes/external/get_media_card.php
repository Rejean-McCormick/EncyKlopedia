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
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with Moodle.  If not, see <http://www.gnu.org/licenses/>.

/**
 * External service returning rendered media card data.
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
require_once(__DIR__ . '/get_media_item.php');

use core_external\external_api;
use core_external\external_function_parameters;
use core_external\external_multiple_structure;
use core_external\external_single_structure;
use core_external\external_value;
use html_writer;
use moodle_url;
use stdClass;

/**
 * Return one permission-filtered rendered media card.
 *
 * Target service name:
 *
 * ```text
 * mod_uckkarchive_get_media_card
 * ```
 *
 * This endpoint is designed for AJAX refreshes in the media library UI.
 * It delegates media loading and policy filtering to `get_media_item`, then
 * prepares a small card context for `templates/media_card.mustache`.
 */
final class get_media_card extends external_api {
    /** Template name for full card rendering. */
    private const TEMPLATE = 'mod_uckkarchive/media_card';

    /** Fallback thumbnail file area. */
    private const AREA_THUMBNAIL = 'media_thumbnail';

    /** Fallback preview file area. */
    private const AREA_PREVIEW = 'media_preview';

    /**
     * Define parameters.
     *
     * @return external_function_parameters
     */
    public static function execute_parameters(): external_function_parameters {
        return new external_function_parameters([
            'cmid' => new external_value(PARAM_INT, 'Course module id.'),
            'mediaid' => new external_value(PARAM_INT, 'Media id. Optional when mediauuid is provided.', VALUE_DEFAULT, 0),
            'mediauuid' => new external_value(PARAM_ALPHANUMEXT, 'Media UUID. Optional when mediaid is provided.', VALUE_DEFAULT, ''),
            'includeversions' => new external_value(PARAM_BOOL, 'Include versions in source data.', VALUE_DEFAULT, false),
            'includerelations' => new external_value(PARAM_BOOL, 'Include relations in source data.', VALUE_DEFAULT, false),
            'includetags' => new external_value(PARAM_BOOL, 'Include tags in source data.', VALUE_DEFAULT, true),
            'includeadvisories' => new external_value(PARAM_BOOL, 'Include content advisory markers in source data.', VALUE_DEFAULT, true),
            'includesource' => new external_value(PARAM_BOOL, 'Include source metadata in source data.', VALUE_DEFAULT, true),
        ]);
    }

    /**
     * Execute service.
     *
     * @param int $cmid Course module id.
     * @param int $mediaid Media id.
     * @param string $mediauuid Media UUID.
     * @param bool $includeversions Include versions.
     * @param bool $includerelations Include relations.
     * @param bool $includetags Include tags.
     * @param bool $includeadvisories Include advisories.
     * @param bool $includesource Include source.
     * @return array
     */
    public static function execute(
        int $cmid,
        int $mediaid = 0,
        string $mediauuid = '',
        bool $includeversions = false,
        bool $includerelations = false,
        bool $includetags = true,
        bool $includeadvisories = true,
        bool $includesource = true
    ): array {
        global $OUTPUT;

        $params = self::validate_parameters(self::execute_parameters(), [
            'cmid' => $cmid,
            'mediaid' => $mediaid,
            'mediauuid' => $mediauuid,
            'includeversions' => $includeversions,
            'includerelations' => $includerelations,
            'includetags' => $includetags,
            'includeadvisories' => $includeadvisories,
            'includesource' => $includesource,
        ]);

        [$course, $cm, $archive, $context] = self::load_page((int)$params['cmid']);
        self::validate_context($context);

        $itemdata = get_media_item::execute(
            (int)$params['cmid'],
            (int)$params['mediaid'],
            (string)$params['mediauuid'],
            (bool)$params['includeversions'],
            (bool)$params['includerelations'],
            (bool)$params['includetags'],
            (bool)$params['includeadvisories'],
            (bool)$params['includesource']
        );

        $card = self::build_card_context($itemdata, $course, $cm, $archive, $context);
        $html = self::render_card($OUTPUT, $card);

        return [
            'media' => $itemdata['media'],
            'card' => $card,
            'templatecontext' => self::encode_json($card),
            'html' => $html,
            'warnings' => $itemdata['warnings'] ?? [],
        ];
    }

    /**
     * Define return structure.
     *
     * @return external_single_structure
     */
    public static function execute_returns(): external_single_structure {
        return new external_single_structure([
            'media' => self::media_structure(),
            'card' => self::card_structure(),
            'templatecontext' => new external_value(PARAM_RAW, 'JSON-encoded template context.'),
            'html' => new external_value(PARAM_RAW, 'Rendered HTML card.'),
            'warnings' => new external_multiple_structure(self::warning_structure(), 'Warnings.'),
        ]);
    }

    /**
     * Load Moodle page objects.
     *
     * @param int $cmid Course module id.
     * @return array{0:stdClass,1:stdClass,2:stdClass,3:\context_module}
     */
    private static function load_page(int $cmid): array {
        [$course, $cm, $archive, $context] = \uckkarchive_require_page($cmid, 0);
        return [$course, $cm, $archive, $context];
    }

    /**
     * Build template context.
     *
     * @param array $itemdata Data returned by get_media_item.
     * @param stdClass $course Course.
     * @param stdClass $cm Course module.
     * @param stdClass $archive Archive.
     * @param \context_module $context Context.
     * @return array
     */
    private static function build_card_context(
        array $itemdata,
        stdClass $course,
        stdClass $cm,
        stdClass $archive,
        \context_module $context
    ): array {
        $media = $itemdata['media'];
        $currentversion = $itemdata['currentversion'] ?? self::empty_version();
        $tags = array_values($itemdata['tags'] ?? []);
        $markers = array_values($itemdata['contentmarkers'] ?? []);
        $source = $itemdata['source'] ?? self::empty_source();

        $mediaid = (int)$media['id'];
        $title = (string)($media['title'] ?? get_string('media', 'uckkarchive'));
        $description = (string)($media['description'] ?? '');

        $viewurl = new moodle_url('/mod/uckkarchive/media.php', [
            'id' => (int)$cm->id,
            'mediaid' => $mediaid,
        ]);

        $thumbnailurl = self::first_file_url($context, self::AREA_THUMBNAIL, $mediaid, false);
        $previewurl = self::first_file_url($context, self::AREA_PREVIEW, $mediaid, false);

        $downloadurl = '';
        if (has_capability('mod/uckkarchive:downloadmedia', $context)) {
            $downloadurl = (string)($media['downloadurl'] ?? $currentversion['downloadurl'] ?? '');
        }

        $isrestricted = !empty($media['isrestricted']);
        $hasadvisory = !empty($markers);
        $canedit = has_capability('mod/uckkarchive:editmedia', $context);
        $candelete = has_capability('mod/uckkarchive:deletemedia', $context);
        $canversion = has_capability('mod/uckkarchive:versionmedia', $context);
        $canexport = has_capability('mod/uckkarchive:exportmedia', $context);
        $candownload = has_capability('mod/uckkarchive:downloadmedia', $context) && $downloadurl !== '';

        return [
            'id' => $mediaid,
            'uuid' => (string)($media['uuid'] ?? ''),
            'archiveid' => (int)($media['archiveid'] ?? $archive->id),
            'courseid' => (int)$course->id,
            'cmid' => (int)$cm->id,
            'contextid' => (int)$context->id,
            'title' => format_string($title, true, ['context' => $context]),
            'description' => format_text($description, FORMAT_HTML, ['context' => $context, 'para' => false]),
            'hasdescription' => trim(strip_tags($description)) !== '',
            'mediatype' => (string)($media['mediatype'] ?? 'other'),
            'mimetype' => (string)($media['mimetype'] ?? ''),
            'status' => (string)($media['status'] ?? 'draft'),
            'statuslabel' => self::label('status', (string)($media['status'] ?? 'draft')),
            'visibility' => (string)($media['visibility'] ?? 'course'),
            'visibilitylabel' => self::label('visibility', (string)($media['visibility'] ?? 'course')),
            'audiencesuitability' => (string)($media['audiencesuitability'] ?? 'guided'),
            'audiencesuitabilitylabel' => self::label('audiencesuitability', (string)($media['audiencesuitability'] ?? 'guided')),
            'sourceid' => (int)($media['sourceid'] ?? 0),
            'source' => $source,
            'tags' => $tags,
            'hastags' => !empty($tags),
            'contentmarkers' => $markers,
            'hasadvisory' => $hasadvisory,
            'advisorycount' => count($markers),
            'currentversion' => $currentversion,
            'hascurrentversion' => !empty($media['hascurrentversion']) || !empty($currentversion['id']),
            'thumbnailurl' => $thumbnailurl,
            'hasthumbnail' => $thumbnailurl !== '',
            'previewurl' => $previewurl,
            'haspreview' => $previewurl !== '',
            'downloadurl' => $downloadurl,
            'hasdownload' => $candownload,
            'viewurl' => $viewurl->out(false),
            'isrestricted' => $isrestricted,
            'canviewrestricted' => !empty($media['canviewrestricted']),
            'timecreated' => (int)($media['timecreated'] ?? 0),
            'timemodified' => (int)($media['timemodified'] ?? 0),
            'timecreatedformatted' => self::format_time((int)($media['timecreated'] ?? 0)),
            'timemodifiedformatted' => self::format_time((int)($media['timemodified'] ?? 0)),
            'metadatajson' => (string)($media['metadatajson'] ?? '{}'),
            'canedit' => $canedit,
            'candelete' => $candelete,
            'canversion' => $canversion,
            'canexport' => $canexport,
            'candownload' => $candownload,
            'actions' => [
                'view' => true,
                'edit' => $canedit,
                'delete' => $candelete,
                'version' => $canversion,
                'export' => $canexport,
                'download' => $candownload,
            ],
        ];
    }

    /**
     * Render the card.
     *
     * @param \renderer_base $renderer Renderer.
     * @param array $card Card context.
     * @return string
     */
    private static function render_card(\renderer_base $renderer, array $card): string {
        if (self::template_exists()) {
            return $renderer->render_from_template(self::TEMPLATE, $card);
        }

        return self::fallback_html($card);
    }

    /**
     * Return whether the target template exists.
     *
     * @return bool
     */
    private static function template_exists(): bool {
        global $CFG;

        return is_readable($CFG->dirroot . '/mod/uckkarchive/templates/media_card.mustache');
    }

    /**
     * Fallback card HTML used while template/media_card.mustache is not present.
     *
     * @param array $card Card context.
     * @return string
     */
    private static function fallback_html(array $card): string {
        $classes = ['uckkarchive-media-card'];
        if (!empty($card['isrestricted'])) {
            $classes[] = 'uckkarchive-media-card--restricted';
        }
        if (!empty($card['hasadvisory'])) {
            $classes[] = 'uckkarchive-media-card--advisory';
        }

        $title = html_writer::link(
            new moodle_url($card['viewurl']),
            s((string)$card['title']),
            ['class' => 'uckkarchive-media-card__title-link']
        );

        $badges = [];
        $badges[] = html_writer::tag('span', s((string)$card['mediatype']), ['class' => 'badge badge-secondary']);
        $badges[] = html_writer::tag('span', s((string)$card['statuslabel']), ['class' => 'badge badge-light']);
        if (!empty($card['isrestricted'])) {
            $badges[] = html_writer::tag('span', s(get_string('restricted', 'uckkarchive')), ['class' => 'badge badge-warning']);
        }
        if (!empty($card['hasadvisory'])) {
            $badges[] = html_writer::tag('span', s(get_string('contentadvisory', 'uckkarchive')), ['class' => 'badge badge-info']);
        }

        $body = html_writer::tag('h3', $title, ['class' => 'uckkarchive-media-card__title']);
        $body .= html_writer::div(implode(' ', $badges), 'uckkarchive-media-card__badges');

        if (!empty($card['hasdescription'])) {
            $body .= html_writer::div((string)$card['description'], 'uckkarchive-media-card__description');
        }

        $meta = get_string('lastmodified') . ': ' . s((string)$card['timemodifiedformatted']);
        $body .= html_writer::div($meta, 'uckkarchive-media-card__meta');

        return html_writer::tag('article', $body, [
            'class' => implode(' ', $classes),
            'data-media-id' => (string)$card['id'],
        ]);
    }

    /**
     * Return first file URL for area.
     *
     * @param \context_module $context Context.
     * @param string $filearea File area.
     * @param int $itemid File item id.
     * @param bool $forcedownload Force download.
     * @return string
     */
    private static function first_file_url(\context_module $context, string $filearea, int $itemid, bool $forcedownload): string {
        if (class_exists('\\mod_uckkarchive\\local\\media_file') &&
                method_exists('\\mod_uckkarchive\\local\\media_file', 'get_first_file_url')) {
            $url = \mod_uckkarchive\local\media_file::get_first_file_url($context, $filearea, $itemid, $forcedownload);
            return $url ? $url->out(false) : '';
        }

        $fs = get_file_storage();
        $files = $fs->get_area_files($context->id, 'mod_uckkarchive', $filearea, $itemid, 'sortorder, filename', false);

        foreach ($files as $file) {
            if ($file->is_directory()) {
                continue;
            }

            return moodle_url::make_pluginfile_url(
                $file->get_contextid(),
                $file->get_component(),
                $file->get_filearea(),
                $file->get_itemid(),
                $file->get_filepath(),
                $file->get_filename(),
                $forcedownload
            )->out(false);
        }

        return '';
    }

    /**
     * Return label for machine value.
     *
     * @param string $prefix String key prefix.
     * @param string $value Machine value.
     * @return string
     */
    private static function label(string $prefix, string $value): string {
        $key = $prefix . ':' . $value;

        if (get_string_manager()->string_exists($key, 'uckkarchive')) {
            return get_string($key, 'uckkarchive');
        }

        return ucwords(str_replace('_', ' ', $value));
    }

    /**
     * Format timestamp.
     *
     * @param int $timestamp Timestamp.
     * @return string
     */
    private static function format_time(int $timestamp): string {
        return $timestamp > 0 ? userdate($timestamp) : '';
    }

    /**
     * Encode template context.
     *
     * @param array $data Data.
     * @return string
     */
    private static function encode_json(array $data): string {
        $json = json_encode($data, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);

        return $json === false ? '{}' : $json;
    }

    /**
     * Empty version placeholder.
     *
     * @return array
     */
    private static function empty_version(): array {
        return [
            'id' => 0,
            'uuid' => '',
            'mediaid' => 0,
            'versionno' => 0,
            'status' => '',
            'filename' => '',
            'filepath' => '/',
            'filearea' => '',
            'filesize' => 0,
            'mimetype' => '',
            'contenthash' => '',
            'downloadurl' => '',
            'timecreated' => 0,
            'timemodified' => 0,
            'metadatajson' => '{}',
        ];
    }

    /**
     * Empty source placeholder.
     *
     * @return array
     */
    private static function empty_source(): array {
        return [
            'id' => 0,
            'uuid' => '',
            'mediaid' => 0,
            'sourcetype' => '',
            'ownershipstatus' => '',
            'citation' => '',
            'sourceurl' => '',
            'license' => '',
            'rightsnote' => '',
            'metadatajson' => '{}',
        ];
    }

    /**
     * Media return structure.
     *
     * @return external_single_structure
     */
    private static function media_structure(): external_single_structure {
        return new external_single_structure([
            'id' => new external_value(PARAM_INT, 'Media id.'),
            'uuid' => new external_value(PARAM_RAW, 'Media UUID.'),
            'archiveid' => new external_value(PARAM_INT, 'Archive id.'),
            'title' => new external_value(PARAM_TEXT, 'Media title.'),
            'description' => new external_value(PARAM_RAW, 'Media description.'),
            'mediatype' => new external_value(PARAM_ALPHANUMEXT, 'Media type.'),
            'mimetype' => new external_value(PARAM_RAW, 'MIME type.'),
            'status' => new external_value(PARAM_ALPHANUMEXT, 'Lifecycle status.'),
            'visibility' => new external_value(PARAM_ALPHANUMEXT, 'Visibility.'),
            'audiencesuitability' => new external_value(PARAM_ALPHANUMEXT, 'Audience suitability.'),
            'sourceid' => new external_value(PARAM_INT, 'Source id.'),
            'currentversionid' => new external_value(PARAM_INT, 'Current version id.'),
            'createdby' => new external_value(PARAM_INT, 'Creator user id.'),
            'modifiedby' => new external_value(PARAM_INT, 'Modifier user id.'),
            'timecreated' => new external_value(PARAM_INT, 'Created timestamp.'),
            'timemodified' => new external_value(PARAM_INT, 'Modified timestamp.'),
            'isrestricted' => new external_value(PARAM_BOOL, 'Whether media is restricted.'),
            'canviewrestricted' => new external_value(PARAM_BOOL, 'Whether user can view restricted media.'),
            'hascurrentversion' => new external_value(PARAM_BOOL, 'Whether media has current version.'),
            'downloadurl' => new external_value(PARAM_RAW, 'Download URL.'),
            'metadatajson' => new external_value(PARAM_RAW, 'Metadata JSON.'),
        ]);
    }

    /**
     * Card return structure.
     *
     * @return external_single_structure
     */
    private static function card_structure(): external_single_structure {
        return new external_single_structure([
            'id' => new external_value(PARAM_INT, 'Media id.'),
            'uuid' => new external_value(PARAM_RAW, 'Media UUID.'),
            'archiveid' => new external_value(PARAM_INT, 'Archive id.'),
            'courseid' => new external_value(PARAM_INT, 'Course id.'),
            'cmid' => new external_value(PARAM_INT, 'Course module id.'),
            'contextid' => new external_value(PARAM_INT, 'Context id.'),
            'title' => new external_value(PARAM_TEXT, 'Title.'),
            'description' => new external_value(PARAM_RAW, 'Description HTML.'),
            'hasdescription' => new external_value(PARAM_BOOL, 'Whether description exists.'),
            'mediatype' => new external_value(PARAM_ALPHANUMEXT, 'Media type.'),
            'mimetype' => new external_value(PARAM_RAW, 'MIME type.'),
            'status' => new external_value(PARAM_ALPHANUMEXT, 'Status.'),
            'statuslabel' => new external_value(PARAM_TEXT, 'Status label.'),
            'visibility' => new external_value(PARAM_ALPHANUMEXT, 'Visibility.'),
            'visibilitylabel' => new external_value(PARAM_TEXT, 'Visibility label.'),
            'audiencesuitability' => new external_value(PARAM_ALPHANUMEXT, 'Audience suitability.'),
            'audiencesuitabilitylabel' => new external_value(PARAM_TEXT, 'Audience suitability label.'),
            'sourceid' => new external_value(PARAM_INT, 'Source id.'),
            'source' => new external_single_structure([
                'id' => new external_value(PARAM_INT, 'Source id.'),
                'uuid' => new external_value(PARAM_RAW, 'Source UUID.'),
                'mediaid' => new external_value(PARAM_INT, 'Media id.'),
                'sourcetype' => new external_value(PARAM_ALPHANUMEXT, 'Source type.'),
                'ownershipstatus' => new external_value(PARAM_ALPHANUMEXT, 'Ownership status.'),
                'citation' => new external_value(PARAM_RAW, 'Citation.'),
                'sourceurl' => new external_value(PARAM_RAW, 'Source URL.'),
                'license' => new external_value(PARAM_TEXT, 'License.'),
                'rightsnote' => new external_value(PARAM_RAW, 'Rights note.'),
                'metadatajson' => new external_value(PARAM_RAW, 'Metadata JSON.'),
            ]),
            'tags' => new external_multiple_structure(new external_single_structure([
                'id' => new external_value(PARAM_INT, 'Tag id.'),
                'mediaid' => new external_value(PARAM_INT, 'Media id.'),
                'tag' => new external_value(PARAM_TEXT, 'Tag.'),
                'tagtype' => new external_value(PARAM_ALPHANUMEXT, 'Tag type.'),
                'timecreated' => new external_value(PARAM_INT, 'Created timestamp.'),
            ])),
            'hastags' => new external_value(PARAM_BOOL, 'Whether tags exist.'),
            'contentmarkers' => new external_multiple_structure(new external_single_structure([
                'id' => new external_value(PARAM_INT, 'Marker id.'),
                'uuid' => new external_value(PARAM_RAW, 'Marker UUID.'),
                'mediaid' => new external_value(PARAM_INT, 'Media id.'),
                'externalworkid' => new external_value(PARAM_INT, 'External work id.'),
                'tag' => new external_value(PARAM_ALPHANUMEXT, 'Content tag.'),
                'severity' => new external_value(PARAM_ALPHANUMEXT, 'Severity.'),
                'audiencesuitability' => new external_value(PARAM_ALPHANUMEXT, 'Audience suitability.'),
                'locator' => new external_value(PARAM_RAW, 'Locator text.'),
                'note' => new external_value(PARAM_RAW, 'Note.'),
                'reviewstate' => new external_value(PARAM_ALPHANUMEXT, 'Review state.'),
                'timecreated' => new external_value(PARAM_INT, 'Created timestamp.'),
                'timemodified' => new external_value(PARAM_INT, 'Modified timestamp.'),
            ])),
            'hasadvisory' => new external_value(PARAM_BOOL, 'Whether advisory markers exist.'),
            'advisorycount' => new external_value(PARAM_INT, 'Advisory count.'),
            'currentversion' => self::version_structure(),
            'hascurrentversion' => new external_value(PARAM_BOOL, 'Whether current version exists.'),
            'thumbnailurl' => new external_value(PARAM_RAW, 'Thumbnail URL.'),
            'hasthumbnail' => new external_value(PARAM_BOOL, 'Whether thumbnail exists.'),
            'previewurl' => new external_value(PARAM_RAW, 'Preview URL.'),
            'haspreview' => new external_value(PARAM_BOOL, 'Whether preview exists.'),
            'downloadurl' => new external_value(PARAM_RAW, 'Download URL.'),
            'hasdownload' => new external_value(PARAM_BOOL, 'Whether download is available.'),
            'viewurl' => new external_value(PARAM_RAW, 'View URL.'),
            'isrestricted' => new external_value(PARAM_BOOL, 'Whether restricted.'),
            'canviewrestricted' => new external_value(PARAM_BOOL, 'Can view restricted.'),
            'timecreated' => new external_value(PARAM_INT, 'Created timestamp.'),
            'timemodified' => new external_value(PARAM_INT, 'Modified timestamp.'),
            'timecreatedformatted' => new external_value(PARAM_TEXT, 'Formatted created time.'),
            'timemodifiedformatted' => new external_value(PARAM_TEXT, 'Formatted modified time.'),
            'metadatajson' => new external_value(PARAM_RAW, 'Metadata JSON.'),
            'canedit' => new external_value(PARAM_BOOL, 'Can edit.'),
            'candelete' => new external_value(PARAM_BOOL, 'Can delete.'),
            'canversion' => new external_value(PARAM_BOOL, 'Can version.'),
            'canexport' => new external_value(PARAM_BOOL, 'Can export.'),
            'candownload' => new external_value(PARAM_BOOL, 'Can download.'),
            'actions' => new external_single_structure([
                'view' => new external_value(PARAM_BOOL, 'View action.'),
                'edit' => new external_value(PARAM_BOOL, 'Edit action.'),
                'delete' => new external_value(PARAM_BOOL, 'Delete action.'),
                'version' => new external_value(PARAM_BOOL, 'Version action.'),
                'export' => new external_value(PARAM_BOOL, 'Export action.'),
                'download' => new external_value(PARAM_BOOL, 'Download action.'),
            ]),
        ]);
    }

    /**
     * Version structure.
     *
     * @return external_single_structure
     */
    private static function version_structure(): external_single_structure {
        return new external_single_structure([
            'id' => new external_value(PARAM_INT, 'Version id.'),
            'uuid' => new external_value(PARAM_RAW, 'Version UUID.'),
            'mediaid' => new external_value(PARAM_INT, 'Media id.'),
            'versionno' => new external_value(PARAM_INT, 'Version number.'),
            'status' => new external_value(PARAM_ALPHANUMEXT, 'Version status.'),
            'filename' => new external_value(PARAM_FILE, 'Filename.'),
            'filepath' => new external_value(PARAM_PATH, 'File path.'),
            'filearea' => new external_value(PARAM_ALPHANUMEXT, 'File area.'),
            'filesize' => new external_value(PARAM_INT, 'File size.'),
            'mimetype' => new external_value(PARAM_RAW, 'MIME type.'),
            'contenthash' => new external_value(PARAM_ALPHANUMEXT, 'Content hash.'),
            'downloadurl' => new external_value(PARAM_RAW, 'Download URL.'),
            'timecreated' => new external_value(PARAM_INT, 'Created timestamp.'),
            'timemodified' => new external_value(PARAM_INT, 'Modified timestamp.'),
            'metadatajson' => new external_value(PARAM_RAW, 'Metadata JSON.'),
        ]);
    }

    /**
     * Warning structure.
     *
     * @return external_single_structure
     */
    private static function warning_structure(): external_single_structure {
        return new external_single_structure([
            'item' => new external_value(PARAM_TEXT, 'Warning item.'),
            'itemid' => new external_value(PARAM_INT, 'Warning item id.'),
            'warningcode' => new external_value(PARAM_ALPHANUMEXT, 'Warning code.'),
            'message' => new external_value(PARAM_TEXT, 'Warning message.'),
        ]);
    }
}
