"""Offline tests of append-only ChatGPT documentary candidate handoff."""
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/'tools/unesco_pilot/recevoir_lots_atlas_v19.py'
SPEC=importlib.util.spec_from_file_location('atlas_intake_v19',SCRIPT)
M=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(M)


class IntakeTest(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup)
        self.root=Path(tmp.name);self.zip=self.root/'lot.zip';self.doc=self.root/'proposals.json';self.ledger=self.root/'ledger'
        self.text=b'Education as a right is a sample text for verification.'
        item={'page_id':42,'title':'Right to education','text_relative_path':'articles/page-42.wikitext.txt',
              'text_sha256':M.sha(self.text),'status':'TEXT_EXTRACTED','text_revision_id':'101'}
        manifest={'format':'koa.unesco-wikipedia-chatgpt-research-batch/1.0','branch':'unesco-mt1-10',
                  'items':[item]}
        self.raw=M.jb(manifest)
        self.anchors=M.jb({'branch':'unesco-mt1-10',
            'anchors':[{'unesco_id':'concept10' if i==0 else f'concept{i+1000}'} for i in range(41)]})
        with zipfile.ZipFile(self.zip,'w') as z:
            z.writestr('LOT_MANIFEST.json',self.raw)
            z.writestr('articles/page-42.wikitext.txt',self.text)
            z.writestr('atlas/ancrages_kristal_stables.json',self.anchors)
        self.data={'format':M.FORMAT,'branch':'unesco-mt1-10','batch_manifest_sha256':M.sha(self.raw),
                   'proposals':[{'candidate_id':'test_01','unesco_id':'concept10','source_page_id':42,
                                 'source_revision_id':'101','source_locator':'Introduction',
                                 'statement':'Education may be studied as a right depending on law.'}]}
        self.doc.write_bytes(M.jb(self.data))

    def test_intake_idempotent_and_read_only_batch(self):
        source=self.zip.read_bytes()
        self.assertEqual(M.main(['intake','--batch',str(self.zip),'--proposals',str(self.doc),
                                 '--ledger',str(self.ledger)]),0)
        self.assertEqual(M.main(['intake','--batch',str(self.zip),'--proposals',str(self.doc),
                                 '--ledger',str(self.ledger)]),0)
        self.assertEqual(len(list(self.ledger.glob('*.json'))),1)
        self.assertEqual(M.main(['report','--ledger',str(self.ledger)]),0)
        self.assertEqual(self.zip.read_bytes(),source)

    def test_bad_revision_blocked(self):
        self.data['proposals'][0]['source_revision_id']='other'
        self.doc.write_bytes(M.jb(self.data))
        self.assertEqual(M.main(['intake','--batch',str(self.zip),'--proposals',str(self.doc),
                                 '--ledger',str(self.ledger)]),2)
        self.assertFalse(self.ledger.exists())

    def test_bad_anchor_blocked(self):
        self.data['proposals'][0]['unesco_id']='Q69370'
        self.doc.write_bytes(M.jb(self.data))
        self.assertEqual(M.main(['intake','--batch',str(self.zip),'--proposals',str(self.doc),
                                 '--ledger',str(self.ledger)]),2)

    def test_claim_cannot_attach_to_missing_text(self):
        self.data['proposals'][0]['source_page_id']=99
        self.doc.write_bytes(M.jb(self.data))
        self.assertEqual(M.main(['intake','--batch',str(self.zip),'--proposals',str(self.doc),
                                 '--ledger',str(self.ledger)]),2)

    def test_tamper_lot_blocked(self):
        with zipfile.ZipFile(self.zip,'w') as z:
            z.writestr('LOT_MANIFEST.json',self.raw)
            z.writestr('articles/page-42.wikitext.txt',b'tampered')
            z.writestr('atlas/ancrages_kristal_stables.json',self.anchors)
        self.assertEqual(M.main(['intake','--batch',str(self.zip),'--proposals',str(self.doc),
                                 '--ledger',str(self.ledger)]),2)


if __name__=='__main__':unittest.main()
