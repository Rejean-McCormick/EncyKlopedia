import test from 'node:test';
import assert from 'node:assert/strict';
import { once } from 'node:events';
import { createApp,startFromEnvironment } from '../src/server.mjs';
import {validateResearchView} from '../src/research.mjs';

function fixture(){
 const sources=Array.from({length:6},(_,i)=>({id:`SRC-T${i}`,label:`Test source ${i}`,url:'https://example.org/source',locator:'section 1',capture_status:'NOT_CAPTURED',review_status:'pending'}));
 const claims=Array.from({length:19},(_,i)=>({id:`RTE-KA-PROP-${String(i+1).padStart(3,'0')}`,statement:'Synthetic test statement',section:'Testing',source_id:sources[0].id,source_locator:'section 1',status:'candidate_unreviewed'}));
 const articles=Array.from({length:41},(_,i)=>({
   id:`unesco:concept${i+10}`,unesco_id:`concept${i+10}`,
   unesco_uri:`http://vocabularies.unesco.org/thesaurus/concept${i+10}`,
   slug:`test-concept-${i+10}`,semantic_id:`KQ${i+1}`,identity_status:'provisional',
   wikidata_candidate:i<36?{id:`Q${i+100}`,status:'candidate',relation:'proposed_exact_match'}:null,
   skos_relations:{broader:[],narrower:[],related:[]},
   editorial_status:i===0?'research_candidate_unapproved':'source_anchor_only',
   source_refs:i===0?sources:[],claim_proposals:i===0?claims:[],
   localized:{en:{title:`Test ${i}`,summary:'test fixture',sections:[{heading:'Test',body:'Synthetic'}]}}
 }));
 return {profile:'encyklopedia.unesco-research-view/1.0',mode:'private-research',qualified:false,
   publication_enabled:false,publication_id:'NONE_PRIVATE_RESEARCH_NOT_A_PUBLICATION',
   locales:['en'],branch:{id:'unesco-mt1-10',language:'en'},articles,root_catalog:[],
   rdf_comparison:{historical_matched:40},source_sha256:{source:'fake'}};
}

async function withApp(view,run){
 const app=createApp(view,{research:true});app.listen(0,'127.0.0.1');await once(app,'listening');
 try{return await run(`http://127.0.0.1:${app.address().port}`);}finally{await new Promise(done=>app.close(done));}
}
test('private research input is explicit, never demo/public',()=>{
 const f=fixture();validateResearchView(f);
 assert.throws(()=>createApp(f),/cannot run as demo/);
 assert.throws(()=>startFromEnvironment({ENCYKLOPEDIA_MODE:'public'}),/blocked/);
 assert.throws(()=>startFromEnvironment({ENCYKLOPEDIA_MODE:'research',ENCYKLOPEDIA_HOST:'0.0.0.0'}),/loopback/);
 assert.throws(()=>startFromEnvironment({ENCYKLOPEDIA_MODE:'research'}),/absolute file path/);
});
test('reject implicit approvals, external crosswalk promotion, malformed sources and incomplete claims',()=>{
 const cases=[
  f=>{f.qualified=true;},
  f=>{f.publication_enabled=true;},
  f=>{f.articles[0].identity_status='approved';},
  f=>{f.articles[0].wikidata_candidate.status='approved';},
  f=>{f.articles[0].claim_proposals[0].status='approved';},
  f=>{f.articles[0].source_refs[0].capture_status='CAPTURED';},
  f=>{f.articles[0].source_refs[0].url='javascript:alert(1)';},
  f=>{f.articles[0].claim_proposals.pop();}
 ];
 for(const mutate of cases){let f=fixture();mutate(f);assert.throws(()=>validateResearchView(f));}
});
test('private research API keeps evidence and publication gates visible',()=>withApp(fixture(),async base=>{
 const status=await (await fetch(base+'/api/v1/status')).json();
 assert.equal(status.mode,'private-research');assert.equal(status.production_enabled,false);
 const health=await (await fetch(base+'/healthz')).json();assert.equal(health.publication_enabled,false);
 const article=await (await fetch(base+'/api/v1/articles/test-concept-10?lang=en')).json();
 assert.equal(article.synthetic,false);assert.equal(article.unapproved_research,true);
 assert.equal(article.claim_proposals.length,19);assert.equal(article.source_refs.length,6);
 const search=await (await fetch(base+'/api/v1/search?q=Test')).json();assert.equal(search.results.length,30);
 assert.equal(search.results[0].claim_proposals,undefined);
 const branch=await (await fetch(base+'/api/v1/unesco/branch')).json();assert.equal(branch.comparison.historical_matched,40);assert.equal(branch.concepts.length,41);
 const denied=await fetch(base+'/api/v1/search',{method:'POST'});assert.equal(denied.status,405);
}));
