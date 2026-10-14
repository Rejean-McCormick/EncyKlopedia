"""Geographic scope is explicit, counted, review-only and index-read-only."""
import io
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile
from skope.db import _eid, connect
from skope.geography import validate_geography
from skope.scope import explore,validate_recipe
from skope.export import bundle
from test_integration import REC,make_index

GEO={'focus':'north-america','priority':'canada','mode':'annotate',
     'region_qid':'Q49','priority_qid':'Q16','evidence_properties':['P9714','P183','P2341']}

class GeographicScopeTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.path=Path(self.tmp.name)/'index.sqlite';make_index(self.path)
        with sqlite3.connect(self.path) as c:
            c.executemany('INSERT INTO entity_edge VALUES (?,?,?,?,?)',[
                (_eid('Q900000001'),9714,_eid('Q16'),1,1),
                (_eid('Q900000002'),9714,_eid('Q30'),1,1),
                (_eid('Q900000003'),183,_eid('Q1904'),1,1),
                (_eid('Q1904'),131,_eid('Q16'),1,1),
                (_eid('Q900000004'),2341,_eid('Q142'),1,1),
            ])
        self.rec={**REC,'geography':GEO}
    def test_validation_and_no_geographic_inference_of_absence(self):
        self.assertEqual(validate_recipe(self.rec)['geography']['priority_qid'],'Q16')
        for bad in [{**GEO,'mode':'bad'}, {**GEO,'region_qid':'Q17'},
                    {**GEO,'evidence_properties':['P17']}, {**GEO,'unknown_flag':True}]:
            with self.assertRaises(ValueError):validate_geography(bad)
        with connect(self.path) as c:
            report=explore(c,self.rec)
        cov=report['geography_coverage']
        self.assertEqual(report['counts']['entities'],5)
        for key,value in [('priority_documented',2),('region_other_documented',1),
                          ('other_area_only',1),('no_geographic_evidence',1)]:
            self.assertEqual(cov[key],value)
        self.assertIn('undocumented ≠ absent',cov['warnings'][0])
        self.assertEqual(report['nodes'][0]['geography']['category'],'priority')
        self.assertEqual(report['nodes'][1]['geography']['category'],'priority')
    def test_custom_geography_can_define_another_region_and_priority(self):
        custom={**GEO,'focus':'custom','priority':'custom','region_qid':'Q30','priority_qid':'Q1904'}
        with connect(self.path) as c:
            report=explore(c,{**self.rec,'geography':custom})
        self.assertEqual(report['recipe']['geography']['region_qid'],'Q30')
        self.assertEqual(report['geography_coverage']['priority_documented'],1)
        self.assertEqual(report['geography_coverage']['region_other_documented'],1)
    def test_strict_documentation_is_not_global_claim(self):
        cfg={**self.rec,'geography':{**GEO,'mode':'documented_only'}}
        with connect(self.path) as c:
            report=explore(c,cfg)
        self.assertEqual(report['counts']['entities'],4)
        self.assertEqual(report['geography_coverage']['pre_filter_entities'],5)
        self.assertIn(REC['root'],{n['id'] for n in report['nodes']})
        self.assertNotIn('Q900000004',{n['id'] for n in report['nodes']})
        self.assertEqual(set(report['recipe']['geography']['evidence_properties']),{'P9714','P183','P2341'})
    def test_bundle_carries_intent_and_measured_coverage(self):
        original=self.path.read_bytes()
        with connect(self.path) as c:
            z=bundle(c,self.rec)
        with ZipFile(io.BytesIO(z)) as archive:
            manifest=json.loads(archive.read('manifest.json'))
            self.assertEqual(manifest['scope_key'],'skope-q900000000-na-ca')
            self.assertEqual(manifest['geography_coverage']['priority_documented'],2)
            self.assertFalse(manifest['publication_authorized'])
            self.assertTrue('geography_scope' in json.loads(archive.read('review/scope.recipe.json')) or 'geography' in json.loads(archive.read('review/scope.recipe.json')))
            entry=[k for k in archive.namelist() if k.endswith('.scope.json')][0]
            cfg=json.loads(archive.read(entry))
            self.assertEqual(cfg['geography_scope']['priority'],'canada')
        self.assertEqual(self.path.read_bytes(),original)
    def test_wizard_has_click_to_apply_scope(self):
        static=Path(__file__).resolve().parents[1]/'skope/static'
        html=(static/'index.html').read_text()
        js=(static/'wizard.js').read_text()
        app=(static/'app.js').read_text()
        self.assertIn("5 · Geography",js)
        self.assertIn("button('Apply geographic scope'",js)
        self.assertIn('setGeography:',app)
        self.assertIn('geography:{...geography}',app)
        self.assertIn('geocounts',html)
        self.assertIn('id="wizard-open"',html)

if __name__=='__main__':unittest.main()
