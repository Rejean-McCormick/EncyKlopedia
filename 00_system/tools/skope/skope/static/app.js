'use strict';
const el=id=>document.getElementById(id);
let root='',branchOverrides={},selectedCandidates=new Set(),last=null,timer=null,previewBusy=false;
let geography={mode:'off'};
let activeLargeJob=null,largeTimer=null;
const GEO_CANADA={focus:'north-america',priority:'canada',mode:'annotate',region_qid:'Q49',priority_qid:'Q16',evidence_properties:['P9714','P183','P2341']};
const $=s=>document.querySelector(s);
async function api(path,body){const resp=await fetch(path,body===undefined?{}:{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});const x=await resp.json();if(!resp.ok)throw new Error(x.error||resp.statusText);return x}
function recipe(){return {root,default_depth:+el('depth').value,branches:{...branchOverrides},direction:el('direction').value,allowed_properties:el('props').value.split(',').map(v=>v.trim()).filter(Boolean),max_entities:+el('budget').value,convergence:{threshold_percent:+el('threshold').value,min_support:+el('minsupport').value,extra_depth:+el('extra').value,include:[...selectedCandidates].sort()},geography:{...geography}}}
function status(x){el('status').textContent=x}
function geotext(){const area=geography.region_qid==='Q49'?'North America':'Region '+(geography.region_qid||'?'),country=geography.priority_qid==='Q16'?'Canada':'Area '+(geography.priority_qid||'?');return geography.mode==='off'?'Geography off · Wizard → Geography':(geography.mode==='annotate'?area+' · '+country+' priority · No taxon excluded':area+' · '+country+' priority · Documented geographic links only');}
function syncGeoUi(){
  el('geo-primary-ui').value=geography.priority_qid||'Q16';
  el('geo-secondary-ui').value=geography.region_qid||'Q49';
  el('geo-mode-ui').value=geography.mode||'off';
  const hint=el('geo-hint');hint.classList.remove('geo-error');
  hint.textContent='Priority area: '+geoLabel(geography.priority_qid||'Q16')+' · Secondary area: '+geoLabel(geography.region_qid||'Q49')+' · Wikidata links are indicative, not verified observations.';
}
function geoLabel(qid){return ({Q16:'Canada (Q16)',Q49:'North America (Q49)',Q30:'United States (Q30)',Q96:'Mexico (Q96)'}[qid]||qid)}
function showGeostate(){el('geostate').textContent=geotext();syncGeoUi()}
function invalidateGeoPreview(){
  last=null;
  el('geocounts').classList.add('hidden');el('geocounts').textContent='';
  for(const id of ['kpinodes','kpiedges','kpicands','kpiwarn'])el(id).textContent='—';
  window.SkopeDensity.clear();
  for(const id of ['nodelist','candidates'])el(id).replaceChildren();
  el('manifest').textContent='Scope changed: recalculate to update the manifest.';
}
function setGeoSpecification(spec){
  if(!spec||!['off','annotate','documented_only'].includes(spec.mode))throw new Error('Invalid geography mode');
  const region=(spec.region_qid||'Q49').toUpperCase(),priority=(spec.priority_qid||'Q16').toUpperCase();
  if(spec.mode!=='off'&&(!/^Q[1-9][0-9]*$/.test(region)||!/^Q[1-9][0-9]*$/.test(priority)||region===priority)){
    throw new Error('Two different geographic QIDs are required (e.g. Canada Q16 and North America Q49).');
  }
  geography=spec.mode==='off'?{mode:'off'}:{...GEO_CANADA,...spec,region_qid:region,priority_qid:priority,focus:region==='Q49'?'north-america':'custom',priority:priority==='Q16'?'canada':'custom'};
  invalidateGeoPreview();showGeostate();
  status('Areas applied: '+geotext()+'. Click Calculate scope to measure the effect.');
}
function applyGeoFromSidebar(){
  const hint=el('geo-hint');
  try{setGeoSpecification({mode:el('geo-mode-ui').value,priority_qid:el('geo-primary-ui').value.trim().toUpperCase(),region_qid:el('geo-secondary-ui').value.trim().toUpperCase()});}
  catch(err){hint.classList.add('geo-error');hint.textContent='Error: '+err.message;status('Areas not applied: '+err.message);}
}
function mk(tag,text,klass){const e=document.createElement(tag);if(text!=null)e.textContent=text;if(klass)e.className=klass;return e}
function debounce(fn){clearTimeout(timer);timer=setTimeout(fn,400)}
async function loadBranches(){if(!root){el('branches').textContent='Select an entity or load a project recipe.';el('branchcount').textContent='0';return;}try{const rs=await api('/api/branches?root='+encodeURIComponent(root)+'&direction='+encodeURIComponent(el('direction').value)+(recipe().allowed_properties.map(v=>'&pid='+encodeURIComponent(v)).join('')));const holder=el('branches');holder.replaceChildren();el('branchcount').textContent=rs.length;rs.forEach(b=>{const row=mk('div',null,'branch');const desc=mk('div',null,'desc');desc.append(mk('b',b.property_label+' · '+b.pid+' · '+(b.direction==='out'?'outgoing':'incoming')),mk('small',b.first_hop_count+' neighbor(s) · '+b.examples.map(n=>n.label).join(', ')));const select=mk('select');for(let i=0;i<=8;i++){const o=mk('option','Lvl. '+i);o.value=i;select.append(o)}select.value=branchOverrides[b.key]??+el('depth').value;select.addEventListener('change',()=>{branchOverrides[b.key]=+select.value;debounce(maybePreview)});row.append(desc,select);holder.append(row)});if(!rs.length)holder.append(mk('span','No branch found for these PIDs in this index.','muted'));}catch(e){status('Branches: '+e.message)}}
async function search(){
  const query=el('search').value.trim();
  if(!query){status('Enter a botanical name or a QID.');return;}
  const button=el('find');button.disabled=true;button.textContent='Searching…';
  el('results').replaceChildren();
  status('Searching the local index: '+query+'…');
  const controller=new AbortController();
  const timeout=setTimeout(()=>controller.abort(),15000);
  try{
    const resp=await fetch('/api/search?q='+encodeURIComponent(query),{signal:controller.signal});
    const hits=await resp.json();
    if(!resp.ok)throw new Error(hits.error||'HTTP '+resp.status);
    for(const hit of hits){
      const b=mk('button',hit.label+' · '+hit.id,'suggestion');
      b.addEventListener('click',()=>{
        root=hit.id;selectedCandidates.clear();branchOverrides={};
        el('rootqid').textContent=root;el('rootlabel').textContent=hit.label;el('search').value=hit.id;
        el('projecttitle').textContent='Scope · '+hit.label;el('results').replaceChildren();
        status('Root selected: '+root+'. Loading branches…');
        loadBranches().then(maybePreview);
      });
      el('results').append(b);
    }
    status(hits.length?hits.length+' result(s). Click an entity to select it.':'No matches in the local index.');
  }catch(e){
    status(e.name==='AbortError'?'Search timed out after 15s. Check the Skope version and idx_name_norm.':'Search: '+e.message);
  }finally{
    clearTimeout(timeout);button.disabled=false;button.textContent='Chercher';
  }
}
function graph(report){window.SkopeDensity.render(report,root)}
function render(report){last=report;
  const cov=report.geography_coverage;const out=el('geocounts');
  if(cov){out.classList.remove('hidden');out.textContent='Wikidata geographic signals · Priority area ('+cov.priority+') : '+cov.priority_documented+' · Region ('+cov.focus+') outside priority: '+cov.region_other_documented+' · Other regions only: '+cov.other_area_only+' · Unknown geography: '+cov.no_geographic_evidence+' · Aggregated, unverified links; missing evidence is not evidence of absence.';}
  else{out.classList.add('hidden');out.textContent='';}el('kpinodes').textContent=report.counts.entities+(report.preview_only?' (preview)':'');el('kpiedges').textContent=report.counts.relations;el('kpicands').textContent=report.counts.candidates;el('kpiwarn').textContent=report.truncated?'Yes':'No';graph(report);const nodes=el('nodelist');nodes.replaceChildren();
  let shown=0;
  const appendNodes=()=>{
    const chunk=report.nodes.slice(shown,shown+250);
    for(const n of chunk){const e=mk('div',null,'item'),detail=mk('div');detail.append(mk('strong',n.label+' '),mk('code',n.id),mk('small',n.description||'—'),mk('small',n.reasons.join(' · ')),...(n.geography?[mk('small','Area : '+({priority:'Priority area (indicator)',region:'Region (indicator)',outside_only:'Other documented area',unknown:'Unknown distribution in this index'}[n.geography.category]||n.geography.category))]:[]));e.append(detail);nodes.append(e)}
    shown+=chunk.length;
    if(shown<report.nodes.length){
      const more=mk('button','Show next 250 ('+shown+'/'+report.nodes.length+')','suggestion');
      more.addEventListener('click',()=>{more.remove();appendNodes()});nodes.append(more);
    }
  };
  appendNodes();
  const cand=el('candidates');cand.replaceChildren();for(const c of report.candidates){const e=mk('div',null,'item'),checkbox=mk('input'),d=mk('div');checkbox.type='checkbox';checkbox.checked=selectedCandidates.has(c.id);checkbox.addEventListener('change',()=>{checkbox.checked?selectedCandidates.add(c.id):selectedCandidates.delete(c.id);debounce(maybePreview)});d.append(mk('strong',c.label+' '),mk('code',c.id),mk('small',c.support+' internal nodes · '+c.ratio_percent+' % · '+c.relations.join(', ')),mk('small','From: '+c.from.join(', ')));e.append(checkbox,d);cand.append(e)}if(!report.candidates.length)cand.append(mk('p','No external convergence at this threshold.','muted'));el('manifest').textContent=JSON.stringify({recipe:report.recipe,source_snapshot_digest:report.source_snapshot_digest,counts:report.counts,geography_coverage:report.geography_coverage,truncated:report.truncated,limitations:report.limitations},null,2)}
function maybePreview(){
  if(!root)return;
  if(+el('budget').value===0 || +el('budget').value>1500){status('Large scope: the preview is capped at 10,000; click Calculate scope or start the disk-backed batch collection.');return;}
  return preview();
}
async function preview(){
  if(!root){status('Choose a root in the local index.');return;}
  if(previewBusy){status('Calculation in progress: wait for updated counts.');return;}
  previewBusy=true;
  const button=el('preview');button.disabled=true;
  try{
    const big=+el('budget').value===0||+el('budget').value>1500;
    status(big?'Deep traversal on read-only SQLite… this may take a while.':'Computing locally…');
    const out=await api('/api/preview',recipe());render(out);
    status(out.truncated?(out.preview_only?'Preview limited to 10,000: start batch collection for an unlimited traversal.':'TRUNCATED scope: refine your settings.'):'Scope calculated from the aggregated index. Review required before any promotion.');
  }catch(e){status('Error: '+e.message)}
  finally{previewBusy=false;button.disabled=false;}
}
async function exportZip(){if(!root){status('Choose a root before exporting.');return;}try{status('Preparing ZIP…');const resp=await fetch('/api/export',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(recipe())});if(!resp.ok){const err=await resp.json();throw new Error(err.error)}const data=await resp.blob();const url=URL.createObjectURL(data);const link=document.createElement('a');link.href=url;link.download='skope-encyk-'+root+'-proposition.zip';document.body.append(link);link.click();link.remove();setTimeout(()=>URL.revokeObjectURL(url),5000);status(+el('budget').value===0||+el('budget').value>10000?'Large-scope recipe downloaded, NOT a complete QID list. Start batch collection to produce the inventory.':'EncyK proposal downloaded (non-canonical; review required).')}catch(e){status(e.message)}}
for(const id of ['depth','threshold','extra'])el(id).addEventListener('input',()=>{el(id+'val').textContent=el(id).value+(id==='threshold'?' %':'');if(id==='depth')loadBranches();debounce(maybePreview)});
for(const id of ['props','direction','budget','minsupport'])el(id).addEventListener('change',()=>{if(id==='props'||id==='direction')loadBranches();debounce(maybePreview)});
el('geo-apply-ui').addEventListener('click',applyGeoFromSidebar);
for(const id of ['geo-primary-ui','geo-secondary-ui','geo-mode-ui'])el(id).addEventListener('change',()=>{
 const hint=el('geo-hint');hint.classList.remove('geo-error');hint.textContent='Pending changes: click Apply areas.';
});
el('find').addEventListener('click',search);el('search').addEventListener('keydown',e=>{if(e.key==='Enter')search()});el('preview').addEventListener('click',preview);el('export').addEventListener('click',exportZip);el('copy').addEventListener('click',()=>navigator.clipboard?.writeText(el('manifest').textContent));
for(const b of document.querySelectorAll('.tabs button'))b.addEventListener('click',()=>{document.querySelectorAll('.tabs button').forEach(x=>x.classList.remove('active'));b.classList.add('active');document.querySelectorAll('.pane').forEach(x=>x.classList.add('hidden'));el('pane-'+b.dataset.tab).classList.remove('hidden')});
async function boot(){
  try{
    const [meta,config]=await Promise.all([api('/api/meta'),api('/api/config')]);
    el('dbstate').textContent=(meta.entity_count||'0')+' entities in the EncyK index';
    if(config.target_kristal){
      const t=config.target_kristal;
      el('targettitle').textContent=t.title+' · '+t.slug;
      el('targetdesc').textContent='State: '+(t.state_ref||'not declared')+' · domain: '+(t.domain||'unknown')+' · non-canonical proposal.';
      if(t.slug==='kristal-botany'){
        geography={...GEO_CANADA};showGeostate();
        el('search').value='Embryophyta';
        el('props').value='P171';
        el('direction').value='in';
        el('depth').value='6';el('depthval').textContent='6';
        el('budget').value='0';
        el('threshold').value='14.6';el('thresholdval').textContent='14.6 %';
        el('minsupport').value='8';el('extra').value='0';el('extraval').textContent='0';
      }
    }else{
      el('targettitle').textContent='No Kristal selected';
    }
    showGeostate();
    if(config.guidance){el('projectsubtitle').textContent='Suggested Arketype v1.4 guide: '+config.guidance.profile_slug+' (review required).';}
    if(config.recipe){
      const r=config.recipe;
      geography={...(r.geography||{mode:'off'})};showGeostate();
      root=r.root;branchOverrides={...(r.branches||{})};selectedCandidates=new Set((r.convergence||{}).include||[]);
      el('depth').value=r.default_depth;el('depthval').textContent=r.default_depth;
      el('direction').value=r.direction;el('props').value=(r.allowed_properties||[]).join(',');
      el('budget').value=r.max_entities;el('threshold').value=r.convergence.threshold_percent;
      el('thresholdval').textContent=r.convergence.threshold_percent+' %';
      el('minsupport').value=r.convergence.min_support;el('extra').value=r.convergence.extra_depth;
      el('extraval').textContent=r.convergence.extra_depth;
      const n=await api('/api/node?qid='+encodeURIComponent(root));
      el('rootqid').textContent=root;el('rootlabel').textContent=n?.label||root;
      el('search').value=root;el('projecttitle').textContent='Scope · '+(n?.label||root);
      el('projectsubtitle').textContent='External recipe loaded. Scope remains non-canonical.';
      await loadBranches();await preview();
    }else{
      if(config.target_kristal?.slug==='kristal-botany'){
        try{
          const n=await api('/api/node?qid=Q192154');
          if(n?.id==='Q192154'){
            root=n.id;selectedCandidates.clear();branchOverrides={};
            el('rootqid').textContent=n.id;el('rootlabel').textContent=n.label||n.id;
            el('search').value=n.id;el('projecttitle').textContent='Scope · '+(n.label||n.id);
            await loadBranches();
            status('Global botany settings ready (P171, depth 6, unlimited QIDs). Preview capped at 10,000; batch collection below.');
          }else status('Q192154 not found: choose a root and calculate.');
        }catch(e){status('Automatic root unavailable: '+e.message+'; select it manually.');}
      }else{
        el('branches').textContent='No project recipe loaded.';
        status('Kristal selected. Confirm the Wikidata root and calculate the scope.');
      }
    }
  }catch(e){status('Startup: '+e.message)}
}
// Interface explicite, limitée aux contrôles de l'UI d'origine. Le wizard ne change
// settings without a click. Metrics use the read-only preview endpoint.
window.SkopeWizardBridge = {
  current: () => ({root, recipe:recipe(), last}),
  apply: (patch) => {
    let needsBranches=false;
    for (const [id,value] of Object.entries(patch)) {
      if (id==='resetBranches') {if(value){branchOverrides={};needsBranches=true;}continue;}
      const control=el(id);
      if(!control || !['depth','direction','props','budget','threshold','minsupport','extra'].includes(id))continue;
      control.value=String(value);
      if (['depth','direction','props'].includes(id))needsBranches=true;
      if (['depth','extra','threshold'].includes(id)) el(id+'val').textContent=String(value)+(id==='threshold'?' %':'');
    }
    if(needsBranches && root)loadBranches();
    status('Recommended fields applied. Click Calculate scope to update counts.');
  },
  setGeography: (spec) => setGeoSpecification(spec),
  calculate: () => preview(),
  chooseRoot: async (qid) => {
    const n=await api('/api/node?qid='+encodeURIComponent(qid));
    if(!n || n.id!==qid)throw new Error('QID is not available in this index');
    root=qid;selectedCandidates.clear();branchOverrides={};
    el('rootqid').textContent=qid;el('rootlabel').textContent=n.label||qid;
    el('search').value=qid;el('projecttitle').textContent='Scope · '+(n.label||qid);
    el('results').replaceChildren();await loadBranches();
    status('Root selected: '+qid+'. Click Calculate scope to update.');
  },
};
boot();

// v0.13.14: inventory always starts explicitly, never on a slider update.
function showLargeJob(out){
  activeLargeJob=out.job;
  window.SkopeLastLargeStatus=out;
  window.SkopeJobModal?.update(out);
  el('large-progress').textContent='Job '+out.job.slice(0,8)+' · '+out.state+' · '+out.selected.toLocaleString('en-US')+' QIDs selected · '+out.pending.toLocaleString('en-US')+' pending · '+out.expanded.toLocaleString('en-US')+' expansions\n'+(out.message||'')+(out.output_ready?'\nQID inventory ready on D: / '+out.working_zone:'');
  el('large-start').textContent=['paused','failed','limit_reached'].includes(out.state)?'↻ Resume collection':(out.state==='running'?'Collecting…':'▶ Start batch QID collection');
  el('large-start').disabled=out.state==='running'||out.state==='queued';
  el('large-results').disabled=!(out.state==='completed'&&out.output_ready);
  if(largeTimer){clearTimeout(largeTimer);largeTimer=null;}
  if(['queued','running','pausing'].includes(out.state))largeTimer=setTimeout(refreshLargeJob,2500);
}
async function refreshLargeJob(){if(!activeLargeJob)return;try{showLargeJob(await api('/api/large/status?job='+activeLargeJob));}catch(e){el('large-progress').textContent='Job status: '+e.message;}}
async function startLargeJob(){
  if(!root){status('Select a Wikidata root first.');return;}
  const r=recipe();
  if(!r.allowed_properties.length||r.direction==='both'){status('Batch collection requires at least one PID (e.g. P171) and a single direction.');return;}
  if(r.geography.mode==='documented_only'){status('Strict geographic filtering cannot be verified with the compact index; use Prioritize without excluding.');return;}
  if(!window.confirm('Start or resume a disk-backed QID inventory on D:?\n\nQID target: '+(r.max_entities===0?'unlimited':r.max_entities)+'\nDepth: '+r.default_depth+'\nRelations: '+r.allowed_properties.join(',')+'\n\nThis may take time and use disk space on D:. Pause stops at a safe batch boundary. No Kristal canon will be modified.'))return;
  try{const resume=activeLargeJob&&window.SkopeLastLargeStatus && ['paused','failed','interrupted','limit_reached','running'].includes(window.SkopeLastLargeStatus.state)?activeLargeJob:null;
    const out=await api('/api/large/start',{recipe:r,...(resume?{resume}:{})});showLargeJob(out);window.SkopeJobModal?.show();
    status('Disk-backed QID collection started. The index stays read-only.');
  }catch(e){status('Collection: '+e.message);}
}
async function pauseLargeJob(){if(!activeLargeJob){status('No active collection.');return;}try{const out=await api('/api/large/pause',{job:activeLargeJob});status(out.message);setTimeout(refreshLargeJob,1000);}catch(e){status('Pause: '+e.message);}}
el('large-start').addEventListener('click',startLargeJob);
el('large-pause').addEventListener('click',pauseLargeJob);
api('/api/large/latest').then(out=>{if(out){showLargeJob(out);if(out.state==='running'){el('large-start').disabled=false;el('large-start').textContent='↻ Resume interrupted job';}}}).catch(()=>{});
