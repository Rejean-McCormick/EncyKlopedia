<?php
// This file is part of Moodle - https://moodle.org/.
//
// Moodle is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// any later version.

/**
 * External service for removing ordinary media tags.
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

use context_module;
use core_external\external_api;
use core_external\external_function_parameters;
use core_external\external_multiple_structure;
use core_external\external_single_structure;
use core_external\external_value;
use invalid_parameter_exception;
use mod_uckkarchive\local\media;
use mod_uckkarchive\local\media_policy;
use mod_uckkarchive\local\media_tag;
use stdClass;

/**
 * Remove one ordinary media-library tag from a media object.
 *
 * This service intentionally manages only ordinary media tags in
 * `{uckkarchive_media_tag}`. Content advisory tags, cultural protocol tags,
 * audience suitability tags, and warning markers are owned by the content
 * advisory subsystem and must be managed through content marker/tag services.
 *
 * Supported delete modes:
 *
 * - by `tagid`;
 * - by `mediaid + tagkey + tagtype`.
 *
 * Target service name:
 *
 * ```text
 * mod_uckkarchive_untag_media
 * ```
 */
final class untag_media extends external_api {
    /** Media table. */
    private const TABLE_MEDIA = 'uckkarchive_media';

    /** Media tag table. */
    private const TABLE_TAG = 'uckkarchive_media_tag';

    /**
     * Return external function parameters.
     *
     * @return external_function_parameters
     */
    public static function execute_parameters(): external_function_parameters {
        return new external_function_parameters([
            'cmid' => new external_value(PARAM_INT, 'Course module id.'),
            'mediaid' => new external_value(
                PARAM_INT,
                'Media id. Required unless tagid resolves the media id.',
                VALUE_DEFAULT,
                0
            ),
            'tagid' => new external_value(
                PARAM_INT,
                'Existing media tag id. Optional when tagkey is supplied.',
                VALUE_DEFAULT,
                0
            ),
            'tagkey' => new external_value(
                PARAM_RAW,
                'Media tag key or label to remove. Optional when tagid is supplied.',
                VALUE_DEFAULT,
                ''
            ),
            'tagtype' => new external_value(
                PARAM_ALPHANUMEXT,
                'Ordinary media tag type.',
                VALUE_DEFAULT,
                media_tag::TYPE_TOPIC
            ),
            'failifmissing' => new external_value(
                PARAM_BOOL,
                'Throw when the requested tag does not exist.',
                VALUE_DEFAULT,
                false
            ),
        ]);
    }

    /**
     * Execute the service.
     *
     * @param int $cmid Course module id.
     * @param int $mediaid Media id.
     * @param int $tagid Tag id.
     * @param string $tagkey Tag key.
     * @param string $tagtype Tag type.
     * @param bool $failifmissing Whether missing tags should throw.
     * @return array
     */
    public static function execute(
        int $cmid,
        int $mediaid = 0,
        int $tagid = 0,
        string $tagkey = '',
        string $tagtype = media_tag::TYPE_TOPIC,
        bool $failifmissing = false
    ): array {
        global $DB;

        $params = self::validate_parameters(self::execute_parameters(), [
            'cmid' => $cmid,
            'mediaid' => $mediaid,
            'tagid' => $tagid,
            'tagkey' => $tagkey,
            'tagtype' => $tagtype,
            'failifmissing' => $failifmissing,
        ]);

        [$course, $cm, $archive, $context] = self::load_page((int)$params['cmid']);
        self::validate_context($context);
        require_login($course, false, $cm);

        self::require_table(self::TABLE_MEDIA);
        self::require_table(self::TABLE_TAG);

        $tagid = max(0, (int)$params['tagid']);
        $mediaid = max(0, (int)$params['mediaid']);
        $tagkey = (string)$params['tagkey'];
        $tagtype = media_tag::normalise_type((string)$params['tagtype']);
        $failifmissing = !empty($params['failifmissing']);

        if ($tagid <= 0 && ($mediaid <= 0 || trim($tagkey) === '')) {
            throw new invalid_parameter_exception('Provide either tagid or mediaid + tagkey.');
        }

        $tag = null;

        if ($tagid > 0) {
            $tag = $DB->get_record(self::TABLE_TAG, ['id' => $tagid], '*', $failifmissing ? MUST_EXIST : IGNORE_MISSING);
            if ($tag) {
                $mediaid = (int)$tag->mediaid;
                $tagkey = (string)$tag->tagkey;
                $tagtype = (string)$tag->tagtype;
            }
        } else {
            $normalisedkey = media_tag::normalise_key($tagkey);
            media_tag::validate_key($normalisedkey);

            $tag = $DB->get_record(self::TABLE_TAG, [
                'mediaid' => $mediaid,
                'tagkey' => $normalisedkey,
                'tagtype' => $tagtype,
            ], '*', $failifmissing ? MUST_EXIST : IGNORE_MISSING);

            $tagkey = $normalisedkey;
        }

        if ($mediaid <= 0) {
            throw new invalid_parameter_exception('Unable to resolve media id for tag removal.');
        }

        $media = self::get_media_record($mediaid);
        self::require_media_belongs_to_archive($media, (int)$archive->id);
        self::require_edit_media($context, $media);

        $deleted = false;
        $deletedtagid = 0;

        if ($tag) {
            if ((int)$tag->mediaid !== $mediaid) {
                throw new invalid_parameter_exception('The tag does not belong to the supplied media record.');
            }

            $deletedtagid = (int)$tag->id;

            $transaction = $DB->start_delegated_transaction();
            $deleted = media_tag::delete((int)$tag->id);
            $transaction->allow_commit();
        }

        $remaining = media_tag::export_list(
            media_tag::list_for_media($mediaid),
            has_capability('mod/uckkarchive:editmedia', $context)
        );

        return [
            'deleted' => $deleted,
            'tagid' => $deletedtagid,
            'mediaid' => $mediaid,
            'tagkey' => (string)$tagkey,
            'tagtype' => $tagtype,
            'tags' => $remaining,
            'permissions' => self::get_permissions($context, $media),
            'warnings' => $deleted ? [] : [
                self::warning(
                    'media_tag',
                    $tagid,
                    'tagnotfound',
                    'The requested media tag was not found.'
                ),
            ],
        ];
    }

    /**
     * Return external function response structure.
     *
     * @return external_single_structure
     */
    public static function execute_returns(): external_single_structure {
        return new external_single_structure([
            'deleted' => new external_value(PARAM_BOOL, 'Whether a tag record was deleted.'),
            'tagid' => new external_value(PARAM_INT, 'Deleted tag id, or 0 when no tag was deleted.'),
            'mediaid' => new external_value(PARAM_INT, 'Media id.'),
            'tagkey' => new external_value(PARAM_RAW, 'Normalized tag key.'),
            'tagtype' => new external_value(PARAM_ALPHANUMEXT, 'Tag type.'),
            'tags' => new external_multiple_structure(self::tag_structure(), 'Remaining media tags.'),
            'permissions' => self::permissions_structure(),
            'warnings' => self::warnings_structure(),
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
            'uuid' => new external_value(PARAM_RAW, 'Stable UUID.'),
            'mediaid' => new external_value(PARAM_INT, 'Media id.'),
            'tagkey' => new external_value(PARAM_RAW, 'Normalized tag key.'),
            'label' => new external_value(PARAM_TEXT, 'Display label.'),
            'tagtype' => new external_value(PARAM_ALPHANUMEXT, 'Tag type.'),
            'source' => new external_value(PARAM_ALPHANUMEXT, 'Tag source.'),
            'weight' => new external_value(PARAM_INT, 'Tag weight.'),
            'userid' => new external_value(PARAM_INT, 'User id associated with tag.'),
            'timecreated' => new external_value(PARAM_INT, 'Creation timestamp.'),
            'timemodified' => new external_value(PARAM_INT, 'Modified timestamp.'),
            'metadata' => new external_value(PARAM_RAW, 'Optional metadata JSON or object.', VALUE_OPTIONAL),
        ]);
    }

    /**
     * Return permissions structure.
     *
     * @return external_single_structure
     */
    private static function permissions_structure(): external_single_structure {
        return new external_single_structure([
            'viewmedia' => new external_value(PARAM_BOOL, 'Can view media.'),
            'editmedia' => new external_value(PARAM_BOOL, 'Can edit media.'),
            'viewrestrictedmedia' => new external_value(PARAM_BOOL, 'Can view restricted media.'),
            'manageadvisories' => new external_value(PARAM_BOOL, 'Can manage content advisories.'),
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
     * Load course, cm, archive and context.
     *
     * @param int $cmid Course module id.
     * @return array{0:stdClass,1:stdClass,2:stdClass,3:context_module}
     */
    private static function load_page(int $cmid): array {
        if ($cmid <= 0) {
            throw new invalid_parameter_exception('cmid must be a positive integer.');
        }

        [$course, $cm, $archive, $context] = \uckkarchive_require_page($cmid, 0);

        return [$course, $cm, $archive, $context];
    }

    /**
     * Load a media record.
     *
     * @param int $mediaid Media id.
     * @return stdClass
     */
    private static function get_media_record(int $mediaid): stdClass {
        global $DB;

        if ($mediaid <= 0) {
            throw new invalid_parameter_exception('mediaid must be a positive integer.');
        }

        if (class_exists(media::class) && method_exists(media::class, 'get_record')) {
            return media::get_record($mediaid, MUST_EXIST);
        }

        return $DB->get_record(self::TABLE_MEDIA, ['id' => $mediaid], '*', MUST_EXIST);
    }

    /**
     * Require that media belongs to the current archive when schema exposes it.
     *
     * @param stdClass $media Media record.
     * @param int $archiveid Archive id.
     * @return void
     */
    private static function require_media_belongs_to_archive(stdClass $media, int $archiveid): void {
        foreach (['archiveid', 'uckkarchiveid'] as $field) {
            if (property_exists($media, $field)) {
                if ((int)$media->{$field} !== $archiveid) {
                    throw new invalid_parameter_exception('Media does not belong to this UCKK Archive instance.');
                }

                return;
            }
        }
    }

    /**
     * Require authority to edit media tags.
     *
     * @param context_module $context Context.
     * @param stdClass $media Media record.
     * @return void
     */
    private static function require_edit_media(context_module $context, stdClass $media): void {
        if (class_exists(media_policy::class) && method_exists(media_policy::class, 'require_edit_media')) {
            media_policy::require_edit_media($context, $media);
            return;
        }

        require_capability('mod/uckkarchive:editmedia', $context);
    }

    /**
     * Return permissions.
     *
     * @param context_module $context Context.
     * @param stdClass $media Media record.
     * @return array
     */
    private static function get_permissions(context_module $context, stdClass $media): array {
        $canedit = false;

        if (class_exists(media_policy::class) && method_exists(media_policy::class, 'can_edit_media')) {
            $canedit = media_policy::can_edit_media($context, $media);
        } else {
            $canedit = has_capability('mod/uckkarchive:editmedia', $context);
        }

        return [
            'viewmedia' => has_capability('mod/uckkarchive:viewmedia', $context),
            'editmedia' => $canedit,
            'viewrestrictedmedia' => has_capability('mod/uckkarchive:viewrestrictedmedia', $context),
            'manageadvisories' => has_capability('mod/uckkarchive:manageadvisories', $context),
        ];
    }

    /**
     * Return a warning payload.
     *
     * @param string $item Item.
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
     * Require a table.
     *
     * @param string $table Table name.
     * @return void
     */
    private static function require_table(string $table): void {
        global $DB;

        if (!$DB->get_manager()->table_exists(new \xmldb_table($table))) {
            throw new \coding_exception('Missing required table {' . $table . '}.');
        }
    }
}
