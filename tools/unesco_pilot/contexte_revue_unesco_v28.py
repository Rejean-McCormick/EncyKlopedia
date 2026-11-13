#!/usr/bin/env python3
"""Contexte documentaire local pour les paquets UNESCO v28 (lecture seule).

Le CSV de decisions et ses preuves restent parfaitement immuables. Les extraits
proviennent exclusivement du XML local, via son index d'offsets v21 valide.
Sans XML fiable, la generation continue en indiquant les preuves manquantes.
"""
from __future__ import annotations

from contextlib import closing
import hashlib
import io
import json
import os
from pathlib import Path
import re
import sqlite3
import sys
import uuid
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parent))

FORMAT = 'encyklopedia.unesco-review-context.v28/1'
CACHE_VERSION = 3
MAX_PAGE_XML_BYTES = 2_000_000
MAX_EXCERPT_CHARS = 3400
MAX_EVIDENCE = 18
MAX_SEEDS_PER_ARTICLE = 2


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _plain_lead(wikitext: str) -> str:
    """Compact readable synopsis from local wikitext, not a fabricated summary."""
    # A few pages open with extensive infoboxes; inspect a bounded prefix.
    text = wikitext[:85000]
    text = re.sub(r'<!--.*?-->', ' ', text, flags=re.S)
    text = re.sub(r'<ref\b[^>]*>.*?</ref\s*>|<ref\b[^>]*/>', ' ', text, flags=re.I | re.S)
    text = re.sub(r'<(?!/?(?:br|p)\b)[^>]{1,300}>', ' ', text)
    # Strip nested MediaWiki templates without confusing the rest of the page.
    parts = []
    i = 0
    depth = 0
    while i < len(text):
        if text.startswith('{{', i):
            depth += 1; i += 2; continue
        if text.startswith('}}', i) and depth:
            depth -= 1; i += 2; continue
        if depth == 0:
            parts.append(text[i])
        i += 1
    text = ''.join(parts)
    text = re.split(r'(?m)^={2,}[^=\n]+={2,}\s*$', text, maxsplit=1)[0]
    text = re.sub(r'\[\[(?:File|Image|Category):[^\]]+\]\]', ' ', text, flags=re.I)
    text = re.sub(r'\[\[([^\]|]+)\|([^\]]+)\]\]', r'\2', text)
    text = re.sub(r'\[\[([^\]]+)\]\]', r'\1', text)
    text = re.sub(r'\[(https?://[^\s\]]+)(?:\s+([^\]]+))?\]', lambda m:m.group(2) or '', text)
    text = re.sub(r"'{2,5}", '', text)
    text = re.sub(r'(?m)^\s*[|!}{].*$', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text[:MAX_EXCERPT_CHARS]


def _concepts(repo: Path, stage: Path | None = None):
    # La branche du fichier v28 provient des métadonnées de la découverte, pas
    # d'un intitulé fourni par ChatGPT. Le code original ne connaissait que MT1.10.
    if stage is not None and stage.is_file():
        try:
            with closing(sqlite3.connect(stage.resolve().as_uri()+'?mode=ro',uri=True)) as db:
                value=db.execute("SELECT value FROM meta WHERE key='branch_id'").fetchone()
            bid=value[0] if value else None
            if bid:
                import catalogue_global_v25 as v25
                root=repo/'tools'/'unesco_pilot'/'v25_data'
                for manifest in sorted(root.rglob('branche_*.json')) if root.is_dir() else []:
                    b=v25.load_branch(manifest)
                    if b['id']!=bid:continue
                    result={}
                    for c in b['concepts']:
                        cid=c['unesco_id']
                        def vals(name,language):
                            item=c.get(name,{})
                            if isinstance(item,dict):
                                x=item.get(language,[])
                                return x if isinstance(x,list) else [x] if isinstance(x,str) else []
                            return []
                        result[cid]={
                          'titre_en':vals('preferred_labels','en')[:1],
                          'titre_fr':vals('preferred_labels','fr')[:1],
                          'note_portee_en':vals('scope_notes','en')[:2],
                          'note_portee_fr':vals('scope_notes','fr')[:2],
                          'autres_libelles_en':vals('alternate_labels','en')[:8],
                          'relations_broader':c.get('broader',[])[:10],
                          'source':'UNESCO Thesaurus local / '+bid}
                    return result
                return {}  # Manifeste non retrouvé : ne pas inventer des notes.
        except (OSError,ValueError,sqlite3.Error,KeyError,TypeError):
            pass
    path = repo/'tools'/'unesco_pilot'/'v25_data'/'unesco_2026_educational_policy.json'
    try:
        data = json.loads(path.read_text('utf-8'))
    except (OSError, ValueError):
        return {}
    def label(item,language):
        return item.get('preferred_labels',{}).get(language,[])[:1]
    result = {}
    for c in data.get('concepts',[]):
        cid = c.get('unesco_id')
        if cid:
            result[cid] = {
                'titre_en': label(c,'en'), 'titre_fr': label(c,'fr'),
                'note_portee_en': c.get('scope_notes',{}).get('en',[])[:2],
                'note_portee_fr': c.get('scope_notes',{}).get('fr',[])[:2],
                'autres_libelles_en': c.get('alternate_labels',{}).get('en',[])[:8],
                'relations_broader': c.get('broader',[])[:10],
                'source': 'UNESCO Thesaurus local'
            }
    return result


def _open_optional_xml_context():
    """Return (index db, XML binary file, reason); validate the index/source pair."""
    from pathlib import Path
    import production_kristals_v27 as v27
    xml = v27.DEFAULT_XML
    idx = v27.DEFAULT_INDEX
    if not xml.is_file():
        return None, None, 'XML source absent : '+str(xml)
    if not idx.is_file():
        return None, None, 'Index direct XML v21 absent : '+str(idx)
    index = None
    f = None
    try:
        signature = v27.xml_signature(xml)  # Only first and last MiB.
        index = v27.ro_sql(idx)
        actual = v27.value(index, 'v21_meta', 'source_signature')
        if not actual or json.loads(actual) != signature:
            raise ValueError('signature du XML differente de celle de l index v21')
        if json.loads(v27.value(index, 'v21_meta', 'complete') or 'false') is not True:
            raise ValueError('index XML incomplet')
        f = xml.open('rb')
        return index, f, None
    except (OSError, ValueError, sqlite3.Error, v27.Refusal) as ex:
        if index is not None: index.close()
        if f is not None: f.close()
        return None, None, 'XML/index non utilisable : '+str(ex)




def _open_prepared_xml_v31():
    """Cache d'extraits construit sur le XML lui-même (pas sur les offsets v21)."""
    from pathlib import Path
    import production_kristals_v27 as v27
    import preuves_xml_v31 as v31
    p=v31.DEFAULT_CACHE
    if not p.is_file():return None,'Cache XML V31 absent'
    db=None
    try:
        actual=v31.xml_sig(v27.DEFAULT_XML)
        db=sqlite3.connect(p.resolve().as_uri()+'?mode=ro',uri=True,timeout=10)
        db.row_factory=sqlite3.Row
        schema=db.execute("SELECT value FROM meta WHERE key='schema'").fetchone()
        sig=db.execute("SELECT value FROM meta WHERE key='xml_signature'").fetchone()
        if not schema or schema[0]!=v31.VERSION or not sig or sig[0]!=actual:
            raise ValueError('signature XML du cache v31 incompatible')
        return db,None
    except (ValueError,OSError,sqlite3.Error) as ex:
        if db:db.close()
        return None,'Cache V31 indisponible : '+str(ex)


def _prepared_article_v31(db,source,pid,labels):
    """Ne présente pas une citation si la révision ne correspond pas à wiki_pages."""
    if source is None:return {'etat':'verification_revision_impossible'}
    r=db.execute('SELECT * FROM prepared_pages WHERE page_id=?',(pid,)).fetchone()
    if r is None:return {'etat':'introuvable_dans_cache_v31'}
    page=source.execute('SELECT latest_revision,title FROM wiki_pages WHERE page_id=? AND ns=0',(pid,)).fetchone()
    if page is None or str(page[0])!=str(r['revision_id']):
        return {'etat':'revision_xml_differente','revision_xml':r['revision_id'],
                'revision_index':page[0] if page else None}
    wikitext=r['wikitext']
    if _sha(wikitext.encode('utf-8'))!=r['sha256_stored']:
        return {'etat':'cache_v31_empreinte_incoherente'}
    if r['complete_text'] and r['sha256_full']!=r['sha256_stored']:
        return {'etat':'cache_v31_empreinte_originale_incoherente'}
    return {'etat':'texte_source_verifie','title_xml':r['title'],'revision_id':r['revision_id'],
            'texte_intro':_plain_lead(wikitext),
            'passages_termes_concept':_targeted_passages(wikitext,labels),
            'empreinte_wikitexte_sha256':r['sha256_full'],
            'extrait_tronque':not bool(r['complete_text']),
            'source_extrait':'parcours_XML_v31_sans_index_offsets'}


def _targeted_passages(wikitext: str, labels: list[str]):
    """Find short observed passages, not generated summaries or invented facts."""
    words=[]
    for label in labels:
        words += [s.lower() for s in re.findall(r"[A-Za-z]{5,}", str(label))]
    words=[x for x in dict.fromkeys(words) if x not in
           {'about','after','other','there','which','their','these','those','education',
            'educational','policy','policies','state','school'}]
    words.sort(key=len,reverse=True)
    if not words:
        return []
    found=[]
    visited=[]
    for term in words[:8]:
        for match in re.finditer(r'\b'+re.escape(term)+r'\b',wikitext,flags=re.I):
            if any(abs(match.start()-pos)<280 for pos in visited):
                continue
            start=max(0,match.start()-160)
            end=min(len(wikitext),match.end()+210)
            snippet=wikitext[start:end]
            snippet=re.sub(r'\[\[([^\]|]+)\|([^\]]+)\]\]',r'\2',snippet)
            snippet=re.sub(r'\[\[([^\]]+)\]\]',r'\1',snippet)
            snippet=re.sub(r'<[^>]{1,180}>',' ',snippet)
            snippet=re.sub(r"'{2,5}",'',snippet)
            snippet=' '.join(snippet.split())[:400]
            if len(snippet)>60:
                found.append({'mot_recherche':term,'passage_source':snippet})
                visited.append(match.start())
            if len(found)>=3:
                return found
    return found


def _safe_article(index, xml_handle, page_id, cache, labels=None):
    """Targeted seek of one indexed page, bounded by index byte_length."""
    cache_key=(page_id,tuple(labels or []))
    if cache_key in cache:return cache[cache_key]
    import production_kristals_v27 as v27
    r = index.execute('SELECT byte_length FROM pages WHERE page_id=?',(page_id,)).fetchone()
    if r is None:
        obj={'etat':'introuvable_dans_index'}
    elif int(r[0]) > MAX_PAGE_XML_BYTES:
        obj={'etat':'article_trop_volumineux_pour_extrait','octets':int(r[0])}
    else:
        try:
            raw, revision, title = v27.page_from_index(index, xml_handle, page_id)
            obj = {'etat':'texte_source_verifie','title_xml':title,'revision_id':revision,
                   'texte_intro':_plain_lead(raw.decode('utf-8')),
                   'passages_termes_concept':_targeted_passages(raw.decode('utf-8'),labels or []),
                   'empreinte_wikitexte_sha256':_sha(raw)}
        except (OSError,ValueError,v27.Refusal,UnicodeError) as ex:
            obj={'etat':'impossible_de_lire_article','detail':str(ex)[:250]}
    cache[cache_key] = obj
    return obj


def _categories(source, pid):
    if source is None:return []
    try:
        cur = source.execute('''SELECT lt.title FROM wiki_categorylink_ids c INDEXED BY idx_wiki_catid_from
             JOIN wiki_linktargets lt ON lt.target_id=c.target_id AND lt.ns=14
             WHERE c.source_page_id=? LIMIT 31''',(pid,))
        return [str(r[0]).replace('_',' ') for r in cur]
    except sqlite3.Error:
        return []


def _open_source():
    import production_kristals_v27 as v27
    import catalogue_global_v25 as v25
    path=v25.DEFAULT_SOURCE if hasattr(v25,'DEFAULT_SOURCE') else Path(r'D:\EncyKlopedia\80_search_indexes\mediatheque-references\wikipedia_en.sqlite')
    try:
        return v27.ro_sql(path) if path.is_file() else None
    except (OSError,sqlite3.Error,v27.Refusal):
        return None


def _evidences(work, baseline):
    for row in baseline:
        evid = []
        if work is not None:
            try:
                result=work.execute('''SELECT e.seed_page_id,e.kind,e.detail,s.title AS seed_title
                  FROM evidence e LEFT JOIN seed_queue s
                    ON s.branch_id=e.branch_id AND s.page_id=e.seed_page_id
                  WHERE e.branch_id=? AND e.concept_id=? AND e.page_id=?
                  ORDER BY e.seed_page_id,e.kind,e.detail LIMIT ?''',
                  (row['branch_id'],row['concept_id'],int(row['page_id']),MAX_EVIDENCE))
                evid = [{'page_id_source':int(r['seed_page_id']),
                         'article_source':r['seed_title'] or str(r['seed_page_id']),
                         'type_lien':r['kind'],'detail':r['detail']} for r in result]
            except sqlite3.Error:
                evid=[]
        yield row,evid


def enriched_bytes(original: bytes, source_csv: bytes, repo: Path, stage: Path):
    """Augment only documentary context; never alter the original CSV or IDs."""
    import poste_chatgpt_v30 as v30
    rows = v30.read_baseline(source_csv)
    concepts = _concepts(repo,stage)
    ix = xhandle = prepared_v31 = None
    source = work = None
    reason = None
    from pathlib import Path
    import production_kristals_v27 as v27
    try:
        ix,xhandle,reason = _open_optional_xml_context()
        if ix is None:
            prepared_v31, cache_reason = _open_prepared_xml_v31()
            if prepared_v31 is not None:
                reason='Extraits XML V31 verifies directement (sans index v21)'
            else:
                reason='; '.join(filter(None,(reason,cache_reason)))
        source = _open_source()
        try:
            work = v27.ro_sql(stage) if stage.is_file() else None
        except (sqlite3.Error,OSError,v27.Refusal):
            work = None
        cached={}
        data=[]
        readable=0
        for row,evid in _evidences(work,rows):
            pid=int(row['page_id'])
            concept=concepts.get(row['concept_id'],{'titre_en':[row['concept_en']]})
            labels=concept.get('titre_en',[])+concept.get('autres_libelles_en',[])
            article=(_safe_article(ix,xhandle,pid,cached,labels) if ix is not None else
                _prepared_article_v31(prepared_v31,source,pid,labels) if prepared_v31 is not None else
                {'etat':'non_disponible','motif':reason})
            readable += article['etat']=='texte_source_verifie'
            data.append({
                'candidate_id':row['candidate_id'],'concept_id':row['concept_id'],
                'concept':concept,
                'article':{'page_id':pid,'titre':row['title'],'categories_wikipedia':_categories(source,pid),
                           **article},
                'resume_preuves_csv':{'exemples_originaux':row['examples'],
                    'nombre_graines':row['seed_count'], 'liens':row['link_evidence'],
                    'categories_partagees':row['category_evidence'],
                    'sous_categories':row['subcategory_evidence'],
                    'empreinte_preuves_originales':row['evidence_sha256']},
                'evidence':evid,
                'limites':('Cet extrait est un document-source local Wikipedia; il peut etre incomplete ou errone. '
                           'Un lien ou une categorie ne prouve pas a lui seul un rattachement UNESCO.')})
        contexts = ('\n'.join(json.dumps(v,ensure_ascii=False,sort_keys=True) for v in data)+'\n').encode('utf-8')
        manifest = {'format':FORMAT,'nombre_candidats':len(rows),
                    'extraits_xml_valides':readable,'extraits_xml_indisponibles':len(rows)-readable,
                    'source_csv_sha256':_sha(source_csv),'information_xml':reason or 'Index v21 et XML verifies',
                    'disponibilite_categories':source is not None,
                    'aucune_admission_canonique':True,'version_cache':CACHE_VERSION}
        guide = '''REVUE UNESCO v28 — CONTEXTE DOCUMENTAIRE ENRICHI\n\nLisez REVUE_*.csv et CONTEXTES_DOCUMENTAIRES_V28.jsonl en reliant les lignes par candidate_id.\nChaque ligne JSONL contient le concept UNESCO (labels et notes de portee), les categories de l article,\nles liens documentaires et, si le XML local indexe est disponible, un extrait d introduction et des passages contenant des termes du concept.\nLa preuve conserve sa provenance; une absence d extrait est indiquee explicitement.\nUtilisez APPROVE si l article traite substantiellement du concept (pas seulement s il le mentionne).\nUtilisez REJECT pour les liens manifestement hors sujet ou incidentalement lies.\nUtilisez HOLD si le contexte reste insuffisant ou contradictoire.\nNe fabriquez aucun fait. Ni canonisation ni publication.\nNe modifiez JAMAIS REVUE_*.csv ni les identifiants; repondez uniquement avec\nDECISIONS_<id>.csv a 3 colonnes candidate_id,decision,justification.\n'''.encode('utf-8')
        new = io.BytesIO()
        with zipfile.ZipFile(io.BytesIO(original),'r') as zin, zipfile.ZipFile(new,'w',zipfile.ZIP_DEFLATED,compresslevel=7) as zout:
            for info in zin.infolist():
                if info.filename in ('CONTEXTES_DOCUMENTAIRES_V28.jsonl','MANIFEST_CONTEXTE_V28.json','GUIDE_CONTEXTE_UNESCO_V28.txt'):
                    raise ValueError('Paquet source deja enrichi; version inattendue')
                content=zin.read(info.filename)
                if info.filename in ('PROMPT_CHATGPT.txt','INSTRUCTIONS_CHATGPT.txt'):
                    content += ("\n\nINFORMATION COMPLEMENTAIRE v28 : Consulter en priorite "
                        "CONTEXTES_DOCUMENTAIRES_V28.jsonl, joint a ce ZIP, avant de trancher. "
                        "Ce fichier contient les extraits locaux disponibles, les notes UNESCO et "
                        "les liens precis. Le rappel precedent decrit le CSV de base, pas "
                        "ce dossier enrichi. Les identifiants et le CSV source restent invariables.\n").encode('utf-8')
                zout.writestr(info,content)
            zout.writestr('CONTEXTES_DOCUMENTAIRES_V28.jsonl',contexts)
            zout.writestr('MANIFEST_CONTEXTE_V28.json',json.dumps(manifest,ensure_ascii=False,indent=2).encode('utf-8'))
            zout.writestr('GUIDE_CONTEXTE_UNESCO_V28.txt',guide)
        return new.getvalue(),manifest
    finally:
        if work is not None:work.close()
        if source is not None:source.close()
        if xhandle is not None:xhandle.close()
        if ix is not None:ix.close()
        if prepared_v31 is not None:prepared_v31.close()


def _input_state(stage: Path):
    """Stat only: refresh the context when the XML/index become available."""
    import production_kristals_v27 as v27
    import catalogue_global_v25 as v25
    def stat(path):
        try:
            s=path.stat()
            return [s.st_size,s.st_mtime_ns]
        except OSError:
            return None
    import preuves_xml_v31 as v31
    return {'xml':stat(v27.DEFAULT_XML),'index':stat(v27.DEFAULT_INDEX),
            'xml_cache_v31':stat(v31.DEFAULT_CACHE),
            'wikipedia_sqlite':stat(v25.DEFAULT_SOURCE),'v28_stage':stat(stage)}


def cached_enriched_bundle(source_bundle: Path, source_csv: Path, repo: Path,
                           stage: Path, work_root: Path):
    """Separate cache, leaving original ZIP and station SQLite immutable."""
    cache_dir=work_root/'review_context_cache'
    path=cache_dir/source_bundle.name
    stamp=cache_dir/(source_bundle.stem+'.provenance.json')
    original_hash=_sha(source_bundle.read_bytes())
    source_hash=_sha(source_csv.read_bytes())
    current_inputs=_input_state(stage)
    if path.is_file() and stamp.is_file():
        try:
            info=json.loads(stamp.read_text('utf-8'))
            if (info.get('version')==CACHE_VERSION and info.get('bundle_sha256')==original_hash and
                    info.get('source_sha256')==source_hash and info.get('inputs')==current_inputs and
                    info.get('output_sha256')==_sha(path.read_bytes())):
                return path
        except (OSError,ValueError):pass
    # Create only cache files, atomically; task/bundle hashes remain unchanged.
    augmented,manifest=enriched_bytes(source_bundle.read_bytes(),source_csv.read_bytes(),repo,stage)
    cache_dir.mkdir(parents=True,exist_ok=True)
    tmp=path.with_name(path.name+'.'+uuid.uuid4().hex+'.tmp')
    try:
        tmp.write_bytes(augmented)
        os.replace(tmp,path)
        stamp_tmp=stamp.with_name(stamp.name+'.'+uuid.uuid4().hex+'.tmp')
        try:
            stamp_tmp.write_text(json.dumps({'version':CACHE_VERSION,'bundle_sha256':original_hash,
                'source_sha256':source_hash,'output_sha256':_sha(augmented),
                'inputs':current_inputs,'manifest':manifest},ensure_ascii=False,indent=2),encoding='utf-8')
            os.replace(stamp_tmp,stamp)
        finally:
            if stamp_tmp.exists():stamp_tmp.unlink()
    finally:
        if tmp.exists():tmp.unlink()
    return path
