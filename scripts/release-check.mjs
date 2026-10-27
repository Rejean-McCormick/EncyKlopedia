import fs from 'node:fs';
import { execFileSync } from 'node:child_process';

const pkg = JSON.parse(fs.readFileSync(new URL('../package.json', import.meta.url), 'utf8'));
const checks=[];
const add=(id,ok,detail)=>checks.push({id,ok,detail});
const nodeMajor=Number(process.versions.node.split('.')[0]);
const nodeMinor=Number(process.versions.node.split('.')[1]);
const supported=nodeMajor>24 || (nodeMajor===24 && nodeMinor>=15); // package minimum 24.15.0
add('node-version',supported,`running ${process.versions.node}; requires ${pkg.engines.node}`);
add('lockfile',fs.existsSync(new URL('../package-lock.json',import.meta.url)), 'package-lock.json must be committed');
try { execFileSync(process.execPath,[new URL('./check-svelte-structure.mjs',import.meta.url).pathname],{stdio:'pipe'}); add('svelte-structure',true,'Svelte blocks and interactive SVG accessibility structure pass'); } catch (e) { add('svelte-structure',false,'Svelte structural/accessibility static gate failed'); }
try { execFileSync(process.execPath,[new URL('./check-frontend-security.mjs',import.meta.url).pathname],{stdio:'pipe'}); add('frontend-security',true,'frontend source is compatible with strict public CSP and contains no raw HTML/dynamic-code sinks'); } catch (e) { add('frontend-security',false,'frontend security/CSP static gate failed'); }
try { execFileSync(process.execPath,[new URL('./release-manifest.mjs',import.meta.url).pathname,'--check'],{stdio:'pipe'}); add('release-manifest',true,'source manifest is synchronized'); } catch (e) { add('release-manifest',false,'RELEASE-MANIFEST.json is missing or stale'); }
try { execFileSync(process.execPath,[new URL('./generate-sbom.mjs',import.meta.url).pathname,'--check'],{stdio:'pipe'}); add('sbom',true,'CycloneDX SBOM is synchronized and lockfile-complete'); } catch (e) { add('sbom',false,'SBOM.cdx.json is absent, stale, or incomplete without package-lock.json'); }
for(const file of ['contracts/navigation-plan.schema.json','contracts/navigation-projection.schema.json','contracts/renderer-registry.schema.json','contracts/navigation-hints.schema.json','contracts/exploration-state.schema.json']){
  try{JSON.parse(fs.readFileSync(new URL(`../${file}`,import.meta.url),'utf8'));add(`json:${file}`,true,'valid JSON');}catch(e){add(`json:${file}`,false,e.message);}
}
if(process.argv.includes('--execute')){
  const steps = [
    ['docs',['run','docs:check']],
    ['tests',['test']],
    ['ui-tests',['run','test:ui']],
    ['build',['run','build']],
    ['playwright',['run','test:e2e']],
    ['benchmark-full',['run','benchmark','--','--full']],
  ];
  for(const [id,args] of steps){
    try{execFileSync('npm',args,{stdio:'inherit'});add(id,true,'passed');}catch(e){add(id,false,`failed with ${e.status ?? 'unknown status'}`);}
  }
}
console.log(JSON.stringify({schemaVersion:'1.0',version:pkg.version,checks},null,2));
if(checks.some(c=>!c.ok)) process.exitCode=1;
