import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { MANAGER_LOCAL_FORMAT, MANAGER_POLICY_FORMAT, validateManagerInventory,
  validateManagerAccessPolicy, projectManagerInventory } from '../server/integrations/manager-adapter.mjs';
import { projectKitDiscovery, validateDiscoveryCatalog, enrichAuthorizedFleet,
  AUTHORITY, DISCOVERY_FORMAT } from '../server/integrations/discovery.mjs';
import { readFleetExport, readDiscoveryCatalog, fleetForPrincipal } from '../server/integrations/fleet.mjs';
import { loadConfig } from '../server/config.mjs';
const digest = 'sha256:'+'a'.repeat(64);
const sfp = 'sha256:'+'b'.repeat(64);
const raw = (records) => ({format:MANAGER_LOCAL_FORMAT,mode:'local-read-only',semantic_authority:false,
  validated_domain_facts:false, generated_at:'2026-10-13T00:00:00Z',identity_rule:'state_ref is the identity; slug is not authoritative',
  record_count:records.length,records,warnings:[]});
const record = (overrides={}) => ({title:'Sensitive Sample', slug:'private-sample',
  state_ref:'urn:kristal:state:sample',state_commitment:digest, readiness:'READY',
  availability:'local',qualification:'NOT_ESTABLISHED', publication:'NOT_ESTABLISHED', archetype:'UNDECLARED', ...overrides});
const grant = (overrides={}) => ({state_ref:'urn:kristal:state:sample',state_commitment:digest,
  allowed_principals:['alice'],allowed_roles:[],...overrides});
const policy = (grants) => ({format:MANAGER_POLICY_FORMAT,grants});
const principal = {id:'alice',roles:[],scopes:['read']};
const kit = () => ({format:'kristal.discovery/1.0', state_ref:'urn:kristal:state:sample',
  authority:AUTHORITY, source_fingerprint:sfp,
  classification:{primary_archetype:'ARK-08',primary_usage:'PRF-15',domain:'automotive'},
  data_layout:{organization:'segmented',inventory_ref:'derived/reader-inventory.json'},
  reader:{profile:'kristal.reader/causal-graph-v1',hints_ref:'derived/reader-profile.json'},
  size:{class:'small',tracked_local_bytes:2201,completeness:'measured_referenced_local_files'}});
const kitProfile = () => ({format:'kristal.reader-profile/1.0',state_ref:'urn:kristal:state:sample',
  source_fingerprint:sfp, configuration_status:'advisory_only',access_pattern:'selective'});

test('Manager candidate inventory is supported only through exact operator ACL and identity',()=>{
  const rows = validateManagerInventory(raw([record()]));
  const projected = projectManagerInventory(rows, validateManagerAccessPolicy(policy([grant()])));
  assert.equal(projected.length,1);
  assert.equal(projected[0].readiness,'not_checked');
  assert.equal(projected[0].availability,'available');
  assert.equal(projected[0].archetype,undefined);
  assert.deepEqual(fleetForPrincipal(principal,projected).items[0].openable,false);
  assert.equal(fleetForPrincipal({id:'bob',roles:[],scopes:['read']},projected).items.length,0);
  assert.equal(projectManagerInventory(rows,validateManagerAccessPolicy(policy([grant({state_commitment:'sha256:'+'f'.repeat(64)})]))).length,0);
  assert.equal(projectManagerInventory(rows,validateManagerAccessPolicy(policy([]))).length,0);
});

test('Manager export fails closed for local paths, malformed claims, collision and duplicate grants',()=>{
  for (const r of [record({local_path:'C:/private'}),record({state_commitment:'bad'})])
    assert.throws(()=>validateManagerInventory(raw([r])),{code:'FLEET_EXPORT_INVALID'});
  assert.throws(()=>validateManagerInventory({...raw([record()]),record_count:9}),{code:'FLEET_EXPORT_INVALID'});
  assert.throws(()=>validateManagerAccessPolicy(policy([grant(),grant()])),{code:'FLEET_POLICY_INVALID'});
  const duplicate=validateManagerInventory(raw([record(),record({title:'different',slug:'other'})]));
  assert.equal(projectManagerInventory(duplicate, [grant()]).length,0);
  assert.equal(projectManagerInventory(validateManagerInventory(raw([record({identity_collision:true})])),[grant()]).length,0);
});

test('Raw Manager requires policy file, no implicit default access', t=>{
  const dir=fs.mkdtempSync(path.join(os.tmpdir(),'konstellation-manager-'));
  t.after(()=>fs.rmSync(dir,{recursive:true,force:true}));
  const inv=path.join(dir,'inventory.json'); const acl=path.join(dir,'policy.json');
  fs.writeFileSync(inv,JSON.stringify(raw([record()])));
  assert.throws(()=>readFleetExport(inv),{code:'FLEET_POLICY_REQUIRED'});
  fs.writeFileSync(acl,JSON.stringify(policy([grant()])));
  assert.equal(readFleetExport(inv,acl).length,1);
  fs.writeFileSync(acl,JSON.stringify(policy([grant({allowed_principals:[]})])));
  assert.equal(readFleetExport(inv,acl).length,0);
});

test('Authoring Kit Discovery 3.3 becomes advisory sanitized local projection only',()=>{
  const derived=projectKitDiscovery(kit(),kitProfile());
  assert.equal(derived.size_class,'small');
  assert.equal(projectKitDiscovery({...kit(),classification:{organization:'single', secondary_usages:['PRF-06'], arketype_origin_slug:'arketype-08', classification_source:'arketype.instance.json-unverified'}}).classification.classification_source, 'arketype.instance.json-unverified');
  const cat=validateDiscoveryCatalog({format:DISCOVERY_FORMAT,entries:[derived]});
  const own = {source:'local_manager_preview',stateRef:derived.state_ref,title:'Accessible'};
  const hosted={source:'github_v10_checkout',stateRef:derived.state_ref,title:'Hosted'};
  const enriched=enrichAuthorizedFleet([own,hosted],cat);
  assert.equal(enriched[0].discovery.classification.primary_usage,'PRF-15');
  assert.equal(enriched[0].discovery.verification,'declared_noncanonical');
  assert.equal(enriched[1].discovery,undefined);
  assert.throws(()=>projectKitDiscovery({...kit(),authority:'published'},kitProfile()),{code:'DISCOVERY_INVALID'});
  assert.throws(()=>projectKitDiscovery(kit(),{...kitProfile(),source_fingerprint:'sha256:'+'e'.repeat(64)}),{code:'DISCOVERY_INVALID'});
  assert.throws(()=>validateDiscoveryCatalog({format:DISCOVERY_FORMAT,entries:[derived,derived]}),{code:'DISCOVERY_INVALID'});
  assert.throws(()=>validateDiscoveryCatalog({format:DISCOVERY_FORMAT,entries:[{...derived,local_path:'/secret'}]}),{code:'DISCOVERY_INVALID'});
});

test('Discovery catalog read is explicit, bounded, and no symlink is followed', t=>{
  const dir=fs.mkdtempSync(path.join(os.tmpdir(),'konstellation-discovery-'));
  t.after(()=>fs.rmSync(dir,{recursive:true,force:true}));
  const file=path.join(dir,'catalog.json');
  fs.writeFileSync(file,JSON.stringify({format:DISCOVERY_FORMAT,entries:[projectKitDiscovery(kit())]}));
  assert.equal(readDiscoveryCatalog(file).length,1);
  assert.deepEqual(readDiscoveryCatalog(null),[]);
  const alias=path.join(dir,'alias.json');
  try {fs.symlinkSync(file,alias); assert.throws(()=>readDiscoveryCatalog(alias),{code:'FLEET_EXPORT_INVALID'});}
  catch(e) {if(e.code !== 'EPERM') throw e;}
});

test('My Kristals refuses non-loopback serving and all nonlocal profiles',()=>{
  const flags={KONSTELLATION_ENABLE_MY_KRISTALS:'true',KONSTELLATION_FLEET_EXPORT:'abc',
    KONSTELLATION_FLEET_POLICY:'xyz',KONSTELLATION_DISCOVERY_CATALOG:'123'};
  assert.equal(loadConfig({...flags,HOST:'0.0.0.0'}).fleetEnabled,false);
  assert.equal(loadConfig({...flags,HOST:'127.0.0.1'}).fleetEnabled,true);
  const pub=loadConfig({...flags,KONSTELLATION_DEPLOYMENT_PROFILE:'public',KONSTELLATION_ANONYMOUS_READONLY:'true'});
  assert.equal(pub.fleetEnabled,false);
  assert.equal(pub.fleetPolicyFile,null);
  assert.equal(pub.fleetDiscoveryFile,null);
});


test('Manager alpha.14 operational report is sanitized, scoped and never elevates readiness',()=>{
  const alpha14=record({
    discovery:{status:'stale',issues:['size changed: /home/private/important.json'],classification:{primary_archetype:'ARK-08'}},
    operational_result:'ATTENTION_REQUIRED',framework_state_verification:'VERIFIED',
  });
  const projected=projectManagerInventory(validateManagerInventory(raw([alpha14])),validateManagerAccessPolicy(policy([grant()])));
  assert.equal(projected[0].readiness,'not_checked');
  assert.deepEqual({o:projected[0].operational_result,d:projected[0].discovery_status,f:projected[0].framework_state_verification},
    {o:'ATTENTION_REQUIRED',d:'stale',f:'VERIFIED'});
  const entries=fleetForPrincipal(principal,projected).items;
  assert.equal(entries[0].openable,false);
  assert.equal(entries[0].managerAssessment.authority,'operational_observation_only');
  assert.equal(JSON.stringify(entries).includes('/home/private'),false);
  assert.equal(fleetForPrincipal({id:'bob',roles:[],scopes:['read']},projected).items.length,0);
  assert.throws(()=>validateManagerInventory(raw([record({operational_result:'APPROVED'})])),{code:'FLEET_EXPORT_INVALID'});
});


test('Explicit local v10 reader is selectable but is not merged with Manager evidence',()=>{
  const reader={source:'kristal-local-v10',items:[{id:'local-v10',label:'Fixture',stateRef:'urn:kristal:state:sample',available:true}]};
  const local=projectManagerInventory(validateManagerInventory(raw([record({operational_result:'LOCAL_STRUCTURE_ONLY'})])),[grant()]);
  const view=fleetForPrincipal(principal,local,reader).items;
  assert.equal(view.length,2);
  const configured=view.find(item=>item.source==='local_v10_reader');
  assert.equal(configured.openable,true);
  assert.equal(configured.verification,'checked_on_open');
  assert.equal(configured.managerAssessment,undefined);
  assert.equal(view.find(item=>item.source==='local_manager_preview').openable,false);
});
