// Optional, read-only, local Kristal v9 reader. Nothing here publishes, activates,
// validates domain truth, or modifies upstream canonical/derived content.
// Discovery 1.0 and Arketype are advisory, never permission or an executable plan.
import fs from 'node:fs';
import path from 'node:path';
import { createHash } from 'node:crypto';
import { fail } from '../errors.mjs';
import { semanticLabel, readableNodeLabel } from '../../src/lib/semantic-display.mjs';

const SHA = /^sha256:[a-f0-9]{64}$/;
const FORMAT = 'kristal.discovery/1.0';
const MAX_JSON = 12 * 1024 * 1024;
const isObject = x => x !== null && typeof x === 'object' && !Array.isArray(x);
const digest = bytes => 'sha256:' + createHash('sha256').update(bytes).digest('hex');
const id = (prefix, name) => `${prefix}:${createHash('sha256').update(name).digest('hex').slice(0, 28)}`;
const safeText = (v, max=512) => typeof v === 'string' && v.length > 0 && v.length <= max && !/[\x00-\x1f\x7f]/.test(v);
const check = (ok, message) => { if (!ok) fail('KRISTAL_LOCAL_INVALID', message, 422); };

function localOnly() {
  const host = process.env.HOST || '127.0.0.1';
  check((process.env.KONSTELLATION_DEPLOYMENT_PROFILE || 'local') === 'local' &&
    ['127.0.0.1','localhost','::1'].includes(host) &&
    process.env.KONSTELLATION_ANONYMOUS_READONLY !== 'true' &&
    process.env.KONSTELLATION_PUBLIC_READONLY !== 'true',
  'La lecture du Kristal local v9 exige un serveur local privé sur loopback.');
}
function rootOf(config, base) {
  localOnly();
  check(safeText(config?.directory, 4096), 'Chemin local explicitement configuré requis.');
  let root;
  try { root=fs.realpathSync(path.resolve(base, config.directory)); }
  catch { fail('KRISTAL_LOCAL_UNAVAILABLE', 'Le dossier du Kristal est introuvable.', 422); }
  check(fs.statSync(root).isDirectory(), 'Le chemin Kristal n’est pas un dossier.');
  return root;
}
function checkedFile(root, relative, maxBytes=MAX_JSON) {
  check(safeText(relative, 500) && relative.split(/[\\/]/).every(part=>part && part!=='.' && part!=='..') &&
    !path.isAbsolute(relative) && !/^[A-Za-z]:/.test(relative), 'Chemin de ressource interdit.');
  let filename, info, real;
  try {
    filename=path.resolve(root,relative);
    info=fs.lstatSync(filename); real=fs.realpathSync(filename);
  } catch { fail('KRISTAL_LOCAL_UNAVAILABLE','Ressource Kristal absente.',422); }
  let cursor = root;
  for (const component of relative.split(/[\\/]/)) {
    cursor = path.join(cursor, component);
    check(!fs.lstatSync(cursor).isSymbolicLink(), 'Lien symbolique non admis.');
  }
  check(real.startsWith(root+path.sep) && info.isFile() && !info.isSymbolicLink() &&
    path.relative(root,real).split(path.sep).every(Boolean) &&
    info.size<=maxBytes, 'Chemin, type ou capacité de la ressource non autorisés.');
  return {filename,size:info.size};
}
function bytesFor(root, relative, max=MAX_JSON, declared=null) {
  const f=checkedFile(root,relative,max);
  if (declared) check(Number.isSafeInteger(declared.size_bytes) && declared.size_bytes===f.size &&
    SHA.test(declared.sha256), 'Taille ou empreinte d’inventaire incohérente.');
  const bytes=fs.readFileSync(f.filename);
  if(declared) check(digest(bytes)===declared.sha256,'Empreinte des octets différente de l’inventaire.');
  return bytes;
}
function jsonFor(root,relative,max=MAX_JSON,declared=null) {
  let data;
  try { data=JSON.parse(bytesFor(root,relative,max,declared).toString('utf8')); }
  catch(e) { if(e?.code) throw e; fail('KRISTAL_LOCAL_INVALID','Document JSON non conforme.',422); }
  return data;
}
function discoveryMetadata(root, stateRef) {
  const paths=['kristal.discovery.json','derived/reader-inventory.json','derived/reader-profile.json'];
  const exists=paths.map(p=>fs.existsSync(path.join(root,p)));
  if(!exists.some(Boolean)) return {status:'absent',inventory:null};
  if(!exists.every(Boolean)) return {status:'incomplete',inventory:null};
  let d,i,p;
  try {
    d=jsonFor(root,paths[0],128*1024);
    i=jsonFor(root,paths[1],1024*1024);
    p=jsonFor(root,paths[2],1024*1024);
  } catch {return {status:'invalid',inventory:null};}
  if(d?.format!==FORMAT || i?.format!=='kristal.reader-inventory/1.0' ||
    p?.format!=='kristal.reader-profile/1.0' ||
    d?.authority!=='noncanonical_derived_metadata_not_access_or_publication_authority' ||
    d?.data_layout?.inventory_ref!==paths[1] || d?.reader?.hints_ref!==paths[2] ||
    d?.state_ref!==stateRef || i?.state_ref!==stateRef || p?.state_ref!==stateRef ||
    !SHA.test(d?.source_fingerprint) || d.source_fingerprint!==i.source_fingerprint ||
    d.source_fingerprint!==p.source_fingerprint ||
    !Array.isArray(i.files) || !Array.isArray(p.artifact_strategies) ||
    p.configuration_status!=='advisory_only') return {status:'invalid',inventory:null};
  // Verify the known local files independently before trusting specialization.
  // This does not rederive Authoring Kit's source_fingerprint: freshness is
  // 'bounded_files_checked_not_kit_freshness', NOT a Kit audit or Framework qualification.
  let skippedOversize=false;
  try {
    check(i.files.length>0 && i.files.length<=5000,'Inventaire absent ou trop volumineux.');
    const observed=new Set();
    for(const f of i.files){
      check(isObject(f) && safeText(f.path) && !observed.has(f.path) &&
        Number.isSafeInteger(f.size_bytes) && f.size_bytes>=0 && SHA.test(f.sha256),
      'Entrée inventaire invalide.');
      observed.add(f.path);
      // Bound total read; huge files are verified only on-demand, never for a hint.
      if(f.size_bytes>MAX_JSON) { skippedOversize=true; continue; }
      bytesFor(root,f.path,MAX_JSON,f);
    }
    const strategies=new Map(p.artifact_strategies.map(x=>[x.path,x]));
    for(const f of i.files){
      const s=strategies.get(f.path);
      check(s && s.must_verify_digest===f.sha256 && s.size_bytes_measured===f.size_bytes,
        'Stratégie de lecture et inventaire divergents.');
    }
  } catch {return {status:'stale',inventory:null};}
  return {status:skippedOversize ? 'partial_files_checked' : 'bounded_files_checked_not_kit_freshness',inventory:skippedOversize ? null : i,readerProfile:d.reader.profile,
    classification:d.classification || {}};
}
function checkState(state, workspace) {
  check(isObject(state) && state.schema_version==='9.0' &&
    state.artifact_type==='kristal_state_snapshot' && safeText(state.state_ref) &&
    state.state_ref===workspace.state_ref &&
    isObject(state.logical_commitment) && SHA.test(state.logical_commitment.digest) &&
    Array.isArray(state.members) && state.members.length<=8192 &&
    Array.isArray(state.references),'État v9 manquant, incompatible ou non borné.');
  const ids=new Set();
  for(const m of state.members){
    check(isObject(m) && safeText(m.artifact_id) && !ids.has(m.artifact_id) &&
      isObject(m.logical_contract) && safeText(m.logical_contract.id) &&
      isObject(m.logical_commitment) && SHA.test(m.logical_commitment.digest),
      'Membre v9 invalide.');
    ids.add(m.artifact_id);
  }
}
function graphReadModel(root, config) {
  if(!config.readModel) return null;
  const cfg=config.readModel;
  check(isObject(cfg) && cfg.type==='node-edge-json/1' &&
    safeText(cfg.manifest) && safeText(cfg.nodes) && safeText(cfg.edges),
    'Profil de lecture dérivé non pris en charge.');
  const manifest=jsonFor(root,cfg.manifest,128*1024);
  check(manifest.noncanonical===true && manifest.rebuildable===true &&
    isObject(manifest.canonical_input_sha256) && Object.keys(manifest.canonical_input_sha256).length<=64,
    'Le graphe doit être déclaré dérivé et reconstructible.');
  for(const [file,expected] of Object.entries(manifest.canonical_input_sha256)){
    check(/^[a-f0-9]{64}$/.test(expected),'Empreinte du manifeste invalide.');
    const fd=checkedFile(root,file,64*1024*1024);
    // Input SHA-256 checked without bringing large canonical files into a JSON parser.
    check(digest(fs.readFileSync(fd.filename))==='sha256:'+expected,
      'Entrées canoniques modifiées : graphe dérivé potentiellement périmé.');
  }
  const nodes=jsonFor(root,cfg.nodes,10*1024*1024);
  const edges=jsonFor(root,cfg.edges,10*1024*1024);
  check(Array.isArray(nodes) && nodes.length<=100000 &&
    Array.isArray(edges) && edges.length<=200000,'Graphe JSON invalide ou trop volumineux.');
  if(isObject(manifest.counts)) check(manifest.counts.nodes===nodes.length && manifest.counts.edges===edges.length,
    'Décompte de graphe dérivé incohérent.');
  const nodeIds=new Set();
  for(const n of nodes){
    check(isObject(n) && safeText(n.id,1024) && safeText(n.label,300) &&
      safeText(n.kind,128) && !nodeIds.has(n.id), 'Nœud de lecture invalide.');
    nodeIds.add(n.id);
  }
  const edgeIds=new Set();
  for(const e of edges){
    check(isObject(e) && safeText(e.id,1024) && !edgeIds.has(e.id) &&
      nodeIds.has(e.from) && nodeIds.has(e.to) && safeText(e.predicate,128) &&
      (e.evidence===undefined || JSON.stringify(e.evidence).length <= 2048),
      'Relation de lecture invalide ou extrémité absente.');
    edgeIds.add(e.id);
  }
  const presentation=cfg.presentation || {};
  check(isObject(presentation) &&
    (presentation.preferredKind===undefined || safeText(presentation.preferredKind,128)) &&
    (presentation.kindLabels===undefined || isObject(presentation.kindLabels)) &&
    (presentation.predicateLabels===undefined || isObject(presentation.predicateLabels)) &&
    (presentation.featuredKinds===undefined || (Array.isArray(presentation.featuredKinds) && presentation.featuredKinds.length<=12)),
    'Présentation locale invalide.');
  const knownKinds=new Set(nodes.map(n=>n.kind));
  if(presentation.preferredKind!==undefined)
    check(knownKinds.has(presentation.preferredKind), 'Type initial absent du graphe.');
  for(const [kind,label] of Object.entries(presentation.kindLabels || {}))
    check(knownKinds.has(kind) && safeText(label,80),'Libellé de type invalide.');
  for(const kind of presentation.featuredKinds || [])
    check(safeText(kind,128) && knownKinds.has(kind), 'Type mis en avant absent du graphe.');
  const knownPredicates=new Set(edges.map(e=>e.predicate));
  for(const [predicate,label] of Object.entries(presentation.predicateLabels || {}))
    check(knownPredicates.has(predicate) && safeText(label,80),'Libellé de relation invalide.');
  return {manifest,nodes,edges,manifestPath:cfg.manifest,presentation};
}
const relation=(id,label,domain,range='string',valueKind='string')=>({id,label:{fr:label,en:label},domain,range,valueKind,operators:['exists','in','none_of']});
const defaultPolicy=()=>({id:'view:local-v9-derived',label:'Local v10 / état v9, lecture dérivée',
  description:'Navigation non normative; sans vérification épistémique ni publication.',
  profile:'konstellation.normalized-reader.v1',showLabels:true,statuses:['unspecified'],
  certainties:['*'],validationStatuses:['*'],validatedAs:['*'],authorities:['*'],requireSources:true});
export function inspectLocalV10(config, base) {
  const root=rootOf(config,base);
  const workspace=jsonFor(root,'kristal.workspace.json',256*1024);
  check(workspace.format==='kristal.local-workspace/3.2.0' && safeText(workspace.state_ref) &&
    safeText(workspace.title,300),'Workspace local v9 non reconnu.');
  // Framework v10 keeps v9 semantic state; hosting and publication are separate.
  // Prefer the v10 reader surface, accept the v9 build fallback for local workspaces.
  const statePath=config.state || (fs.existsSync(path.join(root,'state/state-snapshot.json'))
    ? 'state/state-snapshot.json' : 'build/v9/state-snapshot.json');
  if (!config.state && fs.existsSync(path.join(root,'state/state-snapshot.json')) &&
      fs.existsSync(path.join(root,'build/v9/state-snapshot.json'))) {
    check(digest(bytesFor(root,'state/state-snapshot.json',4*1024*1024)) ===
      digest(bytesFor(root,'build/v9/state-snapshot.json',4*1024*1024)),
      'État exporté et état construit divergents.');
  }
  const d=discoveryMetadata(root,workspace.state_ref);
  const registered=d.inventory?.files.find(f=>f.path===statePath) || null;
  // When discovery is stale, never use an old digest as an access grant or
  // suppress generic opening; independently bound the state file instead.
  const state=jsonFor(root,statePath,4*1024*1024,registered);
  checkState(state,workspace);
  return {root,workspace,state,discovery:d,statePath};
}
export function loadLocalV10(config,base) {
  const {root,workspace,state,discovery,statePath}=inspectLocalV10(config,base);
  const graph=graphReadModel(root,config);
  const title=(config.title && safeText(config.title,300)) ? config.title : workspace.title;
  const stateId=id('v9state',state.state_ref);
  const sourceId=id('v9source',state.state_ref+':'+state.logical_commitment.digest);
  const entities=[{id:stateId,type:'v9_state',label:title,description:`État déclaré ${state.state_ref} (engagement non revérifié)`}];
  const assertions=[];
  const registry=[relation('v9:declares_member','Membre v9 déclaré',['v9_state'],'v9_artifact','entity')];
  const sourceRefs=[sourceId];
  const source={id:sourceId,title:`État structurel v9 : ${title}`,
    description:'Projection locale de l’état logique v9, sans vérification des engagements canoniques ni qualification.'};
  const emit=(aid,subject,relation,value,more={})=>assertions.push({
    id:aid,subject,relation,value,status:'unspecified',certainty:'not_evaluated',
    validationStatus:'not_evaluated',validatedAs:'not_evaluated',authority:'not_evaluated',
    scope:{domain:'read_only_local_projection'},sourceRefs,derivedProjection:true,...more,
  });
  for(const m of state.members){
    const eid=id('v9artifact',m.artifact_id);
    entities.push({id:eid,type:'v9_artifact',label:m.artifact_id.slice(0,300),
      description:`Contrat ${m.logical_contract.id}/${m.logical_contract.version}; engagement déclaré ${m.logical_commitment.digest}`});
    emit(id('v9assertion',m.artifact_id),stateId,'v9:declares_member',eid);
  }
  const graphTypeLabels={};
  let orderedGraphTypes=[];
  let featuredTypes=[];
  if(graph){
    // The source's declared kinds are presentation boundaries, not new
    // canonical classifications. Never collapse candidate matches into identity.
    const kindToType=new Map();
    const typeForKind=(kind)=>{
      if(!kindToType.has(kind)) {
        // Preserve readable, stable type names when they are safe identifiers.
        const safe=/^[a-z][a-z0-9_]{0,100}$/.test(kind) && !['v9_state','v9_artifact'].includes(kind);
        kindToType.set(kind,safe?kind:id('kind',kind));
      }
      return kindToType.get(kind);
    };
    for(const n of graph.nodes) typeForKind(n.kind);
    const byKind=graph.presentation.kindLabels || {};
    for(const [kind,type] of kindToType) graphTypeLabels[type]=byKind[kind] ||
      kind.replace(/[_-]+/g,' ').replace(/^./,c=>c.toUpperCase());
    featuredTypes=(graph.presentation.featuredKinds || []).map(k=>kindToType.get(k));
    const preferred=graph.presentation.preferredKind;
    orderedGraphTypes=[...kindToType.keys()]
      .sort((a,b)=> (a===preferred?-1:0)-(b===preferred?-1:0) ||
        graphTypeLabels[kindToType.get(a)].localeCompare(graphTypeLabels[kindToType.get(b)],'fr'))
      .map(kind=>kindToType.get(kind));
    const nodesById=new Map(graph.nodes.map(n=>[n.id,n]));
    const edgeTypes=new Map();
    for(const e of graph.edges){
      const from=nodesById.get(e.from),to=nodesById.get(e.to);
      const range=typeForKind(to.kind),domain=typeForKind(from.kind);
      const key=JSON.stringify([e.predicate,range]);
      if(!edgeTypes.has(key)) edgeTypes.set(key,{predicate:e.predicate,range,domains:new Set()});
      edgeTypes.get(key).domains.add(domain);
    }
    // The published Konstellation relation-registry/0.2 schema permits at most
    // ten entity types per relation.domain. Split large source-type unions
    // instead of weakening the shared schema or discarding source relations.
    // The returned mapping associates every original domain with its own
    // schema-compatible relation ID; entities and source evidence are untouched.
    const MAX_RELATION_DOMAINS=10;
    const addDomainBoundedRelations=(baseId,label,domains,range='string',valueKind='string')=>{
      const ordered=[...new Set(domains)].sort();
      const lookup=new Map();
      for(let index=0;index<ordered.length;index+=MAX_RELATION_DOMAINS){
        const group=ordered.slice(index,index+MAX_RELATION_DOMAINS);
        const rid=ordered.length<=MAX_RELATION_DOMAINS?baseId:`${baseId}:part${Math.floor(index/MAX_RELATION_DOMAINS)+1}`;
        registry.push(relation(rid,label,group,range,valueKind));
        for(const type of group) lookup.set(type,rid);
      }
      return lookup;
    };
    const kindRelationIds=addDomainBoundedRelations('v9:node_kind','Type d’élément',orderedGraphTypes);
    const edgeRelationIds=new Map();
    for(const [key,def] of [...edgeTypes].sort(([a],[b])=>a.localeCompare(b))){
      const baseId=id('v9rel',key);
      const label=semanticLabel(def.predicate, {
        // Explicit viewer dictionary corrects legacy raw-code labels; the original
        // predicate remains in each assertion for inspection and provenance.
        configured: graph.presentation.predicateLabels?.[def.predicate],
        rangeKind: [...kindToType].find(([,v])=>v===def.range)?.[0] || '',
      });
      edgeRelationIds.set(key,addDomainBoundedRelations(baseId,label,def.domains,def.range,'entity'));
    }
    for(const n of graph.nodes){
      const eid=id('v9node',n.id);
      entities.push({id:eid,type:typeForKind(n.kind),label:readableNodeLabel(n.label,n.kind),
        description:typeof n.description === 'string' && n.description.length <= 500 ? n.description :
          `Élément de la projection locale · ${graphTypeLabels[typeForKind(n.kind)]}.`,
        upstreamRef:n.id,originalKind:n.kind});
      emit(id('v9kind',n.id),eid,kindRelationIds.get(typeForKind(n.kind)),n.kind);
    }
    for(const e of graph.edges){
      const target=nodesById.get(e.to);
      const relationKey=JSON.stringify([e.predicate,typeForKind(target.kind)]);
      emit(id('v9edge',e.id),id('v9node',e.from),
        edgeRelationIds.get(relationKey).get(typeForKind(nodesById.get(e.from).kind)),id('v9node',e.to),{
        originalPredicate:e.predicate,originalKind:e.kind||null,
        originalEvidence:e.evidence||null,sourceEdgeId:e.id,
        // Candidate identity remains only a candidate link.
      });
    }
  }
  return {
    schemaVersion:'0.3',synthetic:false,title:`Kristal local v10 · ${title}`,
    description:graph ? 'Vue locale de graphe dérivé et de membres v9, sans altérer le Kristal.' :
      'Vue structurelle locale des membres v9. Pas de décodeur sémantique universel implicite.',
    registry:{schemaVersion:'0.2',registryRef:'konstellation:local-v10-reader-0.1',
      entityTypes:graph?[...orderedGraphTypes,'v9_state','v9_artifact']:['v9_state','v9_artifact'],relations:registry},
    entities,assertions,sources:[source],policies:[defaultPolicy()],
    integration:{adapter:'kristal-local-v10',
      presentation:{typeLabels:graph?graphTypeLabels:{},featuredTypes},viewKind:graph?'derived-node-edge-graph':'v9-declared-topology',
      stateRef:state.state_ref,declaredStateCommitment:state.logical_commitment,
      checks:{stateShapeChecked:true,canonicalCommitmentVerified:false,verifiedStatePath:statePath,
        canonicalInputsMatched:Boolean(graph),derivedGraphRebuildVerified:false,discoveryStatus:discovery.status},
      readerHintsUsed:false,hostingVerified:false,publicationVerified:false,activationVerified:false,
      classification:discovery.status==='bounded_files_checked_not_kit_freshness'?discovery.classification:{}},
  };
}
export function listLocalV10(config,base) {
  const {workspace}=inspectLocalV10(config,base);
  return [{id:'local-v10',label:workspace.title,stateRef:workspace.state_ref,available:true}];
}
