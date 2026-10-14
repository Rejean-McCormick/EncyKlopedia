
'use strict';
(() => {
  const $ = id => document.getElementById(id);
  const dialog=$('large-job-modal');
  const help=$('convergence-help');
  const number=n=>Number(n||0).toLocaleString('en-US');
  let job=null;
  const feedback=t=>$('large-dialog-feedback').textContent=t;
  const isComplete=s=>s==='completed';
  function update(s){
    if(!s||!s.job)return;
    job=s;
    $('large-dialog-state').textContent=({queued:'Queued',running:'Collecting…',pausing:'Pausing…',paused:'Paused',completed:'Completed',limit_reached:'Target limit reached — incomplete',failed:'Failed',interrupted:'Interrupted'}[s.state]||s.state)+ ' · Job '+s.job.slice(0,8);
    $('large-dialog-selected').textContent=number(s.selected);
    $('large-dialog-expanded').textContent=number(s.expanded);
    $('large-dialog-pending').textContent=number(s.pending);
    $('large-dialog-message').textContent=s.message||'';
    const finite=Number(s.requested_max_entities)>0;
    const p=$('large-dialog-progress');
    if(isComplete(s.state)){p.max=100;p.value=100;$('large-dialog-bar-caption').textContent='Traversal finished for the requested scope. This is not a global species coverage percentage.';}
    else if(finite){p.max=Number(s.requested_max_entities);p.value=Math.min(Number(s.selected||0),p.max);$('large-dialog-bar-caption').textContent=number(s.selected)+' / '+number(s.requested_max_entities)+' QID target (not traversal completeness).';}
    else {p.removeAttribute('value');p.max=100;$('large-dialog-bar-caption').textContent='Unlimited mode · total QID count unknown until traversal ends.';}
    const ready=isComplete(s.state)&&s.output_ready;
    for(const id of ['large-dialog-open','large-dialog-download','large-dialog-copy'])$(id).disabled=!ready;
    $('large-dialog-pause').disabled=!['running','queued'].includes(s.state);
    $('large-dialog-resume').disabled=!['paused','limit_reached','failed','interrupted'].includes(s.state);
    $('large-results').disabled=!ready;
  }
  function show(){if(!dialog.open)dialog.showModal();}
  async function send(route){
    if(!job)return;
    try{
      const res=await fetch(route,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({job:job.job})});
      const data=await res.json();if(!res.ok)throw new Error(data.error||res.statusText);
      feedback(data.message||(route.endsWith('/open')?'Opened results folder in Windows Explorer.':'ZIP file copied to the Windows clipboard; paste in Explorer with Ctrl+V.'));
    }catch(err){feedback('Action failed: '+err.message+' · Use Download Results ZIP instead.');}
  }
  $('large-dialog-open').addEventListener('click',()=>send('/api/large/open'));
  $('large-dialog-copy').addEventListener('click',()=>send('/api/large/copy'));
  $('large-dialog-download').addEventListener('click',()=>{
    if(!job)return;
    const a=document.createElement('a');a.href='/api/large/result.zip?job='+encodeURIComponent(job.job);a.download='skope-'+job.job.slice(0,8)+'-results.zip';document.body.append(a);a.click();a.remove();feedback('Results ZIP download requested. Includes QIDs, settings and summary.');
  });
  $('large-dialog-close').addEventListener('click',()=>dialog.close());
  $('large-results').addEventListener('click',show);
  $('large-dialog-pause').addEventListener('click',()=>$('large-pause').click());
  $('large-dialog-resume').addEventListener('click',()=>{$('large-start').click();});
  $('convergence-help-open').addEventListener('click',()=>help.showModal());
  $('convergence-help-close').addEventListener('click',()=>help.close());
  $('convergence-help-done').addEventListener('click',()=>help.close());
  window.SkopeJobModal={update,show,feedback};
  // Race-safe startup: latest status may arrive before this script loads.
  if(window.SkopeLastLargeStatus)update(window.SkopeLastLargeStatus);
  fetch('/api/large/latest').then(r=>r.ok?r.json():null).then(r=>{if(r)update(r)}).catch(()=>{});
})();
