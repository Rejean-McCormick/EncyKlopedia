/**
 * EncyKlopedia's narrow, non-canonical public display format.
 * It does not validate, approve or publish Kristal semantic authority.
 */
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';

export const DEMO_FIXTURE = fileURLToPath(new URL('../examples/synthetic-publication.json', import.meta.url));
export const PUBLICATION_PROFILE = 'encyklopedia.publication-bundle/0.1.0';
export const V11_VIEW_PROFILE = 'kristal.integration.read-view/v11.0-draft.1';
const SLUG = /^[a-z0-9]+(?:-[a-z0-9]+)*$/;
const LOCALE = /^[a-z]{2,3}(?:-[A-Za-z0-9]{2,8}){0,2}$/;
const MAX_RESULTS = 30;

export function validateDemoPublication(data) {
  if (!data || typeof data !== 'object' || Array.isArray(data)) throw new Error('invalid publication document');
  if (data.profile !== PUBLICATION_PROFILE) throw new Error('unsupported publication profile');
  if (data.mode !== 'synthetic-demo' || data.qualified !== false) throw new Error('unqualified/public data blocked');
  if (data.source_view_profile !== V11_VIEW_PROFILE) throw new Error('unexpected upstream reader profile');
  if (!Array.isArray(data.articles) || data.articles.length > 200 || data.articles.length === 0) throw new Error('invalid demo articles');
  if (!Array.isArray(data.locales) || data.locales.length < 1 || data.locales.length > 20 || !data.locales.includes('en')) throw new Error('invalid demo locales');
  if (new Set(data.locales).size !== data.locales.length || data.locales.some(l => typeof l !== 'string' || !LOCALE.test(l))) throw new Error('invalid locale identifiers');
  if (typeof data.publication_id !== 'string' || !data.publication_id.startsWith('demo-')) throw new Error('demo publication id required');
  const seen = new Set();
  for (const a of data.articles) {
    if (!a || typeof a !== 'object' || typeof a.id !== 'string' || !a.id.startsWith('demo:')) throw new Error('only synthetic article ids allowed');
    if (typeof a.slug !== 'string' || !SLUG.test(a.slug) || a.slug.length > 80 || seen.has(a.slug)) throw new Error('invalid or duplicate slug');
    seen.add(a.slug);
    if (typeof a.semantic_id !== 'string' || !a.semantic_id.startsWith('demo:')) throw new Error('synthetic identities required');
    if (!a.localized || typeof a.localized !== 'object' || Array.isArray(a.localized) || !a.localized.en) throw new Error('English demo fallback required');
    if (!Array.isArray(a.source_refs) || a.source_refs.length > 10) throw new Error('invalid source refs');
    for (const loc of Object.keys(a.localized)) {
      const x = a.localized[loc];
      if (!data.locales.includes(loc) || !x || typeof x.title !== 'string' || !x.title.trim() || typeof x.summary !== 'string' ||
          !Array.isArray(x.sections) || x.sections.length > 12 || x.sections.some(s => typeof s.heading !== 'string' || typeof s.body !== 'string')) {
        throw new Error('invalid localized article');
      }
    }
    for (const ref of a.source_refs) {
      if (!ref || typeof ref.label !== 'string' || !ref.id?.startsWith('demo:') || ref.url !== null) throw new Error('real source references forbidden in demo');
    }
  }
  return data;
}

export function loadDemoPublication(path = DEMO_FIXTURE) {
  return validateDemoPublication(JSON.parse(readFileSync(path, 'utf8')));
}

export function requestedLocale(raw, supported) {
  const key = String(raw ?? 'en').slice(0, 40).trim();
  return LOCALE.test(key) ? key : 'en';
}

export function localizeArticle(article, locale) {
  const direct = article.localized[locale];
  const base = locale.split('-')[0];
  const content = direct ?? article.localized[base] ?? article.localized.en;
  const effective_locale = direct ? locale : article.localized[base] ? base : 'en';
  // UI article availability, NOT normative Framework v11 lexical coverage.
  const display_status = direct ? 'direct' : content ? 'fallback' : 'missing';
  return {
    id: article.id, slug: article.slug, semantic_id: article.semantic_id,
    requested_locale: locale, effective_locale, display_status,
    title: content?.title ?? null, summary: content?.summary ?? null,
    sections: content?.sections ?? [], source_refs: article.source_refs
  };
}

export function browse(publication, locale = 'en', query = '', limit = MAX_RESULTS) {
  const q = String(query).trim().slice(0, 200).normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLocaleLowerCase();
  const max = Math.min(MAX_RESULTS, Math.max(1, Number.isFinite(limit) ? limit : MAX_RESULTS));
  return publication.articles.map(a => localizeArticle(a, locale)).filter(a => {
    if (!q) return true;
    const hay = `${a.title ?? ''} ${a.summary ?? ''} ${a.semantic_id}`.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLocaleLowerCase();
    return hay.includes(q);
  }).slice(0, max).map(({sections,source_refs,...preview}) => preview);
}

export function articleBySlug(publication, slug, locale = 'en') {
  const a = publication.articles.find(item => item.slug === slug);
  return a ? localizeArticle(a, locale) : null;
}
