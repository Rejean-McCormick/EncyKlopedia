"""Regression du deblocage v27 sous dump XML non aligne avec les offsets v21."""
from pathlib import Path
import hashlib
import json
import sqlite3
import sys
import unittest

BASE=Path(__file__).resolve().parents[1]/'tools'/'unesco_pilot'
sys.path.insert(0,str(BASE))
import production_kristals_v27 as v27
import test_production_kristals_v27 as fixtures


def mutate_index_signature(index, source_signature):
    con=sqlite3.connect(index)
    try:
        con.execute('UPDATE v21_meta SET value=? WHERE name=?',
                    (json.dumps(source_signature,sort_keys=True),'source_signature'))
        con.commit()
    finally:con.close()


class XmlFallbackTests(unittest.TestCase):
    """Only the additional v27 checks, reusing the native fixture."""
    setUp=fixtures.V27Pipeline.setUp
    tearDown=fixtures.V27Pipeline.tearDown
    args=fixtures.V27Pipeline.args
    def test_stale_signature_but_page_offsets_verified(self):
        # Index meta references an older XML while its offsets still point to
        # provably identical pages. Every article is verified before use.
        old=v27.xml_signature(self.xml)
        old['path']='C:/old/dump.xml'
        mutate_index_signature(self.index,old)
        cat,ix,src=v27.validated_sources(self.catalogue,self.index,self.xml)
        try:self.assertFalse(src['index_v21_matches_current_xml'])
        finally:cat.close();ix.close()
        result=v27.produce(self.args(max_packs=3))
        self.assertEqual(result['queue'].get('PACKED'),3)
        self.assertEqual(result['xml_pages_scanned_in_fallback'],0)
        self.assertGreater(result['xml_fulltexts_verified_by_offset'],0)
        for record in result['packs']:
            with __import__('zipfile').ZipFile(record['path']) as z:
                for a in json.loads(z.read('MANIFEST_PACK_V27.json'))['articles']:
                    self.assertEqual(z.read(a['text_path']),self.orig[a['page_id']])

    def test_shifted_offsets_trigger_one_targeted_fulltext_scan(self):
        before_index=hashlib.sha256(self.index.read_bytes()).hexdigest()
        before_cat=hashlib.sha256(self.catalogue.read_bytes()).hexdigest()
        # XML still valid but shift offsets and XML signature compared with v21.
        before=self.xml.read_bytes()
        self.xml.write_bytes(before.replace(b'<mediawiki>', b'<mediawiki><!-- changed-length-prefix -->'))
        result=v27.produce(self.args(max_articles=1,max_packs=2))
        self.assertEqual(result['packets_created_this_run'],2)
        self.assertEqual(result['queue'].get('PACKED'),2)
        self.assertGreater(result['xml_pages_scanned_in_fallback'],0)
        self.assertEqual(result['xml_fulltexts_verified_by_cache'],2)
        for record in result['packs']:
            with __import__('zipfile').ZipFile(record['path']) as z:
                for a in json.loads(z.read('MANIFEST_PACK_V27.json'))['articles']:
                    self.assertEqual(z.read(a['text_path']),self.orig[a['page_id']])
                    self.assertNotEqual(a['revision_id'],'')
        # Existing on-disk target cache makes the next pack possible with no scan.
        other=v27.produce(self.args(max_articles=1,max_packs=1))
        self.assertEqual(other['packets_created_this_run'],1)
        self.assertEqual(other['xml_pages_scanned_in_fallback'],0)
        self.assertGreater(other['xml_fulltexts_verified_by_cache'],0)
        self.assertEqual(hashlib.sha256(self.index.read_bytes()).hexdigest(),before_index)
        self.assertEqual(hashlib.sha256(self.catalogue.read_bytes()).hexdigest(),before_cat)

    def test_old_work_keeps_old_pack_and_records_source_epoch(self):
        first=v27.produce(self.args(max_packs=1))
        self.assertEqual(first['packets_created_this_run'],1)
        original_pack=Path(first['packs'][0]['path'])
        pack_sha=v27.hash_file(original_pack)
        src=self.xml.read_bytes()
        self.xml.write_bytes(src.replace(b'<mediawiki>',b'<mediawiki><!-- new-dump -->'))
        second=v27.produce(self.args(max_packs=1))
        self.assertEqual(second['packets_created_this_run'],1)
        self.assertEqual(v27.hash_file(original_pack),pack_sha)
        self.assertNotEqual(first['packs'][0]['pack_id'],second['packs'][0]['pack_id'])
        self.assertEqual(v27.report(self.work)['packs_created'],2)
        with __import__('zipfile').ZipFile(original_pack) as z:
            old=json.loads(z.read('MANIFEST_PACK_V27.json'))
        with __import__('zipfile').ZipFile(second['packs'][0]['path']) as z:
            new=json.loads(z.read('MANIFEST_PACK_V27.json'))
        self.assertNotEqual(old['source']['xml_signature'],new['source']['xml_signature'])
        db=sqlite3.connect(self.work/'FILE_PACKS_V27.sqlite')
        try:
            self.assertEqual(db.execute('SELECT count(*) FROM source_epoch_history').fetchone()[0],1)
        finally:db.close()

    def test_missing_target_not_false_approval(self):
        # Shift all old positions, remove one page from the XML: the page is
        # unavailable and must not be packaged with invented fulltext.
        original=self.xml.read_bytes()
        xml=original.replace(b'<mediawiki>',b'<mediawiki><!-- shifted -->')
        start=xml.index(b'<page><title>Right_to_education')
        end=xml.index(b'</page>',start)+len(b'</page>')
        self.xml.write_bytes(xml[:start]+xml[end:])
        output=v27.produce(self.args(max_packs=3))
        self.assertEqual(output['queue'].get('PACKED'),2)
        self.assertEqual(output['queue'].get('FAILED'),1)
        for record in output['packs']:
            with __import__('zipfile').ZipFile(record['path']) as z:
                self.assertNotIn(11,[a['page_id'] for a in json.loads(z.read('MANIFEST_PACK_V27.json'))['articles']])

    def test_wikitext_integrity_cache_tampering_refused(self):
        self.xml.write_bytes(self.xml.read_bytes().replace(b'<mediawiki>', b'<mediawiki><!-- offset-shift -->'))
        result=v27.produce(self.args(max_articles=1,max_packs=1))
        self.assertEqual(result['packets_created_this_run'],1)
        cachefiles=list(self.work.glob('CACHE_XML_INTEGRAL_VERIFIE_V27_*.sqlite'))
        self.assertEqual(len(cachefiles),1)
        db=sqlite3.connect(cachefiles[0])
        db.execute('UPDATE pages SET wikitext=? WHERE page_id=?',(b'HACKED',22))
        db.commit();db.close()
        with self.assertRaisesRegex(ValueError,'altéré'):
            v27.produce(self.args(max_articles=1,max_packs=1))


if __name__=='__main__':unittest.main()
