"""Read-only integrity checks for the Educational Policy English research proposals.
Never calls authoring APIs, writes canon, or grants approval.
"""
import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent

def validate(root=ROOT):
    errs = []
    with (root / '41_identity_recommendations_en.csv').open(encoding='utf-8-sig', newline='') as f:
        identities = list(csv.DictReader(f))
    with (root / 'source_register_en.json').open(encoding='utf-8') as f:
        sources = json.load(f)['sources']
    with (root / '19_ka_ks_research_proposals_en.jsonl').open(encoding='utf-8') as f:
        claims = [json.loads(x) for x in f if x.strip()]
    article = (root / 'right-to-education.en.md').read_text(encoding='utf-8')
    if len(identities) != 41: errs.append('expected 41 UNESCO anchors')
    if len(set(r['local_kq'] for r in identities)) != len(identities): errs.append('duplicate KQ')
    if len(set(r['unesco_id'] for r in identities)) != len(identities): errs.append('duplicate UNESCO id')
    if len([r for r in identities if r['wikidata_qid_candidate']]) != 36: errs.append('expected 36 candidate QIDs')
    if len([r for r in identities if not r['wikidata_qid_candidate']]) != 5: errs.append('expected 5 missing QIDs')
    if any(r['editorial_decision'].strip() for r in identities): errs.append('identity approval found in research-only pack')
    by_kq = {r['local_kq']: r for r in identities}
    if not by_kq['KQ2']['recommendation_not_a_decision'].startswith('LIKELY_SAME_SCOPE'): errs.append('KQ2 triage incorrect')
    if not by_kq['KQ26']['recommendation_not_a_decision'].startswith('PROBABLE_NOT_EXACT'): errs.append('KQ26 triage incorrect')
    if len(sources) != 6 or len({s['source_id'] for s in sources}) != 6: errs.append('expected 6 unique sources')
    ids = {s['source_id'] for s in sources}
    for s in sources:
        if not s['url'].startswith('https://'): errs.append('insecure source URL')
        if s['capture_status'] != 'NOT_CAPTURED' or s['capture_sha256'] is not None or s['canonical_ks_id'] is not None: errs.append('source portrayed as approved/captured')
    if len(claims) != 19 or len({c['proposal_id'] for c in claims}) != 19: errs.append('expected 19 unique research claims')
    for c in claims:
        ident = c['proposal_id']
        if not re.fullmatch(r'RTE-KA-PROP-[0-9]{3}',ident): errs.append('invalid proposal id')
        if c['source_id'] not in ids: errs.append(ident+' unknown source')
        if c['subject_provisional_kq'] != 'KQ3': errs.append(ident+' wrong subject')
        if not c['source_locator'] or not c['applicability'] or not c['statement_en']: errs.append(ident+' missing claim metadata')
        if not c['not_canon'] or c['canonical_ka_id'] is not None or c['canonical_ks_id'] is not None or c['canonical_kp_id'] is not None: errs.append(ident+' canon was implied')
        if c['source_capture_sha256'] is not None or c['editorial_decision'] is not None: errs.append(ident+' review was implied')
        if ident not in article: errs.append(ident+' not referenced in article')
    if 'NOT CANON' not in article or 'NOT FOR PUBLICATION' not in article: errs.append('article missing publication guard')
    return errs, {'anchors':len(identities), 'qid_candidates':36, 'sources':len(sources), 'claim_proposals':len(claims), 'canonical_ka':0, 'approved_identities':0}

if __name__ == '__main__':
    problems, summary = validate()
    print(json.dumps(summary, indent=2))
    if problems:
        for issue in problems: print('ERROR:',issue)
        raise SystemExit(1)
    print('ROUND2_VALID_RESEARCH_ONLY — NOT AN APPROVAL OR A RELEASE')
