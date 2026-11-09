import bz2,hashlib,json,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'/'unesco_pilot'))
from offline_xml_evidence import extract,read_inventory,EvidenceError
class TestOfflineEvidence(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
  self.root=Path(self.temp.name)
  self.inv=self.root/'inventory.json';self.xml=self.root/'test.xml.bz2';self.out=self.root/'output'
  self.records=[{'unesco_id':f'concept{i+1}','wikidata':{'qid':'Q10'},
                 'wikipedia_en_inventory':([{'page_id':42,'title':'Right_to_education','latest_revision_id':17,'redirect':False}] if i==0 else [])}for i in range(41)]
  self.data={'profile':'encyklopedia.unesco-local-wikipedia-handoff/1.0','branch':'unesco-mt1-10','not_canonical':True,'not_publication':True,'approval_status':'BLOCKED','wiki_content_extracted':False,'records':self.records}
  self.inv.write_text(json.dumps(self.data))
  self.body=b'''<?xml version="1.0" encoding="utf-8"?><mediawiki xmlns="http://www.mediawiki.org/xml/export-0.11/"><page><title>Right to education</title><ns>0</ns><id>42</id><revision><id>17</id><timestamp>2026-11-05T01:00:00Z</timestamp><text xml:space="preserve">A short test article &amp; reference.</text></revision></page><page><title>Other</title><ns>0</ns><id>56</id><revision><id>18</id><text>Do not copy</text></revision></page></mediawiki>'''
  self.xml.write_bytes(bz2.compress(self.body))
 def test_selects_only_matching_page_with_provenance(self):
  m=extract(self.inv,self.xml,self.out,progress_every=0)
  self.assertEqual((m['pages_scanned'],m['extracted_pages'],m['missing_page_ids']),(2,1,[]))
  self.assertTrue(m['pages'][0]['inventory_revision_agrees'])
  self.assertEqual(m['pages'][0]['sha256'],hashlib.sha256((self.out/'page-42.wikitext.txt').read_bytes()).hexdigest())
  self.assertFalse((self.out/'page-56.wikitext.txt').exists())
  self.assertFalse(m['public_upload_authorized'])
 def test_different_revision_flagged(self):
  self.records[0]['wikipedia_en_inventory'][0]['latest_revision_id']=99
  self.inv.write_text(json.dumps(self.data))
  m=extract(self.inv,self.xml,self.out,progress_every=0)
  self.assertFalse(m['pages'][0]['inventory_revision_agrees'])
 def test_rejects_output_overwrite(self):
  self.out.mkdir()
  with self.assertRaises(EvidenceError):extract(self.inv,self.xml,self.out,progress_every=0)
 def test_rejects_noncandidate_input(self):
  self.data['approval_status']='AUTHORIZED';self.inv.write_text(json.dumps(self.data))
  with self.assertRaises(EvidenceError):extract(self.inv,self.xml,self.out,progress_every=0)
 def test_bad_bzip2_fails_closed(self):
  self.xml.write_bytes(b'BROKEN')
  with self.assertRaises(EvidenceError):extract(self.inv,self.xml,self.out,progress_every=0)
  self.assertTrue((self.out/'INCOMPLETE.txt').exists())
if __name__=='__main__':unittest.main()
