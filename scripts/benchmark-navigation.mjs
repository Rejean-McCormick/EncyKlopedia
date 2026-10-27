import fs from 'node:fs';
import { performance } from 'node:perf_hooks';
import { StructuralProfiler } from '../server/navigation/profiler.mjs';
import { buildNavigationPlan } from '../server/navigation/planner.mjs';

const baseline = JSON.parse(fs.readFileSync(new URL('../benchmarks/navigation-baseline.json', import.meta.url), 'utf8'));
const full = process.argv.includes('--full') || process.env.KONSTELLATION_BENCH_FULL === '1';
const sizes = full ? [10_000, 100_000, 1_000_000] : [10_000, 100_000];
const ops = ['exists', 'missing_in_view', 'in', 'none_of'];
const relation = (id, fr, valueKind = 'entity') => ({ id, label:{fr,en:fr}, domain:['node'], range:valueKind === 'entity' ? 'node' : 'value', valueKind, operators:ops });
const entities = (count) => Array.from({length:count},(_,i)=>({id:`n:${i}`,type:'node',label:`Node ${i}`}));

function mixed(count) {
  const relations = [
    relation('bench:depends_on','dépend de'), relation('bench:precedes','précède'),
    relation('bench:year','année','integer'), relation('bench:dimension_value','dimension','integer'),
  ];
  const entityCount = Math.max(2, Math.ceil(Math.sqrt(count)));
  const rows = entities(entityCount);
  const assertions = Array.from({length:count},(_,i)=>{
    const subject=`n:${i%entityCount}`; const k=i%4;
    if(k===0) return {id:`a:${i}`,subject,relation:'bench:depends_on',value:`n:${(i+1)%entityCount}`,sourceRefs:[]};
    if(k===1) return {id:`a:${i}`,subject,relation:'bench:precedes',value:`n:${(i+3)%entityCount}`,sourceRefs:[]};
    if(k===2) return {id:`a:${i}`,subject,relation:'bench:year',value:1800+(i%225),sourceRefs:[]};
    return {id:`a:${i}`,subject,relation:'bench:dimension_value',value:i%100,sourceRefs:[]};
  });
  return { registry:{entityTypes:['node'],relations}, entities:rows, assertions, sources:[] };
}

function dense(count) {
  const rel = relation('bench:related','lié à');
  const entityCount = Math.max(32, Math.floor(Math.sqrt(count) / 2));
  const rows = entities(entityCount);
  const assertions = Array.from({length:count},(_,i)=>({
    id:`d:${i}`, subject:`n:${i%entityCount}`, relation:rel.id,
    value:`n:${(i * 17 + 23) % entityCount}`, sourceRefs:[],
  }));
  return { registry:{entityTypes:['node'],relations:[rel]}, entities:rows, assertions, sources:[] };
}

function timeline(count) {
  const year = relation('bench:year','année','integer');
  const precedes = relation('bench:precedes','précède');
  const entityCount = Math.max(2, Math.ceil(Math.sqrt(count)));
  const rows = entities(entityCount);
  const assertions = Array.from({length:count},(_,i)=> i%2===0
    ? {id:`t:${i}`,subject:`n:${i%entityCount}`,relation:year.id,value:1500+(i%525),sourceRefs:[]}
    : {id:`t:${i}`,subject:`n:${i%entityCount}`,relation:precedes.id,value:`n:${(i+1)%entityCount}`,sourceRefs:[]});
  return { registry:{entityTypes:['node'],relations:[year,precedes]}, entities:rows, assertions, sources:[] };
}

function deepDag(count) {
  const dep = relation('bench:depends_on','dépend de');
  const entityCount = Math.max(2, Math.min(count + 1, 120_000));
  const rows = entities(entityCount);
  const assertions = Array.from({length:count},(_,i)=>({
    id:`g:${i}`, subject:`n:${i%entityCount}`, relation:dep.id,
    value:`n:${Math.min(entityCount-1,(i+1)%entityCount)}`, sourceRefs:[],
  }));
  return { registry:{entityTypes:['node'],relations:[dep]}, entities:rows, assertions, sources:[] };
}

function multiscale(count) {
  const cross = relation('bench:cross_scale','interaction inter-échelle');
  const entityCount = Math.max(2, Math.ceil(Math.sqrt(count)));
  const rows = entities(entityCount);
  const scales=['molecular','cellular','tissue','organ','system'];
  const layers=['metabolic','neural','vascular','immune'];
  const assertions = Array.from({length:count},(_,i)=>({
    id:`m:${i}`, subject:`n:${i%entityCount}`, relation:cross.id, value:`n:${(i+7)%entityCount}`, sourceRefs:[],
    coordinates:[{axis:'scale',value:scales[i%scales.length]},{axis:'layer',value:layers[i%layers.length]}],
  }));
  return { registry:{entityTypes:['node'],relations:[cross]}, entities:rows, assertions, sources:[] };
}

function highCardinality(count) {
  const facet = relation('bench:facet','catégorie','string');
  const entityCount = Math.max(2, Math.ceil(Math.sqrt(count)));
  const rows = entities(entityCount);
  const assertions = Array.from({length:count},(_,i)=>({
    id:`h:${i}`, subject:`n:${i%entityCount}`, relation:facet.id, value:`value:${i}`, sourceRefs:[],
  }));
  return { registry:{entityTypes:['node'],relations:[facet]}, entities:rows, assertions, sources:[] };
}

function measure(name, count, factory, ceiling) {
  const input = factory(count);
  const memBefore = process.memoryUsage().heapUsed;
  const t0 = performance.now();
  const profiler = new StructuralProfiler(input);
  const t1 = performance.now();
  const plan = buildNavigationPlan({ profiler, query:{selection:{entityType:'node'}}, lens:null });
  const t2 = performance.now();
  const row = {
    scenario:name, assertions:count,
    profilerMs:Number((t1-t0).toFixed(2)), plannerMs:Number((t2-t1).toFixed(2)),
    heapDeltaMb:Number(((process.memoryUsage().heapUsed-memBefore)/1024/1024).toFixed(2)),
    recipes:plan.views.map(v=>v.id),
  };
  row.withinBaseline = !ceiling || (row.profilerMs<=ceiling.maxProfilerMs && row.plannerMs<=ceiling.maxPlannerMs);
  return row;
}

let failed = false;
const results = [];
for (const size of sizes) {
  const row = measure('mixed', size, mixed, baseline.profiles[String(size)]);
  if (!row.withinBaseline) failed = true;
  results.push(row);
}

// Structural-shape coverage is fixed at 100k to keep normal CI bounded while
// still exercising the pathological families required by the production spec.
const scenarioSize = 100_000;
for (const [name, factory] of Object.entries({ dense, timeline, 'deep-dag':deepDag, multiscale, 'high-cardinality':highCardinality })) {
  const row = measure(name, scenarioSize, factory, baseline.scenarios?.[name]);
  if (!row.withinBaseline) failed = true;
  results.push(row);
}

console.log(JSON.stringify({schemaVersion:'1.0',full,results},null,2));
if(failed) process.exitCode=1;
