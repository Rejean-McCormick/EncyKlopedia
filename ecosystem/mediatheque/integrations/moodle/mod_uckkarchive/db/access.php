<?php
// This file is part of Moodle - https://moodle.org/
//
// Moodle is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// any later version.

/**
 * Capability definitions for UCKK Archives.
 *
 * @package    mod_uckkarchive
 * @copyright  2026 Univers-Cité King Klown
 * @license    https://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later
 */

defined('MOODLE_INTERNAL') || die();

/**
 * UCKK Archive capability policy.
 *
 * mod_uckkarchive owns archive, media, content advisory, external reference,
 * provenance, validation, export, and module-level restricted-data permissions.
 *
 * It does not own:
 * - global UCKK registry permissions, which belong to local_uckk;
 * - course-format display permissions, which belong to format_uckk;
 * - challenge workflow permissions, which belong to mod_uckkchallenge;
 * - assembly workflow permissions, which belong to mod_uckkassembly;
 * - integrity case permissions, which belong to tool_uckkintegrity;
 * - reporting permissions, which belong to report_uckk.
 *
 * Archive service code must still enforce ownership, provenance, validation
 * state, visibility, retention, privacy, cultural protocol, restricted-data,
 * File API, and workflow rules. Capabilities are permission gates, not
 * automatic authority to bypass archive policy.
 */
$capabilities = [

    /*
     * Add a UCKK Archive activity to a course.
     *
     * This is a course-level activity-creation capability, matching Moodle's
     * standard module add-instance pattern.
     */
    'mod/uckkarchive:addinstance' => [
        'riskbitmask' => RISK_XSS,
        'captype' => 'write',
        'contextlevel' => CONTEXT_COURSE,
        'archetypes' => [
            'editingteacher' => CAP_ALLOW,
            'manager' => CAP_ALLOW,
        ],
        'clonepermissionsfrom' => 'moodle/course:manageactivities',
    ],

    /*
     * View the archive activity and non-restricted archive items.
     *
     * This grants access to the archive activity shell and public/non-restricted
     * archive items. Restricted records remain protected by
     * mod/uckkarchive:viewrestricted and service-layer checks.
     */
    'mod/uckkarchive:view' => [
        'riskbitmask' => 0,
        'captype' => 'read',
        'contextlevel' => CONTEXT_MODULE,
        'archetypes' => [
            'guest' => CAP_PREVENT,
            'student' => CAP_ALLOW,
            'teacher' => CAP_ALLOW,
            'editingteacher' => CAP_ALLOW,
            'manager' => CAP_ALLOW,
        ],
    ],

    /*
     * Add an archive item, proof record, Kristal, or portfolio-linked memory
     * item inside the archive activity.
     *
     * Services must still enforce item ownership, context, provenance,
     * visibility, workflow state, accepted file types, and submission rules.
     */
    'mod/uckkarchive:additem' => [
        'riskbitmask' => RISK_XSS | RISK_SPAM,
        'captype' => 'write',
        'contextlevel' => CONTEXT_MODULE,
        'archetypes' => [
            'student' => CAP_ALLOW,
            'teacher' => CAP_ALLOW,
            'editingteacher' => CAP_ALLOW,
            'manager' => CAP_ALLOW,
        ],
    ],

    /*
     * Validate archive items and mark evidence as human-reviewed or verified.
     *
     * This is intended for Archiviste, Mentor, Gestionnaire UCKK, or similarly
     * trusted technical roles configured by administrators. This capability does
     * not allow automated validation or AI-only validation.
     */
    'mod/uckkarchive:validateitem' => [
        'riskbitmask' => RISK_PERSONAL,
        'captype' => 'write',
        'contextlevel' => CONTEXT_MODULE,
        'archetypes' => [
            'teacher' => CAP_ALLOW,
            'editingteacher' => CAP_ALLOW,
            'manager' => CAP_ALLOW,
        ],
    ],

    /*
     * Revise archive items and create new archive revision records.
     *
     * Students may receive this by default so they can revise their own
     * submitted archive records. Service code must still check ownership,
     * validation state, lock state, and workflow state before accepting
     * revisions.
     */
    'mod/uckkarchive:reviseitem' => [
        'riskbitmask' => RISK_XSS | RISK_SPAM,
        'captype' => 'write',
        'contextlevel' => CONTEXT_MODULE,
        'archetypes' => [
            'student' => CAP_ALLOW,
            'teacher' => CAP_ALLOW,
            'editingteacher' => CAP_ALLOW,
            'manager' => CAP_ALLOW,
        ],
    ],

    /*
     * View restricted, private, hidden, or restricted-integrity archive data.
     *
     * This capability must not be granted broadly. It protects sensitive
     * evidence, integrity-linked records, privacy-sensitive material, hidden
     * provenance, and restricted institutional memory.
     */
    'mod/uckkarchive:viewrestricted' => [
        'riskbitmask' => RISK_PERSONAL | RISK_DATALOSS,
        'captype' => 'read',
        'contextlevel' => CONTEXT_MODULE,
        'archetypes' => [
            'manager' => CAP_ALLOW,
        ],
    ],

    /*
     * Export archive items, evidence packages, or archive bundles.
     *
     * Export services must still enforce validation state, provenance,
     * visibility, retention, privacy, restricted-data, and redaction rules.
     */
    'mod/uckkarchive:export' => [
        'riskbitmask' => RISK_PERSONAL | RISK_DATALOSS,
        'captype' => 'read',
        'contextlevel' => CONTEXT_MODULE,
        'archetypes' => [
            'editingteacher' => CAP_ALLOW,
            'manager' => CAP_ALLOW,
        ],
    ],

    /*
     * View non-restricted media records in the archive media library.
     *
     * This permits access to media metadata and media-library UI. Actual file
     * delivery still goes through pluginfile access checks and media policy.
     */
    'mod/uckkarchive:viewmedia' => [
        'riskbitmask' => 0,
        'captype' => 'read',
        'contextlevel' => CONTEXT_MODULE,
        'archetypes' => [
            'student' => CAP_ALLOW,
            'teacher' => CAP_ALLOW,
            'editingteacher' => CAP_ALLOW,
            'manager' => CAP_ALLOW,
        ],
    ],

    /*
     * Add media records and upload media files.
     *
     * Service code must still validate file area, file type, ownership,
     * provenance, source type, advisory requirements, and draft-file state.
     */
    'mod/uckkarchive:addmedia' => [
        'riskbitmask' => RISK_XSS | RISK_SPAM | RISK_PERSONAL,
        'captype' => 'write',
        'contextlevel' => CONTEXT_MODULE,
        'archetypes' => [
            'student' => CAP_ALLOW,
            'teacher' => CAP_ALLOW,
            'editingteacher' => CAP_ALLOW,
            'manager' => CAP_ALLOW,
        ],
    ],

    /*
     * Edit media metadata, source information, tags, and File API associations.
     *
     * Services must still enforce ownership, lock state, validation state,
     * revision/version rules, cultural restrictions, and retention policy.
     */
    'mod/uckkarchive:editmedia' => [
        'riskbitmask' => RISK_XSS | RISK_PERSONAL,
        'captype' => 'write',
        'contextlevel' => CONTEXT_MODULE,
        'archetypes' => [
            'student' => CAP_ALLOW,
            'teacher' => CAP_ALLOW,
            'editingteacher' => CAP_ALLOW,
            'manager' => CAP_ALLOW,
        ],
    ],

    /*
     * Delete or soft-delete media records.
     *
     * Deletion must remain policy-controlled. Services should prefer
     * soft-delete or retention-safe deletion when the record has provenance,
     * export, validation, advisory, or integrity references.
     */
    'mod/uckkarchive:deletemedia' => [
        'riskbitmask' => RISK_DATALOSS | RISK_PERSONAL,
        'captype' => 'write',
        'contextlevel' => CONTEXT_MODULE,
        'archetypes' => [
            'editingteacher' => CAP_ALLOW,
            'manager' => CAP_ALLOW,
        ],
    ],

    /*
     * Download media files from Moodle File API areas.
     *
     * This does not bypass pluginfile access checks. Restricted, cultural,
     * external-rights, and redacted files require additional policy checks.
     */
    'mod/uckkarchive:downloadmedia' => [
        'riskbitmask' => RISK_PERSONAL | RISK_DATALOSS,
        'captype' => 'read',
        'contextlevel' => CONTEXT_MODULE,
        'archetypes' => [
            'teacher' => CAP_ALLOW,
            'editingteacher' => CAP_ALLOW,
            'manager' => CAP_ALLOW,
        ],
    ],

    /*
     * Create media version records.
     *
     * Versioning must preserve provenance and must not overwrite original
     * files without keeping version history.
     */
    'mod/uckkarchive:versionmedia' => [
        'riskbitmask' => RISK_XSS | RISK_PERSONAL,
        'captype' => 'write',
        'contextlevel' => CONTEXT_MODULE,
        'archetypes' => [
            'student' => CAP_ALLOW,
            'teacher' => CAP_ALLOW,
            'editingteacher' => CAP_ALLOW,
            'manager' => CAP_ALLOW,
        ],
    ],

    /*
     * Manage media collections.
     *
     * Collections organize media but must not change the authority boundary of
     * the underlying media records, file areas, advisories, or export policy.
     */
    'mod/uckkarchive:managemediacollections' => [
        'riskbitmask' => RISK_XSS,
        'captype' => 'write',
        'contextlevel' => CONTEXT_MODULE,
        'archetypes' => [
            'teacher' => CAP_ALLOW,
            'editingteacher' => CAP_ALLOW,
            'manager' => CAP_ALLOW,
        ],
    ],

    /*
     * Export media records, media metadata, media file manifests, or media
     * collection packages.
     *
     * Export services must still enforce restricted media, cultural protocol,
     * rights status, redaction, File API, retention, and privacy constraints.
     */
    'mod/uckkarchive:exportmedia' => [
        'riskbitmask' => RISK_PERSONAL | RISK_DATALOSS,
        'captype' => 'read',
        'contextlevel' => CONTEXT_MODULE,
        'archetypes' => [
            'editingteacher' => CAP_ALLOW,
            'manager' => CAP_ALLOW,
        ],
    ],

    /*
     * View restricted media records and restricted media metadata.
     *
     * This includes restricted, restricted-integrity, private, hidden,
     * sensitive, and policy-protected media. It does not automatically grant
     * cultural protocol access.
     */
    'mod/uckkarchive:viewrestrictedmedia' => [
        'riskbitmask' => RISK_PERSONAL | RISK_DATALOSS,
        'captype' => 'read',
        'contextlevel' => CONTEXT_MODULE,
        'archetypes' => [
            'manager' => CAP_ALLOW,
        ],
    ],

    /*
     * View content advisory panels, trigger/content warnings, and
     * non-restricted advisory markers.
     *
     * This should usually be available wherever media is viewable so learners
     * can see safety and suitability notices.
     */
    'mod/uckkarchive:viewadvisories' => [
        'riskbitmask' => 0,
        'captype' => 'read',
        'contextlevel' => CONTEXT_MODULE,
        'archetypes' => [
            'student' => CAP_ALLOW,
            'teacher' => CAP_ALLOW,
            'editingteacher' => CAP_ALLOW,
            'manager' => CAP_ALLOW,
        ],
    ],

    /*
     * Manage content advisory markers, content tags, tag sets, and marker
     * metadata.
     *
     * Services must still enforce restricted/cultural visibility, human review,
     * locator redaction, and external-work provenance rules.
     */
    'mod/uckkarchive:manageadvisories' => [
        'riskbitmask' => RISK_XSS | RISK_PERSONAL,
        'captype' => 'write',
        'contextlevel' => CONTEXT_MODULE,
        'archetypes' => [
            'teacher' => CAP_ALLOW,
            'editingteacher' => CAP_ALLOW,
            'manager' => CAP_ALLOW,
        ],
    ],

    /*
     * Compatibility alias used by older/generated service code.
     *
     * Prefer mod/uckkarchive:manageadvisories in new code.
     */
    'mod/uckkarchive:managecontentadvisories' => [
        'riskbitmask' => RISK_XSS | RISK_PERSONAL,
        'captype' => 'write',
        'contextlevel' => CONTEXT_MODULE,
        'archetypes' => [
            'teacher' => CAP_ALLOW,
            'editingteacher' => CAP_ALLOW,
            'manager' => CAP_ALLOW,
        ],
        'clonepermissionsfrom' => 'mod/uckkarchive:manageadvisories',
    ],

    /*
     * Review and approve content advisory markers.
     *
     * AI-generated or automated suggestions must not become approved markers
     * unless a user with this capability performs human review.
     */
    'mod/uckkarchive:reviewadvisories' => [
        'riskbitmask' => RISK_PERSONAL,
        'captype' => 'write',
        'contextlevel' => CONTEXT_MODULE,
        'archetypes' => [
            'teacher' => CAP_ALLOW,
            'editingteacher' => CAP_ALLOW,
            'manager' => CAP_ALLOW,
        ],
    ],

    /*
     * View culturally restricted media, markers, locator details, cultural
     * protocol notes, and culturally restricted advisory material.
     *
     * This must be granted narrowly and does not imply global Indigenous,
     * cultural, ceremonial, or community authority outside this Moodle context.
     */
    'mod/uckkarchive:viewculturallyrestricted' => [
        'riskbitmask' => RISK_PERSONAL | RISK_DATALOSS,
        'captype' => 'read',
        'contextlevel' => CONTEXT_MODULE,
        'archetypes' => [
            'manager' => CAP_ALLOW,
        ],
    ],

    /*
     * View external work references.
     *
     * External works are references to media/books/films/articles/etc. not
     * produced by UCKK. They may be used by media provenance and content
     * advisory markers.
     */
    'mod/uckkarchive:viewexternalworks' => [
        'riskbitmask' => 0,
        'captype' => 'read',
        'contextlevel' => CONTEXT_MODULE,
        'archetypes' => [
            'student' => CAP_ALLOW,
            'teacher' => CAP_ALLOW,
            'editingteacher' => CAP_ALLOW,
            'manager' => CAP_ALLOW,
        ],
    ],

    /*
     * Add external work references.
     *
     * This does not import or copy third-party material. It only creates an
     * archive-owned reference record with citation, rights, and source metadata.
     */
    'mod/uckkarchive:addexternalworks' => [
        'riskbitmask' => RISK_XSS | RISK_SPAM,
        'captype' => 'write',
        'contextlevel' => CONTEXT_MODULE,
        'archetypes' => [
            'teacher' => CAP_ALLOW,
            'editingteacher' => CAP_ALLOW,
            'manager' => CAP_ALLOW,
        ],
    ],

    /*
     * Edit external work references.
     *
     * Services must still enforce source rights, cultural protocol notes,
     * advisory links, and restricted visibility.
     */
    'mod/uckkarchive:editexternalworks' => [
        'riskbitmask' => RISK_XSS | RISK_PERSONAL,
        'captype' => 'write',
        'contextlevel' => CONTEXT_MODULE,
        'archetypes' => [
            'teacher' => CAP_ALLOW,
            'editingteacher' => CAP_ALLOW,
            'manager' => CAP_ALLOW,
        ],
    ],

    /*
     * Delete or retire external work references.
     *
     * Deletion should be policy-aware when references are used by content
     * markers, media sources, exports, or provenance records.
     */
    'mod/uckkarchive:deleteexternalworks' => [
        'riskbitmask' => RISK_DATALOSS,
        'captype' => 'write',
        'contextlevel' => CONTEXT_MODULE,
        'archetypes' => [
            'editingteacher' => CAP_ALLOW,
            'manager' => CAP_ALLOW,
        ],
    ],

    /*
     * Manage external work references.
     *
     * This is the broad external-reference administration capability. It may be
     * checked by older or generated service code as a single management gate.
     */
    'mod/uckkarchive:manageexternalworks' => [
        'riskbitmask' => RISK_XSS | RISK_PERSONAL | RISK_DATALOSS,
        'captype' => 'write',
        'contextlevel' => CONTEXT_MODULE,
        'archetypes' => [
            'teacher' => CAP_ALLOW,
            'editingteacher' => CAP_ALLOW,
            'manager' => CAP_ALLOW,
        ],
    ],

    /*
     * Manage autonomous public media libraries, site mappings and bridges.
     *
     * This is deliberately system-level because a bridge can expose public
     * content across otherwise independent Univers-Cité sites.
     */
    'mod/uckkarchive:managelibraries' => [
        'riskbitmask' => RISK_DATALOSS | RISK_CONFIG,
        'captype' => 'write',
        'contextlevel' => CONTEXT_SYSTEM,
        'archetypes' => [
            'manager' => CAP_ALLOW,
        ],
    ],
];