import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const offline = process.argv.includes('--offline');
const outputArg = process.argv.find((x) => x.startsWith('--output='));
const baseArg = process.argv.find((x) => x.startsWith('--base='));
const OUTPUT = outputArg ? path.resolve(ROOT, outputArg.slice(9)) : path.join(ROOT, 'data', 'biblical.pack.json');
const BASE = baseArg ? path.resolve(baseArg.slice(7).replace(/^\"|\"$/g, '')) : (process.env.KONSTELLATION_BASE_PACK ? path.resolve(process.env.KONSTELLATION_BASE_PACK) : path.join(ROOT, 'data', 'demo.pack.json'));
const seed = JSON.parse(fs.readFileSync(path.join(ROOT, 'data', 'biblical-seed.json'), 'utf8'));
const base = JSON.parse(fs.readFileSync(BASE, 'utf8'));
if (base.schemaVersion !== '0.3') throw new Error(`Base pack incompatible (${BASE}) : schemaVersion 0.3 requis.`);
console.log(`Base : ${BASE}`);

const BIBLE_DATA = 'https://raw.githubusercontent.com/BradyStephenson/bible-data/main/';
const URLS = {
  persons: BIBLE_DATA + 'BibleData-Person.csv',
  labels: BIBLE_DATA + 'BibleData-PersonLabel.csv',
  relationships: BIBLE_DATA + 'BibleData-PersonRelationship.csv',
};

function parseCsv(text) {
  const rows = [];
  let row = [], field = '', quoted = false;
  for (let i = 0; i < text.length; i += 1) {
    const c = text[i];
    if (quoted) {
      if (c === '"' && text[i + 1] === '"') { field += '"'; i += 1; }
      else if (c === '"') quoted = false;
      else field += c;
    } else if (c === '"') quoted = true;
    else if (c === ',') { row.push(field); field = ''; }
    else if (c === '\n') { row.push(field.replace(/\r$/, '')); rows.push(row); row = []; field = ''; }
    else field += c;
  }
  if (field || row.length) { row.push(field); rows.push(row); }
  const headers = rows.shift().map((x) => x.replace(/^\uFEFF/, ''));
  return rows.filter((r) => r.some(Boolean)).map((r) => Object.fromEntries(headers.map((h, i) => [h, r[i] ?? ''])));
}

async function fetchText(url) {
  const response = await fetch(url, { headers: { 'User-Agent': 'Konstellation-Biblical-Corpus/1.0' } });
  if (!response.ok) throw new Error(`${response.status} ${response.statusText} — ${url}`);
  return response.text();
}

const clone = (x) => structuredClone(x);
const pack = clone(base);
pack.title = 'Konstellation · Corpus biblique';
pack.description = 'Atlas des idées enrichi : personnes/personnages bibliques, œuvres canoniques, deutérocanoniques et apocryphes, attributions et degrés de certitude.';
pack.synthetic = false;
pack.registry.registryRef = 'konstellation:biblical-corpus-v1';

for (const t of ['person', 'event', 'group', 'term', 'tradition', 'work', 'concept'])
  if (!pack.registry.entityTypes.includes(t)) pack.registry.entityTypes.push(t);

const relationIds = new Set(pack.registry.relations.map((r) => r.id));
function addRelation(r) { if (!relationIds.has(r.id)) { relationIds.add(r.id); pack.registry.relations.push(r); } }
const ops = ['exists', 'missing_in_view', 'in', 'none_of'];
for (const r of [
  {id:'alias', label:{fr:'Alias',en:'alias'}, domain:['person','human','work','concept','event','group','term','tradition'], range:'string', valueKind:'string', operators:ops},
  {id:'role', label:{fr:'Rôle',en:'role'}, domain:['person'], range:'concept', valueKind:'entity', operators:ops},
  {id:'genre', label:{fr:'Genre',en:'genre'}, domain:['work'], range:'concept', valueKind:'entity', operators:ops},
  {id:'canonical_in', label:{fr:'Canonique dans',en:'canonical in'}, domain:['work'], range:'tradition', valueKind:'entity', operators:ops, inverseOf:'canonical_work'},
  {id:'canonical_work', label:{fr:'Œuvre canonique',en:'canonical work'}, domain:['tradition'], range:'work', valueKind:'entity', operators:ops, inverseOf:'canonical_in'},
  {id:'noncanonical_in', label:{fr:'Non canonique dans',en:'non-canonical in'}, domain:['work'], range:'tradition', valueKind:'entity', operators:ops},
  {id:'traditional_author', label:{fr:'Auteur attribué par la tradition',en:'traditional author'}, domain:['work'], range:'person', valueKind:'entity', operators:ops, inverseOf:'traditional_authorship'},
  {id:'traditional_authorship', label:{fr:'Œuvre traditionnellement attribuée',en:'traditionally attributed work'}, domain:['person'], range:'work', valueKind:'entity', operators:ops, inverseOf:'traditional_author'},
  {id:'historical_author', label:{fr:'Auteur historiquement attribué',en:'historical author'}, domain:['work'], range:'person', valueKind:'entity', operators:ops, inverseOf:'historical_authorship'},
  {id:'historical_authorship', label:{fr:'Œuvre attribuée historiquement',en:'historically authored work'}, domain:['person'], range:'work', valueKind:'entity', operators:ops, inverseOf:'historical_author'},
  {id:'pseudepigraphic_author', label:{fr:'Auteur pseudépigraphique',en:'pseudepigraphic author'}, domain:['work'], range:'person', valueKind:'entity', operators:ops, inverseOf:'pseudepigraphic_authorship'},
  {id:'pseudepigraphic_authorship', label:{fr:'Œuvre pseudépigraphique attribuée',en:'pseudepigraphic attributed work'}, domain:['person'], range:'work', valueKind:'entity', operators:ops, inverseOf:'pseudepigraphic_author'},
  {id:'disputed_author', label:{fr:'Attribution disputée',en:'disputed author'}, domain:['work'], range:'person', valueKind:'entity', operators:ops, inverseOf:'disputed_authorship'},
  {id:'disputed_authorship', label:{fr:'Œuvre à attribution disputée',en:'disputed authorship work'}, domain:['person'], range:'work', valueKind:'entity', operators:ops, inverseOf:'disputed_author'},
  {id:'attributed_author', label:{fr:'Auteur attribué',en:'attributed author'}, domain:['work'], range:'person', valueKind:'entity', operators:ops, inverseOf:'attributed_authorship'},
  {id:'attributed_authorship', label:{fr:'Œuvre attribuée',en:'attributed work'}, domain:['person'], range:'work', valueKind:'entity', operators:ops, inverseOf:'attributed_author'},
  {id:'authorship_note', label:{fr:"Note d'attribution",en:'authorship note'}, domain:['work'], range:'string', valueKind:'string', operators:ops},
  {id:'tribe', label:{fr:'Tribu',en:'tribe'}, domain:['person'], range:'string', valueKind:'string', operators:ops},
  {id:'sex', label:{fr:'Sexe dans la source',en:'sex in source'}, domain:['person'], range:'string', valueKind:'string', operators:ops}
]) addRelation(r);

const entities = new Map(pack.entities.map((e) => [e.id, e]));
function entity(id, type, label, description = '', extras = {}) {
  if (!entities.has(id)) { const e = {id,type,label,description,...extras}; entities.set(id,e); pack.entities.push(e); return e; }
  return entities.get(id);
}

for (const t of seed.traditions) entity(`biblical:tradition:${t.id}`, 'tradition', t.label, 'Tradition canonique utilisée comme contexte de classement.');
for (const role of seed.roles) entity(`biblical:role:${role.normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase().replace(/[^a-z0-9]+/g,'-').replace(/^-|-$/g,'')}`, 'concept', role, 'Rôle de navigation du corpus biblique.');
const genreIds = new Map();
function genreEntity(label) {
  if (!genreIds.has(label)) {
    const slug = label.normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase().replace(/[^a-z0-9]+/g,'-').replace(/^-|-$/g,'');
    genreIds.set(label, entity(`biblical:genre:${slug}`, 'concept', label, 'Genre ou famille littéraire.').id);
  }
  return genreIds.get(label);
}

const sources = new Map(pack.sources.map((s) => [s.id,s]));
function source(id,title,description,url) { if (!sources.has(id)) { const s={id,title,description,url}; sources.set(id,s); pack.sources.push(s); } }
source('biblical:bibledata','BibleData — structured biblical data','Brady Stephenson, BibleData. Import des personnes, variantes de noms et relations. Licence CC BY 4.0.','https://github.com/BradyStephenson/bible-data');
source('biblical:editorial','Konstellation Biblical Graph v1','Métadonnées éditoriales de navigation : canons, genres et distinctions de types d’attribution. Les niveaux de certitude empêchent de confondre tradition et conclusion historique.','local:Konstellation');
source('biblical:nasscal','NASSCAL · e-Clavis: Christian Apocrypha','Référence bibliographique pour le repérage et la nomenclature des textes apocryphes chrétiens.','https://www.nasscal.com/e-clavis-christian-apocrypha/');

let assertionCounter = Math.max(0,...pack.assertions.map((a)=>Number(String(a.id).match(/(\d+)$/)?.[1]||0)));
function addAssertion(subject, relation, value, {status='sourced',certainty='medium',validatedAs='sourced_claim',authority='authority:biblical-editorial',sourceRefs=['biblical:editorial'],scope='biblical-corpus'}={}) {
  pack.assertions.push({
    id:`biblical:a${String(++assertionCounter).padStart(7,'0')}`, subject, relation, value, status, certainty,
    validationStatus:'not_evaluated', validatedAs, authority, scope:{domain:scope}, sourceRefs
  });
}

const seedPeopleByKey = new Map(seed.people.map((p)=>[p.key,p]));
const importedPersonIds = new Map();
function safePart(x){ return String(x).replace(/[^a-zA-Z0-9_.:-]/g,'_'); }
function ensurePerson(key, fallbackLabel = key.replace(/_\d+$/,'')) {
  if (importedPersonIds.has(key)) return importedPersonIds.get(key);
  const meta = seedPeopleByKey.get(key);
  const id = `biblical:person:${safePart(key)}`;
  entity(id,'person',meta?.aliases?.[0] || meta?.label || fallbackLabel,'Personne ou personnage du corpus biblique. Le type « person » n’implique pas à lui seul une conclusion sur l’historicité.',{aliases:[...(meta?.aliases||[]),...(meta?.label?[meta.label]:[])]});
  importedPersonIds.set(key,id);
  return id;
}

let imported = {persons:0, aliases:0, relationships:0};
if (!offline) {
  try {
    console.log('Téléchargement BibleData…');
    const [personText,labelText,relationshipText] = await Promise.all([fetchText(URLS.persons),fetchText(URLS.labels),fetchText(URLS.relationships)]);
    const persons = parseCsv(personText);
    for (const p of persons) {
      const meta = seedPeopleByKey.get(p.person_id);
      const id = `biblical:person:${safePart(p.person_id)}`;
      const aliases = [...new Set([...(meta?.aliases||[]),p.person_name].filter(Boolean))];
      entity(id,'person',meta?.aliases?.[0] || p.person_name || p.person_id,p.unique_attribute || 'Personne ou personnage nommé dans le corpus biblique.',{aliases,bibleDataId:p.person_id});
      importedPersonIds.set(p.person_id,id); imported.persons += 1;
      if (p.tribe) addAssertion(id,'tribe',p.tribe,{authority:'authority:bibledata',sourceRefs:['biblical:bibledata'],certainty:'medium'});
      if (p.sex) addAssertion(id,'sex',p.sex,{authority:'authority:bibledata',sourceRefs:['biblical:bibledata'],certainty:'medium'});
    }
    const aliasesByPerson = new Map();
    for (const l of parseCsv(labelText)) {
      const id = importedPersonIds.get(l.person_id); if (!id) continue;
      const vals = [l.english_label,l.hebrew_label,l.hebrew_label_transliterated,l.greek_label,l.greek_label_transliterated].filter(Boolean);
      if (!aliasesByPerson.has(id)) aliasesByPerson.set(id,new Set());
      vals.forEach((v)=>aliasesByPerson.get(id).add(v));
    }
    for (const [id,set] of aliasesByPerson) {
      const e=entities.get(id); e.aliases=[...new Set([...(e.aliases||[]),...set])].slice(0,40); imported.aliases += set.size;
    }
    const relLabels = {
      father:'père',mother:'mère',son:'fils',daughter:'fille',brother:'frère',sister:'sœur',husband:'époux',wife:'épouse',ancestor:'ancêtre',descendant:'descendant',killer:'meurtrier de','killed by':'tué par',teacher:'maître de',student:'disciple de',friend:'ami de',servant:'serviteur de',master:'maître de',king:'roi de'
    };
    for (const rel of parseCsv(relationshipText)) {
      const s = importedPersonIds.get(rel.person_id_1), v = importedPersonIds.get(rel.person_id_2); if (!s || !v) continue;
      const slug = rel.relationship_type.normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase().replace(/[^a-z0-9]+/g,'-').replace(/^-|-$/g,'') || 'related';
      const rid = `bibrel.${slug}`;
      if (!relationIds.has(rid)) addRelation({id:rid,label:{fr:relLabels[rel.relationship_type.toLowerCase()]||rel.relationship_type,en:rel.relationship_type},domain:['person'],range:'person',valueKind:'entity',operators:ops});
      addAssertion(s,rid,v,{status:rel.relationship_category==='inferred'?'hypothesis':'sourced',certainty:rel.relationship_category==='inferred'?'medium':'high',validatedAs:rel.relationship_category==='inferred'?'inferred_relation':'textual_relation',authority:'authority:bibledata',sourceRefs:['biblical:bibledata'],scope:'biblical-text'});
      imported.relationships += 1;
    }
  } catch (err) {
    console.warn('BibleData indisponible : génération du corpus de base seulement.');
    console.warn(err.message);
  }
}

// Ensure curated people exist even if the network import was skipped or a source key differs.
for (const [id,label,aliases] of [
  ['holy-spirit','Saint-Esprit',['Esprit Saint','st-esprit','pneumatologie']],
  ['resurrection','Résurrection',['ressurection','resurection']],
  ['parousia','Parousie',['second avènement','retour du Christ']],
  ['eschatology','Eschatologie',['fins dernières']],
  ['iconoclasm','Iconoclasme',['iconoclaste','icônes','images sacrées']],
  ['revelation','Révélation',['inspiration']],
  ['covenant','Alliance',['alliance biblique']],
  ['law','Loi',['Torah']],
  ['prophecy','Prophétisme',['prophétie']]
]) entity(`biblical:concept:${id}`,'concept',label,'Concept servant de cap à l’Astrolabe.',{aliases});

for (const p of seed.people) ensurePerson(p.key,p.label);

for (const p of seed.people) {
  const pid = ensurePerson(p.key,p.label);
  const e = entities.get(pid); e.aliases = [...new Set([...(e.aliases||[]),...(p.aliases||[]),p.label])];
  for (const alias of p.aliases||[]) addAssertion(pid,'alias',alias,{certainty:'high'});
  for (const role of p.roles||[]) {
    const slug = role.normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase().replace(/[^a-z0-9]+/g,'-').replace(/^-|-$/g,'');
    addAssertion(pid,'role',`biblical:role:${slug}`,{certainty:'medium'});
  }
}

const authorRelation = (kind) => ({
  historical:'historical_author', traditional:'traditional_author', traditional_disputed:'disputed_author', disputed:'disputed_author', pseudepigraphic:'pseudepigraphic_author', attributed:'attributed_author'
}[kind] || 'attributed_author');

for (const w of seed.works) {
  const wid = `biblical:work:${safePart(w.id)}`;
  const descBits = [w.genre, w.ecca].filter(Boolean);
  entity(wid,'work',w.label,descBits.join(' · ') || 'Œuvre du corpus biblique et para-biblique.',{aliases:[w.id],ecca:w.ecca||undefined});
  if (w.genre) addAssertion(wid,'genre',genreEntity(w.genre),{certainty:'high'});
  for (const c of w.canonical||[]) addAssertion(wid,'canonical_in',`biblical:tradition:${c}`,{certainty:'high',validatedAs:'canonical_status'});
  for (const c of w.noncanonical||[]) addAssertion(wid,'noncanonical_in',`biblical:tradition:${c}`,{certainty:'high',validatedAs:'canonical_status'});
  if (w.author?.person) {
    const pid = ensurePerson(w.author.person);
    const relation = authorRelation(w.author.kind);
    const status = ['disputed','traditional_disputed'].includes(w.author.kind)?'disputed':'sourced';
    const validatedAs = w.author.kind==='historical'?'historical_authorship':w.author.kind==='pseudepigraphic'?'pseudepigraphic_attribution':w.author.kind==='traditional'?'traditional_attribution':w.author.kind==='traditional_disputed'?'traditional_attribution_disputed':'attributed_authorship';
    addAssertion(wid,relation,pid,{status,certainty:w.author.certainty||'medium',validatedAs});
    if (w.author.note) addAssertion(wid,'authorship_note',w.author.note,{certainty:'high'});
  }
}

// Make policies admit the new documented authorities without weakening their status filters.
for (const policy of pack.policies) {
  for (const authority of ['authority:biblical-editorial','authority:bibledata']) if (!policy.authorities.includes(authority)) policy.authorities.push(authority);
}

fs.mkdirSync(path.dirname(OUTPUT),{recursive:true});
fs.writeFileSync(OUTPUT,JSON.stringify(pack,null,2)+'\n');
console.log(`Corpus écrit : ${OUTPUT}`);
console.log(`Entités : ${pack.entities.length} · assertions : ${pack.assertions.length} · relations : ${pack.registry.relations.length}`);
if (imported.persons) console.log(`BibleData : ${imported.persons} personnes · ${imported.aliases} alias · ${imported.relationships} relations.`);
else console.log('Mode de base : personnages/auteurs curatés + œuvres. Relancer sans --offline pour importer toutes les personnes BibleData.');
