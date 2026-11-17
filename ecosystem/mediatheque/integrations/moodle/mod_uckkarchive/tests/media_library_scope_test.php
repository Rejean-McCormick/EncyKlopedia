<?php
// This file is part of Moodle - https://moodle.org/.

/**
 * Tests for autonomous media libraries and sharing bridges.
 *
 * @package    mod_uckkarchive
 * @category   test
 * @copyright  2026 Univers-Cité King Klown
 * @license    https://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later
 */

declare(strict_types=1);

namespace mod_uckkarchive;

use advanced_testcase;
use mod_uckkarchive\local\media_library_scope;

defined('MOODLE_INTERNAL') || die();

/**
 * @covers \mod_uckkarchive\local\media_library_scope
 */
final class media_library_scope_test extends advanced_testcase {
    protected function setUp(): void {
        parent::setUp();
        $this->resetAfterTest(true);
    }

    public function test_default_libraries_are_distinct(): void {
        $scope = new media_library_scope();

        $uckk = $scope->resolve_by_slug(media_library_scope::LIBRARY_UCKK);
        $ucc = $scope->resolve_by_slug(media_library_scope::LIBRARY_UCC);
        $math = $scope->resolve_by_slug(media_library_scope::LIBRARY_MATH);

        $this->assertNotNull($uckk);
        $this->assertNotNull($ucc);
        $this->assertNotNull($math);
        $this->assertNotSame((int)$uckk->id, (int)$ucc->id);
        $this->assertNotSame((int)$uckk->id, (int)$math->id);
        $this->assertNotSame((int)$ucc->id, (int)$math->id);
    }

    public function test_same_library_can_be_primary_for_two_sites(): void {
        $scope = new media_library_scope();
        $shared = $scope->create_library('shared-demo', 'Fonds partagé de démonstration');

        $scope->attach_library_to_site('shared-demo', 'site-a', media_library_scope::SITE_ROLE_PRIMARY);
        $scope->attach_library_to_site('shared-demo', 'site-b', media_library_scope::SITE_ROLE_PRIMARY);

        $sitea = $scope->resolve_primary_for_site('site-a');
        $siteb = $scope->resolve_primary_for_site('site-b');

        $this->assertNotNull($sitea);
        $this->assertNotNull($siteb);
        $this->assertSame((int)$shared->id, (int)$sitea->id);
        $this->assertSame((int)$shared->id, (int)$siteb->id);
    }

    public function test_bridge_records_are_directional(): void {
        $scope = new media_library_scope();
        $source = $scope->resolve_by_slug(media_library_scope::LIBRARY_UCC);
        $target = $scope->resolve_by_slug(media_library_scope::LIBRARY_MATH);

        $this->assertNotNull($source);
        $this->assertNotNull($target);

        $scope->create_bridge(
            media_library_scope::LIBRARY_UCC,
            media_library_scope::LIBRARY_MATH,
            media_library_scope::SCOPE_LIBRARY,
            0,
            'UCC vers math'
        );

        $bridges = $scope->get_all_bridges();
        $this->assertCount(1, $bridges);
        $bridge = reset($bridges);
        $this->assertSame((int)$source->id, (int)$bridge->sourcelibraryid);
        $this->assertSame((int)$target->id, (int)$bridge->targetlibraryid);
    }
}
