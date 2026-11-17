"""v31.8: prospective depth instructions, complete section map, strict quotes, old v27 compatibility."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
import zipfile

PILOT=Path(__file__).resolve().parents[1]/'tools'/'unesco_pilot'
sys.path.insert(0,str(PILOT))
import production_kristals_v27 as p
import poste_chatgpt_v30 as station


class DeepSynthesisTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.entries=[]
        for pid in (11,22,33):
            lines=['A school policy was founded to expand access and reorganize public teaching.']
            for i in range(1,10):
                lines.extend([f'== Chapter {i} ==',
                              f'Chapter {i} describes a significant institutional transformation in 19{i:02d}, with long-term consequences.'])
            lines.extend(['== Late legacy ==','The final legacy was a landmark change to civic education and teacher training.',
                          '== References ==','<ref>Bibliographical citation here.</ref>'])
            raw='\n'.join(lines).encode('utf-8')
            self.entries.append({'page_id':pid,'text':raw,'revision_id':f'900{pid}',
                 'xml_title':f'School policy {pid}', 'catalog_title':f'School {pid}',
                 'catalog_revision':f'900{pid}', 'qid':f'Q{pid}','assignments':[],
                 'word_count':len(raw.decode().split()),'score':30})
        self.pack,_=p.make_pack(self.entries,'PACK_V27_000318',{'catalogue':'synthetic'},self.root)
        self.manifest=p.verify_pack(self.pack)
        self.article=self.manifest['articles'][0]
        self.proof='A school policy was founded to expand access and reorganize public teaching.'

    def delta(self, claims=True):
        note='\n'.join(f'enwiki:{a["page_id"]} | definition, histoire et consequences | '+
                       ('1 fait, premiere source' if i==0 and claims else '0 fait solide')+
                       ' | sections et omissions revues sans autre fait probant'
                       for i,a in enumerate(self.manifest['articles']))
        entries=[]
        if claims:
            entries=[{'source_page_id':self.article['page_id'],
                'source_revision_id':self.article['revision_id'],
                'subject_ref':self.article['article_id'], 'predicate':'has_educational_mission',
                'object':{'type':'text','value':'Expand access to public education'},
                'statement_en':'The policy aimed to expand access to public teaching.',
                'unesco_concepts':[], 'source_locator':'Introduction',
                'source_quote':self.proof,'confidence':'high'}]
        return {'format':p.DELTA_FORMAT,'pack_id':self.manifest['pack_id'],
                'pack_sha256':p.hash_file(self.pack),'producer':'ChatGPT',
                'canonical_admissions':0,'publication_authorized':False,
                'coverage_note':note,'claims':entries}

    def write(self, delta):
        path=self.root/'delta.json'
        path.write_bytes(p.encoded(delta))
        return path

    def test_section_map_covers_late_content_not_just_selected_excerpts(self):
        self.assertEqual(self.manifest['synthesis_audit'],p.SYNTHESIS_AUDIT_V318)
        with zipfile.ZipFile(self.pack) as z:
            guide=[json.loads(line) for line in z.read('DOSSIER_PRIORITAIRE_KRISTAL_V316.jsonl').splitlines()]
            self.assertEqual(len(guide),3)
            for row,article in zip(guide,self.manifest['articles']):
                self.assertEqual(row['text_sha256'],article['text_sha256'])
                self.assertEqual(row['section_inventory'][-2]['heading'],'Late legacy')
                self.assertTrue(row['section_inventory'][-1]['is_reference_section'])
                self.assertEqual(len(row['section_inventory']),12)
                text=z.read(article['text_path']).decode('utf-8')
                for excerpt in row['samples']:
                    self.assertIn(excerpt['exact_excerpt'],text)
            instructions=z.read('INSTRUCTIONS_CHATGPT.md').decode('utf-8')
            for term in ('SIX PASSES','AUDIT D\'OMISSIONS','source_quote EXACTE','section_inventory'):
                self.assertIn(term,instructions)
        self.assertIn('SIX PASSES',station.prompt({'kind':'v27','key':'PACK_V27_000318',
                                                  'bundle_path':str(self.pack),'source_sha256':'abc'}))
        self.assertEqual(station.REVIEW_SIZE,4000)

    def test_exact_proof_and_per_article_coverage_required(self):
        self.assertEqual(len(p.validate_delta(self.pack,self.write(self.delta()))[-1]),1)
        # No forced claims quota: honest zero-claim pack is valid with full coverage.
        self.assertEqual(len(p.validate_delta(self.pack,self.write(self.delta(False)))[-1]),0)
        not_proven=self.delta();not_proven['claims'][0]['source_quote']='A plausible sentence never present in the source.'
        with self.assertRaisesRegex(p.Refusal,'citation absente'):
            p.validate_delta(self.pack,self.write(not_proven))
        not_proven['claims'][0]['source_quote']=''
        with self.assertRaisesRegex(p.Refusal,'citation absente'):
            p.validate_delta(self.pack,self.write(not_proven))
        incomplete=self.delta();incomplete['coverage_note']=incomplete['coverage_note'].splitlines()[0]
        with self.assertRaisesRegex(p.Refusal,'article\\(s\\) absent'):
            p.validate_delta(self.pack,self.write(incomplete))
        malformed=self.delta();malformed['coverage_note']=malformed['coverage_note'].replace('enwiki:22 |','A review of enwiki:22 |')
        with self.assertRaisesRegex(p.Refusal,'article\\(s\\) absent'):
            p.validate_delta(self.pack,self.write(malformed))
        swapped=self.delta();swapped['claims'][0]['source_page_id']=22
        swapped['claims'][0]['source_revision_id']='90022'
        with self.assertRaisesRegex(p.Refusal,'citation absente'):
            swapped['claims'][0]['source_quote']='Chapter 1 describes a significant institutional transformation in 1901, with long-term consequences.'
            # The quote occurs on both pages; cannot test cross-page with this shared fixture.
            swapped['claims'][0]['source_quote']='A real-looking but absent statement about school policy.'
            p.validate_delta(self.pack,self.write(swapped))

    def test_map_tampering_detected(self):
        tampered=self.root/'modified.zip'
        with zipfile.ZipFile(self.pack) as src, zipfile.ZipFile(tampered,'w') as dst:
            for name in src.namelist():
                raw=src.read(name)
                if name=='DOSSIER_PRIORITAIRE_KRISTAL_V316.jsonl':
                    rows=[json.loads(x) for x in raw.splitlines()]
                    rows[0]['section_inventory'].pop(-2)
                    raw=('\n'.join(json.dumps(r) for r in rows)+'\n').encode()
                dst.writestr(name,raw)
        with self.assertRaisesRegex(p.Refusal,'Inventaire des sections'):
            p.verify_pack(tampered)

    def test_legacy_v27_remains_accepted_without_new_requirements(self):
        archive=self.root/'legacy.zip'
        with zipfile.ZipFile(self.pack) as src, zipfile.ZipFile(archive,'w') as dst:
            for name in src.namelist():
                raw=src.read(name)
                if name=='MANIFEST_PACK_V27.json':
                    m=json.loads(raw);m.pop('synthesis_audit');raw=p.encoded(m)
                if name=='DOSSIER_PRIORITAIRE_KRISTAL_V316.jsonl':
                    rows=[json.loads(line) for line in raw.splitlines()]
                    for row in rows:row.pop('section_inventory')
                    raw=('\n'.join(json.dumps(row) for row in rows)+'\n').encode()
                dst.writestr(name,raw)
        legacy=p.verify_pack(archive)
        self.assertNotIn('synthesis_audit',legacy)
        delta=self.delta()
        delta['pack_sha256']=p.hash_file(archive)
        delta['claims'][0]['source_quote']=''  # historic contract allowed empty quote
        delta['coverage_note']='selective'  # historic contract allowed brief note
        self.assertEqual(len(p.validate_delta(archive,self.write(delta))[-1]),1)


if __name__=='__main__':unittest.main(verbosity=2)
