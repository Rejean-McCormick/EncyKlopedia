"""Real byte-offset, crash-recovery, ZIP and provenance tests for v21.

Entirely synthetic Wikimedia XML; requires neither user's 110 GiB nor network.
"""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
import zipfile

HERE = Path(__file__).resolve().parents[1] / 'tools' / 'wiki' / 'atlas'
sys.path.insert(0, str(HERE))
import index_xml_v21 as idx
import extraire_lots_xml_v21 as export


def page(pid, title=None, ns=0, redirect=False, text='Synthetic educational research'):
    title=title or f'Page {pid}'
    redir='<redirect title="Target" />' if redirect else ''
    # HTML & and XML markup kept safely escaped in the source.
    return (f'  <page>\n    <title>{title}</title>\n    <ns>{ns}</ns>\n    <id>{pid}</id>\n    {redir}\n'
            f'    <revision>\n      <id>{pid+1000}</id>\n      <text xml:space="preserve">{text}</text>\n'
            '    </revision>\n  </page>\n').encode('utf-8')


def write_dump(path, rows):
    path.write_bytes(b'<?xml version="1.0" encoding="utf-8"?>\n<mediawiki>\n' +
                     b''.join(rows) + b'</mediawiki>\n')


def write_atlas(path, ids):
    import io
    path.mkdir()
    files={}
    f=io.StringIO(newline='')
    w=csv.DictWriter(f,fieldnames=['page_id','title','revision_id','qid','rank','redirect'])
    w.writeheader()
    for pid in ids:w.writerow({'page_id':pid,'title':f'Page {pid}',
                               'revision_id':str(pid+1000),'qid':'','rank':1,'redirect':False})
    files['pages.csv']=f.getvalue().encode('utf-8')
    files['ancrages_kristal_stables.json']=b'{}\n'
    files['liens_internes.csv']=b'source_page_id,target_page_id\n'
    files['pages_prioritaires_a_selectionner.csv']=b'selected,page_id\n'
    meta={'branch':'unesco-mt1-10','files':{}}
    for name,content in files.items():
        (path/name).write_bytes(content)
        meta['files'][name]={'sha256':hashlib.sha256(content).hexdigest(),'bytes':len(content)}
    (path/'manifest.json').write_text(json.dumps(meta))


def write_selection(path,ids):
    with path.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=['selected','page_id','title','revision_id','qid'])
        w.writeheader()
        for pid in ids:w.writerow({'selected':1,'page_id':pid,'title':f'Page {pid}',
                                  'revision_id':str(pid+1000),'qid':''})


class TestDirectXML(unittest.TestCase):
    def setUp(self):
        self.t=tempfile.TemporaryDirectory();self.addCleanup(self.t.cleanup)
        self.root=Path(self.t.name)
        self.xml=self.root/'wiki.xml';self.db=self.root/'v21.sqlite'

    def test_resume_and_exact_raw_offsets_across_boundaries(self):
        ids=[10,11,12,13,14]
        write_dump(self.xml,[page(ids[0],text='a'*1024),page(ids[1]),page(ids[2],ns=2),
                             page(ids[3],redirect=True),page(ids[4],text='x &amp; y')])
        first=idx.build(self.xml,self.db,batch_pages=2,progress_pages=2,max_pages=3,chunk_bytes=31)
        self.assertEqual(first['status'],'V21_INDEX_PARTIEL_REPRENABLE')
        self.assertEqual(idx.audit(self.xml,self.db)['pages_indexed'],3)
        second=idx.build(self.xml,self.db,batch_pages=2,progress_pages=2,chunk_bytes=19)
        self.assertEqual(second['pages_indexed'],5)
        self.assertTrue(idx.audit(self.xml,self.db,require_complete=True)['complete'])
        with idx.ro_connect(self.db) as c,self.xml.open('rb') as f:
            for pid in ids:
                row=c.execute('''SELECT page_id,byte_offset,byte_length,namespace,title,revision_id,is_redirect
                                  FROM pages WHERE page_id=?''',(pid,)).fetchone()
                self.assertIsNotNone(row)
                raw=idx.read_one(f,row,pid)
                self.assertIn(b'<page>',raw)
        done=idx.build(self.xml,self.db)
        self.assertEqual(done['status'],'V21_INDEX_DEJA_COMPLET')

    def test_xml_identity_and_non_mutation(self):
        write_dump(self.xml,[page(123),page(456)])
        idx.build(self.xml,self.db,batch_pages=1)
        first=self.xml.stat().st_size
        with self.assertRaisesRegex(ValueError,'source|Source|XML|signature'):
            # Appending anything changes source signature; index refuses reuse.
            with self.xml.open('ab') as f:f.write(b'--altered--')
            idx.audit(self.xml,self.db)
        self.assertGreater(self.xml.stat().st_size,first)

    def test_reject_non_xml_and_incomplete(self):
        self.xml.write_bytes(b'not a dump')
        with self.assertRaises(ValueError):idx.build(self.xml,self.db)
        self.assertFalse(self.db.exists())

    def test_zip_provenance_and_replay(self):
        ids=[42,43]
        write_dump(self.xml,[page(42),page(43,text='Research &amp; rights')])
        idx.build(self.xml,self.db,batch_pages=1)
        atlas=self.root/'atlas';write_atlas(atlas,ids)
        selection=self.root/'new_lot.csv';write_selection(selection,ids)
        output=self.root/'new_lot.zip'
        a=export.parse(['build','--xml',str(self.xml),'--db',str(self.db),
             '--atlas',str(atlas),'--selection',str(selection),
             '--output',str(output),'--future-lot'])
        r=export.build(a)
        self.assertEqual(r['texts_extracted'],2)
        self.assertEqual(export.build(a)['operation'],'REPRISE_IDENTIQUE')
        with zipfile.ZipFile(output) as z:
            m=json.loads(z.read('LOT_MANIFEST.json'))
            self.assertEqual([x['page_id'] for x in m['items']],ids)
            self.assertEqual(z.read('articles/page-43.wikitext.txt'),b'Research & rights')
            h=json.loads(z.read('MEDIATHEQUE_HANDOFF_CANDIDAT.json'))
            self.assertEqual(h['status'],'CANDIDATE_ONLY_NOT_IMPORTED_NOT_ATTESTED')
        with output.open('ab') as f:f.write(b'ALTERED')
        with self.assertRaisesRegex(ValueError,'Empreinte'):export.verify(output)

    def test_reject_redirect_and_missing(self):
        write_dump(self.xml,[page(42,redirect=True),page(43)])
        idx.build(self.xml,self.db)
        with idx.ro_connect(self.db) as c,self.xml.open('rb') as f:
            row=c.execute('SELECT page_id,byte_offset,byte_length,namespace,title,revision_id,is_redirect FROM pages WHERE page_id=42').fetchone()
            raw=idx.read_one(f,row,42)
            with self.assertRaisesRegex(ValueError,'Redirection'):export.read_wikitext(raw,42)
            self.assertIsNone(c.execute('SELECT * FROM pages WHERE page_id=99').fetchone())

if __name__=='__main__':unittest.main()
