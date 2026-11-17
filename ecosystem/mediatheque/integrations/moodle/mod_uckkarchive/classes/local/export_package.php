<?php
// This file is part of Moodle - https://moodle.org/
//
// Moodle is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// any later version.

/**
 * Local domain model for one UCKK archive export package.
 *
 * @package    mod_uckkarchive
 * @copyright  2026 Univers-Cité King Klown
 * @license    https://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later
 */

declare(strict_types=1);

namespace mod_uckkarchive\local;

use stdClass;

defined('MOODLE_INTERNAL') || die();

/**
 * Domain object for an archive export package.
 *
 * This class normalises and validates export package data before service or
 * database layers insert, update, generate files, redact restricted data, or
 * expose download links.
 *
 * It does not generate files, decide permissions, redact content, validate
 * evidence, publish archive items, or write to the database directly.
 */
final class export_package {
    /** Export format: JSON. */
    public const FORMAT_JSON = 'json';

    /** Export format: CSV. */
    public const FORMAT_CSV = 'csv';

    /** Export format: ZIP. */
    public const FORMAT_ZIP = 'zip';

    /** Export format: HTML. */
    public const FORMAT_HTML = 'html';

    /** Export format: PDF. */
    public const FORMAT_PDF = 'pdf';

    /** Export format: Moodle backup-like package. */
    public const FORMAT_MOODLE = 'moodle';

    /** Export scope: selected items only. */
    public const SCOPE_SELECTED = 'selected';

    /** Export scope: validated items only. */
    public const SCOPE_VALIDATED_ONLY = 'validated_only';

    /** Export scope: public items only. */
    public const SCOPE_PUBLIC_ONLY = 'public_only';

    /** Export scope: full archive. */
    public const SCOPE_FULL_ARCHIVE = 'full_archive';

    /** Export scope: full archive with revisions. */
    public const SCOPE_FULL_WITH_REVISIONS = 'full_with_revisions';

    /** Export scope: restricted redacted package. */
    public const SCOPE_RESTRICTED_REDACTED = 'restricted_redacted';

    /** Status: draft. */
    public const STATUS_DRAFT = 'draft';

    /** Status: pending. */
    public const STATUS_PENDING = 'pending';

    /** Status: processing. */
    public const STATUS_PROCESSING = 'processing';

    /** Status: completed. */
    public const STATUS_COMPLETED = 'completed';

    /** Status: failed. */
    public const STATUS_FAILED = 'failed';

    /** Status: cancelled. */
    public const STATUS_CANCELLED = 'cancelled';

    /** Status: archived. */
    public const STATUS_ARCHIVED = 'archived';

    /** Visibility: private. */
    public const VISIBILITY_PRIVATE = 'private';

    /** Visibility: user. */
    public const VISIBILITY_USER = 'user';

    /** Visibility: group. */
    public const VISIBILITY_GROUP = 'group';

    /** Visibility: course. */
    public const VISIBILITY_COURSE = 'course';

    /** Visibility: cohort. */
    public const VISIBILITY_COHORT = 'cohort';

    /** Visibility: program. */
    public const VISIBILITY_PROGRAM = 'program';

    /** Visibility: institution. */
    public const VISIBILITY_INSTITUTION = 'institution';

    /** Visibility: public. */
    public const VISIBILITY_PUBLIC = 'public';

    /** Visibility: restricted. */
    public const VISIBILITY_RESTRICTED = 'restricted';

    /** Visibility: restricted integrity. */
    public const VISIBILITY_RESTRICTED_INTEGRITY = 'restricted_integrity';

    /** Visibility: archived. */
    public const VISIBILITY_ARCHIVED = 'archived';

    /** Provenance: human. */
    public const PROVENANCE_HUMAN = 'human';

    /** Provenance: system. */
    public const PROVENANCE_SYSTEM = 'system';

    /** Provenance: archive. */
    public const PROVENANCE_ARCHIVE = 'archive';

    /** Provenance: integrity. */
    public const PROVENANCE_INTEGRITY = 'integrity';

    /** Provenance: imported. */
    public const PROVENANCE_IMPORTED = 'imported';

    /** Database id. */
    private int $id = 0;

    /** Parent archive activity instance id. */
    private int $archiveid = 0;

    /** Moodle course id. */
    private int $courseid = 0;

    /** Moodle course module id. */
    private int $cmid = 0;

    /** Moodle context id. */
    private int $contextid = 0;

    /** User associated with the export, when relevant. */
    private int $userid = 0;

    /** Export title. */
    private string $title = '';

    /** Export description. */
    private string $description = '';

    /** Export format. */
    private string $exportformat = self::FORMAT_JSON;

    /** Export scope. */
    private string $exportscope = self::SCOPE_VALIDATED_ONLY;

    /** Export status. */
    private string $status = self::STATUS_DRAFT;

    /** Export visibility. */
    private string $visibility = self::VISIBILITY_PRIVATE;

    /** Provenance source. */
    private string $provenance = self::PROVENANCE_SYSTEM;

    /** Optional package hash. */
    private string $packagehash = '';

    /** Optional provenance hash. */
    private string $provenancehash = '';

    /** Stored filename. */
    private string $filename = '';

    /** File area used by Moodle file API. */
    private string $filearea = 'export_package';

    /** File item id used by Moodle file API. */
    private int $fileitemid = 0;

    /** File size in bytes. */
    private int $filesize = 0;

    /** MIME type. */
    private string $mimetype = '';

    /** Number of archive items included. */
    private int $itemcount = 0;

    /** Number of revisions included. */
    private int $revisioncount = 0;

    /** Number of files included. */
    private int $filecount = 0;

    /** Whether files are included. */
    private bool $includefiles = false;

    /** Whether revisions are included. */
    private bool $includerevisions = false;

    /** Whether restricted data was detected in source set. */
    private bool $hasrestricteddata = false;

    /** Whether the export package is redacted. */
    private bool $redacted = true;

    /** Whether integrity summary data is included. */
    private bool $includeintegrity = false;

    /** Whether AI logs are included. */
    private bool $includeailogs = false;

    /** Whether the package can be downloaded. */
    private bool $downloadable = false;

    /** Optional expiry timestamp. */
    private int $timeexpires = 0;

    /** Optional generation start timestamp. */
    private int $timestarted = 0;

    /** Optional generation finish timestamp. */
    private int $timecompleted = 0;

    /** User who created/requested the export. */
    private int $createdby = 0;

    /** User or task that last modified the export. */
    private int $modifiedby = 0;

    /** Creation timestamp. */
    private int $timecreated = 0;

    /** Modification timestamp. */
    private int $timemodified = 0;

    /** Version number. */
    private int $versionno = 1;

    /** Variable metadata. */
    private array $metadata = [];

    /**
     * Constructor.
     *
     * @param array<string, mixed>|stdClass|null $data Initial data.
     */
    public function __construct(array|stdClass|null $data = null) {
        if ($data !== null) {
            $this->apply_data((array)$data);
        }
    }

    /**
     * Build from a Moodle DB record.
     *
     * @param stdClass $record Record from {uckkarchive_export}.
     * @return self
     */
    public static function from_record(stdClass $record): self {
        return new self($record);
    }

    /**
     * Build a new export package.
     *
     * @param int $archiveid Parent archive id.
     * @param int $contextid Context id.
     * @param int $userid Requesting user id.
     * @param string $title Export title.
     * @param string $exportformat Export format.
     * @param string $exportscope Export scope.
     * @return self
     */
    public static function create(
        int $archiveid,
        int $contextid,
        int $userid,
        string $title,
        string $exportformat = self::FORMAT_JSON,
        string $exportscope = self::SCOPE_VALIDATED_ONLY
    ): self {
        return new self([
            'archiveid' => $archiveid,
            'contextid' => $contextid,
            'userid' => $userid,
            'title' => $title,
            'exportformat' => $exportformat,
            'exportscope' => $exportscope,
            'status' => self::STATUS_DRAFT,
            'visibility' => self::VISIBILITY_PRIVATE,
            'provenance' => self::PROVENANCE_SYSTEM,
            'redacted' => true,
            'versionno' => 1,
        ]);
    }

    /**
     * Apply raw data to this object.
     *
     * @param array<string, mixed> $data Raw data.
     */
    private function apply_data(array $data): void {
        $this->id = max(0, (int)($data['id'] ?? $this->id));
        $this->archiveid = max(0, (int)($data['archiveid'] ?? $data['uckkarchiveid'] ?? $this->archiveid));
        $this->courseid = max(0, (int)($data['courseid'] ?? $this->courseid));
        $this->cmid = max(0, (int)($data['cmid'] ?? $this->cmid));
        $this->contextid = max(0, (int)($data['contextid'] ?? $this->contextid));
        $this->userid = max(0, (int)($data['userid'] ?? $this->userid));

        $this->title = self::normalise_title((string)($data['title'] ?? $data['name'] ?? $this->title));
        $this->description = trim((string)($data['description'] ?? $this->description));

        $this->exportformat = self::normalise_export_format(
            (string)($data['exportformat'] ?? $data['format'] ?? $this->exportformat)
        );
        $this->exportscope = self::normalise_export_scope(
            (string)($data['exportscope'] ?? $data['scope'] ?? $this->exportscope)
        );

        $this->status = self::normalise_status((string)($data['status'] ?? $this->status));
        $this->visibility = self::normalise_visibility((string)($data['visibility'] ?? $this->visibility));
        $this->provenance = self::normalise_provenance((string)($data['provenance'] ?? $this->provenance));

        $this->packagehash = clean_param((string)($data['packagehash'] ?? $this->packagehash), PARAM_ALPHANUMEXT);
        $this->provenancehash = clean_param((string)($data['provenancehash'] ?? $this->provenancehash), PARAM_ALPHANUMEXT);

        $this->filename = clean_param((string)($data['filename'] ?? $this->filename), PARAM_FILE);
        $this->filearea = clean_param((string)($data['filearea'] ?? $this->filearea), PARAM_ALPHANUMEXT);
        $this->fileitemid = max(0, (int)($data['fileitemid'] ?? $this->fileitemid));
        $this->filesize = max(0, (int)($data['filesize'] ?? $this->filesize));
        $this->mimetype = clean_param((string)($data['mimetype'] ?? $this->mimetype), PARAM_MIMETYPE);

        $this->itemcount = max(0, (int)($data['itemcount'] ?? $this->itemcount));
        $this->revisioncount = max(0, (int)($data['revisioncount'] ?? $this->revisioncount));
        $this->filecount = max(0, (int)($data['filecount'] ?? $this->filecount));

        $this->includefiles = self::normalise_bool($data['includefiles'] ?? $this->includefiles);
        $this->includerevisions = self::normalise_bool($data['includerevisions'] ?? $this->includerevisions);
        $this->hasrestricteddata = self::normalise_bool($data['hasrestricteddata'] ?? $this->hasrestricteddata);
        $this->redacted = self::normalise_bool($data['redacted'] ?? $this->redacted);
        $this->includeintegrity = self::normalise_bool($data['includeintegrity'] ?? $this->includeintegrity);
        $this->includeailogs = self::normalise_bool($data['includeailogs'] ?? $this->includeailogs);
        $this->downloadable = self::normalise_bool($data['downloadable'] ?? $this->downloadable);

        $this->timeexpires = max(0, (int)($data['timeexpires'] ?? $this->timeexpires));
        $this->timestarted = max(0, (int)($data['timestarted'] ?? $this->timestarted));
        $this->timecompleted = max(0, (int)($data['timecompleted'] ?? $this->timecompleted));

        $this->createdby = max(0, (int)($data['createdby'] ?? $this->createdby));
        $this->modifiedby = max(0, (int)($data['modifiedby'] ?? $this->modifiedby));
        $this->timecreated = max(0, (int)($data['timecreated'] ?? $this->timecreated));
        $this->timemodified = max(0, (int)($data['timemodified'] ?? $this->timemodified));
        $this->versionno = max(1, (int)($data['versionno'] ?? $this->versionno));

        if (array_key_exists('metadata', $data)) {
            $this->metadata = self::normalise_metadata($data['metadata']);
        }
    }

    /**
     * Validate this package.
     *
     * @throws \coding_exception If invalid.
     */
    public function validate(): void {
        if ($this->archiveid <= 0) {
            throw new \coding_exception('Archive export package requires a valid archiveid.');
        }

        if ($this->contextid <= 0) {
            throw new \coding_exception('Archive export package requires a valid contextid.');
        }

        if ($this->userid <= 0 && $this->createdby <= 0) {
            throw new \coding_exception('Archive export package requires a requesting user.');
        }

        if ($this->title === '') {
            throw new \coding_exception('Archive export package requires a title.');
        }

        if (!in_array($this->exportformat, self::get_allowed_export_formats(), true)) {
            throw new \coding_exception('Invalid archive export format: ' . $this->exportformat);
        }

        if (!in_array($this->exportscope, self::get_allowed_export_scopes(), true)) {
            throw new \coding_exception('Invalid archive export scope: ' . $this->exportscope);
        }

        if (!in_array($this->status, self::get_allowed_statuses(), true)) {
            throw new \coding_exception('Invalid archive export status: ' . $this->status);
        }

        if (!in_array($this->visibility, self::get_allowed_visibilities(), true)) {
            throw new \coding_exception('Invalid archive export visibility: ' . $this->visibility);
        }

        if (!in_array($this->provenance, self::get_allowed_provenance_sources(), true)) {
            throw new \coding_exception('Invalid archive export provenance: ' . $this->provenance);
        }

        if ($this->visibility === self::VISIBILITY_PUBLIC && $this->hasrestricteddata && !$this->redacted) {
            throw new \coding_exception('Public archive export packages containing restricted data must be redacted.');
        }

        if ($this->exportscope === self::SCOPE_RESTRICTED_REDACTED && !$this->redacted) {
            throw new \coding_exception('Restricted redacted export scope requires redaction.');
        }

        if ($this->status === self::STATUS_COMPLETED && $this->downloadable && $this->filename === '') {
            throw new \coding_exception('Downloadable completed archive export packages require a filename.');
        }

        if ($this->timeexpires > 0 && $this->timecreated > 0 && $this->timeexpires <= $this->timecreated) {
            throw new \coding_exception('Archive export expiry must be after creation time.');
        }
    }

    /**
     * Convert to database record for {uckkarchive_export}.
     *
     * @param int|null $userid Acting user id.
     * @param int|null $now Current timestamp.
     * @return stdClass
     */
    public function to_record(?int $userid = null, ?int $now = null): stdClass {
        $this->validate();

        $userid ??= 0;
        $now ??= time();

        $record = new stdClass();

        if ($this->id > 0) {
            $record->id = $this->id;
        }

        $record->archiveid = $this->archiveid;
        $record->courseid = $this->courseid;
        $record->cmid = $this->cmid;
        $record->contextid = $this->contextid;
        $record->userid = $this->userid;
        $record->title = $this->title;
        $record->description = $this->description;
        $record->exportformat = $this->exportformat;
        $record->exportscope = $this->exportscope;
        $record->status = $this->status;
        $record->visibility = $this->visibility;
        $record->provenance = $this->provenance;
        $record->packagehash = $this->packagehash !== '' ? $this->packagehash : null;
        $record->provenancehash = $this->provenancehash !== '' ? $this->provenancehash : null;
        $record->filename = $this->filename;
        $record->filearea = $this->filearea;
        $record->fileitemid = $this->fileitemid;
        $record->filesize = $this->filesize;
        $record->mimetype = $this->mimetype;
        $record->itemcount = $this->itemcount;
        $record->revisioncount = $this->revisioncount;
        $record->filecount = $this->filecount;
        $record->includefiles = $this->includefiles ? 1 : 0;
        $record->includerevisions = $this->includerevisions ? 1 : 0;
        $record->hasrestricteddata = $this->hasrestricteddata ? 1 : 0;
        $record->redacted = $this->redacted ? 1 : 0;
        $record->includeintegrity = $this->includeintegrity ? 1 : 0;
        $record->includeailogs = $this->includeailogs ? 1 : 0;
        $record->downloadable = $this->downloadable ? 1 : 0;
        $record->timeexpires = $this->timeexpires;
        $record->timestarted = $this->timestarted;
        $record->timecompleted = $this->timecompleted;
        $record->createdby = $this->createdby > 0 ? $this->createdby : $userid;
        $record->modifiedby = $userid > 0 ? $userid : $this->modifiedby;
        $record->timecreated = $this->timecreated > 0 ? $this->timecreated : $now;
        $record->timemodified = $now;
        $record->versionno = $this->versionno;
        $record->metadata = $this->metadata === []
            ? null
            : json_encode($this->metadata, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);

        return $record;
    }

    /**
     * Convert to export-safe display/API data.
     *
     * @param bool $includerestricted Whether restricted metadata may be exposed.
     * @return stdClass
     */
    public function to_export(bool $includerestricted = false): stdClass {
        $data = new stdClass();
        $data->id = $this->id;
        $data->archiveid = $this->archiveid;
        $data->courseid = $this->courseid;
        $data->cmid = $this->cmid;
        $data->contextid = $this->contextid;
        $data->userid = $this->userid;
        $data->title = $this->title;
        $data->description = $this->description;
        $data->exportformat = $this->exportformat;
        $data->exportscope = $this->exportscope;
        $data->status = $this->status;
        $data->visibility = $this->visibility;
        $data->provenance = $this->provenance;
        $data->packagehash = $this->packagehash;
        $data->filename = $this->filename;
        $data->filearea = $this->filearea;
        $data->fileitemid = $this->fileitemid;
        $data->filesize = $this->filesize;
        $data->mimetype = $this->mimetype;
        $data->itemcount = $this->itemcount;
        $data->revisioncount = $this->revisioncount;
        $data->filecount = $this->filecount;
        $data->includefiles = $this->includefiles;
        $data->includerevisions = $this->includerevisions;
        $data->hasrestricteddata = $this->hasrestricteddata;
        $data->redacted = $this->redacted;
        $data->includeintegrity = $this->includeintegrity;
        $data->includeailogs = $this->includeailogs;
        $data->downloadable = $this->downloadable;
        $data->timeexpires = $this->timeexpires;
        $data->timestarted = $this->timestarted;
        $data->timecompleted = $this->timecompleted;
        $data->timecreated = $this->timecreated;
        $data->timemodified = $this->timemodified;
        $data->versionno = $this->versionno;
        $data->expired = $this->is_expired();

        if ($includerestricted || !$this->requires_restricted_handling()) {
            $data->metadata = $this->metadata;
            $data->provenancehash = $this->provenancehash;
        } else {
            $data->metadata = [];
            $data->provenancehash = '';
        }

        return $data;
    }

    /**
     * Whether the export package is complete.
     *
     * @return bool
     */
    public function is_completed(): bool {
        return $this->status === self::STATUS_COMPLETED;
    }

    /**
     * Whether the export package failed.
     *
     * @return bool
     */
    public function is_failed(): bool {
        return $this->status === self::STATUS_FAILED;
    }

    /**
     * Whether the export package is still being prepared.
     *
     * @return bool
     */
    public function is_processing(): bool {
        return in_array($this->status, [
            self::STATUS_PENDING,
            self::STATUS_PROCESSING,
        ], true);
    }

    /**
     * Whether this package can be downloaded.
     *
     * @return bool
     */
    public function can_download(): bool {
        return $this->downloadable
            && $this->is_completed()
            && !$this->is_expired()
            && $this->filename !== '';
    }

    /**
     * Whether this package is expired.
     *
     * @return bool
     */
    public function is_expired(): bool {
        return $this->timeexpires > 0 && $this->timeexpires <= time();
    }

    /**
     * Whether restricted handling is required.
     *
     * @return bool
     */
    public function requires_restricted_handling(): bool {
        return $this->hasrestricteddata
            || $this->visibility === self::VISIBILITY_RESTRICTED
            || $this->visibility === self::VISIBILITY_RESTRICTED_INTEGRITY
            || $this->exportscope === self::SCOPE_RESTRICTED_REDACTED
            || $this->includeintegrity;
    }

    /**
     * Whether the package must be redacted before public/institutional exposure.
     *
     * @return bool
     */
    public function requires_redaction(): bool {
        return $this->requires_restricted_handling() && !$this->redacted;
    }

    /**
     * Whether this package can be safely exposed as public metadata.
     *
     * @return bool
     */
    public function can_expose_public_metadata(): bool {
        return $this->visibility === self::VISIBILITY_PUBLIC
            && $this->is_completed()
            && !$this->is_expired()
            && (!$this->hasrestricteddata || $this->redacted);
    }

    /**
     * Return id.
     *
     * @return int
     */
    public function get_id(): int {
        return $this->id;
    }

    /**
     * Return archive id.
     *
     * @return int
     */
    public function get_archiveid(): int {
        return $this->archiveid;
    }

    /**
     * Return context id.
     *
     * @return int
     */
    public function get_contextid(): int {
        return $this->contextid;
    }

    /**
     * Return requesting user id.
     *
     * @return int
     */
    public function get_userid(): int {
        return $this->userid;
    }

    /**
     * Return title.
     *
     * @return string
     */
    public function get_title(): string {
        return $this->title;
    }

    /**
     * Return export format.
     *
     * @return string
     */
    public function get_exportformat(): string {
        return $this->exportformat;
    }

    /**
     * Return export scope.
     *
     * @return string
     */
    public function get_exportscope(): string {
        return $this->exportscope;
    }

    /**
     * Return status.
     *
     * @return string
     */
    public function get_status(): string {
        return $this->status;
    }

    /**
     * Return visibility.
     *
     * @return string
     */
    public function get_visibility(): string {
        return $this->visibility;
    }

    /**
     * Return filename.
     *
     * @return string
     */
    public function get_filename(): string {
        return $this->filename;
    }

    /**
     * Return file area.
     *
     * @return string
     */
    public function get_filearea(): string {
        return $this->filearea;
    }

    /**
     * Return file item id.
     *
     * @return int
     */
    public function get_fileitemid(): int {
        return $this->fileitemid;
    }

    /**
     * Return metadata.
     *
     * @return array<string, mixed>
     */
    public function get_metadata(): array {
        return $this->metadata;
    }

    /**
     * Return a metadata value.
     *
     * @param string $key Metadata key.
     * @param mixed $default Default value.
     * @return mixed
     */
    public function get_metadata_value(string $key, mixed $default = null): mixed {
        return $this->metadata[$key] ?? $default;
    }

    /**
     * Return copy with database id.
     *
     * @param int $id Record id.
     * @return self
     */
    public function with_id(int $id): self {
        $clone = clone $this;
        $clone->id = max(0, $id);
        return $clone;
    }

    /**
     * Return copy with Moodle context references.
     *
     * @param int $courseid Course id.
     * @param int $cmid Course module id.
     * @param int $contextid Context id.
     * @return self
     */
    public function with_context(int $courseid, int $cmid, int $contextid): self {
        $clone = clone $this;
        $clone->courseid = max(0, $courseid);
        $clone->cmid = max(0, $cmid);
        $clone->contextid = max(0, $contextid);
        return $clone;
    }

    /**
     * Return copy with status.
     *
     * @param string $status Status.
     * @return self
     */
    public function with_status(string $status): self {
        $clone = clone $this;
        $clone->status = self::normalise_status($status);
        return $clone;
    }

    /**
     * Return copy with generated file metadata.
     *
     * @param string $filename Filename.
     * @param string $filearea File area.
     * @param int $fileitemid File item id.
     * @param int $filesize File size.
     * @param string $mimetype MIME type.
     * @param string $packagehash Package hash.
     * @return self
     */
    public function with_file(
        string $filename,
        string $filearea,
        int $fileitemid,
        int $filesize,
        string $mimetype,
        string $packagehash = ''
    ): self {
        $clone = clone $this;
        $clone->filename = clean_param($filename, PARAM_FILE);
        $clone->filearea = clean_param($filearea, PARAM_ALPHANUMEXT);
        $clone->fileitemid = max(0, $fileitemid);
        $clone->filesize = max(0, $filesize);
        $clone->mimetype = clean_param($mimetype, PARAM_MIMETYPE);
        $clone->packagehash = clean_param($packagehash, PARAM_ALPHANUMEXT);
        $clone->downloadable = $clone->filename !== '';
        return $clone;
    }

    /**
     * Return copy with counts.
     *
     * @param int $itemcount Item count.
     * @param int $revisioncount Revision count.
     * @param int $filecount File count.
     * @return self
     */
    public function with_counts(int $itemcount, int $revisioncount, int $filecount): self {
        $clone = clone $this;
        $clone->itemcount = max(0, $itemcount);
        $clone->revisioncount = max(0, $revisioncount);
        $clone->filecount = max(0, $filecount);
        return $clone;
    }

    /**
     * Return copy with metadata.
     *
     * @param array<string, mixed> $metadata Metadata.
     * @return self
     */
    public function with_metadata(array $metadata): self {
        $clone = clone $this;
        $clone->metadata = self::normalise_metadata($metadata);
        return $clone;
    }

    /**
     * Return copy marked as processing.
     *
     * @param int $userid Acting user id.
     * @param int|null $now Timestamp.
     * @return self
     */
    public function mark_processing(int $userid, ?int $now = null): self {
        $clone = clone $this;
        $clone->status = self::STATUS_PROCESSING;
        $clone->modifiedby = max(0, $userid);
        $clone->timestarted = $now ?? time();
        $clone->timemodified = $clone->timestarted;
        return $clone;
    }

    /**
     * Return copy marked as completed.
     *
     * @param int $userid Acting user id.
     * @param int|null $now Timestamp.
     * @return self
     */
    public function mark_completed(int $userid, ?int $now = null): self {
        $clone = clone $this;
        $clone->status = self::STATUS_COMPLETED;
        $clone->downloadable = $clone->filename !== '';
        $clone->modifiedby = max(0, $userid);
        $clone->timecompleted = $now ?? time();
        $clone->timemodified = $clone->timecompleted;
        return $clone;
    }

    /**
     * Return copy marked as failed.
     *
     * @param int $userid Acting user id.
     * @param string $reason Failure reason.
     * @param int|null $now Timestamp.
     * @return self
     */
    public function mark_failed(int $userid, string $reason, ?int $now = null): self {
        $clone = clone $this;
        $clone->status = self::STATUS_FAILED;
        $clone->downloadable = false;
        $clone->modifiedby = max(0, $userid);
        $clone->timemodified = $now ?? time();
        $clone->metadata['failure_reason'] = $reason;
        return $clone;
    }

    /**
     * Allowed export formats.
     *
     * @return string[]
     */
    public static function get_allowed_export_formats(): array {
        return [
            self::FORMAT_JSON,
            self::FORMAT_CSV,
            self::FORMAT_ZIP,
            self::FORMAT_HTML,
            self::FORMAT_PDF,
            self::FORMAT_MOODLE,
        ];
    }

    /**
     * Allowed export scopes.
     *
     * @return string[]
     */
    public static function get_allowed_export_scopes(): array {
        return [
            self::SCOPE_SELECTED,
            self::SCOPE_VALIDATED_ONLY,
            self::SCOPE_PUBLIC_ONLY,
            self::SCOPE_FULL_ARCHIVE,
            self::SCOPE_FULL_WITH_REVISIONS,
            self::SCOPE_RESTRICTED_REDACTED,
        ];
    }

    /**
     * Allowed statuses.
     *
     * @return string[]
     */
    public static function get_allowed_statuses(): array {
        return [
            self::STATUS_DRAFT,
            self::STATUS_PENDING,
            self::STATUS_PROCESSING,
            self::STATUS_COMPLETED,
            self::STATUS_FAILED,
            self::STATUS_CANCELLED,
            self::STATUS_ARCHIVED,
        ];
    }

    /**
     * Allowed visibilities.
     *
     * @return string[]
     */
    public static function get_allowed_visibilities(): array {
        return [
            self::VISIBILITY_PRIVATE,
            self::VISIBILITY_USER,
            self::VISIBILITY_GROUP,
            self::VISIBILITY_COURSE,
            self::VISIBILITY_COHORT,
            self::VISIBILITY_PROGRAM,
            self::VISIBILITY_INSTITUTION,
            self::VISIBILITY_PUBLIC,
            self::VISIBILITY_RESTRICTED,
            self::VISIBILITY_RESTRICTED_INTEGRITY,
            self::VISIBILITY_ARCHIVED,
        ];
    }

    /**
     * Allowed provenance sources.
     *
     * @return string[]
     */
    public static function get_allowed_provenance_sources(): array {
        return [
            self::PROVENANCE_HUMAN,
            self::PROVENANCE_SYSTEM,
            self::PROVENANCE_ARCHIVE,
            self::PROVENANCE_INTEGRITY,
            self::PROVENANCE_IMPORTED,
        ];
    }

    /**
     * Normalise export format.
     *
     * @param string $format Raw format.
     * @return string
     */
    private static function normalise_export_format(string $format): string {
        $format = clean_param($format, PARAM_ALPHANUMEXT);

        return in_array($format, self::get_allowed_export_formats(), true)
            ? $format
            : self::FORMAT_JSON;
    }

    /**
     * Normalise export scope.
     *
     * @param string $scope Raw scope.
     * @return string
     */
    private static function normalise_export_scope(string $scope): string {
        $scope = clean_param($scope, PARAM_ALPHANUMEXT);

        return in_array($scope, self::get_allowed_export_scopes(), true)
            ? $scope
            : self::SCOPE_VALIDATED_ONLY;
    }

    /**
     * Normalise status.
     *
     * @param string $status Raw status.
     * @return string
     */
    private static function normalise_status(string $status): string {
        $status = clean_param($status, PARAM_ALPHANUMEXT);

        return in_array($status, self::get_allowed_statuses(), true)
            ? $status
            : self::STATUS_DRAFT;
    }

    /**
     * Normalise visibility.
     *
     * @param string $visibility Raw visibility.
     * @return string
     */
    private static function normalise_visibility(string $visibility): string {
        $visibility = clean_param($visibility, PARAM_ALPHANUMEXT);

        return in_array($visibility, self::get_allowed_visibilities(), true)
            ? $visibility
            : self::VISIBILITY_PRIVATE;
    }

    /**
     * Normalise provenance.
     *
     * @param string $provenance Raw provenance.
     * @return string
     */
    private static function normalise_provenance(string $provenance): string {
        $provenance = clean_param($provenance, PARAM_ALPHANUMEXT);

        return in_array($provenance, self::get_allowed_provenance_sources(), true)
            ? $provenance
            : self::PROVENANCE_SYSTEM;
    }

    /**
     * Normalise title.
     *
     * @param string $title Raw title.
     * @return string
     */
    private static function normalise_title(string $title): string {
        return trim(clean_param($title, PARAM_TEXT));
    }

    /**
     * Normalise boolean-ish input.
     *
     * @param mixed $value Raw value.
     * @return bool
     */
    private static function normalise_bool(mixed $value): bool {
        if (is_bool($value)) {
            return $value;
        }

        if (is_numeric($value)) {
            return (int)$value === 1;
        }

        if (is_string($value)) {
            return in_array(strtolower($value), ['1', 'true', 'yes', 'on'], true);
        }

        return !empty($value);
    }

    /**
     * Normalise metadata.
     *
     * @param mixed $metadata Raw metadata array, object, or JSON string.
     * @return array<string, mixed>
     */
    private static function normalise_metadata(mixed $metadata): array {
        if ($metadata === null || $metadata === '') {
            return [];
        }

        if (is_string($metadata)) {
            $decoded = json_decode($metadata, true);

            if (json_last_error() !== JSON_ERROR_NONE || !is_array($decoded)) {
                return [];
            }

            return $decoded;
        }

        if ($metadata instanceof stdClass) {
            return (array)$metadata;
        }

        if (is_array($metadata)) {
            return $metadata;
        }

        return [];
    }
}

