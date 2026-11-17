"""Only offline, private, reviewed-source visualizations may be constructed."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from spek.core import ValidationError
from spek.structural_preview import create_structural_preview, load_preview_contracts

REPO=Path(__file__).resolve().parents[1]


class StructuralPreviewTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.folder=Path(self.tmp.name)/'Kristal-Test'
        self.folder.mkdir()
        self.state_dir=self.folder/'.kristal'/'v8'
        self.state_dir.mkdir(parents=True)
        state={'schema_version':'6.0','artifact_type':'kristal_state','assertions':[
            {'assertion_id':'urn:assertion:test:1','statement':{'subject':{'kind':'item','id':'<script>alert(1)</script>'},'predicate':'test:has','object':{'kind':'item','id':'urn:object:a'}},'evidence_refs':['urn:evidence:1']},
            {'assertion_id':'urn:assertion:test:2','statement':{'subject':{'kind':'item','id':'urn:subject:b'},'predicate':'test:is','object':{'kind':'item','id':'urn:object:b'}},'evidence_refs':[]},
        ]}
        self.state_file=self.state_dir/'portable-state.kristal-state.json'
        raw=json.dumps(state).encode()
        self.state_file.write_bytes(raw)
        review={'source':{'portable_state_relative_path':'.kristal/v8/portable-state.kristal-state.json',
                          'portable_state_raw_sha256':hashlib.sha256(raw).hexdigest(),'assertion_occurrences':2},
                'ordered_structural_sections':[
                    {'section_id':'first','heading':'Relations','planned_template_id':'relation-network','editorial_intent':'Test',
                     'source_observation':{'source_positions_zero_based':[0]}},
                    {'section_id':'other','heading':'Données','planned_template_id':'double-entry-ledger','editorial_intent':'Test',
                     'source_observation':{'source_positions_zero_based':[1]}},
                ],'exclusions_and_risks':['Ne pas inventer de causalité']}
        self.info={'identity':'test','title':'Test','proposal':{'status':'AI_PROPOSED'},'structure_review':review}

    def test_explicit_19_contracts(self):
        contracts=load_preview_contracts(REPO)
        self.assertEqual(len(contracts),19)
        self.assertEqual(contracts['double-entry-ledger']['preview_kind'],'ledger')
        self.assertEqual(contracts['taxonomy-tree']['preview_kind'],'taxonomy')

    def test_generated_page_is_private_and_escaped(self):
        with patch('spek.structural_preview.inspect_kristal',return_value=self.info):
            out=create_structural_preview(REPO,self.folder)
        self.assertEqual(out['status'],'PRIVATE_SOURCE_AUDIT_NOT_PUBLISHABLE')
        p=Path(out['page'])
        html=p.read_text(encoding='utf-8')
        self.assertIn('Relations',html)
        self.assertIn('Matrice journaux, comptes', html)
        self.assertNotIn('&lt;script&gt;alert(1)&lt;/script&gt;',html)
        self.assertNotIn('<script>alert(1)</script>',html)
        self.assertIn('Plan documentaire privé',html)
        self.assertIn('Texte en attente de réalisation SemantiK',html)
        self.assertNotIn(self.info['structure_review']['source']['portable_state_raw_sha256'],html)
        self.assertNotIn('urn:subject:b',html)
        self.assertNotIn('test:has',html)
        self.assertNotIn('urn:object:a',html)
        self.assertNotIn('urn:assertion:test:1',html)
        self.assertNotIn('urn:evidence:1',html)
        self.assertNotIn('Position #',html)
        self.assertIn('#1e6864',html)
        self.assertIn('class="brand-mark"',html)
        self.assertNotIn('RuntimeSet qualifié',html)
        man=json.loads((p.parent/'inspection-manifest.json').read_text())
        self.assertFalse(man['publication_eligible'])
        self.assertFalse(man['semantik_realized'])
        self.assertNotIn('source_raw_sha256',man)
        self.assertEqual(sum(x['observed_occurrences'] for x in man['sections']),2)

    def test_changed_source_is_blocked(self):
        self.state_file.write_text(self.state_file.read_text()+' ',encoding='utf-8')
        with patch('spek.structural_preview.inspect_kristal',return_value=self.info):
            with self.assertRaisesRegex(ValidationError,'source locale diffère'):
                create_structural_preview(REPO,self.folder)

    def test_missing_review_is_blocked(self):
        info={**self.info,'structure_review':None}
        with patch('spek.structural_preview.inspect_kristal',return_value=info):
            with self.assertRaisesRegex(ValidationError,'Aucune revue'):
                create_structural_preview(REPO,self.folder)

    def test_symlink_source_is_blocked(self):
        self.state_file.unlink()
        other=Path(self.tmp.name)/'outside'
        other.write_text('{}')
        self.state_file.symlink_to(other)
        with patch('spek.structural_preview.inspect_kristal',return_value=self.info):
            with self.assertRaisesRegex(ValidationError,'symbolique'):
                create_structural_preview(REPO,self.folder)

    def test_target_cannot_be_under_source(self):
        with patch('spek.structural_preview.inspect_kristal',return_value=self.info):
            with self.assertRaisesRegex(ValidationError,'ne peut pas'):
                create_structural_preview(REPO,self.folder,output=self.folder/'preview')


if __name__ == '__main__':
    unittest.main()
