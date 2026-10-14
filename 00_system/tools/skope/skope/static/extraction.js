"use strict";
(() => {
  const $ = id => document.getElementById(id);
  let check = null, job = null, busy = false, timer = null;
  const list = $('extract-profile'), source = $('extract-source');
  const setSummary = text => { $('extract-summary').textContent = text; };
  const feedback = text => { $('extract-feedback').textContent = text; };
  async function api(path, body) {
    const res = await fetch(path, body === undefined ? {} : {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || ('HTTP '+res.status));
    return data;
  }
  const selected = () => ({profile:list.value,source_job:source.value.trim() || null});
  function invalidate() {
    check = null;
    $('extract-start').disabled = true;
    setSummary('Settings changed. Click Check sources to verify the inventory, dump and fast-access index.');
  }
  list.addEventListener('change', invalidate);
  source.addEventListener('input', invalidate);
  async function preflight() {
    $('extract-start').disabled = true;
    setSummary('Checking source identity, random access, inventory and disk space…');
    try {
      const current = selected();
      check = await api('/api/extract/preflight', current);
      if (list.value !== current.profile || (source.value.trim() || null) !== current.source_job) return;
      $('extract-start').disabled = !check.ready;
      const lines = [check.ready ? 'READY · '+check.total.toLocaleString('en-US')+' QIDs · batches of '+check.batch_size : 'BLOCKED · '+check.blockers.length+' issue(s)'];
      if (check.source) lines.push('Dump: '+check.source.dump+'\nVerified manifest: '+(check.source.verified ? 'yes' : 'no')+' · Random access: '+(check.source.random_access_ready ? 'ready' : 'unavailable'));
      for(const b of check.blockers || []) lines.push('• '+b);
      lines.push('No full-dump scan or canonical Kristal write.');
      setSummary(lines.join('\n'));
    } catch (err) { check=null;setSummary('Check failed: '+err.message); }
  }
  $('extract-preflight').addEventListener('click', preflight);
  async function launch(resume = null) {
    if (busy) return;
    if (!check || !check.ready) { await preflight(); if (!check || !check.ready) return; }
    if (!window.confirm('Extract '+check.total.toLocaleString('en-US')+' complete Wikidata entities from the verified dump on D:?\n\n'+
      'No full dump scan, no automatic index build, no changes to Kristal canon. Work may consume disk space and take time.')) return;
    busy=true;
    try {
      const out=await api('/api/extract/start', {...selected(),resume,confirmed:true});
      render(out); $('extract-modal').showModal();setSummary('Extraction started: '+out.job.slice(0,8)+' · '+out.processed+' / '+out.total);
    } catch(err){setSummary('Extraction could not start: '+err.message);}
    finally{busy=false;}
  }
  $('extract-start').addEventListener('click',()=>launch());
  function render(s) {
    if (!s || !s.job) return;
    job=s;
    $('extract-dialog-state').textContent=s.state.toUpperCase()+' · '+s.job.slice(0,8);
    $('extract-done').textContent=Number(s.processed||0).toLocaleString('en-US');
    $('extract-total').textContent=Number(s.total||0).toLocaleString('en-US');
    $('extract-batches').textContent=Number(s.chunks||0).toLocaleString('en-US');
    $('extract-progress').max=s.total||1;$('extract-progress').value=Math.min(s.processed||0,s.total||1);
    $('extract-message').textContent=s.message||'';
    $('extract-view').disabled=false;
    $('extract-pause').disabled=s.state!=='running'&&s.state!=='queued';
    $('extract-resume').disabled=!['paused','interrupted','failed','missing_source_records'].includes(s.state);
    $('extract-open').disabled=!s.evidence_ready;
    $('extract-copy-path').disabled=!s.evidence_ready;
    clearTimeout(timer);
    if (['running','queued','finalizing'].includes(s.state)) timer=setTimeout(refresh,2000);
  }
  async function refresh() {
    if(!job)return;
    try{render(await api('/api/extract/status?job='+encodeURIComponent(job.job)));}
    catch(err){feedback('Status unavailable: '+err.message);}
  }
  $('extract-view').addEventListener('click',()=>{if(job&&!$('extract-modal').open)$('extract-modal').showModal();refresh();});
  $('extract-close').addEventListener('click',()=>$('extract-modal').close());
  $('extract-pause').addEventListener('click',async()=>{if(!job)return;try{const result=await api('/api/extract/pause',{job:job.job});feedback(result.message);setTimeout(refresh,1200);}catch(err){feedback(err.message);}});
  $('extract-resume').addEventListener('click',()=>{if(job)launch(job.job);});
  $('extract-open').addEventListener('click',async()=>{if(!job)return;try{const result=await api('/api/extract/open',{job:job.job});feedback(result.message);}catch(err){feedback(err.message);}});
  $('extract-copy-path').addEventListener('click',async()=>{if(!job||!job.evidence_ready)return;try{await navigator.clipboard.writeText(job.evidence_path);feedback('Evidence folder path copied.');}catch(err){feedback('Copy blocked: '+err.message);}});
  async function init() {
    try {
      const opts=await api('/api/extract/profiles');
      list.replaceChildren();
      for(const opt of opts){const item=document.createElement('option');item.value=opt.id;item.textContent=opt.title;list.append(item);}
      if(!opts.length){setSummary('No extraction profile JSON installed under config/extraction-profiles.');return;}
      const latest=await api('/api/extract/latest');
      if(latest && latest.job){render(latest);source.value=latest.source_job;}
      else {const inventory=await api('/api/large/latest');if(inventory && inventory.state==='completed')source.value=inventory.job;}
      if(source.value)await preflight();
    } catch(err){setSummary('Initialization failed: '+err.message);}
  }
  init();
})();
