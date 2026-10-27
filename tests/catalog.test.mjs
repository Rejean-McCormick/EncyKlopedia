import test from 'node:test';
import assert from 'node:assert/strict';
import { loadDemoPublication, validateDemoPublication, browse, localizeArticle, articleBySlug, requestedLocale } from '../src/catalog.mjs';
const fixture = loadDemoPublication();
test('synthetic fixture validates',()=>assert.equal(fixture.articles.length,2));
test('search supports French accents and bounded results',()=>{
 assert.equal(browse(fixture,'fr','Observatoire').length,1);
 assert.equal(browse(fixture,'fr','observatoire').length,1);
 assert.equal(browse(fixture,'en','nomatch').length,0);
});
test('direct and fallback are distinguished',()=>{
 assert.equal(localizeArticle(fixture.articles[0],'fr').display_status,'direct');
 const fallback=localizeArticle(fixture.articles[1],'fr');
 assert.equal(fallback.display_status,'fallback');assert.equal(fallback.effective_locale,'en');
 assert.equal(localizeArticle(fixture.articles[0],'fr-CA').effective_locale,'fr');
 assert.equal(localizeArticle(fixture.articles[0],'ja').display_status,'fallback');
});
test('missing pages stay missing; read-only semantics',()=>assert.equal(articleBySlug(fixture,'not-here'),null));
test('invalid locale yields safe English',()=>assert.equal(requestedLocale('../../file',['en']),'en'));
test('reject real-source and qualified flags',()=>{
 const a=structuredClone(fixture);a.qualified=true;assert.throws(()=>validateDemoPublication(a),/blocked/);
 const b=structuredClone(fixture);b.articles[0].source_refs[0].url='https://example.org';assert.throws(()=>validateDemoPublication(b),/forbidden/);
 const c=structuredClone(fixture);c.articles[0].semantic_id='KQ1001';assert.throws(()=>validateDemoPublication(c),/synthetic/);
});
test('duplicate slugs are refused',()=>{
 const a=structuredClone(fixture);a.articles[1].slug=a.articles[0].slug;assert.throws(()=>validateDemoPublication(a),/duplicate/);
});
