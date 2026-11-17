"""Regression tests: isolated fixtures, no live production sources."""
import copy,json,sqlite3,subprocess,sys,unittest
from pathlib import Path
from unittest.mock import patch
from zipfile import ZipFile
import test_end_to_end as fixtures
from encyk_v32 import pipeline as p
from encyk_v32.sql import open_work,DDL,OLD_SCHEMA,SCHEMA
from encyk_v32.config import Settings
from encyk_v32.sources import import_unesco,discover,upsert_candidate
from encyk_v32.federation import scan_islands,describe_island

class ReliabilityTests(unittest.TestCase):
 def setUp(self):
  self.t=fixtures.UnifiedTests();self.t.setUp();self.addCleanup(self.t.doCleanups)
  self.db=self.t.db;self.s=self.t.settings
  import_unesco(self.db,self.s.unesco_root);discover(self.db,self.s,graph_enabled=False)
  with self.db:self.db.execute("UPDATE candidates SET state='SELECTED'")
 def count(self,table):return self.db.execute('SELECT count(*) FROM '+table).fetchone()[0]
 def articles(self,j):
  with ZipFile(j['path']) as z:return [json.loads(x) for x in z.read('articles.jsonl').splitlines()]
 def facts(self,j):
  return [dict(page_id=a['page_id'],revision_id=a['revision_id'],subject_key=a['subjects'][0],statement=self.t.pages[a['page_id']][1],predicate='describes',object={'type':'text','value':'event'},source_quote=self.t.pages[a['page_id']][1],source_locator='Intro',concept_ids=a['concept_ids']) for a in self.articles(j)]
 def reply(self,j,facts=None,coverage=None,**kw):
  data={'format':'encyk.enrichment-delta.v32/2','job_id':j['job_id'],'facts':self.facts(j) if facts is None else facts,'source_coverage':coverage if coverage is not None else [{'page_id':a['page_id'],'status':'processed','note':'Article examiné'} for a in self.articles(j)]}
  path=Path(self.t.temp.name)/'response.zip'
  with ZipFile(path,'w') as z:z.writestr('kristal_delta.json',json.dumps(data))
  return p.import_for_job(self.db,path,j['job_id'],**kw)
 def add_candidate(self,concept='concept2',pid=1,priority=100):
  with self.db:
   cid=upsert_candidate(self.db,'unesco.mt1.10',concept,'Q11',{'page_id':pid,'title':'Article','latest_revision':11},'TEST','Q11','test',priority)
   self.db.execute("UPDATE candidates SET state='SELECTED' WHERE candidate_id=?",(cid,))
  return cid
 def test_branch_isolation(self):
  j=p.make_wave(self.db,self.s,'unesco.mt1.10','enrich')[0]
  self.assertEqual({b for a in self.articles(j) for b in a['branches']},{'unesco.mt1.10'})
  self.assertEqual(self.db.execute("SELECT state FROM candidates WHERE branch_id='unesco.mt1.05'").fetchone()[0],'SELECTED')
 def test_empty_review_and_explicit_no_claim(self):
  j=p.make_enrichment(self.db,self.s);r=self.reply(j,[])
  self.assertEqual(r['status'],'REVIEW_REQUIRED')
  ids=[r[0] for r in self.db.execute('SELECT candidate_id FROM candidates')]
  self.assertEqual(dict(self.db.execute('SELECT state,count(*) FROM candidates GROUP BY state')),{'NO_FACTS_REVIEW':2})
  p.retry_candidates(self.db,ids,'Nouvelle vérification de couverture')
  j=p.make_enrichment(self.db,self.s)
  r=self.reply(j,[],[{'page_id':a['page_id'],'status':'no_relevant_claim','note':'Aucun fait pertinent démontré'} for a in self.articles(j)])
  self.assertEqual(r['status'],'DONE_EMPTY')
 def test_context_and_unknown_fields_preserved_exported(self):
  j=p.make_enrichment(self.db,self.s);a=self.facts(j)[0];b=copy.deepcopy(a)
  a['qualifiers']={'period':'2001'};b['qualifiers']={'period':'2010'};b['domain_extra']={'method':'observation'}
  r=self.reply(j,[a,b]);self.assertEqual(r['new_proposals'],2);self.assertTrue(Path(r['archive_path']).is_file())
  path=Path(self.t.temp.name)/'export.jsonl';p.export_proposals(self.db,path)
  rows=[json.loads(x) for x in path.read_text().splitlines()]
  self.assertEqual({x['context']['qualifiers']['period'] for x in rows},{'2001','2010'})
  self.assertTrue(all(x['citations'] and x['occurrences'] for x in rows))
 def test_exact_repeat_and_changed_return_conflict(self):
  j=p.make_enrichment(self.db,self.s);f=self.facts(j);self.reply(j,f)
  self.assertEqual(self.reply(j,f)['status'],'ALREADY_IMPORTED')
  f[0]['statement']='A materially different contextualized statement'
  with self.assertRaisesRegex(ValueError,'RETURN_CONFLICT'):self.reply(j,f)
 def test_correction_preserves_history_invalidates_reuse(self):
  j=p.make_enrichment(self.db,self.s);facts=self.facts(j);self.reply(j,facts)
  old=self.db.execute('SELECT proposal_id FROM proposals WHERE page_id=?',(facts[0]['page_id'],)).fetchone()[0]
  facts[0]['qualifiers']={'period':'2001'};facts[0]['supersedes']=old
  self.assertEqual(self.reply(j,[facts[0]],correction=True)['status'],'CORRECTED')
  self.assertEqual(self.db.execute('SELECT status FROM proposals WHERE proposal_id=?',(old,)).fetchone()[0],'SUPERSEDED')
  self.assertEqual(self.count('proposals'),3)
  self.assertEqual(self.db.execute("SELECT count(*) FROM source_results WHERE status='INVALIDATED'").fetchone()[0],2)
 def test_partial_import_quarantines_invalid_type(self):
  j=p.make_enrichment(self.db,self.s);f=self.facts(j);bad=copy.deepcopy(f[0]);bad['object']={'type':'number','value':'not numeric'}
  r=self.reply(j,f+[bad]);self.assertEqual(r['status'],'PARTIAL');self.assertEqual(r['new_proposals'],2);self.assertEqual(self.count('import_errors'),1)
 def test_all_invalid_keeps_archive_and_reservation(self):
  j=p.make_enrichment(self.db,self.s);f=self.facts(j)
  for fact in f:fact['object']={'type':'boolean','value':'false'}
  with self.assertRaises(ValueError):self.reply(j,f)
  self.assertEqual(self.count('proposals'),0);self.assertEqual(self.count('return_archives'),1);self.assertEqual(self.count('active_items'),2)
 def test_blocked_prefix_does_not_starve(self):
  self.s.enrich_pack_articles=1
  for i in range(12):self.add_candidate(pid=100+i,priority=200)
  j=p.make_enrichment(self.db,self.s)
  self.assertIn(self.articles(j)[0]['page_id'],(1,2))
  self.assertEqual(self.db.execute("SELECT count(*) FROM candidates WHERE state='SOURCE_BLOCKED'").fetchone()[0],12)
 def test_same_concept_reuses_new_concept_complements(self):
  j=p.make_enrichment(self.db,self.s);self.reply(j)
  cid=self.add_candidate();r=p.make_enrichment(self.db,self.s)
  self.assertEqual(r['reused'],1);self.assertEqual(r['status'],'NO_PACK')
  self.assertEqual(self.db.execute('SELECT state FROM candidates WHERE candidate_id=?',(cid,)).fetchone()[0],'REUSED')
  self.add_candidate(concept='concept3')
  a=self.articles(p.make_enrichment(self.db,self.s))[0]
  self.assertEqual(a['task_mode'],'TARGETED_COMPLEMENT');self.assertTrue(a['prior_propositions'])
 def test_two_connections_do_not_double_reserve(self):
  db2=open_work(self.s.db_path);self.addCleanup(db2.close);original=p._read_article;called=[]
  def interleave(settings,pid):
   if not called:
    called.append(1)
    with self.assertRaisesRegex(RuntimeError,'ordonnanceur'):p.make_enrichment(db2,settings)
   return original(settings,pid)
  with patch.object(p,'_read_article',interleave):p.make_enrichment(self.db,self.s)
  self.assertEqual(self.count('jobs'),1);self.assertEqual(self.count('active_items'),2)
 def test_process_lock_releases_on_death(self):
  script="from encyk_v32.locking import writer_lock; import sys;\nwith writer_lock(sys.argv[1],1):\n print('locked',flush=True);sys.stdin.read()"
  proc=subprocess.Popen([sys.executable,'-c',script,str(self.s.db_path)],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
  try:
   self.assertEqual(proc.stdout.readline().strip(),'locked')
   with self.assertRaises(RuntimeError):p.make_enrichment(self.db,self.s)
   proc.kill();proc.wait(timeout=10)
   self.assertIn('job_id',p.make_enrichment(self.db,self.s))
  finally:
   if proc.poll() is None:proc.kill();proc.wait(timeout=10)
   for stream in (proc.stdin,proc.stdout,proc.stderr):stream.close()
 def test_import_failure_rolls_back_then_replays(self):
  j=p.make_enrichment(self.db,self.s)
  with patch.object(p,'_finalize',side_effect=RuntimeError('crash')):
   with self.assertRaises(RuntimeError):self.reply(j)
  self.assertEqual(self.count('proposals'),0);self.assertEqual(self.count('active_items'),2)
  self.assertEqual(self.reply(j)['new_proposals'],2)
 def test_orphan_pack_report_then_retry(self):
  original=p._free_lane;calls=[]
  def fail(db,limit=10):
   calls.append(1);return original(db,limit) if len(calls)==1 else None
  with patch.object(p,'_free_lane',fail):
   with self.assertRaises(RuntimeError):p.make_enrichment(self.db,self.s)
  self.assertEqual(self.count('active_items'),0)
  self.assertEqual(len(p.recovery_report(self.db)['orphan_packs_preserved']),1)
  self.assertIn('job_id',p.make_enrichment(self.db,self.s))
 def test_cancel_refuses_late_return(self):
  j=p.make_enrichment(self.db,self.s);p.cancel_job(self.db,j['job_id'],'Annulation avant nouvel essai')
  with self.assertRaisesRegex(ValueError,'incompatible'):self.reply(j)
  self.assertEqual(self.db.execute("SELECT count(*) FROM candidates WHERE state='SELECTED'").fetchone()[0],2)
 def test_hold_retry_keeps_history(self):
  with self.db:self.db.execute("UPDATE candidates SET state='PENDING'")
  j=p.make_selection(self.db,self.s)
  with ZipFile(j['path']) as z:items=[json.loads(x) for x in z.read('candidates.jsonl').splitlines()]
  def selection(job,decision):
   path=Path(self.t.temp.name)/'decisions.zip'
   content='candidate_id,decision,justification\n'+''.join(x['candidate_id']+','+decision+',Contexte documentaire à examiner\n' for x in items)
   with ZipFile(path,'w') as z:z.writestr('selection_decisions.csv',content)
   p.import_for_job(self.db,path,job['job_id'])
  selection(j,'HOLD');p.retry_candidates(self.db,[x['candidate_id'] for x in items],'Source complémentaire disponible')
  selection(p.make_selection(self.db,self.s),'SELECT');self.assertEqual(self.count('decision_history'),4)
 def test_lane_limit_and_single_oversize(self):
  self.s.lane_count=1;self.s.enrich_pack_articles=1
  self.assertEqual(len(p.make_wave(self.db,self.s,kind='enrich')),1)
  jid=self.db.execute('SELECT job_id FROM jobs').fetchone()[0];p.cancel_job(self.db,jid,'Changement des limites de pack')
  self.s.enrich_word_budget=1
  self.assertEqual(p.make_enrichment(self.db,self.s)['status'],'NO_PACK')
  self.assertEqual(self.db.execute("SELECT count(*) FROM candidates WHERE state='OVERSIZE'").fetchone()[0],2)
 def test_source_epoch_resets_cursor(self):
  discover(self.db,self.s,graph_enabled=True)
  with sqlite3.connect(self.s.wikidata_sql) as g:g.execute('INSERT INTO entity_edge VALUES(?,?,?,?,?)',(12,1000000031,11,1,1))
  self.s.source_epoch='new-snapshot';discover(self.db,self.s,graph_enabled=True)
  self.assertIsNotNone(self.db.execute("SELECT 1 FROM candidates WHERE concept_id='concept2' AND page_id=2").fetchone())
 def test_live_island_conflict_visible(self):
  import shutil
  root=Path(self.s.unesco_root);other=Path(self.t.temp.name)/'other';shutil.copytree(root,other)
  scan_islands(self.db,[str(root),str(other)])
  key=self.db.execute('SELECT island_key FROM kristal_islands LIMIT 1').fetchone()[0]
  with self.assertRaisesRegex(ValueError,'Plusieurs'):describe_island(self.db,key)
 def test_migration_backup_preserves_old_proposals(self):
  path=Path(self.t.temp.name)/'old.sqlite'
  with sqlite3.connect(path) as c:
   c.executescript(DDL);c.execute("INSERT INTO meta VALUES('schema',?)",(OLD_SCHEMA,))
   c.execute('INSERT INTO proposals VALUES(?,?,?,?,?,?,?,?,?,?,?,?)',('old','wd:Q11',1,'11','An old contextual statement','describes','{"type":"text","value":"x"}','quote','Intro','DRAFT','ENR_1','now'))
  c=open_work(path)
  try:
   self.assertEqual(c.execute("SELECT value FROM meta WHERE key='schema'").fetchone()[0],SCHEMA)
   self.assertEqual(c.execute('SELECT proposal_id FROM proposals').fetchone()[0],'old')
   self.assertEqual(c.execute('PRAGMA integrity_check').fetchone()[0],'ok')
  finally:c.close()
  with sqlite3.connect(str(path)+'.before-v32-2.sqlite') as c:self.assertEqual(c.execute("SELECT value FROM meta WHERE key='schema'").fetchone()[0],OLD_SCHEMA)
 def test_portable_example(self):
  config=Settings.load(Path(__file__).resolve().parents[1]/'config/settings.example.json')
  self.assertNotIn('/mnt/data',config.unesco_root);self.assertNotIn('/home/oai',config.work_root)

 def test_bare_json_and_csv_returns(self):
  with self.db:self.db.execute("UPDATE candidates SET state='PENDING'")
  job=p.make_selection(self.db,self.s)
  ids=[r[0] for r in self.db.execute('SELECT candidate_id FROM job_items WHERE job_id=?',(job['job_id'],))]
  target=Path(self.t.temp.name)/'any-selection.csv'
  target.write_text('candidate_id,decision,justification\n'+''.join(cid+',SELECT,Correspondance documentaire établie\n' for cid in ids),encoding='utf-8')
  self.assertEqual(p.import_for_job(self.db,target,job['job_id'])['decided'],2)
  job=p.make_enrichment(self.db,self.s);target=Path(self.t.temp.name)/'any-return.json'
  target.write_text(json.dumps({'format':'encyk.enrichment-delta.v32/2','job_id':job['job_id'],'facts':self.facts(job),'source_coverage':[{'page_id':a['page_id'],'status':'processed','note':'Article examiné'} for a in self.articles(job)]}))
  self.assertEqual(p.import_for_job(self.db,target,job['job_id'])['new_proposals'],2)
 def test_multiple_citations_exported_without_duplicate_claim(self):
  job=p.make_enrichment(self.db,self.s);a=self.facts(job)[0];b=copy.deepcopy(a)
  b['source_quote']=b['source_quote'][:15];b['source_locator']='Début introduction'
  self.assertEqual(self.reply(job,[a,b])['new_proposals'],1)
  out=Path(self.t.temp.name)/'citations.jsonl';p.export_proposals(self.db,out)
  item=json.loads(out.read_text().splitlines()[0]);self.assertEqual(len(item['citations']),2);self.assertEqual(len(item['occurrences']),2)
 def test_doctor_checks_fixture_and_columns(self):
  from encyk_v32.doctor import run
  result=run(self.s)
  self.assertTrue(result['capabilities']['enrichment_fulltext']['available'])
  with sqlite3.connect(self.s.wikipedia_sql) as c:c.execute('ALTER TABLE wiki_qid RENAME COLUMN qid TO wrong')
  result=run(self.s)
  self.assertFalse(result['capabilities']['wikipedia_sql']['available'])
 def test_authority_can_be_selected_and_persists(self):
  import shutil
  from encyk_v32.federation import choose_island_location
  root=Path(self.s.unesco_root);other=Path(self.t.temp.name)/'other';shutil.copytree(root,other)
  scan_islands(self.db,[str(root),str(other)])
  row=self.db.execute('SELECT island_key,root FROM island_locations ORDER BY root LIMIT 1').fetchone()
  choose_island_location(self.db,row['island_key'],row['root'])
  scan_islands(self.db,[str(other),str(root)])
  self.assertEqual(describe_island(self.db,row['island_key'])['root'],row['root'])

if __name__=='__main__':unittest.main()
