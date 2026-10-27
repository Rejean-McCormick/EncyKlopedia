import test from 'node:test';
import assert from 'node:assert/strict';
import { once } from 'node:events';
import { createApp, startFromEnvironment } from '../src/server.mjs';

async function withApp(run){
 const app=createApp();app.listen(0,'127.0.0.1');await once(app,'listening');
 try {return await run(`http://127.0.0.1:${app.address().port}`);} finally {await new Promise(resolve=>app.close(resolve));}
}
test('public and non-loopback modes are blocked',()=>{
 assert.throws(()=>startFromEnvironment({ENCYKLOPEDIA_MODE:'public'}),/blocked/);
 assert.throws(()=>startFromEnvironment({ENCYKLOPEDIA_MODE:'demo',ENCYKLOPEDIA_HOST:'0.0.0.0'}),/loopback/);
});
test('read-only demo API and HTML',()=>withApp(async base=>{
 const status=await (await fetch(`${base}/api/v1/status`)).json();assert.equal(status.production_enabled,false);
 const article=await (await fetch(`${base}/api/v1/articles/atlas-of-imaginary-forests?lang=fr`)).json();
 assert.equal(article.display_status,'fallback');assert.equal(article.effective_locale,'en');
 const search=await (await fetch(`${base}/api/v1/search?lang=fr&q=observatoire`)).json();assert.equal(search.results.length,1);
 const home=await fetch(base);assert.equal(home.status,200);assert.match(await home.text(),/EncyKlopedia/);
 assert.match(home.headers.get('content-security-policy'),/default-src/);
 const broken=await fetch(`${base}/api/v1/articles/not-found`);assert.equal(broken.status,404);
 const blocked=await fetch(`${base}/api/v1/status`,{method:'POST'});assert.equal(blocked.status,405);
 const traversal=await fetch(`${base}/api/v1/articles/%2e%2e%2fsecret`);assert.notEqual(traversal.status,200);
 const long=await fetch(`${base}/api/v1/search?q=${'x'.repeat(201)}`);assert.equal(long.status,400);
}));
