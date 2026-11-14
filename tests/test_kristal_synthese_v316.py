"""Kristal v31.6 : 120 article packs, exact reading guide, v27 compatibility."""
import json
from pathlib import Path
import sys
import unittest
import zipfile
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'/'unesco_pilot'))
import production_kristals_v27 as p
import poste_chatgpt_v30 as station

class SyntheseV316Tests(unittest.TestCase):
    def test_guide_quotes_are_exact_and_no_article_disappears(self):
        entries=[]
        for k in range(1,121):
            body=(f"{k} was established in 1910 and became important for education worldwide. "
                  "It developed major scientific and pedagogical programs throughout the twentieth century.\n"
                  "== History ==\nThe history of this institution includes major changes and new centers for students.\n"
                  "== Impact ==\nThe institution contributed to educational access and professional training across regions.\n"
                  "== References ==\n<ref>Some reference text</ref>\n").encode()
            entries.append({'page_id':k,'text':body,'revision_id':str(k+200),
                 'xml_title':f'School {k}','catalog_title':f'School {k}',
                 'catalog_revision':str(k+200),'qid':f'Q{k}','assignments':[],
                 'word_count':len(body.split()),'score':80})
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            archive,_=p.make_pack(entries,'PACK_V27_000222',{'xml_signature':{'x':1},'catalog_source_sha':'c'},Path(td))
            m=p.verify_pack(archive)
            self.assertEqual(m['articles_count'],120)
            with zipfile.ZipFile(archive) as z:
                rows=[json.loads(line) for line in z.read('DOSSIER_PRIORITAIRE_KRISTAL_V316.jsonl').splitlines()]
                self.assertEqual(len(rows),120)
                self.assertIn('encyklopedia.kristal-reading-guide.v316/1',m['reading_guide_format'])
                for row in rows:
                    original=z.read(row['text_path']).decode()
                    for sample in row['samples']:
                        self.assertIn(sample['exact_excerpt'],original)
                self.assertIn(b'articles',z.read('INSTRUCTIONS_CHATGPT.md'))
    def test_missing_guide_refused_for_new_packs(self):
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            r=Path(td)/'sample.zip'
            content=b'A significant educational institution was founded in 1910.'
            entry={'page_id':1,'text':content,'revision_id':'200',
                   'xml_title':'Institution','catalog_title':'Institution',
                   'catalog_revision':'200','qid':'Q1','assignments':[],
                   'word_count':9,'score':80}
            built,_=p.make_pack([entry],'PACK_V27_000222',{'xml_signature':'a'},Path(td))
            with zipfile.ZipFile(built) as src, zipfile.ZipFile(r,'w') as dst:
                for name in src.namelist():
                    if name != 'DOSSIER_PRIORITAIRE_KRISTAL_V316.jsonl':
                        dst.writestr(name,src.read(name))
            with self.assertRaisesRegex(p.Refusal,'Dossier de lecture declare mais absent'):
                p.verify_pack(r)

    def test_prior_v27_pack_without_guide_remains_valid(self):
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            r=Path(td)/'older.zip'
            data=b'An example article about education.'
            m={'format':p.PACK_FORMAT,'pack_id':'PACK_V27_000111',
               'raw_article_texts_complete':True,'canonical_admissions':0,
               'publication_authorized':False,'articles_count':1,
               'articles':[{'page_id':12,'revision_id':'42',
                            'text_path':'articles/enwiki-12.wikitext.txt',
                            'text_bytes':len(data),'text_sha256':p.digest(data)}]}
            with zipfile.ZipFile(r,'w') as z:
                z.writestr('MANIFEST_PACK_V27.json',p.encoded(m))
                z.writestr('MODELE_DELTA_KRISTAL_V27.json','{}')
                z.writestr('INSTRUCTIONS_CHATGPT.md','Old instructions')
                z.writestr('articles/enwiki-12.wikitext.txt',data)
            self.assertEqual(p.verify_pack(r)['articles_count'],1)
    def test_station_120_and_unesco_unchanged(self):
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            repo=Path(td)
            (repo/'PRODUIRE_KRISTALS_V27.ps1').write_text('dummy')
            st=station.Station(repo,repo/'work',repo/'v27',repo/'v28',repo/'catalogue.sqlite')
            try:
                recorded=[]
                st._run=lambda script,options: (recorded.append((script,options)) or '"queue":{"PACKED":1}')
                with patch.object(st,'_open_review_count',return_value=1), patch.object(st,'_prepare',return_value=None):
                    st._batch()
                args=recorded[0][1]
                self.assertIn('120',args);self.assertIn('400000',args);self.assertIn('62914560',args)
                self.assertEqual(st.snapshot()['volume_v315']['contrat']['kristal_articles_max'],120)
                self.assertEqual(st.snapshot()['volume_v315']['contrat']['kristal_mots_cibles'],400000)
                self.assertEqual(station.REVIEW_SIZE,880)
            finally:
                st.db.close()

if __name__=='__main__':unittest.main()
