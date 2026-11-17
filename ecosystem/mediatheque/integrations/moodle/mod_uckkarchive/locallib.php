<?php
// This file is part of Moodle - https://moodle.org/
//
// Moodle is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// any later version.

/**
 * Local helper library for mod_uckkarchive.
 *
 * This file contains stable procedural helpers used by Moodle callbacks,
 * controllers, forms, external functions, backup/restore code, and tests.
 *
 * It must not become the full business layer. Complex archive validation,
 * export packaging, provenance calculation, privacy export, integrity linking,
 * and long-running tasks belong in autoloaded classes under:
 *
 * - mod_uckkarchive\classes\local
 * - mod_uckkarchive\classes\form
 * - mod_uckkarchive\classes\output
 * - mod_uckkarchive\classes\task
 *
 * @package    mod_uckkarchive
 * @copyright  2026 Univers-Cité King Klown
 * @license    https://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later
 */

defined('MOODLE_INTERNAL') || die();

/**
 * Component name.
 */
defined('UCKKARCHIVE_COMPONENT') || define('UCKKARCHIVE_COMPONENT', 'mod_uckkarchive');
/**
 * Main activity table.
 */
defined('UCKKARCHIVE_TABLE') || define('UCKKARCHIVE_TABLE', 'uckkarchive');
/**
 * Archive item table.
 */
defined('UCKKARCHIVE_ITEM_TABLE') || define('UCKKARCHIVE_ITEM_TABLE', 'uckkarchive_item');
/**
 * Kristal table.
 */
defined('UCKKARCHIVE_KRISTAL_TABLE') || define('UCKKARCHIVE_KRISTAL_TABLE', 'uckkarchive_kristal');
/**
 * Proof table.
 */
defined('UCKKARCHIVE_PROOF_TABLE') || define('UCKKARCHIVE_PROOF_TABLE', 'uckkarchive_proof');
/**
 * Provenance table.
 */
defined('UCKKARCHIVE_PROVENANCE_TABLE') || define('UCKKARCHIVE_PROVENANCE_TABLE', 'uckkarchive_prov');
/**
 * Revision table.
 */
defined('UCKKARCHIVE_REVISION_TABLE') || define('UCKKARCHIVE_REVISION_TABLE', 'uckkarchive_rev');
/**
 * Export package table.
 */
defined('UCKKARCHIVE_EXPORT_TABLE') || define('UCKKARCHIVE_EXPORT_TABLE', 'uckkarchive_export');
/**
 * Media table.
 */
defined('UCKKARCHIVE_MEDIA_TABLE') || define('UCKKARCHIVE_MEDIA_TABLE', 'uckkarchive_media');
/**
 * Media version table.
 */
defined('UCKKARCHIVE_MEDIA_VERSION_TABLE') || define('UCKKARCHIVE_MEDIA_VERSION_TABLE', 'uckkarchive_media_version');
/**
 * Media source table.
 */
defined('UCKKARCHIVE_MEDIA_SOURCE_TABLE') || define('UCKKARCHIVE_MEDIA_SOURCE_TABLE', 'uckkarchive_media_source');
/**
 * Media collection table.
 */
defined('UCKKARCHIVE_MEDIA_COLLECTION_TABLE') || define('UCKKARCHIVE_MEDIA_COLLECTION_TABLE', 'uckkarchive_media_collection');
/**
 * Media collection membership table.
 */
defined('UCKKARCHIVE_MEDIA_COLLECTION_ITEM_TABLE') || define('UCKKARCHIVE_MEDIA_COLLECTION_ITEM_TABLE', 'uckkarchive_media_collection_item');
/**
 * Media relation table.
 */
defined('UCKKARCHIVE_MEDIA_RELATION_TABLE') || define('UCKKARCHIVE_MEDIA_RELATION_TABLE', 'uckkarchive_media_relation');
/**
 * Media tag table.
 */
defined('UCKKARCHIVE_MEDIA_TAG_TABLE') || define('UCKKARCHIVE_MEDIA_TAG_TABLE', 'uckkarchive_media_tag');
/**
 * Content advisory marker table.
 */
defined('UCKKARCHIVE_CONTENT_MARKER_TABLE') || define('UCKKARCHIVE_CONTENT_MARKER_TABLE', 'uckkarchive_content_marker');
/**
 * Content advisory review table.
 */
defined('UCKKARCHIVE_CONTENT_REVIEW_TABLE') || define('UCKKARCHIVE_CONTENT_REVIEW_TABLE', 'uckkarchive_content_review');
/**
 * Content advisory tag table.
 */
defined('UCKKARCHIVE_CONTENT_TAG_TABLE') || define('UCKKARCHIVE_CONTENT_TAG_TABLE', 'uckkarchive_content_tag');
/**
 * Content advisory tag set table.
 */
defined('UCKKARCHIVE_CONTENT_TAG_SET_TABLE') || define('UCKKARCHIVE_CONTENT_TAG_SET_TABLE', 'uckkarchive_content_tag_set');
/**
 * External work reference table.
 */
defined('UCKKARCHIVE_EXTERNAL_WORK_TABLE') || define('UCKKARCHIVE_EXTERNAL_WORK_TABLE', 'uckkarchive_external_work');
/**
 * Archive item status: draft.
 */
defined('UCKKARCHIVE_STATUS_DRAFT') || define('UCKKARCHIVE_STATUS_DRAFT', 'draft');
/**
 * Archive item status: submitted.
 */
defined('UCKKARCHIVE_STATUS_SUBMITTED') || define('UCKKARCHIVE_STATUS_SUBMITTED', 'submitted');
/**
 * Archive item status: under review.
 */
defined('UCKKARCHIVE_STATUS_UNDER_REVIEW') || define('UCKKARCHIVE_STATUS_UNDER_REVIEW', 'under_review');
/**
 * Archive item status: validated.
 */
defined('UCKKARCHIVE_STATUS_VALIDATED') || define('UCKKARCHIVE_STATUS_VALIDATED', 'validated');
/**
 * Archive item status: published.
 */
defined('UCKKARCHIVE_STATUS_PUBLISHED') || define('UCKKARCHIVE_STATUS_PUBLISHED', 'published');
/**
 * Archive item status: restricted.
 */
defined('UCKKARCHIVE_STATUS_RESTRICTED') || define('UCKKARCHIVE_STATUS_RESTRICTED', 'restricted');
/**
 * Archive item status: contested.
 */
defined('UCKKARCHIVE_STATUS_CONTESTED') || define('UCKKARCHIVE_STATUS_CONTESTED', 'contested');
/**
 * Archive item status: invalidated.
 */
defined('UCKKARCHIVE_STATUS_INVALIDATED') || define('UCKKARCHIVE_STATUS_INVALIDATED', 'invalidated');
/**
 * Archive item status: superseded.
 */
defined('UCKKARCHIVE_STATUS_SUPERSEDED') || define('UCKKARCHIVE_STATUS_SUPERSEDED', 'superseded');
/**
 * Archive item status: archived.
 */
defined('UCKKARCHIVE_STATUS_ARCHIVED') || define('UCKKARCHIVE_STATUS_ARCHIVED', 'archived');
/**
 * Validation state: unverified.
 */
defined('UCKKARCHIVE_VALIDATION_UNVERIFIED') || define('UCKKARCHIVE_VALIDATION_UNVERIFIED', 'unverified');
/**
 * Validation state: human reviewed.
 */
defined('UCKKARCHIVE_VALIDATION_HUMAN_REVIEWED') || define('UCKKARCHIVE_VALIDATION_HUMAN_REVIEWED', 'human_reviewed');
/**
 * Validation state: verified.
 */
defined('UCKKARCHIVE_VALIDATION_VERIFIED') || define('UCKKARCHIVE_VALIDATION_VERIFIED', 'verified');
/**
 * Validation state: contested.
 */
defined('UCKKARCHIVE_VALIDATION_CONTESTED') || define('UCKKARCHIVE_VALIDATION_CONTESTED', 'contested');
/**
 * Validation state: invalidated.
 */
defined('UCKKARCHIVE_VALIDATION_INVALIDATED') || define('UCKKARCHIVE_VALIDATION_INVALIDATED', 'invalidated');
/**
 * Validation state: archived.
 */
defined('UCKKARCHIVE_VALIDATION_ARCHIVED') || define('UCKKARCHIVE_VALIDATION_ARCHIVED', 'archived');
/**
 * Archive visibility: private.
 */
defined('UCKKARCHIVE_VISIBILITY_PRIVATE') || define('UCKKARCHIVE_VISIBILITY_PRIVATE', 'private');
/**
 * Archive visibility: course.
 */
defined('UCKKARCHIVE_VISIBILITY_COURSE') || define('UCKKARCHIVE_VISIBILITY_COURSE', 'course');
/**
 * Archive visibility: cohort.
 */
defined('UCKKARCHIVE_VISIBILITY_COHORT') || define('UCKKARCHIVE_VISIBILITY_COHORT', 'cohort');
/**
 * Archive visibility: program.
 */
defined('UCKKARCHIVE_VISIBILITY_PROGRAM') || define('UCKKARCHIVE_VISIBILITY_PROGRAM', 'program');
/**
 * Archive visibility: institution.
 */
defined('UCKKARCHIVE_VISIBILITY_INSTITUTION') || define('UCKKARCHIVE_VISIBILITY_INSTITUTION', 'institution');
/**
 * Archive visibility: public.
 */
defined('UCKKARCHIVE_VISIBILITY_PUBLIC') || define('UCKKARCHIVE_VISIBILITY_PUBLIC', 'public');
/**
 * Archive visibility: restricted.
 */
defined('UCKKARCHIVE_VISIBILITY_RESTRICTED') || define('UCKKARCHIVE_VISIBILITY_RESTRICTED', 'restricted');
/**
 * Archive visibility: culturally restricted.
 */
defined('UCKKARCHIVE_VISIBILITY_RESTRICTED_CULTURAL') || define('UCKKARCHIVE_VISIBILITY_RESTRICTED_CULTURAL', 'restricted_cultural');
/**
 * Archive visibility: restricted integrity.
 */
defined('UCKKARCHIVE_VISIBILITY_RESTRICTED_INTEGRITY') || define('UCKKARCHIVE_VISIBILITY_RESTRICTED_INTEGRITY', 'restricted_integrity');
/**
 * Archive item type: proof.
 */
defined('UCKKARCHIVE_TYPE_PROOF') || define('UCKKARCHIVE_TYPE_PROOF', 'proof');
/**
 * Archive item type: decision.
 */
defined('UCKKARCHIVE_TYPE_DECISION') || define('UCKKARCHIVE_TYPE_DECISION', 'decision');
/**
 * Archive item type: minutes.
 */
defined('UCKKARCHIVE_TYPE_MINUTES') || define('UCKKARCHIVE_TYPE_MINUTES', 'minutes');
/**
 * Archive item type: challenge result.
 */
defined('UCKKARCHIVE_TYPE_CHALLENGE_RESULT') || define('UCKKARCHIVE_TYPE_CHALLENGE_RESULT', 'challenge_result');
/**
 * Archive item type: course work.
 */
defined('UCKKARCHIVE_TYPE_COURSE_WORK') || define('UCKKARCHIVE_TYPE_COURSE_WORK', 'course_work');
/**
 * Archive item type: portfolio item.
 */
defined('UCKKARCHIVE_TYPE_PORTFOLIO_ITEM') || define('UCKKARCHIVE_TYPE_PORTFOLIO_ITEM', 'portfolio_item');
/**
 * Archive item type: Kristal.
 */
defined('UCKKARCHIVE_TYPE_KRISTAL') || define('UCKKARCHIVE_TYPE_KRISTAL', 'kristal');
/**
 * Archive item type: integrity summary.
 */
defined('UCKKARCHIVE_TYPE_INTEGRITY_SUMMARY') || define('UCKKARCHIVE_TYPE_INTEGRITY_SUMMARY', 'integrity_summary');
/**
 * Archive item type: public summary.
 */
defined('UCKKARCHIVE_TYPE_PUBLIC_SUMMARY') || define('UCKKARCHIVE_TYPE_PUBLIC_SUMMARY', 'public_summary');
/**
 * Provenance source: human.
 */
defined('UCKKARCHIVE_PROVENANCE_HUMAN') || define('UCKKARCHIVE_PROVENANCE_HUMAN', 'human');
/**
 * Provenance source: AI-assisted.
 */
defined('UCKKARCHIVE_PROVENANCE_AI_ASSISTED') || define('UCKKARCHIVE_PROVENANCE_AI_ASSISTED', 'ai_assisted');
/**
 * Provenance source: imported.
 */
defined('UCKKARCHIVE_PROVENANCE_IMPORTED') || define('UCKKARCHIVE_PROVENANCE_IMPORTED', 'imported');
/**
 * Provenance source: system.
 */
defined('UCKKARCHIVE_PROVENANCE_SYSTEM') || define('UCKKARCHIVE_PROVENANCE_SYSTEM', 'system');
/**
 * Provenance source: archive.
 */
defined('UCKKARCHIVE_PROVENANCE_ARCHIVE') || define('UCKKARCHIVE_PROVENANCE_ARCHIVE', 'archive');
/**
 * Provenance source: assembly.
 */
defined('UCKKARCHIVE_PROVENANCE_ASSEMBLY') || define('UCKKARCHIVE_PROVENANCE_ASSEMBLY', 'assembly');
/**
 * Provenance source: challenge.
 */
defined('UCKKARCHIVE_PROVENANCE_CHALLENGE') || define('UCKKARCHIVE_PROVENANCE_CHALLENGE', 'challenge');
/**
 * Provenance source: integrity.
 */
defined('UCKKARCHIVE_PROVENANCE_INTEGRITY') || define('UCKKARCHIVE_PROVENANCE_INTEGRITY', 'integrity');
/**
 * Media status: draft.
 */
defined('UCKKARCHIVE_MEDIA_STATUS_DRAFT') || define('UCKKARCHIVE_MEDIA_STATUS_DRAFT', 'draft');
/**
 * Media status: active.
 */
defined('UCKKARCHIVE_MEDIA_STATUS_ACTIVE') || define('UCKKARCHIVE_MEDIA_STATUS_ACTIVE', 'active');
/**
 * Media status: archived.
 */
defined('UCKKARCHIVE_MEDIA_STATUS_ARCHIVED') || define('UCKKARCHIVE_MEDIA_STATUS_ARCHIVED', 'archived');
/**
 * Media status: restricted.
 */
defined('UCKKARCHIVE_MEDIA_STATUS_RESTRICTED') || define('UCKKARCHIVE_MEDIA_STATUS_RESTRICTED', 'restricted');
/**
 * Media status: soft deleted.
 */
defined('UCKKARCHIVE_MEDIA_STATUS_DELETED_SOFT') || define('UCKKARCHIVE_MEDIA_STATUS_DELETED_SOFT', 'deleted_soft');
/**
 * Media type: image.
 */
defined('UCKKARCHIVE_MEDIA_TYPE_IMAGE') || define('UCKKARCHIVE_MEDIA_TYPE_IMAGE', 'image');
/**
 * Media type: audio.
 */
defined('UCKKARCHIVE_MEDIA_TYPE_AUDIO') || define('UCKKARCHIVE_MEDIA_TYPE_AUDIO', 'audio');
/**
 * Media type: video.
 */
defined('UCKKARCHIVE_MEDIA_TYPE_VIDEO') || define('UCKKARCHIVE_MEDIA_TYPE_VIDEO', 'video');
/**
 * Media type: document.
 */
defined('UCKKARCHIVE_MEDIA_TYPE_DOCUMENT') || define('UCKKARCHIVE_MEDIA_TYPE_DOCUMENT', 'document');
/**
 * Media type: link/external reference.
 */
defined('UCKKARCHIVE_MEDIA_TYPE_LINK') || define('UCKKARCHIVE_MEDIA_TYPE_LINK', 'link');
/**
 * Media type: other.
 */
defined('UCKKARCHIVE_MEDIA_TYPE_OTHER') || define('UCKKARCHIVE_MEDIA_TYPE_OTHER', 'other');
/**
 * Media source: produced by UCKK.
 */
defined('UCKKARCHIVE_MEDIA_SOURCE_UCKK_PRODUCED') || define('UCKKARCHIVE_MEDIA_SOURCE_UCKK_PRODUCED', 'uckk_produced');
/**
 * Media source: external / not produced by UCKK.
 */
defined('UCKKARCHIVE_MEDIA_SOURCE_EXTERNAL') || define('UCKKARCHIVE_MEDIA_SOURCE_EXTERNAL', 'external');
/**
 * Media File API area: original.
 */
defined('UCKKARCHIVE_FILEAREA_MEDIA_ORIGINAL') || define('UCKKARCHIVE_FILEAREA_MEDIA_ORIGINAL', 'media_original');
/**
 * Media File API area: preview.
 */
defined('UCKKARCHIVE_FILEAREA_MEDIA_PREVIEW') || define('UCKKARCHIVE_FILEAREA_MEDIA_PREVIEW', 'media_preview');
/**
 * Media File API area: thumbnail.
 */
defined('UCKKARCHIVE_FILEAREA_MEDIA_THUMBNAIL') || define('UCKKARCHIVE_FILEAREA_MEDIA_THUMBNAIL', 'media_thumbnail');
/**
 * Media File API area: derivative.
 */
defined('UCKKARCHIVE_FILEAREA_MEDIA_DERIVATIVE') || define('UCKKARCHIVE_FILEAREA_MEDIA_DERIVATIVE', 'media_derivative');
/**
 * Media File API area: caption.
 */
defined('UCKKARCHIVE_FILEAREA_MEDIA_CAPTION') || define('UCKKARCHIVE_FILEAREA_MEDIA_CAPTION', 'media_caption');
/**
 * Media File API area: transcript.
 */
defined('UCKKARCHIVE_FILEAREA_MEDIA_TRANSCRIPT') || define('UCKKARCHIVE_FILEAREA_MEDIA_TRANSCRIPT', 'media_transcript');
/**
 * Media File API area: attachment.
 */
defined('UCKKARCHIVE_FILEAREA_MEDIA_ATTACHMENT') || define('UCKKARCHIVE_FILEAREA_MEDIA_ATTACHMENT', 'media_attachment');
/**
 * Content review File API area.
 */
defined('UCKKARCHIVE_FILEAREA_CONTENT_REVIEW') || define('UCKKARCHIVE_FILEAREA_CONTENT_REVIEW', 'content_review_files');
/**
 * External work reference File API area.
 */
defined('UCKKARCHIVE_FILEAREA_EXTERNAL_WORK_REFERENCE') || define('UCKKARCHIVE_FILEAREA_EXTERNAL_WORK_REFERENCE', 'external_work_reference_files');
/**
 * Cultural protocol File API area.
 */
defined('UCKKARCHIVE_FILEAREA_CULTURAL_PROTOCOL') || define('UCKKARCHIVE_FILEAREA_CULTURAL_PROTOCOL', 'cultural_protocol_files');
/**
 * Export manifest File API area.
 */
defined('UCKKARCHIVE_FILEAREA_EXPORT_MANIFEST') || define('UCKKARCHIVE_FILEAREA_EXPORT_MANIFEST', 'export_manifest');
/**
 * Export package File API area.
 */
defined('UCKKARCHIVE_FILEAREA_EXPORT_PACKAGE') || define('UCKKARCHIVE_FILEAREA_EXPORT_PACKAGE', 'export_package');
/**
 * Content review state: draft.
 */
defined('UCKKARCHIVE_CONTENT_REVIEW_DRAFT') || define('UCKKARCHIVE_CONTENT_REVIEW_DRAFT', 'draft');
/**
 * Content review state: pending review.
 */
defined('UCKKARCHIVE_CONTENT_REVIEW_PENDING') || define('UCKKARCHIVE_CONTENT_REVIEW_PENDING', 'pending_review');
/**
 * Content review state: reviewed.
 */
defined('UCKKARCHIVE_CONTENT_REVIEW_REVIEWED') || define('UCKKARCHIVE_CONTENT_REVIEW_REVIEWED', 'reviewed');
/**
 * Content review state: approved.
 */
defined('UCKKARCHIVE_CONTENT_REVIEW_APPROVED') || define('UCKKARCHIVE_CONTENT_REVIEW_APPROVED', 'approved');
/**
 * Content review state: contested.
 */
defined('UCKKARCHIVE_CONTENT_REVIEW_CONTESTED') || define('UCKKARCHIVE_CONTENT_REVIEW_CONTESTED', 'contested');
/**
 * Content review state: retired.
 */
defined('UCKKARCHIVE_CONTENT_REVIEW_RETIRED') || define('UCKKARCHIVE_CONTENT_REVIEW_RETIRED', 'retired');
/**
 * Content advisory severity: notice.
 */
defined('UCKKARCHIVE_CONTENT_SEVERITY_NOTICE') || define('UCKKARCHIVE_CONTENT_SEVERITY_NOTICE', 'notice');
/**
 * Content advisory severity: moderate.
 */
defined('UCKKARCHIVE_CONTENT_SEVERITY_MODERATE') || define('UCKKARCHIVE_CONTENT_SEVERITY_MODERATE', 'moderate');
/**
 * Content advisory severity: strong.
 */
defined('UCKKARCHIVE_CONTENT_SEVERITY_STRONG') || define('UCKKARCHIVE_CONTENT_SEVERITY_STRONG', 'strong');
/**
 * Content advisory severity: restricted.
 */
defined('UCKKARCHIVE_CONTENT_SEVERITY_RESTRICTED') || define('UCKKARCHIVE_CONTENT_SEVERITY_RESTRICTED', 'restricted');
/**
 * Audience suitability: general.
 */
defined('UCKKARCHIVE_AUDIENCE_GENERAL') || define('UCKKARCHIVE_AUDIENCE_GENERAL', 'general');
/**
 * Audience suitability: guided.
 */
defined('UCKKARCHIVE_AUDIENCE_GUIDED') || define('UCKKARCHIVE_AUDIENCE_GUIDED', 'guided');
/**
 * Audience suitability: mature.
 */
defined('UCKKARCHIVE_AUDIENCE_MATURE') || define('UCKKARCHIVE_AUDIENCE_MATURE', 'mature');
/**
 * Audience suitability: restricted.
 */
defined('UCKKARCHIVE_AUDIENCE_RESTRICTED') || define('UCKKARCHIVE_AUDIENCE_RESTRICTED', 'restricted');
/**
 * Audience suitability: culturally restricted.
 */
defined('UCKKARCHIVE_AUDIENCE_RESTRICTED_CULTURAL') || define('UCKKARCHIVE_AUDIENCE_RESTRICTED_CULTURAL', 'restricted_cultural');
/**
 * Audience suitability: integrity restricted.
 */
defined('UCKKARCHIVE_AUDIENCE_RESTRICTED_INTEGRITY') || define('UCKKARCHIVE_AUDIENCE_RESTRICTED_INTEGRITY', 'restricted_integrity');
/**
 * Audience suitability: staff only.
 */
defined('UCKKARCHIVE_AUDIENCE_STAFF_ONLY') || define('UCKKARCHIVE_AUDIENCE_STAFF_ONLY', 'staff_only');
/**
 * External work status: draft.
 */
defined('UCKKARCHIVE_EXTERNAL_WORK_STATUS_DRAFT') || define('UCKKARCHIVE_EXTERNAL_WORK_STATUS_DRAFT', 'draft');
/**
 * External work status: active.
 */
defined('UCKKARCHIVE_EXTERNAL_WORK_STATUS_ACTIVE') || define('UCKKARCHIVE_EXTERNAL_WORK_STATUS_ACTIVE', 'active');
/**
 * External work status: restricted.
 */
defined('UCKKARCHIVE_EXTERNAL_WORK_STATUS_RESTRICTED') || define('UCKKARCHIVE_EXTERNAL_WORK_STATUS_RESTRICTED', 'restricted');
/**
 * External work status: archived.
 */
defined('UCKKARCHIVE_EXTERNAL_WORK_STATUS_ARCHIVED') || define('UCKKARCHIVE_EXTERNAL_WORK_STATUS_ARCHIVED', 'archived');
/**
 * External work status: soft deleted.
 */
defined('UCKKARCHIVE_EXTERNAL_WORK_STATUS_DELETED_SOFT') || define('UCKKARCHIVE_EXTERNAL_WORK_STATUS_DELETED_SOFT', 'deleted_soft');
/**
 * External work type: book.
 */
defined('UCKKARCHIVE_EXTERNAL_WORK_TYPE_BOOK') || define('UCKKARCHIVE_EXTERNAL_WORK_TYPE_BOOK', 'book');
/**
 * External work type: film.
 */
defined('UCKKARCHIVE_EXTERNAL_WORK_TYPE_FILM') || define('UCKKARCHIVE_EXTERNAL_WORK_TYPE_FILM', 'film');
/**
 * External work type: article.
 */
defined('UCKKARCHIVE_EXTERNAL_WORK_TYPE_ARTICLE') || define('UCKKARCHIVE_EXTERNAL_WORK_TYPE_ARTICLE', 'article');
/**
 * External work type: podcast.
 */
defined('UCKKARCHIVE_EXTERNAL_WORK_TYPE_PODCAST') || define('UCKKARCHIVE_EXTERNAL_WORK_TYPE_PODCAST', 'podcast');
/**
 * External work type: website.
 */
defined('UCKKARCHIVE_EXTERNAL_WORK_TYPE_WEBSITE') || define('UCKKARCHIVE_EXTERNAL_WORK_TYPE_WEBSITE', 'website');
/**
 * External work type: external video.
 */
defined('UCKKARCHIVE_EXTERNAL_WORK_TYPE_EXTERNAL_VIDEO') || define('UCKKARCHIVE_EXTERNAL_WORK_TYPE_EXTERNAL_VIDEO', 'external_video');
/**
 * External work type: external image.
 */
defined('UCKKARCHIVE_EXTERNAL_WORK_TYPE_EXTERNAL_IMAGE') || define('UCKKARCHIVE_EXTERNAL_WORK_TYPE_EXTERNAL_IMAGE', 'external_image');
/**
 * External work type: public archive item.
 */
defined('UCKKARCHIVE_EXTERNAL_WORK_TYPE_PUBLIC_ARCHIVE_ITEM') || define('UCKKARCHIVE_EXTERNAL_WORK_TYPE_PUBLIC_ARCHIVE_ITEM', 'public_archive_item');
/**
 * External work type: third-party PDF.
 */
defined('UCKKARCHIVE_EXTERNAL_WORK_TYPE_THIRD_PARTY_PDF') || define('UCKKARCHIVE_EXTERNAL_WORK_TYPE_THIRD_PARTY_PDF', 'third_party_pdf');
/**
 * External work type: other.
 */
defined('UCKKARCHIVE_EXTERNAL_WORK_TYPE_OTHER') || define('UCKKARCHIVE_EXTERNAL_WORK_TYPE_OTHER', 'other');
/**
 * External work rights status: unknown.
 */
defined('UCKKARCHIVE_RIGHTS_UNKNOWN') || define('UCKKARCHIVE_RIGHTS_UNKNOWN', 'unknown');
/**
 * External work rights status: third-party copyright.
 */
defined('UCKKARCHIVE_RIGHTS_THIRD_PARTY_COPYRIGHT') || define('UCKKARCHIVE_RIGHTS_THIRD_PARTY_COPYRIGHT', 'third_party_copyright');
/**
 * External work rights status: licensed external.
 */
defined('UCKKARCHIVE_RIGHTS_LICENSED_EXTERNAL') || define('UCKKARCHIVE_RIGHTS_LICENSED_EXTERNAL', 'licensed_external');
/**
 * External work rights status: public domain.
 */
defined('UCKKARCHIVE_RIGHTS_PUBLIC_DOMAIN') || define('UCKKARCHIVE_RIGHTS_PUBLIC_DOMAIN', 'public_domain');
/**
 * External work rights status: open license.
 */
defined('UCKKARCHIVE_RIGHTS_OPEN_LICENSE') || define('UCKKARCHIVE_RIGHTS_OPEN_LICENSE', 'open_license');
/**
 * External work rights status: fair-use reference.
 */
defined('UCKKARCHIVE_RIGHTS_FAIR_USE_REFERENCE') || define('UCKKARCHIVE_RIGHTS_FAIR_USE_REFERENCE', 'fair_use_reference');
/**
 * External work rights status: restricted reference.
 */
defined('UCKKARCHIVE_RIGHTS_RESTRICTED_REFERENCE') || define('UCKKARCHIVE_RIGHTS_RESTRICTED_REFERENCE', 'restricted_reference');
/**
 * Return canonical archive item statuses.
 *
 * @return string[]
 */
if (!function_exists('uckkarchive_get_statuses')) {
function uckkarchive_get_statuses(): array {
    return [
        UCKKARCHIVE_STATUS_DRAFT,
        UCKKARCHIVE_STATUS_SUBMITTED,
        UCKKARCHIVE_STATUS_UNDER_REVIEW,
        UCKKARCHIVE_STATUS_VALIDATED,
        UCKKARCHIVE_STATUS_PUBLISHED,
        UCKKARCHIVE_STATUS_RESTRICTED,
        UCKKARCHIVE_STATUS_CONTESTED,
        UCKKARCHIVE_STATUS_INVALIDATED,
        UCKKARCHIVE_STATUS_SUPERSEDED,
        UCKKARCHIVE_STATUS_ARCHIVED,
    ];
}
}


/**
 * Return archive status labels.
 *
 * @return array<string, string>
 */
if (!function_exists('uckkarchive_get_status_options')) {
function uckkarchive_get_status_options(): array {
    $options = [];

    foreach (uckkarchive_get_statuses() as $status) {
        $options[$status] = uckkarchive_get_string_if_exists(
            'status:' . str_replace('_', '', $status),
            ucfirst(str_replace('_', ' ', $status))
        );
    }

    return $options;
}
}


/**
 * Return validation states.
 *
 * @return string[]
 */
if (!function_exists('uckkarchive_get_validation_states')) {
function uckkarchive_get_validation_states(): array {
    return [
        UCKKARCHIVE_VALIDATION_UNVERIFIED,
        UCKKARCHIVE_VALIDATION_HUMAN_REVIEWED,
        UCKKARCHIVE_VALIDATION_VERIFIED,
        UCKKARCHIVE_VALIDATION_CONTESTED,
        UCKKARCHIVE_VALIDATION_INVALIDATED,
        UCKKARCHIVE_VALIDATION_ARCHIVED,
    ];
}
}


/**
 * Return validation state labels.
 *
 * @return array<string, string>
 */
if (!function_exists('uckkarchive_get_validation_state_options')) {
function uckkarchive_get_validation_state_options(): array {
    $options = [];

    foreach (uckkarchive_get_validation_states() as $state) {
        $options[$state] = uckkarchive_get_string_if_exists(
            'validation:' . str_replace('_', '', $state),
            ucfirst(str_replace('_', ' ', $state))
        );
    }

    return $options;
}
}


/**
 * Return archive visibilities.
 *
 * @return string[]
 */
if (!function_exists('uckkarchive_get_visibilities')) {
function uckkarchive_get_visibilities(): array {
    return [
        UCKKARCHIVE_VISIBILITY_PRIVATE,
        UCKKARCHIVE_VISIBILITY_COURSE,
        UCKKARCHIVE_VISIBILITY_COHORT,
        UCKKARCHIVE_VISIBILITY_PROGRAM,
        UCKKARCHIVE_VISIBILITY_INSTITUTION,
        UCKKARCHIVE_VISIBILITY_PUBLIC,
        UCKKARCHIVE_VISIBILITY_RESTRICTED,
        UCKKARCHIVE_VISIBILITY_RESTRICTED_CULTURAL,
        UCKKARCHIVE_VISIBILITY_RESTRICTED_INTEGRITY,
    ];
}
}


/**
 * Return archive visibility labels.
 *
 * @return array<string, string>
 */
if (!function_exists('uckkarchive_get_visibility_options')) {
function uckkarchive_get_visibility_options(): array {
    $options = [];

    foreach (uckkarchive_get_visibilities() as $visibility) {
        $options[$visibility] = uckkarchive_get_string_if_exists(
            'visibility:' . str_replace('_', '', $visibility),
            ucfirst(str_replace('_', ' ', $visibility))
        );
    }

    return $options;
}
}


/**
 * Return archive item types.
 *
 * @return string[]
 */
if (!function_exists('uckkarchive_get_item_types')) {
function uckkarchive_get_item_types(): array {
    return [
        UCKKARCHIVE_TYPE_PROOF,
        UCKKARCHIVE_TYPE_DECISION,
        UCKKARCHIVE_TYPE_MINUTES,
        UCKKARCHIVE_TYPE_CHALLENGE_RESULT,
        UCKKARCHIVE_TYPE_COURSE_WORK,
        UCKKARCHIVE_TYPE_PORTFOLIO_ITEM,
        UCKKARCHIVE_TYPE_KRISTAL,
        UCKKARCHIVE_TYPE_INTEGRITY_SUMMARY,
        UCKKARCHIVE_TYPE_PUBLIC_SUMMARY,
    ];
}
}


/**
 * Return archive item type labels.
 *
 * @return array<string, string>
 */
if (!function_exists('uckkarchive_get_item_type_options')) {
function uckkarchive_get_item_type_options(): array {
    $options = [];

    foreach (uckkarchive_get_item_types() as $type) {
        $options[$type] = uckkarchive_get_string_if_exists(
            'itemtype:' . str_replace('_', '', $type),
            ucfirst(str_replace('_', ' ', $type))
        );
    }

    return $options;
}
}


/**
 * Return provenance sources.
 *
 * @return string[]
 */
if (!function_exists('uckkarchive_get_provenance_sources')) {
function uckkarchive_get_provenance_sources(): array {
    return [
        UCKKARCHIVE_PROVENANCE_HUMAN,
        UCKKARCHIVE_PROVENANCE_AI_ASSISTED,
        UCKKARCHIVE_PROVENANCE_IMPORTED,
        UCKKARCHIVE_PROVENANCE_SYSTEM,
        UCKKARCHIVE_PROVENANCE_ARCHIVE,
        UCKKARCHIVE_PROVENANCE_ASSEMBLY,
        UCKKARCHIVE_PROVENANCE_CHALLENGE,
        UCKKARCHIVE_PROVENANCE_INTEGRITY,
    ];
}
}


/**
 * Return provenance source labels.
 *
 * @return array<string, string>
 */
if (!function_exists('uckkarchive_get_provenance_options')) {
function uckkarchive_get_provenance_options(): array {
    $options = [];

    foreach (uckkarchive_get_provenance_sources() as $source) {
        $options[$source] = uckkarchive_get_string_if_exists(
            'provenance:' . str_replace('_', '', $source),
            ucfirst(str_replace('_', ' ', $source))
        );
    }

    return $options;
}
}


/**
 * Return true if the value is a valid archive status.
 *
 * @param string $status Status.
 * @return bool
 */
if (!function_exists('uckkarchive_is_valid_status')) {
function uckkarchive_is_valid_status(string $status): bool {
    return in_array($status, uckkarchive_get_statuses(), true);
}
}


/**
 * Return true if the value is a valid validation state.
 *
 * @param string $state Validation state.
 * @return bool
 */
if (!function_exists('uckkarchive_is_valid_validation_state')) {
function uckkarchive_is_valid_validation_state(string $state): bool {
    return in_array($state, uckkarchive_get_validation_states(), true);
}
}


/**
 * Return true if the value is a valid archive visibility.
 *
 * @param string $visibility Visibility.
 * @return bool
 */
if (!function_exists('uckkarchive_is_valid_visibility')) {
function uckkarchive_is_valid_visibility(string $visibility): bool {
    return in_array($visibility, uckkarchive_get_visibilities(), true);
}
}


/**
 * Return true if the value is a valid archive item type.
 *
 * @param string $type Item type.
 * @return bool
 */
if (!function_exists('uckkarchive_is_valid_item_type')) {
function uckkarchive_is_valid_item_type(string $type): bool {
    return in_array($type, uckkarchive_get_item_types(), true);
}
}


/**
 * Return true if the value is a valid provenance source.
 *
 * @param string $source Provenance source.
 * @return bool
 */
if (!function_exists('uckkarchive_is_valid_provenance_source')) {
function uckkarchive_is_valid_provenance_source(string $source): bool {
    return in_array($source, uckkarchive_get_provenance_sources(), true);
}
}


/**
 * Normalise an archive status.
 *
 * @param string|null $status Raw status.
 * @return string
 */
if (!function_exists('uckkarchive_normalise_status')) {
function uckkarchive_normalise_status(?string $status): string {
    $status = clean_param((string)$status, PARAM_ALPHANUMEXT);

    return uckkarchive_is_valid_status($status) ? $status : UCKKARCHIVE_STATUS_DRAFT;
}
}


/**
 * Normalise a validation state.
 *
 * @param string|null $state Raw validation state.
 * @return string
 */
if (!function_exists('uckkarchive_normalise_validation_state')) {
function uckkarchive_normalise_validation_state(?string $state): string {
    $state = clean_param((string)$state, PARAM_ALPHANUMEXT);

    return uckkarchive_is_valid_validation_state($state) ? $state : UCKKARCHIVE_VALIDATION_UNVERIFIED;
}
}


/**
 * Normalise visibility.
 *
 * @param string|null $visibility Raw visibility.
 * @return string
 */
if (!function_exists('uckkarchive_normalise_visibility')) {
function uckkarchive_normalise_visibility(?string $visibility): string {
    $visibility = clean_param((string)$visibility, PARAM_ALPHANUMEXT);

    return uckkarchive_is_valid_visibility($visibility) ? $visibility : UCKKARCHIVE_VISIBILITY_COURSE;
}
}


/**
 * Normalise archive item type.
 *
 * @param string|null $type Raw item type.
 * @return string
 */
if (!function_exists('uckkarchive_normalise_item_type')) {
function uckkarchive_normalise_item_type(?string $type): string {
    $type = clean_param((string)$type, PARAM_ALPHANUMEXT);

    return uckkarchive_is_valid_item_type($type) ? $type : UCKKARCHIVE_TYPE_PROOF;
}
}


/**
 * Normalise provenance source.
 *
 * @param string|null $source Raw provenance source.
 * @return string
 */
if (!function_exists('uckkarchive_normalise_provenance_source')) {
function uckkarchive_normalise_provenance_source(?string $source): string {
    $source = clean_param((string)$source, PARAM_ALPHANUMEXT);

    return uckkarchive_is_valid_provenance_source($source) ? $source : UCKKARCHIVE_PROVENANCE_HUMAN;
}
}


/**
 * Return a translated string if it exists, otherwise a fallback.
 *
 * @param string $key String key.
 * @param string $fallback Fallback.
 * @return string
 */
if (!function_exists('uckkarchive_get_string_if_exists')) {
function uckkarchive_get_string_if_exists(string $key, string $fallback): string {
    if (get_string_manager()->string_exists($key, 'uckkarchive')) {
        return get_string($key, 'uckkarchive');
    }

    return $fallback;
}
}


/**
 * Build a module URL.
 *
 * @param string $script Script filename without leading slash.
 * @param array<string, mixed> $params URL params.
 * @return moodle_url
 */
if (!function_exists('uckkarchive_url')) {
function uckkarchive_url(string $script = 'view.php', array $params = []): moodle_url {
    $script = clean_param($script, PARAM_FILE);

    if ($script === '') {
        $script = 'view.php';
    }

    return new moodle_url('/mod/uckkarchive/' . $script, $params);
}
}


/**
 * Build the activity view URL.
 *
 * @param int $cmid Course module id.
 * @return moodle_url
 */
if (!function_exists('uckkarchive_view_url')) {
function uckkarchive_view_url(int $cmid): moodle_url {
    return uckkarchive_url('view.php', ['id' => $cmid]);
}
}


/**
 * Build the activity index URL.
 *
 * @param int $courseid Course id.
 * @return moodle_url
 */
if (!function_exists('uckkarchive_index_url')) {
function uckkarchive_index_url(int $courseid): moodle_url {
    return uckkarchive_url('index.php', ['id' => $courseid]);
}
}


/**
 * Build archive item URL.
 *
 * @param int $cmid Course module id.
 * @param int $itemid Item id.
 * @return moodle_url
 */
if (!function_exists('uckkarchive_item_url')) {
function uckkarchive_item_url(int $cmid, int $itemid): moodle_url {
    return uckkarchive_url('item.php', [
        'id' => $cmid,
        'itemid' => $itemid,
    ]);
}
}


/**
 * Build add item URL.
 *
 * @param int $cmid Course module id.
 * @param array<string, mixed> $params Extra params.
 * @return moodle_url
 */
if (!function_exists('uckkarchive_add_url')) {
function uckkarchive_add_url(int $cmid, array $params = []): moodle_url {
    return uckkarchive_url('add.php', ['id' => $cmid] + $params);
}
}


/**
 * Build validation URL.
 *
 * @param int $cmid Course module id.
 * @param int $itemid Item id.
 * @return moodle_url
 */
if (!function_exists('uckkarchive_validate_url')) {
function uckkarchive_validate_url(int $cmid, int $itemid): moodle_url {
    return uckkarchive_url('validate.php', [
        'id' => $cmid,
        'itemid' => $itemid,
    ]);
}
}


/**
 * Build export URL.
 *
 * @param int $cmid Course module id.
 * @param array<string, mixed> $params Extra params.
 * @return moodle_url
 */
if (!function_exists('uckkarchive_export_url')) {
function uckkarchive_export_url(int $cmid, array $params = []): moodle_url {
    return uckkarchive_url('export.php', ['id' => $cmid] + $params);
}
}


/**
 * Resolve course, course module, archive instance, and module context.
 *
 * @param int $cmid Course module id.
 * @param int $archiveid Archive instance id.
 * @return array{0: stdClass, 1: stdClass, 2: stdClass, 3: context_module}
 */
if (!function_exists('uckkarchive_get_page_records')) {
function uckkarchive_get_page_records(int $cmid = 0, int $archiveid = 0): array {
    global $DB;

    if ($cmid > 0) {
        $cm = get_coursemodule_from_id('uckkarchive', $cmid, 0, false, MUST_EXIST);
        $course = $DB->get_record('course', ['id' => $cm->course], '*', MUST_EXIST);
        $archive = $DB->get_record(UCKKARCHIVE_TABLE, ['id' => $cm->instance], '*', MUST_EXIST);
    } else if ($archiveid > 0) {
        $archive = $DB->get_record(UCKKARCHIVE_TABLE, ['id' => $archiveid], '*', MUST_EXIST);
        $course = $DB->get_record('course', ['id' => $archive->course], '*', MUST_EXIST);
        $cm = get_coursemodule_from_instance('uckkarchive', $archive->id, $course->id, false, MUST_EXIST);
    } else {
        throw new moodle_exception('missingparam', 'error', '', 'id');
    }

    $context = context_module::instance($cm->id);

    return [$course, $cm, $archive, $context];
}
}


/**
 * Require login and view capability for an archive activity page.
 *
 * @param int $cmid Course module id.
 * @param int $archiveid Archive instance id.
 * @return array{0: stdClass, 1: stdClass, 2: stdClass, 3: context_module}
 */
if (!function_exists('uckkarchive_require_page')) {
function uckkarchive_require_page(int $cmid = 0, int $archiveid = 0): array {
    [$course, $cm, $archive, $context] = uckkarchive_get_page_records($cmid, $archiveid);

    require_login($course, false, $cm);
    require_capability('mod/uckkarchive:view', $context);

    return [$course, $cm, $archive, $context];
}
}


/**
 * Configure PAGE for an archive page.
 *
 * @param moodle_page $page Moodle page.
 * @param stdClass $course Course.
 * @param stdClass $cm Course module.
 * @param context_module $context Context.
 * @param moodle_url $url Page URL.
 * @param string $title Page title.
 * @return void
 */
if (!function_exists('uckkarchive_setup_page')) {
function uckkarchive_setup_page(
    moodle_page $page,
    stdClass $course,
    stdClass $cm,
    context_module $context,
    moodle_url $url,
    string $title
): void {
    $page->set_url($url);
    $page->set_course($course);
    $page->set_cm($cm);
    $page->set_context($context);
    $page->set_title($title);
    $page->set_heading(format_string($course->fullname));
}
}


/**
 * Mark the archive module as viewed.
 *
 * @param stdClass $course Course.
 * @param stdClass $cm Course module.
 * @return void
 */
if (!function_exists('uckkarchive_mark_viewed')) {
function uckkarchive_mark_viewed(stdClass $course, stdClass $cm): void {
    $completion = new completion_info($course);
    $completion->set_module_viewed($cm);
}
}


/**
 * Return whether the user can add archive items.
 *
 * @param context_module $context Context.
 * @param stdClass|null $user User.
 * @return bool
 */
if (!function_exists('uckkarchive_can_add_item')) {
function uckkarchive_can_add_item(context_module $context, ?stdClass $user = null): bool {
    return has_capability('mod/uckkarchive:additem', $context, $user);
}
}


/**
 * Return whether the user can validate archive items.
 *
 * @param context_module $context Context.
 * @param stdClass|null $user User.
 * @return bool
 */
if (!function_exists('uckkarchive_can_validate_item')) {
function uckkarchive_can_validate_item(context_module $context, ?stdClass $user = null): bool {
    return has_capability('mod/uckkarchive:validateitem', $context, $user);
}
}


/**
 * Return whether the user can revise archive items.
 *
 * Canonical UCKK fixed variable list uses reviseitem. If legacy docs mention
 * versionitem, keep the generated plugin aligned on reviseitem.
 *
 * @param context_module $context Context.
 * @param stdClass|null $user User.
 * @return bool
 */
if (!function_exists('uckkarchive_can_revise_item')) {
function uckkarchive_can_revise_item(context_module $context, ?stdClass $user = null): bool {
    return has_capability('mod/uckkarchive:reviseitem', $context, $user);
}
}


/**
 * Return whether the user can see restricted archive data.
 *
 * @param context_module $context Context.
 * @param stdClass|null $user User.
 * @return bool
 */
if (!function_exists('uckkarchive_can_view_restricted')) {
function uckkarchive_can_view_restricted(context_module $context, ?stdClass $user = null): bool {
    return has_capability('mod/uckkarchive:viewrestricted', $context, $user) ||
        uckkarchive_has_capability('mod/uckkarchive:viewrestrictedmedia', $context, $user);
}
}


/**
 * Return whether the user can export archive data.
 *
 * @param context_module $context Context.
 * @param stdClass|null $user User.
 * @return bool
 */
if (!function_exists('uckkarchive_can_export')) {
function uckkarchive_can_export(context_module $context, ?stdClass $user = null): bool {
    return has_capability('mod/uckkarchive:export', $context, $user);
}
}


/**
 * Return whether a user can view an archive item.
 *
 * This is a lightweight guard for controllers and output preparation. The
 * service layer remains responsible for full visibility and integrity policy.
 *
 * @param stdClass $item Archive item record.
 * @param context_module $context Module context.
 * @param stdClass|null $user User.
 * @return bool
 */
if (!function_exists('uckkarchive_can_view_item')) {
function uckkarchive_can_view_item(stdClass $item, context_module $context, ?stdClass $user = null): bool {
    global $USER;

    $user ??= $USER;

    if (!has_capability('mod/uckkarchive:view', $context, $user)) {
        return false;
    }

    $visibility = uckkarchive_normalise_visibility($item->visibility ?? null);
    $status = uckkarchive_normalise_status($item->status ?? null);

    if (in_array($status, [
        UCKKARCHIVE_STATUS_INVALIDATED,
        UCKKARCHIVE_STATUS_SUPERSEDED,
        UCKKARCHIVE_STATUS_ARCHIVED,
    ], true) && !uckkarchive_can_view_restricted($context, $user)) {
        return false;
    }

    if ($visibility === UCKKARCHIVE_VISIBILITY_PRIVATE) {
        return !empty($item->userid) && (int)$item->userid === (int)$user->id;
    }

    if ($visibility === UCKKARCHIVE_VISIBILITY_RESTRICTED_CULTURAL) {
        return uckkarchive_can_view_culturally_restricted($context, $user);
    }

    if (uckkarchive_is_restricted_visibility($visibility)) {
        return uckkarchive_can_view_restricted($context, $user);
    }

    return true;
}
}


/**
 * Return common export context for permission-filtered item cards.
 *
 * @param stdClass $item Archive item record.
 * @param stdClass $cm Course module.
 * @param context_module $context Context.
 * @return stdClass
 */
if (!function_exists('uckkarchive_prepare_item_export')) {
function uckkarchive_prepare_item_export(stdClass $item, stdClass $cm, context_module $context): stdClass {
    $data = new stdClass();

    $data->id = (int)($item->id ?? 0);
    $data->cmid = (int)$cm->id;
    $data->contextid = (int)$context->id;
    $data->title = format_string((string)($item->title ?? $item->name ?? ''));
    $data->itemtype = uckkarchive_normalise_item_type($item->itemtype ?? $item->type ?? null);
    $data->itemtypelabel = uckkarchive_get_item_type_options()[$data->itemtype] ?? $data->itemtype;
    $data->status = uckkarchive_normalise_status($item->status ?? null);
    $data->statuslabel = uckkarchive_get_status_options()[$data->status] ?? $data->status;
    $data->statusclass = 'status-' . str_replace('_', '-', $data->status);
    $data->visibility = uckkarchive_normalise_visibility($item->visibility ?? null);
    $data->visibilitylabel = uckkarchive_get_visibility_options()[$data->visibility] ?? $data->visibility;
    $data->validationstate = uckkarchive_normalise_validation_state($item->validationstate ?? null);
    $data->validationlabel = uckkarchive_get_validation_state_options()[$data->validationstate] ?? $data->validationstate;
    $data->versionno = max(1, (int)($item->versionno ?? 1));
    $data->summary = format_string((string)($item->summary ?? $item->publicsummary ?? ''));
    $data->hassummary = trim($data->summary) !== '';
    $data->url = uckkarchive_item_url((int)$cm->id, $data->id)->out(false);
    $data->hasurl = $data->id > 0;
    $data->timecreated = (int)($item->timecreated ?? 0);
    $data->timecreatedlabel = $data->timecreated > 0 ? userdate($data->timecreated) : '';
    $data->timemodified = (int)($item->timemodified ?? 0);
    $data->timemodifiedlabel = $data->timemodified > 0 ? userdate($data->timemodified) : '';
    $data->metadata = uckkarchive_decode_metadata($item->metadata ?? null);

    return $data;
}
}


/**
 * Load one archive item.
 *
 * @param int $itemid Archive item id.
 * @param int|null $archiveid Optional archive instance id.
 * @return stdClass
 */
if (!function_exists('uckkarchive_get_item')) {
function uckkarchive_get_item(int $itemid, ?int $archiveid = null): stdClass {
    global $DB;

    $conditions = ['id' => $itemid];

    if ($archiveid !== null) {
        $conditions['archiveid'] = $archiveid;
    }

    return $DB->get_record(UCKKARCHIVE_ITEM_TABLE, $conditions, '*', MUST_EXIST);
}
}


/**
 * Load visible archive items for a module instance.
 *
 * @param stdClass $archive Archive instance.
 * @param context_module $context Context.
 * @param stdClass|null $user User.
 * @param array<string, mixed> $filters Filters.
 * @param int $limit Limit.
 * @param int $offset Offset.
 * @return stdClass[]
 */
if (!function_exists('uckkarchive_get_visible_items')) {
function uckkarchive_get_visible_items(
    stdClass $archive,
    context_module $context,
    ?stdClass $user = null,
    array $filters = [],
    int $limit = 0,
    int $offset = 0
): array {
    global $DB, $USER;

    $user ??= $USER;

    $conditions = ['archiveid' => (int)$archive->id];
    $params = [];

    if (!empty($filters['status'])) {
        $conditions['status'] = uckkarchive_normalise_status((string)$filters['status']);
    }

    if (!empty($filters['itemtype'])) {
        $conditions['itemtype'] = uckkarchive_normalise_item_type((string)$filters['itemtype']);
    }

    if (!empty($filters['validationstate'])) {
        $conditions['validationstate'] = uckkarchive_normalise_validation_state((string)$filters['validationstate']);
    }

    [$where, $params] = $DB->get_in_or_equal(array_values($conditions), SQL_PARAMS_NAMED, 'p');

    // get_in_or_equal is not useful for associative equality, so use simple SQL.
    $sqlwhere = [];
    $params = [];

    foreach ($conditions as $field => $value) {
        $param = 'p_' . $field;
        $sqlwhere[] = $field . ' = :' . $param;
        $params[$param] = $value;
    }

    if (!uckkarchive_can_view_restricted($context, $user)) {
        $sqlwhere[] = 'visibility NOT IN (:restrictedvisibility, :culturalvisibility, :integrityvisibility)';
        $params['restrictedvisibility'] = UCKKARCHIVE_VISIBILITY_RESTRICTED;
        $params['culturalvisibility'] = UCKKARCHIVE_VISIBILITY_RESTRICTED_CULTURAL;
        $params['integrityvisibility'] = UCKKARCHIVE_VISIBILITY_RESTRICTED_INTEGRITY;
        $sqlwhere[] = 'status <> :invalidatedstatus';
        $params['invalidatedstatus'] = UCKKARCHIVE_STATUS_INVALIDATED;
    }

    $sql = 'SELECT *
              FROM {' . UCKKARCHIVE_ITEM_TABLE . '}
             WHERE ' . implode(' AND ', $sqlwhere) . '
          ORDER BY timemodified DESC, id DESC';

    return $DB->get_records_sql($sql, $params, $offset, $limit);
}
}


/**
 * Count visible archive items for a module instance.
 *
 * @param stdClass $archive Archive instance.
 * @param context_module $context Context.
 * @param stdClass|null $user User.
 * @param array<string, mixed> $filters Filters.
 * @return int
 */
if (!function_exists('uckkarchive_count_visible_items')) {
function uckkarchive_count_visible_items(
    stdClass $archive,
    context_module $context,
    ?stdClass $user = null,
    array $filters = []
): int {
    return count(uckkarchive_get_visible_items($archive, $context, $user, $filters, 0, 0));
}
}


/**
 * Decode JSON metadata safely.
 *
 * @param mixed $metadata Raw metadata.
 * @return array<string, mixed>
 */
if (!function_exists('uckkarchive_decode_metadata')) {
function uckkarchive_decode_metadata(mixed $metadata): array {
    if ($metadata === null || $metadata === '') {
        return [];
    }

    if (is_array($metadata)) {
        return $metadata;
    }

    if ($metadata instanceof stdClass) {
        return (array)$metadata;
    }

    if (!is_string($metadata)) {
        return [];
    }

    $decoded = json_decode($metadata, true);

    if (json_last_error() !== JSON_ERROR_NONE || !is_array($decoded)) {
        return [];
    }

    return $decoded;
}
}


/**
 * Encode metadata as JSON or null.
 *
 * @param array<string, mixed>|stdClass|null $metadata Metadata.
 * @return string|null
 */
if (!function_exists('uckkarchive_encode_metadata')) {
function uckkarchive_encode_metadata(array|stdClass|null $metadata): ?string {
    if ($metadata instanceof stdClass) {
        $metadata = (array)$metadata;
    }

    if (empty($metadata)) {
        return null;
    }

    return json_encode($metadata, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
}
}


/**
 * Compute a deterministic provenance hash.
 *
 * @param array<string, mixed>|stdClass|string $payload Hash payload.
 * @return string
 */
if (!function_exists('uckkarchive_compute_provenance_hash')) {
function uckkarchive_compute_provenance_hash(array|stdClass|string $payload): string {
    if ($payload instanceof stdClass) {
        $payload = (array)$payload;
    }

    if (is_array($payload)) {
        ksort($payload);
        $payload = json_encode($payload, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
    }

    return hash('sha256', (string)$payload);
}
}


/**
 * Create a revision record from previous and new item state.
 *
 * This helper writes only the revision record. The caller is responsible for
 * updating the archive item itself inside the same delegated transaction when
 * atomicity is required.
 *
 * @param stdClass $olditem Previous item state.
 * @param stdClass $newitem New item state.
 * @param string $reason Change reason.
 * @param int $userid Acting user id.
 * @param int|null $integritycaseid Linked integrity case id.
 * @return int Revision id.
 */
if (!function_exists('uckkarchive_create_revision')) {
function uckkarchive_create_revision(
    stdClass $olditem,
    stdClass $newitem,
    string $reason,
    int $userid,
    ?int $integritycaseid = null
): int {
    global $DB;

    $now = time();

    $record = new stdClass();
    $record->archiveid = (int)($newitem->archiveid ?? $olditem->archiveid ?? 0);
    $record->itemid = (int)($newitem->id ?? $olditem->id ?? 0);
    $record->courseid = (int)($newitem->courseid ?? $olditem->courseid ?? 0);
    $record->cmid = (int)($newitem->cmid ?? $olditem->cmid ?? 0);
    $record->contextid = (int)($newitem->contextid ?? $olditem->contextid ?? 0);
    $record->userid = (int)($newitem->userid ?? $olditem->userid ?? 0);
    $record->createdby = $userid;
    $record->modifiedby = $userid;
    $record->timecreated = $now;
    $record->timemodified = $now;
    $record->status = UCKKARCHIVE_STATUS_VALIDATED;
    $record->visibility = (string)($newitem->visibility ?? $olditem->visibility ?? UCKKARCHIVE_VISIBILITY_COURSE);
    $record->versionno = max(1, (int)($newitem->versionno ?? 1));
    $record->provenancehash = uckkarchive_compute_provenance_hash([
        'old' => $olditem,
        'new' => $newitem,
        'reason' => $reason,
        'userid' => $userid,
        'timecreated' => $now,
    ]);

    $record->previousstate = uckkarchive_encode_metadata((array)$olditem);
    $record->newstate = uckkarchive_encode_metadata((array)$newitem);
    $record->changereason = $reason;
    $record->integritycaseid = $integritycaseid;
    $record->metadata = uckkarchive_encode_metadata([
        'origin' => 'mod_uckkarchive',
        'action' => 'revision',
    ]);

    return (int)$DB->insert_record(UCKKARCHIVE_REVISION_TABLE, $record);
}
}


/**
 * Insert a provenance record for an archive item.
 *
 * @param int $archiveid Archive instance id.
 * @param int $itemid Archive item id.
 * @param int $contextid Context id.
 * @param int $userid User id.
 * @param string $origincomponent Origin component.
 * @param int $originobjectid Origin object id.
 * @param string $source Description of source.
 * @param string $provenance Provenance source.
 * @param array<string, mixed> $metadata Additional metadata.
 * @return int Provenance record id.
 */
if (!function_exists('uckkarchive_create_provenance_record')) {
function uckkarchive_create_provenance_record(
    int $archiveid,
    int $itemid,
    int $contextid,
    int $userid,
    string $origincomponent,
    int $originobjectid,
    string $source,
    string $provenance = UCKKARCHIVE_PROVENANCE_HUMAN,
    array $metadata = []
): int {
    global $DB;

    $now = time();

    $record = new stdClass();
    $record->archiveid = $archiveid;
    $record->itemid = $itemid;
    $record->courseid = (int)($metadata['courseid'] ?? 0);
    $record->cmid = (int)($metadata['cmid'] ?? 0);
    $record->contextid = $contextid;
    $record->userid = $userid;
    $record->createdby = $userid;
    $record->modifiedby = $userid;
    $record->timecreated = $now;
    $record->timemodified = $now;
    $record->status = UCKKARCHIVE_STATUS_VALIDATED;
    $record->visibility = uckkarchive_normalise_visibility($metadata['visibility'] ?? UCKKARCHIVE_VISIBILITY_COURSE);
    $record->versionno = 1;

    $record->origincomponent = clean_param($origincomponent, PARAM_COMPONENT);
    $record->originobjectid = $originobjectid;
    $record->source = $source;
    $record->provenance = uckkarchive_normalise_provenance_source($provenance);
    $record->provenancehash = uckkarchive_compute_provenance_hash([
        'archiveid' => $archiveid,
        'itemid' => $itemid,
        'origincomponent' => $origincomponent,
        'originobjectid' => $originobjectid,
        'source' => $source,
        'userid' => $userid,
    ]);
    $record->metadata = uckkarchive_encode_metadata($metadata);

    return (int)$DB->insert_record(UCKKARCHIVE_PROVENANCE_TABLE, $record);
}
}


/**
 * Return whether an item status is terminal.
 *
 * @param string $status Status.
 * @return bool
 */
if (!function_exists('uckkarchive_is_terminal_status')) {
function uckkarchive_is_terminal_status(string $status): bool {
    $status = uckkarchive_normalise_status($status);

    return in_array($status, [
        UCKKARCHIVE_STATUS_PUBLISHED,
        UCKKARCHIVE_STATUS_INVALIDATED,
        UCKKARCHIVE_STATUS_SUPERSEDED,
        UCKKARCHIVE_STATUS_ARCHIVED,
    ], true);
}
}


/**
 * Return whether an item can be submitted for review.
 *
 * @param stdClass $item Item.
 * @return bool
 */
if (!function_exists('uckkarchive_item_can_submit')) {
function uckkarchive_item_can_submit(stdClass $item): bool {
    $status = uckkarchive_normalise_status($item->status ?? null);

    return in_array($status, [
        UCKKARCHIVE_STATUS_DRAFT,
        UCKKARCHIVE_STATUS_CONTESTED,
    ], true);
}
}


/**
 * Return whether an item can be validated.
 *
 * @param stdClass $item Item.
 * @return bool
 */
if (!function_exists('uckkarchive_item_can_validate')) {
function uckkarchive_item_can_validate(stdClass $item): bool {
    $status = uckkarchive_normalise_status($item->status ?? null);

    return in_array($status, [
        UCKKARCHIVE_STATUS_SUBMITTED,
        UCKKARCHIVE_STATUS_UNDER_REVIEW,
        UCKKARCHIVE_STATUS_CONTESTED,
    ], true);
}
}


/**
 * Return whether an item can be revised.
 *
 * @param stdClass $item Item.
 * @return bool
 */
if (!function_exists('uckkarchive_item_can_revise')) {
function uckkarchive_item_can_revise(stdClass $item): bool {
    $status = uckkarchive_normalise_status($item->status ?? null);

    return !in_array($status, [
        UCKKARCHIVE_STATUS_INVALIDATED,
        UCKKARCHIVE_STATUS_ARCHIVED,
    ], true);
}
}


/**
 * Return whether an item can be exported.
 *
 * @param stdClass $item Item.
 * @return bool
 */
if (!function_exists('uckkarchive_item_can_export')) {
function uckkarchive_item_can_export(stdClass $item): bool {
    $status = uckkarchive_normalise_status($item->status ?? null);

    return in_array($status, [
        UCKKARCHIVE_STATUS_VALIDATED,
        UCKKARCHIVE_STATUS_PUBLISHED,
        UCKKARCHIVE_STATUS_RESTRICTED,
        UCKKARCHIVE_STATUS_ARCHIVED,
    ], true);
}
}


/**
 * Return whether a plugin table exists.
 *
 * @param string $tablename Table name without Moodle prefix.
 * @return bool
 */
if (!function_exists('uckkarchive_table_exists')) {
function uckkarchive_table_exists(string $tablename): bool {
    global $DB;

    return $DB->get_manager()->table_exists(new xmldb_table($tablename));
}
}


/**
 * Return whether a plugin table field exists.
 *
 * @param string $tablename Table name without Moodle prefix.
 * @param string $field Field name.
 * @return bool
 */
if (!function_exists('uckkarchive_table_field_exists')) {
function uckkarchive_table_field_exists(string $tablename, string $field): bool {
    global $DB;

    if (!uckkarchive_table_exists($tablename)) {
        return false;
    }

    $columns = $DB->get_columns($tablename);

    return array_key_exists($field, $columns);
}
}


/**
 * Return the first existing table field from a candidate list.
 *
 * @param string $tablename Table name without Moodle prefix.
 * @param string[] $fields Candidate fields.
 * @return string|null
 */
if (!function_exists('uckkarchive_first_table_field')) {
function uckkarchive_first_table_field(string $tablename, array $fields): ?string {
    foreach ($fields as $field) {
        if (uckkarchive_table_field_exists($tablename, $field)) {
            return $field;
        }
    }

    return null;
}
}


/**
 * Safe capability check.
 *
 * Unknown capabilities are treated as false so this helper remains usable
 * during upgrade/install transitions while db/access.php is being expanded.
 *
 * @param string $capability Capability name.
 * @param context_module $context Context.
 * @param stdClass|null $user User.
 * @return bool
 */
if (!function_exists('uckkarchive_has_capability')) {
function uckkarchive_has_capability(string $capability, context_module $context, ?stdClass $user = null): bool {
    if (function_exists('get_capability_info') && !get_capability_info($capability)) {
        return false;
    }

    return has_capability($capability, $context, $user);
}
}


/**
 * Return media statuses.
 *
 * @return string[]
 */
if (!function_exists('uckkarchive_get_media_statuses')) {
function uckkarchive_get_media_statuses(): array {
    return [
        UCKKARCHIVE_MEDIA_STATUS_DRAFT,
        UCKKARCHIVE_MEDIA_STATUS_ACTIVE,
        UCKKARCHIVE_MEDIA_STATUS_ARCHIVED,
        UCKKARCHIVE_MEDIA_STATUS_RESTRICTED,
        UCKKARCHIVE_MEDIA_STATUS_DELETED_SOFT,
    ];
}
}


/**
 * Return media status options.
 *
 * @return array<string, string>
 */
if (!function_exists('uckkarchive_get_media_status_options')) {
function uckkarchive_get_media_status_options(): array {
    $options = [];

    foreach (uckkarchive_get_media_statuses() as $status) {
        $options[$status] = uckkarchive_get_string_if_exists(
            'mediastatus_' . $status,
            ucfirst(str_replace('_', ' ', $status))
        );
    }

    return $options;
}
}


/**
 * Return media types.
 *
 * @return string[]
 */
if (!function_exists('uckkarchive_get_media_types')) {
function uckkarchive_get_media_types(): array {
    return [
        UCKKARCHIVE_MEDIA_TYPE_IMAGE,
        UCKKARCHIVE_MEDIA_TYPE_AUDIO,
        UCKKARCHIVE_MEDIA_TYPE_VIDEO,
        UCKKARCHIVE_MEDIA_TYPE_DOCUMENT,
        UCKKARCHIVE_MEDIA_TYPE_LINK,
        UCKKARCHIVE_MEDIA_TYPE_OTHER,
    ];
}
}


/**
 * Return media type options.
 *
 * @return array<string, string>
 */
if (!function_exists('uckkarchive_get_media_type_options')) {
function uckkarchive_get_media_type_options(): array {
    $options = [];

    foreach (uckkarchive_get_media_types() as $type) {
        $options[$type] = uckkarchive_get_string_if_exists(
            'mediatype_' . $type,
            ucfirst(str_replace('_', ' ', $type))
        );
    }

    return $options;
}
}


/**
 * Return media source types.
 *
 * @return string[]
 */
if (!function_exists('uckkarchive_get_media_source_types')) {
function uckkarchive_get_media_source_types(): array {
    return [
        UCKKARCHIVE_MEDIA_SOURCE_UCKK_PRODUCED,
        UCKKARCHIVE_MEDIA_SOURCE_EXTERNAL,
    ];
}
}


/**
 * Return content advisory severities.
 *
 * @return string[]
 */
if (!function_exists('uckkarchive_get_content_severities')) {
function uckkarchive_get_content_severities(): array {
    return [
        UCKKARCHIVE_CONTENT_SEVERITY_NOTICE,
        UCKKARCHIVE_CONTENT_SEVERITY_MODERATE,
        UCKKARCHIVE_CONTENT_SEVERITY_STRONG,
        UCKKARCHIVE_CONTENT_SEVERITY_RESTRICTED,
    ];
}
}


/**
 * Return content advisory review states.
 *
 * @return string[]
 */
if (!function_exists('uckkarchive_get_content_review_states')) {
function uckkarchive_get_content_review_states(): array {
    return [
        UCKKARCHIVE_CONTENT_REVIEW_DRAFT,
        UCKKARCHIVE_CONTENT_REVIEW_PENDING,
        UCKKARCHIVE_CONTENT_REVIEW_REVIEWED,
        UCKKARCHIVE_CONTENT_REVIEW_APPROVED,
        UCKKARCHIVE_CONTENT_REVIEW_CONTESTED,
        UCKKARCHIVE_CONTENT_REVIEW_RETIRED,
    ];
}
}


/**
 * Return audience suitability values.
 *
 * @return string[]
 */
if (!function_exists('uckkarchive_get_audience_suitabilities')) {
function uckkarchive_get_audience_suitabilities(): array {
    return [
        UCKKARCHIVE_AUDIENCE_GENERAL,
        UCKKARCHIVE_AUDIENCE_GUIDED,
        UCKKARCHIVE_AUDIENCE_MATURE,
        UCKKARCHIVE_AUDIENCE_RESTRICTED,
        UCKKARCHIVE_AUDIENCE_RESTRICTED_CULTURAL,
        UCKKARCHIVE_AUDIENCE_RESTRICTED_INTEGRITY,
        UCKKARCHIVE_AUDIENCE_STAFF_ONLY,
    ];
}
}


/**
 * Return external work types.
 *
 * @return string[]
 */
if (!function_exists('uckkarchive_get_external_work_types')) {
function uckkarchive_get_external_work_types(): array {
    return [
        UCKKARCHIVE_EXTERNAL_WORK_TYPE_BOOK,
        UCKKARCHIVE_EXTERNAL_WORK_TYPE_FILM,
        UCKKARCHIVE_EXTERNAL_WORK_TYPE_ARTICLE,
        UCKKARCHIVE_EXTERNAL_WORK_TYPE_PODCAST,
        UCKKARCHIVE_EXTERNAL_WORK_TYPE_WEBSITE,
        UCKKARCHIVE_EXTERNAL_WORK_TYPE_EXTERNAL_VIDEO,
        UCKKARCHIVE_EXTERNAL_WORK_TYPE_EXTERNAL_IMAGE,
        UCKKARCHIVE_EXTERNAL_WORK_TYPE_PUBLIC_ARCHIVE_ITEM,
        UCKKARCHIVE_EXTERNAL_WORK_TYPE_THIRD_PARTY_PDF,
        UCKKARCHIVE_EXTERNAL_WORK_TYPE_OTHER,
    ];
}
}


/**
 * Return external work statuses.
 *
 * @return string[]
 */
if (!function_exists('uckkarchive_get_external_work_statuses')) {
function uckkarchive_get_external_work_statuses(): array {
    return [
        UCKKARCHIVE_EXTERNAL_WORK_STATUS_DRAFT,
        UCKKARCHIVE_EXTERNAL_WORK_STATUS_ACTIVE,
        UCKKARCHIVE_EXTERNAL_WORK_STATUS_RESTRICTED,
        UCKKARCHIVE_EXTERNAL_WORK_STATUS_ARCHIVED,
        UCKKARCHIVE_EXTERNAL_WORK_STATUS_DELETED_SOFT,
    ];
}
}


/**
 * Return external work rights statuses.
 *
 * @return string[]
 */
if (!function_exists('uckkarchive_get_external_work_rights_statuses')) {
function uckkarchive_get_external_work_rights_statuses(): array {
    return [
        UCKKARCHIVE_RIGHTS_UNKNOWN,
        UCKKARCHIVE_RIGHTS_THIRD_PARTY_COPYRIGHT,
        UCKKARCHIVE_RIGHTS_LICENSED_EXTERNAL,
        UCKKARCHIVE_RIGHTS_PUBLIC_DOMAIN,
        UCKKARCHIVE_RIGHTS_OPEN_LICENSE,
        UCKKARCHIVE_RIGHTS_FAIR_USE_REFERENCE,
        UCKKARCHIVE_RIGHTS_RESTRICTED_REFERENCE,
    ];
}
}


/**
 * Return canonical media File API areas.
 *
 * @return string[]
 */
if (!function_exists('uckkarchive_get_media_fileareas')) {
function uckkarchive_get_media_fileareas(): array {
    if (class_exists('\mod_uckkarchive\local\file_area_registry') &&
            method_exists('\mod_uckkarchive\local\file_area_registry', 'get_media_fileareas')) {
        return \mod_uckkarchive\local\file_area_registry::get_media_fileareas();
    }

    return [
        UCKKARCHIVE_FILEAREA_MEDIA_ORIGINAL,
        UCKKARCHIVE_FILEAREA_MEDIA_PREVIEW,
        UCKKARCHIVE_FILEAREA_MEDIA_THUMBNAIL,
        UCKKARCHIVE_FILEAREA_MEDIA_DERIVATIVE,
        UCKKARCHIVE_FILEAREA_MEDIA_CAPTION,
        UCKKARCHIVE_FILEAREA_MEDIA_TRANSCRIPT,
        UCKKARCHIVE_FILEAREA_MEDIA_ATTACHMENT,
    ];
}
}


/**
 * Return canonical non-media File API areas owned by this plugin.
 *
 * @return string[]
 */
if (!function_exists('uckkarchive_get_support_fileareas')) {
function uckkarchive_get_support_fileareas(): array {
    return [
        UCKKARCHIVE_FILEAREA_CONTENT_REVIEW,
        UCKKARCHIVE_FILEAREA_EXTERNAL_WORK_REFERENCE,
        UCKKARCHIVE_FILEAREA_CULTURAL_PROTOCOL,
        UCKKARCHIVE_FILEAREA_EXPORT_MANIFEST,
        UCKKARCHIVE_FILEAREA_EXPORT_PACKAGE,
    ];
}
}


/**
 * Return whether a media file area is canonical.
 *
 * @param string $filearea File area.
 * @return bool
 */
if (!function_exists('uckkarchive_is_media_filearea')) {
function uckkarchive_is_media_filearea(string $filearea): bool {
    return in_array(clean_param($filearea, PARAM_ALPHANUMEXT), uckkarchive_get_media_fileareas(), true);
}
}


/**
 * Return whether a plugin file area is canonical.
 *
 * @param string $filearea File area.
 * @return bool
 */
if (!function_exists('uckkarchive_is_filearea')) {
function uckkarchive_is_filearea(string $filearea): bool {
    $fileareas = array_values(array_unique(array_merge(
        uckkarchive_get_media_fileareas(),
        uckkarchive_get_support_fileareas()
    )));

    return in_array(clean_param($filearea, PARAM_ALPHANUMEXT), $fileareas, true);
}
}


/**
 * Build media controller URL.
 *
 * @param int $cmid Course module id.
 * @param int $mediaid Media id.
 * @param array<string, mixed> $params Extra parameters.
 * @return moodle_url
 */
if (!function_exists('uckkarchive_media_url')) {
function uckkarchive_media_url(int $cmid, int $mediaid = 0, array $params = []): moodle_url {
    $params = ['id' => $cmid] + $params;

    if ($mediaid > 0) {
        $params['mediaid'] = $mediaid;
    }

    return uckkarchive_url('media.php', $params);
}
}


/**
 * Build external work URL.
 *
 * @param int $cmid Course module id.
 * @param int $externalworkid External work id.
 * @param array<string, mixed> $params Extra parameters.
 * @return moodle_url
 */
if (!function_exists('uckkarchive_external_work_url')) {
function uckkarchive_external_work_url(int $cmid, int $externalworkid = 0, array $params = []): moodle_url {
    $params = ['id' => $cmid] + $params;

    if ($externalworkid > 0) {
        $params['externalworkid'] = $externalworkid;
    }

    return uckkarchive_url('media.php', $params);
}
}


/**
 * Return whether user can view media.
 *
 * @param context_module $context Context.
 * @param stdClass|null $user User.
 * @return bool
 */
if (!function_exists('uckkarchive_can_view_media')) {
function uckkarchive_can_view_media(context_module $context, ?stdClass $user = null): bool {
    return uckkarchive_has_capability('mod/uckkarchive:viewmedia', $context, $user) ||
        has_capability('mod/uckkarchive:view', $context, $user);
}
}


/**
 * Return whether user can add media.
 *
 * @param context_module $context Context.
 * @param stdClass|null $user User.
 * @return bool
 */
if (!function_exists('uckkarchive_can_add_media')) {
function uckkarchive_can_add_media(context_module $context, ?stdClass $user = null): bool {
    return uckkarchive_has_capability('mod/uckkarchive:addmedia', $context, $user);
}
}


/**
 * Return whether user can edit media.
 *
 * @param context_module $context Context.
 * @param stdClass|null $user User.
 * @return bool
 */
if (!function_exists('uckkarchive_can_edit_media')) {
function uckkarchive_can_edit_media(context_module $context, ?stdClass $user = null): bool {
    return uckkarchive_has_capability('mod/uckkarchive:editmedia', $context, $user);
}
}


/**
 * Return whether user can delete media.
 *
 * @param context_module $context Context.
 * @param stdClass|null $user User.
 * @return bool
 */
if (!function_exists('uckkarchive_can_delete_media')) {
function uckkarchive_can_delete_media(context_module $context, ?stdClass $user = null): bool {
    return uckkarchive_has_capability('mod/uckkarchive:deletemedia', $context, $user);
}
}


/**
 * Return whether user can download media files.
 *
 * @param context_module $context Context.
 * @param stdClass|null $user User.
 * @return bool
 */
if (!function_exists('uckkarchive_can_download_media')) {
function uckkarchive_can_download_media(context_module $context, ?stdClass $user = null): bool {
    return uckkarchive_has_capability('mod/uckkarchive:downloadmedia', $context, $user);
}
}


/**
 * Return whether user can export media.
 *
 * @param context_module $context Context.
 * @param stdClass|null $user User.
 * @return bool
 */
if (!function_exists('uckkarchive_can_export_media')) {
function uckkarchive_can_export_media(context_module $context, ?stdClass $user = null): bool {
    return uckkarchive_has_capability('mod/uckkarchive:exportmedia', $context, $user) ||
        uckkarchive_can_export($context, $user);
}
}


/**
 * Return whether user can create media versions.
 *
 * @param context_module $context Context.
 * @param stdClass|null $user User.
 * @return bool
 */
if (!function_exists('uckkarchive_can_version_media')) {
function uckkarchive_can_version_media(context_module $context, ?stdClass $user = null): bool {
    return uckkarchive_has_capability('mod/uckkarchive:versionmedia', $context, $user);
}
}


/**
 * Return whether user can manage media collections.
 *
 * @param context_module $context Context.
 * @param stdClass|null $user User.
 * @return bool
 */
if (!function_exists('uckkarchive_can_manage_media_collections')) {
function uckkarchive_can_manage_media_collections(context_module $context, ?stdClass $user = null): bool {
    return uckkarchive_has_capability('mod/uckkarchive:managemediacollections', $context, $user);
}
}


/**
 * Return whether user can view content advisories.
 *
 * @param context_module $context Context.
 * @param stdClass|null $user User.
 * @return bool
 */
if (!function_exists('uckkarchive_can_view_advisories')) {
function uckkarchive_can_view_advisories(context_module $context, ?stdClass $user = null): bool {
    return uckkarchive_has_capability('mod/uckkarchive:viewadvisories', $context, $user) ||
        uckkarchive_can_view_media($context, $user);
}
}


/**
 * Return whether user can manage content advisories.
 *
 * @param context_module $context Context.
 * @param stdClass|null $user User.
 * @return bool
 */
if (!function_exists('uckkarchive_can_manage_advisories')) {
function uckkarchive_can_manage_advisories(context_module $context, ?stdClass $user = null): bool {
    return uckkarchive_has_capability('mod/uckkarchive:manageadvisories', $context, $user) ||
        uckkarchive_has_capability('mod/uckkarchive:managecontentadvisories', $context, $user);
}
}


/**
 * Return whether user can review content advisories.
 *
 * @param context_module $context Context.
 * @param stdClass|null $user User.
 * @return bool
 */
if (!function_exists('uckkarchive_can_review_advisories')) {
function uckkarchive_can_review_advisories(context_module $context, ?stdClass $user = null): bool {
    return uckkarchive_has_capability('mod/uckkarchive:reviewadvisories', $context, $user) ||
        uckkarchive_can_manage_advisories($context, $user);
}
}


/**
 * Return whether user can manage external works.
 *
 * @param context_module $context Context.
 * @param stdClass|null $user User.
 * @return bool
 */
if (!function_exists('uckkarchive_can_manage_external_works')) {
function uckkarchive_can_manage_external_works(context_module $context, ?stdClass $user = null): bool {
    return uckkarchive_has_capability('mod/uckkarchive:manageexternalworks', $context, $user) ||
        uckkarchive_can_manage_advisories($context, $user);
}
}


/**
 * Return whether user can view culturally restricted archive/media data.
 *
 * @param context_module $context Context.
 * @param stdClass|null $user User.
 * @return bool
 */
if (!function_exists('uckkarchive_can_view_culturally_restricted')) {
function uckkarchive_can_view_culturally_restricted(context_module $context, ?stdClass $user = null): bool {
    return uckkarchive_has_capability('mod/uckkarchive:viewculturallyrestricted', $context, $user);
}
}


/**
 * Return whether a visibility value is restricted.
 *
 * @param string $visibility Visibility.
 * @return bool
 */
if (!function_exists('uckkarchive_is_restricted_visibility')) {
function uckkarchive_is_restricted_visibility(string $visibility): bool {
    return in_array($visibility, [
        UCKKARCHIVE_VISIBILITY_RESTRICTED,
        UCKKARCHIVE_VISIBILITY_RESTRICTED_CULTURAL,
        UCKKARCHIVE_VISIBILITY_RESTRICTED_INTEGRITY,
    ], true);
}
}


/**
 * Return one media record.
 *
 * @param int $mediaid Media id.
 * @param int|null $archiveid Optional archive id.
 * @return stdClass|null
 */
if (!function_exists('uckkarchive_get_media')) {
function uckkarchive_get_media(int $mediaid, ?int $archiveid = null): ?stdClass {
    global $DB;

    if ($mediaid <= 0 || !uckkarchive_table_exists(UCKKARCHIVE_MEDIA_TABLE)) {
        return null;
    }

    $media = $DB->get_record(UCKKARCHIVE_MEDIA_TABLE, ['id' => $mediaid], '*', IGNORE_MISSING);
    if (!$media) {
        return null;
    }

    if ($archiveid !== null) {
        $archivefield = uckkarchive_first_table_field(UCKKARCHIVE_MEDIA_TABLE, ['archiveid', 'uckkarchiveid']);
        if ($archivefield !== null && (int)$media->{$archivefield} !== (int)$archiveid) {
            return null;
        }
    }

    return $media;
}
}


/**
 * Return visible media records for an archive.
 *
 * @param stdClass $archive Archive instance.
 * @param context_module $context Context.
 * @param stdClass|null $user User.
 * @param array<string, mixed> $filters Filters.
 * @param int $limit Limit.
 * @param int $offset Offset.
 * @return stdClass[]
 */
if (!function_exists('uckkarchive_get_visible_media')) {
function uckkarchive_get_visible_media(
    stdClass $archive,
    context_module $context,
    ?stdClass $user = null,
    array $filters = [],
    int $limit = 0,
    int $offset = 0
): array {
    global $DB, $USER;

    if (!uckkarchive_table_exists(UCKKARCHIVE_MEDIA_TABLE)) {
        return [];
    }

    $user ??= $USER;

    if (!uckkarchive_can_view_media($context, $user)) {
        return [];
    }

    $where = [];
    $params = [];

    $archivefield = uckkarchive_first_table_field(UCKKARCHIVE_MEDIA_TABLE, ['archiveid', 'uckkarchiveid']);
    if ($archivefield !== null) {
        $where[] = $archivefield . ' = :archiveid';
        $params['archiveid'] = (int)$archive->id;
    }

    if (!empty($filters['status']) && uckkarchive_table_field_exists(UCKKARCHIVE_MEDIA_TABLE, 'status')) {
        $where[] = 'status = :status';
        $params['status'] = clean_param((string)$filters['status'], PARAM_ALPHANUMEXT);
    }

    $typefield = uckkarchive_first_table_field(UCKKARCHIVE_MEDIA_TABLE, ['mediatype', 'type']);
    if (!empty($filters['mediatype']) && $typefield !== null) {
        $where[] = $typefield . ' = :mediatype';
        $params['mediatype'] = clean_param((string)$filters['mediatype'], PARAM_ALPHANUMEXT);
    }

    $visibilityfield = uckkarchive_first_table_field(UCKKARCHIVE_MEDIA_TABLE, ['visibility']);
    if (!uckkarchive_can_view_restricted($context, $user)) {
        if ($visibilityfield !== null) {
            $where[] = $visibilityfield . ' NOT IN (:visibilityrestricted, :visibilitycultural, :visibilityintegrity)';
            $params['visibilityrestricted'] = UCKKARCHIVE_VISIBILITY_RESTRICTED;
            $params['visibilitycultural'] = UCKKARCHIVE_VISIBILITY_RESTRICTED_CULTURAL;
            $params['visibilityintegrity'] = UCKKARCHIVE_VISIBILITY_RESTRICTED_INTEGRITY;
        }

        if (uckkarchive_table_field_exists(UCKKARCHIVE_MEDIA_TABLE, 'status')) {
            $where[] = 'status <> :statusrestricted';
            $params['statusrestricted'] = UCKKARCHIVE_MEDIA_STATUS_RESTRICTED;
        }
    }

    if (!uckkarchive_can_delete_media($context, $user) &&
            uckkarchive_table_field_exists(UCKKARCHIVE_MEDIA_TABLE, 'status')) {
        $where[] = 'status <> :statusdeleted';
        $params['statusdeleted'] = UCKKARCHIVE_MEDIA_STATUS_DELETED_SOFT;
    }

    if (empty($where)) {
        $where[] = '1 = 1';
    }

    $sortfield = uckkarchive_table_field_exists(UCKKARCHIVE_MEDIA_TABLE, 'timemodified') ? 'timemodified' : 'id';

    $sql = 'SELECT *
              FROM {' . UCKKARCHIVE_MEDIA_TABLE . '}
             WHERE ' . implode(' AND ', $where) . '
          ORDER BY ' . $sortfield . ' DESC, id DESC';

    return $DB->get_records_sql($sql, $params, $offset, $limit);
}
}


/**
 * Count visible media records.
 *
 * @param stdClass $archive Archive instance.
 * @param context_module $context Context.
 * @param stdClass|null $user User.
 * @param array<string, mixed> $filters Filters.
 * @return int
 */
if (!function_exists('uckkarchive_count_visible_media')) {
function uckkarchive_count_visible_media(
    stdClass $archive,
    context_module $context,
    ?stdClass $user = null,
    array $filters = []
): int {
    return count(uckkarchive_get_visible_media($archive, $context, $user, $filters));
}
}


/**
 * Return content advisory markers for a target.
 *
 * @param string $targettype Target type.
 * @param int $targetid Target id.
 * @param context_module $context Context.
 * @param stdClass|null $user User.
 * @param array<string, mixed> $filters Filters.
 * @return stdClass[]
 */
if (!function_exists('uckkarchive_get_content_markers')) {
function uckkarchive_get_content_markers(
    string $targettype,
    int $targetid,
    context_module $context,
    ?stdClass $user = null,
    array $filters = []
): array {
    global $DB, $USER;

    if ($targetid <= 0 || !uckkarchive_table_exists(UCKKARCHIVE_CONTENT_MARKER_TABLE)) {
        return [];
    }

    $user ??= $USER;

    if (!uckkarchive_can_view_advisories($context, $user)) {
        return [];
    }

    if (class_exists('\mod_uckkarchive\local\content_marker') &&
            method_exists('\mod_uckkarchive\local\content_marker', 'list_by_target')) {
        return \mod_uckkarchive\local\content_marker::list_by_target($targettype, $targetid, $filters);
    }

    $where = [];
    $params = [];

    if (uckkarchive_table_field_exists(UCKKARCHIVE_CONTENT_MARKER_TABLE, 'targettype')) {
        $where[] = 'targettype = :targettype';
        $params['targettype'] = clean_param($targettype, PARAM_ALPHANUMEXT);
    }

    if (uckkarchive_table_field_exists(UCKKARCHIVE_CONTENT_MARKER_TABLE, 'targetid')) {
        $where[] = 'targetid = :targetid';
        $params['targetid'] = $targetid;
    } else if ($targettype === 'media' && uckkarchive_table_field_exists(UCKKARCHIVE_CONTENT_MARKER_TABLE, 'mediaid')) {
        $where[] = 'mediaid = :targetid';
        $params['targetid'] = $targetid;
    } else if ($targettype === 'external_work' &&
            uckkarchive_table_field_exists(UCKKARCHIVE_CONTENT_MARKER_TABLE, 'externalworkid')) {
        $where[] = 'externalworkid = :targetid';
        $params['targetid'] = $targetid;
    }

    if (!uckkarchive_can_view_restricted($context, $user) &&
            uckkarchive_table_field_exists(UCKKARCHIVE_CONTENT_MARKER_TABLE, 'visibility')) {
        $where[] = 'visibility NOT IN (:visibilityrestricted, :visibilitycultural, :visibilityintegrity)';
        $params['visibilityrestricted'] = UCKKARCHIVE_VISIBILITY_RESTRICTED;
        $params['visibilitycultural'] = UCKKARCHIVE_VISIBILITY_RESTRICTED_CULTURAL;
        $params['visibilityintegrity'] = UCKKARCHIVE_VISIBILITY_RESTRICTED_INTEGRITY;
    }

    if (empty($where)) {
        return [];
    }

    $sortfield = uckkarchive_table_field_exists(UCKKARCHIVE_CONTENT_MARKER_TABLE, 'timemodified') ? 'timemodified' : 'id';

    $sql = 'SELECT *
              FROM {' . UCKKARCHIVE_CONTENT_MARKER_TABLE . '}
             WHERE ' . implode(' AND ', $where) . '
          ORDER BY ' . $sortfield . ' DESC, id DESC';

    return $DB->get_records_sql($sql, $params);
}
}


/**
 * Count content markers for an archive.
 *
 * @param stdClass $archive Archive instance.
 * @param context_module $context Context.
 * @param stdClass|null $user User.
 * @return int
 */
if (!function_exists('uckkarchive_count_content_markers')) {
function uckkarchive_count_content_markers(stdClass $archive, context_module $context, ?stdClass $user = null): int {
    global $DB, $USER;

    if (!uckkarchive_table_exists(UCKKARCHIVE_CONTENT_MARKER_TABLE)) {
        return 0;
    }

    $user ??= $USER;

    if (!uckkarchive_can_view_advisories($context, $user)) {
        return 0;
    }

    $where = [];
    $params = [];

    if (uckkarchive_table_field_exists(UCKKARCHIVE_CONTENT_MARKER_TABLE, 'archiveid')) {
        $where[] = 'archiveid = :archiveid';
        $params['archiveid'] = (int)$archive->id;
    }

    if (!uckkarchive_can_view_restricted($context, $user) &&
            uckkarchive_table_field_exists(UCKKARCHIVE_CONTENT_MARKER_TABLE, 'visibility')) {
        $where[] = 'visibility NOT IN (:visibilityrestricted, :visibilitycultural, :visibilityintegrity)';
        $params['visibilityrestricted'] = UCKKARCHIVE_VISIBILITY_RESTRICTED;
        $params['visibilitycultural'] = UCKKARCHIVE_VISIBILITY_RESTRICTED_CULTURAL;
        $params['visibilityintegrity'] = UCKKARCHIVE_VISIBILITY_RESTRICTED_INTEGRITY;
    }

    if (empty($where)) {
        $where[] = '1 = 1';
    }

    return (int)$DB->count_records_sql(
        'SELECT COUNT(1)
           FROM {' . UCKKARCHIVE_CONTENT_MARKER_TABLE . '}
          WHERE ' . implode(' AND ', $where),
        $params
    );
}
}


/**
 * Return one external work.
 *
 * @param int $externalworkid External work id.
 * @param int|null $archiveid Optional archive id.
 * @return stdClass|null
 */
if (!function_exists('uckkarchive_get_external_work')) {
function uckkarchive_get_external_work(int $externalworkid, ?int $archiveid = null): ?stdClass {
    global $DB;

    if ($externalworkid <= 0 || !uckkarchive_table_exists(UCKKARCHIVE_EXTERNAL_WORK_TABLE)) {
        return null;
    }

    $work = $DB->get_record(UCKKARCHIVE_EXTERNAL_WORK_TABLE, ['id' => $externalworkid], '*', IGNORE_MISSING);
    if (!$work) {
        return null;
    }

    if ($archiveid !== null && uckkarchive_table_field_exists(UCKKARCHIVE_EXTERNAL_WORK_TABLE, 'archiveid') &&
            (int)$work->archiveid !== (int)$archiveid) {
        return null;
    }

    return $work;
}
}


/**
 * Return external works for an archive.
 *
 * @param stdClass $archive Archive instance.
 * @param context_module $context Context.
 * @param stdClass|null $user User.
 * @param array<string, mixed> $filters Filters.
 * @param int $limit Limit.
 * @param int $offset Offset.
 * @return stdClass[]
 */
if (!function_exists('uckkarchive_get_external_works')) {
function uckkarchive_get_external_works(
    stdClass $archive,
    context_module $context,
    ?stdClass $user = null,
    array $filters = [],
    int $limit = 0,
    int $offset = 0
): array {
    global $DB, $USER;

    if (!uckkarchive_table_exists(UCKKARCHIVE_EXTERNAL_WORK_TABLE)) {
        return [];
    }

    $user ??= $USER;

    if (!uckkarchive_can_view_advisories($context, $user) && !uckkarchive_can_view_media($context, $user)) {
        return [];
    }

    $where = [];
    $params = [];

    if (uckkarchive_table_field_exists(UCKKARCHIVE_EXTERNAL_WORK_TABLE, 'archiveid')) {
        $where[] = 'archiveid = :archiveid';
        $params['archiveid'] = (int)$archive->id;
    }

    if (!empty($filters['worktype']) && uckkarchive_table_field_exists(UCKKARCHIVE_EXTERNAL_WORK_TABLE, 'worktype')) {
        $where[] = 'worktype = :worktype';
        $params['worktype'] = clean_param((string)$filters['worktype'], PARAM_ALPHANUMEXT);
    }

    if (!empty($filters['status']) && uckkarchive_table_field_exists(UCKKARCHIVE_EXTERNAL_WORK_TABLE, 'status')) {
        $where[] = 'status = :status';
        $params['status'] = clean_param((string)$filters['status'], PARAM_ALPHANUMEXT);
    }

    if (!uckkarchive_can_view_restricted($context, $user) &&
            uckkarchive_table_field_exists(UCKKARCHIVE_EXTERNAL_WORK_TABLE, 'visibility')) {
        $where[] = 'visibility NOT IN (:visibilityrestricted, :visibilitycultural, :visibilityintegrity)';
        $params['visibilityrestricted'] = UCKKARCHIVE_VISIBILITY_RESTRICTED;
        $params['visibilitycultural'] = UCKKARCHIVE_VISIBILITY_RESTRICTED_CULTURAL;
        $params['visibilityintegrity'] = UCKKARCHIVE_VISIBILITY_RESTRICTED_INTEGRITY;
    }

    if (empty($where)) {
        $where[] = '1 = 1';
    }

    $sortfield = uckkarchive_table_field_exists(UCKKARCHIVE_EXTERNAL_WORK_TABLE, 'timemodified') ? 'timemodified' : 'id';

    $sql = 'SELECT *
              FROM {' . UCKKARCHIVE_EXTERNAL_WORK_TABLE . '}
             WHERE ' . implode(' AND ', $where) . '
          ORDER BY ' . $sortfield . ' DESC, id DESC';

    return $DB->get_records_sql($sql, $params, $offset, $limit);
}
}


/**
 * Count external works for an archive.
 *
 * @param stdClass $archive Archive instance.
 * @param context_module $context Context.
 * @param stdClass|null $user User.
 * @return int
 */
if (!function_exists('uckkarchive_count_external_works')) {
function uckkarchive_count_external_works(stdClass $archive, context_module $context, ?stdClass $user = null): int {
    return count(uckkarchive_get_external_works($archive, $context, $user));
}
}


/**
 * Build a compact archive summary for dashboards/reports.
 *
 * @param stdClass $archive Archive instance.
 * @param context_module $context Context.
 * @param stdClass|null $user User.
 * @return stdClass
 */
if (!function_exists('uckkarchive_get_summary')) {
function uckkarchive_get_summary(stdClass $archive, context_module $context, ?stdClass $user = null): stdClass {
    $summary = new stdClass();

    $summary->archiveid = (int)$archive->id;
    $summary->contextid = (int)$context->id;

    $summary->totalitems = uckkarchive_count_visible_items($archive, $context, $user);
    $summary->validateditems = uckkarchive_count_visible_items($archive, $context, $user, [
        'status' => UCKKARCHIVE_STATUS_VALIDATED,
    ]);
    $summary->publisheditems = uckkarchive_count_visible_items($archive, $context, $user, [
        'status' => UCKKARCHIVE_STATUS_PUBLISHED,
    ]);
    $summary->contesteditems = uckkarchive_count_visible_items($archive, $context, $user, [
        'status' => UCKKARCHIVE_STATUS_CONTESTED,
    ]);

    $summary->totalmedia = uckkarchive_count_visible_media($archive, $context, $user);
    $summary->activemedia = uckkarchive_count_visible_media($archive, $context, $user, [
        'status' => UCKKARCHIVE_MEDIA_STATUS_ACTIVE,
    ]);
    $summary->restrictedmedia = uckkarchive_count_visible_media($archive, $context, $user, [
        'status' => UCKKARCHIVE_MEDIA_STATUS_RESTRICTED,
    ]);

    $summary->contentmarkers = uckkarchive_count_content_markers($archive, $context, $user);
    $summary->externalworks = uckkarchive_count_external_works($archive, $context, $user);

    $summary->restrictedvisible = uckkarchive_can_view_restricted($context, $user);
    $summary->culturalrestrictedvisible = uckkarchive_can_view_culturally_restricted($context, $user);
    $summary->canviewmedia = uckkarchive_can_view_media($context, $user);
    $summary->canaddmedia = uckkarchive_can_add_media($context, $user);
    $summary->canmanageadvisories = uckkarchive_can_manage_advisories($context, $user);
    $summary->canmanageexternalworks = uckkarchive_can_manage_external_works($context, $user);

    return $summary;
}
}

