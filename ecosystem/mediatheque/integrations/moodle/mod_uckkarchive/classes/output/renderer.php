<?php
// This file is part of Moodle - https://moodle.org/
//
// Moodle is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// any later version.

/**
 * Output renderer for mod_uckkarchive.
 *
 * @package    mod_uckkarchive
 * @copyright  2026 Univers-Cité King Klown
 * @license    https://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later
 */

declare(strict_types=1);

namespace mod_uckkarchive\output;

defined('MOODLE_INTERNAL') || die();

use plugin_renderer_base;
use renderable;
use stdClass;
use templatable;

/**
 * Renderer for UCKK Archive output objects.
 *
 * This renderer is intentionally presentation-only. It must not validate
 * archive items, revise archive records, expose restricted integrity data,
 * build export packages, calculate provenance, update media, review content
 * advisories, create external work references, or perform workflow actions.
 *
 * Archive business rules belong in mod_uckkarchive service/local classes.
 */
final class renderer extends plugin_renderer_base {
    /**
     * Render the main archive view.
     *
     * @param archive_view $page Archive view renderable.
     * @return string HTML.
     */
    public function render_archive_view(archive_view $page): string {
        return $this->render_templatable($page, 'mod_uckkarchive/archive_view');
    }

    /**
     * Render one archive item card.
     *
     * @param archive_item_card $card Archive item card renderable.
     * @return string HTML.
     */
    public function render_archive_item_card(archive_item_card $card): string {
        return $this->render_templatable($card, 'mod_uckkarchive/archive_item_card');
    }

    /**
     * Render one Kristal card.
     *
     * @param kristal_card $card Kristal card renderable.
     * @return string HTML.
     */
    public function render_kristal_card(kristal_card $card): string {
        return $this->render_templatable($card, 'mod_uckkarchive/kristal_card');
    }

    /**
     * Render a provenance panel.
     *
     * @param provenance_panel $panel Provenance panel renderable.
     * @return string HTML.
     */
    public function render_provenance_panel(provenance_panel $panel): string {
        return $this->render_templatable($panel, 'mod_uckkarchive/provenance_panel');
    }

    /**
     * Render the media library.
     *
     * @param media_library $library Media library renderable.
     * @return string HTML.
     */
    public function render_media_library(media_library $library): string {
        return $this->render_templatable($library, 'mod_uckkarchive/media_library');
    }

    /**
     * Render the unified media-library editor.
     *
     * @param media_library_editor $editor Media-library editor renderable.
     * @return string HTML.
     */
    public function render_media_library_editor(media_library_editor $editor): string {
        return $this->render_templatable($editor, 'mod_uckkarchive/media_library_editor');
    }

    /**
     * Render a media detail page.
     *
     * @param media_detail $detail Media detail renderable.
     * @return string HTML.
     */
    public function render_media_detail(media_detail $detail): string {
        return $this->render_templatable($detail, 'mod_uckkarchive/media_detail');
    }

    /**
     * Render one media card.
     *
     * @param media_card $card Media card renderable.
     * @return string HTML.
     */
    public function render_media_card(media_card $card): string {
        return $this->render_templatable($card, 'mod_uckkarchive/media_card');
    }

    /**
     * Render a media collection.
     *
     * @param media_collection $collection Media collection renderable.
     * @return string HTML.
     */
    public function render_media_collection(media_collection $collection): string {
        return $this->render_templatable($collection, 'mod_uckkarchive/media_collection');
    }

    /**
     * Render a media version list.
     *
     * @param media_version_list $list Media version list renderable.
     * @return string HTML.
     */
    public function render_media_version_list(media_version_list $list): string {
        return $this->render_templatable($list, 'mod_uckkarchive/media_version_list');
    }

    /**
     * Render an external work card.
     *
     * @param external_work_card $card External work card renderable.
     * @return string HTML.
     */
    public function render_external_work_card(external_work_card $card): string {
        return $this->render_templatable($card, 'mod_uckkarchive/external_work_card');
    }

    /**
     * Render a content advisory panel.
     *
     * @param content_advisory_panel $panel Content advisory panel renderable.
     * @return string HTML.
     */
    public function render_content_advisory_panel(content_advisory_panel $panel): string {
        return $this->render_templatable($panel, 'mod_uckkarchive/content_advisory_panel');
    }

    /**
     * Render an archive proof card.
     *
     * Kept untyped because the proof card may be prepared either by a dedicated
     * output object or by another output class using a stdClass context.
     *
     * @param templatable|stdClass|array|string $proof Proof card data.
     * @return string HTML.
     */
    public function render_proof_card($proof): string {
        return $this->render_flexible_context($proof, 'mod_uckkarchive/proof_card');
    }

    /**
     * Render a validation panel.
     *
     * Kept untyped because validation panel data may be produced by the
     * validation controller, a validation form wrapper, or a dedicated output
     * object depending on the page.
     *
     * @param templatable|stdClass|array|string $panel Validation panel data.
     * @return string HTML.
     */
    public function render_validation_panel($panel): string {
        return $this->render_flexible_context($panel, 'mod_uckkarchive/validation_panel');
    }

    /**
     * Render an export panel or export summary.
     *
     * This is presentation only. Export package creation remains in services
     * and tasks.
     *
     * @param templatable|stdClass|array|string $panel Export panel data.
     * @return string HTML.
     */
    public function render_export_panel($panel): string {
        return $this->render_flexible_context($panel, 'mod_uckkarchive/export_panel');
    }

    /**
     * Render a media relation list.
     *
     * Kept flexible because relation lists may be prepared by collection pages,
     * media pages, relation services, or controller-level DTOs.
     *
     * @param templatable|stdClass|array|string $relations Relation list context.
     * @return string HTML.
     */
    public function render_media_relation_list($relations): string {
        return $this->render_flexible_context($relations, 'mod_uckkarchive/media_relation_list');
    }

    /**
     * Render a media upload panel/form wrapper.
     *
     * This renderer only displays the prepared upload context. File processing,
     * draft item handling, validation, and File API writes must remain in forms,
     * controllers, and local service classes.
     *
     * @param templatable|stdClass|array|string $upload Upload context.
     * @return string HTML.
     */
    public function render_media_upload($upload): string {
        return $this->render_flexible_context($upload, 'mod_uckkarchive/media_upload');
    }

    /**
     * Render a generic archive status badge.
     *
     * @param stdClass|array|string $badge Badge data.
     * @return string HTML.
     */
    public function render_status_badge($badge): string {
        return $this->render_flexible_context($badge, 'mod_uckkarchive/status_badge');
    }

    /**
     * Render an empty state.
     *
     * @param stdClass|array|string $emptystate Empty-state data.
     * @return string HTML.
     */
    public function render_empty_state($emptystate): string {
        return $this->render_flexible_context($emptystate, 'mod_uckkarchive/empty_state');
    }

    /**
     * Render a notification list.
     *
     * @param stdClass|array|string $notices Notice data.
     * @return string HTML.
     */
    public function render_notice_list($notices): string {
        return $this->render_flexible_context($notices, 'mod_uckkarchive/notice_list');
    }

    /**
     * Render a generic prepared template context.
     *
     * Use this only when a controller already has a permission-filtered context
     * and no dedicated render method exists yet.
     *
     * @param templatable|stdClass|array|string|null $context Template context.
     * @param string $templatename Template name.
     * @return string HTML.
     */
    public function render_prepared_context($context, string $templatename): string {
        return $this->render_flexible_context($context, $templatename);
    }

    /**
     * Render a templatable object using a specific Mustache template.
     *
     * @param templatable $output Output object.
     * @param string $templatename Template name.
     * @return string HTML.
     */
    private function render_templatable(templatable $output, string $templatename): string {
        $data = $output->export_for_template($this);

        return $this->render_from_template($templatename, $data);
    }

    /**
     * Render templatable objects, stdClass data, array data, strings, or null.
     *
     * This helper keeps controllers flexible while preserving the rule that the
     * renderer only renders already-prepared, permission-filtered data.
     *
     * @param templatable|stdClass|array|string|null $context Template context.
     * @param string $templatename Template name.
     * @return string HTML.
     */
    private function render_flexible_context($context, string $templatename): string {
        if ($context instanceof templatable) {
            $context = $context->export_for_template($this);
        }

        if ($context instanceof renderable && $context instanceof templatable) {
            $context = $context->export_for_template($this);
        }

        if (is_array($context)) {
            $context = $this->array_to_object_recursive($context);
        }

        if ($context === null) {
            $context = new stdClass();
        }

        if (!$context instanceof stdClass && !is_array($context)) {
            $context = (object)[
                'content' => (string)$context,
            ];
        }

        return $this->render_from_template($templatename, $context);
    }

    /**
     * Convert arrays recursively into stdClass structures for Mustache.
     *
     * Numeric arrays remain arrays of converted values. Associative arrays
     * become stdClass objects.
     *
     * @param array $value Raw array.
     * @return array|stdClass
     */
    private function array_to_object_recursive(array $value): array|stdClass {
        $islist = array_is_list($value);

        if ($islist) {
            return array_map(function ($item) {
                if (is_array($item)) {
                    return $this->array_to_object_recursive($item);
                }

                return $item;
            }, $value);
        }

        $object = new stdClass();

        foreach ($value as $key => $item) {
            if (is_array($item)) {
                $item = $this->array_to_object_recursive($item);
            }

            $object->{$key} = $item;
        }

        return $object;
    }

    /**
     * Render an archive item action button.
     *
     * This helper is intentionally small and only formats already-authorised
     * actions prepared by output/service classes.
     *
     * @param string $url Action URL.
     * @param string $label Button label.
     * @param string $style Button style: primary, secondary, danger, warning, info, light, dark, link.
     * @param bool $disabled Whether the action is disabled.
     * @param array<string, scalar|null> $attributes Extra attributes.
     * @return string HTML.
     */
    public function action_button(
        string $url,
        string $label,
        string $style = 'secondary',
        bool $disabled = false,
        array $attributes = []
    ): string {
        $style = $this->normalise_button_style($style);

        $attributes = array_merge([
            'class' => 'btn btn-' . $style . ' uckkarchive-action',
        ], $this->clean_attributes($attributes));

        if ($disabled || trim($url) === '') {
            $attributes['aria-disabled'] = 'true';
            $attributes['tabindex'] = '-1';
            $attributes['class'] .= ' disabled';

            return \html_writer::tag('span', s($label), $attributes);
        }

        return \html_writer::link($url, s($label), $attributes);
    }

    /**
     * Render a POST action form for privileged archive actions.
     *
     * This helper only renders the form shell. Controllers and services remain
     * responsible for sesskey validation, capabilities, state transitions,
     * provenance, events, and audit records.
     *
     * @param string $url Form action URL.
     * @param string $action Action key.
     * @param string $label Button label.
     * @param array<string, scalar|null> $hidden Hidden fields.
     * @param string $style Button style.
     * @param bool $requiresreason Whether to include a reason textarea.
     * @param array<string, scalar|null> $attributes Extra form attributes.
     * @return string HTML.
     */
    public function post_action_form(
        string $url,
        string $action,
        string $label,
        array $hidden = [],
        string $style = 'primary',
        bool $requiresreason = false,
        array $attributes = []
    ): string {
        $style = $this->normalise_button_style($style, [
            'primary',
            'secondary',
            'danger',
            'warning',
            'info',
        ]);

        $formattributes = array_merge([
            'method' => 'post',
            'action' => $url,
            'class' => 'uckkarchive-post-action-form',
        ], $this->clean_attributes($attributes));

        if (isset($formattributes['class'])) {
            $formattributes['class'] = trim((string)$formattributes['class'] . ' uckkarchive-post-action-form');
        }

        $html = \html_writer::start_tag('form', $formattributes);

        $html .= \html_writer::empty_tag('input', [
            'type' => 'hidden',
            'name' => 'sesskey',
            'value' => sesskey(),
        ]);

        $html .= \html_writer::empty_tag('input', [
            'type' => 'hidden',
            'name' => 'action',
            'value' => clean_param($action, PARAM_ALPHANUMEXT),
        ]);

        foreach ($hidden as $name => $value) {
            if ($value === null) {
                continue;
            }

            $html .= \html_writer::empty_tag('input', [
                'type' => 'hidden',
                'name' => clean_param((string)$name, PARAM_ALPHANUMEXT),
                'value' => (string)$value,
            ]);
        }

        if ($requiresreason) {
            $fieldid = 'id_uckkarchive_reason_' . uniqid('', false);

            $html .= \html_writer::start_div('form-group');
            $html .= \html_writer::tag('label', get_string('reason', 'uckkarchive'), [
                'for' => $fieldid,
            ]);
            $html .= \html_writer::tag('textarea', '', [
                'id' => $fieldid,
                'name' => 'reason',
                'class' => 'form-control',
                'rows' => 3,
                'maxlength' => 2000,
                'required' => 'required',
            ]);
            $html .= \html_writer::end_div();
        }

        $html .= \html_writer::tag('button', s($label), [
            'type' => 'submit',
            'class' => 'btn btn-' . $style,
        ]);

        $html .= \html_writer::end_tag('form');

        return $html;
    }

    /**
     * Render a small inline action list.
     *
     * @param array<int, array<string, mixed>|stdClass> $actions Prepared actions.
     * @param string $classes Extra wrapper classes.
     * @return string HTML.
     */
    public function action_list(array $actions, string $classes = ''): string {
        if (empty($actions)) {
            return '';
        }

        $html = \html_writer::start_div(trim('uckkarchive-action-list btn-group ' . $classes), [
            'role' => 'group',
        ]);

        foreach ($actions as $action) {
            $action = is_object($action) ? (array)$action : $action;

            $url = (string)($action['url'] ?? '');
            $label = (string)($action['label'] ?? '');
            $style = (string)($action['style'] ?? ($action['primary'] ?? false ? 'primary' : 'secondary'));
            $disabled = !empty($action['disabled']);

            if ($label === '') {
                continue;
            }

            if ($url === '') {
                $html .= \html_writer::tag('button', s($label), [
                    'type' => 'button',
                    'class' => 'btn btn-' . $this->normalise_button_style($style),
                    'disabled' => $disabled ? 'disabled' : null,
                ]);
                continue;
            }

            $html .= $this->action_button($url, $label, $style, $disabled);
        }

        $html .= \html_writer::end_div();

        return $html;
    }

    /**
     * Render a badge.
     *
     * @param string $label Badge label.
     * @param string $style Badge style.
     * @param array<string, scalar|null> $attributes Extra attributes.
     * @return string HTML.
     */
    public function badge(string $label, string $style = 'secondary', array $attributes = []): string {
        $style = $this->normalise_badge_style($style);

        $attributes = array_merge([
            'class' => 'badge badge-' . $style . ' uckkarchive-badge',
        ], $this->clean_attributes($attributes));

        return \html_writer::tag('span', s($label), $attributes);
    }

    /**
     * Normalise Bootstrap button style.
     *
     * @param string $style Requested style.
     * @param string[]|null $allowedstyles Allowed styles.
     * @return string Normalised style.
     */
    private function normalise_button_style(string $style, ?array $allowedstyles = null): string {
        $style = clean_param($style, PARAM_ALPHANUMEXT);

        $allowedstyles ??= [
            'primary',
            'secondary',
            'success',
            'danger',
            'warning',
            'info',
            'light',
            'dark',
            'link',
        ];

        if (!in_array($style, $allowedstyles, true)) {
            return 'secondary';
        }

        return $style;
    }

    /**
     * Normalise Bootstrap badge style.
     *
     * @param string $style Requested style.
     * @return string Normalised style.
     */
    private function normalise_badge_style(string $style): string {
        $style = clean_param($style, PARAM_ALPHANUMEXT);

        $allowedstyles = [
            'primary',
            'secondary',
            'success',
            'danger',
            'warning',
            'info',
            'light',
            'dark',
        ];

        if (!in_array($style, $allowedstyles, true)) {
            return 'secondary';
        }

        return $style;
    }

    /**
     * Clean HTML attributes.
     *
     * @param array<string, scalar|null> $attributes Raw attributes.
     * @return array<string, scalar>
     */
    private function clean_attributes(array $attributes): array {
        $clean = [];

        foreach ($attributes as $name => $value) {
            if ($value === null) {
                continue;
            }

            $name = clean_param((string)$name, PARAM_ALPHANUMEXT);

            if ($name === '') {
                continue;
            }

            $clean[$name] = is_bool($value) ? ($value ? 'true' : 'false') : $value;
        }

        return $clean;
    }
}