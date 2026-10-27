import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { loadIntegration, loadIntegrationKristal, listIntegrationKristals } from './integrations/kristal.mjs';
import { SemantikAdapter } from './integrations/semantik.mjs';
import { Engine } from './engine.mjs';
import { loadPack, readJson } from './pack.mjs';
import { ROOT, AppError, fail, validate } from './contracts.mjs';
import { loadConfig, cspFor } from './config.mjs';
import { authenticate, requireScope } from './auth.mjs';
import { requestId, increment, observe, gauge, metricsSnapshot, log } from './observability.mjs';
import { versionInfo } from './version.mjs';

export function loadLenses(engine, dir) {
  const configured = [];
  dir ||= process.env.KONSTELLATION_LENSES || null;
  if (dir) {
    if (!fs.existsSync(dir) || !fs.statSync(dir).isDirectory()) fail('INVALID_CONFIG', 'Répertoire de Lens introuvable.', 500);
    for (const name of fs.readdirSync(dir).filter((n) => n.endsWith('.json')).sort()) configured.push(readJson(path.join(dir, name)));
  }
  const validateLens = (lens) => {
    validate('lens', lens);
    if (!engine.pack.registry.entityTypes.includes(lens.rootType)) fail('INVALID_PACK', 'Lens root is unknown');
    const constellationRelations = (lens.constellation?.groups || []).filter((g) => g.source.kind === 'relations').flatMap((g) => g.source.ids);
    for (const id of [...lens.facets.map((f) => f.relation), ...lens.pivots, ...constellationRelations])
      if (!engine.relations.get(id)?.domain.includes(lens.rootType)) fail('INVALID_PACK', 'Lens relation mismatch');
    return lens;
  };
  configured.forEach(validateLens);
  const covered = new Set(configured.map((lens) => lens.rootType));
  const generic = engine.pack.registry.entityTypes.filter((type) => !covered.has(type)).map((type) => {
    const relations = engine.pack.registry.relations.filter((relation) => relation.domain.includes(type));
    const facets = relations.slice(0, 24).map((relation) => ({
      relation: relation.id,
      widget: relation.valueKind === 'interval' ? 'year-range' : relation.valueKind === 'entity' ? 'entity-picker' : 'presence',
    }));
    const pivots = relations.filter((relation) => relation.valueKind === 'entity').slice(0, 16).map((relation) => relation.id);
    const label = engine.profiler.entityTypeLabels[type] || type.replace(/[_:.-]+/g,' ').split(/\s+/).filter(Boolean).map((word)=>word.charAt(0).toLocaleUpperCase('fr')+word.slice(1)).join(' ');
    return validateLens({
      schemaVersion:'0.2', id:`type:${type}`, label:{fr:label,en:label}, rootType:type, facets, pivots,
      constellation:{defaultSatelliteCount:8,groups:[]},
    });
  });
  return [...configured, ...generic];
}

async function body(req) {
  let size = 0; const chunks = [];
  for await (const chunk of req) { size += chunk.length; if (size > 65536) fail('PAYLOAD_TOO_LARGE', 'Requête limitée à 64 Kio.', 413); chunks.push(chunk); }
  try { return JSON.parse(Buffer.concat(chunks).toString('utf8')); } catch { fail('INVALID_QUERY', 'JSON invalide.'); }
}

const types = {'.html':'text/html; charset=utf-8','.js':'text/javascript; charset=utf-8','.css':'text/css; charset=utf-8','.svg':'image/svg+xml','.json':'application/json; charset=utf-8','.png':'image/png','.ico':'image/x-icon','.woff2':'font/woff2'};

function rateLimiter(limit) {
  const windows = new Map();
  return (key) => {
    const now=Date.now(), minute=Math.floor(now/60000), old=windows.get(key);
    const row=old?.minute===minute?old:{minute,count:0}; row.count++; windows.set(key,row);
    if (windows.size>10000) for(const [k,v] of windows) if(v.minute<minute-2) windows.delete(k);
    return row.count<=limit;
  };
}

export function createServer({
  engine = new Engine(loadPack(), { roles:(process.env.KONSTELLATION_ROLES||'public').split(','), ...(process.env.KONSTELLATION_CURSOR_SECRET?{secret:process.env.KONSTELLATION_CURSOR_SECRET}:{}) }),
  lenses,
  semantik = new SemantikAdapter(),
  dist = path.join(ROOT,'dist'),
  config = loadConfig(),
  collection = null,
} = {}) {
  lenses ||= loadLenses(engine);
  // Readiness means more than “the JSON parsed”: build the default policy scope
  // and its navigation profile before accepting traffic. Invalid policy/index
  // state therefore prevents startup instead of degrading silently later.
  const readinessContext = engine.context();
  engine.scope(readinessContext);
  engine.visibleProfiler(readinessContext);
  const allowRate = rateLimiter(config.rateLimitPerMinute);
  const runtimeCache = new Map();
  const packCache = new Map(collection?.defaultKristal ? [[collection.defaultKristal, Promise.resolve(engine.pack)]] : []);
  const collectionItems = new Map((collection?.items || []).map((item) => [item.id, item]));
  const packFor = async (kristal) => {
    if (!kristal) return engine.pack;
    if (!packCache.has(kristal)) {
      const promise = collection.loadPack(kristal);
      packCache.set(kristal, promise);
      promise.catch(() => packCache.delete(kristal));
    }
    return packCache.get(kristal);
  };
  const requestedKristal = (req) => {
    if (!collection?.selectable) return null;
    const raw = req.headers['x-konstellation-kristal'];
    const value = Array.isArray(raw) ? raw[0] : raw;
    const id = value ? String(value) : collection.defaultKristal;
    if (!id || id.length > 200 || !collectionItems.get(id)?.available)
      fail('KRISTAL_NOT_FOUND', 'Kristal sélectionné indisponible.', 422);
    return id;
  };
  const runtimeFor = async (principal, kristal = null) => {
    const roles = [...new Set(principal?.roles || ['public'])].sort();
    const corpusKey = kristal || '__default__';
    const key = `${corpusKey}|${roles.join(',')}`;
    if (!runtimeCache.has(key)) {
      const promise = (async () => {
        const pack = await packFor(kristal);
        const canReuseDefault = (!kristal || kristal === collection?.defaultKristal) && roles.join(',') === engine.roles.join(',');
        const selectedEngine = canReuseDefault
          ? engine
          : new Engine(pack, {
              roles,
              secret: engine.secret,
              maxOperations: engine.limits.maxOperations,
              deadlineMs: engine.limits.deadlineMs,
              cacheSize: engine.cacheSize,
            });
        const selectedLenses = selectedEngine === engine ? lenses : loadLenses(selectedEngine);
        return { engine: selectedEngine, lenses: selectedLenses };
      })();
      runtimeCache.set(key, promise);
      promise.catch(() => runtimeCache.delete(key));
    }
    return runtimeCache.get(key);
  };
  const server = http.createServer(async (req,res) => {
    const started=performance.now(); const rid=requestId(req.headers['x-request-id']);
    res.setHeader('X-Request-ID',rid); res.setHeader('X-Content-Type-Options','nosniff'); res.setHeader('Referrer-Policy','no-referrer'); res.setHeader('X-Frame-Options','DENY'); res.setHeader('Permissions-Policy','camera=(), microphone=(), geolocation=(), payment=(), usb=()'); res.setHeader('Cross-Origin-Opener-Policy','same-origin'); res.setHeader('Cross-Origin-Resource-Policy','same-origin'); res.setHeader('X-Permitted-Cross-Domain-Policies','none'); res.setHeader('Content-Security-Policy',cspFor(config));
    let endpoint='static', status=200, principal=null;
    const send=(data,code=200)=>{status=code; res.writeHead(code,{'Content-Type':'application/json; charset=utf-8','Cache-Control':'no-store','X-Request-ID':rid}); res.end(JSON.stringify(data));};
    try {
      const url=new URL(req.url,'http://localhost'); endpoint=url.pathname;
      const hostHeader=req.headers.host || ''; let hostname=''; try{hostname=new URL('http://'+hostHeader).hostname;}catch{fail('ACCESS_DENIED','Hôte invalide.',403);}
      if (!config.allowedHosts.includes(hostname) && !config.allowedHosts.includes('*')) fail('ACCESS_DENIED','Hôte non autorisé.',403);
      if (url.pathname.startsWith('/api/')) {
        const origin=req.headers.origin;
        if(origin){
          let originHost=''; try{originHost=new URL(origin).host;}catch{fail('ACCESS_DENIED','Origine invalide.',403);}
          if(originHost!==hostHeader && origin!==config.devOrigin) fail('ACCESS_DENIED','Origine non autorisée.',403);
        }
        if(req.headers['sec-fetch-site']==='cross-site') fail('ACCESS_DENIED','Requête intersite refusée.',403);
        const remote=req.socket.remoteAddress || 'unknown';
        if(req.method==='GET' && url.pathname==='/api/health') return send({status:'ok',version:versionInfo().version,requestId:rid});
        if(req.method==='GET' && url.pathname==='/api/ready') return send({status:'ready',version:versionInfo().version,corpusLoaded:Boolean(engine?.pack),registryLoaded:Boolean(engine?.relations?.size),policyLoaded:Boolean(engine?.policies?.size),lensesLoaded:Array.isArray(lenses),scopeIndexReady:Boolean(engine?.scopeCache?.size),navigationProfileReady:Boolean(engine?.policyProfilerCache?.size),requestId:rid});
        if(req.method==='GET' && url.pathname==='/api/version') return send({...versionInfo(engine,{exposeCorpusIdentity:config.exposeCorpusIdentity}),requestId:rid});
        if(!allowRate(`${remote}|preauth`)) fail('RATE_LIMITED','Trop de requêtes.',429);
        principal = authenticate(req, config);
        if(!allowRate(`${remote}|${principal.id}`)) fail('RATE_LIMITED','Trop de requêtes.',429);
        if(req.method==='GET' && url.pathname==='/api/metrics') { requireScope(principal,'metrics'); return send(metricsSnapshot()); }
        if(req.method==='GET' && url.pathname==='/api/kristals') {
          requireScope(principal,'read');
          const current = requestedKristal(req);
          return send({
            selectable: Boolean(collection?.selectable),
            current,
            defaultKristal: collection?.defaultKristal || null,
            items: collection?.items || [],
          });
        }
        const selectedKristal = requestedKristal(req);
        const runtime = await runtimeFor(principal, selectedKristal);
        const requestEngine = runtime.engine;
        const requestLenses = runtime.lenses;
        if(req.method==='GET' && ['/api/bootstrap','/api/capabilities'].includes(url.pathname)) {
          requireScope(principal,'read');
          const requestedPolicyRef=url.searchParams.get('readerPolicyRef');
          const bootContext=requestedPolicyRef ? requestEngine.context(requestedPolicyRef) : requestEngine.context();
          // scope() validates the requested policy before any registry/Lens metadata is exposed.
          requestEngine.scope(bootContext);
          const communication=await semantik.capabilities(); const bootStart=performance.now(); const boot=requestEngine.bootstrap(requestLenses,bootContext); observe('bootstrap_duration_ms',performance.now()-bootStart); boot.capabilities.sa=communication.available;
          return send(url.pathname==='/api/bootstrap'?{...boot,communication,kristal:selectedKristal,principal:{id:principal.id,roles:principal.roles,scopes:principal.scopes}}:{...boot.capabilities,communication});
        }
        if(req.method!=='POST') fail('NOT_FOUND','Endpoint introuvable.',404);
        if(url.pathname.startsWith('/api/sa')) requireScope(principal,'sa'); else requireScope(principal,'read');
        if(!req.headers['content-type']?.startsWith('application/json')) fail('INVALID_QUERY','Content-Type application/json requis.',415);
        const b=await body(req); if(!b||typeof b!=='object'||Array.isArray(b)) fail('INVALID_QUERY','Objet JSON requis.');
        switch(url.pathname){
          case '/api/query': {
            const t=performance.now(); const value=requestEngine.query(b.query,b.cursor); observe('query_evaluation_duration_ms',performance.now()-t); observe('result_set_size',value.total?.value||0); return send(value);
          }
          case '/api/facets': return send(requestEngine.facets(b.query,b.relations));
          case '/api/entity': return send(requestEngine.entity(b.id,b.context));
          case '/api/constellation': return send(requestEngine.constellation(b,requestLenses));
          case '/api/navigation/plan': {
            const t=performance.now(); const value=requestEngine.navigationPlan(b,requestLenses); observe('navigation_planning_duration_ms',performance.now()-t); increment('navigation_recipe_selected_total',{recipe:value.primaryRecipeId}); return send(value);
          }
          case '/api/navigation/project': {
            const t=performance.now(); const value=requestEngine.navigationProjection(b,requestLenses); observe('navigation_projection_duration_ms',performance.now()-t,{renderer:value.rendererId}); increment('navigation_projection_total',{recipe:value.recipeId,renderer:value.rendererId,truncated:Boolean(value.truncated)}); return send(value);
          }
          case '/api/evidence': return send(requestEngine.evidence(b.ids,b.context));
          case '/api/validate-state': {
            const migrated=requestEngine.migrateExplorationState(b,requestLenses); requestEngine.check(migrated.state.query); requestEngine.scope(migrated.state.query.context);
            return send({valid:true,...migrated});
          }
          case '/api/sa/request': return send(semantik.request(requestEngine,b));
          case '/api/sa': return send(await semantik.render(requestEngine,b));
          default: fail('NOT_FOUND','Endpoint introuvable.',404);
        }
      }
      if(!['GET','HEAD'].includes(req.method)) fail('NOT_FOUND','Introuvable.',404);
      const pathname=decodeURIComponent(url.pathname); const file=path.resolve(dist,'.'+(pathname==='/'?'/index.html':pathname));
      if(!file.startsWith(path.resolve(dist)+path.sep)) fail('NOT_FOUND','Introuvable.',404);
      if(!fs.existsSync(file)||!fs.statSync(file).isFile()) fail('NOT_FOUND','Page introuvable. Exécutez npm run build.',404);
      res.writeHead(200,{'Content-Type':types[path.extname(file)]||'application/octet-stream','Cache-Control':pathname.startsWith('/_astro/')?'public, max-age=31536000, immutable':'no-cache','X-Request-ID':rid});
      if(req.method==='HEAD') return res.end(); fs.createReadStream(file).pipe(res);
    } catch(error) {
      if(res.headersSent){res.destroy();return;} const known=error instanceof AppError; status=known?error.status:500;
      increment('http_errors_total',{endpoint,code:known?error.code:'INTERNAL_ERROR'});
      log(known&&status<500?'warn':'error','request_error',{requestId:rid,principalId:principal?.id||null,endpoint,status,code:known?error.code:'INTERNAL_ERROR',message:known?error.message:String(error?.message||error)});
      send({error:{code:known?error.code:'INTERNAL_ERROR',message:known?error.message:'Erreur interne.',requestId:rid,...(known&&error.details?{details:error.details}:{})}},status);
    } finally {
      const duration=performance.now()-started; increment('http_requests_total',{endpoint,status}); observe('http_request_duration_ms',duration,{endpoint,status}); gauge('process_heap_used_bytes',process.memoryUsage().heapUsed);
      log('info','request_complete',{requestId:rid,principalId:principal?.id||null,endpoint,status,durationMs:Math.round(duration*100)/100});
    }
  });
  server.requestTimeout=10000; server.headersTimeout=12000;
  server.on('close',()=>log('info','server_closed'));
  return server;
}

if(process.argv[1]&&fileURLToPath(import.meta.url)===path.resolve(process.argv[1])){
  const config=loadConfig();
  const backendConfig=process.env.KONSTELLATION_BACKEND_CONFIG || null;
  const pack=backendConfig?await loadIntegration(backendConfig):loadPack();
  const selection=backendConfig?listIntegrationKristals(backendConfig):{selectable:false,defaultKristal:null,items:[]};
  const collection=selection.selectable?{
    ...selection,
    loadPack:(kristal)=>loadIntegrationKristal(backendConfig,kristal),
  }:null;
  const engine=new Engine(pack,{roles:(process.env.KONSTELLATION_ROLES||'public').split(','),...(process.env.KONSTELLATION_CURSOR_SECRET?{secret:process.env.KONSTELLATION_CURSOR_SECRET}:{})});
  const semantik=new SemantikAdapter(process.env.KONSTELLATION_SA_CONFIG?readJson(process.env.KONSTELLATION_SA_CONFIG):null);
  const server=createServer({engine,semantik,config,collection});
  const shutdown=(signal)=>{log('info','shutdown_requested',{signal}); server.close(()=>process.exit(0)); setTimeout(()=>process.exit(1),5000).unref();};
  process.on('SIGTERM',()=>shutdown('SIGTERM')); process.on('SIGINT',()=>shutdown('SIGINT'));
  server.listen(config.port,config.host,()=>log('info','server_started',{host:config.host,port:config.port,profile:config.deploymentProfile}));
}
