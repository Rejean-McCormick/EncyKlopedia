#!/usr/bin/env python3
"""UNESCO V22: audited AI-editorial corrections, private research only.

Runs the existing V19 intake contract unmodified. Never writes to any
canonical repository, original source, V11-V21 product, or Wikipedia index.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import html
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile

import recevoir_lots_atlas_v19 as intake

BRANCH = 'unesco-mt1-10'
PAYLOAD = Path(__file__).resolve().parent / 'v22_payload'
WORK = Path(r'D:\EncyKlopedia\30_working\unesco_mt1_10\autopilot_concept10_puis_41')
LOT_NAME = 'atlas_documentaire_v19_LOT_002_CHATGPT_V21.zip'
OUT_NAME = 'semantic_stage_v22_revue_ia'
LEDGER_NAME = 'atlas_documentaire_v19_candidats'
APPROVED = {'APPROUVE_IA_TEXTE', 'APPROUVE_IA_REFORMULE'}
SUSPENDED = 'SUSPENDU_PREUVES'
MAPPING_CORRECT = {'LOT002-V21-018': 'concept11264'}
MAPPING_HOLD = {'LOT002-V21-017', 'LOT002-V21-020'}
EXPECTED = {'APPROUVE_IA_TEXTE': 28, 'APPROUVE_IA_REFORMULE': 10,
            'SUSPENDU_PREUVES': 6}

class Refus(ValueError):
    pass


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def jb(doc: object) -> bytes:
    return (json.dumps(doc, sort_keys=True, ensure_ascii=False, indent=2) + '\n').encode('utf-8')


def load(path: Path, limit=8_000_000):
    if path.is_symlink() or not path.is_file() or path.stat().st_size > limit:
        raise Refus('Fichier absent, lien ou trop grand : ' + str(path))
    return path.read_bytes()


def load_json(path: Path):
    return json.loads(load(path).decode('utf-8-sig'))


def verify_payload():
    m = load_json(PAYLOAD / 'PAYLOAD_MANIFEST_V22.json')
    if m.get('format') != 'koa.unesco-v22-payload-manifest/1.0':
        raise Refus('Manifeste V22 invalide')
    paths = m.get('files_sha256')
    if not isinstance(paths, dict) or len(paths) != 9:
        raise Refus('Nombre de sources V22 incorrect')
    for name, expected in paths.items():
        if '/' in name or '\\' in name or name in ('.', '..') or sha(load(PAYLOAD / name)) != expected:
            raise Refus('Source V22 altérée : ' + str(name))
    return m


def check_work(work: Path, batch: Path):
    if not work.is_dir() or work.is_symlink():
        raise Refus('Workspace UNESCO absent ou lien : ' + str(work))
    report_path = work / 'semantic_stage_v18_framework_quarantine' / 'RAPPORT_V18.json'
    report = load_json(report_path)
    if (report.get('branch') != BRANCH or
        report.get('framework_pinned_technical_check_passed') is not True or
        report.get('approved_KQ_KP_KA_KS') != 0 or
        report.get('canonical_kristal_approved') is not False):
        raise Refus('État V18 inattendu : aucun ajout sûr possible')
    m, batch_sha, allowed, anchors = intake.validate_batch(batch)
    if len(allowed) != 25 or sum(x['status'] == 'TEXT_EXTRACTED' for x in allowed.values()) != 25:
        raise Refus('Lot 002 incomplet : 25 textes nécessaires')
    local_anchor = load_json(work / 'atlas_documentaire_v19' / 'ancrages_kristal_stables.json')
    if {x['unesco_id'] for x in local_anchor['anchors']} != anchors:
        raise Refus('Ancrages atlas V19 différents du lot V21')
    return {'v18_report_sha256': sha(load(report_path)), 'batch': m,
            'batch_manifest_sha256': batch_sha, 'anchors': anchors}


def load_and_validate(work: Path, batch: Path):
    manifest = verify_payload()
    ctx = check_work(work, batch)
    proposals_path = PAYLOAD / 'PROPOSITIONS_ATLAS_LOT002_V21.json'
    validated = intake.validate_changeset(batch, proposals_path)
    if len(validated['candidates']) != 25:
        raise Refus('Réception V19 : nombre de propositions incorrect')
    proposals = load_json(proposals_path)
    r2 = [json.loads(s) for s in load(PAYLOAD / 'R2_PROPOSITIONS_ORIGINE.jsonl').decode('utf-8-sig').splitlines() if s.strip()]
    r2_sources = load_json(PAYLOAD / 'R2_SOURCES_ORIGINE.json')
    decisions = load_json(PAYLOAD / 'DECISIONS_IA_44_V22.json')
    unesco = load_json(PAYLOAD / 'UNESCO_2026_REFERENTIEL.json')
    identities = load_json(PAYLOAD / 'V11_IDENTITES_REFERENTIEL.json')
    registry = load_json(PAYLOAD / 'V11_REGISTRE_REFERENTIEL.json')
    if len(unesco.get('concepts', [])) != 41:
        raise Refus('Référentiel UNESCO 2026 ≠ 41 concepts')
    concepts = {x['unesco_id']: x for x in unesco['concepts']}
    if len(concepts) != 41 or set(concepts) != ctx['anchors']:
        raise Refus('Référentiel 2026 et atlas divergent')
    mapping = identities.get('by_kind', {}).get('Q', {})
    if set(mapping) != {'unesco-skos:' + x for x in concepts}:
        raise Refus('Identity map V11 incompatible avec les 41 concepts')
    kqids = set(mapping.values())
    if len(kqids) != 41 or not all(i.startswith('KQ') for i in kqids):
        raise Refus('Identités KQ non uniques')
    reg = {(x['kind'], x['id']) for x in registry['identities']}
    if not all(('entity', x) in reg for x in kqids):
        raise Refus('Registre v11 incomplet')
    if len(r2) != 19 or len({x['proposal_id'] for x in r2}) != 19:
        raise Refus('R2 : 19 propositions attendues')
    if len(r2_sources.get('sources', [])) != 6:
        raise Refus('R2 : six sources attendues')
    srcids = {s['source_id'] for s in r2_sources['sources']}
    if any(x['unesco_id'] != 'concept10' or x['subject_provisional_kq'] != mapping['unesco-skos:concept10'] or x['source_id'] not in srcids for x in r2):
        raise Refus('R2 : source ou identité incorrecte')
    if (decisions.get('branch') != BRANCH or decisions.get('canonical_admission_authorized') is not False or
        decisions.get('publication_authorized') is not False or decisions.get('human_signature') is not None):
        raise Refus('Décisions non compatibles avec la frontière non canonique')
    records = decisions.get('records', [])
    if len(records) != 44 or len({x['proposal_id'] for x in records}) != 44:
        raise Refus('44 décisions uniques nécessaires')
    if Counter(x['decision'] for x in records) != EXPECTED:
        raise Refus('Répartition des décisions modifiée')
    originals = {x['proposal_id']: x for x in r2}
    originals.update({x['candidate_id']: x for x in proposals['proposals']})
    if set(originals) != {x['proposal_id'] for x in records}:
        raise Refus('Décision sans proposition d’origine ou proposition sans décision')
    if ctx['batch_manifest_sha256'] != proposals['batch_manifest_sha256']:
        raise Refus('Lot V21 différent des propositions reçues')
    data = []
    for r in records:
        uid = r['proposal_id']; orig = originals[uid]
        collection = 'R2_RIGHT_TO_EDUCATION' if uid.startswith('RTE-KA-PROP-') else 'WIKIPEDIA_LOT_002_V21'
        original_statement = orig['statement_en'] if collection.startswith('R2_') else orig['statement']
        target = orig['unesco_id']
        if (r['source_collection'] != collection or r['original_statement'] != original_statement or
            r['une_sco_concept_id'] != target or r['provisional_kq_id'] != mapping['unesco-skos:' + target] or
            r.get('canonical_admission_authorized') is not False or r.get('publication_authorized') is not False):
            raise Refus('Décision non traçable ou non conforme : ' + uid)
        if collection.startswith('R2_') and (r.get('original_source_id') != orig['source_id'] or
                                              r.get('original_source_locator') != orig['source_locator']):
            raise Refus('Localisateur R2 différent : ' + uid)
        d = r['decision']; text = r.get('approved_statement')
        if d in APPROVED and (not isinstance(text, str) or len(text.strip()) < 15):
            raise Refus('Texte approuvé absent : ' + uid)
        if d == 'APPROUVE_IA_TEXTE' and text != original_statement:
            raise Refus('Texte supposé inchangé, modifié : ' + uid)
        if d == 'APPROUVE_IA_REFORMULE' and text == original_statement:
            raise Refus('Reformulation absente : ' + uid)
        if d == SUSPENDED and text is not None:
            raise Refus('Proposition suspendue possédant un texte approuvé : ' + uid)
        if r.get('source_capture_sha256') is not None or r.get('source_capture_status') != 'NOT_CAPTURED':
            raise Refus('Capture de preuve prétendue à tort : ' + uid)
        if not isinstance(r.get('official_sources'), list):
            raise Refus('Références de contrôle absentes : ' + uid)
        eff = MAPPING_CORRECT.get(uid, target)
        if eff not in concepts:
            raise Refus('Concept effectif absent : ' + uid)
        if uid in MAPPING_HOLD:
            mapping_state = 'BLOQUE_CORRESPONDANCE'
        elif uid in MAPPING_CORRECT:
            if r.get('semantic_mapping_review') != 'A_REVOIR' or target != 'concept1480':
                raise Refus('Correction sémantique inattendue : ' + uid)
            mapping_state = 'CORRIGE_IA_V22'
        else:
            if r.get('semantic_mapping_review') != 'COHERENT':
                raise Refus('Correspondance non validée non isolée : ' + uid)
            mapping_state = 'COHERENT'
        review_state = ('SUSPENDU_PREUVES' if d == SUSPENDED else
                        'APPROUVE_IA_MAIS_CARTOGRAPHIE_BLOQUEE' if mapping_state == 'BLOQUE_CORRESPONDANCE' else
                        'APPROUVE_IA_NON_CANONIQUE_PREUVES_A_ARCHIVER')
        data.append({'proposal_id': uid, 'source_collection': collection,
                     'source_page_id': orig.get('source_page_id'),
                     'source_revision_id': orig.get('source_revision_id'),
                     'source_locator': orig.get('source_locator'),
                     'original_unesco_id': target, 'effective_unesco_id': eff,
                     'provisional_kq_id': mapping['unesco-skos:' + eff],
                     'decision': d, 'review_state': review_state, 'mapping_state': mapping_state,
                     'original_statement': original_statement, 'effective_statement': text,
                     'decision_reason_fr': r.get('decision_reason_fr'),
                     'semantic_mapping_note_fr': r.get('semantic_mapping_note_fr'),
                     'official_sources': r['official_sources'],
                     'original_source_id': r.get('original_source_id'),
                     'original_source_locator': r.get('original_source_locator'),
                     'source_capture_status': 'NOT_CAPTURED', 'source_capture_sha256': None,
                     'reviewer': 'ChatGPT (GPT-6) - approbation editoriale IA',
                     'editorial_review_date': '2026-11-10',
                     'canonical_admission_authorized': False,
                     'publication_authorized': False})
    if Counter(x['mapping_state'] for x in data)['BLOQUE_CORRESPONDANCE'] != 2 or len(MAPPING_CORRECT) != 1:
        raise Refus('Corrections de correspondance non conformes')
    ctx.update({'decisions': data, 'concepts': concepts, 'identities': mapping,
                'r2_sources': r2_sources, 'r2_proposals': r2,
                'verified_v19_ledger': validated,
                'manifest': manifest, 'data_source_sha256': {
                    str(p.name): sha(load(p)) for p in sorted(PAYLOAD.glob('*')) if p.is_file()
                }})
    return ctx


def esc(s):
    return html.escape(str(s or ''))


def reader(concept, entries):
    cid = concept['unesco_id']; label = concept['preferred_labels']['en'][0]
    approved = [e for e in entries if e['review_state'] == 'APPROUVE_IA_NON_CANONIQUE_PREUVES_A_ARCHIVER']
    mapping_hold = [e for e in entries if e['review_state'] == 'APPROUVE_IA_MAIS_CARTOGRAPHIE_BLOQUEE']
    suspended = [e for e in entries if e['review_state'] == 'SUSPENDU_PREUVES']
    lines = [f'<h1>{esc(label)} <small>{esc(cid)}</small></h1>',
             '<p><strong>Recherche privée V22. Non canonique, non publiée.</strong> Les approbations sont éditoriales et réalisées par IA. Les sources officielles ne sont pas archivées localement.</p>']
    for title, records in [('Affirmations retenues par IA', approved),
                           ('Rattachements conceptuels bloqués', mapping_hold),
                           ('Propositions suspendues', suspended)]:
        lines.append('<h2>' + title + f' ({len(records)})</h2><ol>')
        for r in records:
            text = r['effective_statement'] or r['original_statement']
            lines.append('<li><strong>' + esc(r['proposal_id']) + '</strong> — ' + esc(text))
            if r['original_statement'] != r['effective_statement'] and r['effective_statement']:
                lines.append('<p class="old">Proposition initiale : ' + esc(r['original_statement']) + '</p>')
            lines.append('<p>Décision : ' + esc(r['decision']) + ' | Concept effectif : ' + esc(r['effective_unesco_id']) +
                         ' | ' + esc(r['mapping_state']) + '</p>')
            if r['decision_reason_fr']:
                lines.append('<p>' + esc(r['decision_reason_fr']) + '</p>')
            if r['official_sources']:
                links = ['<a href="' + esc(x.get('url')) + '">' + esc(x.get('source_key', 'Source')) +
                         ' — ' + esc(x.get('locator')) + '</a>' for x in r['official_sources'] if x.get('url', '').startswith('https://')]
                lines.append('<p>Références de vérification : ' + ', '.join(links) + '</p>')
            lines.append('</li>')
        lines.append('</ol>')
    return ('<!DOCTYPE html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width">'
            '<title>' + esc(label) + ' — UNESCO V22 (private)</title><style>'
            'body{font:16px/1.6 system-ui,sans-serif;max-width:900px;margin:4rem auto;padding:0 1rem;color:#222}'
            'h1,h2{line-height:1.2}h1 small{font-size:.6em;color:#666}.old{color:#665}li{margin:1.4em 0}'
            'a{color:#1463a0}p{margin:.45em 0}</style><p><a href="index.html">Index des 41 concepts</a></p>' +
            '\n'.join(lines) + '</html>\n').encode('utf-8')


def build_files(ctx):
    records = ctx['decisions']
    ct = Counter(x['review_state'] for x in records)
    text_fixes = [x for x in records if x['decision'] == 'APPROUVE_IA_REFORMULE']
    held = [x for x in records if x['mapping_state'] == 'BLOQUE_CORRESPONDANCE']
    suspended = [x for x in records if x['decision'] == SUSPENDED]
    if (len(text_fixes), len(held), len(suspended)) != (10, 2, 6):
        raise Refus('Comptes de sortie inattendus')
    summary = {'format': 'koa.unesco-v22-ai-reviewed-private/1.0', 'branch': BRANCH,
               'source_review_date': '2026-11-10', 'overlay_version': 'v22',
               'source_v18_report_sha256': ctx['v18_report_sha256'],
               'source_lot_002_manifest_sha256': ctx['batch_manifest_sha256'],
               'approval_scope': 'editorial_ai_only',
               'source_capture_status': 'NOT_CAPTURED',
               'canonical_KQ_KP_KA_KS_created': 0, 'publication_authorized': False,
               'counts': {'all_reviewed': 44, 'approved_text_unchanged': 28,
                          'approved_text_revised': 10, 'suspended': 6,
                          'approved_mapping_correct': 36, 'approved_mapping_on_hold': 2,
                          'semantic_mapping_corrected': 1,
                          'atlas_lot_002_v19_candidates': 25,
                          'r2_official_source_references': 6,
                          'concepts_preserved': 41},
               'remaining_gates': ['Archive verified official source captures with SHA-256',
                                   'Resolve two UNESCO concept attachments',
                                   'Run independent Framework/Kit canonical admission qualification if desired']}
    files = {}
    files['RAPPORT_V22.json'] = jb(summary)
    files['REGISTRE_44_REVU_IA_V22.json'] = jb({'format': 'koa.unesco-v22-editorial-records/1.0',
                                                'branch': BRANCH, 'records': records,
                                                'canonical_admissions': 0})
    files['CORRECTIONS_10_TEXTES_ET_1_RATTACHEMENT_V22.json'] = jb({
        'text_corrections': [{'proposal_id': x['proposal_id'], 'before': x['original_statement'],
                              'after': x['effective_statement']} for x in text_fixes],
        'semantic_corrections': [{'proposal_id': x['proposal_id'], 'before': x['original_unesco_id'],
                                  'after': x['effective_unesco_id'], 'status': 'AI_EDITORIAL_REMAP_NON_CANONICAL'}
                                 for x in records if x['mapping_state'] == 'CORRIGE_IA_V22'],
        'mapping_holds': [{'proposal_id': x['proposal_id'], 'concept': x['original_unesco_id']}
                          for x in held]})
    files['SUSPENSIONS_6_V22.json'] = jb({'status': 'NON_INTEGREES', 'records': suspended})
    files['R2_19_APPROBATIONS_IA_NON_CANONIQUES.jsonl'] = ''.join(json.dumps(x, ensure_ascii=False, sort_keys=True) + '\n' for x in records if x['source_collection'] == 'R2_RIGHT_TO_EDUCATION').encode('utf-8')
    files['LOT_002_25_REVUES_IA_NON_CANONIQUES.jsonl'] = ''.join(json.dumps(x, ensure_ascii=False, sort_keys=True) + '\n' for x in records if x['source_collection'] == 'WIKIPEDIA_LOT_002_V21').encode('utf-8')
    files['REFERENCES_R2_6_A_ARCHIVER.json'] = jb(ctx['r2_sources'])
    files['PROVENANCE_V22.json'] = jb({'work_branch': BRANCH,
        'input_payload_sha256': ctx['data_source_sha256'],
        'v18_report_sha256': ctx['v18_report_sha256'],
        'lot_002_manifest_sha256': ctx['batch_manifest_sha256'],
        'ledger_v19_expected_sha256': sha(intake.jb(ctx['verified_v19_ledger'])),
        'source_captures_sha256': None, 'source_captures_locally_archived': False})
    by_concept = defaultdict(list)
    for r in records:
        by_concept[r['effective_unesco_id']].append(r)
    cartography = []
    index_lines = ['<!DOCTYPE html><html lang="en"><meta charset="utf-8"><title>UNESCO V22 — private AI review</title>',
                   '<style>body{font:16px/1.5 system-ui,sans-serif;max-width:1000px;margin:3rem auto;padding:0 1rem}td,th{text-align:left;padding:.5em;border-bottom:1px solid #ddd}table{border-collapse:collapse;width:100%}</style>',
                   '<h1>UNESCO Educational Policy — recherche privée V22</h1>',
                   '<p><strong>44 décisions : 38 propositions retenues par IA (36 bien rattachées, 2 en attente de rattachement), 6 suspendues.</strong> Aucune admission canonique ni publication. Captures officielles non archivées.</p><table><tr><th>Concept</th><th>Approuvées</th><th>Bloquées</th><th>Suspendues</th></tr>']
    for cid, c in sorted(ctx['concepts'].items(), key=lambda a:int(a[0][7:]) if a[0][7:].isdigit() else a[0]):
        ents = by_concept[cid]
        keep = sum(x['review_state'] == 'APPROUVE_IA_NON_CANONIQUE_PREUVES_A_ARCHIVER' for x in ents)
        hold = sum(x['review_state'] == 'APPROUVE_IA_MAIS_CARTOGRAPHIE_BLOQUEE' for x in ents)
        susp = sum(x['review_state'] == 'SUSPENDU_PREUVES' for x in ents)
        label = c['preferred_labels']['en'][0]
        cartography.append({'unesco_id': cid, 'english_label': label,
                            'provisional_kq_id': ctx['identities']['unesco-skos:' + cid],
                            'editorial_ai_approved': keep, 'mapping_hold': hold, 'suspended': susp})
        index_lines.append('<tr><td><a href="' + esc(cid) + '.html">' + esc(label) + '</a> (' + esc(cid) +
                           ')</td><td>' + str(keep) + '</td><td>' + str(hold) + '</td><td>' + str(susp) + '</td></tr>')
        files['reader_en/' + cid + '.html'] = reader(c, ents)
    index_lines.append('</table></html>')
    files['reader_en/index.html'] = ('\n'.join(index_lines) + '\n').encode('utf-8')
    files['CARTOGRAPHIE_41_CONCEPTS_V22.json'] = jb({'branch': BRANCH, 'concepts': cartography})
    r2_lines = ['# Right to education — revue éditoriale IA V22', '',
                '**Recherche privée ; non canonique ; non publiée.**', '',
                'Concept UNESCO `concept10`, KQ3 provisoire. Ces 19 propositions ont été retenues par la revue éditoriale IA, sans preuve archivée locale ni validation de publication.', '']
    for r in records:
        if r['source_collection'] == 'R2_RIGHT_TO_EDUCATION':
            r2_lines.extend(['## ' + r['proposal_id'], '', r['effective_statement'], '',
                             'Référence : ' + ', '.join(x.get('url','') + ' (' + x.get('locator','') + ')' for x in r['official_sources']), ''])
    files['ARTICLE_RIGHT_TO_EDUCATION_IA_V22.md'] = ('\n'.join(r2_lines) + '\n').encode('utf-8')
    files['LIRE_DABORD_V22.md'] = ('# UNESCO V22 — résultats installés\n\n'
        '- `RAPPORT_V22.json` : compte rendu et verrous.\n'
        '- `REGISTRE_44_REVU_IA_V22.json` : les 44 décisions intégrées dans une vue de recherche privée.\n'
        '- `CORRECTIONS_10_TEXTES_ET_1_RATTACHEMENT_V22.json` : corrections réellement appliquées dans cette vue.\n'
        '- `reader_en/index.html` : lecture privée des 41 ancrages et textes retenus.\n'
        '- `ARTICLE_RIGHT_TO_EDUCATION_IA_V22.md` : 19 affirmations R2 revues.\n'
        '- `SUSPENSIONS_6_V22.json` : six propositions non admises.\n'
        '- `atlas_documentaire_v19_candidats/` (dossier voisin) : 25 propositions reçues avec le contrat v19.\n\n'
        '**Frontière** : aucune modification de v18/v19, du Framework, du Workbench ou d’un Kristal canonique. '
        'L’approbation IA ne prétend pas être une signature humaine. Les captures officielles restent à archiver.\n').encode('utf-8')
    files['MANIFESTE_V22.json'] = jb({'format': 'koa.unesco-v22-output-hashes/1.0',
       'branch': BRANCH, 'files_sha256': {k: sha(v) for k,v in sorted(files.items())},
       'canonical_KQ_KP_KA_KS_created': 0, 'publication_authorized': False})
    return files


def validate_existing(out: Path, files: dict):
    if not out.is_dir() or out.is_symlink():
        raise Refus('Sortie V22 existante non conforme')
    found = {str(p.relative_to(out)).replace('\\','/') for p in out.rglob('*') if p.is_file()}
    if found != set(files):
        raise Refus('Sortie V22 existante modifiée (fichiers divergents)')
    for name, content in files.items():
        if sha(load(out / name)) != sha(content):
            raise Refus('Sortie V22 existante modifiée : ' + name)


def apply(work: Path, ctx: dict, files: dict):
    ledger = work / LEDGER_NAME
    if ledger.is_symlink(): raise Refus('Répertoire de registre symbolique')
    ledger_doc = ctx['verified_v19_ledger']
    ledger_data = intake.jb(ledger_doc)
    ledger_digest = sha(ledger_data)
    ledger_file = ledger / (ledger_digest + '.json')
    if ledger_file.exists() and sha(load(ledger_file)) != ledger_digest:
        raise Refus('Registre déjà existant et altéré')
    out = work / OUT_NAME
    if out.exists():
        validate_existing(out, files)
        state = 'DEJA_INSTALLE_IDENTIQUE'
    else:
        temp = Path(tempfile.mkdtemp(prefix='.unesco_v22_stage_',dir=work))
        try:
            for name, content in files.items():
                destination = temp / name
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(content)
            if ledger.exists() and not ledger.is_dir():
                raise Refus('Répertoire registre inaccessible')
            ledger.mkdir(exist_ok=True)
            if not ledger_file.exists():
                try:
                    with ledger_file.open('xb') as f:
                        f.write(ledger_data)
                        f.flush()
                        os.fsync(f.fileno())
                except FileExistsError:
                    if sha(load(ledger_file)) != ledger_digest:
                        raise Refus('Collision avec un registre différent')
            temp.rename(out)
            state = 'V22_CORRECTIONS_APPLIQUEES_PRIVÉES'
        finally:
            if temp.exists(): shutil.rmtree(temp)
    if not ledger_file.is_file() or sha(load(ledger_file)) != ledger_digest:
        raise Refus('Réception V19 non confirmée')
    return {'status': state, 'work': str(work), 'reader': str(out / 'reader_en' / 'index.html'),
            'report': str(out / 'RAPPORT_V22.json'), 'v19_candidate_ledger': str(ledger_file),
            'candidate_records': 25, 'ai_editorial_approved': 38, 'reformulations_applied': 10,
            'mapping_corrections': 1, 'mapping_holds': 2, 'suspended': 6,
            'canonical_admissions': 0, 'publication_authorized': False}


def main(argv=None):
    parser = argparse.ArgumentParser(description='UNESCO V22 : vrai correctif additif de revue IA, sans canonisation')
    parser.add_argument('command', choices=('check','apply','report'))
    parser.add_argument('--work', type=Path, default=WORK)
    parser.add_argument('--batch', type=Path, default=None)
    args = parser.parse_args(argv)
    try:
        work = args.work
        batch = args.batch or (work / LOT_NAME)
        ctx = load_and_validate(work, batch)
        files = build_files(ctx)
        if args.command == 'check':
            result = {'status':'V22_PREFLIGHT_OK','target':str(work / OUT_NAME),
                      'candidate_ledger':str(work / LEDGER_NAME),
                      'files_generated_if_applied':len(files),
                      'ai_approved':38,'corrections':10,'mapping_corrections':1,
                      'mapping_holds':2,'suspended':6,'canonical_admissions':0}
        elif args.command == 'apply':
            result = apply(work, ctx, files)
        else:
            out = work / OUT_NAME
            validate_existing(out,files)
            result = {'status':'V22_RAPPORT_INTEGRE','report':str(out / 'RAPPORT_V22.json'),
                      'ai_approved':38,'corrections_applied':10,'mapping_holds':2,
                      'suspended':6,'canonical_admissions':0}
        print(json.dumps(result,indent=2,ensure_ascii=False))
        return 0
    except (Refus, ValueError, OSError, KeyError, TypeError, json.JSONDecodeError, __import__('zipfile').BadZipFile) as exc:
        print(json.dumps({'status':'V22_REFUS_SECURITE','error':str(exc)},ensure_ascii=False),file=sys.stderr)
        return 2

if __name__ == '__main__':
    sys.exit(main())
