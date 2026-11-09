"""v0.7: real v0.5/v0.6 fixture, safe review, rights, resume, SHA gates."""
import json
import os
import sqlite3
import sys
import unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'/'dictionary-harvester'))
import semantic_enrichment as enrich
import dik_qualification as qual
import test_semantic_enrichment as base


class QualificationTests(unittest.TestCase):
    def setUp(self):
        base.EnrichmentTests.setUp(self)
        enrich.run(self.root,min_free_gb=0,batch_lines=1)
        self.qout=self.root/qual.OUTPUT

    def test_plan_no_output(self):
        qual.plan(self.root)
        self.assertFalse(self.qout.exists())

    def test_full_pipeline_and_hashes(self):
        x=qual.run(self.root,min_free_gb=0)
        self.assertEqual(x['candidate_keys_qualified'],2)
        self.assertEqual(x['language_codes_staged'],2)
        self.assertEqual(x['status'],'qualification_candidates_complete')
        self.assertFalse(x['published'])
        self.assertEqual(x['automatic_accepted_matches'],0)
        self.assertEqual(x['license_sources_pending_manual_review'],4)
        q=qual.verify(self.root)
        self.assertEqual(q['failed'],0)
        docs=[json.loads(v) for v in (self.qout/'review_queue/en.jsonl').read_text().splitlines()]
        self.assertEqual(len(docs),1)
        self.assertEqual(docs[0]['external_sense_ids_sample'],['L321-S1'])
        self.assertIn('Financial institution',docs[0]['glosses_sample'])
        self.assertEqual(docs[0]['semantic_relationship'],None)
        self.assertFalse(docs[0]['may_be_published'])

    def test_idempotent_and_review_notes_preserved(self):
        qual.run(self.root,min_free_gb=0)
        with sqlite3.connect(self.qout/'qualification.sqlite3') as db:
            cid=db.execute('SELECT candidate_id FROM candidates LIMIT 1').fetchone()[0]
        qual.append_event(self.root,kind='review',subject=cid,reviewer='revisor',disposition='defer',rationale='Nécessite un examen des sens')
        qual.run(self.root,min_free_gb=0)
        with sqlite3.connect(self.qout/'qualification.sqlite3') as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM candidates').fetchone()[0],2)
            self.assertEqual(db.execute('SELECT COUNT(*) FROM review_events').fetchone()[0],1)
        qual.verify(self.root)

    def test_pilot_to_world(self):
        pilot=qual.run(self.root,languages=['fr'],min_free_gb=0)
        self.assertEqual(pilot['language_codes_staged'],1)
        self.assertEqual(pilot['status'],'qualification_candidates_partial')
        whole=qual.run(self.root,min_free_gb=0)
        self.assertEqual(whole['language_codes_staged'],2)
        qual.verify(self.root)

    def test_corrupt_v06_export_blocked(self):
        target=self.out/'evidence/en.jsonl'
        target.write_bytes(target.read_bytes()+b'garbage\n')
        with self.assertRaises(RuntimeError):qual.run(self.root,languages=['en'],min_free_gb=0)
        with sqlite3.connect(self.qout/'qualification.sqlite3') as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM completed_languages').fetchone()[0],0)

    def test_modified_v06_export_after_qualification_blocked(self):
        qual.run(self.root,min_free_gb=0)
        with sqlite3.connect(self.out/'enrichment.sqlite3') as db:
            db.execute("UPDATE exports SET sha256='X' WHERE language='en'")
        with self.assertRaises(RuntimeError):qual.run(self.root,languages=['en'],min_free_gb=0)

    def test_corrupt_v07_export_detected(self):
        qual.run(self.root,min_free_gb=0)
        p=self.qout/'review_queue/en.jsonl'
        p.write_text(p.read_text()+'\n')
        with self.assertRaises(RuntimeError):qual.verify(self.root)

    def test_candidate_note_requirements(self):
        qual.run(self.root,min_free_gb=0)
        with sqlite3.connect(self.qout/'qualification.sqlite3') as db:
            cid=db.execute('SELECT candidate_id FROM candidates LIMIT 1').fetchone()[0]
        with self.assertRaises(ValueError):
            qual.append_event(self.root,kind='review',subject=cid,reviewer='a',disposition='defer',rationale='Très bon')
        with self.assertRaises(ValueError):
            qual.append_event(self.root,kind='review',subject=cid,reviewer='reviewer',disposition='accepted',rationale='Vérifié preuve')
        with self.assertRaises(ValueError):
            qual.append_event(self.root,kind='review',subject='fake',reviewer='reviewer',disposition='defer',rationale='Pas de preuve')
        result=qual.append_event(self.root,kind='review',subject=cid,reviewer='reviewer',disposition='escalate_ambiguity',rationale='Plusieurs sens distincts existent')
        self.assertFalse(result['normative_dik_acceptance'])
        qual.verify(self.root)

    def test_license_note_never_marks_reviewed(self):
        qual.run(self.root,min_free_gb=0)
        qual.append_event(self.root,kind='license',subject=1,reviewer='juriste',disposition='needs_legal_review',rationale='Vérifier la compatibilité et les obligations',reference_url='https://example.org/license')
        qual.verify(self.root)
        report=(self.qout/'source_license_review_queue.csv').read_text()
        self.assertIn('PENDING_MANUAL_REVIEW',report)
        self.assertIn('False',report)
        with self.assertRaises(ValueError):
            qual.append_event(self.root,kind='license',subject=1,reviewer='juriste',disposition='approved',rationale='Contrôlé et accepté')

    def test_events_append_only(self):
        qual.run(self.root,min_free_gb=0)
        with sqlite3.connect(self.qout/'qualification.sqlite3') as db:
            cid=db.execute('SELECT candidate_id FROM candidates LIMIT 1').fetchone()[0]
        qual.append_event(self.root,kind='review',subject=cid,reviewer='reviseur',disposition='needs_more_evidence',rationale='Vérifier la source originale')
        with sqlite3.connect(self.qout/'qualification.sqlite3') as db:
            with self.assertRaises(sqlite3.DatabaseError):db.execute('DELETE FROM review_events')
            with self.assertRaises(sqlite3.DatabaseError):db.execute("UPDATE review_events SET rationale='changed'")
        qual.verify(self.root)

    def test_triage_conflicts_are_not_semantic_decisions(self):
        doc={'candidate_id':'abc','language':'fr','search_key':'chat',
             'anchors_total':2,'evidence_captured':2,
             'raw_source_line_evidence':[
                {'status':'observed','family':'kaikki','source_id':1,'source_line':4,
                 'observed_record':{'pos':'noun','senses':[{'glosses':['Animal domestique']},{'glosses':['Une conversation']}]}},
                {'status':'observed','family':'wikidata','source_id':2,'source_line':3,
                 'observed_record':{'lexeme_id':'L12','lexical_category_qid':'Q3',
                   'senses':[{'sense_id':'L12-S1','glosses':[{'language':'fr','value':'Animal'}]}]}}]}
        tier,priority,flags,summary=qual.triage(doc,(1,0,2))
        self.assertIn('heterogeneous_pos_labels_require_mapping',flags)
        self.assertIn('distinct_NFC_spellings_collapsed_by_search_key',flags)
        self.assertEqual(tier,'possible_lexeme_or_normalization_ambiguity')
        self.assertIsNone(summary['semantic_relationship'])
        self.assertFalse(summary['semantic_equivalence_approved'])

    def test_missing_evidence_top_priority(self):
        doc={'candidate_id':'a','language':'fr','search_key':'abc','anchors_total':3,'evidence_captured':1,
             'raw_source_line_evidence':[{'status':'parse_error','family':'kaikki'}]}
        tier,priority,flags,summary=qual.triage(doc,(0,0,1))
        self.assertEqual((tier,priority),('source_evidence_incomplete',1))
        self.assertIn('missing_or_invalid_sample_anchors',flags)

    def test_all_inputs_unchanged(self):
        important=[self.root/qual.INDEX,self.root/qual.V05_DB,self.root/qual.V06_DB]
        old=[qual.sha_file(p) for p in important]
        qual.run(self.root,min_free_gb=0)
        self.assertEqual([qual.sha_file(p) for p in important],old)

    def test_gui_module_import_without_display(self):
        from importlib.util import spec_from_file_location, module_from_spec
        # .pyw extension needs an explicit source loader.
        from importlib.machinery import SourceFileLoader
        path=Path(__file__).resolve().parents[1]/'Qualifier_Dictionnaires_diK_UI.pyw'
        loader=SourceFileLoader('qualify_gui',str(path))
        spec=spec_from_file_location('qualify_gui',str(path),loader=loader)
        module=module_from_spec(spec);spec.loader.exec_module(module)
        self.assertTrue(module.ENGINE.is_file())

if __name__=='__main__':unittest.main()
