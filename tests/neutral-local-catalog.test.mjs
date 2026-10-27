import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { listLocalCatalog, loadLocalCatalog, loadNeutralCatalog } from '../server/integrations/local-catalog.mjs';

function fixture(t) {
  const root=fs.mkdtempSync(path.join(os.tmpdir(),'konstellation-selector-'));
  t.after(()=>fs.rmSync(root,{recursive:true,force:true}));
  const locals=path.join(root,'locals');fs.mkdirSync(locals);
  const create=(folder,title,valid=true)=>{
    const dir=path.join(locals,folder); fs.mkdirSync(dir);
    fs.writeFileSync(path.join(dir,'kristal.workspace.json'),JSON.stringify({format:'kristal.local-workspace/3.2.0',title,state_ref:'urn:kristal:state:'+folder}));
    if (valid) {
      const state={schema_version:'9.0',artifact_type:'kristal_state_snapshot',state_ref:'urn:kristal:state:'+folder,
        logical_commitment:{profile:'kristal.state-commitment/jcs-sha256-v1',digest:'sha256:'+'0'.repeat(64)},
        members:[],references:[]};
      fs.mkdirSync(path.join(dir,'state'));fs.writeFileSync(path.join(dir,'state/state-snapshot.json'),JSON.stringify(state));
    }
    return dir;
  };
  const old={...process.env};
  t.after(()=>{for(const k of Object.keys(process.env)) if(!(k in old)) delete process.env[k]; for(const [k,v] of Object.entries(old)) process.env[k]=v;});
  process.env.KONSTELLATION_DEPLOYMENT_PROFILE='local';process.env.HOST='127.0.0.1';
  delete process.env.KONSTELLATION_ANONYMOUS_READONLY;delete process.env.KONSTELLATION_PUBLIC_READONLY;
  return {root,locals,create};
}
test('a neutral catalogue lists direct local Kristals, and never preselects or reads one',t=>{
  const {locals,create}=fixture(t);create('A-Kristal-Catho','Kristal-Catho');create('A-Kristal-Test','Test');
  create('Unsupported','Unsupported',false);
  fs.mkdirSync(path.join(locals,'not-a-kristal'));
  const cfg={directory:locals};
  const items=listLocalCatalog(cfg,'.');
  assert.deepEqual(items.filter(x=>x.available).map(x=>x.id),['A-Kristal-Catho','A-Kristal-Test']);
  assert.equal(items.find(x=>x.id==='Unsupported')?.available,false);
  assert.equal(items.find(x=>x.id==='not-a-kristal'),undefined);
  assert.equal(loadLocalCatalog(cfg,'.','A-Kristal-Test').integration.adapter,'kristal-local-v10');
  assert.throws(()=>loadLocalCatalog(cfg,'.','../secret'),{code:'KRISTAL_NOT_FOUND'});
});
test('catalogue refuses nonlocal service and skips symlinks',t=>{
  const {locals,create}=fixture(t);const target=create('A-Kristal-Test','Test');
  try {fs.symlinkSync(target,path.join(locals,'Alias'),'dir');} catch {};
  assert(!listLocalCatalog({directory:locals},'.').some(x=>x.id==='Alias'));
  process.env.KONSTELLATION_DEPLOYMENT_PROFILE='public';
  assert.throws(()=>listLocalCatalog({directory:locals},'.'),{code:'INVALID_CONFIG'});
});
test('neutral pack has no canonical statements or preselected Kristal',()=>{
  const pack=loadNeutralCatalog(path.resolve('config'));
  assert.equal(pack.integration.selectionRequired,true);
  assert.equal(pack.assertions.length,0);
  assert(!JSON.stringify(pack).includes('Catho'));
});

test('catalogue accepts the default private local session when profile env is absent',t=>{
  const {locals,create}=fixture(t);create('A-Kristal-Catho','Kristal-Catho');
  delete process.env.KONSTELLATION_DEPLOYMENT_PROFILE;
  delete process.env.HOST;
  assert.deepEqual(listLocalCatalog({directory:locals},'.').filter(x=>x.available).map(x=>x.id),['A-Kristal-Catho']);
  assert.equal(loadLocalCatalog({directory:locals},'.','A-Kristal-Catho').integration.adapter,'kristal-local-v10');
});
test('catalogue refuses public-readonly mode and non-loopback local listener',t=>{
  const {locals,create}=fixture(t);create('A-Kristal-Catho','Kristal-Catho');
  process.env.KONSTELLATION_ANONYMOUS_READONLY='true';
  assert.throws(()=>listLocalCatalog({directory:locals},'.'),{code:'INVALID_CONFIG'});
  delete process.env.KONSTELLATION_ANONYMOUS_READONLY;
  process.env.HOST='0.0.0.0';
  assert.throws(()=>listLocalCatalog({directory:locals},'.'),{code:'INVALID_CONFIG'});
  process.env.HOST='127.0.0.1';
  process.env.KONSTELLATION_PUBLIC_READONLY='true';
  assert.throws(()=>listLocalCatalog({directory:locals},'.'),{code:'INVALID_CONFIG'});
});
