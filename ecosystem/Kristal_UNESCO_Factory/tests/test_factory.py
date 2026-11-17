import csv
import json
import sqlite3
from pathlib import Path
import tempfile
import sys
import unittest
from rdflib import Graph, Namespace, URIRef, Literal
from rdflib.namespace import RDF, SKOS

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from factory_core import Factory

BASE='http://vocabularies.unesco.org/thesaurus/'
UN=Namespace('http://vocabularies.unesco.org/ontology#')
ISO=Namespace('http://purl.org/iso25964/skos-thes#')

class FactoryTests(unittest.TestCase):
    def build_fixture(self,root):
        g=Graph();domain=URIRef(BASE+'domain1');g.add((domain,RDF.type,UN.Domain))
        g.add((domain,SKOS.prefLabel,Literal('Sciences',lang='fr')))
        g.add((domain,SKOS.prefLabel,Literal('Science',lang='en')))
        for m,concepts in [('micro1',['concept111','concept112']),('micro2',['concept113'])]:
            micro=URIRef(BASE+m)
            g.add((micro,RDF.type,UN.MicroThesaurus))
            g.add((domain,ISO.subGroup,micro));g.add((micro,ISO.superGroup,domain))
            g.add((micro,SKOS.prefLabel,Literal('Groupe '+m,lang='fr')))
            g.add((micro,SKOS.prefLabel,Literal('Group '+m,lang='en')))
            for c in concepts:
                cr=URIRef(BASE+c);g.add((cr,RDF.type,SKOS.Concept))
                g.add((micro,SKOS.member,cr))
                g.add((cr,SKOS.prefLabel,Literal('Notice '+c,lang='fr')))
                g.add((cr,SKOS.prefLabel,Literal('Entry '+c,lang='en')))
        # test URIRef in definition
        g.add((URIRef(BASE+'concept111'),SKOS.definition,URIRef(BASE+'concept112')))
        ttl=root/'small.ttl';g.serialize(destination=str(ttl),format='turtle')
        claims=root/'claims.csv';claims.write_text('item,unescoId\nhttp://www.wikidata.org/entity/Q1,concept111\nhttp://www.wikidata.org/entity/Q2,concept113\n',encoding='utf-8')
        return ttl,claims
    def test_end_to_end_with_kit_and_native_spek(self):
        with tempfile.TemporaryDirectory(prefix='unesco-factory-') as tmp:
            root=Path(tmp);ttl,claims=self.build_fixture(root)
            idx=root/'wikidata.compact.sqlite'
            db=sqlite3.connect(idx)
            db.execute('CREATE TABLE entity(id INTEGER PRIMARY KEY,wid TEXT,label_fr TEXT,label_en TEXT,description_fr TEXT,description_en TEXT)')
            db.execute('INSERT INTO entity VALUES(1,?,?,?,?,?)',('Q1','Label Q1','Name Q1','Description française test','English Wikidata description'))
            db.commit();db.close()
            config={'ttl':str(ttl),'claims':str(claims),'index':str(idx),'output':str(root/'run'),
                    'ai_enabled':False,'ai_model':'','ai_limit':0}
            messages=[]
            report=Factory(config,event=lambda k,v:messages.append((k,v))).run()
            self.assertEqual(report['counts']['input_concepts'],3)
            self.assertEqual(report['counts']['kristals_built'],2)
            self.assertEqual(report['counts']['spek_pages_built'],2)
            self.assertEqual(report['counts']['spek_concept_sections'],3)
            self.assertEqual(report['counts']['wd_mapping_count'],2)
            self.assertTrue((next((root/'run').iterdir())/'02_WIKIDATA/local_descriptions.jsonl').is_file())
            run=next((root/'run').iterdir())
            self.assertTrue((run/'04_SPEK/index.html').is_file())
            self.assertTrue((run/'03_KRISTALS/unesco-micro1/build/v9/state-snapshot.json').is_file())
            self.assertTrue((run/'04_SPEK/sites/unesco-micro1/manifest.json').is_file())
            self.assertTrue((run/'RAPPORT_FINAL.json').is_file())
            self.assertTrue((run/'06_AUDIT/audit_p3916.html').is_file())
            self.assertFalse(report['wikidata_mapping_complete']) # test fixture: 1 concept lacks P3916
            self.assertEqual(report['mapping_quality']['concepts_without_p3916'],1)
            self.assertEqual(report['mapping_quality']['single_candidates'],2)
            html_audit=(run/'06_AUDIT/audit_p3916.html').read_text(encoding='utf-8')
            self.assertIn('concept112',html_audit)
            self.assertIn('NO_P3916_MAPPING',html_audit)
            # QIDs never entered the imported-source canonical artifact
            canon=json.loads((run/'03_KRISTALS/unesco-micro1/canon/domain/unesco-source.json').read_text('utf8'))
            self.assertNotIn('Q1',json.dumps(canon))
            self.assertFalse(canon.get('canonical_promotion',False))

    def test_ambiguous_mapping_yields_audit_not_false_success(self):
        with tempfile.TemporaryDirectory(prefix='unesco-factory-ambiguity-') as tmp:
            root=Path(tmp);ttl,claims=self.build_fixture(root)
            claims.write_text('item,unescoId\nhttp://www.wikidata.org/entity/Q1,concept111\nhttp://www.wikidata.org/entity/Q1,concept112\nhttp://www.wikidata.org/entity/Q2,concept113\nhttp://www.wikidata.org/entity/Q3,bogus\n',encoding='utf-8')
            config={'ttl':str(ttl),'claims':str(claims),'index':'','output':str(root/'run'),
                    'ai_enabled':False,'ai_model':'','ai_limit':0}
            report=Factory(config).run()
            self.assertEqual(report['mapping_quality']['ambiguous_concepts'],2)
            self.assertEqual(report['mapping_quality']['single_candidates'],1)
            self.assertEqual(report['mapping_quality']['invalid_p3916_export_rows'],1)
            self.assertFalse(report['wikidata_mapping_complete'])
            audit=Path(report['audit_html']).read_text(encoding='utf-8')
            self.assertIn('Ambigu',audit)
            self.assertIn('Q1',audit)
            self.assertIn('REVIEW_AMBIGUOUS_P3916',audit)

if __name__=='__main__':unittest.main()
