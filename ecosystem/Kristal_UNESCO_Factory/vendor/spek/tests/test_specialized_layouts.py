"""All 19 specialized layouts require explicit semantic units, can render HTML/TeX,
and can enter the standard private Wiki format under an allowed Arketype profile.
"""
from __future__ import annotations
import json
from pathlib import Path
import tempfile
import unittest
from spek.core import ValidationError, compile_inputs, read_json
from spek.render import article_html, article_tex
from spek.specialized_layouts import SPECIALIZED_FAMILIES
from spek.wiki import render_document, load_profiles
from spek.document import project_document

ROOT=Path(__file__).resolve().parents[1]
LAYOUTS=[read_json(p) for p in sorted((ROOT/'layouts').glob('*.json'))]


def synthetic(layout):
    units=[]
    evidence=[]
    entries={}
    slots={}
    counter=0
    for slot, rule in layout['slots'].items():
        refs=[]
        for _ in range(rule['min']):
            counter+=1
            kind=rule['allowed_kinds'][0]
            ident=('e' if kind=='evidence' else 'u')+str(counter)
            key='text'+str(counter)
            refs.append(ident)
            entries[key]={lang:{'text':f'{lang} valeur {ident}','status':'fixture','provider':'manual_test'} for lang in ('fr','en','it')}
            if kind=='evidence':
                evidence.append({'id':ident,'realization_key':key,'status':'illustrative_fixture','locator':'test://fixture'})
            else:
                units.append({'id':ident,'kind':kind,'realization_key':key,'epistemic_status':'design_proposal','evidence_refs':[]})
        slots[slot]=refs
    for k in ('title','subtitle','abstract','heading'):
        entries[k]={lang:{'text':f'{lang} {k}','status':'fixture','provider':'manual_test'} for lang in ('fr','en','it')}
    source={'format':'kristal.layout-article-source/0.1',
            'article':{'id':'article.special.demo','title_key':'title','subtitle_key':'subtitle','abstract_key':'abstract'},
            'source':{'origin':'illustrative_fixture','state_ref':None,'state_commitment':None,'artifact_refs':[],
                      'scientific_review':'not_submitted','disclosure':'local_demo_only','language_review':{'fr':'fixture','en':'fixture','it':'fixture'}},
            'units':units,'evidence':evidence,
            'sections':[{'id':'specialized','layout':layout['id'],'heading_key':'heading','slots':slots}]}
    realizations={'format':'kristal.layout-realizations/0.1','entries':entries}
    return source,realizations


class SpecializedLayoutTests(unittest.TestCase):
    def test_all_19_have_renderers_and_typed_contracts(self):
        self.assertEqual(len(LAYOUTS),27)
        self.assertEqual({l['id'] for l in LAYOUTS if l['id'] in SPECIALIZED_FAMILIES},set(SPECIALIZED_FAMILIES))
        for layout in LAYOUTS:
            if layout['id'] not in SPECIALIZED_FAMILIES:continue
            with self.subTest(template=layout['id']):
                source,real=synthetic(layout)
                model=compile_inputs(source,real,LAYOUTS,languages=('fr','en','it'))
                for lang in ('fr','en','it'):
                    html=article_html(model,lang)
                    tex=article_tex(model,lang)
                    self.assertIn(layout['id'],html)
                    self.assertIn('valeur',html)
                    self.assertIn(layout['id'].replace('-',' ').capitalize(),tex)
                    self.assertIn('specialized',tex)
                    doc=project_document(model,lang)
                    # A valid explicit Arketype allowlist is used for a private demonstration.
                    profiles=load_profiles(ROOT/'template_library/wiki/archetype-profiles.json')
                    available=[p for p in profiles.values() if layout['id'] in p['allowed_layouts']]
                    self.assertTrue(available)
                    pages=render_document(doc,slug='demo-special',archetype='demo',profile=available[0],demo=True)
                    self.assertIn('Kristal-demo-special.md',pages)
                    self.assertIn('NON PUBLIABLE' if lang=='fr' else 'NOT PUBLISHABLE' if lang=='en' else 'NON PUBBLICABILE',pages['Kristal-demo-special.md'])

    def test_missing_specialized_required_slot_is_rejected(self):
        layout=next(x for x in LAYOUTS if x['id']=='double-entry-ledger')
        source,real=synthetic(layout)
        del source['sections'][0]['slots']['entries']
        with self.assertRaisesRegex(ValidationError,'Cardinality violation'):
            compile_inputs(source,real,LAYOUTS,languages=('fr',))

    def test_wrong_kind_is_rejected(self):
        layout=next(x for x in LAYOUTS if x['id']=='taxonomy-tree')
        source,real=synthetic(layout)
        expected=source['sections'][0]['slots']['specializations'][0]
        next(x for x in source['units'] if x['id']==expected)['kind']='concept'
        with self.assertRaisesRegex(ValidationError,'Wrong kind'):
            compile_inputs(source,real,LAYOUTS,languages=('fr',))


if __name__=='__main__':unittest.main()

class SpecializedIntegrationTests(unittest.TestCase):
    def test_private_wiki_draft_uses_selected_specialized_layout(self):
        from spek.wiki import build_wiki, verify_wiki
        layout=next(x for x in LAYOUTS if x['id']=='taxonomy-tree')
        source,real=synthetic(layout)
        with tempfile.TemporaryDirectory() as d:
            folder=Path(d)
            (folder/'article.json').write_text(json.dumps(source),encoding='utf-8')
            (folder/'realizations.json').write_text(json.dumps(real),encoding='utf-8')
            result=build_wiki(source=folder/'article.json',realizations=folder/'realizations.json',
                layouts=ROOT/'layouts',templates=ROOT/'template_library/wiki/archetype-profiles.json',
                archetype='modele-multiplexe',language='fr',slug='test-specialized',
                out=folder/'wiki',demonstration=True)
            self.assertEqual(set(result['files']),{'Home.md','_Sidebar.md','Kristal-test-specialized.md'})
            content=(folder/'wiki/Kristal-test-specialized.md').read_text(encoding='utf-8')
            self.assertIn('### Concepts',content)
            self.assertIn('### Relations de spécialisation',content)
            self.assertIn('DÉMONSTRATION — NON PUBLIABLE',content)
            self.assertEqual(verify_wiki(folder/'wiki')['format'],'spek.wiki-draft/1.0')

    def test_pdf_specialized_layout(self):
        from spek.render import article_pdf
        layout=next(x for x in LAYOUTS if x['id']=='double-entry-ledger')
        source,real=synthetic(layout)
        compiled=compile_inputs(source,real,LAYOUTS,languages=('fr',))
        with tempfile.TemporaryDirectory() as d:
            dest=Path(d)/'rendered.pdf'
            article_pdf(compiled,'fr',dest)
            self.assertTrue(dest.is_file())
            self.assertGreater(dest.stat().st_size,1500)
