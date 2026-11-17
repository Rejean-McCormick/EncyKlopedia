import copy
import html
import json
import tempfile
import unittest
from pathlib import Path
from spek.cli import build, verify_site, import_semantik
from spek.core import ValidationError, compile_inputs, read_json, escape_tex
from spek.render import article_html, article_tex
from argparse import Namespace

BASE=Path(__file__).resolve().parent.parent

def fixtures():
    return (read_json(BASE/'examples/article.json'),read_json(BASE/'examples/realizations.json'),
            [read_json(p) for p in sorted((BASE/'layouts').glob('*.json'))])

class Validations(unittest.TestCase):
    def model(self,modify=None):
        inp=fixtures()
        if modify: modify(*inp)
        return compile_inputs(*inp)

    def test_three_layouts_three_languages(self):
        m=self.model()
        self.assertEqual([s['layout'] for s in m.sections],['result-card','argument-map','comparison'])
        self.assertTrue(m.demo)
        for lang in ['fr','en','it']:
            h=article_html(m,lang)
            self.assertIn(f'<html lang="{lang}">',h)
            self.assertEqual(h.count('<section class="panel"'),3)
            self.assertIn('data-unit-id="u.argument.premise2"',h)
            self.assertIn('DÉMONSTRATION' if lang=='fr' else 'DEMONSTRATION' if lang=='en' else 'DIMOSTRAZIONE',h)
            tex=article_tex(m,lang)
            self.assertIn(r'\documentclass',tex)
            self.assertIn(r'\end{document}',tex)

    def test_missing_language_fails(self):
        def mod(s,r,l): del r['entries']['u.result.claim']['it']
        with self.assertRaisesRegex(ValidationError,'Missing realization'):self.model(mod)

    def test_missing_evidence_fails(self):
        def mod(s,r,l): s['sections'][0]['slots']['evidence']=[]
        with self.assertRaisesRegex(ValidationError,'Cardinality violation'):self.model(mod)

    def test_bad_kind_fails(self):
        def mod(s,r,l): s['sections'][0]['slots']['claim']='u.argument.thesis'
        with self.assertRaisesRegex(ValidationError,'Wrong kind'):self.model(mod)

    def test_unlinked_evidence_fails(self):
        def mod(s,r,l): s['units'][0]['evidence_refs']=['e.layout']
        with self.assertRaisesRegex(ValidationError,'evidence not linked'):self.model(mod)

    def test_argument_requires_evidence(self):
        def mod(s,r,l):
            for u in s['units']:
                if u['id'] in ('u.argument.premise1','u.argument.premise2'):
                    u['evidence_refs']=[]
        with self.assertRaisesRegex(ValidationError,'no referenced evidence'):self.model(mod)

    def test_duplicate_id_fails(self):
        def mod(s,r,l): s['units'][1]['id']=s['units'][0]['id']
        with self.assertRaisesRegex(ValidationError,'Duplicate unit'):self.model(mod)

    def test_html_is_escaped(self):
        def mod(s,r,l): r['entries']['u.result.claim']['fr']['text']='<script>alert(1)</script> & data'
        m=self.model(mod);txt=article_html(m,'fr')
        self.assertIn('&lt;script&gt;alert(1)&lt;/script&gt; &amp; data',txt)
        self.assertNotIn('<script>alert(1)</script>',txt)

    def test_tex_escaping(self):
        self.assertIn(r'\%',escape_tex('x%'))
        self.assertIn(r'\_',escape_tex('unit_key'))
        self.assertIn(r'\textbackslash{}',escape_tex('\\evil'))

    def test_demo_production_blocked(self):
        with self.assertRaisesRegex(ValidationError,'pinned v9 source'):
            compile_inputs(*fixtures(),production=True)

    def test_kristal_identity_reference_mismatch_blocked(self):
        s,r,l=fixtures();s['source']['origin']='kristal_v9';s['source']['state_ref']='urn:kristal:state:wrong';
        s['source']['state_commitment']='sha256:'+'a'*64;s['source']['artifact_refs']=['urn:kristal:example:A']
        snap={'artifact_type':'kristal_state_snapshot','schema_version':'9.0',
              'state_ref':'urn:kristal:state:correct',
              'logical_commitment':{'digest':'sha256:'+'a'*64},
              'members':[{'artifact_id':'urn:kristal:example:A'}]}
        with self.assertRaisesRegex(ValidationError,'snapshot reference/digest mismatch'):
            compile_inputs(s,r,l,state_snapshot=snap)

    def test_output_integrity_and_fail_closed_demo_publication(self):
        with tempfile.TemporaryDirectory() as td:
            target=Path(td)/'site'
            args=Namespace(source=str(BASE/'examples/article.json'),realizations=str(BASE/'examples/realizations.json'),
                           layouts=str(BASE/'layouts'),languages='fr,en,it',state_snapshot=None,
                           out=str(target),formats='html,tex',production=False)
            build(args)
            verify_site(target)
            with self.assertRaisesRegex(ValidationError,'demonstration artifacts'):
                verify_site(target,require_production=True)
            (target/'fr/index.html').write_text('tampered')
            with self.assertRaisesRegex(ValidationError,'altered'):
                verify_site(target)

    def test_import_semantik_stays_fixture(self):
        with tempfile.TemporaryDirectory() as td:
            target=Path(td)/'import.json'
            args=Namespace(input=str(BASE/'examples/semantik-prototype-minimal.json'),
                           mapping=str(BASE/'examples/semantik-case-mapping.json'),out=str(target))
            import_semantik(args)
            x=read_json(target)
            self.assertEqual(x['entries']['u.theophile.A001']['fr']['status'],'fixture')
            self.assertIn('request_id',x['entries']['u.theophile.A001']['fr'])
            self.assertNotIn('en',x['entries']['u.theophile.A001'])

if __name__=='__main__':unittest.main()
