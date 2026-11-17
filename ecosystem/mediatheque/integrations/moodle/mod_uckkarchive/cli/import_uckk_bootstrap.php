<?php
// This file is part of Moodle - https://moodle.org/
//
// Moodle is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// any later version.

/**
 * Import the UCKK Kristal hierarchy and Korpus into the UCKK Médiathèque.
 *
 * Usage:
 *   php mod/uckkarchive/cli/import_uckk_bootstrap.php \
 *     --archiveid=12 \
 *     --bootstrap=/path/to/mediatheque-uckk/bootstrap \
 *     --kristal-root=/path/to/Kristal-Kollection \
 *     --korpus=/path/to/Korpus
 *
 * @package    mod_uckkarchive
 * @copyright  2026 Univers-Cité King Klown
 * @license    https://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later
 */

define('CLI_SCRIPT', true);

require(__DIR__ . '/../../../config.php');
require_once($CFG->libdir . '/clilib.php');

use mod_uckkarchive\local\content_marker;
use mod_uckkarchive\local\kristal_artifact_catalog;
use mod_uckkarchive\local\media;
use mod_uckkarchive\local\media_file;
use mod_uckkarchive\local\media_collection;
use mod_uckkarchive\local\media_library_scope;
use mod_uckkarchive\local\media_source;
use mod_uckkarchive\local\media_tag;
use mod_uckkarchive\local\media_version;

[$options, $unrecognized] = cli_get_params([
    'help' => false,
    'archiveid' => 0,
    'bootstrap' => '',
    'korpus' => '',
    'kristal-root' => '',
    'mode' => 'all',
    'externalize-existing' => false,
    'dry-run' => false,
], [
    'h' => 'help',
]);

if ($options['help'] || !empty($unrecognized)) {
    $help = <<<TXT
Import the UCKK bootstrap into mod_uckkarchive.

Required:
  --archiveid=ID       Existing UCKK Archive activity instance.
  --bootstrap=PATH     mediatheque-uckk/bootstrap directory.

Optional:
  --korpus=PATH        Extracted Korpus directory containing Sorted/.
  --kristal-root=PATH  Canonical Kristal-Kollection root. Falls back to KRISTAL_KOLLECTION_ROOT.
  --mode=all|kristals|korpus|repositories
  --externalize-existing  Remove legacy copied Kristal bytes after hash verification.
  --dry-run            Validate and print planned operations without writing.
  -h, --help

The Kristal import catalogs repository references/version facts in Médiathèque without
copying canonical Kristal bytes. kristal_ref remains owned by Kristal/Kristall.
TXT;
    cli_writeln($help);
    exit($options['help'] ? 0 : 1);
}

$archiveid = (int)$options['archiveid'];
$bootstrap = rtrim((string)$options['bootstrap'], DIRECTORY_SEPARATOR);
$korpusroot = rtrim((string)$options['korpus'], DIRECTORY_SEPARATOR);
$kristalroot = rtrim((string)$options['kristal-root'], DIRECTORY_SEPARATOR);
if ($kristalroot === '') {
    $envroot = getenv('KRISTAL_KOLLECTION_ROOT');
    if (is_string($envroot) && trim($envroot) !== '') {
        $kristalroot = rtrim(trim($envroot), DIRECTORY_SEPARATOR);
    }
}
$externalizeexisting = !empty($options['externalize-existing']);
$mode = strtolower(trim((string)$options['mode']));
$dryrun = !empty($options['dry-run']);

if ($archiveid <= 0 || $bootstrap === '' || !is_dir($bootstrap)) {
    cli_error('archiveid and a readable bootstrap directory are required.');
}
if (!in_array($mode, ['all', 'kristals', 'korpus', 'repositories'], true)) {
    cli_error('mode must be all, kristals, korpus, or repositories.');
}

$planpath = $bootstrap . DIRECTORY_SEPARATOR . 'import-plan.json';
if (!is_readable($planpath)) {
    cli_error('Missing bootstrap import-plan.json: ' . $planpath);
}
$plan = json_decode((string)file_get_contents($planpath), true);
if (!is_array($plan) || !in_array(($plan['format'] ?? ''), [
    'koa.mediatheque.uckk-bootstrap/1.0.0',
    'koa.mediatheque.uckk-bootstrap/1.1.0',
    'koa.mediatheque.uckk-bootstrap/1.2.0',
], true)) {
    cli_error('Unsupported or invalid UCKK bootstrap manifest.');
}

$archive = $DB->get_record('uckkarchive', ['id' => $archiveid], '*', MUST_EXIST);
$cm = get_coursemodule_from_instance('uckkarchive', $archiveid, (int)$archive->course, false, MUST_EXIST);
$context = context_module::instance((int)$cm->id);
$admin = get_admin();
$USER = $admin;

$scope = new media_library_scope();
$library = $scope->resolve_by_slug(media_library_scope::LIBRARY_UCKK);
if (!$library) {
    cli_error('UCKK media library row is missing. Upgrade mod_uckkarchive first.');
}
if (!kristal_artifact_catalog::schema_ready()) {
    cli_error('Kristal artifact catalog tables are missing. Upgrade mod_uckkarchive first.');
}

$stats = [
    'kristals_created' => 0,
    'kristal_versions_created' => 0,
    'kristals_skipped' => 0,
    'korpus_created' => 0,
    'korpus_skipped' => 0,
    'tags_created_or_updated' => 0,
    'advisories_created' => 0,
    'repositories_created' => 0,
    'repositories_updated' => 0,
    'repositories_skipped' => 0,
    'repository_sources_created' => 0,
    'repository_collection_memberships' => 0,
];

/** @return array<string,mixed> */
function uckk_bootstrap_decode_metadata(?string $value): array {
    if ($value === null || trim($value) === '') {
        return [];
    }
    $decoded = json_decode($value, true);
    return is_array($decoded) ? $decoded : [];
}

function uckk_bootstrap_sha256(string $path): string {
    $digest = hash_file('sha256', $path);
    if (!is_string($digest) || !preg_match('/^[0-9a-f]{64}$/', $digest)) {
        throw new RuntimeException('Unable to calculate SHA-256 for ' . $path);
    }
    return $digest;
}

/**
 * Create an immutable media version and attach one local file through Moodle File API.
 */
function uckk_bootstrap_add_file_version(stdClass $mediarecord, string $sourcepath, string $label, string $sha256,
        stdClass $context, int $userid, string $status = 'active'): stdClass {
    global $DB;

    $version = media_version::create($mediarecord, [
        'label' => $label,
        'status' => $status,
        'visibility' => (string)$mediarecord->visibility,
        'audiencesuitability' => (string)$mediarecord->audiencesuitability,
        'filearea' => media_version::FILEAREA_ORIGINAL,
        'filename' => basename($sourcepath),
        'mimetype' => mime_content_type($sourcepath) ?: 'application/octet-stream',
        'iscurrent' => 1,
        'metadata' => ['sha256' => $sha256],
    ], null);

    $stored = media_file::create_file_from_pathname(
        $context,
        media_file::AREA_ORIGINAL,
        (int)$version->id,
        basename($sourcepath),
        $sourcepath,
        '/',
        $userid
    );

    $version->filearea = media_file::AREA_ORIGINAL;
    $version->filename = $stored->get_filename();
    $version->filepath = $stored->get_filepath();
    $version->filesize = $stored->get_filesize();
    $version->mimetype = $stored->get_mimetype();
    $version->contenthash = $stored->get_contenthash();
    $version->provenancehash = $sha256;
    $version->metadata = json_encode(['sha256' => $sha256], JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
    $version->modifiedby = $userid;
    $version->timemodified = time();
    $DB->update_record(media_version::TABLE, $version);

    return media_version::get((int)$version->id);
}

/** Create an immutable metadata-only version pointing at Kristal-Kollection. */
function uckk_bootstrap_add_external_kristal_version(stdClass $mediarecord, string $relativepath, string $sha256,
        int $bytes, string $repositoryurl, int $userid): stdClass {
    return media_version::create($mediarecord, [
        'label' => 'repository-reference',
        'filename' => basename($relativepath),
        'filesize' => max(0, $bytes),
        'mimetype' => 'application/json',
        'mediatype' => media::TYPE_EXTERNAL_REFERENCE,
        'status' => media_version::STATUS_ACTIVE,
        'visibility' => (string)$mediarecord->visibility,
        'audiencesuitability' => (string)$mediarecord->audiencesuitability,
        'iscurrent' => 1,
        'createdby' => $userid,
        'modifiedby' => $userid,
        'metadata' => [
            'sha256' => $sha256,
            'storage_mode' => 'external_repository_reference',
            'repository_id' => 'Kristal-Kollection',
            'repository_url' => $repositoryurl,
            'repository_relative_path' => $relativepath,
        ],
    ], null);
}

/** Convert a legacy copied Kristal media version to an external repository reference. */
function uckk_bootstrap_externalize_existing(stdClass $artifact, stdClass $kversion, string $relativepath,
        string $sha256, string $repositoryurl, stdClass $context, int $userid): void {
    global $DB;
    if (empty($kversion->mediaid) || empty($kversion->mediaversionid)) {
        return;
    }
    $mediarecord = media::get_record((int)$kversion->mediaid, IGNORE_MISSING);
    $mediaversion = media_version::get((int)$kversion->mediaversionid);
    if (!$mediarecord || !$mediaversion) {
        return;
    }
    media_file::delete_area_files($context, media_file::AREA_ORIGINAL, (int)$mediaversion->id);
    $mediarecord->mediatype = media::TYPE_EXTERNAL_REFERENCE;
    $mediarecord->mimetype = 'application/json';
    $mediarecord->source = 'kristal';
    $mediarecord->sourcetype = 'kristal_kollection';
    $mediarecord->sourceurl = $repositoryurl;
    $mediarecord->provenancehash = $sha256;
    $mediarecord->metadata = json_encode([
        'kristal_ref' => $artifact->kristalref,
        'storage_mode' => 'external_repository_reference',
        'repository_id' => 'Kristal-Kollection',
        'repository_url' => $repositoryurl,
        'repository_relative_path' => $relativepath,
        'sha256' => $sha256,
    ], JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
    $mediarecord->modifiedby = $userid;
    $mediarecord->timemodified = time();
    $DB->update_record(media::TABLE, $mediarecord);

    $mediaversion->filename = basename($relativepath);
    $mediaversion->filepath = '/';
    $mediaversion->filesize = 0;
    $mediaversion->contenthash = null;
    $mediaversion->mimetype = 'application/json';
    $mediaversion->mediatype = media::TYPE_EXTERNAL_REFERENCE;
    $mediaversion->metadata = json_encode([
        'sha256' => $sha256,
        'storage_mode' => 'external_repository_reference',
        'repository_id' => 'Kristal-Kollection',
        'repository_url' => $repositoryurl,
        'repository_relative_path' => $relativepath,
    ], JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
    $mediaversion->modifiedby = $userid;
    $mediaversion->timemodified = time();
    $DB->update_record(media_version::TABLE, $mediaversion);
}

if ($mode === 'all' || $mode === 'kristals') {
    if ($kristalroot === '' || !is_dir($kristalroot)) {
        cli_error('--kristal-root (or KRISTAL_KOLLECTION_ROOT) must point to the canonical Kristal-Kollection repository.');
    }
    $entries = $plan['kristals'] ?? [];
    if (!is_array($entries) || count($entries) !== 111) {
        cli_error('Bootstrap must contain exactly 111 Kristal identities.');
    }

    // First pass: identities and immutable stub versions.
    foreach ($entries as $entry) {
        $ref = (string)($entry['kristal_ref'] ?? '');
        $relpath = (string)($entry['source_relative_path'] ?? '');
        $sourcepath = $kristalroot . DIRECTORY_SEPARATOR . str_replace('/', DIRECTORY_SEPARATOR, $relpath);
        if (!is_readable($sourcepath)) {
            cli_error('Missing Kristal stub: ' . $sourcepath);
        }
        $sha256 = uckk_bootstrap_sha256($sourcepath);
        if ($sha256 !== (string)($entry['sha256'] ?? '')) {
            cli_error('Kristal stub hash mismatch: ' . $ref);
        }

        $existingartifact = kristal_artifact_catalog::get_by_ref((int)$library->id, $ref, IGNORE_MISSING);
        if ($dryrun) {
            cli_writeln('[DRY] Kristal ' . $ref . ' -> Kristal-Kollection/' . $relpath);
            continue;
        }

        $artifact = kristal_artifact_catalog::upsert_artifact([
            'uuid' => (string)($entry['catalog_uuid'] ?? ''),
            'libraryid' => (int)$library->id,
            'kristalref' => $ref,
            'kind' => (string)($entry['kind'] ?? 'generic'),
            'title' => (string)($entry['title'] ?? $ref),
            'voiecode' => $entry['voie_code'] ?? null,
            'coursecode' => $entry['course_code'] ?? null,
            'status' => (string)($entry['status'] ?? 'stub'),
            'portablecontract' => (string)($entry['portable_contract'] ?? kristal_artifact_catalog::PORTABLE_CONTRACT),
            'kristallbaseline' => (string)($entry['kristall_baseline'] ?? kristal_artifact_catalog::KRISTALL_BASELINE),
            'sortorder' => (int)($entry['sortorder'] ?? 0),
            'metadata' => [
                'parent_kristal_ref' => $entry['parent_kristal_ref'] ?? null,
                'repository_relative_path' => $relpath,
                'repository_id' => 'Kristal-Kollection',
                'storage_mode' => 'external_repository_reference',
                'semantic_authority' => 'Kristal/Kristall',
            ],
        ]);
        if (!$existingartifact) {
            $stats['kristals_created']++;
        }

        $existingversion = $DB->get_record(kristal_artifact_catalog::TABLE_VERSION, [
            'artifactid' => (int)$artifact->id,
            'sha256' => $sha256,
        ]);
        if ($existingversion) {
            if ($externalizeexisting && !$dryrun) {
                uckk_bootstrap_externalize_existing(
                    $artifact,
                    $existingversion,
                    $relpath,
                    $sha256,
                    (string)($entry['repository_url'] ?? 'https://github.com/Rejean-McCormick/Kristal-Kollection'),
                    $context,
                    (int)$admin->id
                );
            }
            $stats['kristals_skipped']++;
            continue;
        }

        $mediarecord = null;
        if (!empty($artifact->mediaid)) {
            $mediarecord = media::get_record((int)$artifact->mediaid, IGNORE_MISSING);
        }
        if (!$mediarecord) {
            $mediarecord = media::create([
                'uuid' => (string)($entry['media_uuid'] ?? ''),
                'libraryid' => (int)$library->id,
                'archiveid' => (int)$archive->id,
                'courseid' => (int)$archive->course,
                'cmid' => (int)$cm->id,
                'contextid' => (int)$context->id,
                'title' => (string)($entry['title'] ?? $ref),
                'description' => 'External reference to the canonical UCKK Kristal in Kristal-Kollection. Semantic identity remains owned by Kristal/Kristall.',
                'mediatype' => media::TYPE_EXTERNAL_REFERENCE,
                'mimetype' => 'application/json',
                'source' => 'kristal',
                'sourcetype' => 'kristal_kollection',
                'sourceurl' => (string)($entry['repository_url'] ?? 'https://github.com/Rejean-McCormick/Kristal-Kollection'),
                'status' => media::STATUS_ACTIVE,
                'visibility' => media::VISIBILITY_INSTITUTION,
                'audiencesuitability' => media::SUITABILITY_GUIDED,
                'provenance' => 'external_reference_only',
                'provenancehash' => $sha256,
                'metadata' => [
                    'kristal_ref' => $ref,
                    'kind' => $entry['kind'] ?? null,
                    'parent_kristal_ref' => $entry['parent_kristal_ref'] ?? null,
                    'portable_contract' => $entry['portable_contract'] ?? null,
                    'kristall_baseline' => $entry['kristall_baseline'] ?? null,
                    'storage_mode' => 'external_repository_reference',
                    'repository_id' => $entry['repository_id'] ?? 'Kristal-Kollection',
                    'repository_relative_path' => $relpath,
                ],
            ], (int)$admin->id);
        }

        $mediaversion = uckk_bootstrap_add_external_kristal_version(
            $mediarecord,
            $relpath,
            $sha256,
            (int)($entry['bytes'] ?? 0),
            (string)($entry['repository_url'] ?? 'https://github.com/Rejean-McCormick/Kristal-Kollection'),
            (int)$admin->id
        );
        kristal_artifact_catalog::upsert_artifact([
            'libraryid' => (int)$library->id,
            'kristalref' => $ref,
            'kind' => (string)($entry['kind'] ?? 'generic'),
            'title' => (string)($entry['title'] ?? $ref),
            'voiecode' => $entry['voie_code'] ?? null,
            'coursecode' => $entry['course_code'] ?? null,
            'status' => (string)($entry['status'] ?? 'stub'),
            'mediaid' => (int)$mediarecord->id,
            'sortorder' => (int)($entry['sortorder'] ?? 0),
            'metadata' => [
                'parent_kristal_ref' => $entry['parent_kristal_ref'] ?? null,
                'repository_relative_path' => $relpath,
                'repository_id' => 'Kristal-Kollection',
                'storage_mode' => 'external_repository_reference',
                'semantic_authority' => 'Kristal/Kristall',
            ],
        ]);
        kristal_artifact_catalog::record_version((int)$artifact->id, [
            'mediaid' => (int)$mediarecord->id,
            'mediaversionid' => (int)$mediaversion->id,
            'versionlabel' => 'bootstrap-stub',
            'sha256' => $sha256,
            'status' => (string)($entry['status'] ?? 'stub'),
            'portablecontract' => (string)($entry['portable_contract'] ?? kristal_artifact_catalog::PORTABLE_CONTRACT),
            'kristallbaseline' => (string)($entry['kristall_baseline'] ?? kristal_artifact_catalog::KRISTALL_BASELINE),
            'metadata' => [
                'repository_id' => 'Kristal-Kollection',
                'repository_url' => (string)($entry['repository_url'] ?? 'https://github.com/Rejean-McCormick/Kristal-Kollection'),
                'repository_relative_path' => $relpath,
                'storage_mode' => 'external_repository_reference',
            ],
        ]);
        $stats['kristal_versions_created']++;
    }

    // Second pass: resolve hierarchy only after all stable identities exist.
    if (!$dryrun) {
        foreach ($entries as $entry) {
            $artifact = kristal_artifact_catalog::get_by_ref(
                (int)$library->id,
                (string)$entry['kristal_ref'],
                MUST_EXIST
            );
            kristal_artifact_catalog::set_parent_ref(
                (int)$artifact->id,
                isset($entry['parent_kristal_ref']) ? (string)$entry['parent_kristal_ref'] : null
            );
        }
    }
}

if ($mode === 'all' || $mode === 'korpus') {
    if ($korpusroot === '' || !is_dir($korpusroot . DIRECTORY_SEPARATOR . 'Sorted')) {
        cli_error('--korpus must point to an extracted Korpus directory containing Sorted/.');
    }
    $items = $plan['korpus'] ?? [];
    if (!is_array($items) || count($items) !== 64) {
        cli_error('Bootstrap must contain exactly 64 Korpus media records.');
    }

    foreach ($items as $item) {
        $sourcepath = $korpusroot . DIRECTORY_SEPARATOR . str_replace('/', DIRECTORY_SEPARATOR,
            (string)($item['source_relative_path'] ?? ''));
        if (!is_readable($sourcepath)) {
            cli_error('Missing Korpus source file: ' . $sourcepath);
        }
        $sha256 = uckk_bootstrap_sha256($sourcepath);
        if (!empty($item['sha256']) && $sha256 !== (string)$item['sha256']) {
            cli_error('Korpus hash mismatch: ' . $sourcepath);
        }

        $existing = media::get_record_by_uuid((string)$item['media_uuid'], IGNORE_MISSING);
        if ($dryrun) {
            cli_writeln('[DRY] Korpus ' . (string)$item['filename']);
            continue;
        }
        if ($existing) {
            $stats['korpus_skipped']++;
            continue;
        }

        $mediarecord = media::create([
            'uuid' => (string)$item['media_uuid'],
            'libraryid' => (int)$library->id,
            'archiveid' => (int)$archive->id,
            'courseid' => (int)$archive->course,
            'cmid' => (int)$cm->id,
            'contextid' => (int)$context->id,
            'title' => (string)$item['title'],
            'description' => (string)($item['description'] ?? ''),
            'mediatype' => (string)($item['mediatype'] ?? media::TYPE_DOCUMENT),
            'mimetype' => (string)($item['mimetype'] ?? 'application/octet-stream'),
            'source' => 'uckk',
            'sourcetype' => (string)(($item['source'] ?? [])['sourcetype'] ?? 'imported'),
            'status' => (string)($item['status'] ?? media::STATUS_ACTIVE),
            'visibility' => (string)($item['visibility'] ?? media::VISIBILITY_INSTITUTION),
            'audiencesuitability' => (string)($item['audiencesuitability'] ?? media::SUITABILITY_GENERAL),
            'provenance' => 'external_reference_only',
            'provenancehash' => $sha256,
            'metadata' => [
                'language' => $item['language'] ?? null,
                'retentionclass' => $item['retentionclass'] ?? null,
                'redactionstate' => $item['redactionstate'] ?? null,
                'original_filename' => $item['original_filename'] ?? null,
                'sha256' => $sha256,
            ],
        ], (int)$admin->id);

        uckk_bootstrap_add_file_version(
            $mediarecord,
            $sourcepath,
            'korpus-bootstrap',
            $sha256,
            $context,
            (int)$admin->id,
            media_version::STATUS_ACTIVE
        );

        $source = is_array($item['source'] ?? null) ? $item['source'] : [];
        try {
            media_source::create([
                'mediaid' => (int)$mediarecord->id,
                'archiveid' => (int)$archive->id,
                'contextid' => (int)$context->id,
                'sourcetype' => (string)($source['sourcetype'] ?? media_source::SOURCE_IMPORTED),
                'ownership' => (string)($source['sourceownership'] ?? media_source::OWNERSHIP_UNKNOWN_SOURCE),
                'creator' => (string)($source['attribution'] ?? ''),
                'title' => (string)$item['title'],
                'metadata' => ['bootstrap' => 'Korpus'],
            ]);
        } catch (Throwable $e) {
            cli_writeln('WARN source metadata for ' . $item['filename'] . ': ' . $e->getMessage());
        }

        foreach (($item['tags'] ?? []) as $tag) {
            media_tag::add_or_update((int)$mediarecord->id, (string)$tag, [
                'source' => media_tag::SOURCE_SYSTEM,
                'metadata' => ['bootstrap' => 'Korpus'],
            ]);
            $stats['tags_created_or_updated']++;
        }

        foreach (($item['content_advisories'] ?? []) as $advisory) {
            if (!is_array($advisory) || empty($advisory['tagkey'])) {
                continue;
            }
            content_marker::create([
                'archiveid' => (int)$archive->id,
                'courseid' => (int)$archive->course,
                'cmid' => (int)$cm->id,
                'contextid' => (int)$context->id,
                'targettype' => content_marker::TARGET_MEDIA,
                'targetid' => (int)$mediarecord->id,
                'targetuuid' => (string)$mediarecord->uuid,
                'tagkey' => (string)$advisory['tagkey'],
                'locatortype' => content_marker::LOCATOR_MANUAL_REFERENCE,
                'locatorvalue' => 'whole_media',
                'severity' => (string)($advisory['severity'] ?? content_marker::SEVERITY_NOTICE),
                'visibility' => (string)$mediarecord->visibility,
                'audiencesuitability' => (string)$mediarecord->audiencesuitability,
                'reviewstate' => content_marker::REVIEW_DRAFT,
                'note' => (string)($advisory['advisorytext'] ?? ''),
                'metadata' => ['bootstrap' => 'Korpus'],
            ], (int)$admin->id);
            $stats['advisories_created']++;
        }

        $stats['korpus_created']++;
    }
}


if ($mode === 'all' || $mode === 'repositories') {
    $repositories = $plan['repositories'] ?? [];
    if (!is_array($repositories) || count($repositories) < 1) {
        cli_error('Bootstrap does not contain a GitHub repository catalog.');
    }

    $collectiontitle = 'Référentiels GitHub — écosystème kOA';
    $collection = $DB->get_record('uckkarchive_media_collection', [
        'libraryid' => (int)$library->id,
        'archiveid' => (int)$archive->id,
        'title' => $collectiontitle,
    ], '*', IGNORE_MISSING);

    if (!$collection && !$dryrun) {
        $collection = media_collection::create([
            'libraryid' => (int)$library->id,
            'archiveid' => (int)$archive->id,
            'courseid' => (int)$archive->course,
            'cmid' => (int)$cm->id,
            'contextid' => (int)$context->id,
            'title' => $collectiontitle,
            'description' => 'Dépôts GitHub publics référencés par le Kristal kOA Ecosystem. Références externes seulement; aucun transfert de propriété.',
            'visibility' => media_collection::VISIBILITY_COURSE,
            'status' => media_collection::STATUS_ACTIVE,
            'metadata' => [
                'catalog' => 'koa.mediatheque.github-repository-catalog/1.0.0',
                'provider' => 'github',
                'authority' => 'external_reference_only',
            ],
        ], (int)$admin->id);
    }

    foreach ($repositories as $repo) {
        $url = trim((string)($repo['github_url'] ?? ''));
        $name = trim((string)($repo['repository_name'] ?? ''));
        $uuid = trim((string)($repo['media_uuid'] ?? ''));
        if ($name === '' || $uuid === '' || !preg_match('#^https://github\.com/[^/]+/[^/]+/?$#', $url)) {
            cli_error('Invalid GitHub repository entry in bootstrap catalog.');
        }

        if ($dryrun) {
            cli_writeln('[DRY] GitHub ' . $name . ' -> ' . $url);
            continue;
        }

        $existing = media::get_record_by_uuid($uuid, IGNORE_MISSING);
        $metadata = [
            'resource_kind' => 'github_repository',
            'github_slug' => $repo['github_slug'] ?? null,
            'boundary' => $repo['boundary'] ?? null,
            'role' => $repo['role'] ?? null,
            'local_observation' => $repo['local_observation'] ?? null,
            'source_registry_id' => $repo['source_registry_id'] ?? null,
            'pinned_commit' => $repo['pinned_commit'] ?? null,
            'pinned_commit_url' => $repo['pinned_commit_url'] ?? null,
            'observed_at' => $repo['observed_at'] ?? null,
            'authority_note' => $repo['authority_note'] ?? null,
            'catalog_source' => 'Kristal-kOA-Ecosystem-v0.6.3',
        ];
        $descriptionparts = [];
        if (!empty($repo['role'])) {
            $descriptionparts[] = 'Rôle: ' . (string)$repo['role'];
        }
        if (!empty($repo['boundary'])) {
            $descriptionparts[] = 'Boundary: ' . (string)$repo['boundary'];
        }
        if (!empty($repo['authority_note'])) {
            $descriptionparts[] = (string)$repo['authority_note'];
        }
        $description = implode(' · ', $descriptionparts);

        if ($existing) {
            $mediarecord = media::update((int)$existing->id, [
                'title' => $name,
                'description' => $description,
                'mediatype' => media::TYPE_EXTERNAL_REFERENCE,
                'mimetype' => 'text/uri-list',
                'source' => 'github',
                'sourcetype' => media_source::SOURCE_EXTERNAL_REFERENCE_ONLY,
                'sourceurl' => $url,
                'status' => media::STATUS_ACTIVE,
                'visibility' => media::VISIBILITY_PUBLIC,
                'audiencesuitability' => media::SUITABILITY_GENERAL,
                'provenance' => 'external_reference',
                'metadata' => $metadata,
            ], (int)$admin->id);
            $stats['repositories_updated']++;
        } else {
            $mediarecord = media::create([
                'uuid' => $uuid,
                'libraryid' => (int)$library->id,
                'archiveid' => (int)$archive->id,
                'courseid' => (int)$archive->course,
                'cmid' => (int)$cm->id,
                'contextid' => (int)$context->id,
                'title' => $name,
                'description' => $description,
                'mediatype' => media::TYPE_EXTERNAL_REFERENCE,
                'mimetype' => 'text/uri-list',
                'source' => 'github',
                'sourcetype' => media_source::SOURCE_EXTERNAL_REFERENCE_ONLY,
                'sourceurl' => $url,
                'status' => media::STATUS_ACTIVE,
                'visibility' => media::VISIBILITY_PUBLIC,
                'audiencesuitability' => media::SUITABILITY_GENERAL,
                'provenance' => 'external_reference',
                'metadata' => $metadata,
            ], (int)$admin->id);
            $stats['repositories_created']++;
        }

        if (!$DB->record_exists('uckkarchive_media_source', ['mediaid' => (int)$mediarecord->id, 'sourceurl' => $url])) {
            media_source::create([
                'uuid' => (string)($repo['source_uuid'] ?? ''),
                'mediaid' => (int)$mediarecord->id,
                'archiveid' => (int)$archive->id,
                'contextid' => (int)$context->id,
                'sourcetype' => media_source::SOURCE_EXTERNAL_REFERENCE_ONLY,
                'ownership' => media_source::OWNERSHIP_EXTERNAL_REFERENCE,
                'creator' => (string)($repo['github_slug'] ?? ''),
                'title' => $name,
                'sourceurl' => $url,
                'citation' => $name . ' — ' . $url . (!empty($repo['pinned_commit_url']) ? ' — commit ' . (string)$repo['pinned_commit_url'] : ''),
                'rightsstatus' => 'external_reference',
                'metadata' => $metadata,
            ]);
            $stats['repository_sources_created']++;
        }

        foreach (($repo['tags'] ?? []) as $tag) {
            media_tag::add_or_update((int)$mediarecord->id, (string)$tag, [
                'source' => media_tag::SOURCE_SYSTEM,
                'metadata' => ['bootstrap' => 'GitHub repository catalog'],
            ]);
            $stats['tags_created_or_updated']++;
        }

        if ($collection) {
            media_collection::add_media(
                (int)$collection->id,
                (int)$mediarecord->id,
                (int)$admin->id,
                (int)($repo['sortorder'] ?? 0),
                ['provider' => 'github', 'github_url' => $url]
            );
            $stats['repository_collection_memberships']++;
        }
    }
}

cli_writeln(json_encode($stats, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES));
exit(0);
