"""Safety and integration tests for the additive UNESCO V22 overlay.

Optional realistic test fixture: set UNESCO_V22_TEST_WORK to the folder
containing the V19 atlas, V18 report and original lot-002 V21 ZIP.
"""
from __future__ import annotations

from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools' / 'unesco_pilot'))
import overlay_ia_v22 as v22


class OverlayV22Tests(unittest.TestCase):
    def test_payload_integrity(self):
        self.assertEqual(len(v22.verify_payload()['files_sha256']), 9)

    def test_review_contract_and_counts(self):
        j = v22.load_json(v22.PAYLOAD / 'DECISIONS_IA_44_V22.json')
        self.assertEqual(len(j['records']), 44)
        self.assertEqual(Counter(x['decision'] for x in j['records']), v22.EXPECTED)
        self.assertFalse(j['canonical_admission_authorized'])
        self.assertFalse(j['publication_authorized'])
        self.assertTrue(all(x['canonical_admission_authorized'] is False for x in j['records']))

    def test_mapping_correction_has_existing_concept(self):
        d = {x['unesco_id'] for x in v22.load_json(v22.PAYLOAD / 'UNESCO_2026_REFERENTIEL.json')['concepts']}
        self.assertEqual(len(d), 41)
        self.assertEqual(v22.MAPPING_CORRECT, {'LOT002-V21-018': 'concept11264'})
        self.assertTrue(set(v22.MAPPING_CORRECT.values()).issubset(d))

    def test_revisions_are_not_automatically_canonical(self):
        source = v22.load_json(v22.PAYLOAD / 'DECISIONS_IA_44_V22.json')['records']
        self.assertTrue(all(x['source_capture_status'] == 'NOT_CAPTURED' for x in source))
        self.assertTrue(all(x['canonical_ka_id'] is None for x in source))

    def test_missing_payload_is_refused(self):
        # Files are hash pinned; a harmless temporary copy of the original bytes
        # with a one-byte change must be detectable before any write.
        from unittest.mock import patch
        old = v22.PAYLOAD
        with tempfile.TemporaryDirectory() as t:
            path = Path(t)
            for f in old.iterdir():
                if f.is_file(): shutil.copyfile(f, path / f.name)
            candidate = path / 'R2_SOURCES_ORIGINE.json'
            candidate.write_bytes(candidate.read_bytes() + b' ')
            with patch.object(v22, 'PAYLOAD', path):
                with self.assertRaises(v22.Refus): v22.verify_payload()

    @unittest.skipUnless(os.environ.get('UNESCO_V22_TEST_WORK'), 'Dossier de fixture UNESCO non fourni')
    def test_real_snapshot_replay_and_tamper_detection(self):
        original = Path(os.environ['UNESCO_V22_TEST_WORK'])
        with tempfile.TemporaryDirectory() as t:
            work = Path(t)
            names = [v22.LOT_NAME,
                     'atlas_documentaire_v19/ancrages_kristal_stables.json',
                     'semantic_stage_v18_framework_quarantine/RAPPORT_V18.json']
            for rel in names:
                p = work / rel
                p.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(original / rel, p)
            baseline = {rel: hashlib.sha256((work / rel).read_bytes()).hexdigest() for rel in names}
            ctx = v22.load_and_validate(work, work / v22.LOT_NAME)
            files = v22.build_files(ctx)
            self.assertEqual(len(files), 54)
            self.assertEqual(v22.apply(work, ctx, files)['status'], 'V22_CORRECTIONS_APPLIQUEES_PRIVÉES')
            self.assertEqual(v22.apply(work, ctx, files)['status'], 'DEJA_INSTALLE_IDENTIQUE')
            stage = work / v22.OUT_NAME
            for rel in names:
                self.assertEqual(hashlib.sha256((work / rel).read_bytes()).hexdigest(),baseline[rel])
            self.assertEqual(len(list((stage / 'reader_en').glob('concept*.html'))), 41)
            self.assertEqual(len(list((work / v22.LEDGER_NAME).glob('*.json'))), 1)
            for rel, count in [('R2_19_APPROBATIONS_IA_NON_CANONIQUES.jsonl',19),
                               ('LOT_002_25_REVUES_IA_NON_CANONIQUES.jsonl',25)]:
                lines = (stage / rel).read_text(encoding='utf-8').splitlines()
                self.assertEqual(len(lines),count)
                self.assertTrue(all(isinstance(json.loads(x),dict) for x in lines))
            data = json.loads((stage / 'REGISTRE_44_REVU_IA_V22.json').read_text(encoding='utf-8'))
            self.assertEqual(sum(x['review_state'] == 'APPROUVE_IA_NON_CANONIQUE_PREUVES_A_ARCHIVER' for x in data['records']),36)
            corrected = next(x for x in data['records'] if x['proposal_id']=='LOT002-V21-018')
            self.assertEqual(corrected['effective_unesco_id'], 'concept11264')
            self.assertEqual(corrected['provisional_kq_id'], 'KQ38')
            p = stage / 'RAPPORT_V22.json'
            p.write_text('{}',encoding='utf-8')
            with self.assertRaises(v22.Refus): v22.apply(work,ctx,files)
            self.assertEqual(hashlib.sha256((work / names[0]).read_bytes()).hexdigest(),baseline[names[0]])


if __name__ == '__main__':
    unittest.main()
