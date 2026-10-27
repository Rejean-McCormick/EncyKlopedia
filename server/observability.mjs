import { versionInfo } from './version.mjs';
import { randomUUID } from 'node:crypto';

const timings = new Map();
const counters = new Map();
const gauges = new Map();
const MAX_SAMPLES = 512;

export function requestId(headerValue) {
  const value = String(headerValue || '');
  return /^[A-Za-z0-9._:-]{8,128}$/.test(value) ? value : randomUUID();
}
export function increment(name, labels = {}) {
  const key = `${name}|${JSON.stringify(labels)}`;
  counters.set(key, (counters.get(key) || 0) + 1);
}
export function observe(name, value, labels = {}) {
  const key = `${name}|${JSON.stringify(labels)}`;
  const list = timings.get(key) || [];
  list.push(Number(value) || 0); if (list.length > MAX_SAMPLES) list.shift(); timings.set(key, list);
}
export function gauge(name, value, labels = {}) { gauges.set(`${name}|${JSON.stringify(labels)}`, Number(value) || 0); }
function percentile(values, p) {
  if (!values.length) return 0; const sorted = [...values].sort((a,b)=>a-b); return sorted[Math.min(sorted.length-1,Math.floor((sorted.length-1)*p))];
}
function splitKey(key) { const at=key.indexOf('|'); return { name:key.slice(0,at), labels:JSON.parse(key.slice(at+1)||'{}') }; }
export function metricsSnapshot() {
  return {
    schemaVersion:'1.0',
    counters:[...counters].map(([key,value])=>({...splitKey(key),value})),
    timings:[...timings].map(([key,values])=>({...splitKey(key),count:values.length,p50:percentile(values,.5),p95:percentile(values,.95),p99:percentile(values,.99)})),
    gauges:[...gauges].map(([key,value])=>({...splitKey(key),value})),
  };
}
export function log(level, event, fields = {}) {
  const configured = process.env.KONSTELLATION_LOG_LEVEL || (process.env.NODE_ENV === 'test' ? 'silent' : 'info');
  const rank={silent:99,error:40,warn:30,info:20,debug:10};
  if ((rank[level]||20) < (rank[configured]||20) || configured==='silent') return;
  const safe = Object.fromEntries(Object.entries(fields).filter(([key]) => !/payload|token|authorization|secret/i.test(key)));
  const line=JSON.stringify({timestamp:new Date().toISOString(),level,event,service:'konstellation',version:versionInfo().version,...safe});
  (level==='error'?console.error:level==='warn'?console.warn:console.log)(line);
}
