<?php
// This file is part of Moodle - https://moodle.org/.
//
// Moodle is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// any later version.

/**
 * Administration page for autonomous media libraries and bridges.
 *
 * @package    mod_uckkarchive
 * @copyright  2026 Univers-Cité King Klown
 * @license    https://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later
 */

declare(strict_types=1);

require_once(__DIR__ . '/../../config.php');

use mod_uckkarchive\local\media_library_scope;

require_login();

$context = context_system::instance();
require_capability('mod/uckkarchive:managelibraries', $context);

$url = new moodle_url('/mod/uckkarchive/library_admin.php');
$PAGE->set_context($context);
$PAGE->set_url($url);
$PAGE->set_pagelayout('admin');
$PAGE->set_title(get_string('libraryadmin', 'mod_uckkarchive'));
$PAGE->set_heading(get_string('libraryadmin', 'mod_uckkarchive'));

$scope = new media_library_scope();
if (!media_library_scope::schema_ready()) {
    throw new moodle_exception('libraryschemamissing', 'mod_uckkarchive');
}

$action = optional_param('action', '', PARAM_ALPHANUMEXT);

if ($action !== '' && data_submitted()) {
    require_sesskey();

    try {
        switch ($action) {
            case 'create_library':
                $scope->create_library(
                    required_param('slug', PARAM_ALPHANUMEXT),
                    required_param('name', PARAM_TEXT),
                    optional_param('description', '', PARAM_TEXT)
                );
                break;

            case 'attach_site':
                $scope->attach_library_to_site(
                    required_param('libraryslug', PARAM_ALPHANUMEXT),
                    required_param('sitekey', PARAM_ALPHANUMEXT),
                    optional_param('role', media_library_scope::SITE_ROLE_PRIMARY, PARAM_ALPHANUMEXT),
                    optional_param('sortorder', 0, PARAM_INT)
                );
                break;

            case 'assign_media':
                $scope->assign_media_uuid_to_library(
                    required_param('mediauuid', PARAM_TEXT),
                    required_param('libraryslug', PARAM_ALPHANUMEXT)
                );
                break;

            case 'assign_collection':
                $scope->assign_collection_uuid_to_library(
                    required_param('collectionuuid', PARAM_TEXT),
                    required_param('libraryslug', PARAM_ALPHANUMEXT)
                );
                break;

            case 'create_bridge':
                $scopetype = required_param('scopetype', PARAM_ALPHANUMEXT);
                $scopeuuid = optional_param('scopeuuid', '', PARAM_TEXT);
                $scopeid = $scopetype === media_library_scope::SCOPE_LIBRARY
                    ? 0
                    : $scope->resolve_scope_uuid($scopetype, $scopeuuid);

                $scope->create_bridge(
                    required_param('sourcelibraryslug', PARAM_ALPHANUMEXT),
                    required_param('targetlibraryslug', PARAM_ALPHANUMEXT),
                    $scopetype,
                    $scopeid,
                    optional_param('label', '', PARAM_TEXT)
                );
                break;

            case 'deactivate_bridge':
                $scope->deactivate_bridge(required_param('bridgeid', PARAM_INT));
                break;

            default:
                throw new coding_exception('Invalid media-library administration action.');
        }
    } catch (Throwable $exception) {
        redirect($url, $exception->getMessage(), null, \core\output\notification::NOTIFY_ERROR);
    }

    redirect($url, get_string('changessaved'), null, \core\output\notification::NOTIFY_SUCCESS);
}

$libraries = $scope->get_all_libraries();
$sitemappings = $scope->get_all_site_mappings();
$bridges = $scope->get_all_bridges();

$formopen = static function(string $action) use ($url): string {
    return html_writer::start_tag('form', [
        'method' => 'post',
        'action' => $url->out(false),
        'class' => 'mb-4 border rounded p-3',
    ]) .
        html_writer::empty_tag('input', ['type' => 'hidden', 'name' => 'sesskey', 'value' => sesskey()]) .
        html_writer::empty_tag('input', ['type' => 'hidden', 'name' => 'action', 'value' => $action]);
};

$input = static function(string $name, string $label, string $type = 'text', string $value = ''): string {
    return html_writer::div(
        html_writer::tag('label', s($label), ['for' => 'field-' . $name, 'class' => 'form-label']) .
        html_writer::empty_tag('input', [
            'id' => 'field-' . $name,
            'name' => $name,
            'type' => $type,
            'value' => $value,
            'class' => 'form-control',
        ]),
        'mb-3'
    );
};

$select = static function(string $name, string $label, array $options): string {
    return html_writer::div(
        html_writer::tag('label', s($label), ['for' => 'field-' . $name, 'class' => 'form-label']) .
        html_writer::select($options, $name, '', false, ['id' => 'field-' . $name, 'class' => 'form-select']),
        'mb-3'
    );
};

$libraryoptions = [];
foreach ($libraries as $library) {
    if ((string)$library->status === media_library_scope::STATUS_ACTIVE) {
        $libraryoptions[(string)$library->slug] = (string)$library->name . ' (' . (string)$library->slug . ')';
    }
}

echo $OUTPUT->header();
echo $OUTPUT->heading(get_string('libraryadmin', 'mod_uckkarchive'));
echo html_writer::tag('p', get_string('libraryadminintro', 'mod_uckkarchive'), ['class' => 'lead']);

// Existing libraries.
$table = new html_table();
$table->head = [get_string('libraryslug', 'mod_uckkarchive'), get_string('name'), get_string('status')];
foreach ($libraries as $library) {
    $table->data[] = [s((string)$library->slug), format_string((string)$library->name), s((string)$library->status)];
}
echo $OUTPUT->heading(get_string('libraries', 'mod_uckkarchive'), 3);
echo html_writer::table($table);

// Current site/library mappings.
echo $OUTPUT->heading(get_string('librarysitemappings', 'mod_uckkarchive'), 3);
$mappingtable = new html_table();
$mappingtable->head = [
    get_string('sitekey', 'mod_uckkarchive'),
    get_string('libraries', 'mod_uckkarchive'),
    get_string('libraryrole', 'mod_uckkarchive'),
    get_string('status'),
];
foreach ($sitemappings as $mapping) {
    $mappingtable->data[] = [
        s((string)$mapping->sitekey),
        format_string((string)$mapping->libraryname) . ' (' . s((string)$mapping->libraryslug) . ')',
        s((string)$mapping->role),
        s((string)$mapping->status),
    ];
}
echo html_writer::table($mappingtable);

// Create library.
echo $OUTPUT->heading(get_string('createlibrary', 'mod_uckkarchive'), 4);
echo $formopen('create_library');
echo $input('slug', get_string('libraryslug', 'mod_uckkarchive'));
echo $input('name', get_string('name'));
echo $input('description', get_string('description'));
echo html_writer::tag('button', get_string('create'), ['type' => 'submit', 'class' => 'btn btn-primary']);
echo html_writer::end_tag('form');

// Attach/share exact same library with a site.
echo $OUTPUT->heading(get_string('attachlibrarysite', 'mod_uckkarchive'), 4);
echo $formopen('attach_site');
echo $select('libraryslug', get_string('libraries', 'mod_uckkarchive'), $libraryoptions);
echo $input('sitekey', get_string('sitekey', 'mod_uckkarchive'));
// Public search resolves one primary library per site. Older primary mappings
// are retained automatically as secondary/shared audit mappings.
echo html_writer::empty_tag('input', [
    'type' => 'hidden',
    'name' => 'role',
    'value' => media_library_scope::SITE_ROLE_PRIMARY,
]);
echo $input('sortorder', get_string('sortorder'), 'number', '0');
echo html_writer::tag('button', get_string('savechanges'), ['type' => 'submit', 'class' => 'btn btn-primary']);
echo html_writer::end_tag('form');

// Reassign media.
echo $OUTPUT->heading(get_string('assignmedialibrary', 'mod_uckkarchive'), 4);
echo $formopen('assign_media');
echo $input('mediauuid', get_string('mediauuid', 'mod_uckkarchive'));
echo $select('libraryslug', get_string('libraries', 'mod_uckkarchive'), $libraryoptions);
echo html_writer::tag('button', get_string('savechanges'), ['type' => 'submit', 'class' => 'btn btn-primary']);
echo html_writer::end_tag('form');

// Reassign collection.
echo $OUTPUT->heading(get_string('assigncollectionlibrary', 'mod_uckkarchive'), 4);
echo $formopen('assign_collection');
echo $input('collectionuuid', get_string('collectionuuid', 'mod_uckkarchive'));
echo $select('libraryslug', get_string('libraries', 'mod_uckkarchive'), $libraryoptions);
echo html_writer::tag('button', get_string('savechanges'), ['type' => 'submit', 'class' => 'btn btn-primary']);
echo html_writer::end_tag('form');

// Bridges.
echo $OUTPUT->heading(get_string('librarybridges', 'mod_uckkarchive'), 3);
$bridgetable = new html_table();
$bridgetable->head = [
    get_string('bridgesource', 'mod_uckkarchive'),
    get_string('bridgetarget', 'mod_uckkarchive'),
    get_string('scope', 'mod_uckkarchive'),
    get_string('bridgelabel', 'mod_uckkarchive'),
    get_string('status'),
    get_string('actions'),
];
foreach ($bridges as $bridge) {
    $deactivate = '';
    if ((string)$bridge->status === media_library_scope::STATUS_ACTIVE) {
        $deactivate = html_writer::start_tag('form', [
            'method' => 'post',
            'action' => $url->out(false),
            'class' => 'd-inline',
        ]) .
            html_writer::empty_tag('input', ['type' => 'hidden', 'name' => 'sesskey', 'value' => sesskey()]) .
            html_writer::empty_tag('input', ['type' => 'hidden', 'name' => 'action', 'value' => 'deactivate_bridge']) .
            html_writer::empty_tag('input', ['type' => 'hidden', 'name' => 'bridgeid', 'value' => (int)$bridge->id]) .
            html_writer::tag('button', get_string('disable'), ['type' => 'submit', 'class' => 'btn btn-link p-0']) .
            html_writer::end_tag('form');
    }
    $scopevalue = (string)$bridge->scopetype;
    if ((int)$bridge->scopeid > 0) {
        $scopevalue .= ' #' . (int)$bridge->scopeid;
    }
    $bridgetable->data[] = [
        format_string((string)$bridge->sourcename),
        format_string((string)$bridge->targetname),
        s($scopevalue),
        format_string((string)$bridge->label),
        s((string)$bridge->status),
        $deactivate,
    ];
}
echo html_writer::table($bridgetable);

echo $OUTPUT->heading(get_string('createbridge', 'mod_uckkarchive'), 4);
echo $formopen('create_bridge');
echo $select('sourcelibraryslug', get_string('sourcelibrary', 'mod_uckkarchive'), $libraryoptions);
echo $select('targetlibraryslug', get_string('targetlibrary', 'mod_uckkarchive'), $libraryoptions);
echo $select('scopetype', get_string('scope', 'mod_uckkarchive'), [
    media_library_scope::SCOPE_LIBRARY => get_string('wholelibrary', 'mod_uckkarchive'),
    media_library_scope::SCOPE_COLLECTION => get_string('collection', 'mod_uckkarchive'),
    media_library_scope::SCOPE_MEDIA => get_string('media', 'mod_uckkarchive'),
]);
echo $input('scopeuuid', get_string('scopeuuid', 'mod_uckkarchive'));
echo $input('label', get_string('bridgelabel', 'mod_uckkarchive'));
echo html_writer::tag('button', get_string('createbridge', 'mod_uckkarchive'), ['type' => 'submit', 'class' => 'btn btn-primary']);
echo html_writer::end_tag('form');

echo $OUTPUT->footer();
