import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { AdmissionPipeline, canonicalize, requestFingerprint, semanticProjection } from '../dist/index.js';
const here=path.dirname(fileURLToPath(import.meta.url));
const repo=path.resolve(here,'../../..');
function removePointer(doc,pointer){const parts=pointer.slice(1).split('/').map(x=>x.replaceAll('~1','/').replaceAll('~0','~'));let parent=doc;for(let i=0;i<parts.length-1;i++)parent=Array.isArray(parent)?parent[Number(parts[i])]:parent[parts[i]];const last=parts.at(-1);if(Array.isArray(parent))parent.splice(Number(last),1);else delete parent[last];}
const jcs=JSON.parse(fs.readFileSync(path.join(repo,'tck/jcs/vectors.json'),'utf8'));
for(const v of jcs.vectors){const input=structuredClone(v.input);for(const p of (v.content_boundary?.exclude_json_pointers??[]))removePointer(input,p);assert.equal(canonicalize(input),v.expected_canonical,v.id);}
const fp=JSON.parse(fs.readFileSync(path.join(repo,'tck/fingerprint/vectors.json'),'utf8'));
for(const v of fp.vectors){assert.deepEqual(semanticProjection(v.envelope),v.expected_projection,v.id);assert.equal(await requestFingerprint(v.envelope),v.expected_fingerprint,v.id);}
const base=structuredClone(fp.vectors[0].envelope);const changed={...base,id:'different-id',time:'2030-01-01T00:00:00Z',correlation_id:'different',trace:{traceparent:'00-abc',tracestate:null}};assert.equal(await requestFingerprint(base),await requestFingerprint(changed));

const profile={id:'governance.decision.execute',version:'1.0.0',class:'command',source_systems:['konnaxion'],target_systems:['orgo'],delivery:{durability:'durable',idempotency:'required',ordering:'subject'},authority:{required:true,accepted_kinds:['governance-mandate']}};
const memory=new Map();
const pipeline=new AdmissionPipeline({validatePayload(){}},{authenticate(){return 'principal:test';}},{authorize(){}},{lookup(scope,key){return memory.get(`${scope}|${key}`);},reserve(scope,key,record){memory.set(`${scope}|${key}`,record);}});
const admitted=structuredClone(fp.vectors[0].envelope);
assert.equal((await pipeline.admit(admitted,profile,{})).replay,false);
assert.equal((await pipeline.admit(admitted,profile,{})).replay,true);
const divergent=structuredClone(admitted); divergent.data.decision_revision='rev-4';
await assert.rejects(()=>pipeline.admit(divergent,profile,{}),e=>e.code==='IK_IDEMPOTENCY_CONFLICT');

console.log(`PASS JCS=${jcs.vectors.length} fingerprint=${fp.vectors.length} admission=3`);
