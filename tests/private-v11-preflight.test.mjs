import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { inspectDerivedView } from '../src/private-v11-preflight.mjs';

// The fixture is copied from a separate producer snapshot in the same offline
// branch package; this test does not require the Pack to be installed at runtime.
const view = () => JSON.parse(readFileSync(new URL('../examples/derived-v11-demo.json', import.meta.url)));
const digest = (v) => Object.fromEntries(['graph','registry','crosswalk','catalog'].map(k=>[k,v.source[k+'_sha256']]));

test('private inspection accepts the exact derived Pack fixture without granting publication', () => {
  const v = view(); const result = inspectDerivedView(v,digest(v));
  assert.equal(result.status,'STRUCTURALLY_VERIFIED_NOT_PUBLIC');
  assert.equal(result.counts.identities,3);
  assert.equal(result.counts.assertions,1);
  assert.equal(result.counts.lexical.missing,2);
  assert.equal(result.publication_authorized,false);
  assert.equal(result.canonical_authority_claimed,false);
  assert.equal(result.framework_validation_performed,false);
});

for (const [label, mutate] of [
  ['non-derivative',v=>v.derived_only=false],
  ['false public authorization',v=>v.profile='encyklopedia.publication-bundle/0.1.0'],
  ['Wikidata pretending to be canonical',v=>v.presentation[0].semantic_id='Q8018'],
  ['lexical coverage mismatch',v=>v.coverage_counts.fallback=2],
  ['fallback called direct',v=>v.presentation[1].lexical.status='direct'],
  ['invented missing word',v=>v.presentation[0].lexical.term='invented'],
  ['missing assertion entity',v=>v.assertions[0].object.id='KQ999'],
  ['unapproved crosswalk',v=>v.presentation[1].accepted_external_exact.id='P5'],
  ['private source reference changed',v=>v.assertions[0].sources=['Q8018']],
 ]) test('private preflight refuses '+label,()=>{
  const v=view(); mutate(v);
  assert.throws(()=>inspectDerivedView(v,digest(v)),/PRIVATE_V11_REJECTED/);
});

test('private preflight refuses changed or absent input digests',()=>{
  const v=view(); const h=digest(v); h.graph='b'.repeat(64);
  assert.throws(()=>inspectDerivedView(v,h),/digest mismatch/);
  assert.throws(()=>inspectDerivedView(v,{}),/digest mismatch/);
});

// File-level checks complement the structural fixtures: CLI callers must
// supply every original source file and never rely on asserted checksums alone.
test('file preflight requires real matching source bytes and refuses corruption', async () => {
  const { mkdtempSync, writeFileSync, rmSync } = await import('node:fs');
  const { tmpdir } = await import('node:os');
  const { join } = await import('node:path');
  const { createHash } = await import('node:crypto');
  const { inspectFile } = await import('../src/private-v11-preflight.mjs');
  const folder = mkdtempSync(join(tmpdir(), 'encyk-private-v11-test-'));
  try {
    const v = view(); const paths = {};
    for (const name of ['graph', 'registry', 'crosswalk', 'catalog']) {
      const file = join(folder, name + '.json');
      writeFileSync(file, JSON.stringify({name}));
      paths[name] = file;
      v.source[name+'_sha256'] = createHash('sha256').update(readFileSync(file)).digest('hex');
    }
    const file = join(folder, 'view.json'); writeFileSync(file, JSON.stringify(v));
    assert.equal(inspectFile(file, paths).status, 'STRUCTURALLY_VERIFIED_NOT_PUBLIC');
    writeFileSync(paths.graph, JSON.stringify({name:'changed'}));
    assert.throws(() => inspectFile(file, paths), /digest mismatch/);
    assert.throws(() => inspectFile(file, {...paths, catalog:undefined}), /missing canonical input/);
  } finally { rmSync(folder,{recursive:true,force:true}); }
});
