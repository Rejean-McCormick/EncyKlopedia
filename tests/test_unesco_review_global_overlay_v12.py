"""Regression tests for unsigned UNESCO stage-12 code overlay (no network)."""
from __future__ import annotations
import copy
import importlib.util
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
import zipfile

SCRIPT=Path(__file__).resolve().parents[1]/'tools'/'unesco_pilot'/'review_global_overlay_v12.py'
SPEC=importlib.util.spec_from_file_location('unesco_review_overlay_v12',SCRIPT)
MOD=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MOD)

class ReviewOverlayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest,cls.payload=MOD.load_payload()
        cls.tables={
            'identities': MOD.unique_key(MOD.rows_bytes(cls.payload['REVUE_41_IDENTITES_NON_SIGNEE.csv']),'unesco_id',41,'identity'),
            'proposals': {},'relations':{},'sources':{},
        }
        for row in MOD.rows_bytes(cls.payload['REVUE_85_PROPOSITIONS_NON_SIGNEE.csv']):
            cls.tables['proposals'][row['proposal_ref']]={
                'unesco_id':row['unesco_id'],'statement_en':row['texte_original_en'],
                'review_preavis':row['prior_original']}
        for key,row in cls.tables['identities'].items():
            cls.tables['identities'][key]={
                'label_en':row['label_en'],'unesco_uri':row['unesco_uri'],'qid_candidat':row['qid_candidat']}
        for row in MOD.rows_bytes(cls.payload['REVUE_61_RELATIONS_SKOS_NON_SIGNEE.csv']):
            cls.tables['relations'][row['group_ref']]={
                'source_ou_membre_a':row['source_id'],'cible_ou_membre_b':row['target_id'],
                'relation_normalisee':row['relation_skos'],'observations_reciproques':row['observations_reciproques']}
        for row in MOD.rows_bytes(cls.payload['REVUE_81_PISTES_DE_SOURCES_NON_KS.csv']):
            cls.tables['sources'][row['reference_id']]={'url':row['url'],'document_type':row['genre']}

    def test_original_payload_all_verified(self):
        self.assertEqual(len(self.manifest['files_sha256']),52)

    def test_semantic_keys_all_crosscheck(self):
        proposals,idents,relations,sources=MOD.verify_semantics(self.payload,self.tables)
        self.assertEqual(tuple(map(len,(proposals,idents,relations,sources))),(85,41,61,81))

    def test_single_modified_proposal_anchor_blocks(self):
        tables=copy.deepcopy(self.tables)
        first=next(iter(tables['proposals']))
        tables['proposals'][first]['statement_en']='Mauvaise substitution'
        with self.assertRaises(MOD.ReviewError):MOD.verify_semantics(self.payload,tables)

    def test_wrong_identity_qid_blocks(self):
        tables=copy.deepcopy(self.tables)
        tables['identities']['concept10']['qid_candidat']='Q0'
        with self.assertRaises(MOD.ReviewError):MOD.verify_semantics(self.payload,tables)

    def test_wrong_relation_blocks(self):
        tables=copy.deepcopy(self.tables)
        first=next(iter(tables['relations']))
        tables['relations'][first]['relation_normalisee']='narrower'
        with self.assertRaises(MOD.ReviewError):MOD.verify_semantics(self.payload,tables)

    def test_wrong_source_url_blocks(self):
        tables=copy.deepcopy(self.tables)
        first=next(iter(tables['sources']))
        tables['sources'][first]['url']='https://example.invalid'
        with self.assertRaises(MOD.ReviewError):MOD.verify_semantics(self.payload,tables)

    def test_no_unsafe_path(self):
        for candidate in ('../a','/absolute','C:/windows',r'a\\b','x/../y'):
            with self.subTest(path=candidate),self.assertRaises(MOD.ReviewError):
                MOD.safe_relative(candidate)

    def test_new_install_then_idempotent(self):
        with tempfile.TemporaryDirectory() as td:
            dest=Path(td)/'private'
            data={'FICHES_41/concept10.md':b'test','REVIEW.json':b'{"not_canonical":true}'}
            one,count=MOD.publish_new_files(dest,data,check_only=False)
            self.assertEqual(one,'INSTALLE');self.assertEqual(count,0)
            mark=(dest/'REVIEW.json').stat().st_mtime_ns
            two,count=MOD.publish_new_files(dest,data,check_only=False)
            self.assertEqual((two,count),('DEJA_PRESENT',2))
            self.assertEqual(mark,(dest/'REVIEW.json').stat().st_mtime_ns)

    def test_existing_review_is_completed_without_overwrite(self):
        with tempfile.TemporaryDirectory() as td:
            dest=Path(td)
            (dest/'FICHES_41').mkdir()
            (dest/'FICHES_41'/'concept10.md').write_bytes(b'original')
            action,n=MOD.publish_new_files(dest,{'FICHES_41/concept10.md':b'original','NEW.json':b'{}'},check_only=False)
            self.assertEqual(n,1);self.assertTrue((dest/'NEW.json').exists())
            self.assertEqual((dest/'FICHES_41'/'concept10.md').read_bytes(),b'original')

    def test_changed_review_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            dest=Path(td);(dest/'REVIEW.json').write_bytes(b'MODIFIE')
            with self.assertRaises(MOD.ReviewError):
                MOD.publish_new_files(dest,{'REVIEW.json':b'ORIGINAL'},check_only=False)
            self.assertEqual((dest/'REVIEW.json').read_bytes(),b'MODIFIE')

    def test_dry_run_creates_nothing(self):
        with tempfile.TemporaryDirectory() as td:
            dest=Path(td)/'absent'
            action,_=MOD.publish_new_files(dest,{'REPORT.json':b'{}'},check_only=True)
            self.assertEqual(action,'VERIFICATION_SANS_ECRITURE')
            self.assertFalse(dest.exists())

    def test_bundled_file_tamper_blocks(self):
        with tempfile.TemporaryDirectory() as td:
            dest=Path(td)/'tamper.zip'
            with zipfile.ZipFile(MOD.RESOURCE) as src,zipfile.ZipFile(dest,'w') as out:
                for name in src.namelist():
                    data=src.read(name)
                    if name=='REVUE_85_PROPOSITIONS_NON_SIGNEE.csv':data+=b'alteration'
                    out.writestr(name,data)
            with self.assertRaises(MOD.ReviewError):MOD.load_payload(dest)

    def test_handoff_includes_no_canonical_ids(self):
        rows,_,_,_=MOD.verify_semantics(self.payload,self.tables)
        sample={'immutable_files_sha256':{'x':'a'}}
        handoff=MOD.handoff_payload(rows,self.manifest,sample,'d'*64)
        self.assertEqual(len(handoff['proposals']),85)
        self.assertFalse(handoff['canon_admission_authorized'])
        for r in handoff['proposals']:
            self.assertIsNone(r['canonical_KQ']);self.assertIsNone(r['canonical_KP'])
            self.assertIsNone(r['canonical_KA']);self.assertEqual(r['canonical_KS'],[])

if __name__=='__main__':unittest.main()
