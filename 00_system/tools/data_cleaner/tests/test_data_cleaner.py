from pathlib import Path
from importlib.machinery import SourceFileLoader
import importlib.util
import tempfile
import hashlib
import unittest
import sys

path=Path(__file__).resolve().parents[1]/'core.py'
spec=importlib.util.spec_from_loader('encyk_safe_cleaner',SourceFileLoader('encyk_safe_cleaner',str(path)))
mod=importlib.util.module_from_spec(spec);sys.modules[spec.name]=mod;spec.loader.exec_module(mod)

class TestProtectWikidata(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)/'Ddata';self.root.mkdir()
  for n in ['10_sources','30_working','40_kristal','50_mediatheque']:(self.root/n).mkdir()
  self.expected={k:(k+' contents').encode() for k in mod.KNOWN_INGEST}
  self.old_known=mod.KNOWN_INGEST
  mod.KNOWN_INGEST={k:hashlib.sha256(v).hexdigest() for k,v in self.expected.items()}
  for name,payload in self.expected.items():
   a=self.root/'20_ingest'/name;a.parent.mkdir(parents=True,exist_ok=True);a.write_bytes(payload)
   b=self.root/'20_evidence/legacy-ingest'/name;b.parent.mkdir(parents=True,exist_ok=True);b.write_bytes(payload)
  self.works=self.root/'50_mediatheque/catalog/candidates/wikidata/pilot/works.jsonl'
  self.works.parent.mkdir(parents=True);self.works.write_bytes(b'533 structured works')
  self.dump=self.root/'10_sources/wikidata.json.bz2';self.dump.write_bytes(b'dump')
  self.db=self.root/'30_working/wikidata.compact.sqlite';self.db.write_bytes(b'big sqlite')
  self.important=[self.works,self.dump,self.db,self.root/'20_ingest/daat-handoff/catholic-intellectual-pilot/latest.json',self.root/'20_ingest/scope-snapshots/catholic-intellectual-pilot/wikidata-60c195a8624fc3ccaa1c/entities.wikidata.jsonl.gz']
  self.hashes={k:k.read_bytes() for k in self.important}
 def tearDown(self):
  mod.KNOWN_INGEST=self.old_known
  self.temp.cleanup()
 def test_audit_read_only_and_no_originals_deleted(self):
  a,alerts=mod.make_plan(self.root)
  self.assertEqual((sum(x.kind=='move' for x in a),sum(x.kind=='duplicate' for x in a)),(4,12))
  self.assertTrue(all(act.source.parts[-1] for act in a))
  for k,v in self.hashes.items():self.assertEqual(k.read_bytes(),v)
  self.assertEqual(alerts,[])
 def test_execute_preserves_wikidata(self):
  res=mod.apply_plan(self.root,confirm=True)
  self.assertEqual((res['moved'],res['deleted_exact_duplicates']),(4,12))
  self.assertFalse((self.root/'20_evidence/legacy-ingest').exists())
  for f,v in self.hashes.items():self.assertEqual(f.read_bytes(),v)
  for rel in mod.ACTIVE_DEST:
   self.assertFalse((self.root/'20_ingest'/rel).exists())
   self.assertEqual((self.root/mod.ACTIVE_DEST[rel]).read_bytes(),self.expected[rel])
  self.assertEqual(mod.apply_plan(self.root,confirm=True)['deleted_exact_duplicates'],0)
 def test_no_original_then_duplicate_preserved(self):
  f=self.root/'20_ingest/scope-snapshots/catholic-intellectual-pilot/wikidata-60c195a8624fc3ccaa1c/entities.wikidata.jsonl.gz'
  copied=self.root/'20_evidence/legacy-ingest/scope-snapshots/catholic-intellectual-pilot/wikidata-60c195a8624fc3ccaa1c/entities.wikidata.jsonl.gz'
  f.unlink()
  a,alerts=mod.make_plan(self.root)
  self.assertFalse(any(x.source==copied for x in a))
  self.assertTrue(any('seul exemplaire' in x for x in alerts))
  mod.apply_plan(self.root,confirm=True)
  self.assertTrue(copied.exists())
 def test_no_deletion_of_modified_file(self):
  f=self.root/'20_evidence/legacy-ingest/README.md';f.write_bytes(b'not match')
  a,alerts=mod.make_plan(self.root)
  self.assertFalse(any(x.source==f for x in a))
  self.assertTrue(any('non reconnue' in x or 'modifiée' in x for x in alerts))
  mod.apply_plan(self.root,confirm=True)
  self.assertTrue(f.exists())
 def test_reject_without_confirmation(self):
  with self.assertRaises(mod.UnsafeOperation):mod.apply_plan(self.root)
 def test_conflicting_destination_prevents_changes(self):
  f=self.root/mod.ACTIVE_DEST['manifests/wikidata-dump-verified.json']
  f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes(b'conflict')
  with self.assertRaises(mod.UnsafeOperation):mod.apply_plan(self.root,confirm=True)
  self.assertTrue((self.root/'20_ingest/checkpoints/wikidata-index-state.json').exists())
 def test_symlink_prevents_operation(self):
  # malformed link under older copied tree
  p=self.root/'20_evidence/legacy-ingest/provenance/bootstrap.sources.json'
  p.unlink()
  external=Path(self.temp.name)/'external';external.write_bytes(b'outside')
  try:p.symlink_to(external)
  except OSError:self.skipTest('unavailable')
  with self.assertRaises(mod.UnsafeOperation):mod.make_plan(self.root)
 def test_never_allow_deletion_of_wikidata_output_in_apply(self):
  f=self.root/'20_ingest/scope-snapshots/catholic-intellectual-pilot/wikidata-60c195a8624fc3ccaa1c/entities.wikidata.jsonl.gz'
  with self.assertRaises(mod.UnsafeOperation):
   mod._protected_action(mod.Action('duplicate',f,None,mod.KNOWN_INGEST[f.relative_to(self.root/'20_ingest').as_posix()],'fake'),self.root)
 def test_junction_or_code_root_rejected(self):
  (self.root/'.git').mkdir()
  with self.assertRaises(mod.UnsafeOperation):mod.make_plan(self.root)

if __name__=='__main__': unittest.main(verbosity=2)
