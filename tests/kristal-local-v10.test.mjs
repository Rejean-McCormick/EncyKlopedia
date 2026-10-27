import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { createHash } from 'node:crypto';
import { inspectLocalV10, loadLocalV10, listLocalV10 } from '../server/integrations/kristal-local-v10.mjs';

const sha = b => createHash('sha256').update(b).digest('hex');
const ref='urn:kristal:state:fixture';
function fixture(t,{withGraph=false}={}){
  const root=fs.mkdtempSync(path.join(os.tmpdir(),'konstellation-v9-'));
  t.after(()=>fs.rmSync(root,{recursive:true,force:true}));
  const put=(file,obj)=>{
    const filename=path.join(root,file);fs.mkdirSync(path.dirname(filename),{recursive:true});
    fs.writeFileSync(filename,JSON.stringify(obj));
  };
  const workspace={format:'kristal.local-workspace/3.2.0',title:'Fixture',state_ref:ref};
  const state={schema_version:'9.0',artifact_type:'kristal_state_snapshot',state_ref:ref,
    logical_commitment:{profile:'kristal.state-commitment/jcs-sha256-v1',digest:'sha256:'+'1'.repeat(64)},
    members:[{artifact_id:'urn:fixture:one',logical_contract:{id:'fixture',version:'1.0'},
      logical_commitment:{profile:'kristal.logical/jcs-sha256-v1',digest:'sha256:'+'2'.repeat(64)}}],references:[]};
  put('kristal.workspace.json',workspace);
  put('build/v9/state-snapshot.json',state);
  const cfg={directory:root};
  if(withGraph){
    put('canon/domain/test.json',{record:'source'});
    const contents=fs.readFileSync(path.join(root,'canon/domain/test.json'));
    put('derived/test/manifest.json',{noncanonical:true,rebuildable:true,
      canonical_input_sha256:{'canon/domain/test.json':sha(contents)},counts:{nodes:2,edges:1}});
    put('derived/test/nodes.json',[{id:'urn:a',kind:'thing',label:'One'},{id:'urn:b',kind:'thing',label:'Two'}]);
    put('derived/test/edges.json',[{id:'e:1',from:'urn:a',to:'urn:b',kind:'proposed-match',predicate:'candidate_identity_match',evidence:{accepted:false}}]);
    cfg.readModel={type:'node-edge-json/1',manifest:'derived/test/manifest.json',nodes:'derived/test/nodes.json',edges:'derived/test/edges.json'};
  }
  return {root,cfg,put};
}
test('v9 generic reader navigates declared members without inventing canonical authority',t=>{
  const {root,cfg}=fixture(t);
  const {discovery}=inspectLocalV10(cfg,root);
  assert.equal(discovery.status,'absent');
  const pack=loadLocalV10(cfg,root);
  assert.equal(pack.assertions.length,1);
  assert.equal(pack.integration.checks.canonicalCommitmentVerified,false);
  assert.equal(pack.integration.viewKind,'v9-declared-topology');
  assert.deepEqual(listLocalV10(cfg,root).map(x=>x.id),['local-v10']);
});
test('v9 derived graph keeps candidate identity as unvalidated edge with original evidence',t=>{
  const {root,cfg}=fixture(t,{withGraph:true});
  const pack=loadLocalV10(cfg,root);
  assert.equal(pack.integration.viewKind,'derived-node-edge-graph');
  assert.equal(pack.entities.length,4);
  assert.equal(pack.assertions.length,4);
  const edge=pack.assertions.find(x=>x.originalPredicate==='candidate_identity_match');
  assert(edge);
  assert.equal(edge.status,'unspecified');
  assert.equal(edge.originalEvidence.accepted,false);
  assert.equal(pack.integration.checks.canonicalInputsMatched,true);
});
test('modified canonical input causes derived read model to be refused',t=>{
  const {root,cfg,put}=fixture(t,{withGraph:true});
  put('canon/domain/test.json',{record:'tampered'});
  assert.throws(()=>loadLocalV10(cfg,root),{code:'KRISTAL_LOCAL_INVALID'});
});
test('discovery mismatch does not allow specializations and does not block generic read',t=>{
  const {root,cfg,put}=fixture(t);
  const source='sha256:'+'c'.repeat(64);
  const statePath='build/v9/state-snapshot.json';
  const stat=fs.statSync(path.join(root,statePath));
  put('kristal.discovery.json',{format:'kristal.discovery/1.0',state_ref:ref,source_fingerprint:source,
    authority:'noncanonical_derived_metadata_not_access_or_publication_authority',
    data_layout:{inventory_ref:'derived/reader-inventory.json'},reader:{hints_ref:'derived/reader-profile.json'}});
  put('derived/reader-inventory.json',{format:'kristal.reader-inventory/1.0',state_ref:ref,
    source_fingerprint:source,files:[{path:statePath,size_bytes:stat.size+1,sha256:'sha256:'+'f'.repeat(64)}]});
  put('derived/reader-profile.json',{format:'kristal.reader-profile/1.0',state_ref:ref,
    source_fingerprint:source,configuration_status:'advisory_only',artifact_strategies:[{path:statePath,size_bytes_measured:stat.size+1,must_verify_digest:'sha256:'+'f'.repeat(64)}]});
  assert.equal(inspectLocalV10(cfg,root).discovery.status,'stale');
  assert.equal(loadLocalV10(cfg,root).integration.readerHintsUsed,false);
});
test('local reader refuses path traversal and nonlocal deployment',t=>{
  const {root,cfg}=fixture(t);
  assert.throws(()=>loadLocalV10({...cfg,state:'../secrets.json'},root),{code:'KRISTAL_LOCAL_INVALID'});
  const before=process.env.KONSTELLATION_DEPLOYMENT_PROFILE;
  try{
    process.env.KONSTELLATION_DEPLOYMENT_PROFILE='public';
    assert.throws(()=>loadLocalV10(cfg,root),{code:'KRISTAL_LOCAL_INVALID'});
  }finally{
    if(before===undefined)delete process.env.KONSTELLATION_DEPLOYMENT_PROFILE;
    else process.env.KONSTELLATION_DEPLOYMENT_PROFILE=before;
  }
});


test('v10 local reader prefers portable state export and refuses conflicting v9 build',t=>{
  const {root,cfg,put}=fixture(t);
  const current=JSON.parse(fs.readFileSync(path.join(root,'build/v9/state-snapshot.json')));
  put('state/state-snapshot.json',current);
  assert.equal(inspectLocalV10(cfg,root).statePath,'state/state-snapshot.json');
  put('build/v9/state-snapshot.json',{...current,state_ref:'urn:kristal:state:another'});
  assert.throws(()=>inspectLocalV10(cfg,root),{code:'KRISTAL_LOCAL_INVALID'});
});


test('valid Discovery reader inventory opens without unbound status variables', t=>{
  const {root,cfg,put}=fixture(t);
  const statePath='build/v9/state-snapshot.json';
  const data=fs.readFileSync(path.join(root,statePath));
  const fullSha='sha256:'+sha(data);
  const finger='sha256:'+'c'.repeat(64);
  put('kristal.discovery.json',{format:'kristal.discovery/1.0',state_ref:ref,source_fingerprint:finger,
    authority:'noncanonical_derived_metadata_not_access_or_publication_authority',
    data_layout:{inventory_ref:'derived/reader-inventory.json'},reader:{hints_ref:'derived/reader-profile.json'}});
  put('derived/reader-inventory.json',{format:'kristal.reader-inventory/1.0',state_ref:ref,
    source_fingerprint:finger,files:[{path:statePath,size_bytes:data.length,sha256:fullSha}]});
  put('derived/reader-profile.json',{format:'kristal.reader-profile/1.0',state_ref:ref,
    source_fingerprint:finger,configuration_status:'advisory_only',
    artifact_strategies:[{path:statePath,size_bytes_measured:data.length,must_verify_digest:fullSha}]});
  const pack=loadLocalV10(cfg,root);
  assert.equal(pack.integration.checks.discoveryStatus,'bounded_files_checked_not_kit_freshness');
  assert.equal(pack.entities.length,2);
  assert.equal(pack.integration.readerHintsUsed,false);
});

test('local graph presentation opens meaningful kind before technical state, without changing epistemic status',t=>{
  const {root,cfg,put}=fixture(t,{withGraph:true});
  put('derived/test/nodes.json',[
    {id:'urn:a',kind:'catho_person',label:'Personne A'},
    {id:'urn:b',kind:'wikidata_work',label:'Œuvre B'},
  ]);
  // Existing derived manifest remains correct: same node count, edges unchanged.
  cfg.readModel.presentation={preferredKind:'catho_person',
    kindLabels:{catho_person:'Personnes',wikidata_work:'Œuvres'},
    predicateLabels:{candidate_identity_match:'Correspondance candidate (non vérifiée)'}};
  const pack=loadLocalV10(cfg,root);
  assert.equal(pack.synthetic,false);
  assert.deepEqual(pack.registry.entityTypes.slice(0,2),['catho_person','wikidata_work']);
  assert.equal(pack.integration.presentation.typeLabels.catho_person,'Personnes');
  assert.equal(pack.integration.presentation.typeLabels.wikidata_work,'Œuvres');
  const edge=pack.assertions.find(a=>a.originalPredicate==='candidate_identity_match');
  assert(edge);
  assert.equal(edge.status,'unspecified');
  assert.equal(edge.originalEvidence.accepted,false);
  const definition=pack.registry.relations.find(r=>r.id===edge.relation);
  assert.equal(definition.range,'wikidata_work');
  assert(definition.domain.includes('catho_person'));
  assert.equal(definition.label.fr,'Correspondance candidate (non vérifiée)');
});

test('local graph presentation cannot invent kinds or relabel unknown predicates',t=>{
  const {root,cfg}=fixture(t,{withGraph:true});
  cfg.readModel.presentation={preferredKind:'invented'};
  assert.throws(()=>loadLocalV10(cfg,root),{code:'KRISTAL_LOCAL_INVALID'});
  cfg.readModel.presentation={kindLabels:{invented:'Inventé'}};
  assert.throws(()=>loadLocalV10(cfg,root),{code:'KRISTAL_LOCAL_INVALID'});
});

test('graphs with more than ten source kinds keep all relations without violating domain cardinality',t=>{
  const {root,cfg,put}=fixture(t,{withGraph:true});
  const kinds=Array.from({length:13},(_,i)=>`source_kind_${String(i+1).padStart(2,'0')}`);
  const nodes=kinds.map((kind,i)=>({id:`urn:kind:${i}`,kind,label:`Kind ${i}`}));
  nodes.push({id:'urn:target',kind:'target_kind',label:'Target'});
  const edges=kinds.map((kind,i)=>({id:`edge:${i}`,from:`urn:kind:${i}`,to:'urn:target',
    predicate:'shared_predicate',kind:'derived',evidence:{validated:false}}));
  put('derived/test/nodes.json',nodes);
  put('derived/test/edges.json',edges);
  const manifest=JSON.parse(fs.readFileSync(path.join(root,'derived/test/manifest.json')));
  put('derived/test/manifest.json',{...manifest,counts:{nodes:nodes.length,edges:edges.length}});
  const pack=loadLocalV10(cfg,root);
  assert.equal(pack.entities.length,nodes.length+2); // v9 state + one artifact
  assert.equal(pack.assertions.length,1+nodes.length+edges.length);
  assert(pack.registry.relations.every(r=>r.domain.length>=1 && r.domain.length<=10));
  const relations=new Map(pack.registry.relations.map(r=>[r.id,r]));
  const entities=new Map(pack.entities.map(e=>[e.id,e]));
  for(const assertion of pack.assertions){
    const rel=relations.get(assertion.relation);
    assert(rel,`Missing relation ${assertion.relation}`);
    assert(rel.domain.includes(entities.get(assertion.subject).type),`Domain mismatch ${assertion.relation}`);
    if(rel.valueKind==='entity') assert.equal(entities.get(assertion.value).type,rel.range);
  }
  assert.equal(pack.assertions.filter(a=>a.originalPredicate==='shared_predicate').length,13);
});
