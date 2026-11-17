"""Contract integration using an explicitly FAKE linearizer, never a GF proof."""
import json
from pathlib import Path
import sys
import tempfile
import unittest

P=Path(__file__).resolve().parents[1]
F=Path(__file__).resolve().parents[3]
if not (F/'vendor'/'spek').is_dir():
    F=Path('/mnt/data/work_overlay/factory')
S=Path(r'C:\mycode\SemantiK_Architect\SemantiK_Architect')
if not (S/'src'/'semantik_architect').is_dir():
    S=Path('/mnt/data/work_overlay/semantik')
sys.path[:0]=[str(P),str(S/'src'),str(F/'vendor'/'spek'),str(F)]
import pilot
from discourse_factory import instance_for
from spek.composition.engine import Library, resolve, materialize
from spek.composition.semantik_adapter import import_results
from spek.slot_dialogue import KIND_POLICY, compose_request
from semantik_architect.adapters.realization.gf.bridge import GfBridgeRealizer
from semantik_architect.conformance.candidate import CandidateConformance
from semantik_architect.conformance.harness import ConformanceHarness

class ClearlyFakeRuntime:
    def __init__(self,_path):pass
    def linearize(self,expression,language):
        return 'MOCK_NOT_GF_'+language+'_'+expression

class Contracts(unittest.TestCase):
    def test_interop_without_actual_gf_claim(self):
        concept={'unesco_id':'concept10','source_uri':'https://example.org/concept10',
                 'preferred_labels':{'fr':['Éducation'],'en':['Education']},
                 'microthesaurus_ids':['mt1.1'],'status':'source_only_not_canonical'}
        micro={'id':'mt1.1','uri':'https://example.org/micro',
               'label_fr':'Sciences','label_en':'Science'}
        lib=Library(F/'vendor/spek/template_library')
        for lang in ('fr','en'):
            with self.subTest(lang=lang),tempfile.TemporaryDirectory() as tmp:
                inst=instance_for(concept,lang,False)
                resolved=resolve(inst,lib)
                reqdir=Path(tmp)/'requests';resdir=Path(tmp)/'results'
                reqdir.mkdir();resdir.mkdir()
                reqs={}
                for leaf in resolved.leaves:
                    raw=pilot.make_request(concept,micro,lang,leaf)
                    _,force,kinds,limit=KIND_POLICY[leaf.kind]
                    request=compose_request(raw,{'force':force,'block_kinds':kinds,'max_length':limit},language=lang)
                    reqs[leaf.key]=request
                    (reqdir/Path(leaf.request_ref).name).write_text(json.dumps(request),encoding='utf-8')
                cand=pilot.create_candidate(Path(tmp),lang,reqs)
                (cand/'grammar.pgf').write_bytes(b'TEST_FAKE_NOT_GF')
                pilot.create_lock(cand,lang)
                app=CandidateConformance(cand,f'unesco-pilot-{lang}-1',
                  realizer=GfBridgeRealizer(runtime_factory=ClearlyFakeRuntime))
                report=ConformanceHarness(app).run(json.loads((cand/'conformance.suite.json').read_text())).to_dict()
                self.assertTrue(report['passed'],report)
                for leaf in resolved.leaves:
                    (resdir/Path(leaf.request_ref).name).write_text(json.dumps(app.render(reqs[leaf.key])),encoding='utf-8')
                bundle=import_results(resolved,reqdir,resdir,lang)
                rendered=materialize(resolved,bundle,lang)
                self.assertEqual(len(rendered),2)
                self.assertTrue(all(value.startswith('MOCK_NOT_GF_') for value in rendered.values()))

if __name__=='__main__': unittest.main()
