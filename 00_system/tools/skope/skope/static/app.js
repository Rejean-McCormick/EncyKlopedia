'use strict';
const el=id=>document.getElementById(id);
let root='',branchOverrides={},selectedCandidates=new Set(),last=null,timer=null;
const $=s=>document.querySelector(s);
async function api(path,body){const resp=await fetch(path,body===undefined?{}:{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});const x=await resp.json();if(!resp.ok)throw new Error(x.error||resp.statusText);return x}
function recipe(){return {root,default_depth:+el('depth').value,branches:{...branchOverrides},direction:el('direction').value,allowed_properties:el('props').value.split(',').map(v=>v.trim()).filter(Boolean),max_entities:+el('budget').value,convergence:{threshold_percent:+el('threshold').value,min_support:+el('minsupport').value,extra_depth:+el('extra').value,include:[...selectedCandidates].sort()}}}
function status(x){el('status').textContent=x}
function mk(tag,text,klass){const e=document.createElement(tag);if(text!=null)e.textContent=text;if(klass)e.className=klass;return e}
function debounce(fn){clearTimeout(timer);timer=setTimeout(fn,400)}
async function loadBranches(){if(!root){el('branches').textContent='Sélectionne une entité ou charge une recette de projet.';el('branchcount').textContent='0';return;}try{const rs=await api('/api/branches?root='+encodeURIComponent(root)+'&direction='+encodeURIComponent(el('direction').value)+(recipe().allowed_properties.map(v=>'&pid='+encodeURIComponent(v)).join('')));const holder=el('branches');holder.replaceChildren();el('branchcount').textContent=rs.length;rs.forEach(b=>{const row=mk('div',null,'branch');const desc=mk('div',null,'desc');desc.append(mk('b',b.property_label+' · '+b.pid+' · '+(b.direction==='out'?'sortante':'entrante')),mk('small',b.first_hop_count+' voisin(s) · '+b.examples.map(n=>n.label).join(', ')));const select=mk('select');for(let i=0;i<=6;i++){const o=mk('option','Niv. '+i);o.value=i;select.append(o)}select.value=branchOverrides[b.key]??+el('depth').value;select.addEventListener('change',()=>{branchOverrides[b.key]=+select.value;debounce(preview)});row.append(desc,select);holder.append(row)});if(!rs.length)holder.append(mk('span','Aucune branche trouvée dans cet index et avec ces PID.','muted'));}catch(e){status('Branches : '+e.message)}}
async function search(){
  const query=el('search').value.trim();
  if(!query){status('Saisis un nom botanique ou un QID.');return;}
  const button=el('find');button.disabled=true;button.textContent='Recherche…';
  el('results').replaceChildren();
  status('Recherche dans l’index local : '+query+'…');
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
        el('projecttitle').textContent='Portée · '+hit.label;el('results').replaceChildren();
        status('Racine sélectionnée : '+root+'. Chargement des branches…');
        loadBranches().then(preview);
      });
      el('results').append(b);
    }
    status(hits.length?hits.length+' résultat(s). Clique sur une entité pour la choisir.':'Aucun résultat dans l’index local.');
  }catch(e){
    status(e.name==='AbortError'?'Recherche interrompue après 15 s. Vérifie la version de Skope et idx_name_norm.':'Recherche : '+e.message);
  }finally{
    clearTimeout(timeout);button.disabled=false;button.textContent='Chercher';
  }
}
function graph(report){const svg=el('graph');svg.replaceChildren();const ns='http://www.w3.org/2000/svg';const data=report.nodes.slice(0,70);const index=new Map(data.map((n,i)=>[n.id,i]));const coords=new Map();const cx=450,cy=260;data.forEach((n,i)=>{const radius=i===0?0:95+Math.sqrt(i/data.length)*146;const a=(i*2.399963229728653)% (2*Math.PI);coords.set(n.id,{x:cx+Math.cos(a)*radius*1.65,y:cy+Math.sin(a)*radius})});for(const e of report.edges.slice(0,350)){if(!index.has(e.source)||!index.has(e.target))continue;const a=coords.get(e.source),b=coords.get(e.target);const line=document.createElementNS(ns,'line');line.setAttribute('x1',a.x);line.setAttribute('y1',a.y);line.setAttribute('x2',b.x);line.setAttribute('y2',b.y);svg.append(line)}for(const n of data){const pos=coords.get(n.id),g=document.createElementNS(ns,'g'),c=document.createElementNS(ns,'circle'),t=document.createElementNS(ns,'text');c.setAttribute('cx',pos.x);c.setAttribute('cy',pos.y);c.setAttribute('r',n.id===root?'13':'7');c.setAttribute('fill',n.id===root?'#5de2c4':n.reasons.some(s=>s.startsWith('convergence'))?'#ffc681':'#7dbfea');const tooltip=document.createElementNS(ns,'title');tooltip.textContent=n.label+' · '+n.id+'\n'+n.reasons.join(', ');c.append(tooltip);g.append(c);if(n.id===root||data.length<19){t.textContent=n.label.slice(0,22);t.setAttribute('x',pos.x+12);t.setAttribute('y',pos.y-10);g.append(t)}svg.append(g)}el('graphinfo').textContent=data.length+'/'+report.nodes.length+' nœuds dessinés'}
function render(report){last=report;el('kpinodes').textContent=report.counts.entities;el('kpiedges').textContent=report.counts.relations;el('kpicands').textContent=report.counts.candidates;el('kpiwarn').textContent=report.truncated?'Oui':'Non';graph(report);const nodes=el('nodelist');nodes.replaceChildren();for(const n of report.nodes){const e=mk('div',null,'item'),detail=mk('div');detail.append(mk('strong',n.label+' '),mk('code',n.id),mk('small',n.description||'—'),mk('small',n.reasons.join(' · ')));e.append(detail);nodes.append(e)}const cand=el('candidates');cand.replaceChildren();for(const c of report.candidates){const e=mk('div',null,'item'),checkbox=mk('input'),d=mk('div');checkbox.type='checkbox';checkbox.checked=selectedCandidates.has(c.id);checkbox.addEventListener('change',()=>{checkbox.checked?selectedCandidates.add(c.id):selectedCandidates.delete(c.id);debounce(preview)});d.append(mk('strong',c.label+' '),mk('code',c.id),mk('small',c.support+' nœuds internes · '+c.ratio_percent+' % · '+c.relations.join(', ')),mk('small','Depuis : '+c.from.join(', ')));e.append(checkbox,d);cand.append(e)}if(!report.candidates.length)cand.append(mk('p','Aucune convergence au seuil choisi.','muted'));el('manifest').textContent=JSON.stringify({recipe:report.recipe,source_snapshot_digest:report.source_snapshot_digest,counts:report.counts,truncated:report.truncated,limitations:report.limitations},null,2)}
async function preview(){if(!root){status('Choisis une racine dans l’index local.');return;}try{status('Calcul local…');const out=await api('/api/preview',recipe());render(out);status('Périmètre calculé. Examen requis avant promotion.')}catch(e){status('Erreur : '+e.message)}}
async function exportZip(){if(!root){status('Choisis une racine avant d’exporter.');return;}try{status('Préparation du ZIP…');const resp=await fetch('/api/export',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(recipe())});if(!resp.ok){const err=await resp.json();throw new Error(err.error)}const data=await resp.blob();const url=URL.createObjectURL(data);const link=document.createElement('a');link.href=url;link.download='skope-encyk-'+root+'-proposition.zip';document.body.append(link);link.click();link.remove();setTimeout(()=>URL.revokeObjectURL(url),5000);status('Proposition EncyK téléchargée (non canonique, à réviser).')}catch(e){status(e.message)}}
for(const id of ['depth','threshold','extra'])el(id).addEventListener('input',()=>{el(id+'val').textContent=el(id).value+(id==='threshold'?' %':'');if(id==='depth')loadBranches();debounce(preview)});
for(const id of ['props','direction','budget','minsupport'])el(id).addEventListener('change',()=>{if(id==='props'||id==='direction')loadBranches();debounce(preview)});
el('find').addEventListener('click',search);el('search').addEventListener('keydown',e=>{if(e.key==='Enter')search()});el('preview').addEventListener('click',preview);el('export').addEventListener('click',exportZip);el('copy').addEventListener('click',()=>navigator.clipboard?.writeText(el('manifest').textContent));
for(const b of document.querySelectorAll('.tabs button'))b.addEventListener('click',()=>{document.querySelectorAll('.tabs button').forEach(x=>x.classList.remove('active'));b.classList.add('active');document.querySelectorAll('.pane').forEach(x=>x.classList.add('hidden'));el('pane-'+b.dataset.tab).classList.remove('hidden')});
async function boot(){
  try{
    const [meta,config]=await Promise.all([api('/api/meta'),api('/api/config')]);
    el('dbstate').textContent=(meta.entity_count||'0')+' entités dans l’index EncyK';
    if(config.target_kristal){
      const t=config.target_kristal;
      el('targettitle').textContent=t.title+' · '+t.slug;
      el('targetdesc').textContent='État : '+(t.state_ref||'non déclaré')+' · domaine : '+(t.domain||'inconnu')+' · proposition non canonique.';
      if(t.slug==='kristal-botany'){
        el('search').value='Embryophyta';
        el('props').value='P171,P279';
        el('direction').value='in';
        el('depth').value='1';el('depthval').textContent='1';
        el('budget').value='300';
      }
    }else{
      el('targettitle').textContent='Aucun Kristal choisi';
    }
    if(config.guidance){el('projectsubtitle').textContent='Guide Arketype v1.4 proposé : '+config.guidance.profile_slug+' (revue requise).';}
    if(config.recipe){
      const r=config.recipe;
      root=r.root;branchOverrides={...(r.branches||{})};selectedCandidates=new Set((r.convergence||{}).include||[]);
      el('depth').value=r.default_depth;el('depthval').textContent=r.default_depth;
      el('direction').value=r.direction;el('props').value=(r.allowed_properties||[]).join(',');
      el('budget').value=r.max_entities;el('threshold').value=r.convergence.threshold_percent;
      el('thresholdval').textContent=r.convergence.threshold_percent+' %';
      el('minsupport').value=r.convergence.min_support;el('extra').value=r.convergence.extra_depth;
      el('extraval').textContent=r.convergence.extra_depth;
      const n=await api('/api/node?qid='+encodeURIComponent(root));
      el('rootqid').textContent=root;el('rootlabel').textContent=n?.label||root;
      el('search').value=root;el('projecttitle').textContent='Portée · '+(n?.label||root);
      el('projectsubtitle').textContent='Recette de projet externe chargée. Le périmètre reste non canonique.';
      await loadBranches();await preview();
    }else{
      el('branches').textContent='Aucune recette de projet chargée.';
      status('Kristal sélectionné. Confirme la racine Wikidata puis calcule le périmètre.');
    }
  }catch(e){status('Démarrage : '+e.message)}
}
boot();
