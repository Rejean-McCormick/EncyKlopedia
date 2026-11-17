"""Educational adapters: public/demo-only projection, no student/teacher data."""
from __future__ import annotations
import copy
import json
import tempfile
import unittest
from pathlib import Path

from spek.core import ValidationError, compile_inputs, read_json
from spek.education import import_educational
from spek.document import project_document
from spek.render import article_html, article_tex, article_pdf
from spek.cli import verify_site
from spek.locale import UI

ROOT=Path(__file__).resolve().parents[1]
LAYOUTS=[read_json(p) for p in sorted((ROOT/'layouts').glob('*.json'))]

def fixture(adapter='ekole'):
    path='ekole-curated-preview.json' if adapter=='ekole' else 'kompose-public-excerpt.json'
    return read_json(ROOT/'examples/education'/path)

class EducationalInteroperability(unittest.TestCase):
    def test_eight_original_layouts_retained_alongside_specialized_layouts(self):
        self.assertEqual(len(LAYOUTS),27)
        self.assertTrue({'result-card','argument-map','comparison','concept-card','learning-path',
           'evidence-comparison','observation-inference','chronology'} <= {x['id'] for x in LAYOUTS})

    def test_ekole_five_layouts_three_languages_and_identity(self):
        source,realizations=import_educational(fixture(),'ekole')
        compiled=compile_inputs(source,realizations,LAYOUTS)
        self.assertTrue(compiled.demo)
        self.assertEqual(len(compiled.sections),5)
        self.assertEqual(len(compiled.units),29)
        self.assertEqual(len(compiled.evidence),2)
        for lang in ('fr','en','it'):
            doc=project_document(compiled,lang)
            self.assertEqual(len(doc.sections),5)
            self.assertEqual(doc.source_external_system,'ekole')
            for sec in doc.sections:
                for items in sec.slots.values():
                    for item in items:
                        self.assertTrue(item.external_ref.startswith('ekole:'))
            html=article_html(compiled,lang)
            tex=article_tex(compiled,lang)
            self.assertGreaterEqual(html.count('class="source-inspector"'),20)
            self.assertIn('source-inspector',html)
            self.assertIn('data-unit-id=',html)
            self.assertIn('spek-section-id:',tex)
            for layout in ['concept-card','learning-path','evidence-comparison','observation-inference','chronology']:
                self.assertIn(layout,html)
                self.assertIn(UI[lang][layout],tex)
            for layout in ['concept-card','learning-path','evidence-comparison','observation-inference','chronology']:
                self.assertIn(layout,UI[lang])

    def test_kompose_is_not_ekole_and_not_session(self):
        source,realizations=import_educational(fixture('kompose'),'kompose')
        compiled=compile_inputs(source,realizations,LAYOUTS)
        self.assertEqual(len(compiled.sections),1)
        self.assertEqual(project_document(compiled,'en').source_external_system,'kompose')
        self.assertTrue(compiled.demo)
        self.assertEqual(source['source']['disclosure'],'local_demo_only')

    def test_raw_ekole_teacher_material_rejected(self):
        data=fixture();data['document']['teacher_only']={'answer_key':'private'}
        with self.assertRaisesRegex(ValidationError,'Forbidden'):import_educational(data,'ekole')

    def test_raw_kompose_session_rejected(self):
        data=fixture('kompose');data['session']={'roles':[], 'learner_ref':'child'}
        with self.assertRaisesRegex(ValidationError,'Forbidden'):import_educational(data,'kompose')

    def test_reject_private_classification(self):
        for label in ('private_teacher','class_group','student_pii','unclassified'):
            data=fixture();data['scope']['data_classification']=label
            with self.subTest(label=label), self.assertRaises(ValidationError):import_educational(data,'ekole')

    def test_reject_incomplete_or_unapproved_export(self):
        for key,value in [('complete',False),('producer','another'),('format','wrong')]:
            data=fixture();data[key]=value
            with self.subTest(key=key),self.assertRaises(ValidationError):import_educational(data,'ekole')
        data=fixture();data['scope']['export_status']='unfiltered'
        with self.assertRaises(ValidationError):import_educational(data,'ekole')

    def test_reject_unqualified_public_excerpt(self):
        data=fixture();data['scope']['data_classification']='public_released_excerpt'
        with self.assertRaisesRegex(ValidationError,'pedagogical review'):import_educational(data,'ekole')

    def test_no_unreferenced_realizations(self):
        data=fixture();data['realizations']['entries']['hidden.answer']={'fr':{'text':'Secret','status':'fixture','provider':'fixture'}}
        with self.assertRaisesRegex(ValidationError,'Unreferenced'):import_educational(data,'ekole')

    def test_no_arbitrary_phrase_fields(self):
        data=fixture();data['realizations']['entries']['title']['fr']['learner_name']='Private student'
        with self.assertRaisesRegex(ValidationError,'Forbidden'):import_educational(data,'ekole')

    def test_no_teacher_evidence_locator(self):
        data=fixture();data['document']['evidence'][0]['locator']='teacher-only/answer-key.json'
        with self.assertRaisesRegex(ValidationError,'Restricted'):import_educational(data,'ekole')

    def test_missing_source_identity_is_refused(self):
        data=fixture();del data['document']['units'][0]['external_ref']
        with self.assertRaisesRegex(ValidationError,'Missing'):import_educational(data,'ekole')

    def test_wrong_kompose_scope(self):
        data=fixture('kompose');data['selection']['access_scope']='session_only'
        with self.assertRaisesRegex(ValidationError,'statically exported'):import_educational(data,'kompose')

    def test_unapproved_public_fragment_cannot_produce_production(self):
        source,real=import_educational(fixture(),'ekole')
        with self.assertRaisesRegex(ValidationError,'pinned v9'):compile_inputs(source,real,LAYOUTS,production=True)

    def test_end_to_end_pdf_and_document_integrity(self):
        source,real=import_educational(fixture(),'ekole')
        model=compile_inputs(source,real,LAYOUTS)
        with tempfile.TemporaryDirectory() as t:
            for lang in ('fr','en','it'):
                article_pdf(model,lang,Path(t)/f'{lang}.pdf')
                self.assertGreater((Path(t)/f'{lang}.pdf').stat().st_size,1000)
            from pypdf import PdfReader
            self.assertEqual(len(PdfReader(str(Path(t)/'fr.pdf')).pages),2)

if __name__=='__main__': unittest.main()
