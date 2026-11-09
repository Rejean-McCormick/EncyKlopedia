"""Offline v21 manifest verification contract; no D: and no Wikimedia data."""
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

HERE=Path(__file__).resolve().parents[1]
SOURCE=HERE/'tools/unesco_pilot/verifier_overlay_entrepot_v21.py'
spec=importlib.util.spec_from_file_location('verify_v21',SOURCE)
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)

class ManifestTests(unittest.TestCase):
    def test_local_manifest_and_tamper(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); p=root/'EncyKlopedia/EncyKlopedia/HELLO.cmd'
            p.parent.mkdir(parents=True);p.write_bytes(b'hello')
            manifest=root/'local_manifest.json'
            data={'format':module.FMT,'files':{
                'EncyKlopedia/EncyKlopedia/HELLO.cmd':{
                    'bytes':5,'sha256':hashlib.sha256(b'hello').hexdigest()}}}
            manifest.write_text(json.dumps(data))
            self.assertFalse(module.verify(root,manifest)['problems'])
            p.write_bytes(b'hallo')
            self.assertEqual(len(module.verify(root,manifest)['problems']),1)

if __name__=='__main__':unittest.main()
