from __future__ import annotations

import bz2, gzip, hashlib, json, os, re, shutil, sqlite3, sys, zlib
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Iterator


LIB = Path(__file__).resolve().parents[4] / '00_system' / 'lib'
if str(LIB) not in sys.path:
    sys.path.insert(0, str(LIB))
import encyklopedia_fast as fastio

OFFSETS = {"Q": 0, "P": 1_000_000_000, "L": 2_000_000_000}
ID_RE = re.compile(rb'"id"\s*:\s*"([QPL]\d+)"')
QID_RE = re.compile(r"^Q\d+$")


def find_root(start: str | Path | None = None) -> Path:
    p = Path(start or __file__).resolve()
    if p.is_file(): p = p.parent
    for cand in [p, *p.parents]:
        if (cand / "MANIFEST.json").exists() and (cand / "10_sources").exists() and (cand / "30_working").exists(): return cand
    raise RuntimeError("Racine EncyKlopedia introuvable")


def utc_now() -> str: return datetime.now(timezone.utc).isoformat()

def json_loads(data: bytes | str) -> Any: return fastio.loads(data)

def performance_status(root: Path | None = None) -> dict[str,Any]: return fastio.module_status(root)

def load_json(path: str | Path, default: Any = None) -> Any:
    p=Path(path)
    if not p.exists(): return default
    return json.loads(p.read_text(encoding="utf-8-sig"))

def save_json(path: str | Path, obj: Any) -> None:
    p=Path(path); p.parent.mkdir(parents=True,exist_ok=True); tmp=p.with_suffix(p.suffix+".tmp")
    tmp.write_text(json.dumps(obj,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8"); os.replace(tmp,p)

def write_jsonl(path: str | Path, rows: Iterable[dict[str,Any]]) -> int:
    p=Path(path); p.parent.mkdir(parents=True,exist_ok=True); n=0
    with p.open("w",encoding="utf-8",newline="\n") as f:
        for row in rows: f.write(json.dumps(row,ensure_ascii=False,sort_keys=True)+"\n"); n+=1
    return n

def read_jsonl(path: str | Path) -> list[dict[str,Any]]:
    p=Path(path); out=[]
    if not p.exists(): return out
    with p.open(encoding="utf-8-sig") as f:
        for line in f:
            if line.strip(): out.append(json.loads(line))
    return out

def sha256_file(path: str | Path, chunk:int=8*1024*1024)->str:
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        while True:
            b=f.read(chunk)
            if not b: break
            h.update(b)
    return h.hexdigest()

def sha256_bytes(b:bytes)->str: return hashlib.sha256(b).hexdigest()

def encode_wid(wid:str|None)->int|None:
    if not wid or len(wid)<2:return None
    p=wid[0].upper()
    if p not in OFFSETS or not wid[1:].isdigit():return None
    return OFFSETS[p]+int(wid[1:])

def decode_wid(n:int|None)->str|None:
    if n is None:return None
    n=int(n)
    if n>=OFFSETS["L"]:return f"L{n-OFFSETS['L']}"
    if n>=OFFSETS["P"]:return f"P{n-OFFSETS['P']}"
    return f"Q{n}"

def normalize_name(value:str|None)->str:
    import unicodedata
    if not value:return ""
    s=unicodedata.normalize("NFKD",value); s="".join(ch for ch in s if not unicodedata.combining(ch)); s=s.casefold(); s=re.sub(r"[^\w]+"," ",s,flags=re.UNICODE)
    return " ".join(s.split())

def open_db(path:str|Path,read_only:bool=True)->sqlite3.Connection:
    p=Path(path).resolve()
    if read_only:c=sqlite3.connect(f"file:{p.as_posix()}?mode=ro",uri=True)
    else:p.parent.mkdir(parents=True,exist_ok=True); c=sqlite3.connect(p)
    c.row_factory=sqlite3.Row; return c

def db_meta(c:sqlite3.Connection)->dict[str,str]:
    try:return {r["key"]:r["value"] for r in c.execute("SELECT key,value FROM meta")}
    except sqlite3.DatabaseError:return {}

def assert_global_index(c:sqlite3.Connection,require_complete:bool=True)->dict[str,str]:
    tables={r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'")}; needed={"entity","name","claim_presence","entity_edge","chronology"}; missing=needed-tables
    if missing:raise RuntimeError(f"Index global incomplet: tables manquantes {sorted(missing)}")
    m=db_meta(c)
    if require_complete and m.get("complete") not in {"1","true","True"}:raise RuntimeError("L'index global n'est pas marqué complete=1.")
    return m

def default_global_db(root:Path)->Path:
    candidates=[root/"30_working/wikidata/wikidata.compact.sqlite",root/"30_working/wikidata.compact.sqlite",root/"00_system/tools/wikidata-manager/workspace/wikidata.compact.sqlite"]
    for p in candidates:
        if p.exists():return p
    return candidates[0]

def global_index_status(root:Path,db:Path|None=None)->tuple[bool,dict[str,Any]]:
    p=db or default_global_db(root)
    if not p.exists():return False,{"path":str(p),"exists":False,"complete":False}
    try:
        c=open_db(p,True); meta=assert_global_index(c,False); c.close(); ok=meta.get("complete") in {"1","true","True"}; return ok,{"path":str(p),"exists":True,"complete":ok,**meta}
    except Exception as e:return False,{"path":str(p),"exists":True,"complete":False,"error":str(e)}

def choose_discovery_backend(root:Path,requested:str="auto",db:Path|None=None,dump:Path|None=None)->str:
    requested=(requested or "auto").lower()
    if requested not in {"auto","index","fast","raw"}:raise ValueError(requested)
    if requested=="raw":return "raw"
    ok,_=global_index_status(root,db)
    if requested=="index":
        if not ok:raise RuntimeError("Backend index demandé mais l'index global complet n'est pas disponible.")
        return "index"
    if requested=="fast":
        try: dump=dump or find_dump(root)
        except Exception: dump=None
        fok,fi=fast_access_status(root,dump) if dump else (False,{})
        if not (fok and fi.get('random_access_ready')):raise RuntimeError("Backend fast demandé mais le fast-access index n'est pas disponible.")
        return "fast"
    if ok:return "index"
    try: dump=dump or find_dump(root); fok,fi=fast_access_status(root,dump); fok=bool(fok and fi.get('random_access_ready'))
    except Exception:fok=False
    return "fast" if fok else "raw"

def find_dump(root:Path)->Path:
    dirs=[root/"10_sources/wikidata/dumps/current",root/"10_sources/wikidata/dump",root/"00_system/tools/wikidata-manager/workspace/dump"]
    pats=("*.json.bz2","*.json.gz","*.json")
    for d in dirs:
        if not d.exists():continue
        xs=[]
        for pat in pats:xs.extend(d.glob(pat))
        xs=sorted(xs,key=lambda p:p.stat().st_mtime,reverse=True)
        if xs:return xs[0]
    xs=[]
    for pat in ("**/*wikidata*.json.bz2","**/*wikidata*.json.gz","**/*wikidata*.json"):xs.extend(root.glob(pat))
    xs=sorted(set(xs),key=lambda p:p.stat().st_mtime,reverse=True)
    if xs:return xs[0]
    raise FileNotFoundError("Dump Wikidata .json.bz2/.json.gz/.json introuvable")

def dump_descriptor(root:Path,dump:Path)->dict[str,Any]:
    dump=dump.resolve(); st=dump.stat(); found={}
    candidates=[root/"20_evidence/manifests/wikidata-dump-verified.json",root/"20_evidence/acquisition-snapshots/wikidata/latest.json",root/"00_system/tools/wikidata-manager/workspace/dump.verified.json",root/"00_system/tools/wikidata-manager/workspace/snapshot.json"]
    for p in candidates:
        obj=load_json(p,{}) or {}
        if not isinstance(obj,dict):continue
        name=Path(str(obj.get("file") or obj.get("filename") or "")).name
        if name and name!=dump.name:continue
        if obj.get("sha1") or obj.get("expected_sha1"):
            found={**obj,"manifest_path":str(p)}; break
    sha1=(found.get("sha1") or found.get("expected_sha1") or "").lower() or None
    if sha1:
        dump_id="sha1-"+sha1; strength="verified_checksum" if found.get("verified") is not False else "declared_checksum"
    else:
        weak=hashlib.sha256(f"{dump.name}|{st.st_size}".encode()).hexdigest()[:24]; dump_id=f"file-{weak}"; strength="filename_and_size"
    return {"dump_id":dump_id,"filename":dump.name,"path":str(dump),"bytes":st.st_size,"sha1":sha1,"identity_strength":strength,"manifest_path":found.get("manifest_path")}

def load_scope_config(root:Path,scope:str|Path)->tuple[Path,dict[str,Any]]:
    p=Path(scope)
    if not p.exists():p=root/"00_system/tools/scope-builder/config/scopes"/(str(scope) if str(scope).endswith(".json") else f"{scope}.scope.json")
    if not p.exists():raise FileNotFoundError(p)
    return p,load_json(p,{})

def property_groups(root:Path)->dict[str,dict[str,str]]:
    o=load_json(root/"00_system/tools/scope-builder/config/property-groups.json",{}) or {}; return o.get("groups") or {}

def scope_workdir(root:Path,scope_key:str)->Path:return root/"30_working/scopes"/scope_key

def scope_snapshot_dir(root:Path,scope_key:str,snapshot_id:str)->Path:return root/"20_evidence/scope-snapshots"/scope_key/snapshot_id


IDENTITY_KIND_HINTS = {
    "person","collective","work","edition","manifestation","document","concept","place",
    "installation","activity","process","event","physical_object","system","other"
}

def scope_root_semantics(cfg:dict[str,Any])->dict[str,str]:
    sem=cfg.get("root_semantics") or {}
    role=str(sem.get("role") or "person_root")
    kind=str(sem.get("kind") or ("person" if role=="person_root" else "other"))
    if kind not in IDENTITY_KIND_HINTS:kind="other"
    return {"role":role,"kind":kind}

def include_all_root_relations(cfg:dict[str,Any])->bool:
    disc=cfg.get("discovery") or {}
    if "include_all_entity_relations_from_roots" in disc:
        return bool(disc.get("include_all_entity_relations_from_roots"))
    return bool(disc.get("include_all_entity_relations_from_root_people",True))

def reverse_root_relations(cfg:dict[str,Any])->dict[str,dict[str,str]]:
    """Return generic reverse-root discovery rules.

    v0.11 format:
      discovery.reverse_root_relations.P50 = {"source_role":"work","relation_role":"authored_work"}

    Legacy people-first settings remain accepted.
    """
    disc=cfg.get("discovery") or {}
    raw=disc.get("reverse_root_relations")
    out={}
    if isinstance(raw,dict):
        for pid,val in raw.items():
            if not (isinstance(pid,str) and pid.startswith("P") and pid[1:].isdigit()):continue
            if isinstance(val,str):
                out[pid]={"source_role":"other","relation_role":val}
            elif isinstance(val,dict):
                out[pid]={
                    "source_role":str(val.get("source_role") or "other"),
                    "relation_role":str(val.get("relation_role") or val.get("role") or "reverse_root_relation"),
                }
        return out
    if disc.get("include_reverse_authored_works",True):
        for pid,label in (disc.get("reverse_work_properties") or {"P50":"authored_work"}).items():
            out[pid]={"source_role":"work","relation_role":str(label)}
    return out

def root_neighbor_role(cfg:dict[str,Any])->str:
    disc=cfg.get("discovery") or {}
    if disc.get("default_root_neighbor_role"):return str(disc["default_root_neighbor_role"])
    return "person_neighbor" if scope_root_semantics(cfg)["role"]=="person_root" else "root_neighbor"


def vault_path(root:Path,dump_id:str)->Path:
    safe=re.sub(r"[^A-Za-z0-9_.-]+","_",dump_id); return root/"30_working/entity-vaults"/safe/"wikidata.entity-vault.sqlite"

def load_registry(root:Path,cfg:dict[str,Any])->tuple[dict[str,Any],list[dict[str,Any]],Path]:
    src=cfg.get("root_source") or {}
    if src.get("kind")!="registry":raise RuntimeError("Seul root_source.kind=registry est supporté")
    p=root/src["path"]; obj=load_json(p,{}); recs=obj.get("records") if isinstance(obj,dict) else obj
    return obj if isinstance(obj,dict) else {},list(recs or []),p

def entity_row(c:sqlite3.Connection,wid:str)->dict[str,Any]:
    eid=encode_wid(wid)
    if eid is None:return {"wid":wid}
    r=c.execute("SELECT wid,kind,label_fr,label_en,label_mul,description_fr,description_en FROM entity WHERE id=?",(eid,)).fetchone(); return dict(r) if r else {"wid":wid}

def entity_rows(c:sqlite3.Connection,wids:Iterable[str],batch_size:int=900)->dict[str,dict[str,Any]]:
    ids=[]
    for wid in wids:
        eid=encode_wid(wid)
        if eid is not None:ids.append(eid)
    out={}
    for batch in chunks(ids,batch_size):
        qs=','.join('?'*len(batch))
        sql=f"SELECT wid,kind,label_fr,label_en,label_mul,description_fr,description_en FROM entity WHERE id IN ({qs})"
        for r in c.execute(sql,batch):out[r['wid']]=dict(r)
    return out

def years(c:sqlite3.Connection,eid:int)->dict[int,list[int]]:
    out=defaultdict(list)
    for r in c.execute("SELECT property_id,year FROM chronology WHERE subject_id=?",(eid,)):out[int(r["property_id"])].append(int(r["year"]))
    return out

def is_human(c:sqlite3.Connection,eid:int)->bool:
    q5=encode_wid("Q5"); return c.execute("SELECT 1 FROM entity_edge WHERE subject_id=? AND property_id=31 AND target_id=? LIMIT 1",(eid,q5)).fetchone() is not None

def resolve_seed(c:sqlite3.Connection,seed:dict[str,Any])->dict[str,Any]:
    norm=normalize_name(seed.get("display_name")); rows=c.execute("SELECT entity_id,lang,name_kind,value FROM name WHERE norm=? LIMIT 80",(norm,)).fetchall(); candidates=defaultdict(lambda:{"names":[]})
    for r in rows:candidates[int(r["entity_id"])]["names"].append(dict(r))
    chrono=seed.get("chronology") or {}; birth=chrono.get("birth_year"); death=chrono.get("death_year"); scored=[]
    for eid in candidates:
        score=70.0; reasons=["exact_normalized_name"]
        if seed.get("representation_kind")=="historical_person" and is_human(c,eid):score+=12; reasons.append("human")
        ys=years(c,eid)
        for pid,wanted,label in ((569,birth,"birth"),(570,death,"death")):
            if wanted is not None and ys.get(pid):
                delta=min(abs(y-int(wanted)) for y in ys[pid]); score+=max(0,12-min(delta,12))
                if delta<=2:reasons.append(label+"_year_close")
        e=c.execute("SELECT wid,label_fr,label_en FROM entity WHERE id=?",(eid,)).fetchone(); scored.append({"qid":e["wid"] if e else decode_wid(eid),"score":round(score,2),"label_fr":e["label_fr"] if e else None,"label_en":e["label_en"] if e else None,"reasons":reasons})
    scored.sort(key=lambda x:x["score"],reverse=True)
    if not scored:return {"qid":None,"confidence":"unresolved","candidates":[]}
    top=scored[0]; gap=top["score"]-(scored[1]["score"] if len(scored)>1 else 0); conf="high" if top["score"]>=82 and gap>=6 else ("medium" if top["score"]>=74 and gap>=3 else "ambiguous")
    return {"qid":top["qid"] if conf!="ambiguous" else None,"confidence":conf,"score":top["score"],"candidates":scored[:10]}

def pid_num(pid:str|int)->int:
    if isinstance(pid,int):return pid
    if not (pid.startswith("P") and pid[1:].isdigit()):raise ValueError(pid)
    return int(pid[1:])

def chunks(xs:list[Any],n:int)->Iterable[list[Any]]:
    for i in range(0,len(xs),n):yield xs[i:i+n]

def current_dump_id(global_meta:dict[str,str]|None=None,dump:Path|None=None,root:Path|None=None)->str:
    global_meta=global_meta or {}
    if global_meta.get("dump_sha1"):return "sha1-"+str(global_meta["dump_sha1"]).replace(":","_")
    if root is not None and dump is not None:return dump_descriptor(root,dump)["dump_id"]
    return str(global_meta.get("dump_file") or (dump.name if dump else "wikidata-unknown")).replace(":","_")

def ensure_vault(path:Path,dump_id:str)->sqlite3.Connection:
    c=open_db(path,False); c.executescript("""
    PRAGMA journal_mode=WAL; PRAGMA synchronous=NORMAL;
    CREATE TABLE IF NOT EXISTS meta(key TEXT PRIMARY KEY,value TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS entity_raw(wid TEXT PRIMARY KEY,raw_zlib BLOB NOT NULL,raw_bytes INTEGER NOT NULL,sha256 TEXT NOT NULL,captured_at TEXT NOT NULL);
    """); c.execute("INSERT INTO meta(key,value) VALUES('schema_version','encyklopedia-wikidata-entity-vault/v1') ON CONFLICT(key) DO NOTHING"); c.execute("INSERT INTO meta(key,value) VALUES('dump_id',?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",(dump_id,)); c.commit(); return c

def vault_fetch_raw(path:Path,dump_id:str,qids:Iterable[str])->dict[str,bytes]:
    if not path.exists():return {}
    c=open_db(path,True); out={}
    try:
        m=db_meta(c)
        if m.get('dump_id') and m.get('dump_id')!=dump_id:return {}
        ids=list(dict.fromkeys(qids))
        for batch in chunks(ids,500):
            qs=','.join('?'*len(batch))
            for r in c.execute(f'SELECT wid,raw_zlib FROM entity_raw WHERE wid IN ({qs})',batch):
                try:out[r['wid']]=zlib.decompress(r['raw_zlib'])
                except Exception:pass
    finally:c.close()
    return out

def raw_entity_id(raw:bytes)->str|None:
    m=ID_RE.search(raw[:768]); return m.group(1).decode("ascii") if m else None

def compression_index_path(root:Path,dump:Path)->Path:
    desc=dump_descriptor(root,dump); safe=re.sub(r"[^A-Za-z0-9_.-]+","_",desc["dump_id"])
    ext=".gzindex" if dump.name.lower().endswith(".gz") else ".bz2blocks.pkl"
    return root/"30_working/wikidata-fast"/safe/("compression"+ext)

def fast_access_dir(root:Path,dump:Path)->Path:
    desc=dump_descriptor(root,dump); safe=re.sub(r"[^A-Za-z0-9_.-]+","_",desc["dump_id"])
    return root/"30_working/wikidata-fast"/safe

def _global_locator_sidecars(root:Path,dump:Path)->dict[str,Path]:
    base=root/"30_working/wikidata"
    ext="compression.gzindex" if dump.name.lower().endswith('.gz') else "compression.bz2blocks.pkl"
    return {"locator":base/"qid-locator.bin","compression":base/ext,"manifest":base/"fast-sidecars.json"}

def fast_access_status(root:Path,dump:Path|None=None)->tuple[bool,dict[str,Any]]:
    try: dump=dump or find_dump(root)
    except Exception as e: return False,{"complete":False,"error":str(e)}
    d=fast_access_dir(root,dump); man=load_json(d/"manifest.json",{}) or {}; caps=fastio.backend_capabilities(dump,root)
    locator=d/"qid-locator.bin"
    compression=d/('compression.gzindex' if dump.name.lower().endswith('.gz') else 'compression.bz2blocks.pkl')
    source='fast-access'
    # v0.10 global builder can emit the locator/compression sidecars in the same dump pass.
    if not locator.exists():
        g=_global_locator_sidecars(root,dump)
        if g['locator'].exists():
            locator=g['locator']; compression=g['compression']; source='global-builder'
            gm=load_json(g['manifest'],{}) or {}
            man={**gm,**man}
    ok=bool(locator.exists())
    compression_ready=bool(dump.name.lower().endswith('.json') or compression.exists())
    info={**man,"complete":ok,"path":str(d),"locator_path":str(locator),"compression_index_path":str(compression),"locator_source":source,"runtime_backend":caps}
    info["random_access_ready"]=bool(ok and caps.get("random_access") and compression_ready)
    return ok,info

def iter_dump_raw(path:Path,*,root:Path|None=None,threads:int=0,with_offsets:bool=False)->Iterator[Any]:
    idx=compression_index_path(root,path) if root is not None else None
    yield from fastio.iter_dump_raw(path,threads=threads,index_path=idx if idx and idx.exists() else None,root=root,with_offsets=with_offsets)

def _qid_num(wid:str)->int|None:
    return int(wid[1:]) if isinstance(wid,str) and wid.startswith('Q') and wid[1:].isdigit() else None

def fast_fetch_raw(root:Path,dump:Path,qids:Iterable[str],threads:int=0)->dict[str,bytes]:
    ok,st=fast_access_status(root,dump)
    if not ok or not st.get('random_access_ready'): return {}
    locator=Path(st['locator_path']); idx=Path(st['compression_index_path'])
    wanted=[]
    with fastio.DenseQidLocatorReader(locator) as lr:
        for wid in qids:
            q=_qid_num(wid)
            if q is None: continue
            loc=lr.get(q)
            if loc: wanted.append((loc[0],loc[1],wid))
    wanted.sort()
    out={}
    with fastio.DumpStream(dump,threads=threads,index_path=idx if idx.exists() else None,root=root) as ds:
        if not ds.random_access:return {}
        for off,length,wid in wanted:
            ds.seek(off); raw=ds.read(length); s=fastio.normalize_dump_line(raw)
            if s is not None: out[wid]=s
    return out

def fast_reverse_edges(root:Path,dump:Path,targets:Iterable[str],properties:Iterable[str])->list[dict[str,Any]]:
    pids=[pid_num(x) for x in properties]; tids=[_qid_num(x) for x in targets]; tids=[x for x in tids if x is not None]
    if not tids or not pids:return []
    # Prefer the global discovery index: v0.10 no longer needs a duplicate P50/P170 sidecar DB.
    gdb=default_global_db(root)
    gok,_=global_index_status(root,gdb)
    if gok:
        c=open_db(gdb,True); out=[]
        try:
            for tb in chunks(tids,500):
                tq=','.join('?'*len(tb)); pq=','.join('?'*len(pids))
                sql=f"SELECT property_id,target_id,subject_id,statement_count,best_rank FROM entity_edge WHERE target_id IN ({tq}) AND property_id IN ({pq})"
                for r in c.execute(sql,[*tb,*pids]):out.append({'property_id':f"P{r['property_id']}",'target_wid':decode_wid(r['target_id']),'source_wid':decode_wid(r['subject_id']),'statement_count':r['statement_count'],'best_rank':r['best_rank']})
        finally:c.close()
        return out
    ok,st=fast_access_status(root,dump)
    if not ok:return []
    db=Path(st['path'])/'fast-index.sqlite'
    if not db.exists():return []
    c=sqlite3.connect(db); c.row_factory=sqlite3.Row; out=[]
    try:
        for tb in chunks(tids,500):
            tq=','.join('?'*len(tb)); pq=','.join('?'*len(pids))
            sql=f"SELECT property_id,target_id,source_id,statement_count,best_rank FROM reverse_edge WHERE target_id IN ({tq}) AND property_id IN ({pq})"
            for r in c.execute(sql,[*tb,*pids]):out.append({'property_id':f"P{r['property_id']}",'target_wid':f"Q{r['target_id']}",'source_wid':f"Q{r['source_id']}",'statement_count':r['statement_count'],'best_rank':r['best_rank']})
    finally:c.close()
    return out

def snak_entity_wid(snak:dict[str,Any]|None)->str|None:
    if not isinstance(snak,dict) or snak.get("snaktype")!="value":return None
    dv=snak.get("datavalue") or {}
    if dv.get("type")!="wikibase-entityid":return None
    v=dv.get("value") or {}; wid=v.get("id")
    if isinstance(wid,str) and re.fullmatch(r"[QPL]\d+",wid):return wid
    n=v.get("numeric-id"); et=v.get("entity-type"); pref={"item":"Q","property":"P","lexeme":"L"}.get(et)
    return f"{pref}{n}" if pref and isinstance(n,int) else None

def entity_edges_from_obj(obj:dict[str,Any],properties:set[str]|None=None)->list[dict[str,Any]]:
    out=[]; claims=obj.get("claims") or {}
    for pid,statements in claims.items():
        if properties is not None and pid not in properties:continue
        for st in statements or []:
            target=snak_entity_wid(st.get("mainsnak"))
            if target:out.append({"property_id":pid,"target_wid":target,"rank":st.get("rank"),"statement_id":st.get("id")})
    return out

def entity_label(obj:dict[str,Any],preferred=("fr","en","mul"))->tuple[str|None,str|None]:
    labels=obj.get("labels") or {}
    for lang in preferred:
        v=labels.get(lang)
        if isinstance(v,dict) and v.get("value"):return v["value"],lang
    for lang,v in labels.items():
        if isinstance(v,dict) and v.get("value"):return v["value"],lang
    return None,None

def entity_normalized_names(obj:dict[str,Any],languages:set[str]|None=None)->set[str]:
    out=set(); labels=obj.get("labels") or {}; aliases=obj.get("aliases") or {}
    for lang,v in labels.items():
        if languages and lang not in languages:continue
        if isinstance(v,dict) and v.get("value"):out.add(normalize_name(v["value"]))
    for lang,vals in aliases.items():
        if languages and lang not in languages:continue
        for v in vals or []:
            if isinstance(v,dict) and v.get("value"):out.add(normalize_name(v["value"]))
    return {x for x in out if x}

def entity_is_human_obj(obj:dict[str,Any])->bool:
    return any(e["property_id"]=="P31" and e["target_wid"]=="Q5" for e in entity_edges_from_obj(obj,{"P31"}))

def entity_years_obj(obj:dict[str,Any],pid:str)->list[int]:
    out=[]
    for st in (obj.get("claims") or {}).get(pid,[]) or []:
        dv=(st.get("mainsnak") or {}).get("datavalue") or {}
        if dv.get("type")!="time":continue
        t=(dv.get("value") or {}).get("time")
        if not isinstance(t,str):continue
        m=re.match(r"^([+-])(\d+)-",t)
        if m:out.append(int(m.group(2))*(-1 if m.group(1)=="-" else 1))
    return out

def score_raw_candidate(seed:dict[str,Any],obj:dict[str,Any])->dict[str,Any]:
    score=70.0; reasons=["exact_normalized_name"]
    if seed.get("representation_kind")=="historical_person" and entity_is_human_obj(obj):score+=12; reasons.append("human")
    chrono=seed.get("chronology") or {}
    for pid,wanted,label in (("P569",chrono.get("birth_year"),"birth"),("P570",chrono.get("death_year"),"death")):
        ys=entity_years_obj(obj,pid)
        if wanted is not None and ys:
            delta=min(abs(y-int(wanted)) for y in ys); score+=max(0,12-min(delta,12))
            if delta<=2:reasons.append(label+"_year_close")
    label,lang=entity_label(obj); return {"qid":obj.get("id"),"score":round(score,2),"label":label,"label_lang":lang,"reasons":reasons}

def declared_qid(cfg:dict[str,Any],seed:dict[str,Any])->str|None:
    for key in ("wikidata_qid","qid"):
        q=seed.get(key)
        if isinstance(q,str) and QID_RE.match(q):return q
    qmap=cfg.get("root_qids") or {}
    for key in (seed.get("key"),seed.get("display_name")):
        q=qmap.get(key) if key is not None else None
        if isinstance(q,str) and QID_RE.match(q):return q
    return None

def load_cached_qid_map(root:Path)->dict[str,Any]:
    obj=load_json(root/"30_working/registry/qid-map.local.json",{}) or {}; return obj if isinstance(obj,dict) else {}

def human_bytes(n:int|float)->str:
    x=float(n)
    for u in ["B","KiB","MiB","GiB","TiB"]:
        if x<1024 or u=="TiB":return f"{x:.2f} {u}"
        x/=1024
    return f"{x:.2f} TiB"

def free_gib(path:Path)->float:return shutil.disk_usage(path).free/1024**3

def atomic_write_text(path:Path,text:str)->None:
    path.parent.mkdir(parents=True,exist_ok=True); tmp=path.with_suffix(path.suffix+".tmp"); tmp.write_text(text,encoding="utf-8"); os.replace(tmp,path)
