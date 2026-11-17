"""Acceptance and negative tests for the unified template grammar."""
from __future__ import annotations
import copy
import json
import tempfile
import unittest
from pathlib import Path
from spek.composition import Library, resolve, dialogue_plan, materialize, render_html, render_markdown
from spek.composition.commands import preview
from spek.core import ValidationError

ROOT = Path(__file__).resolve().parents[1]
EX = ROOT/'docs'/'COMPOSITION_RECURSIVE_VNEXT'/'exemples'

def fixture(name):
    return json.loads((EX/name).read_text(encoding='utf8'))

class RecursiveCompositionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.library=Library(ROOT/'template_library')

    def test_templates_categories(self):
        self.assertIn('wiki.article@1.0.0',self.library.definitions)
        self.assertIn('rhetorical.argument-evidence@1.0.0',self.library.definitions)
        self.assertEqual(len([k for k in self.library.definitions if k.startswith('rhetorical.')]),62)

    def test_argument_three_proofs(self):
        r=resolve(fixture('argument-trois-preuves.instance.json'),self.library)
        self.assertEqual(len(r.leaves),7)
        self.assertEqual([v.key for v in r.leaves][1:4],['arg1.proof.1','arg1.proof.2','arg1.proof.3'])
        self.assertEqual(len(set(v.path for v in r.leaves)),7)

    def test_fractal_two_arguments_six_proofs(self):
        r=resolve(fixture('wiki-deux-arguments-six-preuves.instance.json'),self.library)
        self.assertEqual(len(r.leaves),16)
        self.assertEqual(len([v for v in r.leaves if '.proof.' in v.key]),6)
        self.assertEqual(len(set(v.key for v in r.leaves)),16)

    def test_idempotent_ast_and_render(self):
        o=fixture('wiki-deux-arguments-six-preuves.instance.json')
        a=resolve(o,self.library);b=resolve(o,self.library)
        self.assertEqual(a,b)
        vals=materialize(a,fixture('wiki-fractal-realizations-FICTIVES.json'),'fr')
        self.assertEqual(render_html(a,vals),render_html(b,vals))
        self.assertEqual(render_markdown(a,vals),render_markdown(b,vals))
        self.assertNotIn('<p><p>',render_html(a,vals))
        self.assertNotIn('rhetorical.argument',render_html(a,vals))
        self.assertNotIn('instance_path',render_html(a,vals))
        self.assertIn('Phrase de démonstration',render_html(a,vals))

    def test_compact_output_preserves_qualifications(self):
        r=resolve(fixture('argument-trois-preuves.instance.json'),self.library)
        b={'format':'kristal.layout-realizations/0.1','entries':{v.key:{'fr':{'text':'Texte '+str(i)+'.','status':'fixture','provider':'test'}} for i,v in enumerate(r.leaves)}}
        vals=materialize(r,b,'fr')
        html=render_html(r,vals)
        self.assertIn('qualification',html)
        self.assertNotIn('<h2>',html)
        self.assertIn('<strong>',html)
        self.assertNotIn('data-request',html)

    def test_comparison_responsive_and_ordered(self):
        r=resolve(fixture('comparaison-narrative.instance.json'),self.library)
        vals={l.key:f'Texte {i}.' for i,l in enumerate(r.leaves)}
        html=render_html(r,vals)
        self.assertIn('comparison-flow',html)
        self.assertIn('@media(max-width:650px)',html)
        self.assertLess(html.index('Texte 2.'),html.index('Texte 3.'))
        self.assertIn('Texte 5.',html)

    def test_missing_repeat_instance(self):
        o=fixture('argument-trois-preuves.instance.json')
        o['bindings']['evidence']['instances'].pop()
        with self.assertRaises(ValidationError):resolve(o,self.library)

    def test_unapproved_request_cannot_be_implied(self):
        o=fixture('argument-trois-preuves.instance.json')
        del o['bindings']['inference']['communication_request_ref']
        with self.assertRaises(ValidationError):resolve(o,self.library)

    def test_missing_required_qualification_refused(self):
        o=fixture('argument-trois-preuves.instance.json')
        del o['bindings']['objection']
        with self.assertRaises(ValidationError):resolve(o,self.library)

    def test_repeat_ref_mismatch(self):
        o=fixture('argument-trois-preuves.instance.json')
        o['bindings']['evidence']['instances'][1]['template_ref']='rhetorical.conclusion@1.0.0'
        with self.assertRaises(ValidationError):resolve(o,self.library)

    def test_no_inference_from_ambiguous_kind(self):
        o=fixture('comparaison-narrative.instance.json')
        o['bindings']['question']['kind']='evidence'
        with self.assertRaises(ValidationError):resolve(o,self.library)

    def test_invalid_version_no_fallback(self):
        o=fixture('argument-trois-preuves.instance.json')
        o['template_ref']='rhetorical.argument-evidence@5.0.0'
        with self.assertRaises(ValidationError):resolve(o,self.library)

    def test_no_implicit_duplicate_phrasing(self):
        o=fixture('argument-trois-preuves.instance.json')
        o['bindings']['evidence']['instances'][0]['bindings']['statement']['realization_key']='arg1.proof.2'
        with self.assertRaises(ValidationError):resolve(o,self.library)

    def test_cycle_detected_on_bound_child(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); folder=root/'rhetorical'/'templates';folder.mkdir(parents=True)
            c={'format':'spek.template-graph/1.0','category':'rhetorical','template_id':'rhetorical.loop','version':'1.0.0',
               'slots':{'next':{'node_kind':'child','allowed_templates':['rhetorical.loop@1.0.0'],'min':1,'max':1}},'ordered_slots':['next'],
               'presentation_policy':{'layout_variant':'flow','show_template_labels':False},'no_fact_selection':True,'no_text_generation':True}
            (folder/'loop.json').write_text(json.dumps(c))
            lib=Library(root)
            i={'format':'spek.composition-instance/1.0','instance_id':'loop','template_ref':'rhetorical.loop@1.0.0',
               'bindings':{'next':{'node_type':'template_ref','template_ref':'rhetorical.loop@1.0.0','bindings':{}}},
               'authority':'editorial_bindings_explicit_not_approved'}
            with self.assertRaises(ValidationError):resolve(i,lib)

    def test_language_and_shape_explicit(self):
        r=resolve(fixture('comparaison-narrative.instance.json'),self.library)
        plan=dialogue_plan(r,'fr')
        self.assertEqual(plan['fields'][0]['form']['force'],'ASK')
        self.assertEqual(plan['fields'][0]['form']['block_kinds'],['question'])
        self.assertEqual(len(plan['fields']),6)
        self.assertFalse(any('semantic_graph' in x for x in plan['fields']))

    def test_semantik_question_force_refusal(self):
        r=resolve(fixture('comparaison-narrative.instance.json'),self.library)
        request={'schema_version':'1.0','semantic_graph':{},'obligations':[{'force':'ASSERT'}],
                 'context':{'target_language':'fr'}, 'constraints':{}}
        with self.assertRaises(ValidationError):dialogue_plan(r,'fr',requests={l.request_ref:request for l in r.leaves})

    def test_semantik_request_does_not_change_obligations(self):
        r=resolve(fixture('argument-trois-preuves.instance.json'),self.library)
        requests={}
        for l in r.leaves:
            force='ASSERT' if l.kind in {'claim','conclusion'} else 'PRESENT'
            requests[l.request_ref]={'schema_version':'1.0','semantic_graph':{'nodes':[]},
                'obligations':[{'force':force,'id':l.key}], 'context':{'target_language':'fr'},'constraints':{}}
        original=copy.deepcopy(requests)
        plan=dialogue_plan(r,'fr',requests=requests)
        self.assertEqual(requests,original)
        self.assertEqual(len(plan['fields']),7)

    def test_missing_realization_and_language(self):
        r=resolve(fixture('wiki-deux-arguments-six-preuves.instance.json'),self.library)
        b=fixture('wiki-fractal-realizations-FICTIVES.json')
        with self.assertRaises(ValidationError):materialize(r,b,'en')
        b['entries'].pop(r.leaves[0].key)
        with self.assertRaises(ValidationError):materialize(r,b,'fr')

    def test_sensitive_data_not_displayed(self):
        r=resolve(fixture('wiki-deux-arguments-six-preuves.instance.json'),self.library)
        for private in ['referent: urn:x','C:\\mycode\\Kristal','a'*64,'file:///private','string: debug']:
            b=fixture('wiki-fractal-realizations-FICTIVES.json')
            b['entries'][r.leaves[0].key]['fr']['text']=private
            with self.assertRaises(ValidationError):materialize(r,b,'fr')

    def test_html_escapes_input(self):
        r=resolve(fixture('wiki-deux-arguments-six-preuves.instance.json'),self.library)
        b=fixture('wiki-fractal-realizations-FICTIVES.json')
        b['entries'][r.leaves[0].key]['fr']['text']='<script>alert(1)</script>'
        vals=materialize(r,b,'fr')
        html=render_html(r,vals)
        self.assertNotIn('<script>alert',html)
        self.assertIn('&lt;script&gt;',html)

    def test_reject_unexpected_values(self):
        r=resolve(fixture('argument-trois-preuves.instance.json'),self.library)
        vals={x.key:'Sentence.' for x in r.leaves}
        vals['bonus']='not permitted'
        with self.assertRaises(ValidationError):render_html(r,vals)

    def test_preview_writes_only_private_readers(self):
        with tempfile.TemporaryDirectory() as d:
            out=Path(d)/'preview'
            x=preview(ROOT,EX/'wiki-deux-arguments-six-preuves.instance.json',EX/'wiki-fractal-realizations-FICTIVES.json','fr',out)
            self.assertEqual({f.name for f in out.iterdir()},{'index.html','Brouillon-prive.md'})
            self.assertEqual(x['status'],'private_not_approved')
            with self.assertRaises(ValidationError):preview(ROOT,EX/'wiki-deux-arguments-six-preuves.instance.json',EX/'wiki-fractal-realizations-FICTIVES.json','fr',out)

    def test_no_upgrade_to_approval(self):
        o=fixture('argument-trois-preuves.instance.json')
        o['authority']='approved_to_publish'
        with self.assertRaises(ValidationError):resolve(o,self.library)

    def test_no_join_mode_inline(self):
        o=fixture('argument-trois-preuves.instance.json')
        o['presentation']['join_mode']='inline-safe'
        with self.assertRaises(ValidationError):resolve(o,self.library)

if __name__ == '__main__':unittest.main()


def test_semantik_recursive_import_validates_real_pairs(tmp_path):
    """Import complete synthetic CommunicationResult pairs, never fake a runtime certification."""
    import hashlib
    from spek.composition.semantik_adapter import import_results
    from spek.slot_dialogue import KIND_POLICY
    library=Library(ROOT/'template_library')
    resolved=resolve(fixture('comparaison-narrative.instance.json'),library)
    reqdir=tmp_path/'requests';resdir=tmp_path/'results'
    reqdir.mkdir();resdir.mkdir()
    for i,leaf in enumerate(resolved.leaves,1):
        _, force, kinds, _ = KIND_POLICY[leaf.kind]
        actual_force='ASK' if force=='ASK' else 'PRESENT'
        block_kind='question' if actual_force=='ASK' else 'utterance'
        sid=f'statement:{i}';oid=f'obligation:{i}'
        req={
            'schema_version':'1.0','request_id':f'req:{i}',
            'semantic_graph':{'nodes':[], 'statements':[{'id':sid,'source_refs':[f'source:{i}']}]},
            'obligations':[{'obligation_id':oid,'semantic_refs':[sid], 'force':actual_force,'source_refs':[f'source:{i}']}],
            'context':{'target_language':'fr', 'target_locale':'fr-CA'},
            'constraints':{'allowed_block_kinds':[block_kind],'output_format':'structured'},
            'capability_profile':'test-profile','runtime_selector':{'runtime_set_id':'test-only-runtime'}
        }
        result={
            'schema_version':'1.0', 'language':'fr', 'locale':'fr-CA',
            'blocks':[{'block_id':f'b:{i}','kind':block_kind,'text':f'Phrase de test {i}.','obligation_ids':[oid]}],
            'plain_text':f'Phrase de test {i}.',
            'coverage':[{'obligation_id':oid,'block_ids':[f'b:{i}'],'realization_unit_ids':[f'u:{i}']}],
            'source_refs':[f'source:{i}'],
            'runtime':{'runtime_set_id':'test-only-runtime','sa_gf_contract_version':'1.0','capability_profile':'test-profile'}
        }
        raw=json.dumps(result,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode('utf8')
        result['deterministic_result_id']='sha256:'+hashlib.sha256(raw).hexdigest()
        filename=Path(leaf.request_ref).name
        (reqdir/filename).write_text(json.dumps(req),encoding='utf8')
        (resdir/filename).write_text(json.dumps(result),encoding='utf8')
    bundle=import_results(resolved,reqdir,resdir,'fr')
    vals=materialize(resolved,bundle,'fr')
    assert len(vals)==6
    assert 'Phrase de test 1' in render_html(resolved,vals)
    # Validation fails closed if any covered obligation is removed.
    filename=Path(resolved.leaves[0].request_ref).name
    bad=json.loads((resdir/filename).read_text(encoding='utf8'))
    bad['coverage']=[]
    (resdir/filename).write_text(json.dumps(bad),encoding='utf8')
    import pytest
    with pytest.raises(ValidationError):import_results(resolved,reqdir,resdir,'fr')


def test_markdown_markup_is_escaped():
    r=resolve(fixture('comparaison-narrative.instance.json'),Library(ROOT/'template_library'))
    values={x.key:'Texte.' for x in r.leaves}
    values[r.leaves[0].key]='<script>alert(1)</script>'
    markdown=render_markdown(r,values)
    assert '<script>' not in markdown
    assert '&lt;script&gt;' in markdown


def test_direct_renderer_cannot_bypass_privacy_filter():
    r=resolve(fixture('comparaison-narrative.instance.json'),Library(ROOT/'template_library'))
    values={x.key:'Texte.' for x in r.leaves}
    values[r.leaves[0].key]='Source de test: '+('a'*64)
    with unittest.TestCase().assertRaises(ValidationError):render_html(r,values)
