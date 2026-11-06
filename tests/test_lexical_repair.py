"""v0.3: repair diagnosed UniMorph archive formats without touching completed sources."""
import csv
import importlib.util
import json
import lzma
import sqlite3
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location('lexidx_v03',ROOT/'tools/dictionary-harvester/lexical_indexer.py')
idx=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(idx)
RECOVERABLE={
 'slk':{'slk-main/slk.xz': lzma.compress('ísť\tídem\tV;PRS;1;SG\n'.encode())},
 'fin':{'fin-master/fin.1':'talo\ttaloissa\tN;INE;PL\n','fin-master/fin.2':'kala\tkaloja\tN;PTV;PL\n','fin-master/fin.1.args':'not-a-normal-paradigm'},
 'olo':{'olo-master/olo-new-written-livvic':'kala\tkalan\tN;GEN;SG\n','olo-master/olo-kondushi':'a\tb\tV;PRS\n'},
 'ckb':{'ckb-master/arab/ckb-arab-large.tsv':'دوو\tدووان\tN;PL\n','ckb-master/latn/ckb-latn-large.tsv':'du\tduan\tN;PL\n','ckb-master/arab/ckb-arab-large.train':'DUP\tDUP\tN;SG\n'},
 'vep':{'vep-master/vep-northern-veps':'kala\tkalaks\tN;TRA\n'},
 'pbs':{'pbs-main/pbs.csv':'toho1ʔo,toho1ʔomʔ,V;FIN;REAL;IPFV;1;SG\n'},
 'lud':{'lud-master/lud-southern-ludian':'kala\tkaloi\tN;PL\n'},
 'sdh':{'sdh-main/sdh':'xwardin\txwem\tV;PRS;1;SG\n'},
}
EMPTY='pib oss zxx pqm pnb epo mon grn'.split()

class TargetedRepair(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory(prefix='ency-repair-')
  self.root=Path(self.temp.name)
  for name in ('10_sources/lexical','20_evidence','30_working','50_mediatheque'):
   (self.root/name).mkdir(parents=True,exist_ok=True)
  self.zips=self.root/'10_sources/lexical/unimorph/repos'
  self.zips.mkdir(parents=True)
  for edition,files in RECOVERABLE.items():
   with zipfile.ZipFile(self.zips/(edition+'.zip'),'w',zipfile.ZIP_DEFLATED) as zf:
    for name,value in files.items():zf.writestr(name,value)
  for edition in EMPTY:
   with zipfile.ZipFile(self.zips/(edition+'.zip'),'w',zipfile.ZIP_DEFLATED) as zf:
    zf.writestr(edition+'-main/README.md','No paradigms here.')
  self.db=self.root/idx.SUBDIR/'lexical.sqlite3'
  con=idx.connect(self.db)
  for info in idx.source_candidates(self.root):
   con.execute("INSERT INTO source_files(relative_path,kind,edition,size_bytes,mtime_ns,status,started_at) VALUES (?,?,?,?,?,'no_data','prior-run')",
              (info['relative'],info['kind'],info['edition'],info['size'],info['mtime']))
  # completed source must stay untouched even though it is a supported ZIP
  extra=self.zips/'fra.zip'
  with zipfile.ZipFile(extra,'w') as z:z.writestr('fra-main/fra','avion\tavions\tN;PL\n')
  info=next(x for x in idx.source_candidates(self.root) if x['edition']=='fra')
  con.execute("INSERT INTO source_files(relative_path,kind,edition,size_bytes,mtime_ns,status,cursor_lines,accepted,started_at) VALUES (?,?,?,?,?,'complete',997,997,'prior-run')",
              (info['relative'],info['kind'],info['edition'],info['size'],info['mtime']))
  con.commit();con.close()
 def tearDown(self):self.temp.cleanup()
 def run_repair(self,extra=None):
  return idx.main(['repair','--data-root',str(self.root),'--min-free-gb','0']+(extra or []))
 def test_formats_selection(self):
  for name in RECOVERABLE:
   with zipfile.ZipFile(self.zips/(name+'.zip')) as zip_:
    members=idx.unimorph_members(zip_,name)
    self.assertTrue(members,name)
  for name in EMPTY:
   with zipfile.ZipFile(self.zips/(name+'.zip')) as zip_:
    self.assertFalse(idx.unimorph_members(zip_,name))
 def test_repair_only_no_data_and_preserve_sources(self):
  before={p.name:p.read_bytes() for p in self.zips.glob('*.zip')}
  self.assertEqual(self.run_repair(),0)
  con=sqlite3.connect(self.db)
  states=dict(con.execute("SELECT edition,status FROM source_files"))
  self.assertTrue(all(states[x]=='complete' for x in RECOVERABLE))
  self.assertTrue(all(states[x]=='no_data' for x in EMPTY))
  self.assertEqual(states['fra'],'complete')
  self.assertEqual(con.execute("SELECT cursor_lines FROM source_files WHERE edition='fra'").fetchone()[0],997)
  # fin 2 paradigms, ckb 2 writing systems, no train/args
  self.assertEqual(con.execute("SELECT accepted FROM source_files WHERE edition='fin'").fetchone()[0],2)
  self.assertEqual(con.execute("SELECT accepted FROM source_files WHERE edition='ckb'").fetchone()[0],2)
  self.assertEqual(con.execute("SELECT accepted FROM source_files WHERE edition='pbs'").fetchone()[0],1)
  self.assertEqual(con.execute('SELECT COUNT(*) FROM entries').fetchone()[0],11)
  self.assertEqual(con.execute("SELECT COUNT(*) FROM source_members WHERE source_id=(SELECT id FROM source_files WHERE edition='fin')").fetchone()[0],2)
  con.close()
  self.assertEqual(before,{p.name:p.read_bytes() for p in self.zips.glob('*.zip')})
  self.assertEqual(self.run_repair(),0)
  con=sqlite3.connect(self.db)
  self.assertEqual(con.execute('SELECT COUNT(*) FROM entries').fetchone()[0],11)
  con.close()
  snapshot=json.loads((self.db.parent/'latest.json').read_text())
  self.assertEqual(snapshot['sources_by_status']['no_data'],len(EMPTY))
  self.assertFalse(snapshot['published'])
  self.assertFalse(snapshot['canonical_dictionary'])
  with open(self.db.parent/'source_members.csv',encoding='utf-8-sig') as stream:
   self.assertEqual(len(list(csv.DictReader(stream))),11)
 def test_repair_resume_after_pilot(self):
  self.assertEqual(self.run_repair(['--max-lines-per-source','1']),0)
  con=sqlite3.connect(self.db)
  self.assertTrue(con.execute("SELECT COUNT(*) FROM source_files WHERE status='partial'").fetchone()[0]>0)
  con.close()
  self.assertEqual(self.run_repair(),0)
  con=sqlite3.connect(self.db)
  self.assertEqual(con.execute('SELECT COUNT(*) FROM entries').fetchone()[0],11)
  con.close()

if __name__=='__main__':unittest.main()
