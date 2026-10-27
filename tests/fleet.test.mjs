import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { readFleetExport, fleetForPrincipal, validateFleetExport, FLEET_PREVIEW_FORMAT } from '../server/integrations/fleet.mjs';
import { loadConfig } from '../server/config.mjs';

const authorized = {id:'alice',roles:['researcher'],scopes:['read']};
const unauthorized = {id:'bob',roles:['public'],scopes:['read']};
const item = (id, overrides={}) => ({id,title:`Test ${id}`,visibility:'private',readiness:'not_checked',availability:'unknown',allowed_principals:['alice'],allowed_roles:[], ...overrides});
const doc = (entries) => ({format:FLEET_PREVIEW_FORMAT,entries});

test('fleet preview requires explicit format, unique IDs, bounded safe attributes', () => {
  assert.equal(validateFleetExport(doc([item('A')])).length,1);
  for(const bad of [
    doc([item('A'),item('A')]), doc([item('A',{state_commitment:'wrong'})]),
    doc([item('A',{title:'Invalid\nnew line'})]),doc([item('A',{path:'C:/private'})]),
    doc([item('A',{readiness:'published'})]),doc([item('A',{allowed_roles:null})]),
    doc([item('A',{state_ref:'x'.repeat(513)})]),
    doc([item('A',{availability:'missing'})]),
    {format:'kristal-local-registry/2.0', entries:[item('A')]},
    doc(Array.from({length:1001},(_,i)=>item(`i${i}`))),
  ]) assert.throws(()=>validateFleetExport(bad),{code:'FLEET_EXPORT_INVALID'});
});

test('principal filters entries before counts/facets; no unauthorized data leaks', () => {
  const entries = validateFleetExport(doc([
    item('visible',{state_ref:'urn:kristal:state:visible'}),
    item('hidden',{title:'Hidden Confidential Domain',allowed_principals:['charlie']}),
    item('via-role',{allowed_principals:[],allowed_roles:['researcher']}),
  ]));
  const a = fleetForPrincipal(authorized,entries);
  const b = fleetForPrincipal(unauthorized,entries);
  assert.equal(a.items.length,2);
  assert.equal(b.items.length,0);
  assert(!JSON.stringify(a).includes('Hidden Confidential Domain'));
  assert(!JSON.stringify(b).includes('Hidden Confidential Domain'));
  assert.deepEqual(Object.keys(a.items[0]).includes('allowed_principals'),false);
  assert.throws(()=>fleetForPrincipal({id:'eve',roles:[],scopes:[]},entries),{code:'ACCESS_DENIED'});
});

test('same slug and state_ref in local and hosted remain separate observations',()=>{
  const ref='urn:kristal:state:demo';
  const entries=validateFleetExport(doc([item('demo',{state_ref:ref})]));
  const result=fleetForPrincipal(authorized,entries,{source:'kristal-github-collection-v10',items:[{id:'demo',label:'Test demo',available:true,stateRef:ref,stateCommitment:'sha256:'+'e'.repeat(64)}]});
  assert.equal(result.items.length,2);
  const local=result.items.find(x=>x.source==='local_manager_preview');
  const host=result.items.find(x=>x.source==='github_v10_checkout');
  assert.equal(local.openable,false);
  assert.equal(local.verification,'declared_only');
  assert.equal(host.openable,true);
  assert.equal(host.verification,'index_only');
  assert.equal(host.viewKind,'technical_hosting');
  assert.notEqual(local.key,host.key);
});

test('failed hosted record stays unavailable, never reported ready or published',()=>{
  const result=fleetForPrincipal(authorized,[],{source:'kristal-github-collection-v10',items:[{id:'offline',label:'Offline',available:false,reason:'secret absolute path'}]});
  assert.equal(result.items[0].availability,'unavailable');
  assert.equal(result.items[0].readiness,'unknown');
  assert(!('readerId' in result.items[0]));
  assert(!JSON.stringify(result).includes('secret absolute path'));
});

test('file loader accepts only explicit regular 1 MiB bounded export, no symlinks',t=>{
  const dir=fs.mkdtempSync(path.join(os.tmpdir(),'fleet-preview-'));
  t.after(()=>fs.rmSync(dir,{recursive:true,force:true}));
  const file=path.join(dir,'authorized.json');
  fs.writeFileSync(file,JSON.stringify(doc([item('A')])));
  assert.equal(readFleetExport(file).length,1);
  const alias=path.join(dir,'alias.json');
  try { fs.symlinkSync(file,alias);assert.throws(()=>readFleetExport(alias),{code:'FLEET_EXPORT_INVALID'}); }catch(e){if(e.code!=='EPERM')throw e;}
  fs.writeFileSync(file,' '.repeat(1024*1024+1));
  assert.throws(()=>readFleetExport(file),{code:'FLEET_EXPORT_INVALID'});
  fs.writeFileSync(file,'{');
  assert.throws(()=>readFleetExport(file),{code:'FLEET_EXPORT_INVALID'});
  assert.throws(()=>readFleetExport(path.join(dir,'missing.json')),{code:'FLEET_EXPORT_UNAVAILABLE'});
  assert.deepEqual(readFleetExport(''),[]);
});

test('opt-in only on the local deployment profile, never on public or LAN',()=>{
  const env={KONSTELLATION_ENABLE_MY_KRISTALS:'true',KONSTELLATION_FLEET_EXPORT:'/private/test.json'};
  assert.equal(loadConfig(env).fleetEnabled,true);
  const pub=loadConfig({...env,KONSTELLATION_DEPLOYMENT_PROFILE:'public',KONSTELLATION_ANONYMOUS_READONLY:'true'});
  assert.equal(pub.fleetEnabled,false);
  assert.equal(pub.fleetExportFile,null);
  const lan=loadConfig({...env,KONSTELLATION_DEPLOYMENT_PROFILE:'lan',KONSTELLATION_ANONYMOUS_READONLY:'true'});
  assert.equal(lan.fleetEnabled,false);
});
