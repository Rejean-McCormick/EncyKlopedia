"""Tests autonomes étape 6, avec données entièrement synthétiques."""
import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parents[1] / 'tools' / 'unesco_pilot' / 'semantic_candidate_stage_v6.py'
spec = importlib.util.spec_from_file_location('etape6', HERE)
s6 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(s6)


def jwrite(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(s6.encode_json(obj))


class Stage6Test(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.work = Path(self.tmp.name) / 'research'
        self.work.mkdir()
        self.cids = ['concept10'] + [f'concept{n}' for n in range(1, 41) if n != 10]
        # Preserve the known five unpaired concepts in this wholly synthetic fixture.
        self.missing = ['concept5999','concept6020','concept17112','concept17163','concept17189']
        self.cids = self.cids[:36] + self.missing
        self.setup_data()

    def tearDown(self):
        self.tmp.cleanup()

    def setup_data(self):
        self.cards = {}
        for idx, cid in enumerate(self.cids):
            wiki = []
            if idx < 16:
                pid = 10000 + idx
                body = f'This is a synthetic example for {cid}.\n'.encode()
                path = self.work / 'wikipedia_extract' / f'page-{pid}.wikitext.txt'
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(body)
                wiki = [{'page_id':pid,'revision_id':'100','sha256':s6.sha(body),
                         'candidate_context_usable': True,'is_redirect':False}]
            card = {'branch':s6.BRANCH,'one_branch_kristal':True,
                    'unesco_id':cid,'unesco_uri':f'http://vocabularies.unesco.org/thesaurus/{cid}',
                    'public_release_authorized':False,'canonical_KQ':None,
                    'canonical_KP':[],'canonical_KA':[],'canonical_KS':[],
                    'wikidata_qid_candidate': None if cid in self.missing else f'Q{idx+1}',
                    'wikidata_mapping_status':'UNREVIEWED_EXTERNAL_CANDIDATE',
                    'target_locales':list(s6.LOCALES),'labels':{'en':[cid]},
                    'wikipedia_en':wiki}
            self.cards[cid] = card
            jwrite(self.work / 'semantic_stage_v4' / 'cards' / (cid+'.json'), card)
        self.edges=[]
        # 122 internal edges, each tuple unique.
        for i in range(122):
            a=self.cids[i % 41];b=self.cids[(i//41+i+1) % 41]
            self.edges.append({'from_unesco_id':a,'relation':('broader','narrower','related')[i//41],
                               'to_unesco_id':b,'to_branch_member':True,'authority':'UNESCO_SKOS_OBSERVED_NOT_KA'})
        for i in range(112):
            self.edges.append({'from_unesco_id':self.cids[i%41],'relation':'related',
                               'to_unesco_id':f'concept{200000+i}', 'to_branch_member':False,
                               'authority':'UNESCO_SKOS_OBSERVED_NOT_KA'})
        jwrite(self.work / 'semantic_stage_v4' / 'skos_candidate_edges.json', {'edges':self.edges})
        # 2 proposals for all, +2 for concept10 and +1 for concept1 => 85.
        self.proposals=[]
        for idx,cid in enumerate(self.cids):
            n=4 if idx==0 else (3 if idx==1 else 2)
            for k in range(n):
                refs=[]
                if idx < 8:
                    # 2 per concept for the first 8 = 16 references exactly
                    if k < 2:
                        w=self.cards[cid]['wikipedia_en'][0]
                        refs=[{'source_type':'wikipedia_en','page_id':w['page_id'],
                               'revision_id':w['revision_id'],'sha256':w['sha256'],
                               'verified_as':'LOCAL_TEXT_IDENTITY_ONLY'}]
                self.proposals.append({'proposal_ref':f'{cid}-P{k+1}','unesco_id':cid,
                                       'text_candidate':f'Unverified statement {idx} {k}',
                                       'model_id':'synthetic-test-model','generation_ref':'synthetic:fixture',
                                       'research_context_refs':refs,'local_research_context_count':len(refs),
                                       'canonical_KA':None,'canonical_KS':[],
                                       'epistemic_status':'AI_CANDIDATE_NOT_ASSERTION',
                                       'review_status':'PENDING','source_validation':'PENDING',
                                       'copyright_review':'PENDING'})
        self.dossier = {'example':'synthetic'}
        self.fnames = {'dossier':'skope_dossier.json','inventory':'inventory.json',
                      'queue':'projection_queue_14_langues.json','report':'RAPPORT_AUTO.json',
                      'xml_manifest':'wikipedia_extract/manifest.json'}
        for label,fname in self.fnames.items():
            jwrite(self.work / fname,self.dossier)
        hashes={k:s6.sha((self.work / v).read_bytes()) for k,v in self.fnames.items()}
        self.m = {'format':s6.STAGE4,'branch':s6.BRANCH,'one_branch_kristal':True,
                  'public_release_authorized':False,'canonical_assertions_approved':0,
                  'canonical_kristal_built':False,'concept_count':41,'candidate_qids':36,
                  'skos_observed_edge_count':234,'cross_branch_link_count':112,
                  'languages_planned':list(s6.LOCALES),'projection_slots':574,
                  'missing_candidate_qids':self.missing, 'source_sha256':hashes}
        jwrite(self.work / 'semantic_stage_v4' / 'manifest.json', self.m)
        self.v5 = {'profile':s6.STAGE5,'branch':s6.BRANCH,'one_branch_kristal':True,
                   'not_canonical':True,'publication_authorized':False,'unreviewed_ai_proposals':True,
                   'canonical_assertions_minted':0,'source_dossier_sha256':hashes['dossier'],
                   'proposed_count':85,'proposals':self.proposals}
        self.v5_path = self.work / 'semantic_stage_v5/candidats_chatgpt_reception_kristalizer.json'
        jwrite(self.v5_path,self.v5)
        self.original_dossier_sha = s6.EXPECTED_DOSSIER_SHA
        self.original_v5_sha = s6.EXPECTED_STAGE5_SHA_NORMALIZED
        s6.EXPECTED_DOSSIER_SHA = hashes['dossier']
        s6.EXPECTED_STAGE5_SHA_NORMALIZED = s6.sha(self.v5_path.read_bytes())

    # Keep monkeypatches isolated across test cases.
    def _restore(self):
        s6.EXPECTED_DOSSIER_SHA=self.original_dossier_sha
        s6.EXPECTED_STAGE5_SHA_NORMALIZED=self.original_v5_sha

    def test_built_structure(self):
        try:
            files,report=s6.build(self.work)
            self.assertEqual(report['concepts'],41)
            self.assertEqual(report['ai_proposals'],85)
            self.assertEqual(report['skos_observations'],234)
            self.assertEqual(report['cross_branch_skos_observations'],112)
            self.assertEqual(report['concept10_ai_proposals'],4)
            self.assertFalse(report['canonical_kristal_built'])
            graph=json.loads(files['graphe_candidat_prive.json'])
            self.assertTrue(graph['one_branch_kristal'])
            self.assertFalse(graph['eligible_for_kit_enable_v11'])
            self.assertEqual(graph['canonical_KQ_KP_KA_KS_created'],0)
        finally:self._restore()

    def test_relaunch_idempotent(self):
        try:
            files,_=s6.build(self.work)
            target=self.work/'semantic_stage_v6'
            self.assertEqual(s6.install(files,target),'NOUVEAU_DOSSIER')
            self.assertEqual(s6.install(files,target),'DEJA_PRESENT_IDENTIQUE')
        finally:self._restore()

    def test_modified_output_blocks_overwrite(self):
        try:
            files,_=s6.build(self.work)
            target=self.work/'semantic_stage_v6'
            s6.install(files,target)
            (target/'REVUE_85_PROPOSITIONS.csv').write_text('tampered')
            with self.assertRaises(s6.Stage6Error):s6.install(files,target)
        finally:self._restore()

    def test_modified_v5_receipt_rejected(self):
        try:
            self.v5_path.write_bytes(self.v5_path.read_bytes()+b' ')
            with self.assertRaisesRegex(s6.Stage6Error,'réception Kristalizer|Réception Kristalizer'):
                s6.build(self.work)
        finally:self._restore()

    def test_windows_crlf_output_is_accepted(self):
        try:
            data=self.v5_path.read_bytes().replace(b'\n',b'\r\n')
            self.v5_path.write_bytes(data)
            self.assertEqual(s6.build(self.work)[1]['ai_proposals'],85)
        finally:self._restore()

    def test_source_sha_drift_rejected(self):
        try:
            (self.work/'inventory.json').write_bytes(b'{}')
            with self.assertRaisesRegex(s6.Stage6Error,'Empreinte source'):
                s6.build(self.work)
        finally:self._restore()

    def test_wikipedia_text_drift_rejected(self):
        try:
            (self.work/'wikipedia_extract/page-10000.wikitext.txt').write_bytes(b'tampered')
            with self.assertRaisesRegex(s6.Stage6Error,'Wikipédia local modifié'):
                s6.build(self.work)
        finally:self._restore()

    def test_redirect_rejected(self):
        try:
            path=self.work/'semantic_stage_v4/cards/concept10.json'
            card=json.loads(path.read_text(encoding='utf8'))
            card['wikipedia_en'][0]['is_redirect']=True
            jwrite(path,card)
            with self.assertRaisesRegex(s6.Stage6Error,'Contexte Wikipédia non admissible'):
                s6.build(self.work)
        finally:self._restore()

    def test_canonical_mint_rejected(self):
        try:
            path=self.work/'semantic_stage_v4/cards/concept10.json'
            card=json.loads(path.read_text(encoding='utf8'))
            card['canonical_KQ']='KQ77'
            jwrite(path,card)
            with self.assertRaisesRegex(s6.Stage6Error,'Fiche dangereuse'):
                s6.build(self.work)
        finally:self._restore()

    def test_prevent_git_output(self):
        try:
            (Path(self.tmp.name)/'.git').mkdir()
            with self.assertRaisesRegex(s6.Stage6Error,'Git interdit'):
                s6.safe_work(self.work,self.work/'semantic_stage_v6')
        finally:self._restore()

    def test_missing_source_rejected(self):
        try:
            (self.work/'skope_dossier.json').unlink()
            with self.assertRaises(s6.Stage6Error):s6.build(self.work)
        finally:self._restore()

if __name__ == '__main__':
    unittest.main()
