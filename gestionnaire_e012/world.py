"""E3.3: exact Q lookup via existing Skope locator, no implicit scan/network/write."""
from __future__ import annotations
import hashlib, importlib.util, json, pickle, pickletools, io, re, subprocess, sys
from pathlib import Path
from ressources import small_json

VENDOR = 'ecosystem/Kristal_UNESCO_Factory/vendor/wikidata_skope/fastio.py'
VENDOR_SHA = 'e6bc9a7203ec2f2916db90ba2d991f5b0e920bf06545f849b3adc58583fe8c07'
REPO = Path(__file__).resolve().parent.parent
MAX_PICKLE = 64*1024*1024
MAX_LINE = 64*1024*1024

def isolated_python():
    p=Path.home()/'ENCYK_RUNTIME'/'wikidata-fast-py314'/'Scripts'/'python.exe'
    return p if p.is_file() else None

class DataOnly(pickle.Unpickler):
    def find_class(self, module, name):
        raise pickle.UnpicklingError('Objet executable interdit')
    def persistent_load(self, pid):
        raise pickle.UnpicklingError('Reference externe interdite')

def offsets(path, dump_bytes):
    # The builder serialized a plain dict[int,int]. No globals or persistent objects.
    # Size limit + subprocess timeout; no authentication of the derived sidecar implied.
    if not 0 < path.stat().st_size <= MAX_PICKLE: raise ValueError('Taille index compression hors limite')
    raw=path.read_bytes()
    if len(raw)>MAX_PICKLE: raise ValueError('Index compression trop volumineux')
    allowed={'PROTO','FRAME','EMPTY_DICT','MEMOIZE','MARK','BININT','BININT1','BININT2','LONG1','LONG4','SETITEM','SETITEMS','STOP','BINPUT','LONG_BINPUT'}
    for op,_,_ in pickletools.genops(raw):
        if op.name not in allowed: raise pickle.UnpicklingError('Opcode interdit : '+op.name)
    f=io.BytesIO(raw);d=DataOnly(f).load()
    if f.read(1): raise ValueError('Donnees surnumeraires dans index compression')
    if type(d) is not dict or not d or len(d)>10_000_000: raise ValueError('Table offsets invalide')
    if any(type(k) is not int or type(v) is not int or not 0<=k<=dump_bytes*8 or not 0<=v<2**63 for k,v in d.items()): raise ValueError('Offset invalide')
    return d

def manifest(data):
    data=Path(data)
    evidence=small_json(data/'20_evidence/manifests/wikidata-dump-verified.json')
    sha=evidence.get('sha1')
    if not isinstance(sha,str) or not re.fullmatch('[0-9a-f]{40}',sha) or evidence.get('verified') is not True or evidence.get('expected_sha1')!=sha: raise ValueError('Verification historique du dump absente')
    dump=Path(evidence['file']); root=data/'10_sources/wikidata/dumps/current'
    if dump.resolve().parent!=root.resolve() or not dump.name.endswith('.json.bz2') or dump.stat().st_size!=evidence.get('bytes'): raise ValueError('Dump / taille incoherents')
    directory=data/'30_working/wikidata-fast'/('sha1-'+sha)
    m=small_json(directory/'manifest.json'); d=m['dump']; backend=m['backend']
    if m.get('schema_version')!='encyklopedia-wikidata-fast-access/v2' or m.get('complete') is not True or m.get('random_access_capable_at_build') is not True or backend.get('backend')!='indexed_bzip2' or backend.get('compression')!='bzip2' or backend.get('random_access') is not True: raise ValueError('Contrat index rapide incompatible')
    if d.get('dump_id')!='sha1-'+sha or d.get('sha1')!=sha or d.get('identity_strength')!='verified_checksum' or d.get('bytes')!=evidence['bytes'] or Path(d['path']).resolve()!=dump.resolve() or d.get('filename')!=dump.name: raise ValueError('Identite du dump incompatible')
    if m.get('locator_file')!='qid-locator.bin' or m.get('compression_index_file')!='compression.bz2blocks.pkl': raise ValueError('Noms sidecars incompatibles')
    locator=directory/'qid-locator.bin'; compression=directory/'compression.bz2blocks.pkl'; maxq=m.get('max_qid'); q=m.get('q_items'); scanned=m.get('entity_lines_scanned')
    if any(type(v) is not int or v<=0 for v in (maxq,q,scanned)) or not q<=min(maxq,scanned) or locator.stat().st_size!=m.get('locator_bytes') or locator.stat().st_size!=(maxq+1)*16 or not 0<compression.stat().st_size<=MAX_PICKLE: raise ValueError('Dimensions sidecars incoherentes')
    return m,dump,locator,compression

def status(data):
    try:
        m,_,_,_=manifest(data)
        return {'state':'MANIFEST_MATCHES_METADATA','q_items':m['q_items'],'entity_lines_scanned':m['entity_lines_scanned'],'max_qid':m['max_qid'],'integrity_recomputed':False,'sidecar_content_verified':False}
    except (ValueError,OSError,KeyError,TypeError) as e:return {'state':'MANIFEST_NOT_VALIDATED','error':str(e)}

def vendor(repo=REPO):
    p=repo/VENDOR
    if hashlib.sha256(p.read_bytes().replace(b'\r\n',b'\n')).hexdigest()!=VENDOR_SHA: raise ValueError('Lecteur Skope local different du snapshot')
    spec=importlib.util.spec_from_file_location('encyk_skope_fastio_pinned',p); mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod

def validate_query(wid,languages):
    if not isinstance(wid,str) or not re.fullmatch(r'Q[1-9][0-9]{0,17}',wid): raise ValueError('Acces mondial Q uniquement ; utiliser le compact pour P')
    if languages is not None and (not languages or len(languages)>16 or len(set(languages))!=len(languages) or any(not isinstance(s,str) or not re.fullmatch(r'[a-zA-Z0-9]+(?:-[a-zA-Z0-9]+)*',s) or len(s)>40 for s in languages)): raise ValueError('Codes exacts : 1 a 16 langues distinctes')

def extract(raw, wid, languages, source):
    e=json.loads(raw)
    if not isinstance(e,dict) or e.get('id')!=wid or e.get('type')!='item': raise ValueError('Identite Q inattendue dans le dump')
    rev=e.get('lastrevid'); fields={k:e.get(k,{}) for k in ('labels','descriptions','aliases')}
    if type(rev) is not int or rev<=0 or any(not isinstance(v,dict) for v in fields.values()): raise ValueError('Revision ou champs invalides')
    langs=languages if languages is not None else sorted(set().union(*(v.keys() for v in fields.values())))
    rows=[]
    def val(x,lang):
        if not isinstance(x,dict) or x.get('language')!=lang or not isinstance(x.get('value'),str): raise ValueError('Valeur linguistique incoherente')
        return x['value']
    for l in langs:
        label=val(fields['labels'][l],l) if l in fields['labels'] else None
        desc=val(fields['descriptions'][l],l) if l in fields['descriptions'] else None
        aliases=fields['aliases'].get(l,[])
        if not isinstance(aliases,list):raise ValueError('Alias invalides')
        if label is not None or desc is not None or aliases: rows.append({'language':l,'label':label,'description':desc,'names':[{'name_kind':'alias','value':val(a,l)} for a in aliases]})
    return dict(source,state='FOUND_IN_LOCAL_DUMP',source_revision=rev,raw_record_sha256=hashlib.sha256(raw).hexdigest(),rows=rows,not_observed_in_index=[l for l in langs if not any(r['language']==l for r in rows)])

def read_world(data,wid,languages,repo=REPO):
    validate_query(wid,languages);m,dump,locator,compression=manifest(data)
    source={'scope':'RAW_DUMP_CANDIDATE_READ_ONLY','external_id':wid,'dump_file':dump.name,'dump_sha1_recorded':m['dump']['sha1'],'publication_authorized':False,'fallback':False,'integrity_recomputed':False,'languages_requested':languages,'rows':[]}
    f=vendor(repo)
    if f.module_status()['indexed_bzip2'] is not True: raise ValueError('indexed_bzip2 absent du Python courant ; aucune lecture sequentielle de secours')
    with f.DenseQidLocatorReader(locator) as loc: entry=loc.get(int(wid[1:]))
    if entry is None:return dict(source,state='NOT_FOUND_IN_Q_LOCATOR')
    off,length,flags=entry
    if flags!=1 or not 0<length<=MAX_LINE: raise ValueError('Entree locator hors contrat')
    blocks=offsets(compression,dump.stat().st_size)
    # Reuse the native reader but do NOT pass index_path (its legacy loader uses unrestricted pickle).
    with f.DumpStream(dump,threads=4) as ds:
        if ds.backend!='indexed_bzip2' or not ds.random_access: raise ValueError('Acces aleatoire indisponible')
        ds.file.set_block_offsets(blocks)
        ds.seek(off)
        raw=ds.read(length)
        if len(raw)!=length: raise ValueError('Lecture tronquee')
    raw=f.normalize_dump_line(raw)
    if raw is None:raise ValueError('Ligne vide')
    return extract(raw,wid,languages,source)

def lookup_world(data,wid,languages):
    validate_query(wid,languages)
    # Bound the native operation in a child, not a Tk thread or an unbounded scan.
    args=[str(isolated_python() or sys.executable),'-B',str(Path(__file__).resolve()),str(data),wid,json.dumps(languages)]
    try: p=subprocess.run(args,capture_output=True,encoding='utf-8',errors='replace',timeout=180)
    except subprocess.TimeoutExpired as e:raise ValueError('Lecture interrompue (180 s) ; aucun repli') from e
    if p.returncode:raise ValueError(p.stderr.strip()[-2000:] or 'Lecteur mondial en echec')
    return json.loads(p.stdout)

if __name__=='__main__':
    try:
        sys.stdout.reconfigure(encoding='utf-8');sys.stderr.reconfigure(encoding='utf-8')
        print(json.dumps(read_world(Path(sys.argv[1]),sys.argv[2],json.loads(sys.argv[3])),ensure_ascii=False))
    except Exception as e:print(str(e),file=sys.stderr);sys.exit(2)
