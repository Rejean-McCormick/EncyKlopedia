"""Regression of real Spek vNext grammar and noncanonical source boundaries."""
import json
import pathlib
import sys
import tempfile
import unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
from discourse_factory import build, instance_for, source_fixture
from spek.composition.engine import Library, resolve, dialogue_plan, materialize, render_html
from spek.composition.discourse import discourse_audit
from discourse_factory import SPEK_ROOT

class DiscourseV15(unittest.TestCase):
    def setUp(self):
        self.concepts={'concept111':{'unesco_id':'concept111',
            'preferred_labels':{'fr':['Environnement'],'en':['Environment']},
            'definitions':{'fr':['Ensemble de conditions dans lesquelles vivent les organismes.'],
                           'en':['Conditions in which organisms live.']},
            'microthesaurus_ids':['mt2.10'],'source_uri':'http://vocabularies.unesco.org/thesaurus/concept111'},
          'concept112':{'unesco_id':'concept112',
            'preferred_labels':{'fr':['Apprentissage'],'en':['Learning']},'definitions':{},
            'microthesaurus_ids':['mt2.10'],'source_uri':'http://vocabularies.unesco.org/thesaurus/concept112'}}
        self.groups=[{'type':'microthesaurus','id':'mt2.10','label_fr':'Sciences','label_en':'Science'}]

    def test_native_62_templates_and_real_discourse(self):
        lib=Library(SPEK_ROOT/'template_library')
        self.assertEqual(sum(x.startswith('rhetorical.') for x in lib.definitions),62)
        concept=self.concepts['concept111']
        obj=instance_for(concept,'fr',True)
        resolved=resolve(obj,lib)
        self.assertEqual(dialogue_plan(resolved,'fr')['fields'][0]['discourse']['function'],'term')
        self.assertEqual(discourse_audit(resolved)['templates_with_discourse_model'],1)
        values=materialize(resolved,source_fixture(concept,'fr',concept['definitions']['fr'][0]),'fr')
        page=render_html(resolved,values,language='fr')
        self.assertIn('conditions dans lesquelles',page)
        self.assertNotIn('PGF qualifié',page)

    def test_all_concepts_and_preview_nocanon(self):
        with tempfile.TemporaryDirectory() as tmp:
            out=pathlib.Path(tmp)/'07_DISCOURS'
            descriptions={'concept112':{'description_fr':'processus d’acquisition de connaissances',
                                        'description_en':'knowledge acquisition process'}}
            report=build(self.concepts,self.groups,out,descriptions=descriptions)
            self.assertEqual(report['instance_count'],4)
            self.assertEqual(report['microthesaurus_preview_pages'],2)
            self.assertEqual(report['GF_PGF_realizations_validated'],0)
            self.assertEqual(report['source_definitions_by_language'],2)
            self.assertEqual(report['wikidata_literal_previews'],2)
            self.assertFalse(report['publication_authorized'])
            fr=(out/'previews/fr/unesco-mt2-10.html').read_text(encoding='utf-8')
            self.assertIn('Wikidata décrit le candidat',fr)
            self.assertIn('classé dans le microthésaurus',fr)
            self.assertIn('non publiables',fr)
            for path in (out/'instances').rglob('*.json'):
                o=json.loads(path.read_text(encoding='utf-8'))
                self.assertEqual(o['authority'],'editorial_bindings_explicit_not_approved')
                self.assertNotIn('editorial_relation',o)
                self.assertNotIn('semantic_graph',json.dumps(o))

if __name__=='__main__':unittest.main()
