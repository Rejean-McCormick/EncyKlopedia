import { resolve, join, relative, isAbsolute } from 'node:path';
import { spawn, spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import {
  loadCatalog, sourceByID, fetchSnapshot, verifyCapture, ingestKaikki,
  ingestIana, listCaptures, inventoryExistingLexical,
  resolveDataRoot, dataPaths, assertDataLayout, validateSnapshotID
} from './lib.mjs';

const HELP = `EncyKlopedia dictionary harvester — code on C:, data on D: (Node 22+)

Usage: node tools/dictionary-harvester/cli.mjs <command> [options]
  sources                           List candidate acquisition sources
  layout                            Check the existing D: data lake without modifying it
  inventory-existing                Read-only inventory of existing lexical dumps on D:
  plan --source ID                  Explain acquisition and expected D: storage
  fetch --source ID --snapshot NAME Explicit HTTPS download to D: lexical sources
  verify --dir PATH                 Verify a captured file against capture.json
  ingest-kaikki --file PATH --source ID --snapshot NAME [--out PATH] [--limit N]
                                    JSONL/gzip -> D: unreviewed working observations
  ingest-iana --file PATH --snapshot NAME [--out PATH]
                                    Local IANA registry -> D: unreviewed working data
  status                            List new harvester captures (not legacy sources)
  index-plan                       Discover already-downloaded Kaikki, UniMorph and Wikidata
  index-run                        Build/resume candidate SQLite lexical index on D: (Python 3.10+)
  index-status                     Index status, without running ingestion
  index-repair                     Repair only incomplete UniMorph sources (v0.3)
  index-lookup --query MOT [--language fr] [--match form]  Search candidates

Optional: --data-root PATH (default on Windows D:\\EncyKlopedia)
          or ENCYK_DATA_ROOT environment variable
No writes under the C: repository; no public publication; no implicit source approval.
`;
function flags(argv) {
  const result = {};
  for(let i=0;i<argv.length;i++) {
    if(!/^--[a-z-]+$/.test(argv[i]) || result[argv[i].slice(2)] !== undefined) throw Error('Invalid/duplicate option');
    if (argv[i] === '--refresh-changed') {result['refresh-changed']='true';continue;}
    if(i+1>=argv.length || argv[i+1].startsWith('--'))throw Error('Missing option value');
    result[argv[i].slice(2)] = argv[++i];
  }
  return result;
}
function required(o,k){ if(!o[k])throw Error('Missing --'+k);return o[k]; }
function outputPathOnDataLake(paths, explicitOutput, defaultOutput) {
  const output = explicitOutput ? resolve(explicitOutput) : defaultOutput;
  const rel = relative(paths.root, output);
  if (!rel || rel === '..' || rel.startsWith('..\\') || rel.startsWith('../') || isAbsolute(rel))
    throw Error('Candidate output must remain inside D: data lake');
  return output;
}
function defaultCandidate(paths, type, source, snapshot) {
  validateSnapshotID(snapshot);
  return join(paths.working, type, source, snapshot + (type === 'iana' ? '.json' : '.jsonl'));
}
export async function main(args=process.argv.slice(2)) {
  const [cmd,...argv]=args;
  if (!cmd || cmd==='--help' || cmd==='help') {console.log(HELP);return;}
  const o=flags(argv);
  if (o.store) throw Error('Obsolete --store: use --data-root to select the D: data lake');
  if (cmd.startsWith('index-')) {
    const commands = {'index-plan':'plan','index-run':'run','index-repair':'repair','index-status':'status','index-lookup':'lookup'};
    if (!commands[cmd]) throw Error('Unknown index command');
    await assertDataLayout(resolveDataRoot(o['data-root']));
    const root = fileURLToPath(new URL('./lexical_indexer.py', import.meta.url));
    const candidates = process.platform === 'win32' ? [['py','-3'],['python']] : [['python3'],['python']];
    let runner;
    for (const c of candidates) {
      const probe = spawnSync(c[0],[...c.slice(1),'--version'],{encoding:'utf8',windowsHide:true});
      if (!probe.error && probe.status === 0 && /Python 3\.(?:1[0-9]|[2-9][0-9])/.test((probe.stdout||'')+(probe.stderr||''))) {runner=c;break;}
    }
    if (!runner) throw Error('Python 3.10+ introuvable : installer Python ou utiliser le lanceur py -3.');
    const params = [root, commands[cmd], '--data-root', resolveDataRoot(o['data-root'])];
    for (const [k,v] of Object.entries(o)) if (k!=='data-root') {
      if (k==='refresh-changed' && v==='true')params.push('--refresh-changed');
      else params.push('--'+k,v);
    }
    const exitCode = await new Promise((accept,reject)=>{
      const child=spawn(runner[0],[...runner.slice(1),...params],{stdio:'inherit',windowsHide:false});
      child.once('error',reject); child.once('close',code=>accept(code));
    });
    if (exitCode !== 0) {process.exitCode=exitCode||1;}
    return;
  }
  const catalog=await loadCatalog();
  let result;
  if(cmd==='sources') result=catalog.sources.map(x=>({id:x.id,name:x.name,format:x.format,download:x.download_url?'opt-in':'discovery-only',public_reuse:x.public_reuse}));
  else if(cmd==='verify') result=await verifyCapture(resolve(required(o,'dir')));
  else {
    // Must fail closed on Linux/CI without an explicit temporary data root.
    const paths=await assertDataLayout(resolveDataRoot(o['data-root']));
    if(cmd==='layout') result={code_location:'the current repository (typically C:)',data_root:paths.root,lexical_sources:paths.lexicalSources,new_capture_store:join(paths.captures,'raw'),evidence:paths.evidence,working:paths.working,mediatheque:paths.mediatheque,data_layout_verified:true,no_files_modified:true};
    else if(cmd==='inventory-existing') result=await inventoryExistingLexical(paths.root);
    else if(cmd==='plan') {const s=sourceByID(catalog,required(o,'source'));result={...s,planned_store:join(paths.captures,'raw',s.id),conditions:['No implicit rights clearance','Do not redownload files already stored in D:','No Kristal identity creation','No public publication','Explicit human review needed']};}
    else if(cmd==='fetch') result=await fetchSnapshot({source:sourceByID(catalog,required(o,'source')),snapshot:required(o,'snapshot'),store:paths.captures});
    else if(cmd==='ingest-kaikki') {
      const s=sourceByID(catalog,required(o,'source'));
      if(s.format!=='wiktextract-jsonl-gz')throw Error('Source is not Wiktextract');
      const limit=o.limit===undefined?Infinity:Number(o.limit);
      result=await ingestKaikki({input:resolve(required(o,'file')),
        output:outputPathOnDataLake(paths,o.out,defaultCandidate(paths,'kaikki',s.id,required(o,'snapshot'))),
        sourceId:s.id,snapshot:required(o,'snapshot'),maxRecords:limit});
    } else if(cmd==='ingest-iana') result=await ingestIana({input:resolve(required(o,'file')),
      output:outputPathOnDataLake(paths,o.out,defaultCandidate(paths,'iana','iana-subtags',required(o,'snapshot')))});
    else if(cmd==='status') result={data_root:paths.root,new_harvester_captures:await listCaptures(paths.captures),existing_legacy_sources_not_included:true,published_dictionaries:0,approval_performed:false};
    else throw Error('Unknown command: '+cmd+'\n'+HELP);
  }
  console.log(JSON.stringify(result,null,2));
}
if(process.argv[1] && import.meta.url.endsWith('/'+process.argv[1].replaceAll('\\','/').split('/').pop())) {
  main().catch(e=>{console.error('[harvester] '+e.message);process.exitCode=1;});
}
