"""v0.2 semantic parity and pagination regression tests."""
import os
import re
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from pypdf import PdfReader

from spek.cli import build, verify_site
from spek.core import compile_inputs, read_json, ValidationError
from spek.document import project_document
from spek.render import article_html, article_pdf, article_tex, _pdf_font_paths
from argparse import Namespace

BASE = Path(__file__).resolve().parent.parent

def model():
    return compile_inputs(read_json(BASE/'examples/article.json'),
                          read_json(BASE/'examples/realizations.json'),
                          [read_json(p) for p in sorted((BASE/'layouts').glob('*.json'))])

class RenderFidelity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model=model()

    def test_every_slot_item_has_consistent_tracing(self):
        for lang in self.model.languages:
            doc=project_document(self.model,lang)
            html=article_html(self.model,lang)
            tex=article_tex(self.model,lang)
            for sec in doc.sections:
                self.assertIn(f'id="{sec.id}"',html)
                for slot,items in sec.slots.items():
                    for item in items:
                        self.assertIn(f'data-unit-id="{item.id}"',html)
                        self.assertIn(f'data-kind="{item.kind}"',html)
                        self.assertIn(f'data-status="{item.status}"',html)
                        self.assertIn(f'data-source-id="{item.id}"',html)
                        self.assertIn(f'<code>{item.id}</code>',html)
                        self.assertNotIn('<span class="ref">',html)
                        self.assertIn(item.trace().replace('_',r'\_'),tex)
                        self.assertEqual(item.evidence_refs,tuple(self.model.item(item.id,lang).get('evidence_refs',[])))
                        self.assertEqual(item.text,self.model.item(item.id,lang)['text'])
            # Technical fingerprints remain in document.json/manifest, never in reading views.
            self.assertNotIn(doc.source_sha256,html)
            self.assertNotIn(doc.layouts_sha256,html)
            self.assertNotIn(doc.realizations_sha256,html)
            self.assertNotIn(doc.source_sha256,tex)
            self.assertNotIn(doc.layouts_sha256,tex)
            self.assertIn('#1e6864',html)
            self.assertIn('class="brand-mark"',html)

    def test_localized_ui_metadata_all_languages(self):
        for lang,expected in {'fr':'Traçabilité', 'en':'Traceability', 'it':'Tracciabilità'}.items():
            h=article_html(self.model,lang)
            self.assertIn(expected,h)
            t=article_tex(self.model,lang)
            self.assertIn(expected,t)

    def test_export_links_are_format_aware(self):
        html=article_html(self.model,'en',formats=('html','tex'))
        self.assertNotIn('href="article.pdf"',html)
        self.assertIn('href="article.tex"',html)
        self.assertIn('href="document.json"',html)

    def test_projected_document_contains_16_units_and_2_evidence(self):
        data=project_document(self.model,'fr').to_dict()
        self.assertEqual(data['format'],'spek.document/0.4')
        ids=[item['id'] for sec in data['sections'] for items in sec['slots'].values() for item in items]
        self.assertEqual(len(set(ids)),18)
        self.assertEqual(len(data['sections']),3)
        self.assertIn('e.layout',data['sections'][0]['slots']['evidence'][0]['id'])

    def test_unicode_font_is_required_not_helvetica_fallback(self):
        with patch.dict(os.environ,{'SPEK_FONT_REGULAR':'/nonexistent/foo.ttf',
                                    'SPEK_FONT_BOLD':'/nonexistent/bar.ttf'}):
            with self.assertRaisesRegex(ValidationError,'not found'):
                _pdf_font_paths()

    def test_pdf_rejects_missing_glyph_instead_of_replacement(self):
        m=model()
        m.realizations['entries']['u.result.claim']['fr']['text'] += ' 🛸'
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaisesRegex(ValidationError,'glyph'):
                article_pdf(m,'fr',Path(td)/'unqualified.pdf')

    def test_pdf_trace_and_no_orphan_page(self):
        with tempfile.TemporaryDirectory() as td:
            for lang in self.model.languages:
                target=Path(td)/(lang+'.pdf')
                article_pdf(self.model,lang,target)
                pdf=PdfReader(str(target))
                self.assertEqual(len(pdf.pages),2,f'{lang}: sample PDF should be two pages')
                pages=[p.extract_text() for p in pdf.pages]
                self.assertGreater(len(pages[-1]),700,f'{lang}: nearly empty last page')
                doc=project_document(self.model,lang)
                contents='\n'.join(pages)
                for sec in doc.sections:
                    for items in sec.slots.values():
                        for item in items:
                            self.assertIn(item.id,contents)
                            self.assertIn(item.status,contents)
                for digest in (doc.source_sha256,doc.realizations_sha256,doc.layouts_sha256):
                    self.assertNotIn(digest,contents)
                self.assertIn(' '.join(doc.title.split()),' '.join(contents.split()))

    def test_build_outputs_shared_document_sidecars(self):
        with tempfile.TemporaryDirectory() as td:
            output=Path(td)/'site'
            b=Namespace(source=str(BASE/'examples/article.json'),realizations=str(BASE/'examples/realizations.json'),
                        layouts=str(BASE/'layouts'),languages='fr,en,it',state_snapshot=None,
                        out=str(output),formats='html,pdf,tex',production=False)
            manifest=build(b)
            self.assertEqual(len(manifest['files']),13)
            verify_site(output)
            for lang in self.model.languages:
                self.assertIn(f'{lang}/document.json',manifest['files'])
                self.assertIn(f'{lang}/index.html',manifest['files'])
                self.assertIn(f'{lang}/article.pdf',manifest['files'])
                self.assertIn(f'{lang}/article.tex',manifest['files'])
                doc=read_json(output/lang/'document.json')
                self.assertEqual(doc['language'],lang)
                self.assertEqual(len(doc['sections']),3)
                html=(output/lang/'index.html').read_text(encoding='utf8')
                self.assertIn('href="article.pdf"',html)
                self.assertIn('href="article.tex"',html)
                self.assertIn('href="document.json"',html)

if __name__ == '__main__':
    unittest.main()
