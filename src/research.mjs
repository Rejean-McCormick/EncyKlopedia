/** Unqualified private UNESCO research format, NEVER a publication adapter. */
import { readFileSync, statSync } from 'node:fs';
import { resolve, join, dirname } from 'node:path';
import { createHash } from 'node:crypto';

export const RESEARCH_PROFILE = 'encyklopedia.unesco-research-view/1.0';
const concept = /^concept\d+$/;
const slug = /^[a-z0-9]+(?:-[a-z0-9]+)*$/;

export function validateResearchView(view) {
  if (!view || typeof view !== 'object' || Array.isArray(view) ||
      view.profile !== RESEARCH_PROFILE || view.mode !== 'private-research' ||
      view.qualified !== false || view.publication_enabled !== false ||
      view.publication_id !== 'NONE_PRIVATE_RESEARCH_NOT_A_PUBLICATION') {
    throw new Error('Only unqualified private UNESCO research views are supported');
  }
  if (JSON.stringify(view.locales) !== '["en"]' ||
      view.branch?.id !== 'unesco-mt1-10' || view.branch?.language !== 'en' ||
      !Array.isArray(view.articles) || view.articles.length !== 41 ||
      !Array.isArray(view.root_catalog) || view.root_catalog.length > 120 ||
      !view.rdf_comparison || !view.source_sha256) throw new Error('Invalid branch research data');
  const ids = new Set(), slugs = new Set();
  let candidates = 0, proposalCount = 0, enriched = 0;
  for (const a of view.articles) {
    if (!concept.test(a.unesco_id ?? '') || a.id !== `unesco:${a.unesco_id}` ||
        !/^KQ\d+$/.test(a.semantic_id ?? '') || a.identity_status !== 'provisional' ||
        !slug.test(a.slug ?? '') || ids.has(a.unesco_id) || slugs.has(a.slug) ||
        a.unesco_uri !== `http://vocabularies.unesco.org/thesaurus/${a.unesco_id}`) {
      throw new Error('Invalid or duplicate provisional UNESCO identity');
    }
    ids.add(a.unesco_id); slugs.add(a.slug);
    if (!a.localized?.en || typeof a.localized.en.title !== 'string' ||
        typeof a.localized.en.summary !== 'string' || !Array.isArray(a.localized.en.sections) ||
        a.localized.en.sections.length > 16 ||
        a.localized.en.sections.some(s => typeof s.heading !== 'string' || typeof s.body !== 'string')) {
      throw new Error('Invalid English research article');
    }
    if (!a.skos_relations || !['broader','narrower','related'].every(r => Array.isArray(a.skos_relations[r]))) throw new Error('SKOS missing');
    if (a.wikidata_candidate !== null) {
      if (!/^Q\d+$/.test(a.wikidata_candidate?.id ?? '') || a.wikidata_candidate.status !== 'candidate' ||
          a.wikidata_candidate.relation !== 'proposed_exact_match') throw new Error('Approved or malformed Wikidata link');
      candidates++;
    }
    if (!Array.isArray(a.source_refs) || !Array.isArray(a.claim_proposals)) throw new Error('Missing unreviewed research arrays');
    if (a.editorial_status === 'research_candidate_unapproved') {
      if (a.unesco_id !== 'concept10' || a.source_refs.length !== 6 || a.claim_proposals.length !== 19) throw new Error('Unsupported research entry');
      enriched++;
    } else if (a.editorial_status !== 'source_anchor_only' || a.claim_proposals.length || a.source_refs.length) {
      throw new Error('Unqualified or non-anchor article');
    }
    for (const s of a.source_refs) {
      if (!/^SRC-[A-Z0-9-]+$/.test(s.id ?? '') || !/^https:\/\//.test(s.url ?? '') ||
          s.capture_status !== 'NOT_CAPTURED' || s.review_status !== 'pending') throw new Error('Source capture/approval not permitted');
    }
    for (const c of a.claim_proposals) {
      if (!/^RTE-KA-PROP-\d{3}$/.test(c.id ?? '') || c.status !== 'candidate_unreviewed' ||
          !a.source_refs.some(s => s.id === c.source_id) || typeof c.statement !== 'string') throw new Error('Claim approval or broken provenance');
      proposalCount++;
    }
  }
  if (ids.size !== 41 || candidates !== 36 || enriched !== 1 || proposalCount !== 19)
    throw new Error('Incomplete research set');
  return view;
}

export function loadResearchView(path) {
  if (typeof path !== 'string' || !path.trim()) throw new Error('Explicit research file is required');
  const abs = resolve(path);
  if (statSync(abs).size > 3 * 1024 * 1024) throw new Error('Research view exceeds safe size');
  const bytes = readFileSync(abs);
  const report = JSON.parse(readFileSync(join(dirname(abs), 'build-report.json'), 'utf8'));
  const digest = createHash('sha256').update(bytes).digest('hex');
  if (report?.status !== 'PRIVATE_RESEARCH_BUILT_UNQUALIFIED' || report?.view_sha256 !== digest ||
      report?.claims_approved !== 0 || report?.public_release !== false) throw new Error('Private research report/digest gate failed');
  return validateResearchView(JSON.parse(bytes.toString('utf8')));
}
