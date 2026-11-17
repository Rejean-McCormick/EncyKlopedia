"""Regressions for real Wikidata statements, refs, and no-canon boundary."""
import csv
import gzip
import json
import sqlite3
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from wikidata_full import extract, EvidenceUnavailable
from factory_core import Factory
import test_factory as fixture_module


def entity(qid,value):
    return {'id':qid,'type':'item','labels':{'fr':{'language':'fr','value':'Sujet '+qid}},
            'descriptions':{'en':{'language':'en','value':'Test knowledge subject'}},
            'claims':{'P31':[{'id':qid+'$abc','type':'statement','rank':'normal',
                'mainsnak':{'snaktype':'value','property':'P31','datatype':'wikibase-item',
                            'datavalue':{'type':'wikibase-entityid','value':{'entity-type':'item','id':value,'numeric-id':int(value[1:])}}},
                'qualifiers':{'P580':[{'snaktype':'value','property':'P580','datatype':'time',
                       'datavalue':{'type':'time','value':{'time':'+2001-01-01T00:00:00Z','precision':11}}}]},
                'references':[{'snaks':{'P854':[{'snaktype':'value','property':'P854','datatype':'url',
                    'datavalue':{'type':'string','value':'https://example.test/sourcing'}}]},'snaks-order':['P854']}]
            }]}}


class FullClaims(unittest.TestCase):
    def test_complete_extraction_provenance_qualifiers_and_refs(self):
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp);source=base/'entities.jsonl'
            source.write_text('\n'.join(json.dumps(entity(k,v)) for k,v in [('Q1','Q5'),('Q2','Q6')])+'\n',encoding='utf8')
            mapping={'concept111':{'status':'SINGLE_P3916_CANDIDATE','wikidata_qid_candidate':'Q1'},
                     'concept112':{'status':'REVIEW_AMBIGUOUS_P3916','wikidata_qid_candidate':'Q2'}}
            manifest, summaries=extract(mapping,source,None,base/'out')
            self.assertTrue(manifest['coverage_complete'])
            self.assertEqual(manifest['requested_unique_qids'],1)
            self.assertEqual(manifest['entities_found'],1)
            self.assertEqual(manifest['reference_groups'],1)
            self.assertEqual(manifest['qualifier_snaks'],1)
            self.assertEqual(manifest['statement_count'],1)
            self.assertEqual(summaries['concept111']['preview'][0][:3],'P31')
            self.assertEqual([json.loads(x)['id'] for x in gzip.open(base/'out/raw_entities.jsonl.gz','rt',encoding='utf8')],['Q1'])
            doc=json.loads((base/'out/facts.jsonl').read_text(encoding='utf8').strip())
            self.assertEqual(doc['claims']['P31'][0]['references'][0]['snaks']['P854'][0]['datavalue']['value'],'https://example.test/sourcing')
            self.assertIn('P580',doc['claims']['P31'][0]['qualifiers'])
            self.assertTrue(doc['source_status'].startswith('read_only'))

    def test_missing_source_rejects_without_full_scan(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp);source=p/'wikidata-all.json.gz'
            with gzip.open(source,'wt') as f:f.write(json.dumps(entity('Q1','Q5'))+'\n')
            with self.assertRaises(EvidenceUnavailable):
                extract({'concept111':{'status':'SINGLE_P3916_CANDIDATE','wikidata_qid_candidate':'Q1'}},source,'',p/'out')

    def test_end_to_end_native_kit_and_spek_with_full_evidence(self):
        with tempfile.TemporaryDirectory(prefix='unesco-with-full-') as tmp:
            root=Path(tmp);ttl,claims=fixture_module.FactoryTests().build_fixture(root)
            source=root/'entities.jsonl'
            source.write_text(json.dumps(entity('Q1','Q5'))+'\n'+json.dumps(entity('Q2','Q6'))+'\n',encoding='utf8')
            cfg={'ttl':str(ttl),'claims':str(claims),'index':'', 'output':str(root/'runs'),
                 'full_enabled':True,'full_source':str(source),'ai_enabled':False,'ai_model':'','ai_limit':0}
            report=Factory(cfg).run();run=next((root/'runs').iterdir())
            self.assertEqual(report['wikidata_full_claims_import'],'COMPLETE_FOR_P3916_UNIQUE_CANDIDATES_NOT_REVIEWED')
            self.assertEqual(report['counts']['full_entities'],2)
            self.assertEqual(report['counts']['wikidata_statements'],2)
            self.assertEqual(report['counts']['kristals_built'],2)
            self.assertEqual(report['counts']['spek_concept_sections'],3)
            self.assertTrue((run/'02_WIKIDATA/FAITS_COMPLETS/faits_consultables.html').is_file())
            self.assertIn('P31', (run/'04_SPEK/inputs/unesco-micro1/realizations.json').read_text('utf8'))
            self.assertIn('wikidata-full-facts-index.json', '\n'.join(x.name for x in (run/'03_KRISTALS/unesco-micro1/derived').iterdir()))
            canon=(run/'03_KRISTALS/unesco-micro1/canon/domain/unesco-source.json').read_text('utf8')
            self.assertNotIn('P31',canon)
            self.assertNotIn('Q1',canon)

if __name__=='__main__':unittest.main()

class SnapshotAcquisition(unittest.TestCase):
    def test_reuse_skope_snapshot_directory_and_no_unmatched_identity(self):
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp);folder=base/'skope';folder.mkdir()
            with gzip.open(folder/'part-000000.jsonl.gz','wt',encoding='utf8') as f:
                f.write(json.dumps(entity('Q11','Q5'))+'\n'+json.dumps(entity('Q12','Q5'))+'\n')
            (folder/'snapshot-manifest.json').write_text(json.dumps({'parts':[{'file':'part-000000.jsonl.gz','count':2}]}))
            mapping={'concept111':{'status':'SINGLE_P3916_CANDIDATE','wikidata_qid_candidate':'Q11'},
                     'concept112':{'status':'NO_P3916_MAPPING','wikidata_qid_candidate':'Q12'}}
            manifest, rows=extract(mapping,folder,'',base/'out')
            self.assertTrue(manifest['coverage_complete'])
            self.assertEqual(set(rows),{'concept111'})
            self.assertNotIn('Q12',(base/'out/facts.jsonl').read_text('utf8'))
