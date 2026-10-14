'use strict';
// No API calls or recipe mutations: density is computed only from the supplied report.
(() => {
  const $=id=>document.getElementById(id), canvas=$('graph'), ctx=canvas.getContext('2d');
  const base=document.createElement('canvas');base.width=1200;base.height=650;
  const bg=base.getContext('2d'), ns='http://www.w3.org/2000/svg';
  let nodes=[], edges=[], byId=new Map(), adjacency=new Map(), positions=new Map(), layers=new Map();
  let rootId='', pinned=false, hovered=null, frame=0, reportTruncated=false;
  const value=id=>Number($('density-'+id).value);
  const color=i=>`hsl(${value('hue-'+i)},75%,${i===2?65:72}%)`;
  const degree=id=>adjacency.get(id)?.size||0;
  const visible=id=>degree(id)>=value('min') && $('density-show-'+layers.get(id)).checked;
  function element(tag,attrs={},text){const e=document.createElementNS(ns,tag);for(const [k,v] of Object.entries(attrs)){if(k==='style'){for(const rule of v.split(';')){const at=rule.indexOf(':');if(at>0)e.style.setProperty(rule.slice(0,at),rule.slice(at+1));}}else e.setAttribute(k,v);}if(text!==undefined)e.textContent=text;return e;}
  // A breadth-first spanning forest gives a stable, topology-based layout.
  // Every report edge is still drawn; the forest only determines coordinates.
  function layout(){
    positions=new Map();const seen=new Set(), children=new Map(), roots=[], order=[], depths=new Map();
    for(const seed of [rootId,...nodes.map(n=>n.id)]){
      if(!byId.has(seed)||seen.has(seed))continue;roots.push(seed);seen.add(seed);depths.set(seed,0);
      const queue=[seed];for(let i=0;i<queue.length;i++){
        const id=queue[i];order.push(id);const kids=[];
        for(const next of adjacency.get(id)){if(seen.has(next))continue;seen.add(next);kids.push(next);depths.set(next,depths.get(id)+1);queue.push(next);}
        children.set(id,kids);
      }
    }
    const weights=new Map();for(const id of [...order].reverse())weights.set(id,Math.max(1,children.get(id).reduce((s,k)=>s+weights.get(k),0)));
    const total=roots.reduce((s,id)=>s+weights.get(id),0)||1, intervals=new Map();let offset=0;
    for(const id of roots){const span=2*Math.PI*weights.get(id)/total;intervals.set(id,[offset,span]);offset+=span;}
    const maxDepth=Math.max(1,...depths.values());
    for(const id of order){const [start,span]=intervals.get(id),angle=start+span/2-Math.PI/2;
      const d=depths.get(id), radius=roots.length===1?d/maxDepth:(d+1)/(maxDepth+1);
      positions.set(id,{x:600+Math.cos(angle)*radius*530,y:325+Math.sin(angle)*radius*275});
      let cursor=start;for(const child of children.get(id)){const size=span*weights.get(child)/weights.get(id);intervals.set(child,[cursor,size]);cursor+=size;}
    }
  }
  function paint(){ctx.clearRect(0,0,1200,650);ctx.drawImage(base,0,0);if(hovered&&visible(hovered)){
    const p=positions.get(hovered);ctx.strokeStyle='#fff';ctx.lineWidth=2;ctx.beginPath();ctx.arc(p.x,p.y,10,0,Math.PI*2);ctx.stroke();
  }}
  function draw(){
    const lo=value('low'),hi=value('high'), counts=[0,0,0], shown=[0,0,0];layers=new Map();
    for(const n of nodes){const d=degree(n.id),layer=d>=hi?2:d>=lo?1:0;layers.set(n.id,layer);counts[layer]++;}
    for(let i=0;i<3;i++){$('density-swatch-'+i).style.color=color(i);$('density-count-'+i).textContent=counts[i];}
    bg.clearRect(0,0,1200,650);let lineCount=0;
    // Dense links and nodes are painted first, underneath the other two layers.
    for(const layer of [2,1,0]){
      bg.strokeStyle=color(layer);bg.fillStyle=color(layer);bg.globalAlpha=layer===2?value('opacity')/100:layer===1?.45:.8;bg.lineWidth=layer===2?.7:layer===1?1:1.2;bg.beginPath();
      for(const e of edges){if(!visible(e.source)||!visible(e.target)||Math.max(layers.get(e.source),layers.get(e.target))!==layer)continue;const a=positions.get(e.source),b=positions.get(e.target);bg.moveTo(a.x,a.y);bg.lineTo(b.x,b.y);lineCount++;}bg.stroke();
      for(const n of nodes){if(layers.get(n.id)!==layer||!visible(n.id))continue;const p=positions.get(n.id);bg.beginPath();bg.arc(p.x,p.y,n.id===rootId?6:layer===2?3.5:1.8,0,Math.PI*2);bg.fill();shown[layer]++;}
    }
    bg.globalAlpha=1;bg.font='14px Segoe UI, sans-serif';const boxes=[];let labels=0;
    const ranked=[...nodes].sort((a,b)=>(b.id===rootId)-(a.id===rootId)||degree(b.id)-degree(a.id));
    for(const n of ranked){if(labels>=value('labels'))break;if(!visible(n.id))continue;const p=positions.get(n.id),name=(n.label||n.id).slice(0,32),w=bg.measureText(name).width+8;
      const x=Math.min(1190-w,Math.max(5,p.x+7)),y=Math.max(18,p.y-7),box={x,y,w};
      if(boxes.some(b=>x<b.x+b.w&&x+w>b.x&&Math.abs(y-b.y)<20))continue;
      boxes.push(box);bg.fillStyle='#09121de8';bg.fillRect(x-3,y-15,w,20);bg.fillStyle=color(layers.get(n.id));bg.fillText(name,x,y);labels++;
    }
    $('graphinfo').textContent=`${shown.reduce((a,b)=>a+b,0)}/${nodes.length} entities · ${lineCount}/${edges.length} links · ${reportTruncated?'truncated report':'complete preview report'}`;
    $('density-empty').hidden=shown.some(Boolean);$('density-empty').textContent=nodes.length?'No entities visible with these filters.':'No entities in this report.';
    if(hovered&&!visible(hovered)){hovered=null;pinned=false;}
    paint();detail();
  }
  function detail(){
    const n=byId.get(hovered);$('density-detail').hidden=!n;if(!n)return;
    $('density-title').textContent=(pinned?'Pinned magnifier · ':'Magnifier · ')+(n.label||n.id)+' · '+n.id;
    const neighbors=[...adjacency.get(n.id)].filter(visible).sort((a,b)=>degree(b)-degree(a)||a.localeCompare(b));
    const selected=neighbors.slice(0,12), ids=new Set([n.id,...selected]);
    const links=edges.filter(e=>ids.has(e.source)&&ids.has(e.target));
    $('density-summary').textContent=`${degree(n.id)} neighbors in report · ${neighbors.length} visible · ${selected.length} shown in magnifier (maximum 12) · ${links.length} links between these entities. Enlarged neighborhood view; labels are not proof of parent/child relationships.`;
    const svg=$('density-lens');svg.replaceChildren();const coords=new Map([[n.id,{x:500,y:170}]]),spread=45+value('zoom')*24;
    selected.forEach((id,i)=>{const left=i%2===0,row=Math.floor(i/2),count=Math.ceil((selected.length-(left?0:1))/2);coords.set(id,{x:500+(left?-1:1)*(160+spread),y:count===1?170:35+row*270/(count-1)});});
    for(const e of links){const a=coords.get(e.source),b=coords.get(e.target);const line=element('line',{x1:a.x,y1:a.y,x2:b.x,y2:b.y,style:`stroke:${color(Math.max(layers.get(e.source),layers.get(e.target)))};stroke-width:1.3`});line.append(element('title',{},e.property||e.pid||'Relation'));svg.append(line);}
    for(const id of ids){const pos=coords.get(id),node=byId.get(id),group=element('g');group.append(element('circle',{cx:pos.x,cy:pos.y,r:id===n.id?8:5,fill:color(layers.get(id))}));
      const center=id===n.id,left=pos.x<500,x=center?500:pos.x+(left?-12:12),anchor=center?'middle':left?'end':'start';
      const label=element('text',{x,y:pos.y+(center?-20:-4),'text-anchor':anchor,style:'paint-order:stroke;stroke:#0c1824;stroke-width:4px;stroke-linejoin:round;fill:#eef6ff'},(node.label||id).slice(0,30));label.append(element('title',{},(node.label||id)+' · '+id));group.append(label,element('text',{x,y:pos.y+(center?30:14),'text-anchor':anchor,style:'font-size:11px;fill:#9fb5c8'},id+' · '+degree(id)+' neighbors'));svg.append(group);
    }
  }
  const controls=['low','high','min','opacity','labels','zoom'];
  for(const id of controls)$('density-'+id).addEventListener('input',()=>{
    if(id==='low'&&value('low')>=value('high'))$('density-high').value=value('low')+1;
    if(id==='high'&&value('high')<=value('low'))$('density-low').value=value('high')-1;
    for(const k of controls)$('density-'+k+'-value').textContent=value(k);
    draw();
  });
  for(let i=0;i<3;i++){ $('density-hue-'+i).addEventListener('input',draw);$('density-show-'+i).addEventListener('change',draw); }
  function focus(id,lock=false){if(!byId.has(id)||!visible(id))return;hovered=id;pinned=lock;paint();detail();}
  canvas.addEventListener('pointermove',event=>{
    if(pinned)return;const rect=canvas.getBoundingClientRect(),x=(event.clientX-rect.left)*1200/rect.width,y=(event.clientY-rect.top)*650/rect.height;
    cancelAnimationFrame(frame);frame=requestAnimationFrame(()=>{if(pinned)return;let closest=null,distance=(18*1200/rect.width)**2;
      for(const n of nodes){if(!visible(n.id))continue;const p=positions.get(n.id),d=(p.x-x)**2+(p.y-y)**2;if(d<distance){closest=n.id;distance=d;}}
      hovered=closest;paint();detail();
    });
  });
  canvas.addEventListener('pointerleave',()=>{cancelAnimationFrame(frame);if(!pinned){hovered=null;paint();detail();}});
  canvas.addEventListener('click',()=>{if(hovered){pinned=!pinned;detail();}});
  function unpin(){pinned=false;hovered=null;$('density-pick').value='';paint();detail();}
  $('density-unpin').addEventListener('click',unpin);document.addEventListener('keydown',e=>{if(e.key==='Escape')unpin();});
  $('density-pick').addEventListener('change',()=>{const query=$('density-pick').value.trim();const n=nodes.find(n=>n.id===query||`${n.label||n.id} · ${n.id}`===query||(n.label||'').toLocaleLowerCase()===query.toLocaleLowerCase());if(n){if(!visible(n.id)){$('density-min').value=0;$('density-min-value').textContent='0';$('density-show-'+layers.get(n.id)).checked=true;draw();}focus(n.id,true);}});
  function reset(){for(const [k,v] of Object.entries({low:3,high:10,min:0,opacity:25,labels:12,zoom:2})){$('density-'+k).value=v;$('density-'+k+'-value').textContent=v;}for(let i=0;i<3;i++){$('density-show-'+i).checked=true;$('density-hue-'+i).value=[35,165,220][i];}unpin();draw();}
  $('density-reset').addEventListener('click',reset);
  window.SkopeDensity={
    render(report,root){cancelAnimationFrame(frame);rootId=root;nodes=report.nodes||[];byId=new Map(nodes.map(n=>[n.id,n]));adjacency=new Map(nodes.map(n=>[n.id,new Set()]));edges=(report.edges||[]).filter(e=>byId.has(e.source)&&byId.has(e.target));
      for(const e of edges){if(e.source===e.target)continue;adjacency.get(e.source).add(e.target);adjacency.get(e.target).add(e.source);}
      reportTruncated=!!report.truncated;const max=Math.max(10,...nodes.map(n=>degree(n.id)));$('density-low').max=max;$('density-high').max=max+1;$('density-min').max=max;
      for(const id of ['low','high','min'])$('density-'+id+'-value').textContent=value(id);
      if(value('low')>=value('high')){$('density-high').value=value('low')+1;$('density-high-value').textContent=value('high');}
      const options=document.createDocumentFragment();for(const n of nodes){const o=document.createElement('option');o.value=`${n.label||n.id} · ${n.id}`;options.append(o);}$('density-options').replaceChildren(options);
      hovered=null;pinned=false;layout();draw();
    },
    clear(){cancelAnimationFrame(frame);nodes=[];edges=[];byId.clear();adjacency.clear();positions.clear();hovered=null;pinned=false;$('density-options').replaceChildren();$('density-pick').value='';draw();$('graphinfo').textContent='Recalculate to display';}
  };
})();
