<?php
// This file is part of Moodle - https://moodle.org/
//
// Moodle is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// any later version.

/**
 * Tests for the public Médiathèque service.
 *
 * @package    mod_uckkarchive
 * @category   test
 * @copyright  2026 Univers-Cité King Klown
 * @license    https://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later
 */

declare(strict_types=1);

namespace mod_uckkarchive;

use advanced_testcase;
use mod_uckkarchive\local\public_mediatheque_service;

defined('MOODLE_INTERNAL') || die();

global $CFG;
require_once($CFG->dirroot . '/mod/uckkarchive/locallib.php');

/**
 * Public Médiathèque service contract tests.
 *
 * This test file protects the public-facing service contract only:
 *
 * - request normalisation;
 * - site-wide public defaults;
 * - public DTO envelope;
 * - pagination defaults and bounds;
 * - public surface metadata;
 * - fail-closed empty response behaviour;
 * - notices and warnings envelope shape.
 *
 * Media persistence, media files, collections, relations, markers, external
 * works, and internal media search are covered by repository, media-library
 * and external-service tests.
 *
 * @covers \mod_uckkarchive\local\public_mediatheque_service
 */
final class public_mediatheque_service_test extends advanced_testcase {
    /**
     * Reset DB after each test.
     *
     * @return void
     */
    protected function setUp(): void {
        parent::setUp();
        $this->resetAfterTest(true);

        if (!class_exists(public_mediatheque_service::class)) {
            $this->markTestSkipped('public_mediatheque_service is not implemented yet.');
        }
    }

    /**
     * The service should expose a stable public response contract even when
     * there are no public media records.
     *
     * @return void
     */
    public function test_search_returns_public_response_contract_when_empty(): void {
        $service = new public_mediatheque_service();

        $result = $service->search([]);

        $this->assertIsArray($result);

        $this->assertArrayHasKey('context', $result);
        $this->assertArrayHasKey('filters', $result);
        $this->assertArrayHasKey('facets', $result);
        $this->assertArrayHasKey('items', $result);
        $this->assertArrayHasKey('pagination', $result);
        $this->assertArrayHasKey('notices', $result);
        $this->assertArrayHasKey('warnings', $result);
        $this->assertArrayHasKey('empty', $result);

        $this->assertSame('mod_uckkarchive', $result['context']['component']);
        $this->assertSame('local_uckk', $result['context']['surface']);
        $this->assertSame('mediatheque', $result['context']['page']);
        $this->assertSame('mediatheque_explorer', $result['context']['explorer']);
        $this->assertArrayHasKey('anonymous', $result['context']);
        $this->assertArrayHasKey('policyfiltered', $result['context']);
        $this->assertTrue((bool)$result['context']['policyfiltered']);

        $this->assertArrayNotHasKey('scope', $result['context']);
        $this->assertArrayNotHasKey('cmid', $result['context']);
        $this->assertArrayNotHasKey('archiveid', $result['context']);

        $this->assertSame([], $result['items']);
        $this->assertSame([], $result['warnings']);

        $this->assertTrue((bool)$result['empty']['isempty']);
        $this->assertIsString($result['empty']['message']);
    }

    /**
     * Empty requests should be normalised to canonical Médiathèque defaults.
     *
     * @return void
     */
    public function test_normalise_request_applies_default_public_filters(): void {
        $service = new public_mediatheque_service();

        $filters = $service->normalise_request([]);

        $this->assertSame(0, $filters['cmid']);
        $this->assertSame(0, $filters['archiveid']);
        $this->assertSame('', $filters['q']);
        $this->assertSame('all', $filters['type']);
        $this->assertSame('all', $filters['mediatype']);
        $this->assertSame('', $filters['collection']);
        $this->assertSame('', $filters['tag']);
        $this->assertSame('', $filters['source']);
        $this->assertSame('all', $filters['advisory']);
        $this->assertSame('all', $filters['cultural']);
        $this->assertSame('all', $filters['audience']);
        $this->assertSame('', $filters['lang']);
        $this->assertSame('all', $filters['validation']);
        $this->assertSame('relevance', $filters['sort']);
        $this->assertSame(1, $filters['page']);
        $this->assertSame(12, $filters['perpage']);
    }

    /**
     * The public service should accept external-style "query" and normalise it
     * to the internal canonical "q" filter.
     *
     * @return void
     */
    public function test_normalise_request_maps_query_to_q(): void {
        $service = new public_mediatheque_service();

        $filters = $service->normalise_request([
            'query' => '  Mémoire publique  ',
        ]);

        $this->assertSame('Mémoire publique', $filters['q']);
    }

    /**
     * Nested external filters should be merged with top-level request values.
     *
     * @return void
     */
    public function test_normalise_request_accepts_nested_external_filters(): void {
        $service = new public_mediatheque_service();

        $filters = $service->normalise_request([
            'cmid' => 12,
            'archiveid' => 34,
            'query' => 'Archive',
            'filters' => [
                'type' => 'media',
                'mediatype' => 'video',
                'collection' => 'collection-uuid',
                'tag' => 'memoire',
                'source' => 'produced_by_uckk',
                'advisory' => 'has_public_advisory',
                'cultural' => 'has_public_protocol',
                'audience' => 'general',
                'lang' => 'fr',
                'validation' => 'verified',
            ],
            'page' => 3,
            'perpage' => 24,
            'sort' => 'newest',
        ]);

        $this->assertSame(12, $filters['cmid']);
        $this->assertSame(34, $filters['archiveid']);
        $this->assertSame('Archive', $filters['q']);
        $this->assertSame('media', $filters['type']);
        $this->assertSame('video', $filters['mediatype']);
        $this->assertSame('collection-uuid', $filters['collection']);
        $this->assertSame('memoire', $filters['tag']);
        $this->assertSame('produced_by_uckk', $filters['source']);
        $this->assertSame('has_public_advisory', $filters['advisory']);
        $this->assertSame('has_public_protocol', $filters['cultural']);
        $this->assertSame('general', $filters['audience']);
        $this->assertSame('fr', $filters['lang']);
        $this->assertSame('verified', $filters['validation']);
        $this->assertSame('newest', $filters['sort']);
        $this->assertSame(3, $filters['page']);
        $this->assertSame(24, $filters['perpage']);
    }

    /**
     * Invalid public parameters should fall back to safe defaults.
     *
     * @return void
     */
    public function test_normalise_request_rejects_invalid_public_filter_values(): void {
        $service = new public_mediatheque_service();

        $filters = $service->normalise_request([
            'cmid' => -100,
            'archiveid' => -200,
            'q' => '  Needle  ',
            'type' => 'not-a-type',
            'mediatype' => 'not-a-format',
            'collection' => '<bad collection>',
            'tag' => '<script>alert(1)</script>',
            'source' => '<raw-source>',
            'advisory' => 'leak-private-advisory',
            'cultural' => 'leak-cultural-protocol',
            'audience' => 'not-audience',
            'lang' => 'not a lang',
            'validation' => 'raw-validation-state',
            'sort' => 'raw-sql-field',
            'page' => -10,
            'perpage' => 999,
        ]);

        $this->assertSame(0, $filters['cmid']);
        $this->assertSame(0, $filters['archiveid']);
        $this->assertSame('Needle', $filters['q']);
        $this->assertSame('all', $filters['type']);
        $this->assertSame('all', $filters['mediatype']);
        $this->assertSame('badcollection', $filters['collection']);
        $this->assertSame('scriptalert1script', $filters['tag']);
        $this->assertSame('', $filters['source']);
        $this->assertSame('all', $filters['advisory']);
        $this->assertSame('all', $filters['cultural']);
        $this->assertSame('all', $filters['audience']);
        $this->assertSame('', $filters['lang']);
        $this->assertSame('all', $filters['validation']);
        $this->assertSame('relevance', $filters['sort']);
        $this->assertSame(1, $filters['page']);
        $this->assertSame(48, $filters['perpage']);
    }

    /**
     * Valid scope parameters should be preserved in filters.
     *
     * @return void
     */
    public function test_normalise_request_preserves_valid_scope_parameters(): void {
        $service = new public_mediatheque_service();

        $filters = $service->normalise_request([
            'cmid' => 12,
            'archiveid' => 34,
        ]);

        $this->assertSame(12, $filters['cmid']);
        $this->assertSame(34, $filters['archiveid']);
    }

    /**
     * Valid public filters should be preserved in canonical form.
     *
     * @return void
     */
    public function test_normalise_request_preserves_valid_public_filters(): void {
        $service = new public_mediatheque_service();

        $filters = $service->normalise_request([
            'q' => 'Video',
            'type' => 'media',
            'mediatype' => 'video',
            'collection' => 'abc-123',
            'tag' => 'memoire',
            'source' => 'produced_by_uckk',
            'advisory' => 'has_public_advisory',
            'cultural' => 'has_public_protocol',
            'audience' => 'general',
            'lang' => 'fr',
            'validation' => 'verified',
            'sort' => 'newest',
            'page' => 3,
            'perpage' => 24,
        ]);

        $this->assertSame('Video', $filters['q']);
        $this->assertSame('media', $filters['type']);
        $this->assertSame('video', $filters['mediatype']);
        $this->assertSame('abc-123', $filters['collection']);
        $this->assertSame('memoire', $filters['tag']);
        $this->assertSame('produced_by_uckk', $filters['source']);
        $this->assertSame('has_public_advisory', $filters['advisory']);
        $this->assertSame('has_public_protocol', $filters['cultural']);
        $this->assertSame('general', $filters['audience']);
        $this->assertSame('fr', $filters['lang']);
        $this->assertSame('verified', $filters['validation']);
        $this->assertSame('newest', $filters['sort']);
        $this->assertSame(3, $filters['page']);
        $this->assertSame(24, $filters['perpage']);
    }

    /**
     * The public DTO must not expose raw database rows or raw file authority.
     *
     * @return void
     */
    public function test_search_response_does_not_expose_raw_private_fields(): void {
        $service = new public_mediatheque_service();

        $result = $service->search([]);

        $forbiddenkeys = [
            'sql',
            'params',
            'rawrecords',
            'metadata',
            'metadatajson',
            'private_notes',
            'culturalprotocolnote',
            'reviewnote',
            'filepath',
            'filedir',
            'contenthash',
            'pathnamehash',
            'originalfileurl',
            'downloadurl',
            'fileurl',
        ];

        foreach ($forbiddenkeys as $key) {
            $this->assertArrayNotHasKey($key, $result);
            $this->assertArrayNotHasKey($key, $result['context']);
            $this->assertArrayNotHasKey($key, $result['filters']);
        }
    }

    /**
     * Notices should be public-safe strings, not raw policy/debug objects.
     *
     * @return void
     */
    public function test_search_returns_public_safe_notices(): void {
        $service = new public_mediatheque_service();

        $result = $service->search([]);

        $this->assertIsArray($result['notices']);
        $this->assertNotEmpty($result['notices']);

        foreach ($result['notices'] as $notice) {
            $this->assertIsArray($notice);
            $this->assertArrayHasKey('type', $notice);
            $this->assertArrayHasKey('code', $notice);
            $this->assertArrayHasKey('message', $notice);

            $this->assertIsString($notice['type']);
            $this->assertIsString($notice['code']);
            $this->assertIsString($notice['message']);

            $this->assertArrayNotHasKey('exception', $notice);
            $this->assertArrayNotHasKey('trace', $notice);
            $this->assertArrayNotHasKey('sql', $notice);
            $this->assertArrayNotHasKey('params', $notice);
        }
    }

    /**
     * Facets should use the canonical grouped public shape.
     *
     * @return void
     */
    public function test_search_returns_canonical_facet_groups(): void {
        $service = new public_mediatheque_service();

        $result = $service->search([]);

        $this->assertIsArray($result['facets']);

        foreach ($result['facets'] as $facet) {
            $this->assertIsArray($facet);
            $this->assertArrayHasKey('key', $facet);
            $this->assertArrayHasKey('label', $facet);
            $this->assertArrayHasKey('items', $facet);

            $this->assertIsString($facet['key']);
            $this->assertIsString($facet['label']);
            $this->assertIsArray($facet['items']);

            foreach ($facet['items'] as $item) {
                $this->assertIsArray($item);
                $this->assertArrayHasKey('value', $item);
                $this->assertArrayHasKey('label', $item);
                $this->assertArrayHasKey('count', $item);
                $this->assertArrayHasKey('active', $item);

                $this->assertIsString($item['value']);
                $this->assertIsString($item['label']);
                $this->assertIsInt($item['count']);
                $this->assertIsBool($item['active']);
            }
        }
    }

    /**
     * Warnings should exist as an array and must not contain raw exceptions.
     *
     * @return void
     */
    public function test_search_returns_public_safe_warnings(): void {
        $service = new public_mediatheque_service();

        $result = $service->search([]);

        $this->assertIsArray($result['warnings']);

        foreach ($result['warnings'] as $warning) {
            $this->assertIsArray($warning);
            $this->assertArrayHasKey('item', $warning);
            $this->assertArrayHasKey('itemid', $warning);
            $this->assertArrayHasKey('warningcode', $warning);
            $this->assertArrayHasKey('message', $warning);

            $this->assertIsString($warning['item']);
            $this->assertIsString($warning['itemid']);
            $this->assertIsString($warning['warningcode']);
            $this->assertIsString($warning['message']);

            $this->assertArrayNotHasKey('exception', $warning);
            $this->assertArrayNotHasKey('trace', $warning);
            $this->assertArrayNotHasKey('sql', $warning);
            $this->assertArrayNotHasKey('params', $warning);
        }
    }
}