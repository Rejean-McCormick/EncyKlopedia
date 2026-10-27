import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { createHash } from 'node:crypto';
import { listGithubKristals, inspectGithubKristal, loadGithubKristal, verifyCollectionIndex } from '../server/integrations/kristal-v10.mjs';

const digest = (bytes) => 'sha256:' + createHash('sha256').update(bytes).digest('hex');
// This fixture follows the Framework v10 draft.3 digest projections (not a semantic state generator).
const cpCompare = (a, b) => {
  const x = Array.from(a, c => c.codePointAt(0)), y = Array.from(b, c => c.codePointAt(0));
  for (let i=0; i<Math.min(x.length,y.length); i++) if (x[i]!==y[i]) return x[i]-y[i];
  return x.length-y.length;
};
const jcs = (value) => value === null || typeof value !== 'object' ? JSON.stringify(value) :
  Array.isArray(value) ? '['+value.map(jcs).join(',')+']' :
    '{'+Object.keys(value).sort(cpCompare).map(k=>JSON.stringify(k)+':'+jcs(value[k])).join(',')+'}';
const jsonDigest = (data) => digest(Buffer.from(jcs(data)));
const commitment = { profile:'kristal.state-commitment/jcs-sha256-v1', digest:'sha256:'+'b'.repeat(64) };
const mkfile = (root, rel, text) => {
  const full=path.join(root,...rel.split('/'));
  fs.mkdirSync(path.dirname(full),{recursive:true});fs.writeFileSync(full,text);
};
function fixture(t) {
  const root=fs.mkdtempSync(path.join(os.tmpdir(),'konstellation-v10-'));
  t.after(()=>fs.rmSync(root,{recursive:true,force:true}));
  const slug='demo'; const prefix=`kristals/${slug}`;
  const state={ schema_version:'9.0', artifact_type:'kristal_state_snapshot', state_ref:'urn:kristal:state:demo', logical_commitment:commitment,
    members:[{artifact_id:'urn:kristal:artifact:one',logical_commitment:{profile:'kristal.logical/jcs-sha256-v1',digest:'sha256:'+'a'.repeat(64)}}], references:[], parents:[] };
  const aiManifest={format:'kristal.portable-ai/1.0',state_ref:state.state_ref,state_logical_commitment:commitment,read_order:['AI_START_HERE.md','ai/INDEX.json']};
  const files=new Map([
    ['AI_START_HERE.md','# Demo\n'],
    ['AI_MANIFEST.json',JSON.stringify(aiManifest)],
    ['state/state-snapshot.json',JSON.stringify(state)],
    ['canon/domain/core.json',JSON.stringify({value:1})],
  ]);
  const catalogEntries=[...files].map(([name,value])=>({path:name,role:name.startsWith('canon/')?'canonical_content':'documentation',size:Buffer.byteLength(value),sha256:digest(value)}));
  const aiIndex={format:'kristal.ai-index/1.0',state_ref:state.state_ref,state_logical_commitment:commitment,
    files:[catalogEntries.find(r=>r.path==='canon/domain/core.json')],materialization_blobs:[]};
  files.set('ai/INDEX.json',JSON.stringify(aiIndex));
  const all=[...files].map(([name,value])=>({path:name,role:name==='state/state-snapshot.json'?'state_snapshot':name==='ai/INDEX.json'?'ai_index':name==='AI_MANIFEST.json'?'ai_manifest':'documentation',size:Buffer.byteLength(value),sha256:digest(value)})).sort((a,b)=>Buffer.compare(Buffer.from(a.path),Buffer.from(b.path)));
  for(const [name,value] of files) mkfile(root,`${prefix}/${name}`,value);
  const sync={format:'kristal.github-sync-manifest/1.0',manager_version:'test',slug,title:'Demo v10',target_root:prefix,entrypoint:'AI_START_HERE.md',state_ref:state.state_ref,state_logical_commitment:commitment,
    file_count:all.length,total_bytes:all.reduce((n,r)=>n+r.size,0),materialization_object_count:0,
    files:all,policy:{derived_read_surface:true,sync_is_not_publication:true,activation_is_separate:true,materialization_blobs_are_not_implicitly_copied:true}};
  sync.surface_digest=jsonDigest({format:'kristal.github-read-surface/1.0',slug,state_ref:sync.state_ref,state_logical_commitment:commitment,entrypoint:sync.entrypoint,files:all,materialization_objects:[]});
  const rows=[{slug,title:'Demo v10',path:prefix,entrypoint:`${prefix}/AI_START_HERE.md`,state_ref:sync.state_ref,state_logical_commitment:commitment,surface_digest:sync.surface_digest,file_count:all.length,total_bytes:sync.total_bytes,materialization_object_count:0}];
  const index={format:'kristal.github-collection-index/1.0',kristals:rows,count:1,index_digest:jsonDigest({format:'kristal.github-collection-index/1.0',kristals:rows})};
  mkfile(root,`${prefix}/.kristal/sync-manifest.json`,JSON.stringify(sync));
  mkfile(root,'kristals/index.json',JSON.stringify(index));
  return {root,slug,prefix,files,sync,index};
}
const inspect=(o)=>inspectGithubKristal({directory:o.root,kristal:o.slug},'.');

test('v10: collection index, byte digests and derived operational navigation',t=>{
  const o=fixture(t);
  assert.equal(listGithubKristals({directory:o.root},'.')[0].id,'demo');
  const verified=inspect(o);
  assert.equal(verified.checks.byteDigestsVerified,true);
  assert.equal(verified.checks.semanticCommitmentVerified,false);
  const pack=loadGithubKristal({directory:o.root,kristal:o.slug},'.');
  assert.equal(pack.synthetic,true);
  assert.equal(pack.assertions.length,o.files.size+1);
  assert(pack.assertions.every(x=>x.status==='unspecified'&&x.validationStatus==='not_evaluated'));
  assert.equal(pack.integration.viewKind,'derived-hosting-navigation');
});
test('v10: refuses tampered byte contents, no trust by filename',t=>{
  const o=fixture(t);mkfile(o.root,`${o.prefix}/AI_START_HERE.md`,'# Evil\n');
  assert.throws(()=>inspect(o),{code:'V10_CONTRACT_INVALID'});
});
test('v10: refuses index digest mismatch',t=>{
  const o=fixture(t); o.index.kristals[0].title='forged';
  assert.throws(()=>verifyCollectionIndex(o.index),{code:'V10_CONTRACT_INVALID'});
});
test('v10: refuses unmanaged file or symlink',t=>{
  const o=fixture(t);mkfile(o.root,`${o.prefix}/rogue.json`,'{}');
  assert.throws(()=>inspect(o),{code:'V10_CONTRACT_INVALID'});
  fs.rmSync(path.join(o.root,o.prefix,'rogue.json'));
  try { fs.symlinkSync(path.join(o.root,o.prefix,'AI_START_HERE.md'),path.join(o.root,o.prefix,'rogue.json')); }
  catch { return; }
  assert.throws(()=>inspect(o),{code:'V10_CONTRACT_INVALID'});
});
test('v10: refuses budget exhaustion and missing required files',t=>{
  const o=fixture(t);
  assert.throws(()=>inspectGithubKristal({directory:o.root,kristal:'demo',maxFiles:2},'.'),{code:'V10_CONTRACT_INVALID'});
  fs.rmSync(path.join(o.root,o.prefix,'ai/INDEX.json'));
  assert.throws(()=>inspect(o),{code:'V10_FILE_MISSING'});
});
test('v10: refuses manifest/index disagreement, even with file digests unchanged',t=>{
  const o=fixture(t);o.sync.surface_digest='sha256:'+'0'.repeat(64);
  mkfile(o.root,`${o.prefix}/.kristal/sync-manifest.json`,JSON.stringify(o.sync));
  assert.throws(()=>inspect(o),{code:'V10_CONTRACT_INVALID'});
});
test('v10: rejects malicious relative paths in declared files',t=>{
  const o=fixture(t);o.sync.files[0].path='../secrets.txt';
  mkfile(o.root,`${o.prefix}/.kristal/sync-manifest.json`,JSON.stringify(o.sync));
  assert.throws(()=>inspect(o),{code:'V10_CONTRACT_INVALID'});
});
