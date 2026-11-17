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
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with Moodle. If not, see <https://www.gnu.org/licenses/>.

/**
 * External service for adding an external work reference to UCKK Archive.
 *
 * @package    mod_uckkarchive
 * @copyright  2026 UCKK
 * @license    https://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later
 */

namespace mod_uckkarchive\external;

use context_module;
use external_api;
use external_function_parameters;
use external_multiple_structure;
use external_single_structure;
use external_value;
use invalid_parameter_exception;
use mod_uckkarchive\local\external_work;

defined('MOODLE_INTERNAL') || die();

require_once($CFG->libdir . '/externallib.php');

/**
 * Add an external work reference.
 *
 * External works are third-party, foreign, public-domain, licensed, fair-use,
 * or reference-only works that the archive may cite, teach, tag, review, or
 * connect to media/content advisories without necessarily copying the work.
 *
 * This service creates the metadata record only. It does not imply UCKK owns
 * the external work, and it does not bypass content advisory, cultural protocol,
 * rights, redaction, or export policy.
 */
final class add_external_work extends external_api {
    /**
     * Describe service parameters.
     *
     * @return external_function_parameters
     */
    public static function execute_parameters(): external_function_parameters {
        return new external_function_parameters([
            'cmid' => new external_value(PARAM_INT, 'Course module id for the UCKK Archive instance.'),
            'title' => new external_value(PARAM_TEXT, 'External work title.'),
            'worktype' => new external_value(PARAM_ALPHANUMEXT, 'External work type.', VALUE_DEFAULT, 'other'),
            'creator' => new external_value(PARAM_TEXT, 'Creator, author, director, artist, or source creator.', VALUE_DEFAULT, ''),
            'publisher' => new external_value(PARAM_TEXT, 'Publisher, distributor, platform, or source.', VALUE_DEFAULT, ''),
            'publicationyear' => new external_value(PARAM_INT, 'Publication/release year.', VALUE_DEFAULT, 0),
            'sourceurl' => new external_value(PARAM_RAW, 'External source URL.', VALUE_DEFAULT, ''),
            'identifier' => new external_value(PARAM_TEXT, 'External identifier such as DOI, ISBN, URI, accession number, or catalogue id.', VALUE_DEFAULT, ''),
            'identifiertype' => new external_value(PARAM_ALPHANUMEXT, 'Identifier type.', VALUE_DEFAULT, ''),
            'citation' => new external_value(PARAM_RAW, 'Citation or reference text.', VALUE_DEFAULT, ''),
            'subtitle' => new external_value(PARAM_TEXT, 'Subtitle.', VALUE_DEFAULT, ''),
            'language' => new external_value(PARAM_ALPHANUMEXT, 'Language code.', VALUE_DEFAULT, ''),
            'description' => new external_value(PARAM_RAW, 'Description.', VALUE_DEFAULT, ''),
            'rightsstatus' => new external_value(PARAM_ALPHANUMEXT, 'Rights status.', VALUE_DEFAULT, 'unknown'),
            'rightsstatement' => new external_value(PARAM_RAW, 'Rights statement.', VALUE_DEFAULT, ''),
            'licensekey' => new external_value(PARAM_TEXT, 'License key or label.', VALUE_DEFAULT, ''),
            'sourcenote' => new external_value(PARAM_RAW, 'Source note.', VALUE_DEFAULT, ''),
            'teachingnote' => new external_value(PARAM_RAW, 'Teaching note.', VALUE_DEFAULT, ''),
            'culturalprotocolnote' => new external_value(PARAM_RAW, 'Cultural protocol note.', VALUE_DEFAULT, ''),
            'visibility' => new external_value(PARAM_ALPHANUMEXT, 'Visibility.', VALUE_DEFAULT, 'course'),
            'status' => new external_value(PARAM_ALPHANUMEXT, 'External work status.', VALUE_DEFAULT, 'draft'),
            'audiencesuitability' => new external_value(PARAM_ALPHANUMEXT, 'Audience suitability.', VALUE_DEFAULT, 'guided'),
            'metadata' => new external_single_structure([
                'keywords' => new external_multiple_structure(
                    new external_value(PARAM_TEXT, 'Keyword.'),
                    'Keywords.',
                    VALUE_DEFAULT,
                    []
                ),
                'notes' => new external_value(PARAM_RAW, 'Internal notes.', VALUE_DEFAULT, ''),
                'sourcecontext' => new external_value(PARAM_RAW, 'Context explaining why this work is referenced.', VALUE_DEFAULT, ''),
                'advisoryhint' => new external_value(PARAM_RAW, 'Optional advisory hint before marker review.', VALUE_DEFAULT, ''),
            ], 'Optional external work metadata.', VALUE_DEFAULT, []),
        ]);
    }

    /**
     * Execute service.
     *
     * @param int $cmid Course module id.
     * @param string $title Title.
     * @param string $worktype Work type.
     * @param string $creator Creator.
     * @param string $publisher Publisher/source.
     * @param int $publicationyear Publication year.
     * @param string $sourceurl Source URL.
     * @param string $identifier Identifier.
     * @param string $identifiertype Identifier type.
     * @param string $citation Citation.
     * @param string $subtitle Subtitle.
     * @param string $language Language code.
     * @param string $description Description.
     * @param string $rightsstatus Rights status.
     * @param string $rightsstatement Rights statement.
     * @param string $licensekey License key.
     * @param string $sourcenote Source note.
     * @param string $teachingnote Teaching note.
     * @param string $culturalprotocolnote Cultural protocol note.
     * @param string $visibility Visibility.
     * @param string $status Status.
     * @param string $audiencesuitability Audience suitability.
     * @param array $metadata Metadata.
     * @return array Result.
     */
    public static function execute(
        int $cmid,
        string $title,
        string $worktype = 'other',
        string $creator = '',
        string $publisher = '',
        int $publicationyear = 0,
        string $sourceurl = '',
        string $identifier = '',
        string $identifiertype = '',
        string $citation = '',
        string $subtitle = '',
        string $language = '',
        string $description = '',
        string $rightsstatus = 'unknown',
        string $rightsstatement = '',
        string $licensekey = '',
        string $sourcenote = '',
        string $teachingnote = '',
        string $culturalprotocolnote = '',
        string $visibility = 'course',
        string $status = 'draft',
        string $audiencesuitability = 'guided',
        array $metadata = []
    ): array {
        global $DB, $USER;

        [
            'cmid' => $cmid,
            'title' => $title,
            'worktype' => $worktype,
            'creator' => $creator,
            'publisher' => $publisher,
            'publicationyear' => $publicationyear,
            'sourceurl' => $sourceurl,
            'identifier' => $identifier,
            'identifiertype' => $identifiertype,
            'citation' => $citation,
            'subtitle' => $subtitle,
            'language' => $language,
            'description' => $description,
            'rightsstatus' => $rightsstatus,
            'rightsstatement' => $rightsstatement,
            'licensekey' => $licensekey,
            'sourcenote' => $sourcenote,
            'teachingnote' => $teachingnote,
            'culturalprotocolnote' => $culturalprotocolnote,
            'visibility' => $visibility,
            'status' => $status,
            'audiencesuitability' => $audiencesuitability,
            'metadata' => $metadata,
        ] = self::validate_parameters(self::execute_parameters(), [
            'cmid' => $cmid,
            'title' => $title,
            'worktype' => $worktype,
            'creator' => $creator,
            'publisher' => $publisher,
            'publicationyear' => $publicationyear,
            'sourceurl' => $sourceurl,
            'identifier' => $identifier,
            'identifiertype' => $identifiertype,
            'citation' => $citation,
            'subtitle' => $subtitle,
            'language' => $language,
            'description' => $description,
            'rightsstatus' => $rightsstatus,
            'rightsstatement' => $rightsstatement,
            'licensekey' => $licensekey,
            'sourcenote' => $sourcenote,
            'teachingnote' => $teachingnote,
            'culturalprotocolnote' => $culturalprotocolnote,
            'visibility' => $visibility,
            'status' => $status,
            'audiencesuitability' => $audiencesuitability,
            'metadata' => $metadata,
        ]);

        $cm = get_coursemodule_from_id('uckkarchive', $cmid, 0, false, MUST_EXIST);
        $course = $DB->get_record('course', ['id' => $cm->course], '*', MUST_EXIST);
        $archive = $DB->get_record('uckkarchive', ['id' => $cm->instance], '*', MUST_EXIST);
        $context = context_module::instance($cm->id);

        self::validate_context($context);
        require_login($course, false, $cm);
        require_capability('mod/uckkarchive:manageexternalworks', $context);

        $worktype = self::normalize_value($worktype);
        $rightsstatus = self::normalize_value($rightsstatus);
        $visibility = self::normalize_visibility($visibility);
        $status = self::normalize_value($status);
        $audiencesuitability = self::normalize_value($audiencesuitability);

        self::require_allowed_value($worktype, self::allowed_work_types(), 'Invalid external work type.');
        self::require_allowed_value($rightsstatus, self::allowed_rights_statuses(), 'Invalid rights status.');
        self::require_allowed_value($visibility, self::allowed_visibility(), 'Invalid visibility.');
        self::require_allowed_value($status, self::allowed_statuses(), 'Invalid external work status.');
        self::require_allowed_value($audiencesuitability, self::allowed_audience_suitability(), 'Invalid audience suitability.');

        if (trim($title) === '') {
            throw new invalid_parameter_exception('External work title is required.');
        }

        if (trim($creator) === '' && trim($publisher) === '' && trim($sourceurl) === '') {
            throw new invalid_parameter_exception('External work requires creator, publisher, or source URL.');
        }

        if (trim($citation) === '' && trim($sourceurl) === '' && trim($identifier) === '') {
            throw new invalid_parameter_exception('External work requires citation, source URL, or identifier.');
        }

        $record = [
            'archiveid' => (int)$archive->id,
            'courseid' => (int)$course->id,
            'cmid' => (int)$cm->id,
            'contextid' => (int)$context->id,
            'title' => $title,
            'subtitle' => $subtitle,
            'worktype' => $worktype,
            'creator' => $creator,
            'publisher' => $publisher,
            'publicationyear' => max(0, (int)$publicationyear),
            'language' => $language,
            'sourceurl' => $sourceurl,
            'identifier' => $identifier,
            'identifiertype' => $identifiertype,
            'citation' => $citation,
            'description' => $description,
            'rightsstatus' => $rightsstatus,
            'rightsstatement' => $rightsstatement,
            'licensekey' => $licensekey,
            'sourcenote' => $sourcenote,
            'teachingnote' => $teachingnote,
            'culturalprotocolnote' => $culturalprotocolnote,
            'visibility' => $visibility,
            'status' => $status,
            'audiencesuitability' => $audiencesuitability,
            'metadata' => $metadata,
        ];

        $transaction = $DB->start_delegated_transaction();

        if (!class_exists(external_work::class) || !method_exists(external_work::class, 'create')) {
            throw new \coding_exception('The external work domain service must implement mod_uckkarchive\\local\\external_work::create().');
        }

        $work = external_work::create($record, (int)$USER->id);

        $transaction->allow_commit();

        self::trigger_created_event($work, $context);

        return self::format_external_work_response($work, $context);
    }

    /**
     * Describe service return structure.
     *
     * @return external_single_structure
     */
    public static function execute_returns(): external_single_structure {
        return new external_single_structure([
            'id' => new external_value(PARAM_INT, 'External work id.'),
            'uuid' => new external_value(PARAM_RAW, 'Stable external work UUID.'),
            'archiveid' => new external_value(PARAM_INT, 'Archive instance id.'),
            'courseid' => new external_value(PARAM_INT, 'Course id.'),
            'cmid' => new external_value(PARAM_INT, 'Course module id.'),
            'contextid' => new external_value(PARAM_INT, 'Context id.'),
            'ownerid' => new external_value(PARAM_INT, 'Owner user id.'),
            'createdby' => new external_value(PARAM_INT, 'Creator user id.'),
            'modifiedby' => new external_value(PARAM_INT, 'Modifier user id.'),
            'worktype' => new external_value(PARAM_ALPHANUMEXT, 'External work type.'),
            'status' => new external_value(PARAM_ALPHANUMEXT, 'Status.'),
            'visibility' => new external_value(PARAM_ALPHANUMEXT, 'Visibility.'),
            'audiencesuitability' => new external_value(PARAM_ALPHANUMEXT, 'Audience suitability.'),
            'rightsstatus' => new external_value(PARAM_ALPHANUMEXT, 'Rights status.'),
            'title' => new external_value(PARAM_TEXT, 'Title.'),
            'subtitle' => new external_value(PARAM_TEXT, 'Subtitle.'),
            'creator' => new external_value(PARAM_TEXT, 'Creator.'),
            'publisher' => new external_value(PARAM_TEXT, 'Publisher/source.'),
            'publicationyear' => new external_value(PARAM_INT, 'Publication year.'),
            'language' => new external_value(PARAM_ALPHANUMEXT, 'Language.'),
            'sourceurl' => new external_value(PARAM_RAW, 'Source URL.'),
            'identifier' => new external_value(PARAM_TEXT, 'Identifier.'),
            'identifiertype' => new external_value(PARAM_ALPHANUMEXT, 'Identifier type.'),
            'citation' => new external_value(PARAM_RAW, 'Citation.'),
            'rightsstatement' => new external_value(PARAM_RAW, 'Rights statement.'),
            'licensekey' => new external_value(PARAM_TEXT, 'License key.'),
            'sourcenote' => new external_value(PARAM_RAW, 'Source note.'),
            'teachingnote' => new external_value(PARAM_RAW, 'Teaching note.'),
            'culturalprotocolnote' => new external_value(PARAM_RAW, 'Cultural protocol note.'),
            'description' => new external_value(PARAM_RAW, 'Description.'),
            'provenanceid' => new external_value(PARAM_INT, 'Provenance id.'),
            'metadatajson' => new external_value(PARAM_RAW, 'JSON-encoded metadata for external API consumers.'),
            'timecreated' => new external_value(PARAM_INT, 'Created timestamp.'),
            'timemodified' => new external_value(PARAM_INT, 'Modified timestamp.'),
            'canview' => new external_value(PARAM_BOOL, 'Whether the current user can view this external work.'),
            'canedit' => new external_value(PARAM_BOOL, 'Whether the current user can edit this external work.'),
            'canreviewadvisories' => new external_value(PARAM_BOOL, 'Whether the current user can review related advisories.'),
        ]);
    }

    /**
     * Format an external work record for external response.
     *
     * @param \stdClass $work External work record.
     * @param \context_module $context Context.
     * @return array
     */
    private static function format_external_work_response(\stdClass $work, \context_module $context): array {
        $export = external_work::export_record($work);

        return [
            'id' => (int)$export['id'],
            'uuid' => (string)$export['uuid'],
            'archiveid' => (int)$export['archiveid'],
            'courseid' => (int)$export['courseid'],
            'cmid' => (int)$export['cmid'],
            'contextid' => (int)$export['contextid'],
            'ownerid' => (int)$export['ownerid'],
            'createdby' => (int)$export['createdby'],
            'modifiedby' => (int)$export['modifiedby'],
            'worktype' => (string)$export['worktype'],
            'status' => (string)$export['status'],
            'visibility' => (string)$export['visibility'],
            'audiencesuitability' => (string)$export['audiencesuitability'],
            'rightsstatus' => (string)$export['rightsstatus'],
            'title' => (string)$export['title'],
            'subtitle' => (string)$export['subtitle'],
            'creator' => (string)$export['creator'],
            'publisher' => (string)$export['publisher'],
            'publicationyear' => (int)$export['publicationyear'],
            'language' => (string)$export['language'],
            'sourceurl' => (string)$export['sourceurl'],
            'identifier' => (string)$export['identifier'],
            'identifiertype' => (string)$export['identifiertype'],
            'citation' => (string)$export['citation'],
            'rightsstatement' => (string)$export['rightsstatement'],
            'licensekey' => (string)$export['licensekey'],
            'sourcenote' => (string)$export['sourcenote'],
            'teachingnote' => (string)$export['teachingnote'],
            'culturalprotocolnote' => (string)$export['culturalprotocolnote'],
            'description' => (string)$export['description'],
            'provenanceid' => (int)$export['provenanceid'],
            'metadatajson' => json_encode($export['metadata'], JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES) ?: '{}',
            'timecreated' => (int)$export['timecreated'],
            'timemodified' => (int)$export['timemodified'],
            'canview' => has_capability('mod/uckkarchive:viewmedia', $context),
            'canedit' => has_capability('mod/uckkarchive:manageexternalworks', $context),
            'canreviewadvisories' => has_capability('mod/uckkarchive:reviewadvisories', $context),
        ];
    }

    /**
     * Trigger external_work_created if the event class exists.
     *
     * @param \stdClass $work External work record.
     * @param \context_module $context Context.
     * @return void
     */
    private static function trigger_created_event(\stdClass $work, \context_module $context): void {
        $eventclass = '\\mod_uckkarchive\\event\\external_work_created';

        if (!class_exists($eventclass)) {
            return;
        }

        try {
            $event = $eventclass::create([
                'objectid' => (int)$work->id,
                'context' => $context,
                'other' => [
                    'uuid' => (string)($work->uuid ?? ''),
                    'worktype' => (string)($work->worktype ?? ''),
                    'visibility' => (string)($work->visibility ?? ''),
                ],
            ]);
            $event->add_record_snapshot('uckkarchive_external_work', $work);
            $event->trigger();
        } catch (\Throwable $ignored) {
            // Event availability must not break persistence while files are generated incrementally.
        }
    }

    /**
     * Validate allowed value.
     *
     * @param string $value Value.
     * @param string[] $allowed Allowed values.
     * @param string $message Error message.
     * @return void
     */
    private static function require_allowed_value(string $value, array $allowed, string $message): void {
        if (!in_array($value, $allowed, true)) {
            throw new invalid_parameter_exception($message);
        }
    }

    /**
     * Normalize compatibility visibility values.
     *
     * @param string $visibility Visibility.
     * @return string
     */
    private static function normalize_visibility(string $visibility): string {
        $visibility = self::normalize_value($visibility);

        return $visibility === 'institutional' ? 'institution' : $visibility;
    }

    /**
     * Normalize machine value.
     *
     * @param string $value Value.
     * @return string
     */
    private static function normalize_value(string $value): string {
        return strtolower(trim($value));
    }

    /**
     * Allowed external work types.
     *
     * @return string[]
     */
    private static function allowed_work_types(): array {
        return [
            'film',
            'book',
            'article',
            'podcast',
            'website',
            'external_video',
            'external_image',
            'public_archive_item',
            'third_party_pdf',
            'other',
        ];
    }

    /**
     * Allowed rights statuses.
     *
     * @return string[]
     */
    private static function allowed_rights_statuses(): array {
        return [
            'unknown',
            'third_party_copyright',
            'licensed_external',
            'public_domain',
            'open_license',
            'fair_use_reference',
            'restricted_reference',
        ];
    }

    /**
     * Allowed visibility values.
     *
     * @return string[]
     */
    private static function allowed_visibility(): array {
        return [
            'private',
            'user',
            'group',
            'course',
            'cohort',
            'program',
            'institution',
            'institutional',
            'public',
            'restricted',
            'restricted_integrity',
            'restricted_cultural',
        ];
    }

    /**
     * Allowed external work statuses.
     *
     * @return string[]
     */
    private static function allowed_statuses(): array {
        return [
            'draft',
            'active',
            'restricted',
            'archived',
            'deleted_soft',
        ];
    }

    /**
     * Allowed audience suitability values.
     *
     * @return string[]
     */
    private static function allowed_audience_suitability(): array {
        return [
            'general',
            'guided',
            'mature',
            'restricted',
            'restricted_cultural',
            'restricted_integrity',
            'staff_only',
        ];
    }
}
