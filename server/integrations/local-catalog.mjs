// Opt-in local selection catalogue. Only immediate children of one operator-configured root.
// This is NOT a qualification, publishing, or authorization mechanism.
import fs from 'node:fs';
import path from 'node:path';
import { fail } from '../errors.mjs';
import { loadConfig } from '../config.mjs';
import { inspectLocalV10, loadLocalV10 } from './kristal-local-v10.mjs';


const ID = /^[A-Za-z0-9][A-Za-z0-9_.-]{0,119}$/;
function rootAndEntries(config, base) {
  // The server defaults to deploymentProfile='local' when unset (loadConfig).
  // Apply the SAME normalized configuration here, rather than requiring a
  // raw environment variable that the neutral launcher never needed to set.
  const runtime = loadConfig();
  if (runtime.deploymentProfile !== 'local' ||
      !['127.0.0.1','localhost','::1'].includes(runtime.host) ||
      runtime.anonymousReadonly)
    fail('INVALID_CONFIG','Le catalogue local nécessite une session locale privée.',422);
  if (typeof config.directory !== 'string' || !config.directory || config.directory.length > 4096)
    fail('INVALID_CONFIG','Le dossier racine des Kristals est requis.',422);
  let root;
  try { root=fs.realpathSync(path.resolve(base,config.directory)); }
  catch { fail('KRISTAL_CATALOG_UNAVAILABLE','Dossier local des Kristals introuvable.',422); }
  if (!fs.statSync(root).isDirectory()) fail('KRISTAL_CATALOG_UNAVAILABLE','Dossier local invalide.',422);
  const children=fs.readdirSync(root,{withFileTypes:true});
  if (children.length>500) fail('KRISTAL_CATALOG_LIMIT','Catalogue local trop volumineux.',422);
  return {root,children};
}
function configured(config, root, name) {
  if (!ID.test(name)) fail('KRISTAL_NOT_FOUND','Identifiant de Kristal invalide.',422);
  const child=path.join(root,name);
  const stat=fs.lstatSync(child);
  if (!stat.isDirectory() || stat.isSymbolicLink() || fs.realpathSync(child)!==child)
    fail('KRISTAL_NOT_FOUND','Dossier de Kristal non autorisé.',422);
  const model=config.readModels?.[name];
  return {directory:child,...(model?{readModel:model}:{})};
}
export function listLocalCatalog(config,base) {
  const {root,children}=rootAndEntries(config,base);
  const items=[];
  for (const entry of children.sort((a,b)=>a.name.localeCompare(b.name,'fr'))) {
    if (!entry.isDirectory() || entry.isSymbolicLink() || !ID.test(entry.name)) continue;
    const workspace=path.join(root,entry.name,'kristal.workspace.json');
    if (!fs.existsSync(workspace)) continue;
    try {
      const {workspace:info}=inspectLocalV10(configured(config,root,entry.name),base);
      items.push({id:entry.name,label:info.title,stateRef:info.state_ref,available:true});
    } catch {
      items.push({id:entry.name,label:entry.name,available:false,reason:'Contrat local non pris en charge ou vérification impossible.'});
    }
  }
  return items;
}
export function loadLocalCatalog(config,base,kristal) {
  const {root,children}=rootAndEntries(config,base);
  if (!ID.test(kristal || '') || !children.some(e=>e.name===kristal && e.isDirectory() && !e.isSymbolicLink()))
    fail('KRISTAL_NOT_FOUND','Kristal non sélectionné ou non autorisé.',422);
  return loadLocalV10(configured(config,root,kristal),base);
}
export function loadNeutralCatalog(base) {
  return JSON.parse(fs.readFileSync(path.resolve(base,'../data/neutral.pack.json'),'utf8'));
}
