'use strict';
/* Optional Skope config wizard; isolated from the original view. All calculations
   use the existing read-only API. No automatic apply, export, extraction or writes. */
(() => {
const e = id => document.getElementById(id);
const w = window.SkopeWizardBridge;
const dlg = e('skope-wizard');
const presets = {
  botany: {
    label:'Recommended · Botany · Canada first',
    summary:'Deep P171 taxonomic traversal; 0 = unlimited collection, 10,000-QID preview, then disk-backed batch inventory.',
    values:{direction:'in',props:'P171',depth:6,budget:0,threshold:14.6,minsupport:8,extra:0},root:'Q192154',
    risk:'The 10,000 preview is partial; click Start batch QID collection in Skope to continue on D:.',
  },
  prudent: {
    label:'Conservative · Small scope',
    summary:'Quick test of top-level botanical lineages, without external expansion.',
    values:{direction:'in',props:'P171',depth:2,budget:1500,threshold:5,minsupport:3,extra:0},root:'Q192154',
    risk:'This is deliberately partial; do not mistake it for a global inventory.'
  },
  expanded: {
    label:'Broader exploration · Review required',
    summary:'Four taxonomic levels before deeper traversal. May truncate.',
    values:{direction:'in',props:'P171',depth:4,budget:5000,threshold:5,minsupport:5,extra:0},root:'Q192154',
    risk:'A depth-4 scope is not the entire plant kingdom, even without truncation.'
  },
  general: {
    label:'Generic conservative discovery',
    summary:'Neighborhood discovery across all properties; the graph can mix unrelated relation types.',
    values:{direction:'both',props:'',depth:1,budget:300,threshold:5,minsupport:3,extra:0},root:null,
    risk:'Without a property filter, results can be heterogeneous; inspect every relation.'
  }
};
const groups = [
  {label:'1 · Starting point', title:'Choose Wikidata root', intro:'The root anchors the whole graph. For botany, start at Embryophyta.', fields:[]},
  {label:'2 · Relations', title:'Choose relation types and direction', intro:'Direction sets which neighbors to visit; property PIDs filter edge types. These choices change what the scope means.',fields:['direction','props']},
  {label:'3 · Size', title:'Control depth and size', intro:'Each level visits neighbors of previously reached entities. A cap can interrupt traversal; it never guarantees completeness.',fields:['depth','budget']},
  {label:'4 · Convergence', title:'Evaluate outside connections', intro:'Convergence suggests external entities supported by several selected nodes. Candidates are never added automatically.',fields:['threshold','minsupport','extra']},
  {label:'5 · Geography', title:'Where do plants grow?', intro:'Set a study region and a geographic priority. Wikidata links are incomplete indicators, not verified occurrence data.',fields:[]},
  {label:'6 · Measure', title:'Compare before applying', intro:'The diagrams are illustrative. Metrics come from actual SQLite calculations when you click Measure.',fields:[]},
  {label:'7 · Full records', title:'Extract full original Wikidata', intro:'After collecting QIDs, select an extraction profile JSON, verify the dump and fast-access index, then explicitly start the extraction.',fields:[]},
];
const fields = {
  direction:{label:'Sens des relations',why:'Incoming = entities pointing to the root (e.g. child taxa via P171). Outgoing = edges from root. Both = wider exploration.',effects:'Incoming targets descendant taxa in this botanical configuration.',format:v=>({in:'Incoming',out:'Outgoing',both:'Both'}[v]||v)},
  props:{label:'Followed properties',why:'P171 = parent taxon; P279 = subclass of. Empty means all properties and a much wider range of relations.',effects:'Only P171 produces a more coherent taxonomy; explore P279 separately.',format:v=>v||'(all)'},
  depth:{label:'Profondeur globale',why:'0 = root only; 1 = immediate neighbors; 2 = neighbors of neighbors. Entity counts may grow nonlinearly.',effects:'Depth 6–8 reaches more descendants but not necessarily all species; node counts can grow rapidly.',format:v=>String(v)},
  budget:{label:'QID target',why:'0 = unlimited batch inventory. Preview is capped at 10,000 QIDs; mass collection writes to disk.',effects:'Targets above 10,000 do not increase graph memory use. Batch collection continues on D: and supports pause/resume.',format:v=>Number(v)===0?'Unlimited (0)':String(v)},
  threshold:{label:'Convergence threshold',why:'Minimum percentage of distinct selected entities connected to an outside candidate. Higher = stricter selection.',effects:'A 3% threshold requires more support than 1%.',format:v=>String(v)+' %'},
  minsupport:{label:'Minimum connections',why:'Minimum distinct selected nodes supporting a convergence candidate. Higher reduces weak candidates.',effects:'8 requires at least eight distinct supporting nodes.',format:v=>String(v)},
  extra:{label:'Extra depth after acceptance',why:'Expansion only occurs after explicit candidate acceptance. 0 = accept without visiting its neighbors; 1+ = extra hop(s).',effects:'0 prevents additional cascading traversal after convergence.',format:v=>String(v)},
};
let index=0, profile='botany', measured=null, busy=false, measurementToken=0;
function context(){return w.current()}
function isBotany(){const text=e('targettitle').textContent.toLowerCase();return text.includes('kristal-botany')}
function activeProfile(){return presets[profile]}
function resetMeasured(){measured=null;measurementToken++}
function displayValue(field,value){return fields[field].format(value)}
function profileRecipe(){const current=context().recipe;const values=activeProfile().values;
  return {...current,geography:isBotany()?{focus:'north-america',priority:'canada',mode:'annotate',region_qid:'Q49',priority_qid:'Q16',evidence_properties:['P9714','P183','P2341']}:{mode:'off'},branches:{},default_depth:values.depth,direction:values.direction,allowed_properties:values.props.split(',').filter(Boolean),max_entities:values.budget,
    convergence:{...current.convergence,threshold_percent:values.threshold,min_support:values.minsupport,extra_depth:values.extra}};
}
function sameRecipe(a,b){if(!a||!b)return false;
  return a.root===b.root&&a.default_depth===b.default_depth&&a.direction===b.direction&&
    a.max_entities===b.max_entities&&JSON.stringify(a.allowed_properties||[])===JSON.stringify(b.allowed_properties||[])&&
    JSON.stringify(a.branches||{})===JSON.stringify(b.branches||{})&&
    a.convergence.threshold_percent===b.convergence.threshold_percent&&
    a.convergence.min_support===b.convergence.min_support&&a.convergence.extra_depth===b.convergence.extra_depth&&
    JSON.stringify(a.convergence.include||[])===JSON.stringify(b.convergence.include||[])&&
    JSON.stringify(a.geography||{mode:'off'})===JSON.stringify(b.geography||{mode:'off'});
}
function node(tag,classname,text){const n=document.createElement(tag);if(classname)n.className=classname;if(text!==undefined)n.textContent=text;return n}
function button(text,fn,classname){const b=node('button',classname,text);b.type='button';b.addEventListener('click',fn);return b}
function status(text){e('wizard-status').textContent=text}
function apply(fieldsToApply){w.apply(fieldsToApply);resetMeasured();status('Settings applied. Recalculate scope to update metrics.');render();}
function applyOne(field){apply({[field]:activeProfile().values[field]})}
function applyAll(){apply({...activeProfile().values,resetBranches:true});if(isBotany())w.setGeography({mode:'annotate'});}
function drawGraph(container,config){const SVG='http://www.w3.org/2000/svg';const svg=document.createElementNS(SVG,'svg');svg.setAttribute('viewBox','0 0 330 132');svg.setAttribute('role','img');svg.setAttribute('aria-label','Illustrative diagram of depth and direction; not measured');
  const mk=(name,attrs)=>{const x=document.createElementNS(SVG,name);for(const [a,v] of Object.entries(attrs))x.setAttribute(a,String(v));return x};
  const center=[155,64],depth=Math.min(3,+config.depth||0),wide=config.props?6:9,limit=Math.min(24,Math.max(1,Math.round((+config.budget||300)/180)));
  const points=[];
  if(depth){for(let k=0;k<wide;k++){const a=(k/wide)*Math.PI*2;points.push([center[0]+60*Math.cos(a),center[1]+44*Math.sin(a),0]);}}
  if(depth>=2){for(let k=0;k<Math.min(wide*2+limit,22);k++){const a=(k/Math.min(wide*2+limit,22))*Math.PI*2;points.push([center[0]+130*Math.cos(a),center[1]+58*Math.sin(a),1]);}}
  if(depth>=3){for(let k=0;k<Math.min(limit+9,25);k++){const a=(k/Math.min(limit+9,25))*Math.PI*2;points.push([center[0]+151*Math.cos(a),center[1]+61*Math.sin(a),2]);}}
  if(config.direction!=='both'){const d=mk('text',{x:10,y:14,fill:'#a8d6d1','font-size':9});d.textContent=config.direction==='in'?'Incoming edges → root':'Root → outgoing edges';svg.append(d)}
  else{const d=mk('text',{x:10,y:14,fill:'#a8d6d1','font-size':9});d.textContent='Incoming + outgoing';svg.append(d)}
  for(const [i,p] of points.entries()){const start=p[2]===0?center:points[i%wide]||center;svg.append(mk('line',{x1:start[0],y1:start[1],x2:p[0],y2:p[1],stroke:p[2]===0?'#4e8292':'#2d5664','stroke-width':1.4}));}
  for(const p of points)svg.append(mk('circle',{cx:p[0],cy:p[1],r:3.7,fill:p[2]===0?'#7dbfea':'#446d80'}));
  svg.append(mk('circle',{cx:center[0],cy:center[1],r:9,fill:'#5de2c4'}));container.append(svg);
}
function vizRow(view){const values=activeProfile().values;const cur=context().recipe;
 const wrap=node('div','wizard-grid');for(const [name,cfg,small] of [['Current settings',{depth:cur.default_depth,direction:cur.direction,props:cur.allowed_properties.join(','),budget:cur.max_entities},'Current Skope settings'],['Recommendation',values,activeProfile().label]]){
 const box=node('div','wizard-vizcard');box.append(node('strong',null,name));drawGraph(box,cfg);box.append(node('small',null,small));wrap.append(box);
 }view.append(wrap,node('div','wizard-explainer','Illustrative propagation diagrams. Drawn points are not actual counts.'));
}
function item(view,key){const def=fields[key],current=configValue(key),rec=activeProfile().values[key];const row=node('div','wizard-item');const content=node('div');content.append(node('h4',null,def.label),node('p',null,def.why));
 const vals=node('div','wizard-values');const now=node('span');now.append('Current: ',node('b',null,displayValue(key,current)));const next=node('span');next.append('Recommended: ',node('b','wizard-reco',displayValue(key,rec)));vals.append(now,next);content.append(vals);row.append(content,button('Apply',()=>applyOne(key)));view.append(row);
}
function configValue(k){const r=context().recipe;const map={direction:r.direction,props:r.allowed_properties.join(','),depth:r.default_depth,budget:r.max_entities,threshold:r.convergence.threshold_percent,minsupport:r.convergence.min_support,extra:r.convergence.extra_depth};return map[k]}
function geoScreen(view){
  const r=context().recipe, current=r.geography||{mode:'off'};
  const intro=node('div','wizard-guide','Secondary area: North America (Q49) · Priority area: Canada (Q16). P9714 (taxon range), P183 (endemic to) and P2341 (indigenous to) are aggregated geographic signals, NOT verified plant occurrence records.');
  view.append(intro);
  const itemBox=node('div','wizard-item'),detail=node('div');detail.append(node('h4',null,'Geographic selection mode'));
  detail.append(node('p',null,'Currently: '+({off:'Disabled',annotate:'Canada first (nothing excluded)',documented_only:'Keep only taxons with documented geographic links (plus context root)'}[current.mode]||current.mode)));
  const selector=node('select');selector.id='wizard-geo-mode';
  for(const [value,label] of [['annotate','Recommended · Canada first, retain unknowns'],['documented_only','Strict · Keep documented North America taxa'],['off','Disable geographic priorities']]){
    const opt=node('option',null,label);opt.value=value;selector.append(opt);
  }
  selector.value=current.mode==='off'?'annotate':current.mode;
  detail.append(selector);
  const country=node('input');country.type='text';country.id='wizard-geo-priority';country.value=current.priority_qid||'Q16';country.maxLength=18;
  const region=node('input');region.type='text';region.id='wizard-geo-region';region.value=current.region_qid||'Q49';region.maxLength=18;
  const geoFields=node('div','wizard-geo-fields');
  const first=node('label',null,'Secondary area (QID) · Q49 = North America');first.append(region);
  const second=node('label',null,'Priority area (QID) · Q16 = Canada');second.append(country);
  geoFields.append(first,second);detail.append(geoFields);
  itemBox.append(detail,button('Apply geographic scope',()=>{
    const area=region.value.trim().toUpperCase(),preferred=country.value.trim().toUpperCase();
    if(selector.value!=='off'&&(!/^Q[1-9][0-9]*$/.test(area)||!/^Q[1-9][0-9]*$/.test(preferred)||area===preferred)){
      status('Enter two distinct valid geographic QIDs.');return;
    }
    w.setGeography({mode:selector.value,region_qid:area,priority_qid:preferred});resetMeasured();status('Geographic focus applied. Click Calculate scope to measure.');render();
  },'primary'));view.append(itemBox);
  view.append(node('div','wizard-notice','WARNING: strict filtering does not prove excluded taxa are absent. Wikidata distribution signals are incomplete. Truncated traversal remains incomplete under any filter.'));
  const g=context().last?.geography_coverage;
  if(g && JSON.stringify(current)===JSON.stringify(context().last.recipe.geography)){
    const wrap=node('div','wizard-metricpane');wrap.append(node('strong',null,'Coverage in last calculation'));
    for(const [label,value] of [['Priority area '+g.priority+' (indicator)',g.priority_documented],['Region '+g.focus+' outside priority (indicator)',g.region_other_documented],['Other areas only',g.other_area_only],['Unknown geography',g.no_geographic_evidence]]){
      const line=node('div','wizard-metricline');line.append(node('span',null,label),node('b',null,String(value)));wrap.append(line);
    }
    view.append(wrap);
  } else view.append(node('div','wizard-guide','To measure Canada / North America / unknown categories, apply the settings and click Calculate scope. No estimated counts.'));
}
function fieldScreen(view){const group=groups[index];view.append(node('h3',null,group.title),node('p',null,group.intro));
 if(index!==3&&index!==4)vizRow(view);
 if(index===4){geoScreen(view);return}
 if(index===0){const cur=context(),rec=activeProfile();const rootBox=node('div','wizard-item'),desc=node('div');desc.append(node('h4',null,'Wikidata root'),node('p',null,'Current: '+(cur.root||'none')+'. The root anchors the subject; it is not an edge type.'));
 if(rec.root){desc.append(node('div','wizard-values','Suggested: '+rec.root+' · Embryophyta (land plants)'));rootBox.append(desc,button('Choose '+rec.root,()=>chooseRoot(rec.root)))}else{rootBox.append(desc,node('small','wizard-caution','Choose an entity using Skope search.'))}view.append(rootBox);
 const tip=node('div','wizard-guide','Tip: Search identifies an exact QID. A label alone does not guarantee identity.');view.append(tip);
 } else{for(const id of group.fields)item(view,id)}
 if(index===2){const tip=node('div','wizard-notice','At depth 2, a full cap of 300/300 with Truncated: Yes means an incomplete scope, not a complete species list.');view.append(tip)}
 if(index===3){const tip=node('div','wizard-guide','Branch-specific depth overrides may differ. Apply all resets overrides only when explicitly clicked.');view.append(tip);
 view.append(button('Reset branch depth overrides',()=>apply({resetBranches:true})));
 }
 if(index!==0 && index!==4 && index!==5){const actions=node('div','wizard-actions');actions.append(button('Apply recommended profile',applyAll,'primary'));view.append(actions)}
 view.append(node('div','wizard-notice',activeProfile().risk));
}
async function chooseRoot(qid){status('Checking QID '+qid+'…');try{await w.chooseRoot(qid);resetMeasured();status('Root '+qid+' selected.');render()}catch(err){status('Failed: '+err.message)}}
function metricsBox(title,report,color,caption,referenceCap){const panel=node('div','wizard-metricpane');panel.append(node('strong',null,title),node('small',null,caption));
 if(!report){panel.append(node('div','wizard-guide','No fresh metrics. Click Calculate scope in Skope.'));return panel}
 const data=[['Entities',report.counts.entities],['Relations',report.counts.relations],['Candidates',report.counts.candidates]];
 for(const [name,number] of data){const line=node('div','wizard-metricline');line.append(node('span',null,name),node('b',null,String(number)));panel.append(line);const track=node('div','wizard-track'),fill=node('div','wizard-fill'+(color?' wizard-color-alt':''));fill.style.width=(Math.min(100,100*number/Math.max(1,referenceCap[name]||1)))+'%';track.append(fill);panel.append(track)}
 panel.append(node('div','wizard-metricwarn',report.truncated?'Truncated: YES · incomplete scope':'Truncated: No · cap not reached'));
 return panel;
}
function measureScreen(view){const profileR=profileRecipe();const measuredRecipe={...profileR,max_entities:profileR.max_entities===0?1500:Math.min(profileR.max_entities,1500)};const ctx=context(),currentFresh=ctx.last&&sameRecipe(ctx.last.recipe,ctx.recipe),cur=currentFresh?ctx.last:null,compare=measured&&sameRecipe(measured.recipe,measuredRecipe)?measured:null;
 view.append(node('h3',null,'Quantify scope changes'),node('p',null,'Calculations are opt-in and do not modify fields, SQLite or Kristal. These are aggregated index data, not complete source statements.'));
 const actions=node('div','wizard-actions');
 actions.append(button('Measure recommendation (read-only)',measure,'primary'));
 actions.append(button('Apply all settings',applyAll));
 actions.append(button('Recalculate current scope',async()=>{dlg.close();await w.calculate();status('Metrics updated in Skope.');},''));
 view.append(actions);
 if(busy)view.append(node('div','wizard-guide','Computing recommended scope. Please wait.'));
 const caps={};for(const [label,key] of [['Entities','entities'],['Relations','relations'],['Candidates','candidates']])caps[label]=Math.max(1,cur?.counts[key]||0,compare?.counts[key]||0);
 const boxes=node('div','wizard-metrics');boxes.append(metricsBox('Current',cur,false,cur?'Calculated with matching settings':'Stale or missing metrics',caps));boxes.append(metricsBox('Recommended',compare,true,compare?((profileR.max_entities===0||profileR.max_entities>1500)?'Measured subset of 1,500 · NOT exhaustive':'Measured with recommended settings'):'Click Measure',caps));view.append(boxes);
 if(!ctx.root)view.append(node('div','wizard-notice','Select a QID in Skope first.'));
 if(cur&&cur.truncated)view.append(node('div','wizard-notice','Current result is truncated: the count is a bounded lower estimate, not a full scope.'));
 if(compare&&compare.truncated)view.append(node('div','wizard-notice','Measurement capped at 1,500; it does not mean full collection is impossible. Click Start batch QID collection.'));
 else if(compare)view.append(node('div','wizard-notice wizard-ok',(profileR.max_entities===0||profileR.max_entities>1500)?'The 1,500-item subscope is not truncated; full traversal is still unverified.':'The recommended calculation is not truncated. Review relations before export.'));
 view.append(node('div','wizard-guide','The wizard measures up to 1,500 entities for quick comparisons—not the complete corpus. Start batch QID collection from the Skope inventory panel. Original Wikidata JSON is not extracted and nothing is written to the Kristal canon.'));
}
async function measure(){if(busy)return;const cur=context();if(!cur.root){status('Select a Wikidata root in Skope first.');return}
 const cfg={...profileRecipe(),max_entities:profileRecipe().max_entities===0?1500:Math.min(profileRecipe().max_entities,1500)};
 const token=++measurementToken;busy=true;status('Measuring up to 1,500 recommended entities without applying any setting…');render();const ac=new AbortController();const timeout=setTimeout(()=>ac.abort(),30000);
 try{const resp=await fetch('/api/preview',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(cfg),signal:ac.signal});const data=await resp.json();if(!resp.ok)throw new Error(data.error||('HTTP '+resp.status));if(token!==measurementToken)return;measured=data;status('Measurement complete; settings unchanged.');}
 catch(err){if(token===measurementToken)status(err.name==='AbortError'?'Measurement timed out after 30s. Try a smaller scope.':'Measurement failed: '+err.message)}
 finally{clearTimeout(timeout);busy=false;if(dlg.open)render()}
}
function extractScreen(view){
 view.append(node('h3',null,'Full Wikidata entity records'));
 view.append(node('p',null,'A completed QID inventory contains identifiers only. Full extraction reads the verified original Wikidata JSON through the existing random-access index, preserving claims, qualifiers, references, aliases and external identifiers. No full dump scan or Kristal canon write.'));
 const guide=node('div','wizard-guide','1. Finish a QID batch inventory. 2. Choose the Botany–Canada extraction JSON profile. 3. Click Check sources. 4. If verified and ready, confirm Extract Full Wikidata Records. 5. Track progress, pause/resume, then open the evidence folder.');view.append(guide);
 const btn=button('Open Full Wikidata Records settings',()=>{dlg.close();e('full-extraction').scrollIntoView({behavior:'smooth',block:'center'});e('extract-profile').focus();},'primary');
 view.append(node('p',null,'If dump identity, locator or space is missing, the preflight explains the blocker and prevents starting.'),btn);
}
function render(){const profileItem=activeProfile(),target=isBotany()?'Kristal-Botany · taxonomy PRF-03':'Target: '+e('targettitle').textContent;e('wizard-target').textContent=target;
 const tabs=e('wizard-steps');tabs.replaceChildren();groups.forEach((group,i)=>{const tab=button(group.label,()=>{index=i;render()},i===index?'active':'');tab.setAttribute('aria-current',i===index?'step':'false');tabs.append(tab)});
 const view=e('wizard-view');view.replaceChildren();if(index===5)measureScreen(view);else if(index===6)extractScreen(view);else fieldScreen(view);
 e('wizard-prev').disabled=index===0;e('wizard-next').textContent=index===groups.length-1?'Finish ✓':'Next →';
}
function open(){const sel=e('wizard-profile');sel.replaceChildren();for(const [id,p] of Object.entries(presets)){if(!isBotany()&&id!=='general')continue;const opt=node('option',null,p.label);opt.value=id;sel.append(opt)}
 profile=isBotany()?'botany':'general';sel.value=profile;index=0;measured=null;status('Profile suggested; Skope settings unchanged.');render();dlg.showModal()}
e('wizard-open').addEventListener('click',open);
e('wizard-close').addEventListener('click',()=>dlg.close());
e('wizard-profile').addEventListener('change',()=>{profile=e('wizard-profile').value;resetMeasured();status('New profile selected; no fields changed.');render()});
e('wizard-prev').addEventListener('click',()=>{index=Math.max(0,index-1);render()});
e('wizard-next').addEventListener('click',()=>{if(index===groups.length-1)dlg.close();else {index++;render()}});
})();
