"""Research-based rhetorical catalogue: structural guarantees only, not semantic truth."""
from __future__ import annotations
import copy
import json
from pathlib import Path
import unittest

from spek.composition.engine import Library, resolve, materialize, render_html, render_markdown, dialogue_plan
from spek.core import ValidationError

ROOT=Path(__file__).resolve().parents[1]
EX=ROOT/'docs/COMPOSITION_RECURSIVE_VNEXT/exemples'

class RhetoricalCatalogueTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.lib=Library(ROOT/'template_library')
        cls.data=json.loads((ROOT/'template_library/rhetorical/research-inventory.json').read_text(encoding='utf-8'))

    def inst(self):
        return json.loads((EX/'toulmin-etude-fictive.instance.json').read_text(encoding='utf-8'))

    def realizations(self):
        return json.loads((EX/'toulmin-etude-fictive-realizations.json').read_text(encoding='utf-8'))

    def test_inventory_exactly_matches_executable_templates(self):
        refs={p['template_ref'] for p in self.data['patterns']}
        self.assertEqual(len(refs),62)
        self.assertEqual(refs, {r for r in self.lib.definitions if r.startswith('rhetorical.')})
        self.assertEqual(len(self.data['sources']),8)

    def test_editorial_relation_marker_must_be_present(self):
        case=self.inst();del case['editorial_relation']
        with self.assertRaises(ValidationError):resolve(case,self.lib)

    def test_relation_tag_is_exact(self):
        case=self.inst();case['editorial_relation']['relation_tag']='rst.evidence'
        with self.assertRaises(ValidationError):resolve(case,self.lib)

    def test_cannot_claim_semantic_validation_or_approval(self):
        case=self.inst();case['editorial_relation']['status']='verified'
        with self.assertRaises(ValidationError):resolve(case,self.lib)

    def test_attestation_must_reference_explicit_sources(self):
        case=self.inst();case['editorial_relation']['source_assertion_refs']=[]
        with self.assertRaises(ValidationError):resolve(case,self.lib)

    def test_no_implicit_duplicate_source_refs(self):
        case=self.inst();case['editorial_relation']['source_assertion_refs']=['a','a']
        with self.assertRaises(ValidationError):resolve(case,self.lib)

    def test_toulmin_example_is_lossless_and_rhetorical(self):
        resolved=resolve(self.inst(),self.lib)
        self.assertEqual(len(resolved.leaves),8)
        values=materialize(resolved,self.realizations(),'fr')
        html=render_html(resolved,values)
        md=render_markdown(resolved,values)
        self.assertEqual(html.count('<p>'),3)
        self.assertIn('<strong>Dans cette étude fictive',html)
        self.assertIn('\\n\\nÀ conditions comparables'.replace('\\n','\n'),md)
        self.assertIn('Une différence de calibration',html)
        self.assertNotIn('fictional.test.claim',html)
        self.assertNotIn('toulmin.claim-grounds-warrant',html)
        for val in values.values():self.assertEqual(html.count(val),1)

    def test_discourse_policy_only_from_allowed_semantik_kinds(self):
        case=self.inst(); resolved=resolve(case,self.lib)
        plan=dialogue_plan(resolved,'fr')
        fields={f['realization_key']:f for f in plan['fields']}
        self.assertEqual(fields['case.thesis']['form']['force'],'ASSERT')
        self.assertEqual(fields['case.proof.1']['form']['force'],'PRESENT')
        self.assertEqual(fields['case.warrant']['form']['force'],'PRESENT')

    def test_bad_break_policy_fails_closed(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            src=ROOT/'template_library/rhetorical/templates/toulmin-compact.json'
            d=json.loads(src.read_text(encoding='utf-8'))
            d['presentation_policy']['paragraph_break_before_slots']=['this-does-not-exist']
            target=Path(tmp)/'rhetorical/templates';target.mkdir(parents=True)
            (target/src.name).write_text(json.dumps(d),encoding='utf-8')
            with self.assertRaises(ValidationError):Library(Path(tmp))

if __name__=='__main__':unittest.main()

def test_all_new_patterns_can_be_explicitly_instantiated_and_rendered():
    """Generate only artificial test bindings, not sources or editorial decisions."""
    import itertools
    lib=Library(ROOT/'template_library')
    data=json.loads((ROOT/'template_library/rhetorical/research-inventory.json').read_text(encoding='utf-8'))
    counter=itertools.count(1)
    def instantiate(ref: str):
        definition=lib.get(ref)
        slots={}
        for slot,rule in definition['slots'].items():
            if not rule['min']: continue
            if rule['node_kind']=='text':
                n=next(counter)
                slots[slot]={'node_type':'text_slot', 'kind':rule['allowed_kinds'][0],
                             'realization_key':f'test.text.{n}',
                             'communication_request_ref':f'requests/test.text.{n}.json'}
            else:
                childref=rule['allowed_templates'][0]
                slots[slot]=instantiate(childref)
        result={'node_type':'template_ref','template_ref':ref,'bindings':slots}
        if 'rhetorical_contract' in definition:
            result['editorial_relation']={'relation_tag':definition['rhetorical_contract']['relationship_label'],
                 'status':'declared_unverified','source_assertion_refs':['fixture.ref.1']}
        return result
    checked=0
    for item in data['patterns']:
        if item['family']=='original_vnext': continue
        instance=instantiate(item['template_ref'])
        instance.update(format='spek.composition-instance/1.0',instance_id='fixture',
                        authority='editorial_bindings_explicit_not_approved')
        resolved=resolve(instance,lib)
        vals={leaf.key:'Phrase de test fictive.' for leaf in resolved.leaves}
        rendered=render_html(resolved, vals)
        assert 'Aperçu privé' in rendered
        assert 'editorial_relation' not in rendered
        assert len(resolved.leaves)>=1
        checked+=1
    assert checked==52

def test_rhetoric_list_cli_is_readonly(capsys):
    from spek.cli import main
    assert main(['rhetoric-list','--family','argument']) == 0
    assert 'rhetorical.walton-analogy' in capsys.readouterr().out
    assert main(['rhetoric-list','--format','json']) == 0
    body=json.loads(capsys.readouterr().out)
    assert len(body['patterns']) == 62
