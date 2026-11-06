import { createHash } from 'node:crypto';
import { readFile } from 'node:fs/promises';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';
const root=fileURLToPath(new URL('../../',import.meta.url));
const manifest=JSON.parse(await readFile(join(root,'tools','dictionary-harvester','OVERLAY_MANIFEST.json'),'utf8'));
if(manifest.profile!=='encyklopedia.dictionary-harvester-overlay/0.3.0')throw Error('Invalid overlay manifest');
for(const item of manifest.files){
 if(typeof item.path!=='string'||item.path.includes('..')||item.path.startsWith('/')||item.path.includes('\\'))throw Error('Invalid manifest path');
 const b=await readFile(join(root,item.path));
 const sha=createHash('sha256').update(b).digest('hex');
 if(sha!==item.sha256)throw Error('Checksum mismatch: '+item.path);
}
console.log(`OK: ${manifest.files.length} overlay files verified`);
