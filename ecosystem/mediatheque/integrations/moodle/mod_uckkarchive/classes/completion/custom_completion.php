<?php
// This file is part of Moodle - https://moodle.org/
//
// Moodle is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// any later version.

/**
 * Custom completion rules for the UCKK Archive activity.
 *
 * @package    mod_uckkarchive
 * @copyright  2026 Univers-Cité King Klown
 * @license    https://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later
 */

declare(strict_types=1);

namespace mod_uckkarchive\completion;

use coding_exception;
use core_completion\activity_custom_completion;
use stdClass;

defined('MOODLE_INTERNAL') || die();

/**
 * Custom completion rules for mod_uckkarchive.
 *
 * This class only reads archive records to determine Moodle completion state.
 * It must not create archive items, validate items, revise records, export
 * packages, alter provenance, or decide visibility/integrity outcomes.
 */
final class custom_completion extends activity_custom_completion {
    /** Completion rule: the user has created at least one archive item. */
    public const RULE_ITEM_ADDED = 'completionrequireitem';

    /** Completion rule: the user has at least one validated archive item. */
    public const RULE_ITEM_VALIDATED = 'completionrequirevalidateditem';

    /** Legacy/config alias used by older install.xml snapshots. */
    private const ALIAS_ITEM_VALIDATED = 'completionrequirevalidation';

    /** Legacy/config alias used by older completion snapshots. */
    private const LEGACY_ITEM_ADDED = 'completionitemadded';

    /** Legacy/config alias used by older completion snapshots. */
    private const LEGACY_ITEM_VALIDATED = 'completionitemvalidated';

    /**
     * Return completion state for a custom rule.
     *
     * @param string $rule Completion rule name.
     * @return int COMPLETION_COMPLETE or COMPLETION_INCOMPLETE.
     */
    public function get_state(string $rule): int {
        $rule = $this->normalise_rule($rule);
        $this->validate_rule($rule);

        if (!$this->is_rule_enabled($rule)) {
            return COMPLETION_INCOMPLETE;
        }

        return match ($rule) {
            self::RULE_ITEM_ADDED => $this->has_user_archive_item(),
            self::RULE_ITEM_VALIDATED => $this->has_user_validated_archive_item(),
            default => COMPLETION_INCOMPLETE,
        };
    }

    /**
     * Return all custom rules defined by this activity.
     *
     * These names must match the rules returned by mod_form::add_completion_rules().
     *
     * @return array<int, string>
     */
    public static function get_defined_custom_rules(): array {
        return [
            self::RULE_ITEM_ADDED,
            self::RULE_ITEM_VALIDATED,
        ];
    }

    /**
     * Return human-readable descriptions of active custom rules.
     *
     * @return array<string, string>
     */
    public function get_custom_rule_descriptions(): array {
        $descriptions = [];

        if ($this->is_rule_enabled(self::RULE_ITEM_ADDED)) {
            $descriptions[self::RULE_ITEM_ADDED] = $this->safe_get_string(
                'completionrequireitem_desc',
                $this->safe_get_string('completionrequireitem', 'Require the learner to add an archive item.')
            );
        }

        if ($this->is_rule_enabled(self::RULE_ITEM_VALIDATED)) {
            $descriptions[self::RULE_ITEM_VALIDATED] = $this->safe_get_string(
                'completionrequirevalidateditem_desc',
                $this->safe_get_string('completionrequirevalidateditem', 'Require the learner to have a validated archive item.')
            );
        }

        return $descriptions;
    }

    /**
     * Return display order for completion rules.
     *
     * Moodle's activity_custom_completion parent requires this method.
     *
     * @return array<int, string>
     */
    public function get_sort_order(): array {
        return [
            'completionview',
            self::RULE_ITEM_ADDED,
            self::RULE_ITEM_VALIDATED,
        ];
    }

    /**
     * Return whether a rule is defined by this activity.
     *
     * @param string $rule Completion rule name.
     * @return bool
     */
    public function is_defined(string $rule): bool {
        return in_array($this->normalise_rule($rule), self::get_defined_custom_rules(), true);
    }

    /**
     * Throw if a rule is unknown.
     *
     * Moodle expects this method to be public.
     *
     * @param string $rule Completion rule name.
     */
    public function validate_rule(string $rule): void {
        if (!$this->is_defined($rule)) {
            throw new coding_exception('Unknown mod_uckkarchive custom completion rule: ' . $rule);
        }
    }

    /**
     * Return whether a custom completion rule is enabled for this cm.
     *
     * Supports values stored in cm_info customdata['customcompletionrules'] and
     * direct fields on the archive instance record. Compatibility aliases cover
     * older snapshots that used completionrequirevalidation or completionitem*.
     *
     * @param string $rule Rule name.
     * @return bool
     */
    private function is_rule_enabled(string $rule): bool {
        $rule = $this->normalise_rule($rule);
        $aliases = $this->get_rule_aliases($rule);

        if (
            isset($this->cm->customdata['customcompletionrules'])
            && is_array($this->cm->customdata['customcompletionrules'])
        ) {
            foreach ($aliases as $alias) {
                if (array_key_exists($alias, $this->cm->customdata['customcompletionrules'])) {
                    return !empty($this->cm->customdata['customcompletionrules'][$alias]);
                }
            }
        }

        $archive = $this->get_archive_instance();

        if ($archive !== null) {
            foreach ($aliases as $alias) {
                if (property_exists($archive, $alias)) {
                    return !empty($archive->{$alias});
                }
            }
        }

        return false;
    }

    /**
     * Normalise legacy/config rule names to active rule names.
     *
     * @param string $rule Rule name.
     * @return string
     */
    private function normalise_rule(string $rule): string {
        return match ($rule) {
            self::ALIAS_ITEM_VALIDATED,
            self::LEGACY_ITEM_VALIDATED => self::RULE_ITEM_VALIDATED,
            self::LEGACY_ITEM_ADDED => self::RULE_ITEM_ADDED,
            default => $rule,
        };
    }

    /**
     * Return accepted storage aliases for a rule.
     *
     * @param string $rule Active rule name.
     * @return array<int, string>
     */
    private function get_rule_aliases(string $rule): array {
        return match ($rule) {
            self::RULE_ITEM_ADDED => [
                self::RULE_ITEM_ADDED,
                self::LEGACY_ITEM_ADDED,
            ],
            self::RULE_ITEM_VALIDATED => [
                self::RULE_ITEM_VALIDATED,
                self::ALIAS_ITEM_VALIDATED,
                self::LEGACY_ITEM_VALIDATED,
            ],
            default => [$rule],
        };
    }

    /**
     * Load the archive instance for this course module.
     *
     * @return stdClass|null
     */
    private function get_archive_instance(): ?stdClass {
        global $DB;

        if (empty($this->cm->instance)) {
            return null;
        }

        return $DB->get_record('uckkarchive', ['id' => $this->cm->instance], '*', IGNORE_MISSING) ?: null;
    }

    /**
     * Return whether a table exists.
     *
     * @param string $tablename Moodle table name without braces.
     * @return bool
     */
    private function table_exists(string $tablename): bool {
        global $DB;

        return $DB->get_manager()->table_exists($tablename);
    }

    /**
     * Return whether a field exists in a table.
     *
     * @param string $tablename Moodle table name without braces.
     * @param string $field Field name.
     * @return bool
     */
    private function field_exists(string $tablename, string $field): bool {
        global $DB;

        if (!$this->table_exists($tablename)) {
            return false;
        }

        $columns = $DB->get_columns($tablename);

        return array_key_exists($field, $columns);
    }

    /**
     * Return the archive foreign-key condition for a child table.
     *
     * @param string $tablename Table name.
     * @return array<string, int>|null
     */
    private function get_archive_condition(string $tablename): ?array {
        if ($this->field_exists($tablename, 'archiveid')) {
            return ['archiveid' => (int)$this->cm->instance];
        }

        if ($this->field_exists($tablename, 'uckkarchiveid')) {
            return ['uckkarchiveid' => (int)$this->cm->instance];
        }

        return null;
    }

    /**
     * Return an OR SQL condition for ownership by the current user.
     *
     * @param string $tablename Table name.
     * @param array<string, mixed> $params Existing params.
     * @return array{sql: string, params: array<string, mixed>}
     */
    private function get_user_condition(string $tablename, array $params = []): array {
        $fields = [];

        foreach (['userid', 'authorid', 'createdby', 'submittedby', 'ownerid'] as $field) {
            if ($this->field_exists($tablename, $field)) {
                $paramname = 'user_' . $field;
                $fields[] = "{$field} = :{$paramname}";
                $params[$paramname] = (int)$this->userid;
            }
        }

        if (empty($fields)) {
            return [
                'sql' => '1 = 0',
                'params' => $params,
            ];
        }

        return [
            'sql' => '(' . implode(' OR ', $fields) . ')',
            'params' => $params,
        ];
    }

    /**
     * Return an SQL condition for accepted validation states.
     *
     * @param string $tablename Table name.
     * @param array<string, mixed> $params Existing params.
     * @return array{sql: string, params: array<string, mixed>}
     */
    private function get_validated_condition(string $tablename, array $params = []): array {
        $parts = [];

        if ($this->field_exists($tablename, 'status')) {
            $parts[] = 'status IN (:statusvalidated, :statuspublished, :statusarchived)';
            $params['statusvalidated'] = 'validated';
            $params['statuspublished'] = 'published';
            $params['statusarchived'] = 'archived';
        }

        if ($this->field_exists($tablename, 'validationstate')) {
            $parts[] = 'validationstate IN (:validationhumanreviewed, :validationverified, :validationarchived)';
            $params['validationhumanreviewed'] = 'human_reviewed';
            $params['validationverified'] = 'verified';
            $params['validationarchived'] = 'archived';
        }

        if (empty($parts)) {
            return [
                'sql' => '1 = 0',
                'params' => $params,
            ];
        }

        return [
            'sql' => '(' . implode(' OR ', $parts) . ')',
            'params' => $params,
        ];
    }

    /**
     * Completion state when the current user has created an archive item.
     *
     * @return int
     */
    private function has_user_archive_item(): int {
        global $DB;

        $tablename = 'uckkarchive_item';

        if (!$this->table_exists($tablename)) {
            return COMPLETION_INCOMPLETE;
        }

        $archivecondition = $this->get_archive_condition($tablename);

        if ($archivecondition === null) {
            return COMPLETION_INCOMPLETE;
        }

        $params = [
            'archiveid' => reset($archivecondition),
        ];

        $archivefield = key($archivecondition);
        $usercondition = $this->get_user_condition($tablename, $params);

        $count = $DB->count_records_select(
            $tablename,
            "{$archivefield} = :archiveid AND {$usercondition['sql']}",
            $usercondition['params']
        );

        return $count > 0 ? COMPLETION_COMPLETE : COMPLETION_INCOMPLETE;
    }

    /**
     * Completion state when the current user has a validated archive item.
     *
     * @return int
     */
    private function has_user_validated_archive_item(): int {
        global $DB;

        $tablename = 'uckkarchive_item';

        if (!$this->table_exists($tablename)) {
            return COMPLETION_INCOMPLETE;
        }

        $archivecondition = $this->get_archive_condition($tablename);

        if ($archivecondition === null) {
            return COMPLETION_INCOMPLETE;
        }

        $params = [
            'archiveid' => reset($archivecondition),
        ];

        $archivefield = key($archivecondition);
        $usercondition = $this->get_user_condition($tablename, $params);
        $validatedcondition = $this->get_validated_condition($tablename, $usercondition['params']);

        $count = $DB->count_records_select(
            $tablename,
            "{$archivefield} = :archiveid AND {$usercondition['sql']} AND {$validatedcondition['sql']}",
            $validatedcondition['params']
        );

        return $count > 0 ? COMPLETION_COMPLETE : COMPLETION_INCOMPLETE;
    }

    /**
     * Safe component language string lookup.
     *
     * @param string $identifier String identifier.
     * @param string $fallback Fallback value.
     * @return string
     */
    private function safe_get_string(string $identifier, string $fallback): string {
        $manager = get_string_manager();

        if ($manager->string_exists($identifier, 'uckkarchive')) {
            return get_string($identifier, 'uckkarchive');
        }

        return $fallback;
    }
}
