"""Spek Wiki is a private, deterministic presentation projection, not Git publication."""
from __future__ import annotations
import json
import tempfile
import unittest
from pathlib import Path
from spek.core import ValidationError
from spek.wiki import build_wiki, load_profiles, safe_md, verify_wiki

ROOT=Path(__file__).resolve().parents[1]

class WikiTemplatesTests(unittest.TestCase):
    def demo(self, tmp: Path, **overrides):
        kw={'source': ROOT/'examples/article.json',
            'realizations':ROOT/'examples/realizations.json',
            'layouts':ROOT/'layouts',
            'templates':ROOT/'template_library/wiki/archetype-profiles.json',
            'archetype':'composition-hybride', 'language':'fr',
            'slug':'demo-test', 'out':tmp/'wiki', 'demonstration':True}
        kw.update(overrides)
        return build_wiki(**kw)

    def test_registry_covers_19_profiles_and_27_layouts(self):
        profiles=load_profiles(ROOT/'template_library/wiki/archetype-profiles.json')
        self.assertEqual(len(profiles),19)
        layouts={p.stem for p in (ROOT/'layouts').glob('*.json')}
        self.assertEqual(len(layouts),27)
        for profile in profiles.values():
            self.assertIn(profile['preferred_layout'],layouts)
            self.assertTrue(set(profile['allowed_layouts']) <=layouts)

    def test_valid_hybrid_markdown_and_verification(self):
        with tempfile.TemporaryDirectory() as td:
            out=Path(td)/'wiki'; result=self.demo(Path(td),out=out)
            self.assertEqual(set(result['files']),{'Home.md','_Sidebar.md','Kristal-demo-test.md'})
            text=(out/'Kristal-demo-test.md').read_text(encoding='utf8')
            self.assertIn('### Prémisses',text)
            self.assertIn('1. Le layout',text)
            self.assertIn('### Incertitudes',text)
            self.assertIn('### Preuves',text)
            self.assertIn('DÉMONSTRATION — NON PUBLIABLE',text)
            self.assertNotIn('internal/private/path',text)
            self.assertEqual(verify_wiki(out)['format'],'spek.wiki-draft/1.0')

    def test_qualified_semantik_binding_with_pinned_mock_state(self):
        # Only checks the Spek handoff; mock markers are NOT a real SA runtime proof.
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            src=json.loads((ROOT/'examples/article.json').read_text(encoding='utf8'))
            real=json.loads((ROOT/'examples/realizations.json').read_text(encoding='utf8'))
            sha='sha256:'+'a'*64
            src['source'].update({'origin':'kristal_v9','state_ref':'kristal:test',
                'state_commitment':sha,'artifact_refs':['k-artifact'],
                'scientific_review':'approved','disclosure':'approved',
                'language_review':{'fr':'approved'}})
            for key,langs in real['entries'].items():
                if 'fr' in langs:
                    langs['fr'].update({'channel':'semantik_architect','status':'qualified',
                        'provider':'semantik_architect','request_id':'test-request-'+key,
                        'runtime_set_id':'test-runtime'})
            state={'artifact_type':'kristal_state_snapshot','schema_version':'9.0',
                   'state_ref':'kristal:test','logical_commitment':{'digest':sha},
                   'members':[{'artifact_id':'k-artifact'}]}
            for name,obj in [('article',src),('realizations',real),('state',state)]:
                (root/(name+'.json')).write_text(json.dumps(obj),encoding='utf8')
            m=self.demo(root,source=root/'article.json',realizations=root/'realizations.json',
                state_snapshot=root/'state.json',demonstration=False)
            self.assertFalse(m['demonstration']);self.assertTrue(m['source_verified'])
            self.assertEqual(m['authorization'],'EXTERNAL_C1_C2_REQUIRED')

    def test_english_realizations(self):
        with tempfile.TemporaryDirectory() as td:
            self.demo(Path(td),language='en')
            self.assertIn('DEMONSTRATION — NOT PUBLISHABLE',(Path(td)/'wiki/Kristal-demo-test.md').read_text())

    def test_wrong_layout_for_archetype_is_blocked(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaisesRegex(ValidationError,'not admitted'):
                self.demo(Path(td),archetype='procedure-protocole')
            self.assertFalse((Path(td)/'wiki').exists())

    def test_production_requires_semantik_and_verified_kristal(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaisesRegex(ValidationError,'Unqualified'):
                self.demo(Path(td),demonstration=False)

    def test_no_overwrite_on_second_run(self):
        with tempfile.TemporaryDirectory() as td:
            self.demo(Path(td))
            with self.assertRaisesRegex(ValidationError,'NEW directory'):
                self.demo(Path(td))

    def test_mutated_markdown_is_detected(self):
        with tempfile.TemporaryDirectory() as td:
            self.demo(Path(td))
            p=Path(td)/'wiki/Home.md';p.write_text(p.read_text()+'tampering',encoding='utf8')
            with self.assertRaisesRegex(ValidationError,'Modified Wiki'):
                verify_wiki(Path(td)/'wiki')

    def test_slug_cannot_escape_private_directory(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaisesRegex(ValidationError,'Unsafe wiki slug'):
                self.demo(Path(td),slug='../escape')

    def test_markup_is_literal_not_rendered_as_html(self):
        result=safe_md('<img src=x onerror=alert(1)> [click](https://x.example)')
        self.assertIn(r'\<img',result)
        self.assertIn(r'\[click\]',result)

    def test_no_git_checkout_output(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);(root/'.git').mkdir()
            with self.assertRaisesRegex(ValidationError,'outside ALL Git'):
                self.demo(root,out=root/'candidate')

if __name__=='__main__':unittest.main()
