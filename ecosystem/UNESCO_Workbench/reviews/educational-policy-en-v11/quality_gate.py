"""Contrôle en lecture seule de la feuille de revue UNESCO / Educational Policy."""
import csv
from pathlib import Path
ROOT = Path(__file__).resolve().parent

def load():
    with (ROOT / '41_UNESCO_WIKIDATA_IDENTITY_REVIEW_EN.csv').open(encoding='utf-8-sig', newline='') as stream:
        return list(csv.DictReader(stream))

def check():
    rows = load()
    problems = []
    if len(rows) != 41: problems.append('41 UNESCO concepts required')
    if len({r['local_kq'] for r in rows}) != len(rows): problems.append('duplicate KQ')
    if len({r['unesco_id'] for r in rows}) != len(rows): problems.append('duplicate UNESCO ID')
    qids = [r['wikidata_qid_candidate'] for r in rows if r['wikidata_qid_candidate']]
    if len(qids) != 36: problems.append('unexpected number of candidate QIDs')
    if len(set(qids)) != len(qids): problems.append('duplicate Wikidata QID candidates')
    n_review = 0
    for r in rows:
        decision = r['editorial_decision'].strip().lower()
        if decision not in ('', 'review', 'approve_exact', 'reject_exact', 'broader', 'narrower', 'related', 'unresolved'):
            problems.append(f"{r['local_kq']}: unknown decision {decision!r}")
        if decision and decision != 'review':
            n_review += 1
            if not r['reviewer'].strip() or not r['evidence_locator'].strip() or not r['editorial_notes'].strip():
                problems.append(f"{r['local_kq']}: decision requires reviewer, evidence_locator and editorial_notes")
            if decision == 'approve_exact' and not r['wikidata_qid_candidate']:
                problems.append(f"{r['local_kq']}: cannot approve exact match without QID")
    return rows, n_review, problems

if __name__ == '__main__':
    rows, reviews, problems = check()
    print('UNESCO anchors:', len(rows), '| explicit editorial decisions:', reviews)
    if problems:
        for p in problems: print('ERROR:', p)
        raise SystemExit(1)
    print('REVIEW_FILE_STRUCTURALLY_VALID — NOT A RELEASE OR CANONICAL APPROVAL')
