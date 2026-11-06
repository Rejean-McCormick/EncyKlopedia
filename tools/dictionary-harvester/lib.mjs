/** Independent local-only research harvester. No imports from EncyKlopedia's reader. */
import { createHash } from 'node:crypto';
import { createReadStream, createWriteStream } from 'node:fs';
import { mkdir, readFile, rename, rm, readdir, stat, writeFile } from 'node:fs/promises';
import { dirname, join, resolve, extname, relative } from 'node:path';
import { createGunzip } from 'node:zlib';
import { createInterface } from 'node:readline';
import { Readable, Transform } from 'node:stream';
import { pipeline } from 'node:stream/promises';
import { fileURLToPath } from 'node:url';

export const SOURCE_FILE = fileURLToPath(new URL('./sources.json', import.meta.url));
export const ROOT = fileURLToPath(new URL('../../', import.meta.url));
// Installation: code on C: (repository), corpus on D: (EncyKlopedia data lake).
// Never silently store data inside the source repository.
export const WINDOWS_DATA_ROOT = 'D:\\EncyKlopedia';
export function resolveDataRoot(explicit = process.env.ENCYK_DATA_ROOT, platform = process.platform) {
  if (explicit !== undefined && explicit !== null && String(explicit).trim()) return resolve(String(explicit));
  if (platform === 'win32') return WINDOWS_DATA_ROOT;
  throw Error('Data root required outside Windows: set ENCYK_DATA_ROOT or --data-root');
}
export function dataPaths(dataRoot) {
  const root = resolve(dataRoot);
  return {
    root,
    lexicalSources: join(root, '10_sources', 'lexical'),
    captures: join(root, '10_sources', 'lexical', 'harvester'),
    evidence: join(root, '20_evidence'),
    working: join(root, '30_working', 'lexical', 'harvester'),
    mediatheque: join(root, '50_mediatheque'),
  };
}
export async function assertDataLayout(dataRoot) {
  const paths = dataPaths(dataRoot);
  for (const key of ['lexicalSources', 'evidence', 'working', 'mediatheque']) {
    const parent = key === 'working' ? join(paths.root, '30_working') : paths[key];
    let entry;
    try { entry = await stat(parent); } catch (e) {
      if (e.code === 'ENOENT') throw Error(`Missing data lake directory (${key}): ${parent}`);
      throw e;
    }
    if (!entry.isDirectory()) throw Error(`Not a data directory: ${parent}`);
  }
  return paths;
}
const safeID = /^[a-z0-9][a-z0-9-]{0,79}$/;
const MAX_ENTRY_BYTES = 2_000_000;

export function sha256(data) { return createHash('sha256').update(data).digest('hex'); }
export function validateCatalog(obj) {
  if (obj?.profile !== 'encyklopedia.dictionary-acquisition-sources/0.1.0' || !Array.isArray(obj.sources)) throw Error('Unsupported source catalog');
  const ids = new Set();
  for (const s of obj.sources) {
    if (!safeID.test(s.id) || ids.has(s.id)) throw Error('Duplicate or unsafe source id');
    ids.add(s.id);
    if (!Array.isArray(s.allowed_hosts) || typeof s.homepage !== 'string' || typeof s.format !== 'string' || s.public_reuse !== 'not_assessed') throw Error('Unreviewed source catalog structure');
    if (s.download_url) {
      const u = new URL(s.download_url);
      if (u.protocol !== 'https:' || u.username || u.password || !s.allowed_hosts.includes(u.hostname) || !Number.isSafeInteger(s.max_bytes) || s.max_bytes < 1) throw Error('Unsafe download source');
    }
  }
  return obj;
}
export async function loadCatalog() { return validateCatalog(JSON.parse(await readFile(SOURCE_FILE, 'utf8'))); }
export function sourceByID(catalog, id) { const src = catalog.sources.find(x => x.id === id); if (!src) throw Error('Unknown source id'); return src; }
export function assertSourceURL(source, candidate) {
  const u = new URL(candidate);
  if (u.protocol !== 'https:' || u.username || u.password || u.port || !source.allowed_hosts.includes(u.hostname)) throw Error('Unapproved acquisition URL/host');
  return u.toString();
}
export function validateSnapshotID(value) {
  if (!/^[a-z0-9][a-z0-9-]{0,79}$/.test(value)) throw Error('Unsafe snapshot id');
  return value;
}
export async function fetchSnapshot({source, store, snapshot, fetchImpl = fetch, timeoutMs = 21_600_000}) {
  if (!store) throw Error('Explicit data store required; no writes to code repository');
  if (!source.download_url) throw Error('This source has no official fixed bulk download');
  validateSnapshotID(snapshot);
  let url = assertSourceURL(source, source.download_url);
  const finalDir = resolve(store, 'raw', source.id, snapshot);
  try { await stat(finalDir); throw Error('Immutable snapshot already exists'); } catch (e) { if (e.code !== 'ENOENT') throw e; }
  const staging = `${finalDir}.partial-${process.pid}`;
  await mkdir(dirname(finalDir), {recursive:true});
  await mkdir(staging, {recursive: false});
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    let response;
    for (let redirects = 0; redirects <= 3; redirects++) {
      response = await fetchImpl(url, {redirect:'manual',signal:controller.signal, headers: {'User-Agent':'EncyKlopedia-Research-Harvester/0.1 (local opt-in download)'}});
      if ([301,302,303,307,308].includes(response.status)) {
        if (redirects === 3) throw Error('Too many redirects');
        const next = response.headers.get('location'); if (!next) throw Error('Redirect without location');
        url = assertSourceURL(source, new URL(next, url).toString()); continue;
      }
      break;
    }
    if (response.status !== 200 || !response.body) throw Error(`Remote source HTTP ${response.status}`);
    const declared = Number(response.headers.get('content-length'));
    if (Number.isFinite(declared) && declared > source.max_bytes) throw Error('Remote file exceeds declared size limit');
    const filename = source.format === 'iana-txt' ? 'registry.txt' : source.format === 'wikidata-json-bz2' ? 'lexemes.json.bz2' : 'wiktextract.jsonl.gz';
    const outFile = join(staging, filename);
    const digest = createHash('sha256'); let size=0;
    const meter = new Transform({transform(chunk, _enc, cb) {
      size += chunk.length;
      if (size > source.max_bytes) return cb(Error('Download over source size limit'));
      digest.update(chunk); cb(null, chunk);
    }});
    await pipeline(Readable.fromWeb(response.body), meter, createWriteStream(outFile, {flags:'wx'}));
    if (size === 0) throw Error('Empty download');
    const manifest = {
      profile:'encyklopedia.source-capture/0.1.0', source_id:source.id, snapshot,
      acquired_at:new Date().toISOString(), source_url:url, declared_format:source.format,
      file:filename, bytes:size, sha256:digest.digest('hex'),
      canonical:false, reviewed:false, public_release:false,
      licensing:source.license_review, owner:'candidate-acquisition-to-Skope-kOA-dik'
    };
    await writeFile(join(staging,'capture.json'),JSON.stringify(manifest,null,2)+'\n',{flag:'wx'});
    await mkdir(dirname(finalDir),{recursive:true});
    await rename(staging, finalDir);
    return {directory:finalDir,manifest};
  } catch(e) { await rm(staging,{recursive:true,force:true}); throw e; }
  finally { clearTimeout(timer); }
}
export async function verifyCapture(captureDir) {
  const m=JSON.parse(await readFile(join(captureDir,'capture.json'),'utf8'));
  if (m.profile !== 'encyklopedia.source-capture/0.1.0' || !safeID.test(m.source_id) || !safeID.test(m.snapshot) || !['registry.txt','lexemes.json.bz2','wiktextract.jsonl.gz'].includes(m.file) || m.reviewed !== false || m.public_release !== false || m.canonical !== false) throw Error('Invalid capture manifest');
  const h=createHash('sha256'); let len=0;
  for await (const chunk of createReadStream(join(captureDir,m.file))) { h.update(chunk); len+=chunk.length; }
  if (len !== m.bytes || h.digest('hex') !== m.sha256) throw Error('Capture integrity mismatch');
  return m;
}
export function normalizeKaikkiEntry(raw, sourceId, snapshot) {
  if (!raw || typeof raw !== 'object' || Array.isArray(raw) || typeof raw.word !== 'string' || !raw.word || raw.word.length > 500 || typeof raw.lang_code !== 'string' || !/^[a-zA-Z0-9-]{2,35}$/.test(raw.lang_code)) return null;
  const senses = Array.isArray(raw.senses) ? raw.senses.slice(0,250).map(s => ({
    glosses:Array.isArray(s.glosses)?s.glosses.filter(x=>typeof x==='string').slice(0,30):[],
    tags:Array.isArray(s.tags)?s.tags.filter(x=>typeof x==='string').slice(0,50):[],
    raw_glosses:Array.isArray(s.raw_glosses)?s.raw_glosses.filter(x=>typeof x==='string').slice(0,30):[]
  })) : [];
  const forms=Array.isArray(raw.forms)?raw.forms.slice(0,1000).filter(x=>typeof x?.form==='string').map(x=>({form:x.form,tags:Array.isArray(x.tags)?x.tags.filter(z=>typeof z==='string').slice(0,50):[]})):[];
  return {
    profile:'encyklopedia.lexical-observation/0.1.0', source_id:sourceId, snapshot,
    language_code:raw.lang_code, language_name:typeof raw.lang==='string'?raw.lang:null,
    lemma:raw.word, pos:typeof raw.pos==='string'?raw.pos:null,
    senses,forms,source_page:typeof raw.url === 'string' && raw.url.startsWith('https://')?raw.url:null,
    status:'unreviewed_observation',semantic_id:null,lexeme_id:null,approved_translation:false,
    rights_review:'required_before_any_publication'
  };
}

export async function ingestKaikki({input,output,sourceId,snapshot,maxRecords = Infinity}) {
  if (!safeID.test(sourceId)) throw Error('Invalid source id');
  validateSnapshotID(snapshot);
  if (!Number.isSafeInteger(maxRecords) && maxRecords !== Infinity) throw Error('Bad limit');
  if (maxRecords < 1) throw Error('Limit must be positive');
  const ext=extname(input).toLowerCase();
  if (!['.gz','.jsonl'].includes(ext)) throw Error('Only JSONL or .gz input supported (not Wikidata .bz2)');
  await mkdir(dirname(resolve(output)),{recursive:true});
  try { await stat(output); throw Error('Immutable candidate output already exists'); } catch(e) { if(e.code !== 'ENOENT') throw e; }
  const staging=`${output}.partial-${process.pid}`;
  const writer=createWriteStream(staging,{flags:'wx'});
  const summary={profile:'encyklopedia.lexical-ingest-report/0.1.0',source_id:sourceId,snapshot,
    input_format:'wiktextract-jsonl', rows_seen:0,observations:0,rejected:0,partial:false,
    approved:0, canonical_mappings:0,source_provenance:'unreviewed'};
  const hash=createHash('sha256');
  const stream = createReadStream(input);
  const decoded = ext === '.gz'?stream.pipe(createGunzip()):stream;
  const lineReader = createInterface({input:decoded,crlfDelay:Infinity});
  try {
    for await (const line of lineReader) {
      if (!line.trim()) continue;
      summary.rows_seen++;
      if (Buffer.byteLength(line,'utf8')>MAX_ENTRY_BYTES) {summary.rejected++;continue;}
      let raw;
      try {raw=JSON.parse(line);}catch { summary.rejected++;continue; }
      const normalized=normalizeKaikkiEntry(raw,sourceId,snapshot);
      if (!normalized){summary.rejected++;continue;}
      const encoded=JSON.stringify(normalized)+'\n';
      if(!writer.write(encoded)){await new Promise((ok,fail)=>{writer.once('drain',ok);writer.once('error',fail);});}
      hash.update(encoded); summary.observations++;
      if (summary.rows_seen >= maxRecords) {summary.partial=true;break;}
    }
    writer.end(); await new Promise((ok,fail)=>{writer.once('finish',ok);writer.once('error',fail);});
    await rename(staging, output);
    summary.output_sha256=hash.digest('hex');
    await writeFile(output+'.report.json',JSON.stringify(summary,null,2)+'\n',{flag:'wx'});
    return summary;
  } catch(e) {writer.destroy();await rm(staging,{force:true});throw e;}
}

export function parseIanaRegistry(text) {
  const lines=text.replace(/\r\n?/g,'\n').split('\n');
  const dateMatch=/^File-Date:\s*(\d{4}-\d{2}-\d{2})$/m.exec(text);
  if (!dateMatch) throw Error('Missing IANA registry File-Date');
  const groups=lines.join('\n').split(/^%%\s*$/m);
  const entries=[];
  for(const group of groups.slice(1)) {
    const fields={};
    for(const line of group.split('\n')) {
      const m=/^([A-Za-z-]+):\s*(.*)$/.exec(line);
      if(m){const k=m[1].toLowerCase();(fields[k]??=[]).push(m[2]);}
    }
    if(!fields.type || (!fields.subtag && !fields.tag)) continue;
    entries.push({type:fields.type[0],subtag:fields.subtag?.[0]??null,tag:fields.tag?.[0]??null,
      descriptions:fields.description??[],preferred_value:fields['preferred-value']?.[0]??null,
      deprecated:fields.deprecated?.[0]??null,scope:fields.scope?.[0]??null});
  }
  return {profile:'encyklopedia.iana-candidate-registry/0.1.0',file_date:dateMatch[1],records:entries,verified_against_iana:false};
}
export async function ingestIana({input,output}) {
  const text=await readFile(input,'utf8');const parsed=parseIanaRegistry(text);
  await mkdir(dirname(resolve(output)),{recursive:true});
  await writeFile(output, JSON.stringify(parsed,null,2)+'\n',{flag:'wx'});
  return {records:parsed.records.length,date:parsed.file_date,output};
}
export async function listCaptures(store) {
  if (!store) throw Error('Explicit data store required');
  const root=join(store,'raw');const result=[];
  let sources=[]; try {sources=await readdir(root,{withFileTypes:true});}catch(e){if(e.code==='ENOENT')return result;throw e;}
  for(const s of sources.filter(x=>x.isDirectory())) {
    for(const sn of await readdir(join(root,s.name),{withFileTypes:true})) {
      if(!sn.isDirectory() || sn.name.includes('.partial-'))continue;
      const location=join(root,s.name,sn.name);
      try {const m=JSON.parse(await readFile(join(location,'capture.json'),'utf8'));result.push({source:s.name,snapshot:sn.name,bytes:m.bytes,sha256:m.sha256,reviewed:false});} catch {result.push({source:s.name,snapshot:sn.name,status:'manifest_missing_or_invalid'});}
    }
  }
  return result;
}

/** Read-only inventory of existing raw lexical files; does NOT download, hash, or reclassify them. */
export async function inventoryExistingLexical(dataRoot, {maxEntries = 10000, maxDepth = 7} = {}) {
  if (!Number.isSafeInteger(maxEntries) || maxEntries < 1 || maxEntries > 100000) throw Error('Invalid inventory limit');
  const paths = await assertDataLayout(dataRoot);
  const root = paths.lexicalSources;
  const found = [];
  const stack = [{dir:root,depth:0}];
  let inspected=0;
  while (stack.length) {
    const {dir,depth}=stack.pop();
    const entries=await readdir(dir,{withFileTypes:true});
    for (const e of entries) {
      if (++inspected > maxEntries) throw Error('Inventory entry limit exceeded');
      const abs=join(dir,e.name);
      if (e.isDirectory() && depth < maxDepth) stack.push({dir:abs,depth:depth+1});
      else if (e.isFile() && /\.(?:jsonl|bz2|gz)$/i.test(e.name)) {
        const st=await stat(abs);
        found.push({relative_path:relative(paths.root,abs).replaceAll('\\','/'),bytes:st.size,
          status:'existing_unverified',imported:false,published:false});
      }
    }
  }
  found.sort((a,b)=>a.relative_path.localeCompare(b.relative_path));
  return {data_root:paths.root,source_files:found.length,total_bytes:found.reduce((sum,x)=>sum+x.bytes,0),
    files:found,integrity_verified:false,canonical:false,publication_approved:false};
}
