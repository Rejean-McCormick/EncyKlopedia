"""Regression on read-only Skope index and external-reader handoff (no network)."""
from __future__ import annotations
import gzip
import hashlib
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from wikidata_reader_worker import run as worker_run
from wikidata_full import extract
from factory_core import Factory
from reader_runtime import _python_in, write_reader_request, ReaderSetupError
from vendor.wikidata_skope.fastio import ENTRY_STRUCT, ENTRY_SIZE


def fixture_source(root, bz2=False):
    folder=root/'10_sources/wikidata/dumps/current';folder.mkdir(parents=True)
    dump=folder/('wikidata-all.json.bz2' if bz2 else 'wikidata-all.json')
    data1=json.dumps({'id':'Q1','claims':{'P31':[{'id':'Q1$1','mainsnak':{'snaktype':'value','datavalue':{'value':{'id':'Q9'}}},'references':[]}]}},separators=(',',':')).encode()+b'\n'
    data2=json.dumps({'id':'Q2','claims':{'P31':[]}},separators=(',',':')).encode()+b'\n'
    blob=data1+data2
    if bz2:
        import bz2
        dump.write_bytes(bz2.compress(blob))
    else:dump.write_bytes(blob)
    weak=hashlib.sha256(f'{dump.name}|{dump.stat().st_size}'.encode()).hexdigest()[:24]
    fast=root/'30_working'/'wikidata-fast'/('file-'+weak);fast.mkdir(parents=True)
    locator=bytearray(ENTRY_SIZE*3)
    ENTRY_STRUCT.pack_into(locator,ENTRY_SIZE,0,len(data1),1)
    ENTRY_STRUCT.pack_into(locator,ENTRY_SIZE*2,len(data1),len(data2),1)
    (fast/'qid-locator.bin').write_bytes(locator)
    (fast/'compression.bz2blocks.pkl').write_bytes(b'not-real-bz2-index')
    compact=root/'30_working'/'wikidata'/'wikidata.compact.sqlite';compact.parent.mkdir(parents=True)
    compact.write_bytes(b'index placeholder')
    return dump, compact, fast

class IndexedReaderV16(unittest.TestCase):
    def test_plain_indexed_worker_respects_requested_qids(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t);source,idx,_=fixture_source(p)
            req=write_reader_request(['Q2','Q1','Q2'],p/'request.json')
            out=p/'result.jsonl.gz'
            meta=worker_run(source,idx,req,out)
            self.assertEqual(meta['requested'],2)
            self.assertEqual(meta['found'],2)
            self.assertTrue(meta['scan_entire_dump'] is False)
            ids=[json.loads(x)['id'] for x in gzip.open(out,'rt',encoding='utf-8')]
            self.assertEqual(ids,['Q1','Q2'])
            self.assertTrue(out.with_suffix(out.suffix+'.reader.json').is_file())
    def test_corrupt_locator_qid_never_accepted(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t);source,idx,fast=fixture_source(p)
            locator=bytearray((fast/'qid-locator.bin').read_bytes())
            # Q1 locator incorrectly points to Q2; must not yield Q2 under Q1.
            off,len2,_=ENTRY_STRUCT.unpack_from(locator,ENTRY_SIZE*2)
            ENTRY_STRUCT.pack_into(locator,ENTRY_SIZE,off,len2,1)
            (fast/'qid-locator.bin').write_bytes(locator)
            req=write_reader_request(['Q1'],p/'request.json')
            meta=worker_run(source,idx,req,p/'result.jsonl.gz')
            self.assertEqual(meta['found'],0)
            self.assertEqual(meta['rejected'][0]['qid'],'Q1')
    def test_factory_handoff_provenance_no_canon(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t)/'EncyK'
            source,idx,_=fixture_source(root,bz2=True)
            f=Factory({'index':str(idx),'full_source':str(source),'full_enabled':True})
            f.output=Path(t)/'run';f.output.mkdir()
            f.log_file=f.output/'fabrique.log'
            mapping={'concept1':{'status':'SINGLE_P3916_CANDIDATE','wikidata_qid_candidate':'Q1'}}
            def simulated_worker(cmd,cwd=None):
                self.assertIn('wikidata_reader_worker.py',str(cmd[1]))
                out=Path(cmd[cmd.index('--out')+1])
                out.parent.mkdir(parents=True,exist_ok=True)
                raw={'id':'Q1','claims':{'P31':[{'id':'Q1$1','rank':'normal',
                    'mainsnak':{'snaktype':'value','datavalue':{'value':{'id':'Q9'}}},
                    'references':[{'snaks':{'P854':[]}}]}]}}
                with gzip.open(out,'wt',encoding='utf-8') as w:w.write(json.dumps(raw)+'\n')
                out.with_suffix(out.suffix+'.reader.json').write_text(json.dumps({
                    'found':1,'rejected':[],'source_dump':str(source),'scan_entire_dump':False}))
            with patch('factory_core.ensure_private_reader',return_value=Path(sys.executable)), \
                 patch.object(f,'run_cmd',side_effect=simulated_worker):
                summary=f.full_wikidata(mapping)
            self.assertEqual(f.stats['full_entities'],1)
            self.assertEqual(f.stats['wikidata_statements'],1)
            self.assertIn('concept1',summary)
            result=json.loads((f.output/'02_WIKIDATA/FAITS_COMPLETS/facts.jsonl').read_text())
            self.assertEqual(result['source_path'],str(source))
            self.assertNotEqual(result['source_path'],f.reader_manifest.get('path'))
            self.assertEqual(f.full_manifest['source_kind'],'indexed_dump_via_private_reader')
            self.assertTrue((f.output/'02_WIKIDATA/FAITS_COMPLETS/reader_runtime.json').exists())
    def test_request_rejects_blank(self):
        with tempfile.TemporaryDirectory() as t:
            with self.assertRaises(ReaderSetupError):write_reader_request([],Path(t)/'ids.json')

if __name__=='__main__':unittest.main()
