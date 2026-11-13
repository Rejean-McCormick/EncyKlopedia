#!/usr/bin/env python3
"""Extraction XML ciblée sans offsets v21 : parcours séquentiel et cache révisionné.

Une lecture du dump pour les pages candidates déjà connues de v28.
Aucun changement du dump, de l'index ou des preuves figées. Un extrait n'est
qualifié 'vérifié' que si la signature XML, la révision et le SHA concordent.
"""
from __future__ import annotations
import argparse
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import sqlite3
from contextlib import closing
import xml.etree.ElementTree as ET

DEFAULT_XML=Path(r'D:\EncyKlopedia\30_working\wikipedia_en_uncompressed\enwiki-latest-pages-articles-multistream.xml')
DEFAULT_STAGE=Path(r'D:\EncyKlopedia\30_working\decouverte_articles_relies_v28\DECOUVERTE_ARTICLES_RELIES_V28.sqlite')
DEFAULT_SOURCE=Path(r'D:\EncyKlopedia\80_search_indexes\mediatheque-references\wikipedia_en.sqlite')
DEFAULT_CACHE=Path(r'D:\EncyKlopedia\30_working\preuves_xml_cibles_v31\PREUVES_XML_CIBLES_V31.sqlite')
VERSION='encyklopedia.xml-targeted-evidence.v31/1'

def now():return datetime.now(timezone.utc).isoformat(timespec='seconds')

def loc(tag):return tag.rsplit('}',1)[-1]

def direct(e,name):return next((x for x in e if loc(x.tag)==name),None)

def content(e,name):
    el=direct(e,name)
    return el.text if el is not None and el.text is not None else ''

def read_targets(stage):
    if not stage.is_file():raise ValueError('Base découverte v28 absente : '+str(stage))
    with closing(sqlite3.connect(stage.resolve().as_uri()+'?mode=ro',uri=True)) as con:
        row=con.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='candidates'").fetchone()
        if not row:raise ValueError('Table candidates v28 absente')
        ids={int(r[0]) for r in con.execute('SELECT DISTINCT page_id FROM candidates')}
    if not ids:raise ValueError('Aucun candidat à enrichir')
    return ids

def xml_sig(xml):
    # Réutilise exactement le contrat v27 quand disponible.
    import production_kristals_v27 as v27
    return json.dumps(v27.xml_signature(xml),ensure_ascii=False,sort_keys=True)

def prepare_cache(path,sig):
    path.parent.mkdir(parents=True,exist_ok=True)
    db=sqlite3.connect(path,timeout=120)
    db.execute('PRAGMA busy_timeout=120000')
    db.execute('PRAGMA journal_mode=WAL')
    db.executescript('''CREATE TABLE IF NOT EXISTS meta(key TEXT PRIMARY KEY,value TEXT NOT NULL);
       CREATE TABLE IF NOT EXISTS prepared_pages(
          page_id INTEGER PRIMARY KEY,revision_id INTEGER NOT NULL,title TEXT NOT NULL,
          wikitext TEXT NOT NULL,sha256_full TEXT NOT NULL,sha256_stored TEXT NOT NULL,
          complete_text INTEGER NOT NULL,stored_chars INTEGER NOT NULL,extracted_utc TEXT NOT NULL);
       CREATE INDEX IF NOT EXISTS idx_prepared_revision ON prepared_pages(revision_id);''')
    for k,v in (('schema',VERSION),('xml_signature',sig)):
        old=db.execute('SELECT value FROM meta WHERE key=?',(k,)).fetchone()
        if old and old[0]!=v:
            db.close();raise ValueError('Le dump XML a changé : utiliser un cache V31 distinct')
        db.execute('INSERT OR IGNORE INTO meta(key,value) VALUES(?,?)',(k,v))
    db.commit();return db

def run(xml,stage,cache,*,text_chars=100000,max_targets=2000000):
    if not xml.is_file():raise ValueError('Dump XML absent : '+str(xml))
    if text_chars<500 or text_chars>2000000:raise ValueError('Limite texte hors bornes')
    targets=read_targets(stage)
    if len(targets)>max_targets:raise ValueError('Trop de pages cibles dans le lot de collecte')
    sig=xml_sig(xml)
    db=prepare_cache(cache,sig)
    found=skipped=0
    try:
        existing={int(r[0]) for r in db.execute('SELECT page_id FROM prepared_pages')}
        remain=targets-existing
        if not remain:
            return {'status':'PREUVES_V31_OK','known_targets':len(targets),'new_excerpts':0,
                    'cached':len(existing & targets),'missing':0,'cache':str(cache)}
        with xml.open('rb') as f:
            iterator=ET.iterparse(f,events=('start','end'))
            _,root=next(iterator)
            for event,e in iterator:
                if event!='end' or loc(e.tag)!='page':continue
                try:
                    pid=int(content(e,'id'))
                    if pid not in remain:continue
                    name=content(e,'title')
                    rev=direct(e,'revision')
                    if rev is None:skipped+=1;continue
                    revision=int(content(rev,'id'))
                    text=content(rev,'text')
                    full_sha=hashlib.sha256(text.encode('utf-8')).hexdigest()
                    stored=text[:text_chars]
                    db.execute('INSERT OR REPLACE INTO prepared_pages VALUES(?,?,?,?,?,?,?,?,?)',
                        (pid,revision,name,stored,full_sha,hashlib.sha256(stored.encode('utf-8')).hexdigest(),
                         int(len(stored)==len(text)),len(stored),now()))
                    found+=1;remain.remove(pid)
                    if found%100==0:db.commit()
                except (ValueError,TypeError):
                    skipped+=1
                finally:
                    e.clear();root.clear()
                if not remain:break
        db.commit()
        return {'status':'PREUVES_V31_OK','known_targets':len(targets),
                'new_excerpts':found,'cached':len(existing & targets),'missing':len(remain),
                'invalid_pages':skipped,'cache':str(cache),'xml_bound_to_signature':True,
                'note':'Le texte provient du XML ; la correspondance de revision avec wiki_pages est vérifiée à la consommation.'}
    finally:db.close()

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--xml',type=Path,default=DEFAULT_XML)
    p.add_argument('--stage',type=Path,default=DEFAULT_STAGE)
    p.add_argument('--cache',type=Path,default=DEFAULT_CACHE)
    p.add_argument('--text-chars',type=int,default=100000)
    a=p.parse_args(argv)
    try:print(json.dumps(run(a.xml,a.stage,a.cache,text_chars=a.text_chars),ensure_ascii=False,indent=2));return 0
    except (OSError,ValueError,sqlite3.Error,ET.ParseError) as ex:
        print(json.dumps({'status':'PREUVES_V31_REFUS','error':str(ex)},ensure_ascii=False));return 2

if __name__=='__main__':raise SystemExit(main())
