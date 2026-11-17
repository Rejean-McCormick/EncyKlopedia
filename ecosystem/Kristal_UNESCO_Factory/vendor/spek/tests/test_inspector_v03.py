"""Tests for source inspection and word attributes (offline, fail-closed)."""
import copy
import unittest
from pathlib import Path
from bs4 import BeautifulSoup
from spek.core import compile_inputs, read_json, ValidationError
from spek.document import project_document
from spek.render import article_html

ROOT=Path(__file__).resolve().parent.parent

def inputs():
    return (read_json(ROOT/'examples/article.json'),read_json(ROOT/'examples/realizations.json'),
            [read_json(p) for p in sorted((ROOT/'layouts').glob('*.json'))])

class SourceExplorer(unittest.TestCase):
    def setUp(self):
        self.model=compile_inputs(*inputs())

    def test_each_card_has_its_own_keyboard_operable_source_toggle(self):
        for lang in ('fr','en','it'):
            doc=project_document(self.model, lang)
            tree=BeautifulSoup(article_html(self.model,lang),'html.parser')
            cards=tree.select('[data-slot]')
            self.assertEqual(len(cards),sum(bool(items) for s in doc.sections for items in s.slots.values()))
            for card in cards:
                source=card.select_one('details.source-inspector')
                self.assertIsNotNone(source)
                self.assertEqual(len(source.select('summary.source-trigger')),1)
                self.assertIsNone(source.get('open'))
                self.assertEqual(card['data-slot'],source['data-inspector-slot'])
                self.assertTrue(source.select('dl.source-attributes'))
                self.assertTrue(source.select('table.token-table'))
                self.assertEqual(len(card.select('[data-unit-id]')),
                                 len(source.select('[data-source-id]')))

    def test_localization(self):
        for lang,label in [('fr','Explorer la source'),('en','Explore source'),('it','Esplora la fonte')]:
            h=article_html(self.model,lang)
            self.assertIn(label,h)
            self.assertIn('data-source-id="u.result.claim"',h)
            self.assertIn('class="source-panel"',h)

    def test_manual_sample_word_attributes_explicitly_marked(self):
        for lang,lemma in [('fr','contrat'),('en','declarative'),('it','contratto')]:
            doc=project_document(self.model,lang)
            item=doc.sections[0].slots['evidence'][0]
            tokens=[tok for tok in item.tokens if tok['annotation_status']=='manual_fixture']
            self.assertEqual(len(tokens),2)
            self.assertEqual(tokens[0]['lemma'],lemma)
            for tok in item.tokens:
                self.assertEqual(tok['surface'],item.text[tok['start']:tok['end']])
                if tok['annotation_status']=='surface_only':
                    self.assertFalse(tok['lemma'])
                    self.assertFalse(tok['pos'])

    def test_source_has_evidence_provider_and_fingerprint(self):
        doc=project_document(self.model,'en')
        item=doc.sections[0].slots['claim'][0]
        self.assertEqual({p['id'] for p in item.evidence_details},{'e.layout','e.tests'})
        self.assertEqual(item.realization_provider,'manual_demo_fixture')
        html=article_html(self.model,'en')
        self.assertNotIn(doc.source_sha256,html)
        self.assertIn('local_artifact',html)
        self.assertIn('manual_demo_fixture',html)
        self.assertIn('Not supplied',html)

    def test_invalid_manual_token_span_refused(self):
        source,real,layout=inputs()
        real['entries']['e.layout']['en']['tokens'][0]['start']=1234
        with self.assertRaisesRegex(ValidationError,'Token span mismatch'):
            compile_inputs(source,real,layout)

    def test_duplicate_token_span_refused(self):
        source,real,layout=inputs()
        token=real['entries']['e.layout']['en']['tokens'][0]
        real['entries']['e.layout']['en']['tokens'].append(copy.deepcopy(token))
        with self.assertRaisesRegex(ValidationError,'duplicate'):
            compile_inputs(source,real,layout)

    def test_fake_qualified_token_refused(self):
        source,real,layout=inputs()
        real['entries']['e.layout']['en']['tokens'][0]['annotation_status']='qualified'
        with self.assertRaisesRegex(ValidationError,'requires qualified realization'):
            compile_inputs(source,real,layout)

    def test_attribute_values_are_escaped(self):
        source,real,layout=inputs()
        real['entries']['e.layout']['fr']['tokens'][0]['features']['Injected']='<img src=x onerror=alert(1)>'
        html=article_html(compile_inputs(source,real,layout),'fr')
        self.assertIn('&lt;img src=x onerror=alert(1)&gt;',html)
        self.assertNotIn('<img src=x onerror=alert(1)>',html)
        self.assertNotIn('<script>alert(1)</script>',html)

    def test_document_sidecar_includes_token_provenance(self):
        d=project_document(self.model,'it').to_dict()
        self.assertEqual(d['format'],'spek.document/0.4')
        self.assertEqual(d['source_origin'],'illustrative_fixture')
        self.assertEqual(d['sections'][0]['slots']['evidence'][0]['tokens'][0]['annotation_status'],'manual_fixture')
        self.assertEqual(d['sections'][0]['slots']['claim'][0]['evidence_details'][0]['id'],'e.layout')

if __name__=='__main__':unittest.main()
