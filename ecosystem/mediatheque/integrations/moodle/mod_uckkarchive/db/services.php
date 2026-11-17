<?php
// This file is part of Moodle - https://moodle.org/
//
// Moodle is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// any later version.

/**
 * External service declarations for UCKK Archives.
 *
 * @package    mod_uckkarchive
 * @copyright  2026 Univers-Cité King Klown
 * @license    https://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later
 */

defined('MOODLE_INTERNAL') || die();

$functions = [
    // -------------------------------------------------------------------------
    // Archive read services.
    // -------------------------------------------------------------------------

    'mod_uckkarchive_get_archive' => [
        'classname' => 'mod_uckkarchive\external\get_archive',
        'methodname' => 'execute',
        'classpath' => '',
        'description' => 'Return a permission-filtered UCKK archive activity view model.',
        'type' => 'read',
        'ajax' => true,
        'capabilities' => 'mod/uckkarchive:view',
        'services' => [
            MOODLE_OFFICIAL_MOBILE_SERVICE,
        ],
    ],

    'mod_uckkarchive_get_archive_items' => [
        'classname' => 'mod_uckkarchive\external\get_archive_items',
        'methodname' => 'execute',
        'classpath' => '',
        'description' => 'Return permission-filtered archive items for a UCKK archive activity.',
        'type' => 'read',
        'ajax' => true,
        'capabilities' => 'mod/uckkarchive:view',
        'services' => [
            MOODLE_OFFICIAL_MOBILE_SERVICE,
        ],
    ],

    'mod_uckkarchive_get_archive_item' => [
        'classname' => 'mod_uckkarchive\external\get_archive_item',
        'methodname' => 'execute',
        'classpath' => '',
        'description' => 'Return a permission-filtered UCKK archive item view model.',
        'type' => 'read',
        'ajax' => true,
        'capabilities' => 'mod/uckkarchive:view',
        'services' => [
            MOODLE_OFFICIAL_MOBILE_SERVICE,
        ],
    ],

    'mod_uckkarchive_get_archive_item_card' => [
        'classname' => 'mod_uckkarchive\external\get_archive_item_card',
        'methodname' => 'execute',
        'classpath' => '',
        'description' => 'Return rendered card data for one permission-filtered UCKK archive item.',
        'type' => 'read',
        'ajax' => true,
        'capabilities' => 'mod/uckkarchive:view',
        'services' => [
            MOODLE_OFFICIAL_MOBILE_SERVICE,
        ],
    ],

    'mod_uckkarchive_get_proofs' => [
        'classname' => 'mod_uckkarchive\external\get_proofs',
        'methodname' => 'execute',
        'classpath' => '',
        'description' => 'Return permission-filtered proof records linked to a UCKK archive item.',
        'type' => 'read',
        'ajax' => true,
        'capabilities' => 'mod/uckkarchive:view',
        'services' => [
            MOODLE_OFFICIAL_MOBILE_SERVICE,
        ],
    ],

    'mod_uckkarchive_get_provenance_panel' => [
        'classname' => 'mod_uckkarchive\external\get_provenance_panel',
        'methodname' => 'execute',
        'classpath' => '',
        'description' => 'Return provenance, source, validation, and visibility data for a UCKK archive item.',
        'type' => 'read',
        'ajax' => true,
        'capabilities' => 'mod/uckkarchive:view',
        'services' => [
            MOODLE_OFFICIAL_MOBILE_SERVICE,
        ],
    ],

    'mod_uckkarchive_get_kristal' => [
        'classname' => 'mod_uckkarchive\external\get_kristal',
        'methodname' => 'execute',
        'classpath' => '',
        'description' => 'Return a permission-filtered UCKK Kristal view model.',
        'type' => 'read',
        'ajax' => true,
        'capabilities' => 'mod/uckkarchive:view',
        'services' => [
            MOODLE_OFFICIAL_MOBILE_SERVICE,
        ],
    ],

    'mod_uckkarchive_get_revisions' => [
        'classname' => 'mod_uckkarchive\external\get_revisions',
        'methodname' => 'execute',
        'classpath' => '',
        'description' => 'Return permission-filtered revision history for a UCKK archive item.',
        'type' => 'read',
        'ajax' => true,
        'capabilities' => 'mod/uckkarchive:view',
        'services' => [
            MOODLE_OFFICIAL_MOBILE_SERVICE,
        ],
    ],

    'mod_uckkarchive_get_restricted_item' => [
        'classname' => 'mod_uckkarchive\external\get_restricted_item',
        'methodname' => 'execute',
        'classpath' => '',
        'description' => 'Return a restricted UCKK archive item for authorised restricted viewers.',
        'type' => 'read',
        'ajax' => true,
        'capabilities' => 'mod/uckkarchive:viewrestricted',
        'services' => [
            MOODLE_OFFICIAL_MOBILE_SERVICE,
        ],
    ],

    // -------------------------------------------------------------------------
    // Archive write/workflow services.
    // -------------------------------------------------------------------------

    'mod_uckkarchive_save_item_draft' => [
        'classname' => 'mod_uckkarchive\external\save_item_draft',
        'methodname' => 'execute',
        'classpath' => '',
        'description' => 'Save a draft UCKK archive item without validating or publishing it.',
        'type' => 'write',
        'ajax' => true,
        'capabilities' => 'mod/uckkarchive:additem',
        'services' => [
            MOODLE_OFFICIAL_MOBILE_SERVICE,
        ],
    ],

    'mod_uckkarchive_add_item' => [
        'classname' => 'mod_uckkarchive\external\add_item',
        'methodname' => 'execute',
        'classpath' => '',
        'description' => 'Create a UCKK archive item with provenance, visibility, validation, and context metadata.',
        'type' => 'write',
        'ajax' => true,
        'capabilities' => 'mod/uckkarchive:additem',
        'services' => [
            MOODLE_OFFICIAL_MOBILE_SERVICE,
        ],
    ],

    'mod_uckkarchive_add_proof' => [
        'classname' => 'mod_uckkarchive\external\add_proof',
        'methodname' => 'execute',
        'classpath' => '',
        'description' => 'Attach a proof record to a UCKK archive item.',
        'type' => 'write',
        'ajax' => true,
        'capabilities' => 'mod/uckkarchive:additem',
        'services' => [
            MOODLE_OFFICIAL_MOBILE_SERVICE,
        ],
    ],

    'mod_uckkarchive_update_provenance' => [
        'classname' => 'mod_uckkarchive\external\update_provenance',
        'methodname' => 'execute',
        'classpath' => '',
        'description' => 'Update provenance metadata for a UCKK archive item or proof record.',
        'type' => 'write',
        'ajax' => true,
        'capabilities' => 'mod/uckkarchive:reviseitem',
        'services' => [
            MOODLE_OFFICIAL_MOBILE_SERVICE,
        ],
    ],

    'mod_uckkarchive_validate_item' => [
        'classname' => 'mod_uckkarchive\external\validate_item',
        'methodname' => 'execute',
        'classpath' => '',
        'description' => 'Record authorised human validation for a UCKK archive item.',
        'type' => 'write',
        'ajax' => true,
        'capabilities' => 'mod/uckkarchive:validateitem',
        'services' => [
            MOODLE_OFFICIAL_MOBILE_SERVICE,
        ],
    ],

    'mod_uckkarchive_revise_item' => [
        'classname' => 'mod_uckkarchive\external\revise_item',
        'methodname' => 'execute',
        'classpath' => '',
        'description' => 'Create a versioned revision of a UCKK archive item without deleting prior evidence.',
        'type' => 'write',
        'ajax' => true,
        'capabilities' => 'mod/uckkarchive:reviseitem',
        'services' => [
            MOODLE_OFFICIAL_MOBILE_SERVICE,
        ],
    ],

    'mod_uckkarchive_create_kristal' => [
        'classname' => 'mod_uckkarchive\external\create_kristal',
        'methodname' => 'execute',
        'classpath' => '',
        'description' => 'Create a UCKK Kristal from selected archive items.',
        'type' => 'write',
        'ajax' => true,
        'capabilities' => 'mod/uckkarchive:validateitem',
        'services' => [
            MOODLE_OFFICIAL_MOBILE_SERVICE,
        ],
    ],

    'mod_uckkarchive_update_kristal' => [
        'classname' => 'mod_uckkarchive\external\update_kristal',
        'methodname' => 'execute',
        'classpath' => '',
        'description' => 'Update a UCKK Kristal through authorised archive workflow.',
        'type' => 'write',
        'ajax' => true,
        'capabilities' => 'mod/uckkarchive:reviseitem',
        'services' => [
            MOODLE_OFFICIAL_MOBILE_SERVICE,
        ],
    ],

    // -------------------------------------------------------------------------
    // Media library services.
    // -------------------------------------------------------------------------

    'mod_uckkarchive_get_media' => [
        'classname' => 'mod_uckkarchive\external\get_media',
        'methodname' => 'execute',
        'classpath' => '',
        'description' => 'Return a permission-filtered media library list for a UCKK archive activity.',
        'type' => 'read',
        'ajax' => true,
        'capabilities' => 'mod/uckkarchive:viewmedia',
        'services' => [
            MOODLE_OFFICIAL_MOBILE_SERVICE,
        ],
    ],

    'mod_uckkarchive_search_media' => [
        'classname' => 'mod_uckkarchive\external\search_media',
        'methodname' => 'execute',
        'classpath' => '',
        'description' => 'Search permission-filtered media records in a UCKK archive activity.',
        'type' => 'read',
        'ajax' => true,
        'capabilities' => 'mod/uckkarchive:viewmedia',
        'services' => [
            MOODLE_OFFICIAL_MOBILE_SERVICE,
        ],
    ],

    'mod_uckkarchive_search_mediatheque' => [
        'classname' => 'mod_uckkarchive\external\search_mediatheque',
        'methodname' => 'execute',
        'classpath' => '',
        'description' => 'Search public UCKK Médiathèque media for the public local_uckk explorer.',
        'type' => 'read',
        'ajax' => true,
        'loginrequired' => false,
    ],

    'mod_uckkarchive_get_media_item' => [
        'classname' => 'mod_uckkarchive\external\get_media_item',
        'methodname' => 'execute',
        'classpath' => '',
        'description' => 'Return one permission-filtered media item with metadata and advisory state.',
        'type' => 'read',
        'ajax' => true,
        'capabilities' => 'mod/uckkarchive:viewmedia',
        'services' => [
            MOODLE_OFFICIAL_MOBILE_SERVICE,
        ],
    ],

    'mod_uckkarchive_get_media_card' => [
        'classname' => 'mod_uckkarchive\external\get_media_card',
        'methodname' => 'execute',
        'classpath' => '',
        'description' => 'Return rendered card data for one permission-filtered media item.',
        'type' => 'read',
        'ajax' => true,
        'capabilities' => 'mod/uckkarchive:viewmedia',
        'services' => [
            MOODLE_OFFICIAL_MOBILE_SERVICE,
        ],
    ],

    'mod_uckkarchive_add_media' => [
        'classname' => 'mod_uckkarchive\external\add_media',
        'methodname' => 'execute',
        'classpath' => '',
        'description' => 'Create a media record in a UCKK archive activity.',
        'type' => 'write',
        'ajax' => true,
        'capabilities' => 'mod/uckkarchive:addmedia',
        'services' => [
            MOODLE_OFFICIAL_MOBILE_SERVICE,
        ],
    ],

    'mod_uckkarchive_update_media' => [
        'classname' => 'mod_uckkarchive\external\update_media',
        'methodname' => 'execute',
        'classpath' => '',
        'description' => 'Update an existing media record in a UCKK archive activity.',
        'type' => 'write',
        'ajax' => true,
        'capabilities' => 'mod/uckkarchive:editmedia',
        'services' => [
            MOODLE_OFFICIAL_MOBILE_SERVICE,
        ],
    ],

    'mod_uckkarchive_delete_media' => [
        'classname' => 'mod_uckkarchive\external\delete_media',
        'methodname' => 'execute',
        'classpath' => '',
        'description' => 'Soft-delete or delete an authorised media record.',
        'type' => 'write',
        'ajax' => true,
        'capabilities' => 'mod/uckkarchive:deletemedia',
        'services' => [
            MOODLE_OFFICIAL_MOBILE_SERVICE,
        ],
    ],

    'mod_uckkarchive_add_media_version' => [
        'classname' => 'mod_uckkarchive\external\add_media_version',
        'methodname' => 'execute',
        'classpath' => '',
        'description' => 'Create a new version record for an existing media item.',
        'type' => 'write',
        'ajax' => true,
        'capabilities' => 'mod/uckkarchive:versionmedia',
        'services' => [
            MOODLE_OFFICIAL_MOBILE_SERVICE,
        ],
    ],

    'mod_uckkarchive_get_media_versions' => [
        'classname' => 'mod_uckkarchive\external\get_media_versions',
        'methodname' => 'execute',
        'classpath' => '',
        'description' => 'Return version history and permission-filtered file metadata for a media item.',
        'type' => 'read',
        'ajax' => true,
        'capabilities' => 'mod/uckkarchive:viewmedia',
        'services' => [
            MOODLE_OFFICIAL_MOBILE_SERVICE,
        ],
    ],

    // -------------------------------------------------------------------------
    // Media collection services.
    // -------------------------------------------------------------------------

    'mod_uckkarchive_get_media_collections' => [
        'classname' => 'mod_uckkarchive\external\get_media_collections',
        'methodname' => 'execute',
        'classpath' => '',
        'description' => 'Return permission-filtered media collections for a UCKK archive activity.',
        'type' => 'read',
        'ajax' => true,
        'capabilities' => 'mod/uckkarchive:viewmedia',
        'services' => [
            MOODLE_OFFICIAL_MOBILE_SERVICE,
        ],
    ],

    'mod_uckkarchive_get_media_collection' => [
        'classname' => 'mod_uckkarchive\external\get_media_collection',
        'methodname' => 'execute',
        'classpath' => '',
        'description' => 'Return one permission-filtered media collection and its items.',
        'type' => 'read',
        'ajax' => true,
        'capabilities' => 'mod/uckkarchive:viewmedia',
        'services' => [
            MOODLE_OFFICIAL_MOBILE_SERVICE,
        ],
    ],

    'mod_uckkarchive_add_media_collection' => [
        'classname' => 'mod_uckkarchive\external\add_media_collection',
        'methodname' => 'execute',
        'classpath' => '',
        'description' => 'Create a media collection in a UCKK archive activity.',
        'type' => 'write',
        'ajax' => true,
        'capabilities' => 'mod/uckkarchive:managemediacollections',
        'services' => [
            MOODLE_OFFICIAL_MOBILE_SERVICE,
        ],
    ],

    'mod_uckkarchive_update_media_collection' => [
        'classname' => 'mod_uckkarchive\external\update_media_collection',
        'methodname' => 'execute',
        'classpath' => '',
        'description' => 'Update a media collection in a UCKK archive activity.',
        'type' => 'write',
        'ajax' => true,
        'capabilities' => 'mod/uckkarchive:managemediacollections',
        'services' => [
            MOODLE_OFFICIAL_MOBILE_SERVICE,
        ],
    ],

    'mod_uckkarchive_add_media_to_collection' => [
        'classname' => 'mod_uckkarchive\external\add_media_to_collection',
        'methodname' => 'execute',
        'classpath' => '',
        'description' => 'Add a media item to a media collection.',
        'type' => 'write',
        'ajax' => true,
        'capabilities' => 'mod/uckkarchive:managemediacollections',
        'services' => [
            MOODLE_OFFICIAL_MOBILE_SERVICE,
        ],
    ],

    'mod_uckkarchive_remove_media_from_collection' => [
        'classname' => 'mod_uckkarchive\external\remove_media_from_collection',
        'methodname' => 'execute',
        'classpath' => '',
        'description' => 'Remove a media item from a media collection.',
        'type' => 'write',
        'ajax' => true,
        'capabilities' => 'mod/uckkarchive:managemediacollections',
        'services' => [
            MOODLE_OFFICIAL_MOBILE_SERVICE,
        ],
    ],

    // -------------------------------------------------------------------------
    // Media relation and tag services.
    // -------------------------------------------------------------------------

    'mod_uckkarchive_get_media_relations' => [
        'classname' => 'mod_uckkarchive\external\get_media_relations',
        'methodname' => 'execute',
        'classpath' => '',
        'description' => 'Return permission-filtered media relation records.',
        'type' => 'read',
        'ajax' => true,
        'capabilities' => 'mod/uckkarchive:viewmedia',
        'services' => [
            MOODLE_OFFICIAL_MOBILE_SERVICE,
        ],
    ],

    'mod_uckkarchive_add_media_relation' => [
        'classname' => 'mod_uckkarchive\external\add_media_relation',
        'methodname' => 'execute',
        'classpath' => '',
        'description' => 'Create a relation between media records or between media and external works.',
        'type' => 'write',
        'ajax' => true,
        'capabilities' => 'mod/uckkarchive:editmedia',
        'services' => [
            MOODLE_OFFICIAL_MOBILE_SERVICE,
        ],
    ],

    'mod_uckkarchive_remove_media_relation' => [
        'classname' => 'mod_uckkarchive\external\remove_media_relation',
        'methodname' => 'execute',
        'classpath' => '',
        'description' => 'Remove a media relation record.',
        'type' => 'write',
        'ajax' => true,
        'capabilities' => 'mod/uckkarchive:editmedia',
        'services' => [
            MOODLE_OFFICIAL_MOBILE_SERVICE,
        ],
    ],

    'mod_uckkarchive_tag_media' => [
        'classname' => 'mod_uckkarchive\external\tag_media',
        'methodname' => 'execute',
        'classpath' => '',
        'description' => 'Attach a tag to a media record.',
        'type' => 'write',
        'ajax' => true,
        'capabilities' => 'mod/uckkarchive:editmedia',
        'services' => [
            MOODLE_OFFICIAL_MOBILE_SERVICE,
        ],
    ],

    'mod_uckkarchive_untag_media' => [
        'classname' => 'mod_uckkarchive\external\untag_media',
        'methodname' => 'execute',
        'classpath' => '',
        'description' => 'Remove a tag from a media record.',
        'type' => 'write',
        'ajax' => true,
        'capabilities' => 'mod/uckkarchive:editmedia',
        'services' => [
            MOODLE_OFFICIAL_MOBILE_SERVICE,
        ],
    ],

    // -------------------------------------------------------------------------
    // Content advisory services.
    // -------------------------------------------------------------------------

    'mod_uckkarchive_get_content_markers' => [
        'classname' => 'mod_uckkarchive\external\get_content_markers',
        'methodname' => 'execute',
        'classpath' => '',
        'description' => 'Return permission-filtered content advisory markers.',
        'type' => 'read',
        'ajax' => true,
        'capabilities' => 'mod/uckkarchive:viewadvisories',
        'services' => [
            MOODLE_OFFICIAL_MOBILE_SERVICE,
        ],
    ],

    'mod_uckkarchive_add_content_marker' => [
        'classname' => 'mod_uckkarchive\external\add_content_marker',
        'methodname' => 'execute',
        'classpath' => '',
        'description' => 'Create a content advisory marker for media or an external work.',
        'type' => 'write',
        'ajax' => true,
        'capabilities' => 'mod/uckkarchive:manageadvisories',
        'services' => [
            MOODLE_OFFICIAL_MOBILE_SERVICE,
        ],
    ],

    'mod_uckkarchive_update_content_marker' => [
        'classname' => 'mod_uckkarchive\external\update_content_marker',
        'methodname' => 'execute',
        'classpath' => '',
        'description' => 'Update a content advisory marker.',
        'type' => 'write',
        'ajax' => true,
        'capabilities' => 'mod/uckkarchive:manageadvisories',
        'services' => [
            MOODLE_OFFICIAL_MOBILE_SERVICE,
        ],
    ],

    'mod_uckkarchive_delete_content_marker' => [
        'classname' => 'mod_uckkarchive\external\delete_content_marker',
        'methodname' => 'execute',
        'classpath' => '',
        'description' => 'Delete or retire a content advisory marker.',
        'type' => 'write',
        'ajax' => true,
        'capabilities' => 'mod/uckkarchive:manageadvisories',
        'services' => [
            MOODLE_OFFICIAL_MOBILE_SERVICE,
        ],
    ],

    'mod_uckkarchive_review_content_marker' => [
        'classname' => 'mod_uckkarchive\external\review_content_marker',
        'methodname' => 'execute',
        'classpath' => '',
        'description' => 'Record authorised human review of a content advisory marker.',
        'type' => 'write',
        'ajax' => true,
        'capabilities' => 'mod/uckkarchive:reviewadvisories',
        'services' => [
            MOODLE_OFFICIAL_MOBILE_SERVICE,
        ],
    ],

    'mod_uckkarchive_get_content_tags' => [
        'classname' => 'mod_uckkarchive\external\get_content_tags',
        'methodname' => 'execute',
        'classpath' => '',
        'description' => 'Return content advisory tags available to the current user.',
        'type' => 'read',
        'ajax' => true,
        'capabilities' => 'mod/uckkarchive:viewadvisories',
        'services' => [
            MOODLE_OFFICIAL_MOBILE_SERVICE,
        ],
    ],

    'mod_uckkarchive_get_content_tag_sets' => [
        'classname' => 'mod_uckkarchive\external\get_content_tag_sets',
        'methodname' => 'execute',
        'classpath' => '',
        'description' => 'Return content advisory tag sets available to the current user.',
        'type' => 'read',
        'ajax' => true,
        'capabilities' => 'mod/uckkarchive:viewadvisories',
        'services' => [
            MOODLE_OFFICIAL_MOBILE_SERVICE,
        ],
    ],

    // -------------------------------------------------------------------------
    // External work services.
    // -------------------------------------------------------------------------

    'mod_uckkarchive_get_external_works' => [
        'classname' => 'mod_uckkarchive\external\get_external_works',
        'methodname' => 'execute',
        'classpath' => '',
        'description' => 'Return permission-filtered external work references.',
        'type' => 'read',
        'ajax' => true,
        'capabilities' => 'mod/uckkarchive:viewmedia',
        'services' => [
            MOODLE_OFFICIAL_MOBILE_SERVICE,
        ],
    ],

    'mod_uckkarchive_get_external_work' => [
        'classname' => 'mod_uckkarchive\external\get_external_work',
        'methodname' => 'execute',
        'classpath' => '',
        'description' => 'Return one permission-filtered external work reference.',
        'type' => 'read',
        'ajax' => true,
        'capabilities' => 'mod/uckkarchive:viewmedia',
        'services' => [
            MOODLE_OFFICIAL_MOBILE_SERVICE,
        ],
    ],

    'mod_uckkarchive_add_external_work' => [
        'classname' => 'mod_uckkarchive\external\add_external_work',
        'methodname' => 'execute',
        'classpath' => '',
        'description' => 'Create an external work reference for media, provenance, or content advisory use.',
        'type' => 'write',
        'ajax' => true,
        'capabilities' => 'mod/uckkarchive:manageadvisories',
        'services' => [
            MOODLE_OFFICIAL_MOBILE_SERVICE,
        ],
    ],

    'mod_uckkarchive_update_external_work' => [
        'classname' => 'mod_uckkarchive\external\update_external_work',
        'methodname' => 'execute',
        'classpath' => '',
        'description' => 'Update an external work reference.',
        'type' => 'write',
        'ajax' => true,
        'capabilities' => 'mod/uckkarchive:manageadvisories',
        'services' => [
            MOODLE_OFFICIAL_MOBILE_SERVICE,
        ],
    ],

    // -------------------------------------------------------------------------
    // Export services.
    // -------------------------------------------------------------------------

    'mod_uckkarchive_get_export_preview' => [
        'classname' => 'mod_uckkarchive\external\get_export_preview',
        'methodname' => 'execute',
        'classpath' => '',
        'description' => 'Return a permission-filtered preview of a UCKK archive export package.',
        'type' => 'read',
        'ajax' => true,
        'capabilities' => 'mod/uckkarchive:export',
        'services' => [
            MOODLE_OFFICIAL_MOBILE_SERVICE,
        ],
    ],

    'mod_uckkarchive_export_items' => [
        'classname' => 'mod_uckkarchive\external\export_items',
        'methodname' => 'execute',
        'classpath' => '',
        'description' => 'Create a UCKK archive export package for authorised archive items.',
        'type' => 'write',
        'ajax' => true,
        'capabilities' => 'mod/uckkarchive:export',
        'services' => [
            MOODLE_OFFICIAL_MOBILE_SERVICE,
        ],
    ],

    'mod_uckkarchive_export_media' => [
        'classname' => 'mod_uckkarchive\external\export_media',
        'methodname' => 'execute',
        'classpath' => '',
        'description' => 'Create a UCKK archive export package for authorised media records.',
        'type' => 'write',
        'ajax' => true,
        'capabilities' => 'mod/uckkarchive:exportmedia',
        'services' => [
            MOODLE_OFFICIAL_MOBILE_SERVICE,
        ],
    ],

    'mod_uckkarchive_export_collection' => [
        'classname' => 'mod_uckkarchive\external\export_collection',
        'methodname' => 'execute',
        'classpath' => '',
        'description' => 'Create a UCKK archive export package for an authorised media collection.',
        'type' => 'write',
        'ajax' => true,
        'capabilities' => 'mod/uckkarchive:exportmedia',
        'services' => [
            MOODLE_OFFICIAL_MOBILE_SERVICE,
        ],
    ],

    'mod_uckkarchive_get_export_status' => [
        'classname' => 'mod_uckkarchive\external\get_export_status',
        'methodname' => 'execute',
        'classpath' => '',
        'description' => 'Return the status of a UCKK archive export package.',
        'type' => 'read',
        'ajax' => true,
        'capabilities' => 'mod/uckkarchive:export',
        'services' => [
            MOODLE_OFFICIAL_MOBILE_SERVICE,
        ],
    ],
];

$services = [
    'UCKK archive service' => [
        'functions' => [
            // Archive read services.
            'mod_uckkarchive_get_archive',
            'mod_uckkarchive_get_archive_items',
            'mod_uckkarchive_get_archive_item',
            'mod_uckkarchive_get_archive_item_card',
            'mod_uckkarchive_get_proofs',
            'mod_uckkarchive_get_provenance_panel',
            'mod_uckkarchive_get_kristal',
            'mod_uckkarchive_get_revisions',
            'mod_uckkarchive_get_restricted_item',

            // Archive write/workflow services.
            'mod_uckkarchive_save_item_draft',
            'mod_uckkarchive_add_item',
            'mod_uckkarchive_add_proof',
            'mod_uckkarchive_update_provenance',
            'mod_uckkarchive_validate_item',
            'mod_uckkarchive_revise_item',
            'mod_uckkarchive_create_kristal',
            'mod_uckkarchive_update_kristal',

            // Media library services.
            'mod_uckkarchive_get_media',
            'mod_uckkarchive_search_media',
            'mod_uckkarchive_search_mediatheque',
            'mod_uckkarchive_get_media_item',
            'mod_uckkarchive_get_media_card',
            'mod_uckkarchive_add_media',
            'mod_uckkarchive_update_media',
            'mod_uckkarchive_delete_media',
            'mod_uckkarchive_add_media_version',
            'mod_uckkarchive_get_media_versions',

            // Media collection services.
            'mod_uckkarchive_get_media_collections',
            'mod_uckkarchive_get_media_collection',
            'mod_uckkarchive_add_media_collection',
            'mod_uckkarchive_update_media_collection',
            'mod_uckkarchive_add_media_to_collection',
            'mod_uckkarchive_remove_media_from_collection',

            // Media relation and tag services.
            'mod_uckkarchive_get_media_relations',
            'mod_uckkarchive_add_media_relation',
            'mod_uckkarchive_remove_media_relation',
            'mod_uckkarchive_tag_media',
            'mod_uckkarchive_untag_media',

            // Content advisory services.
            'mod_uckkarchive_get_content_markers',
            'mod_uckkarchive_add_content_marker',
            'mod_uckkarchive_update_content_marker',
            'mod_uckkarchive_delete_content_marker',
            'mod_uckkarchive_review_content_marker',
            'mod_uckkarchive_get_content_tags',
            'mod_uckkarchive_get_content_tag_sets',

            // External work services.
            'mod_uckkarchive_get_external_works',
            'mod_uckkarchive_get_external_work',
            'mod_uckkarchive_add_external_work',
            'mod_uckkarchive_update_external_work',

            // Export services.
            'mod_uckkarchive_get_export_preview',
            'mod_uckkarchive_export_items',
            'mod_uckkarchive_export_media',
            'mod_uckkarchive_export_collection',
            'mod_uckkarchive_get_export_status',
        ],
        'restrictedusers' => 0,
        'enabled' => 1,
        'shortname' => 'uckkarchive',
        'downloadfiles' => 1,
        'uploadfiles' => 1,
    ],
];