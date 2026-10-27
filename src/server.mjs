import { createServer as createHttpServer } from 'node:http';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { resolve } from 'node:path';
import { articleBySlug, browse, loadDemoPublication, requestedLocale } from './catalog.mjs';

const FILES = new Map([
  ['/', ['../public/index.html', 'text/html; charset=utf-8']],
  ['/app.js', ['../public/app.js', 'text/javascript; charset=utf-8']],
  ['/styles.css', ['../public/styles.css', 'text/css; charset=utf-8']]
]);
const STATIC = new Map([...FILES].map(([route,[relative,mime]]) =>
  [route, {content:readFileSync(fileURLToPath(new URL(relative, import.meta.url))),mime}]));

function send(res, status, data, mime = 'application/json; charset=utf-8', isHead = false) {
  const payload = Buffer.isBuffer(data) ? data : Buffer.from(mime.startsWith('application/json') ? JSON.stringify(data) : String(data));
  res.writeHead(status, {
    'Content-Type':mime,
    'Content-Length':payload.byteLength,
    'Cache-Control':'no-store',
    'X-Content-Type-Options':'nosniff',
    'Referrer-Policy':'no-referrer',
    'X-Frame-Options':'DENY',
    'Content-Security-Policy':"default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; base-uri 'none'; frame-ancestors 'none'; form-action 'none'"
  });
  return res.end(isHead ? undefined : payload);
}

export function createApp(publication = loadDemoPublication()) {
  return createHttpServer((req,res) => {
    if (req.method !== 'GET' && req.method !== 'HEAD') return send(res,405,{error:'read_only'},'application/json; charset=utf-8');
    const head = req.method === 'HEAD';
    let url;
    try { url = new URL(req.url,'http://local.invalid'); }
    catch { return send(res,400,{error:'invalid_url'},'application/json; charset=utf-8',head); }
    const path = url.pathname;
    if (path === '/healthz' || path === '/readyz') return send(res,200,{status:'ok',mode:'synthetic-demo',qualified:false},'application/json; charset=utf-8',head);
    if (path === '/api/v1/status') return send(res,200,{
      app:'EncyKlopedia',version:'0.1.0-alpha.1',mode:'synthetic-demo',production_enabled:false,
      publication_id:publication.publication_id,framework_target:publication.framework_target,
      source_view_profile:publication.source_view_profile,qualified:false
    },'application/json; charset=utf-8',head);
    if (path === '/api/v1/locales') return send(res,200,{
      available_content_locales:publication.locales,requested_locale_can_fallback:true,
      target_language_count:100,certified_languages:0
    },'application/json; charset=utf-8',head);
    if (path === '/api/v1/search') {
      const locale = requestedLocale(url.searchParams.get('lang'),publication.locales);
      const q = url.searchParams.get('q') ?? '';
      if (q.length > 200) return send(res,400,{error:'query_too_long'},'application/json; charset=utf-8',head);
      return send(res,200,{locale,query:q,publication_id:publication.publication_id,results:browse(publication,locale,q)},'application/json; charset=utf-8',head);
    }
    if (path.startsWith('/api/v1/articles/')) {
      const slug = path.slice('/api/v1/articles/'.length);
      if (!/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(slug) || slug.length > 80) return send(res,400,{error:'invalid_slug'},'application/json; charset=utf-8',head);
      const locale = requestedLocale(url.searchParams.get('lang'),publication.locales);
      const article = articleBySlug(publication,slug,locale);
      return article ? send(res,200,{...article,publication_id:publication.publication_id,synthetic:true},'application/json; charset=utf-8',head)
                     : send(res,404,{error:'article_not_found'},'application/json; charset=utf-8',head);
    }
    const entry = STATIC.get(path);
    if (entry) return send(res,200,entry.content,entry.mime,head);
    return send(res,404,{error:'not_found'},'application/json; charset=utf-8',head);
  });
}

export function startFromEnvironment(env = process.env) {
  const mode = env.ENCYKLOPEDIA_MODE ?? 'demo';
  if (mode !== 'demo') throw new Error('Production publication is deliberately blocked in 0.1.0-alpha.1 (C2/C4 gates not implemented).');
  const host = env.ENCYKLOPEDIA_HOST ?? '127.0.0.1';
  if (!['127.0.0.1','localhost','::1'].includes(host)) throw new Error('Alpha can bind to loopback only');
  const port = Number(env.ENCYKLOPEDIA_PORT ?? 8787);
  if (!Number.isInteger(port) || port < 1 || port > 65535) throw new Error('Invalid port');
  const app = createApp();
  app.listen(port,host,() => console.log(`EncyKlopedia demo: http://${host}:${port} (synthetic content only)`));
  return app;
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  startFromEnvironment();
}
