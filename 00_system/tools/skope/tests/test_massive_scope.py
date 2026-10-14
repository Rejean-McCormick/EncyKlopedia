"""Bounded preview + disk-backed extensive traversal. No source DB writes."""
import io
import json
import sqlite3
import tempfile
import time
import unittest
from pathlib import Path
from zipfile import ZipFile
from skope import massive
from skope.scope import validate_recipe, explore
from skope.export import bundle
from skope.db import connect,_eid
from test_integration import make_index,REC

class MassiveScopeTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        folder=Path(self.tmp.name)/'30_working/wikidata';folder.mkdir(parents=True)
        self.idx=folder/'wikidata.compact.sqlite';make_index(self.idx)
        with sqlite3.connect(self.idx) as c:
            for n in range(25):
                q=f'Q{1234000+n}'
                c.execute('INSERT INTO entity VALUES (?,?,?,?,?,?,?,?)',(_eid(q),q,'item',q,q,None,None,None))
                tgt='Q900000000' if n==0 else f'Q{1234000+n-1}'
                c.execute('INSERT INTO entity_edge VALUES (?,?,?,?,?)',(_eid(q),171,_eid(tgt),1,1))
        self.r={**REC,'root':'Q900000000','direction':'in','allowed_properties':['P171'],
                'default_depth':8,'max_entities':0,'convergence':{'threshold_percent':14.6,'min_support':8,'extra_depth':0,'include':[]}}
    def wait(self,job):
        for i in range(150):
            x=massive.status(self.idx,job['job'])
            if x['state'] not in ('queued','running'):return x
            time.sleep(.025)
        self.fail('La tâche de test n’a pas terminé')
    def test_unlimited_preview_export_are_not_full_corpus(self):
        with connect(self.idx) as c:
            p=explore(c,self.r)
            self.assertTrue(p['preview_only']);self.assertEqual(p['preview_budget'],10000)
            z=bundle(c,self.r)
        with ZipFile(io.BytesIO(z)) as archive:
            self.assertIn('review/large-scope.recipe.json',archive.namelist())
            self.assertFalse(any(x.startswith('staged/') for x in archive.namelist()))
            m=json.loads(archive.read('manifest.json'))
            self.assertIsNone(m['selected_entities'])
            self.assertEqual(m['status'],'plan_requires_disk_scan')
    def test_disk_crawl_selects_taxonomic_children_without_modifying_index(self):
        original=self.idx.read_bytes()
        job=massive.start(self.idx,self.r)
        result=self.wait(job)
        self.assertEqual(result['state'],'completed',result['message'])
        self.assertEqual(result['selected'],9)  # root and eight levels of P171
        self.assertTrue(result['scope_complete'])
        path=self.idx.parent.parent/'skope-large-scopes'/job['job']/'selected-qids.jsonl'
        rows=[json.loads(x)['wikidata_qid'] for x in path.read_text().splitlines()]
        self.assertEqual(len(rows),9)
        self.assertIn('Q1234007',rows)
        self.assertNotIn('Q1234008',rows)
        self.assertEqual(self.idx.read_bytes(),original)
    def test_budget_causes_explicit_partial_status(self):
        r={**self.r,'max_entities':4}
        job=massive.start(self.idx,r)
        final=self.wait(job)
        self.assertEqual(final['state'],'limit_reached',final['message'])
        self.assertFalse(final['scope_complete'])
        self.assertEqual(final['selected'],4)
        follow=massive.start(self.idx,{**r,'max_entities':0},resume=job['job'])
        final2=self.wait(follow)
        self.assertEqual(final2['state'],'completed',final2['message'])
        self.assertEqual(final2['selected'],9)
    def test_invalid_job_and_unbounded_too_broad_guard(self):
        with self.assertRaises(ValueError):massive.status(self.idx,'../test')
        with self.assertRaises(ValueError):massive.start(self.idx,{**self.r,'direction':'both'})
        with self.assertRaises(ValueError):massive.start(self.idx,{**self.r,'allowed_properties':[]})

if __name__=='__main__':unittest.main()
