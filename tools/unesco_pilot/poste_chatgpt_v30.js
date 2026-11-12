'use strict';
const $=q=>document.querySelector(q),TOKEN=window.STATION_TOKEN;
let current=null,promptCache='',lastCards='',toastTimer=null;
const esc=s=>String(s??'').replace(/[&<>"']/g,x=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[x]));
const num=v=>Number.isInteger(v)?v.toLocaleString('fr-CA'):'—';
async function api(path,method='GET',body=null){
 const init={method,headers:{}};if(method!=='GET')init.headers['X-Station-Token']=TOKEN;
 if(body!==null)init.body=body;
 const r=await fetch(path,init);const o=await r.json();if(!r.ok)throw Error(o.error||`Erreur HTTP ${r.status}`);return o;
}
function toast(msg,bad=false){const el=$('#toast');el.textContent=msg;el.className='toast'+(bad?' bad':'');clearTimeout(toastTimer);toastTimer=setTimeout(()=>el.classList.add('hidden'),8500);}
function statusLabel(s){return {READY:'Prêt à transmettre',SENT:'Prompt préparé',ERROR:'Import refusé',IMPORTING:'Validation en cours',NEEDS_CONFIRMATION:'HOLD à confirmer',WAITING:'En attente'}[s]||s;}
function render(st){current=st;const occupied=st.lanes.filter(x=>x.job).length;
 $('#articles').textContent=num(st.stats.articles);$('#claims').textContent=num(st.stats.claims);
 $('#occupied').textContent=occupied+' / 10';
 $('#remaining').textContent=num((st.jobs.WAITING||0)+(st.review_index.PENDING||0));
 $('#completed').textContent=num(st.jobs.DONE||0);
 $('#status').innerHTML='<span class="dot '+(st.busy?'busy':'')+'"></span>'+esc(st.busy?st.operation:'Prêt pour la prochaine tâche');
 $('#batch').disabled=$('#prepare').disabled=st.busy;$('#choose').disabled=st.busy;
 $('#freeze').classList.toggle('hidden',!st.v28_frozen);
 const k=st.quality||{};$('#quality').textContent=`Qualité des revues importées : ${num(k.approved||0)} approbations, ${num(k.rejected||0)} rejets, ${num(k.hold||0)} HOLD. Classification provisoire, sans canonisation.`;
 const sig=JSON.stringify(st.lanes);if(sig!==lastCards){lastCards=sig;
 $('#lanes').innerHTML=st.lanes.map(({lane,job:j})=>{
 const number=String(lane).padStart(2,'0');if(!j)return `<article class="lane empty"><div class="lanehead"><span class="number">POSTE ${number}</span><span class="chip">Libre</span></div><h3>En attente de travail</h3><p>Lance le batch global ou reprends les tâches locales.</p></article>`;
 const key=esc(j.id),is27=j.kind==='v27',isError=j.status==='ERROR',hold=j.status==='NEEDS_CONFIRMATION';
 let controls='';
 if(hold){controls=`<button class="btn primary small" data-act="confirm" data-id="${key}">✓ Confirmer la revue</button>`;}
 else if(j.status==='IMPORTING'){controls=`<span class="sub">Importation en cours…</span>`;}
 else {controls=`<button class="btn primary small" data-act="copy" data-id="${key}">📋 Copier + ZIP</button><button class="btn small" data-act="download" data-id="${key}">↓ ZIP</button><button class="btn small" data-act="prompt" data-id="${key}">Prompt</button>`;
 if(isError)controls+=`<button class="btn small" data-act="retry" data-id="${key}">↻ Réessayer</button>`;
 controls+=`<button class="btn ghost small" data-act="skip" data-id="${key}">Ignorer</button>`;}
 return `<article class="lane" data-job="${key}"><div class="lanehead"><span class="number">POSTE ${number} · ${is27?'KRISTAL':'UNESCO'}</span><span class="chip ${is27?'':'v28'} ${isError?'error':hold?'warn':''}">${esc(statusLabel(j.status))}</span></div><div><h3>${esc(is27?j.key:`${j.count} correspondances à examiner`)}</h3><p>${esc(is27?`${j.count} article(s) Wikipédia · delta JSON`:`${j.id} · décisions documentaires`)} · ${esc(j.sent_utc?'Tâche préparée pour transfert':'Tâche prête')}</p></div>${hold?`<div class="errorline">À confirmer : ${j.review_approved} approuvé(s), ${j.review_rejected} rejeté(s), ${j.review_hold} HOLD. Retour abrégé ou tout-HOLD.</div>`:''}${j.error?`<div class="errorline">${esc(j.error)}</div>`:''}<div class="laneactions">${controls}</div></article>`;
 }).join('');}
 const logs=st.events.map(x=>x).join('\n');const el=$('#console');if(el.textContent!==logs){el.textContent=logs||'Aucune opération.';el.scrollTop=el.scrollHeight;}
 $('#receipts').innerHTML=(st.receipts.length?st.receipts.map(r=>{
 const cls=r.status==='OK'?'ok':r.status==='EN_ATTENTE'?'wait':'bad';return `<div class="receipt"><span class="${cls}">${esc(r.status)}</span> · ${esc(r.filename)}<small>${esc(r.detail)}${r.job_id?' · '+esc(r.job_id):''}</small></div>`;
 }).join(''):'<p class="sub">Aucun retour reçu.</p>');
 $('#reopen').disabled=st.busy||!(st.review_index.HOLD>0);
 $('#software').disabled=st.busy;
 $('#updates').innerHTML=st.updates?.length?st.updates.map(u=>`<div class="receipt"><span class="${u.status==='APPLIED'?'ok':'wait'}">${esc(u.status)}</span> · ${esc(u.id)} ${u.status==='APPLIED'?`<button class="btn small warn" data-rollback="${esc(u.id)}">↶ Retour arrière</button>`:''}</div>`).join(''):'Aucune mise à jour logicielle récente.';
}
async function refresh(){try{render(await api('/api/state'));}catch(e){$('#status').textContent='Serveur local indisponible';}}
function openPrompt(text,title='Instructions de la tâche'){$('#modalTitle').textContent=title;$('#promptText').value=text;promptCache=text;$('#modal').classList.remove('hidden');}
function closePrompt(){$('#modal').classList.add('hidden');}
async function copyText(text){try{await navigator.clipboard.writeText(text);return true;}catch(e){openPrompt(text,'Copier avec Ctrl+C');$('#promptText').focus();$('#promptText').select();try{return document.execCommand('copy');}catch{return false;}}}
function download(jid){const a=document.createElement('a');a.href='/api/bundle/'+encodeURIComponent(jid);a.download='';document.body.appendChild(a);a.click();a.remove();}
async function action(type,id){try{
 if(type==='download'){download(id);return;}
 if(type==='retry'){await api('/api/retry/'+encodeURIComponent(id),'POST');toast('Tâche remise en file. Dépose le ZIP corrigé ou recopie les instructions.');return refresh();}
 if(type==='skip'){if(!window.confirm(`Ignorer ${id} ? Cette décision peut être annulée en réactivant la tâche depuis le système.`))return;await api('/api/skip/'+encodeURIComponent(id),'POST');toast('Tâche ignorée; poste renouvelé.');return refresh();}
 if(type==='confirm'){if(!window.confirm('Confirmer explicitement que la revue partielle a été examinée, et importer ses décisions ? Les candidats non fournis resteront HOLD.'))return;await api('/api/confirm-hold/'+encodeURIComponent(id),'POST');toast('Lot tout-HOLD clôturé; poste renouvelé.');return refresh();}
 if(type==='copy')download(id);
 const p=(await api('/api/prompt/'+encodeURIComponent(id))).prompt;
 if(type==='prompt'){openPrompt(p,'Instructions '+id);return;}
 // Browser file-paste into ChatGPT is never guaranteed.
 const n=await api('/api/copy/'+encodeURIComponent(id),'POST');
 if(!n.ok){const ok=await copyText(p);toast(ok?'Instructions copiées; ZIP téléchargé à joindre dans ChatGPT.':'ZIP téléchargé. Ouvre le prompt pour copier ses instructions.',!ok);}
 else toast('Instructions et fichier préparés dans le presse-papiers Windows. Si ChatGPT ne colle que le texte, joins le ZIP téléchargé.');
 await api('/api/sent/'+encodeURIComponent(id),'POST');await refresh();
 }catch(e){toast(e.message,true);}}
$('#lanes').addEventListener('click',e=>{const b=e.target.closest('button[data-act]');if(b)action(b.dataset.act,b.dataset.id);});
async function background(endpoint,label){try{await api(endpoint,'POST');toast(label);setTimeout(refresh,400);}catch(e){toast(e.message,true);}}
$('#batch').addEventListener('click',()=>background('/api/batch','Batch local global démarré. Le journal affichera les étapes.'));
$('#prepare').addEventListener('click',()=>background('/api/prepare','Tâches locales en cours de préparation.'));
$('#reopen').addEventListener('click',async()=>{if(!confirm('Remettre volontairement 500 anciennes propositions HOLD dans la file de revue ?'))return;try{const d=await api('/api/reopen-holds','POST');toast(`${d.reopened} propositions HOLD remises dans la file.`);}catch(e){toast(e.message,true);}});
$('#choose').addEventListener('click',()=>$('#files').click());$('#dropPick').addEventListener('click',e=>{e.stopPropagation();$('#files').click();});$('#drop').addEventListener('click',e=>{if(!e.target.closest('button'))$('#files').click();});
$('#drop').addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();$('#files').click();}});
$('#closeModal').addEventListener('click',closePrompt);$('#modal').addEventListener('click',e=>{if(e.target===$('#modal'))closePrompt();});
$('#copyModal').addEventListener('click',async()=>toast(await copyText(promptCache)?'Instructions copiées.':'Ctrl+A puis Ctrl+C pour copier.',false));
async function upload(files){try{const fd=new FormData();for(const f of files)fd.append('returns',f,f.name);
 const res=await api('/api/upload-batch','POST',fd);toast(`${res.queued_files} archive(s) reçue(s) : validation et importation en cours. Consulte les retours en bas.`);
}catch(e){toast(e.message,true);}refresh();}
$('#files').addEventListener('change',e=>{if(e.target.files.length)upload([...e.target.files]);e.target.value='';});
$('#software').addEventListener('click',()=>$('#softwareFile').click());
$('#softwareFile').addEventListener('change',async e=>{const f=e.target.files[0];e.target.value='';if(!f)return;
 try{const r=await fetch('/api/update/stage',{method:'POST',headers:{'X-Station-Token':TOKEN,'Content-Type':'application/zip'},body:f});const obj=await r.json();if(!r.ok)throw Error(obj.error||'Overlay refusé');
 const files=obj.files.map(x=>`${x.overwrite?'REMPLACE':'AJOUTE'} ${x.path}`).join('\n');
 const msg=`Fichiers : ${obj.files.length}\n\n${files}\n\nATTENTION : SHA-256 vérifie l'intégrité, pas la confiance dans le code. Aucun fichier n'a encore été installé.\n\nInstaller cet overlay et conserver une sauvegarde ?`;
 if(window.confirm(msg)){
  const result=await api('/api/update/apply/'+encodeURIComponent(obj.id),'POST');toast(`${result.installed} fichiers installés avec sauvegardes. Ferme puis relance l'interface.`);
 }else toast('Overlay seulement prévalidé; aucune installation effectuée.');
 }catch(ex){toast(ex.message,true);}refresh();
});
$('#updates').addEventListener('click',async e=>{const b=e.target.closest('button[data-rollback]');if(!b)return;
 if(!confirm(`Annuler l'installation ${b.dataset.rollback} ? L'interface devra être redémarrée.`))return;
 try{await api('/api/update/rollback/'+encodeURIComponent(b.dataset.rollback),'POST');toast('Retour arrière logiciel effectué. Redémarre l’interface.');refresh();}catch(ex){toast(ex.message,true);}
});
const drop=$('#drop');drop.addEventListener('dragover',e=>{e.preventDefault();drop.classList.add('hover');});drop.addEventListener('dragleave',()=>drop.classList.remove('hover'));
drop.addEventListener('drop',e=>{e.preventDefault();drop.classList.remove('hover');if(e.dataTransfer.files.length)upload([...e.dataTransfer.files]);});
refresh();setInterval(refresh,2500);
