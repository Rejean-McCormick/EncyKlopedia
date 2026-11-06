import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtemp, readFile, writeFile, rm, mkdir } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { gzipSync } from 'node:zlib';
import {
  loadCatalog,validateCatalog,sourceByID,assertSourceURL,validateSnapshotID,
  fetchSnapshot,verifyCapture,parseIanaRegistry,ingestIana,
  normalizeKaikkiEntry,ingestKaikki,listCaptures
} from '../tools/dictionary-harvester/lib.mjs';

async function temp(run) {
 const dir=await mkdtemp(join(tmpdir(),'encyk-harvester-'));
 try{return await run(dir);}finally{await rm(dir,{recursive:true,force:true});}
}
const ianaText='File-Date: 2026-09-17\n%%\nType: language\nSubtag: fr\nDescription: French\nAdded: 2005-10-16\n%%\nType: language\nSubtag: aa\nDescription: Afar\n%%\n';

// No external network calls. All fetch tests use injected responses.
test('candidate catalog has valid source metadata and no public approvals',async()=>{
 const c=await loadCatalog();assert.equal(c.sources.length,5);
 assert.equal(c.sources.every(s=>s.public_reuse==='not_assessed'),true);
 assert.equal(sourceByID(c,'unimorph').download_url,null);
 assert.throws(()=>sourceByID(c,'unknown'),/Unknown/);
});
test('catalog validation rejects duplicate or unsafe source',async()=>{
 const c=await loadCatalog();
 assert.throws(()=>validateCatalog({...c,sources:[c.sources[0],c.sources[0]]}),/Duplicate/);
 assert.throws(()=>validateCatalog({...c,sources:[{...c.sources[0],download_url:'http://localhost/'}]}),/Unsafe/);
});
test('destination identifiers refuse directory traversal',()=>{
 for(const s of ['../secret','foo/bar','FOO','foo..bar',''])assert.throws(()=>validateSnapshotID(s));
 assert.equal(validateSnapshotID('iana-2026-11'),'iana-2026-11');
});
test('URL scope blocks untrusted hosts, credentials, ports, and HTTP',async()=>{
 const source=sourceByID(await loadCatalog(),'iana-subtags');
 for(const url of ['http://www.iana.org/x','https://evil.example/x','https://www.iana.org:8443/x','https://u:p@www.iana.org/x'])assert.throws(()=>assertSourceURL(source,url));
 assert.match(assertSourceURL(source,source.download_url),/^https:/);
});
test('opt-in snapshot capture is immutable, SHA-256 verified and never approved',()=>temp(async dir=>{
 const source=sourceByID(await loadCatalog(),'iana-subtags');
 const fn=async ()=>new Response(ianaText,{status:200,headers:{'content-length':String(Buffer.byteLength(ianaText))}});
 const out=await fetchSnapshot({source,store:dir,snapshot:'test-1',fetchImpl:fn});
 assert.equal(out.manifest.reviewed,false);assert.equal(out.manifest.public_release,false);assert.equal(out.manifest.canonical,false);
 const v=await verifyCapture(out.directory);assert.equal(v.sha256,out.manifest.sha256);
 assert.equal((await listCaptures(dir)).length,1);
 await assert.rejects(fetchSnapshot({source,store:dir,snapshot:'test-1',fetchImpl:fn}),/already exists/);
 await writeFile(join(out.directory,'registry.txt'),'tampered');
 await assert.rejects(verifyCapture(out.directory),/integrity mismatch/);
}));
test('HTTP redirects outside source host are blocked',()=>temp(async dir=>{
 const source=sourceByID(await loadCatalog(),'iana-subtags');
 await assert.rejects(fetchSnapshot({source,store:dir,snapshot:'red-1',fetchImpl:async()=>new Response(null,{status:302,headers:{location:'https://evil.invalid/oops'}})}),/Unapproved/);
 assert.deepEqual(await listCaptures(dir),[]);
}));
test('streaming download blocks oversized responses',()=>temp(async dir=>{
 const source={...sourceByID(await loadCatalog(),'iana-subtags'),max_bytes:2};
 await assert.rejects(fetchSnapshot({source,store:dir,snapshot:'limit-1',fetchImpl:async()=>new Response('12345',{status:200})}),/size limit/);
 assert.deepEqual(await listCaptures(dir),[]);
}));
test('IANA text extraction retains source date and no fictitious coverage',()=>{
 const parsed=parseIanaRegistry(ianaText);
 assert.equal(parsed.file_date,'2026-09-17');assert.equal(parsed.records.length,2);
 assert.equal(parsed.records[0].subtag,'fr');assert.equal(parsed.verified_against_iana,false);
 assert.throws(()=>parseIanaRegistry('Type: language\n'),/File-Date/);
});
test('IANA ingest writes candidate registry but never overwrites it',()=>temp(async dir=>{
 const infile=join(dir,'iana.txt'),outfile=join(dir,'candidate.json');
 await writeFile(infile,ianaText);
 const info=await ingestIana({input:infile,output:outfile});assert.equal(info.records,2);
 assert.equal(JSON.parse(await readFile(outfile,'utf8')).records.length,2);
 await assert.rejects(ingestIana({input:infile,output:outfile}),/EEXIST/);
}));
test('Wiktextract normalization preserves senses, forms, and flags unapproved status',()=>{
 const obj=normalizeKaikkiEntry({word:'chat',lang_code:'fr',lang:'French',pos:'noun',senses:[{glosses:['cat'],tags:['animal']}],forms:[{form:'chats',tags:['plural']}]},'kaikki-simple','test-1');
 assert.equal(obj.lemma,'chat');assert.equal(obj.language_code,'fr');assert.equal(obj.senses[0].glosses[0],'cat');assert.equal(obj.forms[0].form,'chats');
 assert.equal(obj.semantic_id,null);assert.equal(obj.approved_translation,false);
 assert.equal(normalizeKaikkiEntry({word:'x',lang_code:'bad//'},'a','b'),null);
});
test('Wiktextract .gz ingestion streams candidates, rejects bad rows and reports counts',()=>temp(async dir=>{
 const file=join(dir,'raw.jsonl.gz'),out=join(dir,'candidates.jsonl');
 const lines=[JSON.stringify({word:'chat',lang:'French',lang_code:'fr',pos:'noun',senses:[{glosses:['cat']}]}),'not-json',JSON.stringify({word:'house',lang_code:'en',forms:[{form:'houses',tags:['plural']}]})].join('\n')+'\n';
 await writeFile(file,gzipSync(Buffer.from(lines)));
 const r=await ingestKaikki({input:file,output:out,sourceId:'kaikki-simple',snapshot:'fixture-1'});
 assert.equal(r.rows_seen,3);assert.equal(r.observations,2);assert.equal(r.rejected,1);assert.equal(r.partial,false);
 assert.equal(r.canonical_mappings,0);
 const rows=(await readFile(out,'utf8')).trim().split('\n').map(x=>JSON.parse(x));
 assert.equal(rows.length,2);assert.equal(rows[1].forms[0].form,'houses');
 await assert.rejects(ingestKaikki({input:file,output:out,sourceId:'kaikki-simple',snapshot:'fixture-1'}),/already exists/);
}));
test('bounded pilot ingest marks partial and stops early',()=>temp(async dir=>{
 const file=join(dir,'raw.jsonl'),out=join(dir,'candidates.jsonl');
 await writeFile(file,[{word:'un',lang_code:'fr'},{word:'deux',lang_code:'fr'}].map(x=>JSON.stringify(x)).join('\n')+'\n');
 const r=await ingestKaikki({input:file,output:out,sourceId:'kaikki-simple',snapshot:'pilot-1',maxRecords:1});
 assert.equal(r.partial,true);assert.equal(r.rows_seen,1);assert.equal(r.observations,1);
}));
test('wikidata .bz2 is not falsely claimed supported by Wiktextract ingest',()=>temp(async dir=>{
 const file=join(dir,'x.bz2');await writeFile(file,'fake');
 await assert.rejects(ingestKaikki({input:file,output:join(dir,'out.jsonl'),sourceId:'kaikki-simple',snapshot:'test-1'}),/Only JSONL/);
}));

// C:/D: separation regression tests
import { resolveDataRoot, dataPaths, assertDataLayout, inventoryExistingLexical, WINDOWS_DATA_ROOT } from '../tools/dictionary-harvester/lib.mjs';
test('on Windows, default data root is D: and never the code repository', () => {
 assert.equal(WINDOWS_DATA_ROOT, 'D:\\EncyKlopedia');
 assert.equal(resolveDataRoot(undefined,'win32'), 'D:\\EncyKlopedia');
 assert.throws(()=>resolveDataRoot(undefined,'linux'),/Data root required/);
});
test('data paths follow D: existing hierarchy without a private-data duplicate',()=>temp(async dir=>{
 const p=dataPaths(dir);
 assert.match(p.lexicalSources,/10_sources[\\/]lexical$/);
 assert.match(p.captures,/10_sources[\\/]lexical[\\/]harvester$/);
 assert.match(p.working,/30_working[\\/]lexical[\\/]harvester$/);
 assert.equal(p.root,dir);
 assert.equal(Object.values(p).some(x=>x.includes('private-data')),false);
 await assert.rejects(assertDataLayout(dir),/Missing data lake directory/);
}));
test('read-only discovery sees existing Kaikki and Wikidata lexical assets without changing them',()=>temp(async dir=>{
 for(const d of ['10_sources/lexical/wikidata/lexemes/dumps/current', '10_sources/lexical/wiktionary/kaikki/enwiktionary/Albanian','20_evidence','30_working','50_mediatheque'])
   await mkdir(join(dir,d),{recursive:true});
 const lexeme=join(dir,'10_sources/lexical/wikidata/lexemes/dumps/current/latest-lexemes.json.bz2');
 const albanian=join(dir,'10_sources/lexical/wiktionary/kaikki/enwiktionary/Albanian/kaikki.org-dictionary-Albanian.jsonl');
 await writeFile(lexeme,'test-lexeme');await writeFile(albanian,'test-albanian');
 const inventory=await inventoryExistingLexical(dir);
 assert.equal(inventory.source_files,2);assert.equal(inventory.integrity_verified,false);
 assert.equal(inventory.publication_approved,false);
 assert.equal((await readFile(lexeme,'utf8')),'test-lexeme');
 assert.equal((await readFile(albanian,'utf8')),'test-albanian');
}));
test('harvester refuses implicit C: code-repository capture store',()=>temp(async dir=>{
 const source=sourceByID(await loadCatalog(),'iana-subtags');
 await assert.rejects(fetchSnapshot({source,snapshot:'test-1',fetchImpl:async()=>new Response('x')}),/Explicit data store required/);
 await assert.rejects(listCaptures(),/Explicit data store required/);
}));
