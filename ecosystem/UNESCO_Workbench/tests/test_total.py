"""No network, no publication. Run: py -3 -m unittest discover -s UNESCO_Workbench/tests -v"""
import copy
import importlib.util
import json
import shutil
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1]/'pipelines/unesco_total.py'
spec=importlib.util.spec_from_file_location('unesco_total',SCRIPT)
total=importlib.util.module_from_spec(spec)
spec.loader.exec_module(total)


class IntegratedPrivateResearch(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)/'UNESCO_Workbench'
        shutil.copytree(SCRIPT.parents[1]/'reference',self.root/'reference')

    def test_2025_rdf_reconciliation_matches_actual_branch(self):
        view=total.make_view(self.root)
        self.assertEqual(len(view['articles']),41)
        cmp=view['rdf_comparison']
        self.assertEqual(cmp['historical_matched'],40)
        self.assertEqual(cmp['added_since_historical'],['concept17189'])
        self.assertEqual(len(cmp['relations']['broader']['added']),2)
        self.assertEqual(len(cmp['relations']['broader']['removed']),1)
        self.assertEqual(len(cmp['relations']['related']['added']),4)

    def test_41_english_anchors_19_unapproved_claims_and_6_sources(self):
        view=total.make_view(self.root)
        rte=next(a for a in view['articles'] if a['unesco_id']=='concept10')
        self.assertEqual(rte['localized']['en']['title'],'Right to education')
        self.assertEqual(rte['semantic_id'],'KQ3')
        self.assertEqual(rte['wikidata_candidate']['id'],'Q69370')
        self.assertEqual(len(rte['claim_proposals']),19)
        self.assertEqual(len(rte['source_refs']),6)
        self.assertEqual(sum(bool(a['wikidata_candidate']) for a in view['articles']),36)
        self.assertTrue(all(a['editorial_status'] in ('source_anchor_only','research_candidate_unapproved') for a in view['articles']))
        self.assertFalse(view['qualified'])
        self.assertFalse(view['publication_enabled'])

    def test_build_deterministic_integrity_gate_and_tamper(self):
        report=total.build(self.root)
        self.assertEqual(report['status'],'PRIVATE_RESEARCH_BUILT_UNQUALIFIED')
        self.assertEqual(total.check(self.root)['articles'],41)
        self.assertEqual(total.build(self.root)['view_sha256'],report['view_sha256'])
        view_path,_=total.output_paths(self.root)
        view_path.write_text(view_path.read_text()+' ',encoding='utf-8')
        with self.assertRaisesRegex(ValueError,'digest mismatch'):
            total.check(self.root)

    def test_fail_closed_on_fake_approval(self):
        ref=self.root/'reference/r2_proposals.jsonl'
        rows=[json.loads(l) for l in ref.read_text().splitlines()]
        rows[0]['canonical_ka_id']='KA1'
        ref.write_text('\n'.join(json.dumps(row) for row in rows))
        with self.assertRaisesRegex(ValueError,'promotion detected'):
            total.make_view(self.root)

    def test_fail_closed_on_source_capture(self):
        f=self.root/'reference/r2_sources.json'
        data=json.loads(f.read_text())
        data['sources'][0]['capture_status']='CAPTURED'
        f.write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError,'captured/reviewed source'):
            total.make_view(self.root)

    def test_fail_closed_on_crosswalk_promotion(self):
        f=self.root/'reference/v11_crosswalk.json'
        data=json.loads(f.read_text())
        data['mappings'][0]['status']='approved'
        f.write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError,'promoted'):
            total.make_view(self.root)

    def test_compare_rdf_origin_sha_strict(self):
        rdf=self.root/'snapshot.ttl'
        rdf.write_text('NOT THE LINKEDDATAHUB SNAPSHOT')
        outcome=total.verify_historical_rdf(self.root,rdf)
        self.assertEqual(outcome['status'],'REFERENCE_CHANGED_REVIEW_REQUIRED')


if __name__=='__main__':unittest.main()
