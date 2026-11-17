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
 * Renderable media collection model for UCKK Archive.
 *
 * @package    mod_uckkarchive
 * @copyright  2026 UCKK
 * @license    http://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later
 */

declare(strict_types=1);

namespace mod_uckkarchive\output;

defined('MOODLE_INTERNAL') || die();

/**
 * Renderable output model for one media collection.
 *
 * This class prepares safe template data only. It does not decide final access,
 * does not modify the database, and does not serve files. Capability checks here
 * are used only to decide which UI actions should be displayed.
 *
 * Canonical template:
 *
 * ```text
 * mod_uckkarchive/templates/media_collection.mustache
 * ```
 */
final class media_collection implements \renderable, \templatable {
    /** @var \stdClass Media collection record. */
    private \stdClass $collection;

    /** @var \stdClass[] Media records contained by the collection. */
    private array $media;

    /** @var \context|null Rendering context. */
    private ?\context $context;

    /** @var array<string, mixed> Rendering options. */
    private array $options;

    /**
     * Constructor.
     *
     * @param \stdClass $collection Media collection record.
     * @param \stdClass[] $media Media records in collection order.
     * @param \context|null $context Moodle context.
     * @param array<string, mixed> $options Rendering options.
     */
    public function __construct(
        \stdClass $collection,
        array $media = [],
        ?\context $context = null,
        array $options = []
    ) {
        $this->collection = $collection;
        $this->media = array_values($media);
        $this->context = $context;
        $this->options = $options;
    }

    /**
     * Create output model from a collection record.
     *
     * @param \stdClass $collection Media collection record.
     * @param \stdClass[] $media Media records.
     * @param \context|null $context Moodle context.
     * @param array<string, mixed> $options Rendering options.
     * @return self
     */
    public static function from_record(
        \stdClass $collection,
        array $media = [],
        ?\context $context = null,
        array $options = []
    ): self {
        return new self($collection, $media, $context, $options);
    }

    /**
     * Set media records after construction.
     *
     * @param \stdClass[] $media Media records.
     * @return self
     */
    public function set_media(array $media): self {
        $this->media = array_values($media);

        return $this;
    }

    /**
     * Add one media record.
     *
     * @param \stdClass $media Media record.
     * @return self
     */
    public function add_media(\stdClass $media): self {
        $this->media[] = $media;

        return $this;
    }

    /**
     * Export data for Mustache.
     *
     * @param \renderer_base $output Renderer.
     * @return array<string, mixed>
     */
    public function export_for_template(\renderer_base $output): array {
        $collection = $this->export_collection($output);
        $media = $this->export_media_items($output);
        $permissions = $this->permissions();

        return [
            'id' => $collection['id'],
            'uuid' => $collection['uuid'],
            'archiveid' => $collection['archiveid'],
            'courseid' => $collection['courseid'],
            'cmid' => $collection['cmid'],
            'contextid' => $collection['contextid'],
            'title' => $collection['title'],
            'description' => $collection['description'],
            'purpose' => $collection['purpose'],
            'status' => $collection['status'],
            'visibility' => $collection['visibility'],
            'metadata' => $collection['metadata'],
            'createdby' => $collection['createdby'],
            'modifiedby' => $collection['modifiedby'],
            'timecreated' => $collection['timecreated'],
            'timemodified' => $collection['timemodified'],

            'isactive' => $collection['status'] === 'active',
            'isdraft' => $collection['status'] === 'draft',
            'isrestricted' => $this->is_restricted($this->collection),
            'isarchived' => $collection['status'] === 'archived',
            'isdeleted' => $collection['status'] === 'deleted_soft',

            'media' => $media,
            'hasmedia' => !empty($media),
            'itemcount' => count($media),
            'mediacount' => count($media),

            'permissions' => $permissions,
            'canview' => $permissions['canview'],
            'canmanage' => $permissions['canmanage'],
            'canedit' => $permissions['canedit'],
            'canaddmedia' => $permissions['canaddmedia'],
            'canremovemedia' => $permissions['canremovemedia'],
            'canreorder' => $permissions['canreorder'],
            'canexport' => $permissions['canexport'],
            'canviewrestricted' => $permissions['canviewrestricted'],

            'urls' => $this->urls(),
            'viewurl' => $this->view_url(),
            'editurl' => $this->edit_url(),
            'addmediaurl' => $this->add_media_url(),
            'exporturl' => $this->export_url(),

            'sesskey' => sesskey(),
            'uniqid' => $this->uniqid(),
        ];
    }

    /**
     * Export collection record.
     *
     * @param \renderer_base $output Renderer.
     * @return array<string, mixed>
     */
    private function export_collection(\renderer_base $output): array {
        $collection = $this->collection;

        return [
            'id' => (int)($collection->id ?? 0),
            'uuid' => (string)($collection->uuid ?? ''),
            'archiveid' => (int)($collection->archiveid ?? 0),
            'courseid' => (int)($collection->courseid ?? 0),
            'cmid' => (int)($collection->cmid ?? $this->cmid()),
            'contextid' => (int)($collection->contextid ?? ($this->context->id ?? 0)),
            'title' => $this->format_title((string)($collection->title ?? '')),
            'description' => $this->format_text((string)($collection->description ?? ''), $output),
            'purpose' => $this->format_title((string)($collection->purpose ?? '')),
            'status' => (string)($collection->status ?? 'draft'),
            'visibility' => (string)($collection->visibility ?? 'course'),
            'metadata' => $this->encode_json($this->decode_metadata($collection->metadata ?? null)),
            'createdby' => (int)($collection->createdby ?? 0),
            'modifiedby' => (int)($collection->modifiedby ?? 0),
            'timecreated' => (int)($collection->timecreated ?? 0),
            'timemodified' => (int)($collection->timemodified ?? 0),
        ];
    }

    /**
     * Export media records.
     *
     * @param \renderer_base $output Renderer.
     * @return array<int, array<string, mixed>>
     */
    private function export_media_items(\renderer_base $output): array {
        $items = [];

        foreach ($this->media as $index => $record) {
            if (!$this->can_view_media($record)) {
                continue;
            }

            $items[] = $this->export_media_item($record, $index, $output);
        }

        return $items;
    }

    /**
     * Export one media item.
     *
     * @param \stdClass $media Media record.
     * @param int $index Zero-based render index.
     * @param \renderer_base $output Renderer.
     * @return array<string, mixed>
     */
    private function export_media_item(\stdClass $media, int $index, \renderer_base $output): array {
        $mediaid = (int)($media->id ?? 0);
        $sortorder = (int)($media->sortorder ?? $index);
        $restricted = $this->is_restricted($media);
        $cultural = $this->is_culturally_restricted($media);
        $canviewrestricted = $this->has_capability('mod/uckkarchive:viewrestrictedmedia') ||
            $this->has_capability('mod/uckkarchive:viewrestricted') ||
            ($cultural && $this->has_capability('mod/uckkarchive:viewculturallyrestricted'));

        $title = (string)($media->title ?? $media->name ?? '');
        $summary = (string)($media->summary ?? $media->description ?? '');

        if ($restricted && !$canviewrestricted) {
            $summary = '';
        }

        return [
            'id' => $mediaid,
            'uuid' => (string)($media->uuid ?? ''),
            'title' => $this->format_title($title),
            'summary' => $this->format_text($summary, $output),
            'mediatype' => (string)($media->mediatype ?? $media->type ?? ''),
            'mimetype' => (string)($media->mimetype ?? ''),
            'status' => (string)($media->status ?? ''),
            'visibility' => (string)($media->visibility ?? ''),
            'audiencesuitability' => (string)($media->audiencesuitability ?? ''),
            'source' => (string)($media->source ?? $media->sourcetype ?? ''),
            'sortorder' => $sortorder,
            'position' => $index + 1,
            'isrestricted' => $restricted,
            'isculturallyrestricted' => $cultural,
            'iscurrent' => !empty($media->iscurrent),
            'metadata' => $this->encode_json($this->decode_metadata($media->collectionitemmetadata ?? $media->metadata ?? null)),
            'timecreated' => (int)($media->timecreated ?? 0),
            'timemodified' => (int)($media->timemodified ?? 0),
            'viewurl' => $this->media_url($mediaid),
            'removeurl' => $this->remove_media_url($mediaid),
            'canview' => $this->can_view_media($media),
            'canremove' => $this->permissions()['canremovemedia'],
            'canreorder' => $this->permissions()['canreorder'],
        ];
    }

    /**
     * Return permissions for template actions.
     *
     * @return array<string, bool>
     */
    private function permissions(): array {
        $canmanage = $this->has_capability('mod/uckkarchive:managemediacollections');

        return [
            'canview' => $this->has_capability('mod/uckkarchive:viewmedia') ||
                $this->has_capability('mod/uckkarchive:view'),
            'canmanage' => $canmanage,
            'canedit' => $canmanage || $this->has_capability('mod/uckkarchive:editmedia'),
            'canaddmedia' => $canmanage || $this->has_capability('mod/uckkarchive:addmedia'),
            'canremovemedia' => $canmanage || $this->has_capability('mod/uckkarchive:editmedia'),
            'canreorder' => $canmanage || $this->has_capability('mod/uckkarchive:editmedia'),
            'canexport' => $this->has_capability('mod/uckkarchive:exportmedia') ||
                $this->has_capability('mod/uckkarchive:export'),
            'canviewrestricted' => $this->has_capability('mod/uckkarchive:viewrestrictedmedia') ||
                $this->has_capability('mod/uckkarchive:viewrestricted') ||
                $this->has_capability('mod/uckkarchive:viewculturallyrestricted'),
        ];
    }

    /**
     * Return action URLs.
     *
     * @return array<string, string>
     */
    private function urls(): array {
        return [
            'view' => $this->view_url(),
            'edit' => $this->edit_url(),
            'addmedia' => $this->add_media_url(),
            'export' => $this->export_url(),
            'reorder' => $this->reorder_url(),
        ];
    }

    /**
     * Return collection view URL.
     *
     * @return string
     */
    private function view_url(): string {
        return $this->url([
            'id' => $this->cmid(),
            'collectionid' => (int)($this->collection->id ?? 0),
        ]);
    }

    /**
     * Return collection edit URL.
     *
     * @return string
     */
    private function edit_url(): string {
        return $this->url([
            'id' => $this->cmid(),
            'action' => 'editcollection',
            'collectionid' => (int)($this->collection->id ?? 0),
        ]);
    }

    /**
     * Return add media URL.
     *
     * @return string
     */
    private function add_media_url(): string {
        return $this->url([
            'id' => $this->cmid(),
            'action' => 'addmediatocollection',
            'collectionid' => (int)($this->collection->id ?? 0),
        ]);
    }

    /**
     * Return reorder URL.
     *
     * @return string
     */
    private function reorder_url(): string {
        return $this->url([
            'id' => $this->cmid(),
            'action' => 'reordercollection',
            'collectionid' => (int)($this->collection->id ?? 0),
        ]);
    }

    /**
     * Return export URL.
     *
     * @return string
     */
    private function export_url(): string {
        return $this->url([
            'id' => $this->cmid(),
            'action' => 'exportcollection',
            'collectionid' => (int)($this->collection->id ?? 0),
        ]);
    }

    /**
     * Return media item URL.
     *
     * @param int $mediaid Media id.
     * @return string
     */
    private function media_url(int $mediaid): string {
        return $this->url([
            'id' => $this->cmid(),
            'mediaid' => $mediaid,
        ]);
    }

    /**
     * Return remove media URL.
     *
     * @param int $mediaid Media id.
     * @return string
     */
    private function remove_media_url(int $mediaid): string {
        return $this->url([
            'id' => $this->cmid(),
            'action' => 'removemediafromcollection',
            'collectionid' => (int)($this->collection->id ?? 0),
            'mediaid' => $mediaid,
            'sesskey' => sesskey(),
        ]);
    }

    /**
     * Build a media page URL.
     *
     * @param array<string, mixed> $params URL parameters.
     * @return string
     */
    private function url(array $params): string {
        if (empty($params['id'])) {
            unset($params['id']);
        }

        return (new \moodle_url('/mod/uckkarchive/media.php', $params))->out(false);
    }

    /**
     * Return cmid from collection/options/context.
     *
     * @return int
     */
    private function cmid(): int {
        if (!empty($this->collection->cmid)) {
            return (int)$this->collection->cmid;
        }

        if (!empty($this->options['cmid'])) {
            return (int)$this->options['cmid'];
        }

        if ($this->context && $this->context->contextlevel === CONTEXT_MODULE) {
            return (int)$this->context->instanceid;
        }

        return 0;
    }

    /**
     * Return whether current user can view a media record.
     *
     * @param \stdClass $media Media record.
     * @return bool
     */
    private function can_view_media(\stdClass $media): bool {
        if ($this->is_restricted($media)) {
            return $this->has_capability('mod/uckkarchive:viewrestrictedmedia') ||
                $this->has_capability('mod/uckkarchive:viewrestricted') ||
                ($this->is_culturally_restricted($media) &&
                    $this->has_capability('mod/uckkarchive:viewculturallyrestricted'));
        }

        return $this->has_capability('mod/uckkarchive:viewmedia') ||
            $this->has_capability('mod/uckkarchive:view');
    }

    /**
     * Return whether record is restricted.
     *
     * @param \stdClass $record Record.
     * @return bool
     */
    private function is_restricted(\stdClass $record): bool {
        $status = (string)($record->status ?? '');
        $visibility = (string)($record->visibility ?? '');

        return $status === 'restricted' ||
            in_array($visibility, ['restricted', 'restricted_integrity', 'restricted_cultural'], true) ||
            !empty($record->restricted);
    }

    /**
     * Return whether record is culturally restricted.
     *
     * @param \stdClass $record Record.
     * @return bool
     */
    private function is_culturally_restricted(\stdClass $record): bool {
        $visibility = (string)($record->visibility ?? '');

        return $visibility === 'restricted_cultural' || !empty($record->culturalprotocol);
    }

    /**
     * Capability helper.
     *
     * Unknown capabilities are treated as unavailable so the output class can
     * remain usable while access.php is being expanded.
     *
     * @param string $capability Capability name.
     * @return bool
     */
    private function has_capability(string $capability): bool {
        if (!$this->context) {
            return false;
        }

        if (function_exists('get_capability_info') && !get_capability_info($capability)) {
            return false;
        }

        return has_capability($capability, $this->context);
    }

    /**
     * Format title.
     *
     * @param string $title Raw title.
     * @return string
     */
    private function format_title(string $title): string {
        return format_string($title, true, [
            'context' => $this->context,
        ]);
    }

    /**
     * Format rich text.
     *
     * @param string $text Raw text.
     * @param \renderer_base $output Renderer.
     * @return string
     */
    private function format_text(string $text, \renderer_base $output): string {
        if ($text === '') {
            return '';
        }

        return format_text($text, FORMAT_HTML, [
            'context' => $this->context,
            'trusted' => false,
            'noclean' => false,
            'filter' => true,
        ]);
    }

    /**
     * Decode metadata from JSON/object/array.
     *
     * @param mixed $metadata Metadata.
     * @return array<string, mixed>
     */
    private function decode_metadata($metadata): array {
        if (is_array($metadata)) {
            return $metadata;
        }

        if ($metadata instanceof \stdClass) {
            return (array)$metadata;
        }

        if (is_string($metadata) && trim($metadata) !== '') {
            $decoded = json_decode($metadata, true);
            return is_array($decoded) ? $decoded : [];
        }

        return [];
    }

    /**
     * Encode JSON safely.
     *
     * @param mixed $data Data.
     * @return string
     */
    private function encode_json($data): string {
        $json = json_encode($data, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);

        return $json === false ? '{}' : $json;
    }

    /**
     * Return deterministic unique DOM id.
     *
     * @return string
     */
    private function uniqid(): string {
        $id = (int)($this->collection->id ?? 0);

        return 'uckkarchive-media-collection-' . $id;
    }
}

