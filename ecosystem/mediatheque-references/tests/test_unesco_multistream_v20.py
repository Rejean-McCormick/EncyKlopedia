"""V20 offline tests: real v19 atlas fixture, synthetic Wikimedia multistream.

The test never accesses D:, downloads anything, or modifies a canonical repo.
"""
from __future__ import annotations
import bz2
import csv
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest
import xml.sax.saxutils as xml_escape
import zipfile

ATLAS=Path(__file__).resolve().parents[1]/'tools/wiki/atlas'
sys.path.insert(0,str(ATLAS))
import atlas_wikipedia as M
import extraction_multistream_v20 as X
import extraire_lots_v20 as V


def fragments(pages):
    return b''.join(
        ('<page><title>'+xml_escape.escape(title)+'</title><ns>0</ns><id>'+str(pid)+
         '</id><revision><id>'+str(rev)+'</id><text xml:space="preserve">'+
         xml_escape.escape('Article about '+title+'\n== References ==\nSection body')+
         '</text></revision></page>') .encode('utf8')
        for pid,title,rev in pages)


def make_xml(path,groups):
    c=0;idx=[]
    with path.open('wb') as f:
        for group in groups:
            raw=b'<mediawiki>'+fragments(group)+b'</mediawiki>'
            f.write(bz2.compress(raw))
            for pid,title,_ in group:idx.append(f'{c}:{pid}:{title}\n')
            c=f.tell()
    return ''.join(idx).encode('utf-8')


class MultiStreamTest(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.xml=self.root/'enwiki-latest-pages-articles-multistream.xml.bz2'
        self.db=self.root/'offsets.sqlite'
        self.groups=[[(1,'Article One',101),(2,'Article Two',102)],
                     [(4,'Article Four',104)],[(7,'Article Seven',107)]]
        self.index_text=make_xml(self.xml,self.groups)

    def test_stream_offsets_and_resume(self):
        a=X.ensure_offsets(self.xml,self.db,{1,4,7},max_streams=1,progress_every=1)
        self.assertEqual(a['status'],'INDEX_PAUSED')
        self.assertEqual(set(a['offsets']),{1})
        first=a['checkpoint']
        a=X.ensure_offsets(self.xml,self.db,{1,4,7},max_streams=1)
        self.assertEqual(a['status'],'INDEX_PAUSED')
        self.assertGreater(a['checkpoint'],first)
        a=X.ensure_offsets(self.xml,self.db,{1,4,7},progress_every=1)
        self.assertEqual(a['status'],'OFFSETS_READY')
        self.assertTrue(a['complete'])
        self.assertEqual(len(a['offsets']),3)
        self.assertEqual(a['page_ids_indexed'],4)
        self.assertEqual(X.audit_index(self.xml,self.db)['streams'],3)
        again=X.ensure_offsets(self.xml,self.db,{1,4,7})
        self.assertEqual(again['checkpoint'],a['checkpoint'])

    def test_missing_id_returns_complete_not_fabricated(self):
        a=X.ensure_offsets(self.xml,self.db,{999},progress_every=5)
        self.assertEqual(a['status'],'PAGES_ABSENTES_DU_DUMP')
        self.assertEqual(a['missing'],[999])
        self.assertTrue(a['complete'])
        again=X.ensure_offsets(self.xml,self.db,{999})
        self.assertEqual(again['status'],'PAGES_ABSENTES_DU_DUMP')

    def test_changed_source_refused(self):
        X.ensure_offsets(self.xml,self.db,{1},max_streams=1)
        with self.xml.open('ab') as f:f.write(b'junk')
        with self.assertRaisesRegex(ValueError,'modifiée'):
            X.ensure_offsets(self.xml,self.db,{7})

    def test_existing_foreign_sqlite_refused(self):
        with sqlite3.connect(self.db) as c:c.execute('CREATE TABLE unrelated(a)')
        with self.assertRaisesRegex(ValueError,'non reconnu'):
            X.ensure_offsets(self.xml,self.db,{1})

    def test_corrupt_member_keeps_checkpoint(self):
        first=bz2.compress(b'<mediawiki>'+fragments(self.groups[0])+b'</mediawiki>')
        self.xml.write_bytes(first+b'NOT_BZ2_STREAM')
        with self.assertRaisesRegex(ValueError,'[Ee]n-tête'):
            X.ensure_offsets(self.xml,self.db,{7})
        with sqlite3.connect(self.db) as c:
            v={k:json.loads(j) for k,j in c.execute('SELECT name,value FROM v20_meta')}
            self.assertEqual(v['checkpoint'],len(first))
            self.assertEqual(c.execute('SELECT COUNT(*) FROM streams').fetchone()[0],1)

    def test_page_revision_id_not_selected(self):
        raw=b'<page><title>X</title><ns>0</ns><id>9</id><revision><id>888</id></revision></page>'
        self.assertEqual(X.page_ids(raw),[9])

    def test_multistream_offsets_compatible_with_v19(self):
        a=X.ensure_offsets(self.xml,self.db,{4,7})
        idx=self.root/'sparse.txt'
        idx.write_text(''.join(f'{a["offsets"][p]}:{p}:Title\n' for p in (4,7)))
        self.assertEqual(M.index_offsets(idx,{4,7}),a['offsets'])
        texts,missing=M.from_multistream(self.xml,idx,{4,7},{4:{'revision_id':'104'},7:{'revision_id':'107'}})
        self.assertEqual(missing,{})
        self.assertIn(b'Article about',texts[4]['text'])


class PortableLotPipelineTest(unittest.TestCase):
    """Portable real-v19-contract fixture, works on Windows without user data."""
    def setUp(self):
        from test_unesco_atlas_v19 import fixture
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        db,inv,cache=fixture(self.root)
        self.atlas=self.root/'atlas'
        self.assertEqual(M.main(['build','--db',str(db),'--inventory',str(inv),
                                 '--out',str(self.atlas),'--max-pages','10',
                                 '--max-links','10','--depth','1']),0)
        self.selection=self.root/'selection.csv'
        with (self.atlas/'pages.csv').open(encoding='utf-8-sig',newline='') as f:
            rows={int(r['page_id']):r for r in csv.DictReader(f)}
        with self.selection.open('w',encoding='utf-8-sig',newline='') as f:
            writer=csv.DictWriter(f,fieldnames=['selected','page_id','title','revision_id','qid'])
            writer.writeheader()
            for pid in (1,2):
                r=rows[pid]
                writer.writerow({k:('1' if k=='selected' else r[k]) for k in writer.fieldnames})
        self.xml=self.root/'enwiki-latest-pages-articles-multistream.xml.bz2'
        self.index_text=make_xml(self.xml,[[(1,'Right to education','102')],
                                           [(2,'Educational policy','103')]])
        self.out=self.root/'portable_LOT_003.zip'
        self.args=['--atlas',str(self.atlas),'--selection',str(self.selection),
                   '--xml',str(self.xml),'--sidecar',str(self.root/'offsets.sqlite'),
                   '--output',str(self.out),'--cache',str(self.root/'nonexistent'),
                   '--future-lot']

    def test_extract_generic_lot_and_audit(self):
        self.assertEqual(V.main(['preflight']+self.args),0)
        self.assertEqual(V.main(['build']+self.args),0)
        self.assertEqual(V.main(['audit','--output',str(self.out)]),0)
        with zipfile.ZipFile(self.out) as z:
            j=json.loads(z.read('LOT_MANIFEST.json'))
            self.assertEqual(j['selected_pages'],2)
            self.assertEqual(j['texts_available'],2)
        self.assertEqual(V.main(['build']+self.args),0)

    def test_bounded_resume_without_final_zip(self):
        self.assertEqual(V.main(['build']+self.args+['--max-streams','1']),3)
        self.assertFalse(self.out.exists())
        self.assertEqual(V.main(['build']+self.args),0)
        self.assertTrue(self.out.exists())

    def test_official_index_without_sqlite(self):
        idx=self.xml.with_name(self.xml.name.removesuffix('.xml.bz2')+'-index.txt.bz2')
        idx.write_bytes(bz2.compress(self.index_text))
        self.assertEqual(V.main(['build']+self.args),0)
        self.assertFalse((self.root/'offsets.sqlite').exists())

    def test_tamper_zip(self):
        self.assertEqual(V.main(['build']+self.args),0)
        with self.out.open('ab') as f:f.write(b'TAMPER')
        self.assertEqual(V.main(['audit','--output',str(self.out)]),2)

    def test_no_generic_flag_refuses_other_lots(self):
        self.assertEqual(V.main(['build']+[x for x in self.args if x!='--future-lot']),2)
        self.assertFalse(self.out.exists())


if __name__=='__main__':unittest.main()
