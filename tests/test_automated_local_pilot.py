"""End-to-end offline regression tests for UNESCO concept10->41 automation.

Works on a cumulative 1+2+3 installation; only a synthetic XML/SQLite and
synthetic UNESCO ZIP are used. Never opens user production sources.
"""
import bz2
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sqlite3
import tempfile
import unittest
from zipfile import ZipFile

MODULE=Path(__file__).resolve().parents[1]/'tools/unesco_pilot/automated_local_pilot.py'
spec=importlib.util.spec_from_file_location('unesco_autopilot',MODULE)
app=importlib.util.module_from_spec(spec)
spec.loader.exec_module(app)
ROOT=Path(__file__).resolve().parents[3]
P='01_CANDIDATE_WORKSPACE/unesco-mt1-10/'


def make_pilot(path:Path):
    concepts=[{'unesco_id':f'concept{x}','source_uri':f'http://vocabularies.unesco.org/thesaurus/concept{x}',
               'preferred_labels':{'en':[('Right to education' if x==10 else f'Topic {x}')],
                                   'fr':[f'Sujet {x}']},'broader':[],'narrower':[],'related':[]}
              for x in range(1,42)]
    source={'concepts':concepts}
    sourcebytes=(json.dumps(source,sort_keys=True)+'\n').encode()
    scope={'grain':{'one_branch_kristal':True,'no_one_kristal_per_concept':True,
                    'individual_articles_are_projections':True},
           'subject':{'unesco_branch_slug':'unesco-mt1-10','expected_seed_count':41},
           'source_sha256':hashlib.sha256(sourcebytes).hexdigest()}
    mappings={'mappings':[{'unesco_id':f'concept{x}',
                           'qid_candidate':'Q69370' if x==10 else None,
                           'status':'SINGLE_P3916_CANDIDATE' if x==10 else 'NO_CANDIDATE'}
                          for x in range(1,42)]}
    with ZipFile(path,'w') as z:
        z.writestr(P+'derived/encyclopedia_scope.en.json',json.dumps(scope))
        z.writestr(P+'canon/domain/unesco-source.json',sourcebytes)
        z.writestr(P+'derived/wikidata-p3916-candidates.json',json.dumps(mappings))


def make_db(path:Path):
    c=sqlite3.connect(path)
    c.executescript('''CREATE TABLE wiki_pages(page_id INTEGER,title TEXT,ns INTEGER,latest_rev INTEGER,is_redirect INTEGER);
      CREATE TABLE wiki_qid(page_id INTEGER,qid TEXT);
      CREATE TABLE ingest_state(stage TEXT,completed INTEGER);
      INSERT INTO wiki_pages VALUES(100,'Right_to_education',0,111,0);
      INSERT INTO wiki_qid VALUES(100,'Q69370');''')
    for k in ('page','page_props','linktarget','externallinks','pagelinks','categorylinks'):
        c.execute('INSERT INTO ingest_state VALUES (?,1)',(k,))
    c.commit();c.close()


def make_xml(path:Path,revision=111):
    text=f'''<mediawiki><page><title>Right to education</title><ns>0</ns><id>100</id>
      <revision><id>{revision}</id><timestamp>2026-10-01T00:00:00Z</timestamp>
      <text xml:space="preserve">Sample encyclopedic context.</text></revision></page></mediawiki>'''
    path.write_bytes(bz2.compress(text.encode()))


class AutopilotTests(unittest.TestCase):
    def setUp(self):
        t=tempfile.TemporaryDirectory();self.addCleanup(t.cleanup)
        self.d=Path(t.name)
        self.pilot=self.d/'UNESCO-Educational-Policy-Scope-EN-test.zip'
        self.db=self.d/'toy.sqlite'
        self.xml=self.d/'toy.xml.bz2'
        self.work=self.d/'private'
        make_pilot(self.pilot);make_db(self.db);make_xml(self.xml)

    def launch(self,**kw):
        return app.run(ROOT,self.pilot,self.db,self.xml,self.work,
                       skip_install_preflight=True,quiet=True,**kw)

    def test_full_run_and_resume_without_duplicate_extraction(self):
        r=self.launch()
        self.assertEqual(r['status'],'PRIVATE_RESEARCH_PREPARED_NOT_PUBLISHED')
        self.assertEqual(r['concepts_discovered'],41)
        self.assertEqual(r['qid_candidates'],1)
        self.assertEqual(r['projections_planned'],574)
        self.assertEqual(r['pilot_wikipedia_candidate_contexts_eligible'],1)
        self.assertEqual(r['articles_generated'],0)
        self.assertFalse(r['public_release_authorized'])
        self.assertEqual(len(list((self.work/'fiches').glob('concept*.json'))),41)
        xml_manifest=self.work/'wikipedia_extract/manifest.json'
        first=xml_manifest.stat().st_mtime_ns
        second=self.launch()
        self.assertEqual(xml_manifest.stat().st_mtime_ns,first)
        self.assertEqual(second['concepts_discovered'],41)
        self.assertEqual(len(list((self.work/'wikipedia_extract').glob('page*.txt'))),1)

    def test_spek_module_launch_avoids_locale_py_shadowing(self):
        # Regression: python spek/unesco_pilot.py crashed at argparse import
        # when spek/locale.py shadowed the standard library under Python 3.14.
        spek_root=ROOT/'Spek_Semantic-publishing/Spek'
        self.assertTrue((spek_root/'spek/locale.py').is_file())
        r=app.Runner(self.work,quiet=True)
        r.cmd('projection_queue',[spek_root/'spek/unesco_pilot.py','--help'])

    def test_metadata_only_then_full(self):
        first=self.launch(metadata_only=True)
        self.assertFalse(first['xml_scan_performed'])
        self.assertTrue((self.work/'concept10/recherche_preliminaire.json').exists())
        self.assertEqual(json.loads((self.work/'projection_queue_14_langues.json').read_text())['projection_queue_size'],574)
        second=self.launch()
        self.assertTrue(second['xml_scan_performed'])
        self.assertEqual(second['pilot_wikipedia_candidate_contexts_eligible'],1)

    def test_mismatched_revision_is_not_ai_evidence(self):
        make_xml(self.xml,revision=222)
        r=self.launch()
        self.assertEqual(r['pilot_wikipedia_candidate_contexts_eligible'],0)
        concept=json.loads((self.work/'concept10/recherche_avec_sources.json').read_text())
        self.assertFalse(concept['wikipedia_local'][0]['candidate_context_usable'])
        self.assertIsNone(concept['wikipedia_local'][0]['local_path'])

    def test_file_tampering_fails_closed(self):
        self.launch(metadata_only=True)
        (self.work/'inventory.json').write_text('CHANGED',encoding='utf8')
        with self.assertRaisesRegex(app.PilotAutomationError,'modifié'):
            self.launch(metadata_only=True)

    def test_modified_sources_cannot_be_mixed(self):
        self.launch(metadata_only=True)
        old=self.db.stat().st_mtime_ns
        os.utime(self.db,ns=(old+1000,old+1000))
        with self.assertRaisesRegex(app.PilotAutomationError,'Sources modifiées'):
            self.launch(metadata_only=True)

    def test_unfinished_sql_stage_rejected(self):
        c=sqlite3.connect(self.db)
        c.execute("UPDATE ingest_state SET completed=0 WHERE stage='pagelinks'")
        c.commit();c.close()
        with self.assertRaisesRegex(app.PilotAutomationError,'non achevé'):
            self.launch(metadata_only=True)

    def test_single_writer_lock(self):
        self.work.mkdir()
        with app.Lock(self.work):
            with self.assertRaisesRegex(app.PilotAutomationError,'déjà actif'):
                with app.Lock(self.work):pass

    def test_record_never_fabricates_canonical_status(self):
        inv={'records':[{'unesco_id':'concept10','unesco_uri':'urn:unesco:10','unesco_preferred_labels':{'en':['Right to education']},
                         'skos':{},'wikidata':{'qid':'Q69370'},'wikipedia_en_inventory':[]}]}
        x=app.concept_record(inv)
        self.assertIsNone(x['canonical_KQ'])
        self.assertEqual(x['canonical_KA'],[])
        self.assertEqual(x['canonical_KS'],[])
        self.assertFalse(x['public_release_authorized'])

if __name__=='__main__':unittest.main()
