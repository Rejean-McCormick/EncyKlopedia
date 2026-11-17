<?php
// This file is part of Moodle - https://moodle.org/
//
// Moodle is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// any later version.

/**
 * Version metadata for the UCKK Archive activity module.
 *
 * @package    mod_uckkarchive
 * @copyright  2026 Univers-Cité King Klown
 * @license    https://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later
 */

defined('MOODLE_INTERNAL') || die();

$plugin->component = 'mod_uckkarchive';
$plugin->version = 2026100303;
$plugin->requires = 2025041400;
$plugin->maturity = MATURITY_BETA;
$plugin->release = '1.3.3-beta';

$plugin->dependencies = [
    'local_uckk' => 2026051200,
    'tool_uckkintegrity' => 2026051200,
];

$plugin->cron = 0;