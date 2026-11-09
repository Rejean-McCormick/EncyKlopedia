#!/usr/bin/env python3
"""Overlay code: integrate ChatGPT's unsigned 41-concept review into private UNESCO work.

This is not a semantic-graph mint, a Kit v11 authoring command, a KS approval,
or a GitHub publish operation. No network, AI API, Wikipedia scan or external DB.

The bundled review is a sealed, explicitly unsigned research input. Verify its
SHA-256 manifest and compare every reviewed key against the stage-11 working
copy before depositing or producing a Kristalizer *review-only* handoff.
"""
from __future__ import annotations

import argparse
import csv
from hashlib import sha256
from io import StringIO
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import sys
import tempfile
import zipfile

BRANCH = 'unesco-mt1-10'
WORK = Path(r'D:\EncyKlopedia\30_working\unesco_mt1_10\autopilot_concept10_puis_41')
RESOURCE = Path(__file__).resolve().parent / 'data' / 'revue_globale_chatgpt_20261107.zip'
STAGE11 = 'semantic_stage_v11_global'
STAGE12 = 'semantic_stage_v12_revue_chatgpt'
HANDOFF = 'RECOMMANDATIONS_85_POUR_KRISTALIZER_NON_CANONIQUES.json'
OVERLAY_MANIFEST = 'MANIFESTE_OVERLAY_ETAPE12.json'
SAFE_SHA = re.compile(r'^[0-9a-f]{64}$')
DECISION_NAMES = (
    ('DECISIONS_41_IDENTITES_EDITABLE.csv', 'unesco_id', 41),
    ('DECISIONS_85_PROPOSITIONS_EDITABLE.csv', 'proposal_ref', 85),
    ('DECISIONS_61_RELATIONS_EDITABLE.csv', 'group_ref', 61),
    ('DECISIONS_4_SOURCES_CONCEPT10_EDITABLE.csv', 'reference_id', 4),
)
REVIEW_FILES = (
    ('REVUE_41_IDENTITES_NON_SIGNEE.csv', 'unesco_id', 41),
    ('REVUE_85_PROPOSITIONS_NON_SIGNEE.csv', 'proposal_ref', 85),
    ('REVUE_61_RELATIONS_SKOS_NON_SIGNEE.csv', 'group_ref', 61),
    ('REVUE_81_PISTES_DE_SOURCES_NON_KS.csv', 'reference_id', 81),
    ('CONCEPT10_8_FRAGMENTS_ANNOTES_NON_KA.csv', 'fragment_ref', 8),
    ('191_RECOMMANDATIONS_NON_SIGNEES.csv', None, 191),
)

class ReviewError(ValueError):
    pass


def fail(reason):
    raise ReviewError(reason)


def digest(raw):
    return sha256(raw).hexdigest()


def file_digest(path):
    h = sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def read_json_bytes(data):
    return json.loads(data.decode('utf-8-sig'))


def json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode('utf-8')


def rows_bytes(data):
    with StringIO(data.decode('utf-8-sig'), newline='') as stream:
        return list(csv.DictReader(stream))


def rows_file(path):
    if not path.is_file():
        fail(f'Fichier source absent: {path}')
    return rows_bytes(path.read_bytes())


def unique_key(rows, field, quantity, name):
    if len(rows) != quantity:
        fail(f'{name}: cardinalite {len(rows)} != {quantity}')
    vals = [r.get(field, '') for r in rows]
    if not all(vals) or len(set(vals)) != quantity:
        fail(f'{name}: identifiant vide ou double')
    return {r[field]: r for r in rows}


def safe_relative(s):
    p = PurePosixPath(s)
    if (not isinstance(s, str) or not s or '\\' in s or s.startswith('/')
            or ':' in s or any(part in ('', '.', '..') for part in p.parts)
            or p.as_posix() != s):
        fail('Chemin interdit dans le manifeste/ZIP: ' + str(s))
    return p


def check_private_directory(work):
    work = work.absolute()
    if not work.is_dir() or work.is_symlink():
        fail(f'Dossier de travail prive absent ou lien: {work}')
    if (work / STAGE11).is_symlink() or (work / STAGE12).is_symlink():
        fail('Lien symbolique de dossier etape interdit')
    for folder in (work, *work.parents):
        if (folder / '.git').exists():
            fail(f'Sortie dans depot Git interdite: {folder}')
    return work


def load_payload(resource=RESOURCE):
    if not resource.is_file():
        fail('Ressource de revue manquante: ' + str(resource))
    contents = {}
    with zipfile.ZipFile(resource) as bundle:
        items = bundle.infolist()
        if len(items) > 100 or sum(i.file_size for i in items) > 5_000_000:
            fail('Ressource de revue hors limites')
        for i in items:
            safe_relative(i.filename)
            if i.is_dir() or i.filename in contents or ((i.external_attr >> 16) & 0o170000) == 0o120000:
                fail('Membre de ZIP non regulier ou double: ' + i.filename)
            contents[i.filename] = bundle.read(i)
    if 'MANIFESTE_RECOMMANDATIONS.json' not in contents:
        fail('Manifeste de revue manquant')
    manifest = read_json_bytes(contents['MANIFESTE_RECOMMANDATIONS.json'])
    if manifest.get('branch') != BRANCH or manifest.get('format') != 'koa.unesco-mt1-10-chatgpt-review-delivery-manifest/1.0':
        fail('Profil ou branche de revue incorrect')
    expected = manifest.get('files_sha256')
    if not isinstance(expected, dict) or set(contents) != set(expected) | {'MANIFESTE_RECOMMANDATIONS.json'}:
        fail('Liste de fichiers de revue incorrecte')
    for rel, sha in expected.items():
        safe_relative(rel)
        if not isinstance(sha, str) or not SAFE_SHA.fullmatch(sha) or digest(contents[rel]) != sha:
            fail('Empreinte de la revue incorrecte: ' + rel)
    for rel, field, count in REVIEW_FILES:
        if rel not in contents:
            fail('Table de revue absente: ' + rel)
        data = rows_bytes(contents[rel])
        if field: unique_key(data, field, count, rel)
        elif len(data) != count:
            fail('191 recommandations: nombre incorrect')
    return manifest, contents


def load_stage11(work, manifest_review):
    source = work / STAGE11
    manifest_file = source / 'MANIFESTE_PASSE_GLOBALE.json'
    if not manifest_file.is_file() or manifest_file.is_symlink():
        fail('Manifeste de la passe globale absent')
    expected_digest = manifest_review.get('input_stage11_manifest_sha256')
    if file_digest(manifest_file) != expected_digest:
        fail('Manifeste de la passe globale DIFFERENT: aucune importation')
    m = read_json_bytes(manifest_file.read_bytes())
    if (m.get('branch') != BRANCH or m.get('format') != 'koa.unesco-mt1-10-stage11-private-manifest/1.0'
            or m.get('canonical_files_created') != 0 or m.get('github_push') is not False):
        fail('Manifeste global non prive ou profil inattendu')
    immutables = m.get('immutable_files_sha256')
    if not isinstance(immutables, dict) or not immutables:
        fail('Manifeste global sans empreintes')
    for rel, expected in immutables.items():
        safe_relative(rel)
        p = source / rel
        if p.is_symlink() or not p.is_file() or not SAFE_SHA.fullmatch(expected) or file_digest(p) != expected:
            fail(f'Fichier immutable stage11 modifie: {rel}')
    tables = {
        'identities': unique_key(rows_file(source / 'TABLEAU_41_IDENTITES.csv'), 'unesco_id', 41, 'identites globales'),
        'proposals': unique_key(rows_file(source / 'TABLEAU_85_PROPOSITIONS.csv'), 'proposal_ref', 85, 'propositions globales'),
        'relations': unique_key(rows_file(source / 'GROUPES_61_RELATIONS_INTERNES.csv'), 'group_ref', 61, 'relations globales'),
        'sources': unique_key(rows_file(source / 'FILE_81_SOURCES_A_ATTESTER.csv'), 'reference_id', 81, 'sources globales'),
    }
    decisions = {}
    for rel, key, count in DECISION_NAMES:
        rows = rows_file(source / rel)
        decisions[rel] = unique_key(rows, key, count, rel)
    for rel, setname, key in (
        ('DECISIONS_41_IDENTITES_EDITABLE.csv', 'identities', 'unesco_id'),
        ('DECISIONS_85_PROPOSITIONS_EDITABLE.csv', 'proposals', 'proposal_ref'),
        ('DECISIONS_61_RELATIONS_EDITABLE.csv', 'relations', 'group_ref'),
    ):
        if set(decisions[rel]) != set(tables[setname]):
            fail(rel + ': decisions ne correspondent pas aux ancrages')
    if not set(decisions['DECISIONS_4_SOURCES_CONCEPT10_EDITABLE.csv']).issubset(set(tables['sources'])):
        fail('Decisions sur sources de concept10 non rattachees')
    for rel, _, _ in DECISION_NAMES:
        for row in decisions[rel].values():
            status = row.get('decision', '')
            allowed = {'PENDING', 'CAPTURE_A_VERIFIER', 'REJETER'} if 'SOURCES_' in rel else {'PENDING', 'SOUMETTRE_A_LA_REVUE', 'REFORMULER', 'REJETER'}
            if status not in allowed:
                fail(rel + ': decision interdite')
            if status != 'PENDING' and not all(row.get(k, '').strip() for k in ('responsable', 'decision_id', 'justification')):
                fail(rel + ': decision non PENDING sans justification/responsable')
    return m, tables, decisions


def verify_semantics(contents, tables):
    rev_i = unique_key(rows_bytes(contents['REVUE_41_IDENTITES_NON_SIGNEE.csv']), 'unesco_id', 41, 'revue identites')
    rev_p = unique_key(rows_bytes(contents['REVUE_85_PROPOSITIONS_NON_SIGNEE.csv']), 'proposal_ref', 85, 'revue propositions')
    rev_r = unique_key(rows_bytes(contents['REVUE_61_RELATIONS_SKOS_NON_SIGNEE.csv']), 'group_ref', 61, 'revue relations')
    rev_s = unique_key(rows_bytes(contents['REVUE_81_PISTES_DE_SOURCES_NON_KS.csv']), 'reference_id', 81, 'revue sources')
    if set(rev_i) != set(tables['identities']) or set(rev_p) != set(tables['proposals']) or set(rev_r) != set(tables['relations']) or set(rev_s) != set(tables['sources']):
        fail('Cles de revue non concordantes avec la passe globale')
    for ref, r in rev_i.items():
        src = tables['identities'][ref]
        if (r['label_en'], r['unesco_uri'], r['qid_candidat']) != (src['label_en'], src['unesco_uri'], src['qid_candidat']):
            fail('Identite editee sans ancrage: ' + ref)
        if r.get('approval_humaine') != 'PENDING' or r.get('exactMatch_approuve') != 'NON':
            fail('Revue d identite declaree approuvee: ' + ref)
    for ref, r in rev_p.items():
        src = tables['proposals'][ref]
        if (r['unesco_id'], r['texte_original_en'], r['prior_original']) != (src['unesco_id'], src['statement_en'], src['review_preavis']):
            fail('Texte ou reference IA modifiee sans ancrage: ' + ref)
        if r.get('decision_humaine_originale') != 'PENDING' or r.get('KQ_KP_KA_crees') != 'NON' or r.get('KS_qualifiee') != 'NON':
            fail('Revue IA tente une admission: ' + ref)
    for ref, r in rev_r.items():
        src = tables['relations'][ref]
        if (r['source_id'], r['target_id'], r['relation_skos'], r['observations_reciproques']) != (
                src['source_ou_membre_a'], src['cible_ou_membre_b'], src['relation_normalisee'], src['observations_reciproques']):
            fail('Relation SKOS editee sans ancrage: ' + ref)
        if r.get('decision_humaine') != 'PENDING' or r.get('KA_creee') != 'NON':
            fail('Revue relation pretend creer KA: ' + ref)
    for ref, r in rev_s.items():
        src = tables['sources'][ref]
        if (r['url'], r['genre']) != (src['url'], src['document_type']):
            fail('Reference documentaire editee: ' + ref)
        if r.get('KS_approvee') != 'NON' or r.get('capture_officielle_verifiee') != 'NON':
            fail('Revue sources indique fausse preuve KS: ' + ref)
    recs = rows_bytes(contents['191_RECOMMANDATIONS_NON_SIGNEES.csv'])
    expected = {('IDENTITE', key) for key in rev_i}
    expected |= {('PROPOSITION', key) for key in rev_p}
    expected |= {('SKOS_INTERNE', key) for key in rev_r}
    concept10 = set(rows_bytes(contents['CONCEPT10_8_FRAGMENTS_ANNOTES_NON_KA.csv'])[0].keys())
    if not {'fragment_ref', 'proposal_ref', 'decision_humaine'}.issubset(concept10):
        fail('Fragments de concept10: colonnes requises absentes')
    targets = {ref for ref, row in rev_s.items() if row['portee'] == 'CIBLE_CONCEPT10'}
    if len(targets) != 4:
        fail('Quatre references concept10 attendues')
    expected |= {('SOURCE_CONCEPT10', x) for x in targets}
    got = [(r['type'], r['ref']) for r in recs]
    if set(got) != expected or len(set(got)) != 191 or any(r.get('decision_humaine') != 'PENDING' for r in recs):
        fail('191 recommandations: ancrages ou decisions alteres')
    atoms = rows_bytes(contents['CONCEPT10_8_FRAGMENTS_ANNOTES_NON_KA.csv'])
    for row in atoms:
        if row['proposal_ref'] not in rev_p or rev_p[row['proposal_ref']]['unesco_id'] != 'concept10':
            fail('Fragment de concept10 non rattache')
        if row.get('decision_humaine') != 'PENDING' or row.get('KQ_KP_KA_KS_generes') != 'NON':
            fail('Fragment concept10 pretend canonique')
    if len([i for i in rev_i.values() if i['qid_candidat']]) != 36:
        fail('36 QID candidats attendus')
    return rev_p, rev_i, rev_r, rev_s


def handoff_payload(review, review_manifest, global_manifest, review_manifest_raw_sha):
    entries = []
    for proposal_ref, row in sorted(review.items()):
        entries.append({
            'proposal_ref': proposal_ref,
            'unesco_id': row['unesco_id'],
            'statement_original_en': row['texte_original_en'],
            'editorial_suggestion_en': row['texte_propose_en'],
            'editorial_assessment': row['avis_chatgpt_non_signe'],
            'source_search_hint_fr': row['preuve_a_chercher_fr'],
            'semantic_risk_fr': row['precision_et_risque_fr'],
            'model_provenance': 'CHATGPT_CONVERSATION_UNSIGNED_REVIEW',
            'not_ks': True,
            'canonical_KQ': None,
            'canonical_KP': None,
            'canonical_KA': None,
            'canonical_KS': [],
            'review_status': 'HUMAN_DECISION_REQUIRED',
        })
    return {
        'format': 'kristalizer.unesco-mt1-10-unsigned-global-review-handoff/1.0',
        'branch': BRANCH,
        'one_branch_kristal': True,
        'source_stage11_manifest_sha256': review_manifest['input_stage11_manifest_sha256'],
        'source_stage11_immutable_file_count': len(global_manifest['immutable_files_sha256']),
        'review_manifest_sha256': review_manifest_raw_sha,
        'recommendation_count': 85,
        'human_decisions_written_by_tool': 0,
        'approved_KS_by_tool': 0,
        'canonical_identifiers_minted_by_tool': 0,
        'canon_admission_authorized': False,
        'publication_authorized': False,
        'proposals': entries,
    }


def verify_output(src, files):
    if src.is_symlink():
        fail('Dossier destination symbolique interdit')
    for rel, data in files.items():
        safe_relative(rel)
        p = src / rel
        if p.is_symlink() or (p.exists() and (not p.is_file() or file_digest(p) != digest(data))):
            fail('Sortie modifiee ou conflit : ' + rel + ' (aucun ecrasement)')


def publish_new_files(dest, files, *, check_only):
    verify_output(dest, files)
    existing = sum((dest / name).is_file() for name in files)
    if check_only:
        return 'VERIFICATION_SANS_ECRITURE', existing
    dest.parent.mkdir(parents=True, exist_ok=True)
    if not dest.exists():
        tmp = Path(tempfile.mkdtemp(prefix='.review-overlay-', dir=dest.parent))
        try:
            for rel, data in files.items():
                p = tmp / rel
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_bytes(data)
            if dest.exists():
                fail('La destination est apparue durant la preparation')
            tmp.rename(dest)
            return 'INSTALLE', 0
        finally:
            if tmp.exists():
                shutil.rmtree(tmp, ignore_errors=True)
    if not dest.is_dir():
        fail('Destination non dossier')
    for rel, data in files.items():
        p = dest / rel
        if not p.exists():
            p.parent.mkdir(parents=True, exist_ok=True)
            try:
                with p.open('xb') as stream:
                    stream.write(data)
            except FileExistsError:
                if file_digest(p) != digest(data):
                    fail('Fichier cree en concurrence et divergent: ' + rel)
            if file_digest(p) != digest(data):
                fail('Erreur de copie du correctif: ' + rel)
    return ('DEJA_PRESENT' if existing == len(files) else 'COMPLETÉ_SANS_ECRASEMENT'), existing


def main(argv=None):
    ap = argparse.ArgumentParser(description='Overlay EncyKlopedia -> Kristalizer: revue non signee et controles (sans canon)')
    ap.add_argument('--work', type=Path, default=WORK)
    ap.add_argument('--check-only', action='store_true', help='verifier les sources, sans ecriture')
    args = ap.parse_args(argv)
    work = check_private_directory(args.work)
    review_manifest, payload = load_payload()
    global_manifest, tables, decisions = load_stage11(work, review_manifest)
    reviews, _, _, _ = verify_semantics(payload, tables)
    handoff = json_bytes(handoff_payload(reviews, review_manifest, global_manifest, digest(payload['MANIFESTE_RECOMMANDATIONS.json'])))
    deposit = {name: payload[name] for name in review_manifest['files_sha256']}
    deposit['MANIFESTE_RECOMMANDATIONS.json'] = payload['MANIFESTE_RECOMMANDATIONS.json']
    deposit[HANDOFF] = handoff
    own_manifest = {
        'format': 'koa.unesco-mt1-10-review-overlay-installation/1.0',
        'branch': BRANCH,
        'stage11_manifest_sha256': review_manifest['input_stage11_manifest_sha256'],
        'payload_zip_sha256': file_digest(RESOURCE),
        'files_sha256': {rel: digest(data) for rel, data in sorted(deposit.items())},
        'publication_authorized': False,
        'canonical_created': 0,
    }
    deposit[OVERLAY_MANIFEST] = json_bytes(own_manifest)
    result, existing = publish_new_files(work / STAGE12, deposit, check_only=args.check_only)
    counts = {n: sum(row['decision'] == 'PENDING' for row in decisions[n].values()) for n,_,_ in DECISION_NAMES}
    output = {
        'status': 'PRIVATE_REVIEW_OVERLAY_INTEGRATED_CANONICAL_BLOCKED',
        'operation': result,
        'output': str(work / STAGE12),
        'branch': BRANCH,
        'reviewed_concepts': 41,
        'reviewed_proposals': 85,
        'reviewed_internal_skos': 61,
        'source_leads': 81,
        'non_signed_recommendations': 191,
        'pending_global_decisions': sum(counts.values()),
        'pending_breakdown': counts,
        'existing_identical_files': existing,
        'canonical_KQ_KP_KA_KS_created': 0,
        'publication_authorized': False,
        'git_push': False,
    }
    print(json.dumps(output, ensure_ascii=False, sort_keys=True, indent=2))
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (ReviewError, ValueError, OSError, KeyError, UnicodeError, zipfile.BadZipFile, json.JSONDecodeError) as exc:
        print('ECHEC SECURISE REVIEW OVERLAY: ' + str(exc), file=sys.stderr)
        sys.exit(2)
